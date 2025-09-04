import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
from core.studio_analyzer import StudioAnalyzer
from auth.auth import has_feature_access, init_auth

# 🚀 AUTO-DETECT CPU CORES pre maximálny výkon
MAX_WORKERS = max(2, cpu_count())  # Minimálne 2, ale použije všetky dostupné cores

def get_optimal_workers_count(data_size):
    """Dynamické určenie optimálneho počtu workerov na základe veľkosti dát"""
    if data_size < 1000:
        return min(2, MAX_WORKERS)
    elif data_size < 10000:
        return min(4, MAX_WORKERS)
    else:
        return MAX_WORKERS  # Pre veľké datasety využij všetky cores

@st.cache_data(ttl=300)  # 5 minút cache
def get_employee_detailed_data_cached(employee_name, file_hash=None, filter_info=None):
    """Cached verzia získania detailných dát pre zamestnanca"""
    studio_analyzer = st.session_state.get('studio_analyzer')
    if not studio_analyzer:
        return pd.DataFrame()
    
    return studio_analyzer.get_employee_detailed_data(employee_name)

@st.cache_data(ttl=300)
def calculate_employee_metrics_cached(emp_data_hash, emp_data_dict):
    """Cached výpočet základných metrík"""
    emp_data = pd.DataFrame(emp_data_dict)
    
    if emp_data.empty:
        return None
    
    total_sales = emp_data['Cena/jedn.'].sum()
    total_orders = len(emp_data)
    avg_order = emp_data['Cena/jedn.'].mean()
    unique_orders = emp_data['Doklad'].nunique()
    
    # Pre výpočet rozsahu dátumov
    if 'Datum real.' in emp_data.columns:
        date_range = (emp_data['Datum real.'].max() - emp_data['Datum real.'].min()).days
    else:
        date_range = 0
    
    return {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'avg_order': avg_order,
        'unique_orders': unique_orders,
        'date_range': date_range
    }

@st.cache_data(ttl=300)
def calculate_category_analysis_cached(emp_data_hash, emp_data_dict):
    """Cached analýza podľa kategórií"""
    emp_data = pd.DataFrame(emp_data_dict)
    
    if emp_data.empty or 'Název_norm' not in emp_data.columns:
        return pd.DataFrame()
    
    category_sales = emp_data.groupby('Název_norm').agg({
        'Cena/jedn.': ['sum', 'count', 'mean']
    }).round(0)
    
    category_sales.columns = ['Celkový predaj', 'Počet kusov', 'Priemerná cena']
    return category_sales.reset_index()

@st.cache_data(ttl=300)
def calculate_time_analysis_parallel(emp_data_hash, emp_data_dict):
    """Paralelný výpočet časovej analýzy"""
    emp_data = pd.DataFrame(emp_data_dict)
    
    if emp_data.empty or 'Datum real.' not in emp_data.columns:
        return None
    
    try:
        # Analýza podľa mesiacov
        monthly_breakdown = emp_data.groupby(emp_data['Datum real.'].dt.month)['Cena/jedn.'].sum()
        
        # Analýza podľa dní v týždni
        weekly_breakdown = emp_data.groupby(emp_data['Datum real.'].dt.dayofweek)['Cena/jedn.'].sum()
        
        # Trend analýza
        daily_sales = emp_data.groupby(emp_data['Datum real.'].dt.date)['Cena/jedn.'].sum()
        
        return {
            'monthly': monthly_breakdown,
            'weekly': weekly_breakdown,
            'daily_trend': daily_sales
        }
    except:
        return None

@st.cache_data(ttl=300)
def calculate_product_analysis_parallel(emp_data_hash, emp_data_dict):
    """Paralelný výpočet produktovej analýzy"""
    emp_data = pd.DataFrame(emp_data_dict)
    
    if emp_data.empty:
        return None
    
    try:
        # Top produkty podľa predaja
        if 'Název' in emp_data.columns:
            top_products = emp_data.groupby('Název')['Cena/jedn.'].sum().sort_values(ascending=False).head(10)
        else:
            top_products = pd.Series()
        
        # Analýza podľa množstva
        if 'Množství' in emp_data.columns:
            quantity_analysis = emp_data.groupby('Název')['Množství'].sum().sort_values(ascending=False).head(10)
        else:
            quantity_analysis = pd.Series()
        
        # Priemerné ceny produktov
        if 'Název' in emp_data.columns:
            avg_prices = emp_data.groupby('Název')['Cena/jedn.'].mean().sort_values(ascending=False).head(10)
        else:
            avg_prices = pd.Series()
        
        return {
            'top_products': top_products,
            'quantity_analysis': quantity_analysis,
            'avg_prices': avg_prices
        }
    except:
        return None

def get_data_hash(data):
    """Vytvorí hash pre pandas DataFrame alebo iné dáta"""
    if isinstance(data, pd.DataFrame):
        return hashlib.md5(str(data.values.tobytes()).encode()).hexdigest()
    return hashlib.md5(str(data).encode()).hexdigest()

def render_employee_metrics_optimized(metrics):
    """Optimalizované renderovanie metrík"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("💰 Celkový predaj", f"{metrics['total_sales']:,.0f} Kč")
    with col2:
        st.metric("📦 Celkom položiek", metrics['total_orders'])
    with col3:
        st.metric("🧾 Unikátne objednávky", metrics['unique_orders'])
    with col4:
        st.metric("📈 Priemerná hodnota", f"{metrics['avg_order']:,.0f} Kč")
    with col5:
        st.metric("📅 Aktívnych dní", metrics['date_range'])

def render_category_charts_optimized(category_sales):
    """Optimalizované renderovanie grafov kategórií"""
    col_chart, col_table = st.columns(2)
    
    with col_chart:
        fig_pie = px.pie(
            category_sales, 
            values='Celkový predaj', 
            names='Název_norm',
            title="Podiel predaja podľa kategórií",
            color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#A259F7']
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_table:
        st.subheader("📋 Tabuľka kategórií")
        category_display = category_sales.copy()
        category_display['Název_norm'] = category_display['Název_norm'].apply(lambda x: x.replace('_', ' ').capitalize())
        category_display['Celkový predaj'] = category_display['Celkový predaj'].apply(lambda x: f"{x:,.0f} Kč")
        category_display['Priemerná cena'] = category_display['Priemerná cena'].apply(lambda x: f"{x:,.0f} Kč")
        st.dataframe(category_display, use_container_width=True, hide_index=True)

def render(selected_employee_name, analyzer_or_data):
    """Detailná stránka pre konkrétneho zamestnanca - optimalizovaná verzia"""
    
    # Meranie výkonu
    start_time = time.time()
    
    # Zabezpečenie, že autentifikácia je inicializovaná
    if 'user_db' not in st.session_state:
        init_auth()
    
    st.title(f"👤 Detail zamestnanca: {selected_employee_name}")
    
    # Info o filtri dátumu ak existuje
    if 'date_filter_info' in st.session_state:
        filter_info = st.session_state['date_filter_info']
        start_date = filter_info['start_date']
        end_date = filter_info['end_date']
        filtered_records = filter_info['filtered_records']
        
        st.info(f"📅 **Filtrované obdobie**: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')} ({filtered_records:,} záznamov)")
        
        if st.button("🔄 Späť na Studio (zmeniť filter)", type="secondary"):
            st.session_state['current_page'] = 'studio'
            st.rerun()
    
    # Kontrola analyzéra
    if not isinstance(analyzer_or_data, StudioAnalyzer):
        st.error("❌ Pre detail zamestnanca potrebuješ StudioAnalyzer, nie DataAnalyzer")
        st.info("💡 Detail zamestnanca funguje len v Studio module s nahratým Excel súborom")
        if st.button("← Späť na Studio"):
            st.session_state['current_page'] = 'studio'
            if 'selected_employee_name' in st.session_state:
                del st.session_state['selected_employee_name']
            st.rerun()
        return
    
    # Cached získanie dát pre zamestnanca
    file_hash = None
    filter_info = st.session_state.get('date_filter_info')
    
    try:
        emp_data = get_employee_detailed_data_cached(
            selected_employee_name, 
            file_hash=file_hash,
            filter_info=filter_info
        )
    except Exception as e:
        st.error(f"❌ Chyba pri načítavaní dát: {e}")
        if st.button("← Späť na Studio"):
            st.session_state['current_page'] = 'studio'
            if 'selected_employee_name' in st.session_state:
                del st.session_state['selected_employee_name']  
            st.rerun()
        return
    
    if emp_data.empty:
        st.warning("Žiadne dáta pre tohto zamestnanca")
        if st.button("← Späť na Studio"):
            st.session_state['current_page'] = 'studio'
            if 'selected_employee_name' in st.session_state:
                del st.session_state['selected_employee_name']  
            st.rerun()
        return
    
    # Hash pre cache invalidation
    emp_data_hash = get_data_hash(emp_data)
    emp_data_dict = emp_data.to_dict('records')
    data_size = len(emp_data)
    optimal_workers = get_optimal_workers_count(data_size)
    
    # Zobrazenie performance info
    st.caption(f"🔥 Employee Detail Performance: {optimal_workers}/{MAX_WORKERS} cores aktívnych")
    
    # Paralelné vykonávanie výpočtov - využívame všetky cores
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Spustenie cached výpočtov paralelne
        future_metrics = executor.submit(
            calculate_employee_metrics_cached, 
            emp_data_hash, 
            emp_data_dict
        )
        future_categories = executor.submit(
            calculate_category_analysis_cached,
            emp_data_hash,
            emp_data_dict
        )
        # Pridáme ďalšie paralelné úlohy pre komplexnejšie spracovanie
        future_time_analysis = executor.submit(
            calculate_time_analysis_parallel,
            emp_data_hash,
            emp_data_dict
        )
        future_product_analysis = executor.submit(
            calculate_product_analysis_parallel,
            emp_data_hash,
            emp_data_dict
        )
        
        # Čakanie na výsledky s timeoutom
        try:
            metrics = future_metrics.result(timeout=10)
            category_sales = future_categories.result(timeout=10)
            time_analysis = future_time_analysis.result(timeout=10)
            product_analysis = future_product_analysis.result(timeout=10)
        except Exception as e:
            st.warning(f"⚠️ Timeout pri paralelnom spracovaní: {e}")
            # Fallback na základné výpočty
            metrics = calculate_employee_metrics_cached(emp_data_hash, emp_data_dict)
            category_sales = calculate_category_analysis_cached(emp_data_hash, emp_data_dict)
            time_analysis = None
            product_analysis = None
    
    # ==================== ZÁKLADNÉ METRIKY ====================
    st.header("📊 Základné metriky")
    
    if metrics:
        render_employee_metrics_optimized(metrics)
    else:
        st.error("❌ Chyba pri výpočte metrík")
        return
    
    st.divider()
    
    # ==================== PREDAJ PODĽA KATEGÓRIÍ ====================
    st.header("🏷️ Predaj podľa kategórií spotrebičov")
    
    if not category_sales.empty:
        render_category_charts_optimized(category_sales)
    else:
        st.warning("⚠️ Žiadne dáta o kategóriách")
    
    st.divider()
    
    # Meranie výkonu - zobrazenie času načítania
    load_time = time.time() - start_time
    if load_time > 1.0:  # Zobraz len ak trvá viac ako 1 sekundu
        st.caption(f"⏱️ Stránka načítaná za {load_time:.2f}s")
    
    # ==================== ✅ NOVÁ SEKCIA: TOP PRODUKTY PODĽA KATEGÓRIÍ ====================
    if has_feature_access("employee_detail_top_products"):
        st.header("🏆 Najpredávanejšie produkty z každej kategórie")
        
        # Používame pôvodné emp_data namiesto cache pre túto sekciu
        top_products_per_category = get_top_products_per_category(emp_data)
        
        if top_products_per_category:
            # Zobrazenie v krásnych kartách
            num_categories = len(top_products_per_category)
            cols = st.columns(min(3, num_categories))  # Max 3 stĺpce
            
            for idx, item in enumerate(top_products_per_category):
                with cols[idx % 3]:
                    # Ikony pre kategórie
                    icons = {
                        'Mikrovlnka': '🔥',
                        'Trouba': '🏠',
                        'Chladnicka': '❄️',
                        'Varna deska': '🍳',
                        'Mycka': '🧽',
                        'Digestor': '💨'
                    }
                    icon = icons.get(item['category'], '📦')
                    
                    # Karta s top produktom
                    st.markdown(f"""
                    <div style="
                        border: 1px solid #444;
                        border-radius: 10px;
                        padding: 15px;
                        margin: 10px 0;
                        background-color: #2d3748;
                        color: white;
                    ">
                        <h4 style="color: #63b3ed; margin-top: 0;">{icon} {item['category']}</h4>
                        <p><strong>Top produkt:</strong><br>{item['product']}</p>
                        <p><strong>Celkový predaj:</strong><br><span style="color: #68d391; font-size: 18px;">{item['value']:,.0f} Kč</span></p>
                        <p><strong>Počet kusov:</strong><br>{item['count']} kusov</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Detailná tabuľka - iba ak má povolenie
            if has_feature_access("employee_detail_product_table"):
                st.subheader("📊 Detailná tabuľka top produktov")
                
                top_df = pd.DataFrame(top_products_per_category)
                top_df['Celkový predaj'] = top_df['value'].apply(lambda x: f"{x:,.0f} Kč")
                top_df_display = top_df[['category', 'product', 'Celkový predaj', 'count']].copy()
                top_df_display.columns = ['Kategória', 'Produkt', 'Celkový predaj', 'Počet kusov']
                
                st.dataframe(top_df_display, use_container_width=True, hide_index=True)
            
        else:
            st.info("Žiadne dáta o predaji produktov podľa kategórií")
    else:
        # Ak nemá prístup, zobraz info správu
        st.info("🔒 **Najpredávanejšie produkty z každej kategórie** - Funkcia nie je dostupná pre váš účet")
    
    st.divider()
    
    # ==================== MESAČNÝ VÝVOJ ====================
    st.header("📅 Mesačný vývoj predaja")
    
    emp_data['Mesiac'] = pd.to_datetime(emp_data['Datum real.']).dt.to_period('M')
    monthly_emp_cat = emp_data.groupby(['Mesiac', 'Název_norm'])['Cena/jedn.'].sum().reset_index()
    monthly_emp_cat['Mesiac'] = monthly_emp_cat['Mesiac'].astype(str)
    
    if not monthly_emp_cat.empty:
        fig_monthly = px.bar(
            monthly_emp_cat,
            x='Mesiac',
            y='Cena/jedn.',
            color='Název_norm',
            title=f'Mesačný vývoj predaja - {selected_employee_name}',
            labels={'Cena/jedn.': 'Predaj (Kč)', 'Název_norm': 'Typ spotrebiča'},
            color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#A259F7']
        )
        fig_monthly.update_layout(height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig_monthly, use_container_width=True)
    
    st.divider()
    
    # ==================== KOMPLETNÁ TABUĽKA ZÁZNAMOV ====================
    st.header("📄 Všetky záznamy")
    
    # Filtrovanie a hľadanie
    search_product = st.text_input("🔍 Hľadať v produktoch", placeholder="Zadajte názov produktu...")
    
    display_data = emp_data.copy()
    if search_product:
        display_data = display_data[display_data['Název'].str.contains(search_product, case=False, na=False)]
    
    # Zoradenie podľa dátumu (najnovšie prvé)
    display_data = display_data.sort_values('Datum real.', ascending=False)
    
    # Zobrazenie tabuľky
    columns_to_show = ['Datum real.', 'Doklad', 'Název', 'Název_norm', 'Cena/jedn.', 'Odběratel']
    st.dataframe(
        display_data[columns_to_show].head(100),  # Zobraz len prvých 100 pre výkon
        use_container_width=True,
        hide_index=True
    )
    
    if len(display_data) > 100:
        st.info(f"Zobrazených prvých 100 z {len(display_data)} záznamov")
    
    # ==================== NÁVRAT SPÄŤ ====================
    if st.button("← Späť na Studio", use_container_width=True):
        st.session_state['current_page'] = 'studio'
        if 'selected_employee_name' in st.session_state:
            del st.session_state['selected_employee_name']
        st.rerun()

# ==================== POMOCNÉ FUNKCIE ====================
def get_top_products_per_category(emp_data):
    """Získa najpredávanejší produkt z každej kategórie pre zamestnanca"""
    
    top_products = []
    
    for category in emp_data['Název_norm'].unique():
        category_data = emp_data[emp_data['Název_norm'] == category]
        
        # Grupovanie podľa produktu a súčet predaja
        grouped_products = category_data.groupby('Název').agg({
            'Cena/jedn.': 'sum',
            'Název': 'count'  # Počet kusov
        }).rename(columns={'Název': 'count'})
        
        if not grouped_products.empty:
            # Najdi produkt s najvyšším predajom
            top_product_name = grouped_products['Cena/jedn.'].idxmax()
            top_value = grouped_products.loc[top_product_name, 'Cena/jedn.']
            top_count = grouped_products.loc[top_product_name, 'count']
            
            top_products.append({
                'category': category.replace('_', ' ').capitalize(),
                'product': top_product_name,
                'value': top_value,
                'count': top_count
            })
    
    # Zoraď podľa hodnoty predaja (zostupne)
    top_products.sort(key=lambda x: x['value'], reverse=True)
    
    return top_products
