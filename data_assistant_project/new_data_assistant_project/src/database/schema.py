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
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user' CHECK (role IN ('admin', 'user')),
        name TEXT,
        profile_picture TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        sql_expertise_level INTEGER DEFAULT 2,
        domain_knowledge INTEGER DEFAULT 2,
        cognitive_load_capacity INTEGER DEFAULT 3,
        has_completed_assessment BOOLEAN DEFAULT FALSE,
        google_id TEXT  -- Keep for backward compatibility
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
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_explanation_feedback_user_id ON explanation_feedback(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_explanation_feedback_session_id ON explanation_feedback(session_id)')
    
    conn.commit()
    conn.close()
    logging.info("Database tables created successfully")

def create_admin_user(db_path: str = "src/database/superstore.db"):
    """Create default admin user."""
    try:
        from new_data_assistant_project.src.database.models import User
        
        # Check if admin already exists
        admin = User.get_by_username(db_path, 'admin')
        if admin:
            logging.info("Admin user already exists")
            return
        
        # Create admin user
        admin_user = User.create_user(
            username='admin',
            email='admin@system.local',
            password='admin123',  # Default password - should be changed in production
            role='admin',
            name='System Administrator'
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
    
    try:
        # Check if the old users table exists and has the old structure
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'google_id' in columns and 'username' not in columns:
            logging.info("Migrating old users table...")
            
            # Backup old data
            cursor.execute("CREATE TABLE users_backup AS SELECT * FROM users")
            
            # Drop old table
            cursor.execute("DROP TABLE users")
            
            # Create new tables
            create_tables(db_path)
            
            # Note: Old Google OAuth users would need manual migration
            # For now, we start fresh with the new authentication system
            
            logging.info("Database migration completed")
        else:
            logging.info("Database already has new schema")
            
    except sqlite3.Error as e:
        logging.error(f"Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_tables()
    create_admin_user() 