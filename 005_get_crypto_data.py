"""005_get_crypto_data.py

Télécharge l’historique des prix (chandeliers) des 3 plus grosses cryptomonnaies
par capitalisation à partir d’un fichier snapshot JSON (le plus récent trouvé automatiquement),
et met à jour les fichiers Parquet existants (sans redondance) sous `crypto_data/pair_data/`.
Les paires sont exprimées en USDC.

Revision 4 – 2025-05-29
-----------------------
* Recherche automatique du fichier JSON le plus récent
* Vérifie l’existence des fichiers `.parquet` pour éviter les doublons
* Concatène les nouvelles données aux anciennes si besoin
* Ignore automatiquement les paires USDC invalides sur Binance
* Change le répertoire de sortie vers `crypto_data/pair_data/`

Usage
-----
```bash
python 005_get_crypto_data.py --interval 1h --years 5
```

Dépendances : Python ⩾ 3.8 + `pandas`, `python-dotenv`, `binance-connector`, `pyarrow`, `config.rest_client`
"""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
import time, argparse, pandas as pd, json, os
from dotenv import load_dotenv
from config import rest_client

load_dotenv()

DATA_DIR = Path("crypto_data/pair_data"); DATA_DIR.mkdir(parents=True, exist_ok=True)
MAX_LIMIT = 1000
MAX_SPAN_DAYS = 200

COLUMNS = [
    "open_time", "open", "high", "low", "close", "volume",
    "close_time", "quote_asset_volume", "nb_trades",
    "taker_buy_base", "taker_buy_quote", "ignore"
]

def iso_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1_000)

def fetch_interval(symbol: str, interval: str, start: datetime, end: datetime) -> list[pd.DataFrame]:
    spot = rest_client()
    frames = []
    cur = start
    while cur < end:
        try:
            kl = spot.klines(
                symbol, interval,
                startTime=iso_ms(cur),
                endTime=iso_ms(end),
                limit=MAX_LIMIT
            )
        except Exception as e:
            print(f"❌ Erreur sur {symbol} – {e}")
            return []
        if not kl:
            break
        df = (pd.DataFrame(kl, columns=COLUMNS)
                .astype({"open_time": "int64", "close_time": "int64",
                         **{c: "float64" for c in ["open", "high", "low", "close", "volume"]}}))
        frames.append(df)
        if len(kl) < MAX_LIMIT:
            break
        last_close_ms = int(df.iloc[-1]["close_time"])
        cur = datetime.fromtimestamp((last_close_ms + 1) / 1000, tz=timezone.utc)
        time.sleep(0.25)
    return frames

def find_latest_json_file(directory: Path) -> Path:
    files = list(directory.glob("*_top_crypto_history.json"))
    if not files:
        raise FileNotFoundError("Aucun fichier JSON trouvé dans le répertoire.")
    return max(files, key=os.path.getmtime)

def get_available_symbols(quote_asset="USDC") -> set[str]:
    spot = rest_client()
    info = spot.exchange_info()
    return {
        s["symbol"]
        for s in info["symbols"]
        if s["quoteAsset"] == quote_asset and s["status"] == "TRADING"
    }

def main(interval: str, years: int):
    json_file = find_latest_json_file(Path("crypto_data/market_data"))
    with open(json_file, 'r') as f:
        data = json.load(f)

    top_3 = sorted(data, key=lambda x: x['market_cap'], reverse=True)[:3]
    available_symbols = get_available_symbols()

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=years * 365)

    for coin in top_3:
        symbol = f"{coin['symbol'].upper()}USDC"
        if symbol not in available_symbols:
            print(f"⛔ {symbol} non disponible sur Binance – ignoré.")
            continue

        safe_symbol = symbol.lower()
        filename = f"{safe_symbol}_{interval}.parquet"
        target = DATA_DIR / filename

        print(f"\n📈 {symbol} ({interval}) – {start_date:%Y-%m-%d} → {end_date:%Y-%m-%d}")

        if target.exists():
            existing = pd.read_parquet(target)
            existing_latest = existing["open_time"].max()
            existing_latest_dt = datetime.fromtimestamp(existing_latest / 1000, tz=timezone.utc)
            print(f"  ➔ Mise à jour depuis {existing_latest_dt:%Y-%m-%d %H:%M}")
            start_fetch = existing_latest_dt + timedelta(milliseconds=1)
        else:
            existing = None
            start_fetch = start_date

        frames = []
        cur_blk = start_fetch
        while cur_blk < end_date:
            blk_end = min(cur_blk + timedelta(days=MAX_SPAN_DAYS), end_date)
            print(f"  ▸ Block {cur_blk:%Y-%m-%d} → {blk_end:%Y-%m-%d}")
            frames.extend(fetch_interval(symbol, interval, cur_blk, blk_end))
            cur_blk = blk_end
            time.sleep(0.35)

        if not frames:
            print(f"❌ Aucun kline récupéré pour {symbol}.")
            continue

        full = (pd.concat(frames, ignore_index=True)
                  .drop_duplicates("open_time")
                  .sort_values("open_time")
                  .reset_index(drop=True))

        full["open_dt"] = pd.to_datetime(full["open_time"], unit="ms", utc=True)
        full["close_dt"] = pd.to_datetime(full["close_time"], unit="ms", utc=True)

        if existing is not None:
            full = pd.concat([existing, full], ignore_index=True)
            full = (full.drop_duplicates("open_time")
                        .sort_values("open_time")
                        .reset_index(drop=True))

        full.to_parquet(target, index=False)
        print(f"✅ {len(full):,} lignes sauvegardées dans {target.name}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Télécharge l'historique des 3 plus grosses cryptos.")
    ap.add_argument("--interval", default="1h",
                    help="L'intervalle des chandeliers (ex: 1m, 15m, 1h, 1d)")
    ap.add_argument("--years", type=int, default=5,
                    help="Nombre d'années à récupérer")
    args = ap.parse_args()

    main(args.interval, args.years)

    # Exemple :
    # python 005_get_crypto_data.py --interval 1h --years 5