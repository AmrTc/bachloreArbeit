# Data Assistant Project

🐳 **AI-powered Data Analysis Assistant with Docker Deployment**

Ein intelligentes System zur Datenanalyse mit Streamlit Frontend und Docker-basiertem Deployment für permanenten, extern erreichbaren Betrieb.

## 🚀 Quick Start

### **Lokale Entwicklung:**
```bash
# Repository klonen
git clone <repository-url>
cd new_data_assistant_project

# Docker-Deployment starten
cd deployment
./docker-deploy.sh deploy --with-nginx
```

### **Server/VM-Deployment:**
```bash
# Auf Server/VM:
git clone <repository-url>
cd new_data_assistant_project/deployment

# Komplettes Setup (Docker + Firewall + externe Erreichbarkeit)
chmod +x vm-install.sh
./vm-install.sh
```

## 🌐 Zugriff

Nach dem Deployment ist die Anwendung erreichbar:

- **Mit Nginx:** `http://your-server-ip` 
- **Direkt:** `http://your-server-ip:8501`
- **SSH-Tunnel:** `ssh -L 8080:localhost:80 user@server` → `http://localhost:8080`

**Login:** admin / admin123 (nach erstem Login ändern!)

## 📁 Projekt-Struktur

```
new_data_assistant_project/
├── deployment/              # 🐳 Docker-Deployment (Hauptfokus)
│   ├── docker-deploy.sh     # Haupt-Deployment-Skript
│   ├── vm-install.sh        # VM-Setup (neu)
│   ├── docker-compose.yml   # Container-Konfiguration
│   ├── Dockerfile          # App-Container
│   ├── nginx.conf          # Reverse-Proxy
│   └── README.md           # Detaillierte Docker-Anleitung
├── frontend/               # Streamlit Web-Interface
├── src/                   # Anwendungslogik
│   ├── agents/            # KI-Agenten
│   ├── database/          # Datenbank-Schema
│   └── utils/            # Hilfsfunktionen
├── data/                 # Daten und Datensätze
├── evaluation/           # Evaluierung und Metriken
└── tests/               # Unit Tests
```

## 🔧 Container-Management

```bash
cd deployment/

# Status prüfen
./docker-deploy.sh status

# Logs anschauen
./docker-deploy.sh logs

# Container neustarten
./docker-deploy.sh restart

# Updates einspielen
git pull origin main
./docker-deploy.sh restart
```

## 🛠️ Erweiterte Konfiguration

### **Umgebungsvariablen (.env):**
```bash
# .env im Hauptverzeichnis erstellen/bearbeiten:
ANTHROPIC_API_KEY=your_anthropic_api_key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_password
SECRET_KEY=your_secret_key
```

### **Monitoring (optional):**
```bash
# Deployment mit Prometheus + Grafana:
./docker-deploy.sh deploy --with-monitoring

# Zugriff:
# Grafana: http://your-server:3000 (admin/admin)
# Prometheus: http://your-server:9090
```

### **SSL/HTTPS (optional):**
```bash
# SSL-Zertifikate in deployment/ssl/ platzieren
# nginx.conf HTTPS-Sektion aktivieren
./docker-deploy.sh restart
```

## 📦 Features

- **🤖 KI-gestützte Datenanalyse** mit Anthropic Claude
- **📊 Interaktive Dashboards** mit Streamlit
- **🔐 Benutzerauthentifizierung** mit Rollenverwaltung
- **📈 Evaluierungs-System** für KI-Performance
- **🐳 Docker-basiertes Deployment** für einfache Installation
- **🌐 Externe Erreichbarkeit** mit Nginx Reverse-Proxy
- **🔄 Permanenter Betrieb** mit automatischen Restarts

## 🆘 Support & Troubleshooting

### **Häufige Probleme:**

**App nicht erreichbar:**
```bash
# Container-Status prüfen
./docker-deploy.sh status

# Firewall prüfen
sudo ufw status

# Logs prüfen
./docker-deploy.sh logs
```

**Updates einspielen:**
```bash
git pull origin main
cd deployment
./docker-deploy.sh restart
```

**Backup erstellen:**
```bash
./docker-deploy.sh backup
```

### **Port-Belegung prüfen:**
```bash
# Welche Ports sind belegt?
ss -tlnp | grep -E "(80|443|8501)"

# Container-Ports
docker ps
```

## 🔒 Sicherheit

- ✅ Admin-Passwort nach erstem Login ändern
- ✅ API-Keys sicher in .env speichern
- ✅ Firewall für externe Ports konfigurieren
- ✅ SSH-Tunnel für sichere Verbindungen nutzen
- ✅ HTTPS mit SSL-Zertifikaten (optional)

## 📚 Dokumentation

- **Deployment:** `deployment/README.md` - Detaillierte Docker-Anleitung
- **VM-Setup:** `VM_SETUP_GUIDE.md` - Server-Konfiguration
- **Access-Setup:** `ACCESS_SETUP.md` - Zugangsdaten-Konfiguration

## 🎯 Deployment-Optionen

| Option | Kommando | Beschreibung |
|--------|----------|--------------|
| **Standard** | `./docker-deploy.sh deploy` | Nur App (Port 8501) |
| **Mit Nginx** | `./docker-deploy.sh deploy --with-nginx` | ⭐ **Empfohlen** - App + Reverse-Proxy (Port 80) |
| **Mit Monitoring** | `./docker-deploy.sh deploy --with-monitoring` | App + Prometheus + Grafana |
| **Vollständig** | `./docker-deploy.sh deploy --with-nginx --with-monitoring` | Alles zusammen |

## 🚀 Das ist alles!

**Docker macht das Deployment super einfach:**
1. `./vm-install.sh` auf dem Server ausführen
2. Browser auf `http://server-ip` öffnen  
3. Einloggen und loslegen! 🎉

---

**🐳 Powered by Docker | 🤖 Powered by AI | 🚀 Ready for Production**
