"""006_preview_crypto_data.py

Lance un dashboard Streamlit pour visualiser de façon interactive les données historiques
crypto extraites au format `.parquet` et stockées dans `crypto_data/pair_data/`.

Revision 3 – 2025-05-29
-----------------------
* Sélection dynamique du fichier `.parquet`
* Filtrage par plage de dates (via calendrier)
* Affichage en chandeliers avec volume en barres colorées (up/down)
* Volume et prix affichés sur deux graphiques superposés

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
st.title("🔍 Visualisation des données crypto (.parquet)")

DATA_DIR = Path("crypto_data/pair_data")
files = sorted(DATA_DIR.glob("*.parquet"))

if not files:
    st.warning("Aucun fichier .parquet trouvé dans crypto_data/pair_data/")
    st.stop()

# --- Sélection du fichier ---
selected_file = st.selectbox("📁 Sélectionne un fichier", files)

# --- Chargement des données ---
df = pd.read_parquet(selected_file)
df["open_dt"] = pd.to_datetime(df["open_dt"])

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

fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df_ohlc.index,
    open=df_ohlc["open"],
    high=df_ohlc["high"],
    low=df_ohlc["low"],
    close=df_ohlc["close"],
    name="Prix"
))

# Déterminer les couleurs des barres volume (vert = up, rouge = down)
colors = ["green" if c >= o else "red" for c, o in zip(df_ohlc["close"], df_ohlc["open"])]
fig.add_trace(go.Bar(
    x=df_ohlc.index,
    y=df_ohlc["volume"],
    name="Volume",
    marker_color=colors,
    yaxis="y2",
    opacity=0.4
))

# Configuration des axes
fig.update_layout(
    title=f"Graphique chandeliers & volumes – {selected_file.name}",
    xaxis_rangeslider_visible=False,
    yaxis=dict(title="Prix"),
    yaxis2=dict(
        title="Volume",
        overlaying="y",
        side="right",
        showgrid=False
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)