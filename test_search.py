#!/usr/bin/env python3
"""
Test search functionality
"""
from instruments_manager import InstrumentsManager

def test_search():
    mgr = InstrumentsManager()
    
    # Test different search queries
    queries = [
        "CESC",
        "CESC CE",
        "CESC CE 200",
        "200",
        "CE"
    ]
    
    for query in queries:
        print(f"\n🔍 Searching for: '{query}'")
        results = mgr.search_instruments(query, limit=5)
        print(f"Found {len(results)} results:")
        
        for result in results:
            print(f"  {result['short_name']} ({result['exchange_code']}) - {result['company_name']}")
            if result['exchange_code'] in ['NFO', 'BFO']:
                print(f"    Strike: {result['strike_price']}, Option: {result['option_type']}, Expiry: {result['expiry_date']}")

if __name__ == "__main__":
    test_search()
