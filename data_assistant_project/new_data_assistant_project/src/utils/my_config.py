"""
Configuration utilities for the Data Assistant project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Docker-compatible imports
try:
    from new_data_assistant_project.src.utils.secrets_path_utils import SecretsPathUtils
except ImportError:
    from src.utils.secrets_path_utils import SecretsPathUtils

class MyConfig:
    """Configuration manager for the data assistant project."""
    
    def __init__(self):
        """Initialize configuration.

        Order of precedence for ANTHROPIC_API_KEY:
        1) Streamlit secrets (recommended for Streamlit Cloud)
        2) Environment variable
        3) .env file (for local development)
        """

        # 1) Try Streamlit secrets if available
        api_key: Optional[str] = None
        try:
            import streamlit as st  # type: ignore

            # Support multiple layouts in secrets.toml
            if "ANTHROPIC_API_KEY" in st.secrets:
                api_key = str(st.secrets["ANTHROPIC_API_KEY"])  # flat key
            elif "anthropic_api_key" in st.secrets:
                api_key = str(st.secrets["anthropic_api_key"])  # alternative flat key
            elif "anthropic" in st.secrets and "api_key" in st.secrets["anthropic"]:
                api_key = str(st.secrets["anthropic"]["api_key"])  # sectioned layout

            if api_key:
                # Mirror into environment for downstream libs that read os.getenv
                os.environ.setdefault("ANTHROPIC_API_KEY", api_key)
        except Exception:
            # Streamlit not available or no secrets configured
            pass

        # 2) If not found yet, check environment (could be set by orchestrator)
        if not api_key:
            api_key = os.getenv("ANTHROPIC_API_KEY")

        # 3) Finally, try loading from .env for local development
        if not api_key:
            secrets_utils = SecretsPathUtils.get_instance()
            env_path = secrets_utils.get_env_file_path()
            if env_path.exists():
                load_dotenv(str(env_path))
                api_key = os.getenv("ANTHROPIC_API_KEY")

        # Store resolved values
        self.api_key = api_key
        self.database_path = os.getenv("DATABASE_PATH", "src/database/superstore.db")
        
    def get_api_key(self) -> str:
        """Get the Anthropic API key."""
        if not self.api_key:
            env_path = SecretsPathUtils.get_instance().get_env_file_path()
            raise ValueError(
                "ANTHROPIC_API_KEY not configured.\n"
                "Set it via Streamlit secrets (preferred) or environment variables.\n"
                f"Checked .env file at: {env_path} (used only for local dev).\n"
                f"CWD: {Path.cwd()}"
            )
        return self.api_key
    
    def get_database_path(self) -> str:
        """Get the database path."""
        return self.database_path

if __name__ == "__main__":
    try:
        # Initialize configuration
        config = MyConfig()
        
        # Test API key loading
        api_key = config.get_api_key()
        print("\nAPI Key Test:")
        print(f"API Key loaded successfully: {'Yes' if api_key else 'No'}")
        print(f"API Key value: {api_key[:8]}..." if api_key else "No API key found")
        
        # Test database path
        db_path = config.get_database_path()
        print("\nDatabase Path Test:")
        print(f"Database path: {db_path}")
        
        # Test .env file location
        secrets_utils = SecretsPathUtils.get_instance()
        env_path = secrets_utils.get_env_file_path()
        
        print("\nEnvironment File Test:")
        print(f".env file location: {env_path}")
        print(f".env file exists: {'Yes' if env_path.exists() else 'No'}")
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")