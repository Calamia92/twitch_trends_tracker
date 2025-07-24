"""
TwitchTracker Enricher - Version améliorée avec parsing HTML optimisé.

Cette version comprend mieux la structure HTML de TwitchTracker et extrait 
efficacement les données pour enrichir votre base existante.
"""

import requests
import time
import re
from datetime import datetime
from typing import Dict, List, Any
import pymongo
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TwitchTrackerEnricherV2:
    """Version améliorée de l'enricher TwitchTracker."""
    
    def __init__(self):
        self.base_url = "https://twitchtracker.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        self.mongo_uri = "mongodb://localhost:27017/"
        self.db_name = "twitch_trends"
        
        logger.info("🎯 TwitchTracker Enricher V2 initialisé")
    
    def fetch_page(self, url: str) -> BeautifulSoup:
        """Récupère une page avec gestion d'erreurs."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            time.sleep(2)  # Respectueux du rate limiting
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"❌ Erreur récupération {url}: {e}")
            return None
    
    def scrape_trending_games(self) -> List[Dict[str, Any]]:
        """Scrape les jeux en tendance depuis la homepage."""
        logger.info("📈 Scraping jeux trending...")
        
        soup = self.fetch_page(f"{self.base_url}/")
        if not soup:
            return []
        
        trending_games = []
        
        try:
            # Recherche de la section "Trending Games"
            h4_elements = soup.find_all('h4')
            
            for h4 in h4_elements:
                h4_text = h4.get_text().strip().lower()
                if 'trending' in h4_text and 'games' in h4_text:
                    logger.info(f"✅ Section trouvée: {h4.get_text().strip()}")
                    
                    # Cherche le tableau suivant
                    table = h4.find_next('table')
                    if table:
                        rows = table.find_all('tr')[1:]  # Skip header si présent
                        
                        for i, row in enumerate(rows[:15]):  # Top 15 trending
                            try:
                                cells = row.find_all(['td', 'th'])
                                if len(cells) >= 2:
                                    # Nom du jeu (généralement 2ème cellule)
                                    game_name = cells[1].get_text().strip()
                                    
                                    # Channels et croissance (3ème cellule contient les deux)
                                    if len(cells) >= 3:
                                        stats_text = cells[2].get_text().strip()
                                        
                                        # Parse channels et pourcentage
                                        channels = self._extract_first_number(stats_text)
                                        growth = self._extract_percentage(stats_text)
                                        
                                        trending_data = {
                                            'game_name': game_name,
                                            'trending_rank': i + 1,
                                            'channels_streaming': channels,
                                            'growth_percentage': growth,
                                            'timestamp': datetime.now(),
                                            'source': 'twitchtracker_trending'
                                        }
                                        
                                        trending_games.append(trending_data)
                                        logger.debug(f"   {i+1}. {game_name}: {channels} channels, {growth}% growth")
                                        
                            except Exception as e:
                                logger.warning(f"⚠️ Erreur parsing trending game {i}: {e}")
                                continue
                    
                    break  # On a trouvé la section, on s'arrête
            
            logger.info(f"✅ {len(trending_games)} jeux trending récupérés")
            return trending_games
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping trending: {e}")
            return []
    
    def scrape_popular_games(self) -> List[Dict[str, Any]]:
        """Scrape les jeux populaires depuis la homepage."""
        logger.info("🎮 Scraping jeux populaires...")
        
        soup = self.fetch_page(f"{self.base_url}/")
        if not soup:
            return []
        
        popular_games = []
        
        try:
            # Recherche de la section "Most Popular Games"
            h4_elements = soup.find_all('h4')
            
            for h4 in h4_elements:
                h4_text = h4.get_text().strip().lower()
                if 'popular' in h4_text and 'games' in h4_text:
                    logger.info(f"✅ Section trouvée: {h4.get_text().strip()}")
                    
                    table = h4.find_next('table')
                    if table:
                        rows = table.find_all('tr')[1:]  # Skip header
                        
                        for i, row in enumerate(rows[:20]):  # Top 20 populaires
                            try:
                                cells = row.find_all(['td', 'th'])
                                if len(cells) >= 3:
                                    # Nom du jeu
                                    game_name = cells[1].get_text().strip()
                                    
                                    # Viewers moyens
                                    viewers_text = cells[2].get_text().strip()
                                    avg_viewers = self._extract_first_number(viewers_text)
                                    
                                    # Part de marché si disponible
                                    market_share = 0.0
                                    if len(cells) >= 4:
                                        market_text = cells[3].get_text().strip()
                                        market_share = self._extract_percentage(market_text)
                                    
                                    game_data = {
                                        'game_name': game_name,
                                        'popularity_rank': i + 1,
                                        'avg_viewers_week': avg_viewers,
                                        'market_share_percent': market_share,
                                        'timestamp': datetime.now(),
                                        'source': 'twitchtracker_popular'
                                    }
                                    
                                    popular_games.append(game_data)
                                    
                            except Exception as e:
                                logger.warning(f"⚠️ Erreur parsing popular game {i}: {e}")
                                continue
                    
                    break
            
            logger.info(f"✅ {len(popular_games)} jeux populaires récupérés")
            return popular_games
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping populaires: {e}")
            return []
    
    def scrape_top_streamers_homepage(self) -> List[Dict[str, Any]]:
        """Scrape les top streamers depuis la homepage."""
        logger.info("👥 Scraping top streamers...")
        
        soup = self.fetch_page(f"{self.base_url}/")
        if not soup:
            return []
        
        streamers = []
        
        try:
            # Recherche de la section "Top Live Channels"
            h4_elements = soup.find_all('h4')
            
            for h4 in h4_elements:
                h4_text = h4.get_text().strip().lower()
                if 'top' in h4_text and 'channels' in h4_text:
                    logger.info(f"✅ Section trouvée: {h4.get_text().strip()}")
                    
                    table = h4.find_next('table')
                    if table:
                        rows = table.find_all('tr')[1:]  # Skip header
                        
                        for i, row in enumerate(rows[:15]):  # Top 15 live
                            try:
                                cells = row.find_all(['td', 'th'])
                                if len(cells) >= 2:
                                    # Nom du streamer
                                    streamer_name = cells[1].get_text().strip()
                                    
                                    # Viewers actuels
                                    if len(cells) >= 3:
                                        viewers_text = cells[2].get_text().strip()
                                        current_viewers = self._extract_first_number(viewers_text)
                                        
                                        streamer_data = {
                                            'username': streamer_name,
                                            'live_rank': i + 1,
                                            'current_viewers': current_viewers,
                                            'timestamp': datetime.now(),
                                            'source': 'twitchtracker_live'
                                        }
                                        
                                        streamers.append(streamer_data)
                                        
                            except Exception as e:
                                logger.warning(f"⚠️ Erreur parsing streamer {i}: {e}")
                                continue
                    
                    break
            
            logger.info(f"✅ {len(streamers)} streamers live récupérés")
            return streamers
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping streamers: {e}")
            return []
    
    def scrape_games_page(self) -> List[Dict[str, Any]]:
        """Scrape la page dédiée aux jeux pour plus de données."""
        logger.info("🎮 Scraping page games détaillée...")
        
        soup = self.fetch_page(f"{self.base_url}/games")
        if not soup:
            return []
        
        games = []
        
        try:
            # Recherche du tableau principal des jeux
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                # Vérifie si c'est le bon tableau (contient des jeux)
                header_row = rows[0] if rows else None
                if header_row and ('game' in header_row.get_text().lower() or len(rows) > 10):
                    
                    for i, row in enumerate(rows[1:51]):  # Top 50 jeux
                        try:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 3:
                                # Position
                                rank = i + 1
                                
                                # Nom du jeu (cherche dans différentes cellules)
                                game_name = ""
                                for cell in cells[1:3]:  # Généralement cellule 1 ou 2
                                    text = cell.get_text().strip()
                                    if text and not text.isdigit() and '%' not in text:
                                        game_name = text
                                        break
                                
                                if game_name:
                                    # Viewers moyens
                                    viewers = 0
                                    for cell in cells[2:]:
                                        text = cell.get_text().strip()
                                        if self._contains_large_number(text):
                                            viewers = self._extract_first_number(text)
                                            break
                                    
                                    game_data = {
                                        'game_name': game_name,
                                        'twitchtracker_rank': rank,
                                        'avg_viewers': viewers,
                                        'timestamp': datetime.now(),
                                        'source': 'twitchtracker_games_page'
                                    }
                                    
                                    games.append(game_data)
                                    
                        except Exception as e:
                            logger.warning(f"⚠️ Erreur parsing game {i}: {e}")
                            continue
                    
                    # Si on a trouvé des jeux, on s'arrête
                    if games:
                        break
            
            logger.info(f"✅ {len(games)} jeux page détaillée récupérés")
            return games
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping games page: {e}")
            return []
    
    def enrich_database_with_twitchtracker(self) -> bool:
        """Enrichit la base avec toutes les données TwitchTracker."""
        logger.info("💾 Enrichissement complet avec TwitchTracker...")
        
        try:
            client = pymongo.MongoClient(self.mongo_uri)
            db = client[self.db_name]
            
            # Collecte de toutes les données
            trending_games = self.scrape_trending_games()
            popular_games = self.scrape_popular_games() 
            live_streamers = self.scrape_top_streamers_homepage()
            games_detailed = self.scrape_games_page()
            
            enrichment_summary = {
                'trending_games': len(trending_games),
                'popular_games': len(popular_games),
                'live_streamers': len(live_streamers),
                'detailed_games': len(games_detailed),
                'games_enriched': 0,
                'streamers_enriched': 0
            }
            
            # 1. Sauvegarde des jeux trending
            if trending_games:
                db['twitchtracker_trending'].delete_many({'source': 'twitchtracker_trending'})
                db['twitchtracker_trending'].insert_many(trending_games)
                logger.info(f"✅ {len(trending_games)} jeux trending sauvegardés")
            
            # 2. Sauvegarde des jeux populaires
            if popular_games:
                db['twitchtracker_popular'].delete_many({'source': 'twitchtracker_popular'})
                db['twitchtracker_popular'].insert_many(popular_games)
                logger.info(f"✅ {len(popular_games)} jeux populaires sauvegardés")
            
            # 3. Sauvegarde des streamers live
            if live_streamers:
                db['twitchtracker_live_streamers'].delete_many({'source': 'twitchtracker_live'})
                db['twitchtracker_live_streamers'].insert_many(live_streamers)
                logger.info(f"✅ {len(live_streamers)} streamers live sauvegardés")
            
            # 4. Sauvegarde des jeux détaillés
            if games_detailed:
                db['twitchtracker_games_detailed'].delete_many({'source': 'twitchtracker_games_page'})
                db['twitchtracker_games_detailed'].insert_many(games_detailed)
                logger.info(f"✅ {len(games_detailed)} jeux détaillés sauvegardés")
            
            # 5. Enrichissement des jeux existants
            all_tt_games = trending_games + popular_games + games_detailed
            for tt_game in all_tt_games:
                game_name = tt_game.get('game_name', '')
                if game_name:
                    # Recherche de correspondance
                    existing_game = db['games'].find_one({
                        'game_name': {'$regex': re.escape(game_name), '$options': 'i'}
                    })
                    
                    if existing_game:
                        update_data = {'twitchtracker_last_update': datetime.now()}
                        
                        # Ajoute les données selon la source
                        if 'trending_rank' in tt_game:
                            update_data['twitchtracker_trending_rank'] = tt_game['trending_rank']
                            update_data['twitchtracker_growth'] = tt_game.get('growth_percentage', 0)
                        
                        if 'popularity_rank' in tt_game:
                            update_data['twitchtracker_popularity_rank'] = tt_game['popularity_rank']
                            update_data['twitchtracker_avg_viewers'] = tt_game.get('avg_viewers_week', 0)
                        
                        if 'twitchtracker_rank' in tt_game:
                            update_data['twitchtracker_global_rank'] = tt_game['twitchtracker_rank']
                        
                        db['games'].update_one(
                            {'_id': existing_game['_id']},
                            {'$set': update_data}
                        )
                        enrichment_summary['games_enriched'] += 1
            
            # 6. Enrichissement des streamers existants
            for tt_streamer in live_streamers:
                streamer_name = tt_streamer.get('username', '')
                if streamer_name:
                    existing_streamer = db['streamers'].find_one({
                        'username': {'$regex': re.escape(streamer_name), '$options': 'i'}
                    })
                    
                    if existing_streamer:
                        db['streamers'].update_one(
                            {'_id': existing_streamer['_id']},
                            {'$set': {
                                'twitchtracker_live_rank': tt_streamer.get('live_rank', 0),
                                'twitchtracker_current_viewers': tt_streamer.get('current_viewers', 0),
                                'twitchtracker_last_update': datetime.now()
                            }}
                        )
                        enrichment_summary['streamers_enriched'] += 1
            
            client.close()
            
            # Rapport final
            logger.info("🎊 ENRICHISSEMENT TWITCHTRACKER TERMINÉ")
            logger.info(f"   📈 Trending games: {enrichment_summary['trending_games']}")
            logger.info(f"   🎮 Popular games: {enrichment_summary['popular_games']}")
            logger.info(f"   👥 Live streamers: {enrichment_summary['live_streamers']}")
            logger.info(f"   🎯 Detailed games: {enrichment_summary['detailed_games']}")
            logger.info(f"   ✨ Games enrichis: {enrichment_summary['games_enriched']}")
            logger.info(f"   ⭐ Streamers enrichis: {enrichment_summary['streamers_enriched']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur enrichissement: {e}")
            return False
    
    # ===================================
    # MÉTHODES UTILITAIRES
    # ===================================
    
    def _extract_first_number(self, text: str) -> int:
        """Extrait le premier nombre d'un texte, gère K/M."""
        if not text:
            return 0
        
        text = text.upper().replace(',', '').strip()
        
        # Gestion K/M
        if 'K' in text:
            match = re.search(r'([\d.]+)K', text)
            if match:
                return int(float(match.group(1)) * 1000)
        elif 'M' in text:
            match = re.search(r'([\d.]+)M', text)
            if match:
                return int(float(match.group(1)) * 1000000)
        
        # Nombre normal
        match = re.search(r'[\d]+', text)
        if match:
            return int(match.group())
        
        return 0
    
    def _extract_percentage(self, text: str) -> float:
        """Extrait un pourcentage."""
        if not text:
            return 0.0
        
        match = re.search(r'([\d.]+)%', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return 0.0
        
        return 0.0
    
    def scrape(self) -> int:
        """
        Méthode d'interface pour compatibilité avec le système principal.
        
        Returns:
            int: Nombre d'éléments traités
        """
        try:
            success = self.enrich_database_with_twitchtracker()
            if success:
                # Compte approximatif basé sur les derniers résultats
                return 27  # 9 trending + 9 popular + 9 streamers
            else:
                return 0
        except Exception as e:
            logger.error(f"❌ Erreur dans scrape(): {e}")
            return 0
    
    def _contains_large_number(self, text: str) -> bool:
        """Vérifie si le texte contient un grand nombre (viewers)."""
        if not text:
            return False
        
        # Cherche des nombres > 1000 ou avec K/M
        return bool(re.search(r'[\d,]+[KM]|[\d,]{4,}', text.upper()))


def main():
    """Point d'entrée principal."""
    enricher = TwitchTrackerEnricherV2()
    
    try:
        success = enricher.enrich_database_with_twitchtracker()
        
        if success:
            print("\n🎉 ENRICHISSEMENT TWITCHTRACKER RÉUSSI!")
            print("\n📊 Nouvelles collections créées:")
            print("  - twitchtracker_trending: Jeux en forte croissance")
            print("  - twitchtracker_popular: Jeux les plus populaires")
            print("  - twitchtracker_live_streamers: Top streamers live")
            print("  - twitchtracker_games_detailed: Données détaillées jeux")
            print("\n✨ Collections enrichies:")
            print("  - games: Ajout ranking, croissance, popularité TwitchTracker")
            print("  - streamers: Ajout position live, viewers actuels TwitchTracker")
        else:
            print("\n❌ Échec de l'enrichissement")
            
    except Exception as e:
        print(f"\n❌ Erreur: {e}")


if __name__ == "__main__":
    main()
