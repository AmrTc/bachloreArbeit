# Streamlit Cloud Setup Guide

## 🚨 WICHTIG: Main File Path korrekt setzen

Das Pfadproblem tritt auf, wenn der "Main file path" in Streamlit Cloud falsch konfiguriert ist.

### ✅ Korrekte Konfiguration:

**Main file path:** `new_data_assistant_project/streamlit_entry.py`

**NICHT:** `new_data_assistant_project/new_data_assistant_project/streamlit_entry.py`
**NICHT:** `new_data_assistant_project/data_assistant_project/new_data_assistant_project/frontend/app.py`

### 🔍 Warum passiert der Fehler?

Streamlit Cloud startet von der Repository-Root und fügt den "Main file path" hinzu. Wenn der Pfad doppelt ist, entsteht:

```
/workspaces/bachloreArbeit/data_assistant_project/  ← Repository Root
└── new_data_assistant_project/                    ← Main file path
    └── streamlit_entry.py                         ← Entry point
```

**Falsch:** `new_data_assistant_project/new_data_assistant_project/streamlit_entry.py`
**Richtig:** `new_data_assistant_project/streamlit_entry.py`

### 📋 Streamlit Cloud Einstellungen:

1. **Repository:** `https://github.com/AmrTc/bachloreArbeit`
2. **Branch:** `main`
3. **Main file path:** `new_data_assistant_project/streamlit_entry.py`
4. **Python version:** 3.12
5. **Requirements file:** `requirements.txt` (Repository Root)

### 🔧 Troubleshooting:

**Falls der Fehler weiterhin auftritt:**

1. **Überprüfe den Main file path** - er sollte exakt `new_data_assistant_project/streamlit_entry.py` sein
2. **Lösche die App** und erstelle sie neu
3. **Warte auf den nächsten Deploy** nach dem Push der Änderungen

### 📁 Verzeichnisstruktur:

```
data_assistant_project/                    ← Repository Root
├── requirements.txt                       ← Dependencies
├── new_data_assistant_project/           ← App Directory
│   ├── streamlit_entry.py               ← Main Entry Point
│   ├── frontend/
│   │   └── app.py                       ← Streamlit App
│   └── src/
│       └── utils/
│           └── my_config.py             ← Configuration
└── .streamlit/
    └── secrets.toml                     ← Local Secrets (nicht committed)
```

### 🚀 Nach dem Setup:

1. **Redeploy** die App in Streamlit Cloud
2. **Überprüfe die Logs** - sie sollten jetzt sauber sein
3. **Teste die App** - sie sollte ohne Pfadfehler starten
