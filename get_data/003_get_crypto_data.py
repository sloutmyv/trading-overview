"""003_get_crypto_data.py

Télécharge l’historique de prix (chandeliers) pour **une seule paire Binance** (ex. : BTCUSDC)
et enregistre toutes les colonnes de l’endpoint `/klines` (12 valeurs)
au format Parquet dans `data/crypto_data/`.

python 003_get_crypto_data.py --pair BTCUSDC --interval 1h --years 5
python 003_get_crypto_data.py --pair BTCUSDC --interval 1h --years 5 --overwrite

"""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
import time, argparse, os
import pandas as pd
from dotenv import load_dotenv
from config import rest_client

load_dotenv()

# --- Configuration ---------------------------------------------------------
DATA_DIR = Path("data/crypto_data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

MAX_LIMIT = 1000          # limite de l’API Binance par appel
MAX_SPAN_DAYS = 200       # taille max d’un bloc de récupération

# Colonnes renvoyées par l’endpoint /klines de Binance (12 valeurs)
COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume",
    "close_time", "quote_asset_volume", "nb_trades",
    "taker_buy_base", "taker_buy_quote", "ignore",
]

# --- Fonctions utilitaires --------------------------------------------------

def iso_ms(dt: datetime) -> int:
    """Convertit un datetime UTC en millisecondes POSIX."""
    return int(dt.timestamp() * 1_000)


def fetch_interval(symbol: str, interval: str, start: datetime, end: datetime) -> list[pd.DataFrame]:
    """Récupère les chandeliers entre *start* et *end* par blocs."""
    spot = rest_client()
    frames: list[pd.DataFrame] = []
    cur = start
    while cur < end:
        try:
            kl = spot.klines(
                symbol, interval,
                startTime=iso_ms(cur),
                endTime=iso_ms(end),
                limit=MAX_LIMIT,
            )
        except Exception as e:
            print(f"❌ Erreur sur {symbol} – {e}")
            return []

        if not kl:  # plus de données dispo
            break

        # Conversion en DataFrame complet (12 colonnes)
        df = pd.DataFrame(kl, columns=COLUMNS)
        df = df.astype({
            "open_time": "int64", "close_time": "int64", "nb_trades": "int64",
            **{c: "float64" for c in [
                "open", "high", "low", "close", "volume",
                "quote_asset_volume", "taker_buy_base", "taker_buy_quote", "ignore",
            ]},
        })
        frames.append(df)

        # si moins que MAX_LIMIT, nous avons atteint la fin
        if len(kl) < MAX_LIMIT:
            break

        # sinon, avance d’une milliseconde après la dernière bougie
        last_close_ms = int(df.iloc[-1]["close_time"])
        cur = datetime.fromtimestamp((last_close_ms + 1) / 1000, tz=timezone.utc)
        time.sleep(0.25)  # respect API

    return frames


def get_available_symbols(quote_asset: str = "USDC") -> set[str]:
    """Renvoie l’ensemble des symboles TRADING avec l’asset coté donné."""
    spot = rest_client()
    info = spot.exchange_info()
    return {
        s["symbol"]
        for s in info["symbols"]
        if s["quoteAsset"] == quote_asset and s["status"] == "TRADING"
    }

# --- Routine principale -----------------------------------------------------

def main(pair: str, interval: str, years: int, overwrite: bool):
    pair = pair.upper()
    available_symbols = get_available_symbols()

    if pair not in available_symbols:
        raise ValueError(f"⛔ La paire {pair} n’est pas disponible (ou pas en TRADING) sur Binance.")

    # Calcul de la période de récupération
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=years * 365)

    target = DATA_DIR / f"{pair.lower()}_{interval}.parquet"

    if overwrite and target.exists():
        target.unlink()  # on repart de zéro

    if target.exists():
        existing = pd.read_parquet(target)
        last_open_ms = existing["open_time"].max()
        start_fetch = datetime.fromtimestamp((last_open_ms + 1) / 1000, tz=timezone.utc)
        print(f"📄 Mise à jour de {target.name} – nouvelles données depuis {start_fetch:%Y-%m-%d %H:%M}")
    else:
        existing = None
        start_fetch = start_date
        print(f"📄 Création de {target.name} – données depuis {start_date:%Y-%m-%d}")

    if start_fetch >= end_date:
        print("✅ Aucune nouvelle donnée à récupérer.")
        return

    # Récupération par blocs de MAX_SPAN_DAYS
    frames: list[pd.DataFrame] = []
    cur_blk = start_fetch
    while cur_blk < end_date:
        blk_end = min(cur_blk + timedelta(days=MAX_SPAN_DAYS), end_date)
        print(f"  ▸ Bloc {cur_blk:%Y-%m-%d} → {blk_end:%Y-%m-%d}")
        frames.extend(fetch_interval(pair, interval, cur_blk, blk_end))
        cur_blk = blk_end
        time.sleep(0.35)

    if not frames:
        print("❌ Aucun kline récupéré.")
        return

    new_data = (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates("open_time")
        .sort_values("open_time")
        .reset_index(drop=True)
    )

    # Fusion avec l’existant si besoin
    if existing is not None:
        full = pd.concat([existing, new_data], ignore_index=True)
        full = (
            full.drop_duplicates("open_time")
            .sort_values("open_time")
            .reset_index(drop=True)
        )
    else:
        full = new_data

    # Sauvegarde complète (12 colonnes)
    full.to_parquet(target, index=False)

    print(f"✅ {len(new_data):,} nouvelles lignes – total {len(full):,} lignes sauvegardées dans {target}")

# --- Script -----------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Télécharge les chandeliers d’une paire Binance en Parquet.")
    parser.add_argument("--pair", required=True, help="Symbole complet Binance (ex. BTCUSDC)")
    parser.add_argument("--interval", default="1h", help="Intervalle des chandeliers : 1m, 15m, 1h, 1d…")
    parser.add_argument("--years", type=int, default=5, help="Nombre d’années à récupérer")
    parser.add_argument("--overwrite", action="store_true", help="Réécrit complètement le fichier Parquet s’il existe")
    args = parser.parse_args()

    main(pair=args.pair, interval=args.interval, years=args.years, overwrite=args.overwrite)
