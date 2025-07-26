import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Setze Standardpfade für die Datenbank und die Excel-Datei
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "superstore.db")
EXCEL_PATH = os.path.join(BASE_DIR, "..", "..", "data", "datasets", "superstore_dataset.xls")


def create_superstore_database(db_path: str = DB_PATH, excel_path: str = EXCEL_PATH):
    """
    Create SQLite database with Superstore dataset.
    Can either load from Excel or generate sample data.
    """
    
    conn = sqlite3.connect(db_path)
    if excel_path and os.path.exists(excel_path):
        # Load from existing Excel
        print(f"Loading data from {excel_path}...")
        df = pd.read_excel(excel_path)
    else:
        # Generate sample Superstore-like data
        print("format not supported, generating sample data...")
        df = generate_sample_superstore_data()

    # Clean and prepare data
    df = prepare_superstore_data(df)
    
    # Create table
    df.to_sql('superstore', conn, if_exists='replace', index=False)
    
    # Create indexes for better performance
    create_indexes(conn)
    
    # Verify data
    verify_database(conn)
    
    conn.close()
    print(f"Database created successfully: {db_path}")
    print(f"Total records: {len(df)}")

def generate_sample_superstore_data(n_records: int = 10000):
    """Generate sample data similar to Tableau Superstore dataset."""
    
    # Sample data for realistic generation
    regions = ['East', 'West', 'Central', 'South']
    states = {
        'East': ['New York', 'Pennsylvania', 'Ohio', 'Massachusetts', 'Connecticut'],
        'West': ['California', 'Washington', 'Oregon', 'Nevada', 'Arizona'],
        'Central': ['Texas', 'Illinois', 'Michigan', 'Wisconsin', 'Minnesota'],
        'South': ['Florida', 'Georgia', 'North Carolina', 'Virginia', 'Tennessee']
    }
    
    categories = ['Technology', 'Furniture', 'Office Supplies']
    sub_categories = {
        'Technology': ['Phones', 'Computers', 'Tablets', 'Accessories'],
        'Furniture': ['Chairs', 'Tables', 'Bookcases', 'Storage'],
        'Office Supplies': ['Paper', 'Binders', 'Pens', 'Supplies']
    }
    
    segments = ['Consumer', 'Corporate', 'Home Office']
    ship_modes = ['Standard Class', 'Second Class', 'First Class', 'Same Day']
    
    # Generate customer names
    first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Lisa', 'Chris', 'Amy', 'Tom', 'Kate']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']
    
    data = []
    
    for i in range(n_records):
        region = random.choice(regions)
        state = random.choice(states[region])
        city = f"{state} City {random.randint(1, 5)}"
        
        category = random.choice(categories)
        sub_category = random.choice(sub_categories[category])
        
        # Generate dates
        order_date = datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1460))  # 4 years
        ship_date = order_date + timedelta(days=random.randint(1, 14))
        
        # Generate financial data
        sales = round(random.uniform(10, 5000), 2)
        quantity = random.randint(1, 10)
        discount = round(random.uniform(0, 0.8), 2)
        profit = round(sales * random.uniform(-0.2, 0.4), 2)  # Can be negative
        
        customer_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        
        data.append({
            'Row ID': i + 1,
            'Order ID': f"US-{2020 + i//2500}-{random.randint(100000, 999999)}",
            'Order Date': order_date.strftime('%Y-%m-%d'),
            'Ship Date': ship_date.strftime('%Y-%m-%d'),
            'Ship Mode': random.choice(ship_modes),
            'Customer ID': f"CG-{random.randint(10000, 99999)}",
            'Customer Name': customer_name,
            'Segment': random.choice(segments),
            'Country': 'United States',
            'City': city,
            'State': state,
            'Postal Code': f"{random.randint(10000, 99999)}",
            'Region': region,
            'Product ID': f"OFF-{category[:2].upper()}-{random.randint(1000000, 9999999)}",
            'Category': category,
            'Sub-Category': sub_category,
            'Product Name': f"{sub_category} Product {random.randint(1, 100)}",
            'Sales': sales,
            'Quantity': quantity,
            'Discount': discount,
            'Profit': profit
        })
    
    return pd.DataFrame(data)

def prepare_superstore_data(df):
    """Clean and prepare Superstore data for database insertion."""
    
    # Ensure date columns are properly formatted
    date_columns = ['Order Date', 'Ship Date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d')
    
    # Clean numeric columns
    numeric_columns = ['Sales', 'Quantity', 'Discount', 'Profit']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Handle missing values
    df = df.fillna({
        'Sales': 0,
        'Quantity': 1,
        'Discount': 0,
        'Profit': 0
    })
    
    # Remove any completely empty rows
    df = df.dropna(how='all')
    
    return df

def create_indexes(conn):
    """Create indexes for better query performance."""
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_region ON superstore(Region);",
        "CREATE INDEX IF NOT EXISTS idx_category ON superstore(Category);",
        "CREATE INDEX IF NOT EXISTS idx_order_date ON superstore([Order Date]);",
        "CREATE INDEX IF NOT EXISTS idx_customer ON superstore([Customer Name]);",
        "CREATE INDEX IF NOT EXISTS idx_product ON superstore([Product Name]);",
        "CREATE INDEX IF NOT EXISTS idx_segment ON superstore(Segment);"
    ]
    
    cursor = conn.cursor()
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    conn.commit()
    print("Indexes created successfully.")

def verify_database(conn):
    """Verify database contents and structure."""
    
    cursor = conn.cursor()
    
    # Check table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")
    
    # Check column info
    cursor.execute("PRAGMA table_info(superstore);")
    columns = cursor.fetchall()
    print(f"Columns: {len(columns)}")
    
    # Basic statistics
    cursor.execute("SELECT COUNT(*) FROM superstore;")
    count = cursor.fetchone()[0]
    print(f"Total records: {count}")
    
    cursor.execute("SELECT MIN([Order Date]), MAX([Order Date]) FROM superstore;")
    date_range = cursor.fetchone()
    print(f"Date range: {date_range[0]} to {date_range[1]}")
    
    cursor.execute("SELECT Region, COUNT(*) FROM superstore GROUP BY Region;")
    regions = cursor.fetchall()
    print(f"Records by region: {regions}")

def test_database_queries(db_path: str = "superstore.db"):
    """Test various SQL queries that will be used in the thesis."""
    
    conn = sqlite3.connect(db_path)
    
    test_queries = [
        # Simple queries (Complexity 1-2)
        "SELECT * FROM superstore LIMIT 10;",
        "SELECT Region, COUNT(*) FROM superstore GROUP BY Region;",
        
        # Medium complexity (Complexity 3)
        "SELECT Category, SUM(Sales) as Total_Sales FROM superstore GROUP BY Category ORDER BY Total_Sales DESC;",
        
        # Higher complexity (Complexity 4-5)
        """SELECT Region, Category, 
           SUM(Sales) as Total_Sales,
           AVG(Profit) as Avg_Profit,
           RANK() OVER (ORDER BY SUM(Sales) DESC) as Sales_Rank
           FROM superstore 
           GROUP BY Region, Category 
           ORDER BY Total_Sales DESC;""",
        
        # Window functions
        """SELECT [Customer Name], Sales, 
           AVG(Sales) OVER (PARTITION BY Region) as Region_Avg_Sales,
           Sales - AVG(Sales) OVER (PARTITION BY Region) as Sales_Diff
           FROM superstore 
           ORDER BY Sales DESC 
           LIMIT 20;"""
    ]
    
    print("\nTesting sample queries:")
    for i, query in enumerate(test_queries, 1):
        try:
            df = pd.read_sql_query(query, conn)
            print(f"Query {i}: Success - {len(df)} rows returned")
        except Exception as e:
            print(f"Query {i}: Error - {e}")
    
    conn.close()

# Example usage for your thesis
if __name__ == "__main__":
    # Option 1: Create database with generated sample data
    create_superstore_database("data_assistant_project/src/database/superstore.db", excel_path="data_assistant_project/data/datasets/superstore_dataset.xls")
    
    # Option 2: If you have the actual Kaggle CSV
    # create_superstore_database("superstore.db", "path/to/your/superstore.csv")
    
    # Test the database
    test_database_queries("data_assistant_project/src/database/superstore.db")
    
    print("\nDatabase setup complete! You can now use this with your ReAct and CLT/CFT agents.")
