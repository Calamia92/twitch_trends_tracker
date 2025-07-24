"""Streamer entity representing a Twitch streamer."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class Streamer:
    """Represents a Twitch streamer with all their associated data."""
    
    username: str
    display_name: Optional[str] = None
    viewer_count: Optional[int] = None
    follower_count: Optional[int] = None
    subscriber_count: Optional[int] = None
    
    # Stream information
    is_live: bool = False
    current_game: Optional[str] = None
    stream_title: Optional[str] = None
    stream_language: Optional[str] = None
    stream_started_at: Optional[datetime] = None
    
    # Profile information
    profile_image_url: Optional[str] = None
    offline_image_url: Optional[str] = None
    description: Optional[str] = None
    twitch_id: Optional[str] = None
    
    # TwitchTracker specific data
    peak_viewers: Optional[int] = None
    avg_viewers: Optional[int] = None
    hours_watched: Optional[int] = None
    hours_streamed: Optional[int] = None
    total_views: Optional[int] = None
    
    # Categories/Tags
    tags: Optional[List[str]] = None
    mature: bool = False
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source: Optional[str] = None  # 'twitch_api', 'twitchtracker', etc.
    
    def __post_init__(self):
        """Post-initialization to set timestamps and defaults."""
        if self.tags is None:
            self.tags = []
        if self.display_name is None:
            self.display_name = self.username
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the streamer entity to a dictionary."""
        return {
            'username': self.username,
            'display_name': self.display_name,
            'viewer_count': self.viewer_count,
            'follower_count': self.follower_count,
            'subscriber_count': self.subscriber_count,
            'is_live': self.is_live,
            'current_game': self.current_game,
            'stream_title': self.stream_title,
            'stream_language': self.stream_language,
            'stream_started_at': self.stream_started_at.isoformat() if self.stream_started_at else None,
            'profile_image_url': self.profile_image_url,
            'offline_image_url': self.offline_image_url,
            'description': self.description,
            'twitch_id': self.twitch_id,
            'peak_viewers': self.peak_viewers,
            'avg_viewers': self.avg_viewers,
            'hours_watched': self.hours_watched,
            'hours_streamed': self.hours_streamed,
            'total_views': self.total_views,
            'tags': self.tags,
            'mature': self.mature,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'source': self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Streamer':
        """Create a Streamer entity from a dictionary."""
        # Convert ISO strings back to datetime objects
        datetime_fields = ['created_at', 'updated_at', 'stream_started_at']
        for field in datetime_fields:
            if field in data and data[field]:
                data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
        
        return cls(**data)
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update the streamer entity with new data."""
        for key, value in data.items():
            if hasattr(self, key) and key not in ['created_at']:  # Don't update created_at
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
    
    def is_trending(self, viewer_threshold: int = 1000) -> bool:
        """Check if the streamer is trending based on viewer count."""
        return self.viewer_count is not None and self.viewer_count >= viewer_threshold
    
    def get_stream_duration(self) -> Optional[int]:
        """Get stream duration in minutes if currently live."""
        if self.is_live and self.stream_started_at:
            duration = datetime.utcnow() - self.stream_started_at
            return int(duration.total_seconds() / 60)
        return None
