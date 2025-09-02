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
        admin_password = "01011970"
        
        if admin_email not in self.users:
            self.users[admin_email] = {
                "password_hash": self.hash_password(admin_password),
                "password_plain": admin_password,  # Pre admin prístup
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
        else:
            # Ak admin už existuje, ale nemá features, pridaj ich
            if "features" not in self.users[admin_email]:
                self.users[admin_email]["features"] = {
                    "employee_detail_top_products": True,
                    "employee_detail_product_table": True,
                    "all_features": True
                }
            
            # Zabezpečí plain text heslo pre admina
            if "password_plain" not in self.users[admin_email]:
                self.users[admin_email]["password_plain"] = admin_password
                
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
        # Validácie
        if not email or not (email.endswith("@sykora.eu") or email.endswith("@sykorahome.cz")):
            return False
        
        if not password or len(password) < 1:
            return False
        
        if email in self.users:
            return False
        
        if not name or len(name.strip()) < 1:
            return False
        
        self.users[email] = {
            "password_hash": self.hash_password(password),
            "password_plain": password,  # Pre admin prístup (🔒 zabezpečené)
            "role": role,
            "cities": cities,
            "name": name,
            "active": True
        }
        
        return self.save_users()
    
    def get_raw_password(self, email: str) -> Optional[str]:
        """Získa plain text heslo (iba pre admin účely)"""
        if email not in self.users:
            return None
        
        # Vráti plain text heslo ak existuje
        return self.users[email].get("password_plain", "[Nedostupné - starý záznam]")
    
    def ensure_admin_has_plain_password(self):
        """Zabezpečí, že admin má plain text heslo"""
        admin_email = "pvarhalik@sykora.eu"
        if admin_email in self.users and "password_plain" not in self.users[admin_email]:
            # Ak admin nemá plain text heslo, pridaj default
            self.users[admin_email]["password_plain"] = "01011970"
            self.save_users()
    
    def update_user(self, email: str, **kwargs) -> bool:
        """Aktualizuje používateľa"""
        if email not in self.users:
            return False
        
        if "password" in kwargs:
            plain_password = kwargs.pop("password")
            kwargs["password_hash"] = self.hash_password(plain_password)
            kwargs["password_plain"] = plain_password  # Uloží aj plain text
        
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
            # Tu môžeš pridať ďalšie funkcie
        }
    
    def get_available_cities(self) -> List[str]:
        """Vráti dostupné mestá z dát"""
        return ["praha", "brno", "zlin", "vizovice"]
    
    def reset_database(self):
        """Resetuje databázu a vytvorí len admin účet"""
        self.users = {}
        self._create_admin_account()
        self.save_users()
