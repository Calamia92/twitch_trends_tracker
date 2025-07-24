"""
Module de gestion des exports de données.

Ce module fournit des fonctionnalités d'export vers différents formats
(CSV, JSON) conformément aux exigences du PDF.

Auteurs: Hicham, Aya, Boubaker
Date: Juillet 2025
"""

import csv
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import sys
import os

# Add project root to path for config imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import config

# Configuration du logger
logger = logging.getLogger(__name__)


class ExportManager:
    """
    Gestionnaire d'export pour les données scrapées.
    
    Prend en charge l'export vers CSV et JSON conformément
    aux exigences du PDF du projet.
    """
    
    def __init__(self):
        """Initialise le gestionnaire d'export."""
        self.export_dir = config.export.BASE_EXPORT_DIR
        self._ensure_export_directory()
    
    def _ensure_export_directory(self):
        """Crée le répertoire d'export s'il n'existe pas."""
        try:
            self.export_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"📁 Répertoire d'export: {self.export_dir}")
        except Exception as e:
            logger.error(f"❌ Erreur création répertoire export: {e}")
    
    def _generate_filename(self, format_type: str) -> str:
        """
        Génère un nom de fichier avec timestamp.
        
        Args:
            format_type: Type de format ('csv' ou 'json')
            
        Returns:
            str: Nom de fichier généré
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == 'csv':
            return f"{config.export.CSV_PREFIX}_{timestamp}.csv"
        elif format_type == 'json':
            return f"{config.export.JSON_PREFIX}_{timestamp}.json"
        else:
            return f"export_{timestamp}.{format_type}"
    
    def export_to_csv(self, data: List[Dict[str, Any]]) -> bool:
        """
        Exporte les données vers un fichier CSV.
        
        Args:
            data: Liste des données à exporter
            
        Returns:
            bool: True si l'export réussit
        """
        if not data:
            logger.warning("⚠️ Aucune donnée à exporter en CSV")
            return False
        
        try:
            filename = self._generate_filename('csv')
            filepath = self.export_dir / filename
            
            # Extraction des clés pour l'en-tête
            fieldnames = set()
            for item in data:
                fieldnames.update(item.keys())
            
            fieldnames = sorted(list(fieldnames))
            
            # Écriture du fichier CSV
            with open(filepath, 'w', newline='', encoding=config.export.FILE_ENCODING) as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # En-tête
                writer.writeheader()
                
                # Données
                for item in data:
                    # Conversion des valeurs complexes en string
                    row = {}
                    for key, value in item.items():
                        if isinstance(value, (dict, list)):
                            row[key] = json.dumps(value)
                        elif isinstance(value, datetime):
                            row[key] = value.isoformat()
                        else:
                            row[key] = value
                    
                    writer.writerow(row)
            
            logger.info(f"✅ Export CSV réussi: {filename}")
            logger.info(f"📊 {len(data)} enregistrements exportés")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur export CSV: {e}")
            return False
    
    def export_to_json(self, data: List[Dict[str, Any]]) -> bool:
        """
        Exporte les données vers un fichier JSON.
        
        Args:
            data: Liste des données à exporter
            
        Returns:
            bool: True si l'export réussit
        """
        if not data:
            logger.warning("⚠️ Aucune donnée à exporter en JSON")
            return False
        
        try:
            filename = self._generate_filename('json')
            filepath = self.export_dir / filename
            
            # Préparation des données pour JSON
            json_data = []
            for item in data:
                json_item = {}
                for key, value in item.items():
                    if isinstance(value, datetime):
                        json_item[key] = value.isoformat()
                    else:
                        json_item[key] = value
                json_data.append(json_item)
            
            # Structure du fichier JSON avec métadonnées
            export_structure = {
                "metadata": {
                    "export_timestamp": datetime.now().isoformat(),
                    "total_records": len(json_data),
                    "source": "Twitch Trends Tracker",
                    "authors": ["Hicham", "Aya", "Boubaker"]
                },
                "data": json_data
            }
            
            # Écriture du fichier JSON
            with open(filepath, 'w', encoding=config.export.FILE_ENCODING) as jsonfile:
                json.dump(
                    export_structure,
                    jsonfile,
                    indent=2,
                    ensure_ascii=False,
                    default=str  # Fallback pour types non sérialisables
                )
            
            logger.info(f"✅ Export JSON réussi: {filename}")
            logger.info(f"📊 {len(data)} enregistrements exportés")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur export JSON: {e}")
            return False
    
    def export_both_formats(self, data: List[Dict[str, Any]]) -> tuple[bool, bool]:
        """
        Exporte vers CSV et JSON simultanément.
        
        Args:
            data: Données à exporter
            
        Returns:
            tuple: (csv_success, json_success)
        """
        csv_success = self.export_to_csv(data)
        json_success = self.export_to_json(data)
        
        return csv_success, json_success
    
    def get_export_files(self) -> List[Path]:
        """
        Retourne la liste des fichiers d'export existants.
        
        Returns:
            List[Path]: Liste des fichiers d'export
        """
        try:
            export_files = []
            for pattern in ["*.csv", "*.json"]:
                export_files.extend(self.export_dir.glob(pattern))
            
            # Tri par date de modification (plus récent en premier)
            export_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            return export_files
            
        except Exception as e:
            logger.error(f"❌ Erreur listage fichiers export: {e}")
            return []
    
    def cleanup_old_exports(self, keep_count: int = 10) -> int:
        """
        Supprime les anciens fichiers d'export.
        
        Args:
            keep_count: Nombre de fichiers à conserver
            
        Returns:
            int: Nombre de fichiers supprimés
        """
        try:
            export_files = self.get_export_files()
            
            if len(export_files) <= keep_count:
                logger.info(f"📁 {len(export_files)} fichiers d'export, nettoyage non nécessaire")
                return 0
            
            # Fichiers à supprimer (les plus anciens)
            files_to_delete = export_files[keep_count:]
            deleted_count = 0
            
            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.debug(f"🗑️ Supprimé: {file_path.name}")
                except Exception as e:
                    logger.warning(f"⚠️ Erreur suppression {file_path.name}: {e}")
            
            logger.info(f"🧹 {deleted_count} anciens fichiers d'export supprimés")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Erreur nettoyage exports: {e}")
            return 0


# Instance globale pour faciliter l'importation
export_manager = ExportManager()
