# ui/styling.py
import streamlit as st


def apply_dark_theme():
    """NUCLEAR VERSION - zničí všetky ružové farby v celej aplikácii"""
    
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* ═══ NUCLEAR OVERRIDE - VŠETKY MOŽNÉ SELEKTORY ═══ */
    
    /* ALL BUTTON SELECTORS - MAXIMUM COVERAGE */
    button, 
    .stButton > button,
    .stDownloadButton > button,
    .stForm > button,
    .stSidebar button,
    .stSidebar .stButton > button,
    div[role='button'],
    div[data-testid*='button'],
    div[data-baseweb='button'],
    .css-1x8cf1d,
    .css-1adrfps,
    .css-1vencpc,
    .css-19rxjzo,
    [data-testid="stButton"] > button,
    [data-testid="stDownloadButton"] > button {
        font-family: 'Inter', sans-serif !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        background-color: #262730 !important;
        color: #fafafa !important;
        border: 1px solid #4a4a4a !important;
    }
    
    /* NUCLEAR HOVER OVERRIDE - VŠETKY STAVY */
    button:hover, button:focus, button:active,
    button:hover *, button:focus *, button:active *,
    .stButton > button:hover, .stButton > button:focus, .stButton > button:active,
    .stDownloadButton > button:hover, .stDownloadButton > button:focus, .stDownloadButton > button:active,
    .stForm > button:hover, .stForm > button:focus, .stForm > button:active,
    .stSidebar button:hover, .stSidebar button:focus, .stSidebar button:active,
    .stSidebar .stButton > button:hover, .stSidebar .stButton > button:focus, .stSidebar .stButton > button:active,
    div[role='button']:hover, div[role='button']:focus, div[role='button']:active,
    div[data-testid*='button']:hover, div[data-testid*='button']:focus, div[data-testid*='button']:active,
    div[data-baseweb='button']:hover, div[data-baseweb='button']:focus, div[data-baseweb='button']:active,
    [data-testid="stButton"] > button:hover, [data-testid="stButton"] > button:focus, [data-testid="stButton"] > button:active,
    [data-testid="stDownloadButton"] > button:hover, [data-testid="stDownloadButton"] > button:focus, [data-testid="stDownloadButton"] > button:active {
        background-color: #2563eb !important;
        background-image: none !important;
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        border-color: #2563eb !important;
        color: white !important;
        box-shadow: 0 0 0 0.2rem rgba(37, 99, 235, 0.25) !important;
        outline: none !important;
        transform: translateY(-1px) !important;
    }
    
    /* PRIMARY BUTTON NUCLEAR OVERRIDE */
    .stButton > button[kind="primary"],
    .stSidebar .stButton > button[kind="primary"],
    button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        border-color: #1d4ed8 !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3) !important;
    }
    
    .stButton > button[kind="primary"]:hover,
    .stButton > button[kind="primary"]:focus,
    .stButton > button[kind="primary"]:active,
    .stSidebar .stButton > button[kind="primary"]:hover,
    .stSidebar .stButton > button[kind="primary"]:focus,
    .stSidebar .stButton > button[kind="primary"]:active,
    button[kind="primary"]:hover,
    button[kind="primary"]:focus,
    button[kind="primary"]:active {
        background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
        border-color: #1d4ed8 !important;
        color: white !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4) !important;
    }
    
    /* SECONDARY BUTTON NUCLEAR OVERRIDE */
    .stButton > button[kind="secondary"],
    .stSidebar .stButton > button[kind="secondary"],
    button[kind="secondary"] {
        background: linear-gradient(135deg, #6b7280, #4b5563) !important;
        border-color: #4b5563 !important;
        color: white !important;
    }
    
    .stButton > button[kind="secondary"]:hover,
    .stButton > button[kind="secondary"]:focus,
    .stButton > button[kind="secondary"]:active,
    .stSidebar .stButton > button[kind="secondary"]:hover,
    .stSidebar .stButton > button[kind="secondary"]:focus,
    .stSidebar .stButton > button[kind="secondary"]:active,
    button[kind="secondary"]:hover,
    button[kind="secondary"]:focus,
    button[kind="secondary"]:active {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        border-color: #2563eb !important;
        color: white !important;
    }
    
    /* ═══ SIDEBAR SPECIFIC NUCLEAR OVERRIDE ═══ */
    
    .stSidebar {
        background: linear-gradient(180deg, #1a202c 0%, #2d3748 100%) !important;
    }
    
    .stSidebar button,
    .stSidebar .stButton > button,
    .stSidebar div[role='button'] {
        width: 100% !important;
        height: 42px !important;
        background: rgba(255, 255, 255, 0.05) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        font-size: 0.9rem !important;
        margin-bottom: 8px !important;
        text-align: left !important;
    }
    
    /* SIDEBAR HOVER - ANTI-PINK NUCLEAR */
    .stSidebar button:hover,
    .stSidebar .stButton > button:hover,
    .stSidebar div[role='button']:hover,
    .stSidebar button:focus,
    .stSidebar .stButton > button:focus,
    .stSidebar div[role='button']:focus,
    .stSidebar button:active,
    .stSidebar .stButton > button:active,
    .stSidebar div[role='button']:active {
        background: rgba(37, 99, 235, 0.2) !important;
        border-color: #2563eb !important;
        color: white !important;
        box-shadow: 0 8px 25px rgba(37, 99, 235, 0.3) !important;
        outline: none !important;
        transform: translateY(-2px) scale(1.02) !important;
    }
    
    /* ═══ GLOBAL CSS VARIABLES OVERRIDE ═══ */
    :root {
        --primary-color: #2563eb !important;
        --primary-color-dark: #1d4ed8 !important;
        --secondary-color: #6b7280 !important;
        --background-color: #0e1117 !important;
        --secondary-background-color: #262730 !important;
        --text-color: #fafafa !important;
    }
    
    /* ═══ REMOVE FOCUS OUTLINES GLOBALLY ═══ */
    *:focus {
        outline: 2px solid #2563eb !important;
        outline-offset: 2px !important;
    }
    
    /* ═══ OVERRIDE ANY REMAINING PINK COLORS ═══ */
    * {
        --primary-color: #2563eb !important;
        --text-color: #fafafa !important;
    }
    
    /* ZÁKLADNÉ NASTAVENIA */
    .main {
        font-family: 'Inter', sans-serif;
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* OSTATNÉ KOMPONENTY */
    .profit-card {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        color: white;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
        margin-bottom: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .stMetric {
        background-color: #262730;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #4a4a4a;
    }
    
    hr {
        border-color: #4a4a4a;
        opacity: 0.3;
    }
    </style>
    """, unsafe_allow_html=True)


def get_dark_plotly_layout():
    """Vráti tmavé nastavenia pre Plotly grafy - OPRAVENÉ bez title konfliktu"""
    
    return {
        'plot_bgcolor': '#0e1117',
        'paper_bgcolor': '#0e1117',
        'font': {
            'color': '#fafafa',
            'family': 'Inter, sans-serif'
        },
        'legend': {
            'font': {
                'color': '#fafafa',
                'family': 'Inter, sans-serif'
            },
            'bgcolor': 'rgba(38, 39, 48, 0.8)',
            'bordercolor': '#4a4a4a',
            'borderwidth': 1
        },
        'xaxis': {
            'title': {
                'font': {'color': '#fafafa'}
            },
            'color': '#fafafa',
            'gridcolor': '#262730',
            'zerolinecolor': '#4a4a4a',
            'tickfont': {'color': '#fafafa'}
        },
        'yaxis': {
            'title': {
                'font': {'color': '#fafafa'}
            },
            'color': '#fafafa',
            'gridcolor': '#262730',
            'zerolinecolor': '#4a4a4a',
            'tickfont': {'color': '#fafafa'}
        }
    }

def get_dark_plotly_title_style():
    """Vráti styling pre title v plotly grafoch"""
    return {
        'font': {
            'color': '#fafafa',
            'size': 18,
            'family': 'Inter, sans-serif'
        }
    }


def get_metric_colors():
    """Vráti farby pre rôzne metriky"""
    
    return {
        'excellent': '#10b981',  # Zelená
        'good': '#3b82f6',       # Modrá
        'average': '#f59e0b',    # Oranžová
        'poor': '#ef4444'        # Červená
    }


def create_section_header(title, icon="📊"):
    """Vytvorí jednotný header pre sekcie"""
    st.markdown("---")
    st.markdown(f"### {icon} {title}")


def create_subsection_header(title, icon="📈"):
    """Vytvorí jednotný podheader pre podsekcie"""
    st.markdown(f"#### {icon} {title}")


def create_metric_card(activity, total_sales=None, is_critical=False, custom_color=None):
    """Vytvorí jednotnú kartu metriky v štýle employee.py"""
    
    # Použiť custom farbu alebo default logiku
    if custom_color:
        border_color = custom_color
    elif hasattr(activity, 'color'):
        border_color = activity['color']
    else:
        border_color = '#3b82f6'
    
    # Ak je kritická aktivita, použiť červenú
    if is_critical:
        border_color = '#ef4444'
    
    # Výpočet efektivity ak je k dispozícii total_sales
    if total_sales and hasattr(activity, 'sales_per_hour'):
        if activity['sales_per_hour'] > 500000:
            efficiency_status = "Výborná"
            efficiency_color = "#10b981"
        elif activity['sales_per_hour'] > 200000:
            efficiency_status = "Dobrá"
            efficiency_color = "#3b82f6"
        elif activity['sales_per_hour'] > 100000:
            efficiency_status = "Priemerná"
            efficiency_color = "#f59e0b"
        else:
            efficiency_status = "Nízka"
            efficiency_color = "#ef4444"
    else:
        efficiency_status = "N/A"
        efficiency_color = "#6b7280"
    
    # Získanie hodnôt
    name = getattr(activity, 'name', str(activity) if isinstance(activity, str) else 'Neznáma aktivita')
    activity_time = getattr(activity, 'activity_time', 0)
    sales_per_hour = getattr(activity, 'sales_per_hour', 0)
    risk_level = getattr(activity, 'risk_level', 'N/A')
    
    with st.container():
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(31, 41, 55, 0.9), rgba(55, 65, 81, 0.9));
            border-left: 4px solid {border_color};
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        ">
            <h5 style="color: {border_color}; margin: 0 0 10px 0; font-size: 1rem;">
                {name}
            </h5>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0;">
                <div>
                    <p style="color: #9ca3af; margin: 2px 0; font-size: 0.8rem;">Čas:</p>
                    <p style="color: white; margin: 2px 0; font-weight: bold;">{activity_time:.1f}h</p>
                </div>
                <div>
                    <p style="color: #9ca3af; margin: 2px 0; font-size: 0.8rem;">Efektivita:</p>
                    <p style="color: {efficiency_color}; margin: 2px 0; font-weight: bold;">{sales_per_hour:,.0f} Kč/h</p>
                </div>
            </div>
            <div style="margin-top: 8px;">
                <span style="
                    background: {efficiency_color}20; 
                    color: {efficiency_color}; 
                    padding: 2px 8px; 
                    border-radius: 12px; 
                    font-size: 0.75rem;
                    font-weight: bold;
                ">
                    {efficiency_status}
                </span>
                <span style="
                    background: rgba(107, 114, 128, 0.2); 
                    color: #9ca3af; 
                    padding: 2px 8px; 
                    border-radius: 12px; 
                    font-size: 0.75rem;
                    margin-left: 5px;
                ">
                    Riziko: {risk_level}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def create_simple_metric_card(title, value, description="", color="#3b82f6"):
    """Vytvorí jednoduchú kartu metriky"""
    
    with st.container():
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(31, 41, 55, 0.9), rgba(55, 65, 81, 0.9));
            border-left: 4px solid {color};
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        ">
            <h5 style="color: {color}; margin: 0 0 10px 0; font-size: 1rem;">
                {title}
            </h5>
            <p style="color: white; margin: 5px 0; font-weight: bold; font-size: 1.2rem;">
                {value}
            </p>
            {f'<p style="color: #9ca3af; margin: 2px 0; font-size: 0.8rem;">{description}</p>' if description else ''}
        </div>
        """, unsafe_allow_html=True)


def create_three_column_layout():
    """Vytvorí jednotný 3-stĺpcový layout"""
    col1, col2, col3 = st.columns(3)
    
    headers = {
        'col1': ('🟢 Produktívne aktivity', '#10b981'),
        'col2': ('🔵 Komunikačné aktivity', '#3b82f6'), 
        'col3': ('🔴 Kritické aktivity', '#ef4444')
    }
    
    return col1, col2, col3, headers
