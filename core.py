"""
Core Trading System - Main orchestrator for all trading operations
"""
from api import BreezeAPI
from managers import *
from fake_trading import FakeTradingSystem
from instruments_manager import InstrumentsManager
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class TradingSystem:
    """
    Main Trading System class that orchestrates all trading operations
    Provides unified interface for all Breeze Connect features
    """
    
    def __init__(self, api_key=None, api_secret=None, session_token=None):
        """
        Initialize the trading system
        
        Args:
            api_key: Breeze Connect API key
            api_secret: Breeze Connect API secret  
            session_token: Session token from login
        """
        self.api = BreezeAPI(api_key, api_secret, session_token)
        
        # Initialize all managers
        self.orders = OrderManager(self.api)
        self.portfolio = PortfolioManager(self.api)
        self.market = MarketDataManager(self.api)
        self.historical = HistoricalDataManager(self.api)
        self.realtime = RealTimeManager(self.api)
        self.gtt = GTTManager(self.api)
        self.calculator = CalculatorManager(self.api)
        
        # Initialize fake trading system
        self.fake_trading = FakeTradingSystem()
        
        # Initialize instruments manager
        self.instruments = InstrumentsManager()
        
        self.is_connected = False
        self.session_id = None
        
    async def initialize(self):
        """Initialize the trading system and authenticate"""
        try:
            logger.info("Initializing Trading System...")
            
            # Refresh instruments data
            logger.info("Refreshing instruments data...")
            await self.instruments.refresh_instruments()
            
            # Authenticate with Breeze Connect
            success = await self.api.authenticate()
            if not success:
                logger.error("Authentication failed")
                return False
                
            self.is_connected = True
            self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Trading System initialized successfully. Session: {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing trading system: {str(e)}")
            return False
    
    async def get_portfolio_summary(self):
        """Get comprehensive portfolio summary"""
        try:
            # Get real portfolio data
            funds_data = await self.portfolio.get_funds()
            holdings_data = await self.portfolio.get_demat_holdings()
            positions_data = await self.portfolio.get_positions()
            margin_data = await self.portfolio.get_margin()
            
            # Extract key values for dashboard
            total_balance = 0
            cash_balance = 0
            total_unrealized_pnl = 0
            holdings_count = 0
            
            # Process funds data
            if funds_data and 'Success' in funds_data:
                funds = funds_data['Success']
                logger.info(f"Processing funds data: {funds}")
                
                # Use unallocated_balance if total_bank_balance is 0
                total_balance = funds.get('total_bank_balance', 0)
                logger.info(f"Initial total_balance from total_bank_balance: {total_balance}")
                
                if total_balance == 0:
                    unallocated = funds.get('unallocated_balance', '0')
                    logger.info(f"Using unallocated_balance: {unallocated} (type: {type(unallocated)})")
                    try:
                        total_balance = float(unallocated)
                        logger.info(f"Converted unallocated_balance to float: {total_balance}")
                    except (ValueError, TypeError) as e:
                        logger.error(f"Error converting unallocated_balance '{unallocated}' to float: {e}")
                        total_balance = 0
                
                cash_balance = total_balance  # Using total balance as cash
                logger.info(f"Final total_balance: {total_balance}, cash_balance: {cash_balance}")
            
            # Process holdings data
            if holdings_data and 'Success' in holdings_data:
                holdings = holdings_data['Success']
                logger.info(f"Processing holdings data: {holdings}")
                logger.info(f"Holdings type: {type(holdings)}")
                logger.info(f"Holdings data structure: {holdings}")
                
                if isinstance(holdings, list):
                    holdings_count = len(holdings)
                    logger.info(f"Holdings is a list with {holdings_count} items")
                elif isinstance(holdings, dict) and 'holdings' in holdings:
                    # Sometimes the API returns {'holdings': [...]}
                    holdings_list = holdings['holdings']
                    if isinstance(holdings_list, list):
                        holdings_count = len(holdings_list)
                        logger.info(f"Holdings found in dict with {holdings_count} items")
                    else:
                        holdings_count = 0
                        logger.info(f"Holdings dict contains non-list data")
                else:
                    holdings_count = 0
                    logger.info(f"Holdings is not a list or dict with holdings key, setting count to 0")
            
            # Process positions data for P&L
            if positions_data and 'Success' in positions_data:
                positions = positions_data['Success']
                if isinstance(positions, list):
                    for position in positions:
                        pnl = position.get('pnl', 0)
                        if pnl:
                            total_unrealized_pnl += float(pnl)
            
            # Fix parsing: Ensure correct values from raw data
            if total_balance == 0 and funds_data and 'Success' in funds_data:
                funds = funds_data['Success']
                unallocated = funds.get('unallocated_balance', '0')
                try:
                    total_balance = float(unallocated)
                    cash_balance = total_balance
                except:
                    pass
            
            if holdings_count == 0 and holdings_data and 'Success' in holdings_data:
                holdings = holdings_data['Success']
                if isinstance(holdings, list):
                    holdings_count = len(holdings)
            
            # Format real summary for dashboard
            real_summary = {
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat(),
                'total_balance': total_balance,
                'cash_balance': cash_balance,
                'total_unrealized_pnl': total_unrealized_pnl,
                'holdings_count': holdings_count,
                'raw_funds': funds_data,
                'raw_holdings': holdings_data,
                'raw_positions': positions_data,
                'raw_margin': margin_data
            }
            
            # Log the parsed values for debugging
            logger.info(f"Parsed portfolio summary: total_balance={total_balance}, cash_balance={cash_balance}, holdings_count={holdings_count}, pnl={total_unrealized_pnl}")
            
            # TEMPORARY: Force correct values for testing
            if total_balance == 0 and funds_data and 'Success' in funds_data:
                funds = funds_data['Success']
                unallocated = funds.get('unallocated_balance', '0')
                try:
                    total_balance = float(unallocated)
                    cash_balance = total_balance
                    logger.info(f"FORCED FIX: Set total_balance and cash_balance to {total_balance}")
                except:
                    pass
            
            if holdings_count == 0 and holdings_data and 'Success' in holdings_data:
                holdings = holdings_data['Success']
                if isinstance(holdings, list) and len(holdings) > 0:
                    holdings_count = len(holdings)
                    logger.info(f"FORCED FIX: Set holdings_count to {holdings_count}")
            
            # Get fake trading summary
            fake_summary = self.fake_trading.get_portfolio_summary()
            
            # Combine both summaries
            summary = {
                **real_summary,
                'fake_trading': fake_summary,
                'is_simulation': True
            }
            return summary
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {str(e)}")
            return None
    
    async def get_market_watch(self, symbols=None):
        """Get live market watch for symbols"""
        try:
            if not symbols:
                symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK']
            
            watchlist = []
            for symbol in symbols:
                quote = await self.market.get_quotes(symbol, 'NSE')
                if quote:
                    watchlist.append(quote)
            
            return watchlist
        except Exception as e:
            logger.error(f"Error getting market watch: {str(e)}")
            return []
    
    async def place_order(self, order_params):
        """Place an order (real or fake based on connection)"""
        try:
            # Validate order parameters
            validated_params = await self.orders.validate_order(order_params)
            if not validated_params:
                return None
            
            # Check if we're connected to real API
            if self.is_connected and self.api:
                # Place real order
                logger.info(f"Placing REAL order: {validated_params}")
                real_response = await self.orders.place_order(validated_params)
                
                if real_response and real_response.get('Status') == 200:
                    logger.info(f"REAL ORDER PLACED: {real_response}")
                    return {
                        'status': 'success',
                        'message': 'Real order placed successfully',
                        'order_id': real_response.get('Success', {}).get('order_id'),
                        'is_simulation': False,
                        'api_response': real_response
                    }
                else:
                    logger.error(f"Real order failed: {real_response}")
                    return {
                        'status': 'failed',
                        'message': f'Real order failed: {real_response.get("Error", "Unknown error")}',
                        'is_simulation': False,
                        'api_response': real_response
                    }
            else:
                # Place fake order
                logger.info(f"Placing FAKE order: {validated_params}")
                fake_response = self.fake_trading.place_fake_order(validated_params)
                
                logger.info(f"FAKE ORDER PLACED: {fake_response}")
                return {
                    'status': 'success',
                    'message': 'Fake order placed successfully (no real execution)',
                    'order_id': fake_response.get('order_id'),
                    'is_simulation': True
                }
            
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return {
                'status': 'failed',
                'message': f'Error placing order: {str(e)}',
                'is_simulation': False
            }
    
    async def get_historical_data(self, **kwargs):
        """Get historical data with support for derivatives and technical indicators"""
        try:
            # Extract parameters
            symbol = kwargs.get('stock_code')
            exchange = kwargs.get('exchange_code', 'NSE')
            interval = kwargs.get('interval', '1day')
            from_date = kwargs.get('from_date')
            to_date = kwargs.get('to_date')
            
            # If using the old format with days parameter
            if 'days' in kwargs and not from_date:
                days = kwargs.get('days', 30)
                from datetime import datetime, timedelta
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                from_date = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                to_date = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
            # Build parameters for historical data manager
            params = {
                'symbol': symbol,
                'exchange': exchange,
                'interval': interval,
                'from_date': from_date,
                'to_date': to_date
            }
            
            # Add derivative-specific parameters
            if exchange in ['NFO', 'BFO']:
                # Determine product type for derivatives
                if 'product_type' in kwargs and kwargs['product_type'] in ['options', 'futures']:
                    params['product_type'] = kwargs['product_type']
                elif 'right' in kwargs and kwargs['right'] in ['CE', 'PE', 'call', 'put']:
                    params['product_type'] = 'options'
                else:
                    params['product_type'] = 'futures'  # Default for NFO/BFO
                
                if 'expiry_date' in kwargs:
                    params['expiry_date'] = kwargs['expiry_date']
                if 'strike_price' in kwargs:
                    params['strike_price'] = kwargs['strike_price']
                if 'right' in kwargs:
                    # Convert option type to API format
                    right = kwargs['right']
                    if right in ['CE', 'call']:
                        params['right'] = 'call'
                    elif right in ['PE', 'put']:
                        params['right'] = 'put'
                    else:
                        params['right'] = 'others'
            
            logger.info(f"Getting historical data with params: {params}")
            
            # Get data from historical data manager
            data = await self.historical.get_data(**params)
            
            # Return the full response for better error handling
            return data
        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}")
            return None
    
    async def start_realtime_streaming(self, symbols, callback=None):
        """Start real-time data streaming"""
        try:
            await self.realtime.start_streaming(symbols, callback)
            return True
        except Exception as e:
            logger.error(f"Error starting real-time streaming: {str(e)}")
            return False
    
    async def place_gtt_order(self, gtt_params):
        """Place GTT (Good Till Trigger) order"""
        try:
            return await self.gtt.place_order(gtt_params)
        except Exception as e:
            logger.error(f"Error placing GTT order: {str(e)}")
            return None
    
    async def get_option_chain(self, symbol, expiry_date):
        """Get option chain for symbol"""
        try:
            return await self.market.get_option_chain(symbol, expiry_date)
        except Exception as e:
            logger.error(f"Error getting option chain: {str(e)}")
            return None
    
    async def calculate_margin(self, orders):
        """Calculate margin for orders"""
        try:
            return await self.calculator.calculate_margin(orders)
        except Exception as e:
            logger.error(f"Error calculating margin: {str(e)}")
            return None
    
    async def get_order_status(self, order_id, exchange_code):
        """Get order status"""
        try:
            return await self.orders.get_order_detail(order_id, exchange_code)
        except Exception as e:
            logger.error(f"Error getting order status: {str(e)}")
            return None
    
    async def get_user_details(self):
        """Get user details"""
        try:
            if self.api and self.is_connected:
                return await self.api.get_user_details()
            else:
                logger.warning("Trading system not connected")
                return None
        except Exception as e:
            logger.error(f"Error getting user details: {str(e)}")
            return None
    
    async def cancel_order(self, order_id, exchange_code):
        """Cancel an order"""
        try:
            return await self.orders.cancel_order(order_id, exchange_code)
        except Exception as e:
            logger.error(f"Error canceling order: {str(e)}")
            return None
    
    async def modify_order(self, order_id, modifications):
        """Modify an existing order"""
        try:
            return await self.orders.modify_order(order_id, modifications)
        except Exception as e:
            logger.error(f"Error modifying order: {str(e)}")
            return None
    
    async def get_trade_history(self, from_date=None, to_date=None):
        """Get trade history"""
        try:
            return await self.orders.get_trade_list(from_date, to_date)
        except Exception as e:
            logger.error(f"Error getting trade history: {str(e)}")
            return None
    
    # Fake trading methods
    def get_fake_funds(self):
        """Get fake funds"""
        return self.fake_trading.get_funds()
    
    def get_fake_holdings(self):
        """Get fake holdings"""
        return self.fake_trading.get_holdings()
    
    def get_fake_ledger(self, limit=100):
        """Get fake ledger"""
        return self.fake_trading.get_ledger(limit)
    
    def get_fake_orders(self, status=None):
        """Get fake orders"""
        return self.fake_trading.get_orders(status)
    
    def execute_fake_order(self, order_id, execution_price):
        """Execute a fake order"""
        return self.fake_trading.execute_fake_order(order_id, execution_price)
    
    def store_historical_data(self, symbol, exchange, data, interval="1day"):
        """Store historical data in fake system"""
        return self.fake_trading.store_historical_data(symbol, exchange, data, interval)
    
    def get_fake_historical_data(self, symbol, exchange, from_date=None, to_date=None, interval="1day"):
        """Get historical data from fake system"""
        return self.fake_trading.get_historical_data(symbol, exchange, from_date, to_date, interval)
    
    def export_fake_data_to_csv(self, table_name, filename, conditions=None):
        """Export fake data to CSV"""
        return self.fake_trading.export_to_csv(table_name, filename, conditions)
    
    async def disconnect(self):
        """Disconnect from all services"""
        try:
            await self.realtime.stop_streaming()
            self.is_connected = False
            logger.info("Trading System disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting: {str(e)}")
    
    def __enter__(self):
        return self
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
