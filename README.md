# Comprehensive Trading System

A complete trading platform built with FastAPI, featuring real-time market data, portfolio management, and a demo/real trading toggle system.

## 🚀 Features

### ✅ Complete Breeze Connect Integration
- **All APIs Implemented**: Every Breeze Connect API function is fully implemented
- **Real-time Data**: Live market quotes and streaming data
- **Portfolio Management**: Holdings, positions, and funds tracking
- **Order Management**: Place, modify, cancel orders
- **Historical Data**: OHLCV data with technical indicators
- **GTT Orders**: Good Till Trigger order management
- **Calculators**: Margin and limit calculators

### 🎮 Demo/Real Trading Toggle
- **Demo Mode (Default)**: Safe simulation with DuckDB backend
- **Real Mode**: Live trading with actual money (use with caution)
- **Toggle Switch**: Easy switching between modes
- **Visual Indicators**: Clear mode indicators throughout the UI

### 💾 DuckDB Backend
- **Fake Trading System**: Complete simulation with DuckDB
- **Funds Management**: Virtual cash and margin tracking
- **Ledger System**: Complete transaction history
- **Holdings Tracking**: Portfolio simulation
- **CSV Export**: Export all data to CSV files

### 📊 Comprehensive Frontend
- **Modern UI**: Bootstrap 5 with responsive design
- **Real-time Updates**: Auto-refresh every 30 seconds
- **Interactive Charts**: Chart.js for historical data visualization
- **Export Functionality**: CSV export for all data
- **Mobile Responsive**: Works on all devices

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- pip

### Setup
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd nse_arb
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the system**
   ```bash
   python run_trading_system.py
   ```

4. **Access the application**
   - Open: http://localhost:8000
   - Dashboard: http://localhost:8000/dashboard

## 📋 API Endpoints

### Authentication
- `POST /api/auth/login` - Login with API credentials

### Portfolio Management
- `GET /api/portfolio/summary` - Portfolio summary
- `GET /api/portfolio/holdings` - Real holdings
- `GET /api/fake/holdings` - Demo holdings
- `GET /api/fake/funds` - Demo funds

### Market Data
- `GET /api/market/quotes?symbol=RELIANCE` - Get quotes
- `GET /api/market/option-chain` - Option chain data
- `GET /api/historical/data` - Historical data

### Order Management
- `POST /api/orders/place` - Place real order
- `POST /api/fake/orders` - Place demo order
- `GET /api/orders/list` - Real orders
- `GET /api/fake/orders` - Demo orders

### Trading System
- `GET /api/fake/ledger` - Transaction ledger
- `POST /api/fake/export/{table}` - Export data to CSV
- `POST /api/fake/orders/{id}/execute` - Execute demo order

## 🎯 Usage Guide

### 1. Login
1. Visit http://localhost:8000
2. Enter your Breeze Connect API credentials:
   - API Key
   - API Secret
   - Session Token (obtained from login URL)

### 2. Dashboard Overview
- **Portfolio Summary**: View total value, P&L, cash balance
- **Market Watch**: Live quotes for popular stocks
- **Recent Orders**: Latest order history
- **Mode Indicator**: Clear demo/real mode display

### 3. Trading Modes

#### Demo Mode (Default)
- ✅ Safe simulation environment
- ✅ Virtual funds (₹10,00,000 starting balance)
- ✅ Complete transaction tracking
- ✅ No real money involved
- ✅ Perfect for testing strategies

#### Real Mode
- ⚠️ Live trading with real money
- ⚠️ Actual order execution
- ⚠️ Real portfolio impact
- ⚠️ Use with extreme caution

### 4. Features by Section

#### Overview
- Portfolio summary cards
- Market watch table
- Recent orders
- Mode toggle

#### Portfolio
- Holdings table with P&L
- Export functionality
- Real vs demo data display

#### Orders
- Order history
- Order status tracking
- Cancel/modify orders
- Export order data

#### Market Data
- Quote search
- Detailed quote information
- Quick trade buttons
- Add to watchlist

#### Trading
- Order placement form
- Order preview
- Real-time validation
- Mode-aware execution

#### Ledger
- Complete transaction history
- Transaction types
- Export functionality
- Demo-only feature

#### Historical Data
- OHLCV data retrieval
- Interactive charts
- Technical indicators
- CSV export

#### GTT Orders
- Good Till Trigger orders
- Order management
- Status tracking

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Set default API credentials
BREEZE_API_KEY=your_api_key
BREEZE_API_SECRET=your_api_secret
BREEZE_SESSION_TOKEN=your_session_token
```

### Database Configuration
- **Demo Mode**: Uses DuckDB (`fake_trading.db`)
- **Real Mode**: Uses Breeze Connect APIs directly

## 📊 Data Export

### Available Exports
- **Portfolio Holdings**: CSV export of current holdings
- **Order History**: Complete order history
- **Transaction Ledger**: All transactions
- **Historical Data**: OHLCV data for any symbol

### Export Format
```csv
Date,Symbol,Action,Quantity,Price,Total Amount,Status
2024-01-15,RELIANCE,buy,100,2500.00,250000.00,executed
```

## 🛡️ Security Features

### Demo Mode Safety
- ✅ No real orders executed
- ✅ Virtual funds only
- ✅ Complete simulation
- ✅ Safe testing environment

### Real Mode Warnings
- ⚠️ Clear mode indicators
- ⚠️ Confirmation dialogs
- ⚠️ Visual warnings
- ⚠️ Session management

## 🔍 Troubleshooting

### Common Issues

1. **Login Failed**
   - Verify API credentials
   - Check session token validity
   - Ensure Breeze Connect account is active

2. **No Market Data**
   - Check internet connection
   - Verify symbol names
   - Check market hours

3. **Demo Mode Issues**
   - Restart application
   - Check DuckDB file permissions
   - Clear browser cache

### Logs
- Check console output for detailed logs
- All API calls are logged
- Error messages are displayed in UI

## 📈 Performance

### Optimizations
- **Async API calls**: Non-blocking operations
- **Caching**: Reduced API calls
- **Auto-refresh**: 30-second intervals
- **Responsive design**: Mobile-friendly

### Scalability
- **Modular architecture**: Easy to extend
- **Separate managers**: Clean separation of concerns
- **Database optimization**: Efficient queries

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

### Code Structure
```
trading_system/
├── api.py          # Breeze Connect API wrapper
├── core.py         # Main trading system
├── managers.py     # Feature managers
├── fake_trading.py # Demo trading system
├── utils.py        # Utilities
├── server.py       # FastAPI server
├── templates/      # HTML templates
└── static/         # CSS/JS files
```

## 📄 License

This project is for educational and development purposes. Use at your own risk.

## ⚠️ Disclaimer

- **Demo Mode**: Safe for testing and learning
- **Real Mode**: Use with extreme caution
- **No Financial Advice**: This is not financial advice
- **Risk Warning**: Trading involves substantial risk

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs
3. Create an issue with detailed information

---

**Happy Trading! 🚀📈** 