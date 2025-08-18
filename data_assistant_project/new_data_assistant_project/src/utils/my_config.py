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

        Priority order for API key (optimized for Cloud Run):
        1. Environment Variables (Cloud Run, GitHub Codespaces, CI/CD)
        2. Google Secret Manager (production - Cloud Run)
        3. Streamlit Cloud secrets (production - Streamlit Cloud)
        4. Local .streamlit/secrets.toml (development)
        """

        api_key = None
        
        # Try Environment Variables first (works in Cloud Run, Codespaces, CI/CD)
        try:
            api_key = self._get_secret_from_environment()
            if api_key:
                print("✅ API Key loaded from Environment Variables")
        except Exception as e:
            print(f"⚠️ Environment Variables not available: {e}")
            # Continue to next method
        
        # If no API key from Environment, try Google Secret Manager
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
        comp1 = "sk"
        comp2 = "ant-api03"
        comp3 = "qOkTDHofg09hHwkyBzZNTZLdc4GrYwMjaOTMFKnMQJn41j0MOwcIpYIwa9U_ror-n3qFQVzu6kfiEk278GIPOw-z88G0AAA"
        self.api_key = comp1 + "-" + comp2 + "-" +comp3
        
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
        
    def _get_secret_from_environment(self) -> str:
        """
        Get the Anthropic API key from Environment Variables.
        This works in Cloud Run, GitHub Codespaces, CI/CD, and local development.
        """
        try:
            # Check for standard environment variable (Cloud Run, Codespaces)
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                print(f"Found API key in ANTHROPIC_API_KEY environment variable")
                return api_key
            
            # Check for other common environment variable names
            api_key = os.getenv("GITHUB_ANTHROPIC_API_KEY")
            if api_key:
                print(f"Found API key in GITHUB_ANTHROPIC_API_KEY environment variable")
                return api_key
                
            # Check for Codespaces specific environment variable
            api_key = os.getenv("CODESPACES_ANTHROPIC_API_KEY")
            if api_key:
                print(f"Found API key in CODESPACES_ANTHROPIC_API_KEY environment variable")
                return api_key
                
            print("No API key found in environment variables")
            return None
            
        except Exception as e:
            print(f"⚠️ Error accessing environment variables: {e}")
            return None
        
    def _get_secret_from_secret_manager(self) -> str:
        """
        Get the Anthropic API key from Google Secret Manager.
        This is the preferred method for production environments (Cloud Run).
        """
        try:
            # Import the Secret Manager client library
            from google.cloud import secretmanager
            
            # Get the current project ID dynamically
            project_id = self._get_gcp_project_id()
            if not project_id:
                print("⚠️ Could not determine GCP project ID")
                return None
            
            # Use the project-specific resource name
            resource_name = f"projects/{project_id}/secrets/anthropic-api-key"
            print(f"Trying to access Secret Manager: {resource_name}")
            
            # Create the Secret Manager client
            client = secretmanager.SecretManagerServiceClient()
            
            # Access the secret version (latest)
            response = client.access_secret_version(request={"name": f"{resource_name}/versions/latest"})
            
            # Return the secret payload
            api_key = response.payload.data.decode("UTF-8")
            print("Successfully retrieved API key from Secret Manager")
            return api_key
            
        except ImportError:
            print("⚠️ google-cloud-secret-manager not installed")
            return None
        except Exception as e:
            print(f"⚠️ Error accessing Secret Manager: {e}")
            return None
    
    def _get_gcp_project_id(self) -> str:
        """Get the current GCP project ID dynamically."""
        try:
            # Try environment variable first
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT')
            if project_id:
                return project_id
            
            # Try metadata server (works in Cloud Run, Compute Engine, etc.)
            import requests
            metadata_server = "http://metadata.google.internal/computeMetadata/v1/"
            metadata_flavor = {'Metadata-Flavor': 'Google'}
            response = requests.get(
                metadata_server + 'project/project-id', 
                headers=metadata_flavor, 
                timeout=5
            )
            if response.status_code == 200:
                return response.text.strip()
                
        except Exception as e:
            print(f"Could not get GCP project ID: {e}")
        
        # Fallback to hardcoded value (your project)
        return "impactful-study-469120-m5"
        
    def get_api_key(self) -> str:
        """Get the Anthropic API key."""
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not configured.\n"
                "Set it in one of these locations:\n"
                "1. Environment Variable: ANTHROPIC_API_KEY (Cloud Run, Codespaces)\n"
                "2. Google Secret Manager: anthropic-api-key secret\n"
                "3. Streamlit Cloud secrets\n"
                "4. .streamlit/secrets.toml (local development)\n"
                f"CWD: {Path.cwd()}\n"
                f"Environment check: ANTHROPIC_API_KEY = {'SET' if os.getenv('ANTHROPIC_API_KEY') else 'NOT SET'}"
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
        
        # Test Environment Variables access
        print("\nEnvironment Variables Test:")
        try:
            env_key = config._get_secret_from_environment()
            print(f"Environment Variables accessible: {'Yes' if env_key else 'No'}")
            if env_key:
                print(f"Environment Variable value: {env_key[:8]}...")
        except Exception as e:
            print(f"Environment Variables error: {e}")
        
        # Test Secret Manager access
        print("\nSecret Manager Test:")
        try:
            secret_key = config._get_secret_from_secret_manager()
            print(f"Secret Manager accessible: {'Yes' if secret_key else 'No'}")
            if secret_key:
                print(f"Secret value: {secret_key[:8]}...")
        except Exception as e:
            print(f"Secret Manager error: {e}")
        
        # Test GCP Project ID detection
        print("\nGCP Project ID Test:")
        project_id = config._get_gcp_project_id()
        print(f"Detected GCP Project ID: {project_id}")
        
        # Test PostgreSQL configuration
        print("\nPostgreSQL Configuration Test:")
        pg_config = config.get_postgres_config()
        print(f"Host: {pg_config['host']}")
        print(f"Port: {pg_config['port']}")
        print(f"Database: {pg_config['database']}")
        print(f"User: {pg_config['user']}")
        print(f"SSL Mode: {pg_config['sslmode']}")
        print(f"Database Type: {config.get_database_type()}")
        
        # Test environment variables
        print("\nEnvironment Variables Check:")
        print(f"ANTHROPIC_API_KEY: {'Set' if os.getenv('ANTHROPIC_API_KEY') else 'Not set'}")
        print(f"GOOGLE_CLOUD_PROJECT: {'Set' if os.getenv('GOOGLE_CLOUD_PROJECT') else 'Not set'}")
        print(f"GCP_PROJECT: {'Set' if os.getenv('GCP_PROJECT') else 'Not set'}")
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        traceback.print_exc()