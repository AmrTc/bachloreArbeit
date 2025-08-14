import os
import sys
from pathlib import Path

# Get the directory where this file is located
CURRENT_DIR = Path(__file__).parent.absolute()

# Add the current directory to Python path for relative imports
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

# Dependencies are installed from requirements.txt at the repo root in Streamlit Cloud.
# Avoid runtime installation attempts here.

try:
    # Simple relative import - most reliable for Streamlit Cloud
    from frontend.app import main
except ImportError as exc:
    # If relative import fails, provide clear error message
    raise RuntimeError(
        f"Could not import frontend.app from {CURRENT_DIR}\n"
        f"Current working directory: {os.getcwd()}\n"
        f"Python path: {sys.path[:3]}...\n"
        f"Available files in current dir: {list(CURRENT_DIR.iterdir())}\n"
        f"Frontend dir exists: {(CURRENT_DIR / 'frontend').exists()}\n"
        f"App.py exists: {(CURRENT_DIR / 'frontend' / 'app.py').exists()}"
    ) from exc


if __name__ == "__main__":
    # Delegate to real app entry
    main()
