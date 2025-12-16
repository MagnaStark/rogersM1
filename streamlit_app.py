"""
Sistema de Dashboard de Presupuestos - Colegio Rogers Hall
VERSION FINAL: CORREGIDA (Fix Curso Escolar)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

# ==================== CONFIGURACIÓN ====================
st.set_page_config(
    page_title="Dashboard Presupuestos - Rogers Hall",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ✅ ENLACE CONFIGURADO (Tu archivo Google Sheet)
FILE_ID = "1TxxfkTKk1ksoO7qsezoJPHNwNB2UAFbvh-TpJVYyZUQ"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv&gid=0"

# ==================== ESTILOS CSS (SINAPSIS) ====================
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    [data-testid="stSidebar"] { background-color: #1a1f2e; }
    [data-testid="stSidebar"] .stMarkdown { color: #ffffff; }
    h1, h2, h3 { color: #ffffff !important; }
    .metric-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #252d3d 100%);
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #2d3748;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .metric-value { font-size: 36px; font-weight: 700; color: #4fd1c5; margin-bottom: 5px; }
    .metric-label { font-size: 14px; color: #a0aec0; text-transform: uppercase; letter-spacing: 1px; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    hr { border-color: #2d3748; }
    .footer { text-align: center; color: #718096; padding: 20px; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# ==================== PALETA DE COLORES ====================
CHART_COLORS = ['#4fd1c5', '#f6ad55', '#fc8181', '#b794f4', '#63b3ed', '#68d391', '#faf089', '#f687b3']

# ==================== CARGAR DATOS ====================
@st.cache_data(ttl=0)
def load_data(url):
    try:
        # Truco técnico: Timestamp para evitar caché
        final_url = f"{url}&v={int(time.time())}"
        
        # Leemos el CSV
        df = pd.read_csv(final_url)
        
        # Limpieza de columnas (minusculas y sin espacios extra)
        df.columns = df.columns.str.lower().str.strip()
        
        # --- CORRECCIÓN DEL ERROR AQUÍ ---
        rename_map = {
            'concepto del gasto': 'concepto',
            'descripción del gasto': 'descripcion',
            'para que va a servir': 'proposito',
            'curso escolar': 'curso_escolar'  # <--- ESTO ARREGLA EL ERROR
        }
        df = df.rename(columns=rename_map)

        # Mapeo de meses
        meses_orden = {'Ene': 1, 'Feb': 2, 'Mar': 3, 'Abr': 4, 'May': 5, 'Jun': 6, 
                       'Jul': 7, 'Ago': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dic': 12}
        
        if 'mes' in df.columns:
            if df['mes'].dtype == object:
                df['mes_num'] = df['mes'].map(meses_orden)
            else:
                df['mes_num'] = df['mes']
        
        # Limpieza de importes
        if 'importe' in df.columns:
            def limpiar_moneda(val):
                if pd.isna(val): return 0
                if isinstance(val, (int, float)): return val
                val = str(val).strip()
                if ',' in val and '.' in val and val.rfind(',') > val.rfind('.'):
                    val = val.replace('.', '').replace(',', '.')
                elif ',' in val and '.' not in val:
                     val = val.replace(',', '.')
                else:
                    val = val.replace(',', '')
                try:
                    return float(val)
                except:
                    return 0
            df['importe'] = df['importe'].apply(limpiar_moneda)
            
        return df, None
    except Exception as e:
        return None, str(e)

# ==================== SIDEBAR ====================
st.sidebar.markdown("### 🔄 Control de Datos")

if st.sidebar.button("⟳ ACTUALIZAR DATOS", type="primary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.info("Modifica el Google Sheet y presiona el botón.")

# Carga inicial
df, error = load_data(SHEET_URL)

if error:
    st.error(f"❌ Error conectando: {error}")
    st.warning("Revisa el enlace o los permisos del Google Sheet.")
    st.stop()

# ==================== FILTROS ====================
st.sidebar.markdown("---")
st.sidebar.markdown("## 🎛️ Filtros")

# Validamos que las columnas existan antes de crear filtros
if 'departamento' not in df.columns or 'curso_escolar' not in df.columns:
    st.error("⚠️ Error de columnas. Verifica que tu Excel tenga: Departamento, Curso Escolar, Año, Mes, Importe")
    st.stop()

departamentos = df['departamento'].unique().tolist()
dept_selected = st.sidebar.multiselect("Departamentos", departamentos, default=departamentos)

st.sidebar.markdown("---")
cursos = df['curso_escolar'].unique().tolist()
curso_selected = st.sidebar.multiselect("Cursos", cursos, default=cursos)

st.sidebar.markdown("---")
años = sorted(df['año'].unique().tolist())
año_selected = st.sidebar.multiselect("Años", años, default=años)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; color: #718096; font-size: 12px; padding: 20px;'>
    <strong>SINAPSIS</strong><br>
    Consultoría en Transformación Digital<br><br>
    📊 Dashboard Cloud
</div>
""", unsafe_allow_html=True)

if not dept_selected or not curso_selected or not año_selected:
    st.warning("⚠️ Selecciona filtros")
    st.stop()

df_filtered = df[
    (df['departamento'].isin(dept_selected)) &
    (df['curso_escolar'].isin(curso_selected)) &
    (df['año'].isin(año_selected))
]

# ==================== KPIs ====================
col1, col2, col3, col4 = st.columns(4)

total_gasto = df_filtered['importe'].sum()
promedio_gasto = df_filtered['importe'].mean() if len(df_filtered) > 0 else 0
num_registros = len(df_filtered)
max_gasto = df_filtered['importe'].max() if len(df_filtered) > 0 else 0

with col1:
    st.markdown(f"""<div class="metric-card"><div class="metric-value">${total_gasto:,.0f}</div><div class="metric-label">Gasto Total</div></div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="metric-card"><div class="metric-value" style="color: #f6ad55;">${promedio_gasto:,.0f}</div><div class="metric-label">Promedio</div></div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="metric-card"><div class="metric-value" style="color: #63b3ed;">{num_registros}</div><div class="metric-label">Registros</div></div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class="metric-card"><div class="metric-value" style="color: #68d391;">${max_gasto:,.0f}</div><div class="metric-label">Máximo</div></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==================== GRÁFICOS ====================
col_chart1, col_chart2 = st.
