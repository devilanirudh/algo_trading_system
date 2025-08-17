"""
Background Job Manager for Historical Data Fetching
Handles long-running tasks with progress tracking and notifications
"""
import asyncio
import uuid
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
from historical_db import get_historical_db

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class JobProgress:
    current_chunk: int = 0
    total_chunks: int = 0
    candles_fetched: int = 0
    percentage: float = 0.0
    message: str = ""
    details: str = ""

@dataclass
class HistoricalDataJob:
    job_id: str
    symbol: str
    exchange: str
    interval: str
    from_date: str
    to_date: str
    status: JobStatus
    progress: JobProgress
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_data: Optional[List] = None
    kwargs: Dict = None
    
    def to_dict(self):
        return {
            'job_id': self.job_id,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'interval': self.interval,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'status': self.status.value,
            'progress': asdict(self.progress),
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'data_count': len(self.result_data) if self.result_data else 0
        }

class HistoricalDataJobManager:
    """Manages background historical data fetching jobs"""
    
    def __init__(self, trading_system):
        self.trading_system = trading_system
        self.jobs: Dict[str, HistoricalDataJob] = {}
        self.active_jobs: Dict[str, asyncio.Task] = {}
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        self.max_parallel_chunks = 10
        
    def create_job(self, symbol: str, exchange: str, interval: str, 
                   from_date: str, to_date: str, **kwargs) -> str:
        """Create a new historical data job"""
        job_id = str(uuid.uuid4())
        
        job = HistoricalDataJob(
            job_id=job_id,
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            from_date=from_date,
            to_date=to_date,
            status=JobStatus.PENDING,
            progress=JobProgress(),
            created_at=datetime.now(),
            kwargs=kwargs or {}
        )
        
        self.jobs[job_id] = job
        logger.info(f"Created job {job_id} for {symbol} {interval} from {from_date} to {to_date}")
        
        # Store job metadata in database immediately
        try:
            get_historical_db().store_job_metadata(
                job_id=job_id,
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                from_date=from_date,
                to_date=to_date,
                status='pending'
            )
            logger.info(f"Job {job_id} metadata stored in database")
        except Exception as e:
            logger.warning(f"Failed to store job metadata for {job_id}: {e}")
        
        return job_id
    
    def start_job(self, job_id: str) -> bool:
        """Start a background job"""
        if job_id not in self.jobs:
            logger.error(f"Job {job_id} not found")
            return False
            
        if job_id in self.active_jobs:
            logger.warning(f"Job {job_id} is already running")
            return False
            
        job = self.jobs[job_id]
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        # Update status in database
        try:
            get_historical_db().update_job_status(job_id, 'running')
        except Exception as e:
            logger.warning(f"Failed to update job status in database: {e}")
        
        # Start the background task
        task = asyncio.create_task(self._execute_job(job))
        self.active_jobs[job_id] = task
        
        logger.info(f"Started job {job_id}")
        return True
    
    async def _execute_job(self, job: HistoricalDataJob):
        """Execute a historical data job with parallel chunk fetching"""
        try:
            # Update progress
            await self._update_progress(job, 0, "Initializing...", "Parsing dates and calculating chunks")
            
            # Parse dates
            from datetime import datetime as dt
            start_dt = dt.fromisoformat(job.from_date.replace('Z', '+00:00'))
            end_dt = dt.fromisoformat(job.to_date.replace('Z', '+00:00'))
            
            # Calculate chunks
            chunk_duration = self._calculate_chunk_duration(job.interval)
            chunks = self._generate_chunks(start_dt, end_dt, chunk_duration)
            
            job.progress.total_chunks = len(chunks)
            await self._update_progress(job, 5, f"Processing {len(chunks)} chunks...", 
                                      f"Using {self.max_parallel_chunks} parallel requests")
            
            # Fetch chunks in parallel batches
            all_data = []
            chunk_num = 0
            
            for i in range(0, len(chunks), self.max_parallel_chunks):
                batch = chunks[i:i + self.max_parallel_chunks]
                
                # Create tasks for parallel execution
                tasks = []
                for chunk_start, chunk_end in batch:
                    chunk_from = chunk_start.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                    chunk_to = chunk_end.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                    
                    task = self._fetch_single_chunk(
                        job.symbol, job.exchange, job.interval,
                        chunk_from, chunk_to, chunk_num + 1, **job.kwargs
                    )
                    tasks.append(task)
                    chunk_num += 1
                
                # Execute batch in parallel
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for idx, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"Chunk {i + idx + 1} failed: {result}")
                        continue
                        
                    if result and 'Success' in result and result['Success']:
                        chunk_data = result['Success']
                        all_data.extend(chunk_data)
                        
                    # Update progress
                    progress_pct = (i + idx + 1) / len(chunks) * 90 + 5  # 5-95%
                    await self._update_progress(
                        job, progress_pct,
                        f"Chunk {i + idx + 1}/{len(chunks)} completed",
                        f"Fetched {len(all_data)} candles so far"
                    )
                
                # Small delay between batches
                await asyncio.sleep(0.1)
            
            # Remove duplicates and sort
            await self._update_progress(job, 95, "Processing data...", "Removing duplicates and sorting")
            
            unique_data = self._process_data(all_data)
            
            # Store data in database
            await self._update_progress(job, 98, "Storing data...", "Saving to database for future access")
            
            try:
                storage_success = get_historical_db().store_job_data(
                    job_id=job.job_id,
                    symbol=job.symbol,
                    exchange=job.exchange,
                    interval=job.interval,
                    from_date=job.from_date,
                    to_date=job.to_date,
                    data=unique_data,
                    chunks_fetched=chunk_num - 1,
                    parallel_requests=self.max_parallel_chunks
                )
                
                if storage_success:
                    logger.info(f"Job {job.job_id} data stored in database successfully")
                else:
                    logger.warning(f"Job {job.job_id} completed but failed to store in database")
            except Exception as e:
                logger.error(f"Database storage error for job {job.job_id}: {e}")
                # Continue with job completion even if database storage fails
            
            # Complete the job
            job.result_data = unique_data
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.progress.candles_fetched = len(unique_data)
            
            # Update status in database
            try:
                get_historical_db().update_job_status(job.job_id, 'completed', total_candles=len(unique_data))
            except Exception as e:
                logger.warning(f"Failed to update completed job status in database: {e}")
            
            await self._update_progress(job, 100, "Complete!", 
                                      f"Successfully fetched and stored {len(unique_data)} candles")
            
            logger.info(f"Job {job.job_id} completed successfully with {len(unique_data)} candles")
            
        except Exception as e:
            logger.error(f"Job {job.job_id} failed: {str(e)}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            
            # Update status in database
            try:
                get_historical_db().update_job_status(job.job_id, 'failed')
            except Exception as db_e:
                logger.warning(f"Failed to update failed job status in database: {db_e}")
            
            await self._update_progress(job, 0, "Failed", f"Error: {str(e)}")
            
        finally:
            # Remove from active jobs
            if job.job_id in self.active_jobs:
                del self.active_jobs[job.job_id]
    
    async def _fetch_single_chunk(self, symbol: str, exchange: str, interval: str,
                                 from_date: str, to_date: str, chunk_num: int, **kwargs):
        """Fetch a single chunk of data"""
        try:
            response = await self.trading_system.historical._get_single_data(
                symbol, exchange, interval, from_date, to_date, **kwargs
            )
            logger.debug(f"Chunk {chunk_num}: Fetched {len(response.get('Success', [])) if response else 0} candles")
            return response
        except Exception as e:
            logger.error(f"Chunk {chunk_num} failed: {e}")
            return None
    
    def _calculate_chunk_duration(self, interval: str) -> timedelta:
        """Calculate chunk duration based on interval"""
        safe_candles = 950
        
        if interval == '1second':
            return timedelta(seconds=safe_candles)
        elif interval == '1minute':
            return timedelta(days=3)
        elif interval == '5minute':
            return timedelta(days=15)
        elif interval == '30minute':
            return timedelta(days=90)
        elif interval == '1day':
            return timedelta(days=950)
        else:
            return timedelta(days=30)
    
    def _generate_chunks(self, start_dt: datetime, end_dt: datetime, 
                        chunk_duration: timedelta) -> List[tuple]:
        """Generate list of chunk date ranges"""
        chunks = []
        current_start = start_dt
        
        while current_start < end_dt:
            current_end = min(current_start + chunk_duration, end_dt)
            chunks.append((current_start, current_end))
            current_start = current_end
            
        return chunks
    
    def _process_data(self, all_data: List) -> List:
        """Remove duplicates and sort data"""
        if not all_data:
            return []
            
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
        
        return unique_data
    
    async def _update_progress(self, job: HistoricalDataJob, percentage: float, 
                              message: str, details: str):
        """Update job progress and notify callbacks"""
        job.progress.percentage = percentage
        job.progress.message = message
        job.progress.details = details
        job.progress.candles_fetched = len(job.result_data) if job.result_data else 0
        
        # Notify progress callbacks
        if job.job_id in self.progress_callbacks:
            for callback in self.progress_callbacks[job.job_id]:
                try:
                    await callback(job)
                except Exception as e:
                    logger.error(f"Progress callback error: {e}")
    
    def get_job(self, job_id: str) -> Optional[HistoricalDataJob]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> List[HistoricalDataJob]:
        """Get all jobs sorted by creation time"""
        return sorted(self.jobs.values(), key=lambda x: x.created_at, reverse=True)
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        if job_id in self.active_jobs:
            task = self.active_jobs[job_id]
            task.cancel()
            
            if job_id in self.jobs:
                self.jobs[job_id].status = JobStatus.CANCELLED
                self.jobs[job_id].completed_at = datetime.now()
                
                # Update status in database
                try:
                    get_historical_db().update_job_status(job_id, 'cancelled')
                    logger.info(f"Job {job_id} marked as cancelled in database")
                except Exception as e:
                    logger.warning(f"Failed to update cancelled job status in database: {e}")
            
            return True
        return False
    
    def add_progress_callback(self, job_id: str, callback: Callable):
        """Add a progress callback for a job"""
        if job_id not in self.progress_callbacks:
            self.progress_callbacks[job_id] = []
        self.progress_callbacks[job_id].append(callback)
    
    def remove_progress_callbacks(self, job_id: str):
        """Remove all progress callbacks for a job"""
        if job_id in self.progress_callbacks:
            del self.progress_callbacks[job_id]
    
    async def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        jobs_to_remove = []
        for job_id, job in self.jobs.items():
            if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED] and
                job.completed_at and job.completed_at < cutoff_time):
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
            if job_id in self.progress_callbacks:
                del self.progress_callbacks[job_id]
        
        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
