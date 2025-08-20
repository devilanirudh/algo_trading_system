# Trading System - GitHub Codespaces Deployment Guide

## 🚀 Quick Start

### 1. Create a Codespace
1. Go to your GitHub repository
2. Click the green "Code" button
3. Select "Codespaces" tab
4. Click "Create codespace on main"

### 2. Wait for Setup
The Codespace will automatically:
- Install Python 3.11
- Install all dependencies from `requirements.txt`
- Set up the development environment
- Initialize databases
- Create default configuration files

### 3. Configure API Credentials
```bash
# Edit the trading configuration
nano trading_config.json
```

Update with your actual API credentials:
```json
{
  "api": {
    "api_key": "your_api_key_here",
    "api_secret": "your_api_secret_here",
    "session_token": "your_session_token_here"
  }
}
```

### 4. Run the Application
```bash
python run_server.py
```

### 5. Access the Application
- **Main App**: http://localhost:8000
- **Dashboard**: http://localhost:8000/dashboard
- **API Docs**: http://localhost:8000/docs

## 🔧 Available Commands

### Core Application
```bash
python run_server.py              # Start the main trading system
python fake_trading.py            # Run fake trading system only
```

### Database Management
```bash
python populate_instruments.py    # Populate instruments database
python fix_instruments_db.py      # Fix database issues
```

### Testing
```bash
python test_market_watch.py       # Test market data functionality
python test_funds_init.py         # Test funds initialization
python test_imports.py            # Test all imports
```

### Utilities
```bash
python check_lot_sizes.py         # Check lot sizes for instruments
python debug_search.py            # Debug search functionality
```

## 📊 Features Available in Codespaces

### ✅ Demo Mode (Default)
- Safe simulation with DuckDB backend
- Virtual funds and portfolio management
- Complete transaction history
- No real money involved

### ✅ Real Trading Mode
- Live market data and trading
- Real portfolio management
- Requires valid API credentials
- **Use with extreme caution**

### ✅ Web Interface
- Modern Bootstrap 5 UI
- Real-time data updates
- Interactive charts
- Mobile responsive design

## 🔐 Security Notes

### API Credentials
- **Never commit** `trading_config.json` to version control
- The file is already in `.gitignore`
- Use GitHub Secrets for production deployments
- Rotate credentials regularly

### Demo Mode Safety
- Demo mode is enabled by default
- No real money is involved
- Perfect for testing and development
- All data is stored locally in DuckDB

## 🛠️ Troubleshooting

### Port Forwarding Issues
If you can't access the application:
1. Check the "Ports" tab in VS Code
2. Ensure port 8000 is forwarded
3. Click "Open in Browser" on port 8000

### Database Issues
```bash
# Reinitialize databases
python fix_instruments_db.py
python populate_instruments.py
```

### Dependency Issues
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Memory Issues
- Codespaces have limited memory
- Close unnecessary files and terminals
- Restart the Codespace if needed

## 📈 Monitoring and Logs

### Application Logs
```bash
# View real-time logs
tail -f logs/apiLogs_*.log
tail -f logs/websocketLogs_*.log
```

### Database Files
- `instruments.db` - Stock instruments data
- `historical_data.db` - Historical price data
- `fake_trading.db` - Demo trading data

### CSV Exports
- Tick data: `logs/ws_ticks_*.csv`
- Trading data: Exported via web interface

## 🎯 Best Practices

### Development Workflow
1. Always work in demo mode first
2. Test thoroughly before switching to real mode
3. Use version control for code changes
4. Keep API credentials secure

### Performance
- Close unused terminals and files
- Monitor memory usage
- Restart Codespace if performance degrades
- Use appropriate machine size for your needs

### Data Management
- Export important data regularly
- Backup configuration files
- Monitor database sizes
- Clean up old log files

## 🔄 Codespace Lifecycle

### Starting
- Automatic dependency installation
- Database initialization
- Configuration file creation

### Running
- Application runs on port 8000
- Auto-reload enabled for development
- Logs written to `logs/` directory

### Stopping
- Save all important data
- Export any needed files
- Stop the application gracefully

## 📞 Support

If you encounter issues:
1. Check the logs in `logs/` directory
2. Review this documentation
3. Check GitHub Issues for known problems
4. Create a new issue with detailed information

---

**Happy Trading! 🚀📈**
