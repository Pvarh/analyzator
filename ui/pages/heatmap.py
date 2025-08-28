# ui/pages/heatmap.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from core.utils import time_to_minutes, calculate_quarter_sales
from ui.styling import (
    get_dark_plotly_layout, apply_dark_theme, create_section_header, 
    create_subsection_header, create_simple_metric_card
)
from auth.auth import filter_data_by_user_access, can_access_city, get_user_cities, get_current_user


def calculate_weighted_benchmarks(analyzer):
    """Vypočíta vážené benchmarky na základe predajných výsledkov"""
    
    if not analyzer.sales_employees:
        return {'internet_benchmark': 50, 'app_benchmark': 50}
    
    total_weighted_internet = 0
    total_weighted_apps = 0
    total_weight = 0
    
    for emp in analyzer.sales_employees:
        emp_name = emp['name']
        
        # Váha = celkové predaje (vyšší predaj = vyššia váha)
        monthly_sales = emp.get('monthly_sales', {})
        total_sales = sum(monthly_sales.values()) if monthly_sales else 0
        weight = max(1, total_sales / 1000000)  # Minimálna váha 1, škálované na milióny
        
        # Výpočet metrík pre tohto zamestnanca
        internet_usage = calculate_raw_internet_usage(analyzer, emp_name)
        app_usage = calculate_raw_app_usage(analyzer, emp_name)
        
        # Vážený prispevok
        total_weighted_internet += internet_usage * weight
        total_weighted_apps += app_usage * weight
        total_weight += weight
    
    # Výpočet vážených priemerov
    if total_weight > 0:
        internet_benchmark = total_weighted_internet / total_weight
        app_benchmark = total_weighted_apps / total_weight
    else:
        internet_benchmark = 50
        app_benchmark = 50
    
    return {
        'internet_benchmark': internet_benchmark,
        'app_benchmark': app_benchmark
    }


def calculate_raw_internet_usage(analyzer, employee_name):
    """Vypočíta surovú hodnotu využívania internetu (bez relatívneho hodnotenia)"""
    
    canonical_name = analyzer.get_canonical_name(employee_name)
    matching_names = [name for name, canon in analyzer.name_mapping.items() if canon == canonical_name]
    
    if analyzer.internet_data is None:
        return 30  # Default nízke využívanie
    
    user_data = analyzer.internet_data[analyzer.internet_data['Osoba ▲'].isin(matching_names)]
    
    if user_data.empty:
        return 30
    
    total_internet_time = 0
    total_available_time = 0
    
    for _, row in user_data.iterrows():
        # Všetky internet aktivity
        internet_time = (
            time_to_minutes(row.get('Mail', '0:00')) +
            time_to_minutes(row.get('IS Sykora', '0:00')) +
            time_to_minutes(row.get('SykoraShop', '0:00')) +
            time_to_minutes(row.get('Web k praci', '0:00')) +
            time_to_minutes(row.get('Chat', '0:00')) +
            time_to_minutes(row.get('Hry', '0:00')) +
            time_to_minutes(row.get('Nepracovni weby', '0:00'))
        )
        
        day_total = time_to_minutes(row.get('Čas celkem ▼', '0:00'))
        if day_total == 0:
            day_total = 480  # 8h
        
        total_internet_time += internet_time
        total_available_time += day_total
    
    if total_available_time > 0:
        return (total_internet_time / total_available_time) * 100
    
    return 30


def calculate_raw_app_usage(analyzer, employee_name):
    """Vypočíta surovú hodnotu využívania aplikácií (bez relatívneho hodnotenia)"""
    
    canonical_name = analyzer.get_canonical_name(employee_name)
    matching_names = [name for name, canon in analyzer.name_mapping.items() if canon == canonical_name]
    
    if analyzer.applications_data is None:
        return 20  # Default nízke využívanie
    
    user_data = analyzer.applications_data[analyzer.applications_data['Osoba ▲'].isin(matching_names)]
    
    if user_data.empty:
        return 20
    
    total_app_time = 0
    total_available_time = 0
    
    for _, row in user_data.iterrows():
        # Produktívne aplikácie
        app_time = (
            time_to_minutes(row.get('Helios Green', '0:00')) +
            time_to_minutes(row.get('Imos - program', '0:00')) +
            time_to_minutes(row.get('Mail', '0:00')) +
            time_to_minutes(row.get('Programy', '0:00')) +
            time_to_minutes(row.get('Půdorysy', '0:00'))
        )
        
        day_total = time_to_minutes(row.get('Čas celkem ▼', '0:00'))
        if day_total == 0:
            day_total = 480
        
        total_app_time += app_time
        total_available_time += day_total
    
    if total_available_time > 0:
        return (total_app_time / total_available_time) * 100
    
    return 20


def calculate_internet_productivity(analyzer, employee_name):
    """Vypočíta relatívne internet skóre oproti váhovanému priemeru"""
    
    # Získanie benchmarkov (iba raz pre všetkých)
    if not hasattr(analyzer, '_heatmap_benchmarks'):
        analyzer._heatmap_benchmarks = calculate_weighted_benchmarks(analyzer)
    
    benchmarks = analyzer._heatmap_benchmarks
    internet_benchmark = benchmarks['internet_benchmark']
    
    # Surová hodnota pre tohto zamestnanca
    raw_usage = calculate_raw_internet_usage(analyzer, employee_name)
    
    # Relatívne hodnotenie (menej internetu = lepšie)
    if internet_benchmark > 0:
        # Inverzný vzťah: ak má menej internetu ako priemer = lepšie skóre
        relative_score = 100 * (internet_benchmark / max(raw_usage, 1))
        return min(100, max(0, relative_score))
    
    return 50


def calculate_app_productivity(analyzer, employee_name):
    """Vypočíta relatívne aplikačné skóre oproti váhovanému priemeru"""
    
    # Získanie benchmarkov (iba raz pre všetkých)
    if not hasattr(analyzer, '_heatmap_benchmarks'):
        analyzer._heatmap_benchmarks = calculate_weighted_benchmarks(analyzer)
    
    benchmarks = analyzer._heatmap_benchmarks
    app_benchmark = benchmarks['app_benchmark']
    
    # Surová hodnota pre tohto zamestnanca
    raw_usage = calculate_raw_app_usage(analyzer, employee_name)
    
    # Relatívne hodnotenie (viac aplikácií = lepšie)
    if app_benchmark > 0:
        # Priamy vzťah: ak má viac aplikácií ako priemer = lepšie skóre
        relative_score = 100 * (raw_usage / app_benchmark)
        return min(100, max(0, relative_score))
    
    return 50


def get_available_quarters(sales_employees):
    """Zistí ktoré štvrťroky majú dostatok dát"""
    
    if not sales_employees:
        return ['Q1', 'Q2']
    
    # Skontroluj aké mesiace máme v dátach
    all_months = set()
    for emp in sales_employees:
        monthly_sales = emp.get('monthly_sales', {})
        for month in monthly_sales.keys():
            if monthly_sales[month] > 0:  # Len mesiace s dátami
                all_months.add(month.lower())
    
    quarters = []
    quarter_months = {
        'Q1': ['leden', 'unor', 'brezen'],
        'Q2': ['duben', 'kveten', 'cerven'], 
        'Q3': ['cervenec', 'srpen', 'zari'],
        'Q4': ['rijen', 'listopad', 'prosinec']
    }
    
    for quarter, months in quarter_months.items():
        # Ak má aspoň jeden mesiac dáta, zahrnúť štvrťrok
        if any(month in all_months for month in months):
            quarters.append(quarter)
    
    return quarters


def render(analyzer):
    """Teplotná mapa výkonnosti zamestnancov - s váhovaným hodnotením"""
    apply_dark_theme()
    
    if not analyzer or not analyzer.sales_employees:
        st.error("❌ Žiadne dáta pre teplotná mapa")
        return
    
    # ✅ NOVÉ - Filtrovanie zamestnancov podľa oprávnení používateľa
    filtered_employees = []
    user_cities = get_user_cities()
    current_user = get_current_user()
    
    for employee in analyzer.sales_employees:
        if current_user and current_user.get('role') == 'admin':
            # Admin vidí všetkých
            filtered_employees.append(employee)
        elif employee.get('workplace', '').lower() in [c.lower() for c in user_cities]:
            # Manažér vidí len svojich
            filtered_employees.append(employee)
    
    if not filtered_employees:
        st.warning("⚠️ Nemáte oprávnenie na zobrazenie týchto dát alebo nie sú dostupné")
        return
    
    # Použitie filtrovaných zamestnancov namiesto pôvodných
    original_employees = analyzer.sales_employees
    analyzer.sales_employees = filtered_employees
    
    # Zistenie dostupných štvrťrokov
    available_quarters = get_available_quarters(analyzer.sales_employees)
    
    # Príprava dát pre heatmapu
    employees = []
    quarterly_scores = {}  # Dynamické štvrťroky
    internet_scores = []
    app_scores = []
    overall_scores = []
    
    for i, emp in enumerate(analyzer.sales_employees):
        emp_name = emp['name']
        
        employees.append(emp_name)
        
        monthly_sales = emp.get('monthly_sales', {})
        
        # Dynamické spracovanie štvrťrokov
        for quarter in available_quarters:
            if quarter not in quarterly_scores:
                quarterly_scores[quarter] = []
            
            quarter_sales = calculate_quarter_sales(monthly_sales, quarter)
            quarter_score = min(100, (quarter_sales / 2000000 * 100)) if quarter_sales else 0
            quarterly_scores[quarter].append(quarter_score)
        
        # ✅ POUŽÍVAME VÁŽENÉ HODNOTENIE
        internet_productivity = calculate_internet_productivity(analyzer, emp_name)
        app_productivity = calculate_app_productivity(analyzer, emp_name)
        
        internet_scores.append(internet_productivity)
        app_scores.append(app_productivity)
        
        # Celkové skóre s dynamickými štvrťrokmi
        total_sales = sum(monthly_sales.values()) if monthly_sales else 0
        target_sales = len(available_quarters) * 2000000  # 2M na štvrťrok
        sales_score = min(100, (total_sales / target_sales * 100)) if total_sales and target_sales > 0 else 0
        overall_score = (sales_score * 0.5 + internet_productivity * 0.25 + app_productivity * 0.25)
        overall_scores.append(overall_score)
    
    # Zobrazenie výsledkov
    show_results_summary(internet_scores, app_scores, overall_scores, available_quarters)
    
    # Vytvorenie heatmapy
    if any(score > 0 for score in internet_scores + app_scores):
        create_dynamic_heatmap_chart(employees, quarterly_scores, internet_scores, app_scores, overall_scores, available_quarters)
        show_dynamic_summary_stats(quarterly_scores, internet_scores, app_scores, overall_scores, available_quarters)
    else:
        st.warning("⚠️ Všetky internet a aplikačné skóre sú 0% - skontrolujte name mapping v analyzer.py")
    
    st.markdown("---")
    
    # Debug tabuľka
    show_dynamic_debug_table(employees, quarterly_scores, internet_scores, app_scores, overall_scores, available_quarters)
    
    # Interpretačná príručka
    show_interpretation_guide()
    
    # ✅ Obnovenie pôvodných dát na konci render funkcie
    analyzer.sales_employees = original_employees


def show_results_summary(internet_scores, app_scores, overall_scores, available_quarters):
    """Zobrazuje súhrn výsledkov s dynamickými štvrťrokmi"""
    
    st.markdown("### 📈 Súhrn výsledkov")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📅 Štvrťroky", f"{len(available_quarters)}", f"Dostupné: {', '.join(available_quarters)}")
    
    with col2:
        non_zero_internet = sum(1 for score in internet_scores if score > 0)
        avg_internet = sum(internet_scores) / len(internet_scores) if internet_scores else 0
        st.metric("🌐 Internet produktivita", f"{non_zero_internet}/{len(internet_scores)} osôb", f"Priemer: {avg_internet:.1f}%")
    
    with col3:
        non_zero_app = sum(1 for score in app_scores if score > 0)
        avg_app = sum(app_scores) / len(app_scores) if app_scores else 0
        st.metric("💻 App produktivita", f"{non_zero_app}/{len(app_scores)} osôb", f"Priemer: {avg_app:.1f}%")
    
    with col4:
        avg_overall = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        st.metric("⭐ Celkový priemer", f"{avg_overall:.1f}%", f"Všetky metriky")


def create_dynamic_heatmap_chart(employees, quarterly_scores, internet_scores, app_scores, overall_scores, available_quarters):
    """Vytvorí heatmapu s dynamickým počtom štvrťrokov"""
    
    st.markdown("### 🎯 Interaktívna teplotná mapa")
    
    # Ovládanie grafu
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        color_scheme = st.selectbox(
            "🎨 Farebná schéma:",
            ["RdYlGn", "Viridis", "Plasma", "Blues", "Reds"],
            index=0
        )
    
    with col2:
        show_values = st.checkbox("📊 Zobraziť hodnoty", value=True)
    
    with col3:
        reverse_colors = st.checkbox("🔄 Obrátené farby", value=False)
    
    # Príprava dátovej matrice a stĺpcov
    data_matrix = []
    column_names = []
    
    # Pridanie štvrťrokov do stĺpcov
    for quarter in available_quarters:
        column_names.append(f'{quarter} Predaj')
    
    # Pridanie ostatných metrík
    column_names.extend(['Internet', 'Aplikácie', 'Celkové'])
    
    # Vytvorenie matrice
    for i in range(len(employees)):
        row = []
        
        # Pridanie štvrťročných skóre
        for quarter in available_quarters:
            row.append(quarterly_scores[quarter][i])
        
        # Pridanie ostatných metrík
        row.extend([internet_scores[i], app_scores[i], overall_scores[i]])
        data_matrix.append(row)
    
    # Skrátenie dlhých mien
    short_employees = [emp[:15] + "..." if len(emp) > 15 else emp for emp in employees]
    
    fig = go.Figure(data=go.Heatmap(
        z=data_matrix,
        x=column_names,
        y=short_employees,
        colorscale=color_scheme if not reverse_colors else color_scheme + "_r",
        text=[[f'{val:.1f}%' for val in row] for row in data_matrix] if show_values else None,
        texttemplate='%{text}' if show_values else None,
        textfont={'size': 10, 'color': 'white'},
        hoverongaps=False,
        hovertemplate="<b>%{y}</b><br>%{x}: %{z:.1f}%<extra></extra>",
        colorbar=dict(
            title=dict(
                text="Skóre (%)",
                font=dict(color='#fafafa')
            ),
            tickfont=dict(color='#fafafa'),
            thickness=20,
            len=0.7
        )
    ))
    
    # Layout s peknou grafikou
    layout_settings = get_dark_plotly_layout()
    layout_settings.update({
        'title': {
            'text': f"🌡️ Teplotná mapa - Vážené hodnotenie ({len(available_quarters)} štvrťroky)",
            'x': 0.5,
            'font': {'size': 20, 'color': '#fafafa'}
        },
        'height': max(500, len(employees) * 35 + 150),
        'hovermode': 'closest',
        'xaxis': {
            'title': {
                'text': "Metriky výkonnosti",
                'font': {'color': '#fafafa'}
            },
            'tickfont': {'color': '#fafafa', 'size': 12},
            'side': 'bottom'
        },
        'yaxis': {
            'title': {
                'text': "Zamestnanci",
                'font': {'color': '#fafafa'}
            },
            'tickfont': {'color': '#fafafa', 'size': 10},
            'autorange': 'reversed'
        },
        'margin': {'l': 120, 'r': 100, 't': 80, 'b': 80}
    })
    
    fig.update_layout(**layout_settings)
    
    st.plotly_chart(fig, use_container_width=True)


def show_dynamic_summary_stats(quarterly_scores, internet_scores, app_scores, overall_scores, available_quarters):
    """Zobrazuje súhrnné štatistiky s dynamickými štvrťrokmi"""
    
    st.markdown("### 📊 Súhrnné štatistiky")
    
    # Výpočet priemerov
    quarter_averages = {}
    for quarter in available_quarters:
        quarter_averages[quarter] = sum(quarterly_scores[quarter]) / len(quarterly_scores[quarter]) if quarterly_scores[quarter] else 0
    
    avg_internet = sum(internet_scores) / len(internet_scores) if internet_scores else 0
    avg_apps = sum(app_scores) / len(app_scores) if app_scores else 0
    avg_overall = sum(overall_scores) / len(overall_scores) if overall_scores else 0
    
    # Dynamické stĺpce pre štvrťroky
    if available_quarters:
        quarter_cols = st.columns(len(available_quarters))
        colors = ["#ef4444", "#f97316", "#eab308", "#84cc16"]  # Červená, oranžová, žltá, zelená
        
        for i, quarter in enumerate(available_quarters):
            with quarter_cols[i]:
                color = colors[i % len(colors)]
                avg_value = quarter_averages[quarter]
                
                # Určenie statusu
                if avg_value >= 80:
                    status = "Výborné"
                    status_color = "#10b981"
                elif avg_value >= 60:
                    status = "Dobré"
                    status_color = "#3b82f6"
                elif avg_value >= 40:
                    status = "Priemerné"
                    status_color = "#f59e0b"
                else:
                    status = "Slabé"
                    status_color = "#ef4444"
                
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
                        {quarter} Štvrťrok
                    </h5>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0;">
                        <div>
                            <p style="color: #9ca3af; margin: 2px 0; font-size: 0.8rem;">Priemer:</p>
                            <p style="color: white; margin: 2px 0; font-weight: bold; font-size: 1.2rem;">{avg_value:.1f}%</p>
                        </div>
                        <div>
                            <p style="color: #9ca3af; margin: 2px 0; font-size: 0.8rem;">Cieľ:</p>
                            <p style="color: #9ca3af; margin: 2px 0; font-weight: bold;">2M Kč</p>
                        </div>
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
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Ostatné metriky
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Internet status
        if avg_internet >= 80:
            internet_status = "Výborná"
            internet_status_color = "#10b981"
        elif avg_internet >= 60:
            internet_status = "Dobrá"
            internet_status_color = "#3b82f6"
        elif avg_internet >= 40:
            internet_status = "Priemerná"
            internet_status_color = "#f59e0b"
        else:
            internet_status = "Nízka"
            internet_status_color = "#ef4444"
            
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(31, 41, 55, 0.9), rgba(55, 65, 81, 0.9));
            border-left: 4px solid #3b82f6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        ">
            <h5 style="color: #3b82f6; margin: 0 0 10px 0; font-size: 1rem;">
                🌐 Internet produktivita
            </h5>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0;">
                <div>
                    <p style="color: #9ca3af; margin: 2px 0; font-size: 0.8rem;">Priemer:</p>
                    <p style="color: white; margin: 2px 0; font-weight: bold; font-size: 1.2rem;">{avg_internet:.1f}%</p>
                </div>
                <div>
                    <p style="color: #9ca3af; margin: 2px 0; font-size: 0.8rem;">Typ:</p>
                    <p style="color: #9ca3af; margin: 2px 0; font-weight: bold;">Vážený</p>
                </div>
            </div>
            <div style="margin-top: 8px;">
                <span style="
                    background: {internet_status_color}20; 
                    color: {internet_status_color}; 
                    padding: 2px 8px; 
                    border-radius: 12px; 
                    font-size: 0.75rem;
                    font-weight: bold;
                ">
                    {internet_status}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Apps status
        if avg_apps >= 80:
            apps_status = "Výborná"
            apps_status_color = "#10b981"
        elif avg_apps >= 60:
            apps_status = "Dobrá"
            apps_status_color = "#3b82f6"
        elif avg_apps >= 40:
            apps_status = "Priemerná"
            apps_status_color = "#f59e0b"
        else:
            apps_status = "Nízka"
            apps_status_color = "#ef4444"
            
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(31, 41, 55, 0.9), rgba(55, 65, 81, 0.9));
            border-left: 4px solid #10b981;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        ">
            <h5 style="color: #10b981; margin: 0 0 10px 0; font-size: 1rem;">
                💻 Aplikácie produktivita
            </h5>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0;">
                <div>
                    <p style="color: #9ca3af; margin: 2px 0; font-size: 0.8rem;">Priemer:</p>
                    <p style="color: white; margin: 2px 0; font-weight: bold; font-size: 1.2rem;">{avg_apps:.1f}%</p>
                </div>
                <div>
                    <p style="color: #9ca3af; margin: 2px 0; font-size: 0.8rem;">Typ:</p>
                    <p style="color: #9ca3af; margin: 2px 0; font-weight: bold;">Vážený</p>
                </div>
            </div>
            <div style="margin-top: 8px;">
                <span style="
                    background: {apps_status_color}20; 
                    color: {apps_status_color}; 
                    padding: 2px 8px; 
                    border-radius: 12px; 
                    font-size: 0.75rem;
                    font-weight: bold;
                ">
                    {apps_status}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Overall status
        if avg_overall >= 80:
            overall_status = "Výborná"
            overall_status_color = "#10b981"
        elif avg_overall >= 60:
            overall_status = "Dobrá"
            overall_status_color = "#3b82f6"
        elif avg_overall >= 40:
            overall_status = "Priemerná"
            overall_status_color = "#f59e0b"
        else:
            overall_status = "Nízka"
            overall_status_color = "#ef4444"
            
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(31, 41, 55, 0.9), rgba(55, 65, 81, 0.9));
            border-left: 4px solid #8b5cf6;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        ">
            <h5 style="color: #8b5cf6; margin: 0 0 10px 0; font-size: 1rem;">
                ⭐ Celkové hodnotenie
            </h5>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0;">
                <div>
                    <p style="color: #9ca3af; margin: 2px 0; font-size: 0.8rem;">Priemer:</p>
                    <p style="color: white; margin: 2px 0; font-weight: bold; font-size: 1.2rem;">{avg_overall:.1f}%</p>
                </div>
                <div>
                    <p style="color: #9ca3af; margin: 2px 0; font-size: 0.8rem;">Váhy:</p>
                    <p style="color: #9ca3af; margin: 2px 0; font-weight: bold;">50-25-25</p>
                </div>
            </div>
            <div style="margin-top: 8px;">
                <span style="
                    background: {overall_status_color}20; 
                    color: {overall_status_color}; 
                    padding: 2px 8px; 
                    border-radius: 12px; 
                    font-size: 0.75rem;
                    font-weight: bold;
                ">
                    {overall_status}
                </span>
                <span style="
                    background: rgba(107, 114, 128, 0.2); 
                    color: #9ca3af; 
                    padding: 2px 8px; 
                    border-radius: 12px; 
                    font-size: 0.75rem;
                    margin-left: 5px;
                ">
                    Kombinované
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def show_dynamic_debug_table(employees, quarterly_scores, internet_scores, app_scores, overall_scores, available_quarters):
    """Zobrazí debug tabuľku s dynamickými štvrťrokmi"""
    
    with st.expander("🔧 Debug - Detailné hodnoty", expanded=False):
        debug_data = []
        for i, emp_name in enumerate(employees):
            row_data = {'Zamestnanec': emp_name}
            
            # Pridanie štvrťrokov
            for quarter in available_quarters:
                row_data[f'{quarter} Predaj'] = f'{quarterly_scores[quarter][i]:.1f}%'
            
            # Pridanie ostatných metrík
            row_data.update({
                'Internet': f'{internet_scores[i]:.1f}%',
                'Aplikácie': f'{app_scores[i]:.1f}%',
                'Celkové': f'{overall_scores[i]:.1f}%'
            })
            
            debug_data.append(row_data)
        
        st.dataframe(pd.DataFrame(debug_data), use_container_width=True)


def show_interpretation_guide():
    """Zobrazuje príručku na interpretáciu výsledkov"""
    
    with st.expander("📚 Príručka interpretácie", expanded=False):
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🎯 Farebné rozlíšenie:**
            - 🟢 **Zelená (80-100%)**: Výborná výkonnosť
            - 🟡 **Žltá (60-79%)**: Dobrá výkonnosť  
            - 🟠 **Oranžová (40-59%)**: Priemerná výkonnosť
            - 🔴 **Červená (0-39%)**: Podpriemerná výkonnosť
            
            **📊 Metriky vysvetlenie:**
            - **Q1/Q2/Q3/Q4 Predaj**: Predajné výsledky za štvrťrok (cieľ 2M Kč)
            - **Internet**: Relatívne skóre oproti váženému priemeru
            - **Aplikácie**: Relatívne skóre oproti váženému priemeru
            """)
        
        with col2:
            st.markdown("""
            **⚖️ Vážené hodnotenie:**
            - **Zamestnanci s vyššími predajmi** majú väčšiu váhu pri tvorbe benchmarkov
            - **Internet skóre**: Menej ako benchmark = vyššie skóre
            - **Aplikácie skóre**: Viac ako benchmark = vyššie skóre
            - **100% = dvojnásobný benchmark výkon**
            
            **🎯 Príklad:**
            - Benchmark internet: 35%, aplikácie: 25%
            - Zamestnanec: 20% internet, 40% aplikácie
            - Skóre: Internet 100%, Aplikácie 100%
            
            **💡 Výhody:**
            - Top performeri ovplyvňujú štandardy
            - Spravodlivé relatívne porovnávanie
            - Zohľadnené predajné výsledky
            """)
        
        st.success("🏆 **Tip**: Hodnotenie je teraz založené na váhovaných benchmarkoch - spravodlivejšie a realistickejšie!")
