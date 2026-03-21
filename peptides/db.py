"""Carga del dataset de péptidos versionado en el repositorio."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def default_peptide_table_path() -> Path:
    """Ruta a ``data/peptides.csv`` en la raíz del proyecto."""
    return Path(__file__).resolve().parent.parent / "data" / "peptides.csv"


def load_peptides(path: Path | str | None = None) -> pd.DataFrame:
    """
    Lee la tabla de péptidos y añade ``length`` (longitud de secuencia).

    Parameters
    ----------
    path
        CSV con columnas: ``id``, ``name``, ``sequence``, ``organism``, ``spectrum``, ``mic_ug_ml``.
        Por defecto, ``data/peptides.csv`` en la raíz del repo.
    """
    csv_path = Path(path) if path is not None else default_peptide_table_path()
    df = pd.read_csv(csv_path)
    df["length"] = df["sequence"].astype(str).str.len()
    return df
