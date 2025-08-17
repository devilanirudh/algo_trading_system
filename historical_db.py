"""
Historical Data Database Manager
Stores and manages historical OHLCV data in DuckDB for fast retrieval and management
"""
import duckdb
import logging
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
# import pandas as pd  # Optional - only needed for CSV export
from pathlib import Path

logger = logging.getLogger(__name__)

class HistoricalDataDB:
    """DuckDB-based historical data storage and management"""
    
    def __init__(self, db_path: str = "historical_data.db"):
        self.db_path = db_path
        self.conn = None
        self.initialize_db()
    
    def initialize_db(self):
        """Initialize DuckDB connection and create tables"""
        try:
            # Ensure directory exists
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Try to connect to database
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.conn = duckdb.connect(self.db_path)
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                        # Try to remove lock file if it exists
                        lock_file = Path(f"{self.db_path}.lock")
                        if lock_file.exists():
                            try:
                                lock_file.unlink()
                                logger.info("Removed stale lock file")
                            except:
                                pass
                        import time
                        time.sleep(1)
                    else:
                        raise
            
            # Create historical data table (DuckDB doesn't need explicit ID)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS historical_data (
                    job_id VARCHAR,
                    symbol VARCHAR NOT NULL,
                    exchange VARCHAR NOT NULL,
                    interval VARCHAR NOT NULL,
                    datetime TIMESTAMP NOT NULL,
                    open DOUBLE,
                    high DOUBLE,
                    low DOUBLE,
                    close DOUBLE,
                    volume BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes separately (DuckDB syntax)
            try:
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol_exchange_interval ON historical_data (symbol, exchange, interval)")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_datetime ON historical_data (datetime)")
                self.conn.execute("CREATE INDEX IF NOT EXISTS idx_job_id ON historical_data (job_id)")
            except Exception as e:
                logger.warning(f"Some indexes may not have been created: {e}")
            
            # Create jobs metadata table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS job_metadata (
                    job_id VARCHAR PRIMARY KEY,
                    symbol VARCHAR NOT NULL,
                    exchange VARCHAR NOT NULL,
                    interval VARCHAR NOT NULL,
                    from_date TIMESTAMP NOT NULL,
                    to_date TIMESTAMP NOT NULL,
                    total_candles INTEGER,
                    status VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    metadata VARCHAR
                )
            """)
            
            logger.info(f"Historical data database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Error initializing historical data database: {e}")
            raise
    
    def store_job_metadata(self, job_id: str, symbol: str, exchange: str, interval: str,
                          from_date: str, to_date: str, status: str = 'pending', **metadata) -> bool:
        """Store job metadata in database (without data)"""
        try:
            logger.info(f"📝 STORING JOB METADATA: {job_id} - {status}")
            
            if not self.conn:
                logger.error("Database connection is None")
                return False
            
            # Delete existing metadata if any
            self.conn.execute("DELETE FROM job_metadata WHERE job_id = ?", [job_id])
            
            # Insert job metadata
            self.conn.execute("""
                INSERT INTO job_metadata 
                (job_id, symbol, exchange, interval, from_date, to_date, total_candles, status, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            """, [
                job_id, symbol, exchange, interval,
                from_date, to_date, 0, status,
                json.dumps(metadata)
            ])
            
            logger.info(f"✅ Job metadata stored for {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing job metadata {job_id}: {e}")
            return False
    
    def update_job_status(self, job_id: str, status: str, **kwargs) -> bool:
        """Update job status and optional fields"""
        try:
            logger.info(f"🔄 UPDATING JOB STATUS: {job_id} -> {status}")
            
            if not self.conn:
                logger.error("Database connection is None")
                return False
            
            # Build update query dynamically
            updates = ["status = ?"]
            params = [status]
            
            if 'total_candles' in kwargs:
                updates.append("total_candles = ?")
                params.append(kwargs['total_candles'])
            
            if status in ['completed', 'failed', 'cancelled']:
                updates.append("completed_at = CURRENT_TIMESTAMP")
            
            query = f"UPDATE job_metadata SET {', '.join(updates)} WHERE job_id = ?"
            params.append(job_id)
            
            self.conn.execute(query, params)
            logger.info(f"✅ Job status updated for {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating job status {job_id}: {e}")
            return False

    def store_job_data(self, job_id: str, symbol: str, exchange: str, interval: str,
                      from_date: str, to_date: str, data: List[Dict], **metadata) -> bool:
        """Store historical data from a completed job"""
        try:
            logger.info(f"🗄️ ATTEMPTING TO STORE JOB DATA: {job_id}")
            logger.info(f"   Symbol: {symbol}, Exchange: {exchange}, Interval: {interval}")
            logger.info(f"   Data points: {len(data) if data else 0}")
            logger.info(f"   Date range: {from_date} to {to_date}")
            
            if not data:
                logger.warning(f"No data to store for job {job_id}")
                return False
            
            # Ensure connection is active
            if not self.conn:
                logger.error("Database connection is None")
                return False
            
            # Store job metadata (DuckDB syntax)
            self.conn.execute("""
                DELETE FROM job_metadata WHERE job_id = ?
            """, [job_id])
            
            self.conn.execute("""
                INSERT INTO job_metadata 
                (job_id, symbol, exchange, interval, from_date, to_date, total_candles, status, created_at, completed_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'completed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?)
            """, [
                job_id, symbol, exchange, interval,
                from_date, to_date, len(data),
                json.dumps(metadata)
            ])
            
            # Store historical data
            logger.info(f"📊 STORING {len(data)} CANDLES TO DATABASE")
            
            # Debug: show sample candle structure
            if data:
                sample_candle = data[0]
                logger.info(f"Sample candle structure: {sample_candle}")
            
            candles_stored = 0
            for i, candle in enumerate(data):
                try:
                    self.conn.execute("""
                        INSERT INTO historical_data 
                        (job_id, symbol, exchange, interval, datetime, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [
                        job_id, symbol, exchange, interval,
                        candle['datetime'], candle['open'], candle['high'],
                        candle['low'], candle['close'], candle['volume']
                    ])
                    candles_stored += 1
                    
                    if i % 1000 == 0:  # Log progress every 1000 candles
                        logger.info(f"   Stored {i+1}/{len(data)} candles...")
                        
                except Exception as candle_error:
                    logger.error(f"Error storing candle {i}: {candle_error}")
                    logger.error(f"Candle data: {candle}")
                    # Continue with next candle instead of failing completely
                    continue
            
            # Explicit commit for DuckDB
            try:
                self.conn.commit()
                logger.info(f"✅ Database transaction committed")
            except Exception as commit_error:
                logger.warning(f"Commit error (might be auto-commit): {commit_error}")
            
            logger.info(f"✅ Successfully stored {candles_stored}/{len(data)} candles for job {job_id}")
            return candles_stored > 0
            
        except Exception as e:
            logger.error(f"Error storing job data {job_id}: {e}")
            return False
    
    def get_job_data(self, job_id: str) -> Optional[Dict]:
        """Retrieve historical data for a specific job"""
        try:
            # Get job metadata
            job_meta = self.conn.execute("""
                SELECT * FROM job_metadata WHERE job_id = ?
            """, [job_id]).fetchone()
            
            if not job_meta:
                return None
            
            # Get historical data
            data = self.conn.execute("""
                SELECT datetime, open, high, low, close, volume
                FROM historical_data 
                WHERE job_id = ?
                ORDER BY datetime ASC
            """, [job_id]).fetchall()
            
            # Convert to list of dicts
            candles = []
            for row in data:
                candles.append({
                    'datetime': row[0],
                    'open': float(row[1]),
                    'high': float(row[2]),
                    'low': float(row[3]),
                    'close': float(row[4]),
                    'volume': int(row[5])
                })
            
            return {
                'job_id': job_meta[0],
                'symbol': job_meta[1],
                'exchange': job_meta[2],
                'interval': job_meta[3],
                'from_date': job_meta[4],
                'to_date': job_meta[5],
                'total_candles': job_meta[6],
                'status': job_meta[7],
                'created_at': job_meta[8],
                'completed_at': job_meta[9],
                'metadata': json.loads(job_meta[10]) if job_meta[10] else {},
                'data': candles
            }
            
        except Exception as e:
            logger.error(f"Error retrieving job data {job_id}: {e}")
            return None
    
    def search_historical_data(self, symbol: str, exchange: str, interval: str,
                             from_date: Optional[str] = None, to_date: Optional[str] = None,
                             limit: int = 10000) -> List[Dict]:
        """Search for historical data by symbol, exchange, interval, and date range"""
        try:
            query = """
                SELECT datetime, open, high, low, close, volume
                FROM historical_data 
                WHERE symbol = ? AND exchange = ? AND interval = ?
            """
            params = [symbol, exchange, interval]
            
            if from_date:
                query += " AND datetime >= ?"
                params.append(from_date)
            
            if to_date:
                query += " AND datetime <= ?"
                params.append(to_date)
            
            query += " ORDER BY datetime ASC LIMIT ?"
            params.append(limit)
            
            data = self.conn.execute(query, params).fetchall()
            
            candles = []
            for row in data:
                candles.append({
                    'datetime': row[0],
                    'open': float(row[1]),
                    'high': float(row[2]),
                    'low': float(row[3]),
                    'close': float(row[4]),
                    'volume': int(row[5])
                })
            
            return candles
            
        except Exception as e:
            logger.error(f"Error searching historical data: {e}")
            return []
    
    def get_available_data_summary(self) -> List[Dict]:
        """Get summary of available historical data"""
        try:
            data = self.conn.execute("""
                SELECT 
                    symbol, exchange, interval,
                    MIN(datetime) as earliest_date,
                    MAX(datetime) as latest_date,
                    COUNT(*) as total_candles,
                    COUNT(DISTINCT job_id) as job_count
                FROM historical_data 
                GROUP BY symbol, exchange, interval
                ORDER BY symbol, exchange, interval
            """).fetchall()
            
            summary = []
            for row in data:
                summary.append({
                    'symbol': row[0],
                    'exchange': row[1],
                    'interval': row[2],
                    'earliest_date': row[3],
                    'latest_date': row[4],
                    'total_candles': row[5],
                    'job_count': row[6]
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting data summary: {e}")
            return []
    
    def get_stored_jobs(self, limit: int = 100) -> List[Dict]:
        """Get list of stored jobs"""
        try:
            data = self.conn.execute("""
                SELECT job_id, symbol, exchange, interval, from_date, to_date, 
                       total_candles, status, created_at, completed_at
                FROM job_metadata 
                ORDER BY created_at DESC
                LIMIT ?
            """, [limit]).fetchall()
            
            jobs = []
            for row in data:
                jobs.append({
                    'job_id': row[0],
                    'symbol': row[1],
                    'exchange': row[2],
                    'interval': row[3],
                    'from_date': row[4],
                    'to_date': row[5],
                    'total_candles': row[6],
                    'status': row[7],
                    'created_at': row[8],
                    'completed_at': row[9]
                })
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error getting stored jobs: {e}")
            return []
    
    def delete_job_data(self, job_id: str) -> bool:
        """Delete all data for a specific job"""
        try:
            # Delete historical data
            self.conn.execute("DELETE FROM historical_data WHERE job_id = ?", [job_id])
            
            # Delete job metadata
            self.conn.execute("DELETE FROM job_metadata WHERE job_id = ?", [job_id])
            
            logger.info(f"Deleted all data for job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting job data {job_id}: {e}")
            return False
    
    def delete_symbol_data(self, symbol: str, exchange: str, interval: str) -> bool:
        """Delete all data for a specific symbol/exchange/interval combination"""
        try:
            # Get job IDs to delete
            job_ids = self.conn.execute("""
                SELECT DISTINCT job_id FROM historical_data 
                WHERE symbol = ? AND exchange = ? AND interval = ?
            """, [symbol, exchange, interval]).fetchall()
            
            # Delete historical data
            self.conn.execute("""
                DELETE FROM historical_data 
                WHERE symbol = ? AND exchange = ? AND interval = ?
            """, [symbol, exchange, interval])
            
            # Delete job metadata
            for job_id_row in job_ids:
                self.conn.execute("DELETE FROM job_metadata WHERE job_id = ?", [job_id_row[0]])
            
            logger.info(f"Deleted all data for {symbol} {exchange} {interval}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting symbol data: {e}")
            return False
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        try:
            stats = {}
            
            # Total records
            stats['total_candles'] = self.conn.execute("SELECT COUNT(*) FROM historical_data").fetchone()[0]
            stats['total_jobs'] = self.conn.execute("SELECT COUNT(*) FROM job_metadata").fetchone()[0]
            
            # Unique symbols
            stats['unique_symbols'] = self.conn.execute("""
                SELECT COUNT(DISTINCT symbol || '-' || exchange || '-' || interval) 
                FROM historical_data
            """).fetchone()[0]
            
            # Date range
            date_range = self.conn.execute("""
                SELECT MIN(datetime), MAX(datetime) FROM historical_data
            """).fetchone()
            
            stats['earliest_date'] = date_range[0]
            stats['latest_date'] = date_range[1]
            
            # Database size (approximate)
            stats['database_size_mb'] = Path(self.db_path).stat().st_size / (1024 * 1024)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def export_to_csv(self, job_id: str, output_path: str) -> bool:
        """Export job data to CSV file"""
        try:
            data = self.get_job_data(job_id)
            if not data:
                return False
            
            # Write CSV manually without pandas dependency
            with open(output_path, 'w', newline='') as f:
                f.write('datetime,open,high,low,close,volume\n')
                for candle in data['data']:
                    f.write(f"{candle['datetime']},{candle['open']},{candle['high']},{candle['low']},{candle['close']},{candle['volume']}\n")
            
            logger.info(f"Exported job {job_id} to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Historical data database connection closed")

# Global instance - lazy initialization
historical_db = None

def get_historical_db():
    """Get or create the global historical database instance"""
    global historical_db
    if historical_db is None:
        try:
            historical_db = HistoricalDataDB()
            # Test the connection
            stats = historical_db.get_database_stats()
            logger.info(f"Database connection verified: {stats}")
        except Exception as e:
            logger.error(f"Failed to initialize historical database: {e}")
            # Return a dummy object that logs errors but doesn't crash
            historical_db = DummyHistoricalDB()
    return historical_db

class DummyHistoricalDB:
    """Dummy database class that logs errors but doesn't crash the app"""
    
    def store_job_metadata(self, *args, **kwargs):
        logger.error("Database not available - job metadata not stored")
        return False
    
    def update_job_status(self, *args, **kwargs):
        logger.error("Database not available - job status not updated")
        return False
    
    def store_job_data(self, *args, **kwargs):
        logger.error("Database not available - job data not stored")
        return False
    
    def get_job_data(self, job_id):
        logger.error("Database not available - cannot retrieve job data")
        return None
    
    def get_stored_jobs(self, limit=100):
        logger.error("Database not available - no stored jobs")
        return []
    
    def get_available_data_summary(self):
        logger.error("Database not available - no data summary")
        return []
    
    def get_database_stats(self):
        logger.error("Database not available - no stats")
        return {}
    
    def search_historical_data(self, *args, **kwargs):
        logger.error("Database not available - no search results")
        return []
    
    def delete_job_data(self, job_id):
        logger.error("Database not available - cannot delete job data")
        return False
    
    def delete_symbol_data(self, *args, **kwargs):
        logger.error("Database not available - cannot delete symbol data")
        return False
