#!/usr/bin/env python3
"""Generate *N* permutations of an OHLC parquet file, split into two complementary
segments inside the last ``LAST_N_BARS`` bars.

- **IN segment**  : first ``PERMUTE_RATIO`` of that window → written to
  ``IN_OUTPUT_DIR``
- **OUT segment** : remaining part of the window           → written to
  ``OUT_OUTPUT_DIR``

Each segment receives ``N_PERM`` independent permutations while bars outside the
window stay untouched.

Example
-------
python get_data/004_in_data_perm.py
"""
from __future__ import annotations

from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

# === CONFIGURATION =========================================================
INPUT_FILE      = "data/crypto_data/btcusdc_1d.parquet"  # Source parquet
IN_OUTPUT_DIR   = "data/in_data_perm/"                    # Folder for IN perms
OUT_OUTPUT_DIR  = "data/out_data_perm/"                  # Folder for OUT perms
N_PERM          = 50                                      # # permutations / segment
LAST_N_BARS     = 2000                                    # Window size (counting from end)
PERMUTE_RATIO   = 0.8                                     # 0 < ratio < 1 → share for IN
SEED            = 42                                      # None → fully random
# ===========================================================================

def _permute_segment(
    df: pd.DataFrame,
    seg_start: int,
    seg_end: int,
    *,
    n_perm: int,
    seed: int | None = None,
) -> List[pd.DataFrame]:
    """Return *n_perm* permutations of ``df`` restricted to ``[seg_start, seg_end]``.

    Bars outside this inclusive range remain identical to the original.  The
    permutation preserves the statistical structure of OHLC bars by
    shuffling (H/L/C) ranges together and (open–close) gaps independently, as
    proposed in López de Prado 2018, *Advances in Financial Machine Learning*.
    """

    assert 0 <= seg_start <= seg_end < len(df), "invalid segment boundaries"

    # ---- Pre‑compute log‑prices and relative moves in the segment ----------
    logp = np.log(df[["open", "high", "low", "close"]])
    gap_open  = (logp["open"]  - logp["close"].shift()).to_numpy()[seg_start : seg_end + 1]
    rel_high  = (logp["high"]  - logp["open"]).to_numpy()[seg_start : seg_end + 1]
    rel_low   = (logp["low"]   - logp["open"]).to_numpy()[seg_start : seg_end + 1]
    rel_close = (logp["close"] - logp["open"]).to_numpy()[seg_start : seg_end + 1]

    seg_len    = seg_end - seg_start + 1
    time_index = df.index

    def _one_perm(rng: np.random.Generator) -> pd.DataFrame:
        # --------------- Random ordering (independent gaps vs bodies) -------
        order_bar = rng.permutation(seg_len)  # high/low/close together
        order_gap = rng.permutation(seg_len)  # gaps independently

        _rel_high  = rel_high[order_bar]
        _rel_low   = rel_low[order_bar]
        _rel_close = rel_close[order_bar]
        _gap_open  = gap_open[order_gap]

        # --- Build output ---------------------------------------------------
        bars = logp.to_numpy().copy()

        # Anchor on bar just before the segment (or on itself if at pos 0)
        anchor_idx   = seg_start - 1 if seg_start > 0 else seg_start
        last_close   = bars[anchor_idx, 3]

        for k in range(seg_len):
            i_row = seg_start + k
            bars[i_row, 0] = last_close + _gap_open[k]    # open
            bars[i_row, 1] = bars[i_row, 0] + _rel_high[k]
            bars[i_row, 2] = bars[i_row, 0] + _rel_low[k]
            bars[i_row, 3] = bars[i_row, 0] + _rel_close[k]
            last_close     = bars[i_row, 3]

        return pd.DataFrame(
            np.exp(bars), index=time_index, columns=["open", "high", "low", "close"]
        )

    master = np.random.default_rng(seed)
    return [
        _one_perm(np.random.default_rng(master.integers(0, 2**32 - 1)))
        for _ in range(n_perm)
    ]


def _write_perms(
    perms: List[pd.DataFrame],
    out_dir: Path,
    base_name: str,
    *,
    original: pd.DataFrame | None = None,
) -> List[Path]:
    """Save permutations (and optionally the original) inside *out_dir*."""

    out_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []

    if original is not None:
        orig_path = out_dir / f"{base_name}_perm000.parquet"
        if not orig_path.exists():
            original.to_parquet(orig_path)
        written.append(orig_path)

    for i, p_df in enumerate(perms, start=1):
        p_path = out_dir / f"{base_name}_perm{i:03d}.parquet"
        p_df.to_parquet(p_path)
        written.append(p_path)
    return written


def main() -> None:
    # ----------------------- Load -----------------------------------------
    df = pd.read_parquet(Path(INPUT_FILE).expanduser())
    n_bars = len(df)

    # ----------------------- Window definition ----------------------------
    if not (0 < LAST_N_BARS <= n_bars):
        raise ValueError("LAST_N_BARS must be in (0, len(df)]")
    if not (0.0 < PERMUTE_RATIO < 1.0):
        raise ValueError("PERMUTE_RATIO must be strictly between 0 and 1")

    window_start = n_bars - LAST_N_BARS
    window_end   = n_bars - 1
    window_len   = LAST_N_BARS

    perm_len_in  = int(round(window_len * PERMUTE_RATIO))
    perm_len_out = window_len - perm_len_in

    # ----------------------- Segments -------------------------------------
    segA_start, segA_end = window_start, window_start + perm_len_in - 1
    segB_start, segB_end = segA_end + 1, window_end

    perms_in = _permute_segment(df, segA_start, segA_end, n_perm=N_PERM, seed=SEED)
    perms_out = _permute_segment(
        df, segB_start, segB_end, n_perm=N_PERM, seed=None if SEED is None else SEED + 1
    )

    # ----------------------- Write on disk --------------------------------
    base_name = Path(INPUT_FILE).stem
    in_paths = _write_perms(
        perms_in, Path(IN_OUTPUT_DIR).expanduser() / base_name, base_name, original=df
    )
    out_paths = _write_perms(
        perms_out, Path(OUT_OUTPUT_DIR).expanduser() / base_name, base_name, original=df
    )

    # ----------------------- Feedback -------------------------------------
    cwd = Path.cwd()
    for p in in_paths:
        try:
            print("IN  →", p.relative_to(cwd))
        except ValueError:
            print("IN  →", p)
    for p in out_paths:
        try:
            print("OUT →", p.relative_to(cwd))
        except ValueError:
            print("OUT →", p)


if __name__ == "__main__":
    main()