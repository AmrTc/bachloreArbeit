import psycopg2
import logging
from psycopg2.extras import RealDictCursor
import os
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_postgres_connection(host: str, port: int, database: str, user: str, password: str):
    """Get PostgreSQL connection."""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            sslmode='require'
        )
        conn.autocommit = False
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise

def create_postgres_tables(host: str, port: int, database: str, user: str, password: str):
    """Create all tables for the intelligent explanation system in PostgreSQL."""
    conn = get_postgres_connection(host, port, database, user, password)
    cursor = conn.cursor()
    
    try:
        # Create users table with extended fields
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
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
            user_level_category VARCHAR(50) DEFAULT 'Beginner',
            age INTEGER,
            gender VARCHAR(100),
            profession VARCHAR(255),
            education_level VARCHAR(255),
            study_training VARCHAR(255)
        )
        ''')
        
        # Create chat_sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            session_uuid VARCHAR(255) NOT NULL,
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
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
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
            system_accuracy VARCHAR(255) NOT NULL,
            system_accuracy_index INTEGER NOT NULL,
            recommendation VARCHAR(255) NOT NULL,
            recommendation_index INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        ''')
        
        # Create superstore table for business data
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS superstore (
            row_id INTEGER PRIMARY KEY,
            order_id VARCHAR(255),
            order_date DATE,
            ship_date DATE,
            ship_mode VARCHAR(255),
            customer_id VARCHAR(255),
            customer_name VARCHAR(255),
            segment VARCHAR(255),
            country VARCHAR(255),
            city VARCHAR(255),
            state VARCHAR(255),
            postal_code VARCHAR(255),
            region VARCHAR(255),
            product_id VARCHAR(255),
            category VARCHAR(255),
            sub_category VARCHAR(255),
            product_name VARCHAR(255),
            sales DECIMAL(10,2),
            quantity INTEGER,
            discount DECIMAL(3,2),
            profit DECIMAL(10,2)
        )
        ''')
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_explanation_feedback_user_id ON explanation_feedback(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_explanation_feedback_session_id ON explanation_feedback(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_comprehensive_feedback_user_id ON comprehensive_feedback(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_superstore_region ON superstore(region)",
            "CREATE INDEX IF NOT EXISTS idx_superstore_category ON superstore(category)",
            "CREATE INDEX IF NOT EXISTS idx_superstore_order_date ON superstore(order_date)",
            "CREATE INDEX IF NOT EXISTS idx_superstore_customer ON superstore(customer_name)",
            "CREATE INDEX IF NOT EXISTS idx_superstore_product ON superstore(product_name)",
            "CREATE INDEX IF NOT EXISTS idx_superstore_segment ON superstore(segment)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        logger.info("PostgreSQL tables created successfully")
        
        # Update existing tables with any missing columns
        update_existing_tables(host, port, database, user, password)
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating PostgreSQL tables: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def update_existing_tables(host: str, port: int, database: str, user: str, password: str):
    """Update existing tables with missing columns."""
    conn = get_postgres_connection(host, port, database, user, password)
    cursor = conn.cursor()
    
    try:
        # Check if sql_expertise column exists in users table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'sql_expertise'
        """)
        
        if not cursor.fetchone():
            logger.info("Adding sql_expertise column to users table...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN sql_expertise INTEGER DEFAULT 0
            """)
            logger.info("Added sql_expertise column to users table")
        
        # Check if other missing columns exist
        missing_columns = [
            ('sql_expertise_level', 'INTEGER DEFAULT 2'),
            ('cognitive_load_capacity', 'INTEGER DEFAULT 3'),
            ('has_completed_assessment', 'BOOLEAN DEFAULT FALSE'),
            ('data_analysis_fundamentals', 'INTEGER DEFAULT 0'),
            ('business_analytics', 'INTEGER DEFAULT 0'),
            ('forecasting_statistics', 'INTEGER DEFAULT 0'),
            ('data_visualization', 'INTEGER DEFAULT 0'),
            ('domain_knowledge_retail', 'INTEGER DEFAULT 0'),
            ('total_assessment_score', 'INTEGER DEFAULT 0'),
            ('user_level_category', 'VARCHAR(50) DEFAULT \'Beginner\''),
            ('age', 'INTEGER'),
            ('gender', 'VARCHAR(100)'),
            ('profession', 'VARCHAR(255)'),
            ('education_level', 'VARCHAR(255)'),
            ('study_training', 'VARCHAR(255)')
        ]
        
        for column_name, column_type in missing_columns:
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = '{column_name}'
            """)
            
            if not cursor.fetchone():
                logger.info(f"Adding {column_name} column to users table...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                logger.info(f"Added {column_name} column to users table")
        
        conn.commit()
        logger.info("Table updates completed successfully")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating tables: {e}")
        raise
    finally:
        conn.close()

def create_admin_user(host: str, port: int, database: str, user: str, password: str):
    """Create default admin user in PostgreSQL."""
    conn = get_postgres_connection(host, port, database, user, password)
    cursor = conn.cursor()
    
    try:
        # Check if admin already exists
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if cursor.fetchone():
            logger.info("Admin user already exists")
            return
        
        # Create admin user with new password
        admin_password = "Nu4attNrF6Bcp5v"
        password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
        
        cursor.execute('''
        INSERT INTO users (
            username, password_hash, role, has_completed_assessment,
            sql_expertise_level, cognitive_load_capacity,
            sql_expertise, data_analysis_fundamentals, business_analytics,
            forecasting_statistics, data_visualization, domain_knowledge_retail,
            total_assessment_score, user_level_category, age, gender,
            profession, education_level, study_training
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            'admin', password_hash, 'admin', True,
            5, 5,  # High expertise levels
            5, 5, 5, 5, 5, 5,  # All domain scores maxed
            30, 'Expert',  # Total score and category
            30, 'Not specified', 'System Administrator', 'PhD', 'Computer Science'
        ))
        
        conn.commit()
        logger.info(f"Admin user created successfully (username: admin, password: {admin_password})")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating admin user: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def migrate_sqlite_to_postgres(sqlite_path: str, host: str, port: int, database: str, user: str, password: str):
    """Migrate data from SQLite to PostgreSQL."""
    import sqlite3
    import pandas as pd
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    
    # Connect to PostgreSQL
    pg_conn = get_postgres_connection(host, port, database, user, password)
    
    try:
        # Migrate superstore data
        logger.info("Migrating superstore data...")
        superstore_df = pd.read_sql_query("SELECT * FROM superstore", sqlite_conn)
        
        if not superstore_df.empty:
            # Convert DataFrame to list of tuples for bulk insert
            data_tuples = [tuple(x) for x in superstore_df.values]
            
            # Bulk insert into PostgreSQL
            cursor = pg_conn.cursor()
            cursor.executemany('''
            INSERT INTO superstore (
                row_id, order_id, order_date, ship_date, ship_mode, customer_id, 
                customer_name, segment, country, city, state, postal_code, 
                region, product_id, category, sub_category, product_name, 
                sales, quantity, discount, profit
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (row_id) DO NOTHING
            ''', data_tuples)
            
            pg_conn.commit()
            logger.info(f"Migrated {len(superstore_df)} superstore records")
        
        # Migrate users data
        logger.info("Migrating users data...")
        users_df = pd.read_sql_query("SELECT * FROM users", sqlite_conn)
        
        if not users_df.empty:
            cursor = pg_conn.cursor()
            for _, user_row in users_df.iterrows():
                cursor.execute('''
                INSERT INTO users (
                    username, password_hash, role, created_at, last_login,
                    sql_expertise_level, cognitive_load_capacity, has_completed_assessment,
                    sql_expertise, data_analysis_fundamentals, business_analytics,
                    forecasting_statistics, data_visualization, domain_knowledge_retail,
                    total_assessment_score, user_level_category, age, gender,
                    profession, education_level, study_training
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
                ''', (
                    user_row['username'], user_row['password_hash'], user_row['role'],
                    user_row['created_at'], user_row['last_login'],
                    user_row['sql_expertise_level'], user_row['cognitive_load_capacity'],
                    user_row['has_completed_assessment'], user_row.get('sql_expertise', 0),
                    user_row.get('data_analysis_fundamentals', 0), user_row.get('business_analytics', 0),
                    user_row.get('forecasting_statistics', 0), user_row.get('data_visualization', 0),
                    user_row.get('domain_knowledge_retail', 0), user_row.get('total_assessment_score', 0),
                    user_row.get('user_level_category', 'Beginner'), user_row.get('age'),
                    user_row.get('gender'), user_row.get('profession'), user_row.get('education_level'),
                    user_row.get('study_training')
                ))
            
            pg_conn.commit()
            logger.info(f"Migrated {len(users_df)} user records")
        
        # Migrate other tables if they exist
        for table in ['chat_sessions', 'explanation_feedback', 'comprehensive_feedback']:
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table}", sqlite_conn)
                if not df.empty:
                    logger.info(f"Migrating {table} data...")
                    cursor = pg_conn.cursor()
                    for _, row in df.iterrows():
                        # Convert row to dict and handle NULL values
                        row_dict = row.to_dict()
                        placeholders = ', '.join(['%s'] * len(row_dict))
                        columns = ', '.join(row_dict.keys())
                        
                        cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) ON CONFLICT DO NOTHING", 
                                     list(row_dict.values()))
                    
                    pg_conn.commit()
                    logger.info(f"Migrated {len(df)} {table} records")
            except Exception as e:
                logger.warning(f"Could not migrate {table}: {e}")
        
        logger.info("Migration completed successfully")
        
    except Exception as e:
        pg_conn.rollback()
        logger.error(f"Error during migration: {e}")
        raise
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    # Example usage
    import os
    
    # Get environment variables for PostgreSQL connection
    PG_HOST = os.getenv('PG_HOST', '34.59.248.159')
    PG_PORT = int(os.getenv('PG_PORT', '5432'))
    PG_DATABASE = os.getenv('PG_DATABASE', 'superstore')
    PG_USER = os.getenv('PG_USER', 'postgres')
    PG_PASSWORD = os.getenv('PG_PASSWORD', 'RHGAgo4<C4fyr')
    
    # Create tables and update existing ones
    create_postgres_tables(PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD)
    
    # Create admin user
    create_admin_user(PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD)
    
    # Migrate data if SQLite file exists
    sqlite_path = "data_assistant_project/new_data_assistant_project/src/database/superstore.db"
    if os.path.exists(sqlite_path):
        migrate_sqlite_to_postgres(sqlite_path, PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD)
