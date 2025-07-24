"""
Module d'utilitaires pour le parsing et traitement des données.

Ce module contient toutes les fonctions utilitaires pour parser,
nettoyer et formater les données scrapées.

Auteurs: Hicham, Aya, Boubaker
Date: Juillet 2025
"""

import re
import logging
from typing import Any, Union, Optional
from datetime import datetime

# Configuration du logger
logger = logging.getLogger(__name__)


class DataParser:
    """Classe utilitaire pour parser les données scrapées."""
    
    @staticmethod
    def parse_number(text: str) -> int:
        """
        Parse les nombres avec suffixes K/M en entiers.
        
        Args:
            text: Texte contenant le nombre (ex: "1.2K", "45M", "123,456")
            
        Returns:
            int: Nombre parsé en entier
            
        Examples:
            >>> DataParser.parse_number("1.2K")
            1200
            >>> DataParser.parse_number("45M")
            45000000
            >>> DataParser.parse_number("123,456")
            123456
        """
        if not text or not isinstance(text, str):
            logger.warning(f"⚠️ Texte invalide pour parsing: {text}")
            return 0
        
        try:
            # Nettoyage du texte
            clean_text = text.replace(",", "").replace(" ", "").upper().strip()
            
            # Suppression des caractères non numériques sauf K/M et point décimal
            clean_text = re.sub(r'[^\d.KM]', '', clean_text)
            
            if not clean_text:
                return 0
            
            # Parsing selon le suffixe
            if clean_text.endswith("K"):
                number_part = clean_text[:-1]
                return int(float(number_part) * 1000)
            elif clean_text.endswith("M"):
                number_part = clean_text[:-1]
                return int(float(number_part) * 1000000)
            else:
                return int(float(clean_text))
                
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Erreur parsing nombre '{text}': {e}")
            return 0
    
    @staticmethod
    def parse_percentage(text: str) -> Optional[float]:
        """
        Parse un pourcentage en float.
        
        Args:
            text: Texte du pourcentage (ex: "12.5%", "+5.2%", "-3.1%")
            
        Returns:
            Optional[float]: Pourcentage parsé, None si erreur
        """
        if not text or not isinstance(text, str):
            return None
        
        try:
            # Nettoyage et extraction du nombre
            clean_text = text.replace("%", "").replace(" ", "").strip()
            
            # Gestion des signes + et -
            if clean_text.startswith("+"):
                clean_text = clean_text[1:]
            
            return float(clean_text)
            
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Erreur parsing pourcentage '{text}': {e}")
            return None
    
    @staticmethod
    def clean_title(title: str) -> str:
        """
        Nettoie et normalise un titre de jeu.
        
        Args:
            title: Titre brut du jeu
            
        Returns:
            str: Titre nettoyé
        """
        if not title or not isinstance(title, str):
            return "Titre inconnu"
        
        # Suppression des espaces en trop et caractères spéciaux
        clean_title = re.sub(r'\s+', ' ', title.strip())
        
        # Suppression des caractères de contrôle
        clean_title = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', clean_title)
        
        return clean_title[:100]  # Limitation à 100 caractères
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Valide une URL d'image.
        
        Args:
            url: URL à valider
            
        Returns:
            bool: True si l'URL est valide
        """
        if not url or not isinstance(url, str):
            return False
        
        # Pattern simple pour validation d'URL
        url_pattern = re.compile(
            r'^https?://'  # http:// ou https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domaine
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # port optionnel
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))


class DataFormatter:
    """Classe utilitaire pour formater les données."""
    
    @staticmethod
    def format_number(number: Union[int, float]) -> str:
        """
        Formate un nombre pour affichage avec suffixes K/M.
        
        Args:
            number: Nombre à formater
            
        Returns:
            str: Nombre formaté (ex: "1.2K", "45M")
        """
        if not isinstance(number, (int, float)):
            return "0"
        
        if number >= 1_000_000:
            return f"{number / 1_000_000:.1f}M"
        elif number >= 1_000:
            return f"{number / 1_000:.1f}K"
        else:
            return str(int(number))
    
    @staticmethod
    def format_percentage(percentage: Optional[float]) -> str:
        """
        Formate un pourcentage pour affichage.
        
        Args:
            percentage: Pourcentage à formater
            
        Returns:
            str: Pourcentage formaté avec signe
        """
        if percentage is None:
            return "N/A"
        
        sign = "+" if percentage > 0 else ""
        return f"{sign}{percentage:.1f}%"
    
    @staticmethod
    def format_timestamp(timestamp: datetime) -> str:
        """
        Formate un timestamp pour affichage.
        
        Args:
            timestamp: Timestamp à formater
            
        Returns:
            str: Timestamp formaté
        """
        if not isinstance(timestamp, datetime):
            return "Date inconnue"
        
        return timestamp.strftime("%d/%m/%Y %H:%M:%S")


class DataValidator:
    """Classe utilitaire pour valider les données."""
    
    @staticmethod
    def validate_game_data(game_data: dict) -> tuple[bool, list[str]]:
        """
        Valide les données d'un jeu avant insertion.
        
        Args:
            game_data: Dictionnaire des données du jeu
            
        Returns:
            tuple: (is_valid, error_messages)
        """
        errors = []
        
        # Vérification des champs obligatoires
        required_fields = ['title', 'viewers', 'image_url']
        for field in required_fields:
            if field not in game_data or not game_data[field]:
                errors.append(f"Champ obligatoire manquant: {field}")
        
        # Validation du titre
        if 'title' in game_data:
            title = game_data['title']
            if not isinstance(title, str) or len(title.strip()) == 0:
                errors.append("Titre invalide")
            elif len(title) > 100:
                errors.append("Titre trop long (>100 caractères)")
        
        # Validation du nombre de viewers
        if 'viewers' in game_data:
            viewers = game_data['viewers']
            if not isinstance(viewers, int) or viewers < 0:
                errors.append("Nombre de viewers invalide")
        
        # Validation de l'URL d'image
        if 'image_url' in game_data:
            url = game_data['image_url']
            if not DataParser.validate_url(url):
                errors.append("URL d'image invalide")
        
        # Validation du changement (optionnel)
        if 'change' in game_data and game_data['change'] is not None:
            change = game_data['change']
            if not isinstance(change, (int, float)):
                errors.append("Changement invalide")
        
        # Validation du share (optionnel)
        if 'share' in game_data and game_data['share'] is not None:
            share = game_data['share']
            if not isinstance(share, str) or '%' not in share:
                errors.append("Share invalide")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    @staticmethod
    def sanitize_game_data(game_data: dict) -> dict:
        """
        Nettoie et sanitise les données d'un jeu.
        
        Args:
            game_data: Données brutes du jeu
            
        Returns:
            dict: Données nettoyées
        """
        sanitized = {}
        
        # Nettoyage du titre
        if 'title' in game_data:
            sanitized['title'] = DataParser.clean_title(game_data['title'])
        
        # Parsing des viewers
        if 'viewers' in game_data:
            if isinstance(game_data['viewers'], str):
                sanitized['viewers'] = DataParser.parse_number(game_data['viewers'])
            else:
                sanitized['viewers'] = int(game_data['viewers'])
        
        # Validation de l'URL
        if 'image_url' in game_data:
            url = game_data['image_url']
            if DataParser.validate_url(url):
                sanitized['image_url'] = url
            else:
                sanitized['image_url'] = ""
        
        # Parsing du changement
        if 'change' in game_data and game_data['change'] is not None:
            if isinstance(game_data['change'], str):
                sanitized['change'] = DataParser.parse_percentage(game_data['change'])
            else:
                sanitized['change'] = float(game_data['change'])
        
        # Nettoyage du share
        if 'share' in game_data and game_data['share']:
            sanitized['share'] = str(game_data['share']).strip()
        
        # Ajout de métadonnées
        sanitized['scraped_at'] = datetime.now()
        
        return sanitized


# Instances globales pour faciliter l'importation
parser = DataParser()
formatter = DataFormatter()
validator = DataValidator()
