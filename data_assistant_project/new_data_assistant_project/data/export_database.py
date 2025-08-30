#!/usr/bin/env python3
"""
Script to export PostgreSQL database tables to CSV files.
"""

import psycopg2
import pandas as pd
import os
from datetime import datetime

# Database connection parameters
DB_CONFIG = {
    'host': '34.59.248.159',
    'port': 5432,
    'database': 'superstore',
    'user': 'postgres',
    'password': 'RHGAgo4<C4fyr',
    'sslmode': 'require'
}

def export_table_to_csv(table_name, output_dir='.'):
    """Export a PostgreSQL table to CSV file."""
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Query all data from the table
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql_query(query, conn)
        
        # Create CSV filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = os.path.join(output_dir, f"{table_name}_{timestamp}.csv")
        
        # Export to CSV
        df.to_csv(csv_filename, index=False)
        
        conn.close()
        
        print(f"✅ Exported {table_name}: {len(df)} rows -> {csv_filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error exporting {table_name}: {e}")
        return False

def list_all_tables():
    """List all tables in the database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        return tables
        
    except Exception as e:
        print(f"❌ Error listing tables: {e}")
        return []

def main():
    """Main export function."""
    print("🚀 Starting PostgreSQL database export...")
    
    # Get current directory
    output_dir = os.getcwd()
    print(f"📁 Output directory: {output_dir}")
    
    # List all tables
    print("\n📋 Discovering tables...")
    tables = list_all_tables()
    
    if not tables:
        print("❌ No tables found!")
        return
    
    print(f"Found {len(tables)} tables: {', '.join(tables)}")
    
    # Export each table
    print("\n📤 Exporting tables...")
    successful_exports = 0
    
    for table in tables:
        if export_table_to_csv(table, output_dir):
            successful_exports += 1
    
    print(f"\n✅ Export completed: {successful_exports}/{len(tables)} tables exported successfully")
    
    # List generated files
    print("\n📁 Generated files:")
    csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
    for csv_file in sorted(csv_files):
        file_path = os.path.join(output_dir, csv_file)
        file_size = os.path.getsize(file_path)
        print(f"  - {csv_file} ({file_size:,} bytes)")

if __name__ == "__main__":
    main()

