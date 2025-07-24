"""Game domain service."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..entities.game import Game
from ..entities.event import Event, EventType
from ..repositories.game_repository import GameRepository
from ..repositories.event_repository import EventRepository


class GameService:
    """Domain service for game-related business logic."""
    
    def __init__(self, game_repository: GameRepository, event_repository: EventRepository):
        self.game_repository = game_repository
        self.event_repository = event_repository
    
    def create_or_update_game(self, game_data: Dict[str, Any]) -> Game:
        """Create a new game or update existing one."""
        existing_game = self.game_repository.find_by_name(game_data['name'])
        
        if existing_game:
            # Check for significant changes that warrant an event
            old_viewers = existing_game.viewers or 0
            new_viewers = game_data.get('viewers', 0)
            
            # Update the game
            existing_game.update_from_dict(game_data)
            updated_game = self.game_repository.update(existing_game)
            
            # Create event if significant viewer change
            if self._is_significant_change(old_viewers, new_viewers):
                event = Event.create_viewer_spike_event(
                    game_name=updated_game.name,
                    current_viewers=new_viewers,
                    previous_viewers=old_viewers
                )
                self.event_repository.save(event)
            
            return updated_game
        else:
            # Create new game
            game = Game.from_dict(game_data)
            saved_game = self.game_repository.save(game)
            
            # Create discovery event
            event = Event(
                event_type=EventType.NEW_GAME_DISCOVERED,
                title=f"New game discovered: {saved_game.name}",
                description=f"Game found with {saved_game.viewers or 0:,} viewers",
                game_name=saved_game.name,
                viewer_count=saved_game.viewers,
                source=saved_game.source
            )
            self.event_repository.save(event)
            
            return saved_game
    
    def get_trending_games(self, viewer_threshold: int = 10000) -> List[Game]:
        """Get games that are currently trending."""
        trending_games = self.game_repository.find_trending(viewer_threshold)
        
        # Create trending events for top games
        for game in trending_games[:5]:  # Top 5 only
            event = Event.create_game_trending_event(
                game_name=game.name,
                viewer_count=game.viewers or 0
            )
            self.event_repository.save(event)
        
        return trending_games
    
    def analyze_game_growth(self, game_name: str, days: int = 7) -> Dict[str, Any]:
        """Analyze a game's growth over time."""
        # This would typically fetch historical data
        # For now, return current state analysis
        game = self.game_repository.find_by_name(game_name)
        if not game:
            return {'error': 'Game not found'}
        
        return {
            'game_name': game.name,
            'current_viewers': game.viewers,
            'current_channels': game.channels,
            'is_trending': game.is_trending(),
            'analysis_period_days': days,
            'last_updated': game.updated_at.isoformat() if game.updated_at else None
        }
    
    def get_game_recommendations(self, current_game: str, limit: int = 5) -> List[Game]:
        """Get game recommendations based on current game."""
        # Simple recommendation: games with similar viewer counts
        current = self.game_repository.find_by_name(current_game)
        if not current or not current.viewers:
            return self.game_repository.get_top_by_viewers(limit)
        
        # Find games with viewer counts in a similar range
        viewer_range = current.viewers * 0.2  # 20% range
        min_viewers = int(current.viewers - viewer_range)
        max_viewers = int(current.viewers + viewer_range)
        
        similar_games = self.game_repository.find_by_viewers_range(min_viewers, max_viewers)
        
        # Filter out the current game and return top ones
        recommendations = [game for game in similar_games if game.name != current_game]
        return recommendations[:limit]
    
    def mark_games_as_trending(self, games: List[Game]) -> List[Event]:
        """Mark multiple games as trending and create events."""
        events = []
        for game in games:
            if game.is_trending():
                event = Event.create_game_trending_event(
                    game_name=game.name,
                    viewer_count=game.viewers or 0
                )
                saved_event = self.event_repository.save(event)
                events.append(saved_event)
        return events
    
    def get_game_statistics(self) -> Dict[str, Any]:
        """Get comprehensive game statistics."""
        stats = self.game_repository.get_statistics()
        trending_count = len(self.game_repository.find_trending())
        
        return {
            **stats,
            'trending_games_count': trending_count,
            'trending_threshold': 10000,
            'last_analysis': datetime.utcnow().isoformat()
        }
    
    def search_games(self, query: str, include_stats: bool = False) -> List[Dict[str, Any]]:
        """Search for games and optionally include statistics."""
        games = self.game_repository.search_by_name(query)
        
        if not include_stats:
            return [game.to_dict() for game in games]
        
        # Include additional statistics for each game
        enriched_games = []
        for game in games:
            game_dict = game.to_dict()
            game_dict['is_trending'] = game.is_trending()
            
            # Get recent events for this game
            recent_events = self.event_repository.find_by_game(game.name)
            game_dict['recent_events_count'] = len(recent_events)
            
            enriched_games.append(game_dict)
        
        return enriched_games
    
    def _is_significant_change(self, old_value: int, new_value: int, threshold_percent: float = 20.0) -> bool:
        """Check if a change is significant enough to warrant an event."""
        if old_value == 0:
            return new_value > 1000  # Arbitrary threshold for new games
        
        change_percent = abs((new_value - old_value) / old_value) * 100
        return change_percent >= threshold_percent and abs(new_value - old_value) >= 1000
