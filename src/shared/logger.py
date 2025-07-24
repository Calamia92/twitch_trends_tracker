"""
Module de gestion centralisée des logs pour Twitch Trends Tracker.

Ce module configure et gère tous les logs de l'application avec différents niveaux
de détail et de sortie selon les besoins.

Auteur: Équipe Twitch Trends Tracker
Date: 24 juillet 2025
Version: 2.0.0
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import sys

from ..config.settings import config


class ColoredFormatter(logging.Formatter):
    """Formateur coloré pour les logs en console."""
    
    # Codes de couleur ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Vert
        'WARNING': '\033[33m',    # Jaune
        'ERROR': '\033[31m',      # Rouge
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """Formate le message avec des couleurs."""
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # Applique la couleur au niveau de log
        record.levelname = f"{log_color}{record.levelname}{reset_color}"
        
        return super().format(record)


class TwitchLogger:
    """Gestionnaire centralisé des logs pour l'application."""
    
    def __init__(self, name: str = "twitch_tracker"):
        """
        Initialise le gestionnaire de logs.
        
        Args:
            name: Nom du logger principal
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, config.logging.level.upper()))
        
        # Évite la duplication des handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Configure les handlers pour les logs."""
        # Handler pour fichier avec rotation
        file_handler = logging.handlers.RotatingFileHandler(
            config.logging.file_path,
            maxBytes=config.logging.max_file_size,
            backupCount=config.logging.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(config.logging.format_string)
        file_handler.setFormatter(file_formatter)
        
        # Handler pour console avec couleurs
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Handler pour erreurs critiques (fichier séparé)
        error_handler = logging.FileHandler(
            config.logging.file_path.parent / "errors.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # Ajout des handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(error_handler)
    
    def get_logger(self, module_name: str) -> logging.Logger:
        """
        Retourne un logger pour un module spécifique.
        
        Args:
            module_name: Nom du module
            
        Returns:
            Logger configuré pour le module
        """
        return logging.getLogger(f"{self.name}.{module_name}")
    
    def log_scraping_session(self, scraper_name: str, status: str, 
                           items_scraped: int = 0, errors: int = 0,
                           duration: float = 0.0, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log une session de scraping avec des détails structurés.
        
        Args:
            scraper_name: Nom du scraper
            status: Statut de la session (success, error, partial)
            items_scraped: Nombre d'éléments scrapés
            errors: Nombre d'erreurs rencontrées
            duration: Durée de la session en secondes
            details: Détails supplémentaires
        """
        session_info = {
            "scraper": scraper_name,
            "status": status,
            "items_scraped": items_scraped,
            "errors": errors,
            "duration": f"{duration:.2f}s",
            "timestamp": datetime.now().isoformat()
        }
        
        if details:
            session_info.update(details)
        
        logger = self.get_logger("scraping")
        
        if status == "success":
            logger.info(f"✅ Session {scraper_name} terminée avec succès: "
                       f"{items_scraped} éléments en {duration:.2f}s")
        elif status == "error":
            logger.error(f"❌ Session {scraper_name} échouée: "
                        f"{errors} erreurs après {duration:.2f}s")
        elif status == "partial":
            logger.warning(f"⚠️ Session {scraper_name} partielle: "
                          f"{items_scraped} éléments, {errors} erreurs en {duration:.2f}s")
        
        # Log détaillé en debug
        logger.debug(f"Détails session: {session_info}")
    
    def log_database_operation(self, operation: str, collection: str, 
                             count: int = 0, success: bool = True,
                             details: Optional[str] = None) -> None:
        """
        Log une opération de base de données.
        
        Args:
            operation: Type d'opération (insert, update, delete, find)
            collection: Nom de la collection
            count: Nombre d'éléments affectés
            success: Succès de l'opération
            details: Détails supplémentaires
        """
        logger = self.get_logger("database")
        
        message = f"💾 {operation.upper()} sur {collection}: {count} éléments"
        if details:
            message += f" - {details}"
        
        if success:
            logger.info(message)
        else:
            logger.error(f"❌ {message} - ÉCHEC")
    
    def log_dashboard_event(self, event_type: str, user_action: str,
                           data: Optional[Dict[str, Any]] = None) -> None:
        """
        Log un événement du dashboard.
        
        Args:
            event_type: Type d'événement (page_view, filter_change, export, etc.)
            user_action: Action utilisateur
            data: Données associées
        """
        logger = self.get_logger("dashboard")
        
        message = f"🖥️ {event_type}: {user_action}"
        if data:
            message += f" - {data}"
        
        logger.info(message)
    
    def log_performance_metric(self, metric_name: str, value: float,
                             unit: str = "", context: Optional[str] = None) -> None:
        """
        Log une métrique de performance.
        
        Args:
            metric_name: Nom de la métrique
            value: Valeur mesurée
            unit: Unité de mesure
            context: Contexte de la mesure
        """
        logger = self.get_logger("performance")
        
        message = f"📊 {metric_name}: {value}{unit}"
        if context:
            message += f" ({context})"
        
        logger.debug(message)
    
    def close(self) -> None:
        """Ferme proprement tous les handlers."""
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)


# Instance globale du gestionnaire de logs
logger_manager = TwitchLogger()

# Fonctions d'accès rapide pour les modules
def get_logger(module_name: str) -> logging.Logger:
    """Fonction utilitaire pour obtenir un logger de module."""
    return logger_manager.get_logger(module_name)

def log_scraping_session(*args, **kwargs) -> None:
    """Fonction utilitaire pour logger une session de scraping."""
    logger_manager.log_scraping_session(*args, **kwargs)

def log_database_operation(*args, **kwargs) -> None:
    """Fonction utilitaire pour logger une opération de base de données."""
    logger_manager.log_database_operation(*args, **kwargs)

def log_dashboard_event(*args, **kwargs) -> None:
    """Fonction utilitaire pour logger un événement du dashboard."""
    logger_manager.log_dashboard_event(*args, **kwargs)

def log_performance_metric(*args, **kwargs) -> None:
    """Fonction utilitaire pour logger une métrique de performance."""
    logger_manager.log_performance_metric(*args, **kwargs)


# Export des éléments principaux
__all__ = [
    "TwitchLogger",
    "logger_manager",
    "get_logger",
    "log_scraping_session",
    "log_database_operation",
    "log_dashboard_event",
    "log_performance_metric"
]
