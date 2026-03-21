"""Filtrado de péptidos según umbrales y criterios."""

from __future__ import annotations

import pandas as pd


def filter_peptides(
    df: pd.DataFrame,
    *,
    sequence_contains: str | None = None,
    name_contains: str | None = None,
    organisms: list[str] | None = None,
    spectra: list[str] | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    max_mic_ug_ml: float | None = None,
    min_score: float | None = None,
) -> pd.DataFrame:
    """
    Filtra filas según criterios opcionales. Valores ``None`` o listas vacías no aplican ese criterio.
    """
    if df.empty:
        return df.copy()

    mask = pd.Series(True, index=df.index)

    if sequence_contains and sequence_contains.strip():
        q = sequence_contains.strip().upper()
        mask &= df["sequence"].astype(str).str.upper().str.contains(q, regex=False, na=False)

    if name_contains and name_contains.strip():
        q = name_contains.strip().lower()
        mask &= df["name"].astype(str).str.lower().str.contains(q, regex=False, na=False)

    if organisms is not None:
        mask &= df["organism"].isin(organisms)

    if spectra is not None:
        mask &= df["spectrum"].isin(spectra)

    if min_length is not None and "length" in df.columns:
        mask &= df["length"] >= min_length

    if max_length is not None and "length" in df.columns:
        mask &= df["length"] <= max_length

    if max_mic_ug_ml is not None and "mic_ug_ml" in df.columns:
        mask &= pd.to_numeric(df["mic_ug_ml"], errors="coerce") <= max_mic_ug_ml

    if min_score is not None and "score" in df.columns:
        mask &= pd.to_numeric(df["score"], errors="coerce") >= min_score

    return df.loc[mask].copy()
