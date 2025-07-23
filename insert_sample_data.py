#!/usr/bin/env python3
"""
Script pour insérer des données de test dans MongoDB.

Ce script permet de tester le dashboard avec des données réalistes
en attendant que le scraper fonctionne correctement.

Usage: python insert_sample_data.py
"""

import sys
import os

# Ajout du path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.mongodb_manager import db_manager
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Fonction principale pour insérer les données de test."""
    print("🎮 === INSERTION DES DONNÉES DE TEST ===")
    print("👥 Créé par: Hicham, Aya, Boubaker")
    print("📅 Version: Juillet 2025")
    print("--" * 25)
    
    try:
        # Vérification de la connexion MongoDB
        if not db_manager.is_connected():
            print("❌ Impossible de se connecter à MongoDB")
            print("💡 Assurez-vous que MongoDB est démarré")
            return
        
        print("✅ Connexion MongoDB établie")
        
        # Insertion des données de test
        print("📊 Insertion des données de test en cours...")
        success = db_manager.insert_sample_data()
        
        if success:
            # Vérification des statistiques
            stats = db_manager.get_database_stats()
            total_games = stats.get('total_games', 0)
            
            print(f"✅ Données insérées avec succès!")
            print(f"🎮 Total de jeux en base: {total_games}")
            print("🚀 Vous pouvez maintenant lancer le dashboard:")
            print("   py -m streamlit run src/dashboard/streamlit_dashboard.py")
        else:
            print("❌ Échec de l'insertion des données")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        logger.error(f"Erreur lors de l'insertion: {e}")
    
    finally:
        db_manager.close_connection()

if __name__ == "__main__":
    main()