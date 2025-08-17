#!/usr/bin/env python3
"""
Test PostgreSQL connection to Google Cloud SQL
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_connection():
    """Test PostgreSQL connection to your instance."""
    
    # PostgreSQL connection configuration
    PG_CONFIG = {
        'host': '34.59.248.159',  # Your instance IP
        'port': 5432,
        'database': 'data_assistant',
        'user': 'postgres',
        'password': '<zdG$DLpmG,~p3A',  # Your password
        'sslmode': 'require',
        'connect_timeout': 30
    }
    
    try:
        logger.info("🔌 Testing PostgreSQL connection...")
        logger.info(f"📍 Host: {PG_CONFIG['host']}")
        logger.info(f"👤 User: {PG_CONFIG['user']}")
        logger.info(f"📚 Database: {PG_CONFIG['database']}")
        
        # Test connection
        conn = psycopg2.connect(**PG_CONFIG)
        cursor = conn.cursor()
        
        # Test basic connection
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"✅ Connection successful!")
        logger.info(f"📊 PostgreSQL version: {version[0]}")
        
        # Test if database exists and is accessible
        cursor.execute("SELECT current_database();")
        current_db = cursor.fetchone()
        logger.info(f"📚 Current database: {current_db[0]}")
        
        # Test if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            logger.info(f"📋 Existing tables: {[table[0] for table in tables]}")
        else:
            logger.info("📋 No tables found in database")
        
        # Test basic operations
        cursor.execute("SELECT 1 as test_value;")
        test_result = cursor.fetchone()
        logger.info(f"🧪 Basic query test: {test_result[0]}")
        
        cursor.close()
        conn.close()
        
        logger.info("🎉 All connection tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return False

def test_environment_variables():
    """Test if environment variables are set correctly."""
    logger.info("🔍 Testing environment variables...")
    
    env_vars = {
        'PG_HOST': os.getenv('PG_HOST'),
        'PG_PORT': os.getenv('PG_PORT'),
        'PG_DATABASE': os.getenv('PG_DATABASE'),
        'PG_USER': os.getenv('PG_USER'),
        'PG_PASSWORD': os.getenv('PG_PASSWORD'),
        'PG_SSLMODE': os.getenv('PG_SSLMODE')
    }
    
    all_set = True
    for var, value in env_vars.items():
        if value:
            logger.info(f"✅ {var}: {value}")
        else:
            logger.warning(f"⚠️ {var}: Not set")
            all_set = False
    
    if all_set:
        logger.info("✅ All environment variables are set")
    else:
        logger.warning("⚠️ Some environment variables are missing")
    
    return all_set

def main():
    """Main test function."""
    logger.info("🚀 PostgreSQL Connection Test")
    logger.info("=" * 40)
    
    # Test environment variables
    test_environment_variables()
    logger.info("")
    
    # Test connection
    success = test_connection()
    
    if success:
        logger.info("")
        logger.info("🎉 Connection test completed successfully!")
        logger.info("📋 Your PostgreSQL instance is ready for migration")
    else:
        logger.error("")
        logger.error("❌ Connection test failed!")
        logger.error("🔍 Please check your configuration and try again")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
