# 🎮 Twitch Trends Tracker v2.0.0

**Système de scraping multi-sources et dashboard interactif pour analyser les tendances gaming en temps réel**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-4.4+-green.svg)](https://mongodb.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)

---

## 🎯 Fonctionnalités

### 🔍 **Scraping Multi-Sources**
- **Jeux Twitch** : Top des jeux les plus streamés avec viewers en temps réel
- **Événements Gaming** : Tournois esports, compétitions et événements majeurs
- **Streamers Français** : Classement et statistiques des créateurs francophones

### 💾 **Gestion des Données**
- **MongoDB** : Stockage NoSQL optimisé avec indexation automatique
- **Validation** : Contrôle de qualité et nettoyage des données en temps réel
- **Export** : Formats CSV, JSON et rapports automatisés

### 📊 **Dashboard Interactif**
- **Interface Streamlit** : Dashboard responsive et moderne
- **Visualisations** : Graphiques interactifs Plotly avec drill-down
- **Temps Réel** : Actualisation automatique des données

---

## 🏗️ Architecture

```
twitch_trends_tracker/
├── 📁 src/                          # Code source principal
│   ├── 📁 config/                   # Configuration centralisée
│   │   ├── settings.py              # Paramètres application
│   │   └── config.py                # Configuration legacy
│   │
│   ├── 📁 scraper/                  # Modules de scraping
│   │   ├── twitch_scraper.py        # Scraper jeux Twitch
│   │   ├── events_scraper.py        # Scraper événements esports
│   │   └── french_streamers_scraper.py # Scraper streamers FR
│   │
│   ├── 📁 database/                 # Gestion base de données
│   │   └── mongodb_manager.py       # Interface MongoDB
│   │
│   ├── 📁 utils/                    # Utilitaires partagés
│   │   ├── logger.py                # Système de logging
│   │   ├── exceptions.py            # Gestion d'erreurs
│   │   ├── data_utils.py           # Utilitaires données
│   │   └── export_manager.py       # Gestionnaire exports
│   │
│   └── 📁 dashboard/                # Interface utilisateur
│       └── streamlit_dashboard.py  # Dashboard Streamlit
│
├── 📁 data/                         # Données et exports
├── 📁 logs/                         # Fichiers de logs
├── 📄 main.py                       # Point d'entrée principal
├── 📄 app.py                        # Application Streamlit
└── 📄 requirements.txt              # Dépendances Python
```

---

## ⚡ Installation Rapide

### 📋 **Prérequis**
- **Python 3.8+**
- **MongoDB 4.4+**
- **Git**

### 🔨 **Installation**

```bash
# 1. Cloner le repository
git clone <repository-url>
cd twitch-trends-tracker

# 2. Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\\Scripts\\activate  # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Démarrer MongoDB
brew services start mongodb-community  # macOS
# systemctl start mongod              # Linux

# 5. Test de l'installation
python main.py --config-check
```

---

## 🚀 Utilisation

### 🎛️ **Interface en Ligne de Commande**

```bash
# Mode complet : scraping puis dashboard
python main.py --mode all

# Scraping uniquement
python main.py --mode scraping

# Dashboard uniquement  
python main.py --mode dashboard

# Scrapers spécifiques
python main.py --scraper games events streamers

# Dashboard sur port personnalisé
python main.py --dashboard --port 8502

# Mode verbeux pour debugging
python main.py --mode all --verbose

# Vérification de configuration
python main.py --config-check

# Statut de l'application
python main.py --status
```

### 🚀 **Démarrage Rapide**

```bash
# Lancement complet (recommandé)
python main.py --mode all

# Accès au dashboard
# http://localhost:8501
```

---

## 📊 Sources de Données

### 🎮 **Jeux Twitch**
- **Source** : TwitchTracker.com
- **Données** : Nom du jeu, viewers actuels, chaînes actives, tendances
- **Format** : JSON structuré avec validation

### 🏆 **Événements Gaming**
- **Sources** : Liquipedia (CS:GO, LoL)
- **Données** : Nom, dates, prize pool, statut, jeu concerné
- **Format** : JSON avec métadonnées étendues

### 🇫🇷 **Streamers Français**
- **Source** : TwitchTracker Français
- **Données** : Pseudo, followers, viewers moyens, rang, tendance
- **Format** : JSON avec calculs de croissance

---

## 🔧 Configuration

### 🌐 **Variables d'Environnement (.env)**

```env
# Base de données
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=twitch_trends

# Scraping
SCRAPING_HEADLESS=true
SCRAPING_DELAY=1.0

# Dashboard
DASHBOARD_PORT=8501
DASHBOARD_CACHE_TTL=30
```

---

## 📈 Dashboard

### 🖥️ **Interface Principale**

Le dashboard Streamlit propose 4 vues principales :

- **📊 Vue d'Ensemble** : Métriques globales et tops
- **🎮 Section Jeux** : Analyse détaillée des jeux Twitch
- **🏆 Section Événements** : Suivi des compétitions esports
- **🇫🇷 Section Streamers** : Classement des créateurs français

### 📱 **Fonctionnalités**

- 🔍 Filtres dynamiques par période et popularité
- 📊 Graphiques interactifs avec Plotly
- 📥 Export CSV/JSON des données
- �� Actualisation temps réel avec cache
- 🎨 Interface responsive

---

## 🛠️ Développement

### 🏁 **Setup Développement**

```bash
# Installation en mode développement
pip install -e .

# Outils de développement
pip install black flake8 pytest mypy

# Tests
python -m pytest tests/ -v

# Formatage
black src/ tests/
```

### 🐛 **Debugging**

```bash
# Mode verbeux
python main.py --mode scraping --verbose

# Logs détaillés
tail -f logs/twitch_tracker.log

# Test MongoDB
python -c "from src.database.mongodb_manager import MongoDBManager; print('DB OK')"
```

---

## 🤝 Contribution

1. **Fork** le repository
2. **Créer** une branche feature
3. **Commiter** vos changements
4. **Pusher** et ouvrir une Pull Request

### 📋 **Guidelines**
- Suivre PEP 8 avec Black
- Ajouter des tests
- Documenter les nouvelles fonctions
- Messages de commit explicites

---

## 📞 Support

- **🐛 Issues** : GitHub Issues
- **📖 Documentation** : Wiki du projet
- **💬 Discussions** : GitHub Discussions

---

<div align="center">

**🎮 Twitch Trends Tracker v2.0.0**

*Architecture propre, code documenté, scraping multi-sources optimisé*

*Développé pour la communauté gaming française* ❤️

</div>
