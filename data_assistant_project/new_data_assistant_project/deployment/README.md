# 🚀 Deployment Guide - Data Assistant Project

## Übersicht

Dieses Verzeichnis enthält alle notwendigen Dateien und Skripte für die Bereitstellung des Data Assistant Projekts auf einer VM. Sie haben zwei Hauptoptionen:

1. **Direkte Installation** - Installation direkt auf der VM
2. **Docker Container** - Containerisierte Bereitstellung

## 📁 Dateien in diesem Verzeichnis

| Datei                  | Beschreibung                                              |
| ---------------------- | --------------------------------------------------------- |
| `deploy.sh`          | Automatisches Deployment-Skript für direkte Installation |
| `docker-deploy.sh`   | Docker-Deployment-Skript für Container                   |
| `Dockerfile`         | Docker-Image-Definition                                   |
| `docker-compose.yml` | Docker Compose-Konfiguration                              |
| `VM_SETUP_GUIDE.md`  | Detaillierte Schritt-für-Schritt Anleitung               |

## 🚀 Schnellstart

### Option 1: Direkte Installation (Empfohlen für Entwicklung)

```bash
# 1. Dateien auf VM übertragen
scp -r new_data_assistant_project/ tchagnaoso@tchagn01.stud.fim.uni-passau.de:/opt/

# 2. Auf VM verbinden
ssh tchagnaoso@tchagn01.stud.fim.uni-passau.de

# 3. Deployment ausführen
cd /opt/new_data_assistant_project/deployment
sudo chmod +x deploy.sh
./deploy.sh
```

### Option 2: Docker Container (Empfohlen für Produktion)

```bash
# 1. Dateien auf VM übertragen
scp -r new_data_assistant_project/ user@your-vm-ip:/opt/

# 2. Auf VM verbinden
ssh user@your-vm-ip

# 3. Docker installieren (falls nötig)
cd /opt/new_data_assistant_project/deployment
./docker-deploy.sh install-docker

# 4. Neu einloggen für Docker-Gruppe
exit
ssh user@your-vm-ip

# 5. Deployment ausführen
cd /opt/new_data_assistant_project/deployment
./docker-deploy.sh deploy
```

## 🔧 Erweiterte Deployment-Optionen

### Docker mit Monitoring

```bash
./docker-deploy.sh deploy --with-monitoring
```

Startet zusätzlich Prometheus (Port 9090) und Grafana (Port 3000)

### Docker mit Nginx Reverse Proxy

```bash
./docker-deploy.sh deploy --with-nginx
```

Startet Nginx als Reverse Proxy auf Port 80

### Beide Optionen kombiniert

```bash
./docker-deploy.sh deploy --with-monitoring --with-nginx
```

## 🛠️ Wartung und Management

### Direkte Installation

```bash
# Service-Status prüfen
sudo systemctl status data-assistant

# Logs anzeigen
sudo journalctl -u data-assistant -f

# Service neustarten
sudo systemctl restart data-assistant

# Backup erstellen
/opt/backups/data_assistant/backup.sh
```

### Docker Container

```bash
# Container-Status
./docker-deploy.sh status

# Logs anzeigen
./docker-deploy.sh logs

# Backup erstellen
./docker-deploy.sh backup

# Container neustarten
./docker-deploy.sh restart

# Bereinigung
./docker-deploy.sh cleanup
```

## 🌐 Zugriff auf die Anwendung

Nach erfolgreichem Deployment ist die Anwendung erreichbar unter:

- **Direkte Installation**: `http://your-vm-ip:8501`
- **Docker (ohne Nginx)**: `http://your-vm-ip:8501`
- **Docker mit Nginx**: `http://your-vm-ip:80`

### Standard-Anmeldedaten

- **Benutzername**: `admin`
- **Passwort**: `admin123`

⚠️ **Wichtig**: Ändern Sie das Standard-Passwort nach der ersten Anmeldung!

## 🔐 Sicherheit

### API-Schlüssel konfigurieren

1. **Direkte Installation**:

   ```bash
   nano /opt/data_assistant/new_data_assistant_project/.env
   ```
2. **Docker**:

   ```bash
   nano /opt/new_data_assistant_project/.env
   ```

Setzen Sie mindestens:

```env
ANTHROPIC_API_KEY=your_actual_api_key_here
```

### Firewall-Konfiguration

Die Skripte konfigurieren automatisch die Firewall. Manuelle Überprüfung:

```bash
sudo ufw status
```

Offene Ports:

- `22` - SSH
- `8501` - Streamlit (direkt)
- `80` - HTTP (Nginx)
- `443` - HTTPS (Nginx, falls SSL konfiguriert)

## 📊 Monitoring (Optional)

Bei Docker-Deployment mit `--with-monitoring`:

- **Prometheus**: `http://your-vm-ip:9090`
- **Grafana**: `http://your-vm-ip:3000`
  - Login: admin/admin

## 🆘 Fehlerbehebung

### Häufige Probleme

1. **Port bereits belegt**:

   ```bash
   sudo netstat -tulpn | grep 8501
   sudo kill -9 <process-id>
   ```
2. **Docker-Berechtigung**:

   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```
3. **Speicherplatz**:

   ```bash
   df -h
   docker system prune -f
   ```
4. **Service startet nicht**:

   ```bash
   sudo journalctl -u data-assistant --no-pager -n 50
   ```

### Log-Dateien

- **Direkte Installation**: `/var/log/data_assistant/`
- **Docker**: `docker-compose logs data-assistant`

## 📞 Support

Für detaillierte Informationen siehe:

- `VM_SETUP_GUIDE.md` - Vollständige Schritt-für-Schritt Anleitung
- Projekt-Repository - Dokumentation und Issues

## 🔄 Updates

### Direkte Installation

```bash
cd /opt/data_assistant/new_data_assistant_project
git pull  # falls Git-Repository
sudo systemctl restart data-assistant
```

### Docker

```bash
cd /opt/new_data_assistant_project/deployment
./docker-deploy.sh stop
docker-compose build --no-cache
./docker-deploy.sh start
```
