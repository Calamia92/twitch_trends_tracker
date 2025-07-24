#!/usr/bin/env python3
"""
Point d'entrée principal pour Twitch Trends Tracker.

Ce script orchestre tous les composants de l'application :
- Scrapers multi-sources (jeux, événements, streamers)
- Gestion de base de données MongoDB
- Dashboard Streamlit
- Logging centralisé

Usage:
    python main.py --mode [scraping|dashboard|all]
    python main.py --scraper [games|events|streamers|all]
    python main.py --dashboard
    python main.py --help

Auteur: Équipe Twitch Trends Tracker
Date: 24 juillet 2025
Version: 2.0.0
"""

import sys
import argparse
import asyncio
from datetime import datetime
from pathlib import Path
import time
from typing import Optional, List, Dict, Any

# Ajout du chemin du projet pour les imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import config  
from src.shared.logger import get_logger, log_scraping_session
from src.shared.exceptions import handle_exceptions, TwitchTrackerException


class TwitchTrendsTracker:
    """
    Classe principale pour orchestrer l'application Twitch Trends Tracker.
    
    Cette classe coordonne tous les composants de l'application et fournit
    une interface unifiée pour l'exécution des différents modes.
    """
    
    def __init__(self):
        """Initialise l'application."""
        self.logger = get_logger("main")
        self.start_time = datetime.now()
        
        # Validation de la configuration
        if not config.validate():
            raise TwitchTrackerException("Configuration invalide")
        
        self.logger.info("🎮 Initialisation de Twitch Trends Tracker v2.0.0")
        self.logger.info(f"📁 Répertoire de travail: {PROJECT_ROOT}")
    
    @handle_exceptions()
    def run_scrapers(self, scraper_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Exécute les scrapers spécifiés.
        
        Args:
            scraper_types: Liste des types de scrapers à exécuter
                          ['games', 'events', 'streamers'] ou None pour tous
        
        Returns:
            dict: Résultats du scraping avec statistiques
        """
        if scraper_types is None:
            scraper_types = ['games', 'events', 'streamers']
        
        self.logger.info(f"🚀 Démarrage des scrapers: {', '.join(scraper_types)}")
        
        results = {
            'scrapers_executed': [],
            'total_items': 0,
            'errors': 0,
            'duration': 0.0,
            'details': {}
        }
        
        start_time = time.time()
        
        try:
            # Import dynamique des scrapers pour éviter les erreurs de dépendances
            scrapers = self._load_scrapers(scraper_types)
            
            for scraper_name, scraper_class in scrapers.items():
                self.logger.info(f"📡 Exécution du scraper: {scraper_name}")
                
                scraper_start = time.time()
                try:
                    # Initialisation et exécution du scraper
                    scraper = scraper_class()
                    items = scraper.scrape()
                    
                    scraper_duration = time.time() - scraper_start
                    
                    # Enregistrement des résultats
                    results['scrapers_executed'].append(scraper_name)
                    results['total_items'] += len(items) if items else 0
                    results['details'][scraper_name] = {
                        'items_count': len(items) if items else 0,
                        'duration': scraper_duration,
                        'status': 'success'
                    }
                    
                    # Log de la session
                    log_scraping_session(
                        scraper_name=scraper_name,
                        status='success',
                        items_scraped=len(items) if items else 0,
                        duration=scraper_duration
                    )
                    
                except Exception as e:
                    scraper_duration = time.time() - scraper_start
                    results['errors'] += 1
                    results['details'][scraper_name] = {
                        'items_count': 0,
                        'duration': scraper_duration,
                        'status': 'error',
                        'error': str(e)
                    }
                    
                    log_scraping_session(
                        scraper_name=scraper_name,
                        status='error',
                        errors=1,
                        duration=scraper_duration,
                        details={'error': str(e)}
                    )
                    
                    self.logger.error(f"❌ Erreur dans {scraper_name}: {e}")
        
        except Exception as e:
            self.logger.error(f"💥 Erreur générale lors du scraping: {e}")
            results['errors'] += 1
        
        finally:
            results['duration'] = time.time() - start_time
            
            # Résumé des résultats
            self.logger.info("📊 Résumé du scraping:")
            self.logger.info(f"   ✅ Scrapers exécutés: {len(results['scrapers_executed'])}")
            self.logger.info(f"   📄 Éléments collectés: {results['total_items']}")
            self.logger.info(f"   ❌ Erreurs: {results['errors']}")
            self.logger.info(f"   ⏱️ Durée totale: {results['duration']:.2f}s")
        
        return results
    
    def _load_scrapers(self, scraper_types: list) -> dict:
        """
        Charge dynamiquement les classes de scrapers.
        
        Args:
            scraper_types: Types de scrapers à charger
        
        Returns:
            dict: Dictionnaire {nom: classe} des scrapers
        """
        scrapers = {}
        
        for scraper_type in scraper_types:
            try:
                if scraper_type == 'games':
                    from src.infrastructure.scrapers.twitch_scraper import TwitchScraper
                    scrapers['games'] = TwitchScraper
                    
                elif scraper_type == 'events':
                    from src.infrastructure.scrapers.events_scraper import EventsScraper
                    scrapers['events'] = EventsScraper
                    
                elif scraper_type == 'streamers':
                    from src.infrastructure.scrapers.french_streamers_scraper import FrenchStreamersScraper
                    scrapers['streamers'] = FrenchStreamersScraper
                    
                elif scraper_type == 'twitchtracker':
                    from src.infrastructure.scrapers.twitchtracker_enricher_v2 import TwitchTrackerEnricherV2
                    scrapers['twitchtracker'] = TwitchTrackerEnricherV2
                    
                else:
                    self.logger.warning(f"⚠️ Type de scraper inconnu: {scraper_type}")
            
            except ImportError as e:
                self.logger.error(f"❌ Impossible de charger le scraper {scraper_type}: {e}")
        
        return scrapers
    
    @handle_exceptions()
    def launch_dashboard(self, port: int = 8501) -> Optional[Any]:
        """
        Lance le dashboard Streamlit.
        
        Args:
            port: Port pour le serveur Streamlit
        """
        self.logger.info(f"🖥️ Lancement du dashboard sur le port {port}")
        
        try:
            import subprocess
            import sys
            
            # Lancement de Streamlit avec l'application
            cmd = [
                sys.executable, "-m", "streamlit", "run", 
                str(PROJECT_ROOT / "app.py"),
                "--server.port", str(port),
                "--server.headless", "true"
            ]
            
            self.logger.info(f"🚀 Commande: {' '.join(cmd)}")
            
            # Lancement en arrière-plan
            process = subprocess.Popen(cmd, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
            
            self.logger.info(f"✅ Dashboard lancé avec PID: {process.pid}")
            self.logger.info(f"🌐 URL: http://localhost:{port}")
            
            return process
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du lancement du dashboard: {e}")
            raise
    
    def run_complete_cycle(self) -> dict:
        """
        Exécute un cycle complet: scraping + dashboard.
        
        Returns:
            dict: Résultats du cycle complet
        """
        self.logger.info("🔄 Démarrage du cycle complet")
        
        # 1. Scraping de toutes les sources
        scraping_results = self.run_scrapers()
        
        # 2. Lancement du dashboard
        try:
            dashboard_process = self.launch_dashboard()
            
            return {
                'scraping': scraping_results,
                'dashboard': {
                    'status': 'launched',
                    'pid': dashboard_process.pid if dashboard_process else None
                },
                'total_duration': time.time() - self.start_time.timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur dans le cycle complet: {e}")
            return {
                'scraping': scraping_results,
                'dashboard': {
                    'status': 'error',
                    'error': str(e)
                },
                'total_duration': time.time() - self.start_time.timestamp()
            }
    
    def get_status(self) -> dict:
        """
        Retourne le statut de l'application.
        
        Returns:
            dict: Informations de statut
        """
        uptime = datetime.now() - self.start_time
        
        return {
            'application': 'Twitch Trends Tracker',
            'version': '2.0.0',
            'status': 'running',
            'uptime': str(uptime),
            'start_time': self.start_time.isoformat(),
            'configuration': {
                'database': {
                    'host': config.database.host,
                    'port': config.database.port,
                    'database': config.database.database_name
                },
                'scrapers_enabled': len(config.scraping.events_sources) + len(config.scraping.streamers_sources) + 1
            }
        }


def create_parser() -> argparse.ArgumentParser:
    """Crée le parser d'arguments en ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Twitch Trends Tracker - Scraping et dashboard multi-sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Twitch Trends Tracker v2.0.0 - CLI Principal

Exemples d'utilisation:
  python main.py --mode scraping                    # Scraping uniquement
  python main.py --mode dashboard                   # Dashboard uniquement  
  python main.py --mode all                         # Scraping + Dashboard
  python main.py --scraper games events             # Scrapers spécifiques
  python main.py --scraper twitchtracker            # Enrichissement TwitchTracker
  python main.py --dashboard --port 8502            # Dashboard sur port custom
  python main.py --status                           # Affiche le statut
        """
    )
    
    # Arguments principaux
    parser.add_argument(
        '--mode', 
        choices=['scraping', 'dashboard', 'all'],
        default='all',
        help='Mode d\'exécution (défaut: all)'
    )
    
    parser.add_argument(
        '--scraper',
        nargs='*',
        choices=['games', 'events', 'streamers', 'twitchtracker', 'all'],
        default=['all'],
        help='Types de scrapers à exécuter (défaut: all)'
    )
    
    parser.add_argument(
        '--dashboard',
        action='store_true',
        help='Lance le dashboard Streamlit'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8501,
        help='Port pour le dashboard (défaut: 8501)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Affiche le statut de l\'application'
    )
    
    parser.add_argument(
        '--config-check',
        action='store_true',
        help='Vérifie la configuration'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mode verbeux'
    )
    
    return parser


def main():
    """Fonction principale."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Initialisation de l'application
        app = TwitchTrendsTracker()
        
        # Configuration du logging verbose
        if args.verbose:
            import logging
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Traitement des commandes
        if args.status:
            # Affichage du statut
            status = app.get_status()
            print("📊 Statut de l'application:")
            for key, value in status.items():
                print(f"   {key}: {value}")
            return
        
        if args.config_check:
            # Vérification de la configuration
            print("🔧 Vérification de la configuration...")
            if config.validate():
                print("✅ Configuration valide")
            else:
                print("❌ Configuration invalide")
                return 1
            return
        
        # Détermination des scrapers à exécuter
        scrapers_to_run = args.scraper
        if 'all' in scrapers_to_run:
            scrapers_to_run = ['games', 'events', 'streamers', 'twitchtracker']
        
        # Exécution selon le mode
        if args.mode == 'scraping':
            results = app.run_scrapers(scrapers_to_run)
            print(f"✅ Scraping terminé: {results['total_items']} éléments collectés")
            
        elif args.mode == 'dashboard' or args.dashboard:
            process = app.launch_dashboard(args.port)
            print(f"🌐 Dashboard disponible sur: http://localhost:{args.port}")
            
            # Attente pour que le dashboard reste actif
            if process:
                try:
                    print("Appuyez sur Ctrl+C pour arrêter...")
                    process.wait()
                except KeyboardInterrupt:
                    print("\n🛑 Arrêt du dashboard...")
                    process.terminate()
            else:
                print("⚠️ Le dashboard n'a pas pu être lancé")
                
        elif args.mode == 'all':
            results = app.run_complete_cycle()
            print("🎉 Cycle complet terminé!")
            print(f"   📄 Éléments scrapés: {results['scraping']['total_items']}")
            print(f"   🖥️ Dashboard: {results['dashboard']['status']}")
            
            if results['dashboard']['status'] == 'launched':
                print(f"🌐 Dashboard disponible sur: http://localhost:{args.port}")
                print("Appuyez sur Ctrl+C pour arrêter...")
                try:
                    import time
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Arrêt de l'application...")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Interruption utilisateur")
        return 130
    
    except Exception as e:
        print(f"💥 Erreur fatale: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
