"""
Data Assistant Project - Global Import Configuration
==================================================

This module ensures proper import paths for both local development and Docker deployment.
It automatically configures PYTHONPATH and handles import fallbacks.
"""

import os
import sys
from pathlib import Path

def setup_imports():
    """Setup proper import paths for the project."""
    
    # Get the project root (where this __init__.py is located)
    project_root = Path(__file__).parent.resolve()
    
    # Add project root to Python path if not already there
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Also add the parent directory (for absolute imports like new_data_assistant_project.src...)
    parent_dir = project_root.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    # Set PYTHONPATH environment variable
    current_pythonpath = os.environ.get('PYTHONPATH', '')
    new_paths = [str(project_root), str(parent_dir)]
    
    for path in new_paths:
        if path not in current_pythonpath:
            if current_pythonpath:
                current_pythonpath = f"{path}:{current_pythonpath}"
            else:
                current_pythonpath = path
    
    os.environ['PYTHONPATH'] = current_pythonpath
    
    # Set working directory to project root
    if os.getcwd() != str(project_root):
        os.chdir(project_root)
    
    return project_root

# Automatically setup imports when this module is imported
PROJECT_ROOT = setup_imports()

# Make common imports available at package level
try:
    # Try to import common modules to verify setup worked
    from new_data_assistant_project.src.utils.auth_manager import AuthManager
    from new_data_assistant_project.src.utils.chat_manager import ChatManager
    from new_data_assistant_project.src.database.schema import create_tables, create_admin_user
    
    print("✅ Global imports configured successfully")
    
except ImportError as e:
    print(f"⚠️ Warning: Could not configure global imports: {e}")
    print(f"📂 Project root: {PROJECT_ROOT}")
    print(f"🐍 Python path: {sys.path[:3]}...")

__version__ = "1.0.0"
__all__ = ['PROJECT_ROOT', 'setup_imports'] 