#!/usr/bin/env python3
"""
Test script to verify Codespace setup
Run this to check if all dependencies and configurations are working
"""

import sys
import os

def test_imports():
    """Test if all required packages can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("✅ Uvicorn imported successfully")
    except ImportError as e:
        print(f"❌ Uvicorn import failed: {e}")
        return False
    
    try:
        import pandas
        print("✅ Pandas imported successfully")
    except ImportError as e:
        print(f"❌ Pandas import failed: {e}")
        return False
    
    try:
        import numpy
        print("✅ NumPy imported successfully")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    try:
        import duckdb
        print("✅ DuckDB imported successfully")
    except ImportError as e:
        print(f"❌ DuckDB import failed: {e}")
        return False
    
    try:
        import breeze_connect
        print("✅ Breeze Connect imported successfully")
    except ImportError as e:
        print(f"❌ Breeze Connect import failed: {e}")
        return False
    
    return True

def test_config_files():
    """Test if configuration files exist"""
    print("\n📁 Testing configuration files...")
    
    config_files = [
        "trading_config.json",
        "trading_config.template.json",
        "requirements.txt"
    ]
    
    all_exist = True
    for file in config_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            all_exist = False
    
    return all_exist

def test_database_files():
    """Test if database files exist or can be created"""
    print("\n🗄️ Testing database files...")
    
    try:
        from historical_db import get_historical_db
        db = get_historical_db()
        print("✅ Historical database initialized")
    except Exception as e:
        print(f"⚠️ Historical database issue: {e}")
    
    # Check if other database files exist
    db_files = [
        "instruments.db",
        "fake_trading.db",
        "historical_data.db"
    ]
    
    for file in db_files:
        if os.path.exists(file):
            size = os.path.getsize(file) / (1024 * 1024)  # MB
            print(f"✅ {file} exists ({size:.1f} MB)")
        else:
            print(f"⚠️ {file} doesn't exist (will be created on first run)")

def test_server_import():
    """Test if the server can be imported"""
    print("\n🚀 Testing server import...")
    
    try:
        from server import app
        print("✅ Server app imported successfully")
    except Exception as e:
        print(f"❌ Server import failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🧪 Trading System Codespace Setup Test")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test config files
    config_ok = test_config_files()
    
    # Test database
    test_database_files()
    
    # Test server
    server_ok = test_server_import()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"  Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"  Config: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"  Server: {'✅ PASS' if server_ok else '❌ FAIL'}")
    
    if imports_ok and config_ok and server_ok:
        print("\n🎉 All tests passed! Your Codespace is ready.")
        print("\n🚀 To start the application:")
        print("   python run_server.py")
        print("\n🌐 Access at: http://localhost:8000")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
