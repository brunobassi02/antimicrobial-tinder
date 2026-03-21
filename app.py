"""Aplicación web Streamlit — punto de entrada."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from peptides import filter_peptides, load_peptides, score_peptides

st.set_page_config(page_title="Antimicrobiano", layout="wide")


@st.cache_data
def _dataset() -> pd.DataFrame:
    raw = load_peptides()
    return score_peptides(raw)


st.title("Antimicrobiano")
st.caption("Base de péptidos del repositorio: filtrá para encontrar candidatos.")

df = _dataset()

with st.sidebar:
    st.header("Filtros")
    seq_q = st.text_input("Secuencia contiene", placeholder="ej. WK, GIG…")
    name_q = st.text_input("Nombre contiene", placeholder="ej. Magainin")

    org_opts = sorted(df["organism"].dropna().unique().tolist())
    org_sel = st.multiselect("Organismo", org_opts, default=org_opts)

    spec_opts = sorted(df["spectrum"].dropna().unique().tolist())
    spec_sel = st.multiselect("Espectro", spec_opts, default=spec_opts)

    lo = int(df["length"].min()) if len(df) else 0
    hi = int(df["length"].max()) if len(df) else 100
    len_range = st.slider("Longitud (residuos)", min_value=lo, max_value=max(hi, lo), value=(lo, hi))

    mic_max = float(df["mic_ug_ml"].max()) if len(df) else 100.0
    max_mic = st.slider("MIC máximo (µg/mL)", min_value=0.0, max_value=max(mic_max, 1.0), value=mic_max, step=0.5)

    min_score = st.slider("Score mínimo", min_value=0.0, max_value=100.0, value=0.0, step=1.0)

filtered = filter_peptides(
    df,
    sequence_contains=seq_q or None,
    name_contains=name_q or None,
    organisms=None if len(org_sel) == len(org_opts) else org_sel,
    spectra=None if len(spec_sel) == len(spec_opts) else spec_sel,
    min_length=len_range[0],
    max_length=len_range[1],
    max_mic_ug_ml=max_mic,
    min_score=min_score,
)

st.subheader("Resultados")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Péptidos en base", len(df))
with c2:
    st.metric("Tras filtros", len(filtered))
with c3:
    st.metric("Score (0–100)", "↑ mejor actividad (MIC más bajo)")

show = filtered[
    [
        "id",
        "name",
        "sequence",
        "length",
        "organism",
        "spectrum",
        "mic_ug_ml",
        "score",
    ]
]
st.dataframe(show, use_container_width=True, hide_index=True)
