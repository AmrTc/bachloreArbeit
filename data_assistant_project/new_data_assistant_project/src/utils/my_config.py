import os
from pathlib import Path
from dotenv import load_dotenv

# Import modules using the installed package

from new_data_assistant_project.src.utils.secrets_path_utils import SecretsPathUtils

class MyConfig:
    """Configuration manager for the data assistant project."""
    
    def __init__(self):
        """Initialize configuration by loading environment variables."""
        # Get secrets path utils instance
        secrets_utils = SecretsPathUtils.get_instance()
        
        # Get path to .env file
        env_path = secrets_utils.get_env_file_path()
        
        # Load environment variables from .env file if it exists
        if not env_path.exists():
            raise FileNotFoundError(
                f"Environment file not found at {env_path}. "
                f"Please create a .env file in the secrets directory with your ANTHROPIC_API_KEY."
            )
        
        # Load the .env file
        load_dotenv(str(env_path))  # Convert Path to string for dotenv
        
        # Initialize configuration values
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.database_path = os.getenv('DATABASE_PATH', 'src/database/superstore.db')
        
    def get_api_key(self) -> str:
        """Get the Anthropic API key."""
        if not self.api_key:
            env_path = SecretsPathUtils.get_instance().get_env_file_path()
            raise ValueError(
                f"ANTHROPIC_API_KEY not found in environment variables.\n"
                f"Checked .env file at: {env_path}\n"
                f"Current working directory: {Path.cwd()}\n"
                f"Please ensure the .env file contains: ANTHROPIC_API_KEY=your_api_key_here"
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