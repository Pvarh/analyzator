# core/metrics_calculator.py
from core.utils import time_to_minutes
import pandas as pd
import unicodedata
from difflib import SequenceMatcher

class EmployeeMetricsCalculator:
    """Centralizované výpočty metrík zamestnancov"""
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
        
    def calculate_all_metrics(self, emp):
        """Vypočíta všetky metriky pre zamestnanca"""
        
        employee_name = emp.get('name', '')
        sales = emp.get('total_sales', 0)
        
        return {
            'sales': {'value': self.calculate_sales_score(sales)},
            'mail': {'value': self.calculate_mail_efficiency(employee_name, sales)},
            'sketchup': {'value': self.calculate_sketchup_usage(employee_name)},
            'internet': {'value': self.calculate_internet_efficiency(employee_name)},
            'overall': {'value': emp.get('score', 0)}
        }
    
    def calculate_sales_score(self, sales, target=2000000):
        """Jednoduchý výpočet bez hardcoded hodnôt"""
        
        # Jednoduchá kontrola rozumnosti
        if sales < 0:

            sales = 0
        

        
        score = min(100, (sales / target) * 100) if sales else 0

        
        return score
    
    def simplify_name(self, name):
        """Pokročilé zjednodušenie mena pre lepšie matchovanie"""
        
        if not name or pd.isna(name):
            return ""
        
        # 1. Odstránenie diakritiky
        simplified = unicodedata.normalize('NFD', str(name))
        simplified = ''.join(char for char in simplified if unicodedata.category(char) != 'Mn')
        
        # 2. Ďalšie čistenie
        simplified = (simplified
                     .lower()
                     .replace(' ', '')
                     .replace('.', '')
                     .replace(',', '')
                     .replace('-', '')
                     .replace('á', 'a')
                     .replace('ě', 'e')
                     .replace('í', 'i')
                     .replace('ý', 'y')
                     .replace('ů', 'u')
                     .replace('ň', 'n')
                     .replace('č', 'c')
                     .replace('š', 's')
                     .replace('ž', 'z'))
        
        return simplified

    def name_similarity(self, name1, name2):
        """Vypočíta podobnosť medzi dvoma menami (0-1)"""
        return SequenceMatcher(None, name1, name2).ratio()

    def find_matching_names(self, employee_name, data_source):
        """Nájde všetky možné varianty mena v danom zdroji dát"""
        
        if data_source is None or data_source.empty:
            return []
        
        # 1. Štandardné mapovanie z analyzer
        canonical_name = self.analyzer.get_canonical_name(employee_name)
        matching_names = [name for name, canon in self.analyzer.name_mapping.items() if canon == canonical_name]
        
        # 2. Rozšírené vyhľadávanie podľa podobnosti
        simplified_target = self.simplify_name(employee_name)
        all_persons = data_source['Osoba ▲'].unique()
        
        for person in all_persons:
            simplified_person = self.simplify_name(person)
            
            # Rôzne stratégie matchovania:
            if (
                simplified_target == simplified_person or  # Presná zhoda
                simplified_target in simplified_person or  # Čiastočná zhoda
                simplified_person in simplified_target or  # Opačná čiastočná zhoda
                self.name_similarity(simplified_target, simplified_person) > 0.8  # Podobnosť > 80%
            ):
                if person not in matching_names:
                    matching_names.append(person)

        
        return matching_names
    
    def calculate_mail_efficiency(self, employee_name, sales):
        """Opravený výpočet mailovej efektivity s lepším debugom"""
        
        
  
        
        # ✅ POKRAČOVANIE - zvyšok funkcie pre výpočet mailovej efektivity
        
        # Nájdenie matchujúcich mien
        matching_names = self.find_matching_names(employee_name, self.analyzer.internet_data)

        
        # Vyhľadanie záznamov pre tohoto zamestnanca
        user_records = self.analyzer.internet_data[self.analyzer.internet_data['Osoba ▲'].isin(matching_names)]

        
        if user_records.empty:
            return 50
        
        # Výpočet času stráveného na mailoch vs celkový čas
        total_mail_time = 0
        total_time = 0
        
        for _, row in user_records.iterrows():
            # Mail čas z internet dát
            mail_time = time_to_minutes(row.get('Mail', '0:00'))
            # Celkový čas v daný deň
            day_total = time_to_minutes(row.get('Čas celkem ▼', '0:00'))
            
            total_mail_time += mail_time
            total_time += day_total
            

        
        if total_time == 0:

            return 50
        
        # Výpočet percenta času na mailoch
        mail_percentage = (total_mail_time / total_time) * 100

        
        # Hodnotenie efektivity mailov
        if 10 <= mail_percentage <= 25:
            # Optimálny rozsah - 10-25% času na mailoch je dobré
            efficiency = 90

        elif mail_percentage < 10:
            # Príliš málo mailov - možno nedostatočná komunikácia
            efficiency = 70

        elif mail_percentage <= 35:
            # Prijateľné, ale už trochu veľa
            efficiency = 75

        elif mail_percentage <= 50:
            # Príliš veľa času na mailoch
            efficiency = 50
 
        else:
            # Nadmerné používanie mailov
            efficiency = 30

        
        # Bonus za vysoké predaje - ak má dobré predaje, môže si dovoliť viac mailov
        if sales > 3000000:  # 3M+ Kč
            efficiency = min(100, efficiency + 15)

        elif sales > 2000000:  # 2M+ Kč
            efficiency = min(100, efficiency + 10)

        
 
        return efficiency
    
    def calculate_sketchup_usage(self, employee_name):
        """OPRAVENÝ SketchUp výpočet s pokročilým name matchingom"""
        
        # ✅ OPRAVENÉ: Hľadáme v INTERNET dátach, nie applications
        if not hasattr(self.analyzer, 'internet_data') or self.analyzer.internet_data is None:
            return 100
        
        # ✅ Pokročilé matchovanie mien
        matching_names = self.find_matching_names(employee_name, self.analyzer.internet_data)
        
        # Vyhľadanie záznamov
        user_records = self.analyzer.internet_data[self.analyzer.internet_data['Osoba ▲'].isin(matching_names)]
        
        if user_records.empty:
            return 100
        
        total_sketchup_time = 0
        
        for idx, (_, row) in enumerate(user_records.iterrows()):
            chat_value = row.get('Chat', '0:00')
            
            if pd.notna(chat_value) and str(chat_value) not in ['nan', '', '0:00', None]:
                minutes = time_to_minutes(str(chat_value))
                total_sketchup_time += minutes
        
        # ✅ REALISTICKÉ hodnotenie
        if total_sketchup_time == 0:
            score = 100
        elif total_sketchup_time <= 30:  # Menej ako 30 minút
            score = 80
        elif total_sketchup_time <= 60:  # 1 hodina
            score = 60
        elif total_sketchup_time <= 120:  # 2 hodiny
            score = 40
        else:  # Viac ako 2 hodiny
            score = 20
        return score

    
    def calculate_internet_efficiency(self, employee_name):
        """Výpočet internetovej efektivity s pokročilým name matchingom"""
        
        if not hasattr(self.analyzer, 'internet_data') or self.analyzer.internet_data is None:

            return 60
        
        # ✅ Použitie pokročilého matchingu
        matching_names = self.find_matching_names(employee_name, self.analyzer.internet_data)
        
        user_records = self.analyzer.internet_data[self.analyzer.internet_data['Osoba ▲'].isin(matching_names)]
        

        
        if user_records.empty:
            return 60
        
        total_productive = 0
        total_unproductive = 0
        total_time = 0
        
        for _, row in user_records.iterrows():
            productive_time = (
                time_to_minutes(row.get('IS Sykora', '0:00')) +
                time_to_minutes(row.get('Mail', '0:00')) +
                time_to_minutes(row.get('SykoraShop', '0:00')) +
                time_to_minutes(row.get('Web k praci', '0:00'))
            )
            
            unproductive_time = (
                time_to_minutes(row.get('Hry', '0:00')) +
                time_to_minutes(row.get('Chat', '0:00')) +
                time_to_minutes(row.get('Nepracovni weby', '0:00'))
            )
            
            day_total = time_to_minutes(row.get('Čas celkem ▼', '0:00'))
            
            total_productive += productive_time
            total_unproductive += unproductive_time
            total_time += day_total
        

        
        if total_time == 0:
            return 60
        
        productivity_percentage = (total_productive / total_time) * 100
        

        
        return min(100, productivity_percentage)
