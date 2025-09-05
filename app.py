# app.py
import streamlit as st
import pandas as pd
import os
from pathlib import Path

# Import nového analyzátora
from core.analyzer import DataAnalyzer
from core.utils import format_money, format_profit_value

# Import UI stránok
from ui.pages import overview, employee, heatmap, benchmark, studio, employee_detail, user_management, settings
from ui.styling import apply_dark_theme

# Import autentifikačného systému
from auth.auth import init_auth, is_authenticated, show_login_page, show_user_info, is_admin, log_page_activity, can_show_sidebar_statistics, get_allowed_pages, can_access_page, get_default_page, can_access_detail_page, get_parent_page_for_detail, has_feature_access
from auth.admin import show_admin_page

# Import server monitoring
from core.server_monitor import get_server_monitor

# Import error handling
from core.error_handler import handle_error, log_error

import sys
import inspect
from datetime import datetime


@handle_error
def load_sales_data():
    """Načíta sales dáta s opravenou logikou filtrovania"""
    
    try:
        # ✅ OPRAVENÉ - hľadá v sales priečinku
        data_path = Path("data/sales")
        
        # ✅ Ak sales neexistuje, skús aj raw ako backup
        if not data_path.exists():
            data_path = Path("data/raw")
            
        if not data_path.exists():
            st.error(f"Priečinok {data_path} neexistuje!")
            return pd.DataFrame(), pd.DataFrame()  # ✅ Vráti tuple namiesto listu
        
        # Nájdi sales súbor
        sales_candidates = []
        for file in data_path.glob("*.xlsx"):
            filename_lower = file.name.lower()
            if any(keyword in filename_lower for keyword in ['prodej', 'sales', 'leden', 'unor', 'user']):
                sales_candidates.append(file)
        
        if not sales_candidates:
            st.error("❌ Žiadny sales súbor nenájdený!")
            return pd.DataFrame(), pd.DataFrame()  # ✅ Vráti tuple namiesto listu
        
        sales_file = sales_candidates[0]
        
        # Načítanie súboru
        df = pd.read_excel(sales_file)
        
        # ✅ OPRAVENÉ FILTROVANIE
        include_terminated = st.session_state.get('include_terminated_employees', False)
        df_filtered = filter_sales_data_new_logic(df, include_terminated)
        
        # Spracovanie do zamestnancov (zostáva rovnaké)
        sales_employees = []
        current_workplace = 'unknown'
        
        for _, row in df_filtered.iterrows():
            user = row.get('user', '')
            
            if user in ['praha', 'zlin', 'brno', 'vizovice']:
                current_workplace = user
                continue
            
            if not user or pd.isna(user) or str(user).strip() == '':
                continue
            
            employee = {
                'name': user,
                'workplace': current_workplace,
                'monthly_sales': {},
                'total_sales': 0,
                'score': 0
            }
            
            # Načítanie mesačných dát
            total_sales = 0
            month_columns = ['leden', 'unor', 'brezen', 'duben', 'kveten', 'cerven', 
                           'cervenec', 'srpen', 'zari', 'rijen', 'listopad', 'prosinec']
            
            for col in df_filtered.columns:
                if str(col).lower() in month_columns:
                    value = row.get(col, 0)
                    
                    # Konverzia 'X' na 0
                    if pd.isna(value) or str(value).upper().strip() == 'X':
                        value = 0
                    else:
                        try:
                            value = float(value)
                        except:
                            value = 0
                    
                    employee['monthly_sales'][col] = value
                    total_sales += value
            
            employee['total_sales'] = total_sales
            employee['score'] = calculate_employee_score_from_sales_amount(total_sales)
            
            sales_employees.append(employee)
        
        return sales_employees, df_filtered  # ✅ Vráti tuple s 2 hodnotami
        
    except Exception as e:
        st.error(f"Chyba pri načítaní sales dát: {e}")
        return pd.DataFrame(), pd.DataFrame()  # ✅ Vráti tuple namiesto listu




def filter_sales_data_new_logic(df, include_terminated=False):
    """
    ✅ OPRAVENÁ LOGIKA - hľadá posledný mesiac s dátami, nie chronologicky posledný
    """
    
    # Identifikácia mesačných stĺpcov v chronologickom poradí
    month_columns = ['leden', 'unor', 'brezen', 'duben', 'kveten', 'cerven', 
                    'cervenec', 'srpen', 'zari', 'rijen', 'listopad', 'prosinec']
    
    # Nájdi skutočné mesačné stĺpce v dátach
    available_months = []
    for col in df.columns:
        col_lower = str(col).lower()
        if col_lower in month_columns:
            available_months.append(col)
    
    if not available_months:
        return df
    
    # Zoradi mesiace chronologicky
    month_order = {month: i for i, month in enumerate(month_columns)}
    available_months.sort(key=lambda x: month_order.get(x.lower(), 999))
    
    # Ak zahrnúť všetkých, vráť všetko
    if include_terminated:
        return df
    
    # ✅ NOVÁ LOGIKA - nájdi posledný mesiac s dátami pre každého zamestnanca
    keep_indices = []
    
    for idx, row in df.iterrows():
        user = row.get('user', '')
        
        # Preskočiť mesta a prázdne riadky
        if (user in ['praha', 'zlin', 'brno', 'vizovice'] or 
            not user or pd.isna(user) or str(user).strip() == ''):
            keep_indices.append(idx)
            continue
        
        # ✅ NÁJDI POSLEDNÝ MESIAC S DÁTAMI (nie chronologicky posledný)
        last_month_with_data = None
        last_value = None
        
        # Prejdi mesiace odzadu (od decembra po január)
        for month in reversed(available_months):
            value = row.get(month, '')
            
            # Ak má mesiac dáta (nie je prázdny/NaN)
            if pd.notna(value) and str(value).strip() != '':
                last_month_with_data = month
                last_value = value
                break  # Našiel som posledný mesiac s dátami
        
        # Ak nenašiel žiadny mesiac s dátami, ponechaj (nový zamestnanec)
        if last_month_with_data is None:
            keep_indices.append(idx)
            continue
        
        # Ak posledný mesiac s dátami obsahuje 'X', vyhoď
        last_value_str = str(last_value).strip().upper()
        if last_value_str == 'X':
            pass  # Vylúčiť
        else:
            keep_indices.append(idx)
    
    df_filtered = df.iloc[keep_indices]
    return df_filtered







def load_internet_data():
    """Load ALL internet data files - vrátené na agregované dáta"""
    
    from pathlib import Path
    import pandas as pd
    
    data_path = Path("data/raw")
    
    if not data_path.exists():
        return None
    
    try:
        all_files = list(data_path.glob("*.xlsx"))
        internet_files = [f for f in all_files if 'internet' in f.name.lower()]
        
        if not internet_files:
            return None
        
        all_dataframes = []
        
        for file in internet_files:
            try:
                df = pd.read_excel(file, header=8)
                df_clean = df.dropna(subset=['Osoba ▲'])
                df_final = df_clean[~df_clean['Osoba ▲'].astype(str).str.startswith('*')]
                
                if len(df_final) > 0:
                    df_final = df_final.copy()
                    df_final['Source_File'] = file.name
                    all_dataframes.append(df_final)
                    
            except Exception:
                continue
        
        if not all_dataframes:
            return None
        
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        
        # Agregácia - obnovená
        time_columns = ['Mail', 'Chat', 'IS Sykora', 'SykoraShop', 'Web k praci', 
                       'Hry', 'Nepracovni weby', 'Čas celkem ▼', 'hladanie prace',
                       'Nezařazené', 'Umela inteligence']
        
        def sum_time_strings(series):
            total_minutes = 0
            for time_str in series.dropna():
                if pd.notna(time_str) and str(time_str) not in ['', 'nan']:
                    try:
                        parts = str(time_str).split(':')
                        if len(parts) >= 2:
                            hours = int(parts[0])
                            minutes = int(parts[1])
                            seconds = int(parts[2]) if len(parts) > 2 else 0
                            total_minutes += hours * 60 + minutes + seconds / 60
                    except:
                        pass
            
            if total_minutes == 0:
                return "00:00:00"
            
            hours = int(total_minutes // 60)
            minutes = int(total_minutes % 60)
            seconds = int((total_minutes % 1) * 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        agg_dict = {}
        for col in time_columns:
            if col in combined_df.columns:
                agg_dict[col] = sum_time_strings
        
        if 'Přihlašovací jméno' in combined_df.columns:
            agg_dict['Přihlašovací jméno'] = 'first'
        
        aggregated_df = combined_df.groupby('Osoba ▲').agg(agg_dict).reset_index()
        
        return aggregated_df
        
    except Exception as e:
        return None



def load_applications_data():
    """Load ALL applications data files - vrátené na agregované dáta"""
    
    from pathlib import Path
    import pandas as pd
    
    data_path = Path("data/raw")
    
    if not data_path.exists():
        return None
    
    try:
        # ✅ OPRAVENÉ - hľadáme "applications" namiesto "application"
        all_files = list(data_path.glob("*.xlsx"))
        app_files = [f for f in all_files if 'applications' in f.name.lower() and 'internet' not in f.name.lower()]
        
        if not app_files:
            return None
        
        # KOMBINÁCIA VŠETKÝCH SÚBOROV
        all_dataframes = []
        
        for file in app_files:
            try:
                df = pd.read_excel(file, header=8)
                df_clean = df.dropna(subset=['Osoba ▲'])
                df_final = df_clean[~df_clean['Osoba ▲'].astype(str).str.startswith('*')]
                
                if len(df_final) > 0:
                    df_final = df_final.copy()
                    df_final['Source_File'] = file.name
                    all_dataframes.append(df_final)
                    
            except Exception:
                continue
        
        if not all_dataframes:
            return None
        
        # Kombinácia všetkých súborov
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        
        # Aplikačné time stĺpce
        app_time_columns = ['Helios Green', 'Chat', 'Imos - program', 'Mail', 
                           'Programy', 'Půdorysy', 'Čas celkem ▼', 'Internet']
        
        # Agregácia časov
        def sum_time_strings(series):
            total_minutes = 0
            for time_str in series.dropna():
                if pd.notna(time_str) and str(time_str) not in ['', 'nan']:
                    try:
                        parts = str(time_str).split(':')
                        if len(parts) >= 2:
                            hours = int(parts[0])
                            minutes = int(parts[1])
                            seconds = int(parts[2]) if len(parts) > 2 else 0
                            total_minutes += hours * 60 + minutes + seconds / 60
                    except:
                        pass
            
            if total_minutes == 0:
                return "00:00:00"
            
            hours = int(total_minutes // 60)
            minutes = int(total_minutes % 60)
            seconds = int((total_minutes % 1) * 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Agregačný slovník
        agg_dict = {}
        for col in app_time_columns:
            if col in combined_df.columns:
                agg_dict[col] = sum_time_strings
        
        # Pridanie non-time stĺpcov
        if 'Přihlašovací jméno' in combined_df.columns:
            agg_dict['Přihlašovací jméno'] = 'first'
        
        # Finálna agregácia podľa osoby
        aggregated_df = combined_df.groupby('Osoba ▲').agg(agg_dict).reset_index()
        
        return aggregated_df
        
    except Exception as e:
        return None


def load_internet_data_detailed():
    """NOVÁ NADSTAVBA: Načíta individuálne denné záznamy pre timeline analýzu"""
    
    from pathlib import Path
    import pandas as pd
    
    data_path = Path("data/raw")
    
    if not data_path.exists():
        return None
    
    try:
        all_files = list(data_path.glob("*.xlsx"))
        internet_files = [f for f in all_files if 'internet' in f.name.lower()]
        
        if not internet_files:
            return None
        
        all_dataframes = []
        
        for file in internet_files:
            try:
                df = pd.read_excel(file, header=8)
                df_clean = df.dropna(subset=['Osoba ▲'])
                df_final = df_clean[~df_clean['Osoba ▲'].astype(str).str.startswith('*')]
                
                if len(df_final) > 0:
                    df_final = df_final.copy()
                    df_final['Source_File'] = file.name
                    
                    # Extrahuj dátum z názvu súboru
                    import re
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', file.name)
                    if date_match:
                        df_final['Date'] = date_match.group(1)
                    else:
                        df_final['Date'] = 'unknown'
                    
                    all_dataframes.append(df_final)
                    
            except Exception:
                continue
        
        if not all_dataframes:
            return None
        
        # ZACHOVÁ INDIVIDUÁLNE RIADKY (žiadna agregácia)
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        
        return combined_df
        
    except Exception:
        return None


def load_applications_data_detailed():
    """NOVÁ NADSTAVBA: Načíta individuálne denné záznamy pre timeline analýzu"""
    
    from pathlib import Path
    import pandas as pd
    
    data_path = Path("data/raw")
    
    if not data_path.exists():
        return None
    
    try:
        # Nájdi VŠETKY applications súbory
        all_files = list(data_path.glob("*.xlsx"))
        app_files = [f for f in all_files if 'application' in f.name.lower() and 'internet' not in f.name.lower()]
        
        if not app_files:
            return None
        
        # KOMBINÁCIA VŠETKÝCH SÚBOROV
        all_dataframes = []
        
        for file in app_files:
            try:
                df = pd.read_excel(file, header=8)
                df_clean = df.dropna(subset=['Osoba ▲'])
                df_final = df_clean[~df_clean['Osoba ▲'].astype(str).str.startswith('*')]
                
                if len(df_final) > 0:
                    df_final = df_final.copy()
                    df_final['Source_File'] = file.name
                    
                    # Extrahuj dátum z názvu súboru
                    import re
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', file.name)
                    if date_match:
                        df_final['Date'] = date_match.group(1)
                    else:
                        df_final['Date'] = 'unknown'
                    
                    all_dataframes.append(df_final)
                    
            except Exception:
                continue
        
        if not all_dataframes:
            return None
        
        # ZACHOVÁ INDIVIDUÁLNE RIADKY (žiadna agregácia)
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        
        return combined_df
        
    except Exception:
        return None





def debug_data_loading():
    """Debug funkcia - deaktivovaná"""
    pass

def calculate_employee_score_from_sales_amount(total_sales):
    """Výpočet skóre na základe celkového predaja"""
    
    if total_sales >= 5000000:  # 5M+
        base_score = 90
    elif total_sales >= 4000000:  # 4M+
        base_score = 85
    elif total_sales >= 3000000:  # 3M+
        base_score = 75
    elif total_sales >= 2000000:  # 2M+
        base_score = 65
    elif total_sales >= 1000000:  # 1M+
        base_score = 50
    elif total_sales > 0:
        base_score = 30
    else:
        base_score = 20
    
    # Malá variácia pre realistickosť
    import random
    random.seed(hash(str(total_sales)))
    variation = random.uniform(-5, 5)
    
    final_score = max(20, min(95, base_score + variation))
    return round(final_score, 2)

@handle_error
def initialize_session_state():
    """Inicializácia s forced reload pri zmene nastavení"""
    
    if 'current_page' not in st.session_state:
        # ✅ Nastav default page podľa používateľských oprávnení
        st.session_state.current_page = get_default_page()
    
    if 'selected_employee' not in st.session_state:
        st.session_state.selected_employee = None
    
    if 'include_terminated_employees' not in st.session_state:
        st.session_state.include_terminated_employees = False
    
    # ✅ FORCE RELOAD ak sa nastavenie zmenilo alebo analyzer neexistuje
    if ('analyzer' not in st.session_state or 
        st.session_state.get('last_terminated_setting') != st.session_state.get('include_terminated_employees')):
        
        # Načítanie dát
        sales_data, raw_sales_df = load_sales_data()
        internet_data = load_internet_data()
        applications_data = load_applications_data()
        
        # Vytvorenie analyzátora
        analyzer = DataAnalyzer()
        analyzer.load_data(
            sales_data=sales_data, 
            internet_data=internet_data, 
            applications_data=applications_data,
            data_path="data/raw"  # ✅ PRIDANÉ
        )
        analyzer.raw_sales_data = raw_sales_df  # Pridáme aj pôvodné DataFrame
        analyzer.validate_sales_consistency()
        
        st.session_state.analyzer = analyzer
        st.session_state.last_terminated_setting = st.session_state.get('include_terminated_employees')




def create_sidebar():
    """Vytvorí postranný panel s navigáciou - context-aware verzia"""
    
    with st.sidebar:
        # Context-aware sidebar obsah
        current_page = st.session_state.get('current_page', 'overview')
        
        if current_page == 'admin':
            # ADMIN PANEL SIDEBAR
            st.markdown("# 👑 Admin Panel")
            
            # Tlačidlo späť na Overview
            if st.button("⬅️ Späť na Overview", width='stretch', type="primary", key="back_to_overview_admin"):
                st.session_state.current_page = 'overview'
                # Vyčisti všetky admin session state
                keys_to_clear = ['show_monitoring_dashboard', 'show_structure', 'show_file_management']
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
            
            st.divider()
            st.markdown("### 🔧 Admin sekcia")
            st.info("Ste v administrácii systému")
            
        else:
            # NORMÁLNE STRÁNKY SIDEBAR  
            # NASTAVENIA - na vrchu (iba pre oprávnených používateľov)
            if is_admin() or has_feature_access("settings_access"):
                if st.button("⚙️ Nastavenia", width='stretch',
                            type="primary" if current_page == 'settings' else "secondary"):
                    st.session_state.current_page = 'settings'
                    st.rerun()
                
                st.divider()
            
            # Získaj povolené stránky pre aktuálneho používateľa
            allowed_pages = get_allowed_pages()
            
            # NAVIGAČNÉ TLAČIDLÁ - iba povolené stránky
            if 'overview' in allowed_pages:
                if st.button("🏠 Prehľad", width='stretch', 
                            type="primary" if current_page == 'overview' else "secondary"):
                    st.session_state.current_page = 'overview'
                    st.session_state.selected_employee = None
                    st.rerun()
            
            if 'employee' in allowed_pages:
                if st.button("👤 Detail zamestnanca", width='stretch',
                            type="primary" if current_page == 'employee' else "secondary"):
                    if st.session_state.selected_employee:
                        st.session_state.current_page = 'employee'
                    else:
                        st.warning("Najprv vyberte zamestnanca v prehľade")
            
            if 'benchmark' in allowed_pages:
                if st.button("🏆 Benchmark", width='stretch',
                            type="primary" if current_page == 'benchmark' else "secondary"):
                    st.session_state.current_page = 'benchmark'
                    st.session_state.selected_employee = None
                    st.rerun()
            
            if 'heatmap' in allowed_pages:
                if st.button("🔥 Heatmapa", width='stretch',
                            type="primary" if current_page == 'heatmap' else "secondary"):
                    st.session_state.current_page = 'heatmap'
                    st.rerun()
                    
            if 'studio' in allowed_pages:
                if st.button("🏢 Studio", width='stretch',
                    type="primary" if current_page == 'studio' else "secondary"):
                    st.session_state.current_page = 'studio'
                    st.session_state.selected_employee = None
                    st.rerun()
            
            if 'kpi_system' in allowed_pages:
                if st.button("🎯 KPI Systém", width='stretch',
                            type="primary" if current_page == 'kpi_system' else "secondary"):
                    st.session_state.current_page = 'kpi_system'
                    st.session_state.selected_employee = None
                    st.rerun()
            
            # ✅ Admin tlačidlo (iba pre adminov s oprávnením)
            if is_admin() and 'admin' in allowed_pages:
                if st.button("👑 Administrácia", width='stretch',
                            type="primary" if current_page == 'admin' else "secondary"):
                    st.session_state.current_page = 'admin'
                    st.rerun()
            
            st.divider()
            
            # INFO O VYBRANOM ZAMESTNANCOVI
            if st.session_state.selected_employee:
                st.markdown("### 👤 Vybratý zamestnanec")
                st.info(f"**{st.session_state.selected_employee}**")
                
                if st.button("❌ Zrušiť výber", width='stretch'):
                    st.session_state.selected_employee = None
                    st.rerun()
            
            st.divider()
            
            # CELKOVÉ ŠTATISTIKY - iba ak má používateľ povolené
            if 'analyzer' in st.session_state and can_show_sidebar_statistics():
                stats = st.session_state.analyzer.calculate_company_statistics()
                
                st.markdown("### 📊 Celkové štatistiky")
                st.metric("Zamestnanci", stats['total_employees'])
                st.metric("Celkový predaj", format_money(stats['total_sales']))
                st.metric("Priemer na zamestnanca", format_money(stats['average_sales_per_employee']))
            
            # BENCHMARK QUICK STATS
            if st.session_state.current_page == 'benchmark':
                st.markdown("### 🏆 Benchmark Info")
                
                # Quick benchmark stats
                employees = st.session_state.analyzer.get_all_employees_summary()
                if employees:
                    # Cieľ pre štvrťrok (2M)
                    target_2m = 2_000_000
                    achieved_target = len([emp for emp in employees if emp.get('total_sales', 0) >= target_2m])
                    
                    st.metric("Dosiahli 2M cieľ", f"{achieved_target}/{len(employees)}")
                    success_rate = (achieved_target / len(employees)) * 100 if employees else 0
                    st.metric("Úspešnosť", f"{success_rate:.1f}%")
        
        st.divider()
        
        # DEBUG INFO
        with st.expander("🔧 Debug Info"):
            debug_info = {
                "current_page": st.session_state.current_page,
                "selected_employee": st.session_state.selected_employee,
                "analyzer_loaded": 'analyzer' in st.session_state,
                "include_terminated": st.session_state.get('include_terminated_employees', False),
                "internet_data_loaded": (hasattr(st.session_state.get('analyzer'), 'internet_data') and 
                                       st.session_state.analyzer.internet_data is not None) if 'analyzer' in st.session_state else False,
                "applications_data_loaded": (hasattr(st.session_state.get('analyzer'), 'applications_data') and 
                                           st.session_state.analyzer.applications_data is not None) if 'analyzer' in st.session_state else False
            }
            st.json(debug_info)



def main():
    """Hlavná funkcia aplikácie s error handlingom"""
    try:
        st.set_page_config(
            page_title="Dashboard produktivity zaměstnanců", 
            page_icon="📊", 
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Inicializácia autentifikačného systému
        init_auth()
        
        # Inicializácia server monitoring
        monitor = get_server_monitor()
        if not monitor.monitoring:
            monitor.start_monitoring(interval_seconds=120)  # Každé 2 minúty
        
        # Ak používateľ nie je prihlásený, zobraz login stránku
        if not is_authenticated():
            show_login_page()
            return
        
        # Volanie hlavnej aplikačnej logiky
        run_main_application()
        
    except Exception as e:
        # Globálne error handling
        log_error(e, {
            "function": "main",
            "page": st.session_state.get('current_page', 'unknown')
        })
        
        st.error("❌ Nastala kritická chyba aplikácie")
        
        # Pre adminov zobraz detaily
        try:
            if is_admin():
                with st.expander("🔧 Detaily chyby (len pre adminov)"):
                    st.code(f"Error: {type(e).__name__}")
                    st.code(f"Message: {str(e)}")
                    st.code(f"Page: {st.session_state.get('current_page', 'unknown')}")
        except:
            pass
        
        # Tlačidlo na refresh
        if st.button("🔄 Obnoviť aplikáciu"):
            st.rerun()


def run_main_application():
    """Hlavná aplikačná logika oddelená od error handlingu"""
    # Inicializácia session state
    initialize_session_state()
    
    # Vytvorenie sidebar navigácie - PRED admin routing
    create_sidebar()
    
    # Ak je prihlásený admin a je na admin stránke
    if st.session_state.get('current_page') == 'admin':
        if is_admin():
            log_page_activity('admin')
            show_admin_page()
            show_user_info()
            return
        else:
            st.error("❌ Nemáte oprávnenie na túto stránku")
            st.session_state.current_page = 'overview'
            st.rerun()
    
    # ✅ SUPER-NUKLEÁRNY CSS PRED apply_dark_theme()
    st.markdown("""
    <style>
    /* EMERGENCY ANTI-PINK OVERRIDE */
    button:hover, button:focus, button:active,
    .stButton > button:hover, .stButton > button:focus, .stButton > button:active,
    .stSidebar button:hover, .stSidebar button:focus, .stSidebar button:active {
        background-color: #2563eb !important;
        background-image: none !important;
        border-color: #2563eb !important;
        color: white !important;
        outline: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Aplikovanie tmavej témy
    apply_dark_theme()
    
    # Zobrazenie informácií o používateľovi
    show_user_info()
    
    # Inicializácia session state
    initialize_session_state()
    
    # ✅ PAGE ACCESS CONTROL - kontrola oprávnení
    current_page = st.session_state.current_page
    
    # Špeciálne pravidlo pre detail stránky
    if current_page in ['employee_detail']:
        if not can_access_detail_page(current_page):
            st.error(f"❌ Nemáte oprávnenie pre {current_page} (potrebujete prístup k parent stránke)")
            
            # Presmeruj na vhodnú parent stránku
            parent_page = get_parent_page_for_detail(current_page)
            st.info(f"🔄 Presmerovávame na: {parent_page}")
            st.session_state.current_page = parent_page
            st.rerun()
    elif not can_access_page(current_page):
        st.error(f"❌ Nemáte oprávnenie pre stránku: {current_page}")
        
        # Presmeruj na default stránku
        default_page = get_default_page()
        st.info(f"🔄 Presmerovávame na: {default_page}")
        st.session_state.current_page = default_page
        st.rerun()
    
    # Získanie analyzátora
    analyzer = st.session_state.analyzer
    
    # ✅ ROZŠÍRENÝ ROUTING - pridaný benchmark
    try:
        if st.session_state.current_page == 'overview':
            log_page_activity('overview')
            overview.render(analyzer)
            
        elif st.session_state.current_page == 'employee':
            log_page_activity('employee')
            if st.session_state.selected_employee:
                employee.render(analyzer, st.session_state.selected_employee)
                
            else:
                st.error("Žiadny zamestnanec nie je vybratý!")
                if st.button("← Späť na prehľad"):
                    st.session_state.current_page = 'overview'
                    st.rerun()
        
        
        # ✅ NOVÝ - Benchmark routing
        elif st.session_state.current_page == 'benchmark':
            log_page_activity('benchmark')
            benchmark.render(analyzer)
                    
        elif st.session_state.current_page == 'heatmap':
            log_page_activity('heatmap')
            heatmap.render(analyzer)
        elif st.session_state.current_page == 'studio':
            log_page_activity('studio')
            studio.render(analyzer)
            
        elif st.session_state.current_page == 'kpi_system':
            log_page_activity('kpi_system')
            from ui.pages import kpi_system
            kpi_system.render()

        elif st.session_state.current_page == 'settings':
            log_page_activity('settings')
            settings.show_settings()

        elif st.session_state.current_page == 'user_management':
            log_page_activity('user_management')
            user_management.render()

        elif st.session_state.current_page == 'employee_detail':
            log_page_activity('employee_detail')
            if 'selected_employee_name' in st.session_state:
                # ✅ OPRAVA: Musíš mať StudioAnalyzer, nie DataAnalyzer
                # Ak prichádzaš zo Studio, použiješ iný analyzer
                if 'studio_analyzer' in st.session_state:
                    employee_detail.render(st.session_state['selected_employee_name'], st.session_state['studio_analyzer'])
                else:
                    # Ak nemáš StudioAnalyzer, presmeruj na Studio
                    st.error("❌ Detail zamestnanca je dostupný len v Studio module")
                    st.session_state.current_page = 'studio' 
                    st.rerun()
            else:
                st.error("Žiadny zamestnanec nie je vybratý!")
                st.session_state.current_page = 'studio'
                st.rerun()

            
        else:
            st.error(f"Neznáma stránka: {st.session_state.current_page}")
            st.session_state.current_page = 'overview'
            st.rerun()
            
    except Exception as e:
        st.error(f"Chyba pri renderovaní stránky: {e}")

        
        # Fallback na overview
        if st.button("🔄 Obnoviť aplikáciu"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


if __name__ == "__main__":
    main()