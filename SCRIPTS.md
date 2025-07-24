# 📋 Scripts et Utilitaires

## 🎯 Scripts Principaux

### `app.py` - Dashboard Streamlit
**Application principale du projet**
- Interface web interactive avec Streamlit
- 6 pages d'analyse : Vue d'ensemble, Jeux, TwitchTracker, Événements, Streamers FR, Revenus
- Visualisations Plotly interactives
- Exports CSV/JSON intégrés
- Cache intelligent pour les performances

```bash
streamlit run app.py
```

### `main.py` - Interface CLI
**Point d'entrée en ligne de commande**
- Orchestration des différents scrapers
- Gestion des tâches automatisées
- Logging centralisé

```bash
python main.py --help
```

### `revenue_scraper.py` - Scraper de Revenus
**Estimation des revenus des streamers**
- Analyse des métriques TwitchTracker
- Calcul des abonnements estimés (Tier 1/2/3/Prime)
- Estimation donations et revenus publicitaires
- Sauvegarde MongoDB automatique

```bash
python revenue_scraper.py
```

### `auto_scraper.py` - Scraper Automatique
**Scraping automatisé multi-sources**
- Collecte données jeux Twitch
- Scraping événements gaming
- Streamers français
- Planification et monitoring

```bash
python auto_scraper.py
```

### `twitchtracker_enriched_scraper.py` - Enrichissement TwitchTracker
**Données TwitchTracker enrichies**
- Stats globales Twitch
- Jeux trending avec métriques avancées
- Top streamers mondiaux
- Données de croissance et part de marché

```bash
python twitchtracker_enriched_scraper.py
```

---

## 🏗️ Architecture des Sources

### `/src` - Code Source Principal
```
src/
├── application/           # Logique métier applicative
├── domain/               # Modèles et entités métier
├── infrastructure/       # Couche d'infrastructure
│   ├── scrapers/        # Modules de scraping spécialisés
│   └── database/        # Gestion MongoDB
├── presentation/         # Interface et vues
└── shared/              # Utilitaires partagés
```

### `/config` - Configuration
- Paramètres de connexion MongoDB
- Configuration des scrapers
- Variables d'environnement

### `/data` - Données Locales
- Fichiers temporaires
- Exports CSV/JSON
- Cache des données

### `/logs` - Logging
- Logs d'exécution des scrapers
- Erreurs et monitoring
- Fichiers de debug

### `/tests` - Tests
- Tests unitaires
- Tests d'intégration
- Mocks et fixtures

---

## 📊 Collections MongoDB

### `top_games` - Jeux Populaires
```json
{
  "game_name": "League of Legends",
  "viewers": 150000,
  "channels": 3000,
  "trend": "rising",
  "timestamp": "2025-07-24T12:00:00Z"
}
```

### `gaming_events` - Événements Gaming
```json
{
  "name": "LEC Summer Split 2025",
  "game": "League of Legends",
  "date": "2025-08-15",
  "prize_pool": "$200,000",
  "status": "Upcoming",
  "impact_score": 95
}
```

### `streamers_francais` - Streamers Français
```json
{
  "username": "Zerator",
  "followers": 1200000,
  "avg_viewers": 15000,
  "main_game": "World of Warcraft",
  "status": "online"
}
```

### `streamers_revenue` - Revenus Estimés
```json
{
  "username": "xQcOW",
  "monthly_total_estimate": 33894.19,
  "monthly_subs_revenue": 5195.0,
  "subs_breakdown": {
    "total_subs": 1926,
    "tier_1": 1637,
    "tier_2": 77,
    "tier_3": 19,
    "prime": 192
  }
}
```

### Collections TwitchTracker Enrichies
- `twitchtracker_global_stats` - Statistiques globales
- `twitchtracker_trending_games` - Jeux trending
- `twitchtracker_games_enriched` - Jeux avec métriques
- `twitchtracker_streamers_enriched` - Streamers mondiaux

---

## 🔧 Commandes Utiles

### Démarrage Rapide
```bash
# Démarrer MongoDB (si local)
brew services start mongodb-community

# Activer environnement virtuel
source .venv/bin/activate

# Lancer dashboard
streamlit run app.py

# Scraping complet
python auto_scraper.py && python revenue_scraper.py
```

### Maintenance
```bash
# Nettoyer les caches
rm -rf __pycache__ src/__pycache__

# Vérifier les dépendances
pip list --outdated

# Export des données
python -c "from pymongo import MongoClient; client = MongoClient(); db = client.twitch_trends; print('Collections:', db.list_collection_names())"
```

### Debug
```bash
# Vérifier connexion MongoDB
python -c "from pymongo import MongoClient; print('MongoDB:', MongoClient().admin.command('hello'))"

# Tester un scraper
python revenue_scraper.py --debug

# Logs en temps réel
tail -f logs/scraper.log
```

---

## 📈 Métriques de Performance

### Données Actuelles
- **15 streamers** avec revenus détaillés
- **100+ jeux** trackés
- **50+ événements** gaming
- **Update** toutes les 30 minutes

### Temps d'Exécution Moyens
- **auto_scraper.py** : ~2-3 minutes
- **revenue_scraper.py** : ~1-2 minutes  
- **twitchtracker_enriched_scraper.py** : ~3-5 minutes
- **Dashboard load** : ~2-3 secondes

---

## 🚨 Résolution de Problèmes

### Erreurs Communes

**MongoDB Connection Error**
```bash
# Vérifier que MongoDB est démarré
brew services list | grep mongodb
# ou
sudo systemctl status mongodb
```

**Module Not Found**
```bash
# Réinstaller les dépendances
pip install -r requirements.txt
```

**Streamlit Port Occupied**
```bash
# Utiliser un port différent
streamlit run app.py --server.port 8502
```

**UTF-8 Encoding Error (JSON Export)**
- Les corrections sont intégrées dans `app.py`
- Nettoyage automatique des caractères problématiques
- Fallback CSV en cas d'échec JSON

---

*Documentation mise à jour le 24 juillet 2025*
