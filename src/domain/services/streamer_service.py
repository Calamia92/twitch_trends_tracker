"""Streamer domain service."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..entities.streamer import Streamer
from ..entities.event import Event, EventType
from ..repositories.streamer_repository import StreamerRepository
from ..repositories.event_repository import EventRepository


class StreamerService:
    """Domain service for streamer-related business logic."""
    
    def __init__(self, streamer_repository: StreamerRepository, event_repository: EventRepository):
        self.streamer_repository = streamer_repository
        self.event_repository = event_repository
    
    def create_or_update_streamer(self, streamer_data: Dict[str, Any]) -> Streamer:
        """Create a new streamer or update existing one."""
        existing_streamer = self.streamer_repository.find_by_username(streamer_data['username'])
        
        if existing_streamer:
            # Check for significant changes
            old_viewers = existing_streamer.viewer_count or 0
            new_viewers = streamer_data.get('viewer_count', 0)
            old_live_status = existing_streamer.is_live
            new_live_status = streamer_data.get('is_live', False)
            
            # Update the streamer
            existing_streamer.update_from_dict(streamer_data)
            updated_streamer = self.streamer_repository.update(existing_streamer)
            
            # Create events for significant changes
            self._create_streamer_events(updated_streamer, old_viewers, new_viewers, old_live_status, new_live_status)
            
            return updated_streamer
        else:
            # Create new streamer
            streamer = Streamer.from_dict(streamer_data)
            saved_streamer = self.streamer_repository.save(streamer)
            
            # Create discovery event if they're live
            if saved_streamer.is_live:
                event = Event(
                    event_type=EventType.STREAMER_WENT_LIVE,
                    title=f"Streamer '{saved_streamer.username}' went live",
                    description=f"Now streaming {saved_streamer.current_game or 'Unknown'} with {saved_streamer.viewer_count or 0:,} viewers",
                    streamer_username=saved_streamer.username,
                    game_name=saved_streamer.current_game,
                    viewer_count=saved_streamer.viewer_count,
                    source=saved_streamer.source
                )
                self.event_repository.save(event)
            
            return saved_streamer
    
    def get_trending_streamers(self, viewer_threshold: int = 1000) -> List[Streamer]:
        """Get streamers that are currently trending."""
        trending_streamers = self.streamer_repository.find_trending(viewer_threshold)
        
        # Create trending events for top streamers
        for streamer in trending_streamers[:10]:  # Top 10 only
            event = Event.create_streamer_trending_event(
                streamer_username=streamer.username,
                viewer_count=streamer.viewer_count or 0,
                game_name=streamer.current_game
            )
            self.event_repository.save(event)
        
        return trending_streamers
    
    def get_live_streamers_by_game(self, game_name: str) -> List[Streamer]:
        """Get all live streamers playing a specific game."""
        game_streamers = self.streamer_repository.find_by_game(game_name)
        return [streamer for streamer in game_streamers if streamer.is_live]
    
    def analyze_streamer_performance(self, username: str) -> Dict[str, Any]:
        """Analyze a streamer's performance metrics."""
        streamer = self.streamer_repository.find_by_username(username)
        if not streamer:
            return {'error': 'Streamer not found'}
        
        # Get recent events for this streamer
        recent_events = self.event_repository.find_by_streamer(username)
        
        # Calculate performance metrics
        performance = {
            'username': streamer.username,
            'display_name': streamer.display_name,
            'current_viewers': streamer.viewer_count,
            'follower_count': streamer.follower_count,
            'is_live': streamer.is_live,
            'current_game': streamer.current_game,
            'is_trending': streamer.is_trending(),
            'stream_duration_minutes': streamer.get_stream_duration(),
            'recent_events_count': len(recent_events),
            'peak_viewers': streamer.peak_viewers,
            'avg_viewers': streamer.avg_viewers,
            'total_views': streamer.total_views,
            'hours_streamed': streamer.hours_streamed,
            'last_updated': streamer.updated_at.isoformat() if streamer.updated_at else None
        }
        
        # Add engagement rate if we have the data
        if streamer.avg_viewers and streamer.follower_count:
            performance['engagement_rate'] = (streamer.avg_viewers / streamer.follower_count) * 100
        
        return performance
    
    def get_streamer_recommendations(self, current_streamer: str, limit: int = 5) -> List[Streamer]:
        """Get streamer recommendations based on current streamer."""
        current = self.streamer_repository.find_by_username(current_streamer)
        if not current:
            return self.streamer_repository.get_top_by_viewers(limit)
        
        recommendations = []
        
        # First, try to find streamers playing the same game
        if current.current_game:
            same_game_streamers = self.get_live_streamers_by_game(current.current_game)
            recommendations.extend([s for s in same_game_streamers if s.username != current_streamer])
        
        # If we need more recommendations, add similar viewer count streamers
        if len(recommendations) < limit and current.viewer_count:
            viewer_range = current.viewer_count * 0.3  # 30% range
            min_viewers = int(current.viewer_count - viewer_range)
            max_viewers = int(current.viewer_count + viewer_range)
            
            similar_streamers = self.streamer_repository.find_by_viewers_range(min_viewers, max_viewers)
            for streamer in similar_streamers:
                if streamer.username != current_streamer and streamer not in recommendations:
                    recommendations.append(streamer)
                    if len(recommendations) >= limit:
                        break
        
        return recommendations[:limit]
    
    def update_stream_status(self, username: str, is_live: bool, current_game: Optional[str] = None) -> bool:
        """Update a streamer's live status and create appropriate events."""
        success = self.streamer_repository.update_stream_status(username, is_live, current_game)
        
        if success:
            # Create appropriate event
            event_type = EventType.STREAMER_WENT_LIVE if is_live else EventType.STREAMER_WENT_OFFLINE
            title = f"Streamer '{username}' went {'live' if is_live else 'offline'}"
            description = f"Now {'streaming' if is_live else 'offline'}"
            
            if is_live and current_game:
                description += f" {current_game}"
            
            event = Event(
                event_type=event_type,
                title=title,
                description=description,
                streamer_username=username,
                game_name=current_game if is_live else None
            )
            self.event_repository.save(event)
        
        return success
    
    def get_streamer_statistics(self) -> Dict[str, Any]:
        """Get comprehensive streamer statistics."""
        stats = self.streamer_repository.get_statistics()
        trending_count = len(self.streamer_repository.find_trending())
        live_count = self.streamer_repository.count_live()
        
        return {
            **stats,
            'live_streamers_count': live_count,
            'trending_streamers_count': trending_count,
            'trending_threshold': 1000,
            'last_analysis': datetime.utcnow().isoformat()
        }
    
    def search_streamers(self, query: str, include_stats: bool = False) -> List[Dict[str, Any]]:
        """Search for streamers and optionally include statistics."""
        streamers = self.streamer_repository.search_by_username(query)
        
        if not include_stats:
            return [streamer.to_dict() for streamer in streamers]
        
        # Include additional statistics for each streamer
        enriched_streamers = []
        for streamer in streamers:
            streamer_dict = streamer.to_dict()
            streamer_dict['is_trending'] = streamer.is_trending()
            streamer_dict['stream_duration_minutes'] = streamer.get_stream_duration()
            
            # Get recent events for this streamer
            recent_events = self.event_repository.find_by_streamer(streamer.username)
            streamer_dict['recent_events_count'] = len(recent_events)
            
            enriched_streamers.append(streamer_dict)
        
        return enriched_streamers
    
    def _create_streamer_events(self, streamer: Streamer, old_viewers: int, new_viewers: int, 
                               old_live_status: bool, new_live_status: bool) -> None:
        """Create events based on streamer changes."""
        # Live status change events
        if old_live_status != new_live_status:
            event_type = EventType.STREAMER_WENT_LIVE if new_live_status else EventType.STREAMER_WENT_OFFLINE
            title = f"Streamer '{streamer.username}' went {'live' if new_live_status else 'offline'}"
            description = f"Now {'streaming' if new_live_status else 'offline'}"
            
            if new_live_status and streamer.current_game:
                description += f" {streamer.current_game}"
            
            event = Event(
                event_type=event_type,
                title=title,
                description=description,
                streamer_username=streamer.username,
                game_name=streamer.current_game if new_live_status else None,
                viewer_count=new_viewers if new_live_status else None
            )
            self.event_repository.save(event)
        
        # Viewer spike events (only when live)
        elif new_live_status and self._is_significant_change(old_viewers, new_viewers):
            event = Event.create_viewer_spike_event(
                streamer_username=streamer.username,
                current_viewers=new_viewers,
                previous_viewers=old_viewers
            )
            self.event_repository.save(event)
    
    def _is_significant_change(self, old_value: int, new_value: int, threshold_percent: float = 25.0) -> bool:
        """Check if a change is significant enough to warrant an event."""
        if old_value == 0:
            return new_value > 500  # Arbitrary threshold for new streamers
        
        change_percent = abs((new_value - old_value) / old_value) * 100
        return change_percent >= threshold_percent and abs(new_value - old_value) >= 100
