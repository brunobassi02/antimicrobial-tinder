# 🧬 TEAM PEPTINDER
**Plataforma Inteligente de Selección de Péptidos Fúngicos**

Peptinder es una herramienta bioinformática interactiva diseñada para acelerar el descubrimiento de péptidos antimicrobianos (AMPs) contra hongos fitopatógenos. Combina análisis de datos fisicoquímicos con Inteligencia Artificial para seleccionar a los mejores candidatos.

### 🚀 Funcionalidades Principales

* 🔍 **Búsqueda Inteligente:** Filtra la base de datos de péptidos especificando el patógeno objetivo (ej. *Fusarium*, *Botrytis*).
* 📊 **Ranking Multicriterio:** Evalúa a los candidatos mediante un "Score Total" basado en carga neta, hidrofobicidad, anfipatía y longitud.
* 🕸️ **Inspección de Candidatos (Radar):** Visualización interactiva del perfil biofísico exacto del péptido seleccionado para evaluar su viabilidad y seguridad.
* 🤖 **Dictamen Estratégico IA:** Integración con Google Gemini para generar un informe técnico instantáneo sobre el mecanismo de acción y la letalidad del péptido contra la membrana del hongo.

---

### 💻 Cómo ejecutar la App localmente

Si deseas correr la aplicación en tu propia máquina, sigue estos sencillos pasos:

**1. Requisitos previos**
Asegúrate de tener Python instalado (versión 3.9 o superior).

**2. Instalar las dependencias**
Abre tu terminal en la carpeta del proyecto e instala las librerías necesarias ejecutando:
`pip install streamlit pandas plotly google-genai python-dotenv`

**3. Configurar la API Key de Google (Gemini)**
Para que el motor de IA funcione, crea un archivo llamado `.env` en la misma carpeta del proyecto y agrega tu clave de la siguiente manera:
`GOOGLE_API_KEY="tu_clave_de_google_aqui"`

*(Nota: La app funcionará y mostrará los datos y gráficos incluso si no tienes la clave, pero la función del "Dictamen Estratégico" estará desactivada).*

**4. Ejecutar Peptinder**
En la terminal, corre el siguiente comando:
`streamlit run app.py`

¡Listo! La aplicación se abrirá automáticamente en tu navegador predeterminado (usualmente en `http://localhost:8501`).