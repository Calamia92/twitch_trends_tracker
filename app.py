import streamlit as st
from pymongo import MongoClient
import altair as alt
import pandas as pd
from dotenv import load_dotenv
import os

# Chargement des variables d'environnement
load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")

# Connexion MongoDB
client = MongoClient(MONGO_URI)
col = client["twitch_tracker"]["top_games"]

# Configuration page
st.set_page_config(page_title="🎮 Twitch Trends Dashboard", layout="wide")
st.title("🔥 Tableau de bord - Tendances Twitch")

# Chargement des données
docs = list(col.find())
if not docs:
    st.warning("Aucune donnée disponible.")
    st.stop()

# Transformation en DataFrame
df = pd.DataFrame(docs)

# Sécurité : renommage si 'title' est présent
if "title" in df.columns:
    df.rename(columns={"title": "name"}, inplace=True)

# Gestion de la date
df["date"] = pd.to_datetime(df["date"])
df["day"] = df["date"].dt.date

# Sidebar - Filtres
with st.sidebar:
    st.header("🎛️ Filtres")

    date_min = df["day"].min()
    date_max = df["day"].max()
    start_date, end_date = st.date_input(
        "📅 Plage de dates", [date_max, date_max],
        min_value=date_min, max_value=date_max
    )

    game_list = sorted(df["name"].unique())
    selected_game = st.selectbox("🎮 Rechercher un jeu", [""] + game_list)

    min_viewers = st.slider("👀 Viewers minimum", 0, int(df["viewers"].max()), 0)

# Application des filtres
filtered_df = df[(df["day"] >= start_date) & (df["day"] <= end_date)]
if selected_game:
    filtered_df = filtered_df[filtered_df["name"] == selected_game]
filtered_df = filtered_df[filtered_df["viewers"] >= min_viewers]

# Layout principal
col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("🏆 Classement du jour")
    latest_day = filtered_df["day"].max()
    top_df = filtered_df[filtered_df["day"] == latest_day]

    # Colonnes présentes uniquement
    display_columns = ["name", "viewers", "share"]
    top_df = top_df[[col for col in display_columns if col in top_df.columns]]
    top_df = top_df.sort_values(by="viewers", ascending=False)

    st.dataframe(top_df.reset_index(drop=True))

with col2:
    st.subheader("📈 Évolution des viewers")
    if not selected_game:
        top_games = (
            filtered_df.groupby("name")["viewers"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
            .index.tolist()
        )
        chart_df = filtered_df[filtered_df["name"].isin(top_games)]
    else:
        chart_df = filtered_df

    if not chart_df.empty:
        line_chart = alt.Chart(chart_df).mark_line(point=True).encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("viewers:Q", title="Viewers"),
            color="name:N",
            tooltip=["name", "date", "viewers"]
        ).properties(height=400)
        st.altair_chart(line_chart, use_container_width=True)
    else:
        st.info("Aucune donnée à afficher.")

# Pie chart
with st.expander("📊 Part de marché Twitch"):
    pie_df = top_df.copy()
    pie_df = pie_df.dropna(subset=["share"])
    pie_df["share"] = pie_df["share"].astype(float)

    if not pie_df.empty:
        pie_chart = alt.Chart(pie_df).mark_arc().encode(
            theta=alt.Theta(field="share", type="quantitative"),
            color=alt.Color(field="name", type="nominal"),
            tooltip=["name", "share"]
        ).properties(height=400)
        st.altair_chart(pie_chart, use_container_width=True)
    else:
        st.info("Pas de données valides.")

# Export CSV
with st.sidebar:
    if st.button("📤 Exporter les résultats"):
        st.download_button(
            "Télécharger CSV",
            data=filtered_df.to_csv(index=False),
            file_name="twitch_trends.csv"
        )

# Résumé
st.markdown("---")
st.caption(f"📦 {len(filtered_df)} lignes affichées entre le {start_date} et le {end_date}.")
