import pandas as pd
import sqlite3
import logging
import os
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_superstore_data(db_path: str = "src/database/superstore.db", excel_path: str = "data/datasets/superstore_dataset.xls"):
    """
    Import Superstore dataset from Excel file into SQLite database.
    
    Args:
        db_path: Path to the SQLite database
        excel_path: Path to the Excel file
    """
    try:
        # Check if Excel file exists
        if not os.path.exists(excel_path):
            logger.error(f"Excel file not found: {excel_path}")
            return False
            
        # Read Excel file
        logger.info(f"Reading Excel file: {excel_path}")
        df = pd.read_excel(excel_path)
        
        logger.info(f"Excel data shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create superstore table
        logger.info("Creating superstore table...")
        
        # Generate CREATE TABLE statement based on DataFrame columns and types
        columns = []
        for col, dtype in df.dtypes.items():
            if 'int' in str(dtype):
                sql_type = 'INTEGER'
            elif 'float' in str(dtype):
                sql_type = 'REAL'
            elif 'datetime' in str(dtype):
                sql_type = 'TEXT'
            else:
                sql_type = 'TEXT'
            
            # Clean column name (remove special characters, spaces)
            clean_col = col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace('/', '_')
            columns.append(f'"{clean_col}" {sql_type}')
        
        create_table_sql = f'''
        CREATE TABLE IF NOT EXISTS superstore (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {', '.join(columns)}
        )
        '''
        
        cursor.execute(create_table_sql)
        logger.info("Superstore table created successfully")
        
        # Insert data
        logger.info("Inserting data into superstore table...")
        
        # Clean column names for insertion
        clean_columns = [col.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace('/', '_') for col in df.columns]
        
        # Prepare data for insertion
        df_clean = df.copy()
        df_clean.columns = clean_columns
        
        # Convert datetime columns to string if they exist
        for col in df_clean.columns:
            if df_clean[col].dtype == 'datetime64[ns]':
                df_clean[col] = df_clean[col].dt.strftime('%Y-%m-%d')
        
        # Insert data row by row to handle any data type issues
        for index, row in df_clean.iterrows():
            placeholders = ', '.join(['?' for _ in row])
            columns_str = ", ".join([f'"{col}"' for col in clean_columns])
            insert_sql = f'INSERT INTO superstore ({columns_str}) VALUES ({placeholders})'
            
            try:
                cursor.execute(insert_sql, tuple(row))
            except Exception as e:
                logger.warning(f"Error inserting row {index}: {e}")
                logger.warning(f"Row data: {row.to_dict()}")
                continue
        
        # Commit changes
        conn.commit()
        
        # Verify data was inserted
        cursor.execute("SELECT COUNT(*) FROM superstore")
        count = cursor.fetchone()[0]
        logger.info(f"Successfully inserted {count} rows into superstore table")
        
        # Show sample data
        cursor.execute("SELECT * FROM superstore LIMIT 3")
        sample_data = cursor.fetchall()
        logger.info(f"Sample data (first 3 rows): {sample_data}")
        
        conn.close()
        logger.info("Superstore data import completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error importing superstore data: {e}")
        return False

def create_superstore_table_only(db_path: str = "src/database/superstore.db"):
    """
    Create only the superstore table structure without importing data.
    This is useful for testing or when you want to create the table manually.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create a basic superstore table structure
        create_table_sql = '''
        CREATE TABLE IF NOT EXISTS superstore (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            "Row_ID" INTEGER,
            "Order_ID" TEXT,
            "Order_Date" TEXT,
            "Ship_Date" TEXT,
            "Ship_Mode" TEXT,
            "Customer_ID" TEXT,
            "Customer_Name" TEXT,
            "Segment" TEXT,
            "Country" TEXT,
            "City" TEXT,
            "State" TEXT,
            "Postal_Code" INTEGER,
            "Region" TEXT,
            "Product_ID" TEXT,
            "Category" TEXT,
            "Sub_Category" TEXT,
            "Product_Name" TEXT,
            "Sales" REAL,
            "Quantity" INTEGER,
            "Discount" REAL,
            "Profit" REAL
        )
        '''
        
        cursor.execute(create_table_sql)
        conn.commit()
        conn.close()
        
        logger.info("Basic superstore table structure created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error creating superstore table: {e}")
        return False

if __name__ == "__main__":
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    
    # Set paths relative to project root
    db_path = project_root / "src" / "database" / "superstore.db"
    excel_path = project_root / "data" / "datasets" / "superstore_dataset.xls"
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Database path: {db_path}")
    logger.info(f"Excel path: {excel_path}")
    
    # Try to import the data
    if import_superstore_data(str(db_path), str(excel_path)):
        logger.info("✅ Superstore data import successful!")
    else:
        logger.warning("⚠️ Superstore data import failed, creating basic table structure...")
        create_superstore_table_only(str(db_path)) 