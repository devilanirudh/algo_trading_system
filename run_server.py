#!/usr/bin/env python3
"""
Run script for Trading System Server
Run this from within the trading_system directory
"""

import uvicorn
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import app

if __name__ == "__main__":
    print("🚀 Starting Trading System Server...")
    print("📊 Demo mode is enabled by default")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📱 Dashboard will be available at: http://localhost:8000/dashboard")
    print("\n" + "="*50)
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
