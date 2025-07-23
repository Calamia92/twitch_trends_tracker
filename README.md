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
## 🚀 Perspectives

Voici quelques pistes d’amélioration pour enrichir ce projet :

- 🧠 Génération automatique de résumé des tendances : un algorithme pourrait détecter les hausses/déclins les plus marquants et générer un court texte d’analyse.
- 📈 Visualisation comparative multi-jeux : permettre la sélection de plusieurs jeux pour comparer leurs évolutions sur plusieurs jours.
- 📊 Clustering comportemental : regrouper automatiquement les jeux ayant des dynamiques similaires (hausse lente, viralité soudaine...).
- 🤖 Recommandation de jeux à streamer : proposer des jeux avec un bon ratio viewers/streamers pour aider à identifier des opportunités.
- 🗃️ Archivage quotidien : historiser les scrapes au lieu d’écraser les données, pour suivre l’évolution réelle dans le temps.

Ces ajouts donneraient une dimension analytique et prédictive au dashboard, en exploitant pleinement les données collectées.

---


## 📸 Aperçu

<img width="2501" height="1252" alt="image" src="https://github.com/user-attachments/assets/f3be3098-8e78-4a0f-971e-2f9f88b357df" />

---

## 👨‍💻 Auteurs

Made by **Hicham, Aya et Boubaker** 

---

