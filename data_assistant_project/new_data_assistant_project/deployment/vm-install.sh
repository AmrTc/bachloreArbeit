#!/bin/bash
# =============================================================================
# Data Assistant - VM Docker Installation & Permanentes Setup
# =============================================================================

set -e

# Farben
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Header
echo -e "${BLUE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════╗
║       Data Assistant - VM Docker Setup           ║
║           Permanenter Betrieb + Externe          ║
║              Erreichbarkeit                       ║
╚═══════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Verzeichnis prüfen
if [[ ! -f "docker-deploy.sh" ]]; then
    error "❌ Bitte aus dem deployment/ Verzeichnis ausführen!"
fi

log "🚀 Starte VM-Setup für permanenten Docker-Betrieb..."

# Schritt 1: Docker installieren
log "📦 Docker Installation..."
if ! command -v docker &> /dev/null; then
    log "Docker nicht gefunden - installiere..."
    ./docker-deploy.sh install-docker
    log "✅ Docker installiert - bitte neu einloggen mit: newgrp docker"
    
    echo -e "\n${YELLOW}⚠️  WICHTIG: Führen Sie nach Docker-Installation aus:${NC}"
    echo -e "${YELLOW}   newgrp docker${NC}"
    echo -e "${YELLOW}   cd $(pwd)${NC}"
    echo -e "${YELLOW}   ./vm-install.sh${NC}"
    echo -e "\n${YELLOW}Oder loggen Sie sich neu ein und wiederholen Sie das Setup.${NC}"
    exit 0
else
    log "✅ Docker bereits installiert"
fi

# Schritt 2: Deployment mit externer Erreichbarkeit
log "🐳 Deployment mit Nginx für externe Erreichbarkeit..."
./docker-deploy.sh deploy --with-nginx

# Schritt 3: Firewall konfigurieren
log "🔥 Firewall für externe Erreichbarkeit konfigurieren..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 80/tcp || true
    sudo ufw allow 443/tcp || true
    sudo ufw allow 8501/tcp || true
    log "✅ Firewall-Regeln hinzugefügt (Ports 80, 443, 8501)"
else
    warn "UFW nicht verfügbar - Firewall manuell konfigurieren"
fi

# Schritt 4: Systemd Service für extra Zuverlässigkeit (optional)
read -p "Möchten Sie einen Systemd-Service für extra Zuverlässigkeit einrichten? (y/N): " setup_systemd
if [[ $setup_systemd == [yY] ]]; then
    log "🔧 Systemd-Service einrichten..."
    
    # Service-Datei erstellen
    sudo tee /etc/systemd/system/data-assistant-docker.service > /dev/null << EOF
[Unit]
Description=Data Assistant Docker Containers
Requires=docker.service
After=docker.service
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=$(whoami)
Group=docker
WorkingDirectory=$(pwd)
ExecStart=/usr/local/bin/docker-compose up -d --profile production
ExecStop=/usr/local/bin/docker-compose down
ExecReload=/usr/local/bin/docker-compose restart
TimeoutStartSec=300
TimeoutStopSec=120
Restart=on-failure
RestartSec=30
Environment=COMPOSE_PROJECT_NAME=data_assistant

[Install]
WantedBy=multi-user.target
EOF

    # Service aktivieren
    sudo systemctl daemon-reload
    sudo systemctl enable data-assistant-docker
    log "✅ Systemd-Service eingerichtet und aktiviert"
fi

# Schritt 5: Status prüfen
log "📊 System-Status prüfen..."
./docker-deploy.sh status

# Schritt 6: Netzwerk-Info sammeln
log "🌐 Netzwerk-Informationen..."
VM_IP=$(hostname -I | awk '{print $1}' || echo "localhost")
HOSTNAME=$(hostname)

echo -e "\n${GREEN}╔═══════════════════════════════════════════════════╗"
echo -e "║               🎉 Setup Erfolgreich!               ║"
echo -e "╚═══════════════════════════════════════════════════╝${NC}\n"

echo -e "${BLUE}🌐 Externe Zugriffs-URLs:${NC}"
echo -e "   🌍 HTTP (empfohlen):  http://$VM_IP"
echo -e "   🌍 HTTPS (falls SSL): https://$VM_IP"
echo -e "   🌍 Direkt zur App:    http://$VM_IP:8501"
echo -e "   🌍 Hostname:          http://$HOSTNAME"

echo -e "\n${BLUE}🔒 SSH-Tunnel (für sichere Verbindung):${NC}"
echo -e "   ssh -L 8080:localhost:80 $(whoami)@$VM_IP"
echo -e "   → Browser: http://localhost:8080"

echo -e "\n${BLUE}🎯 Login-Daten:${NC}"
echo -e "   👤 Benutzername: admin"
echo -e "   🔑 Passwort:     admin123"
echo -e "   ⚠️  WICHTIG: Passwort nach erstem Login ändern!"

echo -e "\n${BLUE}🔧 Container-Management:${NC}"
echo -e "   Status:    ./docker-deploy.sh status"
echo -e "   Logs:      ./docker-deploy.sh logs"
echo -e "   Restart:   ./docker-deploy.sh restart"
echo -e "   Stoppen:   ./docker-deploy.sh stop"
echo -e "   Starten:   ./docker-deploy.sh start"

if [[ $setup_systemd == [yY] ]]; then
echo -e "\n${BLUE}🛠️  Systemd-Service:${NC}"
echo -e "   Status:    sudo systemctl status data-assistant-docker"
echo -e "   Stoppen:   sudo systemctl stop data-assistant-docker"
echo -e "   Starten:   sudo systemctl start data-assistant-docker"
echo -e "   Logs:      sudo journalctl -u data-assistant-docker -f"
fi

echo -e "\n${BLUE}🚀 Container starten automatisch nach Server-Neustart!${NC}"

echo -e "\n${GREEN}✅ Das System läuft permanent und ist extern erreichbar!${NC}"

# Test der Erreichbarkeit
log "🧪 Teste lokale Erreichbarkeit..."
sleep 5
if curl -s http://localhost:80/health > /dev/null 2>&1; then
    log "✅ HTTP (Port 80) funktioniert lokal"
elif curl -s http://localhost:8501 > /dev/null 2>&1; then
    log "✅ App (Port 8501) funktioniert lokal"
else
    warn "⚠️ Lokaler Test fehlgeschlagen - Container starten möglicherweise noch"
fi

echo -e "\n${YELLOW}💡 Nächste Schritte:${NC}"
echo -e "   1. Browser öffnen: http://$VM_IP"
echo -e "   2. Mit admin/admin123 einloggen"
echo -e "   3. Passwort ändern"
echo -e "   4. API-Key in .env konfigurieren (falls noch nicht geschehen)"

echo -e "\n${GREEN}🎉 Setup abgeschlossen!${NC}" 