#!/bin/bash

# =============================================================================
# VM Setup Script for Data Assistant Project
# =============================================================================

set -e  # Exit on any error

echo "🚀 Starting VM Setup for Data Assistant Project..."

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
# 1. System Update
# =============================================================================
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# =============================================================================
# 2. Install Essential Tools
# =============================================================================
print_status "Installing essential tools..."
sudo apt install -y \
    curl \
    wget \
    git \
    unzip \
    vim \
    htop \
    ufw \
    fail2ban \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# =============================================================================
# 3. Install Docker
# =============================================================================
print_status "Installing Docker..."

# Remove old Docker installations
sudo apt-get remove -y docker docker-engine docker.io containerd runc || true

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Add current user to docker group
sudo usermod -aG docker $USER

print_success "Docker installed successfully!"

# =============================================================================
# 4. Install Docker Compose
# =============================================================================
print_status "Installing Docker Compose..."

# Get latest version
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)

# Download and install
sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

print_success "Docker Compose ${DOCKER_COMPOSE_VERSION} installed successfully!"

# =============================================================================
# 5. Configure Firewall
# =============================================================================
print_status "Configuring firewall..."

sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow Streamlit port
sudo ufw allow 8501/tcp

# Enable firewall
sudo ufw --force enable

print_success "Firewall configured successfully!"

# =============================================================================
# 6. Install Python 3.12 (if not available)
# =============================================================================
print_status "Checking Python installation..."

if ! command -v python3.12 &> /dev/null; then
    print_status "Installing Python 3.12..."
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    sudo apt install -y python3.12 python3.12-venv python3.12-pip
fi

# Set Python 3.12 as default python3
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1

print_success "Python 3.12 is ready!"

# =============================================================================
# 7. Create Project Directory
# =============================================================================
print_status "Creating project directory..."

PROJECT_DIR="/opt/data-assistant"
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

print_success "Project directory created at $PROJECT_DIR"

# =============================================================================
# 8. Install Monitoring Tools (Optional)
# =============================================================================
print_status "Installing monitoring tools..."

# Install htop, iotop, nethogs for system monitoring
sudo apt install -y htop iotop nethogs

print_success "Monitoring tools installed!"

# =============================================================================
# 9. Configure Log Rotation
# =============================================================================
print_status "Configuring log rotation..."

sudo tee /etc/logrotate.d/data-assistant > /dev/null <<EOF
/var/log/data-assistant/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF

print_success "Log rotation configured!"

# =============================================================================
# Final Instructions
# =============================================================================
print_success "🎉 VM Setup Complete!"
echo
print_warning "IMPORTANT: Please log out and log back in for Docker group membership to take effect."
echo
print_status "Next steps:"
echo "1. Clone your project repository to $PROJECT_DIR"
echo "2. Configure your .env file with API keys"
echo "3. Run the deployment script"
echo
print_status "Example commands:"
echo "cd $PROJECT_DIR"
echo "git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git ."
echo "cp deployment/config.template deployment/.env"
echo "# Edit deployment/.env with your configuration"
echo "bash deployment/deploy.sh"

print_success "Setup completed successfully! 🚀" 