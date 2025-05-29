"""003_top_stocks_marketcap.py

Ce script extrait les N plus grandes entreprises cotées en bourse en fonction de leur capitalisation boursière à l'aide de l'API Financial Modeling Prep. Les données sont sauvegardées dans un fichier JSON intitulé
`YYMMDD_top_stock_history.json` dans le dossier `stock_data/market_data/`.

Requiert : requests
"""

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import List, Dict

import requests
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# API Financial Modeling Prep (gratuite pour les endpoints de base)
API_KEY = os.getenv("FMP_API_KEY")  # Ajouter la clé dans le fichier .env ou via export
API_URL = "https://financialmodelingprep.com/api/v3/stock-screener"

# Dossier de sauvegarde
TARGET_DIR = Path("stock_data/market_data")
DEFAULT_TOP_N = 50


def _yymmdd(date: dt.date) -> str:
    return date.strftime("%y%m%d")


def fetch_market_caps(top_n: int) -> List[Dict]:
    if not API_KEY:
        raise RuntimeError("FMP_API_KEY non défini. Ajoutez-le dans le fichier .env ou via export.")

    params = {
        "limit": 1000,  # Charger un plus grand nombre d’actions pour un tri précis ensuite
        "exchange": "NASDAQ,NYSE",
        "apikey": API_KEY,
    }
    r = requests.get(API_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    ranked_data = sorted(
        [stock for stock in data if stock.get("marketCap")],
        key=lambda x: x["marketCap"],
        reverse=True
    )

    return [
        {
            "rank": idx + 1,
            "symbol": stock.get("symbol"),
            "name": stock.get("companyName"),
            "market_cap": stock.get("marketCap")
        }
        for idx, stock in enumerate(ranked_data[:top_n])
    ]


def build_snapshot(top_n: int) -> List[Dict]:
    return fetch_market_caps(top_n)


def save_snapshot(snapshot: List[Dict], date: dt.date, overwrite: bool) -> Path:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"{_yymmdd(date)}_top_stock_history.json"
    fpath = TARGET_DIR / fname

    if fpath.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {fpath}. Use --overwrite to replace.")

    with open(fpath, "w", encoding="utf-8") as fp:
        json.dump(snapshot, fp, indent=2)
    return fpath.resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Récupère les N plus grandes entreprises cotées par market cap via FMP API.")
    parser.add_argument("--top", type=int, default=DEFAULT_TOP_N, help="Nombre d'entreprises à extraire (default: 50)")
    parser.add_argument("--date", type=str, help="Date YYYY-MM-DD (défaut: aujourd’hui)")
    parser.add_argument("--overwrite", action="store_true", help="Remplacer si le fichier existe déjà")
    return parser.parse_args()


def main():
    args = parse_args()
    date = dt.date.fromisoformat(args.date) if args.date else dt.date.today()

    print(f"[INFO] Snapshot boursier pour {date.isoformat()} (top {args.top})")
    snapshot = build_snapshot(args.top)

    try:
        path = save_snapshot(snapshot, date, overwrite=args.overwrite)
    except FileExistsError as e:
        print(f"[ABORT] {e}")
        return

    print(f"[OK] Données sauvegardées dans : {path}")


if __name__ == "__main__":
    main()