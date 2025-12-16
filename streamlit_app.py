"""
Sistema de Dashboard de Presupuestos - Colegio Rogers Hall
VERSION CLOUD - Lee desde OneDrive/SharePoint (CON ANTI-CACHÉ)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
from io import BytesIO
import time  # <--- NUEVO: Necesario para el truco del tiempo

# ==================== CONFIGURACIÓN ====================
# Enlace base (Tu enlace público directo)
EXCEL_URL = "https://unimodelo-my.sharepoint.com/:x:/g/personal/maximiliano_baston_modelo_edu_mx/IQBiqVAOknLuQJazwnLNkjWcARZUcbO94bXR8_54VabNL34?download=1"

st.set_page_config(
    page_title="Dashboard Presupuestos - Rogers Hall",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== ESTILOS CSS DARK MODE ====================
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    
    [data-testid="stSidebar"] {
        background-color: #1a1f2e;
    }
    
    h1, h2, h3 {
        color: #ffffff !important;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #252d3d 100%);
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #2d3748;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    
    .metric-value {
        font-size: 36px;
        font-weight: 700;
        color: #4fd1c5;
        margin-bottom: 5px;
    }
    
    .metric-label {
        font-size: 14px;
        color: #a0aec0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .footer {
        text-align: center;
        color: #718096;
        padding: 20px;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== PALETA DE COLORES ====================
CHART_COLORS = ['#4fd1c5', '#f6ad55', '#fc8181', '#b794f4', '#63b3ed', '#68d391', '#faf089', '#f687b3']

# ==================== CARGAR DATOS ====================
# @st.cache_data(ttl=30)  <--- COMENTADO PARA FORZAR RECARGA REAL
def load_data():
    """Descarga y lee el Excel desde OneDrive/SharePoint con Anti-Caché"""
    try:
        # TRUCO: Agregamos un timestamp al final (?v=123456) para que Microsoft
        # piense que es una URL nueva y no nos de el archivo viejo.
        url_con_timestamp = EXCEL_URL + f"&v={time.time()}"
        
        response = requests.get(url_con_timestamp)
        response.raise_for_status()
        
        df = pd.read_excel(BytesIO(response.content), sheet_name='Base datos', engine='openpyxl')
        df.columns = ['concepto', 'proposito', 'descripcion', 'departamento', 'curso_escolar', 'mes', 'año', 'importe']
        
        meses_orden = {'Ene': 1, 'Feb': 2, 'Mar': 3, 'Abr': 4, 'May': 5, 'Jun': 6, 
                       'Jul': 7, 'Ago': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dic': 12}
        df['mes_num'] = df['mes'].map(meses_orden)
        return df, None
    except Exception as e:
        return None, str(e)

# Sidebar - Botón actualizar
st.sidebar.markdown("### 🔄 Actualizar")
if st.sidebar.button("⟳ RECARGAR DATOS", use_container_width=True, type="primary"):
    # Limpiamos caché de Streamlit por si acaso
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("""
<div style='background: #2d3748; padding: 10px; border-radius: 8px; font-size: 12px; color: #a0aec0;'>
    <strong>📝 Para actualizar:</strong><br>
    1. Edita el Excel en OneDrive (Navegador)<br>
    2. Espera que diga "Guardado"<br>
    3. Presiona el botón arriba
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Cargar datos
df, error = load_data()

if error:
    st.error(f"❌ Error al cargar datos: {error}")
    st.stop()

if df is None or len(df) == 0:
    st.error("❌ No se pudieron cargar los datos")
    st.stop()

# ==================== SIDEBAR - FILTROS ====================
st.sidebar.markdown("## 🎛️ Filtros")

# Filtro Departamento
st.sidebar.markdown("### 🏢 Departamento")
departamentos = df['departamento'].unique().tolist()
dept_selected = st.sidebar.multiselect(
    "Departamentos",
    options=departamentos,
    default=departamentos,
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

# Filtro Curso Escolar
st.sidebar.markdown("### 📚 Curso Escolar")
cursos = df['curso_escolar'].unique().tolist()
curso_selected = st.sidebar.multiselect(
    "Cursos",
    options=cursos,
    default=cursos,
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

# Filtro Año
st.sidebar.markdown("### 📅 Año")
años = sorted(df['año'].unique().tolist())
año_selected = st.sidebar.multiselect(
    "Años",
    options=años,
    default=años,
    label_visibility="collapsed"
)

# ==================== APLICAR FILTROS ====================
if not dept_selected or not curso_selected or not año_selected:
    st.warning("⚠️ Selecciona al menos un valor en cada filtro")
    st.stop()

df_filtered = df[
    (df['departamento'].isin(dept_selected)) &
    (df['curso_escolar'].isin(curso_selected)) &
    (df['año'].isin(año_selected))
]

# ==================== HEADER ====================
st.markdown("""
<div style='text-align: center; padding: 20px 0 30px 0;'>
    <h1 style='color: #ffffff; font-size: 32px; margin-bottom: 5px;'>
        🎓 Sistema de Gestión de Presupuestos
    </h1>
    <p style='color: #718096; font-size: 16px;'>
        Colegio Peninsular Rogers Hall
    </p>
</div>
""", unsafe_allow_html=True)

# ==================== KPIs ====================
col1, col2, col3, col4 = st.columns(4)

total_gasto = df_filtered['importe'].sum()
promedio_gasto = df_filtered['importe'].mean() if len(df_filtered) > 0 else 0
num_registros = len(df_filtered)
max_gasto = df_filtered['importe'].max() if len(df_filtered) > 0 else 0

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">${total_gasto:,.0f}</div>
        <div class="metric-label">Gasto Total</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #f6ad55;">${promedio_gasto:,.0f}</div>
        <div class="metric-label">Promedio por Gasto</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #63b3ed;">{num_registros}</div>
        <div class="metric-label">Total Registros</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color: #68d391;">${max_gasto:,.0f}</div>
        <div class="metric-label">Gasto Máximo</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==================== GRÁFICAS ====================
col_chart1, col_chart2 = st.columns([2, 1])

with col_chart1:
    st.markdown("### 📊 Gasto Mensual")
    
    meses_orden = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    df_mes = df_filtered.groupby('mes')['importe'].sum().reset_index()
    df_mes['mes_orden'] = df_mes['mes'].map({m: i for i, m in enumerate(meses_orden)})
    df_mes = df_mes.sort_values('mes_orden')
    
    fig_mes = go.Figure()
    fig_mes.add_trace(go.Bar(
        y=df_mes['mes'],
        x=df_mes['importe'],
        orientation='h',
        marker=dict(
            color=df_mes['importe'],
            colorscale=[[0, '#4fd1c5'], [0.5, '#63b3ed'], [1, '#b794f4']],
        ),
        text=[f'${x:,.0f}' for x in df_mes['importe']],
        textposition='outside',
        textfont=dict(color='#e2e8f0', size=11),
        hovertemplate='<b>%{y}</b><br>Importe: $%{x:,.0f}<extra></extra>'
    ))
    
    fig_mes.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0'),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='', tickformat='$,.0f'),
        yaxis=dict(showgrid=False, categoryorder='array', categoryarray=meses_orden[::-1]),
        margin=dict(l=60, r=80, t=20, b=40),
        height=400
    )
    
    st.plotly_chart(fig_mes, use_container_width=True)

with col_chart2:
    st.markdown("### 🥧 Distribución por Concepto")
    
    df_concepto = df_filtered.groupby('concepto')['importe'].sum().reset_index()
    df_concepto = df_concepto.sort_values('importe', ascending=False)
    
    fig_pie = go.Figure()
    fig_pie.add_trace(go.Pie(
        labels=df_concepto['concepto'],
        values=df_concepto['importe'],
        hole=0.5,
        marker=dict(colors=CHART_COLORS),
        textinfo='percent',
        textposition='outside',
        textfont=dict(color='#e2e8f0', size=11),
        hovertemplate='<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>'
    ))
    
    fig_pie.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0'),
        showlegend=True,
        legend=dict(font=dict(size=10, color='#a0aec0'), orientation='v', yanchor='middle', y=0.5, xanchor='left', x=1.05),
        margin=dict(l=20, r=120, t=20, b=20),
        height=400,
        annotations=[dict(text=f'<b>${total_gasto/1000000:.1f}M</b>', x=0.5, y=0.5, font_size=18, font_color='#4fd1c5', showarrow=False)]
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)

# ==================== FILA 2 ====================
col_chart3, col_chart4 = st.columns(2)

with col_chart3:
    st.markdown("### 🏢 Gasto por Departamento")
    
    df_dept = df_filtered.groupby('departamento')['importe'].sum().reset_index()
    df_dept = df_dept.sort_values('importe', ascending=True)
    
    fig_dept = go.Figure()
    fig_dept.add_trace(go.Bar(
        x=df_dept['importe'],
        y=df_dept['departamento'],
        orientation='h',
        marker=dict(color=CHART_COLORS[:len(df_dept)]),
        text=[f'${x:,.0f}' for x in df_dept['importe']],
        textposition='outside',
        textfont=dict(color='#e2e8f0', size=12),
        hovertemplate='<b>%{y}</b><br>$%{x:,.0f}<extra></extra>'
    ))
    
    fig_dept.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0'),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickformat='$,.0f'),
        yaxis=dict(showgrid=False),
        margin=dict(l=100, r=80, t=20, b=40),
        height=350
    )
    
    st.plotly_chart(fig_dept, use_container_width=True)

with col_chart4:
    st.markdown("### 📈 Tendencia por Año")
    
    meses_ord = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    df_tend = df_filtered.groupby(['año', 'mes', 'mes_num'])['importe'].sum().reset_index()
    
    fig_tend = go.Figure()
    
    for i, año in enumerate(sorted(df_tend['año'].unique())):
        df_año = df_tend[df_tend['año'] == año].sort_values('mes_num')
        fig_tend.add_trace(go.Scatter(
            x=df_año['mes'],
            y=df_año['importe'],
            mode='lines+markers',
            name=str(año),
            line=dict(width=3, color=CHART_COLORS[i]),
            marker=dict(size=8),
            hovertemplate=f'<b>{año}</b><br>%{{x}}: $%{{y:,.0f}}<extra></extra>'
        ))
    
    fig_tend.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0'),
        xaxis=dict(showgrid=False, categoryorder='array', categoryarray=meses_ord),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickformat='$,.0f'),
        legend=dict(font=dict(color='#a0aec0'), orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=60, r=20, t=40, b=40),
        height=350
    )
    
    st.plotly_chart(fig_tend, use_container_width=True)

# ==================== FILA 3 ====================
col_chart5, col_chart6 = st.columns([2, 1])

with col_chart5:
    st.markdown("### 📊 Comparativo Departamento por Curso Escolar")
    
    df_comp = df_filtered.groupby(['departamento', 'curso_escolar'])['importe'].sum().reset_index()
    
    fig_comp = px.bar(
        df_comp,
        x='departamento',
        y='importe',
        color='curso_escolar',
        barmode='group',
        color_discrete_sequence=CHART_COLORS,
        text_auto='.2s'
    )
    
    fig_comp.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0'),
        xaxis=dict(showgrid=False, title=''),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='', tickformat='$,.0f'),
        legend=dict(title='', font=dict(color='#a0aec0'), orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=60, r=20, t=40, b=40),
        height=350
    )
    fig_comp.update_traces(textposition='outside', textfont=dict(color='#e2e8f0', size=10))
    
    st.plotly_chart(fig_comp, use_container_width=True)

with col_chart6:
    st.markdown("### 📅 Por Año")
    
    df_año = df_filtered.groupby('año')['importe'].sum().reset_index()
    
    fig_año = go.Figure()
    fig_año.add_trace(go.Bar(
        x=df_año['año'].astype(str),
        y=df_año['importe'],
        marker=dict(color=['#4fd1c5', '#f6ad55'][:len(df_año)]),
        text=[f'${x:,.0f}' for x in df_año['importe']],
        textposition='outside',
        textfont=dict(color='#e2e8f0', size=14),
        hovertemplate='<b>%{x}</b><br>$%{y:,.0f}<extra></extra>'
    ))
    
    fig_año.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0'),
        xaxis=dict(showgrid=False, title=''),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='', tickformat='$,.0f'),
        margin=dict(l=60, r=20, t=20, b=40),
        height=350
    )
    
    st.plotly_chart(fig_año, use_container_width=True)

# ==================== TABLA ====================
st.markdown("### 📋 Top 10 Gastos")

df_top = df_filtered.nlargest(10, 'importe')[['departamento', 'concepto', 'descripcion', 'curso_escolar', 'mes', 'año', 'importe']]
df_top['importe'] = df_top['importe'].apply(lambda x: f'${x:,.0f}')
df_top.columns = ['Departamento', 'Concepto', 'Descripción', 'Curso', 'Mes', 'Año', 'Importe']

st.dataframe(df_top, use_container_width=True, hide_index=True)

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div class="footer">
    <p>© 2025 Colegio Peninsular Rogers Hall</p>
</div>
""", unsafe_allow_html=True)
