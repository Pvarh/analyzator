import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.studio_analyzer import StudioAnalyzer
from auth.auth import has_feature_access, init_auth

def render(selected_employee_name, analyzer_or_data):
    """Detailná stránka pre konkrétneho zamestnanca"""
    
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
    if isinstance(analyzer_or_data, StudioAnalyzer):
        studio_analyzer = analyzer_or_data
    else:
        st.error("❌ Pre detail zamestnanca potrebuješ StudioAnalyzer, nie DataAnalyzer")
        st.info("💡 Detail zamestnanca funguje len v Studio module s nahratým Excel súborom")
        if st.button("← Späť na Studio"):
            st.session_state['current_page'] = 'studio'
            if 'selected_employee_name' in st.session_state:
                del st.session_state['selected_employee_name']
            st.rerun()
        return
    
    # Získanie dát pre zamestnanca
    emp_data = studio_analyzer.get_employee_detailed_data(selected_employee_name)
    if emp_data.empty:
        st.warning("Žiadne dáta pre tohto zamestnanca")
        if st.button("← Späť na Studio"):
            st.session_state['current_page'] = 'studio'
            if 'selected_employee_name' in st.session_state:
                del st.session_state['selected_employee_name']  
            st.rerun()
        return
    
    # ==================== ZÁKLADNÉ METRIKY ====================
    st.header("📊 Základné metriky")
    
    total_sales = emp_data['Cena/jedn.'].sum()
    total_orders = len(emp_data)
    avg_order = emp_data['Cena/jedn.'].mean()
    unique_orders = emp_data['Doklad'].nunique()
    date_range = (emp_data['Datum real.'].max() - emp_data['Datum real.'].min()).days
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("💰 Celkový predaj", f"{total_sales:,.0f} Kč")
    with col2:
        st.metric("📦 Celkom položiek", total_orders)
    with col3:
        st.metric("🧾 Unikátne objednávky", unique_orders)
    with col4:
        st.metric("📈 Priemerná hodnota", f"{avg_order:,.0f} Kč")
    with col5:
        st.metric("📅 Aktívnych dní", date_range)
    
    st.divider()
    
    # ==================== PREDAJ PODĽA KATEGÓRIÍ ====================
    st.header("🏷️ Predaj podľa kategórií spotrebičov")
    
    category_sales = emp_data.groupby('Název_norm').agg({
        'Cena/jedn.': ['sum', 'count', 'mean']
    }).round(0)
    
    category_sales.columns = ['Celkový predaj', 'Počet kusov', 'Priemerná cena']
    category_sales = category_sales.reset_index()
    
    # Graf podľa kategórií - pie chart
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
    
    st.divider()
    
    # ==================== ✅ NOVÁ SEKCIA: TOP PRODUKTY PODĽA KATEGÓRIÍ ====================
    if has_feature_access("employee_detail_top_products"):
        st.header("🏆 Najpredávanejšie produkty z každej kategórie")
        
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
