import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import re
from pathlib import Path
from ui.styling import get_dark_plotly_layout, get_dark_plotly_title_style
from core.utils import time_to_minutes


def calculate_company_averages(analyzer, data_type='internet'):
    """Vypočíta skutočné firemné priemery z dát - VŠETKÝCH ZAMESTNANCOV"""
    if not analyzer:
        return {}
    
    return analyzer.get_all_employees_averages(data_type)


def calculate_employee_averages(analyzer, employee_name, data_type='internet'):
    """Vypočíta individuálne priemery konkrétneho zamestnanca"""
    if not analyzer:
        return {}
    
    return analyzer.get_employee_averages(employee_name, data_type)


def calculate_employee_daily_averages(analyzer, employee_name, data_type='internet'):
    """Vypočíta denné priemery konkrétneho zamestnanca (hodiny za deň) - OPRAVENÉ"""
    if not analyzer:
        return {}
    
    # ✅ JEDNODUCHO použiť analyzer funkciu
    return analyzer.get_employee_daily_averages(employee_name, data_type)


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
    
    # ✅ NOVÉ MESAČNÉ GRAFY AKTIVÍT - pod grafom predaja
    st.markdown("<br>", unsafe_allow_html=True)
    create_monthly_activity_charts(internet_data, app_data, analyzer, selected_employee)
    
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
    create_internet_analysis(internet_data, analyzer, selected_employee)
    
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
    create_application_analysis(app_data, analyzer, selected_employee)
    
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


def create_monthly_activity_charts(internet_data, app_data, analyzer, employee_name):
    """Vytvorí mesačné stĺpcové grafy pre SketchUp a Mail aktivity"""
    
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
    
    st.markdown("### 📊 Mesačná analýza aktivít")
    
    # OPRAVENÉ: Používame analyzer pre mesačné dáta
    col1, col2 = st.columns(2)
    
    with col1:
        create_monthly_sketchup_chart(internet_data, analyzer, employee_name)
    
    with col2:
        create_monthly_mail_chart(internet_data, app_data, analyzer, employee_name)
    
    st.markdown("</div>", unsafe_allow_html=True)


def create_monthly_sketchup_chart(internet_data, analyzer, employee_name):
    """Vytvorí mesačný stĺpcový graf SketchUp aktivity - VYLEPŠENÉ s timeline dátami"""
    
    st.markdown("#### 🎨 Mesačná aktivita - SketchUp")
    
    # ✅ VYLEPŠENIE: Pokús sa použiť timeline dáta pre presnejšie mesačné agregácie
    timeline_data = analyzer.get_employee_daily_timeline(employee_name, 'internet') if analyzer else pd.DataFrame()
    
    sketchup_monthly = {}
    
    if not timeline_data.empty and 'Date' in timeline_data.columns and 'Chat' in timeline_data.columns:
        # Máme timeline dáta - agreguj presne podľa dátumov
        timeline_data['Month'] = timeline_data['Date'].dt.strftime('%Y-%m')
        
        for month in timeline_data['Month'].unique():
            month_data = timeline_data[timeline_data['Month'] == month]
            total_minutes = 0
            
            for _, row in month_data.iterrows():
                chat_value = row.get('Chat', '0:00')
                if pd.notna(chat_value) and str(chat_value) not in ['0:00', 'nan', '']:
                    total_minutes += time_to_minutes(str(chat_value))
            
            if total_minutes > 0:
                sketchup_monthly[month] = total_minutes / 60  # Konvertuj na hodiny
    else:
        # Fallback na pôvodnú analyzer funkciu
        monthly_data = analyzer.get_employee_monthly_data(employee_name, 'internet') if analyzer else {}
        
        # Extrahuj len Chat (SketchUp) dáta z mesačných údajov 
        for month, activities in monthly_data.items():
            if 'Chat' in activities:
                sketchup_monthly[month] = activities['Chat'] / 60  # Konvertuj na hodiny
    
    if not sketchup_monthly:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #10b981, #059669);
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            color: white;
            margin: 1rem 0;
        ">
            <h3 style="margin: 0; font-size: 1.2rem;">✅ VÝBORNE: Žiadne používanie SketchUp!</h3>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Usporiadaj chronologicky
    sorted_months = sorted(sketchup_monthly.keys())
    months_display = [month.replace('-', '/') for month in sorted_months]
    values = [sketchup_monthly[month] for month in sorted_months]
    
    # Farby podľa rizika
    colors = []
    for val in values:
        if val > 20:  # Viac ako 20h
            colors.append('#ef4444')  # Kritická červená
        elif val > 10:  # 10-20h
            colors.append('#f59e0b')  # Varovná oranžová
        elif val > 5:   # 5-10h
            colors.append('#eab308')  # Žltá
        else:          # Menej ako 5h
            colors.append('#f97316')  # Oranžová
    
    # Graf
    fig = go.Figure(data=[go.Bar(
        x=months_display,
        y=values,
        marker=dict(
            color=colors,
            line=dict(color='rgba(255,255,255,0.3)', width=1)
        ),
        text=[f'{v:.1f}h' if v > 0 else '0h' for v in values],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>SketchUp: %{y:.1f}h<extra></extra>'
    )])
    
    layout = get_dark_plotly_layout()
    layout.update({
        'title': dict(
            text=f"🎨 SketchUp aktivita - Celkom: {sum(values):.1f}h",
            font=dict(size=16, color='white'),
            x=0.5
        ),
        'height': 350,
        'margin': dict(l=40, r=40, t=60, b=40),
        'xaxis': dict(title='Mesiace', color='white'),
        'yaxis': dict(title='Hodiny', color='white')
    })
    
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)
    
    # Upozornenie ak má aktivity
    total_hours = sum(values)
    if total_hours > 40:
        st.error(f"🚨 KRITICKÉ: Celkom {total_hours:.1f}h SketchUp - možná práca pre iných!")
    elif total_hours > 20:
        st.warning(f"⚠️ VYSOKÉ RIZIKO: {total_hours:.1f}h SketchUp")
    elif total_hours > 0:
        st.info(f"ℹ️ NÍZKE RIZIKO: {total_hours:.1f}h SketchUp")


def create_monthly_mail_chart(internet_data, app_data, analyzer, employee_name):
    """Vytvorí mesačný stĺpcový graf Mail aktivity - VYLEPŠENÉ s timeline dátami"""
    
    st.markdown("#### 📧 Mesačná aktivita - Mail")
    
    mail_monthly = {}
    
    # ✅ VYLEPŠENIE: Použij timeline dáta pre presnejšie mesačné agregácie
    internet_timeline = analyzer.get_employee_daily_timeline(employee_name, 'internet') if analyzer else pd.DataFrame()
    app_timeline = analyzer.get_employee_daily_timeline(employee_name, 'applications') if analyzer else pd.DataFrame()
    
    # Agreguj Mail z internet timeline
    if not internet_timeline.empty and 'Date' in internet_timeline.columns and 'Mail' in internet_timeline.columns:
        internet_timeline['Month'] = internet_timeline['Date'].dt.strftime('%Y-%m')
        
        for month in internet_timeline['Month'].unique():
            month_data = internet_timeline[internet_timeline['Month'] == month]
            total_minutes = 0
            
            for _, row in month_data.iterrows():
                mail_value = row.get('Mail', '0:00')
                if pd.notna(mail_value) and str(mail_value) not in ['0:00', 'nan', '']:
                    total_minutes += time_to_minutes(str(mail_value))
            
            if total_minutes > 0:
                if month not in mail_monthly:
                    mail_monthly[month] = 0
                mail_monthly[month] += total_minutes / 60  # Konvertuj na hodiny
    
    # Agreguj Mail z applications timeline
    if not app_timeline.empty and 'Date' in app_timeline.columns and 'Mail' in app_timeline.columns:
        app_timeline['Month'] = app_timeline['Date'].dt.strftime('%Y-%m')
        
        for month in app_timeline['Month'].unique():
            month_data = app_timeline[app_timeline['Month'] == month]
            total_minutes = 0
            
            for _, row in month_data.iterrows():
                mail_value = row.get('Mail', '0:00')
                if pd.notna(mail_value) and str(mail_value) not in ['0:00', 'nan', '']:
                    total_minutes += time_to_minutes(str(mail_value))
            
            if total_minutes > 0:
                if month not in mail_monthly:
                    mail_monthly[month] = 0
                mail_monthly[month] += total_minutes / 60  # Konvertuj na hodiny
    
    # Fallback ak timeline dáta nie sú dostupné
    if not mail_monthly:
        internet_monthly = analyzer.get_employee_monthly_data(employee_name, 'internet') if analyzer else {}
        app_monthly = analyzer.get_employee_monthly_data(employee_name, 'applications') if analyzer else {}
        
        # Mail z internet dát
        for month, activities in internet_monthly.items():
            if 'Mail' in activities:
                if month not in mail_monthly:
                    mail_monthly[month] = 0
                mail_monthly[month] += activities['Mail'] / 60  # Konvertuj na hodiny
        
        # Mail z aplikačných dát  
        for month, activities in app_monthly.items():
            if 'Mail' in activities:
                if month not in mail_monthly:
                    mail_monthly[month] = 0
                mail_monthly[month] += activities['Mail'] / 60  # Konvertuj na hodiny
    
    if not mail_monthly:
        st.info("ℹ️ Žiadne Mail aktivity nájdené")
        return
    
    # Usporiadaj chronologicky
    sorted_months = sorted(mail_monthly.keys())
    months_display = [month.replace('-', '/') for month in sorted_months]
    values = [mail_monthly[month] for month in sorted_months]
    
    # Farby pre Mail (pozitívne aktivity)
    colors = ['#3b82f6' for _ in values]  # Modrá farba pre komunikáciu
    
    # Graf
    fig = go.Figure(data=[go.Bar(
        x=months_display,
        y=values,
        marker=dict(
            color=colors,
            line=dict(color='rgba(255,255,255,0.3)', width=1)
        ),
        text=[f'{v:.1f}h' if v > 0 else '0h' for v in values],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Mail: %{y:.1f}h<extra></extra>'
    )])
    
    layout = get_dark_plotly_layout()
    layout.update({
        'title': dict(
            text=f"📧 Mail aktivita - Celkom: {sum(values):.1f}h",
            font=dict(size=16, color='white'),
            x=0.5
        ),
        'height': 350,
        'margin': dict(l=40, r=40, t=60, b=40),
        'xaxis': dict(title='Mesiace', color='white'),
        'yaxis': dict(title='Hodiny', color='white')
    })
    
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)
    
    # Pozitívne hodnotenie
    total_hours = sum(values)
    if total_hours > 40:
        st.success(f"✅ VÝBORNE: {total_hours:.1f}h Mail komunikácie")
    elif total_hours > 20:
        st.info(f"👍 DOBRÉ: {total_hours:.1f}h Mail komunikácie")
    elif total_hours > 0:
        st.info(f"📧 {total_hours:.1f}h Mail komunikácie")
    else:
        st.warning("⚠️ Žiadna Mail komunikácia")


def get_employee_monthly_internet_data(analyzer, employee_name):
    """Získa mesačné internet dáta bez agregácie - zachová Source_File"""
    
    if not hasattr(analyzer, 'data_path') or not analyzer.data_path:
        return None
    
    data_path = Path(analyzer.data_path)
    if not data_path.exists():
        return None
    
    try:
        all_files = list(data_path.glob("*.xlsx"))
        internet_files = [f for f in all_files if 'internet' in f.name.lower() and 'application' not in f.name.lower()]
        
        if not internet_files:
            return None
        
        # Nájdi matchujúce mená v hlavných dátach
        matching_names = analyzer.find_matching_names(employee_name, analyzer.internet_data) if analyzer.internet_data is not None else [employee_name]
        
        monthly_data = []
        
        for file in internet_files:
            try:
                df = pd.read_excel(file, header=8)
                df_clean = df.dropna(subset=['Osoba ▲'])
                df_final = df_clean[~df_clean['Osoba ▲'].astype(str).str.startswith('*')]
                
                # Filtruj pre tohto zamestnanca
                employee_rows = df_final[df_final['Osoba ▲'].isin(matching_names)]
                
                if len(employee_rows) > 0:
                    for _, row in employee_rows.iterrows():
                        row_dict = row.to_dict()
                        row_dict['Source_File'] = file.name
                        monthly_data.append(row_dict)
                        
            except Exception:
                continue
        
        if not monthly_data:
            return None
        
        return pd.DataFrame(monthly_data)
        
    except Exception:
        return None


def get_employee_monthly_applications_data(analyzer, employee_name):
    """Získa mesačné aplikačné dáta bez agregácie - zachová Source_File"""
    
    if not hasattr(analyzer, 'data_path') or not analyzer.data_path:
        return None
    
    data_path = Path(analyzer.data_path)
    if not data_path.exists():
        return None
    
    try:
        all_files = list(data_path.glob("*.xlsx"))
        app_files = [f for f in all_files if 'application' in f.name.lower() and 'internet' not in f.name.lower()]
        
        if not app_files:
            return None
        
        # Nájdi matchujúce mená v hlavných dátach
        matching_names = analyzer.find_matching_names(employee_name, analyzer.applications_data) if analyzer.applications_data is not None else [employee_name]
        
        monthly_data = []
        
        for file in app_files:
            try:
                df = pd.read_excel(file, header=8)
                df_clean = df.dropna(subset=['Osoba ▲'])
                df_final = df_clean[~df_clean['Osoba ▲'].astype(str).str.startswith('*')]
                
                # Filtruj pre tohto zamestnanca
                employee_rows = df_final[df_final['Osoba ▲'].isin(matching_names)]
                
                if len(employee_rows) > 0:
                    for _, row in employee_rows.iterrows():
                        row_dict = row.to_dict()
                        row_dict['Source_File'] = file.name
                        monthly_data.append(row_dict)
                        
            except Exception:
                continue
        
        if not monthly_data:
            return None
        
        return pd.DataFrame(monthly_data)
        
    except Exception:
        return None


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
            'gridcolor': 'rgba(255,255,255,0.1)'
        },
        'plot_bgcolor': 'rgba(31, 41, 55, 0.8)',
        'paper_bgcolor': 'rgba(17, 24, 39, 1)',
        'margin': dict(l=80, r=30, t=80, b=60)
    })
    
    fig_monthly.update_layout(**layout_settings)
    st.plotly_chart(fig_monthly, use_container_width=True)


def create_employee_internet_chart(internet_data, analyzer, employee_name):
    """Graf 1: CELKOVÉ aktivity zamestnanca za sledované obdobie (SÚČTY)"""
    st.markdown("#### 👤 Vaše aktivity (celkom)")
    
    # Získaj CELKOVÉ hodiny zamestnanca za obdobie (súčty)
    total_activities = analyzer.get_employee_averages(employee_name, 'internet')
    
    # Filtrovanie len aktivít s hodnotami > 0
    filtered_activities = {k: v for k, v in total_activities.items() if v > 0}
    
    if not filtered_activities:
        st.info("ℹ️ Žiadne aktivity")
        return

    # Kolačový graf
    colors = []
    for activity in filtered_activities.keys():
        if activity in ['Mail', 'IS Sykora', 'SykoraShop', 'Web k praci']:
            colors.append('#10b981')  # Zelená
        elif activity == 'Chat':
            colors.append('#ef4444')  # Červená
        else:
            colors.append('#f59e0b')  # Žltá

    # Pridaj informáciu o celkovom čase do titulku
    total_hours = sum(filtered_activities.values())
    
    fig = go.Figure(data=[go.Pie(
        labels=list(filtered_activities.keys()),
        values=list(filtered_activities.values()),
        marker=dict(colors=colors, line=dict(color='rgba(255,255,255,0.3)', width=1)),
        textfont=dict(size=10, color='white'),
        hole=0.3,
        textinfo='label+percent+value',
        texttemplate='%{label}<br>%{value:.1f}h<br>%{percent}'
    )])
    
    layout = get_dark_plotly_layout()
    layout.update({
        'title': dict(
            text=f"👤 Celkové aktivity<br><sub>Spolu: {total_hours:.1f}h</sub>",
            font=dict(color='white', size=14),
            x=0.5
        ),
        'height': 300,
        'showlegend': False,  # Vypnúť legendu pre lepší prehľad
        'margin': dict(l=20, r=20, t=60, b=20)
    })
    
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)


def create_average_internet_chart(internet_data, analyzer, employee_name):
    """Graf 2: SKUTOČNÝ denný priemer zamestnanca"""
    st.markdown("#### 📊 Priemer za deň")
    
    # Získaj SKUTOČNÉ denné priemerné hodnoty tohto zamestnanca
    avg_activities = analyzer.get_employee_daily_averages(employee_name, 'internet')
    
    # Filtrovanie len aktivít s hodnotami > 0
    filtered_activities = {k: v for k, v in avg_activities.items() if v > 0}
    
    if not filtered_activities:
        st.info("Žiadne priemerné dáta dostupné")
        return
    
    colors = []
    for activity in filtered_activities.keys():
        if activity in ['Mail', 'IS Sykora', 'SykoraShop', 'Web k praci']:
            colors.append('#3b82f6')  # Modrá pre produktívne
        elif activity == 'Chat':
            colors.append('#f59e0b')  # Oranžová pre SketchUp/Chat  
        else:
            colors.append('#ef4444')  # Červená pre neproduktívne
    
    # Pridaj informáciu o celkovom čase do titulku
    total_hours = sum(filtered_activities.values())
    
    fig = go.Figure(data=[go.Pie(
        labels=list(filtered_activities.keys()),
        values=list(filtered_activities.values()),
        marker=dict(colors=colors, line=dict(color='rgba(255,255,255,0.3)', width=1)),
        textfont=dict(size=10, color='white'),
        hole=0.3,
        textinfo='label+percent+value',
        texttemplate='%{label}<br>%{value:.1f}h<br>%{percent}'
    )])
    
    layout = get_dark_plotly_layout()
    layout.update({
        'title': dict(
            text=f"📊 Denný priemer<br><sub>Priemer: {total_hours:.1f}h/deň</sub>",
            font=dict(color='white', size=14),
            x=0.5
        ),
        'height': 300,
        'showlegend': False,  # Vypnúť legendu
        'margin': dict(l=20, r=20, t=60, b=20)
    })
    
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)
    
    # Varovanie ak denný priemer je nemožný (viac ako 24h)
    if total_hours > 24:
        st.error(f"🚨 CHYBA: Denný priemer {total_hours:.1f}h je nemožný!")
    elif total_hours > 16:
        st.warning(f"⚠️ VYSOKÝ: Denný priemer {total_hours:.1f}h je podozrivý")


def create_company_internet_chart(analyzer, employee_name):
    """Graf 3: Firemný priemer všetkých zamestnancov"""
    st.markdown("#### 🏢 Firemný priemer")
    
    # Získaj skutočné firemné priemery (všetkých zamestnancov)
    company_activities = calculate_company_averages(analyzer, 'internet')
    
    # Filtrovanie len aktivít s hodnotami > 0  
    filtered_activities = {k: v for k, v in company_activities.items() if v > 0}
    
    if not filtered_activities:
        st.info("Žiadne firemné dáta dostupné")
        return
    
    colors = []
    for activity in filtered_activities.keys():
        if activity in ['Mail', 'IS Sykora', 'SykoraShop', 'Web k praci']:
            colors.append('#8b5cf6')  # Fialová pre firmu
        elif activity == 'Chat':
            colors.append('#ef4444')  # Červená pre SketchUp/Chat
        else:
            colors.append('#f59e0b')  # Oranžová pre ostatné
    
    # Pridaj informáciu o celkovom čase do titulku
    total_hours = sum(filtered_activities.values())
    
    fig = go.Figure(data=[go.Pie(
        labels=list(filtered_activities.keys()),
        values=list(filtered_activities.values()),
        marker=dict(colors=colors, line=dict(color='rgba(255,255,255,0.3)', width=1)),
        textfont=dict(size=10, color='white'),
        hole=0.3,
        textinfo='label+percent+value',
        texttemplate='%{label}<br>%{value:.1f}h<br>%{percent}'
    )])
    
    layout = get_dark_plotly_layout()
    layout.update({
        'title': dict(
            text=f"🏢 Firemný priemer<br><sub>Priemer: {total_hours:.1f}h/deň</sub>",
            font=dict(color='white', size=14),
            x=0.5
        ),
        'height': 300,
        'showlegend': False,  # Vypnúť legendu
        'margin': dict(l=20, r=20, t=60, b=20)
    })
    
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)
    
    # Varovanie ak firemný priemer je nemožný (viac ako 24h)
    if total_hours > 24:
        st.error(f"🚨 CHYBA: Firemný priemer {total_hours:.1f}h je nemožný!")
    elif total_hours > 16:
        st.warning(f"⚠️ VYSOKÝ: Firemný priemer {total_hours:.1f}h je podozrivý")


def create_internet_analysis(internet_data, analyzer, employee_name):
    """Vytvorí analýzu internet aktivít s 3 grafmi vedľa seba"""
    
    st.markdown("### 🌐 Analýza internetových aktivít")
    
    if internet_data is None or internet_data.empty:
        st.warning(f"⚠️ Žiadne internet dáta pre {employee_name}")
        return
    
    # 3 stĺpce pre 3 grafy
    col1, col2, col3 = st.columns(3)
    
    with col1:
        create_employee_internet_chart(internet_data, analyzer, employee_name)
    
    with col2:
        create_average_internet_chart(internet_data, analyzer, employee_name)
    
    with col3:
        create_company_internet_chart(analyzer, employee_name)


def create_employee_application_chart(app_data, analyzer, employee_name):
    """Graf 1: CELKOVÉ aplikačné aktivity zamestnanca za sledované obdobie (SÚČTY)"""
    st.markdown("#### 👤 Vaše aplikácie (celkom)")
    
    # Získaj CELKOVÉ hodiny zamestnanca za obdobie (súčty)
    total_activities = analyzer.get_employee_averages(employee_name, 'applications')
    
    # Filtrovanie len aktivít s hodnotami > 0
    filtered_activities = {k: v for k, v in total_activities.items() if v > 0}
    
    if not filtered_activities:
        st.info("ℹ️ Žiadne aplikačné aktivity")
        return

    colors = []
    for activity in filtered_activities.keys():
        if activity in ['Helios Green', 'Imos - program', 'Programy', 'Půdorysy']:
            colors.append('#10b981')  # Zelená
        elif activity == 'Mail':
            colors.append('#3b82f6')  # Modrá
        elif activity == 'Chat':
            colors.append('#ef4444')  # Červená
        else:
            colors.append('#f59e0b')  # Žltá

    # Pridaj informáciu o celkovom čase do titulku
    total_hours = sum(filtered_activities.values())

    fig = go.Figure(data=[go.Pie(
        labels=list(filtered_activities.keys()),
        values=list(filtered_activities.values()),
        marker=dict(colors=colors, line=dict(color='rgba(255,255,255,0.3)', width=1)),
        textfont=dict(size=10, color='white'),
        hole=0.3,
        textinfo='label+percent+value',
        texttemplate='%{label}<br>%{value:.1f}h<br>%{percent}'
    )])
    
    layout = get_dark_plotly_layout()
    layout.update({
        'title': dict(
            text=f"👤 Celkové aplikácie<br><sub>Spolu: {total_hours:.1f}h</sub>",
            font=dict(color='white', size=14),
            x=0.5
        ),
        'height': 300,
        'showlegend': False,  # Vypnúť legendu
        'margin': dict(l=20, r=20, t=60, b=20)
    })
    
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)


def create_average_application_chart(app_data, analyzer, employee_name):
    """Graf 2: SKUTOČNÝ denný priemer aplikácií zamestnanca"""
    st.markdown("#### 📊 Priemer za deň")
    
    # Získaj SKUTOČNÉ denné priemerné hodnoty aplikácií tohto zamestnanca
    avg_activities = analyzer.get_employee_daily_averages(employee_name, 'applications')
    
    # Filtrovanie len aktivít s hodnotami > 0
    filtered_activities = {k: v for k, v in avg_activities.items() if v > 0}
    
    if not filtered_activities:
        st.info("Žiadne priemerné aplikačné dáta dostupné")
        return
    
    colors = []
    for activity in filtered_activities.keys():
        if activity in ['Helios Green', 'Imos - program', 'Programy', 'Půdorysy']:
            colors.append('#3b82f6')  # Modrá pre produktívne
        elif activity == 'Mail':
            colors.append('#10b981')  # Zelená pre komunikáciu
        elif activity == 'Chat':
            colors.append('#f59e0b')  # Oranžová (ale tento by nemal byť v aplikáciách)
        else:
            colors.append('#6b7280')  # Sivá pre ostatné
    
    # Pridaj informáciu o celkovom čase do titulku
    total_hours = sum(filtered_activities.values())
    
    fig = go.Figure(data=[go.Pie(
        labels=list(filtered_activities.keys()),
        values=list(filtered_activities.values()),
        marker=dict(colors=colors, line=dict(color='rgba(255,255,255,0.3)', width=1)),
        textfont=dict(size=10, color='white'),
        hole=0.3,
        textinfo='label+percent+value',
        texttemplate='%{label}<br>%{value:.1f}h<br>%{percent}'
    )])
    
    layout = get_dark_plotly_layout()
    layout.update({
        'title': dict(
            text=f"📊 Denný priemer<br><sub>Priemer: {total_hours:.1f}h/deň</sub>",
            font=dict(color='white', size=14),
            x=0.5
        ),
        'height': 300,
        'showlegend': False,  # Vypnúť legendu
        'margin': dict(l=20, r=20, t=60, b=20)
    })
    
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)
    
    # Varovanie ak denný priemer je nemožný (viac ako 24h)
    if total_hours > 24:
        st.error(f"🚨 CHYBA: Denný priemer {total_hours:.1f}h je nemožný!")
    elif total_hours > 16:
        st.warning(f"⚠️ VYSOKÝ: Denný priemer {total_hours:.1f}h je podozrivý")


def create_company_application_chart(analyzer, employee_name):
    """Graf 3: Firemný priemer aplikácií všetkých zamestnancov"""
    st.markdown("#### 🏢 Firemný priemer")
    
    # Získaj skutočné firemné priemery aplikácií (všetkých zamestnancov)
    company_activities = calculate_company_averages(analyzer, 'applications')
    
    # Filtrovanie len aktivít s hodnotami > 0
    filtered_activities = {k: v for k, v in company_activities.items() if v > 0}
    
    if not filtered_activities:
        st.info("Žiadne firemné aplikačné dáta dostupné")
        return
    
    colors = []
    for activity in filtered_activities.keys():
        if activity in ['Helios Green', 'Imos - program', 'Programy', 'Půdorysy']:
            colors.append('#8b5cf6')  # Fialová pre firmu
        elif activity == 'Mail':
            colors.append('#10b981')  # Zelená pre komunikáciu
        elif activity == 'Chat':
            colors.append('#f59e0b')  # Oranžová (ale tento by nemal byť v aplikáciách)
        else:
            colors.append('#6b7280')  # Sivá pre ostatné
    
    # Pridaj informáciu o celkovom čase do titulku
    total_hours = sum(filtered_activities.values())
    
    fig = go.Figure(data=[go.Pie(
        labels=list(filtered_activities.keys()),
        values=list(filtered_activities.values()),
        marker=dict(colors=colors, line=dict(color='rgba(255,255,255,0.3)', width=1)),
        textfont=dict(size=10, color='white'),
        hole=0.3,
        textinfo='label+percent+value',
        texttemplate='%{label}<br>%{value:.1f}h<br>%{percent}'
    )])
    
    layout = get_dark_plotly_layout()
    layout.update({
        'title': dict(
            text=f"🏢 Firemný priemer<br><sub>Priemer: {total_hours:.1f}h/deň</sub>",
            font=dict(color='white', size=14),
            x=0.5
        ),
        'height': 300,
        'showlegend': False,  # Vypnúť legendu
        'margin': dict(l=20, r=20, t=60, b=20)
    })
    
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)
    
    # Varovanie ak firemný priemer je nemožný (viac ako 24h)
    if total_hours > 24:
        st.error(f"🚨 CHYBA: Firemný priemer {total_hours:.1f}h je nemožný!")
    elif total_hours > 16:
        st.warning(f"⚠️ VYSOKÝ: Firemný priemer {total_hours:.1f}h je podozrivý")


def create_application_analysis(app_data, analyzer, employee_name):
    """Vytvorí analýzu aplikačných aktivít s 3 grafmi vedľa seba"""
    
    st.markdown("### 💻 Analýza aplikačných aktivít")
    
    if app_data is None or app_data.empty:
        st.warning(f"⚠️ Žiadne aplikačné dáta pre {employee_name}")
        return
    
    # 3 stĺpce pre 3 grafy
    col1, col2, col3 = st.columns(3)
    
    with col1:
        create_employee_application_chart(app_data, analyzer, employee_name)
    
    with col2:
        create_average_application_chart(app_data, analyzer, employee_name)
    
    with col3:
        create_company_application_chart(analyzer, employee_name)
