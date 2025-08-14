# EC2 Deployment Guide (Option A)

Empfohlen für deinen aktuellen Stand (SQLite, Docker Compose).

## 1) EC2 Instanz erstellen
- AMI: Amazon Linux 2023
- Typ: t3.small (min. t3.micro möglich)
- Security Group (eingehend):
  - SSH: TCP 22 von deiner IP
  - HTTP: TCP 80 (für Nginx)
  - Optional: HTTPS TCP 443
  - Optional (Schnellstart ohne Nginx): TCP 8501

## 2) Verbindung herstellen
```bash
ssh -i /path/to/key.pem ec2-user@EC2_PUBLIC_IP
```

## 3) Docker & Compose installieren und App starten
Variante A: Mit Repo (REPO_URL setzen)
```bash
# als ec2-user
cd ~
REPO_URL=https://github.com/<owner>/<repo>.git \
REPO_BRANCH=main \
APP_DIR=/opt/data_assistant \
bash -c "$(cat new_data_assistant_project/deployment/ec2-setup.sh)"
```

Variante B: Manuell
```bash
sudo dnf update -y
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user

# Docker Compose v2 (CLI Plugin) installieren – Fallback, falls Paket fehlt
cd /opt
sudo mkdir -p /opt/tools
sudo chown -R ec2-user:ec2-user /opt/tools
cd /opt/tools
curl -fsSL -O https://raw.githubusercontent.com/<owner>/<repo>/main/new_data_assistant_project/deployment/install-docker-compose.sh
bash install-docker-compose.sh

# Projektverzeichnis
sudo mkdir -p /opt/data_assistant
sudo chown -R ec2-user:ec2-user /opt/data_assistant
cd /opt/data_assistant

# Projekt bereitstellen (git clone oder per scp hochladen)
# git clone https://github.com/<owner>/<repo>.git repo
# cd repo/new_data_assistant_project/deployment

# Start
docker compose build
docker compose up -d
```

## 4) Test
```bash
curl -f http://localhost:8501/_stcore/health
# oder via Browser: http://EC2_PUBLIC_IP:8501 (ohne Nginx)
```

## 5) Optional: Nginx (Port 80) als Reverse Proxy
Variante A: Host Nginx
```bash
cd /opt/data_assistant/repo/new_data_assistant_project/deployment
sudo bash nginx/setup-nginx.sh
# Browser: http://EC2_PUBLIC_IP
```

Variante B: Nginx in Docker
```bash
cd /opt/data_assistant/repo/new_data_assistant_project/deployment
docker compose -f docker-compose.with-nginx.yml up -d --build
# Browser: http://EC2_PUBLIC_IP
```

## 6) Optional: HTTPS (Let's Encrypt)
```bash
sudo dnf install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your.domain.example
```

## Updates
```bash
# in deployment/
docker compose pull || true
docker compose build
docker compose up -d
```

## Logs & Status
```bash
docker compose ps
docker compose logs -f
```

Hinweise:
- Achte auf Security Group Regeln in AWS (eingehend 80/443/8501 nach Bedarf)
- Für Persistenz liegt die SQLite-DB im Host-Bind-Mount (`/app/src/database`)
- Für Domains/HTTPS am besten eine feste Elastic IP + Route53 Eintrag verwenden
