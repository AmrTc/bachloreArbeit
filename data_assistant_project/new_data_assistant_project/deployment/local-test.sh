#!/bin/bash

# Lokales Test-Skript für Data Assistant Docker-Container
# Führt alle notwendigen Schritte für den lokalen Test durch

set -e  # Beende bei Fehlern

echo "🚀 Lokaler Docker-Test für Data Assistant Project"
echo "=================================================="

# Farben für bessere Lesbarkeit
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funktionen
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Prüfe, ob Docker läuft
check_docker() {
    log_info "Prüfe Docker-Status..."
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker läuft nicht! Bitte starte Docker Desktop."
        exit 1
    fi
    log_success "Docker läuft"
}

# Prüfe, ob Docker Compose verfügbar ist
check_docker_compose() {
    log_info "Prüfe Docker Compose..."
    if ! docker-compose --version > /dev/null 2>&1; then
        log_error "Docker Compose ist nicht verfügbar!"
        exit 1
    fi
    log_success "Docker Compose verfügbar"
}

# Bereinige alte Container und Images
cleanup() {
    log_info "Bereinige alte Container und Images..."
    
    # Stoppe laufende Container
    if docker-compose -f docker-compose.yml down > /dev/null 2>&1; then
        log_success "Alte Container gestoppt"
    fi
    
    # Entferne alte Images (optional)
    read -p "Möchtest du alte Images entfernen? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker system prune -f
        log_success "Alte Images entfernt"
    fi
}

# Baue das Docker Image
build_image() {
    log_info "Baue Docker Image..."
    
    # Wechsle ins deployment Verzeichnis
    cd "$(dirname "$0")"
    
    # Baue das Image
    if docker-compose build --no-cache; then
        log_success "Docker Image erfolgreich gebaut"
    else
        log_error "Fehler beim Bauen des Docker Images"
        exit 1
    fi
}

# Starte die Container
start_containers() {
    log_info "Starte Container..."
    
    if docker-compose up -d; then
        log_success "Container erfolgreich gestartet"
    else
        log_error "Fehler beim Starten der Container"
        exit 1
    fi
}

# Prüfe den Status der Container
check_status() {
    log_info "Prüfe Container-Status..."
    
    # Warte kurz, bis der Container vollständig gestartet ist
    sleep 10
    
    # Zeige Container-Status
    echo
    docker-compose ps
    echo
    
    # Prüfe Logs
    log_info "Container-Logs:"
    docker-compose logs --tail=20
}

# Teste die Anwendung
test_application() {
    log_info "Teste Anwendung..."
    
    # Warte auf Anwendung
    log_info "Warte auf Anwendung (max. 60 Sekunden)..."
    
    for i in {1..12}; do
        if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
            log_success "Anwendung ist erreichbar!"
            break
        fi
        
        if [ $i -eq 12 ]; then
            log_error "Anwendung konnte nicht erreicht werden"
            log_info "Zeige Logs für Debugging:"
            docker-compose logs
            exit 1
        fi
        
        echo -n "."
        sleep 5
    done
    
    echo
    log_success "Anwendung läuft erfolgreich auf http://localhost:8501"
}

# Zeige nützliche Befehle
show_commands() {
    echo
    echo "🔧 Nützliche Befehle:"
    echo "====================="
    echo "Container-Logs anzeigen:  docker-compose logs -f"
    echo "Container stoppen:        docker-compose down"
    echo "Container neu starten:    docker-compose restart"
    echo "Container-Status:         docker-compose ps"
    echo "Shell im Container:       docker-compose exec streamlit-app bash"
    echo
}

# Hauptfunktion
main() {
    echo "Starte lokalen Docker-Test..."
    echo
    
    # Wechsle ins deployment Verzeichnis
    cd "$(dirname "$0")"
    
    # Führe alle Schritte aus
    check_docker
    check_docker_compose
    cleanup
    build_image
    start_containers
    check_status
    test_application
    show_commands
    
    log_success "Lokaler Docker-Test erfolgreich abgeschlossen!"
    echo
    echo "🌐 Öffne http://localhost:8501 in deinem Browser"
    echo "🛑 Stoppe die Container mit: docker-compose down"
}

# Skript ausführen
main "$@"
