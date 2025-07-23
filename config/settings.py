"""
Configuration centralisée pour le projet Twitch Trends Tracker.

Ce module contient tous les paramètres de configuration de l'application,
organisés de manière claire et modulaire pour faciliter la maintenance.

Auteurs: Hicham, Aya, Boubaker
Date: Juillet 2025
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Chargement des variables d'environnement
load_dotenv(override=True)  # Force override des variables existantes

class DatabaseConfig:
    """Configuration de la base de données MongoDB."""
    
    # URI de connexion MongoDB
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    
    # Nom de la base de données
    DATABASE_NAME = "twitch_tracker"
    
    # Nom de la collection principale
    COLLECTION_NAME = "top_games"
    
    # Timeout de connexion (secondes)
    CONNECTION_TIMEOUT = 10000


class ScrapingConfig:
    """Configuration du scraping web."""
    
    # URL cible pour le scraping
    TARGET_URL = "https://twitchtracker.com/games"
    
    # Timeouts Selenium (secondes)
    PAGE_LOAD_TIMEOUT = 20
    ELEMENT_WAIT_TIMEOUT = 15
    
    # Options de retry
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    
    # Délai entre les requêtes (politesse)
    REQUEST_DELAY = 1
    
    # User-Agent pour éviter la détection
    USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )


class ExportConfig:
    """Configuration des exports de données."""
    
    # Répertoire de base pour les exports
    BASE_EXPORT_DIR = Path(__file__).parent.parent / "data"
    
    # Formats d'export supportés
    SUPPORTED_FORMATS = ["csv", "json"]
    
    # Préfixes des fichiers d'export
    CSV_PREFIX = "twitch_trends"
    JSON_PREFIX = "twitch_trends"
    
    # Encodage des fichiers
    FILE_ENCODING = "utf-8"


class DashboardConfig:
    """Configuration du dashboard Streamlit."""
    
    # Port par défaut
    DEFAULT_PORT = 8501
    
    # Titre de l'application
    APP_TITLE = "🎮 Twitch Trends Tracker"
    
    # Configuration du cache Streamlit (secondes)
    CACHE_TTL = 300  # 5 minutes
    
    # Nombre maximum d'éléments dans les graphiques
    MAX_CHART_ITEMS = 50
    
    # Thème de couleurs pour les graphiques
    COLOR_SCHEME = [
        "#9146ff",  # Violet Twitch
        "#f0f0ff",  # Violet clair
        "#6441a5",  # Violet foncé
        "#00f5ff",  # Cyan
        "#ff6b6b"   # Rouge
    ]


class LoggingConfig:
    """Configuration des logs."""
    
    # Niveau de log par défaut
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Format des messages de log
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Fichier de log
    LOG_FILE = Path(__file__).parent.parent / "logs" / "app.log"


class AutomationConfig:
    """Configuration de l'automatisation."""
    
    # Intervalle de scraping automatique (heures)
    SCRAPING_INTERVAL_HOURS = 1
    
    # Heure de démarrage du scraping quotidien
    DAILY_START_TIME = "09:00"
    
    # Heure d'arrêt du scraping quotidien
    DAILY_END_TIME = "23:00"
    
    # Jours de la semaine actifs (0=Lundi, 6=Dimanche)
    ACTIVE_WEEKDAYS = [0, 1, 2, 3, 4, 5, 6]  # Tous les jours


# Configuration globale - point d'accès unique
class Config:
    """Configuration principale regroupant tous les modules."""
    
    database = DatabaseConfig()
    scraping = ScrapingConfig()
    export = ExportConfig()
    dashboard = DashboardConfig()
    logging = LoggingConfig()
    automation = AutomationConfig()
    
    # Version de l'application
    VERSION = "2.0.0"
    
    # Mode debug
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    @classmethod
    def get_project_root(cls) -> Path:
        """Retourne la racine du projet."""
        return Path(__file__).parent.parent
    
    @classmethod
    def ensure_directories(cls):
        """Crée les répertoires nécessaires s'ils n'existent pas."""
        directories = [
            cls.export.BASE_EXPORT_DIR,
            cls.logging.LOG_FILE.parent,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Instance globale de configuration
config = Config()

# Création automatique des répertoires nécessaires
config.ensure_directories()
