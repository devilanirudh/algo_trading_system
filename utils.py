"""
Trading System Utilities - Helper functions and utilities
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

class TradingUtils:
    """Utility functions for trading operations"""
    
    @staticmethod
    def format_date_for_api(date_obj):
        """Format date for Breeze Connect API"""
        if isinstance(date_obj, str):
            date_obj = datetime.strptime(date_obj, "%Y-%m-%d")
        
        return date_obj.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    
    @staticmethod
    def format_date_for_display(date_str):
        """Format date for display"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.000Z")
            return date_obj.strftime("%d-%b-%Y %H:%M")
        except:
            return date_str
    
    @staticmethod
    def calculate_pnl(buy_price, sell_price, quantity):
        """Calculate P&L"""
        return (sell_price - buy_price) * quantity
    
    @staticmethod
    def calculate_percentage_change(old_value, new_value):
        """Calculate percentage change"""
        if old_value == 0:
            return 0
        return ((new_value - old_value) / old_value) * 100
    
    @staticmethod
    def format_currency(amount):
        """Format currency for display"""
        return f"₹{amount:,.2f}"
    
    @staticmethod
    def format_number(number):
        """Format number for display"""
        if number >= 10000000:  # 1 crore
            return f"{number/10000000:.2f}Cr"
        elif number >= 100000:  # 1 lakh
            return f"{number/100000:.2f}L"
        elif number >= 1000:
            return f"{number/1000:.2f}K"
        else:
            return f"{number:.2f}"
    
    @staticmethod
    def validate_stock_code(stock_code):
        """Validate stock code format"""
        if not stock_code or len(stock_code) < 2:
            return False
        return True
    
    @staticmethod
    def get_stock_token_format(exchange_code, level, token):
        """Get stock token format for WebSocket"""
        exchange_map = {
            'NSE': '4',
            'BSE': '1',
            'NFO': '4',
            'BFO': '8'
        }
        
        level_map = {
            'quotes': '1',
            'depth': '2'
        }
        
        exchange_num = exchange_map.get(exchange_code, '4')
        level_num = level_map.get(level, '1')
        
        return f"{exchange_num}.{level_num}!{token}"
    
    @staticmethod
    def parse_stock_token(token_str):
        """Parse stock token string"""
        try:
            parts = token_str.split('!')
            if len(parts) != 2:
                return None
            
            level_part = parts[0]
            token = parts[1]
            
            level_parts = level_part.split('.')
            if len(level_parts) != 2:
                return None
            
            exchange_num = level_parts[0]
            level_num = level_parts[1]
            
            return {
                'exchange_num': exchange_num,
                'level_num': level_num,
                'token': token
            }
        except:
            return None


class DataProcessor:
    """Data processing utilities"""
    
    @staticmethod
    def process_quotes_data(quotes_data):
        """Process and format quotes data"""
        if not quotes_data:
            return []
        
        processed_data = []
        for quote in quotes_data:
            processed_quote = {
                'symbol': quote.get('stock_code', ''),
                'exchange': quote.get('exchange_code', ''),
                'ltp': float(quote.get('ltp', 0)),
                'change': float(quote.get('ltp_percent_change', 0)),
                'volume': int(quote.get('total_quantity_traded', 0)),
                'high': float(quote.get('high', 0)),
                'low': float(quote.get('low', 0)),
                'open': float(quote.get('open', 0)),
                'close': float(quote.get('previous_close', 0)),
                'timestamp': quote.get('ltt', '')
            }
            processed_data.append(processed_quote)
        
        return processed_data
    
    @staticmethod
    def process_holdings_data(holdings_data):
        """Process and format holdings data"""
        if not holdings_data:
            return []
        
        processed_data = []
        for holding in holdings_data:
            processed_holding = {
                'stock_code': holding.get('stock_code', ''),
                'quantity': int(holding.get('quantity', 0)),
                'average_price': float(holding.get('average_price', 0)),
                'current_price': float(holding.get('current_market_price', 0)),
                'market_value': float(holding.get('market_value', 0)),
                'pnl': float(holding.get('unrealized_profit', 0)),
                'pnl_percent': float(holding.get('change_percentage', 0))
            }
            processed_data.append(processed_holding)
        
        return processed_data
    
    @staticmethod
    def process_orders_data(orders_data):
        """Process and format orders data"""
        if not orders_data:
            return []
        
        processed_data = []
        for order in orders_data:
            processed_order = {
                'order_id': order.get('order_id', ''),
                'symbol': order.get('stock_code', ''),
                'action': order.get('action', ''),
                'quantity': int(order.get('quantity', 0)),
                'price': float(order.get('price', 0)),
                'order_type': order.get('order_type', ''),
                'status': order.get('status', ''),
                'timestamp': order.get('order_datetime', ''),
                'exchange': order.get('exchange_code', '')
            }
            processed_data.append(processed_order)
        
        return processed_data


class ConfigManager:
    """Configuration management"""
    
    def __init__(self, config_file="trading_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                return self.get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return self.get_default_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
    
    def get_default_config(self):
        """Get default configuration"""
        return {
            'api': {
                'api_key': '',
                'api_secret': '',
                'session_token': ''
            },
            'trading': {
                'default_exchange': 'NSE',
                'default_product': 'cash',
                'max_orders_per_day': 100,
                'max_position_size': 100000
            },
            'ui': {
                'theme': 'dark',
                'refresh_interval': 5,
                'auto_refresh': True
            },
            'alerts': {
                'price_alerts': True,
                'order_alerts': True,
                'position_alerts': True
            }
        }
    
    def get(self, key, default=None):
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key, value):
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()


class Logger:
    """Custom logger for trading operations"""
    
    def __init__(self, name, log_file=None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Create file handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message):
        self.logger.info(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def debug(self, message):
        self.logger.debug(message)


class PerformanceTracker:
    """Track trading performance"""
    
    def __init__(self):
        self.trades = []
        self.performance_metrics = {}
    
    def add_trade(self, trade_data):
        """Add a trade to tracking"""
        self.trades.append({
            'timestamp': datetime.now(),
            **trade_data
        })
        self.calculate_metrics()
    
    def calculate_metrics(self):
        """Calculate performance metrics"""
        if not self.trades:
            return
        
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t.get('pnl', 0) > 0])
        losing_trades = len([t for t in self.trades if t.get('pnl', 0) < 0])
        
        total_pnl = sum(t.get('pnl', 0) for t in self.trades)
        winning_pnl = sum(t.get('pnl', 0) for t in self.trades if t.get('pnl', 0) > 0)
        losing_pnl = sum(t.get('pnl', 0) for t in self.trades if t.get('pnl', 0) < 0)
        
        self.performance_metrics = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'total_pnl': total_pnl,
            'winning_pnl': winning_pnl,
            'losing_pnl': losing_pnl,
            'average_win': winning_pnl / winning_trades if winning_trades > 0 else 0,
            'average_loss': losing_pnl / losing_trades if losing_trades > 0 else 0,
            'profit_factor': abs(winning_pnl / losing_pnl) if losing_pnl != 0 else float('inf')
        }
    
    def get_metrics(self):
        """Get performance metrics"""
        return self.performance_metrics
    
    def export_trades(self, filename):
        """Export trades to CSV"""
        if not self.trades:
            return False
        
        try:
            df = pd.DataFrame(self.trades)
            df.to_csv(filename, index=False)
            return True
        except Exception as e:
            logger.error(f"Error exporting trades: {str(e)}")
            return False
