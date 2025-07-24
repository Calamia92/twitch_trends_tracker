"""Trending data repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.trending_data import TrendingData


class TrendingRepository(ABC):
    """Abstract repository for TrendingData entities."""
    
    @abstractmethod
    def save(self, trending_data: TrendingData) -> TrendingData:
        """Save trending data entity."""
        pass
    
    @abstractmethod
    def find_by_id(self, trending_id: str) -> Optional[TrendingData]:
        """Find trending data by ID."""
        pass
    
    @abstractmethod
    def find_all(self) -> List[TrendingData]:
        """Get all trending data."""
        pass
    
    @abstractmethod
    def find_by_period_type(self, period_type: str) -> List[TrendingData]:
        """Find trending data by period type (hourly, daily, etc.)."""
        pass
    
    @abstractmethod
    def find_by_time_range(self, start_time: datetime, end_time: datetime) -> List[TrendingData]:
        """Find trending data within a time range."""
        pass
    
    @abstractmethod
    def find_latest(self, period_type: str) -> Optional[TrendingData]:
        """Find the latest trending data for a given period type."""
        pass
    
    @abstractmethod
    def find_by_sources(self, sources: List[str]) -> List[TrendingData]:
        """Find trending data by data sources."""
        pass
    
    @abstractmethod
    def find_high_quality(self, min_quality_score: float = 0.8) -> List[TrendingData]:
        """Find trending data with high quality scores."""
        pass
    
    @abstractmethod
    def update(self, trending_data: TrendingData) -> TrendingData:
        """Update existing trending data."""
        pass
    
    @abstractmethod
    def delete(self, trending_id: str) -> bool:
        """Delete trending data by ID."""
        pass
    
    @abstractmethod
    def bulk_save(self, trending_data_list: List[TrendingData]) -> List[TrendingData]:
        """Save multiple trending data entries at once."""
        pass
    
    @abstractmethod
    def get_trending_games_over_time(self, game_name: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get trending data for a specific game over time."""
        pass
    
    @abstractmethod
    def get_trending_streamers_over_time(self, streamer_username: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get trending data for a specific streamer over time."""
        pass
    
    @abstractmethod
    def get_platform_statistics(self, period_type: str = "daily", days: int = 7) -> Dict[str, Any]:
        """Get platform-wide statistics over time."""
        pass
    
    @abstractmethod
    def get_growth_metrics(self, period_type: str = "daily", days: int = 7) -> Dict[str, Any]:
        """Get growth metrics over time."""
        pass
    
    @abstractmethod
    def get_top_games_by_period(self, period_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top games for the latest period of given type."""
        pass
    
    @abstractmethod
    def get_top_streamers_by_period(self, period_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top streamers for the latest period of given type."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get total count of trending data entries."""
        pass
    
    @abstractmethod
    def count_by_period_type(self, period_type: str) -> int:
        """Get count of trending data by period type."""
        pass
    
    @abstractmethod
    def delete_old_data(self, days: int = 90) -> int:
        """Delete trending data older than N days. Returns count of deleted entries."""
        pass
    
    @abstractmethod
    def aggregate_data(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Aggregate trending data over a time period."""
        pass
