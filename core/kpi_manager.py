"""
KPI Manager - Systém pre individuálne ciele a hodnotenie výkonnosti
Modulárny dizajn pripravený na rozšírenia o ďalšie metriky
"""

import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path


class KPIManager:
    """Hlavný manager pre KPI systém"""
    
    def __init__(self):
        self.data_dir = Path("data/kpi")
        self.data_dir.mkdir(exist_ok=True)
        
        self.goals_file = self.data_dir / "goals.json"
        self.performance_file = self.data_dir / "performance.json" 
        self.metrics_config_file = self.data_dir / "metrics_config.json"
        
        self._ensure_files_exist()
        
    def _ensure_files_exist(self):
        """Vytvorí základne súbory ak neexistujú"""
        if not self.goals_file.exists():
            self._create_default_goals()
            
        if not self.performance_file.exists():
            self._create_default_performance()
            
        if not self.metrics_config_file.exists():
            self._create_default_metrics_config()
    
    def _create_default_goals(self):
        """Vytvorí defaultné ciele"""
        default_goals = {
            "global_targets": {
                "2025": {
                    "q1": {"sales": 2000000, "activity_score": 80},
                    "q2": {"sales": 2500000, "activity_score": 85},
                    "q3": {"sales": 2200000, "activity_score": 85},
                    "q4": {"sales": 3000000, "activity_score": 90}
                }
            },
            "individual_targets": {},
            "city_multipliers": {
                "praha": 1.0,
                "brno": 0.8,
                "ostrava": 0.7,
                "bratislava": 1.2
            }
        }
        
        with open(self.goals_file, 'w', encoding='utf-8') as f:
            json.dump(default_goals, f, indent=2, ensure_ascii=False)
    
    def _create_default_performance(self):
        """Vytvorí defaultné performance súbory"""
        default_performance = {
            "last_updated": datetime.now().isoformat(),
            "employees": {}
        }
        
        with open(self.performance_file, 'w', encoding='utf-8') as f:
            json.dump(default_performance, f, indent=2, ensure_ascii=False)
    
    def _create_default_metrics_config(self):
        """Vytvorí konfiguráciu metrík - pripravené na rozšírenia"""
        metrics_config = {
            "active_metrics": {
                "sales": {
                    "name": "Predaj",
                    "weight": 70,
                    "unit": "Kč",
                    "data_source": "excel",
                    "enabled": True,
                    "icon": "💰"
                },
                "activity": {
                    "name": "Aktivita v systéme",
                    "weight": 20,
                    "unit": "body",
                    "data_source": "internal",
                    "enabled": True,
                    "icon": "📊"
                },
                "efficiency": {
                    "name": "Efektivita",
                    "weight": 10,
                    "unit": "%",
                    "data_source": "external",
                    "enabled": False,
                    "icon": "⚡",
                    "note": "Pripravené na budúce napojenie"
                },
                "customer_satisfaction": {
                    "name": "Spokojnosť klientov",
                    "weight": 0,
                    "unit": "body",
                    "data_source": "external", 
                    "enabled": False,
                    "icon": "😊",
                    "note": "Pripravené na budúce napojenie"
                }
            },
            "scoring": {
                "excellent": {"min": 90, "color": "#28a745", "emoji": "🏆"},
                "good": {"min": 75, "color": "#ffc107", "emoji": "🥉"},
                "average": {"min": 50, "color": "#17a2b8", "emoji": "⚠️"},
                "poor": {"min": 0, "color": "#dc3545", "emoji": "❌"}
            }
        }
        
        with open(self.metrics_config_file, 'w', encoding='utf-8') as f:
            json.dump(metrics_config, f, indent=2, ensure_ascii=False)
    
    def load_goals(self) -> Dict:
        """Načíta ciele"""
        with open(self.goals_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_goals(self, goals: Dict):
        """Uloží ciele"""
        with open(self.goals_file, 'w', encoding='utf-8') as f:
            json.dump(goals, f, indent=2, ensure_ascii=False)
    
    def load_performance(self) -> Dict:
        """Načíta performance dáta"""
        with open(self.performance_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_performance(self, performance: Dict):
        """Uloží performance dáta"""
        performance['last_updated'] = datetime.now().isoformat()
        with open(self.performance_file, 'w', encoding='utf-8') as f:
            json.dump(performance, f, indent=2, ensure_ascii=False)
    
    def load_metrics_config(self) -> Dict:
        """Načíta konfiguráciu metrík"""
        with open(self.metrics_config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_employee_kpis(self, employee_email: str, period: str = "current") -> Dict:
        """Získa KPI pre konkrétneho zamestnanca"""
        try:
            goals = self.load_goals()
            performance = self.load_performance()
            metrics_config = self.load_metrics_config()
            
            # Základné info o zamestnanovi
            employee_data = performance.get('employees', {}).get(employee_email, {})
            
            # Výpočet aktuálneho KPI
            current_period = self._get_current_period()
            employee_kpis = self._calculate_employee_kpis(
                employee_email, current_period, goals, performance, metrics_config
            )
            
            return employee_kpis
            
        except Exception as e:
            return {"error": f"Chyba pri načítavaní KPI: {e}"}
    
    def get_city_kpis(self, city: str, period: str = "current") -> List[Dict]:
        """Získa KPI pre všetkých zamestnancov z daného mesta"""
        try:
            # Načítaj dáta zamestnancov z analyzéra
            from core.analyzer import Analyzer
            analyzer = Analyzer()
            
            # Získaj zamestnancov z mesta
            city_employees = []
            all_employees = analyzer.get_all_employees_summary()
            
            for emp in all_employees:
                emp_city = emp.get('workplace', '').lower()
                if emp_city == city.lower():
                    employee_email = emp.get('email', '')
                    if employee_email:
                        emp_kpis = self.get_employee_kpis(employee_email, period)
                        emp_kpis['employee_info'] = emp
                        city_employees.append(emp_kpis)
            
            return city_employees
            
        except Exception as e:
            return [{"error": f"Chyba pri načítavaní KPI pre mesto: {e}"}]
    
    def _get_current_period(self) -> str:
        """Určí aktuálne obdobie"""
        now = datetime.now()
        month = now.month
        
        if month <= 3:
            return "q1"
        elif month <= 6:
            return "q2"
        elif month <= 9:
            return "q3"
        else:
            return "q4"
    
    def _calculate_employee_kpis(self, email: str, period: str, goals: Dict, 
                                performance: Dict, metrics_config: Dict) -> Dict:
        """Vypočíta KPI pre zamestnanca"""
        
        # Načítaj predajné dáta
        sales_data = self._get_sales_data(email, period)
        activity_data = self._get_activity_data(email, period)
        
        # Získaj ciele
        employee_goals = self._get_employee_goals(email, period, goals)
        
        # Vypočítaj metriky
        kpis = {
            'email': email,
            'period': period,
            'last_updated': datetime.now().isoformat(),
            'goals': employee_goals,
            'actuals': {},
            'progress': {},
            'overall_score': 0
        }
        
        total_weight = 0
        weighted_score = 0
        
        # Sales KPI
        if metrics_config['active_metrics']['sales']['enabled']:
            sales_target = employee_goals.get('sales', 0)
            sales_actual = sales_data.get('total', 0)
            sales_progress = (sales_actual / sales_target * 100) if sales_target > 0 else 0
            
            kpis['actuals']['sales'] = sales_actual
            kpis['progress']['sales'] = min(sales_progress, 150)  # Cap na 150%
            
            weight = metrics_config['active_metrics']['sales']['weight']
            weighted_score += min(sales_progress, 150) * weight / 100
            total_weight += weight
        
        # Activity KPI  
        if metrics_config['active_metrics']['activity']['enabled']:
            activity_target = employee_goals.get('activity_score', 80)
            activity_actual = activity_data.get('score', 0)
            activity_progress = (activity_actual / activity_target * 100) if activity_target > 0 else 0
            
            kpis['actuals']['activity'] = activity_actual
            kpis['progress']['activity'] = min(activity_progress, 150)
            
            weight = metrics_config['active_metrics']['activity']['weight']
            weighted_score += min(activity_progress, 150) * weight / 100
            total_weight += weight
        
        # Celkové skóre
        kpis['overall_score'] = weighted_score / total_weight if total_weight > 0 else 0
        kpis['performance_level'] = self._get_performance_level(kpis['overall_score'], metrics_config)
        
        return kpis
    
    def _get_sales_data(self, email: str, period: str) -> Dict:
        """Získa predajné dáta pre zamestnanca"""
        try:
            # Načítaj Excel súbor s predajmi
            excel_path = Path("data/raw/Prodej-2025.xlsx")
            if not excel_path.exists():
                return {'total': 0, 'monthly': {}}
            
            df = pd.read_excel(excel_path)
            
            # Nájdi riadok pre zamestnanca (match podľa mena v email)
            employee_name = email.split('@')[0].replace('.', ' ').title()
            
            # Pokús sa nájsť zamestnanca rôznymi spôsobmi
            employee_row = None
            for idx, row in df.iterrows():
                user = str(row.get('user', '')).lower()
                if employee_name.lower() in user or email.lower() in user:
                    employee_row = row
                    break
            
            if employee_row is None:
                return {'total': 0, 'monthly': {}}
            
            # Mapovanie mesiacov
            month_mapping = {
                'q1': ['leden', 'unor', 'brezen'],
                'q2': ['duben', 'kveten', 'cerven'], 
                'q3': ['cervenec', 'srpen', 'zari'],
                'q4': ['rijen', 'listopad', 'prosinec']
            }
            
            period_total = 0
            monthly_data = {}
            
            if period in month_mapping:
                for month in month_mapping[period]:
                    value = employee_row.get(month, 0)
                    if pd.notna(value) and str(value).replace('.','').replace(',','').isdigit():
                        monthly_data[month] = float(str(value).replace(',', ''))
                        period_total += monthly_data[month]
            
            return {
                'total': period_total,
                'monthly': monthly_data
            }
            
        except Exception as e:
            print(f"Chyba pri načítavaní predajných dát: {e}")
            return {'total': 0, 'monthly': {}}
    
    def _get_activity_data(self, email: str, period: str) -> Dict:
        """Získa activity dáta pre zamestnanca"""
        try:
            # Tu by sa napojili activity logy
            # Zatiaľ vrátime dummy dáta
            return {
                'score': 75,  # Dummy activity score
                'logins': 20,
                'pages_visited': 50,
                'time_spent': 120  # minutes
            }
        except Exception as e:
            return {'score': 0}
    
    def _get_employee_goals(self, email: str, period: str, goals: Dict) -> Dict:
        """Získa ciele pre zamestnanca"""
        # Individuálne ciele
        individual_goals = goals.get('individual_targets', {}).get(email, {}).get(period, {})
        
        # Globálne ciele ako fallback
        global_goals = goals.get('global_targets', {}).get('2025', {}).get(period, {})
        
        # Mestské multiplikátory
        city_multipliers = goals.get('city_multipliers', {})
        
        # TODO: Určiť mesto zamestnanca a aplikovať multiplikátor
        
        # Kombinuj ciele
        employee_goals = {**global_goals, **individual_goals}
        
        return employee_goals
    
    def _get_performance_level(self, score: float, metrics_config: Dict) -> Dict:
        """Určí úroveň výkonnosti"""
        scoring = metrics_config.get('scoring', {})
        
        if score >= scoring['excellent']['min']:
            return {
                'level': 'excellent',
                'label': '🏆 Excelentný',
                'color': scoring['excellent']['color']
            }
        elif score >= scoring['good']['min']:
            return {
                'level': 'good', 
                'label': '🥉 Dobrý',
                'color': scoring['good']['color']
            }
        elif score >= scoring['average']['min']:
            return {
                'level': 'average',
                'label': '⚠️ Priemerný', 
                'color': scoring['average']['color']
            }
        else:
            return {
                'level': 'poor',
                'label': '❌ Podpriemerný',
                'color': scoring['poor']['color']
            }
    
    def set_individual_goal(self, email: str, period: str, metric: str, value: float):
        """Nastaví individuálny cieľ pre zamestnanca"""
        goals = self.load_goals()
        
        if email not in goals['individual_targets']:
            goals['individual_targets'][email] = {}
        
        if period not in goals['individual_targets'][email]:
            goals['individual_targets'][email][period] = {}
        
        goals['individual_targets'][email][period][metric] = value
        
        self.save_goals(goals)
    
    def get_team_overview(self, city: str = None) -> Dict:
        """Získa prehľad tímu/mesta"""
        try:
            city_kpis = self.get_city_kpis(city) if city else []
            
            if not city_kpis:
                return {'error': 'Žiadne dáta'}
            
            # Štatistiky
            total_employees = len(city_kpis)
            avg_score = sum([kpi.get('overall_score', 0) for kpi in city_kpis]) / total_employees
            
            excellent_count = len([kpi for kpi in city_kpis if kpi.get('performance_level', {}).get('level') == 'excellent'])
            
            return {
                'city': city,
                'total_employees': total_employees,
                'average_score': avg_score,
                'excellent_performers': excellent_count,
                'employees': city_kpis
            }
            
        except Exception as e:
            return {'error': f'Chyba pri získavaní prehľadu: {e}'}
