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
    text = text.replace(",", "").upper().strip()
    if text.endswith("K"):
        return int(float(text[:-1]) * 1000)
    elif text.endswith("M"):
        return int(float(text[:-1]) * 1000000)
    return int(text)

def scrape_top_games():
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
        driver.get("https://twitchtracker.com/games")

        # Supprimer le popup cookie s’il existe
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "fc-cta-consent"))
            ).click()
        except Exception:
            print("[⚠️] Aucun popup cookies trouvé ou ignoré.")

        # Attente de la liste de jeux
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "ranked-item"))
        )

def process_game_item(row, col):
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
        
        # Sauvegarde immédiate en base (exigence PDF)
        try:
            col.insert_one(game_item)
            print(f"[💾] Sauvegardé: {title} ({game_item['viewers']:,} viewers)")
        except Exception as e:
            print(f"[❌] Erreur sauvegarde {title}: {e}")
        
        return game_item
        
    except Exception as e:
        print(f"[❌] Erreur traitement item : {e}")
        return None
                    "title": title,
                    "image": image_url,
                    "viewers": parse_number(viewers),
                    "change": change,
                    "share": float(share.replace('%', '').strip()) if share else None
                })
            except Exception as e:
                print("[❌] Erreur sur un jeu :", e)

        # Ajoute la date de scraping (au format UTC ISO 8601)
        now = datetime.utcnow().isoformat()
        for game in games:
            game["date"] = now

        return games

    finally:
        driver.quit()

def export_to_files(data):
    """Export les données vers CSV et JSON (conformité PDF)"""
    if not data:
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export CSV
    csv_filename = f"twitch_games_{timestamp}.csv"
    try:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            if data:
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
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
        print(f"[📄] Export JSON: {json_filename}")
    except Exception as e:
        print(f"[❌] Erreur export JSON: {e}")

def run_scraper():
    """Lance le scraper et sauvegarde les données"""
    print("[🚀] Démarrage du scraper Twitch...")
    
    try:
        data = scrape_top_games()
        if data:
            # Export vers fichiers (exigence PDF)
            export_to_files(data)
            
            # Injection en base de données (exigence PDF)
            # Option 2: Historiser les données (recommandé)
            # Supprimer seulement les données du jour actuel
            today = datetime.utcnow().date().isoformat()
            col.delete_many({"date": {"$regex": f"^{today}"}})
            col.insert_many(data)
            
            print(f"[✅] {len(data)} jeux insérés dans MongoDB")
            print(f"[📊] Données mises à jour pour le {today}")
            
            # Affichage des stats
            total_viewers = sum(game["viewers"] for game in data)
            top_game = max(data, key=lambda x: x["viewers"])
            print(f"[📈] Total viewers: {total_viewers:,}")
            print(f"[🏆] Jeu #1: {top_game['title']} ({top_game['viewers']:,} viewers)")
            
        else:
            print("[⚠️] Aucun jeu récupéré.")
            
    except Exception as e:
        print(f"[❌] Erreur lors du scraping: {e}")
        raise

if __name__ == "__main__":
    run_scraper()
