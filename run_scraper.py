#!/usr/bin/env python3
"""
Script de lancement principal du scraper.

Ce script lance le scraper Twitch avec la nouvelle architecture modulaire.

Auteurs: Hicham, Aya, Boubaker
Date: Juillet 2025
"""

import sys
import os
from pathlib import Path

# Ajout du répertoire racine au path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.scraper.twitch_scraper import main
    
    if __name__ == "__main__":
        print("🎮 === LANCEMENT DU SCRAPER TWITCH ===")
        print("👥 Créé par: Hicham, Aya, Boubaker")
        print("📅 Version: Juillet 2025")
        print("-" * 50)
        
        main()
        
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("💡 Vérifiez que toutes les dépendances sont installées:")
    print("   pip install -r requirements.txt")
    sys.exit(1)
except KeyboardInterrupt:
    print("\n⏹️ Scraping interrompu par l'utilisateur")
    sys.exit(0)
except Exception as e:
    print(f"❌ Erreur inattendue: {e}")
    sys.exit(1)
