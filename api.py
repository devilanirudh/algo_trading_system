"""
BreezeAPI - Core API wrapper for Breeze Connect
Handles authentication and provides unified API interface
"""
from breeze_connect import BreezeConnect
import logging
import asyncio
from datetime import datetime
import urllib.parse

logger = logging.getLogger(__name__)

class BreezeAPI:
    """
    Breeze Connect API wrapper with authentication and error handling
    """
    
    def __init__(self, api_key=None, api_secret=None, session_token=None):
        """
        Initialize Breeze API
        
        Args:
            api_key: Breeze Connect API key
            api_secret: Breeze Connect API secret
            session_token: Session token from login
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.session_token = session_token
        
        self.breeze = None
        self.is_authenticated = False
        self.user_details = None
        
    async def authenticate(self):
        """Authenticate with Breeze Connect"""
        try:
            logger.info("Authenticating with Breeze Connect...")
            logger.info(f"API Key: {self.api_key[:10]}...")
            logger.info(f"Session Token: {self.session_token}")
            
            # Initialize Breeze Connect
            self.breeze = BreezeConnect(api_key=self.api_key)
            
            # Generate session
            response = self.breeze.generate_session(
                api_secret=self.api_secret,
                session_token=self.session_token
            )
            
            logger.info(f"Raw generate_session response: {response}")
            
            # Check if authentication was successful by testing an API call
            try:
                test_response = self.breeze.get_names('NSE', 'RELIANCE')
                logger.info(f"Test API call successful: {test_response}")
                self.is_authenticated = True
                logger.info("Authentication successful")
                
                # Get user details
                await self.get_user_details()
                return True
            except Exception as test_error:
                logger.error(f"Test API call failed: {test_error}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    async def get_user_details(self):
        """Get user details"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.get_customer_details(api_session=self.session_token)
            
            if response and response.get('Status') == 200:
                self.user_details = response.get('Success', {})
                logger.info(f"User: {self.user_details.get('idirect_user_name', 'N/A')}")
                return self.user_details
            else:
                logger.error(f"Failed to get user details: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user details: {str(e)}")
            return None
    
    def get_login_url(self):
        """Get login URL for session token generation"""
        if not self.api_key:
            return None
        
        # URL encode the API key for special characters
        encoded_key = urllib.parse.quote_plus(self.api_key)
        return f"https://api.icicidirect.com/apiuser/login?api_key={encoded_key}"
    
    async def get_stock_names(self, exchange_code, stock_code):
        """Get stock names and tokens"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.get_names(exchange_code=exchange_code, stock_code=stock_code)
            return response
            
        except Exception as e:
            logger.error(f"Error getting stock names: {str(e)}")
            return None
    
    async def get_quotes(self, stock_code, exchange_code, **kwargs):
        """Get quotes for a stock with retry logic"""
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                if not self.is_authenticated:
                    logger.error("Not authenticated")
                    return None
                
                response = self.breeze.get_quotes(
                    stock_code=stock_code,
                    exchange_code=exchange_code,
                    **kwargs
                )
                
                if response and response.get('Status') == 200:
                    return response.get('Success', [])
                elif response and response.get('Status') == 503:
                    # Service temporarily unavailable
                    if attempt < max_retries - 1:
                        logger.warning(f"API returned 503 for {stock_code}, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        logger.error(f"Failed to get quotes after {max_retries} attempts: {response}")
                        return None
                else:
                    logger.error(f"Failed to get quotes: {response}")
                    return None
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Error getting quotes for {stock_code} (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    logger.error(f"Error getting quotes after {max_retries} attempts: {str(e)}")
                    return None
        
        return None
    
    async def get_historical_data(self, **kwargs):
        """Get historical data"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.get_historical_data(**kwargs)
            
            if response and response.get('Status') == 200:
                return response.get('Success', [])
            else:
                logger.error(f"Failed to get historical data: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting historical data: {str(e)}")
            return None
    
    async def get_historical_data_v2(self, **kwargs):
        """Get historical data v2"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.get_historical_data_v2(**kwargs)
            
            # Return the full response for better error handling
            if response:
                if response.get('Status') == 200:
                    return response
                else:
                    logger.error(f"Failed to get historical data v2: {response}")
                    return response  # Return full response even on error
            else:
                logger.error("No response received from historical data v2")
                return None
                
        except Exception as e:
            logger.error(f"Error getting historical data v2: {str(e)}")
            return None
    
    async def place_order(self, **kwargs):
        """Place an order"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.place_order(**kwargs)
            
            if response and response.get('Status') == 200:
                logger.info(f"Order placed successfully: {response.get('Success', {}).get('order_id')}")
                return response  # Return full response with Status field
            else:
                logger.error(f"Failed to place order: {response}")
                return response  # Return full response even on failure
                
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return None
    
    async def get_order_list(self, **kwargs):
        """Get order list"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.get_order_list(**kwargs)
            
            if response and response.get('Status') == 200:
                return response.get('Success', [])
            else:
                logger.error(f"Failed to get order list: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting order list: {str(e)}")
            return None
    
    async def get_order_detail(self, **kwargs):
        """Get order detail"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.get_order_detail(**kwargs)
            
            if response and response.get('Status') == 200:
                return response.get('Success', [])
            else:
                logger.error(f"Failed to get order detail: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting order detail: {str(e)}")
            return None
    
    async def cancel_order(self, **kwargs):
        """Cancel an order"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.cancel_order(**kwargs)
            
            if response and response.get('Status') == 200:
                logger.info(f"Order cancelled successfully: {response.get('Success', {}).get('order_id')}")
                return response.get('Success', {})
            else:
                logger.error(f"Failed to cancel order: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return None
    
    async def modify_order(self, **kwargs):
        """Modify an order"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.modify_order(**kwargs)
            
            if response and response.get('Status') == 200:
                logger.info(f"Order modified successfully: {response.get('Success', {}).get('order_id')}")
                return response.get('Success', {})
            else:
                logger.error(f"Failed to modify order: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error modifying order: {str(e)}")
            return None
    
    async def get_demat_holdings(self):
        """Get demat holdings"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.get_demat_holdings()
            
            if response and response.get('Status') == 200:
                return response.get('Success', [])
            else:
                logger.error(f"Failed to get demat holdings: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting demat holdings: {str(e)}")
            return None
    
    async def get_portfolio_holdings(self, **kwargs):
        """Get portfolio holdings"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.get_portfolio_holdings(**kwargs)
            
            if response and response.get('Status') == 200:
                return response.get('Success', [])
            else:
                logger.error(f"Failed to get portfolio holdings: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting portfolio holdings: {str(e)}")
            return None
    
    async def get_portfolio_positions(self):
        """Get portfolio positions"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.get_portfolio_positions()
            
            if response and response.get('Status') == 200:
                return response.get('Success', [])
            else:
                logger.error(f"Failed to get portfolio positions: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting portfolio positions: {str(e)}")
            return None
    
    async def get_funds(self):
        """Get funds"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.get_funds()
            
            if response and response.get('Status') == 200:
                return response.get('Success', {})
            else:
                logger.error(f"Failed to get funds: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting funds: {str(e)}")
            return None
    
    async def get_margin(self, **kwargs):
        """Get margin"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.get_margin(**kwargs)
            
            if response and response.get('Status') == 200:
                return response.get('Success', {})
            else:
                logger.error(f"Failed to get margin: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting margin: {str(e)}")
            return None
    
    async def get_trade_list(self, **kwargs):
        """Get trade list"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.get_trade_list(**kwargs)
            
            if response and response.get('Status') == 200:
                return response.get('Success', [])
            else:
                logger.error(f"Failed to get trade list: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting trade list: {str(e)}")
            return None
    
    async def get_option_chain_quotes(self, **kwargs):
        """Get option chain quotes"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.get_option_chain_quotes(**kwargs)
            
            if response and response.get('Status') == 200:
                return response.get('Success', [])
            else:
                logger.error(f"Failed to get option chain: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting option chain: {str(e)}")
            return None
    
    async def square_off(self, **kwargs):
        """Square off position"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.square_off(**kwargs)
            
            if response and response.get('Status') == 200:
                logger.info(f"Position squared off successfully: {response.get('Success', {}).get('order_id')}")
                return response.get('Success', {})
            else:
                logger.error(f"Failed to square off: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error squaring off: {str(e)}")
            return None
    
    async def preview_order(self, **kwargs):
        """Preview order"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.preview_order(**kwargs)
            
            if response and response.get('Status') == 200:
                return response.get('Success', {})
            else:
                logger.error(f"Failed to preview order: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error previewing order: {str(e)}")
            return None
    
    async def margin_calculator(self, orders, exchange_code):
        """Calculate margin"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.margin_calculator(orders, exchange_code=exchange_code)
            
            if response and response.get('Status') == 200:
                return response.get('Success', {})
            else:
                logger.error(f"Failed to calculate margin: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error calculating margin: {str(e)}")
            return None
    
    async def limit_calculator(self, **kwargs):
        """Calculate limit"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return None
            
            response = self.breeze.limit_calculator(**kwargs)
            
            if response and response.get('Status') == 200:
                return response.get('Success', {})
            else:
                logger.error(f"Failed to calculate limit: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error calculating limit: {str(e)}")
            return None
    
    def ws_connect(self):
        """Connect to WebSocket"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return False
            
            self.breeze.ws_connect()
            logger.info("WebSocket connected")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to WebSocket: {str(e)}")
            return False
    
    def ws_disconnect(self):
        """Disconnect from WebSocket"""
        try:
            if self.breeze:
                self.breeze.ws_disconnect()
                logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting from WebSocket: {str(e)}")
    
    def subscribe_feeds(self, **kwargs):
        """Subscribe to feeds"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return False
            
            response = self.breeze.subscribe_feeds(**kwargs)
            logger.info(f"Subscribed to feeds: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing to feeds: {str(e)}")
            return False
    
    def unsubscribe_feeds(self, **kwargs):
        """Unsubscribe from feeds"""
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated")
                return False
            
            response = self.breeze.unsubscribe_feeds(**kwargs)
            logger.info(f"Unsubscribed from feeds: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Error unsubscribing from feeds: {str(e)}")
            return False
