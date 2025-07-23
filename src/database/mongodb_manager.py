"""
Module de gestion de la base de données MongoDB.

Ce module fournit une interface unifiée pour toutes les opérations
de base de données, avec gestion d'erreurs robuste et logging.

Auteurs: Hicham, Aya, Boubaker
Date: Juillet 2025
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo import MongoClient, errors
from pymongo.collection import Collection
from config.settings import config

# Configuration du logger
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Gestionnaire de base de données MongoDB avec gestion d'erreurs robuste.
    
    Cette classe fournit une interface simple et sécurisée pour toutes
    les opérations de base de données nécessaires au projet.
    """
    
    def __init__(self):
        """Initialise la connexion à MongoDB."""
        self.client: Optional[MongoClient] = None
        self.database = None
        self.collection: Optional[Collection] = None
        self._connect()
    
    def _connect(self) -> bool:
        """
        Établit la connexion à MongoDB.
        
        Returns:
            bool: True si la connexion est établie, False sinon
        """
        try:
            # Connexion avec timeout configuré
            self.client = MongoClient(
                config.database.MONGODB_URI,
                serverSelectionTimeoutMS=config.database.CONNECTION_TIMEOUT
            )
            
            # Test de la connexion
            self.client.admin.command('ping')
            
            # Sélection de la base et collection
            self.database = self.client[config.database.DATABASE_NAME]
            self.collection = self.database[config.database.COLLECTION_NAME]
            
            logger.info("✅ Connexion MongoDB établie avec succès")
            return True
            
        except errors.ServerSelectionTimeoutError:
            logger.error("❌ Timeout de connexion MongoDB")
            return False
        except errors.ConfigurationError as e:
            logger.error(f"❌ Erreur de configuration MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur inattendue MongoDB: {e}")
            return False
    
    def is_connected(self) -> bool:
        """
        Vérifie si la connexion à la base de données est active.
        
        Returns:
            bool: True si connecté, False sinon
        """
        try:
            if self.client is None:
                return False
            self.client.admin.command('ping')
            return True
        except Exception:
            return False
    
    def insert_game_data(self, game_data: Dict[str, Any]) -> bool:
        """
        Insère ou met à jour les données d'un jeu.
        
        Args:
            game_data: Dictionnaire contenant les données du jeu
            
        Returns:
            bool: True si l'insertion réussit, False sinon
        """
        if not self.is_connected() or self.collection is None:
            logger.error("❌ Pas de connexion à la base de données")
            return False
        
        try:
            # Ajout du timestamp
            game_data['scraped_at'] = datetime.now()
            game_data['updated_at'] = datetime.now()
            
            # Upsert basé sur le titre du jeu
            result = self.collection.update_one(
                {'title': game_data['title']},
                {'$set': game_data},
                upsert=True
            )
            
            action = "mis à jour" if result.matched_count > 0 else "inséré"
            logger.debug(f"✅ Jeu '{game_data['title']}' {action}")
            return True
            
        except errors.DuplicateKeyError:
            logger.warning(f"⚠️ Doublon détecté pour {game_data.get('title', 'Inconnu')}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur insertion: {e}")
            return False
    
    def insert_multiple_games(self, games_data: List[Dict[str, Any]]) -> int:
        """
        Insère plusieurs jeux en une seule opération.
        
        Args:
            games_data: Liste des données de jeux
            
        Returns:
            int: Nombre de jeux insérés avec succès
        """
        if not self.is_connected() or self.collection is None:
            logger.error("❌ Pas de connexion à la base de données")
            return 0
        
        if not games_data:
            logger.warning("⚠️ Aucune donnée à insérer")
            return 0
        
        success_count = 0
        timestamp = datetime.now()
        
        for game_data in games_data:
            try:
                game_data['scraped_at'] = timestamp
                game_data['updated_at'] = timestamp
                
                self.collection.update_one(
                    {'title': game_data['title']},
                    {'$set': game_data},
                    upsert=True
                )
                success_count += 1
                
            except Exception as e:
                logger.error(f"❌ Erreur insertion {game_data.get('title', 'Inconnu')}: {e}")
        
        logger.info(f"✅ {success_count}/{len(games_data)} jeux traités")
        return success_count
    
    def get_all_games(self) -> List[Dict[str, Any]]:
        """
        Récupère tous les jeux de la base de données.
        
        Returns:
            List[Dict]: Liste des jeux, vide si erreur
        """
        if not self.is_connected() or self.collection is None:
            logger.error("❌ Pas de connexion à la base de données")
            return []
        
        try:
            # Tri par nombre de viewers décroissant
            games = list(self.collection.find({}).sort("viewers", -1))
            logger.debug(f"✅ {len(games)} jeux récupérés")
            return games
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération: {e}")
            return []
    
    def get_games_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Récupère les jeux dans une plage de dates.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            List[Dict]: Liste des jeux dans la plage
        """
        if not self.is_connected() or self.collection is None:
            return []
        
        try:
            query = {
                "scraped_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }
            
            games = list(self.collection.find(query).sort("viewers", -1))
            logger.debug(f"✅ {len(games)} jeux trouvés entre {start_date} et {end_date}")
            return games
            
        except Exception as e:
            logger.error(f"❌ Erreur requête par date: {e}")
            return []
    
    def get_top_games(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Récupère le top des jeux par nombre de viewers.
        
        Args:
            limit: Nombre maximum de jeux à retourner
            
        Returns:
            List[Dict]: Top des jeux
        """
        if not self.is_connected() or self.collection is None:
            return []
        
        try:
            games = list(
                self.collection
                .find({})
                .sort("viewers", -1)
                .limit(limit)
            )
            logger.debug(f"✅ Top {len(games)} jeux récupérés")
            return games
            
        except Exception as e:
            logger.error(f"❌ Erreur top games: {e}")
            return []
    
    def delete_old_data(self, days_old: int = 30) -> int:
        """
        Supprime les données anciennes.
        
        Args:
            days_old: Nombre de jours d'ancienneté
            
        Returns:
            int: Nombre de documents supprimés
        """
        if not self.is_connected() or self.collection is None:
            return 0
        
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
            
            result = self.collection.delete_many({
                "scraped_at": {"$lt": cutoff_date}
            })
            
            deleted_count = result.deleted_count
            logger.info(f"✅ {deleted_count} anciens documents supprimés")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Erreur suppression: {e}")
            return 0
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques de la base de données.
        
        Returns:
            Dict: Statistiques de la base
        """
        if not self.is_connected() or self.collection is None:
            return {}
        
        try:
            stats = {
                'total_games': self.collection.count_documents({}),
                'database_name': config.database.DATABASE_NAME,
                'collection_name': config.database.COLLECTION_NAME,
                'last_update': None
            }
            
            # Dernière mise à jour
            latest = self.collection.find_one(sort=[("updated_at", -1)])
            if latest and 'updated_at' in latest:
                stats['last_update'] = latest['updated_at']
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Erreur statistiques: {e}")
            return {}
    
    def close_connection(self):
        """Ferme la connexion à MongoDB."""
        if self.client:
            self.client.close()
            logger.info("✅ Connexion MongoDB fermée")


# Instance globale du gestionnaire de base de données
db_manager = DatabaseManager()
