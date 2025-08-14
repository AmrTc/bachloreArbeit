import os
import sys

# Ensure project root is on sys.path for absolute imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Delegate to the real app
from new_data_assistant_project.frontend.app import main  # type: ignore

if __name__ == "__main__":
    main()
