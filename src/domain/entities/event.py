"""Event entity representing significant events in Twitch data."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class EventType(Enum):
    """Types of events that can occur."""
    GAME_TRENDING = "game_trending"
    STREAMER_TRENDING = "streamer_trending"
    VIEWER_SPIKE = "viewer_spike"
    NEW_GAME_DISCOVERED = "new_game_discovered"
    STREAMER_WENT_LIVE = "streamer_went_live"
    STREAMER_WENT_OFFLINE = "streamer_went_offline"
    PEAK_VIEWERS_REACHED = "peak_viewers_reached"
    CATEGORY_CHANGE = "category_change"


@dataclass
class Event:
    """Represents an event in the Twitch ecosystem."""
    
    event_type: EventType
    title: str
    description: Optional[str] = None
    
    # Associated entities
    game_name: Optional[str] = None
    streamer_username: Optional[str] = None
    
    # Event data
    viewer_count: Optional[int] = None
    previous_value: Optional[int] = None
    new_value: Optional[int] = None
    percentage_change: Optional[float] = None
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None
    
    # Timestamps
    event_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    source: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization to set timestamps."""
        if self.event_time is None:
            self.event_time = datetime.utcnow()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the event entity to a dictionary."""
        return {
            'event_type': self.event_type.value,
            'title': self.title,
            'description': self.description,
            'game_name': self.game_name,
            'streamer_username': self.streamer_username,
            'viewer_count': self.viewer_count,
            'previous_value': self.previous_value,
            'new_value': self.new_value,
            'percentage_change': self.percentage_change,
            'metadata': self.metadata,
            'event_time': self.event_time.isoformat() if self.event_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'source': self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create an Event entity from a dictionary."""
        # Convert event_type string back to enum
        if 'event_type' in data:
            data['event_type'] = EventType(data['event_type'])
        
        # Convert ISO strings back to datetime objects
        datetime_fields = ['event_time', 'created_at']
        for field in datetime_fields:
            if field in data and data[field]:
                data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
        
        return cls(**data)
    
    @classmethod
    def create_game_trending_event(
        cls, 
        game_name: str, 
        viewer_count: int, 
        previous_count: Optional[int] = None
    ) -> 'Event':
        """Create a game trending event."""
        percentage_change = None
        if previous_count and previous_count > 0:
            percentage_change = ((viewer_count - previous_count) / previous_count) * 100
        
        return cls(
            event_type=EventType.GAME_TRENDING,
            title=f"Game '{game_name}' is trending",
            description=f"Game has {viewer_count:,} viewers",
            game_name=game_name,
            viewer_count=viewer_count,
            previous_value=previous_count,
            new_value=viewer_count,
            percentage_change=percentage_change
        )
    
    @classmethod
    def create_streamer_trending_event(
        cls, 
        streamer_username: str, 
        viewer_count: int,
        game_name: Optional[str] = None
    ) -> 'Event':
        """Create a streamer trending event."""
        description = f"Streamer has {viewer_count:,} viewers"
        if game_name:
            description += f" playing {game_name}"
        
        return cls(
            event_type=EventType.STREAMER_TRENDING,
            title=f"Streamer '{streamer_username}' is trending",
            description=description,
            streamer_username=streamer_username,
            game_name=game_name,
            viewer_count=viewer_count,
            new_value=viewer_count
        )
    
    @classmethod
    def create_viewer_spike_event(
        cls,
        game_name: Optional[str] = None,
        streamer_username: Optional[str] = None,
        current_viewers: int = 0,
        previous_viewers: int = 0
    ) -> 'Event':
        """Create a viewer spike event."""
        entity_name = game_name or streamer_username
        entity_type = "Game" if game_name else "Streamer"
        
        percentage_change = None
        if previous_viewers > 0:
            percentage_change = ((current_viewers - previous_viewers) / previous_viewers) * 100
        
        return cls(
            event_type=EventType.VIEWER_SPIKE,
            title=f"{entity_type} '{entity_name}' experiencing viewer spike",
            description=f"Viewers increased from {previous_viewers:,} to {current_viewers:,}",
            game_name=game_name,
            streamer_username=streamer_username,
            viewer_count=current_viewers,
            previous_value=previous_viewers,
            new_value=current_viewers,
            percentage_change=percentage_change
        )
