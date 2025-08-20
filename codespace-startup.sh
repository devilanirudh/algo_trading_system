#!/bin/bash

echo "🚀 Starting Trading System Codespace Setup..."

# Navigate to trading_system directory
cd /workspaces/nse_arb/trading_system

# Install dependencies if requirements.txt exists
if [ -f "../requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    pip install -r ../requirements.txt
fi

# Create default config if it doesn't exist
if [ ! -f "trading_config.json" ]; then
    echo "⚙️  Creating default trading_config.json..."
    cp trading_config.template.json trading_config.json
    echo "⚠️  Please update trading_config.json with your API credentials"
fi

# Initialize databases
echo "🗄️  Initializing databases..."
python -c "
try:
    from historical_db import get_historical_db
    db = get_historical_db()
    print('✅ Historical database initialized')
except Exception as e:
    print(f'⚠️  Historical database issue: {e}')
"

# Create logs directory if it doesn't exist
mkdir -p logs

echo ""
echo "🎉 Trading System Codespace is ready!"
echo ""
echo "📋 Quick Start:"
echo "1. Configure your API credentials in trading_config.json"
echo "2. Run: python run_server.py"
echo "3. Open: http://localhost:8000"
echo "4. Dashboard: http://localhost:8000/dashboard"
echo ""
echo "🔧 Available commands:"
echo "  - python run_server.py              # Start trading system"
echo "  - python populate_instruments.py    # Populate instruments DB"
echo "  - python test_market_watch.py       # Test market data"
echo "  - python fake_trading.py            # Run fake trading system"
echo ""

# Make the script executable
chmod +x codespace-startup.sh
