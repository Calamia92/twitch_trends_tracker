"""
Module de gestion centralisée des erreurs et exceptions pour Twitch Trends Tracker.

Ce module définit des exceptions personnalisées et des gestionnaires d'erreurs
pour améliorer la robustesse et le débogage de l'application.

Auteur: Équipe Twitch Trends Tracker
Date: 24 juillet 2025
Version: 2.0.0
"""

import functools
import traceback
from typing import Any, Callable, Optional, Type, Dict
from datetime import datetime
import sys

from .logger import get_logger


# ================================
# Exceptions personnalisées
# ================================

class TwitchTrackerException(Exception):
    """Exception de base pour l'application Twitch Tracker."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        """
        Initialise l'exception.
        
        Args:
            message: Message d'erreur
            error_code: Code d'erreur unique
            context: Contexte additionnel pour le débogage
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()


class ScrapingException(TwitchTrackerException):
    """Exception liée aux opérations de scraping."""
    
    def __init__(self, message: str, url: Optional[str] = None, 
                 scraper_name: Optional[str] = None, **kwargs):
        """
        Initialise l'exception de scraping.
        
        Args:
            message: Message d'erreur
            url: URL qui a causé l'erreur
            scraper_name: Nom du scraper concerné
        """
        context = kwargs.get('context', {})
        if url:
            context['url'] = url
        if scraper_name:
            context['scraper'] = scraper_name
        
        super().__init__(message, **kwargs)
        self.url = url
        self.scraper_name = scraper_name


class DatabaseException(TwitchTrackerException):
    """Exception liée aux opérations de base de données."""
    
    def __init__(self, message: str, collection: Optional[str] = None,
                 operation: Optional[str] = None, **kwargs):
        """
        Initialise l'exception de base de données.
        
        Args:
            message: Message d'erreur
            collection: Collection MongoDB concernée
            operation: Type d'opération (insert, update, delete, find)
        """
        context = kwargs.get('context', {})
        if collection:
            context['collection'] = collection
        if operation:
            context['operation'] = operation
        
        super().__init__(message, **kwargs)
        self.collection = collection
        self.operation = operation


class DashboardException(TwitchTrackerException):
    """Exception liée au dashboard Streamlit."""
    
    def __init__(self, message: str, component: Optional[str] = None,
                 user_action: Optional[str] = None, **kwargs):
        """
        Initialise l'exception du dashboard.
        
        Args:
            message: Message d'erreur
            component: Composant du dashboard concerné
            user_action: Action utilisateur qui a causé l'erreur
        """
        context = kwargs.get('context', {})
        if component:
            context['component'] = component
        if user_action:
            context['user_action'] = user_action
        
        super().__init__(message, **kwargs)
        self.component = component
        self.user_action = user_action


class ConfigurationException(TwitchTrackerException):
    """Exception liée à la configuration."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        """
        Initialise l'exception de configuration.
        
        Args:
            message: Message d'erreur
            config_key: Clé de configuration problématique
        """
        context = kwargs.get('context', {})
        if config_key:
            context['config_key'] = config_key
        
        super().__init__(message, **kwargs)
        self.config_key = config_key


# ================================
# Gestionnaires d'erreurs
# ================================

class ErrorHandler:
    """Gestionnaire centralisé des erreurs."""
    
    def __init__(self):
        """Initialise le gestionnaire d'erreurs."""
        self.logger = get_logger("error_handler")
        self.error_counts: Dict[str, int] = {}
    
    def handle_exception(self, exc: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Gère une exception de manière centralisée.
        
        Args:
            exc: Exception à gérer
            context: Contexte additionnel
        """
        error_type = exc.__class__.__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Construction du message d'erreur
        error_info = {
            "type": error_type,
            "message": str(exc),
            "count": self.error_counts[error_type],
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Ajout du contexte personnalisé
        if context:
            error_info["context"] = context
        
        # Ajout des informations spécifiques aux exceptions personnalisées
        if isinstance(exc, TwitchTrackerException):
            error_info.update({
                "error_code": exc.error_code,
                "custom_context": exc.context
            })
        
        # Log approprié selon le type d'erreur
        if isinstance(exc, (ScrapingException, DatabaseException)):
            self.logger.error(f"❌ {error_type}: {exc.message}")
        elif isinstance(exc, DashboardException):
            self.logger.warning(f"⚠️ {error_type}: {exc.message}")
        elif isinstance(exc, ConfigurationException):
            self.logger.critical(f"🔥 {error_type}: {exc.message}")
        else:
            self.logger.error(f"💥 Exception non gérée: {error_type} - {str(exc)}")
        
        # Log détaillé en debug
        self.logger.debug(f"Détails erreur: {error_info}")
    
    def get_error_stats(self) -> Dict[str, int]:
        """Retourne les statistiques d'erreurs."""
        return self.error_counts.copy()
    
    def reset_error_counts(self) -> None:
        """Remet à zéro les compteurs d'erreurs."""
        self.error_counts.clear()


# Instance globale du gestionnaire d'erreurs
error_handler = ErrorHandler()


# ================================
# Décorateurs pour la gestion d'erreurs
# ================================

def handle_exceptions(exception_types: tuple = (Exception,), 
                     log_level: str = "error",
                     reraise: bool = False,
                     default_return: Any = None,
                     context_func: Optional[Callable] = None):
    """
    Décorateur pour gérer les exceptions dans les fonctions.
    
    Args:
        exception_types: Types d'exceptions à capturer
        log_level: Niveau de log (error, warning, info, debug)
        reraise: Si True, relance l'exception après l'avoir loggée
        default_return: Valeur de retour par défaut en cas d'erreur
        context_func: Fonction pour générer le contexte
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                # Génération du contexte
                context = {
                    "function": func.__name__,
                    "module": func.__module__,
                    "args": str(args)[:200],  # Limité pour éviter les logs trop longs
                    "kwargs": str(kwargs)[:200]
                }
                
                if context_func:
                    try:
                        context.update(context_func(*args, **kwargs))
                    except Exception:
                        pass  # Ne pas faire échouer la gestion d'erreur
                
                # Gestion de l'erreur
                error_handler.handle_exception(e, context)
                
                if reraise:
                    raise
                
                return default_return
        
        return wrapper
    return decorator


def handle_scraping_errors(scraper_name: str = "", url: str = ""):
    """
    Décorateur spécialisé pour les erreurs de scraping.
    
    Args:
        scraper_name: Nom du scraper
        url: URL de base du scraping
    """
    def context_func(*args, **kwargs):
        return {
            "scraper_name": scraper_name,
            "base_url": url,
            "operation": "scraping"
        }
    
    return handle_exceptions(
        exception_types=(ScrapingException, Exception),
        context_func=context_func,
        reraise=False,
        default_return=[]
    )


def handle_database_errors(collection: str = "", operation: str = ""):
    """
    Décorateur spécialisé pour les erreurs de base de données.
    
    Args:
        collection: Nom de la collection
        operation: Type d'opération
    """
    def context_func(*args, **kwargs):
        return {
            "collection": collection,
            "operation": operation,
            "database_type": "mongodb"
        }
    
    return handle_exceptions(
        exception_types=(DatabaseException, Exception),
        context_func=context_func,
        reraise=False,
        default_return=None
    )


def handle_dashboard_errors(component: str = ""):
    """
    Décorateur spécialisé pour les erreurs du dashboard.
    
    Args:
        component: Nom du composant
    """
    def context_func(*args, **kwargs):
        return {
            "component": component,
            "interface": "streamlit"
        }
    
    return handle_exceptions(
        exception_types=(DashboardException, Exception),
        context_func=context_func,
        reraise=False,
        default_return=None
    )


# ================================
# Fonctions utilitaires
# ================================

def safe_execute(func: Callable, *args, **kwargs) -> tuple[bool, Any]:
    """
    Exécute une fonction de manière sécurisée.
    
    Args:
        func: Fonction à exécuter
        *args: Arguments positionnels
        **kwargs: Arguments nommés
    
    Returns:
        Tuple (succès, résultat)
    """
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        error_handler.handle_exception(e, {
            "function": func.__name__,
            "safe_execution": True
        })
        return False, None


def validate_and_execute(func: Callable, validation_func: Callable, 
                        *args, **kwargs) -> tuple[bool, Any]:
    """
    Valide les paramètres puis exécute une fonction.
    
    Args:
        func: Fonction à exécuter
        validation_func: Fonction de validation
        *args: Arguments positionnels
        **kwargs: Arguments nommés
    
    Returns:
        Tuple (succès, résultat)
    """
    try:
        # Validation
        if not validation_func(*args, **kwargs):
            raise ValueError("Validation des paramètres échouée")
        
        # Exécution
        result = func(*args, **kwargs)
        return True, result
    
    except Exception as e:
        error_handler.handle_exception(e, {
            "function": func.__name__,
            "validation_func": validation_func.__name__,
            "validated_execution": True
        })
        return False, None


# Export des éléments principaux
__all__ = [
    # Exceptions
    "TwitchTrackerException",
    "ScrapingException", 
    "DatabaseException",
    "DashboardException",
    "ConfigurationException",
    
    # Gestionnaire d'erreurs
    "ErrorHandler",
    "error_handler",
    
    # Décorateurs
    "handle_exceptions",
    "handle_scraping_errors",
    "handle_database_errors", 
    "handle_dashboard_errors",
    
    # Fonctions utilitaires
    "safe_execute",
    "validate_and_execute"
]
