# 📚 Documentation Twitch Trends Tracker

## 🏗️ Architecture

### Core Documentation
- **[Clean Architecture](./architecture/CLEAN_ARCHITECTURE.md)** - Guide complet de l'architecture clean implementée
- **[Implementation Summary](./architecture/IMPLEMENTATION_SUMMARY.md)** - Résumé de l'implémentation et des composants

## 📊 Reports & Analysis

### Project Reports
- **[TwitchTracker Enrichment Report](./reports/TWITCHTRACKER_ENRICHMENT_REPORT.md)** - Rapport d'intégration TwitchTracker

## 🛠️ Maintenance

### Cleanup & Organization
- **[Clean Architecture Cleanup](./maintenance/CLEAN_ARCHITECTURE_CLEANUP.md)** - Rapport de nettoyage et organisation
- **[Final Cleanup Report](./maintenance/FINAL_CLEANUP_REPORT.md)** - Rapport final de nettoyage et optimisation
- **[Documentation Organization](./maintenance/DOCUMENTATION_ORGANIZATION_REPORT.md)** - Réorganisation de la documentation

## 🚀 Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Usage
```bash
# CLI principal (Clean Architecture)
python main_clean.py --help

# CLI legacy (compatible)
python cli.py --help

# Dashboard web
streamlit run app.py
```

### Validation
```bash
# Valider l'architecture
python validate_clean_architecture.py
```

## 📁 Project Structure

```
docs/
├── architecture/          # Documentation architecture
│   ├── CLEAN_ARCHITECTURE.md
│   └── IMPLEMENTATION_SUMMARY.md
├── reports/              # Rapports de projet
│   └── TWITCHTRACKER_ENRICHMENT_REPORT.md
└── maintenance/          # Documentation maintenance
    └── CLEAN_ARCHITECTURE_CLEANUP.md
```

## 🔗 Links Utiles

- [README Principal](../README.md) - Guide utilisateur principal
- [Configuration](../config/) - Fichiers de configuration
- [Tests](../tests/) - Suite de tests

---
*Documentation générée automatiquement - Dernière mise à jour: 24 juillet 2025*
