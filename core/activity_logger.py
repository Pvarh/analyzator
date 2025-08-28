import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

class ActivityLogger:
    """Logger pre sledovanie aktivity používateľov"""
    
    def __init__(self, log_file="logs/activity.json"):
        self.log_file = log_file
        self.ensure_log_directory()
    
    def ensure_log_directory(self):
        """Vytvorí logs priečinok ak neexistuje"""
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
    
    def log_page_visit(self, user_email: str, user_name: str, page: str, user_role: str = "manager"):
        """Zaloguje návštevu stránky"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_email": user_email,
                "user_name": user_name,
                "user_role": user_role,
                "page": page,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M:%S")
            }
            
            # Načítanie existujúcich logov
            logs = self.load_logs()
            logs.append(log_entry)
            
            # Uloženie logov (ponechaj len posledných 10000 záznamov)
            if len(logs) > 10000:
                logs = logs[-10000:]
            
            self.save_logs(logs)
            
        except Exception as e:
            print(f"Error logging activity: {e}")
    
    def load_logs(self) -> List[Dict]:
        """Načíta existujúce logy"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_logs(self, logs: List[Dict]):
        """Uloží logy do súboru"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving logs: {e}")
    
    def get_daily_activity(self, date: str = None) -> Dict:
        """Získa dennú aktivitu (dnes ak nie je date špecifikovaný)"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        logs = self.load_logs()
        daily_logs = [log for log in logs if log.get('date') == date]
        
        # Štatistiky
        stats = {
            "date": date,
            "total_visits": len(daily_logs),
            "unique_users": len(set(log['user_email'] for log in daily_logs)),
            "pages": {},
            "users": {},
            "hourly_activity": {}
        }
        
        # Aktivita po stránkach
        for log in daily_logs:
            page = log.get('page', 'unknown')
            stats['pages'][page] = stats['pages'].get(page, 0) + 1
        
        # Aktivita po používateľoch
        for log in daily_logs:
            user = log.get('user_name', 'Unknown')
            email = log.get('user_email', 'unknown')
            role = log.get('user_role', 'unknown')
            
            if email not in stats['users']:
                stats['users'][email] = {
                    'name': user,
                    'role': role,
                    'visits': 0,
                    'pages': []
                }
            stats['users'][email]['visits'] += 1
            stats['users'][email]['pages'].append(log.get('page', 'unknown'))
        
        # Hodinová aktivita
        for log in daily_logs:
            hour = log.get('time', '00:00:00')[:2]
            stats['hourly_activity'][hour] = stats['hourly_activity'].get(hour, 0) + 1
        
        return stats
    
    def get_user_activity(self, user_email: str, days: int = 7) -> Dict:
        """Získa aktivitu konkrétneho používateľa za posledných X dní"""
        logs = self.load_logs()
        
        # Filtruj logy pre používateľa za posledných X dní
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        user_logs = []
        for log in logs:
            try:
                log_date = datetime.fromisoformat(log['timestamp'])
                if (log['user_email'] == user_email and 
                    start_date <= log_date <= end_date):
                    user_logs.append(log)
            except:
                continue
        
        # Štatistiky používateľa
        stats = {
            "user_email": user_email,
            "period_days": days,
            "total_visits": len(user_logs),
            "pages_visited": {},
            "daily_activity": {},
            "most_active_page": None,
            "first_visit": None,
            "last_visit": None
        }
        
        if user_logs:
            # Stránky
            for log in user_logs:
                page = log.get('page', 'unknown')
                stats['pages_visited'][page] = stats['pages_visited'].get(page, 0) + 1
            
            # Najaktívnejšia stránka
            if stats['pages_visited']:
                stats['most_active_page'] = max(stats['pages_visited'].items(), key=lambda x: x[1])
            
            # Denná aktivita
            for log in user_logs:
                date = log.get('date', 'unknown')
                stats['daily_activity'][date] = stats['daily_activity'].get(date, 0) + 1
            
            # Prvá a posledná návšteva
            sorted_logs = sorted(user_logs, key=lambda x: x['timestamp'])
            stats['first_visit'] = sorted_logs[0]['timestamp']
            stats['last_visit'] = sorted_logs[-1]['timestamp']
        
        return stats
    
    def cleanup_old_logs(self, days: int = 30):
        """Vymaže logy staršie ako X dní"""
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        logs = self.load_logs()
        filtered_logs = []
        
        for log in logs:
            try:
                log_date = datetime.fromisoformat(log['timestamp'])
                if log_date >= cutoff_date:
                    filtered_logs.append(log)
            except:
                continue
        
        self.save_logs(filtered_logs)
        return len(logs) - len(filtered_logs)  # Počet vymazaných logov

# Globálna inštancia loggera
activity_logger = ActivityLogger()
