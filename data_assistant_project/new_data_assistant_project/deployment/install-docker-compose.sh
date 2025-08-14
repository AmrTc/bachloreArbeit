#!/bin/bash

# Install Docker Compose v2 as Docker CLI plugin
# Works on Amazon Linux 2023 (and most Linux distros)

set -euo pipefail

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info(){ echo -e "${BLUE}ℹ️  $1${NC}"; }
ok(){ echo -e "${GREEN}✅ $1${NC}"; }
err(){ echo -e "${RED}❌ $1${NC}"; }

VERSION="v2.27.0"
ARCH=$(uname -m)

case "$ARCH" in
  x86_64)
    ASSET="docker-compose-linux-x86_64" ;;
  aarch64|arm64)
    ASSET="docker-compose-linux-aarch64" ;;
  *)
    err "Unsupported architecture: $ARCH"
    exit 1 ;;
 esac

TARGET_DIR="/usr/local/lib/docker/cli-plugins"
TARGET_FILE="$TARGET_DIR/docker-compose"

info "Creating target directory: $TARGET_DIR"
sudo mkdir -p "$TARGET_DIR"

URL="https://github.com/docker/compose/releases/download/${VERSION}/${ASSET}"
info "Downloading Docker Compose ${VERSION} ($ARCH) ..."
sudo curl -fsSL "$URL" -o "$TARGET_FILE"

info "Making it executable ..."
sudo chmod +x "$TARGET_FILE"

info "Verifying installation ..."
if docker compose version; then
  ok "Docker Compose installed successfully."
else
  err "Docker Compose installation failed. Check permissions and PATH."
  echo "Expected plugin at: $TARGET_FILE"
  exit 1
fi
