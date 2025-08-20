# 🚀 Trading System - GitHub Codespaces

## Quick Deploy

1. **Click the green "Code" button** on your GitHub repository
2. **Select "Codespaces" tab**
3. **Click "Create codespace on main"**
4. **Wait for setup** (2-3 minutes)
5. **Run the app**: `python run_server.py`
6. **Open**: http://localhost:8000

## What's Included

✅ **Automatic Setup**
- Python 3.11 environment
- All dependencies installed
- Database initialization
- Default configuration created

✅ **Development Tools**
- VS Code with Python extensions
- Auto-formatting and linting
- Git integration
- Terminal access

✅ **Trading Features**
- Demo mode (safe simulation)
- Real trading mode (with API credentials)
- Web dashboard
- Real-time market data
- Portfolio management

## Security

🔐 **API Credentials**
- Edit `trading_config.json` to add your credentials
- Never commit this file (already in .gitignore)
- Demo mode works without credentials

## Commands

```bash
# Start the application
python run_server.py

# Test market data
python test_market_watch.py

# Populate instruments database
python populate_instruments.py

# Run fake trading only
python fake_trading.py
```

## Access Points

- **Main App**: http://localhost:8000
- **Dashboard**: http://localhost:8000/dashboard
- **API Docs**: http://localhost:8000/docs

## Support

📚 **Documentation**: See `CODESPACE.md` for detailed guide
🐛 **Issues**: Check logs in `logs/` directory
💬 **Help**: Create GitHub issue with details

---

**Happy Trading! 📈**
