import os
import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from dotenv import load_dotenv
import warnings
from io import BytesIO

# 0. Configuración e Higiene
warnings.filterwarnings("ignore", category=FutureWarning)
st.set_page_config(page_title="Antimicrobial Tinder", layout="wide", page_icon="🧪")
load_dotenv()

# 1. 🎨 CSS MEJORADO (CONTRASTE TOTAL)
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; color: #1e293b; }
    [data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        padding: 15px !important;
        border-radius: 12px !important;
    }
    [data-testid="stMetricLabel"] > div { color: #64748b !important; }
    [data-testid="stMetricValue"] > div { color: #4f46e5 !important; }
    
    /* Cajas de código y alertas claras */
    [data-testid="stCodeBlock"] { background-color: #f1f5f9 !important; border: 1px solid #e2e8f0; }
    [data-testid="stCodeBlock"] pre { color: #0f172a !important; }
    .stAlert { background-color: #ffffff !important; color: #1e293b !important; border: 1px solid #e2e8f0 !important; }
    
    /* Estilo para la tabla */
    div[data-testid="stDataFrame"] > div { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# 2. Funciones Core
@st.cache_data
def load_data(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    if 'Sequence_Normalized' not in df.columns and 'sequence' in df.columns:
        df['Sequence_Normalized'] = df['sequence']
    
    # Asegurar columna length
    if 'length' not in df.columns:
        df['length'] = df['Sequence_Length'] if 'Sequence_Length' in df.columns else df['Sequence_Normalized'].str.len()
    
    # Asegurar que todas las columnas críticas sean numéricas
    cols_num = ['length', 'FunctionScore', 'SafetyScore', 'FinalScore', 'net_charge', 'hydrophobicity_eisenberg', 'hydrophobic_moment']
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    if 'id' not in df.columns:
        df['id'] = [f"PEP-{i+1}" for i in range(len(df))]
    return df

def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

# 3. Carga de Datos
data_source = "Peptides_Ranked_Final.csv"
if os.path.exists(data_source):
    df = load_data(data_source)
else:
    uploaded = st.file_uploader("Sube el archivo CSV", type=['csv'])
    if uploaded: df = load_data(uploaded)
    else: st.stop()

# 4. Sidebar (Filtros)
with st.sidebar:
    st.title("🔍 Panel de Control")
    seq_q = st.text_input("Secuencia contiene", placeholder="ej. KKK")
    
    st.subheader("Umbrales Biofísicos")
    min_l, max_l = int(df['length'].min()), int(df['length'].max())
    len_range = st.slider("Longitud", min_l, max_l, (min_l, max_l))
    min_final = st.slider("Puntaje Final Mínimo", 0.0, 100.0, 0.0)
    
    st.divider()
    st.subheader("Visualización")
    num_results = st.selectbox("Cantidad de péptidos a mostrar", options=[5, 10, 50, 100, 500, "Todos"], index=2)

# 5. Main: Búsqueda
st.title("🔬 Antimicrobial Tinder")
pathogen = st.text_input("🎯 Patógeno Objetivo", placeholder="ej. Candida albicans")

# Lógica de filtrado
mask = (df['length'] >= len_range[0]) & (df['length'] <= len_range[1]) & (df['FinalScore'] >= min_final)
if pathogen:
    search_term = pathogen.lower().strip()
    mask &= df['Target Species'].astype(str).str.lower().str.contains(search_term, na=False) | \
            df['Target_Organism'].astype(str).str.lower().str.contains(search_term, na=False)
if seq_q:
    mask &= df['Sequence_Normalized'].str.contains(seq_q, case=False, na=False)

filtered_df = df[mask].sort_values(by='FinalScore', ascending=False)

# 6. RESULTADOS Y EXPORTACIÓN (CORREGIDO Y CIENTÍFICO)
st.subheader("📊 Ranking de Candidatos")

# Botón de exportar
csv_data = convert_df(filtered_df)
st.download_button(
    label="📥 Exportar Resultados Filtrados a CSV",
    data=csv_data,
    file_name=f'resultados_{pathogen if pathogen else "global"}.csv',
    mime='text/csv',
)

# --- DEFINICIÓN DE COLUMNAS RELEVANTES ---
cols_investigador = [
    'id', 'Sequence_Normalized', 'FinalScore', 
    'ChargeScore', 'net_charge',           # El par de Carga
    'HydrophobicityScore', 'hydrophobicity_eisenberg', # El par de Hidrofo.
    'AmphipathicityScore', 'hydrophobic_moment', # El par de Anfipatía
    'LengthScore', 'length', 
    'SafetyScore', 'Category'
]

# Si NO hay patógeno, mostramos 'Target Species' para dar contexto
if not pathogen:
    cols_investigador.insert(2, 'Target Species')

# Verificamos que existan en el DF actual
actual_cols = [c for c in cols_investigador if c in filtered_df.columns]

# Cantidad a mostrar
limit = len(filtered_df) if num_results == "Todos" else num_results

# Tabla Científica Interactiva
st.dataframe(
    filtered_df[actual_cols].head(limit),
    use_container_width=True,
    hide_index=True,
    column_config={
        "id": "ID",
        "Sequence_Normalized": "Secuencia",
        "ChargeScore": st.column_config.ProgressColumn("Score Carga", min_value=0, max_value=100, format="%d"),
        "AmphipathicityScore": st.column_config.ProgressColumn("Score Anf.", min_value=0, max_value=100, format="%d"),
        "HydrophobicityScore": st.column_config.ProgressColumn("Score Hidro.", min_value=0, max_value=100, format="%d"),
        "Hemolytic_activity": "Hemólisis (Original)",
        "FinalScore": st.column_config.ProgressColumn("Total Score", min_value=0, max_value=100, format="%.1f"),
        "length": "Largo (aa)",
        "LengthScore": st.column_config.NumberColumn("Score Largo", format="%d"),
        "FunctionScore": st.column_config.NumberColumn("Func.", format="%.1f"),
        "SafetyScore": st.column_config.NumberColumn("Seg.", format="%.1f"),
        "net_charge": st.column_config.NumberColumn("Carga (+)", format="%.2f"),
        "hydrophobicity_eisenberg": st.column_config.NumberColumn("Hidrof.", format="%.2f"),
        "hydrophobic_moment": st.column_config.NumberColumn("Anfipatía", format="%.2f"),
        "Category": "Calidad",
        "Target Species": "Especies Reportadas"
    }
)

if len(filtered_df) > 0:
    st.caption(f"💡 Mostrando {min(len(filtered_df), limit if isinstance(limit, int) else len(filtered_df))} candidatos de {len(filtered_df)} encontrados. Haz clic en las cabeceras para ordenar.")
else:
    st.warning("No se encontraron péptidos con esos criterios.")

# 7. Análisis Detallado
if not filtered_df.empty:
    st.divider()
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("🧬 Detalle del Candidato")
        # El selectbox ahora también respeta el límite de visualización
        peptide_list = filtered_df['id'].head(limit).tolist()
        sel_id = st.selectbox("Selecciona un ID para inspección:", peptide_list)
        pep = filtered_df[filtered_df['id'] == sel_id].iloc[0]
        
        cat = pep['Category']
        if "Strong" in cat: st.success(f"**Clasificación:** {cat} 🌟")
        elif "Promising" in cat: st.warning(f"**Clasificación:** {cat} ⭐")
        else: st.info(f"**Clasificación:** {cat}")
        
        st.code(pep['Sequence_Normalized'], language="text")
        
        # Explicación científica de los valores
        st.markdown(f"""
        - **Carga Neta:** `{pep['net_charge']:.2f}` (Atracción a membranas fúngicas)
        - **Hidrofobicidad:** `{pep['hydrophobicity_eisenberg']:.2f}` (Capacidad de inserción)
        - **Momento Hidrofóbico:** `{pep['hydrophobic_moment']:.2f}` (Anfipatía/Poro)
        """)
        
        if pep['SafetyScore'] == 50:
            st.caption("ℹ️ *Safety Score de 50: Valor neutral por ausencia de datos de hemólisis.*")

    with c2:
        # Radar con 4 ejes biofísicos clave
        radar_df = pd.DataFrame(dict(
            r=[pep['FunctionScore'], pep['SafetyScore'], min(abs(pep['net_charge'])*10, 100), pep['hydrophobic_moment']*100 if pep['hydrophobic_moment'] < 1 else 100],
            theta=['Eficacia', 'Bioseguridad', 'Carga (+)', 'Anfipatía']
        ))
        fig = px.line_polar(radar_df, r='r', theta='theta', line_close=True)
        fig.update_traces(fill='toself', line_color='#4F46E5', fillcolor='rgba(79, 70, 229, 0.3)')
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(l=40, r=40, t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)