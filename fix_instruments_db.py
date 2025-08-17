#!/usr/bin/env python3
"""
Script to fix instruments database
"""
import duckdb
import os

def fix_database():
    print("🔧 Fixing instruments database...")
    
    try:
        # Connect to database
        conn = duckdb.connect('instruments.db')
        
        # Drop existing tables
        print("🗑️ Dropping existing tables...")
        conn.execute("DROP TABLE IF EXISTS instruments")
        conn.execute("DROP TABLE IF EXISTS instruments_metadata")
        
        # Recreate tables with proper structure
        print("🏗️ Recreating tables...")
        
        # Create metadata table
        conn.execute("""
            CREATE TABLE instruments_metadata (
                id INTEGER PRIMARY KEY,
                last_download TIMESTAMP,
                file_size INTEGER,
                total_instruments INTEGER,
                nse_count INTEGER,
                bse_count INTEGER,
                nfo_count INTEGER,
                bfo_count INTEGER
            )
        """)
        
        # Create instruments table with auto-increment
        conn.execute("""
            CREATE TABLE instruments (
                id INTEGER PRIMARY KEY,
                token VARCHAR,
                short_name VARCHAR,
                series VARCHAR,
                company_name VARCHAR,
                exchange_code VARCHAR,
                instrument_type VARCHAR,
                isin_code VARCHAR,
                lot_size INTEGER,
                tick_size DECIMAL(10,2),
                face_value DECIMAL(10,2),
                permitted_to_trade BOOLEAN,
                search_text VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        conn.execute("CREATE INDEX idx_search_text ON instruments(search_text)")
        conn.execute("CREATE INDEX idx_exchange_short_name ON instruments(exchange_code, short_name)")
        
        conn.commit()
        print("✅ Database structure fixed!")
        
        # Check table structure
        print("\n📋 Table structure:")
        print(conn.execute("DESCRIBE instruments").fetchall())
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error fixing database: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_database()
