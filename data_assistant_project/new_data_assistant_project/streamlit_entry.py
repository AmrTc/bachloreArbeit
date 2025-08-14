import os
import sys

# Ensure project root is on sys.path so absolute imports resolve
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from new_data_assistant_project.frontend.app import main  # type: ignore
except Exception as exc:
    # Fallback: try relative import when package prefix is unavailable
    try:
        from frontend.app import main  # type: ignore
    except Exception as inner_exc:
        raise RuntimeError(
            f"Could not import frontend.app: {exc} / {inner_exc}\n"
            f"CWD={os.getcwd()} ROOT={PROJECT_ROOT}"
        ) from inner_exc

if __name__ == "__main__":
    # Delegate to real app entry
    main()
