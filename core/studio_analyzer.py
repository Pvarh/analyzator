import pandas as pd
import numpy as np
import re
import streamlit as st
from typing import Dict, List, Tuple
import difflib



class StudioAnalyzer:
    """
    Analyzuje predaj spotrebičov z Excelu.
    Zohľadňuje LEN týchto 5 kategórií:
        – mikrovlnka
        – trouba
        – chladnicka
        – varna deska
        – mycka
    Objednávky so stavom '12-Zrušena' alebo len '12' vynecháva.
    """
    
    APPLIANCES = ['mikrovlnka', 'trouba', 'chladnicka', 'varna deska', 'mycka', 'digestor']
    
    def __init__(self, excel_file):
        self.df = self.load_excel_data(excel_file)
        self.process_data()
    
    def load_excel_data(self, file) -> pd.DataFrame:
        """Načíta Excel súbor s automatickou detekciou formátu"""
        df = pd.read_excel(file)
        return df
    
    def process_data(self):
        """Spracuje a vyčistí dáta"""
        # Konverzia dátumu
        self.df['Datum real.'] = pd.to_datetime(self.df['Datum real.'], errors='coerce')
        
        # Filtrovanie - odstránenie zrušených objednávok
        def is_cancelled(status):
            if pd.isna(status):
                return False
            status_str = str(status).strip()
            return status_str == '12-Zrušena' or status_str == '12'
        
        # Aplikuj filter
        cancelled_mask = self.df['Uživatelský stav'].apply(is_cancelled)
        self.df_active = self.df.loc[~cancelled_mask].copy()
        
        # Normalizácia názvov spotrebičov
        self.df_active.loc[:, 'Název_norm'] = self.df_active['Název'].apply(self.realistic_normalize_appliance)
        
        # Ponechaj len relevantné spotrebiče
        relevant_data = self.df_active.loc[self.df_active['Název_norm'].isin(self.APPLIANCES)].copy()
        self.df_active = relevant_data
        
        # Pridanie časových období
        if not self.df_active.empty:
            self.df_active.loc[:, 'Mesiac'] = self.df_active['Datum real.'].dt.to_period('M').astype(str)
            self.df_active.loc[:, 'Štvrťrok'] = self.df_active['Datum real.'].dt.to_period('Q').astype(str)
            self.df_active.loc[:, 'Rok'] = self.df_active['Datum real.'].dt.year


    
    def realistic_normalize_appliance(self, nazev: str) -> str:
        if pd.isna(nazev):
            return 'ostatne'
        nazev_lower = str(nazev).lower().strip()

        exclude_keywords = [
            'baterie', 'příborník', 'kabel', 'trafo', 'zásuvkový systém',
            'filtr', 'svítidlo', 'lišta', 'koš', 'dávkovač', 'sifon', 'stol', 'židle',
            'konektor', 'rohový', 'designové', 'magnetický', 'plastové',
            'držák', 'krytka', 'výpusť', 'miska', 'rolovací',
            'jednotka', 'vypínač', 'track', 'line driver', 'ukončení',
            'rabat', '3d návrh', 'služba', 'polštář', 'matrace', 'spojovací',
            'vodní', 'uhlíkový', 'výztuž', 'odpadkový', 'sedací', 'souprava', 'konferenční',
            'čalouněné', 'křeslo', 'lenoška', 'deka', 'box', 'profil', 'klipy', 'koncovka',
            'sběrnice', 'napaječ', 'komín', 'potrubní', 'adaptér', 'ecotube', 'klapka',
            'čistící prostředek', 'daily clean', 'instalační', 'stabilizátor', 'sada sítka',
            'přepad', 'colorline', 'přídavný', 'pachutěsná', 'movex', 'kráječ',
            'rošt', 'twister'
        ]
        if any(keyword in nazev_lower for keyword in exclude_keywords):
            return 'ostatne'

        # Kategória digestor/odsávač - vynechať ak ide o príslušenstvo!
        if re.search(r'digestoř|digestor|odsávač|odsavač|extractor|hood', nazev_lower):
            if 'příslušenství' in nazev_lower or 'prislusenstvi' in nazev_lower:
                return 'ostatne'
            return 'digestor'

        if re.search(r'\bmikro(vln|w)\b|mikrovln|microwave|mikrovlnná', nazev_lower):
            return 'mikrovlnka'

        if re.search(r'trouba|konvektomat|parní.*troub|horkovzdušn|pyrolytick|pečic|oven|vestavná.*troub', nazev_lower):
            return 'trouba'

        if re.search(r'chladn|lednic|vinoték|vinotek|mraz(ák|nič|ička)|kombinovan.*chladnič|kombinovan.*lednic|refrigerator|freezer|komb.*lednic', nazev_lower):
            return 'chladnicka'

        if re.search(r'(varná|varna|indukční|sklokeramická|plynová).*(deska|plocha)|deska.*(indukční|varná|sklokeramická|plynová)|cooktop|hob|varná.*plocha|indukčná.*deska|indukční.*deska', nazev_lower):
            return 'varna deska'

        if re.search(r'\bmyčk|dishwash|umývačk|umývač.*nádobí|myčka.*nádobí', nazev_lower):
            return 'mycka'

        return 'ostatne'

    def get_employee_summary(self) -> pd.DataFrame:
        """Získa súhrnný prehľad podľa zamestnancov (bez delenia podľa štúdií)"""
        
        if self.df_active.empty:
            st.error("❌ Žiadne aktívne dáta po filtrovaní!")
            return pd.DataFrame()
        
        # Grupovanie len podľa zamestnanca
        summary = self.df_active.groupby(['Kontaktní osoba-Jméno a příjmení', 'Název_norm']).size().unstack(fill_value=0)
        
        # Zabezpečenie všetkých stĺpcov spotrebičov
        for appliance in self.APPLIANCES:
            if appliance not in summary.columns:
                summary[appliance] = 0
        
        # Celkový predaj
        summary['total'] = summary[self.APPLIANCES].sum(axis=1)
        
        # Flagovanie nevyváženého predaja
        def flag_low_sales(row):
            total = row['total']
            if total == 0:
                return {f'{app}_flag': False for app in self.APPLIANCES}
            
            flags = {}
            threshold = 0.15  # Menej ako 15% z celkového predaja
            
            for appliance in self.APPLIANCES:
                ratio = row[appliance] / total if total > 0 else 0
                flags[f'{appliance}_flag'] = ratio < threshold and row[appliance] < (total * 0.2)
            
            return flags
        
        # Aplikovanie flagovania
        flag_data = summary.apply(flag_low_sales, axis=1, result_type='expand')
        
        # Kombinácia dát
        result = pd.concat([summary, flag_data], axis=1).reset_index()
        
        # Zoradenie podľa celkového predaja
        result = result.sort_values('total', ascending=False)
        
        return result
    
    def get_employee_detailed_data(self, employee_name: str) -> pd.DataFrame:
        """Získa detailné dáta pre konkrétneho zamestnanca"""
        return self.df_active[
            self.df_active['Kontaktní osoba-Jméno a příjmení'] == employee_name
        ].copy()
    
    def get_time_series_data(self, employee_name: str):
        """Získa časové rady (mesačne, štvrťročne, ročne) pre zamestnanca"""
        
        employee_data = self.get_employee_detailed_data(employee_name)
        
        if employee_data.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Mesačné dáta
        monthly = employee_data.groupby(['Mesiac', 'Název_norm']).size().unstack(fill_value=0)
        for appliance in self.APPLIANCES:
            if appliance not in monthly.columns:
                monthly[appliance] = 0
        
        # Štvrťročné dáta
        quarterly = employee_data.groupby(['Štvrťrok', 'Název_norm']).size().unstack(fill_value=0)
        for appliance in self.APPLIANCES:
            if appliance not in quarterly.columns:
                quarterly[appliance] = 0
        
        # Ročné dáta
        yearly = employee_data.groupby(['Rok', 'Název_norm']).size().unstack(fill_value=0)
        for appliance in self.APPLIANCES:
            if appliance not in yearly.columns:
                yearly[appliance] = 0
        
        return monthly, quarterly, yearly
    
    def detect_imbalances(self, employee_name: str) -> Dict:
        """Detekuje nevyváženosť predaja spotrebičov"""
        employee_data = self.df_active[
            self.df_active['Kontaktní osoba-Jméno a příjmení'] == employee_name
        ]
        
        # Počet predaných kusov každého spotrebiča
        appliance_counts = employee_data.groupby('Název_norm').size()
        
        # Vypočíta priemer a štandardnú odchýlku
        mean_count = appliance_counts.mean() if len(appliance_counts) > 0 else 0
        std_count = appliance_counts.std() if len(appliance_counts) > 0 else 0
        
        # Označí spotrebiče s abnormálne nízkym predajom
        red_flags = {}
        for appliance in self.APPLIANCES:
            count = appliance_counts.get(appliance, 0)
            # Ak je počet výrazne pod priemerom
            if count < (mean_count - std_count):
                red_flags[appliance] = True
            else:
                red_flags[appliance] = False
        
        return {
            'counts': appliance_counts.to_dict(),
            'red_flags': red_flags,
            'mean': mean_count,
            'std': std_count
        }
    
    def get_overview_stats(self) -> Dict:
        """Získa celkové štatistiky"""
        if self.df_active.empty:
            return {}
        
        return {
            'total_orders': self.df_active['Doklad'].nunique(),
            'total_employees': self.df_active['Kontaktní osoba-Jméno a příjmení'].nunique(),
            'total_revenue': self.df_active['Cena/jedn.'].sum(),
            'date_range': {
                'min': self.df_active['Datum real.'].min().strftime('%Y-%m-%d'),
                'max': self.df_active['Datum real.'].max().strftime('%Y-%m-%d')
            }
        }
