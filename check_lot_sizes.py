#!/usr/bin/env python3
"""
Check lot sizes from the security master database
"""
import duckdb
import os

def check_lot_sizes():
    db_path = "instruments.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return
    
    try:
        conn = duckdb.connect(db_path)
        
        # Check CESC options specifically
        print("🔍 CESC Options Lot Sizes:")
        cesc_options = conn.execute("""
            SELECT short_name, option_type, strike_price, lot_size, expiry_date
            FROM instruments 
            WHERE short_name = 'CESC' AND exchange_code = 'NFO' AND option_type IN ('CE', 'PE')
            ORDER BY strike_price, option_type
            LIMIT 10
        """).fetchall()
        
        for option in cesc_options:
            print(f"  {option[0]} {option[1]} {option[2]} - Lot: {option[3]} - Expiry: {option[4]}")
        
        # Check different stocks and their lot sizes
        print("\n🔍 Different Stocks and Their Lot Sizes:")
        stock_lots = conn.execute("""
            SELECT DISTINCT short_name, lot_size, option_type, strike_price
            FROM instruments 
            WHERE exchange_code = 'NFO' AND option_type IN ('CE', 'PE')
            ORDER BY short_name, lot_size
            LIMIT 20
        """).fetchall()
        
        for stock in stock_lots:
            print(f"  {stock[0]} {stock[2]} {stock[3]} - Lot: {stock[1]}")
        
        # Check lot size distribution
        print("\n📊 Lot Size Distribution:")
        lot_distribution = conn.execute("""
            SELECT lot_size, COUNT(*) as count
            FROM instruments 
            WHERE exchange_code = 'NFO' AND option_type IN ('CE', 'PE')
            GROUP BY lot_size
            ORDER BY lot_size
        """).fetchall()
        
        for lot in lot_distribution:
            print(f"  Lot Size {lot[0]}: {lot[1]} instruments")
        
        # Check specific popular stocks
        popular_stocks = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'CESC', 'RELIANCE', 'TCS', 'INFY']
        print(f"\n🔍 Popular Stocks Lot Sizes:")
        for stock in popular_stocks:
            stock_lot = conn.execute("""
                SELECT DISTINCT short_name, lot_size
                FROM instruments 
                WHERE short_name = ? AND exchange_code = 'NFO' AND option_type IN ('CE', 'PE')
                LIMIT 1
            """, [stock]).fetchone()
            
            if stock_lot:
                print(f"  {stock_lot[0]}: Lot Size {stock_lot[1]}")
            else:
                print(f"  {stock}: Not found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    check_lot_sizes()
