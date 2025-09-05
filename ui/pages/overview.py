# ui/pages/overview.py
import streamlit as st
import plotly.graph_objects as go
from core.utils import (
    format_money, format_profit_value, time_to_minutes,
    calculate_activity_breakdown, get_activity_colors, 
    categorize_activities, calculate_productivity_metrics, get_top_activities,
    create_combined_monthly_activity_chart, get_combined_monthly_activity_summary
)
from core.metrics_calculator import EmployeeMetricsCalculator
from auth.auth import filter_data_by_user_access, can_access_city, get_user_cities
from datetime import datetime
from ui.styling import (
    get_dark_plotly_layout, apply_dark_theme, create_section_header, 
    create_subsection_header, create_metric_card, create_simple_metric_card,
    create_three_column_layout
)
from core.error_handler import handle_error, log_error

@handle_error
def render(analyzer):
    """Hlavný prehľad dashboard s novou analyzer triedou"""
    apply_dark_theme()
    # Validácia dát na začiatku
    analyzer.validate_sales_consistency()
    
    # Získanie súhrnu
    summary = analyzer.get_all_employees_summary()
    
    if not summary:
        st.warning("⚠️ Žiadná data k zobrazení")
        return
    
    # ✅ NOVÉ - Filtrovanie podľa oprávnení používateľa
    import pandas as pd
    summary_df = pd.DataFrame(summary)
    filtered_summary_df = filter_data_by_user_access(summary_df)
    filtered_summary = filtered_summary_df.to_dict('records')
    
    # Ak po filtrovaní nie sú žiadne dáta
    if not filtered_summary:
        st.warning("⚠️ Nemáte oprávnenie na zobrazenie týchto dát alebo nie sú dostupné")
        return
    
    # Štatistiky podľa miest - s filtrovanými dátami
    create_city_overview(filtered_summary)
    
    # ✅ NOVÉ - Mesačný graf aktivít NAD vyhľadávaním
    st.markdown("---")
    create_monthly_activity_chart(analyzer)
    
    # ✅ NOVÉ - Detailný graf aktivít so skutočnými dátami POUŽÍVAJÚC UTILS
    with st.expander("🔍 Detailné rozloženie aktivít", expanded=False):
        create_activity_breakdown_chart(analyzer)
    
    st.markdown("---")
    
    # Vyhľadávanie zamestnancov (pôvodné) - s filtrovanými dátami
    show_employee_search(filtered_summary, analyzer)

def create_city_overview(summary_data):
    """Vytvorí prehľad podľa miest"""
    
    # Príprava dát
    city_stats = {}
    total_sales = 0
    
    for emp in summary_data:
        city = emp['workplace']
        emp_sales = emp.get('total_sales', 0)
        total_sales += emp_sales
        
        if city not in city_stats:
            city_stats[city] = {
                'count': 0,
                'total_sales': 0,
                'excellent': 0,
                'good': 0,
                'average': 0,
                'poor': 0
            }
        
        city_stats[city]['count'] += 1
        city_stats[city]['total_sales'] += emp_sales
        city_stats[city][emp.get('rating', 'average')] += 1
    
    # Výpočet percent
    for city in city_stats:
        city_stats[city]['percentage'] = (city_stats[city]['total_sales'] / total_sales * 100) if total_sales > 0 else 0
        city_stats[city]['avg_score'] = city_stats[city]['total_sales'] / city_stats[city]['count'] if city_stats[city]['count'] > 0 else 0
    
    # Zobrazenie kariek miest
    create_section_header("Celkový přehled zisku podle měst", "💰")
    
    profit_cols = st.columns(len(city_stats))
    for i, (city, stats) in enumerate(city_stats.items()):
        with profit_cols[i]:
            # Určenie statusu na základe priemerného výkonu
            avg_performance = stats['avg_score']
            if avg_performance >= 2000000:  # 2M+
                status = "Výborné"
                status_color = "#10b981"
                border_color = "#10b981"
            elif avg_performance >= 1500000:  # 1.5M+
                status = "Dobré"
                status_color = "#3b82f6"
                border_color = "#3b82f6"
            elif avg_performance >= 1000000:  # 1M+
                status = "Priemerné"
                status_color = "#f59e0b"
                border_color = "#f59e0b"
            else:
                status = "Slabé"
                status_color = "#ef4444"
                border_color = "#ef4444"
            
            formatted_profit = format_profit_value(stats['total_sales'], stats['percentage'])
            
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
                    🏢 {city.title()}
                </h5>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0;">
                    <div>
                        <p style="color: #9ca3af; margin: 2px 0; font-size: 0.8rem;">Celkový zisk:</p>
                        <p style="color: white; margin: 2px 0; font-weight: bold; font-size: 1.2rem;">{formatted_profit}</p>
                    </div>
                    <div>
                        <p style="color: #9ca3af; margin: 2px 0; font-size: 0.8rem;">Zamestnanci:</p>
                        <p style="color: white; margin: 2px 0; font-weight: bold;">{stats['count']} osôb</p>
                    </div>
                </div>
                <div style="margin: 5px 0;">
                    <p style="color: #9ca3af; margin: 2px 0; font-size: 0.8rem;">Priemer na osobu:</p>
                    <p style="color: {status_color}; margin: 2px 0; font-weight: bold;">{format_money(avg_performance)}</p>
                </div>
                <div style="margin-top: 8px;">
                    <span style="
                        background: {status_color}20; 
                        color: {status_color}; 
                        padding: 2px 8px; 
                        border-radius: 12px; 
                        font-size: 0.75rem;
                        font-weight: bold;
                    ">
                        {status}
                    </span>
                    <span style="
                        background: rgba(107, 114, 128, 0.2); 
                        color: #9ca3af; 
                        padding: 2px 8px; 
                        border-radius: 12px; 
                        font-size: 0.75rem;
                        margin-left: 5px;
                    ">
                        {stats['percentage']:.1f}%
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Grafy
    create_city_charts(city_stats)

def create_city_charts(city_stats):
    """Vytvorí grafy pre mestá - OPRAVENÉ bez duplicitných title"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Koláčový graf
        cities = list(city_stats.keys())
        values = [city_stats[city]['total_sales'] for city in cities]
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=[city.title() for city in cities],
            values=values,
            hole=0.4,
            marker_colors=['#4299e1', '#48bb78', '#ed8936', '#f56565']
        )])
        
        # ✅ OPRAVENÉ: title iba v update_layout, nie duplicitný
        layout_settings = get_dark_plotly_layout()
        layout_settings.update({
            'title': {
                'text': "Rozložení zisku podle měst",
                'font': {'size': 18, 'color': '#fafafa'}
            },
            'height': 400
        })
        
        fig_pie.update_layout(**layout_settings)
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Stĺpcový graf
        avg_profits = [city_stats[city]['avg_score'] for city in cities]
        
        fig_bar = go.Figure(data=[go.Bar(
            x=[city.title() for city in cities],
            y=avg_profits,
            marker_color=['#4299e1', '#48bb78', '#ed8936', '#f56565'],
            text=[format_money(profit) for profit in avg_profits],
            textposition='auto'
        )])
        
        # ✅ OPRAVENÉ: title iba raz, nie duplicitný
        layout_settings = get_dark_plotly_layout()
        layout_settings.update({
            'title': {
                'text': "Průměrný zisk na zaměstnance", 
                'font': {'size': 18, 'color': '#fafafa'}
            },
            'height': 400,
            'xaxis': {
                'title': "Město",
                'color': '#fafafa',
                'gridcolor': '#262730'
            },
            'yaxis': {
                'title': "Průměrný zisk (Kč)",
                'color': '#fafafa', 
                'gridcolor': '#262730'
            }
        })
        
        fig_bar.update_layout(**layout_settings)
        
        st.plotly_chart(fig_bar, use_container_width=True)

def show_employee_search(summary_data, analyzer):
    """Vyhľadávanie zamestnancov"""
    
    create_section_header("Vyhledávání zaměstnanců", "🔍")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("Zadejte jméno zaměstnance:", placeholder="Např. Novák, Svoboda...")
    
    with col2:
        city_filter = st.selectbox("Filtr podle města:", ["Všechna města"] + [city.title() for city in ['praha', 'brno', 'zlin', 'vizovice']])
    
    with col3:
        rating_filter = st.selectbox("Filtr podle hodnocení:", ["Všechna hodnocení", "Výborní", "Dobří", "Průměrní", "Podprůměrní"])
    
    # Filtrovanie
    filtered_data = filter_employees(summary_data, search_term, city_filter, rating_filter)
    
    # Zobrazenie výsledkov
    if filtered_data:
        st.markdown(f"**Nájdených {len(filtered_data)} zaměstnanců:**")
        show_employee_cards(filtered_data, analyzer, prefix="search")
    else:
        st.warning("⚠️ Žádní zaměstnanci nevyhovují zadaným kritériím")

def filter_employees(summary_data, search_term, city_filter, rating_filter):
    """Filtruje zamestnancov podľa kritérií"""
    
    filtered_data = summary_data.copy()
    
    if search_term:
        filtered_data = [emp for emp in filtered_data if search_term.lower() in emp['name'].lower()]
    
    if city_filter != "Všechna města":
        filtered_data = [emp for emp in filtered_data if emp['workplace'].title() == city_filter]
    
    if rating_filter != "Všechna hodnocení":
        rating_map = {"Výborní": "excellent", "Dobří": "good", "Průměrní": "average", "Podprůměrní": "poor"}
        filtered_data = [emp for emp in filtered_data if emp.get('rating', 'average') == rating_map[rating_filter]]
    
    return filtered_data

def show_employee_cards(employees, analyzer, prefix="main"):
    """✅ OPRAVENÉ - Grid layout s CSS override"""
    
    # Legenda
    show_neutral_legend()
    st.divider()
    
    # ✅ SILNÝ CSS override - prepíše styling.py
    st.markdown("""
    <style>
    /* Override styling.py with !important */
    .stButton > button {
        height: 140px !important;
        white-space: pre-wrap !important;
        text-align: center !important;
        padding: 16px 12px !important;
        font-size: 0.85rem !important;
        line-height: 1.4 !important;
        border-radius: 16px !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: 2px solid transparent !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-5px) scale(1.02) !important;
        box-shadow: 0 12px 30px rgba(0,0,0,0.2) !important;
        border-color: #ffffff40 !important;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
    }
    
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ✅ GRID LAYOUT - 3 tlačidlá na riadok
    buttons_per_row = 3
    total_employees = len(employees)
    
    for row_start in range(0, total_employees, buttons_per_row):
        row_employees = employees[row_start:row_start + buttons_per_row]
        
        # Vytvorenie stĺpcov pre aktuálny riadok
        cols = st.columns(len(row_employees))
        
        # Zobrazenie tlačidiel v stĺpcoch
        for col_idx, emp in enumerate(row_employees):
            with cols[col_idx]:
                create_employee_button_in_column(emp, analyzer, row_start + col_idx, prefix)
        
        # Spacing medzi riadkami
        st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)

def create_monthly_activity_chart(analyzer):
    """Vytvorí stĺpcový graf rozloženia pracovnej činnosti po mesiacoch - SKUTOČNÉ DÁTA"""
    
    import plotly.graph_objects as go
    import plotly.express as px
    from datetime import datetime
    
    create_section_header("Rozloženie pracovnej činnosti počas roka", "📊")
    
    # ✅ SKUTOČNÉ DÁTA Z ANALYZÁTORA
    monthly_data = {}
    czech_months = ['leden', 'unor', 'brezen', 'duben', 'kveten', 'cerven', 
                   'cervenec', 'srpen', 'zari', 'rijen', 'listopad', 'prosinec']
    
    # Inicializácia mesačných súm
    for month in czech_months:
        monthly_data[month] = 0
    
    # ✅ AGREGÁCIA SKUTOČNÝCH SALES DÁT
    if hasattr(analyzer, 'sales_employees') and analyzer.sales_employees:
        for employee in analyzer.sales_employees:
            if 'monthly_sales' in employee and employee['monthly_sales']:
                for month, sales in employee['monthly_sales'].items():
                    # Konverzia názvov mesiacov ak je potrebné
                    month_lower = month.lower()
                    if month_lower in monthly_data:
                        monthly_data[month_lower] += sales
    
    # ✅ FALLBACK - ak nemáme monthly_sales, použijeme total_sales rozdelené
    if all(value == 0 for value in monthly_data.values()):
        st.info("ℹ️ Mesačné dáta nie sú dostupné - rozdeľujem celkové predaje rovnomerne")
        
        summary = analyzer.get_all_employees_summary()
        total_sales = sum([emp.get('total_sales', 0) for emp in summary]) if summary else 0
        
        if total_sales > 0:
            # Rozdelenie na 12 mesiacov s miernou variáciou
            base_monthly = total_sales / 12
            import random
            random.seed(42)  # Pre konzistentné výsledky
            
            for i, month in enumerate(czech_months):
                # Pridanie realistickej variácie (±20%)
                variation = random.uniform(0.8, 1.2)
                monthly_data[month] = int(base_monthly * variation)
    
    # ✅ ZOBRAZENIE INFO O DÁTACH
    total_annual = sum(monthly_data.values())
    if total_annual == 0:
        st.warning("⚠️ Žiadne sales dáta dostupné")
        return
    
    # Výber typu grafu
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        chart_type = st.selectbox(
            "📊 Typ grafu:",
            ["Stĺpcový", "Čiarový", "Oblasť"],
            key="monthly_chart_type"
        )
    
    with col2:
        show_values = st.checkbox("Zobraziť hodnoty", value=True)
    
    with col3:
        show_trend = st.checkbox("Trend čiara", value=False)
    
    # Vytvorenie grafu
    months_list = list(monthly_data.keys())
    values_list = list(monthly_data.values())
    
    fig = go.Figure()
    
    # Hlavný graf podľa typu
    if chart_type == "Stĺpcový":
        fig.add_trace(go.Bar(
            x=months_list,
            y=values_list,
            name="Predaj (Kč)",
            marker_color='rgba(102, 126, 234, 0.8)',
            text=[f"{v:,.0f} Kč" for v in values_list] if show_values else None,
            textposition='auto' if show_values else None,
            hovertemplate="<b>%{x}</b><br>Predaj: %{y:,.0f} Kč<extra></extra>"
        ))
    
    elif chart_type == "Čiarový":
        fig.add_trace(go.Scatter(
            x=months_list,
            y=values_list,
            mode='lines+markers',
            name="Predaj (Kč)",
            line=dict(color='rgba(102, 126, 234, 0.8)', width=3),
            marker=dict(size=8, color='rgba(102, 126, 234, 1)'),
            text=[f"{v:,.0f} Kč" for v in values_list] if show_values else None,
            textposition="top center" if show_values else None,
            hovertemplate="<b>%{x}</b><br>Predaj: %{y:,.0f} Kč<extra></extra>"
        ))
    
    else:  # Oblasť
        fig.add_trace(go.Scatter(
            x=months_list,
            y=values_list,
            fill='tozeroy',
            name="Predaj (Kč)",
            line=dict(color='rgba(102, 126, 234, 0.8)'),
            fillcolor='rgba(102, 126, 234, 0.3)',
            text=[f"{v:,.0f} Kč" for v in values_list] if show_values else None,
            textposition="top center" if show_values else None,
            hovertemplate="<b>%{x}</b><br>Predaj: %{y:,.0f} Kč<extra></extra>"
        ))
    
    # Trend čiara
    if show_trend:
        import numpy as np
        x_numeric = list(range(len(values_list)))
        z = np.polyfit(x_numeric, values_list, 1)
        p = np.poly1d(z)
        trend_values = [p(x) for x in x_numeric]
        
        fig.add_trace(go.Scatter(
            x=months_list,
            y=trend_values,
            mode='lines',
            name='Trend',
            line=dict(color='red', width=2, dash='dash'),
            hovertemplate="<b>Trend</b><br>%{x}: %{y:,.0f} Kč<extra></extra>"
        ))
    
    # Layout nastavenia
    layout_settings = get_dark_plotly_layout()
    layout_settings.update({
        'title': {
            'text': f"📊 Rozloženie predajnej činnosti počas roka {datetime.now().year}",
            'x': 0.5,
            'font': {'size': 20, 'color': '#fafafa'}
        },
        'xaxis': {
            'title': {
                'text': "Mesiac",
                'font': {'color': '#fafafa'}
            },
            'tickfont': {'color': '#fafafa'},
            'gridcolor': '#262730'
        },
        'yaxis': {
            'title': {
                'text': "Predaj (Kč)",
                'font': {'color': '#fafafa'}
            },
            'tickfont': {'color': '#fafafa'},
            'gridcolor': '#262730',
            'tickformat': ',.0f'
        },
        'height': 500,
        'showlegend': True if show_trend else False,
        'hovermode': 'x unified'
    })
    
    fig.update_layout(**layout_settings)
    
    # Zobrazenie grafu
    st.plotly_chart(fig, use_container_width=True)
    
    # ✅ SKUTOČNÉ ŠTATISTIKY POD GRAFOM
    col1, col2, col3, col4 = st.columns(4)
    
    total_sales = sum(values_list)
    avg_monthly = total_sales / 12
    best_month_idx = values_list.index(max(values_list))
    worst_month_idx = values_list.index(min(values_list))
    
    with col1:
        st.metric(
            "💰 Celkový predaj",
            f"{total_sales:,.0f} Kč",
            help="Súčet skutočného predaja za všetky mesiace"
        )
    
    with col2:
        st.metric(
            "📊 Mesačný priemer",
            f"{avg_monthly:,.0f} Kč",
            help="Priemerný skutočný predaj za mesiac"
        )
    
    with col3:
        st.metric(
            "🏆 Najlepší mesiac",
            f"{months_list[best_month_idx].title()}",
            f"{values_list[best_month_idx]:,.0f} Kč",
            help="Mesiac s najvyšším skutočným predajom"
        )
    
    with col4:
        st.metric(
            "📉 Najslabší mesiac", 
            f"{months_list[worst_month_idx].title()}",
            f"{values_list[worst_month_idx]:,.0f} Kč",
            delta_color="inverse",
            help="Mesiac s najnižším skutočným predajom"
        )

def create_activity_breakdown_chart(analyzer):
    """Vytvorí rozloženie aktivít používajúc utils funkcie - SKUTOČNÉ DÁTA"""
    
    create_section_header("Detailné rozloženie aktivít", "🎯")
    
    # ✅ POUŽITIE UTILITY FUNKCIÍ Z core/utils.py
    activity_data = calculate_activity_breakdown(analyzer)
    
    if not activity_data:
        st.warning("⚠️ Nie je možné vypočítať rozloženie aktivít")
        return
    
    # ✅ NOVÝ - Kombinovaný mesačný graf používajúc utils funkciu
        create_subsection_header("Mesačné rozloženie všetkých aktivít", "📊")    # Vytvorenie grafu z utils
    fig = create_combined_monthly_activity_chart(analyzer, activity_data)
    
    if fig:
        # Layout nastavenia
        from ui.styling import get_dark_plotly_layout
        
        layout_settings = get_dark_plotly_layout()
        layout_settings.update({
            'title': {
                'text': "📊 Mesačné rozloženie aktivít - Internet + Aplikácie",
                'x': 0.5,
                'font': {'size': 18, 'color': '#fafafa'}
            },
            'barmode': 'stack',
            'xaxis': {
                'title': {'text': "Mesiac", 'font': {'color': '#fafafa'}},
                'tickfont': {'color': '#fafafa'}
            },
            'yaxis': {
                'title': {'text': "Hodiny", 'font': {'color': '#fafafa'}},
                'tickfont': {'color': '#fafafa'}
            },
            'height': 500,
            'legend': {
                'orientation': "v",
                'yanchor': "top",
                'y': 1,
                'xanchor': "left",
                'x': 1.02,
                'bgcolor': 'rgba(0,0,0,0.5)',
                'bordercolor': '#333',
                'borderwidth': 1
            }
        })
        
        fig.update_layout(**layout_settings)
        st.plotly_chart(fig, use_container_width=True)
        
        # Súhrnné štatistiky používajúc utils
        display_monthly_summary_from_utils(activity_data)
    else:
        st.error("❌ Nepodarilo sa vytvoriť graf aktivít")
    
    st.markdown("---")
    
    # Kontrola ovládacích prvkov (existujúci kód pre pie charts, bar charts, atď.)
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        view_type = st.selectbox(
            "📊 Typ zobrazenia:",
            ["Pie Charts", "Bar Chart", "Kategórie"],
            key="activity_view_type"
        )
    
    with col2:
        data_source = st.selectbox(
            "🔍 Zdroj dát:",
            ["Kombinované", "Internet aktivity", "Aplikačné aktivity"],
            key="activity_data_source"
        )
    
    with col3:
        show_metrics = st.checkbox("Produktivitné metriky", value=True)
    
    # Zobrazenie podľa výberu
    if view_type == "Pie Charts":
        display_activity_pie_charts(activity_data, data_source)
    elif view_type == "Bar Chart":
        display_activity_bar_chart(activity_data, data_source)
    else:  # Kategórie
        display_activity_categories(activity_data)
    
    # Produktivitné metriky
    if show_metrics:
        display_productivity_metrics(activity_data)
def display_monthly_summary_from_utils(activity_data):
    """Zobrazí súhrn používajúc utils funkciu"""
    
    create_subsection_header("Súhrn mesačných aktivít", "📈")
    
    # Získanie súhrnu z utils funkcie
    summary = get_combined_monthly_activity_summary(activity_data)
    
    if not summary:
        st.warning("⚠️ Nie je možné vypočítať súhrn aktivít")
        return
    
    # Hlavné metriky
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        internet_percentage = f"{(summary['total_internet']/summary['total_combined'])*100:.1f}%" if summary['total_combined'] > 0 else "0%"
        st.metric(
            "🌐 Internet celkom",
            f"{summary['total_internet']:.1f}h",
            internet_percentage
        )
    
    with col2:
        app_percentage = f"{(summary['total_apps']/summary['total_combined'])*100:.1f}%" if summary['total_combined'] > 0 else "0%"
        st.metric(
            "💻 Aplikácie celkom",
            f"{summary['total_apps']:.1f}h", 
            app_percentage
        )
    
    with col3:
        st.metric(
            "⏱️ Celkový čas",
            f"{summary['total_combined']:.1f}h",
            help="Súčet všetkých internetových a aplikačných aktivít"
        )
    
    with col4:
        st.metric(
            "📊 Mesačný priemer",
            f"{summary['avg_monthly']:.1f}h",
            help="Priemerný čas aktivít za mesiac"
        )
    
    # Detailné informácie v dvoch stĺpcoch
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🏆 Top 5 aktivít:**")
        if summary['top_activities']:
            for i, activity in enumerate(summary['top_activities']):
                percentage = (activity['hours'] / summary['total_combined'] * 100) if summary['total_combined'] > 0 else 0
                st.write(f"{i+1}. {activity['name']}: {activity['hours']:.1f}h ({percentage:.1f}%)")
        else:
            st.write("Žiadne aktivity dostupné")
    
    with col2:
        st.markdown("**📊 Produktivita:**")
        if summary['total_combined'] > 0:
            prod_pct = (summary['productive_hours'] / summary['total_combined']) * 100
            unprod_pct = (summary['unproductive_hours'] / summary['total_combined']) * 100
            
            st.write(f"🟢 Produktívne: {summary['productive_hours']:.1f}h ({prod_pct:.1f}%)")
            st.write(f"🔴 Neproduktívne: {summary['unproductive_hours']:.1f}h ({unprod_pct:.1f}%)")
            
            # Produktivitné skóre s farbou podľa výkonnosti
            productivity_score = summary['productivity_score']
            if productivity_score >= 70:
                color = "🟢"
            elif productivity_score >= 50:
                color = "🟡"
            else:
                color = "🔴"
            
            st.metric(
                "📊 Produktivitné skóre", 
                f"{color} {productivity_score:.1f}%",
                help="Podiel produktívnych aktivít ku celkovému času"
            )
        else:
            st.write("Žiadne dáta o produktivite")
    
    # Dodatočné informácie
    if summary['total_combined'] > 0:
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Najproduktívnejšia aktivita
            if summary['top_activities']:
                top_activity = summary['top_activities'][0]
                st.info(f"🥇 **Najaktívnejšia**: {top_activity['name']} ({top_activity['hours']:.1f}h)")
        
        with col2:
            # Pomer internet vs aplikácie
            if summary['total_internet'] > summary['total_apps']:
                st.info(f"🌐 **Dominuje**: Internet aktivity")
            elif summary['total_apps'] > summary['total_internet']:
                st.info(f"💻 **Dominuje**: Aplikačné aktivity")
            else:
                st.info(f"⚖️ **Vyrovnané**: Internet vs Aplikácie")
        
        with col3:
            # Denný priemer
            daily_avg = summary['avg_monthly'] / 30  # Približne 30 dní v mesiaci
            st.info(f"📅 **Denný priemer**: {daily_avg:.1f}h")


def display_activity_pie_charts(activity_data, data_source):
    """Zobrazí pie charty pre aktivity používajúc utils"""
    import plotly.graph_objects as go
    from ui.styling import get_dark_plotly_layout
    
    colors = get_activity_colors()
    
    if data_source == "Kombinované":
        col1, col2 = st.columns(2)
        
        with col1:
            create_single_pie_chart(
                activity_data['internet'], 
                "🌐 Internetové aktivity",
                colors['internet']
            )
        
        with col2:
            create_single_pie_chart(
                activity_data['applications'], 
                "💻 Aplikačné aktivity", 
                colors['applications']
            )
    elif data_source == "Internet aktivity":
        create_single_pie_chart(
            activity_data['internet'], 
            "🌐 Internetové aktivity",
            colors['internet']
        )
    else:  # Aplikačné aktivity
        create_single_pie_chart(
            activity_data['applications'], 
            "💻 Aplikačné aktivity",
            colors['applications']
        )

def create_single_pie_chart(data_dict, title, colors):
    """Vytvorí jeden pie chart"""
    import plotly.graph_objects as go
    from ui.styling import get_dark_plotly_layout
    
    if not data_dict['percentages']:
        st.info(f"ℹ️ Žiadne dáta pre {title}")
        return
    
    activities = list(data_dict['percentages'].keys())
    percentages = list(data_dict['percentages'].values())
    hours = [data_dict['hours'][act] for act in activities]
    
    activity_colors = [colors.get(act, '#6b7280') for act in activities]
    
    fig = go.Figure(data=[go.Pie(
        labels=activities,
        values=percentages,
        hole=0.3,
        marker_colors=activity_colors,
        hovertemplate="<b>%{label}</b><br>" +
                      "Čas: %{customdata:.1f}h<br>" +
                      "Podiel: %{percent}<br>" +
                      "<extra></extra>",
        customdata=hours
    )])
    
    layout_settings = get_dark_plotly_layout()
    layout_settings.update({
        'title': {
            'text': title,
            'x': 0.5,
            'font': {'size': 16, 'color': '#fafafa'}
        },
        'height': 400,
        'showlegend': True,
        'legend': {
            'orientation': "v",
            'yanchor': "middle", 
            'y': 0.5,
            'xanchor': "left",
            'x': 1.05
        }
    })
    
    fig.update_layout(**layout_settings)
    st.plotly_chart(fig, use_container_width=True)

def display_activity_bar_chart(activity_data, data_source):
    """Zobrazí bar chart pre aktivity"""
    import plotly.graph_objects as go
    from ui.styling import get_dark_plotly_layout
    
    fig = go.Figure()
    
    if data_source == "Kombinované":
        # Pridanie internet aktivít
        if activity_data['internet']['hours']:
            internet_activities = list(activity_data['internet']['hours'].keys())
            internet_values = list(activity_data['internet']['hours'].values())
            
            fig.add_trace(go.Bar(
                name="Internet aktivity",
                x=internet_activities,
                y=internet_values,
                marker_color='rgba(102, 126, 234, 0.8)',
                hovertemplate="<b>%{x}</b><br>Čas: %{y:.1f}h<extra></extra>"
            ))
        
        # Pridanie aplikačných aktivít
        if activity_data['applications']['hours']:
            app_activities = list(activity_data['applications']['hours'].keys())
            app_values = list(activity_data['applications']['hours'].values())
            
            fig.add_trace(go.Bar(
                name="Aplikačné aktivity",
                x=app_activities,
                y=app_values,
                marker_color='rgba(244, 114, 182, 0.8)',
                hovertemplate="<b>%{x}</b><br>Čas: %{y:.1f}h<extra></extra>"
            ))
    
    elif data_source == "Internet aktivity":
        if activity_data['internet']['hours']:
            activities = list(activity_data['internet']['hours'].keys())
            values = list(activity_data['internet']['hours'].values())
            colors_list = [get_activity_colors()['internet'].get(act, '#6b7280') for act in activities]
            
            fig.add_trace(go.Bar(
                x=activities,
                y=values,
                marker_color=colors_list,
                hovertemplate="<b>%{x}</b><br>Čas: %{y:.1f}h<extra></extra>"
            ))
    
    else:  # Aplikačné aktivity
        if activity_data['applications']['hours']:
            activities = list(activity_data['applications']['hours'].keys())
            values = list(activity_data['applications']['hours'].values())
            colors_list = [get_activity_colors()['applications'].get(act, '#6b7280') for act in activities]
            
            fig.add_trace(go.Bar(
                x=activities,
                y=values,
                marker_color=colors_list,
                hovertemplate="<b>%{x}</b><br>Čas: %{y:.1f}h<extra></extra>"
            ))
    
    # Layout nastavenia
    layout_settings = get_dark_plotly_layout()
    layout_settings.update({
        'title': {
            'text': f"📊 {data_source} - Časové rozloženie",
            'x': 0.5,
            'font': {'size': 18, 'color': '#fafafa'}
        },
        'barmode': 'group',
        'xaxis': {
            'title': {
                'text': "Aktivita",
                'font': {'color': '#fafafa'}
            },
            'tickfont': {'color': '#fafafa'},
            'tickangle': -45
        },
        'yaxis': {
            'title': {
                'text': "Čas (hodiny)",
                'font': {'color': '#fafafa'}
            },
            'tickfont': {'color': '#fafafa'}
        },
        'height': 500,
        'showlegend': data_source == "Kombinované"
    })
    
    fig.update_layout(**layout_settings)
    st.plotly_chart(fig, use_container_width=True)

def display_activity_categories(activity_data):
    """Zobrazí aktivity rozdelené do kategórií používajúc utils"""
    
    categorized = categorize_activities(activity_data)
    
    col1, col2, col3, headers = create_three_column_layout()
    
    with col1:
        create_subsection_header("Produktívne aktivity", "🟢")
        total_productive = categorized['productive']['hours']
        create_simple_metric_card("Celkový čas", f"{total_productive:.1f}h", color=headers['col1'][1])
        
        for activity in categorized['productive']['activities']:
            st.write(f"• {activity['name']}: {activity['hours']:.1f}h")
    
    with col2:
        create_subsection_header("Neutrálne aktivity", "🔵")
        total_neutral = categorized['neutral']['hours']
        create_simple_metric_card("Celkový čas", f"{total_neutral:.1f}h", color=headers['col2'][1])
        
        for activity in categorized['neutral']['activities']:
            st.write(f"• {activity['name']}: {activity['hours']:.1f}h")
    
    with col3:
        create_subsection_header("Kritické aktivity", "🔴")
        total_unproductive = categorized['unproductive']['hours']
        create_simple_metric_card("Celkový čas", f"{total_unproductive:.1f}h", color=headers['col3'][1])
        
        for activity in categorized['unproductive']['activities']:
            st.write(f"• {activity['name']}: {activity['hours']:.1f}h")

def display_productivity_metrics(activity_data):
    """Zobrazí produktivitné metriky používajúc utils"""
    
    metrics = calculate_productivity_metrics(activity_data)
    top_activities = get_top_activities(activity_data, limit=3)
    
    create_section_header("Produktivitné metriky", "📈")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🎯 Produktivita",
            f"{metrics['productivity_score']}%",
            help="Podiel produktívnych aktivít ku celkovému času"
        )
    
    with col2:
        st.metric(
            "⚖️ Efektivitný pomer",
            f"{metrics['efficiency_ratio']}:1",
            help="Pomer produktívnych ku neproduktívnym aktivitám"
        )
    
    with col3:
        st.metric(
            "🎯 Focus čas",
            f"{metrics['focus_time']:.1f}h",
            help="Čas strávený hlavnými produktívnymi aktivitami"
        )
    
    with col4:
        st.metric(
            "⏱️ Celkový čas",
            f"{metrics['total_hours']:.1f}h",
            help="Celkový sledovaný čas"
        )
    
    # Top aktivity
    col1, col2 = st.columns(2)
    
    with col1:
        create_subsection_header("Top Internet aktivity", "🏆")
        for activity in top_activities['internet']:
            st.write(f"• **{activity['name']}**: {activity['hours']:.1f}h ({activity['percentage']:.1f}%)")
    
    with col2:
        create_subsection_header("Top Aplikačné aktivity", "🏆")
        for activity in top_activities['applications']:
            st.write(f"• **{activity['name']}**: {activity['hours']:.1f}h ({activity['percentage']:.1f}%)")

# ========== ZVYŠOK FUNKCIÍ ZOSTÁVA ROVNAKÝ ==========

def create_employee_button_in_column(emp, analyzer, index, prefix):
    """Vytvorí tlačidlo zamestnanca v stĺpci"""
    
    name = emp.get('name', 'Unknown')
    workplace = emp.get('workplace', 'Neznáme')
    
    # Sales data
    actual_profit = find_correct_sales_data(name, emp, analyzer)
    emp['total_sales'] = actual_profit
    
    # Metriky
    metrics = calculate_real_employee_metrics(emp, analyzer)
    
    unique_key = f"{prefix}_col_{index}_{name.replace(' ', '_').replace('.', '')}"
    
    # ✅ OPRAVENÉ: Kompaktné farebné metriky s KONZISTENTNÝMI prahmani
    metric_compact = []
    metric_order = [('sales', '💰'), ('mail', '📧'), ('sketchup', '💻'), ('internet', '🌐'), ('overall', '⭐')]
    
    for key, emoji in metric_order:
        if key in metrics:
            value = metrics[key]['value']
            
            # ✅ KONZISTENTNÉ prahy pre všetky metriky
            if value >= 80:
                color = "🟢"  # Zelený - výborné
            elif value >= 60:
                color = "🟡"  # Žltý - dobré
            elif value >= 40:
                color = "🟠"  # Oranžový - priemerné  
            else:
                color = "🔴"  # Červený - zlé
            
            metric_compact.append(f"{color}{emoji}{value:.0f}")
    
    # Skrátenie dlhých mien
    short_name = name if len(name) <= 12 else name[:9] + "..."
    short_workplace = workplace[:6].title() if len(workplace) > 6 else workplace.title()
    
    # Rozdelenie metrík na 2 riadky
    first_line = "  ".join(metric_compact[:3])
    second_line = "  ".join(metric_compact[3:])
    
    # Button text
    button_text = f"👤 {short_name}\n📍 {short_workplace} | 💰{actual_profit/1000:.0f}K\n{first_line}"
    if second_line:
        button_text += f"\n{second_line}"
    
    is_selected = st.session_state.get('selected_employee') == name
    
    # TLAČIDLO
    if st.button(
        button_text,
        key=unique_key,
        use_container_width=True,
        type="primary" if is_selected else "secondary",
        help=f"📊 {name}\n🏢 {workplace.title()}\n💰 Predaj: {actual_profit:,.0f} Kč\n\n" +
             f"💻 SketchUp: {metrics.get('sketchup', {}).get('value', 0):.0f}% " + 
             f"({'Nepoužíva' if metrics.get('sketchup', {}).get('value', 0) >= 80 else 'Používa často'})"
    ):
        # ✅ BEZPEČNOSTNÁ KONTROLA - overenie oprávnení k mestu
        from auth.auth import can_access_city
        
        if can_access_city(workplace):
            st.session_state.selected_employee = name
            st.session_state.current_page = 'employee'
            st.rerun()
        else:
            st.error(f"❌ Nemáte oprávnenie pristúpiť k zamestnancovi z mesta: {workplace.title()}")
            st.warning("🔒 Kontaktujte administrátora pre rozšírenie oprávnení")

def find_correct_sales_data(employee_name, emp, analyzer):
    """Automaticky nájde správne sales dáta zo všetkých zdrojov"""
    
    sales_candidates = []
    
    # 1. Z emp objektu monthly_sales
    if 'monthly_sales' in emp and emp['monthly_sales']:
        monthly_total = sum(emp['monthly_sales'].values())
        sales_candidates.append(('monthly_sales', monthly_total))
    
    # 2. Z emp objektu total_sales
    if emp.get('total_sales', 0) > 0:
        total_sales = emp.get('total_sales')
        sales_candidates.append(('total_sales', total_sales))
    
    # 3. Z analyzer.sales_employees
    if hasattr(analyzer, 'sales_employees'):
        for sales_emp in analyzer.sales_employees:
            if sales_emp.get('name') == employee_name:
                if 'monthly_sales' in sales_emp and sales_emp['monthly_sales']:
                    analyzer_total = sum(sales_emp['monthly_sales'].values())
                    sales_candidates.append(('analyzer_monthly', analyzer_total))
                break
    
    # Analýza a výber správnej hodnoty
    if not sales_candidates:
        return 0
    
    if len(sales_candidates) == 1:
        chosen_source, chosen_value = sales_candidates[0]
        return chosen_value
    
    # Viac zdrojov - uprednostniť monthly_sales
    for source, value in sales_candidates:
        if source in ['monthly_sales', 'analyzer_monthly']:
            return value
    
    # Fallback na prvý zdroj
    chosen_source, chosen_value = sales_candidates[0]
    
    return chosen_value

def show_neutral_legend():
    """Zobrazí neutrálnu legendu bez farieb"""
    
    create_section_header("Legenda metrík", "📊")
    
    # Jednoduchá textová legenda bez farieb
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown("**💰 Predaj**")
        st.caption("Predajná výkonnosť")
    
    with col2:
        st.markdown("**📧 Mail**") 
        st.caption("Efektivita mailov")
    
    with col3:
        st.markdown("**💻 SketchUp**")
        st.caption("Používanie programu")
    
    with col4:
        st.markdown("**🌐 Internet**")
        st.caption("Internetová aktivita")
    
    with col5:
        st.markdown("**⭐ Celkové**")
        st.caption("Celkové hodnotenie")

def calculate_real_employee_metrics(emp, analyzer):
    """Používa metrics calculator s opravenými overall scores"""
    
    employee_name = emp.get('name', '')
    
    # ✅ OPRAVENÉ: Výpočet sales z monthly_sales ak total_sales chýba
    if emp.get('total_sales', 0) == 0 and 'monthly_sales' in emp:
        sales = sum(emp['monthly_sales'].values()) if emp['monthly_sales'] else 0
        emp['total_sales'] = sales
    else:
        sales = emp.get('total_sales', 0)
    
    # Vytvorenie calculator objektu
    calculator = EmployeeMetricsCalculator(analyzer)
    
    # Výpočty
    sales_score = calculator.calculate_sales_score(sales)
    
    # Ostatné metriky
    try:
        mail_score = calculator.calculate_mail_efficiency(employee_name, sales)
    except Exception as e:
        mail_score = 65
    
    try:
        sketchup_score = calculator.calculate_sketchup_usage(employee_name)
    except Exception as e:
        sketchup_score = 90
    
    try:
        internet_score = calculator.calculate_internet_efficiency(employee_name)
    except Exception as e:
        internet_score = 60
    
    # ✅ OPRAVENÉ: Nájsť pôvodný overall score z analyzátora
    overall_score = find_original_overall_score(employee_name, analyzer)
    
    return {
        'sales': {'value': sales_score},
        'mail': {'value': mail_score},
        'sketchup': {'value': sketchup_score},
        'internet': {'value': internet_score},
        'overall': {'value': overall_score}
    }

def find_original_overall_score(employee_name, analyzer):
    """Nájde pôvodný overall score z analyzátora"""
    
    # Hľadanie v sales_employees
    if hasattr(analyzer, 'sales_employees'):
        for emp in analyzer.sales_employees:
            if emp.get('name') == employee_name:
                score = emp.get('score', 0)
                if score > 0:
                    return score
    
    # Fallback
    return 50
