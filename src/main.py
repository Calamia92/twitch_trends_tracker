#!/usr/bin/env python3
"""
Point d'entrée principal pour le système de scraping Twitch Trends Tracker.

Ce script orchestre le scraping multi-sources et sauvegarde les données
dans MongoDB selon les exigences du TP.
"""

import sys
import os
import asyncio
import schedule
import time
from datetime import datetime
import logging

# Ajout du chemin pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import config
from database.mongodb_manager import db_manager
from scraper.twitch_scraper import TwitchScraper
from scraper.events_scraper import EventsScraper
from scraper.french_streamers_scraper import FrenchStreamersScraper

# Configuration du logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TwitchTrendsOrchestrator:
    """
    Orchestrateur principal du système de scraping multi-sources.
    
    Cette classe coordonne tous les scrapers et gère la collecte
    de données selon les exigences du TP.
    """
    
    def __init__(self):
        """Initialise l'orchestrateur."""
        self.twitch_scraper = None
        self.events_scraper = None
        self.streamers_scraper = None
        self.is_running = False
        
        logger.info("🎮 Initialisation du Twitch Trends Orchestrator")
    
    def initialize_scrapers(self) -> bool:
        """
        Initialise tous les scrapers.
        
        Returns:
            bool: True si l'initialisation réussit
        """
        try:
            logger.info("🔄 Initialisation des scrapers...")
            
            # Scraper Twitch principal
            self.twitch_scraper = TwitchScraper()
            logger.info("✅ Scraper Twitch initialisé")
            
            # Scraper d'événements gaming
            self.events_scraper = EventsScraper()
            logger.info("✅ Scraper événements initialisé")
            
            # Scraper streamers français
            self.streamers_scraper = FrenchStreamersScraper()
            logger.info("✅ Scraper streamers français initialisé")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation: {e}")
            return False
    
    def run_twitch_scraping(self) -> bool:
        """
        Exécute le scraping des jeux Twitch.
        
        Returns:
            bool: True si le scraping réussit
        """
        try:
            logger.info("🎮 Démarrage du scraping Twitch...")
            
            if not self.twitch_scraper:
                logger.error("❌ Scraper Twitch non initialisé")
                return False
            
            # Scraping des jeux populaires
            games_data = self.twitch_scraper.scrape_with_retry(max_retries=3)
            
            if games_data:
                logger.info(f"✅ {len(games_data)} jeux récupérés depuis Twitch")
                
                # Sauvegarde en base
                saved_count = 0
                for game in games_data:
                    if db_manager.insert_data(game):
                        saved_count += 1
                
                logger.info(f"💾 {saved_count}/{len(games_data)} jeux sauvegardés")
                return True
            else:
                logger.warning("⚠️ Aucune donnée récupérée depuis Twitch")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur scraping Twitch: {e}")
            return False
    
    def run_events_scraping(self) -> bool:
        """
        Exécute le scraping des événements gaming.
        
        Returns:
            bool: True si le scraping réussit
        """
        try:
            logger.info("🎯 Démarrage du scraping événements...")
            
            if not self.events_scraper:
                logger.error("❌ Scraper événements non initialisé")
                return False
            
            # Scraping des événements Liquipedia
            events_data = self.events_scraper.scrape_liquipedia_events()
            
            # Scraping des actualités gaming
            news_data = self.events_scraper.scrape_gaming_news()
            
            # Combinaison des données
            all_events = events_data + news_data
            
            if all_events:
                logger.info(f"✅ {len(all_events)} événements/actualités récupérés")
                
                # Sauvegarde en base
                saved_count = 0
                for event in all_events:
                    if db_manager.insert_event_data(event):
                        saved_count += 1
                
                logger.info(f"💾 {saved_count}/{len(all_events)} événements sauvegardés")
                return True
            else:
                logger.warning("⚠️ Aucun événement récupéré")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur scraping événements: {e}")
            return False
    
    def run_streamers_scraping(self) -> bool:
        """
        Exécute le scraping des streamers français.
        
        Returns:
            bool: True si le scraping réussit
        """
        try:
            logger.info("🇫🇷 Démarrage du scraping streamers français...")
            
            if not self.streamers_scraper:
                logger.error("❌ Scraper streamers non initialisé")
                return False
            
            # Scraping des top streamers français
            streamers_data = self.streamers_scraper.scrape_french_streamers_twitchtracker()
            
            if streamers_data:
                logger.info(f"✅ {len(streamers_data)} streamers français récupérés")
                
                # Sauvegarde en base
                saved_count = 0
                for streamer in streamers_data:
                    if db_manager.insert_streamer_data(streamer):
                        saved_count += 1
                
                logger.info(f"💾 {saved_count}/{len(streamers_data)} streamers sauvegardés")
                return True
            else:
                logger.warning("⚠️ Aucun streamer récupéré")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur scraping streamers: {e}")
            return False
    
    def run_full_scraping_cycle(self) -> Dict[str, bool]:
        """
        Exécute un cycle complet de scraping multi-sources.
        
        Returns:
            Dict[str, bool]: Résultats de chaque scraper
        """
        logger.info("🚀 Démarrage du cycle complet de scraping")
        
        results = {
            'twitch': False,
            'events': False,
            'streamers': False,
            'timestamp': datetime.now()
        }
        
        # Vérification de la base de données
        if not db_manager.is_connected():
            logger.error("❌ Base de données non connectée")
            return results
        
        # Initialisation des scrapers
        if not self.initialize_scrapers():
            logger.error("❌ Échec de l'initialisation des scrapers")
            return results
        
        # Exécution séquentielle des scrapers
        results['twitch'] = self.run_twitch_scraping()
        results['events'] = self.run_events_scraping()
        results['streamers'] = self.run_streamers_scraping()
        
        # Rapport final
        successful = sum(1 for result in results.values() if isinstance(result, bool) and result)
        total = sum(1 for result in results.values() if isinstance(result, bool))
        
        logger.info(f"📊 Cycle terminé: {successful}/{total} scrapers réussis")
        
        return results
    
    def cleanup(self):
        """Nettoie les ressources."""
        try:
            if self.twitch_scraper:
                self.twitch_scraper.close()
            
            if self.events_scraper:
                self.events_scraper.close()
                
            if self.streamers_scraper:
                self.streamers_scraper.close()
            
            logger.info("🧹 Nettoyage terminé")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du nettoyage: {e}")


def run_scheduled_scraping():
    """Fonction pour le scraping programmé."""
    orchestrator = TwitchTrendsOrchestrator()
    try:
        results = orchestrator.run_full_scraping_cycle()
        logger.info(f"⏰ Scraping programmé terminé: {results}")
    finally:
        orchestrator.cleanup()


def main():
    """Fonction principale."""
    logger.info("🎮 Démarrage de Twitch Trends Tracker")
    
    if len(sys.argv) > 1 and sys.argv[1] == '--schedule':
        # Mode programmé
        logger.info("⏰ Mode programmé activé")
        
        # Programmation du scraping toutes les 30 minutes
        schedule.every(30).minutes.do(run_scheduled_scraping)
        
        # Premier scraping immédiat
        run_scheduled_scraping()
        
        # Boucle d'attente
        logger.info("⏰ Attente des prochains cycles de scraping...")
        while True:
            schedule.run_pending()
            time.sleep(60)  # Vérification chaque minute
    
    else:
        # Mode manuel - un seul cycle
        orchestrator = TwitchTrendsOrchestrator()
        try:
            results = orchestrator.run_full_scraping_cycle()
            
            # Affichage des résultats
            print("\n" + "="*60)
            print("📊 RÉSULTATS DU SCRAPING")
            print("="*60)
            print(f"🎮 Scraper Twitch: {'✅ Réussi' if results['twitch'] else '❌ Échec'}")
            print(f"🎯 Scraper Événements: {'✅ Réussi' if results['events'] else '❌ Échec'}")
            print(f"🇫🇷 Scraper Streamers: {'✅ Réussi' if results['streamers'] else '❌ Échec'}")
            print(f"🕒 Timestamp: {results['timestamp']}")
            print("="*60)
            
            successful = sum(1 for key in ['twitch', 'events', 'streamers'] if results[key])
            if successful == 3:
                print("🏆 Tous les scrapers ont réussi !")
            elif successful >= 2:
                print("⚠️ La plupart des scrapers ont réussi.")
            else:
                print("❌ Plusieurs échecs détectés.")
            
            print("\n🎯 Dashboard disponible sur: http://localhost:8501")
            print("📊 Utilisez 'streamlit run app.py' pour voir les données")
            
        finally:
            orchestrator.cleanup()


if __name__ == "__main__":
    main()
