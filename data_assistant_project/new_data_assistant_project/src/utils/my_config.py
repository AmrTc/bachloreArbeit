"""
Configuration utilities for the Data Assistant project.
"""

import os
from pathlib import Path

# Docker-compatible imports
try:
    from new_data_assistant_project.src.utils.secrets_path_utils import SecretsPathUtils
except ImportError:
    from src.utils.secrets_path_utils import SecretsPathUtils

class MyConfig:
    """Configuration manager for the data assistant project."""
    
    def __init__(self):
        """Initialize configuration.

        Priority order for API key:
        1. Streamlit Cloud secrets (production)
        2. Local .streamlit/secrets.toml (development)
        """

        api_key = None
        
        # Try Streamlit Cloud secrets first
        try:
            import streamlit as st  # type: ignore

            if "ANTHROPIC_API_KEY" in st.secrets:
                api_key = str(st.secrets["ANTHROPIC_API_KEY"])  # flat key
            elif "anthropic_api_key" in st.secrets:
                api_key = str(st.secrets["anthropic_api_key"])  # alt flat key
            elif "anthropic" in st.secrets and "api_key" in st.secrets["anthropic"]:
                api_key = str(st.secrets["anthropic"]["api_key"])  # sectioned
        except Exception:
            # Streamlit not available → try local secrets.toml
            pass
        
        # If no API key from Streamlit, try local secrets.toml
        if not api_key:
            try:
                import toml
                secrets_path = Path(__file__).parent.parent.parent / ".streamlit" / "secrets.toml"
                
                if secrets_path.exists():
                    with open(secrets_path, "r") as f:
                        secrets = toml.load(f)
                    
                    if "ANTHROPIC_API_KEY" in secrets:
                        api_key = str(secrets["ANTHROPIC_API_KEY"])
                    elif "anthropic" in secrets and "api_key" in secrets["anthropic"]:
                        api_key = str(secrets["anthropic"]["api_key"])
            except Exception:
                # Local secrets not available
                pass

        # Store
        self.api_key = api_key
        self.database_path = os.getenv("DATABASE_PATH", "src/database/superstore.db")
        
    def get_api_key(self) -> str:
        """Get the Anthropic API key."""
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not configured.\n"
                "Set it in one of these locations:\n"
                "1. Streamlit Cloud secrets (production)\n"
                "2. .streamlit/secrets.toml (local development)\n"
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
        
        # Test local secrets.toml
        secrets_path = Path(__file__).parent.parent.parent / ".streamlit" / "secrets.toml"
        print("\nLocal Secrets Test:")
        print(f"secrets.toml location: {secrets_path}")
        print(f"secrets.toml exists: {'Yes' if secrets_path.exists() else 'No'}")
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")