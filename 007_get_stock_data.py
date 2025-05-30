"""007_get_stock_data.py

Extrait les données historiques (1H et 1D) des 4 plus grandes capitalisations boursières
à partir du fichier JSON généré par le script 003_top_stocks_marketcap.py. Les fichiers sont sauvegardés au format `.parquet`
dans le dossier `stock_data/stocks_data/`.

Revision 3 – 2025-05-29
------------------------
* Ajout automatique des nouvelles données sans écrasement
* Nettoyage et uniformisation des colonnes avec les cryptos
* Création automatique du dossier `stock_data/stocks_data/`

Usage
-----
```bash
python 007_get_stock_data.py --interval 1h --years 5
```

Dépendances : Python ⩾ 3.8 + `yfinance`, `pandas`, `pyarrow`
"""

import argparse
from datetime import datetime, timedelta
import time
import pandas as pd
import yfinance as yf
from pathlib import Path
import json

DATA_DIR = Path("stock_data/stocks_data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_YEARS = 5
DEFAULT_INTERVAL = "1h"

# Formatage des noms de fichiers
def symbol_to_filename(symbol, interval):
    return f"{symbol.lower()}_{interval}.parquet"

# Téléchargement avec consolidation
def fetch_and_update(symbol, interval, years):
    filename = symbol_to_filename(symbol, interval)
    path = DATA_DIR / filename
    start = datetime.now() - timedelta(days=365 * years)
    end = datetime.now()

    print(f"📈 Téléchargement {symbol} ({interval}) de {start.date()} à {end.date()}…")
    ticker = yf.Ticker(symbol)
    df = ticker.history(interval=interval, start=start, end=end)

    if df.empty:
        print(f"❌ Aucune donnée pour {symbol}")
        return

    df = df.reset_index()
    df["open_dt"] = pd.to_datetime(df["Date"])
    df = df.rename(columns={
        "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"
    })
    df = df[["open_dt", "open", "high", "low", "close", "volume"]]

    if path.exists():
        df_old = pd.read_parquet(path)
        df = pd.concat([df_old, df], ignore_index=True).drop_duplicates("open_dt").sort_values("open_dt")

    df.to_parquet(path, index=False)
    print(f"✅ {symbol}: {len(df)} lignes sauvegardées → {path.name}")

# Lecture du fichier JSON + sélection top N
def get_top_symbols(json_file, n=4):
    with open(json_file) as f:
        data = json.load(f)
    data_sorted = sorted(data, key=lambda x: x["market_cap"], reverse=True)
    return [d["symbol"] for d in data_sorted[:n]]

def main(interval, years):
    # Trouver le JSON le plus récent
    json_files = sorted(Path("stock_data/market_data").glob("*_top_stock_history.json"), reverse=True)
    if not json_files:
        print("❌ Aucun fichier JSON trouvé dans stock_data/market_data")
        return

    latest = json_files[0]
    print(f"[INFO] Lecture depuis {latest.name}")

    symbols = get_top_symbols(latest, n=4)
    for symbol in symbols:
        fetch_and_update(symbol, interval, years)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extrait l'historique des 4 plus grosses capitalisations boursières.")
    parser.add_argument("--interval", default=DEFAULT_INTERVAL, help="Pas de temps : 1h, 1d, etc. [default: 1h]")
    parser.add_argument("--years", type=int, default=DEFAULT_YEARS, help="Nombre d'années à récupérer [default: 5]")
    args = parser.parse_args()
    main(args.interval, args.years)
