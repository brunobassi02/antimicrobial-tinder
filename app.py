"""Aplicación web Streamlit — punto de entrada."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from peptides import filter_peptides, score_peptides

st.set_page_config(page_title="Antimicrobiano", layout="wide")

st.title("Antimicrobiano")
st.caption("Scoring y filtrado de péptidos (módulo `peptides`).")

with st.sidebar:
    st.header("Parámetros")
    min_score = st.number_input(
        "Score mínimo",
        value=0.0,
        step=0.1,
        help="Solo aplica si existe la columna `score` tras el scoring.",
    )

uploaded = st.file_uploader("CSV de péptidos", type=["csv"])

if uploaded is None:
    st.info("Sube un CSV para procesar, o integra aquí tu fuente de datos.")
    st.stop()

df = pd.read_csv(uploaded)
scored = score_peptides(df)
filtered = filter_peptides(scored, min_score=min_score)

st.subheader("Resultado")
col_a, col_b = st.columns(2)
with col_a:
    st.metric("Filas originales", len(df))
with col_b:
    st.metric("Filas tras filtro", len(filtered))

st.dataframe(filtered, use_container_width=True)
