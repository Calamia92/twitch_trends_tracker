import streamlit as st
import pymongo
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Configuration de la page
st.set_page_config(
    page_title="🎮 Twitch Trends Tracker",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Chargement des données
games_df = load_games_data()
events_df = load_events_data()
streamers_df = load_streamers_data()

# Sidebar pour navigation
st.sidebar.title("🎯 Navigation")
page = st.sidebar.selectbox(
    "Choisir une vue",
    ["📊 Vue d'ensemble", "🎮 Jeux Twitch", "🎯 Événements Gaming", "🇫🇷 Streamers Français"]
)

# Métriques principales
if not games_df.empty or not events_df.empty or not streamers_df.empty:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_viewers = games_df['viewers'].sum() if not games_df.empty else 0
        st.metric("👥 Viewers Totaux", f"{total_viewers:,}")
    
    with col2:
        total_games = len(games_df) if not games_df.empty else 0
        st.metric("🎮 Jeux Suivis", total_games)
    
    with col3:
        total_events = len(events_df) if not events_df.empty else 0
        st.metric("🎯 Événements", total_events)
    
    with col4:
        total_streamers = len(streamers_df) if not streamers_df.empty else 0
        st.metric("🇫🇷 Streamers FR", total_streamers)

# Affichage selon la page sélectionnée
if page == "📊 Vue d'ensemble":
    st.header("📊 Vue d'ensemble")
    
    # Graphiques côte à côte
    col1, col2 = st.columns(2)
    
    with col1:
        if not games_df.empty:
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
    
    with col2:
        if not streamers_df.empty:
            st.subheader("🇫🇷 Top Streamers Français")
            top_streamers = streamers_df.nlargest(10, 'followers')
            
            fig = px.bar(
                top_streamers,
                x='username',
                y='followers',
                color='followers',
                color_continuous_scale='plasma',
                title="Streamers par followers"
            )
            fig.update_layout(height=500, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
    
    # Événements en cours
    if not events_df.empty:
        st.subheader("🎯 Événements Gaming")
        
        col1, col2, col3 = st.columns(3)
        live_events = events_df[events_df['status'] == 'Live']
        upcoming_events = events_df[events_df['status'] == 'Upcoming']
        
        with col1:
            st.metric("🔴 En Direct", len(live_events))
        with col2:
            st.metric("📅 À Venir", len(upcoming_events))
        with col3:
            avg_impact = events_df['impact_score'].mean() if 'impact_score' in events_df.columns else 0
            st.metric("📈 Impact Moyen", f"{avg_impact:.1f}/100")

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

elif page == "🎯 Événements Gaming":
    st.header("🎯 Événements Gaming")
    
    if not events_df.empty:
        # Métriques des événements
        col1, col2, col3 = st.columns(3)
        
        with col1:
            live_count = len(events_df[events_df['status'] == 'Live'])
            st.metric("🔴 Événements Live", live_count)
        
        with col2:
            upcoming_count = len(events_df[events_df['status'] == 'Upcoming'])
            st.metric("📅 Événements À Venir", upcoming_count)
        
        with col3:
            if 'prize_pool' in events_df.columns:
                # Extraction des montants des prize pools
                total_prizes = 0
                for prize in events_df['prize_pool']:
                    if isinstance(prize, str) and '$' in prize:
                        amount_str = prize.replace('$', '').replace(',', '')
                        try:
                            total_prizes += float(amount_str)
                        except:
                            pass
                st.metric("💰 Prize Pools Total", f"${total_prizes:,.0f}")
        
        # Graphique des événements par jeu
        if 'game' in events_df.columns:
            st.subheader("🎮 Événements par Jeu")
            game_events = events_df['game'].value_counts()
            
            fig = px.bar(
                x=game_events.values,
                y=game_events.index,
                orientation='h',
                title="Nombre d'événements par jeu"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Liste détaillée des événements
        st.subheader("📋 Liste des Événements")
        
        for i, event in events_df.iterrows():
            with st.expander(f"{event['name']} - {event.get('game', 'N/A')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Jeu:** {event.get('game', 'N/A')}")
                    st.write(f"**Date:** {event.get('date', 'N/A')}")
                    st.write(f"**Type:** {event.get('type', 'N/A')}")
                
                with col2:
                    status = event.get('status', 'N/A')
                    status_emoji = "🔴" if status == "Live" else "📅" if status == "Upcoming" else "✅"
                    st.write(f"**Statut:** {status_emoji} {status}")
                    
                    prize = event.get('prize_pool', 'N/A')
                    st.write(f"**Prize Pool:** {prize}")
                    
                    impact = event.get('impact_score', 'N/A')
                    st.write(f"**Score d'Impact:** {impact}/100" if impact != 'N/A' else "**Score d'Impact:** N/A")
    else:
        st.warning("Aucune donnée d'événements disponible")

elif page == "🇫🇷 Streamers Français":
    st.header("🇫🇷 Streamers Français")
    
    if not streamers_df.empty:
        # Graphiques des streamers
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Top 10 par Followers")
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
        
        with col2:
            st.subheader("📈 Tendances des Streamers")
            if 'trend' in streamers_df.columns:
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
        
        # Jeux principaux des streamers
        if 'main_game' in streamers_df.columns:
            st.subheader("🎮 Jeux Principaux des Streamers")
            game_counts = streamers_df['main_game'].value_counts()
            
            fig = px.bar(
                x=game_counts.index,
                y=game_counts.values,
                title="Jeux les plus streamés"
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Tableau détaillé des streamers
        st.subheader("📋 Classement Détaillé")
        
        # Tri par followers
        streamers_sorted = streamers_df.sort_values('followers', ascending=False)
        
        for i, streamer in streamers_sorted.iterrows():
            rank = streamer.get('rank', i+1)
            
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
    else:
        st.warning("Aucune donnée de streamers disponible")

# Footer
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
