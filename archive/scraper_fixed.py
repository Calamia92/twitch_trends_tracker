import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import time
import json
import csv

load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGO_URI)
col = client["twitch_tracker"]["top_games"]

def parse_number(text):
    """Parse les nombres avec suffixes K/M en entiers"""
    text = text.replace(",", "").upper().strip()
    if text.endswith("K"):
        return int(float(text[:-1]) * 1000)
    elif text.endswith("M"):
        return int(float(text[:-1]) * 1000000)
    return int(text)

def process_game_item(row, collection):
    """Traite un item jeu et le sauvegarde immédiatement (exigence PDF)"""
    try:
        title = row.find_element(By.CLASS_NAME, "ri-name").text.strip()
        image_url = row.find_element(By.CLASS_NAME, "ri-image").find_element(By.TAG_NAME, "img").get_attribute("src")
        viewers = row.find_element(By.CLASS_NAME, "ri-value").text.strip()

        try:
            change_container = row.find_element(By.CLASS_NAME, "ri-change")
            change_elements = change_container.find_elements(By.CLASS_NAME, "to-number-lg")
            if change_elements:
                change = float(change_elements[0].text.strip())
            else:
                change = None
        except Exception as e:
            print(f"[⚠️] Change non trouvé pour {title} : {e}")
            change = None

        try:
            share = row.find_element(By.CLASS_NAME, "ri-share").get_attribute("textContent").strip()
        except:
            share = None

        # Construction de l'item
        game_item = {
            "title": title,
            "image": image_url,
            "viewers": parse_number(viewers),
            "change": change,
            "share": float(share.replace('%', '').strip()) if share else None,
            "date": datetime.utcnow().isoformat()
        }
        
        # Transformation et nettoyage des données (exigence PDF)
        if game_item["viewers"] < 0:
            game_item["viewers"] = 0
        
        if game_item["share"] and (game_item["share"] < 0 or game_item["share"] > 100):
            game_item["share"] = None
        
        # Sauvegarde immédiate en base (exigence PDF)
        try:
            collection.insert_one(game_item.copy())  # Copie pour éviter les modifications
            print(f"[💾] Sauvegardé: {title} ({game_item['viewers']:,} viewers)")
        except Exception as e:
            print(f"[❌] Erreur sauvegarde {title}: {e}")
        
        return game_item
        
    except Exception as e:
        print(f"[❌] Erreur traitement item : {e}")
        return None

def scrape_top_games():
    """Scrape les jeux les plus populaires sur Twitch avec traitement temps réel"""
    options = Options()
    options.add_argument("--headless=new")  
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    
    # Gestion automatique de ChromeDriver
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("[✅] ChromeDriver installé automatiquement")
    except Exception as e:
        print(f"[⚠️] Erreur avec webdriver-manager, utilisation du driver système: {e}")
        driver = webdriver.Chrome(service=Service(), options=options)
    
    print(f"[DEBUG] MONGO_URI: {MONGO_URI[:20]}..." if MONGO_URI else "[DEBUG] MONGO_URI: Non défini")

    try:
        print("[🌐] Accès à TwitchTracker...")
        driver.get("https://twitchtracker.com/games")

        # Gestion du popup cookies avec timeout plus court
        try:
            WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "fc-cta-consent"))
            ).click()
            print("[✅] Popup cookies fermé")
        except TimeoutException:
            print("[ℹ️] Aucun popup cookies détecté")

        # Attente de la liste de jeux avec timeout plus long
        print("[⏳] Chargement de la liste des jeux...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "ranked-item"))
        )

        # Nettoyage des données du jour pour éviter les doublons
        today = datetime.utcnow().date().isoformat()
        col.delete_many({"date": {"$regex": f"^{today}"}})
        print(f"[🧹] Données existantes du {today} supprimées")

        # Traitement item par item (exigence PDF)
        games = []
        rows = driver.find_elements(By.CLASS_NAME, "ranked-item")
        print(f"[📊] Traitement de {len(rows)} jeux...")
        
        for i, row in enumerate(rows, 1):
            game_item = process_game_item(row, col)
            if game_item:
                games.append(game_item)
            
            # Pause pour éviter la surcharge
            time.sleep(0.1)
            
            if i % 10 == 0:
                print(f"[📈] Progression: {i}/{len(rows)} jeux traités")

        print(f"[✅] Scraping terminé: {len(games)} jeux collectés")
        return games

    except Exception as e:
        print(f"[💥] Erreur durant le scraping: {e}")
        return []
    finally:
        driver.quit()
        print("[🔒] Navigateur fermé")

def export_to_files(data):
    """Export les données vers CSV et JSON (exigence PDF)"""
    if not data:
        print("[⚠️] Aucune donnée à exporter")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export CSV
    csv_filename = f"twitch_games_{timestamp}.csv"
    try:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for game in data:
                writer.writerow(game)
        print(f"[📄] Export CSV: {csv_filename}")
    except Exception as e:
        print(f"[❌] Erreur export CSV: {e}")
    
    # Export JSON
    json_filename = f"twitch_games_{timestamp}.json"
    try:
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False, default=str)
        print(f"[📄] Export JSON: {json_filename}")
    except Exception as e:
        print(f"[❌] Erreur export JSON: {e}")

def run_scraper():
    """Lance le scraper et sauvegarde les données (Pipeline complet)"""
    print("=" * 60)
    print("🎮 TWITCH TRENDS TRACKER - SCRAPER")
    print("=" * 60)
    print("[🚀] Démarrage du pipeline de scraping...")
    
    start_time = datetime.now()
    
    try:
        # 1. Scraping avec traitement temps réel
        data = scrape_top_games()
        
        if data:
            # 2. Export vers fichiers (exigence PDF)
            export_to_files(data)
            
            # 3. Statistiques finales
            total_viewers = sum(game["viewers"] for game in data)
            top_game = max(data, key=lambda x: x["viewers"])
            
            print("\n" + "=" * 60)
            print("📊 STATISTIQUES DE SCRAPING")
            print("=" * 60)
            print(f"✅ Jeux collectés: {len(data)}")
            print(f"👀 Total viewers: {total_viewers:,}")
            print(f"📈 Moyenne viewers: {total_viewers//len(data):,}")
            print(f"🏆 Jeu #1: {top_game['title']} ({top_game['viewers']:,} viewers)")
            
            # 4. Durée d'exécution
            duration = datetime.now() - start_time
            print(f"⏱️ Durée: {duration.total_seconds():.1f} secondes")
            print("=" * 60)
            
        else:
            print("[⚠️] Aucun jeu récupéré.")
            
    except Exception as e:
        print(f"[❌] Erreur lors du scraping: {e}")
        raise

if __name__ == "__main__":
    run_scraper()
