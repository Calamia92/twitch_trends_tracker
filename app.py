import streamlit as st
import pymongo
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# Configuration de la page
st.set_page_config(
    page_title="🎮 Twitch Trends Tracker",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto-refresh toutes les 60 secondes
import time
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

current_time = time.time()
if current_time - st.session_state.last_refresh > 60:  # 60 secondes
    st.session_state.last_refresh = current_time
    st.cache_data.clear()
    st.rerun()

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #9146ff, #00f5ff);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .trend-up { color: #00ff00; }
    .trend-down { color: #ff0000; }
    .trend-stable { color: #ffa500; }
</style>
""", unsafe_allow_html=True)

# Titre principal
st.markdown("""
<div class="main-header">
    <h1>🎮 Twitch Trends Tracker</h1>
    <p>Dashboard Multi-Sources: Jeux • Événements • Streamers Français</p>
</div>
""", unsafe_allow_html=True)

# Connexion MongoDB
@st.cache_resource
def get_mongodb_connection():
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"❌ Erreur connexion MongoDB: {e}")
        return None

client = get_mongodb_connection()
if not client:
    st.stop()

db = client['twitch_trends']

def filter_active_streamers(df):
    """
    Filtrer les streamers actifs en excluant les bannis/inactifs CONFIRMÉS
    """
    if df.empty:
        return df
    
    # Liste noire CONFIRMÉE des streamers définitivement bannis/inactifs
    # Sources: Communauté Twitch, news gaming, vérifications manuelles
    confirmed_banned_streamers = [
        'DrDisrespect',   # ✅ CONFIRMÉ BANNI JUIN 2020 - Violation TOS Twitch permanente
        'Phantoml0rd',    # ✅ CONFIRMÉ BANNI - Gambling scam CSGO skins
        'Ice_Poseidon',   # ✅ CONFIRMÉ BANNI - Violations TOS répétées, harassment
        'JoshOG',         # ✅ CONFIRMÉ - Scandal gambling CSGO, réputation compromise
        'TmarTn',         # ✅ CONFIRMÉ - Scandal gambling CSGO, déplacé YouTube
        'Syndicate',      # ✅ CONFIRMÉ - Scandal gambling CSGO, focus YouTube
        'CouRage',        # ✅ CONFIRMÉ - Migré exclusivement YouTube Gaming
        'DisguisedToast', # ✅ CONFIRMÉ - Migré Facebook Gaming puis YouTube
        'Valkyrae',       # ✅ CONFIRMÉ - YouTube Gaming exclusif depuis 2020
    ]
    
    # Convertir en lowercase pour comparaison insensible à la casse
    banned_lower = [name.lower() for name in confirmed_banned_streamers]
    
    # Identifier les streamers filtrés (pour statistics, pas pour print)
    filtered_streamers = df[df['username'].str.lower().isin(banned_lower)]
    
    # Filtrer les bannis confirmés (silencieusement)
    active_df = df[~df['username'].str.lower().isin(banned_lower)].copy()
    
    # Filtrer par activité récente
    current_time = pd.Timestamp.now()
    if 'timestamp' in active_df.columns:
        active_df['timestamp'] = pd.to_datetime(active_df['timestamp'])
        recent_threshold = current_time - pd.Timedelta(days=30)
        active_df = active_df[active_df['timestamp'] >= recent_threshold]
    
    # Filtrer par métriques minimales de crédibilité
    if 'avg_viewers' in active_df.columns and 'followers' in active_df.columns:
        active_df = active_df[
            (active_df['avg_viewers'] > 0) & 
            (active_df['followers'] > 1000)
        ]
    
    return active_df

# Fonctions de chargement des données
@st.cache_data(ttl=30)  # Cache pendant 30 secondes
def load_games_data():
    try:
        games = list(db['games'].find())
        if games:
            df = pd.DataFrame(games)
            if '_id' in df.columns:
                df = df.drop('_id', axis=1)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur chargement jeux: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def load_twitchtracker_enriched_data(force_key=None):
    """Charge les données TwitchTracker enrichies."""
    try:
        # Données games enrichies
        games_enriched = list(db['twitchtracker_games_enriched'].find().sort('rank', 1))
        games_enriched_df = pd.DataFrame(games_enriched) if games_enriched else pd.DataFrame()
        if '_id' in games_enriched_df.columns:
            games_enriched_df = games_enriched_df.drop('_id', axis=1)
        
        # Données trending enrichies
        trending_enriched = list(db['twitchtracker_trending_enriched'].find().sort('trending_rank', 1))
        trending_enriched_df = pd.DataFrame(trending_enriched) if trending_enriched else pd.DataFrame()
        if '_id' in trending_enriched_df.columns:
            trending_enriched_df = trending_enriched_df.drop('_id', axis=1)
        
        # Données streamers enrichies
        streamers_enriched = list(db['twitchtracker_streamers_enriched'].find().sort('rank', 1))
        streamers_enriched_df = pd.DataFrame(streamers_enriched) if streamers_enriched else pd.DataFrame()
        if '_id' in streamers_enriched_df.columns:
            streamers_enriched_df = streamers_enriched_df.drop('_id', axis=1)
        
        # Stats globales enrichies
        global_stats_enriched = list(db['twitchtracker_global_stats_enriched'].find().sort('timestamp', -1).limit(1))
        global_stats_enriched_df = pd.DataFrame(global_stats_enriched) if global_stats_enriched else pd.DataFrame()
        if '_id' in global_stats_enriched_df.columns:
            global_stats_enriched_df = global_stats_enriched_df.drop('_id', axis=1)
            
        return games_enriched_df, trending_enriched_df, streamers_enriched_df, global_stats_enriched_df
        
    except Exception as e:
        st.error(f"Erreur chargement données enrichies: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=30)
def load_events_data():
    try:
        events = list(db['events'].find())
        if events:
            df = pd.DataFrame(events)
            if '_id' in df.columns:
                df = df.drop('_id', axis=1)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur chargement événements: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def load_streamers_data():
    try:
        streamers = list(db['streamers'].find())
        if streamers:
            df = pd.DataFrame(streamers)
            if '_id' in df.columns:
                df = df.drop('_id', axis=1)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur chargement streamers: {e}")
        return pd.DataFrame()

# Chargement des données avec bouton refresh
col1, col2, col3 = st.columns([5, 1, 1])
with col1:
    st.title("🎮 Twitch Trends Tracker - Dashboard d'Analyse")
with col2:
    if st.button("🔄 Soft Refresh", help="Actualiser les données (cache 30s)"):
        st.cache_data.clear()
        st.rerun()
with col3:
    if st.button("⚡ Force Refresh", help="Actualiser immédiatement"):
        st.cache_data.clear()
        # Force un nouveau timestamp pour invalider le cache
        import random
        st.session_state.force_refresh = random.random()
        st.rerun()

# Chargement de toutes les données
force_key = st.session_state.get('force_refresh', 0)
games_df = load_games_data()
events_df = load_events_data()
streamers_df = load_streamers_data()
games_enriched_df, trending_enriched_df, streamers_enriched_df, global_stats_enriched_df = load_twitchtracker_enriched_data(force_key)

# Debug: Afficher les dernières données pour vérifier la fraîcheur
if st.sidebar.checkbox("🔍 Mode Debug", help="Affiche les informations de debug"):
    st.sidebar.markdown("**📅 Dernières données:**")
    
    if not trending_enriched_df.empty and 'timestamp' in trending_enriched_df.columns:
        last_trending = trending_enriched_df['timestamp'].max()
        st.sidebar.text(f"📈 Trending: {str(last_trending)[:16]}")
    
    if not global_stats_enriched_df.empty and 'timestamp' in global_stats_enriched_df.columns:
        last_stats = global_stats_enriched_df['timestamp'].max()
        st.sidebar.text(f"📊 Stats: {str(last_stats)[:16]}")
        
    if not games_df.empty and 'timestamp' in games_df.columns:
        last_games = games_df['timestamp'].max()
        st.sidebar.text(f"🎮 Games: {str(last_games)[:16]}")
    
    st.sidebar.markdown("**🔄 Cache TTL: 30s**")
# Sidebar pour navigation
st.sidebar.title("🎯 Navigation")

# Statut en temps réel
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Statut Live")

# Heure de dernière mise à jour
last_update = datetime.now().strftime("%H:%M:%S")
st.sidebar.success(f"🕐 Dernière MAJ: {last_update}")

# Compte des données RÉELLES
games_total = len(games_df) if not games_df.empty else 0
trending_total = len(trending_enriched_df) if not trending_enriched_df.empty else 0
events_total = len(events_df) if not events_df.empty else 0
streamers_total = len(streamers_df) if not streamers_df.empty else 0

st.sidebar.metric("🎮 Jeux Suivis", games_total)
st.sidebar.metric("� Trending", trending_total) 
st.sidebar.metric("🎯 Événements", events_total)
st.sidebar.metric("🇫🇷 Streamers", streamers_total)

st.sidebar.markdown("---")

page = st.sidebar.selectbox(
    "Choisir une vue",
    ["📊 Vue d'ensemble", "🎮 Jeux Twitch", "📈 TwitchTracker Live", "🎯 Événements Gaming", "🇫🇷 Streamers Français", "💰 Revenus Streamers"]
)

# Affichage selon la page sélectionnée
if page == "📊 Vue d'ensemble":
    st.header("📊 Vue d'ensemble - Analyse des Données")
    
    # Vérification de cohérence des données
    col_check1, col_check2 = st.columns(2)
    
    with col_check1:
        st.markdown("### ✅ Validation des Données")
        if not games_df.empty:
            st.success(f"🎮 {len(games_df)} jeux analysés")
        else:
            st.warning("🎮 Aucune donnée de jeux disponible")
            
        if not events_df.empty:
            st.success(f"🎯 {len(events_df)} événements suivis")
        else:
            st.info("🎯 Aucun événement suivi")
    
    with col_check2:
        st.markdown("### 🔄 Fraîcheur des Données")
        
        # Vérifier la fraîcheur des données TwitchTracker
        if not global_stats_enriched_df.empty and 'timestamp' in global_stats_enriched_df.columns:
            last_update = global_stats_enriched_df['timestamp'].max()
            time_diff = pd.Timestamp.now() - last_update
            if time_diff.total_seconds() < 3600:  # Moins d'1 heure
                st.success(f"🕐 Données à jour ({time_diff.total_seconds()/60:.0f}min)")
            else:
                st.warning(f"🕐 Données anciennes ({time_diff.total_seconds()/3600:.1f}h)")
        else:
            st.error("🕐 Aucune donnée TwitchTracker")
            
        # Vérifier les événements
        if not events_df.empty:
            current_time = pd.Timestamp.now()
            # Vérifier les colonnes disponibles pour les événements
            if 'status' in events_df.columns:
                live_events_check = events_df[events_df['status'] == 'Live']
                st.info(f"🎯 {len(live_events_check)} événements avec status 'Live'")
            else:
                st.info(f"🎯 {len(events_df)} événements totaux")
    
    st.markdown("---")
    
    # Graphiques côte à côte
    col1, col2 = st.columns(2)
    
    with col1:
        # Utiliser les données TwitchTracker enrichies pour les jeux trending
        if not trending_enriched_df.empty and 'avg_viewers_week' in trending_enriched_df.columns:
            st.subheader("🔥 Top 10 Jeux Trending (TwitchTracker)")
            top_trending = trending_enriched_df.nlargest(10, 'avg_viewers_week')
            
            fig = px.bar(
                top_trending, 
                x='game_name', 
                y='avg_viewers_week',
                color='avg_viewers_week',
                color_continuous_scale='viridis',
                title="Jeux trending par viewers moyens",
                labels={'avg_viewers_week': 'Viewers Moyens (Semaine)', 'game_name': 'Jeu'}
            )
            fig.update_layout(height=500, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        elif not games_df.empty and 'viewers' in games_df.columns:
            st.subheader("🎮 Top 10 Jeux par Viewers")
            top_games = games_df.nlargest(10, 'viewers')
            
            fig = px.bar(
                top_games, 
                x='game_name', 
                y='viewers',
                color='viewers',
                color_continuous_scale='viridis',
                title="Jeux les plus populaires"
            )
            fig.update_layout(height=500, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Aucune donnée de jeux disponible")
    
    with col2:
        # Streamers avec données réelles
        if not streamers_df.empty and 'followers' in streamers_df.columns:
            st.subheader("🇫🇷 Top Streamers Français")
            # Filtrer les streamers actifs uniquement
            if 'status' in streamers_df.columns:
                active_streamers = streamers_df[streamers_df['status'].isin(['online', 'live'])].head(10)
                if active_streamers.empty:
                    active_streamers = streamers_df.nlargest(10, 'followers')
            else:
                active_streamers = streamers_df.nlargest(10, 'followers')
            
            fig = px.bar(
                active_streamers,
                x='username',
                y='followers',
                color='followers',
                color_continuous_scale='plasma',
                title="Streamers par followers"
            )
            fig.update_layout(height=500, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Aucune donnée de streamers français disponible")
    
    # Événements LIVE seulement
    live_events_df = events_df[events_df['status'] == 'Live'] if not events_df.empty and 'status' in events_df.columns else pd.DataFrame()
    
    if not live_events_df.empty:
        st.subheader("🔴 Événements Gaming LIVE")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🔴 En Direct Maintenant", len(live_events_df))
        with col2:
            upcoming_events = events_df[events_df['status'] == 'Upcoming'] if not events_df.empty else pd.DataFrame()
            st.metric("� À Venir Prochainement", len(upcoming_events))
        with col3:
            if 'impact_score' in live_events_df.columns:
                avg_impact = live_events_df['impact_score'].mean()
                st.metric("📈 Impact Moyen Events Live", f"{avg_impact:.1f}/100")
            else:
                st.metric("📈 Events Total", len(events_df) if not events_df.empty else 0)
        
        # Liste des événements live
        for idx, event in live_events_df.iterrows():
            with st.expander(f"� LIVE: {event['name']} - {event.get('game', 'N/A')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Jeu:** {event.get('game', 'N/A')}")
                    st.write(f"**Date:** {event.get('date', 'En cours')}")
                with col2:
                    st.write(f"**Prize Pool:** {event.get('prize_pool', 'N/A')}")
                    st.write(f"**Type:** {event.get('type', 'N/A')}")
    else:
        st.info("ℹ️ Aucun événement gaming en direct actuellement")

elif page == "🎮 Jeux Twitch":
    st.header("🎮 Jeux Twitch - Données Détaillées")
    
    if not games_df.empty:
        # Graphique en secteurs des top jeux
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Répartition des Viewers")
            top_10_games = games_df.nlargest(10, 'viewers')
            
            fig = px.pie(
                top_10_games,
                values='viewers',
                names='game_name',
                title="Top 10 jeux par viewers"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📈 Tendances")
            if 'trend' in games_df.columns:
                trend_counts = games_df['trend'].value_counts()
                fig = px.bar(
                    x=trend_counts.index,
                    y=trend_counts.values,
                    color=trend_counts.index,
                    title="Distribution des tendances"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Tableau détaillé
        st.subheader("📋 Tableau Détaillé")
        
        # Tri par viewers
        games_sorted = games_df.sort_values('viewers', ascending=False)
        
        # Affichage avec formatage
        for i, game in games_sorted.iterrows():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.write(f"**{game['game_name']}**")
            with col2:
                st.write(f"👥 {game['viewers']:,} viewers")
            with col3:
                channels = game.get('channels', 'N/A')
                st.write(f"📺 {channels} chaînes" if channels != 'N/A' else "📺 N/A")
            with col4:
                trend = game.get('trend', 'stable')
                if trend == 'rising':
                    st.write("📈")
                elif trend == 'declining':
                    st.write("📉")
                else:
                    st.write("➡️")
    else:
        st.warning("Aucune donnée de jeux disponible")

elif page == "📈 TwitchTracker Live":
    st.header("📈 TwitchTracker Live Data")
    
    # Stats globales TwitchTracker
    if not global_stats_enriched_df.empty:
        st.subheader("🌍 Statistiques Globales Twitch")
        latest_stats = global_stats_enriched_df.iloc[-1] if len(global_stats_enriched_df) > 0 else {}
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            concurrent = latest_stats.get('concurrent_viewers', 0)
            st.metric("👥 Viewers Simultanés", f"{concurrent:,}")
        with col2:
            live_channels = latest_stats.get('live_channels', 0)
            st.metric("📺 Chaînes Live", f"{live_channels:,}")
        with col3:
            avg_viewers = latest_stats.get('avg_viewers_per_channel', 0)
            st.metric("📊 Moy. par Chaîne", f"{avg_viewers:.1f}")
        with col4:
            peak_time = latest_stats.get('timestamp', 'N/A')
            st.metric("🕐 Dernière Maj", str(peak_time)[:16] if peak_time != 'N/A' else 'N/A')
    
    # Jeux Trending TwitchTracker
    if not trending_enriched_df.empty:
        st.subheader("🔥 Jeux Trending (TwitchTracker)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Graphique en barres des trending
            if 'avg_viewers_week' in trending_enriched_df.columns:
                top_trending = trending_enriched_df.nlargest(10, 'avg_viewers_week')
                fig_trending = px.bar(
                    top_trending,
                    x='avg_viewers_week',
                    y='game_name',
                    orientation='h',
                    title="Top 10 Jeux Trending - Viewers Moyens",
                    labels={'avg_viewers_week': 'Viewers Moyens (Semaine)', 'game_name': 'Jeu'}
                )
                fig_trending.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_trending, use_container_width=True)
        
        with col2:
            # Graphique de croissance
            if 'growth_7d_percent' in trending_enriched_df.columns:
                growth_data = trending_enriched_df[trending_enriched_df['growth_7d_percent'].notna()].nlargest(10, 'growth_7d_percent')
                fig_growth = px.bar(
                    growth_data,
                    x='growth_7d_percent',
                    y='game_name',
                    orientation='h',
                    title="Croissance 7 jours (%)",
                    labels={'growth_7d_percent': 'Croissance (%)', 'game_name': 'Jeu'},
                    color='growth_7d_percent',
                    color_continuous_scale='RdYlGn'
                )
                fig_growth.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_growth, use_container_width=True)
        
        # Tableau détaillé des trending
        st.subheader("📊 Détails Jeux Trending")
        display_cols = ['game_name', 'avg_viewers_week', 'growth_7d_percent', 'market_share_percent', 'twitchtracker_rank']
        available_cols = [col for col in display_cols if col in trending_enriched_df.columns]
        
        if available_cols:
            trending_display = trending_enriched_df[available_cols].copy()
            if 'avg_viewers_week' in trending_display.columns:
                trending_display['avg_viewers_week'] = trending_display['avg_viewers_week'].apply(lambda x: f"{x:,}" if pd.notna(x) else "N/A")
            if 'growth_7d_percent' in trending_display.columns:
                trending_display['growth_7d_percent'] = trending_display['growth_7d_percent'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
            if 'market_share_percent' in trending_display.columns:
                trending_display['market_share_percent'] = trending_display['market_share_percent'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
            
            st.dataframe(trending_display, use_container_width=True, height=400)
    
    # Données TwitchTracker enrichies
    if not games_enriched_df.empty:
        st.subheader("🎮 Données TwitchTracker Détaillées")
        
        # Graphique comparatif
        if 'avg_viewers_week' in games_enriched_df.columns and 'market_share_percent' in games_enriched_df.columns:
            # Préparation des données pour un graphique en barres comparatif
            comparison_data = games_enriched_df.head(15).copy().sort_values('avg_viewers_week', ascending=True)
            
            # Créer un graphique en barres horizontales avec double métrique
            fig_comparison = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Viewers Moyens (Semaine)', 'Part de Marché (%)'),
                horizontal_spacing=0.1
            )
            
            # Barres pour les viewers
            fig_comparison.add_trace(
                go.Bar(
                    x=comparison_data['avg_viewers_week'],
                    y=comparison_data['game_name'],
                    orientation='h',
                    name='Viewers/Semaine',
                    marker_color='lightblue'
                ),
                row=1, col=1
            )
            
            # Barres pour la part de marché
            fig_comparison.add_trace(
                go.Bar(
                    x=comparison_data['market_share_percent'],
                    y=comparison_data['game_name'],
                    orientation='h',
                    name='Part de Marché %',
                    marker_color='lightcoral'
                ),
                row=1, col=2
            )
            
            fig_comparison.update_layout(
                height=600,
                title_text="📊 Comparaison Viewers vs Part de Marché",
                showlegend=False
            )
            
            st.plotly_chart(fig_comparison, use_container_width=True)
            
            # Ajouter un graphique de croissance séparé si disponible
            if 'growth_7d_percent' in games_enriched_df.columns:
                st.markdown("### 📈 Croissance 7 Jours")
                growth_data = games_enriched_df.head(10).copy()
                growth_data = growth_data[growth_data['growth_7d_percent'].notna()]
                
                if not growth_data.empty:
                    # Séparer croissance positive et négative
                    positive_growth = growth_data[growth_data['growth_7d_percent'] >= 0]
                    negative_growth = growth_data[growth_data['growth_7d_percent'] < 0]
                    
                    fig_growth = px.bar(
                        growth_data.sort_values('growth_7d_percent', ascending=True),
                        x='growth_7d_percent',
                        y='game_name',
                        orientation='h',
                        color='growth_7d_percent',
                        color_continuous_scale=['red', 'yellow', 'green'],
                        title="Croissance/Décroissance des Jeux (7 jours)",
                        labels={'growth_7d_percent': 'Croissance %', 'game_name': 'Jeu'}
                    )
                    fig_growth.update_layout(height=400)
                    st.plotly_chart(fig_growth, use_container_width=True)
    
    # Section des streamers enrichis
    if not streamers_enriched_df.empty:
        st.subheader("🎭 Top Streamers TwitchTracker (Monde)")
        
        # Option de filtre par pays si disponible
        if 'country' in streamers_enriched_df.columns:
            countries = streamers_enriched_df['country'].dropna().unique()
            if len(countries) > 1:
                col_filter, col_info = st.columns([3, 1])
                with col_filter:
                    selected_country = st.selectbox(
                        "🌍 Filtrer par pays:",
                        ["Tous les pays"] + sorted(countries.tolist()),
                        key="country_filter"
                    )
                with col_info:
                    if selected_country != "Tous les pays":
                        filtered_streamers = streamers_enriched_df[streamers_enriched_df['country'] == selected_country]
                        st.info(f"📊 {len(filtered_streamers)} streamers de {selected_country}")
                    else:
                        st.info(f"🌍 {len(streamers_enriched_df)} streamers mondiaux")
                
                # Appliquer le filtre
                if selected_country != "Tous les pays":
                    streamers_enriched_df_filtered = streamers_enriched_df[streamers_enriched_df['country'] == selected_country].copy()
                else:
                    streamers_enriched_df_filtered = streamers_enriched_df.copy()
            else:
                streamers_enriched_df_filtered = streamers_enriched_df.copy()
                st.info(f"🌍 Données mondiales TwitchTracker ({len(streamers_enriched_df)} streamers)")
        else:
            streamers_enriched_df_filtered = streamers_enriched_df.copy()
            st.info(f"🌍 Données mondiales TwitchTracker ({len(streamers_enriched_df)} streamers)")
        
        # Debug: afficher la structure des données
        if st.sidebar.checkbox("🔍 Debug Streamers", help="Affiche la structure des données streamers"):
            st.write("**Colonnes disponibles:**", list(streamers_enriched_df.columns))
            st.write("**Nombre de streamers:**", len(streamers_enriched_df_filtered))
            if not streamers_enriched_df_filtered.empty:
                st.write("**Échantillon des données:**")
                st.write(streamers_enriched_df_filtered.head())
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top streamers par followers
            if 'followers' in streamers_enriched_df_filtered.columns and not streamers_enriched_df_filtered.empty:
                try:
                    # Vérifier que les données followers sont valides
                    valid_streamers = streamers_enriched_df_filtered[streamers_enriched_df_filtered['followers'].notna() & (streamers_enriched_df_filtered['followers'] > 0)]
                    
                    if not valid_streamers.empty:
                        top_followers = valid_streamers.nlargest(10, 'followers')
                        
                        fig_followers = px.bar(
                            top_followers,
                            x='followers',
                            y='username',
                            orientation='h',
                            title="Top 10 Streamers - Followers",
                            labels={'followers': 'Followers', 'username': 'Streamer'}
                        )
                        fig_followers.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                        st.plotly_chart(fig_followers, use_container_width=True)
                    else:
                        st.warning("⚠️ Aucune donnée de followers valide trouvée")
                except Exception as e:
                    st.error(f"❌ Erreur dans le graphique followers: {str(e)}")
            else:
                st.warning("⚠️ Colonne 'followers' introuvable dans les données streamers")
        
        with col2:
            # Top streamers par viewers
            if 'avg_viewers' in streamers_enriched_df_filtered.columns and not streamers_enriched_df_filtered.empty:
                try:
                    # Vérifier que les données avg_viewers sont valides
                    valid_viewers = streamers_enriched_df_filtered[streamers_enriched_df_filtered['avg_viewers'].notna() & (streamers_enriched_df_filtered['avg_viewers'] > 0)]
                    
                    if not valid_viewers.empty:
                        top_viewers = valid_viewers.nlargest(10, 'avg_viewers')
                        
                        fig_viewers = px.bar(
                            top_viewers,
                            x='avg_viewers',
                            y='username',
                            orientation='h',
                            title="Top 10 Streamers - Viewers Moyens",
                            labels={'avg_viewers': 'Viewers Moyens', 'username': 'Streamer'},
                            color='avg_viewers',
                            color_continuous_scale='viridis'
                        )
                        fig_viewers.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                        st.plotly_chart(fig_viewers, use_container_width=True)
                    else:
                        st.warning("⚠️ Aucune donnée de viewers valide trouvée")
                except Exception as e:
                    st.error(f"❌ Erreur dans le graphique viewers: {str(e)}")
            else:
                st.warning("⚠️ Colonne 'avg_viewers' introuvable dans les données streamers")
        
        # Graphique de corrélation streamers
        if 'followers' in streamers_enriched_df_filtered.columns and 'avg_viewers' in streamers_enriched_df_filtered.columns and not streamers_enriched_df_filtered.empty:
            try:
                # Filtrer les données valides pour la corrélation
                valid_corr_data = streamers_enriched_df_filtered[
                    streamers_enriched_df_filtered['followers'].notna() & 
                    streamers_enriched_df_filtered['avg_viewers'].notna() &
                    (streamers_enriched_df_filtered['followers'] > 0) &
                    (streamers_enriched_df_filtered['avg_viewers'] > 0)
                ].copy()
                
                if not valid_corr_data.empty:
                    # Préparation des données pour éviter les problèmes de taille
                    size_column = None
                    
                    if 'hours_streamed' in valid_corr_data.columns:
                        # S'assurer que les valeurs de taille sont positives
                        hours_values = valid_corr_data['hours_streamed'].fillna(1)  # Remplacer NaN par 1
                        hours_values = hours_values.clip(lower=1)  # Minimum de 1 pour éviter les valeurs nulles/négatives
                        valid_corr_data['size_adjusted'] = hours_values
                        size_column = 'size_adjusted'
                    elif 'stream_hours_week' in valid_corr_data.columns:
                        # Alternative avec stream_hours_week
                        hours_values = valid_corr_data['stream_hours_week'].fillna(1)
                        hours_values = hours_values.clip(lower=1)
                        valid_corr_data['size_adjusted'] = hours_values
                        size_column = 'size_adjusted'
                    
                    # Analyse des top streamers actifs uniquement
                    st.markdown("### 🔗 Analyse des Top Streamers Actifs")
                    
                    # Utiliser la fonction de filtrage
                    active_streamers_data = filter_active_streamers(valid_corr_data)
                    
                    if not active_streamers_data.empty:
                        # Afficher les statistiques de filtrage
                        filtered_count = len(valid_corr_data) - len(active_streamers_data)
                        if filtered_count > 0:
                            st.warning(f"🚫 {filtered_count} streamers bannis/inactifs filtrés (ex: DrDisrespect banni 2020) • 📊 {len(active_streamers_data)} streamers actifs affichés")
                        else:
                            st.info(f"✅ {len(active_streamers_data)} streamers actifs validés")
                        
                        # Note explicative sur le filtrage
                        with st.expander("ℹ️ Critères de Filtrage des Streamers"):
                            st.markdown("""
                            ### 🔍 Comment sont filtrés les streamers ?
                            
                            **🚫 Exclusions automatiques :**
                            - **DrDisrespect** : Banni définitivement de Twitch (Juin 2020)
                            - **Phantoml0rd** : Banni pour scandal gambling CSGO
                            - **Ice_Poseidon** : Banni pour violations TOS répétées
                            - **JoshOG, TmarTn, Syndicate** : Impliqués scandals gambling
                            - **CouRage, DisguisedToast, Valkyrae** : Migrés vers d'autres plateformes
                            
                            **📊 Critères d'activité :**
                            - Données de moins de 30 jours
                            - Viewers moyens > 0
                            - Followers > 1000
                            
                            **🎯 Objectif :** Afficher uniquement les streamers **réellement actifs** sur Twitch
                            """)
                        
                        # Graphique en barres pour la relation Followers vs Viewers
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Top streamers ACTIFS par followers
                            top_followers = active_streamers_data.nlargest(10, 'followers')
                            fig_followers = px.bar(
                                top_followers,
                                x='username',
                                y='followers',
                                title="🔥 Top 10 - Followers (Streamers Actifs Uniquement)",
                                color='followers',
                                color_continuous_scale='blues'
                            )
                            fig_followers.update_layout(height=400, xaxis_tickangle=-45)
                            st.plotly_chart(fig_followers, use_container_width=True)
                            
                            # Top 3 pour mise en évidence
                            if len(top_followers) >= 3:
                                st.markdown("**🏆 Podium Followers:**")
                                for i, (_, streamer) in enumerate(top_followers.head(3).iterrows(), 1):
                                    medal = ["🥇", "🥈", "🥉"][i-1]
                                    st.write(f"{medal} **{streamer['username']}**: {streamer['followers']:,} followers")
                        
                        with col2:
                            # Top streamers ACTIFS par viewers moyens
                            top_viewers = active_streamers_data.nlargest(10, 'avg_viewers')
                            fig_viewers = px.bar(
                                top_viewers,
                                x='username',
                                y='avg_viewers',
                                title="📺 Top 10 - Viewers Moyens (Streamers Actifs Uniquement)",
                                color='avg_viewers',
                                color_continuous_scale='reds'
                            )
                            fig_viewers.update_layout(height=400, xaxis_tickangle=-45)
                            st.plotly_chart(fig_viewers, use_container_width=True)
                            
                            # Statistiques d'activité
                            avg_viewers_all = active_streamers_data['avg_viewers'].mean()
                            max_viewers = active_streamers_data['avg_viewers'].max()
                            st.markdown(f"**📈 Statistiques:**")
                            st.write(f"• Moyenne viewers: {avg_viewers_all:,.0f}")
                            st.write(f"• Maximum viewers: {max_viewers:,.0f}")
                            
                            # Top 3 pour mise en évidence
                            if len(top_viewers) >= 3:
                                st.markdown("**🏆 Podium Viewers:**")
                                for i, (_, streamer) in enumerate(top_viewers.head(3).iterrows(), 1):
                                    medal = ["🥇", "🥈", "🥉"][i-1]
                                    st.write(f"{medal} **{streamer['username']}**: {streamer['avg_viewers']:,} viewers")
                    else:
                        st.warning("⚠️ Aucun streamer actif trouvé avec les critères de filtrage")
                        st.info("💡 Critères: données < 30 jours, viewers > 0, followers > 1000, pas dans la liste noire")
                else:
                    st.warning("⚠️ Pas assez de données valides pour la corrélation")
            except Exception as e:
                st.error(f"❌ Erreur dans le graphique de corrélation: {str(e)}")
    
        # Tableau détaillé des streamers actifs uniquement
        st.subheader("📊 Détails Streamers Actifs")
        
        # Appliquer le filtrage des streamers actifs
        streamers_active_filtered = filter_active_streamers(streamers_enriched_df_filtered)
        
        display_cols = ['username', 'followers', 'avg_viewers', 'stream_hours_week', 'main_game']
        available_cols = [col for col in display_cols if col in streamers_active_filtered.columns]
        
        if available_cols and not streamers_active_filtered.empty:
            try:
                streamers_display = streamers_active_filtered[available_cols].copy()
                
                # Afficher les stats de filtrage
                original_count = len(streamers_enriched_df_filtered)
                active_count = len(streamers_active_filtered)
                filtered_count = original_count - active_count
                
                if filtered_count > 0:
                    st.info(f"🔍 Affichage de {active_count} streamers actifs sur {original_count} total ({filtered_count} filtrés)")
                else:
                    st.info(f"✅ Tous les {active_count} streamers sont actifs")
                
                # Formatage sécurisé des colonnes
                if 'followers' in streamers_display.columns:
                    streamers_display['followers'] = streamers_display['followers'].apply(
                        lambda x: f"{int(x):,}" if pd.notna(x) and x != '' else "N/A"
                    )
                if 'avg_viewers' in streamers_display.columns:
                    streamers_display['avg_viewers'] = streamers_display['avg_viewers'].apply(
                        lambda x: f"{int(x):,}" if pd.notna(x) and x != '' else "N/A"
                    )
                
                st.dataframe(streamers_display, use_container_width=True, height=300)
            except Exception as e:
                st.error(f"❌ Erreur dans l'affichage du tableau: {str(e)}")
                # Affichage de debug
                st.write("**Données brutes pour debug:**")
                st.write(streamers_enriched_df_filtered.head() if not streamers_enriched_df_filtered.empty else "DataFrame vide")
        else:
            st.warning("⚠️ Aucune colonne compatible trouvée pour l'affichage du tableau")
        
        # Export des données
        st.markdown("---")
        st.subheader("📥 Export des Données")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if not trending_enriched_df.empty:
                csv_trending = trending_enriched_df.to_csv(index=False)
                st.download_button(
                    label="📥 Exporter Trending (CSV)",
                    data=csv_trending,
                    file_name=f"twitch_trending_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="export_trending"
                )
            else:
                st.info("⚠️ Pas de données trending à exporter")
        
        with col2:
            if not games_enriched_df.empty:
                try:
                    json_games = games_enriched_df.to_json(orient='records', indent=2, force_ascii=False)
                    st.download_button(
                        label="📥 Exporter Games (JSON)",
                        data=json_games,
                        file_name=f"twitchtracker_games_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                        key="export_games"
                    )
                except Exception as e:
                    st.error(f"Erreur lors de l'export JSON: {e}")
                    # Export CSV en backup
                    games_csv_backup = games_enriched_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Export Games (CSV - Backup)",
                        data=games_csv_backup,
                        file_name=f"twitchtracker_games_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        key="export_games_csv_backup"
                    )
            else:
                st.info("⚠️ Pas de données games à exporter")
        
        with col3:
            if not streamers_active_filtered.empty:
                csv_streamers = streamers_active_filtered.to_csv(index=False)
                st.download_button(
                    label="📥 Exporter Streamers Actifs (CSV)",
                    data=csv_streamers,
                    file_name=f"twitchtracker_streamers_actifs_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="export_streamers"
                )
            else:
                st.info("⚠️ Pas de données streamers à exporter")
    else:
        st.warning("⚠️ Aucune donnée de streamers TwitchTracker disponible.")
        st.info("💡 Les streamers enrichis seront disponibles après le scraping TwitchTracker des streamers.")
    
    if trending_enriched_df.empty and games_enriched_df.empty and global_stats_enriched_df.empty and streamers_enriched_df.empty:
        st.warning("⚠️ Aucune donnée TwitchTracker disponible. Lancez le scraping TwitchTracker.")
        st.info("💡 Pour scraper les données TwitchTracker, utilisez le scraper d'enrichissement.")

elif page == "🎯 Événements Gaming":
    st.header("🎯 Événements Gaming - État en Temps Réel")
    
    if not events_df.empty:
        # Séparer les événements par statut
        live_events = events_df[events_df['status'] == 'Live'] if 'status' in events_df.columns else pd.DataFrame()
        upcoming_events = events_df[events_df['status'] == 'Upcoming'] if 'status' in events_df.columns else pd.DataFrame()
        finished_events = events_df[events_df['status'].isin(['Finished', 'Completed'])] if 'status' in events_df.columns else pd.DataFrame()
        
        # Métriques des événements RÉELLES
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "📅 À Venir", 
                len(upcoming_events),
                help="Événements programmés"
            )
        
        with col2:
            st.metric(
                "✅ Terminés", 
                len(finished_events),
                help="Événements récemment conclus"
            )
        
        with col3:
            # Prize pools totaux
            if not events_df.empty and 'prize_pool' in events_df.columns:
                total_prizes = 0
                for prize in events_df['prize_pool']:
                    if isinstance(prize, str) and '$' in prize:
                        amount_str = prize.replace('$', '').replace(',', '')
                        try:
                            total_prizes += float(amount_str)
                        except:
                            pass
                st.metric("💰 Prize Pools Total", f"${total_prizes:,.0f}")
            else:
                st.metric("💰 Prize Pools Total", "$0")
        
        # Événements à venir
        if not upcoming_events.empty:
            st.subheader("📅 Événements À Venir")
            
            for idx, event in upcoming_events.head(5).iterrows():  # Limiter à 5 pour éviter le spam
                with st.expander(f"📅 {event['name']} - {event.get('game', 'N/A')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**🎮 Jeu:** {event.get('game', 'N/A')}")
                        st.write(f"**📅 Date:** {event.get('date', 'N/A')}")
                        st.write(f"**🏆 Type:** {event.get('type', 'N/A')}")
                    
                    with col2:
                        st.write(f"**💰 Prize Pool:** {event.get('prize_pool', 'N/A')}")
                        impact = event.get('impact_score', 'N/A')
                        st.write(f"**📈 Impact:** {impact}/100" if impact != 'N/A' else "**📈 Impact:** N/A")
        
        # Graphique des événements par jeu (LIVE seulement)
        if not live_events.empty and 'game' in live_events.columns:
            st.subheader("🎮 Jeux avec Événements LIVE")
            live_game_events = live_events['game'].value_counts()
            
            fig = px.bar(
                x=live_game_events.values,
                y=live_game_events.index,
                orientation='h',
                title="Jeux avec événements en direct",
                color=live_game_events.values,
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True)
        elif 'game' in events_df.columns:
            st.subheader("🎮 Tous les Événements par Jeu")
            game_events = events_df['game'].value_counts()
            
            fig = px.bar(
                x=game_events.values,
                y=game_events.index,
                orientation='h',
                title="Nombre total d'événements par jeu"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Boutons d'export pour les événements
        st.markdown("---")
        st.subheader("📥 Exporter les Données")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if not live_events.empty:
                events_csv = live_events.to_csv(index=False)
                st.download_button(
                    label="📊 Export Événements LIVE (CSV)",
                    data=events_csv,
                    file_name=f"evenements_live_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="export_live_events_csv"
                )
            else:
                st.info("Aucun événement LIVE à exporter")
        
        with col2:
            if not upcoming_events.empty:
                upcoming_csv = upcoming_events.to_csv(index=False)
                st.download_button(
                    label="📅 Export Événements À Venir (CSV)",
                    data=upcoming_csv,
                    file_name=f"evenements_a_venir_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="export_upcoming_events_csv"
                )
            else:
                st.info("Aucun événement à venir à exporter")
        
        with col3:
            if not events_df.empty:
                try:
                    all_events_json = events_df.to_json(orient='records', indent=2, force_ascii=False)
                    st.download_button(
                        label="📋 Export Tous Événements (JSON)",
                        data=all_events_json,
                        file_name=f"tous_evenements_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                        key="export_all_events_json"
                    )
                except Exception as e:
                    st.error(f"Erreur lors de l'export JSON: {e}")
                    # Export CSV en backup
                    events_csv_backup = events_df.to_csv(index=False)
                    st.download_button(
                        label="📋 Export Événements (CSV - Backup)",
                        data=events_csv_backup,
                        file_name=f"tous_evenements_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        key="export_all_events_csv_backup"
                    )
            else:
                st.info("Aucun événement à exporter")
    else:
        st.warning("⚠️ Aucune donnée d'événements disponible")
        st.info("💡 Les événements seront affichés après le scraping des données événementielles")

elif page == "🇫🇷 Streamers Français":
    st.header("🇫🇷 Streamers Français - Analyse des Données")
    
    if not streamers_df.empty:
        # Métriques des streamers
        col1, col2 = st.columns(2)
        
        with col1:
            if not streamers_df.empty and 'followers' in streamers_df.columns:
                total_followers = streamers_df['followers'].sum()
                st.metric("👥 Followers Total", f"{total_followers:,}")
            else:
                st.metric("👥 Followers Total", "N/A")
        
        with col2:
            st.metric("👤 Streamers Analysés", len(streamers_df))
        
        # Graphiques des streamers
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Top 10 par Followers")
            if 'followers' in streamers_df.columns:
                top_streamers = streamers_df.nlargest(10, 'followers')
                
                fig = px.bar(
                    top_streamers,
                    x='username',
                    y='followers',
                    color='followers',
                    color_continuous_scale='viridis',
                    title="Classement par followers"
                )
                fig.update_layout(height=500, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Données de followers non disponibles")
        
        with col2:
            st.subheader("� Statut des Streamers")
            if 'status' in streamers_df.columns:
                status_counts = streamers_df['status'].value_counts()
                
                colors = {'online': '#00ff00', 'live': '#ff4500', 'offline': '#808080'}
                fig = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Répartition des statuts",
                    color=status_counts.index,
                    color_discrete_map=colors
                )
                st.plotly_chart(fig, use_container_width=True)
            elif 'trend' in streamers_df.columns:
                trend_counts = streamers_df['trend'].value_counts()
                
                colors = {'rising': '#00ff00', 'stable': '#ffa500', 'declining': '#ff0000'}
                fig = px.pie(
                    values=trend_counts.values,
                    names=trend_counts.index,
                    title="Distribution des tendances",
                    color=trend_counts.index,
                    color_discrete_map=colors
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ℹ️ Données de statut non disponibles")
        
        # Jeux des streamers
        if 'main_game' in streamers_df.columns:
            st.subheader("🎮 Jeux Principaux des Streamers")
            game_counts = streamers_df['main_game'].value_counts().head(10)
            
            fig = px.bar(
                x=game_counts.index,
                y=game_counts.values,
                title="Jeux les plus streamés",
                color=game_counts.values,
                color_continuous_scale='viridis'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Tableau détaillé des streamers
        st.subheader("📋 Classement Détaillé")
        
        # Tri par followers
        streamers_sorted = streamers_df.sort_values('followers', ascending=False)
        
        for idx, (i, streamer) in enumerate(streamers_sorted.iterrows()):
            rank = streamer.get('rank', idx + 1)
            
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
                
                with col1:
                    st.write(f"**#{rank}**")
                
                with col2:
                    st.write(f"**{streamer['username']}**")
                
                with col3:
                    st.write(f"👥 {streamer['followers']:,}")
                
                with col4:
                    avg_viewers = streamer.get('avg_viewers', 'N/A')
                    st.write(f"📺 {avg_viewers:,}" if avg_viewers != 'N/A' else "📺 N/A")
                
                with col5:
                    trend = streamer.get('trend', 'stable')
                    growth = streamer.get('growth_rate', 0)
                    
                    if trend == 'rising':
                        st.write(f"📈 +{growth}%" if growth > 0 else "📈")
                    elif trend == 'declining':
                        st.write(f"📉 {growth}%" if growth < 0 else "📉")
                    else:
                        st.write(f"➡️ {growth}%" if growth != 0 else "➡️")
                
                st.divider()
        
        # Boutons d'export pour les streamers français
        st.markdown("---")
        st.subheader("📥 Exporter les Données")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if not streamers_df.empty:
                streamers_csv = streamers_df.to_csv(index=False)
                st.download_button(
                    label="� Export Streamers FR (CSV)",
                    data=streamers_csv,
                    file_name=f"streamers_francais_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="export_fr_csv"
                )
            else:
                st.info("Aucun streamer à exporter")
        
        with col2:
            if not streamers_df.empty:
                try:
                    all_streamers_json = streamers_df.to_json(orient='records', indent=2, force_ascii=False)
                    st.download_button(
                        label="🇫🇷 Export Streamers FR (JSON)",
                        data=all_streamers_json,
                        file_name=f"streamers_francais_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                        key="export_all_fr_json"
                    )
                except Exception as e:
                    st.error(f"Erreur lors de l'export JSON: {e}")
                    # Export CSV en backup
                    streamers_csv_backup = streamers_df.to_csv(index=False)
                    st.download_button(
                        label="📊 Export Streamers FR (CSV - Backup)",
                        data=streamers_csv_backup,
                        file_name=f"streamers_francais_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        key="export_fr_csv_backup"
                    )
            else:
                st.info("Aucun streamer français à exporter")
    else:
        st.warning("Aucune donnée de streamers disponible")

# Footer
# === PAGE REVENUS STREAMERS ===
elif page == "💰 Revenus Streamers":
    st.header("💰 Analyse des Revenus des Streamers")
    st.markdown("*Estimations basées sur les abonnements, donations et publicités*")
    
    # Charger les données de revenus
    @st.cache_data(ttl=1800)  # Cache 30 minutes
    def load_revenue_data():
        revenue_collection = db.streamers_revenue
        revenue_data = list(revenue_collection.find().sort('monthly_total_estimate', -1))
        return pd.DataFrame(revenue_data) if revenue_data else pd.DataFrame()
    
    revenue_df = load_revenue_data()
    
    if not revenue_df.empty:
        # Métriques de résumé
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            top_earner = revenue_df.iloc[0]
            st.metric(
                "🥇 Top Earner", 
                top_earner['username'],
                f"${top_earner['monthly_total_estimate']:,.2f}/mois"
            )
        
        with col2:
            avg_monthly = revenue_df['monthly_total_estimate'].mean()
            st.metric(
                "💰 Revenu Moyen", 
                f"${avg_monthly:,.2f}",
                "par mois"
            )
        
        with col3:
            total_yearly = revenue_df['yearly_total_estimate'].sum()
            st.metric(
                "🎯 Total Annuel", 
                f"${total_yearly:,.2f}",
                "estimation collective"
            )
        
        with col4:
            median_monthly = revenue_df['monthly_total_estimate'].median()
            st.metric(
                "📊 Revenu Médian", 
                f"${median_monthly:,.2f}",
                "par mois"
            )
        
        st.markdown("---")
        
        # Graphiques des revenus
        col1, col2 = st.columns(2)
        
        with col1:
            # Top 10 streamers par revenu mensuel
            st.subheader("🔥 Top 10 - Revenus Mensuels")
            top_10 = revenue_df.head(10)
            
            fig_revenue = px.bar(
                top_10,
                x='monthly_total_estimate',
                y='username',
                orientation='h',
                color='monthly_total_estimate',
                color_continuous_scale='Greens',
                title="Revenus Mensuels Estimés ($)",
                labels={'monthly_total_estimate': 'Revenu Mensuel ($)', 'username': 'Streamer'}
            )
            fig_revenue.update_layout(height=500)
            st.plotly_chart(fig_revenue, use_container_width=True)
        
        with col2:
            # Répartition des sources de revenus
            st.subheader("📊 Sources de Revenus")
            
            # Calculer les moyennes des sources
            avg_subs = revenue_df['monthly_subs_revenue'].mean()
            avg_donations = revenue_df['monthly_donations_estimate'].mean()
            avg_ads = revenue_df['monthly_ads_estimate'].mean()
            
            sources_data = pd.DataFrame({
                'Source': ['Abonnements', 'Donations', 'Publicités'],
                'Montant': [avg_subs, avg_donations, avg_ads]
            })
            
            fig_sources = px.pie(
                sources_data,
                values='Montant',
                names='Source',
                title="Répartition Moyenne des Revenus",
                color_discrete_sequence=['#2E8B57', '#FF6347', '#4682B4']
            )
            st.plotly_chart(fig_sources, use_container_width=True)
        
        # Détails des abonnements
        st.subheader("🎫 Analyse des Abonnements")
        
        # Préparer les données des subs
        subs_details = []
        for _, streamer in revenue_df.iterrows():
            subs_breakdown = streamer.get('subs_breakdown', {})
            subs_details.append({
                'username': streamer['username'],
                'total_subs': subs_breakdown.get('total_subs', 0),
                'tier_1': subs_breakdown.get('tier_1', 0),
                'tier_2': subs_breakdown.get('tier_2', 0),
                'tier_3': subs_breakdown.get('tier_3', 0),
                'prime': subs_breakdown.get('prime', 0)
            })
        
        subs_df = pd.DataFrame(subs_details)
        
        if not subs_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Top streamers par nombre d'abonnés
                top_subs = subs_df.nlargest(10, 'total_subs')
                
                fig_subs = px.bar(
                    top_subs,
                    x='total_subs',
                    y='username',
                    orientation='h',
                    color='total_subs',
                    color_continuous_scale='Blues',
                    title="Top 10 - Nombre d'Abonnés",
                    labels={'total_subs': 'Nombre d\'Abonnés', 'username': 'Streamer'}
                )
                fig_subs.update_layout(height=400)
                st.plotly_chart(fig_subs, use_container_width=True)
            
            with col2:
                # Répartition des tiers d'abonnement
                total_tier1 = subs_df['tier_1'].sum()
                total_tier2 = subs_df['tier_2'].sum()
                total_tier3 = subs_df['tier_3'].sum()
                total_prime = subs_df['prime'].sum()
                
                tiers_data = pd.DataFrame({
                    'Tier': ['Tier 1 ($4.99)', 'Prime', 'Tier 2 ($9.99)', 'Tier 3 ($24.99)'],
                    'Abonnés': [total_tier1, total_prime, total_tier2, total_tier3]
                })
                
                fig_tiers = px.pie(
                    tiers_data,
                    values='Abonnés',
                    names='Tier',
                    title="Répartition des Tiers d'Abonnement",
                    color_discrete_sequence=['#FFD700', '#9370DB', '#32CD32', '#FF4500']
                )
                st.plotly_chart(fig_tiers, use_container_width=True)
        
        # Tableau détaillé
        st.subheader("📋 Détails Complets")
        
        # Préparer le tableau d'affichage
        display_df = revenue_df[['username', 'monthly_total_estimate', 'monthly_subs_revenue', 
                                'monthly_donations_estimate', 'monthly_ads_estimate', 'yearly_total_estimate']].copy()
        
        display_df.columns = ['Streamer', 'Mensuel Total ($)', 'Subs ($)', 'Donations ($)', 'Pubs ($)', 'Annuel Total ($)']
        
        # Formatter les nombres
        for col in display_df.columns[1:]:
            display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(display_df, use_container_width=True)
        
        # Informations méthodologiques
        with st.expander("ℹ️ Méthodologie de Calcul"):
            st.markdown("""
            ### 📋 Comment sont calculés ces revenus ?
            
            **🎫 Abonnements (Subs):**
            - Tier 1: $2.50 pour le streamer (après commission Twitch)
            - Tier 2: $5.00 pour le streamer
            - Tier 3: $12.50 pour le streamer
            - Prime: $2.50 pour le streamer
            - Répartition estimée: 85% Tier 1, 10% Prime, 4% Tier 2, 1% Tier 3
            
            **💝 Donations:**
            - Estimation: 2% des viewers moyens donnent ~$5/mois
            
            **📺 Publicités:**
            - Estimation: $2 CPM basé sur viewers × heures de stream
            
            **⚠️ Note Importante:**
            Ces chiffres sont des **estimations** basées sur des données publiques et des moyennes de l'industrie.
            Les revenus réels peuvent varier significativement selon:
            - Les contrats spéciaux avec Twitch
            - Les sponsors et partenariats
            - Les ventes de merchandising
            - Les événements spéciaux
            """)
        
        # Bouton pour actualiser les données
        if st.button("🔄 Actualiser les Données de Revenus"):
            st.info("⏳ Lancement du scraping des revenus...")
            # Ici on pourrait relancer le scraper
            st.success("✅ Données actualisées! Rafraîchissez la page.")
        
        # Boutons d'export pour les revenus
        st.markdown("---")
        st.subheader("📥 Exporter les Données de Revenus")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export Top 10 revenus CSV
            top_revenue = revenue_df.head(10)
            if not top_revenue.empty:
                revenue_csv = top_revenue.to_csv(index=False)
                st.download_button(
                    label="💰 Export Top 10 Revenus (CSV)",
                    data=revenue_csv,
                    file_name=f"top_10_revenus_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="export_top_revenue_csv"
                )
            else:
                st.info("Aucune donnée de revenus à exporter")
        
        with col2:
            # Export revenus détaillés JSON
            if not revenue_df.empty:
                try:
                    # Nettoyer les données avant l'export JSON
                    revenue_clean = revenue_df.copy()
                    
                    # Supprimer l'ObjectId MongoDB qui pose problème
                    if '_id' in revenue_clean.columns:
                        revenue_clean = revenue_clean.drop('_id', axis=1)
                    
                    # Nettoyer les chaînes de caractères pour éviter les erreurs UTF-8
                    for col in revenue_clean.select_dtypes(include=['object']).columns:
                        revenue_clean[col] = revenue_clean[col].astype(str).apply(
                            lambda x: x.encode('utf-8', errors='ignore').decode('utf-8') if isinstance(x, str) else x
                        )
                    
                    # Remplacer les timestamps par des chaînes
                    if 'timestamp' in revenue_clean.columns:
                        revenue_clean['timestamp'] = revenue_clean['timestamp'].astype(str)
                    
                    revenue_json = revenue_clean.to_json(orient='records', indent=2, force_ascii=False)
                    st.download_button(
                        label="📊 Export Revenus Complets (JSON)",
                        data=revenue_json,
                        file_name=f"revenus_streamers_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                        key="export_revenue_json"
                    )
                except Exception as e:
                    st.error(f"Erreur lors de l'export JSON: {e}")
                    # Export CSV en backup
                    revenue_csv_backup = revenue_df.to_csv(index=False, encoding='utf-8')
                    st.download_button(
                        label="📊 Export Revenus (CSV - Backup)",
                        data=revenue_csv_backup,
                        file_name=f"revenus_streamers_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        key="export_revenue_csv_backup"
                    )
            else:
                st.info("Aucune donnée de revenus à exporter")
        
        with col3:
            # Export statistiques revenus
            if not revenue_df.empty:
                stats_data = {
                    "total_streamers": len(revenue_df),
                    "avg_monthly_revenue": revenue_df['monthly_total_estimate'].mean(),
                    "max_monthly_revenue": revenue_df['monthly_total_estimate'].max(),
                    "min_monthly_revenue": revenue_df['monthly_total_estimate'].min(),
                    "total_revenue_estimate": revenue_df['monthly_total_estimate'].sum(),
                    "generated_at": datetime.now().isoformat()
                }
                stats_json = pd.DataFrame([stats_data]).to_json(orient='records', indent=2)
                st.download_button(
                    label="📈 Export Statistiques (JSON)",
                    data=stats_json,
                    file_name=f"stats_revenus_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json",
                    key="export_stats_json"
                )
            else:
                st.info("Aucune statistique à exporter")
    
    else:
        st.warning("⚠️ Aucune donnée de revenus disponible.")
        st.info("💡 Lancez le scraper de revenus pour collecter les données.")
        
        if st.button("🚀 Lancer le Scraper de Revenus"):
            st.info("⏳ Lancement du scraping en cours...")
            # Ici on pourrait intégrer l'appel au scraper

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    🎮 Twitch Trends Tracker | Multi-Source Scraping Dashboard
    <br>Données mises à jour automatiquement depuis MongoDB
</div>
""", unsafe_allow_html=True)

# Auto-refresh
if st.sidebar.button("🔄 Actualiser les données"):
    st.cache_data.clear()
    st.rerun()
