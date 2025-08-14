#!/bin/bash

# Installs and configures Nginx as reverse proxy for Streamlit on EC2 (Amazon Linux 2023)
# Must be run with sudo privileges

set -euo pipefail

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log() { echo -e "${BLUE}ℹ️  $1${NC}"; }
ok() { echo -e "${GREEN}✅ $1${NC}"; }
err() { echo -e "${RED}❌ $1${NC}"; }

if [ "$EUID" -ne 0 ]; then
  err "Please run as root: sudo bash setup-nginx.sh"
  exit 1
fi

log "Installing Nginx..."
dnf install -y nginx
systemctl enable --now nginx

CONFIG_SRC_DIR=$(dirname "$0")
CONFIG_FILE_SRC="$CONFIG_SRC_DIR/streamlit.conf"
CONFIG_FILE_DST="/etc/nginx/conf.d/streamlit.conf"

if [ ! -f "$CONFIG_FILE_SRC" ]; then
  err "Config file not found: $CONFIG_FILE_SRC"
  exit 1
fi

log "Deploying Nginx config to $CONFIG_FILE_DST ..."
cp "$CONFIG_FILE_SRC" "$CONFIG_FILE_DST"

log "Testing Nginx configuration..."
nginx -t

log "Reloading Nginx..."
systemctl reload nginx

ok "Nginx is configured. Ensure your Security Group allows inbound 80/443."

echo "" 
echo "To enable HTTPS with Let's Encrypt, run:" 
echo "  dnf install -y certbot python3-certbot-nginx" 
echo "  certbot --nginx -d your.domain.example"
