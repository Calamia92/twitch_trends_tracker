#!/usr/bin/env python3
"""
Script d'automatisation pour Twitch Trends Tracker
Lance le scraper à intervalles réguliers
"""

import time
import schedule
import subprocess
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SCRAPING_INTERVAL = int(os.getenv("SCRAPING_INTERVAL", 300))  # 5 minutes par défaut
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))

def run_scraper():
    """Exécute le scraper avec gestion des erreurs"""
    print(f"\n[🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Lancement du scraper...")
    
    for attempt in range(MAX_RETRIES):
        try:
            result = subprocess.run(
                [sys.executable, "scraper.py"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                print(f"[✅] Scraper terminé avec succès (tentative {attempt + 1})")
                print(result.stdout)
                return True
            else:
                print(f"[❌] Erreur scraper (tentative {attempt + 1}):")
                print(result.stderr)
                
        except subprocess.TimeoutExpired:
            print(f"[⏰] Timeout scraper (tentative {attempt + 1})")
        except Exception as e:
            print(f"[💥] Exception scraper (tentative {attempt + 1}): {e}")
        
        if attempt < MAX_RETRIES - 1:
            print(f"[🔄] Nouvelle tentative dans 30 secondes...")
            time.sleep(30)
    
    print(f"[💀] Échec du scraper après {MAX_RETRIES} tentatives")
    return False

def main():
    """Fonction principale d'automatisation"""
    print("🤖 Démarrage de l'automatisation Twitch Trends Tracker")
    print(f"📅 Intervalle de scraping: {SCRAPING_INTERVAL} secondes")
    print("📊 Appuyez sur Ctrl+C pour arrêter")
    
    # Premier scraping immédiat
    run_scraper()
    
    # Programmation des scrapes suivants
    schedule.every(SCRAPING_INTERVAL).seconds.do(run_scraper)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[👋] Arrêt de l'automatisation")
        return 0

if __name__ == "__main__":
    sys.exit(main())
