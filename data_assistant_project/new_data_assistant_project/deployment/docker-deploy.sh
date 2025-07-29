#!/bin/bash
# =============================================================================
# Data Assistant Project - Docker Deployment Script
# =============================================================================

set -e  # Exit on any error

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging Funktionen
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
DOCKER_IMAGE_NAME="data-assistant"
DOCKER_TAG="latest"
COMPOSE_FILE="docker-compose.yml"

# Header
echo -e "${BLUE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════╗
║           Data Assistant Docker Deploy            ║
║              Container Deployment                 ║
╚═══════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Funktionen
check_prerequisites() {
    log "Überprüfe Voraussetzungen..."
    
    # Docker installiert?
    if ! command -v docker &> /dev/null; then
        error "Docker ist nicht installiert. Bitte installieren Sie Docker zuerst."
    fi
    
    # Docker-Compose installiert?
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose ist nicht installiert."
    fi
    
    # Docker läuft?
    if ! docker info &> /dev/null; then
        error "Docker läuft nicht. Starten Sie Docker zuerst."
    fi
    
    # Projektverzeichnis vorhanden?
    if [[ ! -f "../frontend/app.py" ]]; then
        error "Projektverzeichnis nicht gefunden. Führen Sie das Skript aus dem deployment/ Verzeichnis aus."
    fi
    
    log "✅ Alle Voraussetzungen erfüllt"
}

install_docker() {
    log "Installiere Docker..."
    
    # Docker installieren
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    
    # Docker Compose installieren
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # User zur Docker-Gruppe hinzufügen
    sudo usermod -aG docker $USER
    
    log "✅ Docker installiert. Bitte loggen Sie sich neu ein oder führen Sie 'newgrp docker' aus."
}

setup_environment() {
    log "Richte Docker-Umgebung ein..."
    
    # Arbeitsverzeichnisse erstellen
    mkdir -p data/database
    mkdir -p data/user_profiles
    mkdir -p logs
    mkdir -p monitoring
    
    # .env Datei erstellen falls nicht vorhanden
    if [[ ! -f "../.env" ]]; then
        cat > ../.env << EOF
# API Konfiguration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database Konfiguration
DATABASE_URL=sqlite:///src/database/superstore.db

# Streamlit Konfiguration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Application
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)

# Docker Spezifisch
TZ=Europe/Berlin
EOF
        warn "⚠️ .env Datei erstellt. Bitte konfigurieren Sie Ihren API-Schlüssel!"
    fi
    
    # Berechtigungen setzen
    chmod 600 ../.env
    
    log "✅ Umgebung vorbereitet"
}

build_image() {
    log "Baue Docker Image..."
    
    # Image bauen
    docker build -f Dockerfile -t $DOCKER_IMAGE_NAME:$DOCKER_TAG ..
    
    # Image Info
    docker images $DOCKER_IMAGE_NAME:$DOCKER_TAG
    
    log "✅ Docker Image erfolgreich gebaut"
}

deploy_with_compose() {
    log "Deploye mit Docker Compose..."
    
    # Alte Container stoppen und entfernen
    docker-compose down 2>/dev/null || true
    
    # Container starten
    docker-compose up -d
    
    # Warten bis Container gestartet sind
    log "Warte auf Container-Start..."
    sleep 10
    
    # Status prüfen
    docker-compose ps
    
    log "✅ Container gestartet"
}

setup_monitoring() {
    log "Richte Monitoring ein..."
    
    # Prometheus Konfiguration
    mkdir -p monitoring
    cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'data-assistant'
    static_configs:
      - targets: ['data-assistant:8501']
    metrics_path: '/metrics'
    scrape_interval: 30s
EOF
    
    # Monitoring Container starten (optional)
    if [[ "$1" == "--with-monitoring" ]]; then
        docker-compose --profile monitoring up -d
        log "✅ Monitoring Container gestartet"
    fi
}

setup_nginx_proxy() {
    log "Richte Nginx Reverse Proxy ein..."
    
    # Nginx Konfiguration
    cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream data_assistant {
        server data-assistant:8501;
    }

    server {
        listen 80;
        server_name _;

        client_max_body_size 50M;

        location / {
            proxy_pass http://data_assistant;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            proxy_read_timeout 86400;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

    # Nginx Container starten (falls im compose definiert)
    if [[ "$1" == "--with-nginx" ]]; then
        docker-compose --profile production up -d
        log "✅ Nginx Proxy gestartet"
    fi
}

health_check() {
    log "Führe Health-Check durch..."
    
    # Warten auf Service
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8501/_stcore/health &>/dev/null; then
            log "✅ Anwendung ist erreichbar"
            return 0
        fi
        
        log "Warte auf Anwendung... (Versuch $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    error "❌ Health-Check fehlgeschlagen"
}

show_status() {
    log "Zeige Container-Status..."
    
    echo -e "\n${BLUE}📊 Container Status:${NC}"
    docker-compose ps
    
    echo -e "\n${BLUE}📊 Resource Usage:${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
    
    echo -e "\n${BLUE}📊 Logs (letzte 20 Zeilen):${NC}"
    docker-compose logs --tail=20 data-assistant
}

cleanup() {
    log "Bereinige alte Container und Images..."
    
    # Stoppe Container
    docker-compose down
    
    # Entferne ungenutzte Images
    docker image prune -f
    
    # Entferne ungenutzte Volumes (Vorsicht!)
    read -p "Möchten Sie ungenutzte Volumes entfernen? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume prune -f
    fi
    
    log "✅ Bereinigung abgeschlossen"
}

backup_data() {
    log "Erstelle Datenbank-Backup..."
    
    # Timestamp
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="./backups"
    
    mkdir -p $backup_dir
    
    # Datenbank aus Container kopieren
    docker-compose exec -T data-assistant cp /app/src/database/superstore.db /tmp/superstore_backup.db || true
    docker cp $(docker-compose ps -q data-assistant):/tmp/superstore_backup.db $backup_dir/superstore_${timestamp}.db
    
    log "✅ Backup erstellt: $backup_dir/superstore_${timestamp}.db"
}

show_deployment_info() {
    echo -e "\n${GREEN}╔═══════════════════════════════════════════════════╗"
    echo -e "║          🐳 Docker Deployment Erfolgreich!        ║"
    echo -e "╚═══════════════════════════════════════════════════╝${NC}\n"
    
    echo -e "${BLUE}📋 Deployment-Informationen:${NC}"
    echo -e "   🌐 Streamlit URL: http://localhost:8501"
    echo -e "   🌐 Nginx URL: http://localhost:80 (falls aktiviert)"
    echo -e "   📊 Monitoring: http://localhost:9090 (Prometheus)"
    echo -e "   📊 Dashboard: http://localhost:3000 (Grafana)"
    
    echo -e "\n${BLUE}🔧 Docker-Befehle:${NC}"
    echo -e "   Container Status:   docker-compose ps"
    echo -e "   Logs anzeigen:      docker-compose logs -f"
    echo -e "   Container stoppen:  docker-compose down"
    echo -e "   Container starten:  docker-compose up -d"
    echo -e "   Shell öffnen:       docker-compose exec data-assistant bash"
    
    echo -e "\n${BLUE}🔧 Wartungs-Befehle:${NC}"
    echo -e "   Backup erstellen:   $0 backup"
    echo -e "   Status anzeigen:    $0 status"
    echo -e "   Bereinigung:        $0 cleanup"
    
    echo -e "\n${YELLOW}⚠️  Wichtige Hinweise:${NC}"
    echo -e "   1. Konfigurieren Sie Ihren API-Schlüssel in ../.env"
    echo -e "   2. Standard-Login: admin / admin123"
    echo -e "   3. Datenbank wird in ./data/database persistiert"
    echo -e "   4. Logs werden in ./logs/ gespeichert"
}

# Main-Funktion
main() {
    case "${1:-deploy}" in
        "install-docker")
            install_docker
            ;;
        "deploy")
            check_prerequisites
            setup_environment
            build_image
            deploy_with_compose
            setup_monitoring "$2"
            setup_nginx_proxy "$2"
            health_check
            show_deployment_info
            ;;
        "status")
            show_status
            ;;
        "backup")
            backup_data
            ;;
        "cleanup")
            cleanup
            ;;
        "logs")
            docker-compose logs -f data-assistant
            ;;
        "restart")
            docker-compose restart data-assistant
            ;;
        "stop")
            docker-compose down
            ;;
        "start")
            docker-compose up -d
            ;;
        *)
            echo "Usage: $0 {deploy|install-docker|status|backup|cleanup|logs|restart|stop|start}"
            echo ""
            echo "  deploy           - Vollständiges Deployment"
            echo "  install-docker   - Docker installieren"
            echo "  status          - Container-Status anzeigen"
            echo "  backup          - Datenbank-Backup erstellen"
            echo "  cleanup         - Alte Container bereinigen"
            echo "  logs            - Live-Logs anzeigen"
            echo "  restart         - Container neustarten"
            echo "  stop            - Container stoppen"
            echo "  start           - Container starten"
            echo ""
            echo "Deployment-Optionen:"
            echo "  $0 deploy --with-monitoring  # Mit Prometheus/Grafana"
            echo "  $0 deploy --with-nginx       # Mit Nginx Reverse Proxy"
            exit 1
            ;;
    esac
}

# Fehler-Handler
trap 'error "Docker-Deployment fehlgeschlagen in Zeile $LINENO"' ERR

# Script ausführen
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 