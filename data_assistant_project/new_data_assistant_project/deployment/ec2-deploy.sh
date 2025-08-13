#!/bin/bash

# EC2 Deployment Script für Data Assistant Project
# Führen Sie dieses Script auf Ihrer EC2 Instance aus

echo "🚀 Starting EC2 Deployment for Data Assistant Project..."

# System aktualisieren
echo "📦 Updating system packages..."
sudo yum update -y

# Docker installieren
echo "🐳 Installing Docker..."
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Docker Compose installieren
echo "📋 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Git installieren
echo "📚 Installing Git..."
sudo yum install -y git

# Firewall konfigurieren (Port 8501 öffnen)
echo "🔥 Configuring firewall..."
sudo yum install -y firewalld
sudo systemctl start firewalld
sudo systemctl enable firewalld
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --reload

# Projekt klonen (ersetzen Sie die URL durch Ihre Repository-URL)
echo "📥 Cloning project..."
cd /home/ec2-user
git clone https://github.com/YOUR_USERNAME/data_assistant_project.git
cd data_assistant_project

# Environment Variables setzen
echo "🔐 Setting up environment variables..."
cat > .env << EOF
ENVIRONMENT=production
ANTHROPIC_API_KEY=your_api_key_here
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
EOF

# Docker Container starten
echo "🐳 Starting Docker containers..."
docker-compose up -d --build

# Status prüfen
echo "✅ Checking deployment status..."
sleep 10
docker-compose ps
docker-compose logs streamlit-app

echo "🎉 Deployment completed!"
echo "🌐 Your app should be available at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8501"
echo "📊 Check logs with: docker-compose logs -f streamlit-app"
