"""
Benchmark stránka - ranking zamestnancov s pokročilým dizajnom a konkrétnymi obdobiami
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import calendar


def render(analyzer):
    """Benchmark stránka s anti-pink CSS a konkrétnymi obdobiami"""
    
    # ✅ ANTI-PINK CSS OVERRIDE pre benchmark
    st.markdown("""
    <style>
    /* BENCHMARK SPECIFIC ANTI-PINK */
    button, .stButton > button {
        background-color: #262730 !important;
        color: white !important;
        border: 1px solid #4a4a4a !important;
    }
    
    button:hover, .stButton > button:hover,
    button:focus, .stButton > button:focus,
    button:active, .stButton > button:active {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        border-color: #2563eb !important;
        color: white !important;
        outline: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Kontrola analyzera
    if analyzer is None:
        st.error("❌ Dáta nie sú načítané. Prejdite najskôr na Overview stránku.")
        return
    
    # ✅ NOVÉ - Role-based filtering pre benchmark dáta
    from auth.auth import get_current_user
    user = get_current_user()
    
    if user and user.get('role') != 'admin':
        # Manager - aplikuj city filtering
        user_cities = user.get('cities', [])
        
        # Filtruj len zamestnancov z povolených miest
        try:
            original_employees = analyzer.get_all_employees_summary()
            filtered_employees = []
            
            for emp in original_employees:
                emp_workplace = emp.get('workplace', '').lower()
                if any(city.lower() in emp_workplace or emp_workplace in city.lower() for city in user_cities):
                    filtered_employees.append(emp)
            
            # Ak nemáme filtered employees, použijeme pôvodných (fallback)
            employees_summary = filtered_employees if filtered_employees else original_employees
            
            if filtered_employees:
                st.success(f"🔒 **Filtrované dáta** - Zobrazujú sa len zamestnanci z miest: {', '.join([c.title() for c in user_cities])}")
                st.info(f"👥 **Nájdených zamestnancov**: {len(filtered_employees)} z celkových {len(original_employees)}")
            else:
                st.warning(f"⚠️ **Žiadni zamestnanci** z vašich miest ({', '.join([c.title() for c in user_cities])}) neboli nájdení.")
                
        except Exception as e:
            st.error(f"❌ Chyba pri filtrovaní podľa miest: {e}")
            employees_summary = analyzer.get_all_employees_summary()
    else:
        # Admin vidí všetkých zamestnancov
        employees_summary = analyzer.get_all_employees_summary()
        st.success("👑 **Admin prístup** - Zobrazujú sa všetky dáta")
    
    if not employees_summary:
        st.error("❌ Žiadni zamestnanci neboli nájdení.")
        return
    
    # ✅ ROZŠÍRENÉ CIELE S KONKRÉTNYMI OBDOBIAMI
    TARGETS = {
        # Štvrťroky
        "q1": 2_000_000,    # Q1: Január-Marec
        "q2": 2_000_000,    # Q2: Apríl-Jún
        "q3": 2_000_000,    # Q3: Júl-September
        "q4": 2_000_000,    # Q4: Október-December
        
        # Polroky
        "h1": 5_000_000,    # H1: Január-Jún
        "h2": 5_000_000,    # H2: Júl-December
        
        # Celý rok
        "year": 12_000_000, # Celý rok
    }
    
    # ✅ HLAVNÝ CONTROL PANEL S NOVÝMI MOŽNOSŤAMI
    st.markdown("## 🎛️ Hlavné Nastavenia")
    
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            main_period = st.selectbox(
                "🎯 Hlavné obdobie pre prehľad:",
                ["q1", "q2", "q3", "q4", "h1", "h2", "year"],
                format_func=lambda x: {
                    "q1": f"🌱 Q1 - Január-Marec (Cieľ: {TARGETS['q1']:,} Kč)",
                    "q2": f"🌞 Q2 - Apríl-Jún (Cieľ: {TARGETS['q2']:,} Kč)",
                    "q3": f"🍂 Q3 - Júl-September (Cieľ: {TARGETS['q3']:,} Kč)",
                    "q4": f"❄️ Q4 - Október-December (Cieľ: {TARGETS['q4']:,} Kč)",
                    "h1": f"🌸 H1 - Január-Jún (Cieľ: {TARGETS['h1']:,} Kč)",
                    "h2": f"🍁 H2 - Júl-December (Cieľ: {TARGETS['h2']:,} Kč)",
                    "year": f"🎯 Celý rok (Cieľ: {TARGETS['year']:,} Kč)"
                }[x],
                key="main_period"
            )
        
        with col2:
            main_target = TARGETS[main_period]
            period_labels = {
                "q1": "Q1 (Jan-Mar)",
                "q2": "Q2 (Apr-Jún)",
                "q3": "Q3 (Júl-Sep)",
                "q4": "Q4 (Okt-Dec)",
                "h1": "H1 (Jan-Jún)",
                "h2": "H2 (Júl-Dec)",
                "year": "Celý rok"
            }
            st.metric(
                label=f"🎯 {period_labels[main_period]}",
                value=f"{main_target:,} Kč"
            )
        
        with col3:
            if st.button("📊 Zobraziť štatistiky", use_container_width=True):
                st.session_state.show_main_stats = not st.session_state.get('show_main_stats', False)
    
    # ✅ VÝPOČET S NOVÝMI OBDOBIAMI
    main_benchmark_data = calculate_benchmark_data(employees_summary, main_target, main_period)
    
    # ✅ EXPANDABLE HLAVNÉ ŠTATISTIKY
    if st.session_state.get('show_main_stats', False):
        with st.expander("📊 Detailné štatistiky hlavného prehľadu", expanded=True):
            display_main_statistics(main_benchmark_data, main_target, main_period)
    
    st.markdown("---")
    
    # ✅ TOP PERFORMERS SEKCIA
    st.markdown("## 🏆 Top Performers")
    
    tab1, tab2, tab3 = st.tabs(["📊 Top 10 Graf", "🥇 Podium", "📈 Trending"])
    
    with tab1:
        display_top10_chart(main_benchmark_data, main_target, main_period)
    
    with tab2:
        display_podium(main_benchmark_data, main_target)
    
    with tab3:
        display_trending_analysis(main_benchmark_data, main_target)
    
    st.markdown("---")
    
    # ✅ POKROČILÝ RANKING PANEL
    st.markdown("## 📋 Pokročilý Ranking")
    
    # Ranking control panel s krásnym dizajnom
    with st.container():
        st.markdown("### ⚙️ Nastavenia Rankingu")
        st.markdown("*Nezávislé nastavenia pre detailný ranking - môže byť iné ako hlavný prehľad*")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            ranking_period = st.selectbox(
                "🎯 Obdobie pre ranking:",
                ["q1", "q2", "q3", "q4", "h1", "h2", "year"],
                format_func=lambda x: period_labels[x],
                index=["q1", "q2", "q3", "q4", "h1", "h2", "year"].index(main_period),
                key="ranking_period_selector"
            )
        
        with col2:
            workplace_filter = st.selectbox(
                "🏢 Pracovisko:",
                ["Všetky"] + list(set([emp['workplace'] for emp in employees_summary])),
                key="ranking_workplace_filter"
            )
        
        with col3:
            performance_filter = st.selectbox(
                "📈 Výkon:",
                ["Všetky", "🏆 Cieľ splnený", "🥉 Blízko k cieľu", "⚠️ Podpriemerný", "❌ Kritický"],
                key="ranking_performance_filter"
            )
        
        with col4:
            show_count = st.selectbox(
                "📊 Zobraziť:",
                [10, 20, 50, "Všetkých"],
                format_func=lambda x: f"Top {x}" if x != "Všetkých" else "Všetkých",
                index=1,  # Default 20
                key="ranking_count"
            )
    
    # Ranking target a prepočítanie
    ranking_target = TARGETS[ranking_period]
    ranking_data = calculate_benchmark_data(employees_summary, ranking_target, ranking_period)
    
    # ✅ RANKING INFO PANEL
    display_ranking_info_panel(ranking_data, ranking_target, ranking_period, main_period)
    
    # ✅ APLIKOVANIE FILTROV
    filtered_ranking = apply_ranking_filters(
        ranking_data, workplace_filter, performance_filter, show_count
    )
    
    # ✅ KRÁSNE ZOBRAZENIE RANKINGU
    if filtered_ranking:
        display_beautiful_ranking(filtered_ranking, ranking_target, ranking_period)
    else:
        st.info("ℹ️ Žiadni zamestnanci nevyhovujú zvoleným filtrom.")
    
    st.markdown("---")
    
    # ✅ ANALÝZY A INSIGHTS
    st.markdown("## 📊 Analýzy a Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        display_performance_distribution(ranking_data, ranking_period)
    
    with col2:
        display_workplace_analysis(ranking_data)
    
    st.markdown("---")
    
    # ✅ EXPORT A AKCIE
    st.markdown("## 💾 Export a Akcie")
    display_export_section(ranking_data, ranking_target, ranking_period)


def calculate_benchmark_data(employees_summary, target, period):
    """✅ Vypočíta benchmark dáta pre konkrétne obdobia v roku"""
    benchmark_data = []
    
    for emp in employees_summary:
        name = emp.get('name', 'Unknown')
        total_sales = emp.get('total_sales', 0)
        monthly_sales = emp.get('monthly_sales', {})
        workplace = emp.get('workplace', 'unknown')
        score = emp.get('score', 0)
        
        # ✅ NOVÝ VÝPOČET: Konkrétne obdobia namiesto "posledných N mesiacov"
        period_sales = calculate_specific_period_sales(monthly_sales, period)
        
        # Výpočet progress na základe obdobia
        progress = (period_sales / target) * 100 if target > 0 else 0
        
        # Klasifikácia výkonu
        if progress >= 100:
            performance = "🏆 Cieľ splnený"
            color = "#28a745"
            tier = "excellent"
        elif progress >= 75:
            performance = "🥉 Blízko k cieľu"
            color = "#ffc107"
            tier = "good"
        elif progress >= 50:
            performance = "⚠️ Podpriemerný"
            color = "#17a2b8"
            tier = "average"
        else:
            performance = "❌ Kritický"
            color = "#dc3545"
            tier = "poor"
        
        benchmark_data.append({
            'name': name,
            'total_sales': total_sales,
            'period_sales': period_sales,
            'progress': progress,
            'performance': performance,
            'color': color,
            'tier': tier,
            'workplace': workplace,
            'score': score,
            'monthly_sales': monthly_sales,
            'to_target': max(0, target - period_sales),
            'target': target,
            'period': period
        })
    
    # Zoradenie podľa predaja za obdobie
    benchmark_data.sort(key=lambda x: x['period_sales'], reverse=True)
    for i, emp in enumerate(benchmark_data):
        emp['position'] = i + 1
        emp['medal'] = get_medal(i + 1)
    
    return benchmark_data


def calculate_specific_period_sales(monthly_sales, period):
    """✅ Vypočíta predaj pre konkrétne obdobia v roku"""
    
    if not monthly_sales:
        return 0
    
    # Definícia konkrétnych období
    period_definitions = {
        # Štvrťroky
        "q1": ['leden', 'unor', 'brezen'],           # Q1: jan-mar
        "q2": ['duben', 'kveten', 'cerven'],         # Q2: apr-jun  
        "q3": ['cervenec', 'srpen', 'zari'],         # Q3: jul-sep
        "q4": ['rijen', 'listopad', 'prosinec'],     # Q4: oct-dec
        
        # Polroky
        "h1": ['leden', 'unor', 'brezen', 'duben', 'kveten', 'cerven'],           # H1: jan-jun
        "h2": ['cervenec', 'srpen', 'zari', 'rijen', 'listopad', 'prosinec'],    # H2: jul-dec
        
        # Celý rok
        "year": ['leden', 'unor', 'brezen', 'duben', 'kveten', 'cerven', 
                'cervenec', 'srpen', 'zari', 'rijen', 'listopad', 'prosinec'],
    }
    
    # Získaj mesiace pre dané obdobie
    months_to_sum = period_definitions.get(period, ['leden', 'unor', 'brezen'])
    
    # Spočítaj predaj za dané mesiace
    period_sales = 0
    for month in months_to_sum:
        if month in monthly_sales:
            try:
                # Ošetrenie pre X hodnoty
                value = monthly_sales[month]
                if isinstance(value, str) and value.upper() in ['X']:
                    continue
                period_sales += float(value) if value else 0
            except (ValueError, TypeError):
                continue
    
    return period_sales


def get_medal(position):
    """Vráti medailu na základe pozície"""
    if position == 1:
        return "🥇"
    elif position == 2:
        return "🥈"
    elif position == 3:
        return "🥉"
    elif position <= 10:
        return "🏅"
    else:
        return f"#{position}"


def display_main_statistics(benchmark_data, target, period):
    """Zobrazí hlavné štatistiky s novými názvami období"""
    
    total_employees = len(benchmark_data)
    achieved_target = len([emp for emp in benchmark_data if emp['progress'] >= 100])
    avg_progress = sum([emp['progress'] for emp in benchmark_data]) / total_employees if total_employees > 0 else 0
    total_sales = sum([emp['period_sales'] for emp in benchmark_data])
    top_performer = benchmark_data[0] if benchmark_data else None
    
    # Informácie o období
    period_info = {
        "q1": "prvý štvrťrok (január-marec)",
        "q2": "druhý štvrťrok (apríl-jún)",
        "q3": "tretí štvrťrok (júl-september)",
        "q4": "štvrtý štvrťrok (október-december)",
        "h1": "prvý polrok (január-jún)",
        "h2": "druhý polrok (júl-december)",
        "year": "celý rok"
    }
    
    st.info(f"📅 **Obdobie**: {period_info[period]} | **Cieľ**: {target:,} Kč")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="👥 Zamestnanci",
            value=total_employees,
            help="Celkový počet hodnotených zamestnancov"
        )
    
    with col2:
        st.metric(
            label="🏆 Splnili cieľ", 
            value=f"{achieved_target}/{total_employees}",
            delta=f"{(achieved_target/total_employees*100):.1f}%" if total_employees > 0 else "0%",
            help=f"Počet zamestnancov ktorí dosiahli cieľ za {period_info[period]}"
        )
    
    with col3:
        st.metric(
            label="📊 Priemerný pokrok",
            value=f"{avg_progress:.1f}%",
            help="Priemerný pokrok všetkých zamestnancov ku cieľu"
        )
    
    with col4:
        st.metric(
            label="💰 Celkový predaj",
            value=f"{total_sales:,.0f} Kč",
            help=f"Súčet predaja všetkých zamestnancov za {period_info[period]}"
        )
    
    with col5:
        if top_performer:
            st.metric(
                label="🥇 TOP Performer",
                value=top_performer['name'],
                delta=f"{top_performer['period_sales']:,} Kč",
                help=f"Najlepší zamestnanec za {period_info[period]}"
            )


def display_top10_chart(benchmark_data, target, period):
    """Zobrazí TOP 10 graf s novými názvami období"""
    
    top_10 = benchmark_data[:10]
    
    if not top_10:
        st.warning("Žiadni zamestnanci na zobrazenie.")
        return
    
    names = [emp['name'] for emp in top_10]
    sales = [emp['period_sales'] for emp in top_10]
    colors = [emp['color'] for emp in top_10]
    
    # Vytvorenie grafu
    fig = go.Figure()
    
    # Stĺpce
    fig.add_trace(go.Bar(
        x=names,
        y=sales,
        marker_color=colors,
        text=[f"{s:,.0f} Kč<br>{((s/target)*100):.1f}%<br>{get_medal(i+1)}" for i, s in enumerate(sales)],
        textposition='auto',
        name="Predaj",
        hovertemplate="<b>%{x}</b><br>Predaj: %{y:,.0f} Kč<br>Pokrok: %{customdata:.1f}%<extra></extra>",
        customdata=[(s/target)*100 for s in sales]
    ))
    
    # Cieľová čiara
    fig.add_hline(
        y=target,
        line_dash="dash",
        line_color="red",
        line_width=3,
        annotation_text=f"🎯 Cieľ: {target:,} Kč",
        annotation_position="top right",
        annotation=dict(font=dict(size=14, color="red"))
    )
    
    period_labels = {
        "q1": "Q1 (Január-Marec)",
        "q2": "Q2 (Apríl-Jún)", 
        "q3": "Q3 (Júl-September)",
        "q4": "Q4 (Október-December)",
        "h1": "H1 (Január-Jún)",
        "h2": "H2 (Júl-December)",
        "year": "Celý rok"
    }
    
    fig.update_layout(
        title=dict(
            text=f"🏆 TOP 10 - {period_labels[period]} (Cieľ: {target:,} Kč)",
            x=0.5,
            font=dict(size=20)
        ),
        xaxis_title="Zamestnanci",
        yaxis_title="Predaj (Kč)",
        showlegend=False,
        height=600,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_podium(benchmark_data, target):
    """Zobrazí podium s top 3"""
    
    if len(benchmark_data) < 3:
        st.warning("Nedostatok dát pre podium.")
        return
    
    st.markdown("### 🏆 Podium - Top 3")
    
    # Podium layout
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    # 2. miesto (ľavé)
    with col1:
        emp = benchmark_data[1]
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(145deg, #f0f0f0, #d0d0d0); border-radius: 10px; height: 200px;">
            <div style="font-size: 3rem;">🥈</div>
            <div style="font-size: 1.2rem; font-weight: bold;">{emp['name']}</div>
            <div style="font-size: 1rem; color: #666;">{emp['workplace']}</div>
            <div style="font-size: 1.1rem; color: #333; margin-top: 0.5rem;">{emp['period_sales']:,} Kč</div>
            <div style="font-size: 0.9rem; color: #777;">{emp['progress']:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 1. miesto (stred, vyššie)
    with col2:
        emp = benchmark_data[0]
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(145deg, #ffd700, #ffed4e); border-radius: 10px; height: 250px; margin-top: -25px;">
            <div style="font-size: 4rem;">🥇</div>
            <div style="font-size: 1.4rem; font-weight: bold;">{emp['name']}</div>
            <div style="font-size: 1.1rem; color: #444;">{emp['workplace']}</div>
            <div style="font-size: 1.3rem; color: #333; margin-top: 0.5rem; font-weight: bold;">{emp['period_sales']:,} Kč</div>
            <div style="font-size: 1rem; color: #555;">{emp['progress']:.1f}%</div>
            <div style="font-size: 0.8rem; color: #666; margin-top: 0.5rem;">👑 VÍŤAZ</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 3. miesto (pravé)
    with col3:
        emp = benchmark_data[2]
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(145deg, #cd7f32, #deb887); border-radius: 10px; height: 200px;">
            <div style="font-size: 3rem;">🥉</div>
            <div style="font-size: 1.2rem; font-weight: bold;">{emp['name']}</div>
            <div style="font-size: 1rem; color: #666;">{emp['workplace']}</div>
            <div style="font-size: 1.1rem; color: #333; margin-top: 0.5rem;">{emp['period_sales']:,} Kč</div>
            <div style="font-size: 0.9rem; color: #777;">{emp['progress']:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)


def display_trending_analysis(benchmark_data, target):
    """Zobrazí trending analýzu"""
    
    st.markdown("### 📈 Analýza Trendov")
    
    # Rozdelenie do kategórií
    tiers = {
        "excellent": [emp for emp in benchmark_data if emp['tier'] == 'excellent'],
        "good": [emp for emp in benchmark_data if emp['tier'] == 'good'],
        "average": [emp for emp in benchmark_data if emp['tier'] == 'average'],
        "poor": [emp for emp in benchmark_data if emp['tier'] == 'poor']
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 Distribúcia výkonu:**")
        for tier_name, tier_data in tiers.items():
            count = len(tier_data)
            percentage = (count / len(benchmark_data)) * 100 if benchmark_data else 0
            
            tier_labels = {
                "excellent": "🏆 Excelentní",
                "good": "🥉 Dobrí", 
                "average": "⚠️ Priemerni",
                "poor": "❌ Slabí"
            }
            
            st.metric(
                label=tier_labels[tier_name],
                value=f"{count} ({percentage:.1f}%)"
            )
    
    with col2:
        st.markdown("**🎯 Insights:**")
        
        avg_sales = sum([emp['period_sales'] for emp in benchmark_data]) / len(benchmark_data)
        median_sales = sorted([emp['period_sales'] for emp in benchmark_data])[len(benchmark_data)//2]
        gap_to_target = sum([emp['to_target'] for emp in benchmark_data])
        
        st.write(f"• Priemerný predaj: **{avg_sales:,.0f} Kč**")
        st.write(f"• Medián predaja: **{median_sales:,.0f} Kč**")
        st.write(f"• Celková medzera k cieľu: **{gap_to_target:,.0f} Kč**")
        
        if len(tiers["excellent"]) > 0:
            top_workplace = max(set([emp['workplace'] for emp in tiers["excellent"]]), 
                              key=lambda x: len([emp for emp in tiers["excellent"] if emp['workplace'] == x]))
            st.write(f"• Najlepšie pracovisko: **{top_workplace}**")


def display_ranking_info_panel(ranking_data, ranking_target, ranking_period, main_period):
    """Zobrazí info panel pre ranking"""
    
    period_info = {
        "q1": "Q1 (jan-mar)",
        "q2": "Q2 (apr-jún)",
        "q3": "Q3 (júl-sep)",
        "q4": "Q4 (okt-dec)",
        "h1": "H1 (jan-jún)",
        "h2": "H2 (júl-dec)",
        "year": "celý rok"
    }
    
    # Porovnanie s hlavným nastavením
    if ranking_period != main_period:
        st.info(f"ℹ️ Ranking používa iný cieľ než hlavný prehľad: **{ranking_target:,} Kč** za {period_info[ranking_period]}")
    
    # Metrics panel
    col1, col2, col3, col4 = st.columns(4)
    
    success_count = len([emp for emp in ranking_data if emp['progress'] >= 100])
    avg_progress = sum([emp['progress'] for emp in ranking_data]) / len(ranking_data)
    total_gap = sum([emp['to_target'] for emp in ranking_data])
    
    with col1:
        st.metric("🎯 Cieľ", f"{ranking_target:,} Kč")
    
    with col2:
        st.metric("✅ Splnili", f"{success_count}/{len(ranking_data)}")
    
    with col3:
        st.metric("📊 Avg pokrok", f"{avg_progress:.1f}%")
    
    with col4:
        st.metric("📉 Celková medzera", f"{total_gap:,.0f} Kč")


def apply_ranking_filters(ranking_data, workplace_filter, performance_filter, show_count):
    """Aplikuje filtre na ranking dáta"""
    
    filtered = []
    
    for emp in ranking_data:
        # Workplace filter
        if workplace_filter != "Všetky" and emp['workplace'] != workplace_filter:
            continue
        
        # Performance filter
        if performance_filter != "Všetky" and emp['performance'] != performance_filter:
            continue
        
        filtered.append(emp)
    
    # Limit count
    if show_count != "Všetkých":
        filtered = filtered[:show_count]
    
    return filtered


def display_beautiful_ranking(filtered_ranking, ranking_target, ranking_period):
    """Zobrazí krásny ranking s natívnym Streamlit styling"""
    
    period_info = {
        "q1": "prvý štvrťrok (január-marec)",
        "q2": "druhý štvrťrok (apríl-jún)",
        "q3": "tretí štvrťrok (júl-september)",
        "q4": "štvrtý štvrťrok (október-december)",
        "h1": "prvý polrok (január-jún)",
        "h2": "druhý polrok (júl-december)",
        "year": "celý rok"
    }
    
    st.markdown("### 🏆 Ranking Tabuľka")
    st.markdown(f"*Klasifikácia pre **{period_info[ranking_period]}** (cieľ: {ranking_target:,} Kč)*")
    
    # Rozdelenie na kategórie
    categories = {
        "🏆 Cieľ splnený": [emp for emp in filtered_ranking if "🏆" in emp['performance']],
        "🥉 Blízko k cieľu": [emp for emp in filtered_ranking if "🥉" in emp['performance']],
        "⚠️ Podpriemerný": [emp for emp in filtered_ranking if "⚠️" in emp['performance']],
        "❌ Kritický": [emp for emp in filtered_ranking if "❌" in emp['performance']]
    }
    
    # Zobrazenie každej kategórie
    for category_name, category_data in categories.items():
        if not category_data:
            continue
        
        with st.expander(f"{category_name} ({len(category_data)} ľudí)", expanded=True):
            
            # Tabuľka pre kategóriu
            table_data = []
            for emp in category_data:
                table_data.append({
                    "🏅 Pozícia": emp['medal'],
                    "👤 Meno": emp['name'],
                    "🏢 Pracovisko": emp['workplace'],
                    "💰 Predaj (obdobie)": f"{emp['period_sales']:,} Kč",
                    "📊 Pokrok": f"{emp['progress']:.1f}%",
                    "🎯 Do cieľa": f"{emp['to_target']:,} Kč" if emp['to_target'] > 0 else "✅ Splnené",
                    "⭐ Skóre": f"{emp['score']:.1f}%",
                    "📅 Celkom (info)": f"{emp['total_sales']:,} Kč"
                })
            
            df_category = pd.DataFrame(table_data)
            st.dataframe(df_category, use_container_width=True, hide_index=True)
            
            # Top 3 v kategórii
            if len(category_data) > 0:
                st.markdown("**🏅 Najlepší v kategórii:**")
                
                cols = st.columns(min(3, len(category_data)))
                for i, (col, emp) in enumerate(zip(cols, category_data[:3])):
                    with col:
                        medal = ["🥇", "🥈", "🥉"][i]
                        delta_text = f"-{emp['to_target']:,} Kč" if emp['to_target'] > 0 else "✅ Cieľ splnený!"
                        
                        st.metric(
                            label=f"{medal} {emp['name']}",
                            value=f"{emp['period_sales']:,} Kč",
                            delta=delta_text,
                            delta_color="inverse" if emp['to_target'] > 0 else "normal"
                        )


def display_performance_distribution(ranking_data, ranking_period):
    """Zobrazí distribúciu výkonu"""
    
    st.markdown("### 📊 Distribúcia Výkonu")
    
    # Príprava dát pre pie chart
    performance_counts = {}
    for emp in ranking_data:
        perf = emp['performance']
        performance_counts[perf] = performance_counts.get(perf, 0) + 1
    
    if performance_counts:
        period_labels = {
            "q1": "Q1",
            "q2": "Q2",
            "q3": "Q3",
            "q4": "Q4",
            "h1": "H1",
            "h2": "H2",
            "year": "Rok"
        }
        
        fig_pie = px.pie(
            values=list(performance_counts.values()),
            names=list(performance_counts.keys()),
            title=f"Výkon - {period_labels[ranking_period]}",
            color_discrete_map={
                "🏆 Cieľ splnený": "#28a745",
                "🥉 Blízko k cieľu": "#ffc107", 
                "⚠️ Podpriemerný": "#17a2b8",
                "❌ Kritický": "#dc3545"
            },
            height=400
        )
        
        fig_pie.update_layout(
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5)
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)


def display_workplace_analysis(ranking_data):
    """Zobrazí analýzu pracovísk"""
    
    st.markdown("### 🏢 Analýza Pracovísk")
    
    # Výpočet štatistík pre pracoviska
    workplace_stats = {}
    
    for emp in ranking_data:
        workplace = emp['workplace']
        if workplace not in workplace_stats:
            workplace_stats[workplace] = {
                'count': 0,
                'total_sales': 0,
                'avg_progress': 0,
                'successful': 0
            }
        
        workplace_stats[workplace]['count'] += 1
        workplace_stats[workplace]['total_sales'] += emp['period_sales']
        workplace_stats[workplace]['avg_progress'] += emp['progress']
        if emp['progress'] >= 100:
            workplace_stats[workplace]['successful'] += 1
    
    # Výpočet priemerných hodnôt
    for workplace in workplace_stats:
        count = workplace_stats[workplace]['count']
        workplace_stats[workplace]['avg_progress'] /= count
        workplace_stats[workplace]['avg_sales'] = workplace_stats[workplace]['total_sales'] / count
        workplace_stats[workplace]['success_rate'] = (workplace_stats[workplace]['successful'] / count) * 100
    
    # Zobrazenie tabuľky
    workplace_table = []
    for workplace, stats in workplace_stats.items():
        workplace_table.append({
            "🏢 Pracovisko": workplace.title(),
            "👥 Počet": stats['count'],
            "💰 Avg predaj": f"{stats['avg_sales']:,.0f} Kč",
            "📊 Avg pokrok": f"{stats['avg_progress']:.1f}%",
            "✅ Úspešnosť": f"{stats['success_rate']:.1f}%"
        })
    
    df_workplace = pd.DataFrame(workplace_table)
    df_workplace = df_workplace.sort_values("✅ Úspešnosť", ascending=False)
    
    st.dataframe(df_workplace, use_container_width=True, hide_index=True)


def display_export_section(ranking_data, ranking_target, ranking_period):
    """Zobrazí export sekciu"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📥 CSV Export", use_container_width=True):
            csv_data = []
            for emp in ranking_data:
                csv_data.append({
                    "Pozícia": emp['position'],
                    "Meno": emp['name'],
                    "Pracovisko": emp['workplace'],
                    "Predaj_za_obdobie_Kč": emp['period_sales'],
                    "Celkový_predaj_Kč": emp['total_sales'],
                    "Cieľ_Kč": ranking_target,
                    "Pokrok_%": round(emp['progress'], 2),
                    "Výkon": emp['performance'],
                    "Skóre_%": emp['score'],
                    "Do_cieľa_Kč": emp['to_target'],
                    "Obdobie": ranking_period
                })
            
            csv_df = pd.DataFrame(csv_data)
            csv_string = csv_df.to_csv(index=False, encoding='utf-8')
            
            st.download_button(
                label="💾 Stiahnuť CSV",
                data=csv_string,
                file_name=f"benchmark_{ranking_period}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("🔄 Obnoviť", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.button("📊 Prehľad", use_container_width=True):
            st.session_state.current_page = 'overview'
            st.rerun()
    
    with col4:
        if st.button("📈 Heatmapa", use_container_width=True):
            st.session_state.current_page = 'heatmap'
            st.rerun()
