"""
Fake Trading System - Simulated trading with DuckDB backend
No real orders are placed, all operations are simulated
"""
import duckdb
import pandas as pd
import logging
from datetime import datetime, timedelta, time
import pytz
from typing import Dict, List, Optional, Any
import json
import os

logger = logging.getLogger(__name__)

class FakeTradingSystem:
    """Fake trading system with DuckDB backend"""
    
    def __init__(self, db_path="fake_trading.db"):
        self.db_path = db_path
        self.conn = None
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize DuckDB database with required tables"""
        try:
            self.conn = duckdb.connect(self.db_path)
            
            # Create funds table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS funds (
                    id INTEGER PRIMARY KEY,
                    cash_balance DECIMAL(15,2) DEFAULT 1000000.00,
                    equity_balance DECIMAL(15,2) DEFAULT 0.00,
                    fno_balance DECIMAL(15,2) DEFAULT 0.00,
                    commodity_balance DECIMAL(15,2) DEFAULT 0.00,
                    currency_balance DECIMAL(15,2) DEFAULT 0.00,
                    total_balance DECIMAL(15,2) DEFAULT 1000000.00,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create ledger table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS ledger (
                    id INTEGER PRIMARY KEY,
                    transaction_id VARCHAR(50) UNIQUE,
                    transaction_type VARCHAR(20),
                    symbol VARCHAR(20),
                    exchange VARCHAR(10),
                    action VARCHAR(10),
                    quantity INTEGER,
                    price DECIMAL(10,2),
                    total_amount DECIMAL(15,2),
                    segment VARCHAR(20),
                    status VARCHAR(20),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    remarks TEXT
                )
            """)
            
            # Create holdings table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS holdings (
                    id INTEGER PRIMARY KEY,
                    symbol VARCHAR(20),
                    exchange VARCHAR(10),
                    quantity INTEGER DEFAULT 0,
                    average_price DECIMAL(10,2) DEFAULT 0.00,
                    current_price DECIMAL(10,2) DEFAULT 0.00,
                    market_value DECIMAL(15,2) DEFAULT 0.00,
                    unrealized_pnl DECIMAL(15,2) DEFAULT 0.00,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create orders table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY,
                    order_id VARCHAR(50) UNIQUE,
                    symbol VARCHAR(20),
                    exchange VARCHAR(10),
                    action VARCHAR(10),
                    order_type VARCHAR(20),
                    quantity INTEGER,
                    price DECIMAL(10,2),
                    status VARCHAR(20),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed_quantity INTEGER DEFAULT 0,
                    average_price DECIMAL(10,2) DEFAULT 0.00
                )
            """)
            
            # Create market_watch table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS market_watch (
                    id INTEGER PRIMARY KEY,
                    symbol VARCHAR(20),
                    exchange VARCHAR(10),
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, exchange)
                )
            """)
            
            # Create initialization tracking table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS system_flags (
                    flag_name VARCHAR(50) PRIMARY KEY,
                    flag_value BOOLEAN,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create historical_data table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS historical_data (
                    id INTEGER PRIMARY KEY,
                    symbol VARCHAR(20),
                    exchange VARCHAR(10),
                    date DATE,
                    open DECIMAL(10,2),
                    high DECIMAL(10,2),
                    low DECIMAL(10,2),
                    close DECIMAL(10,2),
                    volume BIGINT,
                    interval VARCHAR(20),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Initialize funds if empty
            result = self.conn.execute("SELECT COUNT(*) FROM funds").fetchone()[0]
            if result == 0:
                self.conn.execute("""
                    INSERT INTO funds (id, cash_balance, equity_balance, fno_balance, commodity_balance, currency_balance, total_balance) 
                    VALUES (1, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00)
                """)
            
            self.conn.commit()
            logger.info("Fake trading database initialized successfully")
            
            # Initialize default market watch symbols if table is empty
            self.initialize_default_market_watch()
                
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def get_funds(self) -> Dict[str, Any]:
        """Get current funds"""
        try:
            result = self.conn.execute("SELECT * FROM funds WHERE id = 1").fetchone()
            if result:
                return {
                    'cash_balance': float(result[1]),
                    'equity_balance': float(result[2]),
                    'fno_balance': float(result[3]),
                    'commodity_balance': float(result[4]),
                    'currency_balance': float(result[5]),
                    'total_balance': float(result[6]),
                    'last_updated': result[7]
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting funds: {str(e)}")
            return {}
    
    def update_funds(self, amount: float, transaction_type: str, segment: str = "cash"):
        """Update funds based on transaction"""
        try:
            if transaction_type == "debit":
                amount = -abs(amount)
            else:
                amount = abs(amount)
            
            # Update the appropriate balance
            if segment == "cash":
                self.conn.execute("""
                    UPDATE funds 
                    SET cash_balance = cash_balance + ?, total_balance = total_balance + ?, last_updated = CURRENT_TIMESTAMP
                    WHERE id = 1
                """, [amount, amount])
            elif segment == "equity":
                self.conn.execute("""
                    UPDATE funds 
                    SET equity_balance = equity_balance + ?, total_balance = total_balance + ?, last_updated = CURRENT_TIMESTAMP
                    WHERE id = 1
                """, [amount, amount])
            elif segment == "fno":
                self.conn.execute("""
                    UPDATE funds 
                    SET fno_balance = fno_balance + ?, total_balance = total_balance + ?, last_updated = CURRENT_TIMESTAMP
                    WHERE id = 1
                """, [amount, amount])
            
            self.conn.commit()
            logger.info(f"Funds updated: {transaction_type} {amount} in {segment}")
            
        except Exception as e:
            logger.error(f"Error updating funds: {str(e)}")
    
    def is_market_open(self) -> bool:
        """Check if market is currently open (9:20 AM to 3:15 PM IST)"""
        try:
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            market_start = time(9, 20)  # 9:20 AM
            market_end = time(15, 15)   # 3:15 PM
            
            # Check if it's a weekday (Monday = 0, Sunday = 6)
            if now.weekday() >= 5:  # Saturday or Sunday
                return False
            
            current_time = now.time()
            return market_start <= current_time <= market_end
        except Exception as e:
            logger.error(f"Error checking market hours: {str(e)}")
            return False  # Default to closed if error
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get current market status"""
        is_open = self.is_market_open()
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        
        return {
            'is_open': is_open,
            'current_time': now.strftime('%H:%M:%S'),
            'current_date': now.strftime('%Y-%m-%d'),
            'market_start': '09:20',
            'market_end': '15:15'
        }

    def place_fake_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place a fake order with market hours check"""
        try:
            # Check if market is open
            if not self.is_market_open():
                return {
                    'status': 'failed',
                    'message': 'Market is closed. Trading hours: 9:20 AM to 3:15 PM IST (Mon-Fri)',
                    'order_id': None
                }
            
            # Validate required fields
            required_fields = ['stock_code', 'exchange_code', 'action', 'order_type', 'quantity']
            for field in required_fields:
                if field not in order_data:
                    return {'status': 'failed', 'message': f'Missing required field: {field}', 'order_id': None}
            
            symbol = order_data.get('symbol') or order_data.get('stock_code') or 'UNKNOWN'
            exchange = order_data.get('exchange_code', 'NSE')
            action = order_data.get('action')
            order_type = order_data.get('order_type')
            quantity = int(order_data.get('quantity', 0))
            price = float(order_data.get('price', 0))
            
            # Validate order type and price
            if order_type == 'market':
                price = 0  # Market orders don't have a specific price
                logger.info(f"Market order for {symbol}: price set to 0")
            elif order_type == 'limit' and price <= 0:
                return {
                    'status': 'failed',
                    'message': 'Limit orders require a valid price greater than 0',
                    'order_id': None
                }
            
            # Generate order ID
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            order_id = f"FAKE_{timestamp}_{symbol}"
            
            # Check if user has sufficient funds
            current_funds = self.get_funds()
            required_amount = quantity * price if price > 0 else 0
            
            if action == 'buy' and required_amount > current_funds['cash_balance']:
                return {
                    'status': 'failed',
                    'message': f'Insufficient funds. Required: ₹{required_amount:.2f}, Available: ₹{current_funds["cash_balance"]:.2f}',
                    'order_id': None
                }
            
            # Add order to database
            self.add_order({
                'order_id': order_id,
                'symbol': symbol,
                'exchange': exchange,
                'action': action,
                'quantity': quantity,
                'price': price,
                'order_type': order_type,
                'status': 'pending',
                'timestamp': datetime.now().isoformat()
            })
            
            # Block funds for buy orders
            if action == 'buy' and required_amount > 0:
                self.update_funds(required_amount, "debit", "cash")
            
            # Execute market orders immediately
            if order_type == 'market':
                # For market orders, we'll simulate execution at current price
                # For now, just mark as executed with the order price
                execution_price = price if price > 0 else 100.0  # Fallback price
                result = self.execute_fake_order(order_id, execution_price)
                if result['status'] == 'success':
                    return {
                        'status': 'success',
                        'message': f'Market order executed immediately at ₹{execution_price:.2f}',
                        'order_id': order_id,
                        'execution_price': execution_price
                    }
            
            # Limit orders remain pending
            self.conn.commit()
            return {
                'status': 'success',
                'message': 'Limit order placed successfully (pending execution)',
                'order_id': order_id
            }
            
        except Exception as e:
            logger.error(f"Error placing fake order: {str(e)}")
            return {'status': 'failed', 'message': f'Error placing order: {str(e)}', 'order_id': None}
    
    def execute_fake_order(self, order_id: str, execution_price: float) -> Dict[str, Any]:
        """Execute a fake order"""
        try:
            # Get order details
            order = self.conn.execute("SELECT * FROM orders WHERE order_id = ?", [order_id]).fetchone()
            if not order:
                return {'status': 'failed', 'message': 'Order not found'}
            
            # Update order status
            self.conn.execute("""
                UPDATE orders 
                SET status = 'executed', executed_quantity = quantity, average_price = ?
                WHERE order_id = ?
            """, [execution_price, order_id])
            
            # Calculate total amount
            total_amount = order[5] * execution_price  # quantity * price
            
            # Update ledger
            self.add_ledger_entry({
                'transaction_id': f"{order_id}_EXEC",
                'transaction_type': 'order_executed',
                'symbol': order[2],
                'exchange': order[3],
                'action': order[4],
                'quantity': order[5],
                'price': execution_price,
                'total_amount': total_amount,
                'segment': 'cash',
                'status': 'executed',
                'remarks': f"Fake order executed: {order[4]} {order[5]} {order[2]} @ {execution_price}"
            })
            
            # Update holdings
            self.update_holdings(order[2], order[3], order[4], order[5], execution_price)
            
            self.conn.commit()
            
            return {
                'status': 'success',
                'message': 'Fake order executed successfully',
                'order_id': order_id,
                'execution_price': execution_price
            }
            
        except Exception as e:
            logger.error(f"Error executing fake order: {str(e)}")
            return {'status': 'failed', 'message': f'Error executing order: {str(e)}'}
    
    def add_ledger_entry(self, entry_data: Dict[str, Any]):
        """Add entry to ledger"""
        try:
            # Get next ID
            result = self.conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM ledger").fetchone()
            next_id = result[0] if result else 1
            
            self.conn.execute("""
                INSERT INTO ledger (
                    id, transaction_id, transaction_type, symbol, exchange, action, 
                    quantity, price, total_amount, segment, status, remarks
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                next_id,
                entry_data['transaction_id'],
                entry_data['transaction_type'],
                entry_data['symbol'],
                entry_data['exchange'],
                entry_data['action'],
                entry_data['quantity'],
                entry_data['price'],
                entry_data['total_amount'],
                entry_data['segment'],
                entry_data['status'],
                entry_data['remarks']
            ])
            
        except Exception as e:
            logger.error(f"Error adding ledger entry: {str(e)}")
    
    def update_holdings(self, symbol: str, exchange: str, action: str, quantity: int, price: float):
        """Update holdings based on transaction"""
        try:
            # Check if holding exists
            existing = self.conn.execute("""
                SELECT * FROM holdings WHERE symbol = ? AND exchange = ?
            """, [symbol, exchange]).fetchone()
            
            if existing:
                current_quantity = existing[3]
                current_avg_price = existing[4]
                
                if action.upper() == 'BUY':
                    new_quantity = current_quantity + quantity
                    new_avg_price = ((current_quantity * current_avg_price) + (quantity * price)) / new_quantity
                else:  # SELL
                    new_quantity = current_quantity - quantity
                    new_avg_price = current_avg_price  # Keep same average price
                
                self.conn.execute("""
                    UPDATE holdings 
                    SET quantity = ?, average_price = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE symbol = ? AND exchange = ?
                """, [new_quantity, new_avg_price, symbol, exchange])
                
            else:
                # Create new holding
                if action.upper() == 'BUY':
                    self.conn.execute("""
                        INSERT INTO holdings (symbol, exchange, quantity, average_price, current_price)
                        VALUES (?, ?, ?, ?, ?)
                    """, [symbol, exchange, quantity, price, price])
            
        except Exception as e:
            logger.error(f"Error updating holdings: {str(e)}")
    
    def get_holdings(self) -> List[Dict[str, Any]]:
        """Get current holdings"""
        try:
            result = self.conn.execute("""
                SELECT symbol, exchange, quantity, average_price, current_price, 
                       market_value, unrealized_pnl, last_updated
                FROM holdings 
                WHERE quantity > 0
                ORDER BY market_value DESC
            """).fetchall()
            
            holdings = []
            for row in result:
                holdings.append({
                    'symbol': row[0],
                    'exchange': row[1],
                    'quantity': row[2],
                    'average_price': float(row[3]),
                    'current_price': float(row[4]),
                    'market_value': float(row[5]),
                    'unrealized_pnl': float(row[6]),
                    'last_updated': row[7]
                })
            
            return holdings
            
        except Exception as e:
            logger.error(f"Error getting holdings: {str(e)}")
            return []
    
    def get_ledger(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get ledger entries"""
        try:
            result = self.conn.execute("""
                SELECT * FROM ledger 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, [limit]).fetchall()
            
            ledger = []
            for row in result:
                ledger.append({
                    'transaction_id': row[1],
                    'transaction_type': row[2],
                    'symbol': row[3],
                    'exchange': row[4],
                    'action': row[5],
                    'quantity': row[6],
                    'price': float(row[7]),
                    'total_amount': float(row[8]),
                    'segment': row[9],
                    'status': row[10],
                    'timestamp': row[11],
                    'remarks': row[12]
                })
            
            return ledger
            
        except Exception as e:
            logger.error(f"Error getting ledger: {str(e)}")
            return []
    
    def get_orders(self, status: str = None) -> List[Dict[str, Any]]:
        """Get orders"""
        try:
            query = "SELECT * FROM orders"
            params = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status)
            
            query += " ORDER BY timestamp DESC"
            
            result = self.conn.execute(query, params).fetchall()
            
            orders = []
            for row in result:
                orders.append({
                    'order_id': row[1],
                    'symbol': row[2],
                    'exchange': row[3],
                    'action': row[4],
                    'order_type': row[5],
                    'quantity': row[6],
                    'price': float(row[7]),
                    'status': row[8],
                    'timestamp': row[9],
                    'executed_quantity': row[10],
                    'average_price': float(row[11]) if row[11] else 0.0
                })
            
            return orders
            
        except Exception as e:
            logger.error(f"Error getting orders: {str(e)}")
            return []
    
    def store_historical_data(self, symbol: str, exchange: str, data: List[Dict[str, Any]], interval: str = "1day"):
        """Store historical data"""
        try:
            for record in data:
                self.conn.execute("""
                    INSERT OR REPLACE INTO historical_data 
                    (symbol, exchange, date, open, high, low, close, volume, interval)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    symbol,
                    exchange,
                    record.get('datetime', datetime.now().date()),
                    record.get('open', 0),
                    record.get('high', 0),
                    record.get('low', 0),
                    record.get('close', 0),
                    record.get('volume', 0),
                    interval
                ])
            
            self.conn.commit()
            logger.info(f"Stored {len(data)} historical records for {symbol}")
            
        except Exception as e:
            logger.error(f"Error storing historical data: {str(e)}")
    
    def get_historical_data(self, symbol: str, exchange: str, from_date: str = None, to_date: str = None, interval: str = "1day") -> List[Dict[str, Any]]:
        """Get historical data"""
        try:
            query = """
                SELECT date, open, high, low, close, volume, interval
                FROM historical_data 
                WHERE symbol = ? AND exchange = ? AND interval = ?
            """
            params = [symbol, exchange, interval]
            
            if from_date:
                query += " AND date >= ?"
                params.append(from_date)
            
            if to_date:
                query += " AND date <= ?"
                params.append(to_date)
            
            query += " ORDER BY date"
            
            result = self.conn.execute(query, params).fetchall()
            
            data = []
            for row in result:
                data.append({
                    'datetime': row[0],
                    'open': float(row[1]),
                    'high': float(row[2]),
                    'low': float(row[3]),
                    'close': float(row[4]),
                    'volume': row[5],
                    'interval': row[6]
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}")
            return []
    
    def initialize_default_market_watch(self):
        """Initialize default market watch symbols only once"""
        try:
            # Check if defaults have been initialized before
            result = self.conn.execute("""
                SELECT flag_value FROM system_flags 
                WHERE flag_name = 'market_watch_initialized'
            """).fetchone()
            
            if result and result[0]:
                # Already initialized, don't add defaults again
                logger.info("Market watch defaults already initialized - skipping")
                return
            
            # Check if market watch table has any data
            count = self.conn.execute("SELECT COUNT(*) FROM market_watch").fetchone()[0]
            
            if count == 0:
                # Table is empty, add default symbols
                default_symbols = [
                    ('RELIANCE', 'NSE'),
                    ('TCS', 'NSE'),
                    ('INFY', 'NSE'),
                    ('HDFC', 'NSE'),
                    ('ICICIBANK', 'NSE')
                ]
                
                for i, (symbol, exchange) in enumerate(default_symbols, 1):
                    self.conn.execute("""
                        INSERT INTO market_watch (id, symbol, exchange)
                        VALUES (?, ?, ?)
                    """, [i, symbol, exchange])
                
                # Mark as initialized
                self.conn.execute("""
                    INSERT OR REPLACE INTO system_flags (flag_name, flag_value)
                    VALUES ('market_watch_initialized', true)
                """)
                
                self.conn.commit()
                logger.info("Initialized default market watch symbols")
            else:
                # Table has data, mark as initialized anyway
                self.conn.execute("""
                    INSERT OR REPLACE INTO system_flags (flag_name, flag_value)
                    VALUES ('market_watch_initialized', true)
                """)
                self.conn.commit()
                logger.info("Market watch already has data - marked as initialized")
                
        except Exception as e:
            logger.error(f"Error initializing default market watch: {str(e)}")
    
    def get_market_watch_symbols(self) -> List[Dict[str, str]]:
        """Get all market watch symbols"""
        try:
            result = self.conn.execute("""
                SELECT symbol, exchange FROM market_watch 
                ORDER BY added_at
            """).fetchall()
            
            return [{'symbol': row[0], 'exchange': row[1]} for row in result]
            
        except Exception as e:
            logger.error(f"Error getting market watch symbols: {str(e)}")
            return []
    
    def add_market_watch_symbol(self, symbol: str, exchange: str) -> bool:
        """Add symbol to market watch"""
        try:
            # Get the next available ID
            result = self.conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM market_watch").fetchone()
            next_id = result[0] if result else 1
            
            self.conn.execute("""
                INSERT INTO market_watch (id, symbol, exchange)
                VALUES (?, ?, ?)
            """, [next_id, symbol, exchange])
            
            self.conn.commit()
            logger.info(f"Added {symbol} ({exchange}) to market watch")
            return True
            
        except Exception as e:
            logger.error(f"Error adding symbol to market watch: {str(e)}")
            return False
    
    def remove_market_watch_symbol(self, symbol: str, exchange: str) -> bool:
        """Remove symbol from market watch"""
        try:
            self.conn.execute("""
                DELETE FROM market_watch 
                WHERE symbol = ? AND exchange = ?
            """, [symbol, exchange])
            
            self.conn.commit()
            logger.info(f"Removed {symbol} ({exchange}) from market watch")
            return True
            
        except Exception as e:
            logger.error(f"Error removing symbol from market watch: {str(e)}")
            return False
    
    def export_to_csv(self, table_name: str, filename: str, conditions: Dict[str, Any] = None) -> bool:
        """Export table data to CSV"""
        try:
            query = f"SELECT * FROM {table_name}"
            params = []
            
            if conditions:
                where_clause = " AND ".join([f"{k} = ?" for k in conditions.keys()])
                query += f" WHERE {where_clause}"
                params.extend(conditions.values())
            
            # Execute query and get results
            result = self.conn.execute(query, params).fetchall()
            
            if not result:
                logger.warning(f"No data found for export from {table_name}")
                return False
            
            # Get column names
            columns = [desc[0] for desc in self.conn.description]
            
            # Create DataFrame and export
            df = pd.DataFrame(result, columns=columns)
            df.to_csv(filename, index=False)
            
            logger.info(f"Exported {len(result)} records from {table_name} to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return False
    
    def add_order(self, order_data: Dict[str, Any]) -> bool:
        """Add a new order"""
        try:
            # Get the next available ID
            result = self.conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM orders").fetchone()
            next_id = result[0] if result else 1
            
            symbol = order_data.get('symbol') or order_data.get('stock_code')
            self.conn.execute("""
                INSERT INTO orders (id, order_id, symbol, exchange, action, order_type, quantity, price, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                next_id,
                order_data.get('order_id'),
                symbol,
                order_data.get('exchange'),
                order_data.get('action'),
                order_data.get('order_type'),
                order_data.get('quantity'),
                order_data.get('price'),
                'pending'  # Default status
            ])
            
            self.conn.commit()
            logger.info(f"Added order {order_data.get('order_id')} for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding order: {str(e)}")
            return False
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel a fake order"""
        try:
            # Check if order exists
            order = self.conn.execute(
                "SELECT * FROM orders WHERE order_id = ?", 
                [order_id]
            ).fetchone()
            
            if not order:
                return {
                    'status': 'failed',
                    'message': 'Order not found'
                }
            
            # Check if order can be cancelled
            if order[8] != 'pending':  # status
                return {
                    'status': 'failed',
                    'message': f'Order cannot be cancelled. Current status: {order[8]}'
                }
            
            # Update order status to cancelled
            self.conn.execute(
                "UPDATE orders SET status = 'cancelled' WHERE order_id = ?",
                [order_id]
            )
            
            # Add to ledger
            self.add_ledger_entry({
                'transaction_id': f"{order_id}_CANCEL",
                'transaction_type': 'order_cancelled',
                'symbol': order[2],  # symbol
                'exchange': order[3],  # exchange
                'action': order[4],  # action
                'quantity': order[5],  # quantity
                'price': order[6],  # price
                'total_amount': order[5] * order[6],  # quantity * price
                'segment': 'cash',
                'status': 'cancelled',
                'remarks': f"Fake order cancelled: {order[4]} {order[5]} {order[2]} @ {order[6]}"
            })
            
            # Unblock funds
            total_amount = order[5] * order[6]  # quantity * price
            self.update_funds(total_amount, "credit", "cash")
            
            self.conn.commit()
            
            return {
                'status': 'success',
                'message': 'Fake order cancelled successfully',
                'order_id': order_id
            }
            
        except Exception as e:
            logger.error(f"Error cancelling fake order: {str(e)}")
            return {
                'status': 'failed',
                'message': f'Error cancelling order: {str(e)}'
            }
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary"""
        try:
            funds = self.get_funds()
            holdings = self.get_holdings()
            
            total_holdings_value = sum(h['market_value'] for h in holdings)
            total_unrealized_pnl = sum(h['unrealized_pnl'] for h in holdings)
            
            return {
                'total_balance': funds['total_balance'],
                'cash_balance': funds['cash_balance'],
                'total_holdings_value': total_holdings_value,
                'total_unrealized_pnl': total_unrealized_pnl,
                'net_worth': funds['total_balance'] + total_holdings_value,
                'holdings_count': len(holdings),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {str(e)}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
