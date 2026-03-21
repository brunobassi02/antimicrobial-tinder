"""Cálculo de scores para péptidos."""

from __future__ import annotations

import pandas as pd


def score_peptides(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade ``score`` en [0, 100]: menor MIC (µg/mL) implica mayor score.

    Requiere la columna ``mic_ug_ml``. Si falta, ``score`` queda en 0.
    """
    out = df.copy()
    if out.empty or "mic_ug_ml" not in out.columns:
        out["score"] = 0.0 if not out.empty else pd.Series(dtype=float)
        return out

    mic = pd.to_numeric(out["mic_ug_ml"], errors="coerce")
    valid = mic.notna()
    out["score"] = 0.0
    if valid.any():
        lo, hi = float(mic[valid].min()), float(mic[valid].max())
        if hi > lo:
            out.loc[valid, "score"] = 100.0 * (hi - mic[valid]) / (hi - lo)
        else:
            out.loc[valid, "score"] = 50.0
    return out
