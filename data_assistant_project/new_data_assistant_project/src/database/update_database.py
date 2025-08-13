#!/usr/bin/env python3
"""
Database update script to add the new comprehensive_feedback table.
Run this script to update existing databases with the new schema.
"""

import sqlite3
import logging
from pathlib import Path
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_database(db_path: str = "src/database/superstore.db"):
    """Update existing database with new tables and columns."""
    logger = logging.getLogger(__name__)
    
    if not os.path.exists(db_path):
        logger.warning(f"Database file not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if comprehensive_feedback table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='comprehensive_feedback'
        """)
        if cursor.fetchone():
            logger.info("comprehensive_feedback table already exists")
        else:
            logger.info("Creating comprehensive_feedback table...")
            cursor.execute('''
            CREATE TABLE comprehensive_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                frequency_rating INTEGER NOT NULL,
                frequency_reason TEXT,
                explanation_quality_rating INTEGER NOT NULL,
                explanation_quality_reason TEXT,
                system_helpfulness_rating INTEGER NOT NULL,
                system_helpfulness_reason TEXT,
                learning_improvement_rating INTEGER NOT NULL,
                learning_improvement_reason TEXT,
                auto_explanation BOOLEAN NOT NULL,
                auto_reason TEXT,
                system_accuracy TEXT NOT NULL,
                system_accuracy_index INTEGER NOT NULL,
                recommendation TEXT NOT NULL,
                recommendation_index INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            ''')
            cursor.execute('CREATE INDEX idx_comprehensive_feedback_user_id ON comprehensive_feedback(user_id)')
            logger.info("comprehensive_feedback table created successfully")
        
        # Check if age column exists in users table
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'age' not in columns:
            logger.info("Adding age column to users table...")
            cursor.execute('ALTER TABLE users ADD COLUMN age INTEGER')
            logger.info("age column added successfully")
        else:
            logger.info("age column already exists in users table")
        
        conn.commit()
        conn.close()
        logger.info("✅ Database updated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error updating database: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def main():
    """Main function to update database."""
    print("🔄 Updating database with new comprehensive_feedback table...")
    
    # Try multiple possible database paths
    possible_paths = [
        "src/database/superstore.db",
        "new_data_assistant_project/src/database/superstore.db",
        "../src/database/superstore.db"
    ]
    
    success = False
    for db_path in possible_paths:
        if Path(db_path).exists():
            print(f"📁 Found database at: {db_path}")
            if update_database(db_path):
                success = True
                break
        else:
            print(f"❌ Database not found at: {db_path}")
    
    if success:
        print("✅ Database update completed successfully!")
    else:
        print("❌ Failed to update database. Please check the database path.")

if __name__ == "__main__":
    main() 