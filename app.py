import os
import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from dotenv import load_dotenv
import warnings

# 0. 🔑 INICIALIZACIÓN Y PERSISTENCIA (A PRUEBA DE HACKATHON)
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

# Inicialización del cliente de IA (si la llave existe)
client = genai.Client(api_key=api_key) if api_key else None

# --- MANEJO DE ESTADO (Para que la IA no se borre al filtrar) ---
if 'ai_report' not in st.session_state:
    st.session_state.ai_report = None
if 'selected_peptide_id' not in st.session_state:
    st.session_state.selected_peptide_id = None

warnings.filterwarnings("ignore", category=FutureWarning)
st.set_page_config(page_title="Antimicrobial Tinder", layout="wide", page_icon="🧪")

# 1. 🎨 CSS CIENTÍFICO LIGHT HOMOGÉNEO (REGENERACIÓN TOTAL)
st.markdown("""
<style>
    /* Fondo claro menta en toda la app */
    .stApp, header { background-color: #F0FDF4 !important; }
    
    /* Texto verde bosque oscuro */
    html, body, p, span, h1, h2, h3, h4, h5, h6, li, label { 
        color: #052E16 !important; 
    }

    /* Títulos destacados en Esmeralda */
    h1, h2, h3 { color: #166534 !important; }

    /* Cajas de código y números */
    .stCodeBlock, [data-testid="stCodeBlock"] pre, [data-testid="stCodeBlock"] code {
        background-color: #D1FAE5 !important; /* Fondo verde clarito */
        color: #052E16 !important;
        border: 1px solid #A7F3D0 !important;
    }
    p code {
        background-color: #D1FAE5 !important;
        color: #166534 !important;
        padding: 4px 12px !important;
        border-radius: 6px !important;
        font-weight: 800 !important; /* Negrita más fuerte */
        font-size: 1.25rem !important; /* Letra mucho más grande */
    }

    /* Menús desplegables blancos */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="popover"] > div, 
    ul[role="listbox"], 
    li[role="option"] {
        background-color: #FFFFFF !important;
        color: #052E16 !important;
    }
    li[role="option"]:hover, li[aria-selected="true"] {
        background-color: #D1FAE5 !important; /* Menta hover */
    }

    /* Tablas blancas limpias */
    [data-testid="stDataFrame"] > div { background-color: #FFFFFF !important; }
    
    /* Botón IA */
    .stButton>button { background-color: #16A34A !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# 2. 🧠 FUNCIONES CORE
@st.cache_data
def load_data(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    # Homogeneizar columnas
    df['Sequence_Normalized'] = df['sequence'] if 'sequence' in df.columns else df.get('Sequence_Normalized', "")
    if 'length' not in df.columns:
        df['length'] = df['Sequence_Normalized'].str.len()
    
    # Asegurar que todas las columnas críticas sean numéricas
    cols_num = ['length', 'FunctionScore', 'SafetyScore', 'FinalScore', 'net_charge', 
                'hydrophobicity_eisenberg', 'hydrophobic_moment', 'ChargeScore', 
                'HydrophobicityScore', 'AmphipathicityScore', 'LengthScore']
    
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    if 'id' not in df.columns:
        df['id'] = [f"PEP-{i+1}" for i in range(len(df))]
    return df

def generar_briefing_peptido(pep_row, hongo_nombre, modelo_seleccionado):
    if not client: return "⚠️ Error: API Key no configurada."
    
    # Extraemos los datos exactos del péptido seleccionado
    pep_id = pep_row['id']
    seq = pep_row['Sequence_Normalized']
    carga = pep_row['net_charge']
    hidro = pep_row['hydrophobicity_eisenberg']
    anfip = pep_row['hydrophobic_moment']
    
    prompt = f"""
    Como experto en fitopatología, analiza este candidato específico ({pep_id}) diseñado para combatir a: {hongo_nombre}.
    
    Datos exactos del {pep_id}:
    - Secuencia: {seq}
    - Carga Neta: {carga:.2f}
    - Hidrofobicidad: {hidro:.2f}
    - Anfipatía: {anfip:.2f}
    
    Genera un dictamen técnico indicando: 
    1. Mecanismo de acción probable para los valores exactos de este péptido. 
    2. Por qué es letal vs {hongo_nombre}. 
    3. Recomendación de uso.
    """
    
    try:
        response = client.models.generate_content(model=modelo_seleccionado, contents=prompt)
        return response.text
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e): return "🚨 QUOTA_EXCEEDED"
        return f"Error en la consulta: {e}"

# 3. 📂 CARGA DE DATOS
data_source = "Peptides_Ranked_Final.csv"
if os.path.exists(data_source):
    df = load_data(data_source)
else:
    # Mostramos el warning al jurado si falta el archivo
    st.error("👋 Por favor, asegúrate de que el archivo 'Peptides_Ranked_Final.csv' esté en la carpeta del proyecto.")
    st.stop()

# 4. 🎯 INTERFAZ PRINCIPAL (SIN SIDEBAR VISUAL)
st.title("Bienvenido a Peptinder")
st.markdown("### Plataforma Inteligente de Selección de Péptidos Fúngicos")

if not api_key:
    # Usamos la alerta roja corregida del CSS
    st.error("⚠️ No se encontró la GOOGLE_API_KEY en el archivo .env. El briefing estratégico no funcionará.")

col_filt1, col_filt2 = st.columns([2, 1])

with col_filt1:
    pathogen = st.text_input("🎯 Patógeno Objetivo", placeholder="ej. Fusarium, Candida...")

with col_filt2:
    num_results = st.selectbox("📊 Cantidad a mostrar", options=[5, 10, 50, 100, "Todos"], index=1)

# Lógica de filtrado
mask = df['length'] > 1 

if pathogen:
    search_term = pathogen.lower().strip()
    mask &= df.apply(lambda row: search_term in str(row.get('Target Species', '')).lower() or 
                                 search_term in str(row.get('Target_Organism', '')).lower(), axis=1)

filtered_df = df[mask].sort_values(by='FinalScore', ascending=False)
limit = len(filtered_df) if num_results == "Todos" else num_results

# 5. RESULTADOS (TABLA CON NOMBRES AMIGABLES)
st.subheader("📊 Ranking de Candidatos")
st.write(f"Se encontraron **{len(filtered_df)}** péptidos que cumplen los criterios.")

cols_cientificas = [
    'id', 'Sequence_Normalized', 'FinalScore', 
    'ChargeScore', 'net_charge', 
    'HydrophobicityScore', 'hydrophobicity_eisenberg',
    'AmphipathicityScore', 'hydrophobic_moment',
    'LengthScore', 'length', 'Category'
]

st.dataframe(
    filtered_df[cols_cientificas].head(limit),
    use_container_width=True,
    hide_index=True,
    column_config={
        "id": "ID",
        "Sequence_Normalized": "Secuencia",
        "net_charge": st.column_config.NumberColumn("Carga Neta", format="%.2f"),
        "hydrophobicity_eisenberg": st.column_config.NumberColumn("Hidrofobicidad", format="%.2f"),
        "hydrophobic_moment": st.column_config.NumberColumn("Anfipatía (μH)", format="%.2f"),
        "length": "Longitud (aa)",
        "Category": "Categoría",
        "FinalScore": st.column_config.ProgressColumn("Score Total 🎯", min_value=0, max_value=100, format="%.1f"),
        "ChargeScore": st.column_config.ProgressColumn("Score Carga", min_value=0, max_value=100, format="%d"),
        "HydrophobicityScore": st.column_config.ProgressColumn("Score Hidrof.", min_value=0, max_value=100, format="%d"),
        "AmphipathicityScore": st.column_config.ProgressColumn("Score Anfipatía", min_value=0, max_value=100, format="%d"),
        "LengthScore": st.column_config.NumberColumn("Score Longitud", format="%d")
    }
)

# 6. RECUPERACIÓN DEL GRÁFICO DE RADAR Y DETALLE (NUEVO PANEL)
if not filtered_df.empty:
    st.divider()
    
    # Panel de Selección de Péptido para Detalle
    st.subheader("🧬 Inspección Detallada del Candidato")
    col_sel, col_empty = st.columns([1, 2])
    with col_sel:
        peptide_list = filtered_df['id'].head(limit).tolist()
        st.session_state.selected_peptide_id = st.selectbox("Selecciona un ID para detalle:", peptide_list)

    if st.session_state.selected_peptide_id:
        # Obtenemos los datos del péptido seleccionado
        pep = filtered_df[filtered_df['id'] == st.session_state.selected_peptide_id].iloc[0]
        
        c_radar, c_raw = st.columns([2, 1])
        
        with c_radar:
            radar_df = pd.DataFrame(dict(
                r=[pep['ChargeScore'], pep['HydrophobicityScore'], pep['AmphipathicityScore'], pep['LengthScore'], pep['SafetyScore']],
                theta=['Carga', 'Hidrofo.', 'Anfipatía', 'Largo', 'Seguridad']
            ))
            fig = px.line_polar(radar_df, r='r', theta='theta', line_close=True)
            
            # Cambiamos a Verde Esmeralda
            fig.update_traces(fill='toself', line_color='#16A34A', fillcolor='rgba(22, 163, 74, 0.3)')
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#052E16', size=14),
                polar=dict(
                    bgcolor='rgba(255,255,255,0.5)',
                    radialaxis=dict(visible=True, range=[0, 100])
                ),
                margin=dict(l=30, r=30, t=30, b=30)
            )
            st.plotly_chart(fig, use_container_width=True)

        with c_raw:
            # Datos Raw Científicos
            st.success(f"**Calidad:** {pep['Category']} ✨")
            st.code(pep['Sequence_Normalized'], language="text")
            
            st.markdown(f"""
            - **Carga Neta Raw:** `{pep['net_charge']:.2f}`
            - **Hidrofobicidad Raw (Eisenberg):** `{pep['hydrophobicity_eisenberg']:.2f}`
            - **Anfipatía Raw (μH):** `{pep['hydrophobic_moment']:.2f}`
            - **Longitud Raw:** `{pep['length']} aa`
            - **Puntaje Final Raw:** `{pep['FinalScore']:.1f}`
            """)

# 7. 🚀 BRIEFING ESTRATÉGICO DE LA IA (CENTRALIZADO Y APILADO)
st.divider()

st.markdown("<h2 style='text-align: center; color: #166534;'>🛡️ Informe de Inteligencia Fúngica</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.1rem;'>Selecciona el modelo y presiona el botón para comenzar el análisis del candidato seleccionado.</p>", unsafe_allow_html=True)
st.write("")

col_izq, col_centro, col_der = st.columns([1, 2, 1])

target_pathogen = pathogen if (pathogen and pathogen.strip() != "") else "Hongos Fitopatógenos"

with col_centro:
    modelo_ai = st.selectbox("🤖 Selecciona el Motor de IA", options=[
        "gemini-3.1-flash-lite-preview",
        "gemini-3-flash-preview",
        "gemini-2.5-flash-lite-preview-09-2025"
    ])
    
    if st.button("🔬 Generar Dictamen Estratégico", use_container_width=True):
        # 1. Verificamos que haya un péptido seleccionado en el panel de arriba
        if st.session_state.selected_peptide_id:
            # 2. Buscamos la fila exacta de ese péptido
            pep_seleccionado = filtered_df[filtered_df['id'] == st.session_state.selected_peptide_id].iloc[0]
            
            with st.spinner(f"Gemini está analizando el {pep_seleccionado['id']}..."):
                # 3. Llamamos a la nueva función
                resultado = generar_briefing_peptido(pep_seleccionado, target_pathogen, modelo_ai)
                
                if resultado == "🚨 QUOTA_EXCEEDED":
                    st.error("❌ Cuota agotada para este modelo.")
                    st.warning("⚠️ Selecciona otro 'Motor de IA' en la lista desplegable de arriba.")
                    st.session_state.ai_report = None 
                else:
                    # Le agregamos un título clarísimo al reporte para que no queden dudas
                    st.session_state.ai_report = f"### 🎯 Análisis Técnico para el candidato: {pep_seleccionado['id']}\n\n" + resultado
        else:
            st.warning("Primero debes seleccionar un ID de péptido en el panel de Inspección Detallada.")

if st.session_state.ai_report:
    st.markdown("<br>", unsafe_allow_html=True)
    st.info(st.session_state.ai_report)