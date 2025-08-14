#!/bin/bash

# EC2 Setup Script for Amazon Linux 2023
# - Installs Docker, Docker Compose plugin and Git
# - Starts Docker and enables on boot
# - Optionally clones repository and starts docker compose
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/<YOUR_REPO>/deployment/ec2-setup.sh | bash
# or copy this file to the EC2 instance and run: bash ec2-setup.sh
#
# Optional env vars:
#   REPO_URL=https://github.com/<owner>/<repo>.git
#   REPO_BRANCH=main
#   APP_DIR=/opt/data_assistant

set -euo pipefail

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log() { echo -e "${BLUE}ℹ️  $1${NC}"; }
ok() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
err() { echo -e "${RED}❌ $1${NC}"; }

APP_DIR=${APP_DIR:-/opt/data_assistant}
REPO_URL=${REPO_URL:-}
REPO_BRANCH=${REPO_BRANCH:-main}

log "Updating system packages..."
sudo dnf update -y

log "Installing Docker, Docker Compose plugin, and Git..."
sudo dnf install -y docker docker-compose-plugin git

log "Enabling and starting Docker service..."
sudo systemctl enable --now docker

log "Adding current user to docker group..."
sudo usermod -aG docker $USER || true

# Note: group change requires re-login; we'll use sudo docker for this run

log "Creating application directory at ${APP_DIR}..."
sudo mkdir -p ${APP_DIR}
sudo chown -R $USER:$USER ${APP_DIR}
cd ${APP_DIR}

if [ -n "${REPO_URL}" ]; then
  log "Cloning repository ${REPO_URL} (branch: ${REPO_BRANCH})..."
  if [ ! -d repo ]; then
    git clone --branch ${REPO_BRANCH} ${REPO_URL} repo
  else
    cd repo && git fetch && git checkout ${REPO_BRANCH} && git pull && cd -
  fi
  cd repo/new_data_assistant_project/deployment
else
  warn "REPO_URL not set. Skipping git clone. Copy your project to ${APP_DIR} and run docker compose manually."
fi

if [ -f docker-compose.yml ]; then
  log "Building Docker images..."
  sudo docker compose build

  log "Starting services..."
  sudo docker compose up -d

  ok "Services started."
  log "Check status: sudo docker compose ps"
  log "Follow logs: sudo docker compose logs -f"
else
  warn "docker-compose.yml not found in $(pwd). Skipping compose start."
fi

ok "EC2 setup complete."
