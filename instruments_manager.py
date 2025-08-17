"""
Instruments Manager - Handles security master files and stock search functionality
"""
import os
import csv
import json
import logging
import asyncio
import aiohttp
import aiofiles
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import duckdb

logger = logging.getLogger(__name__)

class InstrumentsManager:
    """Manages security master files and provides stock search functionality"""
    
    def __init__(self, db_path="instruments.db"):
        self.db_path = db_path
        self.conn = None
        self.instruments_url = "https://directlink.icicidirect.com/NewSecurityMaster/SecurityMaster.zip"
        self.last_download = None
        self.download_interval = 10000  # 10,000 seconds = ~2.78 hours
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize the database for storing instruments data"""
        try:
            self.conn = duckdb.connect(self.db_path)
            
            # Create tables for instruments data
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS instruments_metadata (
                    id INTEGER PRIMARY KEY,
                    last_download TIMESTAMP,
                    file_size INTEGER,
                    total_instruments INTEGER,
                    nse_count INTEGER,
                    bse_count INTEGER,
                    nfo_count INTEGER,
                    bfo_count INTEGER
                )
            """)
            
            # Create table for instruments data
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS instruments (
                    id INTEGER PRIMARY KEY,
                    token VARCHAR,
                    short_name VARCHAR,
                    series VARCHAR,
                    company_name VARCHAR,
                    exchange_code VARCHAR,
                    instrument_type VARCHAR,
                    isin_code VARCHAR,
                    lot_size INTEGER,
                    tick_size DECIMAL(10,2),
                    face_value DECIMAL(10,2),
                    permitted_to_trade BOOLEAN,
                    search_text VARCHAR,
                    expiry_date VARCHAR,
                    strike_price DECIMAL(10,2),
                    option_type VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for search
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_text ON instruments(search_text)
            """)
            
            # Create index for exchange and short_name
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_exchange_short_name ON instruments(exchange_code, short_name)
            """)
            
            self.conn.commit()
            logger.info("Instruments database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing instruments database: {str(e)}")
            raise
    
    async def should_download_instruments(self) -> bool:
        """Check if instruments file should be downloaded"""
        try:
            result = self.conn.execute("""
                SELECT last_download FROM instruments_metadata 
                ORDER BY id DESC LIMIT 1
            """).fetchone()
            
            if not result:
                logger.info("No previous download found, will download instruments")
                return True
            
            last_download = result[0]
            time_diff = (datetime.now() - last_download).total_seconds()
            
            if time_diff > self.download_interval:
                logger.info(f"Instruments file is {time_diff:.0f} seconds old, will download")
                return True
            
            logger.info(f"Instruments file is {time_diff:.0f} seconds old, no download needed")
            return False
            
        except Exception as e:
            logger.error(f"Error checking download status: {str(e)}")
            return True
    
    async def download_instruments_file(self) -> bool:
        """Download the instruments master file"""
        try:
            logger.info("Downloading instruments master file...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.instruments_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Save the zip file
                        async with aiofiles.open("SecurityMaster.zip", "wb") as f:
                            await f.write(content)
                        
                        logger.info(f"Downloaded instruments file: {len(content)} bytes")
                        return True
                    else:
                        logger.error(f"Failed to download instruments file: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error downloading instruments file: {str(e)}")
            return False
    
    def extract_instruments_data(self) -> Dict[str, List[Dict]]:
        """Extract and parse instruments data from the zip file"""
        try:
            import zipfile
            
            instruments_data = {
                'NSE': [],
                'BSE': [],
                'NFO': [],
                'BFO': []
            }
            
            with zipfile.ZipFile("SecurityMaster.zip", 'r') as zip_ref:
                # Extract files
                zip_ref.extractall(".")
                
                # Parse each file
                file_mappings = {
                    'NSEScripMaster.txt': 'NSE',
                    'BSEScripMaster.txt': 'BSE',
                    'FONSEScripMaster.txt': 'NFO',
                    'FOBSEScripMaster.txt': 'BFO'
                }
                
                for filename, exchange in file_mappings.items():
                    if os.path.exists(filename):
                        logger.info(f"Parsing {filename} for {exchange}")
                        
                        with open(filename, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            
                            # Clean column names (remove extra spaces and quotes)
                            cleaned_fieldnames = []
                            for field in reader.fieldnames:
                                cleaned_field = field.strip().strip('"').strip()
                                cleaned_fieldnames.append(cleaned_field)
                            
                            logger.info(f"Original columns: {reader.fieldnames[:5]}...")
                            logger.info(f"Cleaned columns: {cleaned_fieldnames[:5]}...")
                            
                            for row in reader:
                                # Clean the row data (remove extra spaces and quotes)
                                cleaned_row = {}
                                for key, value in row.items():
                                    cleaned_key = key.strip().strip('"').strip()
                                    cleaned_value = value.strip().strip('"').strip() if value else ""
                                    cleaned_row[cleaned_key] = cleaned_value
                                
                                # Clean and process the data
                                processed_row = self.process_instrument_row(cleaned_row, exchange)
                                if processed_row:
                                    instruments_data[exchange].append(processed_row)
                        
                        logger.info(f"Parsed {len(instruments_data[exchange])} instruments for {exchange}")
            
            return instruments_data
            
        except Exception as e:
            logger.error(f"Error extracting instruments data: {str(e)}")
            return {}
    
    def process_instrument_row(self, row: Dict, exchange: str) -> Optional[Dict]:
        """Process a single instrument row"""
        try:
            # Extract key fields based on exchange
            if exchange == 'NSE':
                token = row.get('Token', '').strip('"')
                short_name = row.get('ShortName', '').strip('"')
                company_name = row.get('CompanyName', '').strip('"')
                series = row.get('Series', '').strip('"')
                instrument_type = row.get('InstrumentType', '').strip('"')
                isin_code = row.get('ISINCode', '').strip('"')
                lot_size = int(row.get('Lotsize', '1').strip('"') or '1')
                tick_size = float(row.get('ticksize', '0.01').strip('"') or '0.01')
                face_value = float(row.get('FaceValue', '10').strip('"') or '10')
                permitted = True  # Default for NSE - the field seems to be incorrectly set in the file
                expiry_date = ''  # No expiry date for equity
                strike_price = 0.0  # No strike price for equity
                option_type = ''  # No option type for equity
                
            elif exchange == 'BSE':
                token = row.get('Token', '').strip('"')
                short_name = row.get('ShortName', '').strip('"')
                company_name = row.get('ScripName', '').strip('"')
                series = row.get('Series', '').strip('"')
                instrument_type = 'EQ'  # Default for BSE
                isin_code = row.get('ISINCode', '').strip('"')
                lot_size = int(row.get('LotSize', '1').strip('"') or '1')
                tick_size = float(row.get('TickSize', '0.01').strip('"') or '0.01')
                face_value = float(row.get('FaceValue', '10').strip('"') or '10')
                permitted = True  # Default for BSE
                expiry_date = ''  # No expiry date for equity
                strike_price = 0.0  # No strike price for equity
                option_type = ''  # No option type for equity
                
            elif exchange in ['NFO', 'BFO']:
                token = row.get('Token', '').strip('"')
                short_name = row.get('ShortName', '').strip('"')
                company_name = row.get('CompanyName', '').strip('"')
                series = row.get('Series', '').strip('"')
                instrument_type = row.get('InstrumentType', '').strip('"')
                isin_code = row.get('ISINCode', '').strip('"')
                lot_size = int(row.get('LotSize', '1').strip('"') or '1')
                tick_size = float(row.get('TickSize', '0.01').strip('"') or '0.01')
                face_value = float(row.get('FaceValue', '10').strip('"') or '10')
                permitted = True  # Default for F&O
                expiry_date = row.get('ExpiryDate', '').strip('"')  # Extract expiry date
                strike_price = float(row.get('StrikePrice', '0').strip('"') or '0')  # Extract strike price
                option_type = row.get('OptionType', '').strip('"')  # Extract option type (CE/PE)
                
            else:
                return None
            
            # Create search text for autocomplete
            search_text = f"{short_name} {company_name} {exchange}".lower()
            
            return {
                'token': token,
                'short_name': short_name,
                'series': series,
                'company_name': company_name,
                'exchange_code': exchange,
                'instrument_type': instrument_type,
                'isin_code': isin_code,
                'lot_size': lot_size,
                'tick_size': tick_size,
                'face_value': face_value,
                'permitted_to_trade': permitted,
                'search_text': search_text,
                'expiry_date': expiry_date,
                'strike_price': strike_price,
                'option_type': option_type
            }
            
        except Exception as e:
            logger.error(f"Error processing instrument row: {str(e)}")
            return None
    
    async def update_instruments_database(self, instruments_data: Dict[str, List[Dict]]):
        """Update the database with new instruments data"""
        try:
            # Clear existing data
            self.conn.execute("DELETE FROM instruments")
            self.conn.execute("DELETE FROM instruments_metadata")
            self.conn.commit()
            logger.info("Cleared existing instruments data")
            
            # Insert new data
            total_count = 0
            for exchange, instruments in instruments_data.items():
                for instrument in instruments:
                    self.conn.execute("""
                        INSERT INTO instruments (
                            id, token, short_name, series, company_name, exchange_code,
                            instrument_type, isin_code, lot_size, tick_size, face_value,
                            permitted_to_trade, search_text, expiry_date, strike_price, option_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        total_count + 1,  # Manual ID increment
                        instrument['token'],
                        instrument['short_name'],
                        instrument['series'],
                        instrument['company_name'],
                        instrument['exchange_code'],
                        instrument['instrument_type'],
                        instrument['isin_code'],
                        instrument['lot_size'],
                        instrument['tick_size'],
                        instrument['face_value'],
                        instrument['permitted_to_trade'],
                        instrument['search_text'],
                        instrument['expiry_date'],
                        instrument['strike_price'],
                        instrument['option_type']
                    ))
                    total_count += 1
            
            # Update metadata
            self.conn.execute("""
                INSERT INTO instruments_metadata (
                    id, last_download, file_size, total_instruments, nse_count, bse_count, nfo_count, bfo_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                1,  # Manual ID
                datetime.now(),
                os.path.getsize("SecurityMaster.zip") if os.path.exists("SecurityMaster.zip") else 0,
                total_count,
                len(instruments_data.get('NSE', [])),
                len(instruments_data.get('BSE', [])),
                len(instruments_data.get('NFO', [])),
                len(instruments_data.get('BFO', []))
            ))
            
            self.conn.commit()
            logger.info(f"Updated instruments database with {total_count} instruments")
            
        except Exception as e:
            logger.error(f"Error updating instruments database: {str(e)}")
            raise
    
    async def refresh_instruments(self) -> bool:
        """Main method to refresh instruments data"""
        try:
            if await self.should_download_instruments():
                # Download new file
                if await self.download_instruments_file():
                    # Extract and parse data
                    instruments_data = self.extract_instruments_data()
                    
                    if instruments_data:
                        # Update database
                        await self.update_instruments_database(instruments_data)
                        
                        # Clean up files
                        self.cleanup_files()
                        
                        logger.info("Instruments data refreshed successfully")
                        return True
                    else:
                        logger.error("Failed to extract instruments data")
                        return False
                else:
                    logger.error("Failed to download instruments file")
                    return False
            else:
                logger.info("Instruments data is up to date")
                return True
                
        except Exception as e:
            logger.error(f"Error refreshing instruments: {str(e)}")
            return False
    
    def cleanup_files(self):
        """Clean up temporary files"""
        try:
            files_to_remove = [
                "SecurityMaster.zip",
                "NSEScripMaster.txt",
                "BSEScripMaster.txt",
                "FONSEScripMaster.txt",
                "FOBSEScripMaster.txt"
            ]
            
            for file in files_to_remove:
                if os.path.exists(file):
                    os.remove(file)
                    
            logger.info("Cleaned up temporary files")
            
        except Exception as e:
            logger.error(f"Error cleaning up files: {str(e)}")
    
    def search_instruments(self, query: str, limit: int = 20, exchange_filter: str = None, instrument_type_filter: str = None) -> List[Dict]:
        """Search instruments by query with optional filters"""
        try:
            query = query.strip()
            if not query:
                return []
            
            # Build WHERE clause with filters  
            where_conditions = []
            params = []
            
            # Parse the query for specific components
            query_words = query.lower().split()
            option_type = None
            strike_price = None
            text_words = []
            
            # Identify option type and strike price
            for word in query_words:
                if word.upper() in ['CE', 'PE']:
                    option_type = word.upper()
                elif word.replace('.', '').isdigit():
                    strike_price = float(word)
                else:
                    text_words.append(word)
            
            # Build search conditions
            search_conditions = []
            search_params = []
            
            # If we have text words, search in symbol and company name
            if text_words:
                text_query = ' '.join(text_words)
                search_conditions.extend([
                    "UPPER(short_name) LIKE ?",
                    "UPPER(company_name) LIKE ?",
                    "UPPER(search_text) LIKE ?"
                ])
                search_params.extend([f"%{text_query.upper()}%"] * 3)
                
                # Create base condition with OR for text search
                base_condition = f"({' OR '.join(search_conditions)})"
                where_conditions.append(base_condition)
                params.extend(search_params)
                
                # Add additional filters with AND
                if option_type:
                    where_conditions.append("option_type = ?")
                    params.append(option_type)
                
                if strike_price is not None:
                    where_conditions.append("strike_price = ?")
                    params.append(strike_price)
            
            # If no text words but have option type or strike price
            elif option_type or strike_price is not None:
                if option_type:
                    where_conditions.append("option_type = ?")
                    params.append(option_type)
                
                if strike_price is not None:
                    where_conditions.append("strike_price = ?")
                    params.append(strike_price)
            
            # Fallback to basic search if no conditions
            else:
                where_conditions.append("(UPPER(short_name) LIKE ? OR UPPER(company_name) LIKE ? OR UPPER(search_text) LIKE ?)")
                params.extend([f"%{query.upper()}%"] * 3)
            
            # Add exchange filter if specified
            if exchange_filter:
                where_conditions.append("exchange_code = ?")
                params.append(exchange_filter.upper())
            
            # Add instrument type filter if specified
            if instrument_type_filter:
                where_conditions.append("instrument_type = ?")
                params.append(instrument_type_filter.upper())
            
            where_clause = " AND ".join(where_conditions)
            
            # Search in database with exchange priority
            result = self.conn.execute(f"""
                SELECT token, short_name, company_name, exchange_code, instrument_type,
                       lot_size, tick_size, face_value, isin_code, series, expiry_date, strike_price, option_type
                FROM instruments 
                WHERE {where_clause}
                ORDER BY 
                    CASE 
                        WHEN short_name LIKE ? THEN 1
                        WHEN company_name LIKE ? THEN 2
                        ELSE 3
                    END,
                    CASE 
                        WHEN exchange_code IN ('NSE', 'BSE') THEN 1
                        WHEN exchange_code IN ('NFO', 'BFO') THEN 2
                        ELSE 3
                    END,
                    short_name
                LIMIT ?
            """, params + [f"{query}%", f"{query}%", limit]).fetchall()
            
            instruments = []
            for row in result:
                instruments.append({
                    'token': row[0],
                    'short_name': row[1],
                    'company_name': row[2],
                    'exchange_code': row[3],
                    'instrument_type': row[4],
                    'lot_size': row[5],
                    'tick_size': row[6],
                    'face_value': row[7],
                    'isin_code': row[8],
                    'series': row[9],
                    'expiry_date': row[10],
                    'strike_price': row[11],
                    'option_type': row[12],
                    'display_name': f"{row[1]} ({row[3]}) - {row[2]}"
                })
            
            logger.info(f"Search query: '{query}', Found {len(instruments)} results")
            return instruments
            
        except Exception as e:
            logger.error(f"Error searching instruments: {str(e)}")
            return []
    
    def advanced_search(self, **kwargs) -> List[Dict]:
        """Advanced search with multiple criteria"""
        try:
            # Build WHERE clause based on provided criteria
            where_conditions = []
            params = []
            
            if kwargs.get('symbol'):
                where_conditions.append("short_name LIKE ?")
                params.append(f"%{kwargs['symbol']}%")
            
            if kwargs.get('company'):
                where_conditions.append("company_name LIKE ?")
                params.append(f"%{kwargs['company']}%")
            
            if kwargs.get('exchange'):
                where_conditions.append("exchange_code = ?")
                params.append(kwargs['exchange'].upper())
            
            if kwargs.get('instrument_type'):
                where_conditions.append("instrument_type = ?")
                params.append(kwargs['instrument_type'].upper())
            
            if kwargs.get('series'):
                where_conditions.append("series = ?")
                params.append(kwargs['series'].upper())
            
            if kwargs.get('option_type'):
                where_conditions.append("option_type = ?")
                params.append(kwargs['option_type'].upper())
            
            if kwargs.get('strike_price'):
                where_conditions.append("strike_price = ?")
                params.append(float(kwargs['strike_price']))
            
            if kwargs.get('expiry_date'):
                where_conditions.append("expiry_date = ?")
                params.append(kwargs['expiry_date'])
            
            # If no conditions, return empty
            if not where_conditions:
                return []
            
            where_clause = " AND ".join(where_conditions)
            limit = kwargs.get('limit', 50)
            
            result = self.conn.execute(f"""
                SELECT token, short_name, company_name, exchange_code, instrument_type,
                       lot_size, tick_size, face_value, isin_code, series, expiry_date, strike_price, option_type
                FROM instruments 
                WHERE {where_clause}
                ORDER BY exchange_code, short_name
                LIMIT ?
            """, params + [limit]).fetchall()
            
            instruments = []
            for row in result:
                instruments.append({
                    'token': row[0],
                    'short_name': row[1],
                    'company_name': row[2],
                    'exchange_code': row[3],
                    'instrument_type': row[4],
                    'lot_size': row[5],
                    'tick_size': row[6],
                    'face_value': row[7],
                    'isin_code': row[8],
                    'series': row[9],
                    'expiry_date': row[10],
                    'strike_price': row[11],
                    'option_type': row[12],
                    'display_name': f"{row[1]} ({row[3]}) - {row[2]}"
                })
            
            return instruments
            
        except Exception as e:
            logger.error(f"Error in advanced search: {str(e)}")
            return []
    
    def get_instrument_by_token(self, token: str, exchange: str) -> Optional[Dict]:
        """Get instrument details by token and exchange"""
        try:
            result = self.conn.execute("""
                SELECT token, short_name, company_name, exchange_code, instrument_type,
                       lot_size, tick_size, face_value, isin_code, series
                FROM instruments 
                WHERE token = ? AND exchange_code = ?
            """, (token, exchange)).fetchone()
            
            if result:
                return {
                    'token': result[0],
                    'short_name': result[1],
                    'company_name': result[2],
                    'exchange_code': result[3],
                    'instrument_type': result[4],
                    'lot_size': result[5],
                    'tick_size': result[6],
                    'face_value': result[7],
                    'isin_code': result[8],
                    'series': result[9]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting instrument by token: {str(e)}")
            return None
    
    def get_instrument_by_short_name(self, short_name: str, exchange: str) -> Optional[Dict]:
        """Get instrument details by short name and exchange"""
        try:
            result = self.conn.execute("""
                SELECT token, short_name, company_name, exchange_code, instrument_type,
                       lot_size, tick_size, face_value, isin_code, series
                FROM instruments 
                WHERE short_name = ? AND exchange_code = ?
            """, (short_name, exchange)).fetchone()
            
            if result:
                return {
                    'token': result[0],
                    'short_name': result[1],
                    'company_name': result[2],
                    'exchange_code': result[3],
                    'instrument_type': result[4],
                    'lot_size': result[5],
                    'tick_size': result[6],
                    'face_value': result[7],
                    'isin_code': result[8],
                    'series': result[9]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting instrument by short name: {str(e)}")
            return None
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        try:
            result = self.conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN exchange_code = 'NSE' THEN 1 END) as nse_count,
                    COUNT(CASE WHEN exchange_code = 'BSE' THEN 1 END) as bse_count,
                    COUNT(CASE WHEN exchange_code = 'NFO' THEN 1 END) as nfo_count,
                    COUNT(CASE WHEN exchange_code = 'BFO' THEN 1 END) as bfo_count
                FROM instruments
            """).fetchone()
            
            metadata = self.conn.execute("""
                SELECT last_download FROM instruments_metadata 
                ORDER BY id DESC LIMIT 1
            """).fetchone()
            
            return {
                'total_instruments': result[0],
                'nse_count': result[1],
                'bse_count': result[2],
                'nfo_count': result[3],
                'bfo_count': result[4],
                'last_download': metadata[0] if metadata else None
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
