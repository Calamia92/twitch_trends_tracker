"""Streamer repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.streamer import Streamer


class StreamerRepository(ABC):
    """Abstract repository for Streamer entities."""
    
    @abstractmethod
    def save(self, streamer: Streamer) -> Streamer:
        """Save a streamer entity."""
        pass
    
    @abstractmethod
    def find_by_username(self, username: str) -> Optional[Streamer]:
        """Find a streamer by username."""
        pass
    
    @abstractmethod
    def find_by_id(self, streamer_id: str) -> Optional[Streamer]:
        """Find a streamer by ID."""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Streamer]:
        """Get all streamers."""
        pass
    
    @abstractmethod
    def find_live_streamers(self) -> List[Streamer]:
        """Find all currently live streamers."""
        pass
    
    @abstractmethod
    def find_trending(self, viewer_threshold: int = 1000) -> List[Streamer]:
        """Find streamers that are currently trending."""
        pass
    
    @abstractmethod
    def find_by_game(self, game_name: str) -> List[Streamer]:
        """Find streamers playing a specific game."""
        pass
    
    @abstractmethod
    def find_by_viewers_range(self, min_viewers: int, max_viewers: int) -> List[Streamer]:
        """Find streamers within a viewer count range."""
        pass
    
    @abstractmethod
    def find_by_language(self, language: str) -> List[Streamer]:
        """Find streamers by stream language."""
        pass
    
    @abstractmethod
    def find_by_source(self, source: str) -> List[Streamer]:
        """Find streamers by data source."""
        pass
    
    @abstractmethod
    def find_updated_since(self, since: datetime) -> List[Streamer]:
        """Find streamers updated since a specific datetime."""
        pass
    
    @abstractmethod
    def update(self, streamer: Streamer) -> Streamer:
        """Update an existing streamer."""
        pass
    
    @abstractmethod
    def delete(self, streamer_id: str) -> bool:
        """Delete a streamer by ID."""
        pass
    
    @abstractmethod
    def bulk_save(self, streamers: List[Streamer]) -> List[Streamer]:
        """Save multiple streamers at once."""
        pass
    
    @abstractmethod
    def get_top_by_viewers(self, limit: int = 10) -> List[Streamer]:
        """Get top streamers by viewer count."""
        pass
    
    @abstractmethod
    def get_top_by_followers(self, limit: int = 10) -> List[Streamer]:
        """Get top streamers by follower count."""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregate statistics about streamers."""
        pass
    
    @abstractmethod
    def search_by_username(self, query: str) -> List[Streamer]:
        """Search streamers by username pattern."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get total count of streamers."""
        pass
    
    @abstractmethod
    def count_live(self) -> int:
        """Get count of currently live streamers."""
        pass
    
    @abstractmethod
    def exists(self, username: str) -> bool:
        """Check if a streamer exists by username."""
        pass
    
    @abstractmethod
    def update_stream_status(self, username: str, is_live: bool, current_game: Optional[str] = None) -> bool:
        """Update a streamer's live status and current game."""
        pass
