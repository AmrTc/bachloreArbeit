#!/bin/bash

# Debug-Skript für Docker-Container
# Zeigt detaillierte Informationen für Fehleranalyse

echo "🔍 Debug-Informationen für Data Assistant Docker-Container"
echo "=========================================================="

# Wechsle ins deployment Verzeichnis
cd "$(dirname "$0")"

echo ""
echo "📊 Docker-Status:"
echo "================="
docker info 2>/dev/null | head -20 || echo "❌ Docker läuft nicht"

echo ""
echo "🐳 Docker Compose Version:"
echo "=========================="
docker-compose --version || echo "❌ Docker Compose nicht verfügbar"

echo ""
echo "📁 Aktuelles Verzeichnis:"
echo "=========================="
pwd
ls -la

echo ""
echo "📋 Docker Compose Konfiguration:"
echo "================================"
docker-compose config || echo "❌ Konfigurationsfehler"

echo ""
echo "📦 Docker Images:"
echo "================="
docker images | grep -E "(data_assistant|streamlit)" || echo "Keine relevanten Images gefunden"

echo ""
echo "🚢 Docker Container:"
echo "==================="
docker ps -a | grep -E "(data_assistant|streamlit)" || echo "Keine relevanten Container gefunden"

echo ""
echo "🌐 Netzwerk-Status:"
echo "=================="
docker network ls | grep deployment || echo "Kein deployment Netzwerk gefunden"

echo ""
echo "💾 Disk-Speicher:"
echo "================="
df -h | head -5

echo ""
echo "🔧 System-Informationen:"
echo "========================"
echo "OS: $(uname -a)"
echo "Python: $(python3 --version 2>/dev/null || echo 'Nicht verfügbar')"
echo "Port 8501: $(lsof -i :8501 2>/dev/null || echo 'Nicht belegt')"

echo ""
echo "📝 Container-Logs (falls vorhanden):"
echo "==================================="
if docker-compose ps | grep -q "Up"; then
    docker-compose logs --tail=20
else
    echo "Keine laufenden Container gefunden"
fi

echo ""
echo "🔍 Debug abgeschlossen!"
echo "Verwende 'docker-compose logs' für detaillierte Logs"
