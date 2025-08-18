import sqlite3
import logging

def create_tables(db_path: str = "src/database/superstore.db"):
    """Create all tables for the intelligent explanation system."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table with extended fields
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user' CHECK (role IN ('admin', 'user')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        sql_expertise_level INTEGER DEFAULT 2,
        cognitive_load_capacity INTEGER DEFAULT 3,
        has_completed_assessment BOOLEAN DEFAULT FALSE,
        sql_expertise INTEGER DEFAULT 0,
        data_analysis_fundamentals INTEGER DEFAULT 0,
        business_analytics INTEGER DEFAULT 0,
        forecasting_statistics INTEGER DEFAULT 0,
        data_visualization INTEGER DEFAULT 0,
        domain_knowledge_retail INTEGER DEFAULT 0,
        total_assessment_score INTEGER DEFAULT 0,
        user_level_category TEXT DEFAULT 'Beginner',
        age INTEGER,
        gender TEXT,
        profession TEXT,
        education_level TEXT,
        study_training TEXT
    )
    ''')
    
    # Create chat_sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_uuid TEXT NOT NULL,
        user_message TEXT NOT NULL,
        system_response TEXT NOT NULL,
        sql_query TEXT,
        explanation_given BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    
    # Create explanation_feedback table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS explanation_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session_id INTEGER NOT NULL,
        explanation_given BOOLEAN NOT NULL,
        was_needed BOOLEAN,
        was_helpful BOOLEAN,
        would_have_been_needed BOOLEAN,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
    )
    ''')
    
    # Create comprehensive_feedback table for research study feedback
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comprehensive_feedback (
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
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_explanation_feedback_user_id ON explanation_feedback(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_explanation_feedback_session_id ON explanation_feedback(session_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_comprehensive_feedback_user_id ON comprehensive_feedback(user_id)')
    
    conn.commit()
    conn.close()
    logging.info("Database tables created successfully")

    # Ensure existing databases are migrated to include newly added columns
    try:
        migrate_database(db_path)
    except Exception as e:
        logging.warning(f"Database migration step after table creation failed or was unnecessary: {e}")

def create_admin_user(db_path: str = "src/database/superstore.db"):
    """Create default admin user."""
    try:
        # Make sure schema is up-to-date (adds columns like sql_expertise if missing)
        try:
            migrate_database(db_path)
        except Exception as e:
            logging.warning(f"Skipping migration before admin creation (possibly already migrated): {e}")

        # Docker-compatible imports
        try:
            from new_data_assistant_project.src.database.models import User
        except ImportError:
            from src.database.models import User
        
        # Check if admin already exists
        admin = User.get_by_username(db_path, 'admin')
        if admin:
            logging.info("Admin user already exists")
            return
        
        # Create admin user
        admin_user = User.create_user(
            username='admin',
            password='admin123',  # Default password - should be changed in production
            role='admin'
        )
        admin_user.has_completed_assessment = True  # Admin doesn't need assessment
        admin_user.save(db_path)
        
        logging.info("Admin user created successfully (username: admin, password: admin123)")
        
    except Exception as e:
        logging.error(f"Error creating admin user: {e}")

def migrate_database(db_path: str = "src/database/superstore.db"):
    """Migrate existing database to new schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Basic columns to drop if exist
    for col in ["email", "profile_picture", "google_id", "name", "preferred_language"]:
        try:
            cursor.execute(f"ALTER TABLE users DROP COLUMN {col}")
        except Exception:
            pass
    
    # Ensure assessment columns exist
    for stmt in [
        "ALTER TABLE users ADD COLUMN sql_expertise INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN data_analysis_fundamentals INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN business_analytics INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN forecasting_statistics INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN data_visualization INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN domain_knowledge_retail INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN total_assessment_score INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN user_level_category TEXT DEFAULT 'Beginner'",
        "ALTER TABLE users ADD COLUMN gender TEXT",
        "ALTER TABLE users ADD COLUMN profession TEXT",
        "ALTER TABLE users ADD COLUMN education_level TEXT",
        "ALTER TABLE users ADD COLUMN study_training TEXT",
    ]:
        try:
            cursor.execute(stmt)
        except Exception:
            pass
    
    conn.commit()
    conn.close()
    logging.info("Database migrated successfully")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_tables()
    create_admin_user() 