#!/usr/bin/env python3
"""
Script de configuration et d'installation pour Twitch Trends Tracker
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Vérifie que Python 3.8+ est installé"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ requis. Version actuelle:", sys.version)
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} détecté")
    return True

def install_dependencies():
    """Installe les dépendances Python"""
    print("\n📦 Installation des dépendances...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dépendances installées avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation: {e}")
        return False

def check_chrome_driver():
    """Vérifie si ChromeDriver est disponible"""
    print("\n🔍 Vérification de ChromeDriver...")
    
    # Vérifier si chromedriver est dans le PATH
    if shutil.which("chromedriver"):
        print("✅ ChromeDriver trouvé dans le PATH")
        return True
    
    print("⚠️ ChromeDriver non trouvé")
    print("💡 Solutions:")
    print("   1. Installer ChromeDriver manuellement: https://chromedriver.chromium.org/")
    print("   2. Ou installer via Homebrew: brew install chromedriver")
    print("   3. Ou utiliser webdriver-manager (ajouté aux requirements)")
    
    return False

def create_env_file():
    """Crée un fichier .env d'exemple"""
    env_path = Path(".env")
    
    if env_path.exists():
        print("✅ Fichier .env déjà existant")
        return True
    
    print("\n📝 Création du fichier .env...")
    env_content = """# Configuration MongoDB
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority

# Exemple pour une instance locale MongoDB
# MONGODB_URI=mongodb://localhost:27017/

# Configuration optionnelle
SCRAPING_INTERVAL=300  # Intervalle en secondes entre les scrapes
MAX_RETRIES=3          # Nombre de tentatives en cas d'échec
"""
    
    try:
        with open(env_path, "w") as f:
            f.write(env_content)
        print("✅ Fichier .env créé")
        print("⚠️ N'oubliez pas de configurer votre MONGODB_URI dans le fichier .env")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la création du .env: {e}")
        return False

def test_mongodb_connection():
    """Teste la connexion MongoDB"""
    print("\n🔗 Test de connexion MongoDB...")
    
    try:
        from dotenv import load_dotenv
        from pymongo import MongoClient
        
        load_dotenv()
        mongo_uri = os.getenv("MONGODB_URI")
        
        if not mongo_uri or "<username>" in mongo_uri:
            print("⚠️ MONGODB_URI non configuré dans .env")
            return False
        
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.server_info()  # Test de connexion
        
        print("✅ Connexion MongoDB réussie")
        return True
        
    except ImportError:
        print("⚠️ Dépendances non installées, connexion non testée")
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion MongoDB: {e}")
        return False

def create_launch_scripts():
    """Crée des scripts de lancement"""
    print("\n📜 Création des scripts de lancement...")
    
    # Script pour le scraper
    scraper_script = """#!/bin/bash
echo "🚀 Lancement du scraper Twitch..."
python scraper.py
"""
    
    # Script pour le dashboard
    dashboard_script = """#!/bin/bash
echo "🎮 Lancement du dashboard Twitch..."
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0
"""
    
    try:
        with open("run_scraper.sh", "w") as f:
            f.write(scraper_script)
        os.chmod("run_scraper.sh", 0o755)
        
        with open("run_dashboard.sh", "w") as f:
            f.write(dashboard_script)
        os.chmod("run_dashboard.sh", 0o755)
        
        print("✅ Scripts de lancement créés:")
        print("   - run_scraper.sh")
        print("   - run_dashboard.sh")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des scripts: {e}")
        return False

def main():
    """Fonction principale de configuration"""
    print("🎮 Configuration de Twitch Trends Tracker")
    print("=" * 50)
    
    # Vérifications
    checks = [
        check_python_version(),
        install_dependencies(),
        create_env_file(),
        check_chrome_driver(),
        create_launch_scripts(),
        test_mongodb_connection()
    ]
    
    print("\n" + "=" * 50)
    print("📋 Résumé de la configuration:")
    
    if all(checks[:5]):  # Tous sauf MongoDB (optionnel pour le setup)
        print("✅ Configuration terminée avec succès!")
        print("\n🚀 Prochaines étapes:")
        print("1. Configurez votre MONGODB_URI dans le fichier .env")
        print("2. Lancez le scraper: python scraper.py")
        print("3. Lancez le dashboard: streamlit run dashboard.py")
        print("\n💡 Ou utilisez les scripts:")
        print("   ./run_scraper.sh")
        print("   ./run_dashboard.sh")
    else:
        print("⚠️ Configuration incomplète. Veuillez résoudre les erreurs ci-dessus.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
