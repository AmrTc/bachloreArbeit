import sqlite3

def create_users_table(db_path: str = "data_assistant_project/src/database/superstore.db"):
    """Create users table for Google authentication."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        google_id TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        name TEXT,
        profile_picture TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        sql_expertise_level INTEGER DEFAULT 2,
        domain_knowledge INTEGER DEFAULT 2,
        cognitive_load_capacity INTEGER DEFAULT 3
    )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_users_table() 