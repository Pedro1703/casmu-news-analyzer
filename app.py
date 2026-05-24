#!/usr/bin/env python3
"""
Dashboard de Análisis de Noticias CASMU
Con autenticación y diseño moderno
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import hashlib
from datetime import datetime
from pathlib import Path

# ============================================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================================

st.set_page_config(
    page_title="CASMU | Análisis de Medios",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# SISTEMA DE AUTENTICACIÓN
# ============================================================================

def check_password():
    """Verifica la contraseña del usuario"""

    def password_entered():
        """Valida la contraseña ingresada"""
        if st.session_state["password"] == "1":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    # Primera ejecución o contraseña incorrecta
    if "password_correct" not in st.session_state:
        st.markdown("""
        <style>
            .stApp {
                background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
                min-height: 100vh;
            }
            .login-wrapper {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 2rem;
                margin-top: 3rem;
            }
            .login-card {
                max-width: 480px;
                width: 100%;
                background: linear-gradient(145deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 24px;
                padding: 3rem 2.5rem;
                text-align: center;
                box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
                backdrop-filter: blur(10px);
            }
            .login-icon {
                font-size: 4rem;
                margin-bottom: 1rem;
                display: block;
            }
            .login-title {
                font-size: 2.2rem;
                font-weight: 700;
                color: white;
                margin-bottom: 0.5rem;
                letter-spacing: -0.5px;
            }
            .login-brand {
                background: linear-gradient(90deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .login-subtitle {
                color: rgba(255,255,255,0.7);
                font-size: 1.1rem;
                margin-bottom: 2rem;
                line-height: 1.6;
            }
            .login-divider {
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                margin: 1.5rem 0;
            }
            .login-features {
                display: flex;
                flex-direction: column;
                gap: 0.8rem;
                margin-bottom: 2rem;
                text-align: left;
            }
            .login-feature {
                display: flex;
                align-items: center;
                gap: 0.8rem;
                color: rgba(255,255,255,0.8);
                font-size: 0.95rem;
            }
            .login-feature-icon {
                width: 32px;
                height: 32px;
                background: linear-gradient(135deg, rgba(102,126,234,0.2), rgba(118,75,162,0.2));
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1rem;
            }
            .login-footer {
                margin-top: 2rem;
                color: rgba(255,255,255,0.4);
                font-size: 0.85rem;
            }
        </style>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div class="login-wrapper">
                <div class="login-card">
                    <span class="login-icon">📊</span>
                    <h1 class="login-title">CASMU <span class="login-brand">Media Analyzer</span></h1>
                    <p class="login-subtitle">
                        Plataforma de inteligencia mediática para monitorear
                        la presencia de CASMU en medios uruguayos
                    </p>

                    <div class="login-divider"></div>

                    <div class="login-features">
                        <div class="login-feature">
                            <span class="login-feature-icon">🔍</span>
                            <span>Monitoreo de 5 medios uruguayos en tiempo real</span>
                        </div>
                        <div class="login-feature">
                            <span class="login-feature-icon">🧠</span>
                            <span>Análisis de sentimiento con NLP especializado</span>
                        </div>
                        <div class="login-feature">
                            <span class="login-feature-icon">📈</span>
                            <span>Datos históricos desde 2022 con tendencias</span>
                        </div>
                        <div class="login-feature">
                            <span class="login-feature-icon">📧</span>
                            <span>Reportes semanales automáticos por email</span>
                        </div>
                    </div>

                    <div class="login-divider"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.text_input(
                "Contraseña",
                type="password",
                on_change=password_entered,
                key="password",
                placeholder="Ingresa la contraseña"
            )

            if "password_correct" in st.session_state and not st.session_state["password_correct"]:
                st.error("❌ Contraseña incorrecta")

            st.markdown("""
            <p class="login-footer">
                Herramienta desarrollada para análisis interno de CASMU
            </p>
            """, unsafe_allow_html=True)

        return False

    elif not st.session_state["password_correct"]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input(
                "Contraseña",
                type="password",
                on_change=password_entered,
                key="password"
            )
            st.error("❌ Contraseña incorrecta")
        return False

    return True


# Verificar autenticación
if not check_password():
    st.stop()

# ============================================================================
# ESTILOS CSS PERSONALIZADOS
# ============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .stApp {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
    }

    .hero-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3);
    }

    .hero-title {
        font-size: 2.8rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }

    .hero-subtitle {
        font-size: 1.1rem;
        color: rgba(255,255,255,0.85);
        font-weight: 400;
    }

    .metric-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.2);
    }

    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .metric-label {
        font-size: 0.9rem;
        color: rgba(255,255,255,0.6);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 0.5rem;
    }

    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: white;
        margin: 2rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .section-divider {
        height: 1px;
        background: linear-gradient(90deg, rgba(102,126,234,0.5) 0%, transparent 100%);
        margin: 2rem 0;
    }

    .content-card {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .badge-positive {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .badge-negative {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .badge-neutral {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .info-box {
        background: rgba(102, 126, 234, 0.1);
        border-left: 4px solid #667eea;
        padding: 1rem 1.5rem;
        border-radius: 0 12px 12px 0;
        margin: 1rem 0;
    }

    .info-box p {
        color: rgba(255,255,255,0.8);
        margin: 0;
        font-size: 0.9rem;
    }

    .last-update {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 10px;
        padding: 0.5rem 1rem;
        color: #10b981;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 1rem;
    }

    .logout-btn {
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# BOTÓN DE LOGOUT
# ============================================================================

col_logout = st.columns([8, 1])
with col_logout[1]:
    if st.button("🚪 Salir"):
        st.session_state["password_correct"] = False
        st.rerun()

# ============================================================================
# CARGAR DATOS
# ============================================================================

@st.cache_data
def cargar_datos():
    """Carga los datos precargados"""
    data_path = Path(__file__).parent / "data" / "noticias_casmu.json"

    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        df['fecha'] = pd.to_datetime(df['fecha'])
        return df
    else:
        st.error("No se encontraron datos. Ejecuta collect_data.py primero.")
        return pd.DataFrame()


def get_last_update():
    """Obtiene la fecha de última actualización"""
    data_path = Path(__file__).parent / "data" / "noticias_casmu.json"
    if data_path.exists():
        import os
        timestamp = os.path.getmtime(data_path)
        return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M")
    return "Desconocida"


# Cargar datos
df = cargar_datos()

if df.empty:
    st.stop()

# ============================================================================
# HERO SECTION
# ============================================================================

st.markdown("""
<div class="hero-container">
    <div class="hero-title">📊 Análisis de Medios: CASMU</div>
    <div class="hero-subtitle">Monitoreo de menciones y sentimiento en medios uruguayos • 2022 - 2026</div>
</div>
""", unsafe_allow_html=True)

# Última actualización
st.markdown(f'<div class="last-update">🔄 Última actualización: {get_last_update()}</div>', unsafe_allow_html=True)

# ============================================================================
# MÉTRICAS PRINCIPALES
# ============================================================================

col1, col2, col3, col4 = st.columns(4)

total_noticias = len(df)
total_medios = df['medio'].nunique()
promedio_año = total_noticias / df['año'].nunique()
pct_negativo = len(df[df['sentimiento'] == 'NEGATIVO']) / total_noticias * 100

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total_noticias}</div>
        <div class="metric-label">Total Menciones</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{promedio_año:.0f}</div>
        <div class="metric-label">Promedio por Año</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total_medios}</div>
        <div class="metric-label">Medios Analizados</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{pct_negativo:.1f}%</div>
        <div class="metric-label">Cobertura Negativa</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# SECCIÓN 1: EVOLUCIÓN DE MENCIONES
# ============================================================================

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">📈 Evolución de Menciones en el Tiempo</div>', unsafe_allow_html=True)

df_por_año = df.groupby('año').size().reset_index(name='menciones')
df_por_año['promedio'] = df_por_año['menciones'].mean()

fig_menciones = go.Figure()

fig_menciones.add_trace(go.Bar(
    x=df_por_año['año'],
    y=df_por_año['menciones'],
    name='Menciones',
    marker=dict(
        color=df_por_año['menciones'],
        colorscale=[[0, '#667eea'], [1, '#764ba2']],
        line=dict(width=0)
    ),
    text=df_por_año['menciones'],
    textposition='outside',
    textfont=dict(size=14, color='white', family='Inter')
))

fig_menciones.add_trace(go.Scatter(
    x=df_por_año['año'],
    y=[promedio_año] * len(df_por_año),
    name=f'Promedio ({promedio_año:.0f})',
    line=dict(color='#f59e0b', width=2, dash='dash'),
    mode='lines'
))

fig_menciones.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter', color='white'),
    showlegend=True,
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.02,
        xanchor='right',
        x=1,
        font=dict(size=12)
    ),
    xaxis=dict(
        title='',
        tickfont=dict(size=14),
        gridcolor='rgba(255,255,255,0.05)',
        tickmode='array',
        tickvals=df_por_año['año'].tolist(),
        ticktext=[str(y) for y in df_por_año['año'].tolist()]
    ),
    yaxis=dict(
        title=dict(text='Cantidad de Menciones', font=dict(size=12)),
        tickfont=dict(size=12),
        gridcolor='rgba(255,255,255,0.05)',
        zeroline=False
    ),
    height=400,
    margin=dict(l=60, r=40, t=40, b=40),
    bargap=0.3
)

st.plotly_chart(fig_menciones, use_container_width=True)

st.markdown("""
<div class="info-box">
    <p>📌 <strong>Insight:</strong> Se observa un incremento significativo de menciones a partir de 2024,
    coincidiendo con la intervención de la mutualista y mayor cobertura mediática sobre su situación financiera.</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SECCIÓN 2: ANÁLISIS DE SENTIMIENTO
# ============================================================================

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">🎭 Análisis de Sentimiento</div>', unsafe_allow_html=True)

col_filtro1, col_filtro2, col_filtro3 = st.columns([2, 2, 2])

with col_filtro1:
    medios_opciones = ['Todos los medios'] + sorted(df['medio'].unique().tolist())
    medio_seleccionado = st.selectbox(
        '📺 Medio de comunicación',
        medios_opciones,
        key='filtro_medio'
    )

with col_filtro2:
    años_opciones = ['Todos los años'] + sorted(df['año'].unique().tolist(), reverse=True)
    año_seleccionado = st.selectbox(
        '📅 Año',
        años_opciones,
        key='filtro_año'
    )

with col_filtro3:
    sentimiento_opciones = ['Todos', 'POSITIVO', 'NEGATIVO', 'NEUTRO']
    sentimiento_seleccionado = st.selectbox(
        '🎯 Sentimiento',
        sentimiento_opciones,
        key='filtro_sentimiento'
    )

df_filtrado = df.copy()
if medio_seleccionado != 'Todos los medios':
    df_filtrado = df_filtrado[df_filtrado['medio'] == medio_seleccionado]
if año_seleccionado != 'Todos los años':
    df_filtrado = df_filtrado[df_filtrado['año'] == año_seleccionado]
if sentimiento_seleccionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['sentimiento'] == sentimiento_seleccionado]

st.markdown(f"<p style='color: rgba(255,255,255,0.6); font-size: 0.9rem;'>Mostrando {len(df_filtrado)} de {len(df)} noticias</p>", unsafe_allow_html=True)

col_sent1, col_sent2 = st.columns([1, 1])

with col_sent1:
    sent_counts = df_filtrado['sentimiento'].value_counts().reset_index()
    sent_counts.columns = ['sentimiento', 'cantidad']

    colors_map = {'POSITIVO': '#10b981', 'NEGATIVO': '#ef4444', 'NEUTRO': '#f59e0b'}

    fig_donut = go.Figure(data=[go.Pie(
        labels=sent_counts['sentimiento'],
        values=sent_counts['cantidad'],
        hole=0.65,
        marker=dict(colors=[colors_map.get(s, '#666') for s in sent_counts['sentimiento']]),
        textinfo='percent',
        textfont=dict(size=14, color='white', family='Inter'),
        hovertemplate='<b>%{label}</b><br>%{value} noticias<br>%{percent}<extra></extra>'
    )])

    fig_donut.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color='white'),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.1,
            xanchor='center',
            x=0.5,
            font=dict(size=11)
        ),
        height=350,
        margin=dict(l=20, r=20, t=30, b=50),
        annotations=[dict(
            text=f'<b>{len(df_filtrado)}</b><br>noticias',
            x=0.5, y=0.5,
            font=dict(size=18, color='white', family='Inter'),
            showarrow=False
        )]
    )

    st.plotly_chart(fig_donut, use_container_width=True)

with col_sent2:
    df_sent_año = df_filtrado.groupby(['año', 'sentimiento']).size().reset_index(name='cantidad')

    fig_stack = px.bar(
        df_sent_año,
        x='año',
        y='cantidad',
        color='sentimiento',
        color_discrete_map=colors_map,
        barmode='stack'
    )

    fig_stack.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color='white'),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.2,
            xanchor='center',
            x=0.5,
            font=dict(size=11),
            title=''
        ),
        xaxis=dict(
            title='',
            tickfont=dict(size=12),
            gridcolor='rgba(255,255,255,0.05)'
        ),
        yaxis=dict(
            title=dict(text='Cantidad', font=dict(size=11)),
            tickfont=dict(size=11),
            gridcolor='rgba(255,255,255,0.05)'
        ),
        height=350,
        margin=dict(l=50, r=20, t=30, b=60),
        bargap=0.3
    )

    st.plotly_chart(fig_stack, use_container_width=True)

# ============================================================================
# SECCIÓN 3: ANÁLISIS POR MEDIO
# ============================================================================

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">📺 Cobertura por Medio</div>', unsafe_allow_html=True)

df_medio = df_filtrado.groupby('medio').agg({
    'titulo': 'count',
    'sentimiento': lambda x: (x == 'NEGATIVO').sum() / len(x) * 100 if len(x) > 0 else 0
}).reset_index()
df_medio.columns = ['medio', 'total', 'pct_negativo']
df_medio = df_medio.sort_values('total', ascending=True)

fig_medio = go.Figure()

fig_medio.add_trace(go.Bar(
    y=df_medio['medio'],
    x=df_medio['total'],
    orientation='h',
    name='Total menciones',
    marker=dict(
        color=df_medio['pct_negativo'],
        colorscale=[[0, '#10b981'], [0.5, '#f59e0b'], [1, '#ef4444']],
        colorbar=dict(
            title=dict(text='% Negativo', font=dict(size=11, color='white')),
            tickfont=dict(size=10, color='white'),
            len=0.5,
            thickness=15
        )
    ),
    text=[f"{t} ({n:.0f}% neg)" for t, n in zip(df_medio['total'], df_medio['pct_negativo'])],
    textposition='outside',
    textfont=dict(size=11, color='white', family='Inter'),
    hovertemplate='<b>%{y}</b><br>%{x} menciones<br>%{marker.color:.1f}% negativas<extra></extra>'
))

fig_medio.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter', color='white'),
    showlegend=False,
    xaxis=dict(
        title=dict(text='Cantidad de menciones', font=dict(size=11)),
        tickfont=dict(size=11),
        gridcolor='rgba(255,255,255,0.05)'
    ),
    yaxis=dict(
        title='',
        tickfont=dict(size=12)
    ),
    height=300,
    margin=dict(l=130, r=100, t=20, b=50)
)

st.plotly_chart(fig_medio, use_container_width=True)

# ============================================================================
# SECCIÓN 4: LISTA DE NOTICIAS
# ============================================================================

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">📰 Noticias Recientes</div>', unsafe_allow_html=True)

df_display = df_filtrado.sort_values('fecha', ascending=False).head(20)

for _, row in df_display.iterrows():
    sent_class = {
        'POSITIVO': 'badge-positive',
        'NEGATIVO': 'badge-negative',
        'NEUTRO': 'badge-neutral'
    }.get(row['sentimiento'], 'badge-neutral')

    fecha_str = row['fecha'].strftime('%d %b %Y') if pd.notna(row['fecha']) else str(row['año'])

    st.markdown(f"""
    <div class="content-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem;">
            <div style="flex: 1;">
                <div style="color: rgba(255,255,255,0.5); font-size: 0.75rem; margin-bottom: 0.3rem;">
                    {row['medio']} • {fecha_str}
                </div>
                <div style="color: white; font-size: 0.95rem; line-height: 1.4;">
                    {row['titulo'][:120]}{'...' if len(row['titulo']) > 120 else ''}
                </div>
            </div>
            <div>
                <span class="{sent_class}">{row['sentimiento']}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Botón de descarga
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

csv = df_filtrado.to_csv(index=False).encode('utf-8')
col_dl1, col_dl2, col_dl3 = st.columns([1, 1, 1])
with col_dl2:
    st.download_button(
        label="📥 Descargar datos completos (CSV)",
        data=csv,
        file_name=f"casmu_analisis_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )

# ============================================================================
# FOOTER CON INFO DE NLP
# ============================================================================

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

with st.expander("ℹ️ Sobre el análisis de sentimiento (NLP)"):
    st.markdown("""
    ### Metodología de Análisis

    Este dashboard utiliza **Análisis Léxico Ponderado Fine-Tuned** para clasificar el sentimiento:

    | Componente | Descripción |
    |------------|-------------|
    | **Diccionario** | ~350 palabras en español con pesos específicos |
    | **Frases** | ~80 expresiones compuestas (ej: "riesgo asistencial") |
    | **Negadores** | Manejo de "sin", "no" (ej: "sin conflictos" = positivo) |
    | **Contexto** | Ajustado para salud, finanzas y relaciones laborales |

    ### Categorías de sentimiento

    - 🟢 **POSITIVO**: Nuevos servicios, alianzas, logros, mejoras
    - 🔴 **NEGATIVO**: Crisis, déficit, conflictos, denuncias, intervención
    - 🟡 **NEUTRO**: Información factual sin carga emocional clara

    ### Actualización

    Los datos se actualizan **semanalmente** de forma automática.
    """)

# Footer
st.markdown("""
<div style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.4); font-size: 0.8rem;">
    Dashboard de análisis de medios • Actualización semanal automática
</div>
""", unsafe_allow_html=True)
