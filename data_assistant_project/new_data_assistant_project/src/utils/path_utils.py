import os
from pathlib import Path

def get_project_root() -> Path:
    """Get the absolute path to the project root directory."""
    current_file = Path(__file__).resolve()
    # Go up 3 levels: utils -> src -> data_assistant_project
    project_root = current_file.parent.parent.parent
    return project_root

def get_relative_path(path: str) -> str:
    """Convert absolute path to relative path from project root."""
    abs_path = Path(path).resolve()
    project_root = get_project_root()
    return str(abs_path.relative_to(project_root))

def get_absolute_path(relative_path: str) -> str:
    """Convert relative path to absolute path from project root."""
    project_root = get_project_root()
    return str(project_root / relative_path) 