#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all imports"""
    try:
        print("Testing imports...")
        
        # Test core imports
        from core import TradingSystem
        print("✅ TradingSystem imported successfully")
        
        from api import BreezeAPI
        print("✅ BreezeAPI imported successfully")
        
        from utils import TradingUtils, DataProcessor, ConfigManager
        print("✅ Utils imported successfully")
        
        from managers import OrderManager, PortfolioManager, MarketDataManager
        print("✅ Managers imported successfully")
        
        from fake_trading import FakeTradingSystem
        print("✅ FakeTradingSystem imported successfully")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n🚀 Ready to run the server!")
    else:
        print("\n🔧 Please fix import issues before running the server.")
