"""
Scraper pour les événements gaming et actualités eSports.

Ce module scrape les événements gaming depuis Liquipedia et autres sources
pour croiser avec les données de viewers Twitch.

Auteurs: Hicham, Aya, Boubaker
Date: Juillet 2025
"""

import time
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
import json

from ..database.mongodb_manager import db_manager

# Configuration du logger
logger = logging.getLogger(__name__)


class EventsScraper:
    """
    Scraper pour les événements gaming et actualités eSports.
    """
    
    def __init__(self):
        """Initialise le scraper d'événements."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        })
        logger.info("🗓️ Scraper événements initialisé")
    
    def scrape_liquipedia_events(self) -> List[Dict]:
        """
        Scrape les événements depuis Liquipedia.
        
        Returns:
            List[Dict]: Liste des événements
        """
        try:
            logger.info("🏆 Scraping événements Liquipedia...")
            
            events = []
            
            # URLs des principales pages d'événements
            urls = [
                "https://liquipedia.net/leagueoflegends/Main_Page",
                "https://liquipedia.net/valorant/Main_Page",
                "https://liquipedia.net/counterstrike/Main_Page"
            ]
            
            for url in urls:
                try:
                    response = self.session.get(url, timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Recherche des événements en cours et à venir
                    event_sections = soup.find_all(['div', 'section'], class_=re.compile(r'(tournament|event|match)', re.I))
                    
                    for section in event_sections[:5]:  # Limite à 5 événements par page
                        event_data = self._extract_event_data(section, url)
                        if event_data:
                            events.append(event_data)
                    
                    time.sleep(2)  # Respect du rate limiting
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erreur scraping {url}: {e}")
                    continue
            
            logger.info(f"✅ {len(events)} événements Liquipedia trouvés")
            return events
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping Liquipedia: {e}")
            return []
    
    def scrape_gaming_news(self) -> List[Dict]:
        """
        Scrape les actualités gaming depuis plusieurs sources.
        
        Returns:
            List[Dict]: Liste des actualités
        """
        try:
            logger.info("📰 Scraping actualités gaming...")
            
            news = []
            
            # Sources d'actualités gaming
            news_sources = [
                {
                    'url': 'https://www.jeuxvideo.com/news/',
                    'name': 'JeuxVideo.com',
                    'selector': '.news-item'
                },
                {
                    'url': 'https://www.gamekult.com/actualite/',
                    'name': 'Gamekult',
                    'selector': '.news-item'
                }
            ]
            
            for source in news_sources:
                try:
                    response = self.session.get(source['url'], timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Recherche des articles de news
                    articles = soup.find_all(['article', 'div'], class_=re.compile(r'(news|article|post)', re.I))
                    
                    for article in articles[:3]:  # 3 articles par source
                        news_data = self._extract_news_data(article, source)
                        if news_data:
                            news.append(news_data)
                    
                    time.sleep(2)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erreur scraping {source['name']}: {e}")
                    continue
            
            logger.info(f"✅ {len(news)} actualités trouvées")
            return news
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping actualités: {e}")
            return []
    
    def _extract_event_data(self, section, source_url: str) -> Optional[Dict]:
        """
        Extrait les données d'un événement depuis un élément HTML.
        
        Args:
            section: Élément BeautifulSoup
            source_url: URL de la source
            
        Returns:
            Optional[Dict]: Données de l'événement ou None
        """
        try:
            # Extraction du titre
            title_elem = section.find(['h1', 'h2', 'h3', 'h4'], text=re.compile(r'.+'))
            if not title_elem:
                title_elem = section.find('a', text=re.compile(r'.+'))
            
            title = title_elem.get_text(strip=True) if title_elem else "Événement"
            
            # Extraction des dates (si disponibles)
            date_elem = section.find(string=re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'))
            event_date = datetime.now()
            if date_elem:
                try:
                    # Parsing basique de date
                    date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', str(date_elem))
                    if date_match:
                        day, month, year = date_match.groups()
                        if len(year) == 2:
                            year = "20" + year
                        event_date = datetime(int(year), int(month), int(day))
                except:
                    pass
            
            # Détermination du jeu basée sur l'URL
            game = "Unknown"
            if "leagueoflegends" in source_url:
                game = "League of Legends"
            elif "valorant" in source_url:
                game = "Valorant"
            elif "counterstrike" in source_url:
                game = "Counter-Strike"
            
            return {
                'title': title,
                'game': game,
                'event_date': event_date,
                'source': source_url,
                'type': 'tournament',
                'scraped_at': datetime.now(),
                'impact_score': self._calculate_impact_score(title, game)
            }
            
        except Exception as e:
            logger.debug(f"Erreur extraction événement: {e}")
            return None
    
    def _extract_news_data(self, article, source: Dict) -> Optional[Dict]:
        """
        Extrait les données d'une actualité depuis un élément HTML.
        
        Args:
            article: Élément BeautifulSoup
            source: Dictionnaire source
            
        Returns:
            Optional[Dict]: Données de l'actualité ou None
        """
        try:
            # Extraction du titre
            title_elem = article.find(['h1', 'h2', 'h3', 'a'])
            title = title_elem.get_text(strip=True) if title_elem else "Actualité"
            
            # Extraction du contenu/description
            content_elem = article.find(['p', 'div'], class_=re.compile(r'(desc|content|summary)', re.I))
            content = content_elem.get_text(strip=True)[:200] if content_elem else ""
            
            # Détermination du jeu mentionné
            game = self._detect_game_in_text(title + " " + content)
            
            return {
                'title': title,
                'content': content,
                'game': game,
                'source': source['name'],
                'type': 'news',
                'scraped_at': datetime.now(),
                'impact_score': self._calculate_impact_score(title, game)
            }
            
        except Exception as e:
            logger.debug(f"Erreur extraction actualité: {e}")
            return None
    
    def _detect_game_in_text(self, text: str) -> str:
        """
        Détecte le jeu mentionné dans un texte.
        
        Args:
            text: Texte à analyser
            
        Returns:
            str: Nom du jeu détecté
        """
        text_lower = text.lower()
        
        game_keywords = {
            'League of Legends': ['league of legends', 'lol', 'riot games'],
            'Valorant': ['valorant', 'val'],
            'Counter-Strike': ['counter-strike', 'cs:go', 'cs2'],
            'Fortnite': ['fortnite', 'epic games'],
            'Apex Legends': ['apex legends', 'apex'],
            'Call of Duty': ['call of duty', 'cod', 'warzone']
        }
        
        for game, keywords in game_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return game
        
        return "General Gaming"
    
    def _calculate_impact_score(self, title: str, game: str) -> float:
        """
        Calcule un score d'impact pour un événement/actualité.
        
        Args:
            title: Titre de l'événement
            game: Jeu concerné
            
        Returns:
            float: Score d'impact (0-10)
        """
        score = 5.0  # Score de base
        
        title_lower = title.lower()
        
        # Mots clés augmentant l'impact
        high_impact_words = ['championship', 'tournament', 'final', 'world', 'major', 'update', 'release']
        for word in high_impact_words:
            if word in title_lower:
                score += 1.5
        
        # Jeux populaires ont plus d'impact
        popular_games = ['League of Legends', 'Valorant', 'Counter-Strike']
        if game in popular_games:
            score += 1.0
        
        return min(10.0, score)
    
    def collect_all_events_data(self) -> int:
        """
        Collecte toutes les données d'événements et actualités.
        
        Returns:
            int: Nombre total d'éléments collectés
        """
        try:
            logger.info("🚀 Début collecte événements et actualités")
            
            total_collected = 0
            
            # Collecte des événements Liquipedia
            events = self.scrape_liquipedia_events()
            for event in events:
                if db_manager.insert_event_data(event):
                    total_collected += 1
            
            # Collecte des actualités gaming
            news = self.scrape_gaming_news()
            for article in news:
                if db_manager.insert_event_data(article):
                    total_collected += 1
            
            logger.info(f"🎉 Collecte terminée: {total_collected} événements/actualités collectés")
            return total_collected
            
        except Exception as e:
            logger.error(f"❌ Erreur collecte événements: {e}")
            return 0
    
    def __del__(self):
        """Nettoyage des ressources."""
        if hasattr(self, 'session'):
            self.session.close()


# Instance globale
events_scraper = EventsScraper()
