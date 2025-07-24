"""MongoDB implementation of Game repository."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection

from ...domain.entities.game import Game
from ...domain.repositories.game_repository import GameRepository


class MongoGameRepository(GameRepository):
    """MongoDB implementation of the Game repository."""
    
    def __init__(self, mongo_client: MongoClient, database_name: str = "twitch_trends"):
        self.client = mongo_client
        self.db = self.client[database_name]
        self.collection: Collection = self.db.games
        
        # Create indexes for better performance
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for better query performance."""
        self.collection.create_index("name", unique=True)
        self.collection.create_index("viewers")
        self.collection.create_index("source")
        self.collection.create_index("updated_at")
        self.collection.create_index("created_at")
    
    def save(self, game: Game) -> Game:
        """Save a game entity."""
        game_dict = game.to_dict()
        
        # Use upsert to handle both create and update
        result = self.collection.replace_one(
            {"name": game.name},
            game_dict,
            upsert=True
        )
        
        if result.upserted_id:
            game_dict["_id"] = result.upserted_id
        
        return Game.from_dict(game_dict)
    
    def find_by_name(self, name: str) -> Optional[Game]:
        """Find a game by its name."""
        doc = self.collection.find_one({"name": name})
        return Game.from_dict(doc) if doc else None
    
    def find_by_id(self, game_id: str) -> Optional[Game]:
        """Find a game by its ID."""
        from bson import ObjectId
        try:
            doc = self.collection.find_one({"_id": ObjectId(game_id)})
            return Game.from_dict(doc) if doc else None
        except:
            return None
    
    def find_all(self) -> List[Game]:
        """Get all games."""
        docs = self.collection.find().sort("viewers", -1)
        return [Game.from_dict(doc) for doc in docs]
    
    def find_trending(self, viewer_threshold: int = 10000) -> List[Game]:
        """Find games that are currently trending."""
        docs = self.collection.find({
            "viewers": {"$gte": viewer_threshold}
        }).sort("viewers", -1)
        return [Game.from_dict(doc) for doc in docs]
    
    def find_by_viewers_range(self, min_viewers: int, max_viewers: int) -> List[Game]:
        """Find games within a viewer count range."""
        docs = self.collection.find({
            "viewers": {"$gte": min_viewers, "$lte": max_viewers}
        }).sort("viewers", -1)
        return [Game.from_dict(doc) for doc in docs]
    
    def find_by_source(self, source: str) -> List[Game]:
        """Find games by data source."""
        docs = self.collection.find({"source": source}).sort("viewers", -1)
        return [Game.from_dict(doc) for doc in docs]
    
    def find_updated_since(self, since: datetime) -> List[Game]:
        """Find games updated since a specific datetime."""
        docs = self.collection.find({
            "updated_at": {"$gte": since.isoformat()}
        }).sort("updated_at", -1)
        return [Game.from_dict(doc) for doc in docs]
    
    def update(self, game: Game) -> Game:
        """Update an existing game."""
        game.updated_at = datetime.utcnow()
        return self.save(game)
    
    def delete(self, game_id: str) -> bool:
        """Delete a game by ID."""
        from bson import ObjectId
        try:
            result = self.collection.delete_one({"_id": ObjectId(game_id)})
            return result.deleted_count > 0
        except:
            return False
    
    def bulk_save(self, games: List[Game]) -> List[Game]:
        """Save multiple games at once."""
        if not games:
            return []
        
        operations = []
        for game in games:
            game_dict = game.to_dict()
            operations.append({
                "replaceOne": {
                    "filter": {"name": game.name},
                    "replacement": game_dict,
                    "upsert": True
                }
            })
        
        if operations:
            self.collection.bulk_write(operations)
        
        return games
    
    def get_top_by_viewers(self, limit: int = 10) -> List[Game]:
        """Get top games by viewer count."""
        docs = self.collection.find(
            {"viewers": {"$ne": None}}
        ).sort("viewers", -1).limit(limit)
        return [Game.from_dict(doc) for doc in docs]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregate statistics about games."""
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_games": {"$sum": 1},
                    "total_viewers": {"$sum": "$viewers"},
                    "avg_viewers": {"$avg": "$viewers"},
                    "max_viewers": {"$max": "$viewers"},
                    "min_viewers": {"$min": "$viewers"}
                }
            }
        ]
        
        result = list(self.collection.aggregate(pipeline))
        if result:
            stats = result[0]
            stats.pop("_id", None)
            return stats
        
        return {
            "total_games": 0,
            "total_viewers": 0,
            "avg_viewers": 0,
            "max_viewers": 0,
            "min_viewers": 0
        }
    
    def search_by_name(self, query: str) -> List[Game]:
        """Search games by name pattern."""
        docs = self.collection.find({
            "name": {"$regex": query, "$options": "i"}
        }).sort("viewers", -1)
        return [Game.from_dict(doc) for doc in docs]
    
    def count(self) -> int:
        """Get total count of games."""
        return self.collection.count_documents({})
    
    def exists(self, name: str) -> bool:
        """Check if a game exists by name."""
        return self.collection.count_documents({"name": name}) > 0
