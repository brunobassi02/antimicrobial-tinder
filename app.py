import os
import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from dotenv import load_dotenv
import warnings

# 0. Limpieza de advertencias
warnings.filterwarnings("ignore", category=FutureWarning)

# 1. Configuración de página
st.set_page_config(page_title="Antimicrobial Tinder", layout="wide", page_icon="🧪")

# 2. 🎨 CSS DEFINITIVO (PARA ARREGLAR LOS COLORES DE LA CAPTURA)
st.markdown("""
<style>
    /* ========================================================= */
    /* 🎨 DISEÑO ARMONIZADO: ALTO CONTRASTO Y LEGIBILIDAD */
    /* ========================================================= */
    
    .stApp { background-color: #f8fafc; color: #0f172a; } /* Fondo global claro */

    /* 1. Arreglo de Métricas (Tarjetas Profesionales) */
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    /* Ajustes específicos de color dentro de stMetric */
    [data-testid="stMetricLabel"] > div {
        color: #64748b !important; /* Gris Slate (Etiqueta) */
    }
    [data-testid="stMetricValue"] > div {
        color: #4f46e5 !important; /* Indigo (El valor resalta) */
    }

    /* 2. Arreglo de Tabla y DataFrame */
    div[data-testid="stDataFrame"] > div {
        border-radius: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        overflow: hidden;
    }

    /* 3. Sidebar (Panel de Control) */
    .css-1d391kg { background-color: #ffffff; border-right: 1px solid #e2e8f0; }

    /* ========================================================= */
    /* 🛠️ ARREGLOS DE LEGIBILIDAD CRÍTICOS (NEGRO SOBRE NEGRO) 🛠️ */
    /* ========================================================= */

    /* 4. La Caja de Secuencia Normalized (st.code()) */
    /* Fix: Gris oscuro sobre caja gris oscuro */
    [data-testid="stCodeBlock"] {
        background-color: #f1f5f9 !important; /* Forzar fondo gris muy claro */
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
    [data-testid="stCodeBlock"] pre {
        color: #0f172a !important; /* Forzar texto oscuro para legibilidad */
        padding: 10px;
    }

    /* 5. La Caja de Justificación Científica (st.info() / st.alert()) */
    /* Fix: Texto oscuro sobre fondo oscuro en "Justificación de Categoría" */
    /* Hacemos que la justificación parezca una nota científica destacada */
    [data-testid="stAlert"] {
        background-color: #ffffff !important; /* Forzar fondo blanco */
        color: #1e293b !important; /* Forzar texto oscuro legible */
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    /* Si estás usando st.info(), st.success(), etc., podemos estilizar el fondo. */
    /* Vamos a hacer que el reporte de IA se vea diferente, como una nota azulada clara. */
    .IA-Justification {
        background-color: #f0f9ff !important; /* Fondo azulado muy claro */
        color: #1e40af !important; /* Texto azul oscuro legible */
        border: 1px solid #bfdbfe !important; /* Borde azulado claro */
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 1.5rem;
    }

</style>
""", unsafe_allow_html=True)

load_dotenv()

# 3. Funciones de carga (Con fix para 'length')
@st.cache_data
def load_data(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    
    # Normalizar secuencia
    if 'Sequence_Normalized' not in df.columns and 'sequence' in df.columns:
        df['Sequence_Normalized'] = df['sequence']
    
    # FIX CRÍTICO: Asegurar columna 'length'
    if 'length' not in df.columns:
        if 'Sequence_Length' in df.columns:
            df['length'] = df['Sequence_Length']
        else:
            df['length'] = df['Sequence_Normalized'].astype(str).str.len()

    # Convertir a números
    cols_num = ['length', 'FunctionScore', 'SafetyScore', 'FinalScore', 'net_charge', 'hydrophobicity_eisenberg', 'hydrophobic_moment']
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    if 'id' not in df.columns:
        df['id'] = [f"PEP-{i+1}" for i in range(len(df))]
        
    return df

def get_gemini_targets(pathogen: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return "⚠️ API Key no configurada."
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Actúa como experto. Para el hongo {pathogen}, lista 3 blancos moleculares y PDB IDs."
        return model.generate_content(prompt).text
    except Exception as e: return f"❌ Error: {str(e)}"

# --- LÓGICA DE CARGA ---
data_source = "Peptides_Ranked_Final.csv"
if os.path.exists(data_source):
    df = load_data(data_source)
else:
    uploaded = st.file_uploader("Sube el CSV", type=['csv'])
    if uploaded: df = load_data(uploaded)
    else: st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🔍 Filtros")
    seq_q = st.text_input("Secuencia")
    # Fix para el slider de longitud
    min_l = int(df['length'].min())
    max_l = int(df['length'].max())
    len_range = st.slider("Longitud", min_l, max_l, (min_l, max_l))
    max_hemo = st.slider("Hemólisis máx (%)", 0.0, 100.0, 100.0)
    min_final = st.slider("FinalScore mín", 0.0, 100.0, 0.0)

# --- MAIN ---
st.title("🔬 Antimicrobial Tinder")
pathogen = st.text_input("Objetivo (Hongo)", placeholder="ej. Candida albicans")

if st.button("✨ Analizar con IA") and pathogen:
    st.info(get_gemini_targets(pathogen))

# Filtrado
mask = (df['length'] >= len_range[0]) & (df['length'] <= len_range[1]) & (df['FinalScore'] >= min_final)
if pathogen:
    mask &= df['Target Species'].astype(str).str.contains(pathogen, case=False, na=False) | \
            df['Target_Organism'].astype(str).str.contains(pathogen, case=False, na=False)
if seq_q:
    mask &= df['Sequence_Normalized'].str.contains(seq_q, case=False, na=False)

filtered_df = df[mask].sort_values(by='FinalScore', ascending=False)

# --- MÉTRICAS (Las que fallaban) ---
st.subheader("📊 Estadísticas de Búsqueda")
m1, m2, m3 = st.columns(3)
m1.metric("Universo Total", len(df))
m2.metric("Matches Hongo", len(df[df['Target Species'].str.contains(pathogen, case=False, na=False)]) if pathogen else 0)
m3.metric("Candidatos Finales", len(filtered_df))

st.dataframe(filtered_df[['id', 'Sequence_Normalized', 'FinalScore', 'Category']].head(50), use_container_width=True)

# --- RADAR ---
if not filtered_df.empty:
    st.divider()
    c1, c2 = st.columns([1, 1])
    with c1:
        sel_id = st.selectbox("Detalle del Péptido", filtered_df['id'])
        pep = filtered_df[filtered_df['id'] == sel_id].iloc[0]
        st.write(f"**ID:** {pep['id']}")
        st.code(pep['Sequence_Normalized'])
        st.write(f"**Categoría:** {pep['Category']}")
    
    with c2:
        radar_df = pd.DataFrame(dict(
            r=[pep['FunctionScore'], pep['SafetyScore'], pep['FinalScore'], (abs(pep['net_charge'])*5)],
            theta=['Función', 'Seguridad', 'FinalScore', 'Carga']
        ))
        fig = px.line_polar(radar_df, r='r', theta='theta', line_close=True)
        fig.update_traces(fill='toself', line_color='#4F46E5')
        st.plotly_chart(fig, use_container_width=True)