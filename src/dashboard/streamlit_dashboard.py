"""
Module dashboard Streamlit - Version refactorisée et modulaire.

Dashboard interactif pour visualiser les données de Twitch Trends
avec architecture modulaire et fonctionnalités avancées.

Auteurs: Hicham, Aya, Boubaker
Date: Juillet 2025
"""

import sys
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd

# Ajout du path pour les imports relatifs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import altair as alt
import plotly.express as px
import plotly.graph_objects as go

from config.settings import config
from src.database.mongodb_manager import db_manager
from src.utils.data_utils import formatter

# Configuration du logging
logging.basicConfig(level=getattr(logging, config.logging.LOG_LEVEL))
logger = logging.getLogger(__name__)


class TwitchDashboard:
    """
    Dashboard principal pour la visualisation des données Twitch.
    
    Cette classe fournit une interface Streamlit modulaire et interactive
    pour explorer les données scrapées.
    """
    
    def __init__(self):
        """Initialise le dashboard."""
        self.setup_page_config()
        logger.info("🎮 Dashboard Twitch initialisé")
    
    def setup_page_config(self):
        """Configure la page Streamlit."""
        st.set_page_config(
            page_title=config.dashboard.APP_TITLE,
            page_icon="🎮",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # CSS personnalisé pour le thème Twitch
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #9146ff 0%, #6441a5 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-container {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #9146ff;
        }
        .game-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)
    
    @st.cache_data(ttl=config.dashboard.CACHE_TTL)
    def load_data(_self) -> pd.DataFrame:
        """
        Charge les données depuis MongoDB avec cache.
        
        Returns:
            pd.DataFrame: Données des jeux
        """
        try:
            logger.info("📊 Chargement des données depuis MongoDB")
            
            if not db_manager.is_connected():
                st.error("❌ Connexion à la base de données impossible")
                return pd.DataFrame()
            
            # Récupération des données
            games_data = db_manager.get_all_games()
            
            if not games_data:
                st.warning("⚠️ Aucune donnée trouvée dans la base")
                return pd.DataFrame()
            
            # Conversion en DataFrame
            df = pd.DataFrame(games_data)
            
            # Nettoyage et préparation des données
            if 'scraped_at' in df.columns:
                df['scraped_at'] = pd.to_datetime(df['scraped_at'], errors='coerce')
            
            if 'viewers' in df.columns:
                df['viewers'] = pd.to_numeric(df['viewers'], errors='coerce').fillna(0)
            
            if 'change' in df.columns:
                df['change'] = pd.to_numeric(df['change'], errors='coerce')
            
            logger.info(f"✅ {len(df)} jeux chargés")
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement données: {e}")
            st.error(f"Erreur de chargement: {e}")
            return pd.DataFrame()
    
    def render_header(self):
        """Affiche l'en-tête du dashboard."""
        st.markdown("""
        <div class="main-header">
            <h1>🎮 Twitch Trends Tracker</h1>
            <p>Dashboard interactif des jeux les plus streamés sur Twitch</p>
            <p><em>Créé par Hicham, Aya et Boubaker</em></p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar_filters(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Affiche les filtres dans la sidebar.
        
        Args:
            df: DataFrame des données
            
        Returns:
            Dict: Filtres sélectionnés
        """
        st.sidebar.header("🔧 Filtres")
        
        filters = {}
        
        if not df.empty:
            # Filtre par nombre minimum de viewers
            min_viewers = st.sidebar.slider(
                "👥 Viewers minimum",
                min_value=0,
                max_value=int(df['viewers'].max()) if 'viewers' in df.columns else 100000,
                value=0,
                step=1000
            )
            filters['min_viewers'] = min_viewers
            
            # Filtre par jeu (multiselect)
            if 'title' in df.columns:
                unique_games = df['title'].unique()
                selected_games = st.sidebar.multiselect(
                    "🎮 Jeux spécifiques",
                    options=sorted(unique_games),
                    default=[]
                )
                filters['selected_games'] = selected_games
            
            # Filtre par date
            if 'scraped_at' in df.columns and not df['scraped_at'].isna().all():
                date_range = st.sidebar.date_input(
                    "📅 Période",
                    value=(
                        df['scraped_at'].min().date(),
                        df['scraped_at'].max().date()
                    ),
                    min_value=df['scraped_at'].min().date(),
                    max_value=df['scraped_at'].max().date()
                )
                filters['date_range'] = date_range
        
        return filters
    
    def apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Applique les filtres aux données.
        
        Args:
            df: DataFrame original
            filters: Filtres à appliquer
            
        Returns:
            pd.DataFrame: DataFrame filtré
        """
        filtered_df = df.copy()
        
        # Filtre viewers minimum
        if 'min_viewers' in filters:
            filtered_df = filtered_df[filtered_df['viewers'] >= filters['min_viewers']]
        
        # Filtre jeux sélectionnés
        if 'selected_games' in filters and filters['selected_games']:
            filtered_df = filtered_df[filtered_df['title'].isin(filters['selected_games'])]
        
        # Filtre par date
        if 'date_range' in filters and len(filters['date_range']) == 2:
            start_date, end_date = filters['date_range']
            filtered_df = filtered_df[
                (filtered_df['scraped_at'].dt.date >= start_date) &
                (filtered_df['scraped_at'].dt.date <= end_date)
            ]
        
        return filtered_df
    
    def render_metrics(self, df: pd.DataFrame):
        """
        Affiche les métriques principales.
        
        Args:
            df: DataFrame des données
        """
        if df.empty:
            st.warning("⚠️ Aucune donnée pour calculer les métriques")
            return
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_games = len(df)
            st.metric(
                label="🎮 Total Jeux",
                value=total_games,
                help="Nombre total de jeux dans les données"
            )
        
        with col2:
            if 'viewers' in df.columns:
                total_viewers = df['viewers'].sum()
                st.metric(
                    label="👥 Total Viewers",
                    value=formatter.format_number(total_viewers),
                    help="Nombre total de viewers sur Twitch"
                )
        
        with col3:
            if 'viewers' in df.columns:
                avg_viewers = df['viewers'].mean()
                st.metric(
                    label="📊 Moyenne Viewers",
                    value=formatter.format_number(int(avg_viewers)),
                    help="Nombre moyen de viewers par jeu"
                )
        
        with col4:
            if 'change' in df.columns:
                avg_change = df['change'].mean()
                change_str = formatter.format_percentage(avg_change) if pd.notna(avg_change) else "N/A"
                st.metric(
                    label="📈 Tendance Moyenne",
                    value=change_str,
                    help="Évolution moyenne des viewers"
                )
    
    def render_top_games_chart(self, df: pd.DataFrame):
        """
        Affiche le graphique des top jeux.
        
        Args:
            df: DataFrame des données
        """
        st.subheader("🏆 Top Jeux par Viewers")
        
        if df.empty:
            st.info("Aucune donnée à afficher")
            return
        
        # Limitation pour la lisibilité
        top_games = df.nlargest(min(20, len(df)), 'viewers')
        
        # Graphique Altair
        chart = alt.Chart(top_games).mark_bar(
            color='#9146ff',
            cornerRadiusTopLeft=3,
            cornerRadiusTopRight=3
        ).add_selection(
            alt.selection_single()
        ).encode(
            x=alt.X('viewers:Q', title='Nombre de Viewers'),
            y=alt.Y('title:N', sort='-x', title='Jeux'),
            tooltip=['title:N', 'viewers:Q', 'change:Q'],
            color=alt.condition(
                alt.datum.change > 0,
                alt.value('#00ff7f'),  # Vert pour positif
                alt.value('#ff6b6b')   # Rouge pour négatif
            )
        ).properties(
            height=500
        )
        
        st.altair_chart(chart, use_container_width=True)
    
    def render_viewers_distribution(self, df: pd.DataFrame):
        """
        Affiche la distribution des viewers.
        
        Args:
            df: DataFrame des données
        """
        st.subheader("📊 Distribution des Viewers")
        
        if df.empty or 'viewers' not in df.columns:
            st.info("Aucune donnée de viewers disponible")
            return
        
        # Histogramme avec Plotly
        fig = px.histogram(
            df,
            x='viewers',
            nbins=30,
            title="Distribution du nombre de viewers",
            color_discrete_sequence=['#9146ff']
        )
        
        fig.update_layout(
            xaxis_title="Nombre de Viewers",
            yaxis_title="Nombre de Jeux",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_market_share_pie(self, df: pd.DataFrame):
        """
        Affiche le camembert des parts de marché.
        
        Args:
            df: DataFrame des données
        """
        st.subheader("🥧 Parts de Marché Twitch")
        
        if df.empty or 'viewers' not in df.columns:
            st.info("Aucune donnée disponible")
            return
        
        # Top 10 + "Autres"
        top_10 = df.nlargest(10, 'viewers')
        others_viewers = df[~df.index.isin(top_10.index)]['viewers'].sum()
        
        # Préparation des données pour le pie chart
        pie_data = top_10[['title', 'viewers']].copy()
        if others_viewers > 0:
            pie_data = pd.concat([
                pie_data,
                pd.DataFrame({'title': ['Autres'], 'viewers': [others_viewers]})
            ])
        
        # Graphique en camembert
        fig = px.pie(
            pie_data,
            values='viewers',
            names='title',
            title="Répartition des viewers par jeu",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_data_table(self, df: pd.DataFrame):
        """
        Affiche le tableau des données.
        
        Args:
            df: DataFrame des données
        """
        st.subheader("📋 Données Détaillées")
        
        if df.empty:
            st.info("Aucune donnée à afficher")
            return
        
        # Sélection des colonnes à afficher
        display_columns = ['title', 'viewers', 'change', 'share']
        available_columns = [col for col in display_columns if col in df.columns]
        
        if available_columns:
            display_df = df[available_columns].copy()
            
            # Formatage pour l'affichage
            if 'viewers' in display_df.columns:
                display_df['viewers'] = display_df['viewers'].apply(
                    lambda x: formatter.format_number(x) if pd.notna(x) else 'N/A'
                )
            
            if 'change' in display_df.columns:
                display_df['change'] = display_df['change'].apply(
                    lambda x: formatter.format_percentage(x) if pd.notna(x) else 'N/A'
                )
            
            # Affichage avec possibilité de téléchargement
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Bouton de téléchargement CSV
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Télécharger CSV",
                data=csv,
                file_name=f"twitch_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    def render_database_info(self):
        """Affiche les informations de la base de données."""
        st.sidebar.header("💾 Info Base de Données")
        
        try:
            stats = db_manager.get_database_stats()
            
            if stats:
                st.sidebar.metric("Total jeux", stats.get('total_games', 0))
                
                if stats.get('last_update'):
                    last_update = stats['last_update']
                    if isinstance(last_update, str):
                        last_update = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                    
                    st.sidebar.write(f"**Dernière MAJ:** {formatter.format_timestamp(last_update)}")
                
                st.sidebar.write(f"**Base:** {stats.get('database_name', 'N/A')}")
                st.sidebar.write(f"**Collection:** {stats.get('collection_name', 'N/A')}")
            
        except Exception as e:
            st.sidebar.error(f"Erreur info DB: {e}")
    
    def run(self):
        """Exécute le dashboard principal."""
        try:
            # En-tête
            self.render_header()
            
            # Chargement des données
            df = self.load_data()
            
            if df.empty:
                st.error("❌ Aucune donnée disponible. Lancez d'abord le scraper.")
                st.code("python src/scraper/twitch_scraper.py")
                return
            
            # Filtres sidebar
            filters = self.render_sidebar_filters(df)
            filtered_df = self.apply_filters(df, filters)
            
            # Info base de données
            self.render_database_info()
            
            # Métriques principales
            self.render_metrics(filtered_df)
            
            # Graphiques en colonnes
            col1, col2 = st.columns(2)
            
            with col1:
                self.render_top_games_chart(filtered_df)
            
            with col2:
                self.render_viewers_distribution(filtered_df)
            
            # Graphique pleine largeur
            self.render_market_share_pie(filtered_df)
            
            # Tableau des données
            self.render_data_table(filtered_df)
            
            # Footer
            st.markdown("---")
            st.markdown(
                "<div style='text-align: center; color: #666;'>"
                "🎮 Twitch Trends Tracker - Créé par Hicham, Aya et Boubaker"
                "</div>",
                unsafe_allow_html=True
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur dashboard: {e}")
            st.error(f"Erreur inattendue: {e}")


def main():
    """Point d'entrée principal du dashboard."""
    try:
        dashboard = TwitchDashboard()
        dashboard.run()
    except Exception as e:
        st.error(f"Erreur fatale: {e}")
        logger.error(f"❌ Erreur fatale dashboard: {e}")


if __name__ == "__main__":
    main()
