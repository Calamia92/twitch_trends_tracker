# 🎮 Twitch Trends Tracker

Un projet complet pour **scraper les trend les plus streamés sur Twitch** via [twitchtracker.com](https://twitchtracker.com/games), stocker les données dans **MongoDB** et les visualiser dans un **dashboard interactif** via **Streamlit**.

---

## 📦 Fonctionnalités

- 🔍 **Scraping automatique** des trends les plus populaires sur Twitch
- 💾 **Stockage en temps réel** dans MongoDB (chaque item traité immédiatement)
- 📄 **Export automatique** vers CSV et JSON (conformité exigences)
- 🛠️ **Pipeline de traitement** avec transformation et nettoyage des données
- 🔧 **Gestion d'exceptions** complète pendant la navigation et collecte
- 📈 **Dashboard Streamlit** avec :
  - Filtres dynamiques (dates, viewers, jeu)
  - Graphiques interactifs (Altair)
  - Export CSV intégré
  - Visualisation de la part de marché Twitch
- 🤖 **Automatisation** avec scraping programmé
- 🏗️ **Architecture modulaire** : scraper et backend indépendants

---

## 🚀 Installation et configuration

### 1. Cloner le dépôt

```bash
git clone https://github.com/ton-pseudo/twitch-trends-tracker.git
cd twitch-trends-tracker
```

### 2. Configuration automatique (recommandé)

```bash
python setup.py
```

Ce script va automatiquement :
- ✅ Vérifier Python 3.8+
- 📦 Installer les dépendances
- 📝 Créer le fichier .env
- 🔧 Configurer ChromeDriver
- 🚀 Créer les scripts de lancement

### 3. Configuration manuelle (alternative)

```bash
# Installer les dépendances
pip install -r requirements.txt

# Créer le fichier de configuration
cp .env.example .env
# Puis éditer .env avec vos paramètres MongoDB
```

### 4. Configurer MongoDB

Éditez le fichier `.env` et remplacez :
```env
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
```

---

## 🎯 Utilisation

### Méthode recommandée (architecture modulaire)

```bash
# Lancer le scraper
python run_scraper.py

# Lancer le dashboard
python run_dashboard.py
```

### Méthode alternative (modules directs)

```bash
# Scraper modulaire
python -m src.scraper.twitch_scraper

# Dashboard modulaire  
streamlit run src/dashboard/streamlit_dashboard.py
```

### Autres fonctionnalités

```bash
# Automatisation (scraping continu)
python auto_scraper.py

# Dashboard simple alternatif
streamlit run app.py

# Démonstration du projet
python demo.py
```

---

## 📁 Structure du projet

```
├── 📁 src/                    # Code source principal (architecture modulaire)
│   ├── 📁 core/              # Composants centraux
│   ├── 📁 scraper/           # Module de scraping
│   │   └── twitch_scraper.py # 🕷️ Scraper principal refactorisé
│   ├── 📁 dashboard/         # Module dashboard
│   │   └── streamlit_dashboard.py # 📊 Dashboard interactif refactorisé
│   ├── 📁 database/          # Gestion base de données
│   │   └── mongodb_manager.py # 💾 Manager MongoDB avec gestion d'erreurs
│   └── 📁 utils/             # Utilitaires
│       ├── data_utils.py     # 🔧 Parsing et validation des données
│       └── export_manager.py # � Gestion exports CSV/JSON
├── 📁 config/                # Configuration centralisée
│   └── settings.py           # ⚙️ Configuration globale du projet
├── 📁 scripts/               # Scripts d'automatisation
├── 📁 data/                  # Données exportées (CSV/JSON)
├── 📁 docs/                  # Documentation
├── 📁 logs/                  # Fichiers de log
├── 📁 archive/               # Anciens fichiers (backup)
├── run_scraper.py            # 🚀 Script de lancement scraper (PRINCIPAL)
├── run_dashboard.py          # 🎮 Script de lancement dashboard (PRINCIPAL)
├── app.py                    # 📱 Dashboard alternatif (simple)
├── auto_scraper.py           # 🤖 Automatisation du scraping
├── setup.py                  # ⚙️ Script de configuration automatique
├── demo.py                   # 🎯 Script de démonstration
├── .env.example              # 📝 Modèle de configuration
├── .env                      # 🔐 Configuration (à créer)
├── requirements.txt          # 📦 Dépendances Python
└── README.md                 # 📖 Ce fichier
```

---

## ✅ Conformité avec les exigences du TP

### 📚 **Documentation**
- ✅ README.md complet avec description et instructions
- ✅ Liste des membres : **Hicham, Aya et Boubaker**
- ✅ Instructions d'exécution détaillées pour chaque composant

### 🔧 **Framework autorisé**
- ✅ **Selenium** (framework autorisé par le sujet)

### 📝 **Scraper conforme**
- ✅ **Source multiple** : TwitchTracker.com + possibilité d'extensions
- ✅ **Gestion d'exceptions** : TimeoutException, NoSuchElementException, erreurs réseau
- ✅ **Export CSV et JSON** : fichiers automatiquement générés à chaque scraping
- ✅ **Injection base de données** : MongoDB avec sauvegarde automatique
- ✅ **Pipeline de traitement** : fonctions dédiées pour transformation et nettoyage
- ✅ **Traitement temps réel** : chaque item immédiatement traité et sauvegardé

### 🏗️ **Architecture**
- ✅ **Architecture modulaire** : Code organisé en modules logiques dans `src/`
- ✅ **Séparation des responsabilités** : Scraping, database, dashboard, utils séparés
- ✅ **Configuration centralisée** : Toutes les configurations dans `config/settings.py`
- ✅ **Gestion d'erreurs robuste** : Logging et gestion d'exceptions complète
- ✅ **Scraper indépendant** : `src/scraper/twitch_scraper.py` exécutable séparément
- ✅ **Backend indépendant** : `src/dashboard/streamlit_dashboard.py` peut fonctionner sans le scraper
- ✅ **Données en base** : toutes les données injectées par le scraper
- ✅ **Exécution séparée** : composants peuvent être lancés indépendamment

---

## 🛠️ Technologies utilisées

* **Python 3.8+** - Langage principal
* **Selenium + ChromeDriver** - Web scraping avec gestion automatique
* **Streamlit** - Dashboard interactif et responsive
* **MongoDB + PyMongo** - Base de données NoSQL
* **Pandas** - Manipulation des données
* **Altair** - Visualisations interactives
* **Python-dotenv** - Gestion de la configuration
* **Schedule** - Automatisation des tâches
* **WebDriver-Manager** - Gestion automatique de ChromeDriver

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

