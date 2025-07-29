#!/bin/bash
# =============================================================================
# Debian-spezifisches Deployment für tchagn01.stud.fim.uni-passau.de
# =============================================================================

set -e

echo "🚀 Starte Debian-Deployment auf tchagn01.stud.fim.uni-passau.de..."

# Konfiguration für Ihre VM
export VM_HOST="tchagn01.stud.fim.uni-passau.de"
export VM_USER="tchagnaoso"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="admin123"
export ADMIN_EMAIL="admin@example.com"

# Farben
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Prüfen ob wir im richtigen Verzeichnis sind
if [[ ! -f "../frontend/app.py" ]]; then
    error "❌ Bitte führen Sie das Skript aus dem deployment/ Verzeichnis aus!"
fi

log "📋 Systeminfo..."
echo "Host: $(hostname)"
echo "User: $(whoami)"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME)"
echo "Arbeitsverzeichnis: $(pwd)"

# Python-Version ermitteln
log "🐍 Python Setup für Debian..."

# Verfügbare Python-Versionen prüfen
PYTHON_CMD=""
for version in python3.12 python3.11 python3.10 python3; do
    if command -v $version &> /dev/null; then
        PYTHON_CMD=$version
        log "✅ Gefunden: $version ($(${version} --version))"
        break
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    error "❌ Keine Python3-Installation gefunden!"
fi

# Falls nur python3.9 oder älter verfügbar, Python 3.11 installieren
PYTHON_VERSION=$(${PYTHON_CMD} --version | cut -d' ' -f2 | cut -d'.' -f1,2)
log "Verwende Python $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" == "3.9" ]] || [[ "$PYTHON_VERSION" < "3.10" ]]; then
    log "🔄 Installiere neuere Python-Version..."
    sudo apt update
    sudo apt install -y python3.11 python3.11-pip python3.11-venv python3.11-dev python3.11-distutils
    PYTHON_CMD="python3.11"
fi

# Falls Python 3.11 nicht verfügbar, von Source installieren
if ! command -v python3.11 &> /dev/null && [[ "$PYTHON_CMD" == "python3" ]]; then
    log "📦 Installiere notwendige Python-Pakete..."
    sudo apt update
    sudo apt install -y python3-pip python3-venv python3-dev python3-distutils build-essential
fi

# Virtual Environment erstellen
log "📦 Virtual Environment Setup..."
cd ..

# Altes venv entfernen falls vorhanden
if [[ -d "venv" ]]; then
    rm -rf venv
fi

# Neues venv erstellen
$PYTHON_CMD -m venv venv

# Virtual Environment aktivieren
source venv/bin/activate

# Pip upgraden
log "📚 Dependencies vorbereiten..."
python -m pip install --upgrade pip

# Dependencies installieren mit Fallback
log "📚 Dependencies installieren..."
if ! pip install -r requirements.txt; then
    log "🔄 Installiere Dependencies einzeln..."
    pip install streamlit
    pip install pandas
    pip install anthropic
    pip install python-dotenv
    pip install numpy
fi

# Umgebungsvariablen konfigurieren
log "⚙️ Umgebung konfigurieren..."
cat > .env << EOF

# Database Konfiguration
DATABASE_URL=sqlite:///src/database/superstore.db

# Streamlit Konfiguration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Debug Modus
DEBUG=False

# Sicherheit
SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || echo "$(date +%s)$(whoami)" | sha256sum | cut -d' ' -f1)
SESSION_TIMEOUT=10000
MAX_LOGIN_ATTEMPTS=99

# Admin Benutzer
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com
EOF

chmod 600 .env

# PYTHONPATH setzen
export PYTHONPATH=$(pwd)

# Verzeichnisse erstellen
log "📁 Verzeichnisse erstellen..."
mkdir -p src/database
mkdir -p data/user_profiles
mkdir -p evaluation/results
mkdir -p logs

# Datenbank initialisieren
log "🗄️ Datenbank initialisieren..."
python -c "
import sys
sys.path.insert(0, '.')
try:
    from src.database.schema import create_tables, create_admin_user
    create_tables()
    create_admin_user()
    print('✅ Datenbank erfolgreich initialisiert')
except Exception as e:
    print(f'⚠️ Datenbank-Info: {e}')
    print('Das kann normal sein wenn bereits existiert oder Dependencies fehlen.')
" || echo "⚠️ Datenbank-Initialisierung übersprungen"

# Test der Anwendung
log "🧪 Anwendungstest..."
if python -c "import streamlit; print('✅ Streamlit verfügbar')"; then
    log "✅ Grundlegende Dependencies funktionieren"
else
    error "❌ Streamlit-Import fehlgeschlagen"
fi

# Systemd Service erstellen
log "🔧 Systemd Service erstellen..."
SERVICE_NAME="data-assistant"
PROJECT_DIR=$(pwd)

sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=Data Assistant Streamlit App
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=5
StandardOutput=append:/var/log/data-assistant.log
StandardError=append:/var/log/data-assistant-error.log

[Install]
WantedBy=multi-user.target
EOF

# Log-Dateien erstellen
sudo touch /var/log/data-assistant.log
sudo touch /var/log/data-assistant-error.log
sudo chown $(whoami):$(whoami) /var/log/data-assistant*.log

# Service aktivieren und starten
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}

# Service starten
log "🚀 Service starten..."
if sudo systemctl start ${SERVICE_NAME}; then
    log "✅ Service gestartet"
else
    log "⚠️ Service-Start Probleme, prüfe Logs..."
    sudo journalctl -u ${SERVICE_NAME} --no-pager -n 10
fi

# Firewall konfigurieren (falls UFW installiert)
if command -v ufw &> /dev/null; then
    log "🔥 Firewall konfigurieren..."
    sudo ufw allow 8501/tcp || true
    sudo ufw --force enable || true
fi

# Status prüfen
log "📊 Service Status..."
sudo systemctl status ${SERVICE_NAME} --no-pager -l || true

# Netzwerk-Info
log "🌐 Netzwerk-Informationen..."
IP=$(hostname -I | awk '{print $1}' || echo "localhost")
echo "Lokale IP: $IP"
echo "Hostname: $(hostname)"

# Test ob Port erreichbar ist
log "🔍 Port-Test..."
sleep 5
if ss -tlnp | grep :8501; then
    log "✅ Port 8501 ist aktiv"
else
    log "⚠️ Port 8501 noch nicht aktiv, Service startet möglicherweise noch"
fi

# Erfolgsmeldung
echo -e "\n${GREEN}╔═══════════════════════════════════════════════════╗"
echo -e "║          🎉 Debian Deployment Erfolgreich!        ║"
echo -e "╚═══════════════════════════════════════════════════╝${NC}\n"

echo -e "${BLUE}📋 Zugriff:${NC}"
echo -e "   🌐 Lokal: http://localhost:8501"
echo -e "   🌐 Extern: http://$IP:8501"
echo -e "   🌐 Domain: http://tchagn01.stud.fim.uni-passau.de:8501"

echo -e "\n${BLUE}🔧 Verwaltung:${NC}"
echo -e "   Status:      sudo systemctl status data-assistant"
echo -e "   Logs:        sudo journalctl -u data-assistant -f"
echo -e "   App-Logs:    tail -f /var/log/data-assistant.log"
echo -e "   Error-Logs:  tail -f /var/log/data-assistant-error.log"
echo -e "   Neustart:    sudo systemctl restart data-assistant"
echo -e "   Stoppen:     sudo systemctl stop data-assistant"

echo -e "\n${BLUE}👤 Login:${NC}"
echo -e "   Benutzername: admin"
echo -e "   Passwort:     admin123"

echo -e "\n${YELLOW}⚠️  Wichtige Hinweise:${NC}"
echo -e "   🔑 Setzen Sie Ihren ANTHROPIC_API_KEY in .env"
echo -e "   🔐 Ändern Sie das Admin-Passwort nach erstem Login"
echo -e "   🚪 Port 8501 muss für externen Zugriff freigeschaltet sein"
echo -e "   🐍 Verwendet Python: $($PYTHON_CMD --version)"

echo -e "\n${GREEN}✅ Das System läuft permanent als Systemd-Service!${NC}" 