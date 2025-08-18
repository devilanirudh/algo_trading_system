"""
Trading System Managers - Individual managers for different operations
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

class OrderManager:
    """Order Management - Place, modify, cancel orders"""
    
    def __init__(self, api):
        self.api = api
    
    async def validate_order(self, order_params):
        """Validate order parameters"""
        required_fields = ['stock_code', 'exchange_code', 'action', 'order_type', 'quantity']
        
        for field in required_fields:
            if field not in order_params:
                logger.error(f"Missing required field: {field}")
                return None
        
        # Set default product if not provided
        if 'product' not in order_params:
            # Determine product based on exchange
            if order_params['exchange_code'] in ['NFO', 'BFO']:
                # For derivatives, we need to determine if it's futures or options
                # This would ideally come from the instrument selection, but for now use a default
                # In a real implementation, this should be passed from the frontend based on selected instrument
                order_params['product'] = 'futures'  # Default for derivatives (can be overridden)
            else:
                order_params['product'] = 'cash'  # Default for equity
        else:
            # Product is provided, validate it
            valid_products = ['cash', 'margin', 'futures', 'options']
            if order_params['product'] not in valid_products:
                logger.error(f"Invalid product '{order_params['product']}'. Must be one of: {valid_products}")
                return None
        
        # Validate order type
        if order_params['order_type'] not in ['limit', 'market']:
            logger.error("Invalid order type. Must be 'limit' or 'market'")
            return None
        
        # Validate action
        if order_params['action'] not in ['buy', 'sell']:
            logger.error("Invalid action. Must be 'buy' or 'sell'")
            return None
        
        # Validate price for different order types
        if order_params['order_type'] == 'market':
            # For market orders, price should be 0 or not provided
            order_params['price'] = 0
            logger.info("Market order: price set to 0 (will execute at market price)")
        elif order_params['order_type'] == 'limit':
            # For limit orders, price is required and must be > 0
            price = order_params.get('price', 0)
            if not price or price <= 0:
                logger.error("Limit orders require a valid price > 0")
                return None
        
        return order_params
    
    async def place_order(self, order_params):
        """Place an order"""
        try:
            response = await self.api.place_order(**order_params)
            return response
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return None
    
    async def get_order_list(self, exchange_code="NSE", from_date=None, to_date=None):
        """Get order list"""
        try:
            params = {'exchange_code': exchange_code}
            if from_date:
                params['from_date'] = from_date
            if to_date:
                params['to_date'] = to_date
            
            response = await self.api.get_order_list(**params)
            return response
        except Exception as e:
            logger.error(f"Error getting order list: {str(e)}")
            return None
    
    async def get_order_detail(self, order_id, exchange_code):
        """Get order detail"""
        try:
            response = await self.api.get_order_detail(
                order_id=order_id,
                exchange_code=exchange_code
            )
            return response
        except Exception as e:
            logger.error(f"Error getting order detail: {str(e)}")
            return None
    
    async def cancel_order(self, order_id, exchange_code):
        """Cancel an order"""
        try:
            response = await self.api.cancel_order(
                order_id=order_id,
                exchange_code=exchange_code
            )
            return response
        except Exception as e:
            logger.error(f"Error canceling order: {str(e)}")
            return None
    
    async def modify_order(self, order_id, modifications):
        """Modify an order"""
        try:
            params = {'order_id': order_id, **modifications}
            response = await self.api.modify_order(**params)
            return response
        except Exception as e:
            logger.error(f"Error modifying order: {str(e)}")
            return None
    
    async def get_trade_list(self, from_date=None, to_date=None, exchange_code="NSE"):
        """Get trade list"""
        try:
            params = {'exchange_code': exchange_code}
            if from_date:
                params['from_date'] = from_date
            if to_date:
                params['to_date'] = to_date
            
            response = await self.api.get_trade_list(**params)
            return response
        except Exception as e:
            logger.error(f"Error getting trade list: {str(e)}")
            return None


class PortfolioManager:
    """Portfolio Management - Holdings, positions, funds"""
    
    def __init__(self, api):
        self.api = api
    
    async def get_demat_holdings(self):
        """Get demat holdings"""
        try:
            response = await self.api.get_demat_holdings()
            return response
        except Exception as e:
            logger.error(f"Error getting demat holdings: {str(e)}")
            return None
    
    async def get_portfolio_holdings(self, exchange_code="", from_date="", to_date="", stock_code="", portfolio_type=""):
        """Get portfolio holdings"""
        try:
            params = {
                'exchange_code': exchange_code,
                'from_date': from_date,
                'to_date': to_date,
                'stock_code': stock_code,
                'portfolio_type': portfolio_type
            }
            response = await self.api.get_portfolio_holdings(**params)
            return response
        except Exception as e:
            logger.error(f"Error getting portfolio holdings: {str(e)}")
            return None
    
    async def get_positions(self):
        """Get portfolio positions"""
        try:
            response = await self.api.get_portfolio_positions()
            return response
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return None
    
    async def get_funds(self):
        """Get funds"""
        try:
            response = await self.api.get_funds()
            return response
        except Exception as e:
            logger.error(f"Error getting funds: {str(e)}")
            return None
    
    async def get_margin(self, exchange_code="NSE"):
        """Get margin"""
        try:
            response = await self.api.get_margin(exchange_code=exchange_code)
            return response
        except Exception as e:
            logger.error(f"Error getting margin: {str(e)}")
            return None
    
    async def set_funds(self, transaction_type, amount, segment):
        """Set funds"""
        try:
            response = await self.api.set_funds(
                transaction_type=transaction_type,
                amount=amount,
                segment=segment
            )
            return response
        except Exception as e:
            logger.error(f"Error setting funds: {str(e)}")
            return None


class MarketDataManager:
    """Market Data Management - Quotes, option chains"""
    
    def __init__(self, api):
        self.api = api
    
    async def get_quotes(self, stock_code, exchange_code, **kwargs):
        """Get quotes for a stock"""
        try:
            response = await self.api.get_quotes(
                stock_code=stock_code,
                exchange_code=exchange_code,
                **kwargs
            )
            return response
        except Exception as e:
            logger.error(f"Error getting quotes: {str(e)}")
            return None
    
    async def get_option_chain(self, stock_code, exchange_code, product_type, expiry_date, **kwargs):
        """Get option chain"""
        try:
            params = {
                'stock_code': stock_code,
                'exchange_code': exchange_code,
                'product_type': product_type,
                'expiry_date': expiry_date,
                **kwargs
            }
            response = await self.api.get_option_chain_quotes(**params)
            return response
        except Exception as e:
            logger.error(f"Error getting option chain: {str(e)}")
            return None
    
    async def get_stock_names(self, exchange_code, stock_code):
        """Get stock names and tokens"""
        try:
            response = await self.api.get_stock_names(exchange_code, stock_code)
            return response
        except Exception as e:
            logger.error(f"Error getting stock names: {str(e)}")
            return None


class HistoricalDataManager:
    """Historical Data Management - OHLCV data with technical indicators"""
    
    def __init__(self, api):
        self.api = api
    
    async def get_data(self, symbol, exchange, interval="1day", days=30, from_date=None, to_date=None, **kwargs):
        """Get historical data with automatic chunking to bypass 1000 candle limit"""
        try:
            # Use provided dates or calculate from days
            if not from_date or not to_date:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                from_date = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                to_date = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
            # Parse dates
            from datetime import datetime
            start_dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            
            # Calculate total duration and check if chunking is needed
            total_duration = end_dt - start_dt
            estimated_candles = self._estimate_candles(interval, total_duration)
            
            logger.info(f"Estimated candles: {estimated_candles} for interval {interval}")
            
            # If estimated candles > 950 (safety margin), use chunking
            if estimated_candles > 950:
                return await self._get_chunked_data(symbol, exchange, interval, start_dt, end_dt, **kwargs)
            else:
                return await self._get_single_data(symbol, exchange, interval, from_date, to_date, **kwargs)
                
        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}")
            return None
    
    def _estimate_candles(self, interval, total_duration):
        """Estimate number of candles based on interval and duration, respecting market hours"""
        # Market hours: 9:15 AM to 3:30 PM IST = 6 hours 15 minutes = 22,500 seconds per day
        market_seconds_per_day = 22500
        
        interval_seconds = {
            '1second': 1,
            '1minute': 60,
            '5minute': 300,
            '30minute': 1800,
            '1day': market_seconds_per_day  # Only market hours count
        }
        
        if interval == '1day':
            # For daily candles, count trading days (approximately)
            total_days = total_duration.days
            trading_days = total_days * 5 / 7  # Rough estimate: 5 trading days per week
            return int(trading_days)
        else:
            # For intraday intervals, calculate based on market hours only
            total_days = total_duration.days + (total_duration.seconds / 86400)
            trading_days = total_days * 5 / 7  # Approximate trading days
            total_market_seconds = trading_days * market_seconds_per_day
            
            return int(total_market_seconds / interval_seconds.get(interval, 86400))
    
    def _calculate_chunk_duration(self, interval):
        """Calculate optimal chunk duration to stay under 1000 candles, respecting market hours"""
        # Use 950 candles as safety margin
        safe_candles = 950
        
        # Market hours: 9:15 AM to 3:30 PM IST = 6 hours 15 minutes = 22,500 seconds per day
        if interval == '1second':
            # 950 seconds = ~16 minutes of market time
            return timedelta(seconds=safe_candles)
        elif interval == '1minute':
            # 950 minutes = ~16 hours of market time ≈ 2.5 trading days
            return timedelta(days=3)  # Use 3 days to account for weekends
        elif interval == '5minute':
            # 950 * 5 minutes = ~79 hours of market time ≈ 12.6 trading days
            return timedelta(days=15)  # Use 15 days to account for weekends
        elif interval == '30minute':
            # 950 * 30 minutes = ~475 hours of market time ≈ 76 trading days
            return timedelta(days=90)  # Use 90 days to account for weekends
        elif interval == '1day':
            # 950 trading days ≈ 3.8 years (accounting for weekends/holidays)
            return timedelta(days=950)
        else:
            return timedelta(days=30)
    
    async def _get_chunked_data(self, symbol, exchange, interval, start_dt, end_dt, **kwargs):
        """Get historical data in chunks and combine results"""
        try:
            chunk_duration = self._calculate_chunk_duration(interval)
            all_data = []
            current_start = start_dt
            chunk_num = 1
            
            logger.info(f"Starting chunked data fetch from {start_dt} to {end_dt}")
            logger.info(f"Chunk duration: {chunk_duration}, Interval: {interval}")
            
            while current_start < end_dt:
                current_end = min(current_start + chunk_duration, end_dt)
                
                # Format dates for API
                chunk_from = current_start.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                chunk_to = current_end.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                
                logger.info(f"Fetching chunk {chunk_num}: {chunk_from} to {chunk_to}")
                
                # Get data for this chunk
                chunk_response = await self._get_single_data(
                    symbol, exchange, interval, chunk_from, chunk_to, **kwargs
                )
                
                if chunk_response and 'Success' in chunk_response and chunk_response['Success']:
                    chunk_data = chunk_response['Success']
                    all_data.extend(chunk_data)
                    logger.info(f"Chunk {chunk_num}: Got {len(chunk_data)} candles ({len(all_data)} total)")
                elif chunk_response and 'Error' in chunk_response:
                    logger.error(f"Chunk {chunk_num} failed: {chunk_response['Error']}")
                    # Continue with next chunk instead of failing completely
                else:
                    logger.warning(f"Chunk {chunk_num}: No data received")
                
                current_start = current_end
                chunk_num += 1
                
                # Add small delay between requests to avoid rate limiting
                await asyncio.sleep(0.2)  # Slightly longer delay
            
            # Remove duplicates and sort by datetime
            if all_data:
                # Remove duplicates based on datetime
                seen_times = set()
                unique_data = []
                for candle in all_data:
                    dt = candle.get('datetime')
                    if dt and dt not in seen_times:
                        seen_times.add(dt)
                        unique_data.append(candle)
                
                # Sort by datetime
                unique_data.sort(key=lambda x: x.get('datetime', ''))
                
                logger.info(f"Chunked fetch complete: {len(unique_data)} total candles from {chunk_num-1} chunks")
                
                return {
                    'Success': unique_data,
                    'Status': 200,
                    'Error': None,
                    'chunked': True,
                    'chunks_fetched': chunk_num - 1
                }
            else:
                return {
                    'Success': [],
                    'Status': 200,
                    'Error': None,
                    'chunked': True,
                    'chunks_fetched': chunk_num - 1
                }
                
        except Exception as e:
            logger.error(f"Error in chunked data fetch: {str(e)}")
            return {
                'Success': [],
                'Status': 500,
                'Error': f"Chunked fetch failed: {str(e)}",
                'chunked': True
            }
    
    async def _get_single_data(self, symbol, exchange, interval, from_date, to_date, **kwargs):
        """Get historical data for a single request (original logic)"""
        try:
            params = {
                'interval': interval,
                'from_date': from_date,
                'to_date': to_date,
                'stock_code': symbol,
                'exchange_code': exchange
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
            
            logger.info(f"Getting single historical data with params: {params}")
            
            response = await self.api.get_historical_data_v2(**params)
            
            # Return the full response for better error handling
            if response:
                return response
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting single historical data: {str(e)}")
            return None
    
    async def add_technical_indicators(self, data):
        """Add technical indicators to data"""
        try:
            if not data:
                return None
            
            df = pd.DataFrame(data)
            
            # Convert price columns to numeric
            price_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in price_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Add technical indicators
            df = self._add_sma(df)
            df = self._add_ema(df)
            df = self._add_rsi(df)
            df = self._add_macd(df)
            df = self._add_bollinger_bands(df)
            
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error adding technical indicators: {str(e)}")
            return data
    
    def _add_sma(self, df, periods=[20, 50]):
        """Add Simple Moving Average"""
        for period in periods:
            df[f'SMA_{period}'] = df['close'].rolling(window=period).mean()
        return df
    
    def _add_ema(self, df, periods=[12, 26]):
        """Add Exponential Moving Average"""
        for period in periods:
            df[f'EMA_{period}'] = df['close'].ewm(span=period).mean()
        return df
    
    def _add_rsi(self, df, period=14):
        """Add Relative Strength Index"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df
    
    def _add_macd(self, df, fast=12, slow=26, signal=9):
        """Add MACD"""
        df['EMA_fast'] = df['close'].ewm(span=fast).mean()
        df['EMA_slow'] = df['close'].ewm(span=slow).mean()
        df['MACD'] = df['EMA_fast'] - df['EMA_slow']
        df['MACD_signal'] = df['MACD'].ewm(span=signal).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
        return df
    
    def _add_bollinger_bands(self, df, period=20, std=2):
        """Add Bollinger Bands"""
        df['BB_middle'] = df['close'].rolling(window=period).mean()
        bb_std = df['close'].rolling(window=period).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * std)
        df['BB_lower'] = df['BB_middle'] - (bb_std * std)
        return df


class RealTimeManager:
    """Real-time Data Management - WebSocket streaming"""
    
    def __init__(self, api):
        self.api = api
        self.is_connected = False
        self.subscriptions = []
        self.callback = None
        # CSV logging
        self._csv_enabled = True
        self._csv_file = None
        self._csv_writer = None
        self._csv_headers_written = False
        self._current_log_date = None
    
    async def start_streaming(self, symbols, callback=None):
        """Start real-time streaming"""
        try:
            if not self.api.is_authenticated:
                logger.error("Not authenticated")
                return False
            
            self.callback = callback
            
            # Connect to WebSocket
            if not self.api.ws_connect():
                logger.error("Failed to connect to WebSocket")
                return False
            
            # Attach tick handler
            try:
                # BreezeConnect calls this sync callback from its own thread
                self.api.breeze.on_ticks = self._on_ticks
            except Exception as e:
                logger.error(f"Failed to attach on_ticks handler: {e}")
                return False
            
            self.is_connected = True
            
            # Prepare CSV logger
            self._ensure_csv_logger()
            
            # Subscribe to symbols
            for symbol in symbols:
                if isinstance(symbol, dict):
                    # Complex subscription with parameters
                    success = self.api.subscribe_feeds(**symbol)
                else:
                    # Simple stock token subscription
                    success = self.api.subscribe_feeds(stock_token=symbol)
                
                if success:
                    self.subscriptions.append(symbol)
                    logger.info(f"Subscribed to {symbol}")
                else:
                    logger.error(f"Failed to subscribe to {symbol}")
            
            return True
        except Exception as e:
            logger.error(f"Error starting streaming: {str(e)}")
            return False
    
    async def stop_streaming(self):
        """Stop real-time streaming"""
        try:
            # Unsubscribe from all feeds
            for subscription in self.subscriptions:
                if isinstance(subscription, dict):
                    self.api.unsubscribe_feeds(**subscription)
                else:
                    self.api.unsubscribe_feeds(stock_token=subscription)
            
            # Disconnect WebSocket
            self.api.ws_disconnect()
            
            self.is_connected = False
            self.subscriptions = []
            self.callback = None
            
            logger.info("Real-time streaming stopped")
        except Exception as e:
            logger.error(f"Error stopping streaming: {str(e)}")

    # Internal helpers for CSV logging and tick handling
    def _ensure_csv_logger(self):
        """Ensure CSV logger is ready for today's date"""
        try:
            import os
            from datetime import datetime
            import csv
            log_dir = os.path.join(os.path.dirname(__file__), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            today = datetime.now().strftime('%Y%m%d')
            if self._current_log_date != today or self._csv_file is None:
                # Close previous file if open
                try:
                    if self._csv_file:
                        self._csv_file.flush()
                        self._csv_file.close()
                except Exception:
                    pass
                file_path = os.path.join(log_dir, f'ws_ticks_{today}.csv')
                # Open in append mode
                self._csv_file = open(file_path, 'a', newline='')
                self._csv_writer = csv.writer(self._csv_file)
                self._csv_headers_written = os.path.getsize(file_path) > 0
                if not self._csv_headers_written:
                    self._csv_writer.writerow(['timestamp', 'tick_json'])
                    self._csv_headers_written = True
                self._current_log_date = today
        except Exception as e:
            logger.error(f"Failed to prepare CSV logger: {e}")
            self._csv_enabled = False
    
    def _write_csv_tick(self, ticks):
        """Write raw tick JSON into CSV with timestamp"""
        if not self._csv_enabled:
            return
        try:
            import json
            from datetime import datetime
            self._ensure_csv_logger()
            if self._csv_writer:
                ts = datetime.now().isoformat()
                self._csv_writer.writerow([ts, json.dumps(ticks, ensure_ascii=False)])
                # Flush occasionally to avoid data loss
                try:
                    self._csv_file.flush()
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Failed to write tick to CSV: {e}")
            self._csv_enabled = False
    
    def _on_ticks(self, ticks):
        """Breeze on_ticks callback (sync). Logs and forwards ticks."""
        try:
            # 1) CSV logging of raw payload
            self._write_csv_tick(ticks)
            # 2) Forward to external callback if provided
            if self.callback:
                try:
                    self.callback(ticks)
                except Exception as cb_err:
                    logger.error(f"Realtime callback error: {cb_err}")
        except Exception as e:
            logger.error(f"on_ticks handler error: {e}")


class GTTManager:
    """GTT (Good Till Trigger) Order Management"""
    
    def __init__(self, api):
        self.api = api
    
    async def place_single_gtt(self, gtt_params):
        """Place single leg GTT order"""
        try:
            response = await self.api.gtt_single_leg_place_order(**gtt_params)
            return response
        except Exception as e:
            logger.error(f"Error placing single GTT order: {str(e)}")
            return None
    
    async def place_oco_gtt(self, gtt_params):
        """Place OCO (One Cancels Other) GTT order"""
        try:
            response = await self.api.gtt_three_leg_place_order(**gtt_params)
            return response
        except Exception as e:
            logger.error(f"Error placing OCO GTT order: {str(e)}")
            return None
    
    async def modify_gtt(self, gtt_order_id, modifications, gtt_type="single"):
        """Modify GTT order"""
        try:
            if gtt_type == "single":
                response = await self.api.gtt_single_leg_modify_order(
                    gtt_order_id=gtt_order_id,
                    **modifications
                )
            else:
                response = await self.api.gtt_three_leg_modify_order(
                    gtt_order_id=gtt_order_id,
                    **modifications
                )
            return response
        except Exception as e:
            logger.error(f"Error modifying GTT order: {str(e)}")
            return None
    
    async def cancel_gtt(self, gtt_order_id, gtt_type="single"):
        """Cancel GTT order"""
        try:
            if gtt_type == "single":
                response = await self.api.gtt_single_leg_cancel_order(
                    gtt_order_id=gtt_order_id
                )
            else:
                response = await self.api.gtt_three_leg_cancel_order(
                    gtt_order_id=gtt_order_id
                )
            return response
        except Exception as e:
            logger.error(f"Error canceling GTT order: {str(e)}")
            return None
    
    async def get_gtt_orders(self, exchange_code, from_date=None, to_date=None):
        """Get GTT order book"""
        try:
            params = {'exchange_code': exchange_code}
            if from_date:
                params['from_date'] = from_date
            if to_date:
                params['to_date'] = to_date
            
            response = await self.api.gtt_order_book(**params)
            return response
        except Exception as e:
            logger.error(f"Error getting GTT orders: {str(e)}")
            return None


class CalculatorManager:
    """Calculator Management - Margin, limit calculations"""
    
    def __init__(self, api):
        self.api = api
    
    async def calculate_margin(self, orders, exchange_code="NFO"):
        """Calculate margin for orders"""
        try:
            response = await self.api.margin_calculator(orders, exchange_code)
            return response
        except Exception as e:
            logger.error(f"Error calculating margin: {str(e)}")
            return None
    
    async def calculate_limit(self, **kwargs):
        """Calculate limit for order"""
        try:
            response = await self.api.limit_calculator(**kwargs)
            return response
        except Exception as e:
            logger.error(f"Error calculating limit: {str(e)}")
            return None
    
    async def preview_order(self, **kwargs):
        """Preview order with charges"""
        try:
            response = await self.api.preview_order(**kwargs)
            return response
        except Exception as e:
            logger.error(f"Error previewing order: {str(e)}")
            return None
