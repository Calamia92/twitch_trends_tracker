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
    
    def insert_sample_data(self) -> bool:
        """
        Insère des données d'exemple pour tester le dashboard.
        
        Returns:
            bool: True si l'insertion réussit
        """
        if not self.is_connected() or self.collection is None:
            logger.error("❌ Pas de connexion à la base de données")
            return False
        
        try:
            # Données d'exemple réalistes basées sur les vrais top jeux Twitch (50+ jeux)
            sample_games = [
                # Top 10
                {"title": "League of Legends", "viewers": 156789, "change": 5.2, "share": 12.5, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/21779-285x380.jpg"},
                {"title": "Fortnite", "viewers": 134256, "change": -2.1, "share": 10.8, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/33214-285x380.jpg"},
                {"title": "Valorant", "viewers": 98745, "change": 8.7, "share": 7.9, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/516575-285x380.jpg"},
                {"title": "Counter-Strike 2", "viewers": 87321, "change": 3.4, "share": 7.0, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/32399-285x380.jpg"},
                {"title": "World of Warcraft", "viewers": 76543, "change": -1.8, "share": 6.1, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/18122-285x380.jpg"},
                {"title": "Grand Theft Auto V", "viewers": 65432, "change": 12.3, "share": 5.2, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/32982-285x380.jpg"},
                {"title": "Minecraft", "viewers": 54321, "change": 4.6, "share": 4.3, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/27471-285x380.jpg"},
                {"title": "Apex Legends", "viewers": 43210, "change": -3.2, "share": 3.5, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/511224-285x380.jpg"},
                {"title": "Dota 2", "viewers": 32109, "change": 1.9, "share": 2.6, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/29595-285x380.jpg"},
                {"title": "Call of Duty: Warzone", "viewers": 21098, "change": -5.4, "share": 1.7, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/512710-285x380.jpg"},
                
                # 11-20
                {"title": "Overwatch 2", "viewers": 19876, "change": 7.1, "share": 1.6, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/515025-285x380.jpg"},
                {"title": "Rocket League", "viewers": 18654, "change": 2.3, "share": 1.5, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/30921-285x380.jpg"},
                {"title": "FIFA 24", "viewers": 17432, "change": -4.7, "share": 1.4, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/1869092879-285x380.jpg"},
                {"title": "Dead by Daylight", "viewers": 16210, "change": 6.8, "share": 1.3, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/491487-285x380.jpg"},
                {"title": "Rust", "viewers": 14988, "change": 3.9, "share": 1.2, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/263490-285x380.jpg"},
                {"title": "Among Us", "viewers": 13766, "change": -8.2, "share": 1.1, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/510218-285x380.jpg"},
                {"title": "Fall Guys", "viewers": 12544, "change": 15.6, "share": 1.0, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/512980-285x380.jpg"},
                {"title": "Hearthstone", "viewers": 11322, "change": -1.4, "share": 0.9, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/138585-285x380.jpg"},
                {"title": "Chess", "viewers": 10100, "change": 4.2, "share": 0.8, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/743-285x380.jpg"},
                {"title": "Teamfight Tactics", "viewers": 9878, "change": 2.7, "share": 0.8, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/513143-285x380.jpg"},
                
                # 21-30
                {"title": "Genshin Impact", "viewers": 9656, "change": 9.3, "share": 0.7, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/1649144309-285x380.jpg"},
                {"title": "PUBG", "viewers": 9434, "change": -3.6, "share": 0.7, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/493057-285x380.jpg"},
                {"title": "Rainbow Six Siege", "viewers": 9212, "change": 1.8, "share": 0.7, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/460630-285x380.jpg"},
                {"title": "Escape From Tarkov", "viewers": 8990, "change": 11.4, "share": 0.7, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/491931-285x380.jpg"},
                {"title": "Lost Ark", "viewers": 8768, "change": -6.8, "share": 0.7, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/490100-285x380.jpg"},
                {"title": "New World", "viewers": 8546, "change": 7.9, "share": 0.6, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/493597-285x380.jpg"},
                {"title": "Destiny 2", "viewers": 8324, "change": 3.1, "share": 0.6, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/497057-285x380.jpg"},
                {"title": "Diablo IV", "viewers": 8102, "change": 14.7, "share": 0.6, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/515024-285x380.jpg"},
                {"title": "Path of Exile", "viewers": 7880, "change": -2.9, "share": 0.6, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/29307-285x380.jpg"},
                {"title": "Warframe", "viewers": 7658, "change": 5.4, "share": 0.6, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/66170-285x380.jpg"},
                
                # 31-40
                {"title": "Sea of Thieves", "viewers": 7436, "change": 8.6, "share": 0.5, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/490377-285x380.jpg"},
                {"title": "Terraria", "viewers": 7214, "change": 2.4, "share": 0.5, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/31376-285x380.jpg"},
                {"title": "Stardew Valley", "viewers": 6992, "change": 12.1, "share": 0.5, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/490744-285x380.jpg"},
                {"title": "Cyberpunk 2077", "viewers": 6770, "change": -4.3, "share": 0.5, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/65876-285x380.jpg"},
                {"title": "The Witcher 3", "viewers": 6548, "change": 6.7, "share": 0.5, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/115977-285x380.jpg"},
                {"title": "Dark Souls III", "viewers": 6326, "change": 1.5, "share": 0.5, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/490292-285x380.jpg"},
                {"title": "Elden Ring", "viewers": 6104, "change": 18.9, "share": 0.4, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/512953-285x380.jpg"},
                {"title": "Hades", "viewers": 5882, "change": 4.8, "share": 0.4, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/508455-285x380.jpg"},
                {"title": "Hollow Knight", "viewers": 5660, "change": 3.2, "share": 0.4, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/490184-285x380.jpg"},
                {"title": "Cities: Skylines", "viewers": 5438, "change": 7.3, "share": 0.4, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/369252-285x380.jpg"},
                
                # 41-50
                {"title": "Factorio", "viewers": 5216, "change": 9.7, "share": 0.4, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/31518-285x380.jpg"},
                {"title": "RimWorld", "viewers": 4994, "change": 2.9, "share": 0.4, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/394568-285x380.jpg"},
                {"title": "Europa Universalis IV", "viewers": 4772, "change": 1.6, "share": 0.3, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/32597-285x380.jpg"},
                {"title": "Total War: Warhammer III", "viewers": 4550, "change": 5.8, "share": 0.3, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/513115-285x380.jpg"},
                {"title": "Civilization VI", "viewers": 4328, "change": -1.7, "share": 0.3, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/461449-285x380.jpg"},
                {"title": "Age of Empires IV", "viewers": 4106, "change": 8.4, "share": 0.3, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/506416-285x380.jpg"},
                {"title": "Crusader Kings III", "viewers": 3884, "change": 3.7, "share": 0.3, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/514888-285x380.jpg"},
                {"title": "Stellaris", "viewers": 3662, "change": 6.2, "share": 0.3, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/491572-285x380.jpg"},
                {"title": "Hearts of Iron IV", "viewers": 3440, "change": 2.1, "share": 0.2, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/394552-285x380.jpg"},
                {"title": "Anno 1800", "viewers": 3218, "change": 4.5, "share": 0.2, "image_url": "https://static-cdn.jtvnw.net/ttv-boxart/499003-285x380.jpg"}
            ]
            
            # Ajout des timestamps et insertion
            timestamp = datetime.now()
            success_count = 0
            
            for game_data in sample_games:
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
                    logger.error(f"❌ Erreur insertion {game_data['title']}: {e}")
            
            logger.info(f"✅ {success_count}/{len(sample_games)} jeux d'exemple insérés")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ Erreur insertion données d'exemple: {e}")
            return False
    
    def close_connection(self):
        """Ferme la connexion à MongoDB."""
        if self.client:
            self.client.close()
            logger.info("✅ Connexion MongoDB fermée")


# Instance globale du gestionnaire de base de données
db_manager = DatabaseManager()
