"""
FastAPI Server for Comprehensive Trading System
Provides REST API endpoints for all trading operations
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
import uvicorn
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import pytz
import json

from core import TradingSystem
from utils import TradingUtils, DataProcessor, ConfigManager
from job_manager import HistoricalDataJobManager
from historical_db import get_historical_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global trading_system, job_manager
    
    # Startup
    logger.info("Starting Trading System Server...")
    
    # Load configuration
    api_key = config_manager.get('api.api_key')
    api_secret = config_manager.get('api.api_secret')
    session_token = config_manager.get('api.session_token')
    
    # Only initialize if we have all credentials
    if api_key and api_secret and session_token:
        logger.info("Found saved credentials, initializing trading system...")
        trading_system = TradingSystem(api_key, api_secret, session_token)
        success = await trading_system.initialize()
        if success:
            logger.info("Trading system initialized successfully")
            # Initialize job manager (global variable)
            global job_manager
            job_manager = HistoricalDataJobManager(trading_system)
            logger.info("Job manager initialized successfully")
            
            # Initialize database on startup
            try:
                db = get_historical_db()
                stats = db.get_database_stats()
                logger.info(f"Historical database ready: {stats.get('total_candles', 0)} candles, {stats.get('total_jobs', 0)} jobs")
            except Exception as e:
                logger.warning(f"Database initialization issue: {e}")
        else:
            logger.warning("Failed to initialize trading system")
    else:
        logger.info("No saved credentials found, starting in demo mode")
    
    yield
    
    # Shutdown
    if trading_system:
        await trading_system.disconnect()
    logger.info("Trading System Server shutdown")

# Initialize FastAPI app
app = FastAPI(
    title="Trading System API",
    description="Comprehensive trading system with Breeze Connect integration",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Global trading system instance
trading_system = None
job_manager = None
config_manager = ConfigManager()
websocket_connections = []

# Pydantic models for request/response
from pydantic import BaseModel

class LoginRequest(BaseModel):
    api_key: str
    api_secret: str
    session_token: str

class OrderRequest(BaseModel):
    stock_code: str
    exchange_code: str = "NSE"
    product: str = "cash"
    action: str
    order_type: str
    quantity: int
    price: Optional[float] = None
    validity: str = "day"
    stoploss: Optional[float] = None
    disclosed_quantity: int = 0
    user_remark: Optional[str] = None

class GTTRequest(BaseModel):
    exchange_code: str
    stock_code: str
    product: str
    quantity: int
    gtt_type: str
    order_details: List[Dict[str, Any]]

class HistoricalDataRequest(BaseModel):
    symbol: str
    exchange: str = "NSE"
    interval: str = "1day"
    days: int = 30

class MarketWatchRequest(BaseModel):
    symbols: List[str]

# Dependency to get trading system
async def get_trading_system():
    global trading_system
    if not trading_system or not trading_system.is_connected:
        # Return None instead of raising exception for demo mode
        return None
    return trading_system

# Background task for real-time data
async def background_realtime_task():
    """Background task for real-time data processing"""
    global trading_system
    while True:
        try:
            # Update market watch data every 30 seconds
            if trading_system and trading_system.is_connected:
                await trading_system.update_market_watch()
            
            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"Error in background task: {str(e)}")
            await asyncio.sleep(60)



# Web routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Landing page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request):
    """Orders page"""
    return templates.TemplateResponse("orders.html", {"request": request})

@app.get("/portfolio", response_class=HTMLResponse)
async def portfolio_page(request: Request):
    """Portfolio page"""
    return templates.TemplateResponse("portfolio.html", {"request": request})

@app.get("/market", response_class=HTMLResponse)
async def market_page(request: Request):
    """Market data page"""
    return templates.TemplateResponse("market.html", {"request": request})

@app.get("/charts", response_class=HTMLResponse)
async def charts_page(request: Request):
    """Charts page"""
    return templates.TemplateResponse("charts.html", {"request": request})

@app.get("/gtt", response_class=HTMLResponse)
async def gtt_page(request: Request):
    """GTT orders page"""
    return templates.TemplateResponse("gtt.html", {"request": request})

# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Trading System is running"}

@app.get("/api/user/details")
async def get_user_details(ts: TradingSystem = Depends(get_trading_system)):
    """Get user details"""
    try:
        if ts:
            user_details = await ts.get_user_details()
            if user_details:
                return {
                    "status": "success",
                    "user_details": user_details
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to get user details"
                }
        else:
            return {
                "status": "demo",
                "user_details": {
                    "idirect_user_name": "Demo User",
                    "idirect_userid": "DEMO001"
                }
            }
    except Exception as e:
        logger.error(f"Error getting user details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get user details: {str(e)}")

# API routes
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Login to trading system"""
    global trading_system
    
    try:
        logger.info(f"Login attempt with API Key: {request.api_key[:10]}...")
        logger.info(f"Session Token: {request.session_token}")
        
        # Initialize trading system
        trading_system = TradingSystem(
            request.api_key,
            request.api_secret,
            request.session_token
        )
        
        success = await trading_system.initialize()
        if success:
            # Save credentials to config only after successful authentication
            config_manager.set('api.api_key', request.api_key)
            config_manager.set('api.api_secret', request.api_secret)
            config_manager.set('api.session_token', request.session_token)
            
            return {
                "status": "success",
                "message": "Login successful",
                "session_id": trading_system.session_id
            }
        else:
            raise HTTPException(status_code=401, detail="Authentication failed. Please check your credentials and session token.")
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/api/auth/logout")
async def logout():
    """Logout from trading system"""
    global trading_system
    
    try:
        if trading_system:
            await trading_system.disconnect()
            trading_system = None
        
        return {"status": "success", "message": "Logout successful"}
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

@app.get("/api/auth/status")
async def auth_status():
    """Get authentication status"""
    global trading_system
    
    return {
        "connected": trading_system is not None and trading_system.is_connected,
        "session_id": trading_system.session_id if trading_system else None
    }

@app.get("/api/test/breeze-connect")
async def test_breeze_connect(ts: TradingSystem = Depends(get_trading_system)):
    """Test Breeze Connect connection and basic APIs"""
    try:
        if ts and ts.is_connected:
            # Test basic APIs
            test_results = {
                "connection_status": "Connected",
                "session_id": ts.session_id,
                "tests": {}
            }
            
            # Test get_funds
            try:
                funds = await ts.portfolio.get_funds()
                test_results["tests"]["get_funds"] = {
                    "status": "success" if funds else "failed",
                    "data": funds
                }
            except Exception as e:
                test_results["tests"]["get_funds"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Test get_demat_holdings
            try:
                holdings = await ts.portfolio.get_demat_holdings()
                test_results["tests"]["get_demat_holdings"] = {
                    "status": "success" if holdings else "failed",
                    "data": holdings
                }
            except Exception as e:
                test_results["tests"]["get_demat_holdings"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Test get_positions
            try:
                positions = await ts.portfolio.get_positions()
                test_results["tests"]["get_positions"] = {
                    "status": "success" if positions else "failed",
                    "data": positions
                }
            except Exception as e:
                test_results["tests"]["get_positions"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            return test_results
        else:
            return {
                "connection_status": "Not Connected",
                "error": "Trading system not initialized or not connected"
            }
    except Exception as e:
        logger.error(f"Error testing Breeze Connect: {str(e)}")
        return {
            "connection_status": "Error",
            "error": str(e)
        }

@app.get("/api/portfolio/summary")
async def get_portfolio_summary(ts: TradingSystem = Depends(get_trading_system)):
    """Get portfolio summary (works in demo mode)"""
    try:
        if ts and ts.is_connected:
            # Real trading system is connected
            logger.info("Fetching real portfolio summary...")
            summary = await ts.get_portfolio_summary()
            if summary:
                logger.info(f"Real portfolio summary fetched successfully: {summary}")
                
                # FIX: Ensure correct parsing of real data
                if summary.get('total_balance', 0) == 0 and summary.get('raw_funds'):
                    raw_funds = summary.get('raw_funds', {})
                    # Check if raw_funds is already the Success data or has Success key
                    if 'unallocated_balance' in raw_funds:
                        funds = raw_funds
                    elif 'Success' in raw_funds:
                        funds = raw_funds.get('Success', {})
                    else:
                        funds = {}
                    
                    unallocated = funds.get('unallocated_balance', '0')
                    try:
                        fixed_balance = float(unallocated)
                        summary['total_balance'] = fixed_balance
                        summary['cash_balance'] = fixed_balance
                        logger.info(f"Fixed total_balance and cash_balance to {fixed_balance}")
                    except:
                        pass
                
                if summary.get('holdings_count', 0) == 0 and summary.get('raw_holdings'):
                    raw_holdings = summary.get('raw_holdings', [])
                    if isinstance(raw_holdings, list) and len(raw_holdings) > 0:
                        summary['holdings_count'] = len(raw_holdings)
                        logger.info(f"Fixed holdings_count to {len(raw_holdings)}")
                    elif isinstance(raw_holdings, dict) and 'Success' in raw_holdings:
                        holdings = raw_holdings.get('Success', [])
                        if isinstance(holdings, list) and len(holdings) > 0:
                            summary['holdings_count'] = len(holdings)
                            logger.info(f"Fixed holdings_count to {len(holdings)}")
                
                return summary
            else:
                logger.warning("Real portfolio summary returned None, falling back to demo mode")
                # Fall back to demo mode if real data fails
                from fake_trading import FakeTradingSystem
                fake_system = FakeTradingSystem()
                fake_summary = fake_system.get_portfolio_summary()
                return {
                    "session_id": "demo_session",
                    "timestamp": datetime.now().isoformat(),
                    "fake_trading": fake_summary,
                    "is_simulation": True
                }
        else:
            # Demo mode - return fake data
            logger.info("Using demo mode for portfolio summary")
            from fake_trading import FakeTradingSystem
            fake_system = FakeTradingSystem()
            fake_summary = fake_system.get_portfolio_summary()
            return {
                "session_id": "demo_session",
                "timestamp": datetime.now().isoformat(),
                "fake_trading": fake_summary,
                "is_simulation": True
            }
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {str(e)}")
        # Return demo data on error
        try:
            from fake_trading import FakeTradingSystem
            fake_system = FakeTradingSystem()
            fake_summary = fake_system.get_portfolio_summary()
            return {
                "session_id": "demo_session",
                "timestamp": datetime.now().isoformat(),
                "fake_trading": fake_summary,
                "is_simulation": True,
                "error": str(e)
            }
        except Exception as fallback_error:
            logger.error(f"Fallback demo data also failed: {str(fallback_error)}")
            raise HTTPException(status_code=500, detail=f"Failed to get portfolio summary: {str(e)}")

# Fake trading endpoints
@app.get("/api/fake/funds")
async def get_fake_funds():
    """Get fake funds"""
    try:
        from fake_trading import FakeTradingSystem
        fake_system = FakeTradingSystem()
        funds = fake_system.get_funds()
        return funds
    except Exception as e:
        logger.error(f"Error getting fake funds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get fake funds: {str(e)}")

@app.post("/api/fake/funds/update")
async def update_fake_funds(request: dict):
    """Update fake funds"""
    try:
        from fake_trading import FakeTradingSystem
        fake_system = FakeTradingSystem()
        
        amount = request.get('amount', 0)
        transaction_type = request.get('transaction_type', 'credit')  # credit or debit
        segment = request.get('segment', 'cash')  # cash, equity, or fno
        
        fake_system.update_funds(amount, transaction_type, segment)
        
        # Return updated funds
        updated_funds = fake_system.get_funds()
        return {
            "status": "success", 
            "message": f"Funds updated: {transaction_type} {amount} in {segment}",
            "data": updated_funds
        }
    except Exception as e:
        logger.error(f"Error updating fake funds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update fake funds: {str(e)}")

@app.get("/api/fake/holdings")
async def get_fake_holdings():
    """Get fake holdings"""
    try:
        from fake_trading import FakeTradingSystem
        fake_system = FakeTradingSystem()
        holdings = fake_system.get_holdings()
        return holdings
    except Exception as e:
        logger.error(f"Error getting fake holdings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get fake holdings: {str(e)}")

@app.get("/api/fake/ledger")
async def get_fake_ledger(limit: int = 100):
    """Get fake ledger"""
    try:
        from fake_trading import FakeTradingSystem
        fake_system = FakeTradingSystem()
        ledger = fake_system.get_ledger(limit)
        return ledger
    except Exception as e:
        logger.error(f"Error getting fake ledger: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get fake ledger: {str(e)}")

@app.post("/api/fake/ledger/add")
async def add_fake_ledger_entry(request: dict):
    """Add manual ledger entry"""
    try:
        from fake_trading import FakeTradingSystem
        fake_system = FakeTradingSystem()
        
        entry_data = {
            'transaction_id': request.get('transaction_id', f"MANUAL_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            'transaction_type': request.get('transaction_type', 'manual_adjustment'),
            'symbol': request.get('symbol', ''),
            'exchange': request.get('exchange', ''),
            'action': request.get('action', ''),
            'quantity': request.get('quantity', 0),
            'price': request.get('price', 0),
            'total_amount': request.get('total_amount', 0),
            'segment': request.get('segment', 'cash'),
            'status': request.get('status', 'completed'),
            'remarks': request.get('remarks', 'Manual funds adjustment')
        }
        
        fake_system.add_ledger_entry(entry_data)
        
        return {
            "status": "success",
            "message": "Ledger entry added successfully"
        }
    except Exception as e:
        logger.error(f"Error adding ledger entry: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add ledger entry: {str(e)}")

@app.get("/api/fake/orders")
async def get_fake_orders():
    """Get all fake orders"""
    try:
        from fake_trading import FakeTradingSystem
        fake_system = FakeTradingSystem()
        orders = fake_system.get_orders()
        return {"status": "success", "data": orders}
    except Exception as e:
        logger.error(f"Error getting fake orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get fake orders: {str(e)}")

@app.post("/api/fake/orders")
async def place_fake_order(request: dict):
    """Place a fake order"""
    try:
        from fake_trading import FakeTradingSystem
        fake_system = FakeTradingSystem()
        
        # Use the new place_fake_order method
        result = fake_system.place_fake_order(request)
        return result
    except Exception as e:
        logger.error(f"Error placing fake order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to place fake order: {str(e)}")

@app.get("/api/market-watch/symbols")
async def get_market_watch_symbols():
    """Get market watch symbols"""
    try:
        from fake_trading import FakeTradingSystem
        fake_system = FakeTradingSystem()
        symbols = fake_system.get_market_watch_symbols()
        return {"status": "success", "data": symbols}
    except Exception as e:
        logger.error(f"Error getting market watch symbols: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get market watch symbols: {str(e)}")

@app.post("/api/market-watch/symbols")
async def add_market_watch_symbol(request: dict):
    """Add symbol to market watch"""
    try:
        from fake_trading import FakeTradingSystem
        fake_system = FakeTradingSystem()
        success = fake_system.add_market_watch_symbol(request['symbol'], request['exchange'])
        
        if success:
            return {"status": "success", "message": f"Added {request['symbol']} to market watch"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add symbol")
    except Exception as e:
        logger.error(f"Error adding market watch symbol: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add symbol: {str(e)}")

@app.delete("/api/market-watch/symbols")
async def remove_market_watch_symbol(symbol: str, exchange: str):
    """Remove symbol from market watch"""
    try:
        from fake_trading import FakeTradingSystem
        fake_system = FakeTradingSystem()
        success = fake_system.remove_market_watch_symbol(symbol, exchange)
        
        if success:
            return {"status": "success", "message": f"Removed {symbol} from market watch"}
        else:
            raise HTTPException(status_code=400, detail="Failed to remove symbol")
    except Exception as e:
        logger.error(f"Error removing market watch symbol: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to remove symbol: {str(e)}")

@app.post("/api/fake/orders/{order_id}/execute")
async def execute_fake_order(
    order_id: str,
    execution_price: float,
    ts: TradingSystem = Depends(get_trading_system)
):
    """Execute a fake order"""
    try:
        result = ts.execute_fake_order(order_id, execution_price)
        return result
    except Exception as e:
        logger.error(f"Error executing fake order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute fake order: {str(e)}")

@app.post("/api/fake/historical/store")
async def store_fake_historical_data(
    symbol: str,
    exchange: str,
    data: List[Dict[str, Any]],
    interval: str = "1day",
    ts: TradingSystem = Depends(get_trading_system)
):
    """Store historical data in fake system"""
    try:
        ts.store_historical_data(symbol, exchange, data, interval)
        return {"status": "success", "message": f"Stored {len(data)} records for {symbol}"}
    except Exception as e:
        logger.error(f"Error storing fake historical data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store fake historical data: {str(e)}")

@app.get("/api/fake/historical/{symbol}")
async def get_fake_historical_data(
    symbol: str,
    exchange: str = "NSE",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    interval: str = "1day",
    ts: TradingSystem = Depends(get_trading_system)
):
    """Get historical data from fake system"""
    try:
        data = ts.get_fake_historical_data(symbol, exchange, from_date, to_date, interval)
        return data
    except Exception as e:
        logger.error(f"Error getting fake historical data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get fake historical data: {str(e)}")

@app.post("/api/fake/export/{table_name}")
async def export_fake_data(
    table_name: str,
    filename: str,
    conditions: Optional[Dict[str, Any]] = None,
    ts: TradingSystem = Depends(get_trading_system)
):
    """Export fake data to CSV"""
    try:
        success = ts.export_fake_data_to_csv(table_name, filename, conditions)
        if success:
            return {
                "status": "success",
                "message": f"Data exported to {filename}",
                "filename": filename
            }
        else:
            raise HTTPException(status_code=400, detail="Export failed")
    except Exception as e:
        logger.error(f"Error exporting fake data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export fake data: {str(e)}")

@app.get("/api/portfolio/holdings")
async def get_holdings(ts: TradingSystem = Depends(get_trading_system)):
    """Get demat holdings"""
    try:
        holdings = await ts.portfolio.get_demat_holdings()
        processed_holdings = DataProcessor.process_holdings_data(holdings)
        return processed_holdings
    except Exception as e:
        logger.error(f"Error getting holdings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get holdings: {str(e)}")

@app.get("/api/portfolio/positions")
async def get_positions(ts: TradingSystem = Depends(get_trading_system)):
    """Get portfolio positions"""
    try:
        positions = await ts.portfolio.get_positions()
        return positions
    except Exception as e:
        logger.error(f"Error getting positions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get positions: {str(e)}")

@app.get("/api/portfolio/funds")
async def get_funds(ts: TradingSystem = Depends(get_trading_system)):
    """Get funds"""
    try:
        funds = await ts.portfolio.get_funds()
        return funds
    except Exception as e:
        logger.error(f"Error getting funds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get funds: {str(e)}")

@app.get("/api/market/watch")
async def get_market_watch(
    symbols: Optional[str] = None,
    ts: TradingSystem = Depends(get_trading_system)
):
    """Get market watch"""
    try:
        if symbols:
            symbol_list = symbols.split(',')
        else:
            symbol_list = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK']
        
        watchlist = await ts.get_market_watch(symbol_list)
        processed_watchlist = DataProcessor.process_quotes_data(watchlist)
        return processed_watchlist
    except Exception as e:
        logger.error(f"Error getting market watch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get market watch: {str(e)}")

@app.get("/api/market/quotes")
async def get_quotes(
    symbol: str,
    exchange: str = "NSE",
    expiry_date: Optional[str] = None,
    option_type: Optional[str] = None,
    strike_price: Optional[float] = None,
    ts: TradingSystem = Depends(get_trading_system)
):
    """Get quotes for a symbol"""
    try:
        if ts:
            # Real trading system is connected
            # For NFO/BFO, we need to pass expiry_date as a separate parameter
            if (exchange in ['NFO', 'BFO']) and expiry_date:
                # Debug: Log the request details
                logger.info(f"Quote request - Symbol: {symbol}, Exchange: {exchange}, Expiry: {expiry_date}, Option: {option_type}, Strike: {strike_price}")
                
                # Use the specific option details passed from frontend
                if option_type and option_type in ['CE', 'PE']:
                    # This is an option
                    right = 'Call' if option_type == 'CE' else 'Put'
                    product_type = 'Options'
                    strike_price_str = str(strike_price) if strike_price and strike_price > 0 else "0"
                    
                    logger.info(f"Using option details - Right: {right}, Strike: {strike_price_str}")
                    
                    quote = await ts.market.get_quotes(
                        stock_code=symbol,
                        exchange_code=exchange,
                        expiry_date=expiry_date,
                        product_type=product_type,
                        right=right,
                        strike_price=strike_price_str
                    )
                else:
                    # This is likely a future or we don't have option details
                    logger.info(f"Using future details - No option type specified")
                    
                    quote = await ts.market.get_quotes(
                        stock_code=symbol,
                        exchange_code=exchange,
                        expiry_date=expiry_date,
                        product_type="Futures",
                        right="Others",
                        strike_price="0"
                    )
            else:
                quote = await ts.market.get_quotes(symbol, exchange)
                
            if quote:
                processed_quote = DataProcessor.process_quotes_data(quote)
                return {
                    "status": "success",
                    "data": processed_quote[0] if processed_quote else None
                }
            return {
                "status": "error",
                "message": "Failed to fetch quotes"
            }
        else:
            # Demo mode - return fake data
            import random
            fake_quotes = {
                "symbol": symbol,
                "exchange": exchange,
                "ltp": round(1000 + (random.random() * 500), 2),
                "change": round((random.random() - 0.5) * 50, 2),
                "change_percent": round((random.random() - 0.5) * 5, 2),
                "volume": str(random.randint(100000, 1000000)),
                "high": round(1050 + (random.random() * 100), 2),
                "low": round(950 + (random.random() * 100), 2),
                "open": round(1000 + (random.random() * 50), 2),
                "close": round(1000 + (random.random() * 50), 2)
            }
            return {
                "status": "success",
                "data": fake_quotes
            }
    except Exception as e:
        logger.error(f"Error getting quotes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get quotes: {str(e)}")

@app.get("/api/instruments/search")
async def search_instruments(
    query: str, 
    limit: int = 100,
    exchange: Optional[str] = None,
    instrument_type: Optional[str] = None
):
    """Search instruments by query with optional filters"""
    try:
        from instruments_manager import InstrumentsManager
        instruments_mgr = InstrumentsManager()
        
        results = instruments_mgr.search_instruments(query, limit, exchange, instrument_type)
        
        return {
            "status": "success",
            "data": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching instruments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search instruments: {str(e)}")

@app.post("/api/instruments/advanced-search")
async def advanced_search_instruments(request: dict):
    """Advanced search instruments with multiple criteria"""
    try:
        from instruments_manager import InstrumentsManager
        instruments_mgr = InstrumentsManager()
        
        results = instruments_mgr.advanced_search(**request)
        
        return {
            "status": "success",
            "data": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error in advanced search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to perform advanced search: {str(e)}")

@app.get("/api/instruments/stats")
async def get_instruments_stats():
    """Get instruments database statistics"""
    try:
        from instruments_manager import InstrumentsManager
        instruments_mgr = InstrumentsManager()
        
        stats = instruments_mgr.get_database_stats()
        
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error getting instruments stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get instruments stats: {str(e)}")

@app.get("/api/instruments/refresh")
async def refresh_instruments():
    """Manually refresh instruments data"""
    try:
        from instruments_manager import InstrumentsManager
        instruments_mgr = InstrumentsManager()
        
        success = await instruments_mgr.refresh_instruments()
        
        if success:
            return {
                "status": "success",
                "message": "Instruments data refreshed successfully"
            }
        else:
            return {
                "status": "error",
                "message": "Failed to refresh instruments data"
            }
    except Exception as e:
        logger.error(f"Error refreshing instruments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh instruments: {str(e)}")

@app.get("/api/market/historical")
async def get_historical_data(
    symbol: str,
    exchange: str = "NSE",
    interval: str = "1day",
    days: int = 30,
    ts: TradingSystem = Depends(get_trading_system)
):
    """Get historical data for charts"""
    try:
        if ts:
            # Real trading system is connected
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            historical_data = await ts.get_historical_data(
                stock_code=symbol,
                exchange_code=exchange,
                interval=interval,
                from_date=start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                to_date=end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            )
            
            if historical_data:
                return {
                    "status": "success",
                    "data": historical_data
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to fetch historical data"
                }
        else:
            # Demo mode - return fake historical data
            import random
            from datetime import datetime, timedelta
            
            fake_data = []
            base_price = 1000 + (random.random() * 500)
            
            for i in range(days):
                date = datetime.now() - timedelta(days=days-i-1)
                price_change = (random.random() - 0.5) * 20
                base_price += price_change
                
                fake_data.append({
                    "datetime": date.strftime("%Y-%m-%d"),
                    "open": round(base_price - (random.random() * 10), 2),
                    "high": round(base_price + (random.random() * 15), 2),
                    "low": round(base_price - (random.random() * 15), 2),
                    "close": round(base_price, 2),
                    "volume": random.randint(100000, 1000000)
                })
            
            return {
                "status": "success",
                "data": fake_data
            }
    except Exception as e:
        logger.error(f"Error fetching historical data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch historical data: {str(e)}")

@app.get("/api/market/option-chain/{symbol}")
async def get_option_chain(
    symbol: str,
    expiry_date: str,
    exchange: str = "NFO",
    ts: TradingSystem = Depends(get_trading_system)
):
    """Get option chain"""
    try:
        option_chain = await ts.get_option_chain(symbol, expiry_date)
        return option_chain
    except Exception as e:
        logger.error(f"Error getting option chain: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get option chain: {str(e)}")

@app.get("/api/historical/test")
async def test_historical_data(
    symbol: str = "RELIND",
    exchange: str = "NSE",
    interval: str = "1minute",
    ts: TradingSystem = Depends(get_trading_system)
):
    """Test historical data with known working parameters"""
    try:
        if not ts or not ts.is_connected:
            raise HTTPException(status_code=503, detail="Trading system not connected.")
        
        # Use recent dates and known symbols
        end_date = datetime.now()
        start_date = end_date - timedelta(days=2)
        
        from_date = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        to_date = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        # Test with simple equity first - use RELIND (known to work)
        params = {
            'stock_code': symbol,
            'exchange_code': exchange,
            'interval': interval,
            'from_date': from_date,
            'to_date': to_date,
            'product_type': 'cash'
        }
        
        # Create a working curl command for manual testing
        curl_cmd = f"""
        # Test this curl command manually:
        curl "http://localhost:8000/api/historical/test?symbol=RELIND&exchange=NSE&interval=1minute"
        """
        logger.info(curl_cmd)
        
        logger.info(f"Testing historical data with params: {params}")
        
        data = await ts.get_historical_data(**params)
        return {
            'status': 'test_complete',
            'params_sent': params,
            'raw_response': data,
            'data_count': len(data.get('Success', [])) if data and 'Success' in data else 0
        }
        
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        return {
            'status': 'test_error',
            'error': str(e),
            'params_sent': params if 'params' in locals() else None
        }

@app.get("/api/historical/data")
async def get_historical_data(
    symbol: str,
    exchange: str = "NSE",
    interval: str = "1day",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    days: Optional[int] = None,  # Keep for backward compatibility
    product_type: Optional[str] = None,
    expiry_date: Optional[str] = None,
    strike_price: Optional[str] = None,
    right: Optional[str] = None,
    ts: TradingSystem = Depends(get_trading_system)
):
    """Get historical data with support for derivatives"""
    try:
        if not ts or not ts.is_connected:
            raise HTTPException(status_code=503, detail="Trading system not connected. Please check your connection and try again.")
        
        # Handle date parameters - prioritize from_date/to_date, fallback to days
        if from_date and to_date:
            # Use provided dates - convert to proper format if needed
            try:
                # Parse ISO format dates from frontend
                from datetime import datetime as dt
                start_dt = dt.fromisoformat(from_date.replace('Z', '+00:00'))
                end_dt = dt.fromisoformat(to_date.replace('Z', '+00:00'))
                
                # Format for API
                api_from_date = start_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                api_to_date = end_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                
            except Exception as e:
                logger.error(f"Error parsing provided dates: {e}")
                raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS.000Z)")
        else:
            # Fallback to days calculation for backward compatibility
            days = days or 30  # Default to 30 days if not provided
            
            # Use Indian timezone for proper market dates
            ist = pytz.timezone('Asia/Kolkata')
            end_date = dt.now(ist)
            
            # CRITICAL: Ensure we're using PAST dates only
            # If today is weekend, go back to last Friday
            while end_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                end_date = end_date - timedelta(days=1)
            
            # For 1second interval, limit to much smaller range (max 1000 candles)
            if interval == "1second":
                # Use market hours data - go back to last trading session
                start_date = end_date.replace(hour=9, minute=15) - timedelta(days=1)
                end_date = end_date.replace(hour=15, minute=30) - timedelta(days=1)
            elif interval == "1minute":
                # Use last 2 trading days
                start_date = end_date - timedelta(days=3)
            elif interval in ["5minute", "30minute"]:
                # Use smaller range for intraday intervals
                start_date = end_date - timedelta(days=min(days, 10))
            else:
                # For 1day, use reasonable range
                start_date = end_date - timedelta(days=min(days, 60))
            
            # Format dates for API - use proper ISO format
            api_from_date = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            api_to_date = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        logger.info(f"Date range ({interval}): {api_from_date} to {api_to_date}")
        
        # Build parameters for historical data
        params = {
            'stock_code': symbol,
            'exchange_code': exchange,
            'interval': interval,
            'from_date': api_from_date,
            'to_date': api_to_date
        }
        
        # CRITICAL: Always set product_type for all exchanges
        if exchange in ['NFO', 'BFO']:
            # Determine product type for derivatives
            if product_type and product_type in ['options', 'futures']:
                params['product_type'] = product_type
            elif right and right in ['CE', 'PE', 'call', 'put']:
                params['product_type'] = 'options'
            else:
                params['product_type'] = 'futures'  # Default for NFO/BFO
        else:
            # For NSE/BSE equity, MUST use 'cash'
            params['product_type'] = 'cash'
            
            if expiry_date:
                # Convert expiry date to ISO format for API call
                try:
                    # If it's in DD-MMM-YYYY format, convert to ISO
                    if '-' in expiry_date and len(expiry_date.split('-')) == 3:
                        parts = expiry_date.split('-')
                        if len(parts[1]) == 3 and parts[1].isalpha():  # DD-MMM-YYYY format
                            parsed_date = datetime.strptime(expiry_date, "%d-%b-%Y")
                            params['expiry_date'] = parsed_date.strftime("%Y-%m-%dT07:00:00.000Z")
                        else:
                            # DD-MM-YYYY format
                            parsed_date = datetime.strptime(expiry_date, "%d-%m-%Y")
                            params['expiry_date'] = parsed_date.strftime("%Y-%m-%dT07:00:00.000Z")
                    else:
                        # Try other formats
                        try:
                            parsed_date = datetime.strptime(expiry_date, "%Y-%m-%d")
                            params['expiry_date'] = parsed_date.strftime("%Y-%m-%dT07:00:00.000Z")
                        except:
                            # If already in ISO format, use as-is
                            params['expiry_date'] = expiry_date
                except Exception as e:
                    logger.warning(f"Could not parse expiry date '{expiry_date}': {e}, using as-is")
                    params['expiry_date'] = expiry_date
            if strike_price and strike_price != '0':
                params['strike_price'] = strike_price
            if right:
                # Convert option type to API format
                if right in ['CE', 'call']:
                    params['right'] = 'call'
                elif right in ['PE', 'put']:
                    params['right'] = 'put'
                else:
                    params['right'] = 'others'
        
        logger.info(f"Original symbol parameter: {symbol}")
        logger.info(f"Fetching historical data with params: {params}")
        
        # Create debug curl command
        debug_curl = f"""
        DEBUG: Equivalent curl command for testing:
        curl -X POST "https://api.icicidirect.com/breezeapi/api/v1/historicaldata" \\
        -H "Content-Type: application/json" \\
        -H "X-SessionToken: YOUR_SESSION_TOKEN" \\
        -H "apikey: YOUR_API_KEY" \\
        -d '{{"interval": "{params.get("interval")}", "from_date": "{params.get("from_date")}", "to_date": "{params.get("to_date")}", "stock_code": "{params.get("stock_code")}", "exchange_code": "{params.get("exchange_code")}", "product_type": "{params.get("product_type", "")}", "expiry_date": "{params.get("expiry_date", "")}", "right": "{params.get("right", "")}", "strike_price": "{params.get("strike_price", "")}"}}'
        """
        logger.info(debug_curl)
        
        # Get historical data
        data = await ts.get_historical_data(**params)
        
        # Return raw API response for better error handling
        if data:
            if 'Success' in data and data['Success']:
                return {
                    'status': 'success',
                    'data': data['Success'],
                    'raw_response': data
                }
            elif 'Error' in data:
                logger.error(f"API Error: {data['Error']}")
                return {
                    'status': 'error',
                    'error': data['Error'],
                    'raw_response': data
                }
            else:
                return {
                    'status': 'success',
                    'data': data,
                    'raw_response': data
                }
        else:
            return {
                'status': 'error',
                'error': 'No data received from API',
                'raw_response': None
            }
            
    except Exception as e:
        logger.error(f"Error getting historical data: {str(e)}")
        return {
            'status': 'error',
            'error': f"Failed to get historical data: {str(e)}",
            'raw_response': None
        }

@app.post("/api/orders/place")
async def place_order(
    order: OrderRequest,
    ts: TradingSystem = Depends(get_trading_system)
):
    """Place an order"""
    try:
        if not ts or not ts.is_connected:
            raise HTTPException(status_code=503, detail="Trading system not connected. Please check your connection and try again.")
        
        order_params = order.dict()
        response = await ts.place_order(order_params)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to place order: {str(e)}")

@app.get("/api/orders/list")
async def get_orders(
    exchange: str = "NSE",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    ts: TradingSystem = Depends(get_trading_system)
):
    """Get order list"""
    try:
        orders = await ts.orders.get_order_list(exchange, from_date, to_date)
        processed_orders = DataProcessor.process_orders_data(orders)
        return processed_orders
    except Exception as e:
        logger.error(f"Error getting orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get orders: {str(e)}")

@app.get("/api/orders/{order_id}")
async def get_order_detail(
    order_id: str,
    exchange: str = "NSE",
    ts: TradingSystem = Depends(get_trading_system)
):
    """Get order detail"""
    try:
        order_detail = await ts.get_order_status(order_id, exchange)
        return order_detail
    except Exception as e:
        logger.error(f"Error getting order detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get order detail: {str(e)}")

@app.delete("/api/orders/{order_id}")
async def cancel_order(
    order_id: str,
    exchange: str = "NSE",
    ts: TradingSystem = Depends(get_trading_system)
):
    """Cancel an order"""
    try:
        response = await ts.cancel_order(order_id, exchange)
        return response
    except Exception as e:
        logger.error(f"Error canceling order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel order: {str(e)}")

@app.delete("/api/fake/orders/{order_id}")
async def cancel_fake_order(order_id: str):
    """Cancel a fake order"""
    try:
        from fake_trading import FakeTradingSystem
        fake_system = FakeTradingSystem()
        
        result = fake_system.cancel_order(order_id)
        
        if result['status'] == 'success':
            return result
        else:
            raise HTTPException(status_code=400, detail=result['message'])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling fake order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel fake order: {str(e)}")

@app.put("/api/orders/{order_id}")
async def modify_order(
    order_id: str,
    modifications: Dict[str, Any],
    ts: TradingSystem = Depends(get_trading_system)
):
    """Modify an order"""
    try:
        response = await ts.modify_order(order_id, modifications)
        return response
    except Exception as e:
        logger.error(f"Error modifying order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to modify order: {str(e)}")

@app.post("/api/gtt/place")
async def place_gtt_order(
    gtt_request: GTTRequest,
    ts: TradingSystem = Depends(get_trading_system)
):
    """Place GTT order"""
    try:
        gtt_params = gtt_request.dict()
        response = await ts.place_gtt_order(gtt_params)
        return response
    except Exception as e:
        logger.error(f"Error placing GTT order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to place GTT order: {str(e)}")

@app.get("/api/gtt/orders")
async def get_gtt_orders(
    exchange: str = "NFO",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    ts: TradingSystem = Depends(get_trading_system)
):
    """Get GTT orders"""
    try:
        gtt_orders = await ts.gtt.get_gtt_orders(exchange, from_date, to_date)
        return gtt_orders
    except Exception as e:
        logger.error(f"Error getting GTT orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get GTT orders: {str(e)}")

@app.get("/api/trades")
async def get_trades(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    exchange: str = "NSE",
    ts: TradingSystem = Depends(get_trading_system)
):
    """Get trade history"""
    try:
        trades = await ts.get_trade_history(from_date, to_date)
        return trades
    except Exception as e:
        logger.error(f"Error getting trades: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get trades: {str(e)}")

@app.post("/api/calculate/margin")
async def calculate_margin(
    orders: List[Dict[str, Any]],
    exchange: str = "NFO",
    ts: TradingSystem = Depends(get_trading_system)
):
    """Calculate margin"""
    try:
        margin = await ts.calculate_margin(orders)
        return margin
    except Exception as e:
        logger.error(f"Error calculating margin: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate margin: {str(e)}")

@app.post("/api/streaming/start")
async def start_streaming(
    symbols: List[str],
    ts: TradingSystem = Depends(get_trading_system)
):
    """Start real-time streaming"""
    try:
        success = await ts.start_realtime_streaming(symbols)
        return {"status": "success" if success else "failed"}
    except Exception as e:
        logger.error(f"Error starting streaming: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start streaming: {str(e)}")

@app.post("/api/streaming/stop")
async def stop_streaming(ts: TradingSystem = Depends(get_trading_system)):
    """Stop real-time streaming"""
    try:
        await ts.realtime.stop_streaming()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error stopping streaming: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop streaming: {str(e)}")

@app.get("/api/market/status")
async def get_market_status():
    """Get current market status"""
    try:
        from fake_trading import FakeTradingSystem
        fake_system = FakeTradingSystem()
        status = fake_system.get_market_status()
        return {"status": "success", "data": status}
    except Exception as e:
        logger.error(f"Error getting market status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get market status: {str(e)}")

@app.get("/api/config")
async def get_config():
    """Get configuration"""
    return config_manager.config

@app.put("/api/config")
async def update_config(config_data: Dict[str, Any]):
    """Update configuration"""
    try:
        for key, value in config_data.items():
            config_manager.set(key, value)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error updating config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")

# WebSocket for real-time job progress updates
@app.websocket("/ws/jobs")
async def websocket_jobs_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time job progress updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    logger.info("WebSocket client connected")
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

async def broadcast_job_update(job):
    """Broadcast job update to all connected WebSocket clients"""
    if not websocket_connections:
        return
        
    message = {
        "type": "job_progress",
        "job": job.to_dict()
    }
    
    disconnected = []
    for websocket in websocket_connections:
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error broadcasting to websocket: {e}")
            disconnected.append(websocket)
    
    # Remove disconnected clients
    for ws in disconnected:
        if ws in websocket_connections:
            websocket_connections.remove(ws)

# Job Management Endpoints
class HistoricalJobRequest(BaseModel):
    symbol: str
    exchange: str = "NSE"
    interval: str = "1day"
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    product_type: Optional[str] = None
    expiry_date: Optional[str] = None
    strike_price: Optional[str] = None
    right: Optional[str] = None

@app.post("/api/jobs/historical")
async def create_historical_job(request: HistoricalJobRequest):
    """Create a background historical data job"""
    global job_manager
    
    if not job_manager:
        raise HTTPException(status_code=503, detail="Job manager not available")
    
    try:
        # Validate dates
        from_date = request.from_date
        to_date = request.to_date
        
        if not from_date or not to_date:
            # Default to last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            from_date = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            to_date = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        # Create job
        kwargs = {}
        if request.product_type:
            kwargs['product_type'] = request.product_type
        if request.expiry_date:
            kwargs['expiry_date'] = request.expiry_date
        if request.strike_price:
            kwargs['strike_price'] = request.strike_price
        if request.right:
            kwargs['right'] = request.right
            
        job_id = job_manager.create_job(
            symbol=request.symbol,
            exchange=request.exchange,
            interval=request.interval,
            from_date=from_date,
            to_date=to_date,
            **kwargs
        )
        
        # Add progress callback
        job_manager.add_progress_callback(job_id, broadcast_job_update)
        
        # Start the job
        job_manager.start_job(job_id)
        
        return {
            "status": "success",
            "job_id": job_id,
            "message": f"Historical data job created for {request.symbol}"
        }
        
    except Exception as e:
        logger.error(f"Error creating historical job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@app.get("/api/jobs")
async def get_all_jobs():
    """Get all jobs (from memory and database)"""
    global job_manager
    
    try:
        all_jobs = []
        
        # Get jobs from memory (job manager)
        if job_manager:
            memory_jobs = job_manager.get_all_jobs()
            all_jobs.extend([job.to_dict() for job in memory_jobs])
            logger.info(f"Found {len(memory_jobs)} jobs in memory")
        
        # Also get completed jobs from database
        try:
            db_jobs = get_historical_db().get_stored_jobs(50)  # Get last 50 stored jobs
            logger.info(f"Found {len(db_jobs)} jobs in database")
            
            # Merge database jobs with memory jobs (avoid duplicates)
            memory_job_ids = {job['job_id'] for job in all_jobs}
            for db_job in db_jobs:
                if db_job['job_id'] not in memory_job_ids:
                    # Convert database job format to match memory job format
                    db_job_formatted = {
                        'job_id': db_job['job_id'],
                        'symbol': db_job['symbol'],
                        'exchange': db_job['exchange'],
                        'interval': db_job['interval'],
                        'from_date': db_job['from_date'],
                        'to_date': db_job['to_date'],
                        'status': db_job['status'],
                        'progress': {
                            'percentage': 100.0,
                            'message': 'Complete',
                            'details': 'Data stored in database'
                        },
                        'created_at': db_job['created_at'],
                        'completed_at': db_job['completed_at'],
                        'data_count': db_job['total_candles']
                    }
                    all_jobs.append(db_job_formatted)
        except Exception as e:
            logger.warning(f"Could not fetch database jobs: {e}")
        
        logger.info(f"Returning {len(all_jobs)} total jobs")
        return {"jobs": all_jobs}
        
    except Exception as e:
        logger.error(f"Error getting all jobs: {e}")
        return {"jobs": []}

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get specific job by ID"""
    global job_manager
    
    if not job_manager:
        raise HTTPException(status_code=404, detail="Job manager not available")
    
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"job": job.to_dict()}

@app.get("/api/jobs/{job_id}/data")
async def get_job_data(job_id: str):
    """Get job result data (from database or memory)"""
    try:
        # First try to get from database (persistent storage)
        db_data = get_historical_db().get_job_data(job_id)
        if db_data:
            return {
                "status": "success",
                "data": db_data['data'],
                "job_info": {
                    "symbol": db_data['symbol'],
                    "exchange": db_data['exchange'],
                    "interval": db_data['interval'],
                    "from_date": db_data['from_date'],
                    "to_date": db_data['to_date'],
                    "candles_count": len(db_data['data'])
                },
                "source": "database"
            }
        
        # Fallback to in-memory job manager
        global job_manager
        if not job_manager:
            raise HTTPException(status_code=404, detail="Job not found and job manager not available")
        
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status.value != "completed":
            raise HTTPException(status_code=400, detail="Job not completed yet")
        
        return {
            "status": "success",
            "data": job.result_data,
            "job_info": {
                "symbol": job.symbol,
                "exchange": job.exchange,
                "interval": job.interval,
                "from_date": job.from_date,
                "to_date": job.to_date,
                "candles_count": len(job.result_data) if job.result_data else 0
            },
            "source": "memory"
        }
        
    except Exception as e:
        logger.error(f"Error getting job data: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving job data: {str(e)}")

@app.delete("/api/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running job"""
    global job_manager
    
    if not job_manager:
        raise HTTPException(status_code=404, detail="Job manager not available")
    
    success = job_manager.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Job not found or not cancellable")
    
    return {"status": "success", "message": "Job cancelled"}

# Database Management Endpoints
@app.get("/api/historical/database/summary")
async def get_database_summary():
    """Get summary of stored historical data"""
    try:
        summary = get_historical_db().get_available_data_summary()
        stats = get_historical_db().get_database_stats()
        
        return {
            "status": "success",
            "summary": summary,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting database summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving database summary: {str(e)}")

@app.get("/api/historical/database/jobs")
async def get_stored_jobs(limit: int = 100):
    """Get list of stored jobs in database"""
    try:
        jobs = get_historical_db().get_stored_jobs(limit)
        return {
            "status": "success",
            "jobs": jobs
        }
    except Exception as e:
        logger.error(f"Error getting stored jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving stored jobs: {str(e)}")

@app.get("/api/historical/search")
async def search_historical_data(
    symbol: str,
    exchange: str = "NSE",
    interval: str = "1day",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 10000
):
    """Search for existing historical data in database"""
    try:
        data = get_historical_db().search_historical_data(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            from_date=from_date,
            to_date=to_date,
            limit=limit
        )
        
        return {
            "status": "success",
            "data": data,
            "count": len(data),
            "symbol": symbol,
            "exchange": exchange,
            "interval": interval
        }
    except Exception as e:
        logger.error(f"Error searching historical data: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching historical data: {str(e)}")

@app.delete("/api/historical/database/job/{job_id}")
async def delete_job_from_database(job_id: str):
    """Delete job data from database"""
    try:
        success = get_historical_db().delete_job_data(job_id)
        if success:
            return {"status": "success", "message": f"Job {job_id} deleted from database"}
        else:
            raise HTTPException(status_code=404, detail="Job not found in database")
    except Exception as e:
        logger.error(f"Error deleting job from database: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting job: {str(e)}")

@app.delete("/api/historical/database/symbol")
async def delete_symbol_from_database(symbol: str, exchange: str, interval: str):
    """Delete all data for a symbol/exchange/interval combination"""
    try:
        success = get_historical_db().delete_symbol_data(symbol, exchange, interval)
        if success:
            return {"status": "success", "message": f"All data for {symbol} {exchange} {interval} deleted"}
        else:
            raise HTTPException(status_code=404, detail="No data found for the specified symbol")
    except Exception as e:
        logger.error(f"Error deleting symbol data: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting symbol data: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    global trading_system
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "trading_system_connected": trading_system is not None and trading_system.is_connected
    }

if __name__ == "__main__":
    uvicorn.run(
        "trading_system.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
