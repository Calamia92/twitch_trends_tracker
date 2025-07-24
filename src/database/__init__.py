"""
Package de gestion de la base de données.

Ce package contient tous les modules nécessaires pour gérer
les opérations de base de données MongoDB.
"""

from .mongodb_manager import MongoDBManager, db_manager

__all__ = ['MongoDBManager', 'db_manager']
