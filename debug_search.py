#!/usr/bin/env python3
"""
Debug search functionality
"""
import duckdb
import os

def debug_search():
    db_path = "instruments.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return
    
    try:
        conn = duckdb.connect(db_path)
        
        # Search for CESC instruments
        print("🔍 Searching for CESC instruments:")
        cesc_instruments = conn.execute("""
            SELECT short_name, company_name, exchange_code, instrument_type, 
                   expiry_date, strike_price, option_type, search_text
            FROM instruments 
            WHERE short_name LIKE '%CESC%' OR company_name LIKE '%CESC%'
            LIMIT 10
        """).fetchall()
        
        for instrument in cesc_instruments:
            print(f"  {instrument[0]} ({instrument[2]}) - {instrument[1]}")
            print(f"    Type: {instrument[3]}, Expiry: {instrument[4]}, Strike: {instrument[5]}, Option: {instrument[6]}")
            print(f"    Search text: {instrument[7]}")
            print()
        
        # Search for instruments with strike price 200
        print("🔍 Searching for instruments with strike price 200:")
        strike_200 = conn.execute("""
            SELECT short_name, company_name, exchange_code, instrument_type, 
                   expiry_date, strike_price, option_type
            FROM instruments 
            WHERE strike_price = 200
            LIMIT 5
        """).fetchall()
        
        for instrument in strike_200:
            print(f"  {instrument[0]} ({instrument[2]}) - Strike: {instrument[5]}")
        
        # Search for CE options
        print("\n🔍 Searching for CE options:")
        ce_options = conn.execute("""
            SELECT short_name, company_name, exchange_code, instrument_type, 
                   expiry_date, strike_price, option_type
            FROM instruments 
            WHERE option_type = 'CE'
            LIMIT 5
        """).fetchall()
        
        for instrument in ce_options:
            print(f"  {instrument[0]} ({instrument[2]}) - {instrument[6]}")
        
        # Test the current search logic
        print("\n🔍 Testing search for 'CESC CE 200':")
        search_query = "CESC CE 200"
        search_results = conn.execute("""
            SELECT short_name, company_name, exchange_code, instrument_type, 
                   expiry_date, strike_price, option_type, search_text
            FROM instruments 
            WHERE search_text LIKE ?
            LIMIT 5
        """, [f"%{search_query.lower()}%"]).fetchall()
        
        print(f"Found {len(search_results)} results:")
        for result in search_results:
            print(f"  {result[0]} ({result[2]}) - {result[1]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    debug_search()
