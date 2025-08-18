#!/usr/bin/env python3
"""
Deployment Script with Admin User Creation
This script ensures an admin user is created during deployment.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_admin_user():
    """Ensure admin user exists with correct credentials."""
    try:
        # Import PostgreSQL modules
        from src.database.postgres_config import PostgresConfig
        from src.database.postgres_models import User
        
        # Get database configuration
        config = PostgresConfig()
        db_config = config.get_connection_params()
        
        logger.info("🔌 Testing PostgreSQL connection...")
        
        # Test connection
        import psycopg2
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Check if admin exists
        cursor.execute("SELECT id, username, role FROM users WHERE username = 'admin'")
        existing_admin = cursor.fetchone()
        
        if existing_admin:
            logger.info(f"ℹ️ Admin user already exists: ID={existing_admin[0]}, Username={existing_admin[1]}, Role={existing_admin[2]}")
            
            # Update admin password if needed
            admin_password = "Nu4attNrF6Bcp5v"
            password_hash = User._hash_password(admin_password)
            
            cursor.execute("UPDATE users SET password_hash = %s WHERE username = 'admin'", (password_hash,))
            conn.commit()
            logger.info(f"✅ Admin password updated to: {admin_password}")
            
        else:
            logger.info("👤 Creating admin user...")
            
            # Create admin user
            admin_user = User.create_user("admin", "Nu4attNrF6Bcp5v", "admin")
            admin_user.sql_expertise_level = 5
            admin_user.cognitive_load_capacity = 5
            admin_user.has_completed_assessment = True
            admin_user.sql_expertise = 5
            admin_user.data_analysis_fundamentals = 5
            admin_user.business_analytics = 5
            admin_user.forecasting_statistics = 5
            admin_user.data_visualization = 5
            admin_user.domain_knowledge_retail = 5
            admin_user.total_assessment_score = 30
            admin_user.user_level_category = "Expert"
            admin_user.age = 30
            admin_user.gender = "Not specified"
            admin_user.profession = "System Administrator"
            admin_user.education_level = "PhD"
            admin_user.study_training = "Computer Science"
            
            admin_user.save(db_config)
            logger.info("✅ Admin user created successfully!")
            logger.info(f"👤 Username: admin")
            logger.info(f"🔑 Password: Nu4attNrF6Bcp5v")
            logger.info(f"👑 Role: admin")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error ensuring admin user: {e}")
        return False

def test_database_connection():
    """Test database connection and basic functionality."""
    try:
        from src.database.postgres_config import PostgresConfig
        from src.database.postgres_models import User
        
        config = PostgresConfig()
        db_config = config.get_connection_params()
        
        # Test connection
        import psycopg2
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Test basic queries
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        logger.info("✅ Database connection test successful!")
        logger.info(f"📊 Total users: {user_count}")
        logger.info(f"📋 Available tables: {tables}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        return False

def main():
    """Main deployment function."""
    logger.info("🚀 Starting deployment with admin user creation...")
    
    # Step 1: Test database connection
    if not test_database_connection():
        logger.error("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Step 2: Ensure admin user exists
    if not ensure_admin_user():
        logger.error("❌ Failed to ensure admin user")
        sys.exit(1)
    
    logger.info("🎉 Deployment completed successfully!")
    logger.info("✅ Database connection working")
    logger.info("✅ Admin user ready")
    logger.info("\n🔑 Admin credentials:")
    logger.info("   Username: admin")
    logger.info("   Password: Nu4attNrF6Bcp5v")
    logger.info("   Role: admin")

if __name__ == "__main__":
    main()
