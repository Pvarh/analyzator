import streamlit as st
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil
from auth.users_db import UserDatabase
from auth.auth import get_current_user, is_admin, get_activity_stats, get_user_activity_stats

def show_admin_page():
    """Zobrazí administrátorskú stránku"""
    user = get_current_user()
    if not user or user.get('role') != 'admin':
        st.error("❌ Nemáte oprávnenie na túto stránku")
        return
    
    st.title("👑 Admin Panel - Kompletný systém je úspešne nasadený!")
    
    # Activity logs ako prvý tab
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Aktivita logov",
        "➕ Pridať používateľa", 
        "📋 Zoznam používateľov", 
        "🎛️ Správa funkcií", 
        "📁 Správa dát"
    ])
    
    user_db = st.session_state.user_db
    
    with tab1:
        show_activity_logs()
    
    with tab2:
        show_add_user_form(user_db)
    
    with tab3:
        show_users_list(user_db)
    
    with tab4:
        show_feature_management(user_db)
    
    with tab5:
        show_data_management()

def show_activity_logs():
    """Zobrazí activity logy manažérov"""
    st.subheader("📊 Activity Logs - Aktivita manažérov")
    
    # Výber dátumu
    selected_date = st.date_input("📅 Vyberte dátum:", datetime.now())
    date_str = selected_date.strftime("%Y-%m-%d")
    
    # Získanie štatistík
    stats = get_activity_stats(date_str)
    
    if stats.get('total_visits', 0) == 0:
        st.info(f"📊 Žiadna aktivita zaznamenaná pre {date_str}")
        st.info("💡 Aktivita sa zaznamenáva len keď sa používatelia prihlasia a používajú aplikáciu")
        return
    
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

def show_add_user_form(user_db):
    """Formulár na pridanie nového používateľa"""
    st.subheader("Pridať nového používateľa")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("👤 Meno a priezvisko", placeholder="Jan Novák")
            email = st.text_input("📧 Email", placeholder="jan.novak@sykora.eu")
        
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
            if not all([name, email, password]):
                st.error("❌ Všetky polia sú povinné!")
            elif role == "manager" and not cities:
                st.error("❌ Pre manažéra musíte vybrať aspoň jedno mesto!")
            else:
                success = user_db.add_user(email, password, role, cities, name)
                if success:
                    st.success(f"✅ Používateľ {name} bol úspešne pridaný!")
                    st.rerun()
                else:
                    st.error("❌ Používateľ sa nepodarilo pridať (možno už existuje)")

def show_users_list(user_db):
    """Zoznam všetkých používateľov"""
    st.subheader("📋 Zoznam používateľov")
    
    users = user_db.get_all_users()
    
    if not users:
        st.info("👤 Žiadni používatelia v systéme")
        return
    
    st.info(f"👥 Celkom používateľov: {len(users)}")
    
    # Zoznam používateľov
    for user in users:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                role_icon = "👑" if user['role'] == 'admin' else "👔"
                st.markdown(f"**{role_icon} {user['name']}**")
                st.markdown(f"📧 {user['email']}")
            
            with col2:
                if user['role'] == 'admin':
                    st.markdown("🌍 **Prístup**: Všetky mestá")
                else:
                    cities_text = ", ".join([c.title() for c in user['cities']])
                    st.markdown(f"🏙️ **Mestá**: {cities_text}")
            
            with col3:
                if user['email'] != "pvarhalik@sykora.eu":  # Nemôže zmazať seba
                    if st.button("🗑️", key=f"delete_{user['email']}", help="Zmazať používateľa"):
                        if user_db.remove_user(user['email']):
                            st.success(f"✅ Používateľ {user['name']} bol zmazaný!")
                            st.rerun()
                        else:
                            st.error("❌ Chyba pri mazaní používateľa")
        
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
