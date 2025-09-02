# Error Handling Systém

Komplexný error handling systém pre Analyzator aplikáciu.

## 📋 Funkcie

### 🔧 Automatické logovanie chýb
- Všetky chyby sa automaticky logujú do `logs/errors.json`
- Obsahuje informácie o používateľovi, kontexte, session state
- Stack trace pre debugovanie

### 🎯 Dekorátor `@handle_error`
```python
from core.error_handler import handle_error

@handle_error
def my_function():
    # Váš kód tu
    pass
```

### 📊 Admin panel monitoring
- Nový tab "🐛 Error Logs" v admin paneli
- Prehľad nedávnych chýb
- Štatistiky typov chýb a používateľov
- Čistenie starých chýb

## 🚀 Použitie

### 1. Automatické logovanie
```python
from core.error_handler import log_error

try:
    # riziková operácia
    dangerous_operation()
except Exception as e:
    log_error(e, context={"operation": "dangerous_operation"})
```

### 2. Dekorátor pre funkcie
```python
@handle_error
def process_data():
    # Akákoľvek chyba tu bude automaticky zalogovaná
    return result
```

### 3. Admin monitoring
- Prejdite do Admin panelu
- Kliknite na tab "🐛 Error Logs"
- Sledujte chyby v reálnom čase

## 📁 Súbory

### `core/error_handler.py`
- Hlavná trieda `ErrorHandler`
- Dekorátor `@handle_error`
- Utility funkcie

### `logs/errors.json`
- JSON súbor s error logmi
- Automaticky sa vytvára
- Max 1000 posledných chýb

### `logs/app.log`
- Štandardný log súbor
- Všetky úrovne logov

## 🔒 Bezpečnosť

- Session state sa filtruje pre bezpečnosť
- Používateľské údaje sú anonymizované
- Stacktrace len pre adminov

## 🧹 Údržba

- Staré chyby sa automaticky čistia
- Admin môže manuálne vyčistiť logy
- Rotácia logov po 30 dňoch

## 📈 Štatistiky

V admin paneli môžete sledovať:
- Najčastejšie typy chýb
- Používateľov s najviac chybami  
- Časové trendy chýb
- Detailné stack traces
