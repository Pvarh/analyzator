# 📊 Analyzator - Správa dát

Aplikácia pre analýzu predajných dát so Streamlit rozhraním a pokročilou správou súborov.

## 🚀 Rýchly štart

### Lokálne spustenie
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
streamlit run app.py
```

### Docker spustenie
```bash
docker-compose up -d --build
```

## 📁 Správa dát cez Admin Panel

### Prístup
1. Prihlás sa ako admin (`pvarhalik@sykora.eu`) - Peter Varhalik
2. Choď do **Admin Panel** → **Správa dát**

### Funkcie
- **📤 Upload súborov** - Drag & drop alebo browse súbory
- **👁️ Náhľad súborov** - Preview prvých 10 riadkov
- **📥 Stiahnutie** - Download súborov
- **🗑️ Mazanie** - Bezpečné mazanie s potvrdením
- **💾 Zálohovanie** - Automatické zálohy pri prepísaní
- **📊 Štatistiky** - Celková veľkosť a počet súborov

### Podporované kategórie
- **📊 Excel súbory (Predajné dáta)** - `data/raw/`
  - Prodej-*.xlsx súbory
  - Report_Applications_*.xlsx
  - Report_Internet_*.xlsx

- **🏢 Studio dáta** - `data/studio/`
  - Studio reporty pre analýzu zamestnancov
  - Cross-matching súbory

### Podporované formáty
- `.xlsx` - Excel 2007+
- `.xls` - Excel starší
- `.csv` - Comma separated values

## 🔧 Bezpečnostné funkcie

- **🔒 Admin prístup** - Len administrátori môžu spravovať súbory
- **💾 Automatické zálohy** - Pri prepísaní súboru sa vytvorí záloha
- **⚠️ Potvrdenie mazania** - Dvojklik pre bezpečné mazanie
- **📊 Validácia súborov** - Kontrola formátu pri upload

## 🎯 Používateľské rozhranie

### Upload proces
1. Vyber kategóriu súborov
2. Drag & drop súbory alebo klikni na "Browse files"
3. Skontroluj zoznam súborov na upload
4. Klikni "⬆️ Uložiť súbory"
5. Sleduj progress bar
6. Potvrdenie úspešného upload

### Správa existujúcich súborov
1. Vyber kategóriu
2. Zobrazí sa zoznam súborov s metadátami:
   - 📄 Názov súboru
   - 📅 Dátum poslednej úpravy  
   - 💾 Veľkosť súboru
3. Operácie:
   - **👁️ Náhľad** - Zobrazí prvých 10 riadkov
   - **📥 Stiahnuť** - Download súboru
   - **🗑️ Zmazать** - Bezpečné mazanie

### Štatistiky priečinka
- 📄 **Celkom súborov** - Počet všetkých súborov
- 📊 **Dátové súbory** - Počet .xlsx/.xls/.csv súborov
- 💾 **Celková veľkosť** - Suma všetkých súborov

## 🌐 Server deployment

### Git workflow
```bash
# Windows
git add .
git commit -m "Update: nové súbory/funkcie"
git push origin main

# Server
ssh user@server
cd /path/to/analyzator
./update.sh
```

### Docker na serveri
```bash
# Prvé nasadenie
git clone https://github.com/user/analyzator.git
cd analyzator
cp auth/sessions.template.json auth/sessions.json
docker-compose up -d --build

# Aktualizácie
git pull origin main
docker-compose down
docker-compose up -d --build
```

## 🔄 Aktualizačný workflow

### Vývoj (Windows)
1. Urob zmeny v kóde
2. Test lokálne na `http://localhost:8501`
3. Git commit & push

### Produkcia (Server)
1. SSH na server
2. `./update.sh` alebo manuálne:
   ```bash
   git pull origin main
   docker-compose down
   docker-compose up -d --build
   ```

## 📋 TODO / Plány

- [ ] **S3 integrácia** - Cloud storage pre súbory
- [ ] **SFTP upload** - Vzdialený upload súborov
- [ ] **Scheduled imports** - Automatické načítavanie dát
- [ ] **API endpoints** - REST API pre upload/download
- [ ] **Audit log** - Sledovanie zmien súborov
- [ ] **Bulk operations** - Hromadné operácie

## 🎯 Technické detaily

### Architektúra
```
analyzator/
├── app.py              # Main aplikácia
├── auth/               # Autentifikácia + admin
│   ├── admin.py       # Admin panel s data management
│   ├── auth.py        # Auth funkcie
│   └── users_db.py    # User databáza
├── data/              # Dátové súbory
│   ├── raw/          # Excel predajné dáta
│   └── studio/       # Studio dáta
├── core/              # Business logika
├── ui/                # UI komponenty
└── Docker files       # Kontajnerizácia
```

### Závislosti
- `streamlit` - Web framework
- `pandas` - Dátové operácie
- `plotly` - Grafy a vizualizácie
- `openpyxl` - Excel súbory

---

**Aplikácia je pripravená na produkčné nasadenie! 🚀**
