import os
import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from dotenv import load_dotenv
import warnings

# ==============================================================================
# 0. 🔑 INICIALIZACIÓN, PERSISTENCIA Y CONFIGURACIÓN
# ==============================================================================
# Carga de entorno robusta
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key or api_key == "":
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if "GOOGLE_API_KEY" in line and "=" in line:
                    api_key = line.split("=")[1].strip().replace('"', '').replace("'", "")
                    break

client = genai.Client(api_key=api_key) if api_key else None

# Persistencia de la IA y selección
if 'ai_report' not in st.session_state:
    st.session_state.ai_report = None
if 'selected_peptide_id' not in st.session_state:
    st.session_state.selected_peptide_id = None

# Higiene de la App y forzado de modo claro inicial
warnings.filterwarnings("ignore", category=FutureWarning)
st.set_page_config(
    page_title="Peptinder", 
    layout="wide", 
    page_icon="🧪",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# 🌟 1. BANNER SUPERIOR DE EQUIPO (Branding Incorporado y Centrado Vertical Solucionado)
# ==============================================================================
IMG_FONDO_PLANTACION = "https://images.unsplash.com/photo-1530836369250-ef71a3f5e48c?q=80&w=1600&auto=format&fit=crop"

# Variables de branding (Edita tus URLs de LinkedIn)
BRANDING_NAME = "TEAM PEPTINDER" # <--- ¡Cumplimos tu requisito de branding!
DESARROLLADO_POR_LABEL = "DESARROLLADO POR:"
MIEMBROS_EQUIPO = [
    {"nombre": "Daniel García Taddia", "url": "https://www.linkedin.com/in/danielgarciataddia/"},
    {"nombre": "Bruno Bassi", "url": "https://www.linkedin.com/in/bruno-bassi-65660823b/"},
]

# Construimos los botones en una sola línea continua (sin saltos de línea \n) para evitar fantasmas HTML
botones_links_html = "".join([f'<a href="{m["url"]}" target="_blank" class="linkedin-link">💼 {m["nombre"]}</a>' for m in MIEMBROS_EQUIPO])

st.markdown(f"""
<style>
    /* BANNER SUPERIOR EMERALD */
    .emerald-banner {{
        width: 100%;
        padding: 55px 0 25px 0; /* <--- Más espacio adentro (arriba) para que baje el texto */
        margin-bottom: 25px;
        margin-top: -4rem; /* <--- Menos agresivo para no salirse de la pantalla */
        
        /* Imagen de fondo suave translúcida (90% opacidad menta) */
        background-image: 
            linear-gradient(rgba(240, 253, 244, 0.65), rgba(240, 253, 244, 0.65)), 
            url('{IMG_FONDO_PLANTACION}');
        background-size: cover;
        background-position: center;
        border-bottom: 2px solid #A7F3D0;
        border-radius: 0 0 15px 15px;
        
        /* Flexbox COLUMN para centrar verticalmente todo el bloque de contenido */
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 8px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
    }}

    /* Título principal de Branding (Grande, Esmeralda) - Cumple requisito */
    .banner-title {{
        color: #166534 !important;
        font-size: 2.2rem !important; /* <--- Muy grande y destacado */
        font-weight: 800;
        margin: 0 !important;
        letter-spacing: -1px;
    }}

    /* Etiqueta 'Desarrollado por' (Gris neutro) */
    .banner-label {{
        color: #64748b !important;
        font-size: 0.85rem !important;
        font-weight: 500;
        margin: 0 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    /* Contenedor de links */
    .linkedin-container {{
        display: flex; gap: 15px; flex-wrap: wrap; justify-content: center;
    }}

    /* Botones de LinkedIn Emerald Lab */
    .linkedin-link {{
        background-color: #16A34A !important;
        color: white !important;
        text-decoration: none !important;
        padding: 8px 18px !important;
        border-radius: 25px !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 6px -1px rgba(22,163,74,0.3);
        transition: all 0.2s ease;
    }}
    .linkedin-link:hover {{
        background-color: #15803d !important;
        box-shadow: 0 8px 15px -3px rgba(22, 163, 74, 0.3);
        transform: translateY(-2px);
    }}

    /* ESTILOS GLOBALES EMERALD (Matando el modo oscuro forzado) */
    html, body, .stApp {{ background-color: #F0FDF4 !important; }}
    html, body, [class*="st-"] {{ color: #052E16 !important; font-family: 'Inter', sans-serif; }}
    h1, h2, h3 {{ color: #166534 !important; font-weight: 700 !important; letter-spacing: -1px; }}
    
    label p {{ color: #0F5132 !important; font-weight: 600 !important; font-size: 1.15rem !important; }}

    div[data-baseweb="select"] div[role="button"],
    .stSelectbox div[data-baseweb="select"],
    .stTextInput>div>div>input {{
        background-color: white !important;
        color: #052E16 !important;
        border-radius: 8px !important;
        border: 1px solid #A7F3D0 !important;
    }}

    /* Fix para el menú desplegable del autocompletar */
    div[data-testid="stVirtualDropdown"] div[role="listbox"] {{ background-color: white !important; }}
    div[data-testid="stVirtualDropdown"] li {{ color: #052E16 !important; background-color: white !important; }}
    div[data-testid="stVirtualDropdown"] li:hover {{ background-color: #D1FAE5 !important; }}

    /* Tabla */
    div[data-testid="stDataFrame"] {{
        background-color: white !important;
        border-radius: 12px;
        padding: 10px;
        border: 1px solid #A7F3D0;
    }}
    [data-testid="stDataFrame"] div[role="row"],
    [data-testid="stDataFrame"] div[role="cell"],
    [data-testid="stDataFrame"] div[role="columnheader"] {{ color: #052E16 !important; }}

    /* Botones de acción */
    .stButton>button {{
        background-color: #22C55E !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.2s ease;
    }}
    .stButton>button:hover {{ background-color: #16A34A !important; }}

    /* Cajas de IA y Valores Raw (Fuentes Grandes) */
    .stInfo {{
        background-color: #FFFFFF !important;
        color: #052E16 !important;
        border-left: 5px solid #22C55E !important;
        border-radius: 8px;
    }}
    .stCodeBlock, [data-testid="stCodeBlock"] pre, [data-testid="stCodeBlock"] code {{
        background-color: #D1FAE5 !important;
        color: #052E16 !important;
        border-radius: 8px;
    }}
    p code {{
        background-color: #D1FAE5 !important;
        color: #166534 !important;
        padding: 4px 12px !important;
        border-radius: 6px !important;
        font-weight: 800 !important;
        font-size: 1.25rem !important; /* Letra bien grande */
        margin: 0 2px;
    }}
</style>

<div class="emerald-banner"><h1 class="banner-title">{BRANDING_NAME}</h1><p class="banner-label">{DESARROLLADO_POR_LABEL}</p><div class="linkedin-container">{botones_links_html}</div></div>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. 🧠 FUNCIONES CORE Y LÓGICA DE DATOS
# ==============================================================================
@st.cache_data
def load_data(file) -> pd.DataFrame:
    df = pd.read_csv(file)
    df['Sequence_Normalized'] = df['sequence'] if 'sequence' in df.columns else df.get('Sequence_Normalized', "")
    if 'length' not in df.columns:
        df['length'] = df['Sequence_Normalized'].str.len()
    
    cols_num = ['length', 'FunctionScore', 'SafetyScore', 'FinalScore', 'net_charge', 'hydrophobicity_eisenberg', 'hydrophobic_moment']
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    if 'id' not in df.columns:
        df['id'] = [f"PEP-{i+1}" for i in range(len(df))]
    return df

def generar_briefing_peptido(pep_row, hongo_nombre, modelo_seleccionado):
    if not client: return "⚠️ Error: API Key no configurada."
    
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
    
    Genera un dictamen técnico breve indicando: 
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


# ==============================================================================
# 3. 📂 CARGA DE DATOS Y FILTROS PRINCIPALES
# ==============================================================================
data_source = "Peptides_Ranked_Final.csv"
if os.path.exists(data_source):
    df = load_data(data_source)
else:
    st.error("Archivo 'Peptides_Ranked_Final.csv' no encontrado.")
    st.stop()

st.title("🔬 Bienvenido a Peptinder")
st.markdown("### Plataforma Inteligente de Selección de Péptidos Fúngicos")

if not api_key:
    st.error("⚠️ No se encontró la GOOGLE_API_KEY en el archivo .env.")

col_filt1, col_filt2 = st.columns([2, 1])
with col_filt1:
    pathogen = st.text_input("🎯 Patógeno Objetivo", placeholder="ej. Fusarium, Candida...")
with col_filt2:
    num_results = st.selectbox("📊 Cantidad a mostrar en tabla", options=[5, 10, 50, 100, "Todos"], index=1)

mask = df['id'].notnull()
if pathogen:
    search_term = pathogen.lower().strip()
    mask &= df.apply(lambda row: search_term in str(row.get('Target Species', '')).lower() or 
                                 search_term in str(row.get('Target_Organism', '')).lower(), axis=1)

filtered_df = df[mask].sort_values(by='FinalScore', ascending=False)
limit = len(filtered_df) if num_results == "Todos" else num_results


# ==============================================================================
# 4. 📊 TABLA DE RESULTADOS (Nombres Limpios y Barras Emerald Lab)
# ==============================================================================
st.subheader("📊 Ranking de Candidatos")
st.write(f"Se encontraron **{len(filtered_df)}** péptidos que cumplen los criterios.")

cols_cientificas = [
    'id', 'Sequence_Normalized', 'FinalScore', 
    'ChargeScore', 'net_charge', 
    'HydrophobicityScore', 'hydrophobicity_eisenberg',
    'AmphipathicityScore', 'hydrophobic_moment',
    'LengthScore', 'length', 'Category'
]

# Tabla Científica Interactiva (Clara, texto oscuro)
st.dataframe(
    filtered_df[cols_cientificas].head(limit),
    use_container_width=True,
    hide_index=True,
    column_config={
        "id": "ID",
        "Sequence_Normalized": "Secuencia",
        "net_charge": st.column_config.NumberColumn("Carga Neta Raw", format="%.2f"),
        "hydrophobicity_eisenberg": st.column_config.NumberColumn("Hidrofobicidad Raw", format="%.2f"),
        "hydrophobic_moment": st.column_config.NumberColumn("Anfipatía Raw (μH)", format="%.2f"),
        "length": "Longitud (aa)",
        "Category": "Categoría ✨",
        "FinalScore": st.column_config.ProgressColumn("Puntaje Total ✨🎯", min_value=0, max_value=100, format="%.1f"),
        "ChargeScore": st.column_config.ProgressColumn("Score Carga", min_value=0, max_value=100, format="%d"),
        "HydrophobicityScore": st.column_config.ProgressColumn("Score Hidrofobicidad", min_value=0, max_value=100, format="%d"),
        "AmphipathicityScore": st.column_config.ProgressColumn("Score Anfipatía", min_value=0, max_value=100, format="%d"),
        "LengthScore": st.column_config.NumberColumn("Score Largo", format="%d")
    }
)


# ==============================================================================
# 5. 🧬 DETALLE Y RADAR (Transparente y Homogéneo)
# ==============================================================================
if not filtered_df.empty:
    st.divider()
    st.subheader("🧬 Inspección Detallada del Candidato")
    
    col_sel, col_empty = st.columns([1, 2.5])
    with col_sel:
        peptide_list = filtered_df['id'].head(limit).tolist()
        if not st.session_state.selected_peptide_id or st.session_state.selected_peptide_id not in peptide_list:
            st.session_state.selected_peptide_id = peptide_list[0]
            
        st.session_state.selected_peptide_id = st.selectbox("Selecciona un ID de la tabla para detalle:", peptide_list)

    if st.session_state.selected_peptide_id:
        pep = filtered_df[filtered_df['id'] == st.session_state.selected_peptide_id].iloc[0]
        c_radar, c_raw = st.columns([1.5, 1])
        
        with c_radar:
            radar_df = pd.DataFrame(dict(
                r=[pep['ChargeScore'], pep['HydrophobicityScore'], pep['AmphipathicityScore'], pep['LengthScore'], pep['SafetyScore']],
                theta=['Score Carga', 'Score Hidro.', 'Score Anfipatía', 'Score Largo', 'Bioseguridad']
            ))
            fig = px.line_polar(radar_df, r='r', theta='theta', line_close=True)
            # Trazado Emerald Lab
            fig.update_traces(fill='toself', line_color='#22C55E', fillcolor='rgba(34, 197, 94, 0.25)')
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', # Fondo 100% transparente para mezclarse con la app
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#052E16', size=14),
                polar=dict(
                    bgcolor='rgba(255,255,255,0.4)', # Fondo del radar blanco suave translúcido
                    radialaxis=dict(visible=True, range=[0, 100])
                ),
                margin=dict(l=30, r=30, t=30, b=30)
            )
            st.plotly_chart(fig, use_container_width=True)

        with c_raw:
            # Datos Raw Científicos (Letras grandes)
            st.markdown(f"**Categoría:** `{pep['Category']}` ✨")
            st.code(pep['Sequence_Normalized'], language="text")
            st.markdown(f"""
            - **Carga Neta:** `{pep['net_charge']:.2f}`
            - **Hidrofobicidad (Eisenberg):** `{pep['hydrophobicity_eisenberg']:.2f}`
            - **Anfipatía (μH):** `{pep['hydrophobic_moment']:.2f}`
            - **Longitud:** `{pep['length']} aa`
            - **Puntaje Total ✨🎯:** `{pep['FinalScore']:.1f}`
            """)


# ==============================================================================
# 6. 🚀 BRIEFING ESTRATÉGICO DE LA IA (Centrado y Apilado)
# ==============================================================================
st.divider()

st.markdown("<h2 style='text-align: center; color: #166534;'>🛡️ Informe de Inteligencia Fúngica</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.15rem; margin-bottom: 5px;'>Selecciona el modelo y presiona el botón para comenzar el análisis del candidato seleccionado en el panel de inspección de arriba.</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1rem; color: #475569; margin-top: 0;'>Gemini analizará la vulnerabilidad del patógeno específico contra este péptido.</p>", unsafe_allow_html=True)
st.write("")

col_izq, col_centro, col_der = st.columns([1, 2, 1])
target_pathogen = pathogen if (pathogen and pathogen.strip() != "") else "Hongos Fitopatógenos"

with col_centro:
    # Selector de modelo de respaldo integrado aquí
    modelo_ai = st.selectbox("🤖 Selecciona el Motor de IA (Respaldo)", options=[
        "gemini-3.1-flash-lite-preview",
        "gemini-3-flash-preview",
        "gemini-2.5-flash-lite-preview-09-2025"
    ], help="Si un modelo falla por cuota o tokens, prueba con otro.")
    
    # Botón ocupando el ancho central
    if st.button("🔬 Generar Dictamen Estratégico", use_container_width=True):
        if st.session_state.selected_peptide_id:
            pep_seleccionado = filtered_df[filtered_df['id'] == st.session_state.selected_peptide_id].iloc[0]
            
            with st.spinner(f"Gemini analizando el perfil de {pep_seleccionado['id']} contra membrane de {target_pathogen}..."):
                resultado = generar_briefing_peptido(pep_seleccionado, target_pathogen, modelo_ai)
                
                if resultado == "🚨 QUOTA_EXCEEDED":
                    st.error("❌ Cuota agotada para este modelo.")
                    st.warning("⚠️ Selecciona otro 'Motor de IA' en la lista desplegable de arriba para continuar.")
                    st.session_state.ai_report = None 
                else:
                    # Título clarísimo en el reporte persistente
                    st.session_state.ai_report = f"### 🎯 Análisis Técnico para el candidato: {pep_seleccionado['id']}\n\n" + resultado
        else:
            st.warning("Primero debes seleccionar un ID de péptido válido en el panel de Inspección Detallada de arriba.")

# Muestra el reporte ocupando todo el ancho inferior, centrado visualmente
if st.session_state.ai_report:
    st.markdown("<br>", unsafe_allow_html=True)
    st.info(st.session_state.ai_report)
