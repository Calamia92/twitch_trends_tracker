"""Game repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.game import Game


class GameRepository(ABC):
    """Abstract repository for Game entities."""
    
    @abstractmethod
    def save(self, game: Game) -> Game:
        """Save a game entity."""
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Game]:
        """Find a game by its name."""
        pass
    
    @abstractmethod
    def find_by_id(self, game_id: str) -> Optional[Game]:
        """Find a game by its ID."""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Game]:
        """Get all games."""
        pass
    
    @abstractmethod
    def find_trending(self, viewer_threshold: int = 10000) -> List[Game]:
        """Find games that are currently trending."""
        pass
    
    @abstractmethod
    def find_by_viewers_range(self, min_viewers: int, max_viewers: int) -> List[Game]:
        """Find games within a viewer count range."""
        pass
    
    @abstractmethod
    def find_by_source(self, source: str) -> List[Game]:
        """Find games by data source."""
        pass
    
    @abstractmethod
    def find_updated_since(self, since: datetime) -> List[Game]:
        """Find games updated since a specific datetime."""
        pass
    
    @abstractmethod
    def update(self, game: Game) -> Game:
        """Update an existing game."""
        pass
    
    @abstractmethod
    def delete(self, game_id: str) -> bool:
        """Delete a game by ID."""
        pass
    
    @abstractmethod
    def bulk_save(self, games: List[Game]) -> List[Game]:
        """Save multiple games at once."""
        pass
    
    @abstractmethod
    def get_top_by_viewers(self, limit: int = 10) -> List[Game]:
        """Get top games by viewer count."""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregate statistics about games."""
        pass
    
    @abstractmethod
    def search_by_name(self, query: str) -> List[Game]:
        """Search games by name pattern."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get total count of games."""
        pass
    
    @abstractmethod
    def exists(self, name: str) -> bool:
        """Check if a game exists by name."""
        pass
