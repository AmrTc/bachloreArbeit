# Multi-stage Dockerfile für Data Assistant Project
FROM python:3.12-slim as builder

# System-Dependencies installieren
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis setzen
WORKDIR /app

# Python Dependencies kopieren und installieren
COPY requirements-production.txt requirements.txt

# setup.py direkt erstellen (umgeht Build-Context-Problem)
RUN echo 'from setuptools import setup, find_packages\n\
setup(\n\
    name="new_data_assistant_project",\n\
    version="0.1.0",\n\
    packages=find_packages(include=["new_data_assistant_project", "new_data_assistant_project.*"]),\n\
    install_requires=[\n\
        "anthropic",\n\
        "pandas",\n\
        "numpy",\n\
        "streamlit",\n\
    ],\n\
    python_requires=">=3.8",\n\
)' > setup.py

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e .

# Production Image
FROM python:3.12-slim

# System-Dependencies für Runtime
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root User erstellen
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Verzeichnisse erstellen
RUN mkdir -p /app /home/appuser/.streamlit && \
    chown -R appuser:appuser /app /home/appuser

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Python Dependencies von Builder kopieren
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Anwendung kopieren
COPY .. .

# setup.py direkt erstellen (umgeht Build-Context-Problem)
RUN echo 'from setuptools import setup, find_packages\n\
setup(\n\
    name="new_data_assistant_project",\n\
    version="0.1.0",\n\
    packages=find_packages(include=["new_data_assistant_project", "new_data_assistant_project.*"]),\n\
    install_requires=[\n\
        "anthropic",\n\
        "pandas",\n\
        "numpy",\n\
    ],\n\
    python_requires=">=3.8",\n\
)' > setup.py

# Projekt im finalen Image installieren
RUN pip install --no-cache-dir -e .

# Setup-Script erstellen für PYTHONPATH
RUN echo '#!/bin/bash\nexport PYTHONPATH=/app:$PYTHONPATH\ncd /app\nexec "$@"' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Streamlit Konfiguration
RUN mkdir -p /home/appuser/.streamlit && \
    echo '[server]\nheadless = true\nport = 8501\naddress = "0.0.0.0"\n[browser]\ngatherUsageStats = false\n[theme]\nbase = "light"' > /home/appuser/.streamlit/config.toml

# Berechtigungen setzen
RUN chown -R appuser:appuser /app /home/appuser && \
    mkdir -p /app/src/database && \
    chown -R appuser:appuser /app/src/database

# Auf non-root User wechseln
USER appuser

# Umgebungsvariablen
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV HOME=/home/appuser

# Port exponieren
EXPOSE 8501

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Startkommando mit entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["streamlit", "run", "frontend/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
