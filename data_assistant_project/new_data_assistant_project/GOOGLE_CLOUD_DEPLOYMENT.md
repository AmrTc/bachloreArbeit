# Google Cloud Deployment Guide

Dieser Guide erklärt, wie Sie die Data Assistant Anwendung sicher auf Google Cloud deployen können.

## 🚀 Schnellstart

### 1. Voraussetzungen

- Google Cloud Projekt erstellt
- gcloud CLI installiert und authentifiziert
- Billing aktiviert

### 2. Projekt-ID setzen

```bash
# Ersetzen Sie "your-project-id" mit Ihrer tatsächlichen Projekt-ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID
```

### 3. Secrets sicher einrichten

```bash
# Führen Sie das Setup-Skript aus
chmod +x setup_secrets.sh
./setup_secrets.sh
```

**Wichtig:** Geben Sie Ihren Anthropic API-Key ein, wenn Sie dazu aufgefordert werden.

### 4. Deployment

```bash
# Führen Sie das Deployment-Skript aus
chmod +x deploy.sh
./deploy.sh
```

## 🔐 Sichere Secrets-Verwaltung

### Option 1: Google Secret Manager (Empfohlen)

Der Anthropic API-Key wird sicher in Google Secret Manager gespeichert:

```bash
# Secret erstellen
echo "your-api-key" | gcloud secrets create anthropic-api-key --data-file=-

# Secret in der Anwendung verwenden
gcloud secrets versions access latest --secret=anthropic-api-key
```

### Option 2: Umgebungsvariablen (Nur für Entwicklung)

```bash
# Lokale Entwicklung
export ANTHROPIC_API_KEY="your-api-key"
streamlit run streamlit_entry.py
```

## 🐳 Docker & Cloud Build

### Manueller Build

```bash
# Docker Image bauen
docker build -t gcr.io/$PROJECT_ID/data-assistant .

# Image pushen
docker push gcr.io/$PROJECT_ID/data-assistant
```

### Automatischer Build mit Cloud Build

```bash
# Mit Cloud Build bauen
gcloud builds submit --config cloudbuild.yaml

# Mit Secrets (empfohlen)
gcloud builds submit --config cloudbuild.secrets.yaml
```

## 🌐 Cloud Run Deployment

### Automatisches Deployment

Das `deploy.sh` Skript:
- Baut das Docker Image
- Deployed auf Cloud Run
- Konfiguriert die notwendigen Umgebungsvariablen
- Setzt die richtigen Ressourcenlimits

### Manuelles Deployment

```bash
gcloud run deploy data-assistant \
    --image gcr.io/$PROJECT_ID/data-assistant \
    --platform managed \
    --region europe-west1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 10
```

## 🔧 Konfiguration

### Umgebungsvariablen

- `STREAMLIT_SERVER_PORT`: 8080
- `STREAMLIT_SERVER_ADDRESS`: 0.0.0.0
- `ANTHROPIC_API_KEY`: Aus Secret Manager

### Ressourcenlimits

- **Memory**: 2Gi
- **CPU**: 1 vCPU
- **Max Instances**: 10
- **Port**: 8080

## 📁 Dateistruktur

```
new_data_assistant_project/
├── Dockerfile                 # Standard Docker Image
├── Dockerfile.secrets        # Docker Image mit Secret Manager
├── cloudbuild.yaml           # Standard Cloud Build
├── cloudbuild.secrets.yaml   # Cloud Build mit Secrets
├── .dockerignore            # Docker Build Optimierung
├── deploy.sh                # Deployment-Skript
├── setup_secrets.sh         # Secret Manager Setup
└── GOOGLE_CLOUD_DEPLOYMENT.md # Diese Anleitung
```

## 🚨 Sicherheitshinweise

1. **Nie API-Keys in den Code committen**
2. **Verwenden Sie Secret Manager für Produktionsumgebungen**
3. **Setzen Sie die richtigen IAM-Berechtigungen**
4. **Überwachen Sie die API-Nutzung**

## 🔍 Troubleshooting

### Häufige Probleme

1. **Permission Denied**: IAM-Berechtigungen prüfen
2. **Build Failed**: Dockerfile und .dockerignore überprüfen
3. **Secret Access Error**: Secret Manager Berechtigungen prüfen

### Logs anzeigen

```bash
# Cloud Build Logs
gcloud builds log [BUILD_ID]

# Cloud Run Logs
gcloud logs read --service=data-assistant --limit=50
```

## 📞 Support

Bei Problemen:
1. Google Cloud Console Logs prüfen
2. gcloud CLI Debug-Ausgaben aktivieren
3. Docker Image lokal testen

---

**Wichtig**: Ersetzen Sie immer `your-project-id` mit Ihrer tatsächlichen Google Cloud Projekt-ID!
