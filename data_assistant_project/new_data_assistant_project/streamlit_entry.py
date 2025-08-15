import os
import sys
from pathlib import Path

# Get the directory where this file is located in the project root
CURRENT_DIR = Path(__file__).parent.absolute()

# Add the current directory to Python path for relative imports
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

# Debug output für Streamlit Cloud
print(f"Current directory: {CURRENT_DIR}")
print(f"Working directory: {os.getcwd()}")
print(f"Directory contents: {list(CURRENT_DIR.iterdir())}")

try:
    # Import based on your actual structure
    # Annahme: Sie haben eine app.py direkt im Hauptverzeichnis
    # oder in src/
    
    # Option 1: Wenn app.py im Hauptverzeichnis ist
    from app import main
    
    # Option 2: Wenn app.py in src/ ist
    # from src.app import main
    
    # Option 3: Wenn Sie eine andere Hauptdatei haben
    # from src.streamlit_app import main
    
except ImportError as exc:
    # Detaillierte Fehlerdiagnose
    src_dir = CURRENT_DIR / 'src'
    raise RuntimeError(
        f"Could not import app from {CURRENT_DIR}\n"
        f"Current working directory: {os.getcwd()}\n"
        f"Python path: {sys.path[:3]}...\n"
        f"Available files in current dir: {list(CURRENT_DIR.iterdir())}\n"
        f"Src dir exists: {src_dir.exists()}\n"
        f"Files in src: {list(src_dir.iterdir()) if src_dir.exists() else 'N/A'}"
    ) from exc

if __name__ == "__main__":
    main()