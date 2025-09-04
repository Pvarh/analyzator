import streamlit as st
import time
from typing import Dict, List
from auth.users_db import UserDatabase
from auth.auth import get_current_user, is_admin


def render():
    """Hlavná stránka pre správu používateľov"""
    st.title("👥 Správa používateľov")
    st.markdown("**Kompletné rozhranie pre správu všetkých používateľov systému**")
    
    # Kontrola admin oprávnení
    if not is_admin():
        st.error("❌ Nemáte oprávnenie na túto stránku!")
        return
    
    user_db = UserDatabase()
    
    # Sidebar pre navigáciu
    with st.sidebar:
        st.markdown("### 👥 User Management")
        
        # Tlačidlo pre pridanie nového používateľa
        if st.button("➕ Pridať nového používateľa", use_container_width=True, type="primary"):
            st.session_state.user_mgmt_mode = "add_new"
            st.session_state.selected_user_email = None
            st.rerun()
        
        st.divider()
        
        # Zoznam používateľov
        try:
            all_users_data = user_db.load_users()
            
            if all_users_data:
                st.markdown("**📋 Vyberte používateľa:**")
                
                for email, user_data in all_users_data.items():
                    # Status indikátor
                    status_icon = "✅" if user_data.get('active', True) else "❌"
                    role_icon = "👑" if user_data.get('role') == 'admin' else "👤"
                    
                    # Tlačidlo pre každého používateľa
                    button_text = f"{status_icon} {role_icon} {user_data.get('name', email)}"
                    
                    if st.button(
                        button_text, 
                        key=f"user_select_{email}",
                        use_container_width=True,
                        help=f"Email: {email}\nRola: {user_data.get('role', 'N/A')}"
                    ):
                        st.session_state.user_mgmt_mode = "edit_user"
                        st.session_state.selected_user_email = email
                        st.rerun()
            else:
                st.warning("⚠️ Žiadni používatelia v databáze")
                
        except Exception as e:
            st.error(f"❌ Chyba pri načítaní používateľov: {e}")
    
    # Hlavný obsah
    mode = st.session_state.get('user_mgmt_mode', 'overview')
    
    if mode == "add_new":
        show_add_user_form(user_db)
    elif mode == "edit_user":
        selected_email = st.session_state.get('selected_user_email')
        if selected_email:
            show_user_detail(user_db, selected_email)
        else:
            show_overview(user_db)
    else:
        show_overview(user_db)


def show_overview(user_db):
    """Zobrazí prehľad všetkých používateľov"""
    st.header("📊 Prehľad používateľov")
    
    try:
        all_users_data = user_db.load_users()
        
        if not all_users_data:
            st.info("📝 **Zatiaľ žiadni používatelia.** Použite tlačidlo '➕ Pridať nového používateľa' v sidebar-e.")
            return
        
        # Štatistiky
        total_users = len(all_users_data)
        active_users = sum(1 for user in all_users_data.values() if user.get('active', True))
        admin_users = sum(1 for user in all_users_data.values() if user.get('role') == 'admin')
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👥 Celkom používateľov", total_users)
        with col2:
            st.metric("✅ Aktívnych", active_users)
        with col3:
            st.metric("❌ Neaktívnych", total_users - active_users)
        with col4:
            st.metric("👑 Adminov", admin_users)
        
        st.divider()
        
        # Tabuľka používateľov
        st.subheader("📋 Zoznam používateľov")
        
        users_data = []
        for email, user_data in all_users_data.items():
            users_data.append({
                'Email': email,
                'Meno': user_data.get('name', 'N/A'),
                'Rola': user_data.get('role', 'N/A'),
                'Mestá': ', '.join(user_data.get('cities', [])),
                'Aktívny': "✅ Áno" if user_data.get('active', True) else "❌ Nie",
                'Stránky': len(user_data.get('page_permissions', []))
            })
        
        if users_data:
            st.dataframe(users_data, use_container_width=True, hide_index=True)
        
        # Info panel
        st.info("💡 **Tip:** Kliknite na používateľa v sidebar-e pre detailnú správu jeho nastavení.")
        
    except Exception as e:
        st.error(f"❌ Chyba pri zobrazení prehľadu: {e}")


def show_add_user_form(user_db):
    """Formulár pre pridanie nového používateľa"""
    st.header("➕ Pridať nového používateľa")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("👤 Meno a priezvisko *", placeholder="napr. Jan Novák")
            email = st.text_input("📧 Email *", placeholder="jan.novak@sykora.eu")
            password = st.text_input("🔒 Heslo *", type="password", placeholder="Minimálne 6 znakov")
        
        with col2:
            role = st.selectbox("🎭 Rola *", ["manager", "admin"], index=0)
            available_cities = user_db.get_available_cities()
            cities = st.multiselect("🏙️ Prístupné mestá *", available_cities)
            active = st.checkbox("✅ Aktívny účet", value=True)
        
        st.divider()
        st.markdown("### 🔐 Oprávnenia stránok")
        
        # Page permissions
        available_pages = {
            'overview': '🏠 Prehľad',
            'employee': '👤 Detail zamestnanca',
            'benchmark': '🏆 Benchmark', 
            'heatmap': '🔥 Heatmapa',
            'studio': '🏢 Studio',
            'kpi_system': '🎯 KPI Systém'
        }
        
        if role == "admin":
            available_pages['admin'] = '👑 Administrácia'
        
        page_permissions = []
        cols = st.columns(3)
        for i, (page_id, page_name) in enumerate(available_pages.items()):
            with cols[i % 3]:
                if st.checkbox(page_name, value=True, key=f"page_{page_id}"):
                    page_permissions.append(page_id)
        
        submitted = st.form_submit_button("✅ Vytvoriť používateľa", type="primary")
        
        if submitted:
            # Validácie
            if not name or not email or not password:
                st.error("❌ Všetky povinné polia musia byť vyplnené!")
                return
            
            if not cities:
                st.error("❌ Vyberte aspoň jedno mesto!")
                return
            
            if len(password) < 6:
                st.error("❌ Heslo musí mať aspoň 6 znakov!")
                return
            
            try:
                # Vytvor používateľa
                if user_db.add_user(email, password, role, cities, name):
                    # Aktualizuj page permissions
                    user_db.update_user(email, page_permissions=page_permissions, active=active)
                    
                    st.success(f"✅ **Používateľ {name} bol úspešne vytvorený!**")
                    st.info(f"📧 **Email:** {email}")
                    st.info(f"🔐 **Povolené stránky:** {', '.join([available_pages[p] for p in page_permissions])}")
                    
                    time.sleep(2)
                    st.session_state.user_mgmt_mode = "overview"
                    st.rerun()
                else:
                    st.error("❌ Používateľ s týmto emailom už existuje alebo nastala chyba!")
                    
            except Exception as e:
                st.error(f"❌ Chyba pri vytváraní používateľa: {e}")


def show_user_detail(user_db, email):
    """Detailná správa konkrétneho používateľa"""
    try:
        all_users_data = user_db.load_users()
        user_data = all_users_data.get(email)
        
        if not user_data:
            st.error(f"❌ Používateľ {email} nebol nájdený!")
            return
        
        # Header s informáciami o používateľovi
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.header(f"👤 {user_data.get('name', email)}")
            st.caption(f"📧 {email}")
        with col2:
            role_icon = "👑" if user_data.get('role') == 'admin' else "👤"
            st.metric(f"{role_icon} Rola", user_data.get('role', 'N/A'))
        with col3:
            status_icon = "✅" if user_data.get('active', True) else "❌"
            st.metric(f"{status_icon} Status", "Aktívny" if user_data.get('active', True) else "Neaktívny")
        
        # Taby pre rôzne funkcie
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📝 Základné info",
            "🔐 Oprávnenia stránok", 
            "🎛️ Funkcie",
            "🔒 Zmena hesla",
            "🗑️ Správa účtu"
        ])
        
        with tab1:
            show_basic_user_info(user_db, email, user_data)
        
        with tab2:
            show_page_permissions_tab(user_db, email, user_data)
        
        with tab3:
            show_features_tab(user_db, email, user_data)
        
        with tab4:
            show_password_change_tab(user_db, email, user_data)
        
        with tab5:
            show_account_management_tab(user_db, email, user_data)
            
    except Exception as e:
        st.error(f"❌ Chyba pri zobrazení detailu používateľa: {e}")


def show_basic_user_info(user_db, email, user_data):
    """Tab pre základné informácie používateľa"""
    st.subheader("📝 Základné informácie")
    
    with st.form("basic_info_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("👤 Meno a priezvisko", value=user_data.get('name', ''))
            role = st.selectbox("🎭 Rola", ["manager", "admin"], 
                               index=0 if user_data.get('role') == 'manager' else 1)
        
        with col2:
            available_cities = user_db.get_available_cities()
            current_cities = user_data.get('cities', [])
            cities = st.multiselect("🏙️ Prístupné mestá", available_cities, default=current_cities)
            active = st.checkbox("✅ Aktívny účet", value=user_data.get('active', True))
        
        if st.form_submit_button("💾 Uložiť zmeny", type="primary"):
            try:
                user_db.update_user(email, name=name, role=role, cities=cities, active=active)
                st.success("✅ Základné informácie boli aktualizované!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Chyba pri aktualizácii: {e}")


def show_page_permissions_tab(user_db, email, user_data):
    """Tab pre oprávnenia stránok"""
    st.subheader("🔐 Oprávnenia stránok")
    
    # Definícia všetkých dostupných stránok
    available_pages = {
        'overview': '🏠 Prehľad',
        'employee': '👤 Detail zamestnanca',
        'benchmark': '🏆 Benchmark', 
        'heatmap': '🔥 Heatmapa',
        'studio': '🏢 Studio',
        'kpi_system': '🎯 KPI Systém',
        'admin': '👑 Administrácia'
    }
    
    current_permissions = user_data.get('page_permissions', [])
    
    # Admin má vždy všetky oprávnenia
    if user_data.get('role') == 'admin':
        st.success("👑 **Admin používateľ má automaticky prístup ku všetkým stránkam**")
        
        # Zobraz iba informatívne
        for page_id, page_name in available_pages.items():
            st.checkbox(
                page_name, 
                value=True, 
                disabled=True,
                key=f"perm_{email}_{page_id}_info",
                help="Admin má vždy prístup"
            )
    else:
        st.info("✅ Zaškrtnuté stránky bude používateľ môcť vidieť")
        
        new_permissions = []
        
        for page_id, page_name in available_pages.items():
            if page_id == 'admin':
                # Admin stránka iba pre adminov
                st.checkbox(
                    f"{page_name} (iba pre adminov)", 
                    value=False, 
                    disabled=True,
                    key=f"perm_{email}_{page_id}_disabled",
                    help="Admin stránka je dostupná iba pre admin používateľov"
                )
            else:
                # Ostatné stránky
                is_enabled = st.checkbox(
                    page_name, 
                    value=page_id in current_permissions,
                    key=f"perm_{email}_{page_id}"
                )
                
                if is_enabled:
                    new_permissions.append(page_id)
        
        # Tlačidlo na uloženie
        if st.button("💾 Uložiť oprávnenia", type="primary"):
            try:
                user_db.update_user(email, page_permissions=new_permissions)
                st.success(f"✅ **Oprávnenia uložené!**")
                st.info(f"🔐 **Povolené stránky:** {', '.join([available_pages[p] for p in new_permissions])}")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Chyba pri uložení: {e}")


def show_features_tab(user_db, email, user_data):
    """Tab pre správu funkcií"""
    st.subheader("🎛️ Správa funkcií")
    
    available_features = user_db.get_available_features()
    current_features = user_data.get('features', {})
    
    st.info("🔧 **Funkcie:** Zapnite/vypnite špecifické funkcie pre tohto používateľa")
    
    new_features = {}
    
    for feature_id, feature_description in available_features.items():
        current_value = current_features.get(feature_id, False)
        
        new_value = st.checkbox(
            f"**{feature_description}**",
            value=current_value,
            key=f"feature_{email}_{feature_id}",
            help=f"Feature ID: {feature_id}"
        )
        
        new_features[feature_id] = new_value
    
    if st.button("💾 Uložiť funkcie", type="primary"):
        try:
            user_db.update_user(email, features=new_features)
            st.success("✅ **Funkcie boli aktualizované!**")
            
            enabled_features = [desc for fid, desc in available_features.items() if new_features.get(fid, False)]
            if enabled_features:
                st.info(f"🔧 **Zapnuté funkcie:** {', '.join(enabled_features)}")
            else:
                st.info("🔧 **Žiadne špeciálne funkcie nie sú zapnuté**")
                
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"❌ Chyba pri aktualizácii funkcií: {e}")


def show_password_change_tab(user_db, email, user_data):
    """Tab pre zmenu hesla"""
    st.subheader("🔒 Zmena hesla")
    
    with st.form("password_change_form"):
        st.info(f"🔑 **Zmena hesla pre:** {user_data.get('name', email)}")
        
        new_password = st.text_input("🔒 Nové heslo", type="password", placeholder="Minimálne 6 znakov")
        confirm_password = st.text_input("🔒 Potvrďte heslo", type="password", placeholder="Zopakujte nové heslo")
        
        if st.form_submit_button("🔑 Zmeniť heslo", type="primary"):
            if not new_password:
                st.error("❌ Heslo nemôže byť prázdne!")
            elif len(new_password) < 6:
                st.error("❌ Heslo musí mať aspoň 6 znakov!")
            elif new_password != confirm_password:
                st.error("❌ Heslá sa nezhodujú!")
            else:
                try:
                    if user_db.reset_user_password(email, new_password):
                        st.success("✅ **Heslo bolo úspešne zmenené!**")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Chyba pri zmene hesla!")
                except Exception as e:
                    st.error(f"❌ Chyba pri zmene hesla: {e}")


def show_account_management_tab(user_db, email, user_data):
    """Tab pre správu účtu (deaktivácia, mazanie)"""
    st.subheader("🗑️ Správa účtu")
    
    # Deaktivácia/aktivácia účtu
    st.markdown("### ⏸️ Aktivácia/Deaktivácia účtu")
    current_status = user_data.get('active', True)
    
    col1, col2 = st.columns(2)
    with col1:
        if current_status:
            if st.button("⏸️ Deaktivovať účet", type="secondary"):
                try:
                    user_db.update_user(email, active=False)
                    st.success("✅ Účet bol deaktivovaný!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Chyba pri deaktivácii: {e}")
        else:
            if st.button("▶️ Aktivovať účet", type="primary"):
                try:
                    user_db.update_user(email, active=True)
                    st.success("✅ Účet bol aktivovaný!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Chyba pri aktivácii: {e}")
    
    with col2:
        status_text = "✅ Aktívny" if current_status else "❌ Neaktívny"
        st.info(f"**Aktuálny stav:** {status_text}")
    
    st.divider()
    
    # Mazanie účtu
    st.markdown("### 🗑️ Zmazanie účtu")
    st.warning("⚠️ **Pozor!** Zmazanie účtu je nevratná operácia.")
    
    with st.expander("🔓 Zmazať účet", expanded=False):
        st.error("⚠️ **NEBEZPEČNÁ OPERÁCIA**")
        st.markdown("Zmazanie účtu:")
        st.markdown("- ❌ **Nevratne** zmaže všetky údaje používateľa")
        st.markdown("- ❌ Používateľ sa **nebude môcť prihlásiť**")
        st.markdown("- ❌ **Stratia sa všetky nastavenia** a oprávnenia")
        
        confirm_text = st.text_input(
            f"🔑 Pre potvrdenie napíšte: **{user_data.get('name', email)}**",
            placeholder=f"Napíšte: {user_data.get('name', email)}"
        )
        
        if confirm_text == user_data.get('name', email):
            if st.button("🗑️ DEFINITÍVNE ZMAZAŤ ÚČET", type="primary"):
                try:
                    if user_db.delete_user(email):
                        st.success(f"✅ Účet {user_data.get('name', email)} bol zmazaný!")
                        time.sleep(2)
                        st.session_state.user_mgmt_mode = "overview"
                        st.session_state.selected_user_email = None
                        st.rerun()
                    else:
                        st.error("❌ Chyba pri mazaní účtu!")
                except Exception as e:
                    st.error(f"❌ Chyba pri mazaní: {e}")
        else:
            st.button("🗑️ DEFINITÍVNE ZMAZAŤ ÚČET", disabled=True, help="Najprv potvrďte meno používateľa")
