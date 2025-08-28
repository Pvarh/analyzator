#!/bin/bash

echo "🔄 Aktualizujem Analyzator..."

# Backup aktuálnej verzie
echo "📦 Vytváram zálohu..."
cp -r /home/user/analyzator /home/user/analyzator-backup-$(date +%Y%m%d-%H%M%S)

# Prejsť do adresára
cd /home/user/analyzator

# Zastaviť aplikáciu
echo "⏸️ Zastavujem aplikáciu..."
docker-compose down

# Stiahnuť najnovšie zmeny
echo "⬇️ Sťahujem zmeny..."
git pull origin main

# Rebuild a spustiť
echo "🔨 Rebuilding a spúšťam..."
docker-compose up -d --build

# Počkať na spustenie
echo "⏳ Čakám na spustenie..."
sleep 15

# Kontrola stavu
echo "📊 Kontrola stavu..."
docker-compose ps

echo "✅ Aktualizácia dokončená!"
echo "🌐 App dostupná na: http://$(hostname -I | awk '{print $1}'):8501"