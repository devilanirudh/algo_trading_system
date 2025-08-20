#!/bin/bash

echo "🚀 Trading System Codespace Setup Complete!"

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

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

# Create logs directory
mkdir -p logs

# Run setup test
echo ""
echo "🧪 Running setup verification..."
python test_codespace_setup.py

echo ""
echo "🎉 Setup Complete! Your Trading System is ready."
echo ""
echo "📋 Quick Start:"
echo "1. Configure API credentials: nano trading_config.json"
echo "2. Start the app: python run_server.py"
echo "3. Open: http://localhost:8000"
echo "4. Dashboard: http://localhost:8000/dashboard"
echo ""
echo "📚 For more info, see: CODESPACE.md"
echo ""
