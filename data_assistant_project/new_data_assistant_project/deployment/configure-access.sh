#!/bin/bash
# =============================================================================
# Access-Konfigurationsskript für Data Assistant VM-Deployment
# =============================================================================

set -e

# Farben für Output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════╗
║         🔐 Access-Konfiguration Setup             ║
║            Data Assistant Project                 ║
╚═══════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Funktionen
prompt_input() {
    local prompt="$1"
    local default="$2"
    local secret="$3"
    
    if [[ "$secret" == "true" ]]; then
        echo -n -e "${YELLOW}$prompt${NC}"
        [[ -n "$default" ]] && echo -n " [Standard: $default]"
        echo -n ": "
        read -s value
        echo
    else
        echo -n -e "${YELLOW}$prompt${NC}"
        [[ -n "$default" ]] && echo -n " [Standard: $default]"
        echo -n ": "
        read value
    fi
    
    [[ -z "$value" ]] && value="$default"
    echo "$value"
}

generate_secret_key() {
    openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))" || echo "$(date +%s | sha256sum | head -c 64)"
}

main() {
    echo -e "${GREEN}Konfigurieren Sie die Access-Daten für Ihr VM-Deployment${NC}\n"
    
    # SSH-Konfiguration
    echo -e "${BLUE}📡 VM SSH-Verbindung${NC}"
    VM_HOST=$(prompt_input "VM IP-Adresse oder Domain" "")
    VM_USER=$(prompt_input "SSH-Benutzername" "ubuntu")
    VM_SSH_KEY=$(prompt_input "SSH-Key-Pfad (leer für Passwort-Auth)" "")
    VM_PORT=$(prompt_input "SSH-Port" "22")
    
    echo
    
    # Admin-Konfiguration
    echo -e "${BLUE}👤 Anwendungs-Administrator${NC}"
    ADMIN_USERNAME=$(prompt_input "Admin-Benutzername" "admin")
    ADMIN_PASSWORD=$(prompt_input "Admin-Passwort" "admin123" "true")
    ADMIN_EMAIL=$(prompt_input "Admin E-Mail" "admin@example.com")
    
    echo
    
    # API-Konfiguration
    echo -e "${BLUE}🔑 API-Schlüssel${NC}"
    ANTHROPIC_API_KEY=$(prompt_input "Anthropic API-Schlüssel" "" "true")
    OPENAI_API_KEY=$(prompt_input "OpenAI API-Schlüssel (optional)" "" "true")
    
    echo
    
    # Sicherheitseinstellungen
    echo -e "${BLUE}🔒 Sicherheit${NC}"
    SECRET_KEY=$(generate_secret_key)
    echo -e "${YELLOW}Secret Key automatisch generiert${NC}"
    
    SESSION_TIMEOUT=$(prompt_input "Session-Timeout (Sekunden)" "3600")
    MAX_LOGIN_ATTEMPTS=$(prompt_input "Max. Anmeldeversuche" "5")
    
    echo
    
    # SSL-Konfiguration
    echo -e "${BLUE}🔐 SSL/HTTPS (Optional)${NC}"
    SSL_ENABLED=$(prompt_input "SSL aktivieren? (true/false)" "false")
    if [[ "$SSL_ENABLED" == "true" ]]; then
        DOMAIN_NAME=$(prompt_input "Domain-Name" "")
        SSL_CERT_PATH=$(prompt_input "SSL-Zertifikat-Pfad" "")
        SSL_KEY_PATH=$(prompt_input "SSL-Schlüssel-Pfad" "")
    else
        DOMAIN_NAME=""
        SSL_CERT_PATH=""
        SSL_KEY_PATH=""
    fi
    
    echo
    
    # Monitoring
    echo -e "${BLUE}📊 Monitoring (Optional)${NC}"
    ENABLE_MONITORING=$(prompt_input "Monitoring aktivieren? (true/false)" "false")
    if [[ "$ENABLE_MONITORING" == "true" ]]; then
        GRAFANA_ADMIN_PASSWORD=$(prompt_input "Grafana Admin-Passwort" "admin" "true")
    else
        GRAFANA_ADMIN_PASSWORD="admin"
    fi
    
    echo
    
    # Konfigurationsdateien erstellen
    echo -e "${GREEN}💾 Erstelle Konfigurationsdateien...${NC}"
    
    # VM-Config erstellen
    cat > vm-config.sh << EOF
#!/bin/bash
# Automatisch generierte VM-Konfiguration
# Erstellt am: $(date)

# SSH-Verbindung
export VM_HOST="$VM_HOST"
export VM_USER="$VM_USER"
export VM_SSH_KEY="$VM_SSH_KEY"
export VM_PORT="$VM_PORT"

# Admin-Benutzer
export ADMIN_USERNAME="$ADMIN_USERNAME"
export ADMIN_PASSWORD="$ADMIN_PASSWORD"
export ADMIN_EMAIL="$ADMIN_EMAIL"

# API-Schlüssel
export ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"
export OPENAI_API_KEY="$OPENAI_API_KEY"

# Sicherheit
export SECRET_KEY="$SECRET_KEY"
export SESSION_TIMEOUT="$SESSION_TIMEOUT"
export MAX_LOGIN_ATTEMPTS="$MAX_LOGIN_ATTEMPTS"

# SSL
export SSL_ENABLED="$SSL_ENABLED"
export DOMAIN_NAME="$DOMAIN_NAME"
export SSL_CERT_PATH="$SSL_CERT_PATH"
export SSL_KEY_PATH="$SSL_KEY_PATH"

# Monitoring
export ENABLE_MONITORING="$ENABLE_MONITORING"
export GRAFANA_ADMIN_PASSWORD="$GRAFANA_ADMIN_PASSWORD"
EOF
    
    chmod 600 vm-config.sh
    
    # .env für Docker erstellen
    cat > ../.env << EOF
# Automatisch generierte Umgebungskonfiguration
# Erstellt am: $(date)

# API-Konfiguration
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
OPENAI_API_KEY=$OPENAI_API_KEY

# Datenbank-Konfiguration
DATABASE_URL=sqlite:///src/database/superstore.db

# Streamlit-Konfiguration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Anwendungs-Konfiguration
DEBUG=False
APP_ENV=production
LOG_LEVEL=INFO

# Sicherheit
SECRET_KEY=$SECRET_KEY
SESSION_TIMEOUT=$SESSION_TIMEOUT
MAX_LOGIN_ATTEMPTS=$MAX_LOGIN_ATTEMPTS

# Admin-Benutzer
ADMIN_USERNAME=$ADMIN_USERNAME
ADMIN_PASSWORD=$ADMIN_PASSWORD
ADMIN_EMAIL=$ADMIN_EMAIL

# SSL/TLS
SSL_ENABLED=$SSL_ENABLED
DOMAIN_NAME=$DOMAIN_NAME

# Monitoring
ENABLE_METRICS=$ENABLE_MONITORING
GRAFANA_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD

# Docker-spezifisch
TZ=Europe/Berlin
EOF
    
    chmod 600 ../.env
    
    # SSH-Verbindungstest anbieten
    echo -e "\n${GREEN}✅ Konfiguration erstellt!${NC}"
    echo -e "\n${BLUE}📁 Erstellte Dateien:${NC}"
    echo -e "   🔧 vm-config.sh - VM-Konfiguration"
    echo -e "   🔧 ../.env - Anwendungs-Umgebung"
    
    echo -e "\n${YELLOW}🔍 Möchten Sie die SSH-Verbindung testen? (y/N):${NC} "
    read -n 1 test_ssh
    echo
    
    if [[ "$test_ssh" =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}🧪 Teste SSH-Verbindung...${NC}"
        
        ssh_cmd="ssh"
        [[ -n "$VM_SSH_KEY" ]] && ssh_cmd="$ssh_cmd -i $VM_SSH_KEY"
        [[ "$VM_PORT" != "22" ]] && ssh_cmd="$ssh_cmd -p $VM_PORT"
        ssh_cmd="$ssh_cmd $VM_USER@$VM_HOST"
        
        echo -e "${YELLOW}Führe aus: $ssh_cmd 'echo Verbindung erfolgreich!'${NC}"
        
        if eval "$ssh_cmd 'echo \"✅ SSH-Verbindung erfolgreich!\"'"; then
            echo -e "${GREEN}✅ SSH-Verbindung funktioniert!${NC}"
        else
            echo -e "${RED}❌ SSH-Verbindung fehlgeschlagen. Überprüfen Sie Ihre Einstellungen.${NC}"
        fi
    fi
    
    # Deployment-Optionen anzeigen
    echo -e "\n${GREEN}🚀 Nächste Schritte:${NC}"
    echo -e "\n${BLUE}Option 1 - Direkte Installation:${NC}"
    echo -e "   source vm-config.sh"
    echo -e "   ./deploy-to-vm.sh"
    
    echo -e "\n${BLUE}Option 2 - Docker Deployment:${NC}"
    echo -e "   source vm-config.sh"
    echo -e "   ./docker-deploy-to-vm.sh"
    
    echo -e "\n${BLUE}Option 3 - Manuell:${NC}"
    echo -e "   scp -r ../new_data_assistant_project/ \$VM_USER@\$VM_HOST:/opt/"
    echo -e "   ssh \$VM_USER@\$VM_HOST"
    echo -e "   cd /opt/new_data_assistant_project/deployment"
    echo -e "   ./deploy.sh  # oder ./docker-deploy.sh deploy"
    
    echo -e "\n${YELLOW}⚠️  Wichtige Hinweise:${NC}"
    echo -e "   🔐 Bewahren Sie vm-config.sh und .env sicher auf!"
    echo -e "   🔐 Fügen Sie diese Dateien NICHT zu Git hinzu!"
    echo -e "   🔄 Admin-Passwort nach erstem Login ändern!"
    
    echo -e "\n${GREEN}🎉 Konfiguration abgeschlossen!${NC}"
}

# Script ausführen
main "$@" 