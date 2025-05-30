"""006_preview_crypto_data.py

Lance un dashboard Streamlit pour visualiser de façon interactive les données historiques
crypto ou actions extraites au format `.parquet`.
Les fichiers doivent être placés dans les dossiers suivants :
- `crypto_data/pair_data/` pour les cryptomonnaies (scripts 005)
- `stock_data/stocks_data/` pour les actions (script 007)

Revision 5 – 2025-05-29
-----------------------
* Sélection dynamique du fichier `.parquet`
* Filtrage par plage de dates (via calendrier)
* Affichage en chandeliers avec volume en barres colorées (up/down)
* Volume et prix affichés sur deux graphiques séparés
* Support des colonnes de dates nommées "Date" ou "open_dt"

Usage
-----
```bash
streamlit run 006_preview_crypto_data.py
```

Dépendances : Python ⩾ 3.8 + `streamlit`, `pandas`, `plotly`
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("🔍 Visualisation des données (.parquet)")

# Fusionner les fichiers provenant des deux répertoires
DATA_DIRS = [Path("crypto_data/pair_data"), Path("stock_data/stocks_data")]
files = []
for d in DATA_DIRS:
    if d.exists():
        files.extend(d.glob("*.parquet"))

files = sorted(files)

if not files:
    st.warning("Aucun fichier .parquet trouvé dans crypto_data/pair_data/ ou stock_data/stocks_data/")
    st.stop()

# --- Sélection du fichier ---
selected_file = st.selectbox("📁 Sélectionne un fichier", files)

# --- Chargement des données ---
df = pd.read_parquet(selected_file)

# Harmoniser les noms de colonnes possibles
if "Date" in df.columns:
    df["open_dt"] = pd.to_datetime(df["Date"])
elif "open_dt" in df.columns:
    df["open_dt"] = pd.to_datetime(df["open_dt"])
else:
    st.error("Le fichier sélectionné ne contient pas de colonne 'Date' ou 'open_dt'")
    st.stop()

min_date = df["open_dt"].min().date()
max_date = df["open_dt"].max().date()

# --- Sélection de la plage de temps ---
st.sidebar.markdown("### ⏱️ Plage de temps")
start_date = st.sidebar.date_input("Date début", min_value=min_date, max_value=max_date, value=min_date)
end_date   = st.sidebar.date_input("Date fin", min_value=min_date, max_value=max_date, value=max_date)

mask = (df["open_dt"].dt.date >= start_date) & (df["open_dt"].dt.date <= end_date)
filtered = df.loc[mask].copy()

if filtered.empty:
    st.warning("Aucune donnée disponible pour cette plage de dates.")
    st.stop()

# --- Préparation des données OHLC ---
df_ohlc = filtered.set_index("open_dt")

# Déterminer les colonnes de prix et de volume
open_col = "Open" if "Open" in df_ohlc.columns else "open"
high_col = "High" if "High" in df_ohlc.columns else "high"
low_col = "Low" if "Low" in df_ohlc.columns else "low"
close_col = "Close" if "Close" in df_ohlc.columns else "close"
vol_col = "Volume" if "Volume" in df_ohlc.columns else "volume"

# --- Graphique chandeliers ---
fig_price = go.Figure()
fig_price.add_trace(go.Candlestick(
    x=df_ohlc.index,
    open=df_ohlc[open_col],
    high=df_ohlc[high_col],
    low=df_ohlc[low_col],
    close=df_ohlc[close_col],
    name="Prix"
))
fig_price.update_layout(
    title=f"Prix – {selected_file.name}",
    xaxis_rangeslider_visible=False,
    yaxis_title="Prix"
)

# --- Graphique volume ---
colors = ["green" if c >= o else "red" for c, o in zip(df_ohlc[close_col], df_ohlc[open_col])]
fig_vol = go.Figure()
fig_vol.add_trace(go.Bar(
    x=df_ohlc.index,
    y=df_ohlc[vol_col],
    marker_color=colors,
    name="Volume"
))
fig_vol.update_layout(
    title=f"Volume – {selected_file.name}",
    yaxis_title="Volume"
)

st.plotly_chart(fig_price, use_container_width=True)