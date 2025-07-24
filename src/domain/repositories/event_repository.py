"""Event repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.event import Event, EventType


class EventRepository(ABC):
    """Abstract repository for Event entities."""
    
    @abstractmethod
    def save(self, event: Event) -> Event:
        """Save an event entity."""
        pass
    
    @abstractmethod
    def find_by_id(self, event_id: str) -> Optional[Event]:
        """Find an event by ID."""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Event]:
        """Get all events."""
        pass
    
    @abstractmethod
    def find_by_type(self, event_type: EventType) -> List[Event]:
        """Find events by type."""
        pass
    
    @abstractmethod
    def find_by_game(self, game_name: str) -> List[Event]:
        """Find events related to a specific game."""
        pass
    
    @abstractmethod
    def find_by_streamer(self, streamer_username: str) -> List[Event]:
        """Find events related to a specific streamer."""
        pass
    
    @abstractmethod
    def find_by_time_range(self, start_time: datetime, end_time: datetime) -> List[Event]:
        """Find events within a time range."""
        pass
    
    @abstractmethod
    def find_recent(self, hours: int = 24) -> List[Event]:
        """Find recent events within the last N hours."""
        pass
    
    @abstractmethod
    def find_by_source(self, source: str) -> List[Event]:
        """Find events by data source."""
        pass
    
    @abstractmethod
    def find_trending_events(self, limit: int = 10) -> List[Event]:
        """Find the most significant trending events."""
        pass
    
    @abstractmethod
    def update(self, event: Event) -> Event:
        """Update an existing event."""
        pass
    
    @abstractmethod
    def delete(self, event_id: str) -> bool:
        """Delete an event by ID."""
        pass
    
    @abstractmethod
    def bulk_save(self, events: List[Event]) -> List[Event]:
        """Save multiple events at once."""
        pass
    
    @abstractmethod
    def get_event_statistics(self) -> Dict[str, Any]:
        """Get aggregate statistics about events."""
        pass
    
    @abstractmethod
    def get_event_counts_by_type(self) -> Dict[str, int]:
        """Get count of events by type."""
        pass
    
    @abstractmethod
    def get_event_timeline(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get event timeline for the last N hours."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get total count of events."""
        pass
    
    @abstractmethod
    def count_by_type(self, event_type: EventType) -> int:
        """Get count of events by type."""
        pass
    
    @abstractmethod
    def delete_old_events(self, days: int = 30) -> int:
        """Delete events older than N days. Returns count of deleted events."""
        pass
