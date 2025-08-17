#!/usr/bin/env python3
"""
Check lot sizes from instruments manager
"""
from instruments_manager import InstrumentsManager

def check_lot_sizes():
    try:
        mgr = InstrumentsManager()
        
        # Check CESC options
        print("🔍 CESC Options:")
        cesc_results = mgr.search_instruments("CESC", limit=10)
        cesc_options = [r for r in cesc_results if r['exchange_code'] == 'NFO' and r['option_type'] in ['CE', 'PE']]
        
        for option in cesc_options[:5]:
            print(f"  {option['short_name']} {option['option_type']} {option['strike_price']} - Lot: {option['lot_size']}")
        
        # Check different stocks
        print("\n🔍 Different Stocks Lot Sizes:")
        stocks_to_check = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'CESC', 'RELIANCE', 'TCS']
        
        for stock in stocks_to_check:
            results = mgr.search_instruments(stock, limit=5)
            options = [r for r in results if r['exchange_code'] == 'NFO' and r['option_type'] in ['CE', 'PE']]
            
            if options:
                option = options[0]
                print(f"  {stock}: Lot Size {option['lot_size']}")
            else:
                print(f"  {stock}: No options found")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    check_lot_sizes()
