import streamlit as st
from auth.users_db import UserDatabase
from typing import Optional, Dict
import hashlib
import json
import os
import secrets
import uuid
import logging
from datetime import datetime, timedelta
from core.activity_logger import activity_logger

logger = logging.getLogger(__name__)

# Súbor pre uloženie persistent sessions
SESSIONS_FILE = "auth/sessions.json"

def verify_current_session():
    """Overí či je aktuálne prihlásenie stále platné"""
    browser_id = get_browser_id()
    
    saved_sessions_file = os.path.join(os.path.dirname(__file__), 'saved_sessions.json')
    if not os.path.exists(saved_sessions_file):
        return False
    
    try:
        with open(saved_sessions_file, 'r') as f:
            saved_sessions = json.load(f)
        
        # Skontroluj či session stále existuje a je platná
        if browser_id in saved_sessions:
            session_data = saved_sessions[browser_id]
            expire_time = datetime.fromisoformat(session_data['expires_at'])
            
            if expire_time > datetime.now():
                return True
            else:
                # Session vypršala, odstráň ju
                del saved_sessions[browser_id]
                with open(saved_sessions_file, 'w') as f:
                    json.dump(saved_sessions, f)
                # Odhláš používateľa
                st.session_state.authenticated_user = None
                return False
        
    except Exception as e:
        logger.error(f"Error verifying session: {e}")
    
    return False


def init_auth():
    """Inicializuje autentifikačný systém"""
    if 'user_db' not in st.session_state:
        st.session_state.user_db = UserDatabase()
    
    if 'authenticated_user' not in st.session_state:
        st.session_state.authenticated_user = None
    
    # VŽDY sa pokús načítať uložené prihlásenie (dôležité pre refresh)
    if not is_authenticated():
        load_saved_login()
    else:
        # Aj keď je používateľ prihlásený, skontroluj či session stále platí
        verify_current_session()

def get_browser_id():
    """Vytvorí skutočne jedinečný ID pre prehliadač/session ktorý prežije refresh"""
    if 'browser_id' not in st.session_state:
        # Pokús sa načítať z URL query parameters (hack pre persistence)
        query_params = st.query_params
        stored_browser_id = query_params.get('browser_id', None)
        
        if stored_browser_id and len(stored_browser_id) == 32:
            # Validuj že browser_id vyzerá správne (32 hex znakov)
            try:
                int(stored_browser_id, 16)
                st.session_state.browser_id = stored_browser_id
            except ValueError:
                stored_browser_id = None
        
        if not stored_browser_id:
            # Vytvor skutočne náhodný ID pre tento konkrétny session
            unique_id = str(uuid.uuid4())
            timestamp = str(datetime.now().timestamp())
            random_part = secrets.token_hex(8)
            
            # Kombinuj všetko pre maximálnu jedinečnosť
            combined = f"{unique_id}-{timestamp}-{random_part}"
            browser_id = hashlib.sha256(combined.encode()).hexdigest()[:32]
            
            st.session_state.browser_id = browser_id
            
            # Nastav query parameter pre persistence cez refresh
            st.query_params['browser_id'] = browser_id
    
    return st.session_state.browser_id

def load_sessions() -> Dict:
    """Načíta sessions zo súboru"""
    try:
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_sessions(sessions: Dict) -> bool:
    """Uloží sessions do súboru"""
    try:
        os.makedirs(os.path.dirname(SESSIONS_FILE), exist_ok=True)
        with open(SESSIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

def clean_expired_sessions():
    """Vyčistí expired sessions"""
    sessions = load_sessions()
    now = datetime.now()
    
    expired_sessions = []
    for session_id, session_data in sessions.items():
        try:
            expires_str = session_data.get('expires', '')
            if expires_str:
                expires = datetime.fromisoformat(expires_str)
                if now > expires:
                    expired_sessions.append(session_id)
        except Exception:
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del sessions[session_id]
    
    if expired_sessions:
        save_sessions(sessions)

def save_login(user_data: Dict, remember_me: bool = False):
    """Uloží prihlasovacie údaje ak je zvolené 'zostať prihlásený'"""
    if not remember_me:
        return
    
    try:
        browser_id = get_browser_id()
        sessions = load_sessions()
        
        # Vyčisti expired sessions
        clean_expired_sessions()
        
        # Vytvor nový session s dodatočnými údajmi pre lepšiu identifikáciu
        expires = datetime.now() + timedelta(days=30)  # Platnosť 30 dní
        session_data = {
            'user': {
                'email': user_data['email'],
                'name': user_data['name'],
                'role': user_data['role'],
                'cities': user_data['cities']
            },
            'created': datetime.now().isoformat(),
            'expires': expires.isoformat(),
            'browser_id': browser_id,
            'session_key': secrets.token_hex(16)  # Dodatočný bezpečnostný kľúč
        }
        
        sessions[browser_id] = session_data
        
        if save_sessions(sessions):
            st.session_state['persistent_session_id'] = browser_id
            st.session_state['session_key'] = session_data['session_key']
            return True
        
    except Exception as e:
        st.warning(f"Nepodarilo sa uložiť prihlásenie: {e}")
    
    return False

def load_saved_login():
    """Načíta uložené prihlásenie"""
    try:
        browser_id = get_browser_id()
        sessions = load_sessions()
        
        # Vyčisti expired sessions
        clean_expired_sessions()
        
        # Hľadaj session pre tento prehliadač
        session_data = sessions.get(browser_id)
        if not session_data:
            return False
        
        # Skontroluj expiry
        expires_str = session_data.get('expires', '')
        if expires_str:
            expires = datetime.fromisoformat(expires_str)
            if datetime.now() > expires:
                # Session expirovala, vymaž ju
                del sessions[browser_id]
                save_sessions(sessions)
                return False
        
        # Dodatočná kontrola session key pre bezpečnosť
        stored_session_key = session_data.get('session_key', '')
        current_session_key = st.session_state.get('session_key', '')
        
        # Ak už máme session key a nezhoduje sa, nevykonaj auto-login
        if current_session_key and current_session_key != stored_session_key:
            return False
        
        # Overí či používateľ stále existuje v databáze
        user_data = session_data.get('user', {})
        email = user_data.get('email', '')
        
        if email:
            # Inicializuj user_db ak neexistuje
            if 'user_db' not in st.session_state:
                st.session_state.user_db = UserDatabase()
            
            db_user = st.session_state.user_db.users.get(email)
            if db_user and db_user.get('active', True):
                st.session_state.authenticated_user = user_data
                st.session_state['persistent_session_id'] = browser_id
                st.session_state['session_key'] = stored_session_key
                return True
        
        # Ak user neexistuje alebo nie je aktívny, vymaž session
        del sessions[browser_id]
        save_sessions(sessions)
        
    except Exception:
        pass
    
    return False

def clear_saved_login():
    """Vymaže uložené prihlásenie"""
    try:
        browser_id = get_browser_id()
        sessions = load_sessions()
        
        if browser_id in sessions:
            del sessions[browser_id]
            save_sessions(sessions)
        
        if 'persistent_session_id' in st.session_state:
            del st.session_state['persistent_session_id']
        
        if 'session_key' in st.session_state:
            del st.session_state['session_key']
        
    except Exception:
        pass

def is_authenticated() -> bool:
    """Skontroluje či je používateľ prihlásený"""
    return st.session_state.get('authenticated_user') is not None

def get_current_user() -> Optional[Dict]:
    """Vráti aktuálneho prihláseného používateľa"""
    return st.session_state.get('authenticated_user')

def is_admin() -> bool:
    """Skontroluje či je aktuálny používateľ admin"""
    user = get_current_user()
    return user and user.get('role') == 'admin'

def can_access_city(city: str) -> bool:
    """Skontroluje či používateľ má prístup k mestu"""
    user = get_current_user()
    if not user:
        return False
    
    cities = user.get('cities', [])
    return 'all' in cities or city.lower() in [c.lower() for c in cities]

def get_user_cities() -> list:
    """Vráti mestá ku ktorým má používateľ prístup"""
    user = get_current_user()
    if not user:
        return []
    
    cities = user.get('cities', [])
    if 'all' in cities:
        return ["praha", "brno", "zlin", "vizovice"]
    
    return cities

def filter_data_by_user_access(df):
    """Filtruje dáta podľa oprávnení používateľa"""
    user = get_current_user()
    if not user:
        return df.iloc[0:0]  # Prázdny DataFrame
    
    cities = user.get('cities', [])
    if 'all' in cities:
        return df  # Admin vidí všetko
    
    # Filtruj podľa miest
    if 'workplace' in df.columns:
        return df[df['workplace'].str.lower().isin([c.lower() for c in cities])]
    
    return df

def logout():
    """Odhlási používateľa"""
    st.session_state.authenticated_user = None
    clear_saved_login()  # Vymaž uložené prihlásenie
    st.rerun()

def show_login_page():
    """Zobrazí prihlasovaciu stránku"""
    st.title("🔐 Prihlásenie do systému")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Sykora Dashboard")
        st.markdown("---")
        
        with st.form("login_form"):
            email = st.text_input(
                "📧 Email", 
                placeholder="meno@sykora.eu",
                help="Používajte iba @sykora.eu emailové adresy"
            )
            password = st.text_input(
                "🔑 Heslo", 
                type="password",
                placeholder="Zadajte heslo"
            )
            
            # ✅ NOVÝ: Checkbox pre "zostať prihlásený"
            remember_me = st.checkbox(
                "🔒 Zostať prihlásený", 
                value=False,
                help="Zapamätá si vaše prihlásenie pre ďalšie návštevy"
            )
            
            submitted = st.form_submit_button("🚀 Prihlásiť sa", use_container_width=True)
            
            if submitted:
                if not email or not password:
                    st.error("⚠️ Vyplňte všetky polia")
                elif not email.endswith("@sykora.eu"):
                    st.error("❌ Povolené sú iba @sykora.eu emailové adresy")
                else:
                    user = st.session_state.user_db.authenticate(email, password)
                    if user:
                        st.session_state.authenticated_user = user
                        
                        # ✅ NOVÉ: Ulož prihlásenie ak je zvolené
                        if remember_me:
                            save_login(user, remember_me=True)
                            st.success("✅ Úspešne prihlásený! Prihlásenie bude zapamätané.")
                        else:
                            st.success("✅ Úspešne prihlásený!")
                        
                        st.rerun()
                    else:
                        st.error("❌ Neplatné prihlasovacie údaje")
        
        st.markdown("---")
        st.markdown("**💡 Potrebujete prístup?**")
        st.info("Kontaktujte administrátora pre vytvorenie účtu")
        
        # ✅ NOVÝ: Info o uloženom prihlásení
        if st.session_state.get('persistent_session_id'):
            st.markdown("---")
            st.markdown("**🔒 Uložené prihlásenie**")
            st.info("V systéme je uložené prihlásenie. Pri ďalšej návšteve budete automaticky prihlásený.")
            
            if st.button("🗑️ Vymazať uložené prihlásenie", help="Vymaže zapamätané prihlásenie zo systému"):
                clear_saved_login()
                st.success("✅ Uložené prihlásenie bolo vymazané")
                st.rerun()

def show_user_info():
    """Zobrazí info o aktuálnom používateľovi"""
    user = get_current_user()
    if not user:
        return
    
    with st.sidebar:
        st.markdown("### 👤 Používateľ")
        st.write(f"**{user['name']}**")
        st.write(f"📧 {user['email']}")
        st.write(f"🏢 Role: {user['role'].title()}")
        
        if user['role'] == 'admin':
            st.write("🌍 **Prístup**: Všetky mestá")
        else:
            cities = ", ".join([c.title() for c in user['cities']])
            st.write(f"🏙️ **Mestá**: {cities}")
        
        # ✅ NOVÝ: Info o uloženom prihlásení
        if st.session_state.get('persistent_session_id'):
            st.write("🔒 **Prihlásenie zapamätané**")
        
        if st.button("🚪 Odhlásiť sa", use_container_width=True):
            logout()


def has_feature_access(feature: str) -> bool:
    """Kontroluje, či má aktuálny používateľ prístup k funkcii"""
    current_user = get_current_user()
    if not current_user:
        return False
    
    user_db = st.session_state.get('user_db')
    if not user_db:
        # Inicializuj user_db ak neexistuje
        st.session_state.user_db = UserDatabase()
        user_db = st.session_state.user_db
    
    # Dodatočná kontrola či má user_db has_feature metódu
    if not hasattr(user_db, 'has_feature'):
        return False
    
    return user_db.has_feature(current_user['email'], feature)


def get_user_features(email: str = None) -> Dict[str, bool]:
    """Získa funkcie pre používateľa"""
    if email is None:
        current_user = get_current_user()
        if not current_user:
            return {}
        email = current_user['email']
    
    user_db = st.session_state.get('user_db')
    if not user_db:
        # Inicializuj user_db ak neexistuje
        st.session_state.user_db = UserDatabase()
        user_db = st.session_state.user_db
    
    if not hasattr(user_db, 'get_user_features'):
        return {}
    
    return user_db.get_user_features(email)


def update_user_features(email: str, features: Dict[str, bool]) -> bool:
    """Aktualizuje funkcie pre používateľa"""
    user_db = st.session_state.get('user_db')
    if not user_db:
        # Inicializuj user_db ak neexistuje
        st.session_state.user_db = UserDatabase()
        user_db = st.session_state.user_db
    
    if not hasattr(user_db, 'update_user_features'):
        return False
    
    return user_db.update_user_features(email, features)


def get_available_features() -> Dict[str, str]:
    """Získa dostupné funkcie s popismi"""
    user_db = st.session_state.get('user_db')
    if not user_db:
        # Inicializuj user_db ak neexistuje
        st.session_state.user_db = UserDatabase()
        user_db = st.session_state.user_db
    
    if not hasattr(user_db, 'get_available_features'):
        return {}
    
    return user_db.get_available_features()


def log_page_activity(page_name: str):
    """Zaloguje návštevu stránky pre aktuálneho používateľa"""
    try:
        current_user = get_current_user()
        if current_user:
            activity_logger.log_page_visit(
                user_email=current_user['email'],
                user_name=current_user['name'],
                page=page_name,
                user_role=current_user.get('role', 'manager')
            )
    except Exception as e:
        # Tichý fail - activity logging nemá ovplyvniť aplikáciu
        pass


def get_activity_stats(date: str = None) -> Dict:
    """Získa štatistiky aktivity pre špecifický deň"""
    try:
        return activity_logger.get_daily_activity(date)
    except Exception:
        return {}


def get_user_activity_stats(user_email: str = None, days: int = 7) -> Dict:
    """Získa štatistiky aktivity pre používateľa"""
    try:
        if user_email is None:
            current_user = get_current_user()
            if current_user:
                user_email = current_user['email']
            else:
                return {}
        
        return activity_logger.get_user_activity(user_email, days)
    except Exception:
        return {}
