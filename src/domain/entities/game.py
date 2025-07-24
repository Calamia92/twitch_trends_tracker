"""Game entity representing a Twitch game."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class Game:
    """Represents a Twitch game with all its associated data."""
    
    name: str
    viewers: Optional[int] = None
    channels: Optional[int] = None
    category: Optional[str] = None
    description: Optional[str] = None
    box_art_url: Optional[str] = None
    twitch_id: Optional[str] = None
    
    # TwitchTracker specific data
    peak_viewers: Optional[int] = None
    peak_channels: Optional[int] = None
    avg_viewers: Optional[int] = None
    avg_channels: Optional[int] = None
    hours_watched: Optional[int] = None
    hours_streamed: Optional[int] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source: Optional[str] = None  # 'twitch_api', 'twitchtracker', etc.
    
    def __post_init__(self):
        """Post-initialization to set timestamps."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the game entity to a dictionary."""
        return {
            'name': self.name,
            'viewers': self.viewers,
            'channels': self.channels,
            'category': self.category,
            'description': self.description,
            'box_art_url': self.box_art_url,
            'twitch_id': self.twitch_id,
            'peak_viewers': self.peak_viewers,
            'peak_channels': self.peak_channels,
            'avg_viewers': self.avg_viewers,
            'avg_channels': self.avg_channels,
            'hours_watched': self.hours_watched,
            'hours_streamed': self.hours_streamed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'source': self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Game':
        """Create a Game entity from a dictionary."""
        # Convert ISO strings back to datetime objects
        if 'created_at' in data and data['created_at']:
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        if 'updated_at' in data and data['updated_at']:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        
        return cls(**data)
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update the game entity with new data."""
        for key, value in data.items():
            if hasattr(self, key) and key not in ['created_at']:  # Don't update created_at
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
    
    def is_trending(self, viewer_threshold: int = 10000) -> bool:
        """Check if the game is trending based on viewer count."""
        return self.viewers is not None and self.viewers >= viewer_threshold
