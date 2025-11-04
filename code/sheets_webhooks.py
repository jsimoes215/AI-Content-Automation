"""
Google Sheets Webhook Support for Real-time Sheet Change Processing

This module provides webhook endpoint support for Google Sheets updates, integrating
with the bulk job queue system and real-time event processing infrastructure.

Features:
- Webhook endpoint for receiving Google Sheets change notifications
- Real-time event processing and WebSocket broadcasting
- Sheet change detection and validation
- Integration with bulk job queue system
- Security validation and signature verification
"""

import json
import asyncio
import logging
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.responses import JSONResponse
import asyncpg
import jwt
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===============================
# Data Models and Enums
# ===============================

class WebhookEventType(Enum):
    """Types of Google Sheets webhook events"""
    SHEET_UPDATED = "sheet.updated"
    SHEET_CREATED = "sheet.created"
    SHEET_DELETED = "sheet.deleted"
    RANGE_UPDATED = "range.updated"
    ROW_ADDED = "row.added"
    ROW_DELETED = "row.deleted"
    COLUMN_ADDED = "column.added"
    COLUMN_DELETED = "column.deleted"
    CELL_UPDATED = "cell.updated"

class JobState(Enum):
    """Job states matching the API design"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    CANCELING = "canceling"
    CANCELED = "canceled"
    FAILED = "failed"

class Priority(Enum):
    """Job priority levels"""
    URGENT = "urgent"
    NORMAL = "normal"
    LOW = "low"

@dataclass
class SheetChange:
    """Represents a change in a Google Sheet"""
    sheet_id: str
    event_type: WebhookEventType
    range_address: Optional[str] = None
    old_values: Optional[List[List[Any]]] = None
    new_values: Optional[List[List[Any]]] = None
    user_email: Optional[str] = None
    timestamp: Optional[datetime] = None
    revision_id: Optional[str] = None

@dataclass
class WebhookValidationResult:
    """Result of webhook validation"""
    is_valid: bool
    error_message: Optional[str] = None
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    scopes: Optional[List[str]] = None

@dataclass
class ProcessingJob:
    """Job data for queue processing"""
    job_id: str
    tenant_id: str
    sheet_id: str
    change_data: SheetChange
    priority: Priority
    callback_url: Optional[str] = None
    idempotency_key: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# ===============================
# Configuration and Dependencies
# ===============================

class WebhookConfig:
    """Configuration for webhook processing"""
    
    def __init__(self):
        self.secret_key = "your-webhook-secret-key"  # From environment
        self.google_verify_token = "google-verify-token"  # From environment
        self.max_sheet_size = 1000000  # cells
        self.batch_size = 100
        self.max_retries = 3
        self.retry_backoff_seconds = [1, 3, 9]
        self.rate_limits = {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "cells_per_minute": 100000
        }
        self.supported_ranges = [
            "A1:Z1000", "A1:AA1000", "A1:Z500", "A1:Z100"
        ]
        
    def validate_sheet_access(self, sheet_id: str, user_token: str) -> bool:
        """Validate user has access to the specified sheet"""
        # Implementation would check Google API permissions
        # This is a placeholder for the actual validation logic
        return True

config = WebhookConfig()

# ===============================
# Security and Validation
# ===============================

class SecurityValidator:
    """Handles security validation for webhook requests"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode('utf-8')
    
    def verify_google_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Google Sheets webhook signature"""
        expected = hmac.new(
            self.secret_key,
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)
    
    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token from user"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=["HS256"]
            )
            return payload
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    def validate_sheet_permissions(self, token_payload: Dict, sheet_id: str) -> bool:
        """Validate user permissions for the sheet"""
        # Check if user has access to this sheet
        user_scopes = token_payload.get('scopes', [])
        tenant_id = token_payload.get('tenant_id')
        
        # This would check against the actual sheet permissions
        # For now, return True as placeholder
        return "sheets:read" in user_scopes or "sheets:write" in user_scopes
    
    def validate_change_data(self, change: SheetChange) -> List[str]:
        """Validate sheet change data"""
        errors = []
        
        # Validate sheet ID format
        if not change.sheet_id or len(change.sheet_id) < 10:
            errors.append("Invalid sheet ID")
        
        # Validate range if provided
        if change.range_address and change.range_address not in config.supported_ranges:
            errors.append(f"Unsupported range format: {change.range_address}")
        
        # Validate data size
        if change.new_values:
            total_cells = sum(len(row) for row in change.new_values)
            if total_cells > config.max_sheet_size:
                errors.append(f"Sheet change too large: {total_cells} cells")
        
        # Validate timestamp
        if change.timestamp and change.timestamp > datetime.now(timezone.utc):
            errors.append("Timestamp cannot be in the future")
        
        return errors

security_validator = SecurityValidator(config.secret_key)

# ===============================
# Database and Queue Integration
# ===============================

class DatabaseManager:
    """Manages database operations"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    async def create_pool(self) -> asyncpg.Pool:
        """Create database connection pool"""
        return await asyncpg.create_pool(self.connection_string)
    
    async def store_webhook_event(self, conn: asyncpg.Connection, 
                                 change: SheetChange, 
                                 job: ProcessingJob) -> str:
        """Store webhook event in database"""
        event_id = await conn.fetchval("""
            INSERT INTO webhook_events (
                event_id, tenant_id, sheet_id, event_type, 
                change_data, job_id, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING event_id
        """, 
            f"webhook_{datetime.now().timestamp()}",
            job.tenant_id,
            change.sheet_id,
            change.event_type.value,
            json.dumps(asdict(change)),
            job.job_id,
            datetime.now(timezone.utc)
        )
        return event_id
    
    async def create_bulk_job(self, conn: asyncpg.Connection, job: ProcessingJob) -> str:
        """Create bulk job from webhook event"""
        job_id = await conn.fetchval("""
            INSERT INTO bulk_jobs (
                id, tenant_id, state, priority, 
                input_source, callback_url, 
                idempotency_key, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """,
            job.job_id,
            job.tenant_id,
            JobState.PENDING.value,
            job.priority.value,
            json.dumps({
                "type": "sheet_webhook",
                "sheet_id": job.sheet_id,
                "change_data": asdict(job.change_data)
            }),
            job.callback_url,
            job.idempotency_key,
            job.created_at,
            job.updated_at
        )
        return job_id

class QueueManager:
    """Manages job queue operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def queue_job(self, job: ProcessingJob) -> bool:
        """Add job to processing queue"""
        pool = await self.db_manager.create_pool()
        try:
            async with pool.acquire() as conn:
                # Create bulk job record
                await self.db_manager.create_bulk_job(conn, job)
                
                # Add to processing queue
                await conn.execute("""
                    INSERT INTO job_queue (
                        job_id, tenant_id, priority, 
                        status, payload, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    job.job_id,
                    job.tenant_id,
                    job.priority.value,
                    "queued",
                    json.dumps(asdict(job)),
                    datetime.now(timezone.utc)
                )
                return True
        except Exception as e:
            logger.error(f"Failed to queue job: {str(e)}")
            return False
        finally:
            await pool.close()
    
    async def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get job status"""
        pool = await self.db_manager.create_pool()
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM bulk_jobs WHERE id = $1
                """, job_id)
                
                if row:
                    return dict(row)
                return None
        finally:
            await pool.close()

# ===============================
# Real-time Event Processing
# ===============================

class EventBroadcaster:
    """Handles real-time event broadcasting via WebSockets"""
    
    def __init__(self):
        self.websocket_connections: Dict[str, List] = {}
        self.tenant_channels: Dict[str, str] = {}
    
    async def broadcast_job_event(self, job_id: str, event_type: str, data: Dict):
        """Broadcast job event to connected WebSocket clients"""
        message = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "job_id": job_id,
            "data": data
        }
        
        # Broadcast to all connections for this job
        connections = self.websocket_connections.get(job_id, [])
        for websocket in connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {str(e)}")
                # Remove failed connection
                if websocket in connections:
                    connections.remove(websocket)
    
    async def broadcast_sheet_event(self, sheet_id: str, event_type: str, data: Dict):
        """Broadcast sheet event to connected clients"""
        message = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sheet_id": sheet_id,
            "data": data
        }
        
        # Broadcast to all connections monitoring this sheet
        for job_id, connections in self.websocket_connections.items():
            if any(data.get('sheet_id') == sheet_id for conn in connections):
                for websocket in connections:
                    try:
                        await websocket.send_text(json.dumps(message))
                    except Exception as e:
                        logger.error(f"Failed to send WebSocket message: {str(e)}")
    
    def register_connection(self, job_id: str, websocket):
        """Register a WebSocket connection for a job"""
        if job_id not in self.websocket_connections:
            self.websocket_connections[job_id] = []
        self.websocket_connections[job_id].append(websocket)
    
    def unregister_connection(self, job_id: str, websocket):
        """Unregister a WebSocket connection"""
        if job_id in self.websocket_connections:
            if websocket in self.websocket_connections[job_id]:
                self.websocket_connections[job_id].remove(websocket)
            
            # Clean up empty lists
            if not self.websocket_connections[job_id]:
                del self.websocket_connections[job_id]

event_broadcaster = EventBroadcaster()

# ===============================
# Sheet Change Detection
# ===============================

class SheetChangeDetector:
    """Detects and processes sheet changes"""
    
    def __init__(self):
        self.change_cache: Dict[str, Dict] = {}
        self.processed_changes: set = set()
    
    async def validate_change_origin(self, change: SheetChange) -> bool:
        """Validate that the change originated from a legitimate source"""
        # Check if change matches expected patterns
        # Verify against Google Sheets API if needed
        return True
    
    async def detect_duplicate(self, change: SheetChange) -> bool:
        """Detect if this change has already been processed"""
        change_key = f"{change.sheet_id}_{change.timestamp}_{change.revision_id}"
        if change_key in self.processed_changes:
            return True
        
        self.processed_changes.add(change_key)
        return False
    
    async def enrich_change_data(self, change: SheetChange) -> SheetChange:
        """Enrich change data with additional information"""
        # Fetch additional metadata from Google Sheets API
        # Add computed fields like change impact, affected range size, etc.
        return change
    
    def calculate_change_impact(self, change: SheetChange) -> Dict[str, Any]:
        """Calculate the impact of a sheet change"""
        impact = {
            "cells_affected": 0,
            "range_size": 0,
            "has_formulas": False,
            "has_formatting": False
        }
        
        if change.new_values:
            impact["cells_affected"] = sum(len(row) for row in change.new_values)
            impact["range_size"] = len(change.new_values)
            
            # Check for formulas and formatting (simplified)
            for row in change.new_values:
                for cell in row:
                    if isinstance(cell, str) and cell.startswith('='):
                        impact["has_formulas"] = True
                    if isinstance(cell, dict) and "formatting" in cell:
                        impact["has_formatting"] = True
        
        return impact

sheet_change_detector = SheetChangeDetector()

# ===============================
# Webhook Processing Engine
# ===============================

class WebhookProcessor:
    """Main webhook processing engine"""
    
    def __init__(self, db_manager: DatabaseManager, queue_manager: QueueManager):
        self.db_manager = db_manager
        self.queue_manager = queue_manager
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    async def process_webhook(self, 
                            request: Request,
                            change: SheetChange,
                            validation_result: WebhookValidationResult) -> Dict[str, Any]:
        """Process incoming webhook request"""
        try:
            # Create processing job
            job = ProcessingJob(
                job_id=f"job_{datetime.now().timestamp()}_{change.sheet_id}",
                tenant_id=validation_result.tenant_id,
                sheet_id=change.sheet_id,
                change_data=change,
                priority=self._determine_priority(change),
                idempotency_key=f"webhook_{change.sheet_id}_{change.timestamp}",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Validate change data
            validation_errors = security_validator.validate_change_data(change)
            if validation_errors:
                raise HTTPException(
                    status_code=422,
                    detail=f"Validation errors: {', '.join(validation_errors)}"
                )
            
            # Check for duplicates
            if await sheet_change_detector.detect_duplicate(change):
                logger.info(f"Duplicate change detected for sheet {change.sheet_id}")
                return {"status": "duplicate", "message": "Change already processed"}
            
            # Enrich change data
            change = await sheet_change_detector.enrich_change_data(change)
            
            # Queue for processing
            success = await self.queue_manager.queue_job(job)
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to queue job for processing"
                )
            
            # Broadcast real-time event
            await event_broadcaster.broadcast_job_event(
                job.job_id,
                "job.created",
                {
                    "sheet_id": change.sheet_id,
                    "event_type": change.event_type.value,
                    "impact": sheet_change_detector.calculate_change_impact(change)
                }
            )
            
            return {
                "status": "success",
                "job_id": job.job_id,
                "message": "Webhook processed successfully"
            }
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error: {str(e)}"
            )
    
    def _determine_priority(self, change: SheetChange) -> Priority:
        """Determine job priority based on change characteristics"""
        # Urgent: Large changes, critical sheets
        if change.range_address and "A1:Z" in change.range_address:
            return Priority.URGENT
        
        # Normal: Medium-sized changes
        if change.new_values and sum(len(row) for row in change.new_values) > 10:
            return Priority.NORMAL
        
        # Low: Small changes
        return Priority.LOW

# Initialize components
db_manager = DatabaseManager("postgresql://user:pass@localhost/db")
queue_manager = QueueManager(db_manager)
webhook_processor = WebhookProcessor(db_manager, queue_manager)

# ===============================
# FastAPI Application
# ===============================

app = FastAPI(title="Google Sheets Webhook API", version="1.0.0")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/api/v1/sheets/webhook")
async def receive_sheets_webhook(
    request: Request,
    google_signature: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    content_type: str = Header("application/json")
):
    """
    Webhook endpoint for receiving Google Sheets change notifications
    
    This endpoint handles incoming webhook requests from Google Sheets,
    validates security, and processes sheet changes in real-time.
    """
    try:
        # Read request body
        body = await request.body()
        
        # Verify Google signature if provided
        if google_signature and not security_validator.verify_google_signature(body, google_signature):
            raise HTTPException(status_code=401, detail="Invalid Google signature")
        
        # Parse webhook payload
        try:
            payload = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Validate authorization
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization")
        
        token = authorization.split(" ", 1)[1]
        token_payload = security_validator.verify_jwt_token(token)
        
        # Extract change data
        change = SheetChange(
            sheet_id=payload.get("spreadsheetId"),
            event_type=WebhookEventType(payload.get("eventType", "sheet.updated")),
            range_address=payload.get("range"),
            old_values=payload.get("oldValues"),
            new_values=payload.get("newValues"),
            user_email=payload.get("userId"),
            timestamp=datetime.fromisoformat(payload.get("timestamp").replace('Z', '+00:00')),
            revision_id=payload.get("revisionId")
        )
        
        # Validate sheet permissions
        if not security_validator.validate_sheet_permissions(token_payload, change.sheet_id):
            raise HTTPException(status_code=403, detail="Insufficient permissions for sheet")
        
        # Validate change origin
        if not await sheet_change_detector.validate_change_origin(change):
            raise HTTPException(status_code=401, detail="Invalid change origin")
        
        # Create validation result
        validation_result = WebhookValidationResult(
            is_valid=True,
            tenant_id=token_payload.get("tenant_id"),
            user_id=token_payload.get("sub"),
            scopes=token_payload.get("scopes", [])
        )
        
        # Process webhook
        result = await webhook_processor.process_webhook(
            request, change, validation_result
        )
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in webhook endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/webhook/jobs/{job_id}")
async def get_job_status(job_id: str, authorization: str = Header(...)):
    """Get status of a webhook processing job"""
    try:
        # Verify authorization
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization")
        
        token = authorization.split(" ", 1)[1]
        token_payload = security_validator.verify_jwt_token(token)
        
        # Get job status
        job = await queue_manager.get_job_status(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Verify tenant access
        if job["tenant_id"] != token_payload.get("tenant_id"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return JSONResponse(content=job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/sheets/webhook/verify")
async def verify_webhook_endpoint(
    verification_code: str,
    sheet_id: str,
    authorization: str = Header(...)
):
    """Verify webhook endpoint with Google Sheets"""
    if verification_code != config.google_verify_token:
        raise HTTPException(status_code=401, detail="Invalid verification code")
    
    # In a real implementation, this would register the webhook with Google Sheets API
    logger.info(f"Webhook verified for sheet {sheet_id}")
    
    return {"status": "verified", "sheet_id": sheet_id}

# ===============================
# WebSocket Endpoint for Real-time Updates
# ===============================

from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/job/{job_id}")
async def websocket_job_updates(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time job updates"""
    await websocket.accept()
    event_broadcaster.register_connection(job_id, websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        event_broadcaster.unregister_connection(job_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        event_broadcaster.unregister_connection(job_id, websocket)

# ===============================
# Batch Processing Helpers
# ===============================

class BatchProcessor:
    """Handles batch processing of multiple sheet changes"""
    
    def __init__(self, webhook_processor: WebhookProcessor):
        self.webhook_processor = webhook_processor
        self.batch_queue: List[Dict] = []
        self.batch_size = config.batch_size
    
    async def add_to_batch(self, change: SheetChange, validation_result: WebhookValidationResult):
        """Add change to batch queue"""
        self.batch_queue.append({
            "change": change,
            "validation_result": validation_result
        })
        
        if len(self.batch_queue) >= self.batch_size:
            await self.process_batch()
    
    async def process_batch(self):
        """Process all queued changes in batch"""
        if not self.batch_queue:
            return
        
        batch = self.batch_queue.copy()
        self.batch_queue.clear()
        
        # Process in parallel
        tasks = []
        for item in batch:
            task = self.webhook_processor.process_webhook(
                None,  # Request not needed for batch
                item["change"],
                item["validation_result"]
            )
            tasks.append(task)
        
        # Wait for all to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"Processed batch of {len(batch)} changes")

batch_processor = BatchProcessor(webhook_processor)

# ===============================
# Rate Limiting
# ===============================

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}  # tenant_id -> [timestamps]
    
    async def is_rate_limited(self, tenant_id: str) -> bool:
        """Check if tenant is rate limited"""
        now = datetime.now(timezone.utc)
        window_start = now.timestamp() - 60  # 1 minute window
        
        # Clean old requests
        if tenant_id in self.requests:
            self.requests[tenant_id] = [
                ts for ts in self.requests[tenant_id] 
                if ts > window_start
            ]
        else:
            self.requests[tenant_id] = []
        
        # Check limit
        if len(self.requests[tenant_id]) >= config.rate_limits["requests_per_minute"]:
            return True
        
        # Add current request
        self.requests[tenant_id].append(now.timestamp())
        return False

rate_limiter = RateLimiter()

# ===============================
# Export Configuration and Startup
# ===============================

async def startup_event():
    """Application startup tasks"""
    logger.info("Starting Google Sheets Webhook Service")
    # Initialize database connections, cache, etc.

async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("Shutting down Google Sheets Webhook Service")
    # Clean up resources

app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

# Export main components for testing and integration
__all__ = [
    "app",
    "webhook_processor",
    "event_broadcaster",
    "security_validator",
    "WebhookEventType",
    "SheetChange",
    "ProcessingJob",
    "WebhookValidationResult"
]