#!/bin/bash
# =============================================================================
# Schnell-Deployment für tchagn01.stud.fim.uni-passau.de
# =============================================================================

set -e

echo "🚀 Starte Deployment auf tchagn01.stud.fim.uni-passau.de..."

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
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

# Prüfen ob wir im richtigen Verzeichnis sind
if [[ ! -f "../frontend/app.py" ]]; then
    echo "❌ Bitte führen Sie das Skript aus dem deployment/ Verzeichnis aus!"
    exit 1
fi

log "📋 Systeminfo..."
echo "Host: $(hostname)"
echo "User: $(whoami)"
echo "Arbeitsverzeichnis: $(pwd)"

# Python 3.12 prüfen/installieren
log "🐍 Python 3.12 Setup..."
if ! command -v python3.12 &> /dev/null; then
    log "Installiere Python 3.12..."
    sudo apt update
    sudo apt install -y software-properties-common
    sudo add-apt-repository ppa:deadsnakes/ppa -y || true
    sudo apt update
    sudo apt install -y python3.12 python3.12-pip python3.12-venv python3.12-dev
fi

# Virtual Environment erstellen
log "📦 Virtual Environment Setup..."
cd ..
if [[ ! -d "venv" ]]; then
    python3.12 -m venv venv
fi

# Virtual Environment aktivieren
source venv/bin/activate

# Dependencies installieren
log "📚 Dependencies installieren..."
pip install --upgrade pip
pip install -r requirements.txt

# Umgebungsvariablen konfigurieren
log "⚙️ Umgebung konfigurieren..."
cat > .env << EOF
# API Konfiguration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database Konfiguration
DATABASE_URL=sqlite:///src/database/superstore.db

# Streamlit Konfiguration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Debug Modus
DEBUG=False

# Sicherheit
SECRET_KEY=$(openssl rand -hex 32)
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
try:
    from src.database.schema import create_tables, create_admin_user
    create_tables()
    create_admin_user()
    print('✅ Datenbank erfolgreich initialisiert')
except Exception as e:
    print(f'⚠️ Datenbank-Info: {e} (kann normal sein wenn bereits existiert)')
"

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
Environment=PATH=$PROJECT_DIR/venv/bin
Environment=PYTHONPATH=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=3
StandardOutput=append:/var/log/data-assistant.log
StandardError=append:/var/log/data-assistant-error.log

[Install]
WantedBy=multi-user.target
EOF

# Service aktivieren und starten
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl start ${SERVICE_NAME}

# Firewall konfigurieren (falls UFW installiert)
if command -v ufw &> /dev/null; then
    log "🔥 Firewall konfigurieren..."
    sudo ufw allow 8501/tcp
    sudo ufw --force enable
fi

# Status prüfen
log "📊 Service Status..."
sudo systemctl status ${SERVICE_NAME} --no-pager -l

# Netzwerk-Info
log "🌐 Netzwerk-Informationen..."
IP=$(hostname -I | awk '{print $1}')
echo "Lokale IP: $IP"
echo "Hostname: $(hostname)"

# Erfolgsmeldung
echo -e "\n${GREEN}╔═══════════════════════════════════════════════════╗"
echo -e "║          🎉 Deployment Erfolgreich!               ║"
echo -e "╚═══════════════════════════════════════════════════╝${NC}\n"

echo -e "${BLUE}📋 Zugriff:${NC}"
echo -e "   🌐 Lokal: http://localhost:8501"
echo -e "   🌐 Extern: http://$IP:8501"
echo -e "   🌐 Domain: http://tchagn01.stud.fim.uni-passau.de:8501"

echo -e "\n${BLUE}🔧 Verwaltung:${NC}"
echo -e "   Status:      sudo systemctl status data-assistant"
echo -e "   Logs:        sudo journalctl -u data-assistant -f"
echo -e "   Neustart:    sudo systemctl restart data-assistant"
echo -e "   Stoppen:     sudo systemctl stop data-assistant"

echo -e "\n${BLUE}👤 Login:${NC}"
echo -e "   Benutzername: admin"
echo -e "   Passwort:     admin123"

echo -e "\n${YELLOW}⚠️  Wichtige Hinweise:${NC}"
echo -e "   🔑 Setzen Sie Ihren ANTHROPIC_API_KEY in .env"
echo -e "   🔐 Ändern Sie das Admin-Passwort nach erstem Login"
echo -e "   🚪 Port 8501 muss für externen Zugriff freigeschaltet sein"

echo -e "\n${GREEN}✅ Das System läuft permanent als Systemd-Service!${NC}" 