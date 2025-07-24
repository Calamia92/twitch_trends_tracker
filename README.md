# 🎮 Twitch Trends Tracker

**Dashboard avancé d'analyse des tendances gaming avec scraping multi-sources et données en temps réel**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-4.4+-green.svg)](https://mongodb.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## � Description

**Twitch Trends Tracker** est un système complet d'analyse des tendances gaming qui combine scraping automatisé, stockage NoSQL et visualisation interactive. Le projet offre une vue d'ensemble en temps réel de l'écosystème Twitch français et international.

### 🎯 Objectifs
- **Analyser** les tendances gaming sur Twitch en temps réel
- **Suivre** les performances des streamers français
- **Monitorer** les événements esports et gaming
- **Estimer** les revenus des créateurs de contenu

---

## ✨ Fonctionnalités

### � **Scraping Multi-Sources**
- **🎮 Jeux Twitch** : Top des jeux avec viewers, channels et tendances
- **🏆 Événements Gaming** : Tournois esports, prize pools et calendrier
- **🇫🇷 Streamers Français** : Classement, métriques et analyse de performance
- **💰 Revenus Streamers** : Estimations basées sur abonnements, donations et publicités

### 📊 **Dashboard Interactif**
- **Interface Streamlit** moderne et responsive
- **Graphiques Plotly** interactifs avec drill-down
- **Exports** CSV/JSON des données analysées
- **Filtres** avancés par pays, catégorie, période

### 💾 **Gestion des Données**
- **MongoDB** avec indexation optimisée
- **Validation** automatique et nettoyage des données
- **Cache** intelligent pour les performances
- **Logs** détaillés pour le monitoring

---

## 🏗️ Architecture

```
twitch_trends_tracker/
├── � app.py                        # Application Streamlit principale
├── 📄 main.py                       # Point d'entrée CLI
├── � requirements.txt              # Dépendances Python
├── 📄 .env.example                  # Template configuration
│
├── 📁 src/                          # Code source principal
│   ├── 📁 application/              # Logique applicative
│   ├── 📁 domain/                   # Modèles métier
│   ├── 📁 infrastructure/           # Couche infrastructure
│   │   ├── 📁 scrapers/            # Modules de scraping
│   │   │   ├── twitch_scraper.py   # Scraper jeux Twitch
│   │   │   ├── events_scraper.py   # Scraper événements
│   │   │   └── french_streamers_scraper.py # Streamers FR
│   │   └── 📁 database/            # Gestion BDD
│   ├── 📁 presentation/            # Interface utilisateur
│   └── 📁 shared/                  # Utilitaires partagés
│
├── 📁 config/                       # Configuration
├── 📁 data/                         # Données locales
├── 📁 docs/                         # Documentation
├── 📁 logs/                         # Fichiers de logs
└── 📁 tests/                        # Tests unitaires
```

---

## 🚀 Installation

### Prérequis
- **Python 3.8+**
- **MongoDB 4.4+**
- **Git**

### 1. Cloner le projet
```bash
git clone https://github.com/votre-username/twitch_trends_tracker.git
cd twitch_trends_tracker
```

### 2. Environnement virtuel
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configuration
```bash
cp .env.example .env
# Éditer .env avec vos paramètres MongoDB
```

### 5. Lancement
```bash
# Dashboard Streamlit
streamlit run app.py

# Ou scraping via CLI
python main.py --help
```

---

## � Utilisation

### Dashboard Web
1. **Lancer l'application** : `streamlit run app.py`
2. **Accéder** à `http://localhost:8501`
3. **Explorer** les différentes pages :
   - 📊 **Vue d'ensemble** : Métriques globales
   - 🎮 **Jeux Twitch** : Analyse des jeux populaires
   - 📈 **TwitchTracker Live** : Données enrichies temps réel
   - 🎯 **Événements Gaming** : Calendrier esports
   - 🇫🇷 **Streamers Français** : Classement national
   - 💰 **Revenus Streamers** : Estimations financières

### Scraping Automatisé
```bash
# Scraper tous les modules
python main.py --all

# Scraper spécifique
python revenue_scraper.py
python auto_scraper.py
python twitchtracker_enriched_scraper.py
```

---

## 📊 Données Collectées

### Jeux Twitch
- Nombre de viewers actuels
- Nombre de chaînes actives
- Tendances de croissance
- Métadonnées des jeux

### Streamers
- Nombre de followers
- Viewers moyens
- Heures de stream par semaine
- Jeu principal
- Estimations de revenus

### Événements
- Calendrier des tournois
- Prize pools
- Statut (Live, À venir, Terminé)
- Impact score

---

## 🛠️ Technologies

- **Backend** : Python 3.8+, MongoDB
- **Frontend** : Streamlit, Plotly
- **Scraping** : Selenium, BeautifulSoup, Requests
- **Data** : Pandas, NumPy
- **Deployment** : Docker (à venir)

---

## 📈 Métriques

- **15+ streamers** avec données de revenus détaillées
- **100+ jeux** trackés en temps réel
- **50+ événements** gaming suivis
- **Mise à jour** toutes les 30 minutes

---

## 🤝 Contribution

1. **Fork** le projet
2. **Créer** une branche feature (`git checkout -b feature/amazing-feature`)
3. **Commit** vos changements (`git commit -m 'Add amazing feature'`)
4. **Push** sur la branche (`git push origin feature/amazing-feature`)
5. **Ouvrir** une Pull Request

---

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 👥 Équipe

- **Hicham** - Lead Developer & Architecture
- **Aya** - Data Analysis & Scraping
- **Boubaker** - Frontend & Visualization

---

## 📞 Contact

- 📧 Email : votre.email@example.com
- 🐙 GitHub : [twitch_trends_tracker](https://github.com/votre-username/twitch_trends_tracker)
- 📊 Dashboard Live : [Demo](http://votre-demo-url.com)

---

*Développé avec ❤️ pour la communauté gaming française*
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

## � Documentation

### 📖 **Documentation Complète**
- **[Documentation Index](./docs/README.md)** - Index complet de la documentation
- **[Clean Architecture](./docs/architecture/CLEAN_ARCHITECTURE.md)** - Guide d'architecture
- **[Implementation Summary](./docs/architecture/IMPLEMENTATION_SUMMARY.md)** - Résumé technique

### 📊 **Rapports & Analyses**
- **[TwitchTracker Report](./docs/reports/TWITCHTRACKER_ENRICHMENT_REPORT.md)** - Rapport d'intégration
- **[Cleanup Report](./docs/maintenance/CLEAN_ARCHITECTURE_CLEANUP.md)** - Rapport de nettoyage

---

## �🛠️ Développement

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
