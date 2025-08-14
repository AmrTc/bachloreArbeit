# Lokaler Docker-Test für Data Assistant Project

Dieses Verzeichnis enthält alle notwendigen Dateien und Skripte, um die Docker-Container lokal zu testen, bevor sie auf AWS deployed werden.

## 🚀 Schnellstart

### Voraussetzungen
- Docker Desktop installiert und läuft
- Docker Compose verfügbar
- Terminal/Command Line

### Option 1: Vollständiger Test (Empfohlen)
```bash
./local-test.sh
```

### Option 2: Schnelltest
```bash
./quick-test.sh
```

## 📁 Dateien

### Docker-Dateien
- `Dockerfile` - Produktions-Dockerfile für die Anwendung
- `docker-compose.yml` - Docker Compose Konfiguration
- `.dockerignore` - Dateien, die vom Docker-Build ausgeschlossen werden

### Skripte
- `local-test.sh` - Vollständiger lokaler Test mit allen Checks
- `quick-test.sh` - Einfacher Schnelltest
- `start.sh` - Lokales Start-Skript ohne Docker

### Konfiguration
- `requirements-production.txt` - Python-Dependencies für Produktion
- `requirements.txt` - Python-Dependencies für Entwicklung

## 🔧 Manuelle Schritte

### 1. Container bauen
```bash
cd new_data_assistant_project/deployment
docker-compose build
```

### 2. Container starten
```bash
docker-compose up -d
```

### 3. Status prüfen
```bash
docker-compose ps
docker-compose logs -f
```

### 4. Anwendung testen
```bash
curl http://localhost:8501/_stcore/health
```

### 5. Container stoppen
```bash
docker-compose down
```

## 🌐 Zugriff

Nach erfolgreichem Start ist die Anwendung verfügbar unter:
- **URL**: http://localhost:8501
- **Health Check**: http://localhost:8501/_stcore/health

## 🐛 Troubleshooting

### Häufige Probleme

#### 1. Port 8501 bereits belegt
```bash
# Prüfe, was den Port belegt
lsof -i :8501

# Stoppe den Prozess oder ändere den Port in docker-compose.yml
```

#### 2. Docker Build fehlgeschlagen
```bash
# Bereinige Docker-Cache
docker system prune -a

# Baue neu ohne Cache
docker-compose build --no-cache
```

#### 3. Container startet nicht
```bash
# Zeige detaillierte Logs
docker-compose logs

# Prüfe Container-Status
docker-compose ps
```

#### 4. Anwendung nicht erreichbar
```bash
# Prüfe Container-Logs
docker-compose logs streamlit-app

# Prüfe Netzwerk
docker network ls
docker network inspect data_assistant_project_default
```

### Debug-Befehle

```bash
# Shell im Container öffnen
docker-compose exec streamlit-app bash

# Container-Informationen
docker inspect data_assistant_project_streamlit-app_1

# Ressourcen-Verbrauch
docker stats
```

## 📊 Monitoring

### Container-Status
```bash
docker-compose ps
```

### Logs verfolgen
```bash
docker-compose logs -f streamlit-app
```

### Ressourcen
```bash
docker stats
```

## 🔄 Entwicklung

### Code-Änderungen testen
1. Code ändern
2. Container neu bauen: `docker-compose build`
3. Container neu starten: `docker-compose up -d`

### Hot-Reload (für Entwicklung)
```bash
# Starte mit Volume-Mounts für Code-Änderungen
docker-compose up -d
```

## 🚀 Deployment

Nach erfolgreichem lokalen Test können die Container auf AWS deployed werden:

1. **EC2-Instanz vorbereiten**
2. **Docker installieren**
3. **Code deployen**
4. **Container starten**

## 📝 Notizen

- Der lokale Test verwendet die gleichen Docker-Images wie die Produktion
- Alle Umgebungsvariablen sind in `docker-compose.yml` konfiguriert
- Die Anwendung läuft im Container als nicht-root Benutzer (Sicherheit)
- Health-Checks sind konfiguriert für automatische Überwachung
