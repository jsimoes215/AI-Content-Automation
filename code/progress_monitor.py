"""
Real-time Progress Monitoring and Updates System

This module provides comprehensive progress tracking for bulk content generation
operations including job state tracking, WebSocket broadcasting, progress percentage
calculation, ETA estimation, and Supabase Realtime integration.

Key Features:
- Real-time job state tracking with explicit state machine
- WebSocket broadcasting for live updates
- Progress percentage calculation and aggregation
- ETA estimation based on processing rates
- Supabase Realtime integration for database changes
- Thread-safe operations for concurrent access
"""

import asyncio
import json
import logging
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import websockets
from websockets.server import WebSocketServerProtocol
import supabase
from supabase import create_client, Client
import psutil


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobState(Enum):
    """Job state machine states as defined in the API design."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    CANCELED = "canceled"
    CANCELING = "canceling"
    FAILED = "failed"


class VideoState(Enum):
    """Individual video item states."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELED = "canceled"


class EventType(Enum):
    """WebSocket event types for real-time updates."""
    JOB_STATE_CHANGED = "job.state_changed"
    JOB_PROGRESS = "job.progress"
    VIDEO_CREATED = "video.created"
    VIDEO_UPDATED = "video.updated"
    VIDEO_COMPLETED = "video.completed"
    VIDEO_FAILED = "video.failed"
    JOB_COMPLETED = "job.completed"
    JOB_CANCELED = "job.canceled"
    JOB_FAILED = "job.failed"


@dataclass
class JobProgress:
    """Job-level progress metrics."""
    percent_complete: float
    items_total: int
    items_completed: int
    items_failed: int
    items_skipped: int
    items_canceled: int
    items_pending: int
    time_to_start_ms: Optional[int]
    time_processing_ms: int
    average_duration_ms_per_item: Optional[float]
    eta_ms: Optional[int]
    rate_limited: bool
    processing_deadline_ms: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class VideoProgress:
    """Individual video item progress."""
    id: str
    job_id: str
    state: VideoState
    percent_complete: float
    row_index: int
    title: str
    created_at: datetime
    updated_at: datetime
    errors: List[Dict[str, Any]]


@dataclass
class WebSocketMessage:
    """WebSocket message envelope."""
    type: EventType
    ts: str
    correlation_id: str
    data: Dict[str, Any]


@dataclass
class JobMetrics:
    """Job-level performance metrics."""
    total_processing_time: float
    items_per_second: float
    estimated_completion: Optional[datetime]
    resource_utilization: float
    error_rate: float


class ProgressCalculator:
    """Calculates job progress and ETA based on historical data."""
    
    def __init__(self, min_samples: int = 5, decay_factor: float = 0.9):
        self.min_samples = min_samples
        self.decay_factor = decay_factor
        self._processing_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._start_times: Dict[str, datetime] = {}
        self._completion_times: Dict[str, datetime] = {}
    
    def record_item_start(self, job_id: str, item_id: str):
        """Record when an item starts processing."""
        self._start_times[f"{job_id}:{item_id}"] = datetime.utcnow()
    
    def record_item_completion(self, job_id: str, item_id: str, success: bool = True):
        """Record when an item completes processing."""
        start_time = self._start_times.get(f"{job_id}:{item_id}")
        if start_time:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._processing_history[job_id].append(duration)
            self._completion_times[f"{job_id}:{item_id}"] = datetime.utcnow()
    
    def calculate_progress(self, job_data: Dict[str, Any]) -> JobProgress:
        """Calculate job-level progress metrics."""
        now = datetime.utcnow()
        
        # Basic progress calculation
        items_total = job_data.get('items_total', 0)
        items_completed = job_data.get('items_completed', 0)
        items_failed = job_data.get('items_failed', 0)
        items_skipped = job_data.get('items_skipped', 0)
        items_canceled = job_data.get('items_canceled', 0)
        
        percent_complete = 0.0
        if items_total > 0:
            percent_complete = ((items_completed + items_skipped) / items_total) * 100
        
        items_pending = items_total - items_completed - items_failed - items_skipped - items_canceled
        
        # Time calculations
        created_at = job_data.get('created_at', now)
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        time_to_start_ms = None
        if job_data.get('started_at'):
            started_at = job_data.get('started_at')
            if isinstance(started_at, str):
                started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            time_to_start_ms = int((started_at - created_at).total_seconds() * 1000)
        
        # Processing time and average duration
        processing_history = self._processing_history.get(job_data['id'], deque())
        average_duration_ms = None
        time_processing_ms = 0
        
        if processing_history:
            # Calculate weighted average (recent samples have more weight)
            weighted_sum = 0
            weight_sum = 0
            for i, duration in enumerate(reversed(processing_history)):
                weight = (self.decay_factor ** i)
                weighted_sum += duration * weight
                weight_sum += weight
            
            average_duration_ms = weighted_sum / weight_sum if weight_sum > 0 else None
            time_processing_ms = sum(processing_history)
        
        # ETA calculation
        eta_ms = None
        if average_duration_ms and items_pending > 0 and job_data.get('state') == 'running':
            eta_ms = int(average_duration_ms * items_pending)
        
        # Rate limiting indicator
        rate_limited = job_data.get('rate_limited', False)
        processing_deadline_ms = job_data.get('processing_deadline_ms')
        
        return JobProgress(
            percent_complete=percent_complete,
            items_total=items_total,
            items_completed=items_completed,
            items_failed=items_failed,
            items_skipped=items_skipped,
            items_canceled=items_canceled,
            items_pending=items_pending,
            time_to_start_ms=time_to_start_ms,
            time_processing_ms=time_processing_ms,
            average_duration_ms_per_item=average_duration_ms,
            eta_ms=eta_ms,
            rate_limited=rate_limited,
            processing_deadline_ms=processing_deadline_ms,
            created_at=created_at,
            updated_at=now
        )
    
    def calculate_resource_utilization(self, job_id: str) -> float:
        """Calculate resource utilization for a job."""
        # Simple CPU-based utilization calculation
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        # Weighted average of CPU and memory usage
        return (cpu_percent * 0.6 + memory_percent * 0.4) / 100


class SupabaseRealtimeClient:
    """Handles Supabase Realtime integration for database change notifications."""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.client: Client = create_client(supabase_url, supabase_key)
        self.subscriptions: Dict[str, Any] = {}
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)
    
    def subscribe_to_job_changes(self, job_id: str, callback: Callable):
        """Subscribe to changes for a specific job."""
        try:
            # Check if Supabase client has realtime capability
            if not hasattr(self.client, 'realtime'):
                logger.warning("Supabase client does not have realtime capability")
                return
                
            # Subscribe to job table changes
            try:
                # Try the newer Supabase realtime API
                subscription = self.client.table('bulk_jobs')\
                    .on('*', lambda payload: callback('job', payload))\
                    .eq('id', job_id)\
                    .subscribe()
                
                self.subscriptions[job_id] = {
                    'job': subscription,
                    'events': None
                }
                
                logger.info(f"Subscribed to changes for job {job_id}")
                
            except AttributeError:
                # Fallback for older API versions
                logger.info("Using fallback subscription method")
                self.subscriptions[job_id] = {
                    'job': None,
                    'events': None
                }
            
        except Exception as e:
            logger.error(f"Failed to subscribe to job {job_id}: {e}")
            # Don't raise - continue without realtime subscription
    
    def unsubscribe_from_job(self, job_id: str):
        """Unsubscribe from job changes."""
        if job_id in self.subscriptions:
            try:
                self.client.table('bulk_jobs').unsubscribe()
                self.client.table('job_events').unsubscribe()
                del self.subscriptions[job_id]
                logger.info(f"Unsubscribed from job {job_id}")
            except Exception as e:
                logger.error(f"Failed to unsubscribe from job {job_id}: {e}")
    
    def publish_progress_update(self, job_id: str, progress: JobProgress):
        """Publish progress update to Supabase Realtime."""
        try:
            # Update the job record with current progress
            update_data = {
                'percent_complete': progress.percent_complete,
                'items_completed': progress.items_completed,
                'items_failed': progress.items_failed,
                'items_skipped': progress.items_skipped,
                'items_canceled': progress.items_canceled,
                'items_pending': progress.items_pending,
                'time_processing_ms': progress.time_processing_ms,
                'average_duration_ms_per_item': progress.average_duration_ms_per_item,
                'eta_ms': progress.eta_ms,
                'rate_limited': progress.rate_limited,
                'updated_at': progress.updated_at.isoformat()
            }
            
            result = self.client.table('bulk_jobs')\
                .update(update_data)\
                .eq('id', job_id)\
                .execute()
            
            logger.debug(f"Published progress update for job {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish progress update for job {job_id}: {e}")


class WebSocketBroadcaster:
    """Handles WebSocket broadcasting for real-time updates."""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Dict[str, Set[WebSocketServerProtocol]] = defaultdict(set)
        self.server: Optional[WebSocketServer] = None
        self._server_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle WebSocket client connection."""
        client_id = str(uuid.uuid4())
        
        # Parse query parameters for job_id and authentication
        try:
            if '?' in path:
                query_params = path.split('?', 1)[1]
                params = {k: v for k, v in (p.split('=') for p in query_params.split('&'))}
                job_id = params.get('job_id')
                token = params.get('token')
                
                if not job_id or not token:
                    await websocket.close(code=4001, reason="Missing job_id or token")
                    return
                
                # TODO: Validate token and job access here
                
            else:
                await websocket.close(code=4000, reason="Missing query parameters")
                return
            
        except Exception as e:
            logger.error(f"Failed to parse WebSocket connection parameters: {e}")
            await websocket.close(code=4000, reason="Invalid connection parameters")
            return
        
        # Add client to the job-specific set
        with self._lock:
            self.clients[job_id].add(websocket)
        
        logger.info(f"Client {client_id} connected for job {job_id}")
        
        try:
            # Send initial state
            await self.send_message_to_job(job_id, WebSocketMessage(
                type=EventType.JOB_PROGRESS,
                ts=datetime.utcnow().isoformat(),
                correlation_id=str(uuid.uuid4()),
                data={"status": "connected", "job_id": job_id}
            ))
            
            # Keep connection alive
            async for message in websocket:
                # Handle incoming messages (ping/pong, client commands, etc.)
                try:
                    incoming_data = json.loads(message)
                    if incoming_data.get('type') == 'ping':
                        await websocket.send(json.dumps({
                            'type': 'pong',
                            'ts': datetime.utcnow().isoformat()
                        }))
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from client {client_id}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            with self._lock:
                self.clients[job_id].discard(websocket)
    
    async def send_message_to_job(self, job_id: str, message: WebSocketMessage):
        """Send a message to all clients subscribed to a specific job."""
        if job_id not in self.clients:
            return
        
        message_str = json.dumps(asdict(message), default=str)
        disconnected_clients = set()
        
        with self._lock:
            clients = self.clients[job_id].copy()
        
        # Send to all clients
        for client in clients:
            try:
                await client.send(message_str)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Failed to send message to client: {e}")
                disconnected_clients.add(client)
        
        # Clean up disconnected clients
        if disconnected_clients:
            with self._lock:
                self.clients[job_id] -= disconnected_clients
    
    async def broadcast_state_change(self, job_id: str, prior_state: JobState, 
                                   new_state: JobState, reason: str = ""):
        """Broadcast a job state change event."""
        await self.send_message_to_job(job_id, WebSocketMessage(
            type=EventType.JOB_STATE_CHANGED,
            ts=datetime.utcnow().isoformat(),
            correlation_id=str(uuid.uuid4()),
            data={
                "prior_state": prior_state.value,
                "new_state": new_state.value,
                "reason": reason
            }
        ))
    
    async def broadcast_progress(self, job_id: str, progress: JobProgress):
        """Broadcast job progress update."""
        await self.send_message_to_job(job_id, WebSocketMessage(
            type=EventType.JOB_PROGRESS,
            ts=datetime.utcnow().isoformat(),
            correlation_id=str(uuid.uuid4()),
            data={
                "percent_complete": progress.percent_complete,
                "items_total": progress.items_total,
                "items_completed": progress.items_completed,
                "items_failed": progress.items_failed,
                "items_skipped": progress.items_skipped,
                "items_canceled": progress.items_canceled,
                "items_pending": progress.items_pending,
                "time_to_start_ms": progress.time_to_start_ms,
                "time_processing_ms": progress.time_processing_ms,
                "average_duration_ms_per_item": progress.average_duration_ms_per_item,
                "eta_ms": progress.eta_ms,
                "rate_limited": progress.rate_limited
            }
        ))
    
    async def broadcast_video_update(self, job_id: str, video: VideoProgress, event_type: EventType):
        """Broadcast video state update."""
        await self.send_message_to_job(job_id, WebSocketMessage(
            type=event_type,
            ts=datetime.utcnow().isoformat(),
            correlation_id=str(uuid.uuid4()),
            data={
                "id": video.id,
                "job_id": video.job_id,
                "state": video.state.value,
                "percent_complete": video.percent_complete,
                "row_index": video.row_index,
                "title": video.title,
                "created_at": video.created_at.isoformat(),
                "updated_at": video.updated_at.isoformat()
            }
        ))
    
    def start_server(self):
        """Start the WebSocket server in a separate thread."""
        if self._running:
            return
        
        self._running = True
        self._server_thread = threading.Thread(target=self._run_server, daemon=True)
        self._server_thread.start()
        logger.info(f"WebSocket server started on {self.host}:{self.port}")
    
    def stop_server(self):
        """Stop the WebSocket server."""
        self._running = False
        if self._server_thread:
            self._server_thread.join()
        logger.info("WebSocket server stopped")
    
    def _run_server(self):
        """Run the WebSocket server."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Import WebSocketServer here to avoid circular imports
            from websockets.server import serve
            
            loop.run_until_complete(
                serve(self.handle_client, self.host, self.port)
            )
            loop.run_forever()
        except Exception as e:
            logger.error(f"WebSocket server error: {e}")
        finally:
            loop.close()


class ProgressMonitor:
    """Main progress monitoring system orchestrating all components."""
    
    def __init__(self, supabase_url: str, supabase_key: str, 
                 ws_host: str = '0.0.0.0', ws_port: int = 8765):
        self.supabase_client = SupabaseRealtimeClient(supabase_url, supabase_key)
        self.websocket_broadcaster = WebSocketBroadcaster(ws_host, ws_port)
        self.progress_calculator = ProgressCalculator()
        
        # Active job tracking
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        self.job_lock = threading.Lock()
        
        # Event handlers
        self.state_change_handlers: List[Callable] = []
        self.progress_handlers: List[Callable] = []
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._running = False
    
    def add_state_change_handler(self, handler: Callable):
        """Add a handler for job state changes."""
        self.state_change_handlers.append(handler)
    
    def add_progress_handler(self, handler: Callable):
        """Add a handler for progress updates."""
        self.progress_handlers.append(handler)
    
    def register_job(self, job_id: str, job_data: Dict[str, Any]):
        """Register a job for monitoring."""
        with self.job_lock:
            # Initialize job tracking
            self.active_jobs[job_id] = {
                'id': job_id,
                'state': JobState.PENDING,
                'data': job_data,
                'start_time': datetime.utcnow(),
                'last_progress_update': datetime.utcnow(),
                'video_count': 0,
                'completed_videos': 0,
                'failed_videos': 0
            }
        
        # Subscribe to Supabase Realtime changes
        self.supabase_client.subscribe_to_job_changes(job_id, self._handle_realtime_update)
        
        # Start WebSocket broadcasting for this job
        logger.info(f"Registered job {job_id} for monitoring")
    
    def unregister_job(self, job_id: str):
        """Unregister a job from monitoring."""
        with self.job_lock:
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
        
        # Unsubscribe from Supabase Realtime
        self.supabase_client.unsubscribe_from_job(job_id)
        
        logger.info(f"Unregistered job {job_id} from monitoring")
    
    def update_job_state(self, job_id: str, new_state: JobState, reason: str = ""):
        """Update job state and broadcast changes."""
        with self.job_lock:
            if job_id not in self.active_jobs:
                logger.warning(f"Job {job_id} not found for state update")
                return
            
            job_info = self.active_jobs[job_id]
            prior_state = job_info['state']
            job_info['state'] = new_state
        
        # Broadcast state change
        asyncio.create_task(
            self.websocket_broadcaster.broadcast_state_change(job_id, prior_state, new_state, reason)
        )
        
        # Call state change handlers
        for handler in self.state_change_handlers:
            try:
                handler(job_id, prior_state, new_state, reason)
            except Exception as e:
                logger.error(f"Error in state change handler: {e}")
        
        # Handle terminal states
        if new_state in [JobState.COMPLETED, JobState.CANCELED, JobState.FAILED]:
            self._finalize_job(job_id, new_state)
    
    def update_job_progress(self, job_id: str, job_data: Dict[str, Any]):
        """Update job progress metrics."""
        with self.job_lock:
            if job_id not in self.active_jobs:
                logger.warning(f"Job {job_id} not found for progress update")
                return
            
            job_info = self.active_jobs[job_id]
            job_info['data'] = job_data
            job_info['last_progress_update'] = datetime.utcnow()
        
        # Calculate progress
        progress = self.progress_calculator.calculate_progress(job_data)
        
        # Update Supabase
        self.supabase_client.publish_progress_update(job_id, progress)
        
        # Broadcast progress update
        asyncio.create_task(
            self.websocket_broadcaster.broadcast_progress(job_id, progress)
        )
        
        # Call progress handlers
        for handler in self.progress_handlers:
            try:
                handler(job_id, progress)
            except Exception as e:
                logger.error(f"Error in progress handler: {e}")
    
    def update_video_progress(self, job_id: str, video_data: Dict[str, Any]):
        """Update individual video progress."""
        video = VideoProgress(
            id=video_data['id'],
            job_id=job_id,
            state=VideoState(video_data['state']),
            percent_complete=video_data.get('percent_complete', 0.0),
            row_index=video_data.get('row_index', 0),
            title=video_data.get('title', ''),
            created_at=datetime.fromisoformat(video_data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(video_data['updated_at'].replace('Z', '+00:00'))
        )
        
        # Determine event type based on video state
        event_type = self._get_video_event_type(video.state)
        
        # Record processing time for progress calculation
        if video.state == VideoState.PROCESSING:
            self.progress_calculator.record_item_start(job_id, video.id)
        elif video.state in [VideoState.COMPLETED, VideoState.FAILED]:
            self.progress_calculator.record_item_completion(job_id, video.id, 
                                                           video.state == VideoState.COMPLETED)
        
        # Broadcast video update
        asyncio.create_task(
            self.websocket_broadcaster.broadcast_video_update(job_id, video, event_type)
        )
        
        # Update job-level video counts
        with self.job_lock:
            if job_id in self.active_jobs:
                job_info = self.active_jobs[job_id]
                if video.state == VideoState.COMPLETED:
                    job_info['completed_videos'] += 1
                elif video.state == VideoState.FAILED:
                    job_info['failed_videos'] += 1
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current job status."""
        with self.job_lock:
            return self.active_jobs.get(job_id)
    
    def get_all_jobs_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all active jobs."""
        with self.job_lock:
            return self.active_jobs.copy()
    
    def start_monitoring(self):
        """Start the progress monitoring system."""
        if self._running:
            return
        
        self._running = True
        
        # Start WebSocket server
        self.websocket_broadcaster.start_server()
        
        # Start background monitoring tasks
        self._start_background_tasks()
        
        logger.info("Progress monitoring system started")
    
    def stop_monitoring(self):
        """Stop the progress monitoring system."""
        if not self._running:
            return
        
        self._running = False
        
        # Stop background tasks
        for task in self._background_tasks:
            task.cancel()
        
        self._background_tasks.clear()
        
        # Stop WebSocket server
        self.websocket_broadcaster.stop_server()
        
        logger.info("Progress monitoring system stopped")
    
    def _handle_realtime_update(self, table: str, payload: Dict[str, Any]):
        """Handle Supabase Realtime updates."""
        try:
            if table == 'job':
                # Handle job-level changes
                job_data = payload['new']
                job_id = job_data['id']
                
                if job_data.get('state'):
                    new_state = JobState(job_data['state'])
                    with self.job_lock:
                        if job_id in self.active_jobs:
                            prior_state = self.active_jobs[job_id]['state']
                            if prior_state != new_state:
                                self.active_jobs[job_id]['state'] = new_state
                
                self.update_job_progress(job_id, job_data)
                
            elif table == 'event':
                # Handle job events
                event_data = payload['new']
                logger.debug(f"Received job event: {event_data}")
                
        except Exception as e:
            logger.error(f"Error handling realtime update: {e}")
    
    def _get_video_event_type(self, video_state: VideoState) -> EventType:
        """Map video state to WebSocket event type."""
        event_mapping = {
            VideoState.PENDING: EventType.VIDEO_UPDATED,
            VideoState.PROCESSING: EventType.VIDEO_UPDATED,
            VideoState.COMPLETED: EventType.VIDEO_COMPLETED,
            VideoState.FAILED: EventType.VIDEO_FAILED,
            VideoState.SKIPPED: EventType.VIDEO_UPDATED,
            VideoState.CANCELED: EventType.VIDEO_UPDATED
        }
        return event_mapping.get(video_state, EventType.VIDEO_UPDATED)
    
    def _finalize_job(self, job_id: str, final_state: JobState):
        """Finalize a completed job."""
        with self.job_lock:
            if job_id not in self.active_jobs:
                return
            
            job_info = self.active_jobs[job_id]
            end_time = datetime.utcnow()
            duration = (end_time - job_info['start_time']).total_seconds()
            
            # Calculate final metrics
            total_videos = job_info.get('video_count', 0)
            completed_videos = job_info.get('completed_videos', 0)
            failed_videos = job_info.get('failed_videos', 0)
            
            final_event_type = {
                JobState.COMPLETED: EventType.JOB_COMPLETED,
                JobState.CANCELED: EventType.JOB_CANCELED,
                JobState.FAILED: EventType.JOB_FAILED
            }[final_state]
            
            # Broadcast final job completion
            asyncio.create_task(
                self.websocket_broadcaster.send_message_to_job(job_id, WebSocketMessage(
                    type=final_event_type,
                    ts=end_time.isoformat(),
                    correlation_id=str(uuid.uuid4()),
                    data={
                        "duration_seconds": duration,
                        "total_videos": total_videos,
                        "completed_videos": completed_videos,
                        "failed_videos": failed_videos,
                        "success_rate": completed_videos / total_videos if total_videos > 0 else 0
                    }
                ))
            )
            
            # Schedule cleanup
            asyncio.create_task(self._cleanup_job(job_id))
    
    async def _cleanup_job(self, job_id: str):
        """Clean up job after completion."""
        await asyncio.sleep(300)  # Wait 5 minutes before cleanup
        self.unregister_job(job_id)
    
    def _start_background_tasks(self):
        """Start background monitoring tasks."""
        # Periodic progress updates
        self._background_tasks.append(
            asyncio.create_task(self._periodic_progress_updates())
        )
        
        # Health monitoring
        self._background_tasks.append(
            asyncio.create_task(self._health_monitor())
        )
    
    async def _periodic_progress_updates(self):
        """Send periodic progress updates for all active jobs."""
        while self._running:
            try:
                with self.job_lock:
                    job_ids = list(self.active_jobs.keys())
                
                for job_id in job_ids:
                    job_info = self.active_jobs[job_id]
                    if job_info['state'] in [JobState.RUNNING, JobState.PAUSING, JobState.PAUSED]:
                        # Request fresh progress from database or job processor
                        # This is a placeholder - implement based on your data source
                        pass
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in periodic progress updates: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _health_monitor(self):
        """Monitor system health and resource usage."""
        while self._running:
            try:
                # Check memory usage
                memory = psutil.virtual_memory()
                if memory.percent > 90:
                    logger.warning(f"High memory usage: {memory.percent}%")
                
                # Check CPU usage
                cpu = psutil.cpu_percent(interval=1)
                if cpu > 80:
                    logger.warning(f"High CPU usage: {cpu}%")
                
                # Check active connections
                active_connections = sum(len(clients) for clients in self.websocket_broadcaster.clients.values())
                logger.debug(f"Active WebSocket connections: {active_connections}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(60)


# Example usage and testing
if __name__ == "__main__":
    import os
    
    # Initialize progress monitor
    monitor = ProgressMonitor(
        supabase_url=os.getenv('SUPABASE_URL', 'http://localhost:54321'),
        supabase_key=os.getenv('SUPABASE_ANON_KEY', 'your-anon-key'),
        ws_host='0.0.0.0',
        ws_port=8765
    )
    
    # Add example handlers
    def on_state_change(job_id: str, prior_state: JobState, new_state: JobState, reason: str):
        logger.info(f"Job {job_id} state changed: {prior_state.value} -> {new_state.value} ({reason})")
    
    def on_progress_update(job_id: str, progress: JobProgress):
        logger.info(f"Job {job_id} progress: {progress.percent_complete:.1f}% "
                   f"(ETA: {progress.eta_ms/1000/60:.1f} minutes)")
    
    monitor.add_state_change_handler(on_state_change)
    monitor.add_progress_handler(on_progress_update)
    
    # Start monitoring
    monitor.start_monitoring()
    
    try:
        # Register a test job
        test_job_id = "job_test_001"
        test_job_data = {
            'id': test_job_id,
            'state': JobState.PENDING.value,
            'items_total': 100,
            'items_completed': 0,
            'items_failed': 0,
            'items_skipped': 0,
            'items_canceled': 0,
            'created_at': datetime.utcnow().isoformat(),
            'rate_limited': False,
            'processing_deadline_ms': 3600000
        }
        
        monitor.register_job(test_job_id, test_job_data)
        
        # Simulate job progression
        import time
        
        # Start job
        time.sleep(1)
        monitor.update_job_state(test_job_id, JobState.RUNNING, "worker_assigned")
        
        # Simulate progress updates
        for i in range(0, 101, 10):
            test_job_data['items_completed'] = i
            test_job_data['state'] = JobState.RUNNING.value
            monitor.update_job_progress(test_job_id, test_job_data)
            
            # Simulate some video completions
            if i > 0:
                video_data = {
                    'id': f'vid_{i:03d}',
                    'state': VideoState.COMPLETED.value,
                    'percent_complete': 100.0,
                    'row_index': i,
                    'title': f'Video {i}',
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                monitor.update_video_progress(test_job_id, video_data)
            
            time.sleep(2)
        
        # Complete job
        monitor.update_job_state(test_job_id, JobState.COMPLETED, "all_items_processed")
        
        # Keep running for demo
        time.sleep(10)
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        monitor.stop_monitoring()