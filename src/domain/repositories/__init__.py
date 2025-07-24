"""Repository interfaces for the domain layer."""

from .game_repository import GameRepository
from .streamer_repository import StreamerRepository
from .event_repository import EventRepository
from .trending_repository import TrendingRepository

__all__ = [
    'GameRepository',
    'StreamerRepository',
    'EventRepository',
    'TrendingRepository'
]
