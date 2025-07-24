# Twitch Trends Tracker - Clean Architecture

## 🏗️ Architecture Overview

Cette application suit les principes de **Clean Architecture** pour maintenir une séparation claire des responsabilités et faciliter la maintenance et les tests.

```
src/
├── domain/              # 🏛️ Domain Layer (Business Logic)
│   ├── entities/        # Core business entities
│   ├── repositories/    # Repository interfaces  
│   └── services/        # Domain services
├── application/         # 🚀 Application Layer (Use Cases)
│   ├── services/        # Application services
│   └── usecases/        # Use case implementations
├── infrastructure/     # 🔧 Infrastructure Layer (External Concerns)
│   ├── database/        # Database implementations
│   ├── repositories/    # Repository implementations
│   └── scrapers/        # Web scraping implementations
├── presentation/       # 🎨 Presentation Layer (UI/CLI)
│   ├── cli/            # Command line interface
│   └── web/            # Web interface (Streamlit)
└── shared/             # 🔄 Shared utilities
```

## 🎯 Domain Layer

### Entities
- **Game**: Représente un jeu Twitch avec viewers, channels, métadonnées
- **Streamer**: Représente un streamer avec follower count, status live, etc.
- **Event**: Représente des événements significatifs (trending, spikes, etc.)
- **TrendingData**: Données agrégées de tendances sur une période

### Repository Interfaces
- **GameRepository**: Interface pour la persistance des jeux
- **StreamerRepository**: Interface pour la persistance des streamers  
- **EventRepository**: Interface pour la persistance des événements
- **TrendingRepository**: Interface pour la persistance des données de tendances

### Domain Services
- **GameService**: Logique métier pour les jeux (trending detection, recommendations)
- **StreamerService**: Logique métier pour les streamers (performance analysis)
- **TrendingService**: Logique métier pour l'analyse des tendances
- **EventService**: Logique métier pour la gestion des événements

## 🚀 Application Layer

### Use Cases
- **ScrapeGamesUseCase**: Orchestration du scraping des jeux
- **AnalyzeTrendsUseCase**: Analyse des tendances
- **GenerateReportUseCase**: Génération de rapports
- **MonitorEventsUseCase**: Surveillance en temps réel

### Application Services
- **ScrapingOrchestrator**: Coordination des différents scrapers
- **AnalyticsService**: Service d'analyse et de reporting
- **NotificationService**: Service de notifications

## 🔧 Infrastructure Layer

### Database
- **MongoDBManager**: Gestionnaire de connexion MongoDB
- **MongoGameRepository**: Implémentation MongoDB pour GameRepository
- **MongoStreamerRepository**: Implémentation MongoDB pour StreamerRepository

### Scrapers
- **TwitchScraper**: Scraper principal pour Twitch
- **TwitchTrackerEnricher**: Enrichissement via TwitchTracker.com
- **EventsScraper**: Scraper pour les événements
- **FrenchStreamersScraper**: Scraper spécialisé streamers français

## 🎨 Presentation Layer

### CLI
- **main.py**: Point d'entrée CLI principal
- **Commands**: Handlers pour les différentes commandes

### Web
- **streamlit_dashboard.py**: Dashboard web interactif
- **TwitchDashboard**: Classe principale du dashboard

## 📊 Shared Layer

### Utilities
- **Logger**: Système de logging centralisé
- **DataUtils**: Utilitaires de parsing et formatting
- **ExportManager**: Gestionnaire d'export (JSON, CSV, etc.)
- **Exceptions**: Exceptions métier personnalisées

## 🚀 Getting Started

### Installation
```bash
pip install -r requirements.txt
```

### Configuration
```bash
# Copier et adapter le fichier de configuration
cp config/settings.example.py config/settings.py
```

### Usage

#### CLI Clean Architecture
```bash
# Nouveau point d'entrée clean architecture
python cli.py scrape --source twitchtracker --type games
python cli.py analyze --top 10
python cli.py dashboard --port 8501
```

#### CLI Legacy (compatible)
```bash
# Ancien point d'entrée (toujours fonctionnel)
python main.py --mode scraping --scraper games
python main.py --dashboard
```

#### Dashboard Web
```bash
# Dashboard Streamlit
streamlit run app.py
```

## 🎯 Avantages de l'Architecture

### ✅ Séparation des responsabilités
- **Domain**: Logique métier pure, indépendante de la technologie
- **Application**: Orchestration des use cases
- **Infrastructure**: Détails techniques (DB, scraping, etc.)
- **Presentation**: Interface utilisateur

### ✅ Testabilité
- Tests unitaires faciles grâce aux interfaces
- Mocking simple des dépendances externes
- Tests d'intégration isolés

### ✅ Maintenabilité
- Code organisé en couches logiques
- Couplage faible entre les composants
- Évolutivité facilitée

### ✅ Flexibilité
- Changement de base de données sans impact métier
- Ajout de nouveaux scrapers simplifié
- Nouvelles interfaces utilisateur faciles

## 🔄 Migration du Code Legacy

Le code existant a été réorganisé selon les principes de clean architecture :

- **Scrapers** → `src/infrastructure/scrapers/`
- **Database** → `src/infrastructure/database/`
- **Utils** → `src/shared/`
- **Dashboard** → `src/presentation/web/`
- **Config** → `config/`

## 🧪 Tests

```bash
# Tests unitaires
python -m pytest tests/unit/

# Tests d'intégration
python -m pytest tests/integration/

# Tests complets
python -m pytest tests/
```

## 📈 Roadmap

- [ ] Implémentation complète des repositories MongoDB
- [ ] Création des use cases principaux
- [ ] Migration complète du CLI vers la clean architecture
- [ ] Tests unitaires et d'intégration
- [ ] Documentation API
- [ ] Performance monitoring
- [ ] Système de cache
- [ ] API REST

## 🤝 Contributing

1. Respecter les principes de clean architecture
2. Maintenir la séparation des couches
3. Ajouter des tests pour les nouvelles fonctionnalités
4. Documenter les changements

## 📝 License

MIT License - Voir LICENSE file pour plus de détails.
