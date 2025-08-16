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
        1. Google Secret Manager (production - Cloud Run)
        2. Streamlit Cloud secrets (production - Streamlit Cloud)
        3. Local .streamlit/secrets.toml (development)
        """

        api_key = None
        
        # Try Google Secret Manager first (production - Cloud Run)
        try:
            api_key = self._get_secret_from_secret_manager()
            if api_key:
                print("✅ API Key loaded from Google Secret Manager")
        except Exception as e:
            print(f"⚠️ Google Secret Manager not available: {e}")
            # Continue to next method
        
        # If no API key from Secret Manager, try Streamlit Cloud secrets
        if not api_key:
            try:
                import streamlit as st  # type: ignore

                if "ANTHROPIC_API_KEY" in st.secrets:
                    api_key = str(st.secrets["ANTHROPIC_API_KEY"])  # flat key
                elif "anthropic_api_key" in st.secrets:
                    api_key = str(st.secrets["anthropic_api_key"])  # alt flat key
                elif "anthropic" in st.secrets and "api_key" in st.secrets["anthropic"]:
                    api_key = str(st.secrets["anthropic"]["api_key"])  # sectioned
                
                if api_key:
                    print("✅ API Key loaded from Streamlit Cloud secrets")
            except Exception:
                # Streamlit not available → try local secrets.toml
                pass
        
        # If no API key from Secret Manager or Streamlit, try local secrets.toml
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
                
                if api_key:
                    print("✅ API Key loaded from local secrets.toml")
            except Exception:
                # Local secrets not available
                pass

        # Store
        self.api_key = api_key
        self.database_path = os.getenv("DATABASE_PATH", "src/database/superstore.db")
        
    def _get_secret_from_secret_manager(self) -> str:
        """
        Get the Anthropic API key from Google Secret Manager.
        This is the preferred method for production environments (Cloud Run).
        """
        try:
            # Import the Secret Manager client library
            from google.cloud import secretmanager
            
            # Get project ID from environment or default
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "impactful-study-469120-m5")
            secret_id = "anthropic-api-key"
            
            # Create the Secret Manager client
            client = secretmanager.SecretManagerServiceClient()
            
            # Build the resource name of the secret
            name = client.secret_path(project_id, secret_id)
            
            # Access the secret version (latest)
            response = client.access_secret_version(request={"name": f"{name}/versions/latest"})
            
            # Return the secret payload
            return response.payload.data.decode("UTF-8")
            
        except ImportError:
            print("⚠️ google-cloud-secret-manager not installed")
            return None
        except Exception as e:
            print(f"⚠️ Error accessing Secret Manager: {e}")
            return None
        
    def get_api_key(self) -> str:
        """Get the Anthropic API key."""
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not configured.\n"
                "Set it in one of these locations:\n"
                "1. Google Secret Manager (production - Cloud Run)\n"
                "2. Streamlit Cloud secrets (production - Streamlit Cloud)\n"
                "3. .streamlit/secrets.toml (local development)\n"
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
        
        # Test Secret Manager access
        print("\nSecret Manager Test:")
        try:
            secret_key = config._get_secret_from_secret_manager()
            print(f"Secret Manager accessible: {'Yes' if secret_key else 'No'}")
            if secret_key:
                print(f"Secret value: {secret_key[:8]}...")
        except Exception as e:
            print(f"Secret Manager error: {e}")
        
        # Test database path
        db_path = config.get_database_path()
        print("\nDatabase Path Test:")
        print(f"Database path: {db_path}")
        
        # Test local secrets.toml
        secrets_path = Path(__file__).parent.parent.parent / ".streamlit" / "secrets.toml"
        print("\nLocal Secrets Test:")
        print(f"secrets.toml location: {secrets_path}")
        print(f"secrets.toml exists: {'Yes' if secrets_path.exists() else 'No'}")
        
        # Test environment variables
        print("\nEnvironment Variables Test:")
        print(f"GOOGLE_CLOUD_PROJECT_ID: {os.getenv('GOOGLE_CLOUD_PROJECT_ID', 'Not set')}")
        print(f"DATABASE_PATH: {os.getenv('DATABASE_PATH', 'Not set')}")
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")