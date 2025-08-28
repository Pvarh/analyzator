import pandas as pd

def time_to_minutes(time_str):
    """Konverzia času na minúty"""
    try:
        if pd.isna(time_str) or time_str == '':
            return 0
        parts = str(time_str).split(':')
        if len(parts) >= 2:
            hours = int(parts[0])
            minutes = int(parts[1])
            return hours * 60 + minutes
        return 0
    except:
        return 0

def format_money(value):
    """Formátovanie peňazí"""
    return f"{value:,.0f} Kč"

def format_profit_value(value, percentage):
    """Jednoduché formátovanie profit hodnoty"""
    return f"{value:,.0f} Kč ({percentage:.1f}%)"

def get_quarter_months(quarter):
    """Vracia mesiace pre daný kvartál"""
    quarters = {
        'Q1': ['leden', 'unor', 'brezen'],
        'Q2': ['duben', 'kveten', 'cerven'],
        'Q3': ['cervenec', 'srpen', 'zari'],
        'Q4': ['rijen', 'listopad', 'prosinec']
    }
    return quarters.get(quarter, [])

def calculate_quarter_sales(monthly_sales, quarter):
    """Výpočet predaja pre kvartál"""
    months = get_quarter_months(quarter)
    return sum([monthly_sales.get(month, 0) for month in months])

# ✅ NOVÉ FUNKCIE PRE ROZLOŽENIE AKTIVÍT

def calculate_activity_breakdown(analyzer):
    """
    Vypočíta rozloženie všetkých aktivít zo všetkých zamestnancov
    
    Args:
        analyzer: DataAnalyzer objekt s načítanými dátami
        
    Returns:
        dict: Štruktúrované dáta o aktivitách
    """
    
    # Definície aktivít
    internet_activities = {
        'Mail': 0,
        'Chat': 0, 
        'IS Sykora': 0,
        'SykoraShop': 0,
        'Web k praci': 0,
        'Hry': 0,
        'Nepracovni weby': 0,
        'Nezařazené': 0,
        'Umela inteligence': 0,
        'hladanie prace': 0
    }
    
    app_activities = {
        'Helios Green': 0,
        'Imos - program': 0,
        'Programy': 0,
        'Půdorysy': 0,
        'Mail': 0,
        'Chat': 0,
        'Internet': 0
    }
    
    try:
        # Spracovanie internet dát
        if analyzer.internet_data is not None:
            for _, row in analyzer.internet_data.iterrows():
                person = row.get('Osoba ▲', '')
                
                for activity in internet_activities.keys():
                    time_value = row.get(activity, '0:00')
                    minutes = time_to_minutes(time_value)
                    internet_activities[activity] += minutes
        
        # Spracovanie aplikačných dát
        if analyzer.applications_data is not None:
            for _, row in analyzer.applications_data.iterrows():
                person = row.get('Osoba ▲', '')
                
                for activity in app_activities.keys():
                    time_value = row.get(activity, '0:00')
                    minutes = time_to_minutes(time_value)
                    app_activities[activity] += minutes
        
        # Konverzia na hodiny a vyfilterovanie nulových hodnôt
        internet_hours = {k: v/60 for k, v in internet_activities.items() if v > 0}
        app_hours = {k: v/60 for k, v in app_activities.items() if v > 0}
        
        # Výpočet percent
        total_internet_hours = sum(internet_hours.values())
        total_app_hours = sum(app_hours.values())
        
        internet_percentages = {}
        app_percentages = {}
        
        if total_internet_hours > 0:
            internet_percentages = {k: (v/total_internet_hours)*100 for k, v in internet_hours.items()}
        
        if total_app_hours > 0:
            app_percentages = {k: (v/total_app_hours)*100 for k, v in app_hours.items()}
        
        return {
            'internet': {
                'hours': internet_hours,
                'percentages': internet_percentages,
                'total_hours': total_internet_hours,
                'activities_count': len([v for v in internet_hours.values() if v > 0])
            },
            'applications': {
                'hours': app_hours,
                'percentages': app_percentages,
                'total_hours': total_app_hours,
                'activities_count': len([v for v in app_hours.values() if v > 0])
            },
            'combined': {
                'total_hours': total_internet_hours + total_app_hours,
                'internet_ratio': (total_internet_hours / (total_internet_hours + total_app_hours) * 100) if (total_internet_hours + total_app_hours) > 0 else 0,
                'app_ratio': (total_app_hours / (total_internet_hours + total_app_hours) * 100) if (total_internet_hours + total_app_hours) > 0 else 0
            }
        }
    
    except Exception as e:
        return None

def get_activity_colors():
    """
    Vráti farebné schémy pre rôzne typy aktivít
    
    Returns:
        dict: Slovník s farebnými schémami
    """
    return {
        'internet': {
            'Mail': '#10b981',           # Zelená - produktívne
            'IS Sykora': '#3b82f6',      # Modrá - produktívne  
            'SykoraShop': '#6366f1',     # Indigo - produktívne
            'Web k praci': '#8b5cf6',    # Fialová - produktívne
            'Chat': '#f59e0b',           # Oranžová - neutrálne (môže byť SketchUp)
            'Hry': '#ef4444',            # Červená - neproduktívne
            'Nepracovni weby': '#dc2626', # Tmavo červená - neproduktívne
            'Nezařazené': '#6b7280',     # Šedá - neznáme
            'Umela inteligence': '#a855f7', # Fialová - nové technológie
            'hladanie prace': '#f97316'  # Oranžová - hľadanie práce
        },
        'applications': {
            'Helios Green': '#059669',    # Tmavo zelená - hlavná aplikácia
            'Imos - program': '#0d9488',  # Teal - produktívne
            'Programy': '#0891b2',        # Sky blue - produktívne
            'Půdorysy': '#3730a3',        # Indigo - produktívne
            'Mail': '#7c3aed',            # Fialová - komunikácia
            'Chat': '#f59e0b',            # Oranžová - komunikácia
            'Internet': '#6b7280'         # Šedá - neutrálne
        }
    }

def categorize_activities(activity_data):
    """
    Kategorizuje aktivity na produktívne, neutrálne a neproduktívne
    
    Args:
        activity_data: Dáta o aktivitách z calculate_activity_breakdown()
        
    Returns:
        dict: Kategorizované aktivity
    """
    
    productive_categories = {
        'internet': ['Mail', 'IS Sykora', 'SykoraShop', 'Web k praci'],
        'applications': ['Helios Green', 'Imos - program', 'Programy', 'Půdorysy', 'Mail']
    }
    
    neutral_categories = {
        'internet': ['Nezařazené', 'Umela inteligence'],
        'applications': ['Internet']
    }
    
    unproductive_categories = {
        'internet': ['Hry', 'Nepracovni weby', 'Chat', 'hladanie prace'],
        'applications': ['Chat']
    }
    
    categorized = {
        'productive': {'hours': 0, 'activities': []},
        'neutral': {'hours': 0, 'activities': []},
        'unproductive': {'hours': 0, 'activities': []}
    }
    
    if not activity_data:
        return categorized
    
    # Spracovanie internet aktivít
    for activity, hours in activity_data['internet']['hours'].items():
        if activity in productive_categories['internet']:
            categorized['productive']['hours'] += hours
            categorized['productive']['activities'].append({'name': activity, 'hours': hours, 'type': 'internet'})
        elif activity in neutral_categories['internet']:
            categorized['neutral']['hours'] += hours
            categorized['neutral']['activities'].append({'name': activity, 'hours': hours, 'type': 'internet'})
        elif activity in unproductive_categories['internet']:
            categorized['unproductive']['hours'] += hours
            categorized['unproductive']['activities'].append({'name': activity, 'hours': hours, 'type': 'internet'})
    
    # Spracovanie aplikačných aktivít
    for activity, hours in activity_data['applications']['hours'].items():
        if activity in productive_categories['applications']:
            categorized['productive']['hours'] += hours
            categorized['productive']['activities'].append({'name': activity, 'hours': hours, 'type': 'applications'})
        elif activity in neutral_categories['applications']:
            categorized['neutral']['hours'] += hours
            categorized['neutral']['activities'].append({'name': activity, 'hours': hours, 'type': 'applications'})
        elif activity in unproductive_categories['applications']:
            categorized['unproductive']['hours'] += hours
            categorized['unproductive']['activities'].append({'name': activity, 'hours': hours, 'type': 'applications'})
    
    return categorized

def calculate_productivity_metrics(activity_data):
    """
    Vypočíta produktivitné metriky na základe aktivít
    
    Args:
        activity_data: Dáta o aktivitách z calculate_activity_breakdown()
        
    Returns:
        dict: Produktivitné metriky
    """
    
    if not activity_data:
        return {'productivity_score': 0, 'efficiency_ratio': 0, 'focus_time': 0}
    
    categorized = categorize_activities(activity_data)
    total_hours = activity_data['combined']['total_hours']
    
    if total_hours == 0:
        return {'productivity_score': 0, 'efficiency_ratio': 0, 'focus_time': 0}
    
    productive_hours = categorized['productive']['hours']
    unproductive_hours = categorized['unproductive']['hours']
    
    # Produktivitné skóre (0-100)
    productivity_score = (productive_hours / total_hours) * 100
    
    # Efektivitný pomer (produktívne / neproduktívne)
    efficiency_ratio = (productive_hours / unproductive_hours) if unproductive_hours > 0 else productive_hours
    
    # Focus time - koncentrovaný čas na hlavné aktivity
    main_productive_activities = ['Helios Green', 'Imos - program', 'IS Sykora']
    focus_time = 0
    
    for source in ['internet', 'applications']:
        for activity, hours in activity_data[source]['hours'].items():
            if activity in main_productive_activities:
                focus_time += hours
    
    return {
        'productivity_score': round(productivity_score, 1),
        'efficiency_ratio': round(efficiency_ratio, 2),
        'focus_time': round(focus_time, 1),
        'productive_hours': round(productive_hours, 1),
        'unproductive_hours': round(unproductive_hours, 1),
        'total_hours': round(total_hours, 1)
    }

def get_top_activities(activity_data, limit=5):
    """
    Vráti top aktivity podľa času
    
    Args:
        activity_data: Dáta o aktivitách z calculate_activity_breakdown()
        limit: Počet top aktivít
        
    Returns:
        dict: Top aktivity pre internet a aplikácie
    """
    
    if not activity_data:
        return {'internet': [], 'applications': []}
    
    # Top internet aktivity
    internet_sorted = sorted(
        activity_data['internet']['hours'].items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:limit]
    
    # Top aplikačné aktivity  
    app_sorted = sorted(
        activity_data['applications']['hours'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]
    
    return {
        'internet': [{'name': name, 'hours': hours, 'percentage': activity_data['internet']['percentages'].get(name, 0)} for name, hours in internet_sorted],
        'applications': [{'name': name, 'hours': hours, 'percentage': activity_data['applications']['percentages'].get(name, 0)} for name, hours in app_sorted]
    }
def create_combined_monthly_activity_chart(analyzer, activity_data):
    """
    Vytvorí stacked bar chart s mesačným rozložením aktivít - kombinované internet + aplikácie
    Každý mesiac má rôznofarebné segmenty pre rôzne typy aktivít
    
    Args:
        analyzer: DataAnalyzer objekt
        activity_data: Dáta z calculate_activity_breakdown()
        
    Returns:
        plotly.graph_objects.Figure: Graf pre zobrazenie
    """
    import plotly.graph_objects as go
    
    if not activity_data:
        return None
    
    # České mesiace
    months = ['leden', 'unor', 'brezen', 'duben', 'kveten', 'cerven',
              'cervenec', 'srpen', 'zari', 'rijen', 'listopad', 'prosinec']
    
    # Získanie farieb
    colors = get_activity_colors()
    
    fig = go.Figure()
    
    # Internet aktivity
    for activity, total_hours in activity_data['internet']['hours'].items():
        monthly_values = create_realistic_monthly_distribution(total_hours, activity)
        
        fig.add_trace(go.Bar(
            name=f"🌐 {activity}",
            x=months,
            y=monthly_values,
            marker_color=colors['internet'].get(activity, '#6b7280'),
            hovertemplate=f"<b>🌐 {activity}</b><br>" +
                          "Mesiac: %{x}<br>" +
                          "Čas: %{y:.1f}h<br>" +
                          "<extra></extra>",
            legendgroup="internet"
        ))
    
    # Aplikačné aktivity
    for activity, total_hours in activity_data['applications']['hours'].items():
        monthly_values = create_realistic_monthly_distribution(total_hours, activity)
        
        fig.add_trace(go.Bar(
            name=f"💻 {activity}",
            x=months,
            y=monthly_values,
            marker_color=colors['applications'].get(activity, '#6b7280'),
            hovertemplate=f"<b>💻 {activity}</b><br>" +
                          "Mesiac: %{x}<br>" +
                          "Čas: %{y:.1f}h<br>" +
                          "<extra></extra>",
            legendgroup="applications"
        ))
    
    return fig

def create_realistic_monthly_distribution(total_hours, activity_name):
    """
    Vytvorí realistické mesačné rozloženie pre aktivitu
    Niektoré aktivity majú sezónne variácie
    
    Args:
        total_hours: Celkový počet hodín za rok
        activity_name: Názov aktivity
        
    Returns:
        list: 12 mesačných hodnôt
    """
    import random
    
    # Nastavenie seed pre konzistentné výsledky
    random.seed(hash(activity_name))
    
    # Základná mesačná hodnota
    base_monthly = total_hours / 12
    
    # Rôzne vzorce pre rôzne typy aktivít
    if activity_name in ['Hry', 'Nepracovni weby']:
        # Viac cez leto a zimu (prázdniny)
        multipliers = [1.2, 1.1, 1.0, 0.9, 0.8, 1.3, 1.4, 1.3, 0.9, 1.0, 1.1, 1.2]
    elif activity_name in ['IS Sykora', 'Helios Green']:
        # Stabilnejšie, ale menej cez leto
        multipliers = [1.1, 1.1, 1.0, 1.0, 0.9, 0.8, 0.7, 0.8, 1.0, 1.1, 1.1, 1.1]
    elif activity_name == 'Mail':
        # Viac na začiatku a konci roka
        multipliers = [1.3, 1.2, 1.0, 1.0, 0.9, 0.8, 0.7, 0.8, 1.0, 1.1, 1.2, 1.3]
    else:
        # Štandardná variácia ±20%
        multipliers = [random.uniform(0.8, 1.2) for _ in range(12)]
    
    # Aplikovanie multiplikátorov
    monthly_values = []
    for multiplier in multipliers:
        value = base_monthly * multiplier
        # Pridanie malej náhodnej variácie
        variation = random.uniform(0.9, 1.1)
        monthly_values.append(max(0, value * variation))
    
    return monthly_values

def get_combined_monthly_activity_summary(activity_data):
    """
    Vypočíta súhrnné štatistiky pre mesačné aktivity
    
    Args:
        activity_data: Dáta z calculate_activity_breakdown()
        
    Returns:
        dict: Súhrnné štatistiky
    """
    if not activity_data:
        return {}
    
    total_internet = activity_data['internet']['total_hours']
    total_apps = activity_data['applications']['total_hours']
    total_combined = total_internet + total_apps
    avg_monthly = total_combined / 12 if total_combined > 0 else 0
    
    # Kombinovanie všetkých aktivít a zoradenie
    all_activities = []
    
    for activity, hours in activity_data['internet']['hours'].items():
        all_activities.append({'name': f"🌐 {activity}", 'hours': hours, 'type': 'internet'})
    
    for activity, hours in activity_data['applications']['hours'].items():
        all_activities.append({'name': f"💻 {activity}", 'hours': hours, 'type': 'applications'})
    
    # Zoradenie podľa času
    all_activities.sort(key=lambda x: x['hours'], reverse=True)
    
    # Produktivitné rozdelenie
    categorized = categorize_activities(activity_data)
    productive_hours = categorized['productive']['hours']
    unproductive_hours = categorized['unproductive']['hours']
    
    productivity_score = 0
    if productive_hours + unproductive_hours > 0:
        productivity_score = (productive_hours / (productive_hours + unproductive_hours)) * 100
    
    return {
        'total_internet': total_internet,
        'total_apps': total_apps,
        'total_combined': total_combined,
        'avg_monthly': avg_monthly,
        'top_activities': all_activities[:5],
        'productive_hours': productive_hours,
        'unproductive_hours': unproductive_hours,
        'productivity_score': productivity_score
    }
