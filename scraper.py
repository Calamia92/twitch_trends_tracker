import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

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
    options.add_argument("--headless=new")  # ou commente pour voir le navigateur
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(), options=options)
    print("[DEBUG] MONGO_URI:", MONGO_URI)

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

        games = []
        rows = driver.find_elements(By.CLASS_NAME, "ranked-item")
        for row in rows:
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

                games.append({
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

if __name__ == "__main__":
    data = scrape_top_games()
    if data:
        col.delete_many({})
        col.insert_many(data)
        print(f"[✅] {len(data)} jeux insérés dans MongoDB")
    else:
        print("[⚠️] Aucun jeu récupéré.")
