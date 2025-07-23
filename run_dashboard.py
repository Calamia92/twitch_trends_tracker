#!/usr/bin/env python3
"""
Script de lancement principal du dashboard.

Ce script lance le dashboard Streamlit avec la nouvelle architecture modulaire.

Auteurs: Hicham, Aya, Boubaker
Date: Juillet 2025
"""

import sys
import os
import subprocess
from pathlib import Path

# Ajout du répertoire racine au path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Lance le dashboard Streamlit."""
    print("🎮 === LANCEMENT DU DASHBOARD TWITCH ===")
    print("👥 Créé par: Hicham, Aya, Boubaker")
    print("📅 Version: Juillet 2025")
    print("-" * 50)
    
    try:
        # Chemin vers le module dashboard
        dashboard_path = project_root / "src" / "dashboard" / "streamlit_dashboard.py"
        
        if not dashboard_path.exists():
            print(f"❌ Module dashboard introuvable: {dashboard_path}")
            sys.exit(1)
        
        # Commande Streamlit
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            str(dashboard_path),
            "--server.port", str(8501),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ]
        
        print("🚀 Lancement du serveur Streamlit...")
        print(f"🌐 URL: http://localhost:8501")
        print("⏹️ Appuyez sur Ctrl+C pour arrêter")
        print("-" * 50)
        
        # Exécution de Streamlit
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n⏹️ Dashboard arrêté par l'utilisateur")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lancement Streamlit: {e}")
        print("💡 Vérifiez que Streamlit est installé:")
        print("   pip install streamlit")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
