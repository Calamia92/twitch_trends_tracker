"""Trending data entity for aggregated trending information."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class TrendingData:
    """Represents aggregated trending data for analysis."""
    
    # Time period information
    period_start: datetime
    period_end: datetime
    period_type: str  # 'hourly', 'daily', 'weekly', etc.
    
    # Trending games data
    top_games: Optional[List[Dict[str, Any]]] = None  # List of game data dicts
    total_game_viewers: int = 0
    total_game_channels: int = 0
    
    # Trending streamers data
    top_streamers: Optional[List[Dict[str, Any]]] = None  # List of streamer data dicts
    total_streamer_viewers: int = 0
    total_live_streamers: int = 0
    
    # Platform-wide statistics
    platform_total_viewers: Optional[int] = None
    platform_total_channels: Optional[int] = None
    
    # Growth metrics
    viewer_growth_rate: Optional[float] = None
    channel_growth_rate: Optional[float] = None
    
    # Data sources
    sources: Optional[List[str]] = None  # ['twitch_api', 'twitchtracker', etc.]
    
    # Metadata
    created_at: Optional[datetime] = None
    data_quality_score: Optional[float] = None  # 0.0 to 1.0
    
    def __post_init__(self):
        """Post-initialization to set defaults."""
        if self.sources is None:
            self.sources = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.top_games is None:
            self.top_games = []
        if self.top_streamers is None:
            self.top_streamers = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the trending data entity to a dictionary."""
        return {
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'period_type': self.period_type,
            'top_games': self.top_games,
            'total_game_viewers': self.total_game_viewers,
            'total_game_channels': self.total_game_channels,
            'top_streamers': self.top_streamers,
            'total_streamer_viewers': self.total_streamer_viewers,
            'total_live_streamers': self.total_live_streamers,
            'platform_total_viewers': self.platform_total_viewers,
            'platform_total_channels': self.platform_total_channels,
            'viewer_growth_rate': self.viewer_growth_rate,
            'channel_growth_rate': self.channel_growth_rate,
            'sources': self.sources,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'data_quality_score': self.data_quality_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrendingData':
        """Create a TrendingData entity from a dictionary."""
        # Convert ISO strings back to datetime objects
        datetime_fields = ['period_start', 'period_end', 'created_at']
        for field in datetime_fields:
            if field in data and data[field]:
                data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
        
        return cls(**data)
    
    def add_game_data(self, game_data: Dict[str, Any]) -> None:
        """Add a game to the trending games list."""
        if self.top_games is None:
            self.top_games = []
        self.top_games.append(game_data)
        if 'viewers' in game_data and game_data['viewers']:
            self.total_game_viewers += game_data['viewers']
        if 'channels' in game_data and game_data['channels']:
            self.total_game_channels += game_data['channels']
    
    def add_streamer_data(self, streamer_data: Dict[str, Any]) -> None:
        """Add a streamer to the trending streamers list."""
        if self.top_streamers is None:
            self.top_streamers = []
        self.top_streamers.append(streamer_data)
        if 'viewer_count' in streamer_data and streamer_data['viewer_count']:
            self.total_streamer_viewers += streamer_data['viewer_count']
        if 'is_live' in streamer_data and streamer_data['is_live']:
            self.total_live_streamers += 1
    
    def get_top_games_by_viewers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top games sorted by viewer count."""
        if not self.top_games:
            return []
        sorted_games = sorted(
            self.top_games,
            key=lambda x: x.get('viewers', 0),
            reverse=True
        )
        return sorted_games[:limit]
    
    def get_top_streamers_by_viewers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top streamers sorted by viewer count."""
        if not self.top_streamers:
            return []
        sorted_streamers = sorted(
            self.top_streamers,
            key=lambda x: x.get('viewer_count', 0),
            reverse=True
        )
        return sorted_streamers[:limit]
    
    def calculate_data_quality_score(self) -> float:
        """Calculate a data quality score based on completeness."""
        total_fields = 0
        filled_fields = 0
        
        # Check core fields
        core_fields = [
            self.period_start, self.period_end, self.period_type,
            self.total_game_viewers, self.total_game_channels,
            self.total_streamer_viewers, self.total_live_streamers
        ]
        
        for field in core_fields:
            total_fields += 1
            if field is not None and field != 0:
                filled_fields += 1
        
        # Check if we have data
        if self.top_games:
            filled_fields += 1
        total_fields += 1
        
        if self.top_streamers:
            filled_fields += 1
        total_fields += 1
        
        # Calculate score
        score = filled_fields / total_fields if total_fields > 0 else 0.0
        self.data_quality_score = round(score, 2)
        return self.data_quality_score
    
    def get_period_duration_hours(self) -> float:
        """Get the duration of the trending period in hours."""
        if self.period_start and self.period_end:
            duration = self.period_end - self.period_start
            return duration.total_seconds() / 3600
        return 0.0
