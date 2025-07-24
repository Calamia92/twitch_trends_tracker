"""
Configuration globale du projet Twitch Trends Tracker.

Ce module centralise toutes les configurations et paramètres
utilisés dans l'application.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class DatabaseConfig:
    """Configuration de la base de données MongoDB."""
    MONGODB_URI: str = "mongodb://localhost:27017/"
    DATABASE_NAME: str = "twitch_trends"
    COLLECTION_NAME: str = "games"
    CONNECTION_TIMEOUT: int = 5000


@dataclass
class LoggingConfig:
    """Configuration du logging."""
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class ScrapingConfig:
    """Configuration pour le scraping."""
    CHROME_OPTIONS: list = None
    IMPLICIT_WAIT: int = 10
    PAGE_LOAD_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2
    USER_AGENTS: list = None
    USER_AGENT: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    ELEMENT_WAIT_TIMEOUT: int = 10
    TARGET_URL: str = "https://www.twitch.tv/directory"
    REQUEST_DELAY: int = 2
    
    def __post_init__(self):
        if self.CHROME_OPTIONS is None:
            self.CHROME_OPTIONS = [
                "--headless",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1920,1080",
                "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            ]
        
        if self.USER_AGENTS is None:
            self.USER_AGENTS = [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]


@dataclass
class StreamlitConfig:
    """Configuration de l'interface Streamlit."""
    PAGE_TITLE: str = "🎮 Twitch Trends Tracker"
    PAGE_ICON: str = "🎮"
    LAYOUT: str = "wide"
    INITIAL_SIDEBAR_STATE: str = "expanded"


@dataclass
class AppConfig:
    """Configuration principale de l'application."""
    # Sous-configurations
    database: DatabaseConfig
    scraping: ScrapingConfig
    streamlit: StreamlitConfig
    logging: LoggingConfig
    
    # Configuration générale
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    DATA_REFRESH_INTERVAL: int = 300  # 5 minutes
    
    # URLs et endpoints
    TWITCH_URL: str = "https://www.twitch.tv/directory"
    LIQUIPEDIA_URL: str = "https://liquipedia.net"
    TWITCHTRACKER_URL: str = "https://twitchtracker.com"
    
    # Limites de scraping
    MAX_GAMES_TO_SCRAPE: int = 20
    MAX_STREAMERS_TO_SCRAPE: int = 20
    MAX_EVENTS_TO_SCRAPE: int = 50
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.scraping = ScrapingConfig()
        self.streamlit = StreamlitConfig()
        self.logging = LoggingConfig()


# Instance globale de configuration
config = AppConfig()


def get_config() -> AppConfig:
    """
    Retourne l'instance de configuration globale.
    
    Returns:
        AppConfig: Instance de configuration
    """
    return config


def update_config(**kwargs) -> None:
    """
    Met à jour la configuration avec de nouveaux paramètres.
    
    Args:
        **kwargs: Paramètres à mettre à jour
    """
    global config
    
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)


def get_environment_config() -> Dict[str, Any]:
    """
    Récupère la configuration depuis les variables d'environnement.
    
    Returns:
        Dict: Configuration depuis l'environnement
    """
    env_config = {}
    
    # MongoDB
    if os.getenv('MONGODB_URI'):
        env_config['MONGODB_URI'] = os.getenv('MONGODB_URI')
    
    if os.getenv('DATABASE_NAME'):
        env_config['DATABASE_NAME'] = os.getenv('DATABASE_NAME')
    
    # Debug
    if os.getenv('DEBUG'):
        env_config['DEBUG'] = os.getenv('DEBUG').lower() == 'true'
    
    # Log level
    if os.getenv('LOG_LEVEL'):
        env_config['LOG_LEVEL'] = os.getenv('LOG_LEVEL')
    
    return env_config


# Application de la configuration d'environnement au démarrage
def apply_environment_config():
    """Applique la configuration d'environnement."""
    env_config = get_environment_config()
    
    if env_config:
        print(f"📝 Configuration d'environnement appliquée: {list(env_config.keys())}")
        
        # Application des configurations de base de données
        if 'MONGODB_URI' in env_config:
            config.database.MONGODB_URI = env_config['MONGODB_URI']
        
        if 'DATABASE_NAME' in env_config:
            config.database.DATABASE_NAME = env_config['DATABASE_NAME']
        
        # Application des configurations générales
        if 'DEBUG' in env_config:
            config.DEBUG = env_config['DEBUG']
        
        if 'LOG_LEVEL' in env_config:
            config.LOG_LEVEL = env_config['LOG_LEVEL']


# Application automatique au chargement du module
apply_environment_config()
