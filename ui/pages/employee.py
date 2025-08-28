# ui/pages/employee.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from core.utils import format_money, time_to_minutes
from ui.styling import get_dark_plotly_layout, get_dark_plotly_title_style


def render(analyzer, selected_employee):
    """Nový detailný view zamestnanca s PROFESIONÁLNYMI grafmi"""
    
    # 🔍 DEBUG INFO (dočasne zobrazené)
    with st.expander("🔧 Debug informácie", expanded=False):
        st.write(f"🔍 DEBUG: selected_employee = '{selected_employee}'")
        st.write(f"🔍 DEBUG: analyzer má {len(analyzer.sales_employees)} zamestnancov")
        st.write(f"🔍 DEBUG: Prvých 5 mien: {[emp.get('name') for emp in analyzer.sales_employees[:5]]}")
    
    # ✨ PROFESIONÁLNY HEADER
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #1e40af 100%);
        padding: 2rem 1.5rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
    ">
        <h1 style="
            color: white; 
            text-align: center; 
            margin: 0; 
            font-size: 2.5rem;
            font-weight: 700;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        ">
            👤 {selected_employee}
        </h1>
        <p style="
            color: rgba(255, 255, 255, 0.9); 
            text-align: center; 
            margin: 10px 0 0 0; 
            font-size: 1.1rem;
            font-weight: 300;
        ">
            Komplexná analýza výkonnosti a produktivity
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # ✅ ZÍSKANIE SKUTOČNÝCH DÁT Z ANALYZÁTORA
    employee_data = None
    for emp in analyzer.sales_employees:
        if emp.get('name') == selected_employee:
            employee_data = emp
            break
    
    if not employee_data:
        st.error(f"❌ Zamestnanec '{selected_employee}' nebol nájdený!")
        return
    
    # ✅ PROFESIONÁLNE ZÁKLADNÉ INFORMÁCIE
    monthly_sales = employee_data.get('monthly_sales', {})
    total_sales = sum(monthly_sales.values()) if monthly_sales else 0
    workplace = employee_data.get('workplace', 'Neznáme')
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #10b981, #059669);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
        ">
            <h3 style="margin: 0 0 10px 0; font-size: 0.9rem; opacity: 0.9;">💰 CELKOVÝ PREDAJ</h3>
            <h2 style="margin: 0; font-size: 1.4rem; font-weight: bold;">{total_sales:,.0f} Kč</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_monthly = total_sales / 12 if total_sales > 0 else 0
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        ">
            <h3 style="margin: 0 0 10px 0; font-size: 0.9rem; opacity: 0.9;">📊 MESAČNÝ PRIEMER</h3>
            <h2 style="margin: 0; font-size: 1.4rem; font-weight: bold;">{avg_monthly:,.0f} Kč</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #8b5cf6, #7c3aed);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
        ">
            <h3 style="margin: 0 0 10px 0; font-size: 0.9rem; opacity: 0.9;">🏢 PRACOVISKO</h3>
            <h2 style="margin: 0; font-size: 1.4rem; font-weight: bold;">{workplace.title()}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Výpočet výkonnostného skóre
        performance_score = min(100, (total_sales / 2000000) * 100) if total_sales > 0 else 0
        score_color = '#10b981' if performance_score >= 80 else '#f59e0b' if performance_score >= 60 else '#ef4444'
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {score_color}, {score_color}dd);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
        ">
            <h3 style="margin: 0 0 10px 0; font-size: 0.9rem; opacity: 0.9;">⭐ VÝKONNOSŤ</h3>
            <h2 style="margin: 0; font-size: 1.4rem; font-weight: bold;">{performance_score:.0f}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # ✅ ZÍSKANIE SKUTOČNÝCH INTERNET A APLIKAČNÝCH DÁT
    internet_data = get_employee_internet_data(analyzer, selected_employee)
    app_data = get_employee_application_data(analyzer, selected_employee)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ✅ PROFESIONÁLNE GRAFY S LEPŠÍM SPACINGOM
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.95), rgba(31, 41, 55, 0.95));
        padding: 2rem;
        border-radius: 15px;
        margin: 1.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
    ">
    """, unsafe_allow_html=True)
    
    # ✅ MESAČNÝ PREDAJ GRAF - VYLEPŠENÝ
    create_monthly_sales_chart(monthly_sales)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.95), rgba(31, 41, 55, 0.95));
        padding: 2rem;
        border-radius: 15px;
        margin: 1.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
    ">
    """, unsafe_allow_html=True)
    
    # ✅ ANALÝZA INTERNET AKTIVÍT - VYLEPŠENÁ
    create_internet_analysis(internet_data, selected_employee)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.95), rgba(31, 41, 55, 0.95));
        padding: 2rem;
        border-radius: 15px;
        margin: 1.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
    ">
    """, unsafe_allow_html=True)
    
    # ✅ ANALÝZA APLIKÁCIÍ - VYLEPŠENÁ  
    create_application_analysis(app_data, selected_employee)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(17, 24, 39, 0.95), rgba(31, 41, 55, 0.95));
        padding: 2rem;
        border-radius: 15px;
        margin: 1.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
    ">
    """, unsafe_allow_html=True)
    
    # ✅ POKROČILÉ POROVNANIA AKTIVÍT PROTI PREDAJU
    create_productivity_comparisons(internet_data, app_data, total_sales, selected_employee)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ✅ PRIDANIE DETAILNEJ TABUĽKY NA KONCI
    with st.expander("📋 Detailné dátové tabuľky", expanded=False):
        if not monthly_sales:
            st.warning("Žiadne mesačné predajné dáta")
        else:
            st.markdown("#### 💰 Mesačný predaj")
            monthly_df = pd.DataFrame([
                {"Mesiac": k, "Predaj (Kč)": f"{v:,.0f}", "Podiel (%)": f"{(v/sum(monthly_sales.values())*100):.1f}%"} 
                for k, v in monthly_sales.items() if v > 0
            ])
            st.dataframe(monthly_df, use_container_width=True)
        
        if internet_data is not None and not internet_data.empty:
            st.markdown("#### 🌐 Internet aktivity")
            st.dataframe(internet_data.head(10), use_container_width=True)
        
        if app_data is not None and not app_data.empty:
            st.markdown("#### 💻 Aplikačné aktivity")
            st.dataframe(app_data.head(10), use_container_width=True)


def get_employee_internet_data(analyzer, employee_name):
    """Získa SKUTOČNÉ internet dáta pre zamestnanca"""
    
    if not hasattr(analyzer, 'internet_data') or analyzer.internet_data is None:
        return None
    
    # Hľadanie matchujúcich mien (rovnaká logika ako v analyzátore)
    matching_names = analyzer.find_matching_names(employee_name, analyzer.internet_data)
    
    if not matching_names:
        return None
    
    # Filtruj dáta pre tohto zamestnanca
    employee_internet = analyzer.internet_data[
        analyzer.internet_data['Osoba ▲'].isin(matching_names)
    ]
    
    return employee_internet


def get_employee_application_data(analyzer, employee_name):
    """Získa SKUTOČNÉ aplikačné dáta pre zamestnanca"""
    
    if not hasattr(analyzer, 'applications_data') or analyzer.applications_data is None:
        return None
    
    # Hľadanie matchujúcich mien
    matching_names = analyzer.find_matching_names(employee_name, analyzer.applications_data)
    
    if not matching_names:
        return None
    
    # Filtruj dáta pre tohto zamestnanca
    employee_apps = analyzer.applications_data[
        analyzer.applications_data['Osoba ▲'].isin(matching_names)
    ]
    
    return employee_apps


def create_monthly_sales_chart(monthly_sales):
    """Vytvorí profesionálny mesačný graf predaja s gradientom"""
    
    st.markdown("### 📈 Mesačný vývoj predaja")
    
    months_cz = {
        'leden': 'Január', 'unor': 'Február', 'brezen': 'Marec',
        'duben': 'Apríl', 'kveten': 'Máj', 'cerven': 'Jún',
        'cervenec': 'Júl', 'srpen': 'August', 'zari': 'September',
        'rijen': 'Október', 'listopad': 'November', 'prosinec': 'December'
    }
    
    # Príprava dát
    months = list(months_cz.keys())
    values = [monthly_sales.get(month, 0) for month in months]
    labels = [months_cz[month] for month in months]
    
    # Dynamické farby na základě hodnot
    max_val = max(values) if values else 1
    colors = []
    for v in values:
        if v == 0:
            colors.append('#374151')  # Šedá pre nulové hodnoty
        elif v >= max_val * 0.8:
            colors.append('#10b981')  # Zelená pre vysoké hodnoty
        elif v >= max_val * 0.5:
            colors.append('#3b82f6')  # Modrá pre stredné hodnoty
        elif v >= max_val * 0.3:
            colors.append('#f59e0b')  # Žltá pre nízke hodnoty
        else:
            colors.append('#ef4444')  # Červená pre veľmi nízke hodnoty
    
    # Gradient efekt na pozadí
    fig_monthly = go.Figure()
    
    # Hlavný graf s tieňom
    fig_monthly.add_trace(go.Bar(
        x=labels,
        y=values,
        marker=dict(
            color=colors,
            line=dict(color='rgba(255,255,255,0.2)', width=1.5)
        ),
        text=[f'{v:,.0f} Kč' if v > 0 else 'Žiadny predaj' for v in values],
        textposition='outside',
        textfont=dict(color='white', size=12, family='Arial Black'),
        hovertemplate='<b>%{x}</b><br>Predaj: <b>%{y:,.0f} Kč</b><extra></extra>',
        name='Mesačný predaj'
    ))
    
    # Layout s lepším štýlovaním
    layout_settings = get_dark_plotly_layout()
    layout_settings.update({
        'title': {
            'text': f"💰 Mesačný predaj - Celkom: {sum(values):,.0f} Kč",
            **get_dark_plotly_title_style(),
            'font': dict(size=20, color='white')
        },
        'height': 450,
        'xaxis': {
            **layout_settings['xaxis'],
            'title': dict(text='Mesiace', font=dict(size=14, color='#9ca3af')),
            'tickfont': dict(size=12, color='white'),
            'showgrid': True,
            'gridcolor': 'rgba(255,255,255,0.1)'
        },
        'yaxis': {
            **layout_settings['yaxis'], 
            'title': dict(text='Predaj (Kč)', font=dict(size=14, color='#9ca3af')),
            'tickfont': dict(size=12, color='white'),
            'showgrid': True,
            'gridcolor': 'rgba(255,255,255,0.1)',
            'tickformat': ',.0f'
        },
        'plot_bgcolor': 'rgba(31, 41, 55, 0.8)',
        'paper_bgcolor': 'rgba(17, 24, 39, 1)',
        'margin': dict(l=80, r=30, t=80, b=60)
    })
    
    fig_monthly.update_layout(**layout_settings)
    st.plotly_chart(fig_monthly, use_container_width=True)
    
    # Detailná tabuľka
    with st.expander("📋 Detailný mesačný rozpis", expanded=False):
        monthly_data = []
        for month_cz, month_sk in months_cz.items():
            if month_cz in monthly_sales:
                value = monthly_sales[month_cz]
                monthly_data.append({
                    'Mesiac': month_sk,
                    'Predaj': format_money(value),
                    'Podiel': f"{(value/sum(values)*100):.1f}%" if sum(values) > 0 else "0%"
                })
        
        if monthly_data:
            df_monthly = pd.DataFrame(monthly_data)
            st.dataframe(df_monthly, use_container_width=True)


def create_internet_analysis(internet_data, employee_name):
    """Vytvorí profesionálnu analýzu internet aktivít s lepším dizajnom"""
    
    st.markdown("### 🌐 Analýza internetových aktivít")
    
    if internet_data is None or internet_data.empty:
        st.warning(f"⚠️ Žiadne internet dáta pre {employee_name}")
        return
    
    # Agregácia všetkých internet aktivít
    internet_activities = {
        'Mail': 0,
        'IS Sykora': 0,
        'SykoraShop': 0,
        'Web k praci': 0,
        'Chat': 0,  # SketchUp
        'Hry': 0,
        'Nepracovni weby': 0,
        'Nezařazené': 0,
        'Umela inteligence': 0,
        'hladanie prace': 0
    }
    
    for _, row in internet_data.iterrows():
        for activity in internet_activities.keys():
            time_str = row.get(activity, '0:00')
            minutes = time_to_minutes(time_str)
            internet_activities[activity] += minutes
    
    # Filtrovanie len aktivít s časom > 0
    active_activities = {k: v for k, v in internet_activities.items() if v > 0}
    
    if not active_activities:
        st.info("ℹ️ Žiadne zaznamenané internet aktivity")
        return
    
    # Rozdelenie aktivít na kategórie
    productive_activities = {}
    concerning_activities = {}
    critical_activities = {}
    
    for activity, minutes in active_activities.items():
        if activity in ['Mail', 'IS Sykora', 'SykoraShop', 'Web k praci']:
            productive_activities[activity] = minutes
        elif activity in ['Chat']:  # SketchUp
            critical_activities[activity] = minutes
        else:
            concerning_activities[activity] = minutes
    
    # Vytvorenie kruhového grafu pre lepšiu vizualizáciu
    if len(active_activities) > 5:
        # Pre viac aktivít použijeme pie chart
        activities = list(active_activities.keys())
        minutes = list(active_activities.values())
        hours = [m/60 for m in minutes]
        
        # Kategórie farieb
        colors = []
        for activity in activities:
            if activity in ['Mail', 'IS Sykora', 'SykoraShop', 'Web k praci']:
                colors.append('#10b981')  # Zelená pre produktívne
            elif activity == 'Chat':
                colors.append('#ef4444')  # Červená pre SketchUp
            else:
                colors.append('#f59e0b')  # Žltá pre problematické
        
        fig = go.Figure(data=[
            go.Pie(
                labels=[f'{act}<br>{h:.1f}h' for act, h in zip(activities, hours)],
                values=hours,
                marker=dict(
                    colors=colors,
                    line=dict(color='rgba(255,255,255,0.3)', width=2)
                ),
                textfont=dict(size=12, color='white'),
                hovertemplate='<b>%{label}</b><br>Čas: %{value:.1f}h<br>Podiel: %{percent}<extra></extra>',
                hole=0.4  # Donut chart
            )
        ])
        
        # Center text pre donut
        total_hours = sum(hours)
        fig.add_annotation(
            text=f"<b>{total_hours:.1f}h</b><br>Celkom",
            showarrow=False,
            font=dict(size=18, color='white'),
            x=0.5, y=0.5
        )
        
    else:
        # Pre menej aktivít stĺpcový graf
        activities = list(active_activities.keys())
        minutes = list(active_activities.values())
        hours = [m/60 for m in minutes]
        
        colors = []
        for activity in activities:
            if activity in ['Mail', 'IS Sykora', 'SykoraShop', 'Web k praci']:
                colors.append('#10b981')
            elif activity == 'Chat':
                colors.append('#ef4444')
            else:
                colors.append('#f59e0b')
        
        fig = go.Figure(data=[
            go.Bar(
                x=activities,
                y=hours,
                marker=dict(
                    color=colors,
                    line=dict(color='rgba(255,255,255,0.2)', width=1.5)
                ),
                text=[f'{h:.1f}h' for h in hours],
                textposition='outside',
                textfont=dict(color='white', size=12, family='Arial'),
                hovertemplate='<b>%{x}</b><br>Čas: <b>%{y:.1f}h</b><extra></extra>',
                name='Internet aktivity'
            )
        ])
    
    # Rozšírený layout
    layout_settings = get_dark_plotly_layout()
    layout_settings.update({
        'title': {
            'text': f"🌐 Internet aktivity - Celkom: {sum([m/60 for m in active_activities.values()]):.1f} hodín",
            **get_dark_plotly_title_style(),
            'font': dict(size=18, color='white')
        },
        'height': 500,
        'plot_bgcolor': 'rgba(31, 41, 55, 0.8)',
        'paper_bgcolor': 'rgba(17, 24, 39, 1)',
        'margin': dict(l=80, r=30, t=80, b=60)
    })
    
    # Špecifické nastavenia pre typ grafu
    if len(active_activities) <= 5:
        layout_settings.update({
            'xaxis': {
                **layout_settings['xaxis'],
                'title': dict(text='Aktivity', font=dict(size=14, color='#9ca3af')),
                'tickfont': dict(size=11, color='white'),
                'showgrid': True,
                'gridcolor': 'rgba(255,255,255,0.1)'
            },
            'yaxis': {
                **layout_settings['yaxis'], 
                'title': dict(text='Čas (hodiny)', font=dict(size=14, color='#9ca3af')),
                'tickfont': dict(size=12, color='white'),
                'showgrid': True,
                'gridcolor': 'rgba(255,255,255,0.1)'
            }
        })
    
    fig.update_layout(**layout_settings)
    st.plotly_chart(fig, use_container_width=True)
    
    # Rozšírené upozornenia s kategorizáciou
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if productive_activities:
            total_productive = sum([v/60 for v in productive_activities.values()])
            st.success(f"✅ **Produktívne aktivity**: {total_productive:.1f}h")
            for act, mins in productive_activities.items():
                st.write(f"• {act}: {mins/60:.1f}h")
    
    with col2:
        if concerning_activities:
            total_concerning = sum([v/60 for v in concerning_activities.values()])
            st.warning(f"⚠️ **Problematické aktivity**: {total_concerning:.1f}h")
            for act, mins in concerning_activities.items():
                st.write(f"• {act}: {mins/60:.1f}h")
    
    with col3:
        if critical_activities:
            total_critical = sum([v/60 for v in critical_activities.values()])
            st.error(f"🚨 **Kritické aktivity**: {total_critical:.1f}h")
            
            sketchup_time = critical_activities.get('Chat', 0)
            if sketchup_time > 0:
                hours = sketchup_time / 60
                if hours > 5:
                    st.error(f"**VYSOKÉ RIZIKO**: SketchUp {hours:.1f}h - možná práca pre iných!")
                elif hours > 2:
                    st.warning(f"**STREDNÉ RIZIKO**: SketchUp {hours:.1f}h")
                else:
                    st.info(f"**NÍZKE RIZIKO**: SketchUp {hours:.1f}h")


def create_application_analysis(app_data, employee_name):
    """Vytvorí profesionálnu analýzu aplikačných aktivít"""
    
    st.markdown("### 💻 Analýza aplikačných aktivít")
    
    if app_data is None or app_data.empty:
        st.warning(f"⚠️ Žiadne aplikačné dáta pre {employee_name}")
        return
    
    # Agregácia všetkých aplikačných aktivít
    app_activities = {
        'Helios Green': 0,
        'Imos - program': 0,
        'Programy': 0,
        'Půdorysy': 0,
        'Mail': 0,
        'Chat': 0,
        'Internet': 0
    }
    
    for _, row in app_data.iterrows():
        for activity in app_activities.keys():
            time_str = row.get(activity, '0:00')
            minutes = time_to_minutes(time_str)
            app_activities[activity] += minutes
    
    # Filtrovanie len aktivít s časom > 0
    active_activities = {k: v for k, v in app_activities.items() if v > 0}
    
    if not active_activities:
        st.info("ℹ️ Žiadne zaznamenané aplikačné aktivity")
        return
    
    # Kategorizácia aktivít
    business_apps = {}
    communication_apps = {}
    other_apps = {}
    
    for activity, minutes in active_activities.items():
        if activity in ['Helios Green', 'Imos - program', 'Programy', 'Půdorysy']:
            business_apps[activity] = minutes
        elif activity in ['Mail', 'Chat']:
            communication_apps[activity] = minutes
        else:
            other_apps[activity] = minutes
    
    # Rozhodnutie o type grafu na základe počtu aktivít
    activities = list(active_activities.keys())
    minutes = list(active_activities.values())
    hours = [m/60 for m in minutes]
    
    if len(active_activities) > 6:
        # Stacked horizontal bar pre viacero aktivít
        fig = go.Figure()
        
        # Rozdelenie na kategórie
        if business_apps:
            bus_names = list(business_apps.keys())
            bus_values = [business_apps[name]/60 for name in bus_names]
            fig.add_trace(go.Bar(
                name='Firemné aplikácie',
                y=bus_names,
                x=bus_values,
                orientation='h',
                marker_color='#10b981',
                text=[f'{v:.1f}h' for v in bus_values],
                textposition='auto'
            ))
        
        if communication_apps:
            comm_names = list(communication_apps.keys())
            comm_values = [communication_apps[name]/60 for name in comm_names]
            fig.add_trace(go.Bar(
                name='Komunikácia',
                y=comm_names,
                x=comm_values,
                orientation='h',
                marker_color='#3b82f6',
                text=[f'{v:.1f}h' for v in comm_values],
                textposition='auto'
            ))
        
        if other_apps:
            other_names = list(other_apps.keys())
            other_values = [other_apps[name]/60 for name in other_names]
            fig.add_trace(go.Bar(
                name='Ostatné',
                y=other_names,
                x=other_values,
                orientation='h',
                marker_color='#f59e0b',
                text=[f'{v:.1f}h' for v in other_values],
                textposition='auto'
            ))
        
        layout_height = max(400, len(activities) * 40)
        
    else:
        # Stĺpcový graf pre menej aktivít
        colors = []
        for activity in activities:
            if activity in ['Helios Green', 'Imos - program', 'Programy', 'Půdorysy']:
                colors.append('#10b981')  # Zelená pre firemné
            elif activity in ['Mail']:
                colors.append('#3b82f6')  # Modrá pre komunikáciu
            elif activity == 'Chat':
                colors.append('#ef4444')  # Červená pre problematické
            else:
                colors.append('#f59e0b')  # Žltá pre ostatné
        
        fig = go.Figure(data=[
            go.Bar(
                x=activities,
                y=hours,
                marker=dict(
                    color=colors,
                    line=dict(color='rgba(255,255,255,0.2)', width=1.5)
                ),
                text=[f'{h:.1f}h' for h in hours],
                textposition='outside',
                textfont=dict(color='white', size=12, family='Arial'),
                hovertemplate='<b>%{x}</b><br>Čas: <b>%{y:.1f}h</b><extra></extra>',
                name='Aplikačné aktivity'
            )
        ])
        
        layout_height = 450
    
    # Rozšírený layout
    layout_settings = get_dark_plotly_layout()
    layout_settings.update({
        'title': {
            'text': f"💻 Aplikačné aktivity - Celkom: {sum(hours):.1f} hodín",
            **get_dark_plotly_title_style(),
            'font': dict(size=18, color='white')
        },
        'height': layout_height,
        'plot_bgcolor': 'rgba(31, 41, 55, 0.8)',
        'paper_bgcolor': 'rgba(17, 24, 39, 1)',
        'margin': dict(l=120, r=30, t=80, b=60)
    })
    
    if len(active_activities) <= 6:
        layout_settings.update({
            'xaxis': {
                **layout_settings['xaxis'],
                'title': dict(text='Aplikácie', font=dict(size=14, color='#9ca3af')),
                'tickfont': dict(size=11, color='white'),
                'showgrid': True,
                'gridcolor': 'rgba(255,255,255,0.1)'
            },
            'yaxis': {
                **layout_settings['yaxis'], 
                'title': dict(text='Čas (hodiny)', font=dict(size=14, color='#9ca3af')),
                'tickfont': dict(size=12, color='white'),
                'showgrid': True,
                'gridcolor': 'rgba(255,255,255,0.1)'
            }
        })
    else:
        layout_settings.update({
            'xaxis': {
                **layout_settings['xaxis'],
                'title': dict(text='Čas (hodiny)', font=dict(size=14, color='#9ca3af')),
                'tickfont': dict(size=12, color='white'),
                'showgrid': True,
                'gridcolor': 'rgba(255,255,255,0.1)'
            },
            'yaxis': {
                **layout_settings['yaxis'], 
                'title': dict(text='Aplikácie', font=dict(size=14, color='#9ca3af')),
                'tickfont': dict(size=11, color='white'),
                'showgrid': True,
                'gridcolor': 'rgba(255,255,255,0.1)'
            },
            'barmode': 'stack'
        })
    
    fig.update_layout(**layout_settings)
    st.plotly_chart(fig, use_container_width=True)
    
    # Rozšírené metriky s kategorizáciou
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if business_apps:
            total_business = sum([v/60 for v in business_apps.values()])
            st.success(f"🏢 **Firemné aplikácie**: {total_business:.1f}h")
            
            # Top firemná aplikácia
            top_app = max(business_apps.items(), key=lambda x: x[1])
            st.write(f"🥇 Najviac: {top_app[0]} ({top_app[1]/60:.1f}h)")
            
            # Efektivita
            if total_business > 0:
                if total_business > 6:
                    st.info("💪 Vysoká produktivita")
                elif total_business > 3:
                    st.info("👍 Priemerná produktivita") 
                else:
                    st.warning("⚠️ Nízka produktivita")
        else:
            st.error("❌ **Žiadne firemné aplikácie**")
    
    with col2:
        if communication_apps:
            total_comm = sum([v/60 for v in communication_apps.values()])
            st.info(f"💬 **Komunikácia**: {total_comm:.1f}h")
            
            for app, mins in communication_apps.items():
                if app == 'Chat' and mins > 0:
                    st.error(f"⚠️ {app}: {mins/60:.1f}h (problém!)")
                else:
                    st.write(f"• {app}: {mins/60:.1f}h")
        else:
            st.warning("⚠️ Žiadna komunikačná aktivita")
    
    with col3:
        if other_apps:
            total_other = sum([v/60 for v in other_apps.values()])
            st.warning(f"🔧 **Ostatné aplikácie**: {total_other:.1f}h")
            for app, mins in other_apps.items():
                st.write(f"• {app}: {mins/60:.1f}h")
    
    # Celkové hodnotenie produktivity
    st.markdown("---")
    
    total_productive = sum([v/60 for v in business_apps.values()])
    total_all = sum(hours)
    
    if total_all > 0:
        productivity_ratio = total_productive / total_all * 100
        
        col1, col2 = st.columns(2)
        with col1:
            if productivity_ratio >= 80:
                st.success(f"✅ **Výborná produktivita**: {productivity_ratio:.1f}% času vo firemných aplikáciách")
            elif productivity_ratio >= 60:
                st.info(f"👍 **Dobrá produktivita**: {productivity_ratio:.1f}% času vo firemných aplikáciách")
            elif productivity_ratio >= 40:
                st.warning(f"⚠️ **Priemerná produktivita**: {productivity_ratio:.1f}% času vo firemných aplikáciách")
            else:
                st.error(f"❌ **Nízka produktivita**: {productivity_ratio:.1f}% času vo firemných aplikáciách")
        
        with col2:
            # Aplikačné skóre na základe typu aktivít
            score = 0
            if 'Helios Green' in active_activities:
                score += 30
            if 'Imos - program' in active_activities:
                score += 30
            if 'Programy' in active_activities:
                score += 20
            if 'Mail' in active_activities:
                score += 10
            if 'Chat' in active_activities:
                score -= 20
            
            score = max(0, min(100, score))
            
            if score >= 80:
                st.success(f"🏆 **Aplikačné skóre**: {score}/100")
            elif score >= 60:
                st.info(f"👍 **Aplikačné skóre**: {score}/100")
            else:
                st.warning(f"⚠️ **Aplikačné skóre**: {score}/100")


def create_productivity_comparisons(internet_data, app_data, total_sales, employee_name):
    """Vytvorí pokročilé porovnania aktivít proti predaju s lepšou vizualizáciou"""
    
    st.markdown("### 🎯 Produktivitné analýzy a efektivita")
    
    if total_sales == 0:
        st.warning("⚠️ Žiadne predajné dáta pre porovnanie")
        return
    
    # Zbieranie dát pre analýzy
    activities_data = []
    
    # SketchUp vs Predaj (z internet dát)
    if internet_data is not None and not internet_data.empty:
        sketchup_total = 0
        for _, row in internet_data.iterrows():
            sketchup_total += time_to_minutes(row.get('Chat', '0:00'))
        
        if sketchup_total > 0:
            sketchup_hours = sketchup_total / 60
            efficiency = total_sales / sketchup_hours if sketchup_hours > 0 else 0
            activities_data.append({
                'name': 'SketchUp',
                'activity_time': sketchup_hours,
                'sales_per_hour': efficiency,
                'color': '#ef4444',
                'category': 'Kritické',
                'risk_level': 'Vysoké' if sketchup_hours > 2 else 'Stredné'
            })
    
    # Mail analýza (kombinovaná z oboch zdrojov)
    mail_total_internet = 0
    mail_total_app = 0
    
    if internet_data is not None and not internet_data.empty:
        for _, row in internet_data.iterrows():
            mail_total_internet += time_to_minutes(row.get('Mail', '0:00'))
    
    if app_data is not None and not app_data.empty:
        for _, row in app_data.iterrows():
            mail_total_app += time_to_minutes(row.get('Mail', '0:00'))
    
    mail_total = mail_total_internet + mail_total_app
    if mail_total > 0:
        mail_hours = mail_total / 60
        efficiency = total_sales / mail_hours if mail_hours > 0 else 0
        activities_data.append({
            'name': 'Mail celkovo',
            'activity_time': mail_hours,
            'sales_per_hour': efficiency,
            'color': '#3b82f6',
            'category': 'Komunikácia',
            'risk_level': 'Nízke' if mail_hours < 3 else 'Stredné'
        })
    
    # Imos vs Predaj
    if app_data is not None and not app_data.empty:
        imos_total = 0
        for _, row in app_data.iterrows():
            imos_total += time_to_minutes(row.get('Imos - program', '0:00'))
        
        if imos_total > 0:
            imos_hours = imos_total / 60
            efficiency = total_sales / imos_hours if imos_hours > 0 else 0
            activities_data.append({
                'name': 'Imos',
                'activity_time': imos_hours,
                'sales_per_hour': efficiency,
                'color': '#10b981',
                'category': 'Produktívne',
                'risk_level': 'Žiadne'
            })
        
        # Helios Green vs Predaj
        helios_total = 0
        for _, row in app_data.iterrows():
            helios_total += time_to_minutes(row.get('Helios Green', '0:00'))
        
        if helios_total > 0:
            helios_hours = helios_total / 60
            efficiency = total_sales / helios_hours if helios_hours > 0 else 0
            activities_data.append({
                'name': 'Helios Green',
                'activity_time': helios_hours,
                'sales_per_hour': efficiency,
                'color': '#10b981',
                'category': 'Produktívne',
                'risk_level': 'Žiadne'
            })
    
    # SykoraShop vs Predaj
    if internet_data is not None and not internet_data.empty:
        shop_total = 0
        for _, row in internet_data.iterrows():
            shop_total += time_to_minutes(row.get('SykoraShop', '0:00'))
        
        if shop_total > 0:
            shop_hours = shop_total / 60
            efficiency = total_sales / shop_hours if shop_hours > 0 else 0
            activities_data.append({
                'name': 'SykoraShop',
                'activity_time': shop_hours,
                'sales_per_hour': efficiency,
                'color': '#8b5cf6',
                'category': 'Obchodné',
                'risk_level': 'Nízke'
            })
    
    if not activities_data:
        st.info("ℹ️ Žiadne dáta pre produktivitné porovnania")
        return
    
    # Rozšírená vizualizácia s kombinovaným grafom
    create_advanced_productivity_chart(activities_data, total_sales)
    
    # Detailné metriky v profesionálnom formáte
    st.markdown("---")
    st.markdown("### 📊 Detailné produktivitné metriky")
    
    # Rozdelenie do kategórií
    productive_activities = [a for a in activities_data if a['category'] in ['Produktívne', 'Obchodné']]
    communication_activities = [a for a in activities_data if a['category'] == 'Komunikácia']
    critical_activities = [a for a in activities_data if a['category'] == 'Kritické']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🟢 Produktívne aktivity")
        if productive_activities:
            for activity in productive_activities:
                create_activity_metric_card(activity, total_sales)
        else:
            st.warning("⚠️ Žiadne produktívne aktivity")
    
    with col2:
        st.markdown("#### 🔵 Komunikačné aktivity")
        if communication_activities:
            for activity in communication_activities:
                create_activity_metric_card(activity, total_sales)
        else:
            st.info("ℹ️ Žiadne komunikačné aktivity")
    
    with col3:
        st.markdown("#### 🔴 Kritické aktivity")
        if critical_activities:
            for activity in critical_activities:
                create_activity_metric_card(activity, total_sales, is_critical=True)
        else:
            st.success("✅ Žiadne kritické aktivity")
    
    # Celkové hodnotenie a doporučenia
    st.markdown("---")
    create_overall_productivity_assessment(activities_data, total_sales)


def create_advanced_productivity_chart(activities_data, total_sales):
    """Vytvorí pokročilý kombinovaný graf produktivity"""
    
    # Rozdelenie dát
    names = [a['name'] for a in activities_data]
    times = [a['activity_time'] for a in activities_data]
    efficiencies = [a['sales_per_hour'] for a in activities_data]
    colors = [a['color'] for a in activities_data]
    
    # Bubble chart pre lepšiu vizualizáciu
    fig = go.Figure()
    
    # Hlavný scatter plot
    fig.add_trace(go.Scatter(
        x=times,
        y=efficiencies,
        mode='markers+text',
        marker=dict(
            size=[min(60, max(20, t*8)) for t in times],  # Veľkosť bublin podľa času
            color=colors,
            line=dict(color='rgba(255,255,255,0.5)', width=2),
            sizemode='diameter'
        ),
        text=names,
        textposition='middle center',
        textfont=dict(color='white', size=10, family='Arial Black'),
        hovertemplate='<b>%{text}</b><br>' +
                     'Čas: %{x:.1f}h<br>' +
                     'Efektivita: %{y:,.0f} Kč/h<br>' +
                     '<extra></extra>',
        name='Aktivity'
    ))
    
    # Pridanie trendovej čiary (ak je viac ako 2 body)
    if len(activities_data) > 2:
        z = np.polyfit(times, efficiencies, 1)
        p = np.poly1d(z)
        x_trend = np.linspace(min(times), max(times), 100)
        y_trend = p(x_trend)
        
        fig.add_trace(go.Scatter(
            x=x_trend,
            y=y_trend,
            mode='lines',
            line=dict(color='rgba(255,255,255,0.5)', width=2, dash='dash'),
            name='Trend',
            showlegend=True
        ))
    
    # Rozšírený layout
    layout_settings = get_dark_plotly_layout()
    layout_settings.update({
        'title': {
            'text': f"🎯 Efektivita aktivít - Predaj: {total_sales:,.0f} Kč",
            **get_dark_plotly_title_style(),
            'font': dict(size=18, color='white')
        },
        'height': 500,
        'xaxis': {
            **layout_settings['xaxis'],
            'title': dict(text='Čas aktivity (hodiny)', font=dict(size=14, color='#9ca3af')),
            'tickfont': dict(size=12, color='white'),
            'showgrid': True,
            'gridcolor': 'rgba(255,255,255,0.1)',
            'range': [0, max(times) * 1.1]
        },
        'yaxis': {
            **layout_settings['yaxis'], 
            'title': dict(text='Efektivita (Kč/hodinu)', font=dict(size=14, color='#9ca3af')),
            'tickfont': dict(size=12, color='white'),
            'showgrid': True,
            'gridcolor': 'rgba(255,255,255,0.1)',
            'tickformat': ',.0f'
        },
        'plot_bgcolor': 'rgba(31, 41, 55, 0.8)',
        'paper_bgcolor': 'rgba(17, 24, 39, 1)',
        'margin': dict(l=100, r=30, t=80, b=60),
        'annotations': [
            dict(
                x=0.02, y=0.98,
                xref='paper', yref='paper',
                text="Veľkosť bubliny = čas aktivity",
                showarrow=False,
                font=dict(color='#9ca3af', size=10),
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='rgba(255,255,255,0.2)',
                borderwidth=1
            )
        ]
    })
    
    fig.update_layout(**layout_settings)
    st.plotly_chart(fig, use_container_width=True)


def create_activity_metric_card(activity, total_sales, is_critical=False):
    """Vytvorí kartu metriky aktivity"""
    
    # Výpočet percentuálneho podielu z celkového času
    time_percentage = (activity['activity_time'] / (total_sales / 100000)) * 100 if total_sales > 0 else 0
    
    # Určenie statusu efektivity
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
    
    # Farba karty na základe kritickosti
    border_color = activity['color']
    if is_critical:
        border_color = '#ef4444'
    
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
                {activity['name']}
            </h5>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0;">
                <div>
                    <p style="color: #9ca3af; margin: 2px 0; font-size: 0.8rem;">Čas:</p>
                    <p style="color: white; margin: 2px 0; font-weight: bold;">{activity['activity_time']:.1f}h</p>
                </div>
                <div>
                    <p style="color: #9ca3af; margin: 2px 0; font-size: 0.8rem;">Efektivita:</p>
                    <p style="color: {efficiency_color}; margin: 2px 0; font-weight: bold;">{activity['sales_per_hour']:,.0f} Kč/h</p>
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
                    Riziko: {activity['risk_level']}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def create_overall_productivity_assessment(activities_data, total_sales):
    """Vytvorí celkové hodnotenie produktivity"""
    
    st.markdown("### 🏆 Celkové hodnotenie produktivity")
    
    # Výpočet celkového skóre
    total_score = 0
    max_score = 0
    
    productive_time = 0
    critical_time = 0
    communication_time = 0
    
    for activity in activities_data:
        max_score += 100
        
        if activity['category'] == 'Produktívne':
            total_score += 90
            productive_time += activity['activity_time']
        elif activity['category'] == 'Obchodné':
            total_score += 80
            productive_time += activity['activity_time']
        elif activity['category'] == 'Komunikácia':
            total_score += 60
            communication_time += activity['activity_time']
        elif activity['category'] == 'Kritické':
            total_score += 20
            critical_time += activity['activity_time']
    
    overall_score = (total_score / max_score * 100) if max_score > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        score_color = '#10b981' if overall_score >= 80 else '#f59e0b' if overall_score >= 60 else '#ef4444'
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: {score_color}20; border-radius: 10px; border: 2px solid {score_color};">
            <h2 style="color: {score_color}; margin: 0;">{overall_score:.0f}/100</h2>
            <p style="color: {score_color}; margin: 5px 0; font-weight: bold;">Celkové skóre</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: #10b98120; border-radius: 10px; border: 2px solid #10b981;">
            <h2 style="color: #10b981; margin: 0;">{productive_time:.1f}h</h2>
            <p style="color: #10b981; margin: 5px 0; font-weight: bold;">Produktívny čas</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: #3b82f620; border-radius: 10px; border: 2px solid #3b82f6;">
            <h2 style="color: #3b82f6; margin: 0;">{communication_time:.1f}h</h2>
            <p style="color: #3b82f6; margin: 5px 0; font-weight: bold;">Komunikačný čas</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        critical_color = '#ef4444' if critical_time > 0 else '#10b981'
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background: {critical_color}20; border-radius: 10px; border: 2px solid {critical_color};">
            <h2 style="color: {critical_color}; margin: 0;">{critical_time:.1f}h</h2>
            <p style="color: {critical_color}; margin: 5px 0; font-weight: bold;">Kritický čas</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Odporúčania na základe analýzy
    st.markdown("#### 💡 Personalizované odporúčania")
    
    recommendations = []
    
    if critical_time > 0:
        recommendations.append({
            'type': 'error',
            'text': f"🚨 Znížte kritické aktivity o {critical_time:.1f}h - môže to indikovať prácu pre konkurenciu!"
        })
    
    if productive_time < 4:
        recommendations.append({
            'type': 'warning',
            'text': f"⚠️ Zvýšte čas v produktívnych aplikáciách - aktuálne len {productive_time:.1f}h"
        })
    
    if communication_time > 3:
        recommendations.append({
            'type': 'info',
            'text': f"💬 Optimalizujte komunikačný čas - aktuálne {communication_time:.1f}h"
        })
    
    if overall_score >= 80:
        recommendations.append({
            'type': 'success',
            'text': "✅ Výborná produktivita! Pokračujte v súčasnom tempe."
        })
    
    if not recommendations:
        recommendations.append({
            'type': 'info',
            'text': "📊 Produktivita je v rozumných medziach. Sledujte trendy pre kontinuálne zlepšovanie."
        })
    
    for rec in recommendations:
        if rec['type'] == 'error':
            st.error(rec['text'])
        elif rec['type'] == 'warning':
            st.warning(rec['text'])
        elif rec['type'] == 'success':
            st.success(rec['text'])
        else:
            st.info(rec['text'])



def inject_detailed_styles():
    """CSS pre nový detailný view"""
    st.markdown("""
    <style>
    .employee-header {
        background: linear-gradient(135deg, #1e3a8a, #1e40af);
        padding: 30px;
        border-radius: 15px;
        margin-bottom: 25px;
        color: white;
        text-align: center;
    }
    
    .metric-section {
        background: #1f2937;
        padding: 25px;
        border-radius: 12px;
        margin: 20px 0;
        border: 1px solid #374151;
    }
    
    .comparison-card {
        background: linear-gradient(135deg, #374151, #4b5563);
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
        border-left: 4px solid #60a5fa;
        color: white;
    }
    
    .activity-detail {
        background: #111827;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border: 1px solid #374151;
    }
    
    .recommendation-good { border-left: 4px solid #10b981; }
    .recommendation-warning { border-left: 4px solid #f59e0b; }
    .recommendation-critical { border-left: 4px solid #ef4444; }
    </style>
    """, unsafe_allow_html=True)


def show_employee_header(analysis):
    """Header s informáciami"""
    st.markdown(f"""
    <div class="employee-header">
        <h1>👤 {analysis['name']}</h1>
        <h3>📍 {analysis.get('workplace', 'Neznáme').title()}</h3>
        <p>Komplexná analýza výkonnosti s detailným porovnaním</p>
    </div>
    """, unsafe_allow_html=True)


def show_monthly_sales_detailed(analysis):
    """1️⃣ DETAILNÝ mesačný predaj - PRVÝ v poradí"""
    st.markdown("## 💰 Mesačný predaj - detailný rozpis")
    
    sales_performance = analysis.get('sales_performance', {})
    monthly_sales = sales_performance.get('monthly_sales', {})
    
    if not monthly_sales:
        st.warning("Žiadne predajné dáta")
        return
    
    # Mesačné hodnoty
    months_cz = {
        'leden': 'Január', 'unor': 'Február', 'brezen': 'Marec',
        'duben': 'Apríl', 'kveten': 'Máj', 'cerven': 'Jún',
        'cervenec': 'Júl', 'srpen': 'August', 'zari': 'September',
        'rijen': 'Október', 'listopad': 'November', 'prosinec': 'December'
    }
    
    # Príprava dát pre graf
    months_display = []
    values = []
    colors = []
    
    for month_cz, month_sk in months_cz.items():
        if month_cz in monthly_sales:
            months_display.append(month_sk)
            values.append(monthly_sales[month_cz])
            
            # Farba podľa výšky predaja
            if monthly_sales[month_cz] > 1000000:
                colors.append('#10b981')  # zelená
            elif monthly_sales[month_cz] > 500000:
                colors.append('#f59e0b')  # žltá
            else:
                colors.append('#ef4444')  # červená
    
    if values:
        fig_monthly = go.Figure()
        
        fig_monthly.add_trace(go.Bar(
            x=months_display,
            y=values,
            marker_color=colors,
            text=[f'{v:,.0f} Kč' for v in values],
            textposition='auto',
            textfont={'color': 'white', 'size': 12}
        ))
        
        # Získanie dark layout a úprava
        layout_settings = get_dark_plotly_layout()
        layout_settings.update({
            'title': {
                'text': f"Mesačný predaj - Celkom: {sum(values):,.0f} Kč",
                **get_dark_plotly_title_style()
            },
            'height': 400,
            'xaxis': {
                **layout_settings['xaxis'],
                'title': 'Mesiace'
            },
            'yaxis': {
                **layout_settings['yaxis'], 
                'title': 'Predaj (Kč)'
            }
        })
        
        fig_monthly.update_layout(**layout_settings)
        
        st.plotly_chart(fig_monthly, use_container_width=True)
        
        # Detailná tabuľka
        with st.expander("📋 Detailný mesačný rozpis", expanded=False):
            monthly_data = []
            for month_cz, month_sk in months_cz.items():
                if month_cz in monthly_sales:
                    monthly_data.append({
                        'Mesiac': month_sk,
                        'Predaj': f'{monthly_sales[month_cz]:,.0f} Kč',
                        'Percentuálny podiel': f'{(monthly_sales[month_cz] / sum(values) * 100):.1f}%'
                    })
            
            st.dataframe(pd.DataFrame(monthly_data), use_container_width=True)


def show_quarterly_targets(analyzer, employee_name):
    """2️⃣ Kvartálne ciele"""
    st.markdown("## 🎯 Kvartálne ciele a plnenie")
    
    # Nájdenie employee dát
    employee_data = None
    for emp in analyzer.sales_employees:
        if emp['name'] == employee_name:
            employee_data = emp
            break
    
    if not employee_data:
        st.warning("Žiadne dáta o cieľoch")
        return
    
    monthly_sales = employee_data.get('monthly_sales', {})
    
    # Kvartálne ciele
    quarters = {
        'Q1': {'months': ['leden', 'unor', 'brezen'], 'target': 2000000},
        'Q2': {'months': ['duben', 'kveten', 'cerven'], 'target': 2000000},
        'Q3': {'months': ['cervenec', 'srpen', 'zari'], 'target': 2000000},
        'Q4': {'months': ['rijen', 'listopad', 'prosinec'], 'target': 2000000}
    }
    
    cols = st.columns(4)
    for i, (quarter, config) in enumerate(quarters.items()):
        quarterly_sales = sum([monthly_sales.get(month, 0) for month in config['months']])
        percentage = (quarterly_sales / config['target'] * 100) if config['target'] > 0 else 0
        
        # Status farba
        if percentage >= 100:
            color = '#10b981'
            status = 'Splnený ✅'
        elif percentage >= 80:
            color = '#3b82f6'
            status = 'Dobrý 🔵'
        elif percentage >= 60:
            color = '#f59e0b'
            status = 'Pozor ⚠️'
        else:
            color = '#ef4444'
            status = 'Kritický ❌'
        
        with cols[i]:
            st.markdown(f"""
            <div class="metric-section" style="border-left: 4px solid {color};">
                <h3 style="color: {color}; margin: 0;">{quarter}</h3>
                <h2 style="margin: 10px 0;">{percentage:.1f}%</h2>
                <p style="margin: 5px 0; color: #9ca3af;">{status}</p>
                <hr style="border-color: #374151; margin: 10px 0;">
                <p style="font-size: 0.9em; margin: 5px 0;">Skutočnosť: {quarterly_sales:,.0f} Kč</p>
                <p style="font-size: 0.9em; margin: 5px 0;">Cieľ: {config['target']:,.0f} Kč</p>
            </div>
            """, unsafe_allow_html=True)


def show_detailed_activity_comparisons(analyzer, employee_name, analysis):
    """3️⃣ ROZŠÍRENÉ SketchUp monitoring + ostatné porovnania aktivít s priemerom"""
    st.markdown("## 📊 Detailná analýza aktivít vs. priemer")
    
    # Získanie priemerov všetkých zamestnancov
    all_averages = calculate_company_averages(analyzer)
    
    # Získanie detailných dát pre tohto zamestnanca
    employee_details = get_employee_detailed_activity(analyzer, employee_name)
    
    # ✅ NOVÁ: Špeciálna SketchUp sekcia
    show_sketchup_detailed_analysis(employee_details, all_averages, analysis)
    
    # Porovnania ostatných aktivít
    comparisons = [
        {
            'title': '💬 SketchUp (Chat) vs. Predaj',
            'employee_value': employee_details.get('sketchup_time', 0),
            'average_value': all_averages.get('sketchup_avg', 0),
            'sales': analysis['sales_performance']['total_sales'],
            'category': 'app',
            'description': 'Čas strávený v kresliacom programe SketchUp'
        },
        {
            'title': '📧 Mail vs. Predaj',
            'employee_value': employee_details.get('mail_time', 0),
            'average_value': all_averages.get('mail_avg', 0),
            'sales': analysis['sales_performance']['total_sales'],
            'category': 'productivity',
            'description': 'Čas strávený mailovým komunikáciou'
        },
        {
            'title': '🛍️ SykoraShop vs. Predaj',
            'employee_value': employee_details.get('sykorashop_time', 0),
            'average_value': all_averages.get('sykorashop_avg', 0),
            'sales': analysis['sales_performance']['total_sales'],
            'category': 'productivity',
            'description': 'Čas strávený na SykoraShop portáli'
        },
        {
            'title': '🌐 Celkový čas na internete vs. Predaj',
            'employee_value': employee_details.get('total_internet_time', 0),
            'average_value': all_averages.get('total_internet_avg', 0),
            'sales': analysis['sales_performance']['total_sales'],
            'category': 'general',
            'description': 'Celkový čas strávený internetovou aktivitou'
        }
    ]
    
    for comparison in comparisons:
        show_activity_comparison_card(comparison, all_averages.get('sales_avg', 3000000))


def show_sketchup_detailed_analysis(employee_details, all_averages, analysis):
    """Detailná SketchUp analýza s manažérskym pohľadom"""
    
    st.markdown("### 🚨 SketchUp Monitoring - Firemný cieľ: NULOVÉ používanie")
    
    sketchup_time = employee_details.get('sketchup_time', 0)
    sketchup_avg = all_averages.get('sketchup_avg', 0)
    sales = analysis['sales_performance']['total_sales']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        color = '#10b981' if sketchup_time == 0 else '#ef4444'
        st.markdown(f"""
        <div style="background: {color}20; border-left: 4px solid {color}; padding: 15px; border-radius: 8px;">
            <h4 style="color: {color}; margin: 0;">Tento zamestnanec</h4>
            <h2 style="margin: 10px 0;">{sketchup_time//60}h {sketchup_time%60}m</h2>
            <p style="margin: 0;">{'✅ Cieľ splnený' if sketchup_time == 0 else '❌ Používa SketchUp'}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        color = '#6b7280'
        st.markdown(f"""
        <div style="background: {color}20; border-left: 4px solid {color}; padding: 15px; border-radius: 8px;">
            <h4 style="color: {color}; margin: 0;">Firemný priemer</h4>
            <h2 style="margin: 10px 0;">{sketchup_avg//60}h {int(sketchup_avg%60)}m</h2>
            <p style="margin: 0;">Všetci zamestnanci</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if sketchup_time > 0:
            efficiency = sales / sketchup_time
            color = '#10b981' if efficiency > 50000 else '#ef4444'
            st.markdown(f"""
            <div style="background: {color}20; border-left: 4px solid {color}; padding: 15px; border-radius: 8px;">
                <h4 style="color: {color}; margin: 0;">Efektivita</h4>
                <h2 style="margin: 10px 0;">{efficiency:,.0f}</h2>
                <p style="margin: 0;">Kč/min v SketchUp</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: #10b98120; border-left: 4px solid #10b981; padding: 15px; border-radius: 8px;">
                <h4 style="color: #10b981; margin: 0;">Efektivita</h4>
                <h2 style="margin: 10px 0;">∞</h2>
                <p style="margin: 0;">Nepoužíva SketchUp</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col4:
        # Rizikové skóre
        if sketchup_time == 0:
            risk_color = '#10b981'
            risk_text = 'Nízke'
        elif sales < 1000000 and sketchup_time > 0:
            risk_color = '#ef4444'
            risk_text = 'VYSOKÉ'
        elif sketchup_time > 120:
            risk_color = '#f59e0b'
            risk_text = 'Stredné'
        else:
            risk_color = '#f59e0b'
            risk_text = 'Mierné'
            
        st.markdown(f"""
        <div style="background: {risk_color}20; border-left: 4px solid {risk_color}; padding: 15px; border-radius: 8px;">
            <h4 style="color: {risk_color}; margin: 0;">Riziko</h4>
            <h2 style="margin: 10px 0;">{risk_text}</h2>
            <p style="margin: 0;">Práca pre iných?</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Ak používa SketchUp, pridaj varovanie
    if sketchup_time > 0:
        st.error(f"""
        🚨 **POZOR**: Zamestnanec používa SketchUp {sketchup_time//60}h {sketchup_time%60}m pri predaji {sales:,.0f} Kč.
        
        **Možné dôvody:**
        - Robí projekty pre iných klientov (mimo firmu)
        - Používa nefiremné nástroje
        - Potrebuje školenie o firemných nástrojoch
        
        **Odporúčaná akcia:** Okamžitá konzultácia s vedúcim!
        """)
    else:
        st.success("✅ **Výborné!** Zamestnanec nepoužíva SketchUp a dodržiava firemné pravidlá.")


def show_activity_comparison_card(comparison, avg_sales):
    """Zobrazí kartu porovnania aktivity - BEZ HTML verzia"""
    
    # Výpočet odchýlky od priemeru
    if comparison['average_value'] > 0:
        deviation_pct = ((comparison['employee_value'] - comparison['average_value']) / comparison['average_value']) * 100
    else:
        deviation_pct = 0 if comparison['employee_value'] == 0 else 100
    
    # OPRAVENÝ výpočet efektivity - ochrana pred delením nulou
    if comparison['employee_value'] > 0:
        efficiency = comparison['sales'] / comparison['employee_value']
    else:
        efficiency = 0  # Ak nie je aktivita, efektivita je nula
    
    if comparison['average_value'] > 0:
        avg_efficiency = avg_sales / comparison['average_value']
    else:
        avg_efficiency = 0
    
    # Určenie statusu s lepšou logikou
    if comparison['category'] == 'productivity':
        # Pre produktívne aktivity (mail, SykoraShop)
        if comparison['employee_value'] == 0:
            status = 'Žiadna aktivita'
            color = '#6b7280'
        elif efficiency > avg_efficiency * 1.2:
            status = 'Výborné'
            color = '#10b981'
        elif efficiency >= avg_efficiency * 0.8:
            status = 'Dobré'
            color = '#3b82f6'
        else:
            status = 'Pozor'
            color = '#f59e0b'
    else:
        # Pre ostatné aktivity
        if comparison['employee_value'] == 0 and comparison['average_value'] == 0:
            status = 'Bez aktivity'
            color = '#6b7280'
        elif efficiency > avg_efficiency:
            status = 'Efektívne'
            color = '#10b981'
        elif efficiency >= avg_efficiency * 0.7:
            status = 'Priemerné'
            color = '#6b7280'
        else:
            status = 'Neefektívne'
            color = '#ef4444'
    
    # OPRAVENÉ formátovanie času
    def format_minutes(minutes):
        if minutes == 0:
            return "0h 0m"
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours}h {mins}m"
    
    emp_time = format_minutes(comparison['employee_value'])
    avg_time = format_minutes(comparison['average_value'])
    
    # ✅ NOVÉ: Použitie Streamlit kontajnerov namiesto HTML
    with st.container():
        st.markdown(f"### {comparison['title']}")
        st.caption(comparison['description'])
        
        # Metriky v stĺpcoch
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Zamestnanec", emp_time)
        
        with col2:
            st.metric("Priemer", avg_time)
        
        with col3:
            st.metric("Status", status)
        
        # Efektivita v ďalšom riadku
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("📈 Efektivita", f"{efficiency:,.0f} Kč/min")
        
        with col2:
            st.metric("📊 Odchýlka od priemeru", f"{deviation_pct:+.1f}%")
    
    # Oddeľovač
    st.divider()
    
    # Graf porovnania iba ak sú relevantné dáta
    if comparison['employee_value'] > 0 or comparison['average_value'] > 0:
        create_comparison_chart(comparison, avg_efficiency, efficiency)


def create_comparison_chart(comparison, avg_efficiency, employee_efficiency):
    """Vytvorí graf porovnania"""
    
    fig = go.Figure()
    
    # Stĺpce pre porovnanie času
    fig.add_trace(go.Bar(
        name='Čas (minúty)',
        x=['Zamestnanec', 'Priemer firmy'],
        y=[comparison['employee_value'], comparison['average_value']],
        marker_color=['#60a5fa', '#9ca3af'],
        yaxis='y',
        offsetgroup=1
    ))
    
    # Čiara pre efektivitu
    fig.add_trace(go.Scatter(
        name='Efektivita (Kč/min)',
        x=['Zamestnanec', 'Priemer firmy'],
        y=[employee_efficiency, avg_efficiency],
        mode='lines+markers',
        marker_color='#10b981',
        line=dict(width=3),
        yaxis='y2'
    ))
    
    
    # Získanie dark layout a úprava
    layout_settings = get_dark_plotly_layout()
    layout_settings.update({
        'title': {
            'text': f"Porovnanie: {comparison['title']}",
            **get_dark_plotly_title_style()
        },
        'xaxis': {
            **layout_settings['xaxis'],
            'title': ''
        },
        'yaxis': {
            **layout_settings['yaxis'],
            'title': 'Čas (minúty)', 
            'side': 'left'
        },
        'yaxis2': {'title': 'Efektivita (Kč/min)', 'side': 'right', 'overlaying': 'y'},
        'height': 350,
        'legend': {'x': 0, 'y': 1}
    })
    
    fig.update_layout(**layout_settings)
    
    st.plotly_chart(fig, use_container_width=True)


def calculate_company_averages(analyzer):
    """Vypočíta priemerné hodnoty pre celú firmu"""
    
    total_sketchup = 0
    total_mail = 0
    total_sykorashop = 0
    total_internet = 0
    total_sales = 0
    employee_count = 0
    
    for emp in analyzer.sales_employees:
        employee_details = get_employee_detailed_activity(analyzer, emp['name'])
        
        total_sketchup += employee_details.get('sketchup_time', 0)
        total_mail += employee_details.get('mail_time', 0)
        total_sykorashop += employee_details.get('sykorashop_time', 0)
        total_internet += employee_details.get('total_internet_time', 0)
        total_sales += emp.get('total_sales', 0)
        employee_count += 1
    
    if employee_count == 0:
        return {}
    
    return {
        'sketchup_avg': total_sketchup / employee_count,
        'mail_avg': total_mail / employee_count,
        'sykorashop_avg': total_sykorashop / employee_count,
        'total_internet_avg': total_internet / employee_count,
        'sales_avg': total_sales / employee_count
    }


def get_employee_detailed_activity(analyzer, employee_name):
    """ROZŠÍRENÁ verzia s debug informáciami"""
    
    canonical_name = analyzer.get_canonical_name(employee_name)
    matching_names = [name for name, canon in analyzer.name_mapping.items() if canon == canonical_name]
    
    details = {
        'sketchup_time': 0,
        'mail_time': 0,
        'sykorashop_time': 0,
        'total_internet_time': 0,
        'hry_time': 0,
        'is_sykora_time': 0,
        'helios_time': 0,
        'imos_time': 0
    }
    
    # ✅ ROZŠÍRENÝ debug pre aplikačné dáta
    if hasattr(analyzer, 'applications_data') and analyzer.applications_data is not None:
        app_records = analyzer.applications_data[analyzer.applications_data['Osoba ▲'].isin(matching_names)]
        
        for _, row in app_records.iterrows():
            chat_time = time_to_minutes(row.get('Chat', '0:00'))
            details['sketchup_time'] += chat_time
            
            details['mail_time'] += time_to_minutes(row.get('Mail', '0:00'))
            details['helios_time'] += time_to_minutes(row.get('Helios Green', '0:00'))
            details['imos_time'] += time_to_minutes(row.get('Imos - program', '0:00'))
    
    # Internet dáta
    if hasattr(analyzer, 'internet_data') and analyzer.internet_data is not None:
        internet_records = analyzer.internet_data[analyzer.internet_data['Osoba ▲'].isin(matching_names)]
        
        for _, row in internet_records.iterrows():
            details['mail_time'] += time_to_minutes(row.get('Mail', '0:00'))
            details['sykorashop_time'] += time_to_minutes(row.get('SykoraShop', '0:00'))
            details['hry_time'] += time_to_minutes(row.get('Hry', '0:00'))
            details['is_sykora_time'] += time_to_minutes(row.get('IS Sykora', '0:00'))
            details['total_internet_time'] += time_to_minutes(row.get('Čas celkem ▼', '0:00'))
    
    return details


def show_intelligent_recommendations(analyzer, employee_name, analysis):
    """4️⃣ Inteligentné odporúčania na základe detailných meraní - OPRAVENÉ"""
    st.markdown("## 💡 Personalizované odporúčania")
    
    employee_details = get_employee_detailed_activity(analyzer, employee_name)
    all_averages = calculate_company_averages(analyzer)
    sales = analysis['sales_performance']['total_sales']
    
    recommendations = []
    
    # OPRAVENÁ Mail analýza - lepšie formátovanie
    mail_vs_avg = employee_details.get('mail_time', 0) - all_averages.get('mail_avg', 0)
    if mail_vs_avg > 60:  # Viac ako hodinu nad priemerom
        # OPRAVENÉ formátovanie času
        hours = int(mail_vs_avg // 60)
        mins = int(mail_vs_avg % 60)
        time_diff = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
        
        recommendations.append({
            'type': 'warning',
            'title': '📧 Príliš veľa času na mailoch',
            'description': f'Trávite {time_diff} viac na mailoch ako priemer. Zvážte efektívnejšiu komunikáciu.',
            'action': 'Nastavte si konkrétne časy pre kontrolu mailov, napr. 3x denne po 30 minút.'
        })
    elif mail_vs_avg < -30:  # Menej ako 30 min pod priemerom
        recommendations.append({
            'type': 'good',
            'title': '📧 Efektívna mailová komunikácia',
            'description': 'Vaša mailová komunikácia je pod priemerom, čo je pozitívne pre produktivitu.',
            'action': 'Pokračujte v efektívnom prístupe k elektronickej komunikácii.'
        })
    
    # ✅ OPRAVENÁ INDENTÁCIA - SketchUp analýza
    sketchup_time = employee_details.get('sketchup_time', 0)
    sketchup_avg = all_averages.get('sketchup_avg', 0)

    if sketchup_time > 0:  # Akýkoľvek čas v SketchUp je problém
        # Výpočet pomeru SketchUp/predaj
        sketchup_sales_ratio = sketchup_time / max(sales, 1) * 1000000  # Minúty na milión Kč
        
        if sales < 1000000:  # Nízky predaj + SketchUp = veľký problém
            recommendations.append({
                'type': 'critical',
                'title': '⚠️ SketchUp + nízky predaj = podozrenie',
                'description': f'Používate SketchUp {sketchup_time//60}h {sketchup_time%60}m, ale máte nízky predaj {sales:,.0f} Kč. Možno pracujete pre niekoho iného?',
                'action': 'URGENT: Kontrola s vedúcim - na čom pracujete v SketchUp? Všetka práca by mala ísť cez firmu.'
            })
        elif sketchup_time > 60:  # Viac ako hodina SketchUp = pozor
            recommendations.append({
                'type': 'warning', 
                'title': '💻 Príliš veľa času v SketchUp',
                'description': f'Trávite {sketchup_time//60}h {sketchup_time%60}m v SketchUp. Firmou stanovený cieľ je úplne prestať používať tento program.',
                'action': 'Presuňte všetku prácu do firemných nástrojov. Konzultujte alternatívy s IT oddelením.'
            })
        else:  # Menej ako hodina, ale stále problém
            recommendations.append({
                'type': 'warning',
                'title': '💻 Minimálne používanie SketchUp',
                'description': f'Používate SketchUp {sketchup_time} minút. Aj minimálne používanie je neželané.',
                'action': 'Úplne prestaňte používať SketchUp. Všetka práca by mala byť v firemných nástrojoch.'
            })
            
    elif sketchup_avg > 0:  # Tento zamestnanec nepoužíva, ale iní áno
        recommendations.append({
            'type': 'good',
            'title': '✅ Nepoužívate SketchUp - výborne!',
            'description': f'Správne nedoužívate SketchUp, zatiaľ čo priemer firmy je {sketchup_avg//60}h {sketchup_avg%60}m.',
            'action': 'Pokračujte v používaní iba firemných nástrojov. Ste vzorom pre ostatných.'
        })
    else:  # Nikto nepoužíva SketchUp
        recommendations.append({
            'type': 'good', 
            'title': '✅ SketchUp - celofirmový úspech',
            'description': 'Ani vy ani ostatní nepoužívate SketchUp. Firemný cieľ je splnený.',
            'action': 'Pokračujte v používaní iba firemných nástrojov.'
        })
    
    # Predajná analýza
    avg_sales = all_averages.get('sales_avg', 3000000)
    if sales < avg_sales * 0.7:
        recommendations.append({
            'type': 'critical',
            'title': '💰 Predajná výkonnosť pod očakávaním',
            'description': f'Váš predaj {sales:,.0f} Kč je výrazne pod priemerom {avg_sales:,.0f} Kč.',
            'action': 'Konzultácia s vedúcim o stratégii predaja. Možná potreba školenia alebo presmerovanie úloh.'
        })
    elif sales > avg_sales * 1.3:
        recommendations.append({
            'type': 'good',
            'title': '💰 Výborná predajná výkonnosť',
            'description': f'Váš predaj {sales:,.0f} Kč je výrazne nad priemerom. Skvelá práca!',
            'action': 'Zvážte zdieľanie svojich najlepších praktík s ostatnými kolegami.'
        })
    
    # Zobrazenie odporúčaní
    for rec in recommendations:
        css_class = f"recommendation-{rec['type']}"
        st.markdown(f"""
        <div class="comparison-card {css_class}">
            <h4 style="margin: 0 0 10px 0;">{rec['title']}</h4>
            <p style="color: #d1d5db; margin: 10px 0;">{rec['description']}</p>
            <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; margin-top: 10px;">
                <strong>💡 Akčný plán:</strong> {rec['action']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    if not recommendations:
        st.markdown("""
        <div class="comparison-card recommendation-good">
            <h4 style="color: #10b981; margin: 0 0 10px 0;">✅ Vyvážený pracovný profil</h4>
            <p style="color: #d1d5db;">Vaše aktivity sú v rozumných medziach oproti firemným priemerom.</p>
            <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; margin-top: 10px;">
                <strong>💡 Akčný plán:</strong> Pokračujte v súčasnom nastavení a hľadajte možnosti na ďalšie zlepšenie.
            </div>
        </div>
        """, unsafe_allow_html=True)
