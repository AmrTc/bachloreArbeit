#!/usr/bin/env python3
"""
Switch application from SQLite to PostgreSQL
This script updates the necessary files to use PostgreSQL instead of SQLite
"""

import os
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_original_files():
    """Backup original SQLite-based files."""
    logger.info("📦 Creating backups of original files...")
    
    backup_dir = "backup_sqlite"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    files_to_backup = [
        "data_assistant_project/new_data_assistant_project/src/database/models.py",
        "data_assistant_project/new_data_assistant_project/src/utils/auth_manager.py"
    ]
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = os.path.join(backup_dir, os.path.basename(file_path))
            shutil.copy2(file_path, backup_path)
            logger.info(f"✅ Backed up: {file_path} -> {backup_path}")
    
    logger.info(f"✅ Backups created in: {backup_dir}")

def update_models_file():
    """Update the models.py file to use PostgreSQL."""
    logger.info("📝 Updating models.py to use PostgreSQL...")
    
    models_path = "data_assistant_project/new_data_assistant_project/src/database/models.py"
    
    if not os.path.exists(models_path):
        logger.error(f"❌ Models file not found: {models_path}")
        return False
    
    # Read the current models file
    with open(models_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace SQLite imports with PostgreSQL
    content = content.replace(
        "import sqlite3",
        "import psycopg2\nfrom psycopg2.extras import RealDictCursor"
    )
    
    # Replace connection method
    content = content.replace(
        "conn = sqlite3.connect(db_path)",
        "conn = psycopg2.connect(**db_config)"
    )
    
    # Replace parameter placeholders
    content = content.replace("?", "%s")
    
    # Update the file
    with open(models_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("✅ Updated models.py for PostgreSQL")
    return True

def update_auth_manager():
    """Update the auth_manager.py file to use PostgreSQL."""
    logger.info("📝 Updating auth_manager.py to use PostgreSQL...")
    
    auth_path = "data_assistant_project/new_data_assistant_project/src/utils/auth_manager.py"
    
    if not os.path.exists(auth_path):
        logger.error(f"❌ Auth manager file not found: {auth_path}")
        return False
    
    # Read the current auth manager file
    with open(auth_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace imports
    content = content.replace(
        "from new_data_assistant_project.src.database.models import User",
        "from postgres_models import User"
    )
    content = content.replace(
        "from src.database.models import User",
        "from postgres_models import User"
    )
    
    # Replace database path with config
    content = content.replace(
        "self.db_path = get_absolute_path('src/database/superstore.db')",
        "self.postgres_config = PostgresConfig()\n        self.db_config = self.postgres_config.get_connection_params()"
    )
    
    # Replace all db_path references with db_config
    content = content.replace("self.db_path", "self.db_config")
    
    # Update the file
    with open(auth_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("✅ Updated auth_manager.py for PostgreSQL")
    return True

def create_postgres_imports():
    """Create a postgres_imports.py file for easy switching."""
    logger.info("📝 Creating postgres_imports.py...")
    
    imports_content = '''# PostgreSQL imports for the application
# This file provides PostgreSQL-compatible imports

from postgres_models import User
from postgres_auth_manager import PostgresAuthManager
from postgres_config import PostgresConfig

# Database connection
def get_db_config():
    """Get PostgreSQL database configuration."""
    config = PostgresConfig()
    return config.get_connection_params()

def get_db_connection():
    """Get PostgreSQL database connection."""
    import psycopg2
    config = get_db_config()
    return psycopg2.connect(**config)
'''
    
    with open("postgres_imports.py", 'w', encoding='utf-8') as f:
        f.write(imports_content)
    
    logger.info("✅ Created postgres_imports.py")

def create_migration_guide():
    """Create a migration guide for the user."""
    logger.info("📝 Creating migration guide...")
    
    guide_content = '''# Migration to PostgreSQL - Next Steps

## ✅ What has been done:

1. **Backup created**: Original SQLite files backed up in `backup_sqlite/`
2. **Models updated**: `models.py` now uses PostgreSQL
3. **Auth manager updated**: `auth_manager.py` now uses PostgreSQL
4. **PostgreSQL files created**: All necessary PostgreSQL files are in the root directory

## 🚀 Next steps:

### 1. Test PostgreSQL connection:
```bash
python test_postgres_connection.py
```

### 2. Run migration:
```bash
python migrate_to_postgres.py
```

### 3. Test the application:
```bash
cd data_assistant_project/new_data_assistant_project
streamlit run streamlit_entry.py
```

## 🔧 If you encounter issues:

### Rollback to SQLite:
```bash
# Restore original files
cp backup_sqlite/models.py data_assistant_project/new_data_assistant_project/src/database/
cp backup_sqlite/auth_manager.py data_assistant_project/new_data_assistant_project/src/utils/
```

### Check PostgreSQL connection:
```bash
python test_postgres_connection.py
```

### Verify database tables:
```bash
python -c "
from postgres_config import PostgresConfig
from postgres_schema import create_postgres_tables
config = PostgresConfig().get_connection_params()
create_postgres_tables(**config)
print('Tables created successfully!')
"
```

## 📁 Files created/modified:

- **`postgres_config.py`** - PostgreSQL configuration
- **`postgres_schema.py`** - Database schema
- **`postgres_models.py`** - PostgreSQL-compatible models
- **`postgres_auth_manager.py`** - PostgreSQL-compatible auth manager
- **`migrate_to_postgres.py`** - Migration script
- **`test_postgres_connection.py`** - Connection test
- **`postgres_imports.py`** - Easy imports for PostgreSQL

## 🎯 Success indicators:

- ✅ Connection test passes
- ✅ Migration completes without errors
- ✅ Application starts without database errors
- ✅ Login/registration works
- ✅ All features function normally

Good luck with the migration! 🚀
'''
    
    with open("MIGRATION_NEXT_STEPS.md", 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    logger.info("✅ Created MIGRATION_NEXT_STEPS.md")

def main():
    """Main migration function."""
    logger.info("🚀 Starting application migration to PostgreSQL...")
    
    try:
        # Step 1: Backup original files
        backup_original_files()
        
        # Step 2: Update models.py
        if not update_models_file():
            logger.error("❌ Failed to update models.py")
            return False
        
        # Step 3: Update auth_manager.py
        if not update_auth_manager():
            logger.error("❌ Failed to update auth_manager.py")
            return False
        
        # Step 4: Create helper files
        create_postgres_imports()
        create_migration_guide()
        
        logger.info("🎉 Application migration to PostgreSQL completed successfully!")
        logger.info("📋 Check MIGRATION_NEXT_STEPS.md for next steps")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
