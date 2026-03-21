"""Cálculo de scores para péptidos."""

from __future__ import annotations

import pandas as pd


def score_peptides(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica reglas de scoring a cada fila (péptido).

    Parameters
    ----------
    df
        DataFrame con columnas de tus datos; debe incluir al menos las que uses en las reglas.

    Returns
    -------
    pd.DataFrame
        Copia del DataFrame con columna(s) de score añadidas (p. ej. ``score``).
    """
    out = df.copy()
    # TODO: implementar reglas de scoring reales
    if out.empty:
        out["score"] = pd.Series(dtype=float)
    else:
        out["score"] = 0.0
    return out
