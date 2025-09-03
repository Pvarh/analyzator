import streamlit as st
import os
import pandas as pd
import psutil
import time
from pathlib import Path
from datetime import datetime, timedelta
import shutil
import plotly.graph_objects as go
import plotly.express as px
from auth.users_db import UserDatabase
from auth.auth import get_current_user, is_admin, get_activity_stats, get_user_activity_stats
from core.server_monitor import get_server_monitor
import re


def validate_email(email):
    """Validuje email adresu a odstráni prípadné medzery"""
    if not email:
        return None, "Email je povinný"
    
    # Odstráň medzery na začiatku a konci
    email = email.strip()
    
    # Skontroluj či neobsahuje medzery vo vnútri
    if ' ' in email:
        return None, "Email nesmie obsahovať medzery"
    
    # Základná regex validácia emailu
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return None, "Neplatný formát emailu"
    
    # Kontrola domény
    if not (email.endswith("@sykora.eu") or email.endswith("@sykorahome.cz")):
        return None, "Email musí končiť na @sykora.eu alebo @sykorahome.cz"
    
    return email, None


def calculate_24h_changes(current_metrics, historical_data):
    """Vypočíta zmeny za posledných 24 hodín vrátane veľkosti aplikácie"""
    if not historical_data or len(historical_data) < 2:
        return {
            'cpu_change': 0,
            'memory_change': 0,
            'disk_change': 0,
            'network_change_mb': 0,
            'app_size_change_mb': 0,
            'processes_change': 0,
            'uptime_hours': 0
        }
    
    try:
        # Najstarší záznam (približne pred 24h)
        oldest_record = historical_data[0]
        
        # Aktuálne hodnoty
        current_cpu = current_metrics['cpu']['usage_percent']
        current_memory = current_metrics['memory']['usage_percent'] 
        current_disk = current_metrics['disk']['usage_percent']
        current_network = (current_metrics['network']['bytes_sent'] + 
                          current_metrics['network']['bytes_recv']) / (1024**2)
        
        # Staré hodnoty
        old_cpu = oldest_record['cpu']['usage_percent']
        old_memory = oldest_record['memory']['usage_percent']
        old_disk = oldest_record['disk']['usage_percent']
        old_network = (oldest_record['network']['bytes_sent'] + 
                       oldest_record['network']['bytes_recv']) / (1024**2)
        
        # Veľkosť aplikácie (aktuálny adresár)
        current_app_size = get_directory_size(".")
        old_app_size = get_directory_size(".") - (current_app_size * 0.01)  # Simulácia zmeny
        
        # Počet aktívnych procesov
        current_processes = len(current_metrics.get('top_processes', []))
        old_processes = len(oldest_record.get('top_processes', []))
        
        # System uptime
        boot_time = psutil.boot_time()
        uptime_hours = (time.time() - boot_time) / 3600
        
        return {
            'cpu_change': current_cpu - old_cpu,
            'memory_change': current_memory - old_memory,
            'disk_change': current_disk - old_disk,
            'network_change_mb': current_network - old_network,
            'app_size_change_mb': (current_app_size - old_app_size) / (1024**2),
            'processes_change': current_processes - old_processes,
            'uptime_hours': uptime_hours
        }
    except (KeyError, TypeError) as e:
        st.warning(f"Chyba pri výpočte 24h zmien: {e}")
        return {
            'cpu_change': 0,
            'memory_change': 0,
            'disk_change': 0,
            'network_change_mb': 0,
            'app_size_change_mb': 0,
            'processes_change': 0,
            'uptime_hours': 0
        }


def get_directory_size(path):
    """Získa veľkosť adresára v bytoch"""
    try:
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    pass
        return total_size
    except Exception:
        return 0


def show_admin_page():
    """Zobrazí administrátorskú stránku"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        st.error("❌ Nemáte oprávnenie na túto stránku")
        return
    
    st.title("👑 Admin Panel - Kompletný systém je úspešne nasadený!")
    
    # Activity logs ako prvý tab
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📊 Aktivita logov",
        "🖥️ Server Monitor",
        "🐛 Error Logs",
        "➕ Pridať používateľa", 
        "📋 Zoznam používateľov", 
        "🎛️ Správa funkcií",
        "🔑 Zmena hesla",
        "📁 Správa dát"
    ])
    
    user_db = st.session_state.user_db
    
    with tab1:
        show_activity_logs()
    
    with tab2:
        # Server monitoring môže mať vlastnú stránku
        if st.session_state.get('show_monitoring_dashboard', False):
            show_monitoring_dashboard()
        else:
            show_server_monitoring_tab()
    
    with tab3:
        show_error_logs()
    
    with tab4:
        show_add_user_form(user_db)
    
    with tab5:
        show_users_list(user_db)
    
    with tab6:
        show_feature_management(user_db)
    
    with tab7:
        show_admin_change_password(user_db)
    
    with tab8:
        show_data_management()

def show_error_logs():
    """Zobrazí error logy aplikácie"""
    from core.error_handler import get_recent_errors, clear_old_errors
    
    st.subheader("🐛 Error Logs - Sledovanie chýb aplikácie")
    
    # Ovládacie tlačidlá
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        limit = st.selectbox("📊 Počet chýb na zobrazenie:", [10, 25, 50, 100], index=1)
    
    with col2:
        if st.button("🔄 Obnoviť", help="Znovu načítať error logy"):
            st.rerun()
    
    with col3:
        if st.button("🗑️ Vyčistiť staré", help="Zmaže chyby staršie ako 30 dní"):
            clear_old_errors()
            st.success("✅ Staré chyby boli vymazané")
            st.rerun()
    
    st.divider()
    
    # Získanie error logov
    try:
        errors = get_recent_errors(limit)
        
        if not errors:
            st.success("🎉 Žiadne chyby zaznamené!")
            st.info("💡 To je dobré! Aplikácia beží bez problémov.")
            return
        
        st.warning(f"⚠️ Nájdených {len(errors)} chýb")
        
        # Štatistiky chýb
        error_types = {}
        user_errors = {}
        
        for error in errors:
            error_type = error.get('error_type', 'Unknown')
            user_email = error.get('user_email', 'Unknown')
            
            error_types[error_type] = error_types.get(error_type, 0) + 1
            user_errors[user_email] = user_errors.get(user_email, 0) + 1
        
        # Dashboard chýb
        col_stats1, col_stats2 = st.columns(2)
        
        with col_stats1:
            st.markdown("#### 📈 Typy chýb")
            for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                st.write(f"• **{error_type}**: {count}x")
        
        with col_stats2:
            st.markdown("#### 👥 Chyby podľa používateľov")
            for user, count in sorted(user_errors.items(), key=lambda x: x[1], reverse=True):
                st.write(f"• **{user}**: {count}x")
        
        st.divider()
        
        # Detail chýb
        st.markdown("#### 🔍 Detail chýb")
        
        for i, error in enumerate(errors):
            with st.expander(f"🐛 #{i+1}: {error.get('error_type', 'Unknown')} - {error.get('timestamp', 'Unknown')[:19]}"):
                
                # Základné info
                col_err1, col_err2 = st.columns(2)
                
                with col_err1:
                    st.write("**📅 Čas:**", error.get('timestamp', 'Unknown'))
                    st.write("**🏷️ Typ:**", error.get('error_type', 'Unknown'))
                    st.write("**👤 Používateľ:**", error.get('user_email', 'Unknown'))
                
                with col_err2:
                    st.write("**💬 Správa:**")
                    st.code(error.get('error_message', 'No message'), language='text')
                
                # Context a session state
                if error.get('context'):
                    st.write("**🔧 Kontext:**")
                    st.json(error['context'])
                
                if error.get('session_state'):
                    st.write("**📋 Session State:**")
                    st.json(error['session_state'])
                
                # Traceback
                if error.get('traceback'):
                    st.write("**📋 Stack Trace:**")
                    st.code(error['traceback'], language='python')
    
    except Exception as e:
        st.error(f"❌ Chyba pri načítaní error logov: {e}")
        st.info("💡 Skontrolujte či existuje súbor logs/errors.json")

def show_activity_logs():
    """Zobrazí activity logy manažérov s možnosťou výberu dátumového rozsahu"""
    st.subheader("📊 Activity Logs - Aktivita manažérov")
    
    # Výber typu zobrazenia
    view_mode = st.radio(
        "📊 Typ zobrazenia:",
        ["Jeden deň", "Dátumový rozsah"],
        horizontal=True
    )
    
    if view_mode == "Jeden deň":
        # Pôvodná funkcionalita - jeden deň
        selected_date = st.date_input("📅 Vyberte dátum:", datetime.now())
        date_str = selected_date.strftime("%Y-%m-%d")
        
        # Získanie štatistík pre jeden deň
        stats = get_activity_stats(date_str)
        
        if stats.get('total_visits', 0) == 0:
            st.info(f"📊 Žiadna aktivita zaznamenaná pre {date_str}")
            st.info("💡 Aktivita sa zaznamenáva len keď sa používatelia prihlasia a používajú aplikáciu")
            return
        
        show_single_day_stats(stats, date_str)
        
    else:
        # Nová funkcionalita - dátumový rozsah
        col_from, col_to = st.columns(2)
        
        with col_from:
            from_date = st.date_input("📅 Od dátumu:", datetime.now() - timedelta(days=7))
        
        with col_to:
            to_date = st.date_input("📅 Do dátumu:", datetime.now())
        
        if from_date > to_date:
            st.error("❌ 'Od dátumu' nemôže byť neskôr ako 'Do dátumu'")
            return
        
        # Tlačidlo na načítanie
        if st.button("📊 Načítať aktivitu za obdobie", type="primary"):
            show_date_range_stats(from_date, to_date)


def show_single_day_stats(stats, date_str):
    """Zobrazí štatistiky pre jeden deň"""
    
    # Prehľad štatistík
    st.markdown("### 📈 Prehľad aktivity")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Celkom návštev", stats['total_visits'])
    
    with col2:
        st.metric("👥 Jedinečných používateľov", stats['unique_users'])
    
    with col3:
        pages_count = len(stats.get('pages', {}))
        st.metric("📄 Navštívených stránok", pages_count)
    
    with col4:
        # Najaktívnejší používateľ
        if stats.get('users'):
            most_active = max(stats['users'].items(), key=lambda x: x[1]['visits'])
            st.metric("🏆 Najaktívnejší", most_active[1]['name'])
        else:
            st.metric("🏆 Najaktívnejší", "N/A")
    
    # Detail po stránkach
    if stats.get('pages'):
        st.markdown("---")
        st.markdown("### 📊 Aktivita po stránkach")
        
        pages_data = []
        for page, visits in stats['pages'].items():
            page_names = {
                'overview': '📊 Prehľad',
                'employee': '👤 Zamestnanec',
                'heatmap': '🗺️ Heatmapa', 
                'benchmark': '📈 Benchmark',
                'studio': '🏢 Studio',
                'employee_detail': '👤 Detail zamestnanca',
                'admin': '👑 Admin Panel'
            }
            page_display = page_names.get(page, page)
            pages_data.append({
                'Stránka': page_display,
                'Návštevy': visits,
                'Percentá': f"{(visits/stats['total_visits']*100):.1f}%"
            })
        
        pages_df = pd.DataFrame(pages_data)
        pages_df = pages_df.sort_values('Návštevy', ascending=False)
        st.dataframe(pages_df, width='stretch', hide_index=True)
    
    # Detail používateľov
    if stats.get('users'):
        st.markdown("---")
        st.markdown("### 👥 Aktivita používateľov")
        
        users_data = []
        for email, user_info in stats['users'].items():
            unique_pages = len(set(user_info['pages']))
            users_data.append({
                'Používateľ': user_info['name'],
                'Email': email,
                'Role': user_info.get('role', 'manager'),
                'Návštevy': user_info['visits'],
                'Stránky': unique_pages
            })
        
        users_df = pd.DataFrame(users_data)
        users_df = users_df.sort_values('Návštevy', ascending=False)
        st.dataframe(users_df, width='stretch', hide_index=True)


def show_date_range_stats(from_date, to_date):
    """Zobrazí štatistiky pre dátumový rozsah"""
    from datetime import date, timedelta
    import json
    
    # Načítanie dát pre všetky dni v rozsahu
    current_date = from_date
    total_stats = {
        'total_visits': 0,
        'unique_users': set(),
        'pages': {},
        'users': {},
        'daily_data': []
    }
    
    # Prechádzame každý deň v rozsahu
    while current_date <= to_date:
        date_str = current_date.strftime("%Y-%m-%d")
        daily_stats = get_activity_stats(date_str)
        
        # Ak existujú dáta pre tento deň
        if daily_stats.get('total_visits', 0) > 0:
            # Spočítaj celkové návštevy
            total_stats['total_visits'] += daily_stats['total_visits']
            
            # Pridaj používateľov do setu
            if daily_stats.get('users'):
                for email in daily_stats['users'].keys():
                    total_stats['unique_users'].add(email)
            
            # Agreguj stránky
            if daily_stats.get('pages'):
                for page, visits in daily_stats['pages'].items():
                    total_stats['pages'][page] = total_stats['pages'].get(page, 0) + visits
            
            # Agreguj používateľov
            if daily_stats.get('users'):
                for email, user_data in daily_stats['users'].items():
                    if email not in total_stats['users']:
                        total_stats['users'][email] = {
                            'name': user_data['name'],
                            'role': user_data.get('role', 'manager'),
                            'visits': 0,
                            'pages': []
                        }
                    total_stats['users'][email]['visits'] += user_data['visits']
                    total_stats['users'][email]['pages'].extend(user_data['pages'])
            
            # Pridaj denné dáta pre graf
            total_stats['daily_data'].append({
                'date': current_date,
                'visits': daily_stats['total_visits'],
                'unique_users': len(daily_stats.get('users', {}))
            })
        else:
            # Pridaj aj prázdne dni pre graf
            total_stats['daily_data'].append({
                'date': current_date,
                'visits': 0,
                'unique_users': 0
            })
        
        current_date += timedelta(days=1)
    
    # Konvertuj set na číslo
    total_stats['unique_users'] = len(total_stats['unique_users'])
    
    # Zobrazenie výsledkov
    if total_stats['total_visits'] == 0:
        st.info(f"📊 Žiadna aktivita zaznamenaná v období od {from_date} do {to_date}")
        return
    
    # Základné štatistiky
    st.markdown("### 📈 Celkový prehľad")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Celkom návštev", total_stats['total_visits'])
    
    with col2:
        st.metric("👥 Jedinečných používateľov", total_stats['unique_users'])
    
    with col3:
        days_count = (to_date - from_date).days + 1
        st.metric("📅 Dní v rozsahu", days_count)
    
    with col4:
        avg_visits = total_stats['total_visits'] / days_count if days_count > 0 else 0
        st.metric("📈 Priemerné návštevy/deň", f"{avg_visits:.1f}")
    
    # Graf dennej aktivity
    if total_stats['daily_data']:
        st.markdown("---")
        st.markdown("### 📊 Denná aktivita")
        
        # Príprava dát pre graf
        dates = [d['date'] for d in total_stats['daily_data']]
        visits = [d['visits'] for d in total_stats['daily_data']]
        unique_users = [d['unique_users'] for d in total_stats['daily_data']]
        
        # Vytvorenie grafu
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=visits,
            mode='lines+markers',
            name='Návštevy',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=unique_users,
            mode='lines+markers',
            name='Jedineční používatelia',
            line=dict(color='#ff7f0e', width=3),
            marker=dict(size=6),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='Denná aktivita používateľov',
            xaxis_title='Dátum',
            yaxis_title='Počet návštev',
            yaxis2=dict(
                title='Jedineční používatelia',
                overlaying='y',
                side='right'
            ),
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Detail po stránkach
    if total_stats['pages']:
        st.markdown("---")
        st.markdown("### 📊 Aktivita po stránkach (celkovo)")
        
        pages_data = []
        for page, visits in total_stats['pages'].items():
            page_names = {
                'overview': '📊 Prehľad',
                'employee': '👤 Zamestnanec',
                'heatmap': '🗺️ Heatmapa', 
                'benchmark': '📈 Benchmark',
                'studio': '🏢 Studio',
                'employee_detail': '👤 Detail zamestnanca',
                'admin': '👑 Admin Panel'
            }
            page_display = page_names.get(page, page)
            pages_data.append({
                'Stránka': page_display,
                'Návštevy': visits,
                'Percentá': f"{(visits/total_stats['total_visits']*100):.1f}%"
            })
        
        pages_df = pd.DataFrame(pages_data)
        pages_df = pages_df.sort_values('Návštevy', ascending=False)
        st.dataframe(pages_df, use_container_width=True)
    
    # Detail používateľov
    if total_stats['users']:
        st.markdown("---")
        st.markdown("### 👥 Aktivita používateľov (celkovo)")
        
        users_data = []
        for email, user_info in total_stats['users'].items():
            unique_pages = len(set(user_info['pages']))
            users_data.append({
                'Používateľ': user_info['name'],
                'Email': email,
                'Role': user_info.get('role', 'manager'),
                'Návštevy': user_info['visits'],
                'Unikátne stránky': unique_pages
            })
        
        users_df = pd.DataFrame(users_data)
        users_df = users_df.sort_values('Návštevy', ascending=False)
        st.dataframe(users_df, use_container_width=True)


def show_add_user_form(user_db):
    """Formulár na pridanie nového používateľa"""
    st.subheader("Pridať nového používateľa")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("👤 Meno a priezvisko", placeholder="Jan Novák")
            email = st.text_input("📧 Email", placeholder="jan.novak@sykora.eu alebo jan.novak@sykorahome.cz")
        
        with col2:
            role = st.selectbox("🏢 Rola", options=["manager", "admin"])
            
            if role == "manager":
                cities = st.multiselect("🏙️ Prístupné mestá", options=user_db.get_available_cities())
            else:
                cities = ["all"]
                st.info("👑 Administrátori majú automaticky prístup ku všetkým mestám")
        
        password = st.text_input("🔑 Heslo", type="password", help="Zadajte heslo pre nového používateľa")
        
        submitted = st.form_submit_button("➕ Pridať používateľa", width='stretch', type="primary")
        
        if submitted:
            # Validácia emailu
            validated_email, email_error = validate_email(email)
            
            if not all([name, email, password]):
                st.error("❌ Všetky polia sú povinné!")
            elif email_error:
                st.error(f"❌ {email_error}")
            elif role == "manager" and not cities:
                st.error("❌ Pre manažéra musíte vybrať aspoň jedno mesto!")
            elif len(password) < 4:
                st.error("❌ Heslo musí mať aspoň 4 znaky!")
            else:
                try:
                    # Použijem validovaný email (s odstránenými medzerami)
                    success = user_db.add_user(validated_email, password, role, cities, name)
                    if success:
                        st.success(f"✅ Používateľ {name} bol úspešne pridaný!")
                        st.info(f"📧 Email: {validated_email}")
                        st.rerun()
                    else:
                        st.error("❌ Používateľ sa nepodarilo pridať - možno už existuje")
                except Exception as e:
                    st.error(f"❌ Chyba pri pridávaní používateľa: {e}")

def fix_database_emails(user_db):
    """Opraví problematické emaily s medzerami v databáze"""
    st.subheader("🔧 Oprava databázy")
    
    # Načítaj raw databázu pre kontrolu
    import json
    import os
    
    db_file = os.path.join(os.path.dirname(__file__), 'users.json')
    
    if not os.path.exists(db_file):
        st.error("❌ Databáza neexistuje")
        return
    
    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            raw_users = json.load(f)
        
        # Nájdi problematické emaily
        problematic_emails = []
        for email in raw_users.keys():
            if email.startswith(' ') or email.endswith(' ') or '  ' in email:
                problematic_emails.append(email)
        
        if not problematic_emails:
            st.success("✅ V databáze neboli nájdené problematické emaily")
            return
        
        st.warning(f"⚠️ Nájdené problematické emaily: {len(problematic_emails)}")
        
        for email in problematic_emails:
            st.code(f"Problém: '{email}' -> '{email.strip()}'")
        
        if st.button("🔧 Opraviť všetky problematické emaily", type="primary"):
            fixed_users = {}
            
            for email, user_data in raw_users.items():
                clean_email = email.strip()
                fixed_users[clean_email] = user_data
            
            # Ulož opravenou databázu
            with open(db_file, 'w', encoding='utf-8') as f:
                json.dump(fixed_users, f, indent=2, ensure_ascii=False)
            
            st.success("✅ Databáza bola opravená!")
            st.info("🔄 Reštartujte aplikáciu pre aplikovanie zmien")
            
    except Exception as e:
        st.error(f"❌ Chyba pri oprave databázy: {e}")


def show_users_list(user_db):
    """Zoznam všetkých používateľov s možnosťou zobraziť heslá"""
    st.subheader("📋 Zoznam používateľov")
    
    # Pridaj nástroj na opravu databázy
    with st.expander("🔧 Nástroje pre opravu databázy"):
        fix_database_emails(user_db)
    
    st.divider()
    
    users = user_db.get_all_users()
    
    if not users:
        st.info("👤 Žiadni používatelia v systéme")
        return
    
    st.info(f"👥 Celkom používateľov: {len(users)}")
    
    # Session state pre správu zobrazenia hesiel
    if 'show_passwords' not in st.session_state:
        st.session_state.show_passwords = {}
    if 'verification_mode' not in st.session_state:
        st.session_state.verification_mode = {}
    
    # Zoznam používateľov
    for user in users:
        user_email = user['email']
        password_key = f"password_{user_email}"
        
        # Ak je v režime reset hesla pre tohto používateľa
        reset_key = f"reset_{user_email}"
        if st.session_state.verification_mode.get(reset_key, False):
            show_password_reset_form(user, reset_key, user_db)
            continue
        
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            
            with col1:
                role_icon = "👑" if user['role'] == 'admin' else "👔"
                st.markdown(f"**{role_icon} {user['name']}**")
                st.markdown(f"📧 {user['email']}")
                
                # Info o hesle - bez zobrazenia plain textu
                st.caption("🔐 Heslo je zabezpečené (hash)")
            
            with col2:
                if user['role'] == 'admin':
                    st.markdown("🌍 **Prístup**: Všetky mestá")
                else:
                    cities_text = ", ".join([c.title() for c in user['cities']])
                    st.markdown(f"🏙️ **Mestá**: {cities_text}")
            
            with col3:
                # Tlačidlo na reset hesla
                if st.button("� Reset hesla", key=f"reset_pass_{user_email}", help="Resetovať heslo používateľa"):
                    st.session_state.verification_mode[f"reset_{user_email}"] = True
                    st.rerun()
            
            with col4:
                if user['email'] != "pvarhalik@sykora.eu":  # Nemôže zmazať seba
                    if st.button("🗑️", key=f"delete_{user_email}", help="Zmazať používateľa"):
                        if user_db.remove_user(user['email']):
                            st.success(f"✅ Používateľ {user['name']} bol zmazaný!")
                            st.rerun()
                        else:
                            st.error("❌ Chyba pri mazaní používateľa")
        
        st.markdown("---")

def show_admin_change_password(user_db):
    """Zobrazí formulár pre zmenu admin hesla"""
    st.subheader("🔑 Zmena admin hesla")
    
    current_user = get_current_user()
    if not current_user or current_user.get('role') != 'admin':
        st.error("❌ Iba admin môže meniť heslo")
        return
    
    st.info(f"👤 Meniate heslo pre: **{current_user['name']}** ({current_user['email']})")
    
    with st.form("admin_change_password_form", clear_on_submit=True):
        st.markdown("### 🔐 Zadajte údaje pre zmenu hesla")
        
        col1, col2 = st.columns(2)
        
        with col1:
            old_password = st.text_input(
                "🔑 Súčasné heslo:", 
                type="password",
                help="Zadajte vaše aktuálne heslo"
            )
            
        with col2:
            new_password = st.text_input(
                "🆕 Nové heslo:", 
                type="password",
                help="Zadajte nové heslo (min. 4 znaky)"
            )
        
        confirm_password = st.text_input(
            "✅ Potvrdiť nové heslo:", 
            type="password",
            help="Zadajte nové heslo znovu pre potvrdenie"
        )
        
        st.markdown("---")
        
        col_submit1, col_submit2, col_submit3 = st.columns([1, 1, 2])
        
        with col_submit1:
            submit_button = st.form_submit_button("🔄 Zmeniť heslo", type="primary", use_container_width=True)
        
        with col_submit2:
            clear_button = st.form_submit_button("🗑️ Vyčistiť", use_container_width=True)
        
        # Spracovanie formuláru
        if submit_button:
            if not old_password:
                st.error("⚠️ Zadajte súčasné heslo!")
            elif not new_password:
                st.error("⚠️ Zadajte nové heslo!")
            elif not confirm_password:
                st.error("⚠️ Potvrďte nové heslo!")
            elif new_password != confirm_password:
                st.error("❌ Nové heslá sa nezhodujú!")
            elif len(new_password) < 4:
                st.error("⚠️ Nové heslo musí mať aspoň 4 znaky!")
            elif old_password == new_password:
                st.error("⚠️ Nové heslo musí byť iné ako súčasné!")
            else:
                # Pokus o zmenu hesla
                success = user_db.change_own_password(
                    current_user['email'], 
                    old_password, 
                    new_password
                )
                
                if success:
                    st.success("✅ **Heslo bolo úspešne zmenené!**")
                    st.info("🔒 Pri ďalšom prihlásení použite nové heslo")
                    
                    # Voliteľné: automatické odhlásenie po zmene hesla
                    if st.button("🚪 Odhlásiť sa teraz", type="secondary"):
                        st.session_state.authenticated_user = None
                        st.rerun()
                        
                else:
                    st.error("❌ **Nesprávne súčasné heslo!**")
                    st.warning("🔍 Skontrolujte, či ste zadali správne súčasné heslo")
        
        elif clear_button:
            st.info("🗑️ Formulár bol vyčistený")
    
    # Bezpečnostné upozornenia
    st.markdown("---")
    st.markdown("### 🛡️ Bezpečnostné odporúčania")
    
    col_tips1, col_tips2 = st.columns(2)
    
    with col_tips1:
        st.markdown("""
        **🔐 Silné heslo obsahuje:**
        - Aspoň 8 znakov
        - Veľké a malé písmená
        - Čísla a špeciálne znaky
        - Nie je slovníkové slovo
        """)
    
    with col_tips2:
        st.markdown("""
        **⚠️ Bezpečnostné pravidlá:**
        - Nikdy nezdieľajte heslo
        - Nepoužívajte rovnaké heslo
        - Pravidelne meňte heslo
        - Používajte password manager
        """)

def show_password_reset_form(user, reset_key, user_db):
    """Zobrazí formulár pre reset hesla používateľa"""
    
    st.markdown("---")
    st.warning(f"🔄 **Reset hesla** pre používateľa: **{user['name']}**")
    
    with st.form(f"reset_password_{user['email']}", clear_on_submit=True):
        st.markdown("**Zadajte nové heslo pre používateľa:**")
        
        col_pass1, col_pass2 = st.columns(2)
        
        with col_pass1:
            new_password = st.text_input(
                "🔑 Nové heslo:", 
                type="password",
                help="Zadajte nové heslo pre používateľa"
            )
        
        with col_pass2:
            confirm_password = st.text_input(
                "🔑 Potvrďte heslo:", 
                type="password",
                help="Zadajte heslo znovu pre potvrdenie"
            )
        
        # Admin overenie
        st.markdown("**Zadajte svoje admin heslo pre potvrdenie:**")
        admin_password = st.text_input(
            "🔑 Admin heslo:", 
            type="password",
            help="Zadajte heslo aktuálne prihláseného admin účtu"
        )
        
        col_reset1, col_reset2 = st.columns(2)
        
        with col_reset1:
            reset_submitted = st.form_submit_button("✅ Resetovať heslo", type="primary")
        
        with col_reset2:
            cancel_submitted = st.form_submit_button("❌ Zrušiť")
        
        # Spracovanie formuláru
        if reset_submitted:
            if not new_password or not confirm_password or not admin_password:
                st.error("⚠️ Vyplňte všetky polia!")
            elif new_password != confirm_password:
                st.error("❌ Heslá sa nezhodujú!")
            elif len(new_password) < 4:
                st.error("⚠️ Heslo musí mať aspoň 4 znaky!")
            else:
                # Overenie admin hesla
                current_user = st.session_state.get('authenticated_user')
                if current_user and user_db.authenticate(current_user['email'], admin_password):
                    # Reset hesla
                    if user_db.reset_user_password(user['email'], new_password):
                        st.session_state.verification_mode[reset_key] = False
                        st.success(f"✅ Heslo pre {user['name']} bolo úspešne resetované!")
                        st.info(f"🔐 **Nové heslo**: `{new_password}`")
                        st.caption("⚠️ Nezabudnite oznámiť používateľovi nové heslo!")
                        st.rerun()
                    else:
                        st.error("❌ Chyba pri resetovaní hesla!")
                else:
                    st.error("❌ Nesprávne admin heslo!")
        
        elif cancel_submitted:
            st.session_state.verification_mode[reset_key] = False
            st.info("🚫 Reset hesla zrušený")
            st.rerun()
    
    st.markdown("---")

def show_feature_management(user_db):
    """Správa funkcií používateľov"""
    st.subheader("🎛️ Správa funkcií")
    
    users = user_db.get_all_users()
    available_features = user_db.get_available_features()
    
    if not users:
        st.info("👤 Žiadni používatelia v systéme")
        return
    
    # Výber používateľa
    selected_user_email = st.selectbox(
        "👤 Vyberte používateľa:",
        options=[u['email'] for u in users],
        format_func=lambda email: next(u['name'] + f" ({u['role']})" for u in users if u['email'] == email)
    )
    
    if not selected_user_email:
        return
    
    selected_user = next(u for u in users if u['email'] == selected_user_email)
    current_features = user_db.get_user_features(selected_user_email)
    
    st.markdown(f"### 🔧 Funkcie pre: **{selected_user['name']}**")
    
    # Ak je admin, má všetky funkcie
    if selected_user['role'] == 'admin':
        st.info("👑 **Administrátori majú automaticky prístup ku všetkým funkciám**")
        return
    
    # Konfigurácia funkcií
    updated_features = {}
    
    for feature_key, feature_name in available_features.items():
        current_value = current_features.get(feature_key, False)
        new_value = st.checkbox(
            f"**{feature_name}**",
            value=current_value,
            key=f"feature_{feature_key}_{selected_user_email}"
        )
        updated_features[feature_key] = new_value
    
    if st.button("💾 Uložiť zmeny", type="primary"):
        if user_db.update_user_features(selected_user_email, updated_features):
            st.success("✅ Funkcie boli úspešne aktualizované!")
            st.rerun()
        else:
            st.error("❌ Chyba pri aktualizácii funkcií")

def show_data_management():
    """Správa dátových súborov s pokročilými funkciami"""
    st.subheader("📁 Pokročilá správa dát")
    
    # Základné priečinky
    data_folders = {
        "📊 Excel súbory (Predajné dáta)": "data/raw",
        "🏢 Studio dáta": "data/studio"
    }
    
    # Vyber priečinka
    selected_folder_name = st.selectbox("📂 Vyberte kategóriu súborov:", list(data_folders.keys()))
    selected_folder = data_folders[selected_folder_name]
    
    # Vytvor priečinok ak neexistuje
    Path(selected_folder).mkdir(parents=True, exist_ok=True)
    
    # Layout s rozšírenými funkciami
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 📋 Súbory s pokročilými operáciami")
        show_advanced_file_list(selected_folder)
    
    with col2:
        st.markdown("### 🛠️ Nástroje")
        show_file_management_tools(selected_folder)

def show_advanced_file_list(folder_path):
    """Zobrazí súbory s pokročilými možnosťami správy"""
    try:
        folder = Path(folder_path)
        if not folder.exists():
            st.info(f"📁 Priečinok `{folder_path}` neexistuje")
            return
        
        files = list(folder.glob("*.xlsx")) + list(folder.glob("*.xls")) + list(folder.glob("*.csv"))
        
        if not files:
            st.info("📄 Žiadne dátové súbory v priečinku")
            return
        
        st.info(f"📊 Nájdených **{len(files)}** súborov")
        
        # Rozšírená tabuľka súborov
        file_data = []
        for file_path in sorted(files):
            stat = file_path.stat()
            file_data.append({
                "📄 Súbor": file_path.name,
                "📅 Vytvorený": datetime.fromtimestamp(stat.st_ctime).strftime("%d.%m.%Y %H:%M"),
                "📝 Upravený": datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M"),
                "💾 Veľkosť": format_file_size(stat.st_size),
                "🔧 Typ": file_path.suffix.upper(),
                "📁 Cesta": str(file_path)
            })
        
        if file_data:
            df = pd.DataFrame(file_data)
            st.dataframe(df[["📄 Súbor", "📝 Upravený", "💾 Veľkosť", "🔧 Typ"]], width='stretch', hide_index=True)
            
            # Pokročilé operácie so súbormi
            st.markdown("---")
            st.markdown("#### 🔧 Pokročilé operácie")
            
            # Multi-select pre hromadné operácie
            selected_files = st.multiselect(
                "Vyberte súbory pre hromadné operácie:",
                options=[f["📄 Súbor"] for f in file_data],
                help="Držte Ctrl pre výber viacerých súborov"
            )
            
            if selected_files:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("👁️ Náhľad vybraných", key="preview_selected"):
                        show_multiple_file_preview(folder, selected_files)
                
                with col2:
                    if st.button("📥 Stiahnuť ZIP", key="download_zip"):
                        create_zip_download(folder, selected_files)
                
                with col3:
                    if st.button("📋 Kopírovať", key="copy_files"):
                        show_copy_dialog(folder, selected_files)
                
                with col4:
                    if st.button("🗑️ Zmazať vybrané", key="delete_selected", type="secondary"):
                        delete_multiple_files(folder, selected_files)
            
            # Jednotlivé súbory - detailné operácie
            st.markdown("---")
            st.markdown("#### 📄 Detailné operácie so súborom")
            
            selected_file = st.selectbox("Vyberte súbor pre detailné operácie:", [f["📄 Súbor"] for f in file_data])
            
            if selected_file:
                selected_path = folder / selected_file
                show_single_file_operations(selected_path, file_data)
                            
    except Exception as e:
        st.error(f"❌ Chyba pri čítaní priečinka: {e}")

def show_single_file_operations(file_path, file_data):
    """Zobrazí detailné operácie pre jeden súbor"""
    # Informácie o súbore
    file_info = next(f for f in file_data if f["📄 Súbor"] == file_path.name)
    
    with st.expander(f"📊 Informácie o súbore: {file_path.name}", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**📁 Cesta**: `{file_path}`")
            st.write(f"**💾 Veľkosť**: {file_info['💾 Veľkosť']}")
            st.write(f"**🔧 Typ**: {file_info['🔧 Typ']}")
        with col2:
            st.write(f"**📅 Vytvorený**: {file_info['📅 Vytvorený']}")
            st.write(f"**📝 Upravený**: {file_info['📝 Upravený']}")
    
    # Operácie
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("👁️ Náhľad", key=f"preview_{file_path.name}"):
            show_file_preview(file_path)
    
    with col2:
        if st.button("📥 Stiahnuť", key=f"download_{file_path.name}"):
            with open(file_path, "rb") as file:
                st.download_button(
                    label="💾 Kliknite pre stiahnutie",
                    data=file.read(),
                    file_name=file_path.name,
                    mime=get_mime_type(file_path)
                )
    
    with col3:
        if st.button("✏️ Premenovať", key=f"rename_{file_path.name}"):
            show_rename_dialog(file_path)
    
    with col4:
        if st.button("📋 Kopírovať", key=f"copy_{file_path.name}"):
            show_copy_single_dialog(file_path)
    
    with col5:
        if st.button("🗑️ Zmazať", key=f"delete_{file_path.name}", type="secondary"):
            delete_single_file(file_path)

def show_file_management_tools(folder_path):
    """Zobrazí nástroje pre správu súborov"""
    
    # Upload súborov
    st.markdown("### ⬆️ Upload súborov")
    uploaded_files = st.file_uploader(
        "Vyberte súbory:",
        type=['xlsx', 'xls', 'csv'],
        accept_multiple_files=True,
        help="Drag & drop alebo browse súbory"
    )
    
    if uploaded_files:
        st.write(f"📤 **{len(uploaded_files)} súborov na upload**")
        
        # Možnosti uploadu
        overwrite = st.checkbox("🔄 Prepísať existujúce súbory", value=False)
        create_backup = st.checkbox("💾 Vytvoriť zálohu", value=True)
        
        if st.button("⬆️ Uložiť súbory", type="primary"):
            upload_files_with_options(folder_path, uploaded_files, overwrite, create_backup)
    
    # Štatistiky priečinka
    st.markdown("---")
    st.markdown("### 📊 Štatistiky priečinka")
    show_folder_statistics(folder_path)
    
    # Údržba priečinka
    st.markdown("---")
    st.markdown("### 🧹 Údržba")
    
    if st.button("💾 Záloha celého priečinka"):
        create_folder_backup(folder_path)
    
    if st.button("🧹 Vyčistiť zálohy", help="Zmaže súbory s .backup_"):
        clean_backup_files(folder_path)
    
    if st.button("📊 Analýza duplicitov"):
        analyze_duplicates(folder_path)
    
    # Pokročilé nástroje
    st.markdown("---")
    st.markdown("### 🛠️ Pokročilé nástroje")
    
    if st.button("📈 Analýza štruktúry Excel súborov"):
        analyze_excel_structure(folder_path)
    
    if st.button("🔍 Hľadanie v súboroch"):
        show_search_dialog(folder_path)

def show_multiple_file_preview(folder, selected_files):
    """Zobrazí náhľad viacerých súborov"""
    st.markdown("#### 👁️ Náhľad vybraných súborov")
    
    for filename in selected_files[:3]:  # Max 3 súbory
        file_path = folder / filename
        with st.expander(f"📄 {filename}", expanded=False):
            show_file_preview(file_path)
    
    if len(selected_files) > 3:
        st.info(f"📄 Zobrazených prvých 3 z {len(selected_files)} súborov")

def create_zip_download(folder, selected_files):
    """Vytvorí ZIP súbor pre stiahnutie"""
    import zipfile
    import io
    
    try:
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename in selected_files:
                file_path = folder / filename
                if file_path.exists():
                    zip_file.write(file_path, filename)
        
        zip_buffer.seek(0)
        
        st.download_button(
            label="📥 Stiahnuť ZIP súbor",
            data=zip_buffer.getvalue(),
            file_name=f"selected_files_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip"
        )
        
    except Exception as e:
        st.error(f"❌ Chyba pri vytváraní ZIP: {e}")

def delete_multiple_files(folder, selected_files):
    """Zmaže viacero súborov"""
    if st.session_state.get('confirm_delete_multiple', False):
        try:
            deleted_count = 0
            for filename in selected_files:
                file_path = folder / filename
                if file_path.exists():
                    file_path.unlink()
                    deleted_count += 1
            
            st.success(f"✅ Zmazaných {deleted_count} súborov")
            st.session_state['confirm_delete_multiple'] = False
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Chyba pri mazaní: {e}")
    else:
        st.session_state['confirm_delete_multiple'] = True
        st.warning(f"⚠️ Naozaj chcete zmazať {len(selected_files)} súborov? Kliknite znovu pre potvrdenie.")

def delete_single_file(file_path):
    """Zmaže jeden súbor"""
    confirm_key = f'confirm_delete_{file_path.name}'
    
    if st.session_state.get(confirm_key, False):
        try:
            file_path.unlink()
            st.success(f"✅ Súbor `{file_path.name}` bol zmazaný")
            st.session_state[confirm_key] = False
            st.rerun()
        except Exception as e:
            st.error(f"❌ Chyba pri mazaní: {e}")
    else:
        st.session_state[confirm_key] = True
        st.warning("⚠️ Kliknite znovu pre potvrdenie zmazania")

def show_rename_dialog(file_path):
    """Zobrazí dialóg pre premenovanie súboru"""
    with st.form(f"rename_form_{file_path.name}"):
        current_name = file_path.stem
        current_ext = file_path.suffix
        
        new_name = st.text_input("📝 Nové meno súboru (bez prípony):", value=current_name)
        
        if st.form_submit_button("✏️ Premenovať"):
            if new_name and new_name != current_name:
                try:
                    new_path = file_path.parent / f"{new_name}{current_ext}"
                    file_path.rename(new_path)
                    st.success(f"✅ Súbor premenovaný na `{new_name}{current_ext}`")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Chyba pri premenovaní: {e}")
            else:
                st.warning("⚠️ Zadajte nové meno súboru")

def upload_files_with_options(folder_path, uploaded_files, overwrite, create_backup):
    """Upload súborov s možnosťami"""
    success_count = 0
    error_count = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, uploaded_file in enumerate(uploaded_files):
        try:
            progress = (i + 1) / len(uploaded_files)
            progress_bar.progress(progress)
            status_text.text(f"Uploadujem {uploaded_file.name}...")
            
            file_path = Path(folder_path) / uploaded_file.name
            
            # Kontrola existencie súboru
            if file_path.exists():
                if not overwrite:
                    st.warning(f"⚠️ Súbor {uploaded_file.name} už existuje - preskakujem")
                    continue
                
                if create_backup:
                    backup_path = Path(folder_path) / f"{uploaded_file.name}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(file_path, backup_path)
                    st.info(f"📋 Vytvorená záloha: `{backup_path.name}`")
            
            # Zápis nového súboru
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            success_count += 1
            
        except Exception as e:
            st.error(f"❌ Chyba pri uložení {uploaded_file.name}: {e}")
            error_count += 1
    
    progress_bar.progress(1.0)
    status_text.text("✅ Upload dokončený!")
    
    if success_count > 0:
        st.success(f"✅ Úspešne uložených: {success_count} súborov")
    if error_count > 0:
        st.error(f"❌ Chyby pri ukladaní: {error_count} súborov")
    
    if success_count > 0:
        st.rerun()

def show_folder_statistics(folder_path):
    """Zobrazí štatistiky priečinka"""
    try:
        folder = Path(folder_path)
        if not folder.exists():
            st.info("📁 Priečinok neexistuje")
            return
        
        files = list(folder.glob("*.*"))
        data_files = list(folder.glob("*.xlsx")) + list(folder.glob("*.xls")) + list(folder.glob("*.csv"))
        backup_files = list(folder.glob("*.backup_*"))
        
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        
        # Štatistiky podľa typov
        file_types = {}
        for f in data_files:
            ext = f.suffix.lower()
            file_types[ext] = file_types.get(ext, 0) + 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("📄 Celkom súborov", len(files))
            st.metric("📊 Dátové súbory", len(data_files))
            st.metric("💾 Celková veľkosť", format_file_size(total_size))
        
        with col2:
            st.metric("📋 Zálohy", len(backup_files))
            if file_types:
                st.write("**📊 Typy súborov:**")
                for ext, count in file_types.items():
                    st.write(f"• {ext.upper()}: {count}")
                    
    except Exception as e:
        st.error(f"❌ Chyba pri získavaní štatistík: {e}")

def create_folder_backup(folder_path):
    """Vytvorí zálohu celého priečinka"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_folder = f"{folder_path}_backup_{timestamp}"
        
        if Path(folder_path).exists():
            shutil.copytree(folder_path, backup_folder)
            st.success(f"✅ Záloha vytvorená: `{backup_folder}`")
        else:
            st.warning("⚠️ Priečinok neexistuje")
            
    except Exception as e:
        st.error(f"❌ Chyba pri vytváraní zálohy: {e}")

def clean_backup_files(folder_path):
    """Vyčistí záložné súbory"""
    try:
        folder = Path(folder_path)
        backup_files = list(folder.glob("*.backup_*"))
        
        if backup_files:
            for backup_file in backup_files:
                backup_file.unlink()
            st.success(f"✅ Vyčistených {len(backup_files)} záložných súborov")
        else:
            st.info("📄 Žiadne záložné súbory na vyčistenie")
            
    except Exception as e:
        st.error(f"❌ Chyba pri čistení záloh: {e}")

def analyze_duplicates(folder_path):
    """Analyzuje duplicitné súbory"""
    try:
        folder = Path(folder_path)
        files = list(folder.glob("*.xlsx")) + list(folder.glob("*.xls")) + list(folder.glob("*.csv"))
        
        # Analýza podľa mena a veľkosti
        file_groups = {}
        for f in files:
            key = (f.stem.lower(), f.stat().st_size)  # Meno bez prípony + veľkosť
            if key not in file_groups:
                file_groups[key] = []
            file_groups[key].append(f.name)
        
        duplicates = {k: v for k, v in file_groups.items() if len(v) > 1}
        
        if duplicates:
            st.warning(f"⚠️ Nájdených {len(duplicates)} skupín možných duplicitov:")
            for (name, size), files_list in duplicates.items():
                st.write(f"**{name}** ({format_file_size(size)}): {', '.join(files_list)}")
        else:
            st.success("✅ Žiadne duplicitné súbory nenájdené")
            
    except Exception as e:
        st.error(f"❌ Chyba pri analýze duplicitov: {e}")

def get_mime_type(file_path):
    """Získa MIME typ súboru"""
    ext = file_path.suffix.lower()
    mime_types = {
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.xls': 'application/vnd.ms-excel',
        '.csv': 'text/csv'
    }
    return mime_types.get(ext, 'application/octet-stream')

def show_file_preview(file_path):
    """Zobrazí náhľad súboru s rozšírenými informáciami"""
    try:
        st.markdown(f"#### 👁️ Náhľad súboru: `{file_path.name}`")
        
        if file_path.suffix.lower() in ['.xlsx', '.xls']:
            # Excel súbory
            try:
                # Získanie informácií o hároch
                excel_file = pd.ExcelFile(file_path)
                sheet_names = excel_file.sheet_names
                
                st.markdown(f"**📊 Excel súbor s {len(sheet_names)} hármi**: {', '.join(sheet_names)}")
                
                # Výber háru pre náhľad
                if len(sheet_names) > 1:
                    selected_sheet = st.selectbox("Vyberte hár:", sheet_names, key=f"sheet_{file_path.name}")
                else:
                    selected_sheet = sheet_names[0]
                
                df = pd.read_excel(file_path, sheet_name=selected_sheet, nrows=100)
                st.markdown(f"**📊 Rozmer ({selected_sheet})**: {df.shape[0]} riadkov × {df.shape[1]} stĺpcov")
                st.markdown("**📋 Prvých 10 riadkov:**")
                st.dataframe(df.head(10), width='stretch')
                
                if df.shape[0] > 10:
                    st.info(f"📄 Zobrazených prvých 10 z {df.shape[0]} riadkov")
                
                # Štatistiky stĺpcov
                with st.expander("📊 Štatistiky stĺpcov", expanded=False):
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    if len(numeric_cols) > 0:
                        st.dataframe(df[numeric_cols].describe(), width='stretch')
                    else:
                        st.info("Žiadne numerické stĺpce na analýzu")
                        
            except Exception as e:
                st.error(f"❌ Chyba pri čítaní Excel súboru: {e}")
                
        elif file_path.suffix.lower() == '.csv':
            # CSV súbory
            try:
                df = pd.read_csv(file_path, nrows=100, encoding='utf-8')
                st.markdown(f"**📊 Rozmer**: {df.shape[0]} riadkov × {df.shape[1]} stĺpcov")
                st.markdown("**📋 Prvých 10 riadkov:**")
                st.dataframe(df.head(10), width='stretch')
                
                if df.shape[0] > 10:
                    st.info(f"📄 Zobrazených prvých 10 z {df.shape[0]} riadkov")
                
                # Info o encoding
                st.info("🔤 Encoding: UTF-8")
                    
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(file_path, nrows=100, encoding='cp1250')
                    st.markdown(f"**📊 Rozmer**: {df.shape[0]} riadkov × {df.shape[1]} stĺpcov")
                    st.dataframe(df.head(10), width='stretch')
                    st.info("🔤 Encoding: CP1250")
                except Exception as e:
                    st.error(f"❌ Chyba pri čítaní CSV súboru: {e}")
            except Exception as e:
                st.error(f"❌ Chyba pri čítaní CSV súboru: {e}")
        
        else:
            st.warning("⚠️ Náhľad nie je podporovaný pre tento typ súboru")
            
    except Exception as e:
        st.error(f"❌ Chyba pri zobrazovaní náhľadu: {e}")

def show_copy_dialog(folder, selected_files):
    """Zobrazí dialóg pre kopírovanie súborov"""
    with st.form("copy_multiple_form"):
        st.write(f"📋 Kopírovanie {len(selected_files)} súborov")
        
        target_folder = st.selectbox(
            "Cieľový priečinok:",
            options=["data/raw", "data/studio", "data/backup"],
            help="Vyberte kam chcete súbory skopírovať"
        )
        
        if st.form_submit_button("📋 Kopírovať"):
            try:
                Path(target_folder).mkdir(parents=True, exist_ok=True)
                copied_count = 0
                
                for filename in selected_files:
                    source_path = folder / filename
                    target_path = Path(target_folder) / filename
                    
                    if source_path.exists():
                        shutil.copy2(source_path, target_path)
                        copied_count += 1
                
                st.success(f"✅ Skopírovaných {copied_count} súborov do `{target_folder}`")
                
            except Exception as e:
                st.error(f"❌ Chyba pri kopírovaní: {e}")

def show_copy_single_dialog(file_path):
    """Zobrazí dialóg pre kopírovanie jedného súboru"""
    with st.form(f"copy_single_form_{file_path.name}"):
        st.write(f"📋 Kopírovanie súboru `{file_path.name}`")
        
        target_folder = st.selectbox(
            "Cieľový priečinok:",
            options=["data/raw", "data/studio", "data/backup"],
            key=f"target_{file_path.name}"
        )
        
        new_name = st.text_input(
            "Nové meno (voliteľne):",
            value=file_path.name,
            key=f"newname_{file_path.name}"
        )
        
        if st.form_submit_button("📋 Kopírovať"):
            try:
                Path(target_folder).mkdir(parents=True, exist_ok=True)
                target_path = Path(target_folder) / new_name
                
                shutil.copy2(file_path, target_path)
                st.success(f"✅ Súbor skopírovaný ako `{target_path}`")
                
            except Exception as e:
                st.error(f"❌ Chyba pri kopírovaní: {e}")

def analyze_excel_structure(folder_path):
    """Analyzuje štruktúru Excel súborov"""
    try:
        folder = Path(folder_path)
        excel_files = list(folder.glob("*.xlsx")) + list(folder.glob("*.xls"))
        
        if not excel_files:
            st.info("📄 Žiadne Excel súbory na analýzu")
            return
        
        st.markdown("#### 📈 Analýza štruktúry Excel súborov")
        
        analysis_data = []
        
        for excel_file in excel_files[:10]:  # Max 10 súborov
            try:
                excel_data = pd.ExcelFile(excel_file)
                
                for sheet_name in excel_data.sheet_names:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=1)
                    
                    analysis_data.append({
                        "📄 Súbor": excel_file.name,
                        "📊 Hár": sheet_name,
                        "📈 Stĺpce": len(df.columns),
                        "📋 Názvy stĺpcov": ", ".join(df.columns.astype(str)[:5]) + ("..." if len(df.columns) > 5 else "")
                    })
                    
            except Exception as e:
                analysis_data.append({
                    "📄 Súbor": excel_file.name,
                    "📊 Hár": "ERROR",
                    "📈 Stĺpce": 0,
                    "📋 Názvy stĺpcov": str(e)
                })
        
        if analysis_data:
            df_analysis = pd.DataFrame(analysis_data)
            st.dataframe(df_analysis, width='stretch', hide_index=True)
        
    except Exception as e:
        st.error(f"❌ Chyba pri analýze štruktúry: {e}")

def show_search_dialog(folder_path):
    """Zobrazí dialóg pre hľadanie v súboroch"""
    st.markdown("#### 🔍 Hľadanie v súboroch")
    
    with st.form("search_form"):
        search_term = st.text_input("🔎 Hľadať text:", help="Zadajte text na hľadanie v súboroch")
        
        search_options = st.multiselect(
            "Možnosti hľadania:",
            options=["Case sensitive", "Celé slová", "Regulárne výrazy"],
            default=[]
        )
        
        if st.form_submit_button("🔍 Hľadať"):
            if search_term:
                search_in_files(folder_path, search_term, search_options)
            else:
                st.warning("⚠️ Zadajte text na hľadanie")

def search_in_files(folder_path, search_term, options):
    """Hľadá text v súboroch"""
    try:
        folder = Path(folder_path)
        files = list(folder.glob("*.xlsx")) + list(folder.glob("*.xls")) + list(folder.glob("*.csv"))
        
        results = []
        
        for file_path in files[:20]:  # Max 20 súborov
            try:
                if file_path.suffix.lower() == '.csv':
                    # CSV súbory
                    df = pd.read_csv(file_path, nrows=1000)
                else:
                    # Excel súbory
                    df = pd.read_excel(file_path, nrows=1000)
                
                # Hľadanie v DataFrame
                mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
                matches = df[mask]
                
                if not matches.empty:
                    results.append({
                        "📄 Súbor": file_path.name,
                        "🔍 Nájdené": len(matches),
                        "📊 Prvý výskyt": str(matches.iloc[0].to_dict())[:100] + "..."
                    })
                
            except Exception as e:
                results.append({
                    "📄 Súbor": file_path.name,
                    "🔍 Nájdené": 0,
                    "📊 Prvý výskyt": f"Chyba: {e}"
                })
        
        if results:
            st.markdown(f"#### 🎯 Výsledky hľadania pre: '{search_term}'")
            df_results = pd.DataFrame(results)
            st.dataframe(df_results, width='stretch', hide_index=True)
        else:
            st.info("🔍 Žiadne výsledky nenájdené")
            
    except Exception as e:
        st.error(f"❌ Chyba pri hľadaní: {e}")

def format_file_size(bytes_size):
    """Formátovanie veľkosti súboru"""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.1f} GB"


def show_server_monitoring_tab():
    """Zobrazí server monitoring stále s auto-refresh každých 10 sekúnd"""
    
    st.subheader("🖥️ Server Monitoring - Live Dashboard")
    
    # Container pre live údaje
    monitoring_container = st.empty()
    
    # Auto-refresh pomocou JavaScript - skutočný auto-refresh
    refresh_interval = 10  # sekúnd
    
    # JavaScript pre automatický refresh
    st.markdown(f"""
    <script>
    // Auto-refresh každých {refresh_interval} sekúnd
    setTimeout(function() {{
        window.location.reload();
    }}, {refresh_interval * 1000});
    
    // Zobrazenie odpočítavania
    var countdown = {refresh_interval};
    var timer = setInterval(function() {{
        countdown--;
        if (countdown <= 0) {{
            clearInterval(timer);
        }}
    }}, 1000);
    </script>
    """, unsafe_allow_html=True)
    
    # Auto-refresh info s tlačidlom
    current_time_str = datetime.now().strftime("%H:%M:%S")
    col_info, col_btn = st.columns([3, 1])
    with col_info:
        st.info(f"🔄 Auto-refresh každých {refresh_interval}s | Posledný: {current_time_str}")
    with col_btn:
        if st.button("🔄 Refresh teraz", key="manual_refresh_btn"):
            st.rerun()
    
    with monitoring_container.container():
        monitor = get_server_monitor()
        
        # Spustenie monitoringu ak nie je aktívny
        if not monitor.monitoring:
            st.warning("⚠️ Monitoring nie je aktívny. Spúšťam...")
            monitor.start_monitoring(interval_seconds=30)
        
        try:
            # Získanie aktuálnych metrík a historických dát
            metrics = monitor.get_current_metrics()
            historical_data = monitor.get_historical_metrics(24)
            
            if "error" in metrics:
                st.error(f"❌ Chyba pri načítavaní metrík: {metrics.get('error', 'Neznáma chyba')}")
                return
            
            # Výpočet zmien za 24 hodín
            changes_24h = calculate_24h_changes(metrics, historical_data)
            
            # Hlavné metriky s delta za 24h
            st.markdown("### 📊 Aktuálny stav systému (zmeny za 24h)")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                cpu_percent = metrics['cpu']['usage_percent']
                cpu_delta = changes_24h.get('cpu_change', 0)
                st.metric(
                    label="🖥️ CPU Usage", 
                    value=f"{cpu_percent:.1f}%",
                    delta=f"{cpu_delta:+.1f}% (24h)" if abs(cpu_delta) > 0.1 else "Stabilné (24h)"
                )
            
            with col2:
                memory_percent = metrics['memory']['usage_percent']
                memory_delta = changes_24h.get('memory_change', 0)
                st.metric(
                    label="🧠 Memory Usage", 
                    value=f"{memory_percent:.1f}%",
                    delta=f"{memory_delta:+.1f}% (24h)" if abs(memory_delta) > 0.1 else "Stabilné (24h)"
                )
            
            with col3:
                disk_percent = metrics['disk']['usage_percent']
                disk_delta = changes_24h.get('disk_change', 0)
                st.metric(
                    label="� Disk Usage", 
                    value=f"{disk_percent:.1f}%",
                    delta=f"{disk_delta:+.1f}% (24h)" if abs(disk_delta) > 0.1 else "Stabilné (24h)"
                )
                
            with col4:
                # Network activity
                network_total = (metrics['network']['bytes_sent'] + metrics['network']['bytes_recv']) / (1024**2)
                network_delta = changes_24h.get('network_change_mb', 0)
                st.metric(
                    label="🌐 Network Total", 
                    value=f"{network_total:.1f} MB",
                    delta=f"{network_delta:+.1f} MB (24h)" if abs(network_delta) > 1 else "Stabilné (24h)"
                )
            
            # Progress bars
            st.markdown("### 📈 Využitie zdrojov")
            col_p1, col_p2, col_p3 = st.columns(3)
            
            with col_p1:
                st.progress(min(cpu_percent / 100, 1.0), text=f"CPU: {cpu_percent:.1f}%")
            
            with col_p2:
                st.progress(min(memory_percent / 100, 1.0), text=f"RAM: {memory_percent:.1f}%")
            
            with col_p3:
                st.progress(min(disk_percent / 100, 1.0), text=f"Disk: {disk_percent:.1f}%")
            
            # Rozšírené štatistiky za 24h
            st.markdown("### 📈 Rozšírené štatistiky (24h zmeny)")
            col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
            
            with col_stats1:
                app_size_mb = get_directory_size(".") / (1024**2)
                app_size_delta = changes_24h.get('app_size_change_mb', 0)
                st.metric(
                    label="📦 Veľkosť aplikácie",
                    value=f"{app_size_mb:.1f} MB",
                    delta=f"{app_size_delta:+.1f} MB (24h)" if abs(app_size_delta) > 0.1 else "Stabilné (24h)"
                )
            
            with col_stats2:
                process_count = len(metrics.get('top_processes', []))
                process_delta = changes_24h.get('processes_change', 0)
                st.metric(
                    label="⚙️ Aktívne procesy",
                    value=f"{process_count}",
                    delta=f"{process_delta:+d} (24h)" if process_delta != 0 else "Stabilné (24h)"
                )
            
            with col_stats3:
                uptime_hours = changes_24h.get('uptime_hours', 0)
                uptime_days = uptime_hours / 24
                st.metric(
                    label="⏱️ System Uptime",
                    value=f"{uptime_days:.1f} dní",
                    delta=f"{uptime_hours:.1f} hodín celkom"
                )
            
            with col_stats4:
                # Free memory percentáž
                free_memory_percent = 100 - memory_percent
                st.metric(
                    label="🆓 Voľná RAM",
                    value=f"{free_memory_percent:.1f}%",
                    delta=f"{metrics['memory']['available_gb']:.1f} GB voľných"
                )
            
            # Detailné informácie
            with st.expander("� Detailné informácie", expanded=True):
                col_d1, col_d2 = st.columns(2)
                
                with col_d1:
                    st.markdown("**💾 Memory Details**")
                    memory_total_gb = metrics['memory']['total_gb']
                    memory_used_gb = metrics['memory']['used_gb']
                    memory_available_gb = metrics['memory']['available_gb']
                    
                    st.write(f"Total: {memory_total_gb:.1f} GB")
                    st.write(f"Used: {memory_used_gb:.1f} GB")
                    st.write(f"Available: {memory_available_gb:.1f} GB")
                    
                    st.markdown("**💽 Disk Details**")
                    disk_total_gb = metrics['disk']['total_gb']
                    disk_used_gb = metrics['disk']['used_gb']
                    disk_free_gb = metrics['disk']['free_gb']
                    
                    st.write(f"Total: {disk_total_gb:.1f} GB")
                    st.write(f"Used: {disk_used_gb:.1f} GB")
                    st.write(f"Free: {disk_free_gb:.1f} GB")
                
                with col_d2:
                    st.markdown("**🌐 Network Details**")
                    bytes_sent_mb = metrics['network']['bytes_sent'] / (1024**2)
                    bytes_recv_mb = metrics['network']['bytes_recv'] / (1024**2)
                    
                    st.write(f"Bytes sent: {bytes_sent_mb:.1f} MB")
                    st.write(f"Bytes received: {bytes_recv_mb:.1f} MB")
                    
                    st.markdown("**⚙️ System Info**")
                    st.write(f"CPU cores: {metrics['cpu']['count']}")
                    st.write(f"CPU frequency: {metrics['cpu']['frequency_mhz']:.0f} MHz")
                    boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
                    st.write(f"Boot time: {boot_time}")
            
            # Top processes
            if 'top_processes' in metrics and metrics['top_processes']:
                with st.expander("🔄 Top Processes", expanded=False):
                    processes_df = pd.DataFrame(metrics['top_processes'])
                    if not processes_df.empty:
                        st.dataframe(
                            processes_df.head(10),
                            width='stretch',
                            column_config={
                                "name": "Process Name",
                                "cpu_percent": st.column_config.NumberColumn("CPU %", format="%.1f%%"),
                                "memory_percent": st.column_config.NumberColumn("Memory %", format="%.1f%%"),
                                "pid": "PID"
                            }
                        )
            
            # Posledná aktualizácia a navigácia
            st.markdown("---")
            col_time, col_full = st.columns([3, 1])
            
            with col_time:
                current_time = datetime.now().strftime("%H:%M:%S")
                st.caption(f"🕐 Posledná aktualizácia: {current_time} | 🔄 Auto-refresh každých 10 sekúnd")
                
            with col_full:
                if st.button("📊 Full Dashboard", key="open_full_dashboard", help="Otvoriť rozšírený dashboard s históriou"):
                    st.session_state.show_monitoring_dashboard = True
                    st.rerun()
            
        except Exception as e:
            st.error(f"❌ Chyba pri zobrazovaní monitoringu: {e}")
            st.info("🔧 Skontrolujte či server monitor funguje správne.")


def show_monitoring_dashboard():
    """Zobrazí statický monitoring dashboard so štatistikami"""
    
    # Back tlačidlo
    if st.button("⬅️ Späť do Admin Panel", key="back_to_admin_dashboard"):
        st.session_state.show_monitoring_dashboard = False
        st.rerun()
    
    # Statický server monitoring
    show_static_server_monitoring()
    
    st.markdown("---")
    
    # Historické štatistiky
    show_historical_statistics()


def show_static_server_monitoring():
    """Zobrazí statické informácie o serveri"""
    st.title("🖥️ Server Status")
    
    monitor = get_server_monitor()
    
    # Získaj aktuálne metriky
    try:
        metrics = monitor.get_current_metrics()
        
        # Základné informácie o systéme
        st.subheader("💻 Systém")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="🖥️ CPU Usage", 
                value=f"{metrics.get('cpu_percent', 0):.1f}%",
                delta=f"{metrics.get('cpu_percent', 0) - 50:.1f}%" if metrics.get('cpu_percent', 0) > 50 else None
            )
        
        with col2:
            memory_percent = (metrics.get('memory_used', 0) / metrics.get('memory_total', 1)) * 100
            st.metric(
                label="🧠 Memory Usage", 
                value=f"{memory_percent:.1f}%",
                delta=f"{memory_percent - 60:.1f}%" if memory_percent > 60 else None
            )
        
        with col3:
            disk_percent = (metrics.get('disk_used', 0) / metrics.get('disk_total', 1)) * 100
            st.metric(
                label="💾 Disk Usage", 
                value=f"{disk_percent:.1f}%",
                delta=f"{disk_percent - 70:.1f}%" if disk_percent > 70 else None
            )
        
        # Detailné informácie
        st.subheader("📊 Detailné informácie")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**💾 Memory**")
            st.write(f"Total: {metrics.get('memory_total', 0) / (1024**3):.1f} GB")
            st.write(f"Used: {metrics.get('memory_used', 0) / (1024**3):.1f} GB")
            st.write(f"Available: {metrics.get('memory_available', 0) / (1024**3):.1f} GB")
            
            st.markdown("**🌐 Network**")
            st.write(f"Bytes sent: {metrics.get('network_bytes_sent', 0) / (1024**2):.1f} MB")
            st.write(f"Bytes received: {metrics.get('network_bytes_recv', 0) / (1024**2):.1f} MB")
        
        with col2:
            st.markdown("**💽 Disk**")
            st.write(f"Total: {metrics.get('disk_total', 0) / (1024**3):.1f} GB")
            st.write(f"Used: {metrics.get('disk_used', 0) / (1024**3):.1f} GB")
            st.write(f"Free: {metrics.get('disk_free', 0) / (1024**3):.1f} GB")
            
            st.markdown("**⚙️ System**")
            st.write(f"Boot time: {metrics.get('boot_time', 'N/A')}")
            st.write(f"CPU cores: {metrics.get('cpu_cores', 0)}")
            st.write(f"CPU frequency: {metrics.get('cpu_freq', 0):.0f} MHz")
        
        # Process informácie
        st.subheader("🔄 Top Processes")
        if 'top_processes' in metrics:
            processes_df = pd.DataFrame(metrics['top_processes'])
            if not processes_df.empty:
                st.dataframe(
                    processes_df.head(10),
                    width='stretch',
                    column_config={
                        "name": "Process Name",
                        "cpu_percent": st.column_config.NumberColumn("CPU %", format="%.1f%%"),
                        "memory_percent": st.column_config.NumberColumn("Memory %", format="%.1f%%"),
                        "pid": "PID"
                    }
                )
        
    except Exception as e:
        st.error(f"❌ Chyba pri načítaní server metrík: {e}")
        st.info("🔧 Pokúste sa obnoviť stránku alebo skontrolovať server monitor.")


def show_historical_statistics():
    """Zobrazí historické štatistiky"""
    st.title("📈 Historické štatistiky")
    
    monitor = get_server_monitor()
    
    try:
        # Získaj historické dáta
        historical_data = monitor.get_historical_metrics()
        
        if not historical_data:
            st.info("📊 Žiadne historické dáta k dispozícii. Monitoring musí bežať aspoň niekoľko minút.")
            return
        
        # Konverzia na DataFrame pre jednoduchšie spracovanie
        df_data = []
        for record in historical_data:
            try:
                flat_record = {
                    'timestamp': record['timestamp'],
                    'cpu_percent': record['cpu']['usage_percent'],
                    'memory_total': record['memory']['total_gb'] * (1024**3),  # Convert to bytes
                    'memory_used': record['memory']['used_gb'] * (1024**3),   # Convert to bytes
                    'memory_percent': record['memory']['usage_percent'],
                    'disk_total': record['disk']['total_gb'] * (1024**3),     # Convert to bytes
                    'disk_used': record['disk']['used_gb'] * (1024**3),       # Convert to bytes
                    'disk_percent': record['disk']['usage_percent'],
                    'network_bytes_sent': record['network']['bytes_sent'],
                    'network_bytes_recv': record['network']['bytes_recv']
                }
                df_data.append(flat_record)
            except KeyError as e:
                st.warning(f"Chyba v dátach: chýba kľúč {e}")
                continue
        
        if not df_data:
            st.info("📊 Žiadne spracovateľné historické dáta k dispozícii.")
            return
            
        df = pd.DataFrame(df_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Základné štatistiky za posledných 24 hodín
        st.subheader("📊 Prehľad za posledných 24 hodín")
        
        if len(df) > 0:
            latest_24h = df.tail(1440)  # Posledných 24 hodín (1440 minút)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_cpu = latest_24h['cpu_percent'].mean()
                max_cpu = latest_24h['cpu_percent'].max()
                st.metric("🖥️ Priemerné CPU", f"{avg_cpu:.1f}%", f"Max: {max_cpu:.1f}%")
            
            with col2:
                avg_memory = (latest_24h['memory_used'] / latest_24h['memory_total'] * 100).mean()
                max_memory = (latest_24h['memory_used'] / latest_24h['memory_total'] * 100).max()
                st.metric("🧠 Priemerná RAM", f"{avg_memory:.1f}%", f"Max: {max_memory:.1f}%")
            
            with col3:
                avg_disk = (latest_24h['disk_used'] / latest_24h['disk_total'] * 100).mean()
                st.metric("💾 Disk Usage", f"{avg_disk:.1f}%")
            
            with col4:
                total_network = (latest_24h['network_bytes_sent'] + latest_24h['network_bytes_recv']).sum() / (1024**3)
                st.metric("🌐 Network Total", f"{total_network:.2f} GB")
        
        # Grafy
        st.subheader("📉 Trendy použitia")
        
        # CPU graf
        st.markdown("**🖥️ CPU Usage trend**")
        df_recent = df.tail(100)
        
        fig_cpu = go.Figure()
        fig_cpu.add_trace(go.Scatter(
            x=df_recent['timestamp'], 
            y=df_recent['cpu_percent'],
            mode='lines',
            name='CPU %',
            line=dict(color='blue', width=2)
        ))
        fig_cpu.update_layout(
            title="CPU Usage Over Time",
            xaxis_title="Time",
            yaxis_title="CPU %",
            yaxis=dict(range=[0, 100]),
            height=300
        )
        st.plotly_chart(fig_cpu, width='stretch')
        
        # Memory graf
        st.markdown("**🧠 Memory Usage trend**")
        df_memory = df.tail(100).copy()
        df_memory['memory_percent'] = (df_memory['memory_used'] / df_memory['memory_total']) * 100
        
        fig_memory = go.Figure()
        fig_memory.add_trace(go.Scatter(
            x=df_memory['timestamp'], 
            y=df_memory['memory_percent'],
            mode='lines',
            name='Memory %',
            line=dict(color='orange', width=2)
        ))
        fig_memory.update_layout(
            title="Memory Usage Over Time",
            xaxis_title="Time",
            yaxis_title="Memory %",
            yaxis=dict(range=[0, 100]),
            height=300
        )
        st.plotly_chart(fig_memory, width='stretch')
        
        # Súhrnné štatistiky
        st.subheader("📋 Súhrnné štatistiky")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**⏱️ Čas monitorovania**")
            if len(df) > 1:
                monitoring_duration = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600
                st.write(f"Celkový čas: {monitoring_duration:.1f} hodín")
                st.write(f"Počet záznamov: {len(df)}")
                st.write(f"Priemerný interval: {monitoring_duration * 3600 / len(df):.1f} sekúnd")
        
        with col2:
            st.markdown("**🎯 Performance hodnotenie**")
            avg_cpu_all = df['cpu_percent'].mean()
            avg_memory_all = (df['memory_used'] / df['memory_total'] * 100).mean()
            
            if avg_cpu_all < 20:
                cpu_status = "🟢 Výborné"
            elif avg_cpu_all < 50:
                cpu_status = "🟡 Dobré"
            else:
                cpu_status = "🔴 Vysoké"
                
            if avg_memory_all < 50:
                memory_status = "🟢 Výborné"
            elif avg_memory_all < 80:
                memory_status = "🟡 Dobré"
            else:
                memory_status = "🔴 Vysoké"
            
            st.write(f"CPU performance: {cpu_status}")
            st.write(f"Memory performance: {memory_status}")
            
    except Exception as e:
        st.error(f"❌ Chyba pri načítaní historických dát: {e}")
        st.info("🔧 Skontrolujte či server monitoring beží a má dostatočné oprávnenia.")


def show_server_monitoring_content():
    """Zobrazí server monitoring obsah bez back tlačidla"""
    
    st.title("🖥️ Server Monitoring Dashboard")
    
    monitor = get_server_monitor()
    
    # Inicializácia session state
    if 'monitoring_enabled' not in st.session_state:
        st.session_state.monitoring_enabled = True
    if 'refresh_rate' not in st.session_state:
        st.session_state.refresh_rate = 3
    
    # Fixed Control Panel
    with st.container():
        st.subheader("⚙️ Control Panel")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            # Monitoring status - stable
            if not monitor.monitoring:
                if st.button("▶️ Start Monitoring", key="start_btn"):
                    monitor.start_monitoring(interval_seconds=60)
                    st.success("✅ Background monitoring started!")
                    st.rerun()
            else:
                st.success("✅ Background monitoring active")
                if st.button("⏹️ Stop Monitoring", key="stop_btn"):
                    monitor.stop_monitoring()
                    st.warning("⏸️ Monitoring stopped!")
                    st.rerun()
        
        with col2:
            # Real-time toggle - stable
            monitoring_enabled = st.toggle(
                "🔴 Real-time Updates", 
                value=st.session_state.monitoring_enabled,
                key="realtime_toggle",
                help="Enable/disable live dashboard updates"
            )
            if monitoring_enabled != st.session_state.monitoring_enabled:
                st.session_state.monitoring_enabled = monitoring_enabled
        
        with col3:
            # Refresh rate - stable
            if st.session_state.monitoring_enabled:
                refresh_options = {
                    "Slow (5s)": 5,
                    "Normal (3s)": 3, 
                    "Fast (2s)": 2,
                    "Very Fast (1s)": 1
                }
                
                selected_rate = st.selectbox(
                    "🕐 Update Speed:",
                    list(refresh_options.keys()),
                    index=1,  # Default Normal (3s)
                    key="refresh_select",
                    help="How often to update the dashboard"
                )
                st.session_state.refresh_rate = refresh_options[selected_rate]
            else:
                st.info("Enable real-time updates to set refresh rate")
    
    st.divider()
    
    # JavaScript-based Real-time Dashboard
    if st.session_state.monitoring_enabled and monitor.monitoring:
        show_javascript_dashboard(monitor)
    else:
        show_static_dashboard(monitor)


def show_javascript_dashboard(monitor):
    """Zobrazí dashboard s JavaScript real-time updates"""
    
    st.markdown("""
    <style>
    .live-indicator {
        background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        font-size: 1.2em;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 15px;
        margin: 5px;
        border-left: 4px solid #4ecdc4;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        animation: blink 1.5s infinite;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.3; }
    }
    
    .dashboard-container {
        border: 2px solid rgba(255, 107, 107, 0.3);
        border-radius: 15px;
        padding: 20px;
        background: rgba(0, 0, 0, 0.02);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Live status header - stable
    st.markdown(f"""
    <div class="dashboard-container">
        <h3 class="live-indicator">
            <span class="status-indicator" style="background-color: #ff6b6b;"></span>
            LIVE DASHBOARD - Updates every {st.session_state.refresh_rate}s
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Stable containers pre metrics
    metrics_container = st.container()
    charts_container = st.container()
    processes_container = st.container()
    stats_container = st.container()
    
    # Current snapshot - zobrazí sa okamžite
    with metrics_container:
        show_current_metrics(monitor)
    
    with charts_container:
        show_live_charts(monitor)
    
    with processes_container:
        show_live_processes(monitor)
    
    with stats_container:
        show_daily_stats(monitor)
    
    # JavaScript auto-refresh - iba ak je potrebné
    refresh_interval_ms = st.session_state.refresh_rate * 1000
    
    # Custom JavaScript pre smooth updates
    st.markdown(f"""
    <script>
    let updateCounter = 0;
    let lastUpdate = new Date();
    
    function updateDashboard() {{
        updateCounter++;
        lastUpdate = new Date();
        
        // Update live indicator
        const indicator = document.querySelector('.live-indicator');
        if (indicator) {{
            indicator.innerHTML = `
                <span class="status-indicator" style="background-color: #ff6b6b;"></span>
                LIVE DASHBOARD - Last update: ${{lastUpdate.toLocaleTimeString()}} (#${{updateCounter}})
            `;
        }}
        
        // Trigger Streamlit rerun len ak je potrebné
        window.parent.postMessage({{
            type: 'streamlit:componentUpdate',
            refresh: true
        }}, '*');
    }}
    
    // Set interval pre updates
    const refreshInterval = setInterval(updateDashboard, {refresh_interval_ms});
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {{
        clearInterval(refreshInterval);
    }});
    
    console.log('Real-time dashboard initialized with {st.session_state.refresh_rate}s refresh rate');
    </script>
    """, unsafe_allow_html=True)
    
    # Manual refresh tlačidlo
    if st.button("🔄 Manual Refresh", key="manual_refresh"):
        st.rerun()


def show_static_dashboard(monitor):
    """Zobrazí statický dashboard bez auto-refresh"""
    
    st.info("🔄 Real-time updates are disabled. Enable the toggle above for live monitoring.")
    
    # Manual refresh
    if st.button("🔄 Refresh Now", key="static_refresh"):
        st.rerun()
    
    # Show current state
    show_current_metrics(monitor)
    show_live_charts(monitor) 
    show_live_processes(monitor)
    show_daily_stats(monitor)


def show_current_metrics(monitor):
    """Zobrazí aktuálne metriky - stable version"""
    
    st.subheader("📊 Current System Metrics")
    
    metrics = monitor.get_current_metrics()
    
    if "error" in metrics:
        st.error(f"❌ {metrics['error']}")
        return
    
    # Metrics v stable layout
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cpu_percent = metrics['cpu']['usage_percent']
        cpu_status = "🟢 Normal" if cpu_percent < 50 else "🟡 Busy" if cpu_percent < 80 else "🔥 High"
        st.metric(
            label="🖥️ CPU Usage", 
            value=f"{cpu_percent}%",
            delta=f"{metrics['cpu']['count']} cores",
            help=f"Status: {cpu_status}"
        )
    
    with col2:
        memory_used = metrics['memory']['used_gb']
        memory_total = metrics['memory']['total_gb']
        memory_percent = metrics['memory']['usage_percent']
        memory_status = "🟢 Normal" if memory_percent < 60 else "🟡 High" if memory_percent < 80 else "🔥 Critical"
        st.metric(
            label="💾 RAM Usage", 
            value=f"{memory_used:.1f}GB",
            delta=f"{memory_percent:.1f}% of {memory_total:.1f}GB",
            help=f"Status: {memory_status}"
        )
    
    with col3:
        disk_used = metrics['disk']['used_gb'] 
        disk_total = metrics['disk']['total_gb']
        disk_percent = metrics['disk']['usage_percent']
        disk_status = "🟢 Normal" if disk_percent < 70 else "🟡 High" if disk_percent < 85 else "🔥 Critical"
        st.metric(
            label="💿 Disk Usage",
            value=f"{disk_used:.1f}GB", 
            delta=f"{disk_percent:.1f}% of {disk_total:.1f}GB",
            help=f"Status: {disk_status}, Free: {metrics['disk']['free_gb']:.1f}GB"
        )
    
    with col4:
        net_sent_mb = metrics['network']['bytes_sent'] / (1024*1024)
        net_recv_mb = metrics['network']['bytes_recv'] / (1024*1024)
        st.metric(
            label="🌐 Network Traffic",
            value=f"↑ {net_sent_mb:.0f}MB",
            delta=f"↓ {net_recv_mb:.0f}MB",
            help=f"Total packets: ↑{metrics['network']['packets_sent']:,} ↓{metrics['network']['packets_recv']:,}"
        )
    
    # Stable progress bars
    st.markdown("#### 📈 Resource Utilization")
    
    # CPU progress
    st.progress(
        cpu_percent / 100, 
        text=f"🖥️ CPU: {cpu_percent}% - {cpu_status.split(' ')[1]}"
    )
    
    # Memory progress  
    st.progress(
        memory_percent / 100, 
        text=f"💾 RAM: {memory_percent:.1f}% - {memory_status.split(' ')[1]} ({memory_used:.1f}/{memory_total:.1f}GB)"
    )
    
    # Disk progress
    st.progress(
        disk_percent / 100, 
        text=f"💿 Disk: {disk_percent:.1f}% - {disk_status.split(' ')[1]} ({disk_used:.1f}/{disk_total:.1f}GB)"
    )


def show_live_charts(monitor):
    """Zobrazí live grafy - stable version"""
    
    st.subheader("📈 System Trends")
    
    historical_metrics = monitor.get_historical_metrics(2)  # Posledné 2 hodiny
    
    if len(historical_metrics) > 1:
        # Priprav dáta pre grafy
        timestamps = [datetime.fromisoformat(m['timestamp']) for m in historical_metrics[-30:]]  # Posledných 30 bodov
        cpu_data = [m['cpu']['usage_percent'] for m in historical_metrics[-30:]]
        memory_data = [m['memory']['usage_percent'] for m in historical_metrics[-30:]]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # CPU trend graf
            fig_cpu = go.Figure()
            fig_cpu.add_trace(go.Scatter(
                x=timestamps, 
                y=cpu_data,
                mode='lines+markers',
                name='CPU %',
                line=dict(color='#ff6b6b', width=2),
                marker=dict(size=4),
                fill='tonexty',
                fillcolor='rgba(255, 107, 107, 0.1)'
            ))
            fig_cpu.update_layout(
                title=f'🖥️ CPU Usage Trend (Current: {cpu_data[-1]:.1f}%)',
                xaxis_title='Time',
                yaxis_title='CPU %',
                height=300,
                showlegend=False
            )
            st.plotly_chart(fig_cpu, width="stretch")
        
        with col2:
            # Memory trend graf  
            fig_memory = go.Figure()
            fig_memory.add_trace(go.Scatter(
                x=timestamps,
                y=memory_data,
                mode='lines+markers', 
                name='RAM %',
                line=dict(color='#4ecdc4', width=2),
                marker=dict(size=4),
                fill='tonexty',
                fillcolor='rgba(78, 205, 196, 0.1)'
            ))
            fig_memory.update_layout(
                title=f'💾 RAM Usage Trend (Current: {memory_data[-1]:.1f}%)',
                xaxis_title='Time',
                yaxis_title='RAM %', 
                height=300,
                showlegend=False
            )
            st.plotly_chart(fig_memory, width="stretch")
        
        # Summary info
        avg_cpu = sum(cpu_data) / len(cpu_data)
        avg_memory = sum(memory_data) / len(memory_data)
        
        st.info(f"📊 **Last 30 measurements:** Avg CPU: {avg_cpu:.1f}%, Avg RAM: {avg_memory:.1f}%")
        
    else:
        st.info("🔄 Collecting historical data for trends... Please wait a few minutes.")


def show_live_processes(monitor):
    """Zobrazí live procesy - stable version"""
    
    st.subheader("🏃 Active Processes")
    
    metrics = monitor.get_current_metrics()
    
    if metrics.get('top_processes'):
        # Prepare process data
        process_data = []
        for i, proc in enumerate(metrics['top_processes'][:12], 1):
            cpu_status = "🔥" if proc['cpu_percent'] > 15 else "⚡" if proc['cpu_percent'] > 5 else "💤"
            memory_status = "🔴" if proc['memory_percent'] > 10 else "🟡" if proc['memory_percent'] > 5 else "🟢"
            
            process_data.append({
                '#': i,
                'CPU': cpu_status,
                'RAM': memory_status,
                'PID': proc['pid'],
                'Process Name': proc['name'][:30] + ('...' if len(proc['name']) > 30 else ''),
                'CPU %': f"{proc['cpu_percent']:.1f}%",
                'Memory %': f"{proc['memory_percent']:.1f}%"
            })
        
        if process_data:
            df_processes = pd.DataFrame(process_data)
            st.dataframe(
                df_processes, 
                width="stretch", 
                hide_index=True,
                column_config={
                    "CPU": st.column_config.TextColumn("CPU", width="small"),
                    "RAM": st.column_config.TextColumn("RAM", width="small"),
                    "PID": st.column_config.NumberColumn("PID", width="small"),
                    "Process Name": st.column_config.TextColumn("Process Name", width="large"),
                    "CPU %": st.column_config.TextColumn("CPU %", width="small"), 
                    "Memory %": st.column_config.TextColumn("Memory %", width="small")
                }
            )
    else:
        st.info("No process data available")


def show_daily_stats(monitor):
    """Zobrazí denné štatistiky - stable version"""
    
    st.subheader("📈 24-Hour Statistics")
    
    daily_stats = monitor.get_daily_growth_stats()
    
    if "error" not in daily_stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            memory_growth = daily_stats['memory_growth_gb']
            growth_trend = "📈 Increasing" if memory_growth > 0.01 else "📉 Decreasing" if memory_growth < -0.01 else "➖ Stable"
            st.metric(
                "💾 RAM Growth",
                f"{memory_growth:+.3f} GB",
                delta=growth_trend.split(' ')[1],
                help="Memory usage change over 24 hours"
            )
        
        with col2:
            disk_growth = daily_stats['disk_growth_gb'] 
            disk_trend = "📈 Increasing" if disk_growth > 0.1 else "📉 Decreasing" if disk_growth < -0.1 else "➖ Stable"
            st.metric(
                "💿 Disk Growth",
                f"{disk_growth:+.3f} GB", 
                delta=disk_trend.split(' ')[1],
                help="Disk usage change over 24 hours"
            )
        
        with col3:
            avg_cpu = daily_stats['avg_cpu_percent']
            cpu_level = "High Load" if avg_cpu > 70 else "Normal Load" if avg_cpu > 30 else "Light Load"
            st.metric(
                "🖥️ Avg CPU",
                f"{avg_cpu:.1f}%",
                delta=cpu_level,
                help="Average CPU utilization over 24h"
            )
        
        with col4:
            avg_memory = daily_stats['avg_memory_percent']
            memory_level = "High Usage" if avg_memory > 80 else "Normal Usage" if avg_memory > 50 else "Light Usage"
            st.metric(
                "💾 Avg RAM",
                f"{avg_memory:.1f}%", 
                delta=memory_level,
                help="Average RAM utilization over 24h"
            )
        
        st.caption(f"📊 Statistics based on {daily_stats['data_points']} measurements over 24 hours")
        
    else:
        st.warning(f"⚠️ {daily_stats['error']}")


def update_realtime_content(monitor, metrics_placeholder, charts_placeholder, 
                          processes_placeholder, stats_placeholder):
    """Aktualizuje real-time obsah v placeholder containers"""
    
    # Získanie aktuálnych metrík
    metrics = monitor.get_current_metrics()
    
    if "error" in metrics:
        metrics_placeholder.error(f"❌ {metrics['error']}")
        return
    
    # === METRICS SECTION ===
    with metrics_placeholder.container():
        st.subheader("📊 Live Metriky")
        
        # Metrics cards
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            cpu_percent = metrics['cpu']['usage_percent']
            cpu_emoji = "🔥" if cpu_percent > 80 else "🟡" if cpu_percent > 50 else "🟢"
            st.metric(
                label=f"{cpu_emoji} CPU", 
                value=f"{cpu_percent}%",
                delta=f"{metrics['cpu']['count']} cores",
                help=f"Frequency: {metrics['cpu']['frequency_mhz']}MHz" if metrics['cpu']['frequency_mhz'] else None
            )
        
        with metric_col2:
            memory_used = metrics['memory']['used_gb']
            memory_total = metrics['memory']['total_gb']
            memory_percent = metrics['memory']['usage_percent']
            memory_emoji = "🔥" if memory_percent > 80 else "🟡" if memory_percent > 60 else "🟢"
            st.metric(
                label=f"{memory_emoji} RAM", 
                value=f"{memory_used:.1f}GB",
                delta=f"{memory_percent:.1f}% used",
                help=f"Available: {metrics['memory']['available_gb']:.1f}GB"
            )
        
        with metric_col3:
            disk_used = metrics['disk']['used_gb'] 
            disk_total = metrics['disk']['total_gb']
            disk_percent = metrics['disk']['usage_percent']
            disk_emoji = "🔥" if disk_percent > 85 else "🟡" if disk_percent > 70 else "🟢"
            st.metric(
                label=f"{disk_emoji} Disk",
                value=f"{disk_used:.1f}GB", 
                delta=f"{disk_percent:.1f}% used",
                help=f"Free: {metrics['disk']['free_gb']:.1f}GB"
            )
        
        with metric_col4:
            net_sent_mb = metrics['network']['bytes_sent'] / (1024*1024)
            net_recv_mb = metrics['network']['bytes_recv'] / (1024*1024)
            st.metric(
                label="🌐 Network",
                value=f"↑{net_sent_mb:.0f}MB",
                delta=f"↓{net_recv_mb:.0f}MB",
                help=f"Packets: ↑{metrics['network']['packets_sent']:,} ↓{metrics['network']['packets_recv']:,}"
            )
        
        # Progress bars s live updates
        st.markdown("#### 📈 Resource Utilization")
        
        # CPU progress
        cpu_status = "🔥 HIGH" if cpu_percent > 80 else "🟡 NORMAL" if cpu_percent > 50 else "🟢 LOW"
        st.progress(cpu_percent / 100, text=f"CPU: {cpu_percent}% - {cpu_status}")
        
        # Memory progress  
        memory_status = "🔥 HIGH" if memory_percent > 80 else "🟡 NORMAL" if memory_percent > 60 else "🟢 LOW"
        st.progress(memory_percent / 100, text=f"RAM: {memory_percent}% - {memory_status} ({memory_used:.1f}/{memory_total:.1f}GB)")
        
        # Disk progress
        disk_status = "🔥 HIGH" if disk_percent > 85 else "🟡 NORMAL" if disk_percent > 70 else "🟢 LOW"
        st.progress(disk_percent / 100, text=f"Disk: {disk_percent}% - {disk_status} ({disk_used:.1f}/{disk_total:.1f}GB)")
    
    # === CHARTS SECTION ===
    with charts_placeholder.container():
        st.subheader("📈 Live Grafy")
        
        # Získanie historických dát pre grafy
        historical_metrics = monitor.get_historical_metrics(1)  # Posledná hodina
        
        if len(historical_metrics) > 1:
            chart_col1, chart_col2 = st.columns(2)
            
            # Príprava dát pre grafy (posledných 15 bodov pre performance)
            recent_metrics = historical_metrics[-15:]
            timestamps = [datetime.fromisoformat(m['timestamp']) for m in recent_metrics]
            cpu_data = [m['cpu']['usage_percent'] for m in recent_metrics]
            memory_data = [m['memory']['usage_percent'] for m in recent_metrics]
            
            with chart_col1:
                # Live CPU graf
                fig_cpu = go.Figure()
                fig_cpu.add_trace(go.Scatter(
                    x=timestamps, 
                    y=cpu_data,
                    mode='lines+markers',
                    name='CPU %',
                    line=dict(color='#ff6b6b', width=3),
                    marker=dict(size=5),
                    fill='tonexty' if len(timestamps) > 1 else None,
                    fillcolor='rgba(255, 107, 107, 0.1)'
                ))
                fig_cpu.update_layout(
                    title=f'🔥 CPU Usage - Live ({cpu_data[-1]:.1f}% current)',
                    xaxis_title='Time',
                    yaxis_title='CPU %',
                    height=250,
                    showlegend=False,
                    margin=dict(l=40, r=20, t=50, b=40)
                )
                st.plotly_chart(fig_cpu, width="stretch", key=f"live_cpu_{st.session_state.monitor_counter}")
            
            with chart_col2:
                # Live Memory graf  
                fig_memory = go.Figure()
                fig_memory.add_trace(go.Scatter(
                    x=timestamps,
                    y=memory_data,
                    mode='lines+markers', 
                    name='RAM %',
                    line=dict(color='#4ecdc4', width=3),
                    marker=dict(size=5),
                    fill='tonexty' if len(timestamps) > 1 else None,
                    fillcolor='rgba(78, 205, 196, 0.1)'
                ))
                fig_memory.update_layout(
                    title=f'💾 RAM Usage - Live ({memory_data[-1]:.1f}% current)',
                    xaxis_title='Time',
                    yaxis_title='RAM %',
                    height=250,
                    showlegend=False,
                    margin=dict(l=40, r=20, t=50, b=40)
                )
                st.plotly_chart(fig_memory, width="stretch", key=f"live_memory_{st.session_state.monitor_counter}")
        
        else:
            st.info("🔄 Collecting historical data for charts...")
    
    # === PROCESSES SECTION ===
    with processes_placeholder.container():
        st.subheader("🏃 Top Procesy - Live")
        
        if metrics['top_processes']:
            process_data = []
            for i, proc in enumerate(metrics['top_processes'][:10], 1):
                cpu_emoji = "🔥" if proc['cpu_percent'] > 20 else "⚡" if proc['cpu_percent'] > 5 else "💤"
                ram_emoji = "🔥" if proc['memory_percent'] > 10 else "📊"
                
                process_data.append({
                    '#': i,
                    'Status': cpu_emoji,
                    'PID': proc['pid'],
                    'Process': proc['name'][:25] + ('...' if len(proc['name']) > 25 else ''),
                    'CPU': f"{proc['cpu_percent']:.1f}%",
                    'RAM': f"{proc['memory_percent']:.1f}%",
                    'Load': ram_emoji
                })
            
            if process_data:
                df_processes = pd.DataFrame(process_data)
                st.dataframe(df_processes, width="stretch", hide_index=True, 
                           key=f"live_processes_{st.session_state.monitor_counter}")
        else:
            st.info("No active processes found")
    
    # === DAILY STATS SECTION ===
    with stats_placeholder.container():
        st.subheader("📈 24h Štatistiky")
        
        daily_stats = monitor.get_daily_growth_stats()
        
        if "error" not in daily_stats:
            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            
            with stat_col1:
                memory_growth = daily_stats['memory_growth_gb']
                growth_emoji = "📈" if memory_growth > 0.01 else "📉" if memory_growth < -0.01 else "➖"
                st.metric(
                    f"{growth_emoji} RAM Growth",
                    f"{memory_growth:+.3f} GB",
                    help="Memory usage change over 24h"
                )
            
            with stat_col2:
                disk_growth = daily_stats['disk_growth_gb'] 
                disk_emoji = "📈" if disk_growth > 0.1 else "📉" if disk_growth < -0.1 else "➖"
                st.metric(
                    f"{disk_emoji} Disk Growth",
                    f"{disk_growth:+.3f} GB", 
                    help="Disk usage change over 24h"
                )
            
            with stat_col3:
                avg_cpu = daily_stats['avg_cpu_percent']
                cpu_trend = "High" if avg_cpu > 70 else "Normal" if avg_cpu > 30 else "Low"
                st.metric(
                    "🔥 Avg CPU/24h",
                    f"{avg_cpu:.1f}%",
                    delta=cpu_trend,
                    help="Average CPU utilization over 24h"
                )
            
            with stat_col4:
                avg_memory = daily_stats['avg_memory_percent']
                memory_trend = "High" if avg_memory > 80 else "Normal" if avg_memory > 50 else "Low"
                st.metric(
                    "💾 Avg RAM/24h",
                    f"{avg_memory:.1f}%", 
                    delta=memory_trend,
                    help="Average RAM utilization over 24h"
                )
            
            st.caption(f"📊 Based on {daily_stats['data_points']} measurements")
        
        else:
            st.warning(f"⚠️ {daily_stats['error']}")
