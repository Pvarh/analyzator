import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from core.studio_analyzer import StudioAnalyzer
from auth.auth import filter_data_by_user_access, can_access_city, get_user_cities, get_current_user, has_feature_access
from ui.styling import (
    apply_dark_theme, create_section_header, create_subsection_header, 
    create_simple_metric_card, get_dark_plotly_layout
)
import hashlib
import os

# Simple performance enhancement
@st.cache_data(ttl=300)  # 5 min cache
def load_studio_data_cached():
    """Cached version of studio data loading"""
    return load_studio_data()

@st.cache_data
def create_analyzer_cached(folder_hash):
    """Cached analyzer creation - invalidated when studio folder changes"""
    studio_data = load_studio_data(folder_hash)
    if studio_data is None:
        return None
    return StudioAnalyzer(studio_data)

def get_file_hash(file_path):
    """Simple file hash for cache invalidation"""
    try:
        stat = os.stat(file_path)
        return hashlib.md5(f"{file_path}:{stat.st_size}:{stat.st_mtime}".encode()).hexdigest()[:8]
    except:
        return "unknown"

def get_studio_folder_hash():
    """Hash celého data/studio priečinka pre cache invalidation"""
    try:
        studio_path = Path("data/studio")
        if not studio_path.exists():
            return "no_folder"
        
        # Získaj všetky Excel súbory a ich info
        excel_files = list(studio_path.glob("*.xlsx")) + list(studio_path.glob("*.xls"))
        
        hash_info = []
        for file_path in excel_files:
            stat = os.stat(file_path)
            hash_info.append(f"{file_path.name}:{stat.st_size}:{stat.st_mtime}")
        
        # Hash zoznam súborov + ich info
        folder_content = "|".join(sorted(hash_info))
        return hashlib.md5(folder_content.encode()).hexdigest()[:8]
    except:
        return "unknown"

# ---------------------------------------------------------------------------
# RENDER FUNCTION FOR APP.PY
# ---------------------------------------------------------------------------
def render(analyzer=None):
    """Main render function called from app.py"""
    show_studio_page()

# ---------------------------------------------------------------------------
# HLAVNÁ STRÁNKA - KOMPLETNÁ VERZIA S FILTROVANÍM
# ---------------------------------------------------------------------------
def show_studio_page():
    apply_dark_theme()
    
    # Získaj hash celého data/studio priečinka pre intelligent cache
    folder_hash = get_studio_folder_hash()
    
    # Automatické načítanie súborov z /data/studio/ - cached
    studio_data = load_studio_data(folder_hash)
    
    if studio_data is None:
        st.error("❌ Žiadne súbory nenájdené v priečinku /data/studio/")
        st.info("📁 Umiestnite Excel súbory s dátami o predaji do priečinka /data/studio/")
        return
    
    try:
        # Use cached analyzer creation with folder hash
        analyzer = create_analyzer_cached(folder_hash)
        if analyzer is None:
            raise Exception("Failed to create analyzer")
    except Exception as e:
        st.error(f"❌ Chyba pri načítaní dát: {e}")
        return
    
    if analyzer.df_active.empty:
        st.warning("⚠️ Žiadne relevantné dáta po filtrovaní!")
        return
    
    # Cache info a aktuálne dáta info
    with st.expander("ℹ️ Informácie o dátach a cache", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📁 **Aktuálny súbor:** {Path(studio_data).name}")
            st.info(f"📊 **Počet záznamov:** {len(analyzer.df_active):,}")
        with col2:
            st.info(f"🔄 **Cache hash:** `{folder_hash}`")
            st.success("✅ **Cache stav:** Dáta sa automaticky aktualizujú pri zmene súborov")
            
        # Info o zobrazovaných zamestnancoch
        current_user = get_current_user()
        if current_user and current_user.get('role') == 'admin':
            st.success("👑 **Admin:** Zobrazujú sa všetci zamestnanci")
        elif has_feature_access("studio_see_all_employees"):
            st.success("🌍 **Všetci zamestnanci:** Máte povolenie vidieť všetkých")
        else:
            user_cities = get_user_cities()
            if user_cities:
                st.info(f"🏙️ **Filtrované mestá:** {', '.join(user_cities)}")
            else:
                st.warning("⚠️ **Žiadne prístupné mestá**")
    
    # ===== 🗓️ FILTER DÁTUMU =====
    st.subheader("📅 Filter dátumu")
    
    # Zistenie rozsahu dátumov v dátach
    min_date = pd.to_datetime(analyzer.df_active['Datum real.']).min().date()
    max_date = pd.to_datetime(analyzer.df_active['Datum real.']).max().date()
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        start_date = st.date_input(
            "📅 Od dátumu",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key="studio_start_date"
        )
    
    with col2:
        end_date = st.date_input(
            "📅 Do dátumu", 
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key="studio_end_date"
        )
    
    with col3:
        if st.button("🔄 Reset", help="Resetovať na celé obdobie"):
            st.session_state.studio_start_date = min_date
            st.session_state.studio_end_date = max_date
            st.rerun()
    
    # Role-based filtering pre studio dáta
    user = get_current_user()
    
    if user and user.get('role') != 'admin':
        # Manager - aplikuj city filtering
        user_cities = user.get('cities', [])
        
        # Používame hlavný analyzer zo session_state (ak existuje)
        try:
            main_analyzer = st.session_state.get('analyzer')
            
            if main_analyzer is None:
                st.warning("⚠️ **Hlavný analyzer nie je dostupný** - Choďte najprv na Overview stránku na načítanie dát")
                return
            
            # Nájdi povolených zamestnancov v studio dátach
            allowed_employees = main_analyzer.find_matching_studio_employees(
                analyzer.df_active, user_cities
            )
            
            if allowed_employees:
                # Filtruj studio dáta len na povolených zamestnancov  
                studio_column = 'Kontaktní osoba-Jméno a příjmení'
                analyzer.df_active = analyzer.df_active[
                    analyzer.df_active[studio_column].isin(allowed_employees)
                ].copy()
            else:
                st.warning(f"⚠️ **Žiadni zamestnanci** z vašich miest neboli nájdení v studio dátach.")
                analyzer.df_active = analyzer.df_active.iloc[0:0].copy()  # Prázdny dataframe
        except Exception as e:
            st.error(f"❌ Chyba pri filtrovaní podľa miest: {e}")
    
    # Filtrovanie dát podľa vybraného dátumu
    filtered_analyzer = apply_date_filter(analyzer, start_date, end_date)
    
    if filtered_analyzer.df_active.empty:
        st.warning("⚠️ Žiadne dáta pre vybrané obdobie!")
        return
    
    # Info o filtrovanom období
    total_records = len(analyzer.df_active)
    filtered_records = len(filtered_analyzer.df_active)
    
    # Uloženie filtrovaného analyzéra do session state pre detail zamestnanca
    st.session_state['filtered_studio_analyzer'] = filtered_analyzer
    st.session_state['date_filter_info'] = {
        'start_date': start_date,
        'end_date': end_date,
        'total_records': total_records,
        'filtered_records': filtered_records
    }
    
    st.divider()
    
    # Základné štatistiky
    show_basic_stats(filtered_analyzer)
    
    # Štatistiky podľa kategórií spotrebičov
    st.divider()
    show_appliance_stats_cards(filtered_analyzer)
    
    # Mesačný predaj spotrebičov
    st.divider()
    show_monthly_sales_stats(filtered_analyzer)
    
    # Vyhľadávanie zamestnancov
    st.divider()
    st.subheader("🔍 Vyhľadávanie zamestnancov")
    search_query = st.text_input(
        "Zadajte meno alebo časť mena", 
        placeholder="napr. Novák",
        key="employee_search"
    )
    
    # Zobrazenie zamestnancov s filtrovaním
    show_employees_grid(filtered_analyzer, search_query)

# ---------------------------------------------------------------------------
# FILTER DÁTUMU
# ---------------------------------------------------------------------------
def apply_date_filter(analyzer, start_date, end_date):
    """Aplikuje filter dátumu na analyzer a vráti nový filtrovaný analyzer"""
    
    # Konverzia dátumov na pandas datetime
    start_datetime = pd.to_datetime(start_date)
    end_datetime = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)  # Koniec dňa
    
    # Filtrovanie dátového rámca
    df_filtered = analyzer.df_active[
        (pd.to_datetime(analyzer.df_active['Datum real.']) >= start_datetime) &
        (pd.to_datetime(analyzer.df_active['Datum real.']) <= end_datetime)
    ].copy()
    
    # Vytvorenie nového analyzéra s filtrovanými dátami
    filtered_analyzer = StudioAnalyzer.__new__(StudioAnalyzer)
    filtered_analyzer.df_active = df_filtered
    filtered_analyzer.APPLIANCES = analyzer.APPLIANCES
    
    # Normalizácia názvov v filtrovanom analyzéri (ak existuje metóda)
    if not df_filtered.empty and hasattr(analyzer, 'realistic_normalize_appliance'):
        filtered_analyzer.realistic_normalize_appliance = analyzer.realistic_normalize_appliance
        filtered_analyzer.df_active.loc[:, 'Název_norm'] = filtered_analyzer.df_active['Název'].apply(filtered_analyzer.realistic_normalize_appliance)
    
    return filtered_analyzer

# ---------------------------------------------------------------------------
# AUTOMATICKÉ NAČÍTANIE DÁT Z /data/studio/
# ---------------------------------------------------------------------------
@st.cache_data
def load_studio_data(folder_hash):
    """Automaticky načíta prvý Excel súbor z /data/studio/ priečinka"""
    
    studio_path = Path("data/studio")
    
    if not studio_path.exists():
        return None
    
    # Nájdi Excel súbory
    excel_files = list(studio_path.glob("*.xlsx")) + list(studio_path.glob("*.xls"))
    
    if not excel_files:
        return None
    
    # Použij prvý nájdený súbor (najnovší)
    excel_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)  # Najnovší súbor prvý
    selected_file = excel_files[0]
    
    # Vráti cestu k súboru
    return str(selected_file)

# ---------------------------------------------------------------------------
# ZÁKLADNÉ ŠTATISTIKY
# ---------------------------------------------------------------------------
def show_basic_stats(analyzer):
    """Zobrazí základné štatistiky"""
    
    st.subheader("📊 Základné štatistiky")
    
    # Výpočet základných metrík
    total_sales = analyzer.df_active['Cena/jedn.'].sum()
    unique_employees = analyzer.df_active['Kontaktní osoba-Jméno a příjmení'].nunique()
    total_orders = len(analyzer.df_active)
    avg_order_value = analyzer.df_active['Cena/jedn.'].mean()
    
    # Zobrazenie v 4 stĺpcoch
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Celkový predaj", f"{total_sales:,.0f} Kč")
    
    with col2:
        st.metric("👥 Zamestnanci", unique_employees)
    
    with col3:
        st.metric("📦 Objednávky", total_orders)
    
    with col4:
        st.metric("📈 Priemerná hodnota", f"{avg_order_value:,.0f} Kč")

# ---------------------------------------------------------------------------
# ŠTATISTICKÉ KARTY PRE KATEGÓRIE SPOTREBIČOV
# ---------------------------------------------------------------------------
def show_appliance_stats_cards(analyzer):
    """Zobrazí štatistické karty pre každú kategóriu spotrebičov"""
    
    st.subheader("📈 Prehľad predaja podľa kategórií")
    
    # Výpočet štatistík pre každú kategóriu
    appliance_stats = []
    
    for appliance in analyzer.APPLIANCES:
        appliance_data = analyzer.df_active[
            analyzer.df_active['Název_norm'] == appliance
        ]
        
        if not appliance_data.empty:
            stats = {
                'name': appliance.replace('_', ' ').capitalize(),
                'key': appliance,
                'total_sales': appliance_data['Cena/jedn.'].sum(),
                'total_count': len(appliance_data),
                'employees': appliance_data['Kontaktní osoba-Jméno a příjmení'].nunique(),
                'avg_price': appliance_data['Cena/jedn.'].mean()
            }
        else:
            stats = {
                'name': appliance.replace('_', ' ').capitalize(),
                'key': appliance,
                'total_sales': 0,
                'total_count': 0,
                'employees': 0,
                'avg_price': 0
            }
        
        appliance_stats.append(stats)
    
    # Zobrazenie kariet v riadkoch po 3
    for i in range(0, len(appliance_stats), 3):
        cols = st.columns(3)
        
        for j in range(3):
            if i + j < len(appliance_stats):
                stats = appliance_stats[i + j]
                
                with cols[j]:
                    # Určenie ikony pre kategóriu
                    icons = {
                        'mikrovlnka': '🔥',
                        'trouba': '🏠',
                        'chladnicka': '❄️',
                        'varna_deska': '🍳',
                        'mycka': '🧽',
                        'digestor': '💨'
                    }
                    icon = icons.get(stats['key'], '📦')
                    
                    st.metric(
                        f"{icon} {stats['name']}",
                        f"{stats['total_sales']:,.0f} Kč",
                        delta=f"{stats['total_count']} kusov • {stats['employees']} zam."
                    )

# ---------------------------------------------------------------------------
# MESAČNÉ ŠTATISTIKY PREDAJA
# ---------------------------------------------------------------------------
def show_monthly_sales_stats(analyzer):
    """Zobrazí mesačné štatistiky predaja spotrebičov - STĹPCOVÉ GRAFY S FARBAMI"""
    
    st.subheader("📅 Mesačný predaj spotrebičov")
    
    # Vytvorenie mesačného súhrnu s kategóriami spotrebičov
    df_monthly = analyzer.df_active.copy()
    df_monthly['Mesiac'] = pd.to_datetime(df_monthly['Datum real.']).dt.to_period('M')
    
    # Používame už normalizované kategórie z analyzéra
    monthly_by_category = df_monthly.groupby(['Mesiac', 'Název_norm'])['Cena/jedn.'].sum().reset_index()
    monthly_by_category['Mesiac'] = monthly_by_category['Mesiac'].astype(str)
    
    # Stĺpcový graf s farbami pre rôzne kategórie
    fig = px.bar(
        monthly_by_category,
        x='Mesiac',
        y='Cena/jedn.',
        color='Název_norm',
        title='Mesačný predaj spotrebičov podľa kategórií',
        labels={'Cena/jedn.': 'Predaj (Kč)', 'Mesiac': 'Mesiac', 'Název_norm': 'Typ spotrebiča'},
        color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#A259F7']
    )
    
    fig.update_layout(
        height=500,
        xaxis_tickangle=-45,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Celkové mesačné štatistiky (tabuľka)
    monthly_totals = df_monthly.groupby('Mesiac').agg({
        'Cena/jedn.': ['sum', 'count', 'mean']
    }).round(0)
    
    monthly_totals.columns = ['Celkový predaj', 'Počet objednávok', 'Priemerná hodnota']
    monthly_totals = monthly_totals.reset_index()
    monthly_totals['Mesiac'] = monthly_totals['Mesiac'].astype(str)
    
    # Tabuľka s detailmi
    st.subheader("📋 Detailné mesačné údaje")
    
    # Formátovanie čísel
    monthly_stats_display = monthly_totals.copy()
    monthly_stats_display['Celkový predaj'] = monthly_stats_display['Celkový predaj'].apply(lambda x: f"{x:,.0f} Kč")
    monthly_stats_display['Priemerná hodnota'] = monthly_stats_display['Priemerná hodnota'].apply(lambda x: f"{x:,.0f} Kč")
    
    st.dataframe(monthly_stats_display, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# FILTROVANIE ZAMESTNANCOV PODĽA KATEGÓRIÍ SPOTREBIČOV
# ---------------------------------------------------------------------------
def show_employees_filter_section(analyzer):
    """Zobrazí filtrovacie možnosti pre zamestnancov"""
    
    st.subheader("🔍 Filtrovanie zamestnancov podľa spotrebičov")
    
    # Kontrolné panely pre filtrovanie
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_type = st.selectbox(
            "Typ filtru",
            ["Všetci zamestnanci", "Najmenej predali", "Najviac predali", "Nepredali vôbec"],
            key="filter_type"
        )
    
    with col2:
        appliance_filter = st.selectbox(
            "Kategória spotrebiča", 
            ["Všetky kategórie"] + list(analyzer.APPLIANCES),
            key="appliance_filter"
        )
    
    with col3:
        if filter_type in ["Najmenej predali", "Najviac predali"]:
            min_count = st.number_input(
                "Počet kusov", 
                min_value=1, 
                value=5,
                key="min_count"
            )
        else:
            min_count = 0
    
    return filter_type, appliance_filter, min_count

@st.cache_data(ttl=300)  # 5 minút cache
def get_filtered_employees(_analyzer, filter_type, appliance_filter, min_count=0):
    """Vráti filtrovaných zamestnancov podľa kritérií + autentifikácie"""
    
    # ✅ NOVÉ - Autentifikačné filtrovanie na začiatku
    user_cities = get_user_cities()
    current_user = get_current_user()
    
    # Pre administrátora alebo používateľov s "studio_see_all_employees" bez filtrovania
    if (current_user and current_user.get('role') == 'admin') or has_feature_access("studio_see_all_employees"):
        df_to_use = _analyzer.df_active
    else:
        # Filtrovanie podľa miest používateľa
        if not user_cities:
            # Ak používateľ nemá žiadne mestá, vráti prázdny DataFrame
            return pd.DataFrame()
        
        # Predpokladám že v dátach je stĺpec 'workplace' alebo podobný
        # Tu je potrebné prispôsobiť podľa štruktúry dát
        if 'workplace' in _analyzer.df_active.columns:
            city_filter = _analyzer.df_active['workplace'].str.lower().isin([c.lower() for c in user_cities])
            df_to_use = _analyzer.df_active[city_filter]
        else:
            # Ak nie je stĺpec workplace, použije všetky dáta
            # (môže byť potrebné upraviť podľa skutočnej štruktúry)
            df_to_use = _analyzer.df_active
    
    # Základné štatistiky zamestnancov podľa kategorií spotrebičov
    if appliance_filter == "Všetky kategórie":
        # Celkové štatistiky
        employee_stats = df_to_use.groupby('Kontaktní osoba-Jméno a příjmení').agg({
            'Cena/jedn.': ['sum', 'count', 'mean'],
            'Datum real.': ['min', 'max']
        }).round(0)
        
        employee_stats.columns = ['Celkový predaj', 'Počet objednávok', 'Priemerná hodnota', 'Prvá objednávka', 'Posledná objednávka']
        employee_stats = employee_stats.reset_index()
        
        # Pridanie info o kategórii
        employee_stats['Kategória filter'] = "Všetky"
        employee_stats['Počet v kategórii'] = employee_stats['Počet objednávok']
        
    else:
        # Filtrovanie podľa konkrétnej kategórie
        category_data = df_to_use[
            df_to_use['Název_norm'] == appliance_filter
        ]
        
        if category_data.empty:
            return pd.DataFrame()
        
        employee_stats = category_data.groupby('Kontaktní osoba-Jméno a příjmení').agg({
            'Cena/jedn.': ['sum', 'count', 'mean'],
            'Datum real.': ['min', 'max']
        }).round(0)
        
        employee_stats.columns = ['Celkový predaj', 'Počet objednávok', 'Priemerná hodnota', 'Prvá objednávka', 'Posledná objednávka']
        employee_stats = employee_stats.reset_index()
        
        # Pridanie info o kategórii
        employee_stats['Kategória filter'] = appliance_filter.replace('_', ' ').capitalize()
        employee_stats['Počet v kategórii'] = employee_stats['Počet objednávok']
        
        # Pridanie celkových štatistík zamestnanca
        total_stats = df_to_use.groupby('Kontaktní osoba-Jméno a příjmení').agg({
            'Cena/jedn.': 'sum',
            'Název': 'count'
        })
        total_stats.columns = ['Celkový predaj všetko', 'Celkom objednávok všetko']
        
        employee_stats = employee_stats.merge(
            total_stats, 
            left_on='Kontaktní osoba-Jméno a příjmení',
            right_index=True,
            how='left'
        )
    
    # Aplikovanie filtrov
    if filter_type == "Najmenej predali" and appliance_filter != "Všetky kategórie":
        # Zamestnanci s najmenším počtom v danej kategórii
        employee_stats = employee_stats[
            employee_stats['Počet v kategórii'] <= min_count
        ].sort_values('Počet v kategórii', ascending=True)
        
    elif filter_type == "Najviac predali" and appliance_filter != "Všetky kategórie":
        # Zamestnanci s najvyšším počtom v danej kategórii  
        employee_stats = employee_stats[
            employee_stats['Počet v kategórii'] >= min_count
        ].sort_values('Počet v kategórii', ascending=False)
        
    elif filter_type == "Nepredali vôbec":
        # Všetci zamestnanci, ktorí nepredali nič z danej kategórie
        if appliance_filter != "Všetky kategórie":
            all_employees = _analyzer.df_active['Kontaktní osoba-Jméno a příjmení'].unique()
            employees_with_sales = employee_stats['Kontaktní osoba-Jméno a příjmení'].unique()
            employees_without = [emp for emp in all_employees if emp not in employees_with_sales]
            
            # Vytvorenie prázdneho DataFrame pre zamestnancov bez predaja
            if employees_without:
                zero_sales_df = pd.DataFrame({
                    'Kontaktní osoba-Jméno a příjmení': employees_without,
                    'Celkový predaj': [0] * len(employees_without),
                    'Počet objednávok':[0]  * len(employees_without),        # ✅ Pridané 
                    'Priemerná hodnota':[0]  * len(employees_without),       # ✅ Pridané 
                    'Kategória filter': [appliance_filter.replace('_', ' ').capitalize()] * len(employees_without),
                    'Počet v kategórii': [0] * len(employees_without)
                })
                # Pridanie celkových štatistík
                total_stats = _analyzer.df_active.groupby('Kontaktní osoba-Jméno a příjmení').agg({
                    'Cena/jedn.': 'sum',
                    'Název': 'count'
                }).reindex(employees_without, fill_value=0)
                
                total_stats.columns = ['Celkový predaj všetko', 'Celkom objednávok všetko']
                total_stats = total_stats.reset_index()
                
                employee_stats = zero_sales_df.merge(
                    total_stats,
                    on='Kontaktní osoba-Jméno a příjmení',
                    how='left'
                ).fillna(0)
            else:
                employee_stats = pd.DataFrame()
    else:
        # Všetci zamestnanci - zoradení podľa celkového predaja
        employee_stats = employee_stats.sort_values('Celkový predaj', ascending=False)
    
    return employee_stats

# ---------------------------------------------------------------------------
# ZOBRAZENIE ZAMESTNANCOV - S FILTROVANÍM
# ---------------------------------------------------------------------------
def show_employees_grid(analyzer, name_filter=""):
    """Zobrazí zamestnancov ako veľké klikateľné karty"""
    
    # ✅ PÔVODNÉ FILTROVACIE MOŽNOSTI
    filter_type, appliance_filter, min_count = show_employees_filter_section(analyzer)
    
    st.divider()
    
    # Získanie filtrovaných zamestnancov
    employee_stats = get_filtered_employees(analyzer, filter_type, appliance_filter, min_count)
    
    # Filtrovanie podľa mena
    if name_filter and not employee_stats.empty:
        mask = employee_stats['Kontaktní osoba-Jméno a příjmení'].str.contains(name_filter, case=False, na=False)
        employee_stats = employee_stats[mask]
    
    if employee_stats.empty:
        st.info("🔍 Žiadni zamestnanci nenájdení pre zadané kritériá")
        return
    
    # Zobrazenie počtu výsledkov
    st.subheader(f"👥 Výsledky ({len(employee_stats)} zamestnancov)")
    
    if appliance_filter != "Všetky kategórie":
        st.info(f"📊 Filter: **{filter_type}** pre kategóriu **{appliance_filter.replace('_', ' ').capitalize()}**")
    
    employees = employee_stats.to_dict('records')
    
    # Prečistenie typov dát
    for emp in employees:
        for key in ['Celkový predaj', 'Počet objednávok', 'Počet v kategórii', 'Celkový predaj všetko']:
            if key in emp:
                try:
                    emp[key] = int(float(emp[key])) if pd.notna(emp[key]) else 0
                except (ValueError, TypeError):
                    emp[key] = 0
    
    # ==================== ✅ CELÉ KARTY AKO TLAČIDLÁ ====================
    for i in range(0, len(employees), 3):
        cols = st.columns(3)
        
        for j in range(3):
            if i + j < len(employees):
                emp = employees[i + j]
                
                with cols[j]:
                    employee_name = emp.get('Kontaktní osoba-Jméno a příjmení', 'Neznámy')
                    predaj = emp.get('Celkový predaj', 0)
                    objednavky = emp.get('Počet objednávok', 0)
                    
                    # Výkonnostná ikona a špecializácia
                    icon = "👤"
                    spec_text = ""
                    
                    if 'Počet v kategórii' in emp and appliance_filter != "Všetky kategórie":
                        category_count = emp['Počet v kategórii']
                        category_name = emp.get('Kategória filter', '')
                        
                        if category_count == 0:
                            icon = "❌"
                            spec_text = f"{category_name}: Žiadny predaj"
                        elif category_count <= 2:
                            icon = "⚠️"
                            spec_text = f"{category_name}: {category_count} kusov"
                        elif category_count <= 5:
                            icon = "⭐"
                            spec_text = f"{category_name}: {category_count} kusov"
                        else:
                            icon = "🏆"
                            spec_text = f"{category_name}: {category_count} kusov"
                    
                    # Celkové štatistiky
                    total_text = ""
                    if 'Celkový predaj všetko' in emp:
                        total_sales = emp['Celkový predaj všetko']
                        total_text = f"\n💼 Celkom: {total_sales:,} Kč"
                    
                    # ✅ CELÁ KARTA AKO JEDNO VEĽKÉ TLAČIDLO
                    button_content = f"""{icon} **{employee_name}**

💰 **{predaj:,} Kč** • 📦 **{objednavky:,} kusov**
{spec_text}{total_text}"""
                    
                    # Veľké tlačidlo s celým obsahom
                    if st.button(
                        button_content, 
                        key=f"employee_card_{i+j}", 
                        use_container_width=True,
                        help=f"Kliknite pre detail zamestnanca {employee_name}"
                    ):
                        # ✅ KONTROLA OPRÁVNENÍ pre employee_detail
                        from auth.auth import can_access_detail_page
                        
                        if can_access_detail_page('employee_detail'):
                            st.session_state['selected_employee_name'] = emp['Kontaktní osoba-Jméno a příjmení']
                            # Použijem filtrovaný analyzer namiesto pôvodného
                            st.session_state['studio_analyzer'] = st.session_state.get('filtered_studio_analyzer', analyzer)
                            st.session_state['current_page'] = 'employee_detail'
                            st.rerun()
                        else:
                            st.error("❌ Nemáte oprávnenie pre detail zamestnanca")
                            st.info("🔒 Kontaktujte administrátora pre rozšírenie oprávnení")


# ---------------------------------------------------------------------------
# SPUSTENIE - PRE TESTOVANIE
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    show_studio_page()
