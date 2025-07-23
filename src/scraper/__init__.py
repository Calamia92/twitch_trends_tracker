"""
Module de scraping Twitch.

Contient toute la logique de scraping avec Selenium et gestion d'erreurs.
"""

from .twitch_scraper import TwitchScraper, main

__all__ = ['TwitchScraper', 'main']
