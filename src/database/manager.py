"""
Module de gestion avancée de la base de données MongoDB pour Twitch Trends Tracker.

Ce module fournit une interface robuste et bien documentée pour toutes les 
opérations de base de données, avec gestion d'erreurs, logging et validation.

Auteur: Équipe Twitch Trends Tracker
Date: 24 juillet 2025
Version: 2.0.0
"""

import pymongo
from pymongo import MongoClient, IndexModel
from pymongo.errors import (
    ConnectionFailure, 
    ServerSelectionTimeoutError,
    BulkWriteError,
    DuplicateKeyError
)
from typing import Dict, List, Any, Optional, Union
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

from ..config.settings import config
from ..utils.logger import get_logger, log_database_operation
from ..utils.exceptions import (
    DatabaseException, 
    handle_database_errors,
    safe_execute
)


@dataclass
class DatabaseStats:
    """Statistiques de la base de données."""
    total_documents: int
    collections_count: int
    database_size: float  # En MB
    last_update: datetime
    collections_info: Dict[str, Dict[str, Any]]


class MongoDBManager:
    """
    Gestionnaire avancé de la base de données MongoDB.
    
    Cette classe centralise toutes les opérations de base de données avec:
    - Gestion robuste des erreurs
    - Logging détaillé des opérations
    - Validation des données
    - Optimisation des performances
    - Support des opérations en lot
    """
    
    def __init__(self):
        """Initialise le gestionnaire MongoDB."""
        self.logger = get_logger("mongodb_manager")
        self.client: Optional[MongoClient] = None
        self.db = None
        self._connection_pool_size = 10
        self._is_connected = False
        
        # Statistiques de performance
        self._operation_counts = {
            "insert": 0,
            "update": 0,
            "delete": 0,
            "find": 0
        }
        
        # Connexion automatique
        self.connect()
        
        if self._is_connected:
            self._setup_indexes()
    
    def connect(self) -> bool:
        """
        Établit la connexion à MongoDB avec gestion d'erreurs robuste.
        
        Returns:
            bool: True si la connexion réussit, False sinon
        """
        try:
            self.logger.info("🔌 Tentative de connexion à MongoDB...")
            
            # Configuration du client avec options optimisées
            self.client = MongoClient(
                config.database.connection_string,
                serverSelectionTimeoutMS=config.database.connection_timeout,
                maxPoolSize=self._connection_pool_size,
                retryWrites=True,
                retryReads=True
            )
            
            # Test de la connexion
            self.client.admin.command('ping')
            
            # Sélection de la base de données
            self.db = self.client[config.database.database_name]
            
            self._is_connected = True
            self.logger.info(f"✅ Connexion réussie à MongoDB: {config.database.database_name}")
            
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            self.logger.error(f"❌ Échec de connexion MongoDB: {e}")
            self._is_connected = False
            return False
        except Exception as e:
            self.logger.error(f"💥 Erreur inattendue lors de la connexion: {e}")
            self._is_connected = False
            return False
    
    def _setup_indexes(self) -> None:
        """Configure les index pour optimiser les performances."""
        try:
            collections_indexes = {
                "games": [
                    IndexModel([("game_name", 1)], unique=True),
                    IndexModel([("viewers", -1)], background=True),
                    IndexModel([("timestamp", -1)], background=True)
                ],
                "events": [
                    IndexModel([("name", 1)], unique=True),
                    IndexModel([("status", 1), ("date", 1)], background=True),
                    IndexModel([("game", 1)], background=True)
                ],
                "streamers": [
                    IndexModel([("username", 1)], unique=True),
                    IndexModel([("followers", -1)], background=True),
                    IndexModel([("rank", 1)], background=True)
                ],
                "scraping_logs": [
                    IndexModel([("timestamp", -1)], background=True),
                    IndexModel([("scraper_name", 1), ("timestamp", -1)], background=True)
                ]
            }
            
            for collection_name, indexes in collections_indexes.items():
                collection = self.db[collection_name]
                collection.create_indexes(indexes)
                
            self.logger.info("📊 Index de base de données configurés")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erreur lors de la configuration des index: {e}")\n    \n    def is_connected(self) -> bool:\n        \"\"\"Vérifie si la connexion est active.\"\"\"\n        if not self._is_connected or not self.client:\n            return False\n        \n        try:\n            self.client.admin.command('ping')\n            return True\n        except Exception:\n            self._is_connected = False\n            return False\n    \n    def reconnect(self) -> bool:\n        \"\"\"Tente de reconnecter à la base de données.\"\"\"\n        self.logger.info(\"🔄 Tentative de reconnexion...\")\n        self.close()\n        return self.connect()\n    \n    @handle_database_errors(operation=\"insert\")\n    def insert_games_data(self, games_data: List[Dict[str, Any]], \n                         update_existing: bool = True) -> int:\n        \"\"\"\n        Insère ou met à jour les données de jeux.\n        \n        Args:\n            games_data: Liste des données de jeux\n            update_existing: Si True, met à jour les entrées existantes\n            \n        Returns:\n            int: Nombre d'éléments traités avec succès\n        \"\"\"\n        if not self.is_connected():\n            raise DatabaseException(\"Connexion MongoDB indisponible\", \n                                   collection=\"games\", operation=\"insert\")\n        \n        if not games_data:\n            self.logger.warning(\"⚠️ Aucune donnée de jeux à insérer\")\n            return 0\n        \n        collection = self.db[\"games\"]\n        processed_count = 0\n        \n        try:\n            for game_data in games_data:\n                # Validation des données\n                if not self._validate_game_data(game_data):\n                    continue\n                \n                # Ajout du timestamp\n                game_data[\"timestamp\"] = datetime.now()\n                game_data[\"last_updated\"] = datetime.now()\n                \n                if update_existing:\n                    # Upsert: insert ou update\n                    result = collection.replace_one(\n                        {\"game_name\": game_data[\"game_name\"]},\n                        game_data,\n                        upsert=True\n                    )\n                    if result.upserted_id or result.modified_count > 0:\n                        processed_count += 1\n                else:\n                    # Insert uniquement si n'existe pas\n                    try:\n                        collection.insert_one(game_data)\n                        processed_count += 1\n                    except DuplicateKeyError:\n                        self.logger.debug(f\"Jeu déjà existant: {game_data.get('game_name')}\")\n            \n            self._operation_counts[\"insert\"] += processed_count\n            log_database_operation(\n                \"insert\", \"games\", processed_count, True,\n                f\"Mode: {'upsert' if update_existing else 'insert_only'}\"\n            )\n            \n            return processed_count\n            \n        except Exception as e:\n            raise DatabaseException(\n                f\"Erreur lors de l'insertion des jeux: {e}\",\n                collection=\"games\",\n                operation=\"insert\"\n            )\n    \n    @handle_database_errors(operation=\"insert\")\n    def insert_events_data(self, events_data: List[Dict[str, Any]]) -> int:\n        \"\"\"\n        Insère les données d'événements gaming.\n        \n        Args:\n            events_data: Liste des données d'événements\n            \n        Returns:\n            int: Nombre d'événements insérés\n        \"\"\"\n        if not self.is_connected():\n            raise DatabaseException(\"Connexion MongoDB indisponible\",\n                                   collection=\"events\", operation=\"insert\")\n        \n        if not events_data:\n            return 0\n        \n        collection = self.db[\"events\"]\n        processed_count = 0\n        \n        try:\n            for event_data in events_data:\n                if not self._validate_event_data(event_data):\n                    continue\n                \n                event_data[\"timestamp\"] = datetime.now()\n                event_data[\"last_updated\"] = datetime.now()\n                \n                # Upsert basé sur le nom\n                result = collection.replace_one(\n                    {\"name\": event_data[\"name\"]},\n                    event_data,\n                    upsert=True\n                )\n                \n                if result.upserted_id or result.modified_count > 0:\n                    processed_count += 1\n            \n            self._operation_counts[\"insert\"] += processed_count\n            log_database_operation(\"insert\", \"events\", processed_count, True)\n            \n            return processed_count\n            \n        except Exception as e:\n            raise DatabaseException(\n                f\"Erreur lors de l'insertion des événements: {e}\",\n                collection=\"events\",\n                operation=\"insert\"\n            )\n    \n    @handle_database_errors(operation=\"insert\")\n    def insert_streamers_data(self, streamers_data: List[Dict[str, Any]]) -> int:\n        \"\"\"\n        Insère les données de streamers français.\n        \n        Args:\n            streamers_data: Liste des données de streamers\n            \n        Returns:\n            int: Nombre de streamers insérés\n        \"\"\"\n        if not self.is_connected():\n            raise DatabaseException(\"Connexion MongoDB indisponible\",\n                                   collection=\"streamers\", operation=\"insert\")\n        \n        if not streamers_data:\n            return 0\n        \n        collection = self.db[\"streamers\"]\n        processed_count = 0\n        \n        try:\n            for streamer_data in streamers_data:\n                if not self._validate_streamer_data(streamer_data):\n                    continue\n                \n                streamer_data[\"timestamp\"] = datetime.now()\n                streamer_data[\"last_updated\"] = datetime.now()\n                \n                # Upsert basé sur le username\n                result = collection.replace_one(\n                    {\"username\": streamer_data[\"username\"]},\n                    streamer_data,\n                    upsert=True\n                )\n                \n                if result.upserted_id or result.modified_count > 0:\n                    processed_count += 1\n            \n            self._operation_counts[\"insert\"] += processed_count\n            log_database_operation(\"insert\", \"streamers\", processed_count, True)\n            \n            return processed_count\n            \n        except Exception as e:\n            raise DatabaseException(\n                f\"Erreur lors de l'insertion des streamers: {e}\",\n                collection=\"streamers\",\n                operation=\"insert\"\n            )\n    \n    @handle_database_errors(operation=\"find\")\n    def get_games_data(self, limit: Optional[int] = None, \n                      sort_by: str = \"viewers\", \n                      descending: bool = True) -> List[Dict[str, Any]]:\n        \"\"\"\n        Récupère les données des jeux avec options de tri et limite.\n        \n        Args:\n            limit: Nombre maximum d'éléments à retourner\n            sort_by: Champ de tri\n            descending: Ordre décroissant si True\n            \n        Returns:\n            List[Dict]: Liste des données de jeux\n        \"\"\"\n        if not self.is_connected():\n            return []\n        \n        collection = self.db[\"games\"]\n        \n        try:\n            # Construction de la requête\n            query = collection.find()\n            \n            # Tri\n            sort_order = -1 if descending else 1\n            query = query.sort(sort_by, sort_order)\n            \n            # Limite\n            if limit:\n                query = query.limit(limit)\n            \n            results = list(query)\n            \n            # Suppression des ObjectId pour la sérialisation\n            for result in results:\n                if \"_id\" in result:\n                    del result[\"_id\"]\n            \n            self._operation_counts[\"find\"] += 1\n            log_database_operation(\"find\", \"games\", len(results), True)\n            \n            return results\n            \n        except Exception as e:\n            self.logger.error(f\"Erreur lors de la récupération des jeux: {e}\")\n            return []\n    \n    @handle_database_errors(operation=\"find\")\n    def get_events_data(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:\n        \"\"\"\n        Récupère les données des événements avec filtrage optionnel.\n        \n        Args:\n            status_filter: Filtre par statut (Live, Upcoming, etc.)\n            \n        Returns:\n            List[Dict]: Liste des données d'événements\n        \"\"\"\n        if not self.is_connected():\n            return []\n        \n        collection = self.db[\"events\"]\n        \n        try:\n            # Construction de la requête\n            query_filter = {}\n            if status_filter:\n                query_filter[\"status\"] = status_filter\n            \n            results = list(collection.find(query_filter).sort(\"date\", 1))\n            \n            # Suppression des ObjectId\n            for result in results:\n                if \"_id\" in result:\n                    del result[\"_id\"]\n            \n            self._operation_counts[\"find\"] += 1\n            log_database_operation(\"find\", \"events\", len(results), True)\n            \n            return results\n            \n        except Exception as e:\n            self.logger.error(f\"Erreur lors de la récupération des événements: {e}\")\n            return []\n    \n    @handle_database_errors(operation=\"find\")\n    def get_streamers_data(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:\n        \"\"\"\n        Récupère les données des streamers français.\n        \n        Args:\n            limit: Nombre maximum de streamers à retourner\n            \n        Returns:\n            List[Dict]: Liste des données de streamers\n        \"\"\"\n        if not self.is_connected():\n            return []\n        \n        collection = self.db[\"streamers\"]\n        \n        try:\n            query = collection.find().sort(\"followers\", -1)\n            \n            if limit:\n                query = query.limit(limit)\n            \n            results = list(query)\n            \n            # Suppression des ObjectId\n            for result in results:\n                if \"_id\" in result:\n                    del result[\"_id\"]\n            \n            self._operation_counts[\"find\"] += 1\n            log_database_operation(\"find\", \"streamers\", len(results), True)\n            \n            return results\n            \n        except Exception as e:\n            self.logger.error(f\"Erreur lors de la récupération des streamers: {e}\")\n            return []\n    \n    def get_database_stats(self) -> DatabaseStats:\n        \"\"\"\n        Retourne les statistiques de la base de données.\n        \n        Returns:\n            DatabaseStats: Statistiques complètes\n        \"\"\"\n        if not self.is_connected():\n            return DatabaseStats(0, 0, 0.0, datetime.now(), {})\n        \n        try:\n            # Informations générales\n            db_stats = self.db.command(\"dbStats\")\n            collections = self.db.list_collection_names()\n            \n            # Informations par collection\n            collections_info = {}\n            total_docs = 0\n            \n            for collection_name in collections:\n                collection = self.db[collection_name]\n                count = collection.count_documents({})\n                total_docs += count\n                \n                collections_info[collection_name] = {\n                    \"document_count\": count,\n                    \"indexes\": len(list(collection.list_indexes()))\n                }\n            \n            return DatabaseStats(\n                total_documents=total_docs,\n                collections_count=len(collections),\n                database_size=db_stats.get(\"dataSize\", 0) / (1024 * 1024),  # MB\n                last_update=datetime.now(),\n                collections_info=collections_info\n            )\n            \n        except Exception as e:\n            self.logger.error(f\"Erreur lors de la récupération des stats: {e}\")\n            return DatabaseStats(0, 0, 0.0, datetime.now(), {})\n    \n    def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, int]:\n        \"\"\"\n        Nettoie les anciennes données.\n        \n        Args:\n            days_to_keep: Nombre de jours de données à conserver\n            \n        Returns:\n            Dict[str, int]: Nombre d'éléments supprimés par collection\n        \"\"\"\n        if not self.is_connected():\n            return {}\n        \n        cutoff_date = datetime.now() - timedelta(days=days_to_keep)\n        deleted_counts = {}\n        \n        collections_to_clean = [\"scraping_logs\"]\n        \n        try:\n            for collection_name in collections_to_clean:\n                collection = self.db[collection_name]\n                result = collection.delete_many({\n                    \"timestamp\": {\"$lt\": cutoff_date}\n                })\n                deleted_counts[collection_name] = result.deleted_count\n                \n                if result.deleted_count > 0:\n                    self.logger.info(f\"🧹 Nettoyé {result.deleted_count} entrées de {collection_name}\")\n            \n            return deleted_counts\n            \n        except Exception as e:\n            self.logger.error(f\"Erreur lors du nettoyage: {e}\")\n            return {}\n    \n    def _validate_game_data(self, game_data: Dict[str, Any]) -> bool:\n        \"\"\"\n        Valide les données d'un jeu.\n        \n        Args:\n            game_data: Données du jeu à valider\n            \n        Returns:\n            bool: True si valide, False sinon\n        \"\"\"\n        required_fields = [\"game_name\", \"viewers\"]\n        \n        for field in required_fields:\n            if field not in game_data or game_data[field] is None:\n                self.logger.warning(f\"⚠️ Champ requis manquant: {field}\")\n                return False\n        \n        # Validation du type de viewers\n        try:\n            viewers = int(game_data[\"viewers\"])\n            if viewers < 0:\n                self.logger.warning(f\"⚠️ Nombre de viewers invalide: {viewers}\")\n                return False\n            game_data[\"viewers\"] = viewers\n        except (ValueError, TypeError):\n            self.logger.warning(f\"⚠️ Nombre de viewers non numérique: {game_data['viewers']}\")\n            return False\n        \n        return True\n    \n    def _validate_event_data(self, event_data: Dict[str, Any]) -> bool:\n        \"\"\"\n        Valide les données d'un événement.\n        \n        Args:\n            event_data: Données de l'événement à valider\n            \n        Returns:\n            bool: True si valide, False sinon\n        \"\"\"\n        required_fields = [\"name\"]\n        \n        for field in required_fields:\n            if field not in event_data or not event_data[field]:\n                self.logger.warning(f\"⚠️ Champ requis manquant pour événement: {field}\")\n                return False\n        \n        return True\n    \n    def _validate_streamer_data(self, streamer_data: Dict[str, Any]) -> bool:\n        \"\"\"\n        Valide les données d'un streamer.\n        \n        Args:\n            streamer_data: Données du streamer à valider\n            \n        Returns:\n            bool: True si valide, False sinon\n        \"\"\"\n        required_fields = [\"username\", \"followers\"]\n        \n        for field in required_fields:\n            if field not in streamer_data or streamer_data[field] is None:\n                self.logger.warning(f\"⚠️ Champ requis manquant pour streamer: {field}\")\n                return False\n        \n        # Validation du nombre de followers\n        try:\n            followers = int(streamer_data[\"followers\"])\n            if followers < 0:\n                self.logger.warning(f\"⚠️ Nombre de followers invalide: {followers}\")\n                return False\n            streamer_data[\"followers\"] = followers\n        except (ValueError, TypeError):\n            self.logger.warning(f\"⚠️ Nombre de followers non numérique: {streamer_data['followers']}\")\n            return False\n        \n        return True\n    \n    def get_operation_stats(self) -> Dict[str, int]:\n        \"\"\"\n        Retourne les statistiques d'opérations.\n        \n        Returns:\n            Dict[str, int]: Compteurs d'opérations\n        \"\"\"\n        return self._operation_counts.copy()\n    \n    def reset_operation_stats(self) -> None:\n        \"\"\"Remet à zéro les statistiques d'opérations.\"\"\"\n        self._operation_counts = {key: 0 for key in self._operation_counts}\n    \n    def close(self) -> None:\n        \"\"\"\n        Ferme proprement la connexion à MongoDB.\n        \"\"\"\n        if self.client:\n            self.client.close()\n            self.client = None\n            self.db = None\n            self._is_connected = False\n            self.logger.info(\"🔌 Connexion MongoDB fermée\")\n    \n    def __enter__(self):\n        \"\"\"Support du context manager.\"\"\"\n        return self\n    \n    def __exit__(self, exc_type, exc_val, exc_tb):\n        \"\"\"Nettoyage automatique à la sortie du context manager.\"\"\"\n        self.close()\n    \n    def __del__(self):\n        \"\"\"Nettoyage automatique lors de la destruction de l'objet.\"\"\"\n        self.close()\n\n\n# Instance globale du gestionnaire (singleton)\n_db_manager = None\n\ndef get_db_manager() -> MongoDBManager:\n    \"\"\"\n    Retourne l'instance singleton du gestionnaire de base de données.\n    \n    Returns:\n        MongoDBManager: Instance du gestionnaire\n    \"\"\"\n    global _db_manager\n    if _db_manager is None:\n        _db_manager = MongoDBManager()\n    return _db_manager\n\n\n# Export des éléments principaux\n__all__ = [\n    \"MongoDBManager\",\n    \"DatabaseStats\",\n    \"get_db_manager\"\n]
