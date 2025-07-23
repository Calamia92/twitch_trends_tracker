# 🎮 Twitch Trends Tracker

Un projet complet pour **scraper les trend les plus streamés sur Twitch** via [twitchtracker.com](https://twitchtracker.com/games), stocker les données dans **MongoDB** et les visualiser dans un **dashboard interactif** via **Streamlit**.

---

## 📦 Fonctionnalités

- 🔍 Scraping automatique des trend les plus populaires sur Twitch
- 💾 Stockage des données dans MongoDB
- 📈 Dashboard Streamlit avec :
  - Filtres dynamiques (dates, viewers, jeu)
  - Graphiques interactifs (Altair)
  - Export CSV
  - Visualisation de la part de marché Twitch

---

## 🚀 Lancer le projet

### 1. Cloner le dépôt

```bash
git clone https://github.com/ton-pseudo/twitch-trends-tracker.git
cd twitch-trends-tracker
````

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configuration

Créer un fichier `.env` à la racine du projet :

```env
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
```

> 💡 Tu peux aussi utiliser MongoDB localement : `mongodb://localhost:27017/`

---

### 4. Scraper les données

```bash
python scraper.py
```

Cela lance le navigateur en mode headless, récupère les données et les insère dans MongoDB.

---

### 5. Lancer le dashboard Streamlit

```bash
streamlit run dashboard.py
```

Ouvre automatiquement une page Web avec le tableau de bord interactif.

---

## 📁 Structure

```
├── scraper.py          # Scraping via Selenium
├── dashboard.py        # Interface Streamlit
├── .env                # Clé MongoDB (à créer)
├── requirements.txt    # Dépendances Python
├── README.md           # Ce fichier
```

---

## 🛠️ Dépendances

* Python 3.8+
* Selenium
* Streamlit
* Pandas
* Altair
* Python-dotenv
* PyMongo

---

## 📸 Aperçu

![dashboard](https://via.placeholder.com/800x400.png?text=Dashboard+Twitch+Trends)

---

## 👨‍💻 Auteurs

Made by **Hicham, Aya et Boubaker** 🔥

---

