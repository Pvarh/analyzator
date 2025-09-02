import logging
import traceback
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import streamlit as st


class ErrorHandler:
    """Centralizovaný error handler pre aplikáciu"""
    
    def __init__(self):
        self.setup_logging()
        self.error_log_file = "logs/errors.json"
        self.ensure_log_directory()
    
    def setup_logging(self):
        """Nastaví logging konfiguráciu"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/app.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def ensure_log_directory(self):
        """Zabezpečí že log adresár existuje"""
        Path("logs").mkdir(exist_ok=True)
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None, user_email: str = None):
        """Zaloguje chybu do súboru a databázy"""
        try:
            # Získaj informácie o chybe
            error_info = {
                "timestamp": datetime.now().isoformat(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc(),
                "user_email": user_email or self.get_current_user_email(),
                "context": context or {},
                "session_state": self.get_safe_session_state()
            }
            
            # Zapis do JSON logu
            self.write_error_to_json(error_info)
            
            # Zapis do štandardného logu
            self.logger.error(f"Error: {error_info['error_type']} - {error_info['error_message']}")
            
            return error_info
            
        except Exception as logging_error:
            # Fallback ak sa nepodarí logovať
            print(f"ERROR LOGGING FAILED: {logging_error}")
            print(f"ORIGINAL ERROR: {error}")
    
    def write_error_to_json(self, error_info: Dict[str, Any]):
        """Zapíše chybu do JSON súboru"""
        try:
            # Načítaj existujúce chyby
            if os.path.exists(self.error_log_file):
                with open(self.error_log_file, 'r', encoding='utf-8') as f:
                    errors = json.load(f)
            else:
                errors = []
            
            # Pridaj novú chybu
            errors.append(error_info)
            
            # Zachovaj len posledných 1000 chýb
            if len(errors) > 1000:
                errors = errors[-1000:]
            
            # Zapis späť
            with open(self.error_log_file, 'w', encoding='utf-8') as f:
                json.dump(errors, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to write error to JSON: {e}")
    
    def get_current_user_email(self) -> Optional[str]:
        """Bezpečne získa email aktuálneho používateľa"""
        try:
            if hasattr(st, 'session_state') and hasattr(st.session_state, 'authenticated_user'):
                user = st.session_state.authenticated_user
                if user and isinstance(user, dict):
                    return user.get('email')
        except:
            pass
        return None
    
    def get_safe_session_state(self) -> Dict[str, Any]:
        """Bezpečne získa relevantné session state informácie"""
        try:
            if not hasattr(st, 'session_state'):
                return {}
            
            safe_state = {}
            
            # Bezpečné kľúče ktoré môžeme logovať
            safe_keys = [
                'current_page', 
                'selected_employee',
                'include_terminated_employees',
                'authenticated_user'
            ]
            
            for key in safe_keys:
                if hasattr(st.session_state, key):
                    value = getattr(st.session_state, key)
                    # Pre authenticated_user zobraz len email, nie celé dáta
                    if key == 'authenticated_user' and isinstance(value, dict):
                        safe_state[key] = {'email': value.get('email', 'unknown')}
                    else:
                        safe_state[key] = value
            
            return safe_state
            
        except Exception:
            return {"error": "Failed to get session state"}
    
    def get_recent_errors(self, limit: int = 50) -> list:
        """Získa nedávne chyby pre admin panel"""
        try:
            if not os.path.exists(self.error_log_file):
                return []
            
            with open(self.error_log_file, 'r', encoding='utf-8') as f:
                errors = json.load(f)
            
            # Vráť najnovšie chyby
            return sorted(errors, key=lambda x: x['timestamp'], reverse=True)[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get recent errors: {e}")
            return []
    
    def clear_old_errors(self, days_to_keep: int = 30):
        """Vymaže staré chyby"""
        try:
            if not os.path.exists(self.error_log_file):
                return
            
            with open(self.error_log_file, 'r', encoding='utf-8') as f:
                errors = json.load(f)
            
            # Vypočítaj dátum cutoff
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Filtruj chyby
            filtered_errors = [
                error for error in errors
                if datetime.fromisoformat(error['timestamp']) > cutoff_date
            ]
            
            # Zapis späť
            with open(self.error_log_file, 'w', encoding='utf-8') as f:
                json.dump(filtered_errors, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Cleaned {len(errors) - len(filtered_errors)} old errors")
            
        except Exception as e:
            self.logger.error(f"Failed to clean old errors: {e}")


def handle_error(func):
    """Dekorátor pre automatické error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler = ErrorHandler()
            error_info = error_handler.log_error(
                error=e,
                context={
                    "function": func.__name__,
                    "args": str(args)[:200],  # Obmedzené pre bezpečnosť
                    "kwargs": str(kwargs)[:200]
                }
            )
            
            # Zobraz používateľovi priateľskú chybu
            if hasattr(st, 'error'):
                st.error("❌ Nastala chyba. Bola automaticky zalogovaná.")
                
                # Pre adminov zobraz viac detailov
                try:
                    from auth.auth import is_admin
                    if is_admin():
                        with st.expander("🔧 Detaily chyby (len pre adminov)"):
                            st.code(f"Error: {error_info['error_type']}")
                            st.code(f"Message: {error_info['error_message']}")
                            st.code(f"Timestamp: {error_info['timestamp']}")
                except:
                    pass
            
            # Re-raise error pre debugging
            raise e
    
    return wrapper


# Globálna inštancia
error_handler = ErrorHandler()


def log_error(error: Exception, context: Dict[str, Any] = None, user_email: str = None):
    """Jednoduchá funkcia pre logovanie chýb"""
    return error_handler.log_error(error, context, user_email)


def get_recent_errors(limit: int = 50) -> list:
    """Získa nedávne chyby"""
    return error_handler.get_recent_errors(limit)


def clear_old_errors(days_to_keep: int = 30):
    """Vymaže staré chyby"""
    return error_handler.clear_old_errors(days_to_keep)
