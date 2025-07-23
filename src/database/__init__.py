"""
Module de gestion de base de données.

Contient les managers et utilitaires pour MongoDB.
"""

from .mongodb_manager import DatabaseManager, db_manager

__all__ = ['DatabaseManager', 'db_manager']
