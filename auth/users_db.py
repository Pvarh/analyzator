import json
import hashlib
import os
from typing import Dict, List, Optional

class UserDatabase:
    """Databáza používateľov a ich oprávnení"""
    
    def __init__(self, db_file="auth/users.json"):
        self.db_file = db_file
        self.users = self.load_users()
        self.ensure_admin_exists()
    
    
    def load_users(self) -> Dict:
        """Načíta používateľov zo súboru"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_users(self) -> bool:
        """Uloží používateľov do súboru"""
        try:
            os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"ERROR: Cannot save users: {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        """Hashuje heslo"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def ensure_admin_exists(self):
        """Zabezpečí, že admin účet existuje"""
        admin_email = "pvarhalik@sykora.eu"
        
        if admin_email not in self.users:
            # Pri prvom vytvorení admin účtu je potrebné nastaviť heslo manuálne
            # Hash pre heslo "admin123" - musí sa zmeniť po prvom prihlásení
            default_password_hash = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"  # admin123
            
            self.users[admin_email] = {
                "password_hash": default_password_hash,
                "role": "admin",
                "cities": ["all"],  # Admin vidí všetky mestá
                "name": "Peter Varhalik",
                "active": True,
                "features": {
                    "employee_detail_top_products": True,
                    "employee_detail_product_table": True,
                    "all_features": True  # Admin má prístup ku všetkým funkciám
                }
            }
            self.save_users()
            print("⚠️  BEZPEČNOSTNÉ UPOZORNENIE: Admin účet vytvorený s default heslom 'admin123'")
            print("⚠️  OKAMŽITE ZMEŇTE HESLO PO PRVOM PRIHLÁSENÍ!")
        else:
            # Ak admin už existuje, ale nemá features, pridaj ich
            if "features" not in self.users[admin_email]:
                self.users[admin_email]["features"] = {
                    "employee_detail_top_products": True,
                    "employee_detail_product_table": True,
                    "all_features": True
                }
                self.save_users()
    
    def authenticate(self, email: str, password: str) -> Optional[Dict]:
        """Overí prihlásenie používateľa"""
        if not (email.endswith("@sykora.eu") or email.endswith("@sykorahome.cz")):
            return None
        
        if email not in self.users:
            return None
        
        user = self.users[email]
        if not user.get("active", True):
            return None
        
        password_hash = self.hash_password(password)
        if user["password_hash"] == password_hash:
            return {
                "email": email,
                "role": user["role"],
                "cities": user["cities"],
                "name": user["name"]
            }
        return None
    
    def add_user(self, email: str, password: str, role: str, cities: List[str], name: str) -> bool:
        """Pridá nového používateľa"""
        # Čistenie emailu od medzier
        email = email.strip() if email else ""
        
        # Validácie
        if not email or not (email.endswith("@sykora.eu") or email.endswith("@sykorahome.cz")):
            return False
        
        # Kontrola či email neobsahuje medzery vo vnútri
        if ' ' in email:
            return False
        
        if not password or len(password) < 1:
            return False
        
        if email in self.users:
            return False
        
        if not name or len(name.strip()) < 1:
            return False
        
        self.users[email] = {
            "password_hash": self.hash_password(password),
            "role": role,
            "cities": cities,
            "name": name,
            "active": True,
            "page_permissions": ["overview", "employee", "benchmark", "heatmap", "studio", "kpi_system"] if role == "manager" else ["overview", "employee", "benchmark", "heatmap", "studio", "kpi_system", "admin", "user_management"]
        }
        
        return self.save_users()
    
    def reset_user_password(self, email: str, new_password: str) -> bool:
        """Resetuje heslo používateľa (iba admin)"""
        if email not in self.users:
            return False
        
        self.users[email]["password_hash"] = self.hash_password(new_password)
        return self.save_users()
    
    def change_own_password(self, email: str, old_password: str, new_password: str) -> bool:
        """Umožní používateľovi zmeniť si vlastné heslo"""
        if email not in self.users:
            return False
        
        # Overenie starého hesla
        old_password_hash = self.hash_password(old_password)
        if self.users[email]["password_hash"] != old_password_hash:
            return False
        
        # Nastavenie nového hesla
        self.users[email]["password_hash"] = self.hash_password(new_password)
        return self.save_users()
    
    def get_raw_password(self, email: str) -> Optional[str]:
        """Pre bezpečnosť - nevráti plain text heslo"""
        return "[Heslo nie je dostupné - použite reset hesla]"
    
    def update_user(self, email: str, **kwargs) -> bool:
        """Aktualizuje používateľa"""
        if email not in self.users:
            return False
        
        if "password" in kwargs:
            plain_password = kwargs.pop("password")
            kwargs["password_hash"] = self.hash_password(plain_password)
            # Neukládame plain text heslo
        
        self.users[email].update(kwargs)
        self.save_users()
        return True
    
    def delete_user(self, email: str) -> bool:
        """Zmaže používateľa"""
        if email in self.users and email != "pvarhalik@sykora.eu":  # Nemôže zmazať admina
            del self.users[email]
            self.save_users()
            return True
        return False
    
    def remove_user(self, email: str) -> bool:
        """Alias pre delete_user - pre kompatibilitu s admin rozhraním"""
        return self.delete_user(email)
    
    def get_all_users(self) -> List[Dict]:
        """Vráti všetkých používateľov (bez hesiel) ako list"""
        result = []
        for email, user in self.users.items():
            result.append({
                "email": email,
                "role": user["role"],
                "cities": user["cities"],
                "name": user["name"],
                "active": user.get("active", True),
                "features": user.get("features", {})
            })
        return result
    
    def update_user_features(self, email: str, features: Dict[str, bool]) -> bool:
        """Aktualizuje funkcie pre používateľa"""
        if email not in self.users:
            return False
        
        if "features" not in self.users[email]:
            self.users[email]["features"] = {}
        
        self.users[email]["features"].update(features)
        return self.save_users()
    
    def get_user_features(self, email: str) -> Dict[str, bool]:
        """Získa funkcie pre používateľa"""
        if email not in self.users:
            return {}
        
        return self.users[email].get("features", {})
    
    def has_feature(self, email: str, feature: str) -> bool:
        """Kontroluje, či má používateľ prístup k funkcii"""
        if email not in self.users:
            return False
        
        user_features = self.users[email].get("features", {})
        
        # Admin má prístup ku všetkému
        if self.users[email].get("role") == "admin" or user_features.get("all_features", False):
            return True
        
        return user_features.get(feature, False)
    
    def get_available_features(self) -> Dict[str, str]:
        """Vráti dostupné funkcie s popismi"""
        return {
            "employee_detail_top_products": "Najpredávanejšie produkty z každej kategórie",
            "employee_detail_product_table": "Detailná tabuľka top produktov",
            "sidebar_company_statistics": "Celkové štatistiky firmy v sidebar-e",
            "studio_see_all_employees": "Studio: Zobrazí všetkých zamestnancov (nie iba z vlastných miest)",
            # Tu môžeš pridať ďalšie funkcie
        }
    
    def get_available_cities(self) -> List[str]:
        """Vráti dostupné mestá z dát"""
        return ["praha", "brno", "zlin", "vizovice"]
    
    def delete_user(self, email: str) -> bool:
        """Zmaže používateľa z databázy"""
        if email not in self.users:
            return False
        
        # Zabráň zmazaniu posledného admin účtu
        if self.users[email].get("role") == "admin":
            admin_count = sum(1 for user in self.users.values() if user.get("role") == "admin")
            if admin_count <= 1:
                raise ValueError("Nemôžete zmazať posledný admin účet!")
        
        del self.users[email]
        return self.save_users()
    
    def reset_database(self):
        """Resetuje databázu a vytvorí len admin účet"""
        self.users = {}
        self._create_admin_account()
        self.save_users()
