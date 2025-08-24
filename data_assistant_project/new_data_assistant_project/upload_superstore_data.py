#!/usr/bin/env python3
"""
Script to upload Superstore data to PostgreSQL database.
Supports multiple data sources: Excel, CSV, SQLite
"""

import pandas as pd
import psycopg2
import os
import sys
import logging
from pathlib import Path
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def get_postgres_connection():
    """Get PostgreSQL connection using existing config."""
    try:
        from src.utils.my_config import MyConfig
        config = MyConfig()
        db_config = config.get_postgres_config()
    except:
        # Fallback configuration
        db_config = {
            'host': '34.59.248.159',
            'port': 5432,
            'database': 'superstore',
            'user': 'postgres',
            'password': 'RHGAgo4<C4fyr',
            'sslmode': 'require'
        }
    
    logger.info(f"Connecting to PostgreSQL: {db_config['host']}:{db_config['port']}")
    return psycopg2.connect(**db_config)

def clear_existing_superstore_data(conn):
    """Clear existing superstore data."""
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM superstore")
        count = cursor.rowcount
        conn.commit()
        logger.info(f"Cleared {count} existing rows from superstore table")
    except Exception as e:
        logger.warning(f"Could not clear existing data: {e}")
        conn.rollback()
    finally:
        cursor.close()

def load_from_excel(file_path: str) -> pd.DataFrame:
    """Load data from Excel file."""
    logger.info(f"Loading data from Excel: {file_path}")
    
    try:
        # Try different sheet names
        df = pd.read_excel(file_path)
        logger.info(f"Successfully loaded {len(df)} rows from Excel")
        return df
    except Exception as e:
        logger.error(f"Failed to load Excel file: {e}")
        return None

def load_from_sqlite(db_path: str) -> pd.DataFrame:
    """Load data from SQLite database."""
    logger.info(f"Loading data from SQLite: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM superstore", conn)
        conn.close()
        logger.info(f"Successfully loaded {len(df)} rows from SQLite")
        return df
    except Exception as e:
        logger.error(f"Failed to load SQLite data: {e}")
        return None

def load_from_csv(file_path: str) -> pd.DataFrame:
    """Load data from CSV file."""
    logger.info(f"Loading data from CSV: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Successfully loaded {len(df)} rows from CSV")
        return df
    except Exception as e:
        logger.error(f"Failed to load CSV file: {e}")
        return None

def clean_superstore_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and prepare superstore data for PostgreSQL."""
    logger.info("Cleaning superstore data...")
    
    # Make a copy to avoid modifying original
    df_clean = df.copy()
    
    # Standardize column names to match PostgreSQL schema
    column_mapping = {
        'Row ID': 'row_id',
        'Order ID': 'order_id', 
        'Order Date': 'order_date',
        'Ship Date': 'ship_date',
        'Ship Mode': 'ship_mode',
        'Customer ID': 'customer_id',
        'Customer Name': 'customer_name',
        'Segment': 'segment',
        'Country': 'country',
        'City': 'city',
        'State': 'state',
        'Postal Code': 'postal_code',
        'Region': 'region',
        'Product ID': 'product_id',
        'Category': 'category',
        'Sub-Category': 'sub_category',
        'Product Name': 'product_name',
        'Sales': 'sales',
        'Quantity': 'quantity',
        'Discount': 'discount',
        'Profit': 'profit'
    }
    
    # Rename columns if they exist
    for old_name, new_name in column_mapping.items():
        if old_name in df_clean.columns:
            df_clean = df_clean.rename(columns={old_name: new_name})
    
    # Ensure required columns exist
    required_columns = [
        'row_id', 'order_id', 'order_date', 'ship_date', 'ship_mode',
        'customer_id', 'customer_name', 'segment', 'country', 'city', 
        'state', 'postal_code', 'region', 'product_id', 'category',
        'sub_category', 'product_name', 'sales', 'quantity', 'discount', 'profit'
    ]
    
    # Check for missing columns
    missing_columns = [col for col in required_columns if col not in df_clean.columns]
    if missing_columns:
        logger.warning(f"Missing columns: {missing_columns}")
        # Add missing columns with default values
        for col in missing_columns:
            if col in ['sales', 'quantity', 'discount', 'profit']:
                df_clean[col] = 0
            else:
                df_clean[col] = 'Unknown'
    
    # Clean date columns
    date_columns = ['order_date', 'ship_date']
    for col in date_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
    
    # Clean numeric columns
    numeric_columns = ['sales', 'quantity', 'discount', 'profit']
    for col in numeric_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
    
    # Clean text columns
    text_columns = [col for col in required_columns if col not in date_columns + numeric_columns + ['row_id']]
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).fillna('Unknown')
    
    # Remove rows with missing row_id
    if 'row_id' in df_clean.columns:
        df_clean = df_clean.dropna(subset=['row_id'])
        df_clean['row_id'] = df_clean['row_id'].astype(int)
    else:
        # Create row_id if missing
        df_clean['row_id'] = range(1, len(df_clean) + 1)
    
    # Remove duplicates based on row_id
    df_clean = df_clean.drop_duplicates(subset=['row_id'])
    
    # Select only required columns in the correct order
    df_clean = df_clean[required_columns]
    
    logger.info(f"Data cleaned: {len(df_clean)} rows, {len(df_clean.columns)} columns")
    return df_clean

def upload_to_postgres(df: pd.DataFrame, conn):
    """Upload dataframe to PostgreSQL."""
    logger.info(f"Uploading {len(df)} rows to PostgreSQL...")
    
    cursor = conn.cursor()
    
    try:
        # Prepare INSERT statement
        insert_sql = """
        INSERT INTO superstore (
            row_id, order_id, order_date, ship_date, ship_mode, customer_id,
            customer_name, segment, country, city, state, postal_code,
            region, product_id, category, sub_category, product_name,
            sales, quantity, discount, profit
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (row_id) DO UPDATE SET
            order_id = EXCLUDED.order_id,
            order_date = EXCLUDED.order_date,
            ship_date = EXCLUDED.ship_date,
            ship_mode = EXCLUDED.ship_mode,
            customer_id = EXCLUDED.customer_id,
            customer_name = EXCLUDED.customer_name,
            segment = EXCLUDED.segment,
            country = EXCLUDED.country,
            city = EXCLUDED.city,
            state = EXCLUDED.state,
            postal_code = EXCLUDED.postal_code,
            region = EXCLUDED.region,
            product_id = EXCLUDED.product_id,
            category = EXCLUDED.category,
            sub_category = EXCLUDED.sub_category,
            product_name = EXCLUDED.product_name,
            sales = EXCLUDED.sales,
            quantity = EXCLUDED.quantity,
            discount = EXCLUDED.discount,
            profit = EXCLUDED.profit
        """
        
        # Convert DataFrame to list of tuples
        data_tuples = []
        for _, row in df.iterrows():
            data_tuples.append(tuple(row))
        
        # Batch insert
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(data_tuples), batch_size):
            batch = data_tuples[i:i + batch_size]
            cursor.executemany(insert_sql, batch)
            total_inserted += len(batch)
            logger.info(f"Inserted batch: {total_inserted}/{len(data_tuples)} rows")
        
        conn.commit()
        logger.info(f"✅ Successfully uploaded {total_inserted} rows to PostgreSQL")
        
    except Exception as e:
        logger.error(f"Error uploading to PostgreSQL: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def verify_upload(conn):
    """Verify the data upload was successful."""
    logger.info("Verifying data upload...")
    
    cursor = conn.cursor()
    try:
        # Count total rows
        cursor.execute("SELECT COUNT(*) FROM superstore")
        total_rows = cursor.fetchone()[0]
        
        # Get some sample data
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM superstore 
            GROUP BY category 
            ORDER BY count DESC
        """)
        category_counts = cursor.fetchall()
        
        # Get date range
        cursor.execute("""
            SELECT MIN(order_date) as min_date, MAX(order_date) as max_date
            FROM superstore
        """)
        date_range = cursor.fetchone()
        
        logger.info(f"✅ Verification successful:")
        logger.info(f"   Total rows: {total_rows}")
        logger.info(f"   Date range: {date_range[0]} to {date_range[1]}")
        logger.info(f"   Categories: {category_counts}")
        
        return total_rows > 0
        
    except Exception as e:
        logger.error(f"Error verifying upload: {e}")
        return False
    finally:
        cursor.close()

def main():
    """Main upload process."""
    logger.info("🚀 Starting Superstore data upload to PostgreSQL")
    
    # Define possible data sources (in order of preference)
    base_path = Path(__file__).parent
    data_sources = [
        base_path / "data" / "datasets" / "superstore_dataset.xls",
        base_path / "src" / "database" / "superstore.db",
        base_path / "data" / "datasets" / "superstore_dataset.csv",
        base_path / "data" / "datasets" / "superstore.csv"
    ]
    
    # Try to load data from available sources
    df = None
    source_used = None
    
    for source in data_sources:
        if source.exists():
            logger.info(f"Found data source: {source}")
            
            if source.suffix == '.xls' or source.suffix == '.xlsx':
                df = load_from_excel(str(source))
            elif source.suffix == '.db':
                df = load_from_sqlite(str(source))
            elif source.suffix == '.csv':
                df = load_from_csv(str(source))
            
            if df is not None and len(df) > 0:
                source_used = source
                break
    
    if df is None or len(df) == 0:
        logger.error("❌ No valid data source found or data is empty")
        logger.info(f"Looked for data in: {[str(s) for s in data_sources]}")
        return False
    
    logger.info(f"✅ Using data source: {source_used}")
    logger.info(f"   Original data shape: {df.shape}")
    
    # Clean the data
    df_clean = clean_superstore_data(df)
    
    if len(df_clean) == 0:
        logger.error("❌ No data remaining after cleaning")
        return False
    
    # Connect to PostgreSQL
    try:
        conn = get_postgres_connection()
        logger.info("✅ Connected to PostgreSQL")
        
        # Clear existing data (optional)
        response = input("Clear existing superstore data? (y/N): ").strip().lower()
        if response == 'y':
            clear_existing_superstore_data(conn)
        
        # Upload data
        upload_to_postgres(df_clean, conn)
        
        # Verify upload
        success = verify_upload(conn)
        
        conn.close()
        
        if success:
            logger.info("🎉 Superstore data upload completed successfully!")
            return True
        else:
            logger.error("❌ Upload verification failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Upload cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
