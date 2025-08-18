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
        1. GitHub Repository Secrets (CI/CD, Codespaces)
        2. Google Secret Manager (production - Cloud Run)
        3. Streamlit Cloud secrets (production - Streamlit Cloud)
        4. Local .streamlit/secrets.toml (development)
        """

        api_key = None
        
        # Try GitHub Repository Secrets first (CI/CD, Codespaces)
        try:
            api_key = self._get_secret_from_github()
            if api_key:
                print("✅ API Key loaded from GitHub Repository Secrets")
        except Exception as e:
            print(f"⚠️ GitHub Secrets not available: {e}")
            # Continue to next method
        
        # If no API key from GitHub, try Google Secret Manager
        if not api_key:
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
        
        # PostgreSQL configuration (replaces SQLite)
        self.postgres_config = {
            'host': os.getenv('PG_HOST', '34.59.248.159'),
            'port': int(os.getenv('PG_PORT', '5432')),
            'database': os.getenv('PG_DATABASE', 'superstore'),
            'user': os.getenv('PG_USER', 'postgres'),
            'password': os.getenv('PG_PASSWORD', 'RHGAgo4<C4fyr'),
            'sslmode': os.getenv('PG_SSLMODE', 'require'),
            'connect_timeout': int(os.getenv('PG_CONNECT_TIMEOUT', '30'))
        }
        
        # Database type indicator
        self.database_type = "postgresql"
        
    def _get_secret_from_github(self) -> str:
        """
        Get the Anthropic API key from GitHub Repository Secrets.
        This is the preferred method for CI/CD, Codespaces, and local development.
        """
        try:
            # Check for GitHub Secrets environment variable
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                return api_key
            
            # Check for other common environment variable names
            api_key = os.getenv("GITHUB_ANTHROPIC_API_KEY")
            if api_key:
                return api_key
                
            # Check for Codespaces specific environment variable
            api_key = os.getenv("CODESPACES_ANTHROPIC_API_KEY")
            if api_key:
                return api_key
                
            return None
            
        except Exception as e:
            print(f"⚠️ Error accessing GitHub Secrets: {e}")
            return None
        
    def _get_secret_from_secret_manager(self) -> str:
        """
        Get the Anthropic API key from Google Secret Manager.
        This is the preferred method for production environments (Cloud Run).
        """
        try:
            # Import the Secret Manager client library
            from google.cloud import secretmanager
            
            # Use the specific resource name for this project
            resource_name = "projects/315388300473/secrets/anthropic-api-key"
            
            # Create the Secret Manager client
            client = secretmanager.SecretManagerServiceClient()
            
            # Access the secret version (latest)
            response = client.access_secret_version(request={"name": f"{resource_name}/versions/latest"})
            
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
                "1. GitHub Repository Secrets (CI/CD, Codespaces)\n"
                "2. Google Secret Manager (production - Cloud Run)\n"
                "3. Streamlit Cloud secrets (production - Streamlit Cloud)\n"
                "4. .streamlit/secrets.toml (local development)\n"
                f"CWD: {Path.cwd()}"
            )
        return self.api_key
    
    def get_postgres_config(self) -> dict:
        """Get PostgreSQL connection configuration."""
        return self.postgres_config.copy()
    
    def get_database_type(self) -> str:
        """Get the database type (postgresql)."""
        return self.database_type
    
    def get_database_url(self) -> str:
        """Get PostgreSQL connection URL."""
        config = self.postgres_config
        return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?sslmode={config['sslmode']}"

if __name__ == "__main__":
    try:
        # Initialize configuration
        config = MyConfig()
        
        # Test API key loading
        api_key = config.get_api_key()
        print("\nAPI Key Test:")
        print(f"API Key loaded successfully: {'Yes' if api_key else 'No'}")
        print(f"API Key value: {api_key[:8]}..." if api_key else "No API key found")
        
        # Test GitHub Secrets access
        print("\nGitHub Secrets Test:")
        try:
            github_key = config._get_secret_from_github()
            print(f"GitHub Secrets accessible: {'Yes' if github_key else 'No'}")
            if github_key:
                print(f"GitHub Secret value: {github_key[:8]}...")
        except Exception as e:
            print(f"GitHub Secrets error: {e}")
        
        # Test Secret Manager access
        print("\nSecret Manager Test:")
        try:
            secret_key = config._get_secret_from_secret_manager()
            print(f"Secret Manager accessible: {'Yes' if secret_key else 'No'}")
            if secret_key:
                print(f"Secret value: {secret_key[:8]}...")
        except Exception as e:
            print(f"Secret Manager error: {e}")
        
        # Test PostgreSQL configuration
        print("\nPostgreSQL Configuration Test:")
        pg_config = config.get_postgres_config()
        print(f"Host: {pg_config['host']}")
        print(f"Port: {pg_config['port']}")
        print(f"Database: {pg_config['database']}")
        print(f"User: {pg_config['user']}")
        print(f"SSL Mode: {pg_config['sslmode']}")
        print(f"Database Type: {config.get_database_type()}")
        print(f"Database URL: {config.get_database_url()}")
        
        # Test local secrets.toml
        secrets_path = Path(__file__).parent.parent.parent / ".streamlit" / "secrets.toml"
        print("\nLocal Secrets Test:")
        print(f"secrets.toml location: {secrets_path}")
        print(f"secrets.toml exists: {'Yes' if secrets_path.exists() else 'No'}")
        
        # Test environment variables
        print("\nEnvironment Variables Test:")
        print(f"ANTHROPIC_API_KEY: {'Set' if os.getenv('ANTHROPIC_API_KEY') else 'Not set'}")
        print(f"GITHUB_ANTHROPIC_API_KEY: {'Set' if os.getenv('GITHUB_ANTHROPIC_API_KEY') else 'Not set'}")
        print(f"CODESPACES_ANTHROPIC_API_KEY: {'Set' if os.getenv('CODESPACES_ANTHROPIC_API_KEY') else 'Not set'}")
        print(f"Secret Manager Resource: projects/315388300473/secrets/anthropic-api-key")
        print(f"PG_HOST: {os.getenv('PG_HOST', 'Not set')}")
        print(f"PG_DATABASE: {os.getenv('PG_DATABASE', 'Not set')}")
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")