#! /usr/bin/env python3
"""001_top_crypto_snapshot.py

Generate a daily snapshot of the top-N cryptocurrencies by market cap and
save it in `data/market_analysis/YYMMDD_top_crypto_marketcap.json`.

Usage
-----
python 001_top_crypto_marketcap.py             # top-20 du jour
python 001_top_crypto_marketcap.py --top 50    # top-50
python 001_top_crypto_marketcap.py --overwrite
```
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Dict, List

import requests

# ────────────────────────────────────────────────────────────────────────────────
# .env loader --------------------------------------------------------------------
# ────────────────────────────────────────────────────────────────────────────────

def _load_dotenv(path: str = ".env") -> None:
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as fp:
        for line in fp:
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            k, v = line.rstrip().split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()
API_KEY = os.getenv("COINGECKO_API_KEY")

BASE = "https://pro-api.coingecko.com/api/v3" if API_KEY else "https://api.coingecko.com/api/v3"
HEADERS: Dict[str, str] = {"Accept": "application/json"}
if API_KEY:
    HEADERS["x-cg-pro-api-key"] = API_KEY
else:
    print("[INFO] COINGECKO_API_KEY absent – using public rate limits", file=sys.stderr)

MARKETS = f"{BASE}/coins/markets"

TARGET_DIR = Path("data/market_analysis")
DEFAULT_TOP_N = 20

# ────────────────────────────────────────────────────────────────────────────────
# Helpers ------------------------------------------------------------------------
# ────────────────────────────────────────────────────────────────────────────────

def _yymmdd(d: dt.date) -> str:
    return d.strftime("%y%m%d")


def _http_get(url: str, **kwargs):
    r = requests.get(url, headers=HEADERS, timeout=30, **kwargs)
    try:
        r.raise_for_status()
        return r
    except requests.HTTPError as exc:
        body = exc.response.text[:200]
        raise RuntimeError(f"HTTP {exc.response.status_code} – {body}") from None


def _fallback_to_public_api():
    global BASE, MARKETS
    print("[INFO] Falling back to public CoinGecko API (demo key detected)")
    BASE = "https://api.coingecko.com/api/v3"
    MARKETS = f"{BASE}/coins/markets"

# ────────────────────────────────────────────────────────────────────────────────
# Core logic ---------------------------------------------------------------------
# ────────────────────────────────────────────────────────────────────────────────

def fetch_market_data(n: int) -> List[Dict]:
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": n,
        "page": 1,
        "sparkline": "false",
    }
    try:
        return _http_get(MARKETS, params=params).json()
    except RuntimeError as err:
        if "10011" in str(err) or "Demo API key" in str(err):
            _fallback_to_public_api()
            return _http_get(MARKETS, params=params).json()
        raise


def build_snapshot(top_n: int) -> List[Dict]:
    market = fetch_market_data(top_n)
    return [
        {
            "rank": i + 1,
            "symbol": c["symbol"].upper(),
            "name": c["name"],
            "market_cap": c["market_cap"]
        }
        for i, c in enumerate(market)
    ]


def save_snapshot(data: List[Dict], date: dt.date, overwrite: bool) -> Path:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    path = TARGET_DIR / f"{_yymmdd(date)}_top_crypto_history.json"
    if path.exists() and not overwrite:
        raise FileExistsError(f"File {path} exists (use --overwrite)")
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2)
    return path

# ────────────────────────────────────────────────────────────────────────────────
# CLI ----------------------------------------------------------------------------
# ────────────────────────────────────────────────────────────────────────────────

def _cli(argv: List[str] | None = None):
    p = argparse.ArgumentParser(description="Save top-N crypto snapshot to dated JSON file.")
    p.add_argument("--top", type=int, default=DEFAULT_TOP_N, help="Number of coins (default 20)")
    p.add_argument("--date", type=str, help="Extraction date YYYY-MM-DD (default today)")
    p.add_argument("--overwrite", action="store_true", help="Replace file if it exists")
    return p.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    args = _cli(argv)
    date = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    print(f"[INFO] Building snapshot for {date} (top {args.top})…")

    snap = build_snapshot(args.top)
    try:
        path = save_snapshot(snap, date, overwrite=args.overwrite)
    except FileExistsError as exc:
        print(f"[ABORT] {exc}")
        return

    try:
        print(f"[OK] Snapshot → {path.relative_to(Path.cwd())}")
    except ValueError:
        print(f"[OK] Snapshot → {path}")


if __name__ == "__main__":
    main()
