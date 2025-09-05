# ui/pages/settings.py
import streamlit as st
import pandas as pd
from pathlib import Path
from auth.auth import get_current_user, has_feature_access, is_admin

def show_settings():
    """Zobrazí stránku nastavení"""
    
    st.title("⚙️ Nastavenia")
    
    current_user = get_current_user()
    if not current_user:
        st.error("❌ Nie ste prihlásený")
        return
    
    # Kontrola oprávnení - admin má automaticky prístup
    if not is_admin():
        if not has_feature_access("settings_access"):
            st.error("❌ Nemáte oprávnenie pre prístup k nastaveniam")
            st.info("💡 Kontaktujte administrátora pre povolenie prístupu k nastaveniam")
            return
    
    # Header s info o používateľovi
    st.info(f"👤 **Používateľ:** {current_user.get('name', 'N/A')} ({current_user.get('email', 'N/A')})")
    
    # Sekcie nastavení
    tab1, tab2, tab3 = st.tabs(["📊 Dáta", "🎨 Zobrazenie", "⚙️ Systém"])
    
    with tab1:
        show_data_settings()
    
    with tab2:
        show_display_settings()
    
    with tab3:
        show_system_settings()

def show_data_settings():
    """Nastavenia dát"""
    
    st.subheader("📊 Nastavenia dát")
    
    # Nastavenie pre ukončených zamestnancov
    st.markdown("### 👥 Zamestnanci")
    
    current_setting = st.session_state.get('include_terminated_employees', False)
    
    include_terminated = st.checkbox(
        "🔄 Zahrnúť ukončených zamestnancov", 
        value=current_setting,
        help="Zahrnúť aj zamestnancov s 'X' v poslednom mesiaci do analýz"
    )
    
    # Okamžitá zmena nastavenia
    if include_terminated != current_setting:
        st.session_state.include_terminated_employees = include_terminated
        
        # Vymaž analyzer pre reload
        if 'analyzer' in st.session_state:
            del st.session_state.analyzer
        
        st.success("✅ Nastavenie uložené! Dáta sa načítajú znovu.")
        st.rerun()
    
    # Info o počte zamestnancov
    if st.session_state.get('analyzer'):
        emp_count = len(st.session_state.analyzer.sales_employees)
        st.info(f"📊 **Aktuálne:** {emp_count} zamestnancov v analýze")
    
    # Dátové súbory info
    st.markdown("### 📁 Dátové súbory")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Sales data info
        sales_path = Path("data/sales")
        if sales_path.exists():
            sales_files = list(sales_path.glob("*.xlsx"))
            st.success(f"📈 **Sales dáta:** {len(sales_files)} súborov")
            if sales_files:
                latest_sales = max(sales_files, key=lambda x: x.stat().st_mtime)
                st.info(f"📅 **Posledný:** {latest_sales.name}")
        else:
            st.warning("⚠️ **Sales dáta:** Priečinok neexistuje")
    
    with col2:
        # Studio data info
        studio_path = Path("data/studio")
        if studio_path.exists():
            studio_files = list(studio_path.glob("*.xlsx"))
            st.success(f"🎭 **Studio dáta:** {len(studio_files)} súborov")
            if studio_files:
                latest_studio = max(studio_files, key=lambda x: x.stat().st_mtime)
                st.info(f"📅 **Posledný:** {latest_studio.name}")
        else:
            st.warning("⚠️ **Studio dáta:** Priečinok neexistuje")

def show_display_settings():
    """Nastavenia zobrazenia"""
    
    st.subheader("🎨 Nastavenia zobrazenia")
    
    # Theme settings
    st.markdown("### 🌓 Téma")
    st.info("💡 Téma sa nastavuje automaticky podľa prehliadača")
    
    # Table settings
    st.markdown("### 📋 Tabuľky")
    
    table_height = st.slider(
        "Výška tabuliek (px)",
        min_value=300,
        max_value=800,
        value=st.session_state.get('table_height', 400),
        step=50,
        help="Výška pre hlavné tabuľky v aplikácii"
    )
    
    if table_height != st.session_state.get('table_height', 400):
        st.session_state.table_height = table_height
        st.success("✅ Nastavenie výšky tabuliek uložené")
    
    # Charts settings
    st.markdown("### 📊 Grafy")
    
    chart_theme = st.selectbox(
        "Farebná schéma grafov",
        ["streamlit", "plotly", "plotly_white", "plotly_dark"],
        index=0,
        help="Téma pre Plotly grafy"
    )
    
    if chart_theme != st.session_state.get('chart_theme', 'streamlit'):
        st.session_state.chart_theme = chart_theme
        st.success("✅ Téma grafov uložená")

def show_system_settings():
    """Systémové nastavenia"""
    
    st.subheader("⚙️ Systémové nastavenia")
    
    # Admin only settings
    if is_admin():
        st.markdown("### 🔧 Administrátor")
        
        # Cache management
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Vymazať cache", help="Vymaže všetky cached dáta"):
                try:
                    # Clear session cache
                    for key in list(st.session_state.keys()):
                        if key.startswith(('analyzer', 'filtered_', 'cache_')):
                            del st.session_state[key]
                    
                    # Clear file cache
                    cache_dir = Path("data/cache")
                    if cache_dir.exists():
                        for cache_file in cache_dir.glob("*"):
                            cache_file.unlink()
                    
                    st.success("✅ Cache vymazaná")
                except Exception as e:
                    st.error(f"❌ Chyba pri mazaní cache: {e}")
        
        with col2:
            if st.button("🔄 Reštart analýzy", help="Znovu načíta všetky dáta"):
                # Clear all analyzer data
                for key in list(st.session_state.keys()):
                    if 'analyzer' in key:
                        del st.session_state[key]
                st.success("✅ Analýza sa reštartuje")
                st.rerun()
    
    # User session info
    st.markdown("### 👤 Session info")
    
    if current_user := get_current_user():
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Email:** {current_user.get('email', 'N/A')}")
            st.info(f"**Rola:** {current_user.get('role', 'N/A')}")
        
        with col2:
            cities = current_user.get('cities', [])
            st.info(f"**Mestá:** {', '.join(cities) if cities else 'Žiadne'}")
            
            features = current_user.get('features', {})
            active_features = [k for k, v in features.items() if v]
            st.info(f"**Funkcie:** {len(active_features)} aktívnych")
    
    # System info
    st.markdown("### 💻 Systém")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Streamlit:** {st.__version__}")
        st.info(f"**Session items:** {len(st.session_state)}")
    
    with col2:
        # Memory usage info (basic)
        analyzer_size = "Načítaný" if 'analyzer' in st.session_state else "Nenačítaný"
        st.info(f"**Analyzer:** {analyzer_size}")
        
        cache_files = list(Path("data/cache").glob("*")) if Path("data/cache").exists() else []
        st.info(f"**Cache súbory:** {len(cache_files)}")
