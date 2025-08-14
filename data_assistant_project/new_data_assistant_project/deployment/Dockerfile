# Production Dockerfile für Data Assistant Project
FROM python:3.11-slim

# System-Pakete aktualisieren und notwendige Tools installieren
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis setzen
WORKDIR /app

# Python-Dependencies installieren (Quelle liegt unter deployment/, Build-Kontext ist Projek root)
COPY deployment/requirements-production.txt ./requirements-production.txt
RUN pip install --no-cache-dir -r requirements-production.txt

# Anwendungscode kopieren (alle relevanten Verzeichnisse)
COPY frontend/ ./frontend/
COPY src/ ./src/
COPY data/ ./data/
COPY evaluation/ ./evaluation/
COPY __init__.py .

# Streamlit-Config kopieren
COPY .streamlit/ ./.streamlit/

# Benutzer erstellen (nicht als root laufen)
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /home/appuser

# Zu nicht-root Benutzer wechseln
USER appuser

# Port exponieren
EXPOSE 8501

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Streamlit starten
CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
