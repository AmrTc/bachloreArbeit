# PostgreSQL Migration Guide

## Übersicht

Dieses Dokument beschreibt die Migration von SQLite zu PostgreSQL 17 für das Data Assistant Project. Die Migration ist notwendig, um die Anwendung in Google Cloud zu betreiben, da SQLite nicht für Produktionsumgebungen in der Cloud geeignet ist.

## 🗄️ Ihre PostgreSQL-Instanz

**Instanz-Informationen:**
- **Projekt-ID**: `impactful-study-469120`
- **Instanz-Name**: `superstore-instanz`
- **Verbindungsname**: `impactful-study-469120-m5:us-central1:superstore-instanz`
- **Region**: `us-central1`
- **Host**: `34.59.248.159`
- **Port**: `5432`
- **Benutzer**: `postgres`
- **Passwort**: `<zdG$DLpmG,~p3A`
- **Datenbank**: `data_assistant`

## 🚀 Schnellstart

### 1. Abhängigkeiten installieren

```bash
pip install psycopg2-binary python-dotenv
```

### 2. Verbindung testen

```bash
python test_postgres_connection.py
```

### 3. Migration ausführen

```bash
python migrate_to_postgres.py
```

## 📋 Migrationsschritte

### Schritt 1: Vorbereitung

Stellen Sie sicher, dass alle Abhängigkeiten installiert sind:

```bash
# Im Root-Verzeichnis
cd /Users/amrantchagnao/Desktop/thesis/bachloreArbeit

# Abhängigkeiten installieren
pip install -r requirements.txt
```

### Schritt 2: Verbindung testen

Testen Sie zuerst die Verbindung zu Ihrer PostgreSQL-Instanz:

```bash
python test_postgres_connection.py
```

### Schritt 3: Migration ausführen

Führen Sie das Hauptmigrationsskript aus:

```bash
python migrate_to_postgres.py
```

Das Skript wird:
- ✅ Die Verbindung zu Ihrer PostgreSQL-Instanz testen
- 📋 Alle notwendigen Tabellen erstellen
- 👤 Einen Admin-Benutzer anlegen
- 📊 Alle Daten aus SQLite migrieren
- 🔍 Den Migrationsstatus überwachen

## 🗂️ Datenbankstruktur

### Tabellen

1. **users** - Benutzerprofile und Assessment-Daten
2. **chat_sessions** - Chat-Verläufe
3. **explanation_feedback** - Feedback zu Erklärungen
4. **comprehensive_feedback** - Umfassendes Forschungs-Feedback
5. **superstore** - Geschäftsdaten für Analysen

### Indizes

Alle Tabellen haben optimierte Indizes für bessere Performance:
- Benutzer-ID-basierte Indizes
- Zeitstempel-Indizes
- Geschäftsdaten-Indizes (Region, Kategorie, etc.)

## 🔧 Konfiguration

### Environment-Variablen

Verwenden Sie die `env.postgres`-Datei:

```bash
# PostgreSQL Configuration
PG_HOST=34.59.248.159
PG_PORT=5432
PG_DATABASE=data_assistant
PG_USER=postgres
PG_PASSWORD=<zdG$DLpmG,~p3A
PG_SSLMODE=require
PG_CONNECT_TIMEOUT=30
PG_APP_NAME=data_assistant_app
```

### Anwendungskonfiguration

Aktualisieren Sie Ihre Anwendung, um PostgreSQL zu verwenden:

```python
from postgres_config import PostgresConfig
from postgres_schema import create_postgres_tables

# Konfiguration laden
config = PostgresConfig()
db_config = config.get_connection_params()

# Tabellen erstellen
create_postgres_tables(**db_config)
```

## 🐳 Docker-Entwicklung

Die Docker-Dateien wurden bereits für PostgreSQL angepasst:

- **Dockerfile**: Enthält `libpq-dev` für PostgreSQL-Unterstützung
- **Dockerfile.secrets**: Gleiche Anpassungen für Secret-Manager-Version

## 🔍 Troubleshooting

### Verbindungsfehler

**Fehler**: `connection refused`
**Lösung**: Prüfen Sie, ob die IP-Adresse korrekt ist und der Port 5432 geöffnet ist.

**Fehler**: `authentication failed`
**Lösung**: Überprüfen Sie Benutzername und Passwort.

**Fehler**: `SSL connection required`
**Lösung**: Stellen Sie sicher, dass `sslmode=require` gesetzt ist.

### Migrationsfehler

**Fehler**: `table already exists`
**Lösung**: Das ist normal - Tabellen werden nur erstellt, wenn sie nicht existieren.

**Fehler**: `duplicate key value`
**Lösung**: Verwenden Sie `ON CONFLICT DO NOTHING` für Duplikate.

## 📊 Performance-Optimierungen

### Verbindungspooling

Für Produktionsumgebungen empfehlen wir Verbindungspooling:

```python
import psycopg2.pool

# Verbindungspool erstellen
pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=20,
    **db_config
)

# Verbindung aus dem Pool holen
conn = pool.getconn()
# ... Verwendung ...
pool.putconn(conn)
```

### Indizes

Alle wichtigen Abfragefelder sind bereits indiziert:
- `users.username` (UNIQUE)
- `chat_sessions.user_id`
- `superstore.region`, `superstore.category`

## 🔐 Sicherheit

### SSL-Verbindung

Alle Verbindungen verwenden SSL (`sslmode=require`).

### Netzwerkzugriff

Die Instanz ist für alle IPs zugänglich (`0.0.0.0/0`). Für Produktion sollten Sie den Zugriff einschränken.

### Passwort-Management

Das Passwort ist in den Skripten hartcodiert. Für Produktion sollten Sie:
- Umgebungsvariablen verwenden
- Google Secret Manager nutzen
- Regelmäßig Passwörter rotieren

## 💰 Kosten

### Google Cloud SQL

- **Instanz-Typ**: `db-f1-micro` (kleinste Instanz)
- **Speicher**: 10GB SSD
- **Geschätzte monatliche Kosten**: $25-50 USD

### Kostenoptimierung

- Instanz stoppen, wenn nicht in Verwendung
- Automatische Skalierung aktivieren
- Backup-Strategien optimieren

## 📈 Monitoring

### Cloud SQL Insights

Überwachen Sie Ihre Instanz in der Google Cloud Console:
- CPU- und Speicherauslastung
- Verbindungsanzahl
- Query-Performance

### Logs

Aktivieren Sie PostgreSQL-Logs für Debugging:
- Slow Query Logs
- Connection Logs
- Error Logs

## 🔄 Rollback

Falls die Migration fehlschlägt, können Sie:

1. **SQLite-Datenbank behalten** - Die Migration überschreibt keine bestehenden Daten
2. **PostgreSQL-Tabellen löschen** - `DROP TABLE IF EXISTS table_name;`
3. **Neue Migration starten** - Das Skript ist idempotent

## 📞 Support

Bei Problemen:

1. **Logs prüfen** - Alle Migrationen werden geloggt
2. **Verbindung testen** - `test_postgres_connection.py`
3. **Google Cloud Console** - Instanz-Status prüfen
4. **Dokumentation** - PostgreSQL 17 offizielle Docs

## 🎯 Nächste Schritte

Nach erfolgreicher Migration:

1. ✅ **Anwendung testen** - Alle Funktionen mit PostgreSQL verifizieren
2. 🔄 **CI/CD aktualisieren** - Deployment-Pipelines anpassen
3. 📊 **Performance messen** - Vergleich mit SQLite
4. 🧪 **Backup-Strategie** - Regelmäßige Backups einrichten
5. 📈 **Monitoring** - Cloud SQL Insights aktivieren

## 📁 Verfügbare Skripte

- **`postgres_config.py`** - PostgreSQL-Konfigurationsmanager
- **`postgres_schema.py`** - Tabellenerstellung und Schema-Definitionen
- **`migrate_to_postgres.py`** - Hauptmigrationsskript
- **`test_postgres_connection.py`** - Verbindungstest
- **`env.postgres`** - Environment-Variablen
- **`requirements.txt`** - Aktualisiert mit PostgreSQL-Abhängigkeiten

---

**Viel Erfolg bei der Migration! 🚀**

Bei Fragen oder Problemen können Sie die Logs und die Google Cloud Console zur Fehlersuche verwenden.
