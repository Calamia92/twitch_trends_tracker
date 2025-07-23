"""
Module de scraping Twitch - Version refactorisée et modulaire.

Ce module contient la logique de scraping principal conforme aux exigences PDF:
- Framework Selenium autorisé
- Gestion d'exceptions complète
- Traitement temps réel avec injection MongoDB
- Export automatique CSV/JSON
- Pipeline de traitement et nettoyage

Auteurs: Hicham, Aya, Boubaker
Date: Juillet 2025
"""

import sys
import os
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

# Ajout du path pour les imports relatifs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    WebDriverException,
    ElementNotInteractableException
)
from webdriver_manager.chrome import ChromeDriverManager

from config.settings import config
from src.database.mongodb_manager import db_manager
from src.utils.data_utils import parser, validator
from src.utils.export_manager import ExportManager

# Configuration du logging
logging.basicConfig(
    level=getattr(logging, config.logging.LOG_LEVEL),
    format=config.logging.LOG_FORMAT
)
logger = logging.getLogger(__name__)


class TwitchScraper:
    """
    Scraper principal pour TwitchTracker avec architecture modulaire.
    
    Cette classe implémente tous les requis du PDF:
    - Utilisation du framework Selenium autorisé
    - Gestion complète des exceptions
    - Traitement temps réel des données
    - Pipeline de transformation et nettoyage
    - Export automatique en CSV/JSON
    """
    
    def __init__(self):
        """Initialise le scraper avec la configuration."""
        self.driver: Optional[webdriver.Chrome] = None
        self.export_manager = ExportManager()
        self.scraped_data: List[Dict[str, Any]] = []
        
        logger.info("🚀 Initialisation du TwitchScraper")
    
    def _setup_driver(self) -> bool:
        """
        Configure et initialise le driver Chrome.
        
        Returns:
            bool: True si le driver est configuré avec succès
        """
        try:
            # Configuration des options Chrome
            options = Options()
            
            # Options pour performance et stabilité
            chrome_options = [
                "--headless=new",
                "--disable-gpu", 
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--window-size=1920,1080",
                f"--user-agent={config.scraping.USER_AGENT}"
            ]
            
            for option in chrome_options:
                options.add_argument(option)
            
            # Gestion automatique du ChromeDriver via webdriver-manager
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                logger.info("✅ ChromeDriver configuré automatiquement")
            except Exception as e:
                logger.warning(f"⚠️ Erreur webdriver-manager: {e}")
                # Fallback vers driver système
                self.driver = webdriver.Chrome(options=options)
                logger.info("✅ Driver Chrome système utilisé")
            
            # Configuration des timeouts
            self.driver.set_page_load_timeout(config.scraping.PAGE_LOAD_TIMEOUT)
            self.driver.implicitly_wait(config.scraping.ELEMENT_WAIT_TIMEOUT)
            
            return True
            
        except WebDriverException as e:
            logger.error(f"❌ Erreur configuration ChromeDriver: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur inattendue driver: {e}")
            return False
    
    def _navigate_to_page(self) -> bool:
        """
        Navigue vers la page cible avec gestion d'erreurs.
        
        Returns:
            bool: True si la navigation réussit
        """
        if not self.driver:
            logger.error("❌ Driver non initialisé")
            return False
        
        try:
            logger.info(f"🌐 Navigation vers {config.scraping.TARGET_URL}")
            self.driver.get(config.scraping.TARGET_URL)
            
            # Attente que la page soit complètement chargée
            WebDriverWait(self.driver, config.scraping.ELEMENT_WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ri-name"))
            )
            
            logger.info("✅ Page chargée avec succès")
            return True
            
        except TimeoutException:
            logger.error("❌ Timeout lors du chargement de la page")
            return False
        except WebDriverException as e:
            logger.error(f"❌ Erreur navigation: {e}")
            return False
    
    def _extract_game_data(self, row_element) -> Optional[Dict[str, Any]]:
        """
        Extrait les données d'un jeu depuis un élément de ligne.
        
        Args:
            row_element: Élément Selenium représentant une ligne de jeu
            
        Returns:
            Optional[Dict]: Données du jeu ou None si erreur
        """
        try:
            # Extraction du titre
            title_element = row_element.find_element(By.CLASS_NAME, "ri-name")
            title = title_element.text.strip()
            
            if not title:
                logger.warning("⚠️ Titre vide trouvé, élément ignoré")
                return None
            
            # Extraction de l'image
            try:
                image_element = row_element.find_element(By.CLASS_NAME, "ri-image")
                img_tag = image_element.find_element(By.TAG_NAME, "img")
                image_url = img_tag.get_attribute("src") or img_tag.get_attribute("data-src")
            except NoSuchElementException:
                logger.warning(f"⚠️ Image non trouvée pour {title}")
                image_url = ""
            
            # Extraction du nombre de viewers
            try:
                viewers_element = row_element.find_element(By.CLASS_NAME, "ri-value")
                viewers_text = viewers_element.text.strip()
                viewers = parser.parse_number(viewers_text)
            except NoSuchElementException:
                logger.warning(f"⚠️ Viewers non trouvés pour {title}")
                viewers = 0
            
            # Extraction du changement (optionnel)
            change = None
            try:
                change_container = row_element.find_element(By.CLASS_NAME, "ri-change")
                change_elements = change_container.find_elements(By.CLASS_NAME, "to-number-lg")
                if change_elements:
                    change_text = change_elements[0].text.strip()
                    change = parser.parse_percentage(change_text)
            except NoSuchElementException:
                logger.debug(f"🔍 Changement non trouvé pour {title}")
            
            # Extraction de la part de marché (optionnel)
            share = None
            try:
                share_element = row_element.find_element(By.CLASS_NAME, "ri-share")
                share_text = share_element.get_attribute("textContent").strip()
                if share_text and '%' in share_text:
                    share = parser.parse_percentage(share_text)
            except NoSuchElementException:
                logger.debug(f"🔍 Share non trouvé pour {title}")
            
            # Construction des données brutes
            raw_data = {
                "title": title,
                "image_url": image_url,
                "viewers": viewers,
                "change": change,
                "share": share,
                "scraped_at": datetime.now().isoformat()
            }
            
            return raw_data
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction données: {e}")
            return None
    
    def _process_game_item(self, raw_data: Dict[str, Any]) -> bool:
        """
        Traite un item de jeu: validation, nettoyage et sauvegarde immédiate.
        
        Args:
            raw_data: Données brutes extraites
            
        Returns:
            bool: True si le traitement réussit
        """
        try:
            # Pipeline de traitement et nettoyage (exigence PDF)
            cleaned_data = validator.sanitize_game_data(raw_data)
            
            # Validation des données nettoyées
            is_valid, errors = validator.validate_game_data(cleaned_data)
            
            if not is_valid:
                logger.warning(f"⚠️ Données invalides pour {cleaned_data.get('title', 'Inconnu')}: {errors}")
                return False
            
            # Injection immédiate en base de données (exigence PDF)
            success = db_manager.insert_game_data(cleaned_data)
            
            if success:
                # Ajout aux données pour export
                self.scraped_data.append(cleaned_data)
                logger.info(f"✅ Traité: {cleaned_data['title']} ({cleaned_data['viewers']:,} viewers)")
                return True
            else:
                logger.error(f"❌ Échec sauvegarde: {cleaned_data['title']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur traitement item: {e}")
            return False
    
    def _scrape_games_list(self) -> List[Dict[str, Any]]:
        """
        Scrape la liste complète des jeux avec traitement temps réel.
        
        Returns:
            List[Dict]: Liste des jeux scrapés
        """
        if not self.driver:
            logger.error("❌ Driver non disponible")
            return []
        
        scraped_games = []
        
        try:
            # Recherche de tous les éléments de jeu
            game_rows = self.driver.find_elements(By.CSS_SELECTOR, ".data-table tbody tr")
            
            if not game_rows:
                logger.warning("⚠️ Aucune ligne de jeu trouvée")
                return []
            
            logger.info(f"🎮 {len(game_rows)} jeux détectés, traitement en cours...")
            
            # Traitement de chaque jeu en temps réel
            for i, row in enumerate(game_rows, 1):
                try:
                    # Délai de politesse entre les requêtes
                    if i > 1:
                        time.sleep(config.scraping.REQUEST_DELAY)
                    
                    # Extraction des données
                    raw_data = self._extract_game_data(row)
                    
                    if raw_data:
                        # Traitement immédiat (exigence PDF)
                        if self._process_game_item(raw_data):
                            scraped_games.append(raw_data)
                    
                    # Logging de progression
                    if i % 10 == 0:
                        logger.info(f"📊 Progression: {i}/{len(game_rows)} jeux traités")
                        
                except Exception as e:
                    logger.error(f"❌ Erreur ligne {i}: {e}")
                    continue
            
            logger.info(f"✅ Scraping terminé: {len(scraped_games)} jeux récupérés")
            return scraped_games
            
        except NoSuchElementException:
            logger.error("❌ Structure de page non reconnue")
            return []
        except Exception as e:
            logger.error(f"❌ Erreur scraping: {e}")
            return []
    
    def scrape_with_retry(self, max_retries: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Exécute le scraping avec système de retry.
        
        Args:
            max_retries: Nombre maximum de tentatives
            
        Returns:
            List[Dict]: Données scrapées
        """
        if max_retries is None:
            max_retries = config.scraping.MAX_RETRIES
        
        last_exception = None
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔄 Tentative {attempt}/{max_retries}")
                
                # Configuration du driver
                if not self._setup_driver():
                    raise WebDriverException("Échec configuration driver")
                
                # Navigation
                if not self._navigate_to_page():
                    raise WebDriverException("Échec navigation")
                
                # Scraping principal
                games_data = self._scrape_games_list()
                
                if games_data:
                    logger.info(f"🎉 Scraping réussi: {len(games_data)} jeux")
                    return games_data
                else:
                    raise Exception("Aucune donnée récupérée")
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"⚠️ Tentative {attempt} échouée: {e}")
                
                if attempt < max_retries:
                    logger.info(f"⏳ Nouvelle tentative dans {config.scraping.RETRY_DELAY}s...")
                    time.sleep(config.scraping.RETRY_DELAY)
                
            finally:
                self._cleanup()
        
        # Toutes les tentatives ont échoué
        logger.error(f"❌ Scraping échoué après {max_retries} tentatives")
        if last_exception:
            raise last_exception
        
        return []
    
    def export_data(self) -> bool:
        """
        Exporte les données scrapées vers CSV et JSON (exigence PDF).
        
        Returns:
            bool: True si l'export réussit
        """
        if not self.scraped_data:
            logger.warning("⚠️ Aucune donnée à exporter")
            return False
        
        try:
            # Export CSV (exigence PDF)
            csv_success = self.export_manager.export_to_csv(self.scraped_data)
            
            # Export JSON (exigence PDF)
            json_success = self.export_manager.export_to_json(self.scraped_data)
            
            if csv_success and json_success:
                logger.info("✅ Export CSV et JSON réussi")
                return True
            else:
                logger.warning("⚠️ Export partiel réussi")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur export: {e}")
            return False
    
    def _cleanup(self):
        """Nettoie les ressources utilisées."""
        if self.driver:
            try:
                self.driver.quit()
                logger.debug("🧹 Driver nettoyé")
            except Exception as e:
                logger.warning(f"⚠️ Erreur nettoyage driver: {e}")
            finally:
                self.driver = None
    
    def __enter__(self):
        """Support du context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Nettoyage automatique à la sortie du context manager."""
        self._cleanup()


def main():
    """
    Fonction principale pour exécution en standalone.
    
    Implémente le pipeline complet conforme aux exigences PDF:
    1. Scraping avec gestion d'exceptions
    2. Traitement temps réel avec injection MongoDB
    3. Export automatique CSV/JSON
    """
    logger.info("🎮 === TWITCH TRENDS TRACKER - SCRAPER ===")
    logger.info("👥 Auteurs: Hicham, Aya, Boubaker")
    logger.info("📅 Version: Juillet 2025")
    
    try:
        # Vérification de la connexion base de données
        if not db_manager.is_connected():
            logger.error("❌ Pas de connexion à MongoDB. Vérifiez votre configuration.")
            return
        
        # Exécution du scraping avec context manager
        with TwitchScraper() as scraper:
            # Scraping avec retry automatique
            games_data = scraper.scrape_with_retry()
            
            if games_data:
                # Export automatique (exigence PDF)
                scraper.export_data()
                
                # Statistiques finales
                logger.info(f"📊 === RÉSULTATS ===")
                logger.info(f"🎮 Jeux scrapés: {len(games_data)}")
                logger.info(f"💾 Données en base: {db_manager.get_database_stats().get('total_games', 0)}")
                logger.info("✅ Scraping terminé avec succès")
            else:
                logger.error("❌ Aucune donnée récupérée")
                
    except KeyboardInterrupt:
        logger.info("⏹️ Scraping interrompu par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
    finally:
        # Fermeture propre de la connexion base
        db_manager.close_connection()


if __name__ == "__main__":
    main()
