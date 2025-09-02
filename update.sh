#!/bin/bash
#
# Analyzator Update Script
# Tento skript aktualizuje aplikáciu z GitHub repozitára a reštartuje Docker kontajner
#

echo "🔄 Analyzator Update Script"
echo "=========================="

# Kontrola, či sme v správnom adresári
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ ERROR: docker-compose.yml nenájdený! Spustite skript v root adresári analyzátora."
    exit 1
fi

echo "📥 Sťahujem najnovšie zmeny z GitHub..."
git pull origin main

if [ $? -ne 0 ]; then
    echo "❌ ERROR: Git pull zlyhal!"
    exit 1
fi

echo "� Zastavujem Docker kontajner..."
docker-compose down

echo "🚀 Spúšťam aktualizovaný Docker kontajner..."
docker-compose up --build -d

if [ $? -eq 0 ]; then
    echo "✅ Aktualizácia úspešná!"
    echo "🌐 Aplikácia je dostupná na: http://$(hostname -I | awk '{print $1}'):8501"
    
    echo ""
    echo "📊 Status kontajnera:"
    docker-compose ps
    
    echo ""
    echo "📋 Pre sledovanie logov použite:"
    echo "   docker-compose logs -f analyzator"
else
    echo "❌ ERROR: Spustenie kontajnera zlyhalo!"
    exit 1
fi

echo ""
echo "🎉 Update dokončený!"