# 🚀 VM Setup Guide - Data Assistant Project

## Übersicht
Diese Anleitung hilft Ihnen dabei, das Data Assistant Projekt auf einer VM zu installieren und zu betreiben. Sie haben zwei Optionen:
1. **Direkte Installation** - Installation auf der VM ohne Container
2. **Docker Container** - Containerisierte Bereitstellung (empfohlen für Produktion)

## 📋 Voraussetzungen

### VM-Anforderungen
- **OS**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- **RAM**: Mindestens 2GB (empfohlen: 4GB+)
- **Speicher**: Mindestens 10GB freier Speicherplatz
- **CPU**: Mindestens 2 Kerne
- **Netzwerk**: Port 8501 (Streamlit) muss erreichbar sein

### Zugang
- SSH-Zugang zur VM
- Sudo-Rechte
- Internetverbindung

## 🔧 Option 1: Direkte Installation

### Schritt 1: System vorbereiten

```bash
# Mit VM verbinden
ssh your-username@your-vm-ip

# System aktualisieren
sudo apt update && sudo apt upgrade -y

# Git installieren
sudo apt install -y git curl wget

# Python 3.12 installieren (falls nicht vorhanden)
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.12 python3.12-pip python3.12-venv python3.12-dev

# Python 3.12 als Standard setzen (optional)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
```

### Schritt 2: Projekt clonen und vorbereiten

```bash
# Arbeitsverzeichnis erstellen
cd /opt
sudo mkdir data_assistant
sudo chown $USER:$USER data_assistant
cd data_assistant

# Projekt von lokaler Entwicklung übertragen
# Option A: Git Repository (falls vorhanden)
# git clone https://github.com/your-repo/data_assistant_project.git

# Option B: Dateien übertragen via SCP
# Auf Ihrem lokalen Rechner:
# scp -r new_data_assistant_project/ your-username@your-vm-ip:/opt/data_assistant/

# Option C: Tar-Archiv erstellen und übertragen
# Lokal: tar -czf data_assistant.tar.gz new_data_assistant_project/
# Übertragen: scp data_assistant.tar.gz your-username@your-vm-ip:/opt/data_assistant/
# Auf VM: tar -xzf data_assistant.tar.gz
```

### Schritt 3: Python-Umgebung einrichten

```bash
cd /opt/data_assistant/new_data_assistant_project

# Virtual Environment erstellen
python3.12 -m venv venv

# Virtual Environment aktivieren
source venv/bin/activate

# Dependencies installieren
pip install --upgrade pip
pip install -r requirements.txt

# Zusätzliche Dependencies für Produktion
pip install gunicorn supervisor
```

### Schritt 4: Umgebungsvariablen konfigurieren

```bash
# .env Datei erstellen
cat > .env << EOF
# API Konfiguration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database Konfiguration
DATABASE_URL=sqlite:///src/database/superstore.db

# Streamlit Konfiguration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Debug Modus (für Produktion auf False setzen)
DEBUG=False

# Sicherheit
SECRET_KEY=your_super_secret_key_here
EOF

# Berechtigungen setzen
chmod 600 .env
```

### Schritt 5: Datenbank initialisieren

```bash
# In der Virtual Environment
cd /opt/data_assistant/new_data_assistant_project

# Datenbank-Verzeichnis erstellen falls nötig
mkdir -p src/database

# Python-Pfad konfigurieren
export PYTHONPATH="/opt/data_assistant/new_data_assistant_project:$PYTHONPATH"

# Datenbank initialisieren
python -c "
from src.database.schema import create_tables, create_admin_user
create_tables()
create_admin_user()
print('✅ Datenbank erfolgreich initialisiert')
"
```

### Schritt 6: Systemd Service erstellen

```bash
# Service-Datei erstellen
sudo tee /etc/systemd/system/data-assistant.service > /dev/null << EOF
[Unit]
Description=Data Assistant Streamlit App
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/data_assistant/new_data_assistant_project
Environment=PATH=/opt/data_assistant/new_data_assistant_project/venv/bin
Environment=PYTHONPATH=/opt/data_assistant/new_data_assistant_project
ExecStart=/opt/data_assistant/new_data_assistant_project/venv/bin/streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Service aktivieren und starten
sudo systemctl daemon-reload
sudo systemctl enable data-assistant
sudo systemctl start data-assistant

# Status prüfen
sudo systemctl status data-assistant
```

### Schritt 7: Firewall konfigurieren

```bash
# UFW Firewall konfigurieren
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8501/tcp  # Streamlit
sudo ufw --force enable

# Status prüfen
sudo ufw status
```

## 🐳 Option 2: Docker Container (Empfohlen)

### Schritt 1: Docker installieren

```bash
# Docker installieren
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose installieren
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# User zur Docker-Gruppe hinzufügen
sudo usermod -aG docker $USER

# Neu einloggen oder:
newgrp docker

# Installation testen
docker --version
docker-compose --version
```

### Schritt 2: Projekt übertragen

```bash
# Arbeitsverzeichnis erstellen
cd /opt
sudo mkdir data_assistant_docker
sudo chown $USER:$USER data_assistant_docker
cd data_assistant_docker

# Projekt übertragen (siehe Option 1, Schritt 2)
```

## 🔐 Sicherheit und Wartung

### SSL/TLS einrichten (Reverse Proxy)

```bash
# Nginx installieren
sudo apt install -y nginx certbot python3-certbot-nginx

# Nginx-Konfiguration
sudo tee /etc/nginx/sites-available/data-assistant << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# Site aktivieren
sudo ln -s /etc/nginx/sites-available/data-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# SSL-Zertifikat (optional, für HTTPS)
sudo certbot --nginx -d your-domain.com
```

### Backup-Skript

```bash
# Backup-Skript erstellen
sudo tee /opt/data_assistant/backup.sh << EOF
#!/bin/bash
BACKUP_DIR="/opt/backups/data_assistant"
PROJECT_DIR="/opt/data_assistant/new_data_assistant_project"
DATE=\$(date +%Y%m%d_%H%M%S)

mkdir -p \$BACKUP_DIR

# Datenbank sichern
cp \$PROJECT_DIR/src/database/superstore.db \$BACKUP_DIR/superstore_\$DATE.db

# Logs archivieren
tar -czf \$BACKUP_DIR/logs_\$DATE.tar.gz /var/log/data-assistant/ 2>/dev/null || true

# Alte Backups löschen (älter als 30 Tage)
find \$BACKUP_DIR -name "*.db" -mtime +30 -delete
find \$BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: \$DATE"
EOF

chmod +x /opt/data_assistant/backup.sh

# Cronjob für tägliche Backups
echo "0 2 * * * /opt/data_assistant/backup.sh" | sudo crontab -
```

### Monitoring

```bash
# Einfaches Monitoring-Skript
sudo tee /opt/data_assistant/monitor.sh << EOF
#!/bin/bash
if ! systemctl is-active --quiet data-assistant; then
    echo "Data Assistant Service ist nicht aktiv!"
    sudo systemctl restart data-assistant
    echo "Service wurde neu gestartet: \$(date)"
fi
EOF

chmod +x /opt/data_assistant/monitor.sh

# Monitoring alle 5 Minuten
echo "*/5 * * * * /opt/data_assistant/monitor.sh" | crontab -
```

## 🚀 Anwendung starten

### Nach direkter Installation:
```bash
# Service starten
sudo systemctl start data-assistant

# Logs anzeigen
sudo journalctl -u data-assistant -f
```

### Nach Docker-Installation:
```bash
cd /opt/data_assistant_docker/new_data_assistant_project
docker-compose up -d

# Logs anzeigen
docker-compose logs -f
```

## 🌐 Zugriff

Die Anwendung ist erreichbar unter:
- **HTTP**: `http://your-vm-ip:8501`
- **HTTPS** (mit Nginx): `https://your-domain.com`

### Standard-Anmeldedaten:
- **Username**: admin
- **Password**: admin123 (bitte sofort ändern!)

## 🔍 Fehlerbehebung

### Logs prüfen:
```bash
# Systemd Service Logs
sudo journalctl -u data-assistant -f

# Docker Logs
docker-compose logs -f

# Nginx Logs
sudo tail -f /var/log/nginx/error.log
```

### Port-Überprüfung:
```bash
# Prüfen ob Port 8501 verwendet wird
sudo netstat -tulpn | grep 8501

# Prozesse prüfen
ps aux | grep streamlit
```

### Speicherplatz prüfen:
```bash
df -h
du -sh /opt/data_assistant/
```

## ⚠️ Wichtige Hinweise

1. **API-Schlüssel**: Vergessen Sie nicht, Ihren Anthropic API-Schlüssel in der `.env` Datei zu setzen
2. **Firewall**: Stellen Sie sicher, dass Port 8501 (oder 80/443 für Nginx) erreichbar ist
3. **Updates**: Regelmäßige Updates der Dependencies und des Systems
4. **Backups**: Implementieren Sie regelmäßige Backups der Datenbank
5. **Monitoring**: Überwachen Sie die Anwendung auf Fehler und Performance

## 📞 Support

Bei Problemen prüfen Sie:
1. Logs der Anwendung
2. Systemressourcen (RAM, CPU, Speicher)
3. Netzwerkkonnektivität
4. Berechtigungen der Dateien und Verzeichnisse 