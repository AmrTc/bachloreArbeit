# 🚀 EC2 Deployment Guide für Data Assistant Project

## 📋 Voraussetzungen

- AWS Account
- EC2 Instance (t3.micro für Free Tier)
- Domain (optional, für SSL)
- GitHub Repository mit Ihrem Code

## 🔧 Schritt-für-Schritt Deployment

### **Schritt 1: EC2 Instance starten**

1. **AWS Console** → **EC2** → **Launch Instance**
2. **Instance Type**: `t3.micro` (Free Tier)
3. **AMI**: Amazon Linux 2 (x86)
4. **Storage**: 8 GB (Standard)
5. **Security Group**: Port 8501 öffnen
6. **Key Pair**: Erstellen oder bestehenden verwenden

### **Schritt 2: EC2 Instance verbinden**

```bash
# SSH-Verbindung (ersetzen Sie die IP)
ssh -i your-key.pem ec2-user@your-ec2-ip

# Oder über AWS Console: EC2 → Connect → EC2 Instance Connect
```

### **Schritt 3: Deployment Script ausführen**

```bash
# Script ausführbar machen
chmod +x deployment/ec2-deploy.sh

# Deployment starten
./deployment/ec2-deploy.sh
```

### **Schritt 4: Environment Variables setzen**

```bash
# .env Datei bearbeiten
nano .env

# API Key setzen
ANTHROPIC_API_KEY=your_actual_api_key_here
```

### **Schritt 5: Anwendung starten**

```bash
# Docker Container starten
docker-compose up -d --build

# Status prüfen
docker-compose ps
docker-compose logs streamlit-app
```

## 🌐 Zugriff auf die Anwendung

### **Direkter Zugriff:**
```
http://YOUR_EC2_PUBLIC_IP:8501
```

### **Public IP finden:**
```bash
# Auf der EC2 Instance
curl -s http://169.254.169.254/latest/meta-data/public-ipv4
```

## 🔒 Sicherheit konfigurieren

### **Security Group Einstellungen:**
- **Port 22 (SSH)**: Nur von Ihrer IP
- **Port 8501 (Streamlit)**: 0.0.0.0/0 (öffentlich)
- **Port 80/443**: Für Nginx (optional)

### **Firewall auf EC2:**
```bash
# Firewall Status prüfen
sudo systemctl status firewalld

# Port 8501 ist bereits durch das Script geöffnet
```

## 📊 Monitoring und Wartung

### **Logs anzeigen:**
```bash
# Streamlit Logs
docker-compose logs -f streamlit-app

# System Logs
sudo journalctl -u docker
```

### **Container neu starten:**
```bash
# Anwendung neu starten
docker-compose restart streamlit-app

# Komplett neu bauen
docker-compose down
docker-compose up -d --build
```

### **Updates deployen:**
```bash
# Code aktualisieren
git pull origin main

# Container neu bauen
docker-compose up -d --build
```

## 🚨 Troubleshooting

### **Port nicht erreichbar:**
```bash
# Port Status prüfen
sudo netstat -tlnp | grep 8501

# Firewall Status
sudo firewall-cmd --list-ports
```

### **Docker Probleme:**
```bash
# Docker Status
sudo systemctl status docker

# Docker neu starten
sudo systemctl restart docker
```

### **Container startet nicht:**
```bash
# Logs prüfen
docker-compose logs streamlit-app

# Container Status
docker-compose ps
```

## 💰 Kostenoptimierung

### **Free Tier (12 Monate):**
- **EC2 t3.micro**: 750h/Monat
- **EBS Storage**: 30 GB
- **Data Transfer**: 15 GB

### **Production (ab $15/Monat):**
- **EC2 t3.small**: $15/Monat
- **EBS Storage**: $1.20/GB/Monat
- **Data Transfer**: $0.09/GB

## 🔄 Automatisierung

### **GitHub Actions (optional):**
```yaml
# .github/workflows/deploy.yml
name: Deploy to EC2
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to EC2
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.KEY }}
          script: |
            cd data_assistant_project
            git pull origin main
            docker-compose up -d --build
```

## 📞 Support

Bei Problemen:
1. **Logs prüfen**: `docker-compose logs streamlit-app`
2. **Container Status**: `docker-compose ps`
3. **System Ressourcen**: `htop` oder `free -h`
4. **Network**: `curl localhost:8501`

## 🎯 Nächste Schritte

1. **Domain konfigurieren** (optional)
2. **SSL Certificate** (Let's Encrypt)
3. **Nginx Reverse Proxy** (optional)
4. **Monitoring** (CloudWatch)
5. **Backup-Strategie** implementieren
