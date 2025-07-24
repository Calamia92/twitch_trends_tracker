"""
TwitchTracker Enricher - Version simplifiée et fonctionnelle.

Ce script enrichit votre base de données existante avec des données de TwitchTracker.com
en utilisant des requêtes HTTP simples pour éviter les complications Selenium.

Objectif: Enrichir les collections games, streamers et events avec des données TwitchTracker.
"""

import requests
import time
import re
from datetime import datetime
from typing import Dict, List, Any
import pymongo
from bs4 import BeautifulSoup
import logging

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TwitchTrackerEnricher:
    """Enrichissement simple des données avec TwitchTracker."""
    
    def __init__(self):
        """Initialise l'enricher."""
        self.base_url = "https://twitchtracker.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Configuration MongoDB
        self.mongo_uri = "mongodb://localhost:27017/"
        self.db_name = "twitch_trends"
        
        logger.info("🎯 TwitchTracker Enricher initialisé")
    
    def analyze_existing_data(self) -> Dict[str, Any]:
        """Analyse les données existantes pour planifier l'enrichissement."""
        logger.info("🔍 Analyse des données existantes...")
        
        try:
            client = pymongo.MongoClient(self.mongo_uri)
            db = client[self.db_name]
            
            analysis = {
                'collections': db.list_collection_names(),
                'counts': {},
                'sample_data': {},
                'enrichment_plan': []
            }
            
            # Comptes par collection
            for collection_name in analysis['collections']:
                count = db[collection_name].count_documents({})
                analysis['counts'][collection_name] = count
                
                # Échantillon de données
                sample = db[collection_name].find_one()
                if sample:
                    analysis['sample_data'][collection_name] = {
                        key: type(value).__name__ for key, value in sample.items() 
                        if key != '_id'
                    }
            
            # Plan d'enrichissement
            enrichment_opportunities = []
            
            if 'games' in analysis['collections']:
                enrichment_opportunities.append({
                    'collection': 'games',
                    'source': 'TwitchTracker Games Ranking',
                    'new_data': 'Ranking global, croissance 7j, part de marché Twitch',
                    'fields_to_add': ['twitchtracker_rank', 'growth_7d', 'market_share_percent']
                })
            
            if 'streamers' in analysis['collections']:
                enrichment_opportunities.append({
                    'collection': 'streamers', 
                    'source': 'TwitchTracker Top Streamers',
                    'new_data': 'Ranking global, heures streamées, peak viewers',
                    'fields_to_add': ['global_rank', 'hours_streamed_month', 'peak_viewers_month']
                })
            
            # Nouvelles collections possibles
            enrichment_opportunities.extend([
                {
                    'collection': 'trending_games',
                    'source': 'TwitchTracker Homepage',
                    'new_data': 'Jeux en forte croissance avec pourcentages',
                    'type': 'new_collection'
                },
                {
                    'collection': 'live_stats',
                    'source': 'TwitchTracker Global Stats', 
                    'new_data': 'Statistiques globales Twitch en temps réel',
                    'type': 'new_collection'
                }
            ])
            
            analysis['enrichment_plan'] = enrichment_opportunities
            
            client.close()
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse: {e}")
            return {}
    
    def fetch_twitchtracker_page(self, url: str) -> BeautifulSoup:
        """Récupère et parse une page TwitchTracker."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            time.sleep(1)  # Rate limiting respectueux
            
            return BeautifulSoup(response.content, 'html.parser')
            
        except requests.RequestException as e:
            logger.error(f"❌ Erreur requête {url}: {e}")
            return None
    
    def scrape_global_stats(self) -> Dict[str, Any]:
        """Scrape les statistiques globales depuis la homepage."""
        logger.info("📊 Scraping statistiques globales...")
        
        soup = self.fetch_twitchtracker_page(f"{self.base_url}/")
        if not soup:
            return {}
        
        stats = {
            'timestamp': datetime.now(),
            'source': 'twitchtracker_homepage',
            'concurrent_viewers': 0,
            'concurrent_streams': 0,
            'unique_games': 0
        }
        
        try:
            # Recherche des statistiques dans le texte
            text_content = soup.get_text()
            
            # Pattern pour "X,XXX Viewers watching"
            viewers_match = re.search(r'([\d,]+)\s+Viewers\s+watching', text_content)
            if viewers_match:
                stats['concurrent_viewers'] = self._parse_number(viewers_match.group(1))
            
            # Pattern pour "X,XXX Channels broadcasting"
            streams_match = re.search(r'([\d,]+)\s+Channels\s+broadcasting', text_content)
            if streams_match:
                stats['concurrent_streams'] = self._parse_number(streams_match.group(1))
            
            # Pattern pour "X,XXX Unique games live"
            games_match = re.search(r'([\d,]+)\s+Unique\s+games\s+live', text_content)
            if games_match:
                stats['unique_games'] = self._parse_number(games_match.group(1))
            
            logger.info(f"✅ Stats récupérées: {stats['concurrent_viewers']:,} viewers")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Erreur parsing stats: {e}")
            return stats
    
    def scrape_trending_games(self) -> List[Dict[str, Any]]:
        """Scrape les jeux en tendance depuis la homepage."""
        logger.info("📈 Scraping jeux trending...")
        
        soup = self.fetch_twitchtracker_page(f"{self.base_url}/")
        if not soup:
            return []
        
        trending_games = []
        
        try:
            # Recherche de la section trending games
            trending_header = soup.find('h4', string=re.compile(r'TRENDING\s+GAMES', re.I))
            if trending_header:
                # Trouve le tableau suivant
                table = trending_header.find_next('table')
                if table:
                    rows = table.find_all('tr')[1:]  # Skip header
                    
                    for i, row in enumerate(rows[:15]):  # Top 15
                        try:
                            cells = row.find_all('td')
                            if len(cells) >= 3:
                                game_name = cells[1].get_text().strip()
                                channels_text = cells[2].get_text().strip()
                                growth_text = cells[3].get_text().strip() if len(cells) > 3 else "0%"
                                
                                channels = self._parse_number(channels_text)
                                growth = self._parse_percentage(growth_text)
                                
                                trending_data = {
                                    'game_name': game_name,
                                    'trending_rank': i + 1,
                                    'channels_streaming': channels,
                                    'growth_percentage': growth,
                                    'timestamp': datetime.now(),
                                    'source': 'twitchtracker_trending'
                                }
                                
                                trending_games.append(trending_data)
                                
                        except Exception as e:
                            logger.warning(f"⚠️ Erreur parsing trending game {i}: {e}")
                            continue
            
            logger.info(f"✅ {len(trending_games)} jeux trending récupérés")
            return trending_games
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping trending: {e}")
            return []
    
    def scrape_top_games(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Scrape le top des jeux depuis la page games."""
        logger.info(f"🎮 Scraping top {limit} jeux...")
        
        soup = self.fetch_twitchtracker_page(f"{self.base_url}/games")
        if not soup:
            return []
        
        games = []
        
        try:
            # Recherche du tableau des jeux
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')[1:]  # Skip header
                
                for i, row in enumerate(rows[:limit]):
                    try:
                        cells = row.find_all('td')
                        if len(cells) >= 4:
                            # Position dans le ranking
                            rank = i + 1
                            
                            # Nom du jeu (généralement dans la 2ème cellule)
                            game_cell = cells[1]
                            game_name = game_cell.get_text().strip()
                            
                            # Viewers moyens
                            viewers_text = cells[2].get_text().strip()
                            avg_viewers = self._parse_number(viewers_text)
                            
                            # Changement 7 jours
                            change_text = cells[3].get_text().strip()
                            change_7d = self._parse_percentage(change_text)
                            
                            # Part de marché (si disponible)
                            market_share = 0.0
                            if len(cells) > 4:
                                market_text = cells[4].get_text().strip()
                                market_share = self._parse_percentage(market_text)
                            
                            game_data = {
                                'game_name': game_name,
                                'twitchtracker_rank': rank,
                                'avg_viewers_week': avg_viewers,
                                'growth_7d_percent': change_7d,
                                'market_share_percent': market_share,
                                'timestamp': datetime.now(),
                                'source': 'twitchtracker_games'
                            }
                            
                            games.append(game_data)
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur parsing jeu {i}: {e}")
                        continue
                
                # Si on a trouvé des jeux, on s'arrête là
                if games:
                    break
            
            logger.info(f"✅ {len(games)} jeux récupérés")
            return games
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping jeux: {e}")
            return []
    
    def enrich_database(self) -> bool:
        """Enrichit la base de données avec les nouvelles données."""
        logger.info("💾 Enrichissement de la base de données...")
        
        try:
            client = pymongo.MongoClient(self.mongo_uri)
            db = client[self.db_name]
            
            # 1. Récupération des nouvelles données
            global_stats = self.scrape_global_stats()
            trending_games = self.scrape_trending_games()
            top_games = self.scrape_top_games(50)
            
            enrichment_summary = {
                'global_stats': 0,
                'trending_games': 0,
                'top_games_enriched': 0
            }
            
            # 2. Sauvegarde des statistiques globales
            if global_stats and global_stats.get('concurrent_viewers', 0) > 0:
                db['twitchtracker_live_stats'].insert_one(global_stats)
                enrichment_summary['global_stats'] = 1
                logger.info("✅ Statistiques globales sauvegardées")
            
            # 3. Sauvegarde des jeux trending
            if trending_games:
                # Supprime les anciens trending et insère les nouveaux
                db['twitchtracker_trending'].delete_many({'source': 'twitchtracker_trending'})
                db['twitchtracker_trending'].insert_many(trending_games)
                enrichment_summary['trending_games'] = len(trending_games)
                logger.info(f"✅ {len(trending_games)} jeux trending sauvegardés")
            
            # 4. Enrichissement des jeux existants avec données TwitchTracker
            if top_games:
                for tt_game in top_games:
                    # Recherche de correspondance avec les jeux existants
                    existing_game = db['games'].find_one({
                        'game_name': {'$regex': re.escape(tt_game['game_name']), '$options': 'i'}
                    })
                    
                    if existing_game:
                        # Enrichit le jeu existant
                        db['games'].update_one(
                            {'_id': existing_game['_id']},
                            {'$set': {
                                'twitchtracker_rank': tt_game['twitchtracker_rank'],
                                'twitchtracker_viewers': tt_game['avg_viewers_week'],
                                'twitchtracker_growth_7d': tt_game['growth_7d_percent'],
                                'twitchtracker_market_share': tt_game['market_share_percent'],
                                'twitchtracker_last_update': datetime.now()
                            }}
                        )
                        enrichment_summary['top_games_enriched'] += 1
                
                # Sauvegarde aussi les données complètes TwitchTracker
                db['twitchtracker_games'].delete_many({'source': 'twitchtracker_games'})
                db['twitchtracker_games'].insert_many(top_games)
                logger.info(f"✅ {enrichment_summary['top_games_enriched']} jeux existants enrichis")
                logger.info(f"✅ {len(top_games)} jeux TwitchTracker sauvegardés")
            
            client.close()
            
            # 5. Rapport d'enrichissement
            logger.info("🎊 ENRICHISSEMENT TERMINÉ")
            logger.info(f"   - Stats globales: {enrichment_summary['global_stats']}")
            logger.info(f"   - Jeux trending: {enrichment_summary['trending_games']}")
            logger.info(f"   - Jeux enrichis: {enrichment_summary['top_games_enriched']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur enrichissement: {e}")
            return False
    
    def run_full_analysis_and_enrichment(self) -> bool:
        """Exécute l'analyse complète et l'enrichissement."""
        logger.info("🚀 DÉMARRAGE ANALYSE ET ENRICHISSEMENT TWITCHTRACKER")
        logger.info("=" * 60)
        
        try:
            # 1. Analyse des données existantes
            analysis = self.analyze_existing_data()
            
            if analysis:
                logger.info("📊 ANALYSE DES DONNÉES EXISTANTES:")
                logger.info(f"   Collections: {analysis['collections']}")
                logger.info(f"   Comptes: {analysis['counts']}")
                
                logger.info("\n🎯 PLAN D'ENRICHISSEMENT:")
                for plan in analysis.get('enrichment_plan', []):
                    logger.info(f"   - {plan['collection']}: {plan['new_data']}")
            
            # 2. Enrichissement
            logger.info("\n🔄 DÉBUT DE L'ENRICHISSEMENT...")
            success = self.enrich_database()
            
            if success:
                logger.info("\n✅ ENRICHISSEMENT RÉUSSI!")
                return True
            else:
                logger.error("\n❌ ÉCHEC DE L'ENRICHISSEMENT")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur processus complet: {e}")
            return False
    
    # =====================================
    # MÉTHODES UTILITAIRES
    # =====================================
    
    def _parse_number(self, text: str) -> int:
        """Parse un nombre avec gestion des suffixes K, M."""
        if not text:
            return 0
        
        text = text.upper().replace(',', '').strip()
        
        # Gestion des suffixes
        if 'K' in text:
            number_match = re.search(r'([\d.]+)K', text)
            if number_match:
                return int(float(number_match.group(1)) * 1000)
        elif 'M' in text:
            number_match = re.search(r'([\d.]+)M', text)
            if number_match:
                return int(float(number_match.group(1)) * 1000000)
        
        # Nombre simple
        number_match = re.search(r'[\d]+', text)
        if number_match:
            return int(number_match.group())
        
        return 0
    
    def _parse_percentage(self, text: str) -> float:
        """Parse un pourcentage."""
        if not text:
            return 0.0
        
        percentage_match = re.search(r'([+-]?[\d.]+)%', text)
        if percentage_match:
            try:
                return float(percentage_match.group(1))
            except ValueError:
                return 0.0
        
        return 0.0


def main():
    """Point d'entrée principal."""
    enricher = TwitchTrackerEnricher()
    
    try:
        success = enricher.run_full_analysis_and_enrichment()
        
        if success:
            print("\n🎉 ENRICHISSEMENT TWITCHTRACKER TERMINÉ AVEC SUCCÈS!")
            print("\nNouvelles collections créées:")
            print("  - twitchtracker_live_stats: Statistiques globales")
            print("  - twitchtracker_trending: Jeux en tendance")
            print("  - twitchtracker_games: Données complètes des jeux")
            print("\nCollections enrichies:")
            print("  - games: Ajout de données TwitchTracker (rank, growth, market share)")
        else:
            print("\n❌ Échec de l'enrichissement")
            
    except Exception as e:
        print(f"\n❌ Erreur: {e}")


if __name__ == "__main__":
    main()
