#!/bin/bash

# Schnelltest-Skript für Docker-Container
# Einfache Version für schnelle Tests

echo "🚀 Schnelltest für Data Assistant Docker-Container"

# Wechsle ins deployment Verzeichnis
cd "$(dirname "$0")"

# Stoppe alte Container
echo "🛑 Stoppe alte Container..."
docker-compose down 2>/dev/null || true

# Baue und starte
echo "🔨 Baue Image..."
docker-compose build

echo "🚀 Starte Container..."
docker-compose up -d

echo "⏳ Warte auf Start..."
sleep 15

# Zeige Status
echo "📊 Container-Status:"
docker-compose ps

echo "📝 Logs:"
docker-compose logs --tail=10

echo ""
echo "🌐 Teste Anwendung:"
if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo "✅ Anwendung läuft auf http://localhost:8501"
else
    echo "❌ Anwendung nicht erreichbar"
    echo "📝 Zeige alle Logs:"
    docker-compose logs
fi

echo ""
echo "🛑 Zum Stoppen: docker-compose down"
