"""Filtrado de péptidos según umbrales y criterios."""

from __future__ import annotations

import pandas as pd


def filter_peptides(
    df: pd.DataFrame,
    *,
    min_score: float | None = None,
) -> pd.DataFrame:
    """
    Filtra filas del DataFrame según criterios configurables.

    Parameters
    ----------
    df
        DataFrame con péptidos (posiblemente ya con columna ``score``).
    min_score
        Si se indica, solo se conservan filas con ``score >= min_score``.

    Returns
    -------
    pd.DataFrame
        Vista o copia filtrada.
    """
    if df.empty:
        return df.copy()

    mask = pd.Series(True, index=df.index)
    if min_score is not None and "score" in df.columns:
        mask &= df["score"] >= min_score

    return df.loc[mask].copy()
