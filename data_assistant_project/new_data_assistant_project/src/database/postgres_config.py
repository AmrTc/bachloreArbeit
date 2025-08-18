import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class PostgresConfig:
    """PostgreSQL configuration manager."""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load PostgreSQL configuration from environment variables."""
        return {
            'host': os.getenv('PG_HOST', '34.59.248.159'),  # Updated IP address
            'port': int(os.getenv('PG_PORT', '5432')),
            'database': os.getenv('PG_DATABASE', 'superstore'),
            'user': os.getenv('PG_USER', 'postgres'),
            'password': os.getenv('PG_PASSWORD', 'RHGAgo4<C4fyr'),  # Updated password
            'sslmode': os.getenv('PG_SSLMODE', 'require'),
            'connect_timeout': int(os.getenv('PG_CONNECT_TIMEOUT', '30')),
            'application_name': os.getenv('PG_APP_NAME', 'data_assistant_app')
        }
    
    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        config = self.config
        return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?sslmode={config['sslmode']}"
    
    def get_connection_params(self) -> Dict[str, Any]:
        """Get PostgreSQL connection parameters."""
        return self.config.copy()
    
    def validate_config(self) -> bool:
        """Validate PostgreSQL configuration."""
        required_fields = ['host', 'port', 'database', 'user', 'password']
        
        for field in required_fields:
            if not self.config.get(field):
                logger.error(f"Missing required PostgreSQL configuration: {field}")
                return False
        
        # Validate port range
        if not (1 <= self.config['port'] <= 65535):
            logger.error(f"Invalid PostgreSQL port: {config['port']}")
            return False
        
        logger.info("PostgreSQL configuration validated successfully")
        return True
    
    def get_cloud_sql_config(self) -> Dict[str, Any]:
        """Get Google Cloud SQL specific configuration."""
        cloud_config = self.config.copy()
        
        # Cloud SQL specific settings
        cloud_config.update({
            'sslmode': 'require',
            'application_name': 'data_assistant_cloud',
            'connect_timeout': 30,
            'keepalives_idle': 600,
            'keepalives_interval': 10,
            'keepalives_count': 5
        })
        
        return cloud_config

# Environment variable templates for Google Cloud
ENV_TEMPLATE = """
# PostgreSQL Configuration for Google Cloud
export PG_HOST="34.59.248.159"
export PG_PORT="5432"
export PG_DATABASE="superstore"
export PG_USER="postgres"
export PG_PASSWORD="RHGAgo4<C4fyr"
export PG_SSLMODE="require"
export PG_CONNECT_TIMEOUT="30"
export PG_APP_NAME="data_assistant_app"
"""

# Docker environment file template
DOCKER_ENV_TEMPLATE = """
# PostgreSQL Configuration for Docker/Cloud
PG_HOST=34.59.248.159
PG_PORT=5432
PG_DATABASE=superstore
PG_USER=postgres
PG_PASSWORD=RHGAgo4<C4fyr
PG_SSLMODE=require
PG_CONNECT_TIMEOUT=30
PG_APP_NAME=data_assistant_app
"""

if __name__ == "__main__":
    config = PostgresConfig()
    
    print("PostgreSQL Configuration:")
    print(f"Host: {config.config['host']}")
    print(f"Port: {config.config['port']}")
    print(f"Database: {config.config['database']}")
    print(f"User: {config.config['user']}")
    print(f"SSL Mode: {config.config['sslmode']}")
    
    print("\nConnection String:")
    print(config.get_connection_string())
    
    print("\nEnvironment Variables Template:")
    print(ENV_TEMPLATE)
    
    print("\nDocker Environment Template:")
    print(DOCKER_ENV_TEMPLATE)
