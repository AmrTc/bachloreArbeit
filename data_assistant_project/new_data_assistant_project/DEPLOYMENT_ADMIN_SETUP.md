# 🚀 Deployment mit Admin-User Setup

## 📋 Übersicht

Dieses Dokument erklärt, wie sichergestellt wird, dass beim Deployment automatisch ein Admin-User mit den korrekten Credentials angelegt wird.

## 🔑 Admin-Credentials

**Nach dem Deployment:**
- **Username:** `admin`
- **Password:** `Nu4attNrF6Bcp5v`
- **Role:** `admin`

## 🛠️ Automatische Admin-User-Erstellung

### Option 1: Deployment-Skript ausführen

```bash
# Im Projektverzeichnis
python deploy_with_admin.py
```

**Was passiert:**
1. ✅ Testet die PostgreSQL-Verbindung
2. ✅ Prüft, ob Admin-User bereits existiert
3. ✅ Erstellt Admin-User falls nicht vorhanden
4. ✅ Aktualisiert Admin-Passwort falls nötig
5. ✅ Zeigt Deployment-Status an

### Option 2: Migration-Skript ausführen

```bash
# Im Projektverzeichnis
python src/database/migrate_to_postgres.py
```

**Was passiert:**
1. ✅ Erstellt alle Datenbanktabellen
2. ✅ Legt Admin-User mit neuem Passwort an
3. ✅ Migriert bestehende Daten (falls vorhanden)

## 🔧 Manuelle Admin-User-Erstellung (Cloud Terminal)

Falls du den Admin-User manuell im Cloud Terminal erstellen möchtest:

```bash
# Verbindung zur PostgreSQL-Datenbank
psql -h 34.59.248.159 -U postgres -d superstore

# Admin-User erstellen
INSERT INTO users (
    username, password_hash, role, created_at, has_completed_assessment,
    sql_expertise_level, cognitive_load_capacity,
    sql_expertise, data_analysis_fundamentals, business_analytics,
    forecasting_statistics, data_visualization, domain_knowledge_retail,
    total_assessment_score, user_level_category, age, gender,
    profession, education_level, study_training
) VALUES (
    'admin', 
    'SHA256_HASH_VON_Nu4attNrF6Bcp5v', 
    'admin', 
    NOW(), 
    true,
    5, 5, 5, 5, 5, 5, 5, 30, 'Expert', 30, 'Not specified', 
    'System Administrator', 'PhD', 'Computer Science'
);
```

## 📊 Überprüfung des Admin-Users

```bash
# Im Projektverzeichnis
python -c "
from src.database.postgres_config import PostgresConfig
from src.database.postgres_models import User
import psycopg2

config = PostgresConfig()
db_config = config.get_connection_params()

conn = psycopg2.connect(**db_config)
cursor = conn.cursor()

cursor.execute('SELECT username, role, sql_expertise_level, user_level_category FROM users WHERE username = \"admin\"')
admin = cursor.fetchone()

if admin:
    print(f'✅ Admin user found: {admin[0]} ({admin[1]}) - Level: {admin[3]}')
else:
    print('❌ Admin user not found')

cursor.close()
conn.close()
"
```

## 🚨 Wichtige Hinweise

1. **Passwort-Sicherheit:** Das Admin-Passwort ist in den Skripten hardcodiert - für Produktionsumgebungen sollten Umgebungsvariablen verwendet werden.

2. **Automatische Ausführung:** Das `deploy_with_admin.py` Skript kann in CI/CD-Pipelines integriert werden.

3. **Bestehende User:** Falls bereits ein Admin-User existiert, wird nur das Passwort aktualisiert.

4. **Datenbankverbindung:** Alle Skripte verwenden die Konfiguration aus `src/database/postgres_config.py`.

## 🔍 Troubleshooting

### Admin-User existiert nicht
```bash
python deploy_with_admin.py
```

### Datenbankverbindung fehlschlägt
```bash
# Teste Verbindung
python -c "
from src.database.postgres_config import PostgresConfig
import psycopg2

config = PostgresConfig()
print('Testing connection...')
conn = psycopg2.connect(**config.get_connection_params())
print('✅ Connection successful!')
conn.close()
"
```

### Fehlende Abhängigkeiten
```bash
pip install psycopg2-binary
```

## 📝 Logs überprüfen

Alle Skripte loggen detaillierte Informationen. Suche nach:
- `✅ Admin user created successfully`
- `✅ Admin password updated to: Nu4attNrF6Bcp5v`
- `✅ Deployment completed successfully`

## 🎯 Erfolgsindikatoren

- ✅ Admin-User existiert in der Datenbank
- ✅ Login mit `admin` / `Nu4attNrF6Bcp5v` funktioniert
- ✅ Admin-Rolle ist korrekt gesetzt
- ✅ Alle Expertise-Level sind auf Maximum gesetzt
