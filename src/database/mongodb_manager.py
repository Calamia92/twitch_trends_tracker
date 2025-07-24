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
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import pandas as pd

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBManager:
    """
    Gestionnaire de la base de données MongoDB pour le système de suivi Twitch.
    
    Cette classe centralise toutes les opérations de base de données et fournit
    une interface cohérente pour l'insertion, la récupération et la mise à jour
    des données de gaming.
    """
    
    def __init__(self):
        """Initialise le gestionnaire MongoDB."""
        self.client: Optional[MongoClient] = None
        self.db = None
        self.collection = None
        self.connect()
    
    def connect(self) -> bool:
        """
        Établit la connexion à MongoDB.
        
        Returns:
            bool: True si la connexion réussit, False sinon
        """
        try:
            # Tentative de connexion à MongoDB
            self.client = MongoClient(
                config.database.MONGODB_URI,
                serverSelectionTimeoutMS=5000,  # Timeout de 5 secondes
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Test de la connexion
            self.client.admin.command('ping')
            
            # Sélection de la base de données et collection
            self.db = self.client[config.database.DATABASE_NAME]
            self.collection = self.db[config.database.COLLECTION_NAME]
            
            logger.info(f"✅ Connecté à MongoDB: {config.database.DATABASE_NAME}")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ Erreur de connexion MongoDB: {e}")
            self.client = None
            self.db = None
            self.collection = None
            return False
        except Exception as e:
            logger.error(f"❌ Erreur inattendue lors de la connexion: {e}")
            return False
    
    def is_connected(self) -> bool:
        """
        Vérifie si la connexion à MongoDB est active.
        
        Returns:
            bool: True si connecté, False sinon
        """
        if self.client is None:
            return False
        
        try:
            # Test de ping pour vérifier la connexion
            self.client.admin.command('ping')
            return True
        except Exception:
            logger.warning("⚠️ Connexion MongoDB perdue")
            return False
    
    def reconnect(self) -> bool:
        """
        Reconnecte à MongoDB en cas de perte de connexion.
        
        Returns:
            bool: True si la reconnexion réussit, False sinon
        """
        logger.info("🔄 Tentative de reconnexion à MongoDB...")
        return self.connect()
    
    def insert_data(self, data: Dict[str, Any]) -> bool:
        """
        Insère des données dans la collection principale.
        
        Args:
            data: Dictionnaire contenant les données à insérer
            
        Returns:
            bool: True si l'insertion réussit, False sinon
        """
        if not self.is_connected():
            logger.error("❌ Pas de connexion à la base de données")
            return False
        
        try:
            # Ajout de timestamp automatique
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now()
            
            # Insertion des données
            result = self.collection.insert_one(data)
            
            if result.inserted_id:
                logger.info(f"✅ Données insérées avec l'ID: {result.inserted_id}")
                return True
            else:
                logger.error("❌ Échec de l'insertion des données")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'insertion: {e}")
            return False
    
    def insert_event_data(self, event_data: Dict[str, Any]) -> bool:
        """
        Insère ou met à jour les données d'un événement gaming.
        
        Args:
            event_data: Dictionnaire contenant les données de l'événement
            
        Returns:
            bool: True si l'insertion réussit, False sinon
        """
        if not self.is_connected() or self.client is None:
            logger.error("❌ Pas de connexion à la base de données")
            return False
        
        try:
            # Collection spécifique pour les événements
            events_collection = self.client[config.database.DATABASE_NAME]['events']
            
            # Ajout de timestamp automatique
            if 'timestamp' not in event_data:
                event_data['timestamp'] = datetime.now()
            
            # Upsert basé sur le nom et la date de l'événement
            query = {
                'name': event_data.get('name'),
                'date': event_data.get('date')
            }
            
            result = events_collection.update_one(
                query,
                {'$set': event_data},
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                logger.info(f"✅ Événement mis à jour: {event_data.get('name')}")
                return True
            else:
                logger.warning("⚠️ Aucune modification pour l'événement")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'insertion de l'événement: {e}")
            return False
    
    def insert_streamer_data(self, streamer_data: Dict[str, Any]) -> bool:
        """
        Insère ou met à jour les données d'un streamer.
        
        Args:
            streamer_data: Dictionnaire contenant les données du streamer
            
        Returns:
            bool: True si l'insertion réussit, False sinon
        """
        if not self.is_connected() or self.client is None:
            logger.error("❌ Pas de connexion à la base de données")
            return False
        
        try:
            # Collection spécifique pour les streameurs
            streamers_collection = self.client[config.database.DATABASE_NAME]['streamers']
            
            # Ajout de timestamp automatique
            if 'timestamp' not in streamer_data:
                streamer_data['timestamp'] = datetime.now()
            
            # Upsert basé sur le nom du streamer
            query = {'username': streamer_data.get('username')}
            
            result = streamers_collection.update_one(
                query,
                {'$set': streamer_data},
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                logger.info(f"✅ Streamer mis à jour: {streamer_data.get('username')}")
                return True
            else:
                logger.warning("⚠️ Aucune modification pour le streamer")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'insertion du streamer: {e}")
            return False
    
    def get_latest_data(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère les données les plus récentes.
        
        Args:
            limit: Nombre maximum d'éléments à retourner
            
        Returns:
            List[Dict]: Liste des documents récents
        """
        if not self.is_connected():
            logger.error("❌ Pas de connexion à la base de données")
            return []
        
        try:
            # Récupération des données triées par timestamp décroissant
            cursor = self.collection.find().sort("timestamp", -1).limit(limit)
            data = list(cursor)
            
            logger.info(f"✅ {len(data)} documents récupérés")
            return data
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération: {e}")
            return []
    
    def get_data_by_game(self, game_name: str) -> List[Dict[str, Any]]:
        """
        Récupère les données pour un jeu spécifique.
        
        Args:
            game_name: Nom du jeu à rechercher
            
        Returns:
            List[Dict]: Liste des documents pour ce jeu
        """
        if not self.is_connected():
            logger.error("❌ Pas de connexion à la base de données")
            return []
        
        try:
            # Recherche par nom de jeu (insensible à la casse)
            query = {"game_name": {"$regex": game_name, "$options": "i"}}
            cursor = self.collection.find(query).sort("timestamp", -1)
            data = list(cursor)
            
            logger.info(f"✅ {len(data)} documents trouvés pour '{game_name}'")
            return data
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche: {e}")
            return []
    
    def get_events_data(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère les données des événements gaming.
        
        Args:
            limit: Nombre maximum d'événements à retourner
            
        Returns:
            List[Dict]: Liste des événements
        """
        if not self.is_connected() or self.client is None:
            logger.error("❌ Pas de connexion à la base de données")
            return []
        
        try:
            events_collection = self.client[config.database.DATABASE_NAME]['events']
            cursor = events_collection.find().sort("timestamp", -1).limit(limit)
            data = list(cursor)
            
            logger.info(f"✅ {len(data)} événements récupérés")
            return data
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des événements: {e}")
            return []
    
    def get_streamers_data(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère les données des streamers.
        
        Args:
            limit: Nombre maximum de streamers à retourner
            
        Returns:
            List[Dict]: Liste des streamers
        """
        if not self.is_connected() or self.client is None:
            logger.error("❌ Pas de connexion à la base de données")
            return []
        
        try:
            streamers_collection = self.client[config.database.DATABASE_NAME]['streamers']
            cursor = streamers_collection.find().sort("timestamp", -1).limit(limit)
            data = list(cursor)
            
            logger.info(f"✅ {len(data)} streamers récupérés")
            return data
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des streamers: {e}")
            return []
    
    def get_dataframe(self, limit: int = 1000) -> pd.DataFrame:
        """
        Retourne les données sous forme de DataFrame pandas.
        
        Args:
            limit: Nombre maximum d'éléments à retourner
            
        Returns:
            pd.DataFrame: DataFrame contenant les données
        """
        data = self.get_latest_data(limit)
        
        if not data:
            logger.warning("⚠️ Aucune donnée disponible pour le DataFrame")
            return pd.DataFrame()
        
        try:
            # Conversion en DataFrame
            df = pd.DataFrame(data)
            
            # Suppression de la colonne _id si elle existe (problématique pour Streamlit)
            if '_id' in df.columns:
                df = df.drop('_id', axis=1)
            
            # Conversion des timestamps
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            logger.info(f"✅ DataFrame créé avec {len(df)} lignes")
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création du DataFrame: {e}")
            return pd.DataFrame()
    
    def get_games_summary(self) -> Dict[str, Any]:
        """
        Génère un résumé des données de jeux.
        
        Returns:
            Dict: Statistiques sur les jeux
        """
        if not self.is_connected():
            logger.error("❌ Pas de connexion à la base de données")
            return {}
        
        try:
            # Pipeline d'agrégation pour les statistiques
            pipeline = [
                {
                    "$group": {
                        "_id": "$game_name",
                        "total_viewers": {"$sum": "$viewers"},
                        "avg_viewers": {"$avg": "$viewers"},
                        "max_viewers": {"$max": "$viewers"},
                        "count": {"$sum": 1},
                        "last_update": {"$max": "$timestamp"}
                    }
                },
                {
                    "$sort": {"total_viewers": -1}
                }
            ]
            
            results = list(self.collection.aggregate(pipeline))
            
            # Calcul des totaux
            total_viewers = sum(game["total_viewers"] for game in results)
            total_games = len(results)
            
            summary = {
                "total_viewers": total_viewers,
                "total_games": total_games,
                "games_details": results,
                "last_update": datetime.now()
            }
            
            logger.info(f"✅ Résumé généré: {total_games} jeux, {total_viewers:,} viewers total")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du calcul du résumé: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """
        Supprime les données anciennes pour optimiser l'espace.
        
        Args:
            days: Nombre de jours à conserver
            
        Returns:
            int: Nombre de documents supprimés
        """
        if not self.is_connected():
            logger.error("❌ Pas de connexion à la base de données")
            return 0
        
        try:
            # Date limite pour la suppression
            cutoff_date = datetime.now() - pd.Timedelta(days=days)
            
            # Suppression des données anciennes
            result = self.collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            
            deleted_count = result.deleted_count
            logger.info(f"✅ {deleted_count} documents anciens supprimés")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du nettoyage: {e}")
            return 0
    
    def insert_game_data(self, game_data: Dict[str, Any]) -> bool:
        """
        Insère des données de jeu (alias pour insert_data).
        
        Args:
            game_data: Dictionnaire contenant les données du jeu
            
        Returns:
            bool: True si l'insertion réussit, False sinon
        """
        return self.insert_data(game_data)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques de la base de données.
        
        Returns:
            Dict: Statistiques de la base
        """
        if not self.is_connected():
            return {}
        
        try:
            stats = {
                'total_games': self.collection.count_documents({}),
                'total_events': 0,
                'total_streamers': 0
            }
            
            if self.client:
                # Compter les événements et streamers
                events_collection = self.client[config.database.DATABASE_NAME]['events']
                streamers_collection = self.client[config.database.DATABASE_NAME]['streamers']
                
                stats['total_events'] = events_collection.count_documents({})
                stats['total_streamers'] = streamers_collection.count_documents({})
            
            return stats
        except Exception as e:
            logger.error(f"❌ Erreur stats: {e}")
            return {}

    def close_connection(self):
        """Ferme la connexion à MongoDB."""
        if self.client:
            self.client.close()
            logger.info("✅ Connexion MongoDB fermée")
            self.client = None
            self.db = None
            self.collection = None
    
    def __del__(self):
        """Destructeur pour fermer la connexion."""
        self.close_connection()


# Instance globale du gestionnaire
db_manager = MongoDBManager()
