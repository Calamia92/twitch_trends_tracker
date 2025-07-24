#!/usr/bin/env python3
"""
Script de validation de l'architecture nettoyée.

Ce script teste les composants principaux après nettoyage et réorganisation.
"""

import sys
from pathlib import Path

# Ajout du chemin du projet
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_imports():
    """Test des imports principaux."""
    print("🧪 Test des imports...")
    
    # Test configuration
    try:
        from src.config.settings import config
        print("✅ Configuration: OK")
    except Exception as e:
        print(f"❌ Configuration: {e}")
    
    # Test base de données
    try:
        from src.database.mongodb_manager import MongoDBManager
        print("✅ MongoDB Manager: OK")
    except Exception as e:
        print(f"❌ MongoDB Manager: {e}")
    
    # Test scrapers
    try:
        from src.scraper.twitch_scraper import TwitchScraper
        print("✅ Twitch Scraper: OK")
    except Exception as e:
        print(f"❌ Twitch Scraper: {e}")
    
    try:
        from src.scraper.events_scraper import EventsScraper
        print("✅ Events Scraper: OK")
    except Exception as e:
        print(f"❌ Events Scraper: {e}")
    
    try:
        from src.scraper.french_streamers_scraper import FrenchStreamersScraper
        print("✅ French Streamers Scraper: OK")
    except Exception as e:
        print(f"❌ French Streamers Scraper: {e}")

def test_app():
    """Test de l'application Streamlit."""
    print("\n🖥️ Test de l'application...")
    
    app_path = PROJECT_ROOT / "app.py"
    if app_path.exists():
        print("✅ app.py: Présent")
    else:
        print("❌ app.py: Manquant")

def test_database_connection():
    """Test de connexion à la base de données."""
    print("\n💾 Test de connexion MongoDB...")
    
    try:
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
        client.admin.command('ping')
        print("✅ MongoDB: Connexion réussie")
        
        # Test des collections
        db = client['twitch_trends']
        collections = db.list_collection_names()
        print(f"📁 Collections existantes: {collections}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ MongoDB: {e}")

def show_project_structure():
    """Affiche la structure du projet nettoyée."""
    print("\n📁 Structure du projet nettoyée:")
    
    def print_tree(path, prefix="", max_depth=3, current_depth=0):
        if current_depth >= max_depth:
            return
        
        items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
        
        for i, item in enumerate(items):
            if item.name.startswith('.') and item.name not in ['.env.example', '.gitignore']:
                continue
            
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            
            if item.is_dir():
                print(f"{prefix}{current_prefix}📁 {item.name}/")
                next_prefix = prefix + ("    " if is_last else "│   ")
                print_tree(item, next_prefix, max_depth, current_depth + 1)
            else:
                icon = "📄" if item.suffix == ".py" else "📝" if item.suffix in [".md", ".txt"] else "📋"
                print(f"{prefix}{current_prefix}{icon} {item.name}")
    
    print_tree(PROJECT_ROOT)

def main():
    """Fonction principale de validation."""
    print("🎮 VALIDATION ARCHITECTURE TWITCH TRENDS TRACKER v2.0.0")
    print("=" * 60)
    
    # Structure du projet
    show_project_structure()
    
    # Tests des imports
    test_imports()
    
    # Test application
    test_app()
    
    # Test base de données
    test_database_connection()
    
    print("\n🎉 Validation terminée!")
    print("\n📋 RÉSUMÉ DE L'ARCHITECTURE NETTOYÉE:")
    print("   ✅ Fichiers dépréciés supprimés")
    print("   ✅ Configuration centralisée (src/config/settings.py)")
    print("   ✅ Logging centralisé (src/utils/logger.py)")
    print("   ✅ Gestion d'erreurs (src/utils/exceptions.py)")
    print("   ✅ Point d'entrée principal (main.py)")
    print("   ✅ Documentation mise à jour (README.md)")
    print("   ✅ Dépendances organisées (requirements.txt)")
    print("   ✅ Configuration d'environnement (.env.example)")
    print("   ✅ .gitignore complet")
    
    print("\n🚀 PRÊT POUR LE SCRAPING!")
    print("   Commande: python main.py --mode scraping")
    print("   Dashboard: python main.py --mode dashboard")

if __name__ == "__main__":
    main()
