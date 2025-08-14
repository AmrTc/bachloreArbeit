#!/bin/bash

# Docker-Start-Hilfe-Skript
# Prüft Docker-Status und gibt Hilfestellung

echo "🐳 Docker-Status-Check für Data Assistant Project"
echo "================================================="

# Prüfe Docker-Status
if docker info > /dev/null 2>&1; then
    echo "✅ Docker läuft bereits!"
    echo "Du kannst jetzt die Tests durchführen:"
    echo "  ./local-test.sh    # Vollständiger Test"
    echo "  ./quick-test.sh    # Schnelltest"
    echo "  ./debug.sh         # Debug-Informationen"
else
    echo "❌ Docker läuft nicht!"
    echo ""
    echo "🔧 Lösungsvorschläge:"
    echo ""
    echo "1. Docker Desktop starten:"
    echo "   - Öffne Docker Desktop App"
    echo "   - Warte bis der Docker-Whale grün wird"
    echo ""
    echo "2. Terminal neu starten:"
    echo "   - Schließe dieses Terminal"
    echo "   - Öffne ein neues Terminal"
    echo "   - Führe das Skript erneut aus"
    echo ""
    echo "3. Docker-Status prüfen:"
    echo "   docker --version"
    echo "   docker info"
    echo ""
    echo "4. Nach dem Start von Docker Desktop:"
    echo "   ./local-test.sh"
    echo ""
    echo "💡 Tipp: Docker Desktop läuft im Hintergrund"
    echo "   und muss manchmal manuell gestartet werden"
fi

echo ""
echo "📚 Weitere Hilfe:"
echo "================="
echo "README.md - Vollständige Dokumentation"
echo "local-test.sh - Vollständiger lokaler Test"
echo "quick-test.sh - Schneller Test"
echo "debug.sh - Debug-Informationen"
