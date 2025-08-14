# Übersicht aller verfügbaren Skripte

## 🚀 Hauptskripte

### `start-docker.sh` - Docker-Status-Check
**Verwendung:** `./start-docker.sh`
- Prüft, ob Docker läuft
- Gibt Hilfestellung bei Problemen
- **Erste Anlaufstelle für alle Tests**

### `local-test.sh` - Vollständiger lokaler Test
**Verwendung:** `./local-test.sh`
- Vollständiger Docker-Test mit allen Checks
- Automatische Fehlerbehandlung
- Detaillierte Ausgabe und Logging
- **Empfohlen für gründliche Tests**

### `quick-test.sh` - Schnelltest
**Verwendung:** `./quick-test.sh`
- Einfacher, schneller Docker-Test
- Weniger detailliert, aber schnell
- **Gut für schnelle Überprüfungen**

### `debug.sh` - Debug-Informationen
**Verwendung:** `./debug.sh`
- Zeigt detaillierte System-Informationen
- Hilft bei der Fehleranalyse
- **Verwende bei Problemen**

## 🔧 Hilfsskripte

### `start.sh` - Lokales Start-Skript (ohne Docker)
**Verwendung:** `./start.sh`
- Startet die Anwendung lokal ohne Docker
- Verwendet Python Virtual Environment
- **Für lokale Entwicklung ohne Container**

## 📋 Verwendungsreihenfolge

### 1. Erste Schritte
```bash
./start-docker.sh
```
- Prüft Docker-Status
- Gibt Anweisungen bei Problemen

### 2. Docker starten (falls nicht läuft)
- Öffne Docker Desktop App
- Warte bis der Docker-Whale grün wird
- Führe `./start-docker.sh` erneut aus

### 3. Lokalen Test durchführen
```bash
# Für gründliche Tests:
./local-test.sh

# Für schnelle Tests:
./quick-test.sh
```

### 4. Bei Problemen
```bash
./debug.sh
```

## 🎯 Empfohlener Workflow

1. **Start:** `./start-docker.sh`
2. **Docker starten** (falls nötig)
3. **Test:** `./local-test.sh`
4. **Bei Problemen:** `./debug.sh`
5. **Für Updates:** `./quick-test.sh`

## 📚 Weitere Hilfe

- **README.md** - Vollständige Dokumentation
- **Docker-Logs:** `docker-compose logs -f`
- **Container-Status:** `docker-compose ps`
- **Container stoppen:** `docker-compose down`

## 🚨 Wichtige Hinweise

- Alle Skripte müssen im `deployment/` Verzeichnis ausgeführt werden
- Docker Desktop muss laufen, bevor Tests durchgeführt werden können
- Bei Problemen immer zuerst `./debug.sh` verwenden
- Die Skripte sind für macOS/Linux optimiert
