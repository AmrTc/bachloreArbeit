# Data Assistant - Docker Deployment

🐳 **Professionelles Docker-Deployment für permanenten Betrieb und externe Erreichbarkeit**

## 🚀 Quick Start

```bash
# 1. Docker installieren (falls nötig)
./docker-deploy.sh install-docker

# 2. Permanentes Deployment mit externer Erreichbarkeit
./docker-deploy.sh deploy --with-nginx

# 3. Status prüfen
./docker-deploy.sh status
```

## 📋 Deployment-Optionen

### **Standard (nur App):**
```bash
./docker-deploy.sh deploy
# → App läuft auf Port 8501
```

### **Mit Nginx (empfohlen für externe Erreichbarkeit):**
```bash
./docker-deploy.sh deploy --with-nginx
# → App über Port 80 erreichbar
# → Professionelle Reverse-Proxy Konfiguration
```

### **Mit Monitoring:**
```bash
./docker-deploy.sh deploy --with-monitoring
# → Zusätzlich Prometheus (Port 9090) + Grafana (Port 3000)
```

### **Vollständiges Setup:**
```bash
./docker-deploy.sh deploy --with-nginx --with-monitoring
# → Alles: App + Nginx + Monitoring
```

## 🌐 Externe Erreichbarkeit

### **Option 1: Nginx Reverse Proxy (empfohlen)**
```bash
# Deployment mit Nginx
./docker-deploy.sh deploy --with-nginx

# Zugriff:
# - Lokal: http://localhost:80
# - Extern: http://your-server-ip:80
# - Domain: http://your-domain.com
```

### **Option 2: SSH-Tunnel (für sichere Verbindungen)**
```bash
# Von einem anderen Computer:
ssh -L 8501:localhost:8501 user@your-server
# Browser: http://localhost:8501

# Oder mit Nginx:
ssh -L 8080:localhost:80 user@your-server  
# Browser: http://localhost:8080
```

### **Option 3: Firewall-Konfiguration**
```bash
# Ports für externe Erreichbarkeit öffnen:
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS (falls SSL)
sudo ufw allow 8501/tcp  # Direkt zur App
```

## 🔄 Permanenter Betrieb

### **Docker-Container Management:**
```bash
# Status aller Container
./docker-deploy.sh status

# Live-Logs verfolgen
./docker-deploy.sh logs

# Container neustarten
./docker-deploy.sh restart

# Container stoppen
./docker-deploy.sh stop

# Container starten
./docker-deploy.sh start
```

### **Automatischer Start nach Server-Neustart:**
Container starten automatisch durch `restart: unless-stopped` in docker-compose.yml

## 🛠️ Erweiterte Konfiguration

### **Umgebungsvariablen (.env):**
```bash
# .env Datei im Hauptverzeichnis bearbeiten:
ANTHROPIC_API_KEY=your_api_key_here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
SECRET_KEY=your_secret_key
SESSION_TIMEOUT=3600
MAX_LOGIN_ATTEMPTS=3
```

### **Nginx für Custom Domain:**
```bash
# nginx.conf bearbeiten:
server_name your-domain.com;
```

### **SSL/HTTPS einrichten:**
```bash
# SSL-Zertifikate in ./ssl/ Verzeichnis platzieren
# Dann nginx.conf HTTPS-Sektion aktivieren
```

## 🔧 Wartung & Troubleshooting

### **Container-Diagnose:**
```bash
# Alle Container anzeigen
docker ps -a

# Container-Logs
docker logs data_assistant_app
docker logs data_assistant_nginx

# In Container hinein (Debugging)
docker exec -it data_assistant_app bash

# Container-Ressourcen
docker stats
```

### **Datenbank-Management:**
```bash
# Backup erstellen
./docker-deploy.sh backup

# Datenbank-Volume prüfen
docker volume ls
```

### **Updates:**
```bash
# Code-Updates
git pull origin main
./docker-deploy.sh restart

# Docker-Image neu bauen
docker-compose build --no-cache
./docker-deploy.sh restart
```

## 📁 Datei-Struktur

```
deployment/
├── docker-deploy.sh      # Hauptskript
├── docker-compose.yml    # Container-Konfiguration
├── Dockerfile           # Image-Definition
├── nginx.conf           # Reverse-Proxy Konfiguration
└── README.md           # Diese Anleitung

Generated at runtime:
├── data/               # Persistente Daten
├── logs/              # Container-Logs
└── ssl/               # SSL-Zertifikate (optional)
```

## 🎯 Standard-Login

```
🌐 URL: http://your-server-ip (mit Nginx)
🌐 URL: http://your-server-ip:8501 (direkt)

👤 Benutzername: admin
🔑 Passwort: admin123
```

**⚠️ WICHTIG: Ändern Sie das Admin-Passwort nach dem ersten Login!**

## ⚡ Quick Commands

```bash
# Komplettes Setup (neue VM):
./docker-deploy.sh install-docker
./docker-deploy.sh deploy --with-nginx
./docker-deploy.sh status

# Tägliche Wartung:
./docker-deploy.sh logs     # Logs prüfen
./docker-deploy.sh backup   # Backup erstellen

# Bei Problemen:
./docker-deploy.sh restart  # Neustart
./docker-deploy.sh cleanup  # Bereinigung
```

## 🌍 Zugriff von anderen Systemen

Nach erfolgreichem Deployment ist die App erreichbar unter:

- **Lokal auf dem Server:** `http://localhost` oder `http://localhost:8501`
- **Andere Computer im Netzwerk:** `http://SERVER_IP` oder `http://SERVER_IP:8501`  
- **Internet (falls konfiguriert):** `http://your-domain.com`
- **SSH-Tunnel:** `ssh -L 8080:localhost:80 user@server` → `http://localhost:8080`

🎉 **Das System läuft permanent und ist von überall erreichbar!**
