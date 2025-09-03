"""
KPI System - Individuálne ciele a hodnotenie výkonnosti
Stránka s city-based security a modulárnym dizajnom
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from core.kpi_manager import KPIManager
from auth.auth import get_current_user, is_admin


def render():
    """Hlavná KPI stránka"""
    
    # CSS štýly
    st.markdown("""
    <style>
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .progress-bar {
        background-color: #e9ecef;
        border-radius: 10px;
        height: 20px;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.3s ease;
    }
    .excellent { background-color: #28a745; }
    .good { background-color: #ffc107; }
    .average { background-color: #17a2b8; }
    .poor { background-color: #dc3545; }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="kpi-card">
        <h1>🎯 KPI Systém</h1>
        <p>Individuálne ciele a hodnotenie výkonnosti s real-time trackingom</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializácia
    kpi_manager = KPIManager()
    current_user = get_current_user()
    
    if not current_user:
        st.error("❌ Musíte byť prihlásený")
        return
    
    # Admin vs Manager view
    if is_admin():
        render_admin_view(kpi_manager)
    else:
        render_manager_view(kpi_manager, current_user)


def render_admin_view(kpi_manager: KPIManager):
    """Admin pohľad - všetky mestá a zamestnanci"""
    
    st.subheader("👑 Admin Panel - KPI Management")
    
    # Tabs pre admin
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Prehľad všetkých",
        "🎯 Nastavenie cieľov", 
        "📈 Analýzy",
        "⚙️ Konfigurácia"
    ])
    
    with tab1:
        render_admin_overview(kpi_manager)
    
    with tab2:
        render_goals_management(kpi_manager)
    
    with tab3:
        render_admin_analytics(kpi_manager)
    
    with tab4:
        render_system_config(kpi_manager)


def render_manager_view(kpi_manager: KPIManager, current_user):
    """Manager pohľad - len svoje mesto"""
    
    # Získaj mesto používateľa
    user_city = current_user.get('cities', [''])[0] if current_user.get('cities') else ''
    
    if not user_city or user_city == 'all':
        st.error("❌ Nemáte pridelené žiadne mesto")
        return
    
    st.subheader(f"📊 KPI Dashboard - {user_city.title()}")
    
    # Tabs pre manažéra
    tab1, tab2, tab3 = st.tabs([
        "🎯 Moje KPI",
        "👥 Tím",
        "📈 Analýzy"
    ])
    
    with tab1:
        render_personal_kpis(kpi_manager, current_user['email'], user_city)
    
    with tab2:
        render_team_overview(kpi_manager, user_city)
    
    with tab3:
        render_team_analytics(kpi_manager, user_city)


def render_admin_overview(kpi_manager: KPIManager):
    """Admin prehľad všetkých miest"""
    
    st.markdown("### 🌍 Globálny prehľad")
    
    # Výber mesta pre detail
    analyzer = st.session_state.get('analyzer')
    if not analyzer:
        st.error("❌ Analyzer nie je dostupný")
        return
        
    all_employees = analyzer.get_all_employees_summary()
    
    cities = list(set([emp.get('workplace', 'unknown').lower() for emp in all_employees]))
    cities = [c for c in cities if c != 'unknown']
    
    selected_city = st.selectbox(
        "🏙️ Vyberte mesto pre detail:",
        ["Všetky"] + [city.title() for city in cities]
    )
    
    if selected_city == "Všetky":
        # Celkový prehľad
        render_global_metrics(kpi_manager, cities, analyzer)
    else:
        # Konkrétne mesto
        render_city_detail(kpi_manager, selected_city.lower(), analyzer)


def render_global_metrics(kpi_manager: KPIManager, cities, analyzer):
    """Globálne metriky všetkých miest"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_employees = 0
    total_excellent = 0
    avg_scores = []
    
    for city in cities:
        team_overview = kpi_manager.get_team_overview(city, analyzer)
        if 'error' not in team_overview:
            total_employees += team_overview.get('total_employees', 0)
            total_excellent += team_overview.get('excellent_performers', 0)
            if team_overview.get('average_score'):
                avg_scores.append(team_overview.get('average_score', 0))
    
    with col1:
        st.metric("👥 Celkom zamestnancov", total_employees)
    
    with col2:
        st.metric("🏆 Excelentných", f"{total_excellent}/{total_employees}")
    
    with col3:
        global_avg = sum(avg_scores) / len(avg_scores) if avg_scores else 0
        st.metric("📊 Globálny priemer", f"{global_avg:.1f}%")
    
    with col4:
        success_rate = (total_excellent / total_employees * 100) if total_employees > 0 else 0
        st.metric("✅ Úspešnosť", f"{success_rate:.1f}%")
    
    # Graf porovnania miest
    if cities:
        st.markdown("---")
        render_cities_comparison_chart(kpi_manager, cities, analyzer)


def render_cities_comparison_chart(kpi_manager: KPIManager, cities, analyzer):
    """Graf porovnania miest"""
    
    st.markdown("### 🏙️ Porovnanie miest")
    
    city_data = []
    for city in cities:
        team_overview = kpi_manager.get_team_overview(city, analyzer)
        if 'error' not in team_overview:
            city_data.append({
                'Mesto': city.title(),
                'Zamestnanci': team_overview.get('total_employees', 0),
                'Priemerné skóre': team_overview.get('average_score', 0),
                'Excelentní': team_overview.get('excellent_performers', 0)
            })
    
    if city_data:
        df = pd.DataFrame(city_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_bar = px.bar(
                df, 
                x='Mesto', 
                y='Priemerné skóre',
                title="Priemerné KPI skóre po mestách",
                color='Priemerné skóre',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            fig_scatter = px.scatter(
                df,
                x='Zamestnanci',
                y='Excelentní', 
                size='Priemerné skóre',
                title="Excelentní performers vs veľkosť tímu",
                hover_data=['Mesto']
            )
            st.plotly_chart(fig_scatter, use_container_width=True)


def render_city_detail(kpi_manager: KPIManager, city, analyzer):
    """Detail konkrétneho mesta"""
    
    st.markdown(f"### 🏙️ Detail mesta: {city.title()}")
    
    team_overview = kpi_manager.get_team_overview(city, analyzer)
    
    if 'error' in team_overview:
        st.error(f"❌ {team_overview['error']}")
        return
    
    # Základné metriky
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Zamestnanci", team_overview['total_employees'])
    
    with col2:
        st.metric("📊 Priemer", f"{team_overview['average_score']:.1f}%")
    
    with col3:
        st.metric("🏆 Excelentní", team_overview['excellent_performers'])
    
    with col4:
        success_rate = (team_overview['excellent_performers'] / team_overview['total_employees'] * 100) if team_overview['total_employees'] > 0 else 0
        st.metric("✅ Úspešnosť", f"{success_rate:.1f}%")
    
    # Detail zamestnancov
    render_employees_table(team_overview.get('employees', []))


def render_employees_table(employees):
    """Tabuľka zamestnancov s KPI"""
    
    if not employees:
        st.info("📊 Žiadne dáta o zamestnancoch")
        return
    
    st.markdown("---")
    st.markdown("### 👥 Detail zamestnancov")
    
    # Príprava dát pre tabuľku
    table_data = []
    for emp in employees:
        if 'error' not in emp:
            employee_info = emp.get('employee_info', {})
            table_data.append({
                'Meno': employee_info.get('name', 'Unknown'),
                'Email': emp.get('email', ''),
                'Celkové skóre': f"{emp.get('overall_score', 0):.1f}%",
                'Predaj (aktuálny)': f"{emp.get('actuals', {}).get('sales', 0):,.0f} Kč",
                'Predaj (progress)': f"{emp.get('progress', {}).get('sales', 0):.1f}%", 
                'Aktivita': f"{emp.get('progress', {}).get('activity', 0):.1f}%",
                'Výkon': emp.get('performance_level', {}).get('label', 'N/A')
            })
    
    if table_data:
        df = pd.DataFrame(table_data)
        df = df.sort_values('Celkové skóre', ascending=False, key=lambda x: x.str.rstrip('%').astype(float))
        st.dataframe(df, use_container_width=True)


def render_personal_kpis(kpi_manager: KPIManager, email, city):
    """Osobné KPI manažéra"""
    
    st.markdown("### 🎯 Moje osobné KPI")
    
    # Získaj osobné KPI
    personal_kpis = kpi_manager.get_employee_kpis(email)
    
    if 'error' in personal_kpis:
        st.error(f"❌ {personal_kpis['error']}")
        return
    
    # Celkové skóre
    overall_score = personal_kpis.get('overall_score', 0)
    performance_level = personal_kpis.get('performance_level', {})
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📊 Celkové KPI skóre</h3>
            <h1 style="color: {performance_level.get('color', '#333')}; margin: 0;">
                {overall_score:.1f}%
            </h1>
            <p>{performance_level.get('label', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        period = personal_kpis.get('period', 'current')
        st.metric("📅 Obdobie", period.upper())
    
    with col3:
        last_update = personal_kpis.get('last_updated', '')
        if last_update:
            update_date = datetime.fromisoformat(last_update.replace('Z', '+00:00')).strftime('%d.%m. %H:%M')
            st.metric("🔄 Aktualizované", update_date)
    
    # Detail metrík
    st.markdown("---")
    render_kpi_details(personal_kpis)


def render_kpi_details(kpis):
    """Detail jednotlivých KPI metrík"""
    
    st.markdown("### 📈 Detail metrík")
    
    goals = kpis.get('goals', {})
    actuals = kpis.get('actuals', {})
    progress = kpis.get('progress', {})
    
    # Predajné KPI
    if 'sales' in goals:
        col1, col2 = st.columns(2)
        
        with col1:
            sales_goal = goals['sales']
            sales_actual = actuals.get('sales', 0)
            sales_progress = progress.get('sales', 0)
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>💰 Predajné KPI</h4>
                <p><strong>Cieľ:</strong> {sales_goal:,} Kč</p>
                <p><strong>Aktuálne:</strong> {sales_actual:,} Kč</p>
                <p><strong>Progress:</strong> {sales_progress:.1f}%</p>
                <div class="progress-bar">
                    <div class="progress-fill {'excellent' if sales_progress >= 100 else 'good' if sales_progress >= 75 else 'average' if sales_progress >= 50 else 'poor'}" 
                         style="width: {min(sales_progress, 100)}%"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Graf predajného trendu
            render_sales_trend_chart(kpis)
    
    # Activity KPI
    if 'activity_score' in goals:
        activity_goal = goals['activity_score']
        activity_actual = actuals.get('activity', 0)
        activity_progress = progress.get('activity', 0)
        
        st.markdown(f"""
        <div class="metric-card">
            <h4>📊 Aktivita v systéme</h4>
            <p><strong>Cieľ:</strong> {activity_goal} bodov</p>
            <p><strong>Aktuálne:</strong> {activity_actual} bodov</p>
            <p><strong>Progress:</strong> {activity_progress:.1f}%</p>
            <div class="progress-bar">
                <div class="progress-fill {'excellent' if activity_progress >= 100 else 'good' if activity_progress >= 75 else 'average' if activity_progress >= 50 else 'poor'}" 
                     style="width: {min(activity_progress, 100)}%"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_sales_trend_chart(kpis):
    """Graf predajného trendu"""
    
    # Dummy dáta pre trend (neskôr napojíme na skutočné dáta)
    months = ['Jan', 'Feb', 'Mar']
    actual_sales = [800000, 900000, 750000]  # Dummy
    target_line = [kpis.get('goals', {}).get('sales', 2000000) / 3] * 3
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=months,
        y=actual_sales,
        mode='lines+markers',
        name='Skutočné predaje',
        line=dict(color='#007bff', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=months,
        y=target_line,
        mode='lines',
        name='Mesačný cieľ',
        line=dict(color='red', dash='dash')
    ))
    
    fig.update_layout(
        title="Predajný trend",
        xaxis_title="Mesiac",
        yaxis_title="Predaj (Kč)",
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_team_overview(kpi_manager: KPIManager, city):
    """Prehľad tímu pre manažéra"""
    
    st.markdown(f"### 👥 Prehľad tímu - {city.title()}")
    
    analyzer = st.session_state.get('analyzer')
    if not analyzer:
        st.error("❌ Analyzer nie je dostupný")
        return
    
    team_overview = kpi_manager.get_team_overview(city, analyzer)
    
    if 'error' in team_overview:
        st.error(f"❌ {team_overview['error']}")
        return
    
    # Základné metriky tímu
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Tím", team_overview['total_employees'])
    
    with col2:
        st.metric("📊 Priemer", f"{team_overview['average_score']:.1f}%")
    
    with col3:
        st.metric("🏆 Top performeri", team_overview['excellent_performers'])
    
    with col4:
        success_rate = (team_overview['excellent_performers'] / team_overview['total_employees'] * 100) if team_overview['total_employees'] > 0 else 0
        st.metric("✅ Úspešnosť", f"{success_rate:.1f}%")
    
    # Detail zamestnancov
    st.markdown("---")
    render_employees_table(team_overview.get('employees', []))


def render_team_analytics(kpi_manager: KPIManager, city):
    """Analytické pohľady pre tím"""
    
    st.markdown(f"### 📈 Analytika tímu - {city.title()}")
    
    analyzer = st.session_state.get('analyzer')
    if not analyzer:
        st.error("❌ Analyzer nie je dostupný")
        return
    
    team_overview = kpi_manager.get_team_overview(city, analyzer)
    
    if 'error' in team_overview or not team_overview.get('employees'):
        st.info("📊 Nedostatok dát pre analýzu")
        return
    
    employees = team_overview['employees']
    
    # Graf distribúcie výkonnosti
    performance_counts = {}
    for emp in employees:
        if 'error' not in emp:
            perf_level = emp.get('performance_level', {}).get('level', 'unknown')
            performance_counts[perf_level] = performance_counts.get(perf_level, 0) + 1
    
    if performance_counts:
        fig_pie = px.pie(
            values=list(performance_counts.values()),
            names=list(performance_counts.keys()),
            title=f"Distribúcia výkonnosti - {city.title()}"
        )
        st.plotly_chart(fig_pie, use_container_width=True)


def render_goals_management(kpi_manager: KPIManager):
    """Správa cieľov (len admin)"""
    
    st.markdown("### 🎯 Správa cieľov")
    
    goals = kpi_manager.load_goals()
    
    # Globálne ciele
    st.markdown("#### 🌍 Globálne ciele")
    
    global_targets = goals.get('global_targets', {}).get('2025', {})
    
    for period, targets in global_targets.items():
        with st.expander(f"📅 {period.upper()} - Ciele"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_sales = st.number_input(
                    f"💰 Predaj {period.upper()} (Kč):",
                    value=targets.get('sales', 0),
                    key=f"sales_{period}"
                )
            
            with col2:
                new_activity = st.number_input(
                    f"📊 Aktivita {period.upper()} (body):",
                    value=targets.get('activity_score', 80),
                    key=f"activity_{period}"
                )
            
            if st.button(f"💾 Uložiť {period.upper()}", key=f"save_{period}"):
                goals['global_targets']['2025'][period]['sales'] = new_sales
                goals['global_targets']['2025'][period]['activity_score'] = new_activity
                kpi_manager.save_goals(goals)
                st.success(f"✅ Ciele pre {period.upper()} uložené")
                st.rerun()


def render_admin_analytics(kpi_manager: KPIManager):
    """Admin analytické pohľady"""
    
    st.markdown("### 📈 Pokročilé analýzy")
    st.info("🚧 Pokročilé analytické funkcie budú pridané v ďalšej verzii")


def render_system_config(kpi_manager: KPIManager):
    """Konfigurácia systému"""
    
    st.markdown("### ⚙️ Konfigurácia systému")
    
    metrics_config = kpi_manager.load_metrics_config()
    
    st.markdown("#### 📊 Aktívne metriky")
    
    for metric_key, metric_config in metrics_config['active_metrics'].items():
        with st.expander(f"{metric_config['icon']} {metric_config['name']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                enabled = st.checkbox(
                    "Aktívna",
                    value=metric_config['enabled'],
                    key=f"enabled_{metric_key}"
                )
            
            with col2:
                weight = st.number_input(
                    "Váha (%)",
                    value=metric_config['weight'],
                    min_value=0,
                    max_value=100,
                    key=f"weight_{metric_key}"
                )
            
            with col3:
                if metric_config.get('note'):
                    st.info(metric_config['note'])
            
            # Možnosť uloženia zmien sa pridá neskôr


if __name__ == "__main__":
    render()
