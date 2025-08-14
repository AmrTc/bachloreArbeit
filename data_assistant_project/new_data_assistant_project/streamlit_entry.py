import os
import sys
import subprocess

# Ensure project root is on sys.path so absolute imports resolve
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def ensure_dependencies() -> None:
    """Install required runtime deps if they are missing.

    Note: In managed environments (e.g., Streamlit Cloud), dependencies should be installed via requirements.txt. This function serves as a fallback for local runs.
    """
    missing = []
    for pkg in ("anthropic", "pandas", "numpy", "sqlalchemy", "plotly", "dataclasses_json", "typing_extensions"):
        try:
            __import__(pkg)
        except Exception:
            missing.append(pkg)

    if not missing:
        return

    # Bevorzugt die produktiven Requirements des Projekts installieren
    req_path = os.path.join(PROJECT_ROOT, "deployment", "requirements-production.txt")
    args = [sys.executable, "-m", "pip", "install", "--no-cache-dir"]
    if os.path.isfile(req_path):
        args += ["-r", req_path]
    else:
        args += missing

    try:
        subprocess.check_call(args)
    except Exception as exc:
        raise RuntimeError(f"Failed to install dependencies: {' '.join(args)} -> {exc}") from exc


# Try to ensure deps before importing the app
ensure_dependencies()

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
