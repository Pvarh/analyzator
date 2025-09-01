# core/analyzer.py
import pandas as pd
import unicodedata
from difflib import SequenceMatcher
from core.utils import time_to_minutes


class DataAnalyzer:
    """Hlavná trieda pre analýzu dát zamestnancov"""
    
    def __init__(self):
        self.sales_employees = []
        self.internet_data = None
        self.applications_data = None
        self.name_mapping = {}
        
    def load_data(self, sales_data, internet_data=None, applications_data=None):
        """Načíta všetky dáta do analyzátora"""
        
        # Uložíme pôvodné sales dáta pre city mapping
        self.raw_sales_data = sales_data
        
        # Spracované dáta ako predtým
        self.sales_employees = sales_data
        self.internet_data = internet_data
        self.applications_data = applications_data
        
        
        # Vytvorenie name mappingu
        self._create_name_mapping()
        
    def _create_name_mapping(self):
        """Vytvorí inteligentné mapovanie mien medzi rôznymi súbormi"""
        
        import re
        
        def normalize_name(name):
            """Odstráni diakritiku a normalizuje meno"""
            if not name:
                return ""
            
            # Odstránenie diakritiky
            normalized = unicodedata.normalize('NFD', str(name))
            ascii_name = normalized.encode('ascii', 'ignore').decode('ascii')
            
            # Odstránenie extra informácií (dátumy, poznámky)
            clean_name = re.sub(r'[.,]\s*nast.*', '', ascii_name, flags=re.IGNORECASE)
            clean_name = re.sub(r'[.,]\s*nastup.*', '', clean_name, flags=re.IGNORECASE)
            clean_name = re.sub(r'[.,]\s*konec.*', '', clean_name, flags=re.IGNORECASE)
            clean_name = re.sub(r'\s+', ' ', clean_name).strip()
            
            return clean_name.lower()
        
        def extract_surname_and_first_initial(name):
            """Extrahuje priezvisko a prvé písmeno mena"""
            normalized = normalize_name(name)
            parts = normalized.split()
            
            if len(parts) >= 2:
                surname = parts[0]  # Prvá časť je priezvisko
                first_initial = parts[1][0] if parts[1] else ''
                return f"{surname} {first_initial}"
            
            return normalized
        
        # Získanie všetkých mien z internet/aplikačných dát
        all_monitoring_names = set()
        
        if self.internet_data is not None:
            all_monitoring_names.update(self.internet_data['Osoba ▲'].unique())
        
        if self.applications_data is not None:
            all_monitoring_names.update(self.applications_data['Osoba ▲'].unique())
        
        # Vytvorenie mapovania
        self.name_mapping = {}
        
        for emp in self.sales_employees:
            sales_name = emp.get('name', '')
            if not sales_name:
                continue
                
            sales_normalized = normalize_name(sales_name)
            sales_pattern = extract_surname_and_first_initial(sales_name)
            
            # Základné mapovanie seba na seba
            self.name_mapping[sales_name] = sales_normalized
            
            # Hľadanie zhody v monitoring dátach
            best_match = None
            best_score = 0
            
            for monitoring_name in all_monitoring_names:
                monitoring_normalized = normalize_name(monitoring_name)
                monitoring_pattern = extract_surname_and_first_initial(monitoring_name)
                
                # Skóre zhody
                score = 0
                
                # 1. Presná zhoda po normalizácii
                if sales_normalized == monitoring_normalized:
                    score = 100
                
                # 2. Zhoda priezvisko + prvé písmeno
                elif sales_pattern == monitoring_pattern:
                    score = 80
                
                # 3. Obsahuje priezvisko a prvé písmeno
                elif (sales_pattern.split()[0] in monitoring_normalized and 
                    len(sales_pattern.split()) > 1 and
                    sales_pattern.split()[1] in monitoring_normalized):
                    score = 60
                
                # 4. Obsahuje len priezvisko (aspoň 6 znakov)
                elif (len(sales_pattern.split()[0]) >= 6 and 
                    sales_pattern.split()[0] in monitoring_normalized):
                    score = 40
                
                if score > best_score:
                    best_score = score
                    best_match = monitoring_name
            
            if best_match and best_score >= 60:  # Minimálne 60% zhoda
                self.name_mapping[best_match] = sales_normalized  # Mapovanie monitoring -> canonical

        
    
    def get_canonical_name(self, name):
        """Vráti kanonický tvar mena s inteligentným hľadaním"""
        if not name:
            return ""
        
        # Ak už máme mapovanie, použiť ho
        if name in self.name_mapping:
            return self.name_mapping[name]
        
        # Fallback - normalizácia
        normalized = unicodedata.normalize('NFD', str(name))
        ascii_name = normalized.encode('ascii', 'ignore').decode('ascii')
        return ascii_name.strip().lower()

    
    # ✅ NOVÁ FUNKCIA - analyze_employee
    def analyze_employee(self, employee_name):
        
        
        # Nájdenie zamestnanca v sales dátach
        employee_data = None
        for emp in self.sales_employees:
            if emp.get('name') == employee_name:
                employee_data = emp
                break
        
        if not employee_data:
            return {'error': f'Employee {employee_name} not found'}
        
        # Základné sales dáta
        monthly_sales = employee_data.get('monthly_sales', {})
        total_sales = sum(monthly_sales.values()) if monthly_sales else 0
        
        analysis = {
            'name': employee_name,
            'workplace': employee_data.get('workplace', 'unknown'),
            'sales_performance': {
                'monthly_sales': monthly_sales,
                'total_sales': total_sales,
                'score': employee_data.get('score', 0)
            }
        }
        
        return analysis
    
    # ✅ NOVÁ FUNKCIA - _parse_time_to_minutes
    def _parse_time_to_minutes(self, time_str):
        """Konvertuje čas zo stringu na minúty"""
        if pd.isna(time_str) or str(time_str).strip() in ['', '0', '0:00', '0:00:00']:
            return 0
        
        try:
            time_str = str(time_str).strip()
            
            # Format HH:MM:SS
            if ':' in time_str:
                parts = time_str.split(':')
                if len(parts) == 3:  # HH:MM:SS
                    hours = int(parts[0])
                    minutes = int(parts[1]) 
                    seconds = int(parts[2])
                    return hours * 60 + minutes + seconds / 60
                elif len(parts) == 2:  # HH:MM
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    return hours * 60 + minutes
            
            # Číselná hodnota (už v minútach)
            return float(time_str)
            
        except:
            return 0
    
    # ✅ NOVÁ FUNKCIA - simplify_name
    def _detect_gender(self, name):
        """Detekcia pohlavia na základe koncovky priezviska"""
        name_clean = name.strip().lower()
        
        # Ženské koncovky
        female_endings = ['ová', 'á', 'va', 'na', 'ka', 'ra', 'ta', 'la']
        # Mužské koncovky  
        male_endings = ['ý', 'í', 'ek', 'el', 'or', 'er', 'an', 'en', 'in', 'on', 'ub']
        
        # Hľadáme priezvisko (prvé slovo)
        words = name_clean.split()
        if not words:
            return "unknown"
            
        surname = words[0]
        
        # Kontrola ženských koncoviek
        for ending in female_endings:
            if surname.endswith(ending):
                return "female"
        
        # Kontrola mužských koncoviek, zatial pouzitelne
        for ending in male_endings:
            if surname.endswith(ending):
                return "male"
                
        return "unknown"

    def simplify_name(self, name):
        """Pokročilé zjednodušenie mena pre lepšie matchovanie"""
        
        if not name or pd.isna(name):
            return ""
        
        # Odstránenie diakritiky
        simplified = unicodedata.normalize('NFD', str(name))
        simplified = ''.join(char for char in simplified if unicodedata.category(char) != 'Mn')
        
        # Ďalšie čistenie
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
        
        # Odstránenie všetkých číslic
        simplified = ''.join(char for char in simplified if not char.isdigit())
        
        return simplified
    
    # ✅ NOVÁ FUNKCIA - get_employee_city_mapping
    def get_employee_city_mapping(self):
        """Vytvorí mapovanie mien zamestnancov na mestá zo sales dát"""
        
        if not hasattr(self, 'raw_sales_data') or self.raw_sales_data is None:
            return {}
        
        city_mapping = {}
        current_city = None
        
        for idx, row in self.raw_sales_data.iterrows():
            employee_name = str(row['user']).strip()
            
            # Ak je to názov mesta (napr. "praha", "brno")
            if employee_name.lower() in ['praha', 'brno', 'zlin', 'vizovice']:
                current_city = employee_name.lower()
                continue
            
            # Ak máme aktuálne mesto a meno nie je NaN
            if current_city and employee_name and employee_name != 'nan':
                # Normalizuj meno pre lepšie matchovanie
                simplified_name = self.simplify_name(employee_name)
                city_mapping[employee_name] = current_city
                city_mapping[simplified_name] = current_city
        
        return city_mapping
    
    # ✅ NOVÁ FUNKCIA - find_matching_studio_employees  
    def find_matching_studio_employees(self, studio_data, allowed_cities):
        """Nájde zamestnancov v studio dátach, ktorí patria do povolených miest"""
        
        if studio_data is None or studio_data.empty:
            return []
        
        # Získaj mapovanie mien na mestá
        city_mapping = self.get_employee_city_mapping()
        if not city_mapping:
            return []  # Ak nie sú sales dáta, vráť prázdny list
        
        # Získaj všetkých zamestnancov v studio dátach
        studio_column = 'Kontaktní osoba-Jméno a příjmení'
        if studio_column not in studio_data.columns:
            return []
        
        studio_employees = studio_data[studio_column].dropna().unique()
        
        allowed_studio_employees = []
        
        for studio_employee in studio_employees:
            studio_simplified = self.simplify_name(studio_employee)
            
            # Pokús sa nájsť zhodu v city_mapping
            employee_city = None
            best_match = None
            best_similarity = 0
            rejected_due_to_gender = False  # Flag pre zamietnutie kvôli pohlaviu
            
            # 1. Presná zhoda s pôvodným menom
            if studio_employee in city_mapping:
                employee_city = city_mapping[studio_employee]
                best_match = f"Presná zhoda: '{studio_employee}'"
            # 2. Zhoda so simplifikovaným menom  
            elif studio_simplified in city_mapping:
                employee_city = city_mapping[studio_simplified]
                best_match = f"Simplifikovaná zhoda: '{studio_simplified}'"
            # 3. Fuzzy matching so sales menami + špeciálna logika pre iniciály
            else:
                for sales_name, city in city_mapping.items():
                    sales_simplified = self.simplify_name(sales_name)
                    
                    # Používame rovnakú logiku ako find_matching_names
                    from difflib import SequenceMatcher
                    similarity = SequenceMatcher(None, studio_simplified, sales_simplified).ratio()
                    
                    # Špeciálna logika pre mená s iniciálami (napr. "Formanová K." vs "Formanová Klára")
                    is_initial_match = False
                    if '.' in sales_name or ',' in sales_name:  # Ak sales meno má bodku alebo čiarku (inicál)
                        # Rozdeľ sales meno na priezvisko a inicál
                        sales_parts = sales_name.replace(',', '').replace('.', '').split()
                        if len(sales_parts) >= 2:
                            sales_surname = sales_parts[0].strip()
                            sales_initial = sales_parts[1].strip().upper()[0] if sales_parts[1].strip() else ''
                            
                            # Rozdeľ studio meno
                            studio_parts = studio_employee.split()
                            if len(studio_parts) >= 2:
                                studio_surname = studio_parts[0].strip()
                                studio_firstname = studio_parts[1].strip()
                                
                                # Porovnaj priezvisko (musí byť presné) a prvé písmeno krstného mena (musí byť presné)
                                surname_match = self.simplify_name(sales_surname) == self.simplify_name(studio_surname)
                                initial_match = (len(studio_firstname) > 0 and 
                                               len(sales_initial) > 0 and
                                               self.simplify_name(studio_firstname[0]).upper() == self.simplify_name(sales_initial).upper())
                                
                                if surname_match and initial_match:
                                    is_initial_match = True
                                    similarity = 0.95  # Veľmi vysoká podobnosť pre presný inicál match
                    
                    if (studio_simplified == sales_simplified or 
                        studio_simplified in sales_simplified or
                        sales_simplified in studio_simplified or
                        similarity >= 0.65 or  
                        is_initial_match):  # Pridané inicál matching
                        
                        # Pre všetky fuzzy matches (okrem initial match) pridáme kontrolu pohlavia
                        if not is_initial_match:
                            # Pre presné zhody nerobíme kontrolu pohlavia
                            if studio_simplified != sales_simplified:
                                studio_gender = self._detect_gender(studio_employee)
                                sales_gender = self._detect_gender(sales_name)
                                
                                if studio_gender != "unknown" and sales_gender != "unknown" and studio_gender != sales_gender:
                                    rejected_due_to_gender = True
                                    break  # Prerušíme hľadanie pre tohto zamestnanca
                        
                        employee_city = city
                        if is_initial_match:
                            best_match = f"Inicál match: '{sales_name}' (priezvisko + inicál)"
                        else:
                            best_match = f"Fuzzy match: '{sales_name}' (podobnosť: {similarity:.3f})"
                        best_similarity = similarity
                        break
                    elif similarity > best_similarity:
                        best_similarity = similarity
                        best_match = f"Najlepšia zhoda: '{sales_name}' (podobnosť: {similarity:.3f})"
            
            # Ak zamestnanec patrí do povoleného mesta a nebol zamietnutý, pridaj ho
            if employee_city and employee_city in allowed_cities and not rejected_due_to_gender:
                allowed_studio_employees.append(studio_employee)
        
        return allowed_studio_employees

    # ✅ NOVÁ FUNKCIA - find_matching_names
    def find_matching_names(self, employee_name, data_source):
        """Nájde všetky možné varianty mena v danom zdroji dát"""
        
        if data_source is None or data_source.empty:
            return []
        
        # Rozšírené vyhľadávanie podľa podobnosti
        simplified_target = self.simplify_name(employee_name)
        all_persons = data_source['Osoba ▲'].unique()
        matching_names = []
        
        for person in all_persons:
            simplified_person = self.simplify_name(person)
            
            # Rôzne stratégie matchovania:
            similarity = SequenceMatcher(None, simplified_target, simplified_person).ratio()
            if (
                simplified_target == simplified_person or  # Presná zhoda
                simplified_target in simplified_person or  # Čiastočná zhoda
                simplified_person in simplified_target or  # Opačná čiastočná zhoda
                similarity >= 0.8  # Podobnosť >= 80%
            ):
                if person not in matching_names:
                    matching_names.append(person)

        
        return matching_names
    
    # ✅ NOVÁ FUNKCIA - calculate_mail_score
    def calculate_mail_score(self, person):
        """Calculate mail score based on usage data"""

        
        try:
            
            if not hasattr(self, 'internet_data') or self.internet_data is None:
                return 50.0
            
            
            # Nájdenie matchujúcich mien
            matching_names = self.find_matching_names(person, self.internet_data)

            
            if not matching_names:

                return 50.0
            
            # Nájdenie riadku pre osobu
            person_rows = self.internet_data[self.internet_data['Osoba ▲'].isin(matching_names)]
            
            if person_rows.empty:

                return 50.0
            
            # Získanie času pre mail
            total_mail_time = 0
            total_time = 0
            
            for _, row in person_rows.iterrows():
                mail_time_str = row.get('Mail', '0:00')
                total_time_str = row.get('Čas celkem ▼', '0:00')
                
                mail_minutes = self._parse_time_to_minutes(mail_time_str)
                day_total = self._parse_time_to_minutes(total_time_str)
                
                total_mail_time += mail_minutes
                total_time += day_total
                

            
            if total_time == 0:
                return 50.0
            
            # Výpočet percenta času na mailoch
            mail_percentage = (total_mail_time / total_time) * 100
            
            # Hodnotenie efektivity mailov
            if 10 <= mail_percentage <= 25:
                score = 90
            elif mail_percentage < 10:
                score = 70
            elif mail_percentage <= 35:
                score = 75
            elif mail_percentage <= 50:
                score = 50
            else:
                score = 30
            

            return score
            
        except Exception as e:
 
            return 65.0
    
    # ✅ NOVÁ FUNKCIA - calculate_application_score
    def calculate_application_score(self, person):

        
        try:
            if not hasattr(self, 'internet_data') or self.internet_data is None:

                return 100.0
            
            # Pokročilé matchovanie mien
            matching_names = self.find_matching_names(person, self.internet_data)

            
            # Vyhľadanie záznamov
            user_records = self.internet_data[self.internet_data['Osoba ▲'].isin(matching_names)]

            
            if user_records.empty:
  
                return 100.0
            
            total_sketchup_time = 0
            
            for idx, (_, row) in enumerate(user_records.iterrows()):
                chat_value = row.get('Chat', '0:00')
                if pd.notna(chat_value) and str(chat_value) not in ['nan', '', '0:00', None]:
                    minutes = self._parse_time_to_minutes(str(chat_value))
                    total_sketchup_time += minutes
   
       
            

            if total_sketchup_time == 0:
                score = 100
            elif total_sketchup_time <= 30:
                score = 80
            elif total_sketchup_time <= 60:
                score = 60
            elif total_sketchup_time <= 120:
                score = 40
            else:
                score = 20

            return score
            
        except Exception as e:

            return 90.0
    
    # ✅ NOVÁ FUNKCIA - calculate_internet_score
    def calculate_internet_score(self, person):

        
        try:
            if not hasattr(self, 'internet_data') or self.internet_data is None:
              
                return 60.0
            
            matching_names = self.find_matching_names(person, self.internet_data)
            user_records = self.internet_data[self.internet_data['Osoba ▲'].isin(matching_names)]
            
     
            
            if user_records.empty:
                return 60.0
            
            total_productive = 0
            total_unproductive = 0
            total_time = 0
            
            for _, row in user_records.iterrows():
                # Produktívne aktivity
                productive_time = (
                    self._parse_time_to_minutes(row.get('IS Sykora', '0:00')) +
                    self._parse_time_to_minutes(row.get('Mail', '0:00')) +
                    self._parse_time_to_minutes(row.get('SykoraShop', '0:00')) +
                    self._parse_time_to_minutes(row.get('Web k praci', '0:00'))
                )
                
                # Neproduktívne aktivity
                unproductive_time = (
                    self._parse_time_to_minutes(row.get('Hry', '0:00')) +
                    self._parse_time_to_minutes(row.get('Chat', '0:00')) +
                    self._parse_time_to_minutes(row.get('Nepracovni weby', '0:00'))
                )
                
                day_total = self._parse_time_to_minutes(row.get('Čas celkem ▼', '0:00'))
                
                total_productive += productive_time
                total_unproductive += unproductive_time
                total_time += day_total
            
 
            
            if total_time == 0:
                return 60.0
            
            productivity_percentage = (total_productive / total_time) * 100
            score = min(100, productivity_percentage)

            return score
            
        except Exception as e:

            return 60.0
    
    # PÔVODNÉ FUNKCIE ZOSTÁVAJÚ ROVNAKÉ
    def get_all_employees_summary(self):
        """Vráti súhrn všetkých zamestnancov"""
        
        if not self.sales_employees:
            return []
        
        summary = []
        
        for emp in self.sales_employees:
            emp_summary = {
                'name': emp.get('name', 'Unknown'),
                'workplace': emp.get('workplace', 'unknown'),
                'monthly_sales': emp.get('monthly_sales', {}),
                'total_sales': sum(emp.get('monthly_sales', {}).values()) if emp.get('monthly_sales') else 0,
                'score': emp.get('score', 0),
                'rating': self._calculate_rating(emp)
            }
            
            summary.append(emp_summary)
        
        return summary
    
    def _calculate_rating(self, emp):
        """Vypočíta rating zamestnanca"""
        
        score = emp.get('score', 0)
        
        if score >= 80:
            return 'excellent'
        elif score >= 70:
            return 'good'
        elif score >= 60:
            return 'average'
        else:
            return 'poor'
    
    def validate_sales_consistency(self):
        """Skontroluje konzistenciu sales dát"""
        
        inconsistencies = []
        
        for emp in self.sales_employees:
            name = emp.get('name', 'Unknown')
            
            # Porovnanie rôznych zdrojov
            monthly_total = sum(emp.get('monthly_sales', {}).values()) if emp.get('monthly_sales') else 0
            direct_total = emp.get('total_sales', 0)
            
            if monthly_total > 0 and direct_total > 0 and abs(monthly_total - direct_total) > 1:
                inconsistencies.append({
                    'name': name,
                    'monthly_total': monthly_total,
                    'direct_total': direct_total,
                    'difference': abs(monthly_total - direct_total)
                })
        
        return inconsistencies
    
    def get_employee_by_name(self, name):
        """Nájde zamestnanca podľa mena"""
        
        for emp in self.sales_employees:
            if emp.get('name') == name:
                return emp
        return None
    
    def get_employees_by_workplace(self, workplace):
        """Vráti zamestnancov podľa pracoviska"""
        
        return [emp for emp in self.sales_employees if emp.get('workplace', '').lower() == workplace.lower()]
    
    def calculate_company_statistics(self):
        """Vypočíta celkové štatistiky firmy"""
        
        total_sales = 0
        total_employees = len(self.sales_employees)
        workplace_stats = {}
        
        for emp in self.sales_employees:
            emp_sales = sum(emp.get('monthly_sales', {}).values()) if emp.get('monthly_sales') else 0
            total_sales += emp_sales
            
            workplace = emp.get('workplace', 'unknown')
            if workplace not in workplace_stats:
                workplace_stats[workplace] = {'count': 0, 'sales': 0}
            
            workplace_stats[workplace]['count'] += 1
            workplace_stats[workplace]['sales'] += emp_sales
        
        return {
            'total_sales': total_sales,
            'total_employees': total_employees,
            'average_sales_per_employee': total_sales / total_employees if total_employees > 0 else 0,
            'workplace_stats': workplace_stats
        }
    
    def get_employee_monthly_data(self, employee_name, data_type='internet'):
        """Získa mesačné dáta pre konkrétneho zamestnanca agregované podľa mesiacov"""
        
        if data_type == 'internet':
            data_source = self.internet_data
        else:
            data_source = self.applications_data
            
        if data_source is None or data_source.empty:
            return {}
            
        # Nájdi matchujúce mená
        matching_names = self.find_matching_names(employee_name, data_source)
        if not matching_names:
            return {}
            
        # Filtrovanie dát pre zamestnanca
        employee_data = data_source[data_source['Osoba ▲'].isin(matching_names)]
        
        if employee_data.empty:
            return {}
            
        monthly_data = {}
        
        # Pre každý riadok dát
        for _, row in employee_data.iterrows():
            # Skús extrahovať mesiac z rôznych možných zdrojov
            month = None
            
            # 1. Pokus - Source_File stĺpec
            if 'Source_File' in row and pd.notna(row['Source_File']):
                import re
                month_match = re.search(r'(\d{4}-\d{2})', str(row['Source_File']))
                if month_match:
                    month = month_match.group(1)
            
            # 2. Pokus - ak máme nejaký dátumový stĺpec
            if not month and 'Date' in row and pd.notna(row['Date']):
                try:
                    date_val = pd.to_datetime(row['Date'])
                    month = date_val.strftime('%Y-%m')
                except:
                    pass
            
            # 3. Pokus - default na aktuálny mesiac
            if not month:
                from datetime import datetime
                month = datetime.now().strftime('%Y-%m')
            
            if month not in monthly_data:
                monthly_data[month] = {}
                
            # Agreguj všetky časové stĺpce
            for col in row.index:
                if col in ['Osoba ▲', 'Source_File', 'Date']:
                    continue
                    
                time_value = row[col]
                if pd.notna(time_value) and str(time_value) not in ['0:00', 'nan', '']:
                    minutes = time_to_minutes(str(time_value))
                    if minutes > 0:
                        if col not in monthly_data[month]:
                            monthly_data[month][col] = 0
                        monthly_data[month][col] += minutes
        
        return monthly_data
    
    def get_all_employees_averages(self, data_type='internet'):
        """Vypočíta priemery všetkých zamestnancov pre každú aktivitu"""
        
        if data_type == 'internet':
            data_source = self.internet_data
            activity_columns = ['Mail', 'Chat', 'IS Sykora', 'SykoraShop', 'Web k praci', 'Hry', 'Nepracovni weby', 'Nezařazené', 'Umela inteligence', 'hladanie prace']
        else:
            data_source = self.applications_data  
            activity_columns = ['Helios Green', 'Imos - program', 'Programy', 'Půdorysy', 'Mail', 'Chat', 'Internet']
            
        if data_source is None or data_source.empty:
            return {}
            
        averages = {}
        
        for col in activity_columns:
            if col in data_source.columns:
                total_minutes = 0
                count = 0
                
                for _, row in data_source.iterrows():
                    value = row.get(col, '0:00')
                    if pd.notna(value) and str(value) not in ['0:00', 'nan', '']:
                        total_minutes += time_to_minutes(str(value))
                        count += 1
                
                if count > 0:
                    avg_hours = (total_minutes / count) / 60
                    averages[col] = round(avg_hours, 1)
                else:
                    averages[col] = 0.0
            else:
                averages[col] = 0.0
                
        return averages
    
    def get_employee_averages(self, employee_name, data_type='internet'):
        """Vypočíta individuálne priemery konkrétneho zamestnanca"""
        
        if data_type == 'internet':
            data_source = self.internet_data
            activity_columns = ['Mail', 'Chat', 'IS Sykora', 'SykoraShop', 'Web k praci', 'Hry', 'Nepracovni weby', 'Nezařazené', 'Umela inteligence', 'hladanie prace']
        else:
            data_source = self.applications_data
            activity_columns = ['Helios Green', 'Imos - program', 'Programy', 'Půdorysy', 'Mail', 'Chat', 'Internet']
            
        if data_source is None or data_source.empty:
            return {}
            
        # Nájdi matchujúce mená
        matching_names = self.find_matching_names(employee_name, data_source)
        if not matching_names:
            return {}
            
        # Filtrovanie dát pre tohto zamestnanca
        employee_data = data_source[data_source['Osoba ▲'].isin(matching_names)]
        
        if employee_data.empty:
            return {}
            
        averages = {}
        
        for col in activity_columns:
            if col in employee_data.columns:
                total_minutes = 0
                count = 0
                
                for _, row in employee_data.iterrows():
                    value = row.get(col, '0:00')
                    if pd.notna(value) and str(value) not in ['0:00', 'nan', '']:
                        total_minutes += time_to_minutes(str(value))
                        count += 1
                
                if count > 0:
                    avg_hours = (total_minutes / count) / 60
                    averages[col] = round(avg_hours, 1)
                else:
                    averages[col] = 0.0
            else:
                averages[col] = 0.0
                
        return averages
 
         d e f   g e t _ e m p l o y e e _ d a i l y _ a v e r a g e s ( s e l f ,   e m p l o y e e _ n a m e ,   d a t a _ t y p e = ' i n t e r n e t ' ) :  
         d e f   g e t _ e m p l o y e e _ d a i l y _ a v e r a g e s ( s e l f ,   e m p l o y e e _ n a m e ,   d a t a _ t y p e = ' i n t e r n e t ' ) :  
                 " " " V y p o � d� t a   d e n n �   p r i e m e r y   k o n k r � t n e h o   z a m e s t n a n c a   ( h o d i n y   z a   d e 9� ) " " "  
                  
                 i f   d a t a _ t y p e   = =   ' i n t e r n e t ' :  
                         d a t a _ s o u r c e   =   s e l f . i n t e r n e t _ d a t a  
                         a c t i v i t y _ c o l u m n s   =   [ ' M a i l ' ,   ' C h a t ' ,   ' I S   S y k o r a ' ,   ' S y k o r a S h o p ' ,   ' W e b   k   p r a c i ' ,   ' H r y ' ,   ' N e p r a c o v n i   w e b y ' ,   ' N e z a 9"!a z e n � ' ,   ' U m e l a   i n t e l i g e n c e ' ,   ' h l a d a n i e   p r a c e ' ]  
                 e l s e :  
                         d a t a _ s o u r c e   =   s e l f . a p p l i c a t i o n s _ d a t a  
                         a c t i v i t y _ c o l u m n s   =   [ ' H e l i o s   G r e e n ' ,   ' I m o s   -   p r o g r a m ' ,   ' P r o g r a m y ' ,   ' P 9{d o r y s y ' ,   ' M a i l ' ,   ' C h a t ' ,   ' I n t e r n e t ' ]  
                          
                 i f   d a t a _ s o u r c e   i s   N o n e   o r   d a t a _ s o u r c e . e m p t y :  
                         r e t u r n   { }  
                          
                 #   N �j d i   m a t c h u j _c e   m e n � 
                 m a t c h i n g _ n a m e s   =   s e l f . f i n d _ m a t c h i n g _ n a m e s ( e m p l o y e e _ n a m e ,   d a t a _ s o u r c e )  
                 i f   n o t   m a t c h i n g _ n a m e s :  
                         r e t u r n   { }  
                          
                 #   F i l t r o v a n i e   d �t   p r e   t o h t o   z a m e s t n a n c a  
                 e m p l o y e e _ d a t a   =   d a t a _ s o u r c e [ d a t a _ s o u r c e [ ' O s o b a   �  �' ] . i s i n ( m a t c h i n g _ n a m e s ) ]  
                  
                 i f   e m p l o y e e _ d a t a . e m p t y :  
                         r e t u r n   { }  
                  
                 #   P o � de t   d n �   ( r i a d k o v )   s   d �t a m i   p r e   t o h t o   z a m e s t n a n c a  
                 t o t a l _ d a y s   =   l e n ( e m p l o y e e _ d a t a )  
                  
                 i f   t o t a l _ d a y s   = =   0 :  
                         r e t u r n   { }  
                          
                 a v e r a g e s   =   { }  
                  
                 f o r   c o l   i n   a c t i v i t y _ c o l u m n s :  
                         i f   c o l   i n   e m p l o y e e _ d a t a . c o l u m n s :  
                                 t o t a l _ m i n u t e s   =   0  
                                  
                                 f o r   _ ,   r o w   i n   e m p l o y e e _ d a t a . i t e r r o w s ( ) :  
                                         v a l u e   =   r o w . g e t ( c o l ,   ' 0 : 0 0 ' )  
                                         i f   p d . n o t n a ( v a l u e )   a n d   s t r ( v a l u e )   n o t   i n   [ ' 0 : 0 0 ' ,   ' n a n ' ,   ' ' ] :  
                                                 t o t a l _ m i n u t e s   + =   t i m e _ t o _ m i n u t e s ( s t r ( v a l u e ) )  
                                  
                                 #   D e n n �  p r i e m e r   =   c e l k o v �  � da s   /   p o � de t   d n �  
                                 d a i l y _ a v g _ h o u r s   =   ( t o t a l _ m i n u t e s   /   t o t a l _ d a y s )   /   6 0   i f   t o t a l _ d a y s   >   0   e l s e   0  
                                 a v e r a g e s [ c o l ]   =   r o u n d ( d a i l y _ a v g _ h o u r s ,   1 )  
                         e l s e :  
                                 a v e r a g e s [ c o l ]   =   0 . 0  
                                  
                 r e t u r n   a v e r a g e s  
 