#!/bin/bash
# =============================================================================
# Data Assistant Project - Deployment Script
# =============================================================================

set -e  # Exit on any error

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging Funktion
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Konfiguration
PROJECT_NAME="data_assistant"
PROJECT_DIR="/opt/${PROJECT_NAME}"
SERVICE_NAME="data-assistant"
PYTHON_VERSION="3.12"
USER_NAME=$(whoami)

# Header
echo -e "${BLUE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════╗
║           Data Assistant Deployment               ║
║               VM Installation Script              ║
╚═══════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "Dieses Skript sollte nicht als root ausgeführt werden!"
fi

# Check if sudo is available
if ! sudo -n true 2>/dev/null; then
    error "Sudo-Rechte erforderlich. Führen Sie 'sudo -v' aus."
fi

log "Starte Deployment für ${PROJECT_NAME}..."

# Funktion: System-Dependencies installieren
install_system_dependencies() {
    log "Installiere System-Dependencies..."
    
    # System aktualisieren
    sudo apt update && sudo apt upgrade -y
    
    # Base Dependencies
    sudo apt install -y \
        curl \
        wget \
        git \
        build-essential \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        ufw \
        nginx \
        sqlite3
    
    # Python 3.12 installieren
    if ! command -v python${PYTHON_VERSION} &> /dev/null; then
        log "Installiere Python ${PYTHON_VERSION}..."
        sudo add-apt-repository ppa:deadsnakes/ppa -y
        sudo apt update
        sudo apt install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-pip python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev
    else
        log "Python ${PYTHON_VERSION} bereits installiert"
    fi
}

# Funktion: Projektverzeichnis erstellen
setup_project_directory() {
    log "Erstelle Projektverzeichnis..."
    
    if [[ ! -d "$PROJECT_DIR" ]]; then
        sudo mkdir -p "$PROJECT_DIR"
        sudo chown $USER_NAME:$USER_NAME "$PROJECT_DIR"
    fi
    
    # Backup-Verzeichnis erstellen
    sudo mkdir -p /opt/backups/$PROJECT_NAME
    sudo chown $USER_NAME:$USER_NAME /opt/backups/$PROJECT_NAME
    
    # Log-Verzeichnis erstellen
    sudo mkdir -p /var/log/$PROJECT_NAME
    sudo chown $USER_NAME:$USER_NAME /var/log/$PROJECT_NAME
}

# Funktion: Python Environment einrichten
setup_python_environment() {
    log "Richte Python Environment ein..."
    
    cd "$PROJECT_DIR"
    
    # Virtual Environment erstellen
    if [[ ! -d "venv" ]]; then
        python${PYTHON_VERSION} -m venv venv
    fi
    
    # Virtual Environment aktivieren
    source venv/bin/activate
    
    # pip upgraden
    pip install --upgrade pip
    
    # Requirements installieren
    if [[ -f "new_data_assistant_project/requirements.txt" ]]; then
        pip install -r new_data_assistant_project/requirements.txt
    else
        warn "requirements.txt nicht gefunden. Installiere Standard-Dependencies..."
        pip install streamlit pandas anthropic python-dotenv numpy
    fi
    
    # Zusätzliche Production Dependencies
    pip install gunicorn supervisor
}

# Funktion: Umgebungsvariablen konfigurieren
configure_environment() {
    log "Konfiguriere Umgebungsvariablen..."
    
    cd "$PROJECT_DIR/new_data_assistant_project"
    
    if [[ ! -f ".env" ]]; then
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
EOF
        chmod 600 .env
        log "Umgebungsdatei .env erstellt. Bitte API-Schlüssel konfigurieren!"
    else
        log "Umgebungsdatei .env bereits vorhanden"
    fi
}

# Funktion: Datenbank initialisieren
initialize_database() {
    log "Initialisiere Datenbank..."
    
    cd "$PROJECT_DIR/new_data_assistant_project"
    source ../venv/bin/activate
    
    # PYTHONPATH setzen
    export PYTHONPATH="$PROJECT_DIR/new_data_assistant_project:$PYTHONPATH"
    
    # Datenbank-Verzeichnis erstellen
    mkdir -p src/database
    
    # Datenbank initialisieren
    python -c "
try:
    from src.database.schema import create_tables, create_admin_user
    create_tables()
    create_admin_user()
    print('✅ Datenbank erfolgreich initialisiert')
except Exception as e:
    print(f'❌ Fehler bei Datenbank-Initialisierung: {e}')
    print('Das kann normal sein, wenn die Datenbank bereits existiert.')
"
}

# Funktion: Systemd Service erstellen
create_systemd_service() {
    log "Erstelle Systemd Service..."
    
    sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=Data Assistant Streamlit App
After=network.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$PROJECT_DIR/new_data_assistant_project
Environment=PATH=$PROJECT_DIR/venv/bin
Environment=PYTHONPATH=$PROJECT_DIR/new_data_assistant_project
ExecStart=$PROJECT_DIR/venv/bin/streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=3
StandardOutput=append:/var/log/$PROJECT_NAME/app.log
StandardError=append:/var/log/$PROJECT_NAME/error.log

[Install]
WantedBy=multi-user.target
EOF

    # Service aktivieren
    sudo systemctl daemon-reload
    sudo systemctl enable ${SERVICE_NAME}
}

# Funktion: Firewall konfigurieren
configure_firewall() {
    log "Konfiguriere Firewall..."
    
    # UFW aktivieren falls nicht aktiv
    if ! sudo ufw status | grep -q "Status: active"; then
        sudo ufw --force enable
    fi
    
    # Standard-Regeln
    sudo ufw allow 22/tcp    # SSH
    sudo ufw allow 8501/tcp  # Streamlit
    sudo ufw allow 80/tcp    # HTTP (für Nginx)
    sudo ufw allow 443/tcp   # HTTPS (für Nginx)
    
    log "Firewall-Regeln konfiguriert"
}

# Funktion: Nginx konfigurieren
configure_nginx() {
    log "Konfiguriere Nginx..."
    
    # Nginx Konfiguration für Data Assistant
    sudo tee /etc/nginx/sites-available/$PROJECT_NAME << EOF
server {
    listen 80;
    server_name _;

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
        proxy_read_timeout 86400;
    }

    # Static files (falls benötigt)
    location /static {
        alias $PROJECT_DIR/new_data_assistant_project/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    # Site aktivieren
    sudo ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
    
    # Default Site deaktivieren
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Nginx Konfiguration testen
    sudo nginx -t
    
    # Nginx neustarten
    sudo systemctl enable nginx
    sudo systemctl restart nginx
}

# Funktion: Backup-Skript erstellen
create_backup_script() {
    log "Erstelle Backup-Skript..."
    
    sudo tee /opt/backups/$PROJECT_NAME/backup.sh << EOF
#!/bin/bash
BACKUP_DIR="/opt/backups/$PROJECT_NAME"
PROJECT_DIR="$PROJECT_DIR/new_data_assistant_project"
DATE=\$(date +%Y%m%d_%H%M%S)

# Datenbank sichern
if [[ -f "\$PROJECT_DIR/src/database/superstore.db" ]]; then
    cp "\$PROJECT_DIR/src/database/superstore.db" "\$BACKUP_DIR/superstore_\$DATE.db"
    echo "Database backup: superstore_\$DATE.db"
fi

# Logs archivieren
if [[ -d "/var/log/$PROJECT_NAME" ]]; then
    tar -czf "\$BACKUP_DIR/logs_\$DATE.tar.gz" /var/log/$PROJECT_NAME/ 2>/dev/null || true
    echo "Logs backup: logs_\$DATE.tar.gz"
fi

# Alte Backups löschen (älter als 30 Tage)
find "\$BACKUP_DIR" -name "*.db" -mtime +30 -delete
find "\$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: \$DATE"
EOF

    chmod +x /opt/backups/$PROJECT_NAME/backup.sh
    
    # Cronjob für tägliche Backups hinzufügen
    (crontab -l 2>/dev/null; echo "0 2 * * * /opt/backups/$PROJECT_NAME/backup.sh") | crontab -
}

# Funktion: Service starten
start_services() {
    log "Starte Services..."
    
    # Data Assistant Service starten
    sudo systemctl start ${SERVICE_NAME}
    
    # Status prüfen
    if sudo systemctl is-active --quiet ${SERVICE_NAME}; then
        log "✅ Data Assistant Service läuft"
    else
        warn "❌ Data Assistant Service konnte nicht gestartet werden"
        sudo journalctl -u ${SERVICE_NAME} --no-pager -n 20
    fi
    
    # Nginx Status prüfen
    if sudo systemctl is-active --quiet nginx; then
        log "✅ Nginx läuft"
    else
        warn "❌ Nginx konnte nicht gestartet werden"
    fi
}

# Funktion: Deployment-Info anzeigen
show_deployment_info() {
    echo -e "\n${GREEN}╔═══════════════════════════════════════════════════╗"
    echo -e "║            🎉 Deployment Erfolgreich!             ║"
    echo -e "╚═══════════════════════════════════════════════════╝${NC}\n"
    
    echo -e "${BLUE}📋 Deployment-Informationen:${NC}"
    echo -e "   🌐 URL: http://$(hostname -I | awk '{print $1}'):8501"
    echo -e "   🌐 Nginx URL: http://$(hostname -I | awk '{print $1}')/"
    echo -e "   📁 Projekt-Verzeichnis: $PROJECT_DIR"
    echo -e "   🗄️  Log-Verzeichnis: /var/log/$PROJECT_NAME"
    echo -e "   💾 Backup-Verzeichnis: /opt/backups/$PROJECT_NAME"
    
    echo -e "\n${BLUE}🔧 Nützliche Befehle:${NC}"
    echo -e "   Service Status:     sudo systemctl status ${SERVICE_NAME}"
    echo -e "   Service Neustarten: sudo systemctl restart ${SERVICE_NAME}"
    echo -e "   Logs anzeigen:      sudo journalctl -u ${SERVICE_NAME} -f"
    echo -e "   Backup ausführen:   /opt/backups/$PROJECT_NAME/backup.sh"
    
    echo -e "\n${YELLOW}⚠️  Wichtige Hinweise:${NC}"
    echo -e "   1. Konfigurieren Sie Ihren API-Schlüssel in: $PROJECT_DIR/new_data_assistant_project/.env"
    echo -e "   2. Standard-Login: admin / admin123 (bitte ändern!)"
    echo -e "   3. Überprüfen Sie die Firewall-Einstellungen"
    echo -e "   4. Richten Sie SSL/TLS für Produktion ein"
    
    echo -e "\n${GREEN}✅ Deployment abgeschlossen!${NC}"
}

# Main Deployment-Prozess
main() {
    log "Starte Deployment-Prozess..."
    
    # Pre-check: Projektverzeichnis muss existieren
    if [[ ! -d "new_data_assistant_project" ]]; then
        error "Projektverzeichnis 'new_data_assistant_project' nicht gefunden!"
    fi
    
    # Deployment-Schritte
    install_system_dependencies
    setup_project_directory
    
    # Projektdateien kopieren
    log "Kopiere Projektdateien..."
    cp -r new_data_assistant_project/* "$PROJECT_DIR/new_data_assistant_project/" 2>/dev/null || true
    
    setup_python_environment
    configure_environment
    initialize_database
    create_systemd_service
    configure_firewall
    configure_nginx
    create_backup_script
    start_services
    show_deployment_info
}

# Fehler-Handler
trap 'error "Deployment fehlgeschlagen in Zeile $LINENO"' ERR

# Script ausführen
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 

# =============================================================================
# Deployment Script for Data Assistant Project
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# Configuration
# =============================================================================
PROJECT_NAME="data-assistant"
COMPOSE_FILE="deployment/docker-compose.yml"
ENV_FILE="deployment/.env"
CONFIG_TEMPLATE="deployment/config.template"

print_status "🚀 Starting deployment of $PROJECT_NAME..."

# =============================================================================
# 1. Pre-deployment Checks
# =============================================================================
print_status "Running pre-deployment checks..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running or not accessible. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please run vm-setup.sh first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "$COMPOSE_FILE" ]; then
    print_error "docker-compose.yml not found. Please run this script from the project root."
    exit 1
fi

print_success "Pre-deployment checks passed!"

# =============================================================================
# 2. Environment Configuration
# =============================================================================
print_status "Configuring environment..."

# Create .env file if it doesn't exist
if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$CONFIG_TEMPLATE" ]; then
        cp "$CONFIG_TEMPLATE" "$ENV_FILE"
        print_warning "Created $ENV_FILE from template. Please edit it with your configuration!"
        print_warning "Don't forget to set your ANTHROPIC_API_KEY!"
        
        # Ask user if they want to edit now
        read -p "Do you want to edit the .env file now? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} "$ENV_FILE"
        fi
    else
        print_error "No configuration template found. Please create $ENV_FILE manually."
        exit 1
    fi
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p data/user_profiles
mkdir -p evaluation/results
mkdir -p deployment/secrets

print_success "Environment configured!"

# =============================================================================
# 3. Build and Deploy
# =============================================================================
print_status "Building and starting containers..."

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true

# Pull latest images (for services that use external images)
print_status "Pulling latest base images..."
docker-compose -f "$COMPOSE_FILE" pull --ignore-pull-failures 2>/dev/null || true

# Build and start services
print_status "Building and starting services..."
docker-compose -f "$COMPOSE_FILE" up --build -d

# Wait for services to be healthy
print_status "Waiting for services to be ready..."
sleep 10

# Check if main service is running
if docker-compose -f "$COMPOSE_FILE" ps | grep -q "data-assistant-app.*Up"; then
    print_success "Data Assistant is running!"
else
    print_error "Data Assistant failed to start. Checking logs..."
    docker-compose -f "$COMPOSE_FILE" logs data-assistant
    exit 1
fi

print_success "🎉 Deployment completed successfully!"

# =============================================================================
# 4. Post-deployment Information
# =============================================================================
echo
print_status "📊 Service Status:"
docker-compose -f "$COMPOSE_FILE" ps

echo
print_status "🌐 Access Information:"
echo "  • Main Application: http://localhost:8501"
echo "  • With Nginx (if enabled): http://localhost"
echo "  • Monitoring (if enabled): http://localhost:9090"

echo
print_status "📝 Useful Commands:"
echo "  • View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "  • Stop services: docker-compose -f $COMPOSE_FILE down"
echo "  • Restart: docker-compose -f $COMPOSE_FILE restart"
echo "  • Update: bash deployment/deploy.sh"

echo
print_status "🔧 Management Commands:"
echo "  • Enter container: docker-compose -f $COMPOSE_FILE exec data-assistant bash"
echo "  • View container logs: docker-compose -f $COMPOSE_FILE logs data-assistant"
echo "  • Monitor resources: docker stats"

echo
print_success "✅ Data Assistant is now running!"
print_warning "Don't forget to configure your API keys in $ENV_FILE if you haven't already!" 