"""
Sistema de Dashboard de Presupuestos - Colegio Rogers Hall
VERSION FINAL: GOOGLE SHEETS AUTOMÁTICO (Estilo SINAPSIS)
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

# ✅ ENLACE CONECTADO CORRECTAMENTE
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSJEN3uWSwROA6s6jk3lZSg7iSK95aDlP9mf4AqxVfJZJQb4-mhIOkJyoy_2wRWwE9gWOUFNOzmdRNs/pub?gid=0&single=true&output=csv"

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

# ==================== CARGAR DATOS (SIN CACHÉ) ====================
@st.cache_data(ttl=0)
def load_data(url):
    try:
        # Truco técnico: Agregamos tiempo al link para obligar la descarga fresca
        timestamp = int(time.time())
        final_url = f"{url}&v={timestamp}"
            
        # Leemos directo de Google
        df = pd.read_csv(final_url)
        
        # Limpieza de columnas
        df.columns = df.columns.str.lower().str.strip()
        
        # Mapa de renombres para asegurar compatibilidad
        rename_map = {
            'concepto del gasto': 'concepto',
            'descripción del gasto': 'descripcion',
            'para que va a servir': 'proposito'
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
        
        # --- LIMPIEZA INTELIGENTE DE MONTOS ---
        # Detecta si viene como texto "$10,000.00" o "10.000,00" y lo arregla
        if 'importe' in df.columns:
            def limpiar_moneda(val):
                if isinstance(val, (int, float)):
                    return val
                val = str(val).strip()
                if val == 'nan': return 0
                
                # Caso europeo (Puntos miles, coma decimal): "10.000,00"
                if ',' in val and '.' in val and val.rfind(',') > val.rfind('.'):
                    val = val.replace('.', '').replace(',', '.')
                # Caso mixto raro o simple con coma decimal: "10000,00"
                elif ',' in val and '.' not in val:
                    val = val.replace(',', '.')
                # Caso estándar (Coma miles, punto decimal): "10,000.00"
                else:
                    val = val.replace(',', '') 
                
                return float(val)

            df['importe'] = df['importe'].apply(limpiar_moneda)
            
        return df, None
    except Exception as e:
        return None, str(e)

# ==================== SIDEBAR - CONTROL ====================
st.sidebar.markdown("### 🔄 Control de Datos")

if st.sidebar.button("⟳ ACTUALIZAR DATOS", type="primary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.info("Modifica el Google Sheet y presiona el botón para ver los cambios.")

# Carga inicial
df, error = load_data(SHEET_URL)

if error:
    st.error(f"❌ Error conectando: {error}")
    st.stop()

# ==================== FILTROS ====================
st.sidebar.markdown("---")
st.sidebar.markdown("## 🎛️ Filtros")

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

# ==================== APLICAR FILTROS ====================
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

# ==================== GRÁFICOS (SINAPSIS) ====================
col_chart1, col_chart2 = st.columns([2, 1])

with col_chart1:
    st.markdown("### 📊 Gasto Mensual")
    meses_orden_list = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    df_mes = df_filtered.groupby('mes')['importe'].sum().reset_index()
    # Logica para ordenar meses
    df_mes['mes_orden'] = df_mes['mes'].map({m: i for i, m in enumerate(meses_orden_list)}).fillna(0)
    df_mes = df_mes.sort_values('mes_orden')
    
    fig_mes = go.Figure(go.Bar(
        y=df_mes['mes'], x=df_mes['importe'], orientation='h',
        marker=dict(color=df_mes['importe'], colorscale=[[0, '#4fd1c5'], [1, '#b794f4']]),
        text=[f'${x:,.0f}' for x in df_mes['importe']], textposition='outside',
        textfont=dict(color='#e2e8f0'), hovertemplate='<b>%{y}</b><br>$%{x:,.0f}<extra></extra>'
    ))
    fig_mes.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#e2e8f0'), xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'), margin=dict(l=60, r=80, t=20, b=40), height=400)
    st.plotly_chart(fig_mes, use_container_width=True)

with col_chart2:
    st.markdown("### 🥧 Distribución")
    df_con = df_filtered.groupby('concepto')['importe'].sum().reset_index().sort_values('importe', ascending=False)
    fig_pie = go.Figure(data=[go.Pie(labels=df_con['concepto'], values=df_con['importe'], hole=0.5, marker=dict(colors=CHART_COLORS))])
    fig_pie.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#e2e8f0'), showlegend=False, margin=dict(l=20, r=20, t=20, b=20), height=400, annotations=[dict(text=f'<b>${total_gasto/1000000:.1f}M</b>', x=0.5, y=0.5, font_size=18, font_color='#4fd1c5', showarrow=False)])
    st.plotly_chart(fig_pie, use_container_width=True)

# FILA 2
col_chart3, col_chart4 = st.columns(2)

with col_chart3:
    st.markdown("### 🏢 Gasto por Departamento")
    df_dept = df_filtered.groupby('departamento')['importe'].sum().reset_index().sort_values('importe', ascending=True)
    fig_dept = go.Figure(go.Bar(x=df_dept['importe'], y=df_dept['departamento'], orientation='h', marker=dict(color=CHART_COLORS[:len(df_dept)]), text=[f'${x:,.0f}' for x in df_dept['importe']], textposition='outside', textfont=dict(color='#e2e8f0')))
    fig_dept.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#e2e8f0'), xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'), margin=dict(l=100, r=20, t=20, b=40), height=350)
    st.plotly_chart(fig_dept, use_container_width=True)

with col_chart4:
    st.markdown("### 📈 Tendencia por Año")
    if 'mes_num' in df_filtered.columns:
        df_tend = df_filtered.groupby(['año', 'mes', 'mes_num'])['importe'].sum().reset_index()
        fig_tend = go.Figure()
        for i, año in enumerate(sorted(df_tend['año'].unique())):
            dfa = df_tend[df_tend['año'] == año].sort_values('mes_num')
            fig_tend.add_trace(go.Scatter(x=dfa['mes'], y=dfa['importe'], mode='lines+markers', name=str(año), line=dict(width=3, color=CHART_COLORS[i])))
        fig_tend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#e2e8f0'), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'), legend=dict(orientation='h', y=1.1), margin=dict(l=20, r=20, t=20, b=20), height=350)
        st.plotly_chart(fig_tend, use_container_width=True)

# FILA 3
col_chart5, col_chart6 = st.columns([2, 1])
with col_chart5:
    st.markdown("### 📊 Comparativo Depto/Curso")
    df_comp = df_filtered.groupby(['departamento', 'curso_escolar'])['importe'].sum().reset_index()
    fig_comp = px.bar(df_comp, x='departamento', y='importe', color='curso_escolar', barmode='group', color_discrete_sequence=CHART_COLORS)
    fig_comp.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#e2e8f0'), xaxis=dict(title=''), yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title=''), legend=dict(orientation='h', y=1.1), height=350)
    st.plotly_chart(fig_comp, use_container_width=True)

with col_chart6:
    st.markdown("### 📅 Por Año")
    df_yr = df_filtered.groupby('año')['importe'].sum().reset_index()
    fig_yr = go.Figure(go.Bar(x=df_yr['año'].astype(str), y=df_yr['importe'], marker=dict(color=['#4fd1c5', '#f6ad55']), text=[f'${x:,.0f}' for x in df_yr['importe']], textposition='outside', textfont=dict(color='#e2e8f0')))
    fig_yr.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#e2e8f0'), xaxis=dict(title=''), yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title=''), height=350)
    st.plotly_chart(fig_yr, use_container_width=True)

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div class="footer">
    <p>Desarrollado por <strong style="color: #4fd1c5;">SINAPSIS</strong> - Consultoría en Transformación Digital</p>
    <p>© 2025 Colegio Peninsular Rogers Hall</p>
</div>
""", unsafe_allow_html=True)
