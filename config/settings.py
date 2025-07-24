"""
Configuration principale du projet Twitch Trends Tracker.

Ce module contient toutes les configurations nécessaires pour le bon fonctionnement
de l'application, incluant les paramètres de base de données, les URLs de scraping,
et les configurations du dashboard.

Auteur: Équipe Twitch Trends Tracker
Date: 24 juillet 2025
Version: 2.0.0
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

# Configuration de base
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
DOCS_DIR = PROJECT_ROOT / "docs"

# Création des dossiers s'ils n'existent pas
for directory in [DATA_DIR, LOGS_DIR, DOCS_DIR]:
    directory.mkdir(exist_ok=True)

@dataclass
class DatabaseConfig:
    """Configuration pour MongoDB."""
    host: str = "localhost"
    port: int = 27017
    database_name: str = "twitch_trends"
    connection_timeout: int = 5000
    
    @property
    def connection_string(self) -> str:
        """Retourne la chaîne de connexion MongoDB."""
        return f"mongodb://{self.host}:{self.port}/"

@dataclass
class ScrapingConfig:
    """Configuration pour les scrapers."""
    # URLs de base pour le scraping
    twitch_games_url: str = "https://twitchtracker.com/games"
    events_sources: List[str] = field(default_factory=list)
    streamers_sources: List[str] = field(default_factory=list)
    
    # Configuration des délais
    request_delay: float = 1.0  # Délai entre les requêtes (secondes)
    timeout: int = 30  # Timeout des requêtes (secondes)
    retry_attempts: int = 3  # Nombre de tentatives en cas d'échec
    
    # Configuration Selenium
    headless_mode: bool = True
    window_size: str = "1920,1080"
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    
    def __post_init__(self):
        """Initialise les listes par défaut."""
        if not self.events_sources:
            self.events_sources = [
                "https://liquipedia.net/counterstrike/Main_Page",
                "https://liquipedia.net/leagueoflegends/Main_Page"
            ]
        
        if not self.streamers_sources:
            self.streamers_sources = [
                "https://twitchtracker.com/channels/viewership?lang=fr"
            ]

@dataclass
class DashboardConfig:
    """Configuration pour le dashboard Streamlit."""
    title: str = "🎮 Twitch Trends Tracker"
    icon: str = "🎮"
    layout: str = "wide"
    initial_sidebar_state: str = "expanded"
    
    # Configuration du cache
    cache_ttl: int = 30  # Durée de vie du cache en secondes
    
    # Configuration des métriques
    default_top_count: int = 10  # Nombre d'éléments à afficher par défaut
    
    # Configuration des graphiques
    chart_height: int = 500
    color_schemes: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialise les schémas de couleurs par défaut."""
        if not self.color_schemes:
            self.color_schemes = {
                "games": "viridis",
                "streamers": "plasma",
                "events": "cividis"
            }

@dataclass
class LoggingConfig:
    """Configuration pour les logs."""
    level: str = "INFO"
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Path = LOGS_DIR / "twitch_tracker.log"
    max_file_size: int = 10_000_000  # 10MB
    backup_count: int = 5

@dataclass
class ExportConfig:
    """Configuration pour les exports de données."""
    BASE_EXPORT_DIR: Path = DATA_DIR / "exports"
    CSV_PREFIX: str = "twitch_trends_games"
    JSON_PREFIX: str = "twitch_trends_data"
    FILE_ENCODING: str = "utf-8"
    
    def __post_init__(self):
        """Crée le dossier d'export s'il n'existe pas."""
        self.BASE_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

class Config:
    """Configuration principale de l'application."""
    
    def __init__(self):
        """Initialise la configuration."""
        self.database = DatabaseConfig()
        self.scraping = ScrapingConfig()
        self.dashboard = DashboardConfig()
        self.logging = LoggingConfig()
        self.export = ExportConfig()
        
        # Variables d'environnement
        self._load_environment_variables()
    
    def _load_environment_variables(self) -> None:
        """Charge les variables d'environnement si elles existent."""
        # Configuration de la base de données
        mongodb_host = os.getenv("MONGODB_HOST")
        if mongodb_host:
            self.database.host = mongodb_host
            
        mongodb_port = os.getenv("MONGODB_PORT")
        if mongodb_port:
            self.database.port = int(mongodb_port)
            
        mongodb_db = os.getenv("MONGODB_DATABASE")
        if mongodb_db:
            self.database.database_name = mongodb_db
        
        # Configuration du scraping
        scraping_headless = os.getenv("SCRAPING_HEADLESS")
        if scraping_headless:
            self.scraping.headless_mode = scraping_headless.lower() == "true"
            
        scraping_delay = os.getenv("SCRAPING_DELAY")
        if scraping_delay:
            self.scraping.request_delay = float(scraping_delay)
    
    def get_collections(self) -> Dict[str, str]:
        """Retourne la liste des collections MongoDB utilisées."""
        return {
            "games": "games",
            "events": "events",
            "streamers": "streamers",
            "logs": "scraping_logs"
        }
    
    def get_export_paths(self) -> Dict[str, Path]:
        """Retourne les chemins d'export pour les différents formats."""
        return {
            "csv": DATA_DIR / "exports" / "csv",
            "json": DATA_DIR / "exports" / "json",
            "reports": DATA_DIR / "reports"
        }
    
    def validate(self) -> bool:
        """Valide la configuration."""
        try:
            # Vérification des dossiers nécessaires
            for path in [DATA_DIR, LOGS_DIR, DOCS_DIR]:
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
            
            # Vérification des paramètres critiques
            assert self.database.host is not None, "Host MongoDB requis"
            assert self.database.port > 0, "Port MongoDB invalide"
            assert self.scraping.request_delay >= 0, "Délai de requête invalide"
            
            return True
        except Exception as e:
            print(f"❌ Erreur de validation de la configuration: {e}")
            return False

# Instance globale de la configuration
config = Config()

# Export des configurations principales pour faciliter l'import
__all__ = [
    "config",
    "DatabaseConfig",
    "ScrapingConfig", 
    "DashboardConfig",
    "LoggingConfig",
    "Config",
    "PROJECT_ROOT",
    "DATA_DIR",
    "LOGS_DIR",
    "DOCS_DIR"
]
