#!/usr/bin/env python3
"""
Scraper pour calculer les revenus des streamers basé sur leurs abonnements
VERSION CORRIGÉE - Estimation basée sur les métriques disponibles
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import random
from datetime import datetime, timedelta
from pymongo import MongoClient
import pandas as pd
import re

class TwitchRevenueCalculator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Connexion MongoDB
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['twitch_trends']
        
        # Prix par tier d'abonnement (estimation moyenne après commission Twitch)
        self.sub_prices = {
            'tier_1': 2.50,  # ~$4.99 -> $2.50 pour le streamer
            'tier_2': 5.00,  # ~$9.99 -> $5.00 pour le streamer  
            'tier_3': 12.50, # ~$24.99 -> $12.50 pour le streamer
            'prime': 2.50    # Equivalent tier 1
        }
    
    def estimate_subs_from_metrics(self, username):
        """
        Estimer les abonnements basé sur les métriques disponibles
        (TwitchTracker ne publie pas les données d'abonnements publiquement)
        """
        try:
            print(f"🔍 Estimation subs pour {username} basé sur métriques...")
            
            # Récupérer les données du streamer depuis notre DB
            streamer_data = self.db.twitchtracker_streamers_enriched.find_one(
                {'username': username}
            )
            
            if not streamer_data:
                print(f"❌ Pas de données streamers pour {username}")
                return None
            
            avg_viewers = streamer_data.get('avg_viewers', 0)
            followers = streamer_data.get('followers', 0)
            
            # Estimation des abonnements basée sur l'industrie
            # Règle empirique: ~2-5% des viewers moyens sont abonnés
            # Plus le streamer est populaire, plus le taux de conversion est élevé
            
            if avg_viewers > 50000:
                sub_rate = 0.05  # 5% pour les très gros streamers
            elif avg_viewers > 20000:
                sub_rate = 0.04  # 4% pour les gros streamers
            elif avg_viewers > 5000:
                sub_rate = 0.03  # 3% pour les streamers moyens
            elif avg_viewers > 1000:
                sub_rate = 0.025 # 2.5% pour les petits streamers
            else:
                sub_rate = 0.02  # 2% pour les très petits streamers
            
            estimated_total_subs = int(avg_viewers * sub_rate)
            
            # Répartition estimée des tiers (basée sur statistiques Twitch)
            subs_data = {
                'username': username,
                'total_subs': estimated_total_subs,
                'tier_1_subs': int(estimated_total_subs * 0.85),  # 85% Tier 1
                'tier_2_subs': int(estimated_total_subs * 0.04),  # 4% Tier 2
                'tier_3_subs': int(estimated_total_subs * 0.01),  # 1% Tier 3
                'prime_subs': int(estimated_total_subs * 0.10),   # 10% Prime
                'monthly_revenue_estimate': 0,
                'yearly_revenue_estimate': 0,
                'timestamp': datetime.now(),
                'estimation_method': 'avg_viewers_based'
            }
            
            # Calculer les revenus estimés
            monthly_revenue = (
                subs_data['tier_1_subs'] * self.sub_prices['tier_1'] +
                subs_data['tier_2_subs'] * self.sub_prices['tier_2'] +
                subs_data['tier_3_subs'] * self.sub_prices['tier_3'] +
                subs_data['prime_subs'] * self.sub_prices['prime']
            )
            
            subs_data['monthly_revenue_estimate'] = round(monthly_revenue, 2)
            subs_data['yearly_revenue_estimate'] = round(monthly_revenue * 12, 2)
            
            print(f"✅ {username}: {estimated_total_subs} subs estimés (${monthly_revenue:.2f}/mois)")
            
            return subs_data
            
        except Exception as e:
            print(f"❌ Erreur lors de l'estimation de {username}: {str(e)}")
            return None
    
    def get_streamlabs_donation_estimate(self, username):
        """
        Estimer les donations moyennes (approximation)
        """
        try:
            # Les donations sont difficiles à scraper directement
            # On peut estimer basé sur la popularité du streamer
            
            # Récupérer les données du streamer depuis notre DB
            streamer_data = self.db.twitchtracker_streamers_enriched.find_one(
                {'username': username}
            )
            
            if not streamer_data:
                return 0
            
            avg_viewers = streamer_data.get('avg_viewers', 0)
            
            # Estimation: ~1-3% des viewers donnent en moyenne $3-10/mois
            donation_rate = 0.02  # 2% des viewers
            avg_donation = 5.0    # $5 moyenne par donateur
            
            monthly_donations = avg_viewers * donation_rate * avg_donation
            
            return round(monthly_donations, 2)
            
        except Exception as e:
            print(f"❌ Erreur estimation donations {username}: {str(e)}")
            return 0
    
    def calculate_total_revenue(self, username):
        """
        Calculer le revenu total estimé d'un streamer
        """
        # Données d'abonnements estimées
        subs_data = self.estimate_subs_from_metrics(username)
        if not subs_data:
            return None
        
        # Estimation des donations
        monthly_donations = self.get_streamlabs_donation_estimate(username)
        
        # Revenu total = Subs + Donations + (Estimation Ad Revenue)
        monthly_subs = subs_data['monthly_revenue_estimate']
        
        # Ad revenue estimation: ~$1-3 per 1000 vues
        streamer_data = self.db.twitchtracker_streamers_enriched.find_one(
            {'username': username}
        )
        
        monthly_ads = 0
        if streamer_data:
            avg_viewers = streamer_data.get('avg_viewers', 0)
            stream_hours = streamer_data.get('stream_hours_week', 20)
            # Estimation: avg_viewers * heures/semaine * 4 semaines * $2 CPM
            monthly_ads = avg_viewers * stream_hours * 4 * 0.002
        
        total_revenue = {
            'username': username,
            'monthly_subs_revenue': monthly_subs,
            'monthly_donations_estimate': monthly_donations,
            'monthly_ads_estimate': round(monthly_ads, 2),
            'monthly_total_estimate': round(monthly_subs + monthly_donations + monthly_ads, 2),
            'yearly_total_estimate': round((monthly_subs + monthly_donations + monthly_ads) * 12, 2),
            'subs_breakdown': {
                'total_subs': subs_data['total_subs'],
                'tier_1': subs_data['tier_1_subs'],
                'tier_2': subs_data['tier_2_subs'],
                'tier_3': subs_data['tier_3_subs'],
                'prime': subs_data['prime_subs']
            },
            'timestamp': datetime.now(),
            'calculation_date': datetime.now().strftime('%Y-%m-%d'),
            'estimation_note': 'Estimation basée sur avg_viewers (TwitchTracker ne publie pas les données d\'abonnements)'
        }
        
        return total_revenue
    
    def scrape_streamers_revenue(self, limit=20):
        """
        Scraper les revenus des top streamers
        """
        print("🚀 Démarrage du scraping des revenus streamers...")
        print("💡 Utilisation d'estimations basées sur métriques (subs non publics sur TwitchTracker)")
        
        # Récupérer les top streamers depuis notre DB
        top_streamers = list(self.db.twitchtracker_streamers_enriched.find(
            {},
            {'username': 1, 'avg_viewers': 1, 'followers': 1}
        ).sort('avg_viewers', -1).limit(limit))
        
        if not top_streamers:
            print("❌ Aucun streamer enrichi trouvé. Lancez d'abord le scraper TwitchTracker.")
            return []
        
        revenue_data = []
        
        for i, streamer in enumerate(top_streamers, 1):
            username = streamer['username']
            print(f"📊 [{i}/{len(top_streamers)}] Traitement de {username}...")
            
            revenue = self.calculate_total_revenue(username)
            if revenue:
                revenue_data.append(revenue)
                
                # Sauvegarder dans MongoDB
                self.db.streamers_revenue.update_one(
                    {'username': username},
                    {'$set': revenue},
                    upsert=True
                )
                
                subs_count = revenue['subs_breakdown']['total_subs']
                subs_revenue = revenue['monthly_subs_revenue']
                total_revenue = revenue['monthly_total_estimate']
                
                print(f"✅ {username}: {subs_count} subs → ${subs_revenue:.2f} subs + ${total_revenue-subs_revenue:.2f} autres = ${total_revenue:.2f}/mois")
            
            # Pause pour éviter le rate limiting
            time.sleep(random.uniform(1, 2))
        
        print(f"🎉 Scraping terminé! {len(revenue_data)} streamers traités.")
        return revenue_data

def main():
    calculator = TwitchRevenueCalculator()
    
    # Scraper les revenus des top 15 streamers
    revenue_data = calculator.scrape_streamers_revenue(limit=15)
    
    # Afficher un résumé
    if revenue_data:
        print("\n📈 RÉSUMÉ DES REVENUS ESTIMÉS:")
        print("-" * 60)
        print(f"{'Streamer':<20} {'Subs':<8} {'Subs Rev':<10} {'Total Rev':<12}")
        print("-" * 60)
        
        sorted_streamers = sorted(revenue_data, key=lambda x: x['monthly_total_estimate'], reverse=True)
        
        for streamer in sorted_streamers[:10]:
            subs = streamer['subs_breakdown']['total_subs']
            subs_rev = streamer['monthly_subs_revenue']
            total_rev = streamer['monthly_total_estimate']
            print(f"{streamer['username']:<20} {subs:<8,} ${subs_rev:<9,.2f} ${total_rev:<11,.2f}")
    
    print("\n✅ Données sauvegardées dans MongoDB: collection 'streamers_revenue'")
    print("💡 Note: Les données d'abonnements sont des estimations basées sur avg_viewers")

if __name__ == "__main__":
    main()
