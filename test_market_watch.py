#!/usr/bin/env python3
"""
Test market watch persistence
"""
from fake_trading import FakeTradingSystem

def test_market_watch():
    print("🧪 Testing Market Watch Persistence...")
    
    try:
        # Initialize fake trading system
        fake_system = FakeTradingSystem()
        
        # Get initial symbols
        print("\n📋 Initial market watch symbols:")
        symbols = fake_system.get_market_watch_symbols()
        for symbol in symbols:
            print(f"  - {symbol['symbol']} ({symbol['exchange']})")
        
        # Add a test symbol
        print("\n➕ Adding test symbol...")
        success = fake_system.add_market_watch_symbol("TEST", "NSE")
        if success:
            print("  ✅ Added TEST (NSE)")
        else:
            print("  ❌ Failed to add TEST (NSE)")
        
        # Get symbols again
        print("\n📋 Market watch symbols after adding:")
        symbols = fake_system.get_market_watch_symbols()
        for symbol in symbols:
            print(f"  - {symbol['symbol']} ({symbol['exchange']})")
        
        # Remove the test symbol
        print("\n➖ Removing test symbol...")
        success = fake_system.remove_market_watch_symbol("TEST", "NSE")
        if success:
            print("  ✅ Removed TEST (NSE)")
        else:
            print("  ❌ Failed to remove TEST (NSE)")
        
        # Get symbols again
        print("\n📋 Market watch symbols after removing:")
        symbols = fake_system.get_market_watch_symbols()
        for symbol in symbols:
            print(f"  - {symbol['symbol']} ({symbol['exchange']})")
        
        print("\n✅ Market watch persistence test completed!")
        
    except Exception as e:
        print(f"❌ Error testing market watch: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_market_watch()
