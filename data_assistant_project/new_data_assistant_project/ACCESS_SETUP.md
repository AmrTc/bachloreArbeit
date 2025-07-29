# 🔐 Access & Password Setup Guide

## Übersicht

Hier erfahren Sie, wo und wie Sie alle Access-Daten und Passwörter für Ihr VM-Setup konfigurieren können.

## 🚀 Einfache Konfiguration (Empfohlen)

### Automatisches Setup-Skript verwenden:

```bash
cd new_data_assistant_project/deployment
./configure-access.sh
```

Das Skript führt Sie durch die Konfiguration aller benötigten Access-Daten:
- ✅ SSH-Verbindung zur VM
- ✅ Admin-Benutzer der Anwendung  
- ✅ API-Schlüssel
- ✅ Sicherheitseinstellungen
- ✅ SSL-Konfiguration (optional)
- ✅ Monitoring-Zugänge (optional)

## 📋 Konfigurationsstellen im Detail

### 1. **SSH-Zugang zur VM**

```bash
# In den Deployment-Skripten oder manuell:
VM_HOST="192.168.1.100"        # Ihre VM IP-Adresse
VM_USER="ubuntu"               # SSH-Benutzername
VM_SSH_KEY="~/.ssh/my-key.pem" # SSH-Key (optional)
VM_PORT="22"                   # SSH-Port
```

**Verwendung:**
```bash
ssh $VM_USER@$VM_HOST
# oder mit Key:
ssh -i $VM_SSH_KEY $VM_USER@$VM_HOST
```

### 2. **Anwendungs-Admin-Benutzer**

```bash
# Standard-Anmeldedaten (ÄNDERN!)
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin123"      # ⚠️ WICHTIG: Starkes Passwort verwenden!
ADMIN_EMAIL="admin@example.com"
```

**Wo konfiguriert:**
- `new_data_assistant_project/.env`
- `deployment/vm-config.sh`

### 3. **API-Schlüssel**

```bash
# Erforderlich für KI-Funktionalität
ANTHROPIC_API_KEY="sk-ant-..."  # Ihr Anthropic API-Schlüssel
OPENAI_API_KEY="sk-..."         # Optional: OpenAI API-Schlüssel
```

**Wo konfiguriert:**
- `new_data_assistant_project/.env`

### 4. **Sicherheitseinstellungen**

```bash
SECRET_KEY="abc123..."          # Automatisch generiert
SESSION_TIMEOUT="3600"          # Session-Timeout in Sekunden
MAX_LOGIN_ATTEMPTS="5"          # Max. Anmeldeversuche
```

### 5. **SSL/HTTPS (Optional)**

```bash
SSL_ENABLED="true"              # HTTPS aktivieren
DOMAIN_NAME="your-domain.com"   # Ihre Domain
SSL_CERT_PATH="/path/to/cert"   # SSL-Zertifikat
SSL_KEY_PATH="/path/to/key"     # SSL-Schlüssel
```

## 🛠️ Manuelle Konfiguration

### Option 1: Template verwenden

```bash
# 1. Template kopieren
cp deployment/vm-config.template deployment/vm-config.sh

# 2. Bearbeiten
nano deployment/vm-config.sh

# 3. Konfiguration laden
source deployment/vm-config.sh
```

### Option 2: .env Datei direkt bearbeiten

```bash
# .env Datei erstellen/bearbeiten
nano new_data_assistant_project/.env
```

**Beispiel .env:**
```env
# API-Schlüssel
ANTHROPIC_API_KEY=your_actual_api_key_here

# Admin-Benutzer
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password_here
ADMIN_EMAIL=admin@your-domain.com

# Sicherheit
SECRET_KEY=automatically_generated_secret_key
SESSION_TIMEOUT=3600
MAX_LOGIN_ATTEMPTS=5

# Streamlit
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Anwendung
DEBUG=False
DATABASE_URL=sqlite:///src/database/superstore.db
```

## 🎯 Konfiguration für verschiedene Deployment-Methoden

### Direkte Installation

1. **SSH-Verbindung konfigurieren:**
   ```bash
   VM_HOST="your-vm-ip"
   VM_USER="ubuntu"
   ```

2. **Projekt auf VM übertragen:**
   ```bash
   scp -r new_data_assistant_project/ $VM_USER@$VM_HOST:/opt/
   ```

3. **Auf VM deployment ausführen:**
   ```bash
   ssh $VM_USER@$VM_HOST
   cd /opt/new_data_assistant_project/deployment
   ./deploy.sh
   ```

### Docker Container

1. **Docker-Umgebung konfigurieren:**
   ```bash
   # Lokale .env wird in Container verwendet
   nano new_data_assistant_project/.env
   ```

2. **Container-Deployment:**
   ```bash
   cd new_data_assistant_project/deployment
   ./docker-deploy.sh deploy
   ```

## 🔒 Sicherheits-Checkliste

### ✅ Vor dem Deployment:

- [ ] **Starkes Admin-Passwort** festgelegt (nicht "admin123"!)
- [ ] **API-Schlüssel** konfiguriert
- [ ] **SSH-Key** für VM-Zugang erstellt
- [ ] **.env und vm-config.sh** NICHT in Git eingecheckt
- [ ] **Firewall-Regeln** überprüft

### ✅ Nach dem Deployment:

- [ ] **Admin-Passwort ändern** bei erster Anmeldung
- [ ] **SSH-Passwort-Login deaktivieren** (nur Keys verwenden)
- [ ] **SSL/HTTPS aktivieren** für Produktion
- [ ] **Backups konfigurieren**
- [ ] **Monitoring einrichten**

## 🆘 Häufige Probleme

### Problem: "SSH Connection refused"
```bash
# Lösung: Port und Benutzer überprüfen
ssh -p 22 ubuntu@your-vm-ip
# oder anderen Benutzer versuchen:
ssh -p 22 root@your-vm-ip
```

### Problem: "API Key invalid"
```bash
# Lösung: API-Schlüssel in .env überprüfen
cat new_data_assistant_project/.env | grep ANTHROPIC_API_KEY
```

### Problem: "Admin login fails"
```bash
# Lösung: Admin-Passwort in .env überprüfen
cat new_data_assistant_project/.env | grep ADMIN_PASSWORD
```

### Problem: "Permission denied"
```bash
# Lösung: Dateiberechtigungen setzen
chmod 600 new_data_assistant_project/.env
chmod 600 deployment/vm-config.sh
```

## 📞 Zugriff nach Setup

Nach erfolgreichem Deployment erreichen Sie die Anwendung unter:

- **HTTP**: `http://your-vm-ip:8501`
- **HTTPS**: `https://your-domain.com` (mit SSL)
- **Admin-Login**: Mit konfigurierten Admin-Credentials

## 🔄 Passwörter ändern

### Admin-Passwort ändern:
1. In Anwendung einloggen
2. Benutzereinstellungen aufrufen
3. Neues Passwort setzen

### VM-SSH-Passwort ändern:
```bash
ssh $VM_USER@$VM_HOST
passwd  # Neues Passwort setzen
```

### API-Schlüssel aktualisieren:
```bash
# .env Datei bearbeiten
nano new_data_assistant_project/.env
# Service neustarten
sudo systemctl restart data-assistant
```

---

💡 **Tipp**: Verwenden Sie das automatische Setup-Skript `./configure-access.sh` für die einfachste Konfiguration! 