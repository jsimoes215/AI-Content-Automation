"""
Scheduling Optimization API for AI Content Automation System
Provides endpoints for recommendations, calendar management, and optimization
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Depends, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
import json
import uuid
import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import Database

app = FastAPI(title="Scheduling Optimization API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager for real-time updates
class SchedulingConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.schedule_subscriptions: Dict[str, List[WebSocket]] = {}  # schedule_id -> connections

    async def connect(self, websocket: WebSocket, schedule_id: Optional[str] = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if schedule_id:
            if schedule_id not in self.schedule_subscriptions:
                self.schedule_subscriptions[schedule_id] = []
            self.schedule_subscriptions[schedule_id].append(websocket)
        
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "data": {"message": "Connected to scheduling updates", "schedule_id": schedule_id}
        })

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from all schedule subscriptions
        for schedule_id, connections in self.schedule_subscriptions.items():
            if websocket in connections:
                connections.remove(websocket)
                if not connections:
                    del self.schedule_subscriptions[schedule_id]

    async def broadcast(self, message: dict, schedule_id: Optional[str] = None):
        if schedule_id and schedule_id in self.schedule_subscriptions:
            # Send to schedule-specific subscribers
            connections = self.schedule_subscriptions[schedule_id]
            for connection in connections[:]:  # Copy to avoid modification during iteration
                try:
                    await connection.send_json(message)
                except:
                    if connection in connections:
                        connections.remove(connection)
        else:
            # Broadcast to all connections
            for connection in self.active_connections[:]:  # Copy to avoid modification
                try:
                    await connection.send_json(message)
                except:
                    if connection in self.active_connections:
                        self.active_connections.remove(connection)

    async def send_to_connection(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
        except:
            self.disconnect(websocket)

scheduling_manager = SchedulingConnectionManager()

# Pydantic Models
class RecommendationRequest(BaseModel):
    platforms: Optional[List[str]] = None
    target_count: int = Field(default=10, ge=10, le=200)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    timezone: Optional[str] = "UTC"
    content_type: Optional[str] = None
    page_token: Optional[str] = None
    page_size: int = Field(default=50, ge=10, le=200)
    sort: str = Field(default="score", regex="^(created_at|score)$")
    order: str = Field(default="desc", regex="^(asc|desc)$")

class Recommendation(BaseModel):
    id: str
    window_start: datetime
    window_end: datetime
    score: float
    reasons: List[str]
    platforms: List[str]
    confidence: float
    content_types: List[str]

class RecommendationResponse(BaseModel):
    data: List[Recommendation]
    page: Dict[str, Any]

class ScheduleItemCreate(BaseModel):
    content_id: str
    platform: str
    scheduled_time: datetime
    metadata: Optional[Dict[str, Any]] = None
    callbacks: Optional[Dict[str, str]] = None

class ScheduleCreateRequest(BaseModel):
    title: str
    timezone: str = "UTC"
    items: List[ScheduleItemCreate]
    processing_deadline_ms: Optional[int] = 7200000  # 2 hours default

    @validator('items')
    def validate_items(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one item is required')
        return v

class ScheduleItem(BaseModel):
    id: str
    content_id: str
    platform: str
    state: str
    scheduled_time: datetime
    published_time: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    callbacks: Optional[Dict[str, str]] = None
    errors: List[Dict[str, Any]] = []
    artifacts: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime

class Schedule(BaseModel):
    id: str
    tenant_id: str
    state: str
    title: str
    timezone: str
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
    processing_deadline_ms: int
    created_at: datetime
    updated_at: datetime
    idempotency_key: Optional[str] = None
    items: Optional[List[ScheduleItem]] = None
    page: Optional[Dict[str, Any]] = None

class ScheduleResponse(BaseModel):
    id: str
    tenant_id: str
    state: str
    title: str
    timezone: str
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
    processing_deadline_ms: int
    created_at: datetime
    updated_at: datetime
    idempotency_key: Optional[str] = None

class OptimizationTarget(BaseModel):
    content_id: str
    platform: str
    current_scheduled_time: datetime

class OptimizationConstraint(BaseModel):
    do_not_move_before: Optional[datetime] = None
    do_not_move_after: Optional[datetime] = None
    blackout_windows: Optional[List[Dict[str, datetime]]] = None
    platform_specific_rules: Optional[Dict[str, Any]] = None

class OptimizationRequest(BaseModel):
    schedule_id: str
    targets: List[OptimizationTarget]
    constraints: Optional[OptimizationConstraint] = None
    apply: bool = False

class OptimizationChange(BaseModel):
    content_id: str
    platform: str
    previous_time: datetime
    new_time: datetime
    score_before: float
    score_after: float
    reason: str
    confidence: float

class OptimizationMetrics(BaseModel):
    total_targeted: int
    changed_count: int
    unchanged_count: int
    average_score_lift: float
    rate_limited: bool

class OptimizationResult(BaseModel):
    id: str
    tenant_id: str
    schedule_id: str
    state: str
    changes: List[OptimizationChange]
    metrics: OptimizationMetrics
    created_at: datetime
    updated_at: datetime

class ErrorEnvelope(BaseModel):
    error_code: str
    error_message: str
    error_class: Optional[str] = None
    detail: Optional[Dict[str, Any]] = None

# Database Service for Scheduling
class SchedulingService:
    def __init__(self):
        self.db = Database()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def get_recommendations(self, tenant_id: str, request: RecommendationRequest) -> RecommendationResponse:
        """Get scheduling recommendations based on platform data and user preferences"""
        try:
            cursor = self.db.conn.cursor()
            
            # Build base query with platform timing data
            query = """
            SELECT 
                'rec_' || substr(id::text, 1, 16) as id,
                slot_start as window_start,
                slot_end as window_end,
                confidence_score as score,
                ARRAY['audience_active_peak', 'platform_optimized'] as reasons,
                ARRAY[platform_id] as platforms,
                confidence_score as confidence,
                ARRAY[COALESCE(content_format, 'general')] as content_types
            FROM recommended_schedule_slots
            WHERE valid_to IS NULL
            """
            
            params = []
            
            # Add platform filters
            if request.platforms:
                placeholders = ','.join(['?' for _ in request.platforms])
                query += f" AND platform_id IN ({placeholders})"
                params.extend(request.platforms)
            
            # Add date range filters
            if request.start_at:
                query += " AND slot_start >= ?"
                params.append(request.start_at.isoformat())
            
            if request.end_at:
                query += " AND slot_end <= ?"
                params.append(request.end_at.isoformat())
            
            # Add content type filter
            if request.content_type:
                query += " AND (content_format = ? OR content_format IS NULL)"
                params.append(request.content_type)
            
            # Add ordering and pagination
            query += f" ORDER BY {request.sort} {request.order.upper()}"
            
            if request.page_size:
                query += " LIMIT ?"
                params.append(request.page_size)
            
            if request.page_token:
                # Decode cursor for pagination (simplified)
                query += " OFFSET ?"
                params.append(int(request.page_token))
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            recommendations = []
            for row in rows:
                recommendations.append(Recommendation(
                    id=row['id'],
                    window_start=datetime.fromisoformat(row['window_start'].replace('Z', '+00:00')),
                    window_end=datetime.fromisoformat(row['window_end'].replace('Z', '+00:00')),
                    score=float(row['score']),
                    reasons=row['reasons'],
                    platforms=row['platforms'],
                    confidence=float(row['confidence']),
                    content_types=row['content_types']
                ))
            
            # Generate next page token if there are more results
            next_page_token = None
            if len(recommendations) == request.page_size:
                next_page_token = str(int(request.page_token or "0") + request.page_size)
            
            return RecommendationResponse(
                data=recommendations,
                page={
                    "next_page_token": next_page_token,
                    "page_size": request.page_size
                }
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch recommendations: {str(e)}")
    
    def create_schedule(self, tenant_id: str, request: ScheduleCreateRequest, idempotency_key: Optional[str] = None) -> ScheduleResponse:
        """Create a new schedule"""
        try:
            cursor = self.db.conn.cursor()
            
            # Check for idempotency if provided
            if idempotency_key:
                cursor.execute(
                    "SELECT id FROM content_calendar WHERE idempotency_key = ? AND created_by = ?",
                    (idempotency_key, tenant_id)
                )
                existing = cursor.fetchone()
                if existing:
                    return self.get_schedule(existing['id'])
            
            # Create schedule
            schedule_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO content_calendar (id, name, timezone, created_by, owned_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                schedule_id,
                request.title,
                request.timezone,
                tenant_id,
                tenant_id,
                datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            ))
            
            # Create schedule items
            items_data = []
            for item in request.items:
                item_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO content_schedule_items (
                        id, calendar_id, platform_id, planned_start, scheduled_at, 
                        timezone, status, created_by, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item_id,
                    schedule_id,
                    item.platform,
                    item.scheduled_time,
                    item.scheduled_time,
                    request.timezone,
                    'planned',
                    tenant_id,
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc)
                ))
                
                items_data.append({
                    'id': item_id,
                    'content_id': item.content_id,
                    'platform': item.platform,
                    'scheduled_time': item.scheduled_time
                })
            
            self.db.conn.commit()
            
            # Broadcast schedule creation
            asyncio.create_task(scheduling_manager.broadcast({
                "type": "schedule.created",
                "data": {
                    "schedule_id": schedule_id,
                    "title": request.title,
                    "items_count": len(request.items)
                }
            }))
            
            return ScheduleResponse(
                id=schedule_id,
                tenant_id=tenant_id,
                state="pending",
                title=request.title,
                timezone=request.timezone,
                percent_complete=0.0,
                items_total=len(request.items),
                items_completed=0,
                items_failed=0,
                items_skipped=0,
                items_canceled=0,
                items_pending=len(request.items),
                time_to_start_ms=None,
                time_processing_ms=0,
                average_duration_ms_per_item=None,
                eta_ms=None,
                rate_limited=False,
                processing_deadline_ms=request.processing_deadline_ms or 7200000,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                idempotency_key=idempotency_key
            )
            
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")
    
    def get_schedule(self, schedule_id: str, tenant_id: str, 
                    page_token: Optional[str] = None, 
                    page_size: int = 50,
                    expand: Optional[List[str]] = None) -> ScheduleResponse:
        """Get schedule details with items"""
        try:
            cursor = self.db.conn.cursor()
            
            # Get schedule
            cursor.execute("""
                SELECT cc.*, 
                       COUNT(csi.id) as total_items,
                       COUNT(CASE WHEN csi.status = 'posted' THEN 1 END) as completed_items,
                       COUNT(CASE WHEN csi.status = 'failed' THEN 1 END) as failed_items,
                       COUNT(CASE WHEN csi.status = 'skipped' THEN 1 END) as skipped_items,
                       COUNT(CASE WHEN csi.status = 'canceled' THEN 1 END) as canceled_items
                FROM content_calendar cc
                LEFT JOIN content_schedule_items csi ON cc.id = csi.calendar_id
                WHERE cc.id = ? AND cc.created_by = ?
                GROUP BY cc.id
            """, (schedule_id, tenant_id))
            
            schedule_row = cursor.fetchone()
            if not schedule_row:
                raise HTTPException(status_code=404, detail="Schedule not found")
            
            # Calculate progress
            total_items = schedule_row['total_items'] or 0
            completed_items = schedule_row['completed_items'] or 0
            failed_items = schedule_row['failed_items'] or 0
            skipped_items = schedule_row['skipped_items'] or 0
            canceled_items = schedule_row['canceled_items'] or 0
            pending_items = total_items - completed_items - failed_items - skipped_items - canceled_items
            
            percent_complete = ((completed_items + skipped_items) / total_items * 100) if total_items > 0 else 0
            
            # Get schedule items if expand requested
            items = []
            if expand and 'items' in expand:
                items_query = """
                SELECT csi.*, gc.file_path, gc.content_type, gc.platform
                FROM content_schedule_items csi
                LEFT JOIN generated_content gc ON csi.video_job_id = gc.scene_id
                WHERE csi.calendar_id = ?
                ORDER BY csi.created_at DESC
                """
                
                if page_size:
                    items_query += f" LIMIT {page_size}"
                if page_token:
                    items_query += f" OFFSET {int(page_token)}"
                
                cursor.execute(items_query, (schedule_id,))
                item_rows = cursor.fetchall()
                
                for row in item_rows:
                    items.append(ScheduleItem(
                        id=row['id'],
                        content_id=row['video_job_id'] or '',
                        platform=row['platform_id'],
                        state=row['status'],
                        scheduled_time=row['scheduled_at'],
                        published_time=row['updated_at'] if row['status'] == 'posted' else None,
                        metadata=None,
                        callbacks=None,
                        errors=[],
                        artifacts=[],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    ))
            
            return ScheduleResponse(
                id=schedule_row['id'],
                tenant_id=schedule_row['created_by'],
                state=schedule_row['status'] if hasattr(schedule_row, 'status') else 'running',
                title=schedule_row['name'],
                timezone=schedule_row['timezone'],
                percent_complete=percent_complete,
                items_total=total_items,
                items_completed=completed_items,
                items_failed=failed_items,
                items_skipped=skipped_items,
                items_canceled=canceled_items,
                items_pending=pending_items,
                time_to_start_ms=1500,  # Mock value
                time_processing_ms=45000,  # Mock value
                average_duration_ms_per_item=220,  # Mock value
                eta_ms=350000,  # Mock value
                rate_limited=False,
                processing_deadline_ms=7200000,
                created_at=schedule_row['created_at'],
                updated_at=schedule_row['updated_at'],
                items=items if items else None,
                page={
                    "next_page_token": str(int(page_token or "0") + len(items)) if items else None,
                    "page_size": len(items) if items else 0
                } if items else None
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch schedule: {str(e)}")
    
    def optimize_schedule(self, tenant_id: str, request: OptimizationRequest) -> OptimizationResult:
        """Optimize schedule timing"""
        try:
            cursor = self.db.conn.cursor()
            
            # Create optimization record
            opt_id = f"opt_{str(uuid.uuid4())[:16]}"
            
            # Mock optimization logic - in real implementation, this would use ML models
            changes = []
            
            for target in request.targets:
                # Simulate optimization improvement
                import random
                score_before = random.uniform(0.4, 0.8)
                score_after = min(score_before + random.uniform(0.1, 0.3), 1.0)
                
                # Generate new time (30-90 minutes later)
                from datetime import timedelta
                new_time = target.current_scheduled_time + timedelta(minutes=random.randint(30, 90))
                
                change = OptimizationChange(
                    content_id=target.content_id,
                    platform=target.platform,
                    previous_time=target.current_scheduled_time,
                    new_time=new_time,
                    score_before=score_before,
                    score_after=score_after,
                    reason="audience_active_peak",
                    confidence=random.uniform(0.6, 0.9)
                )
                changes.append(change)
                
                # Update schedule item if apply is True
                if request.apply:
                    cursor.execute("""
                        UPDATE content_schedule_items 
                        SET scheduled_at = ?, updated_at = ?
                        WHERE video_job_id = ? AND platform_id = ?
                    """, (
                        new_time,
                        datetime.now(timezone.utc),
                        target.content_id,
                        target.platform
                    ))
            
            self.db.conn.commit()
            
            # Broadcast optimization completion
            asyncio.create_task(scheduling_manager.broadcast({
                "type": "optimization.completed",
                "data": {
                    "opt_id": opt_id,
                    "schedule_id": request.schedule_id,
                    "changes_count": len(changes)
                },
                "correlation_id": f"sched_{request.schedule_id[:8]}"
            }))
            
            metrics = OptimizationMetrics(
                total_targeted=len(request.targets),
                changed_count=len(changes),
                unchanged_count=0,
                average_score_lift=sum(c.score_after - c.score_before for c in changes) / len(changes) if changes else 0,
                rate_limited=False
            )
            
            return OptimizationResult(
                id=opt_id,
                tenant_id=tenant_id,
                schedule_id=request.schedule_id,
                state="completed",
                changes=changes,
                metrics=metrics,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            self.db.conn.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to optimize schedule: {str(e)}")

# Dependencies
async def get_current_user():
    """Mock authentication - in real implementation, this would validate JWT tokens"""
    return {"id": "tenant_7x9y", "scopes": ["schedules:read", "schedules:write", "optimization:write"]}

# API Routes

@app.get("/api/v1/scheduling/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    platforms: Optional[List[str]] = Query(None),
    target_count: int = Query(10, ge=10, le=200),
    start_at: Optional[datetime] = Query(None),
    end_at: Optional[datetime] = Query(None),
    timezone: str = Query("UTC"),
    content_type: Optional[str] = Query(None),
    page_token: Optional[str] = Query(None),
    page_size: int = Query(50, ge=10, le=200),
    sort: str = Query("score", regex="^(created_at|score)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: dict = Depends(get_current_user)
):
    """Get scheduling recommendations"""
    request = RecommendationRequest(
        platforms=platforms,
        target_count=target_count,
        start_at=start_at,
        end_at=end_at,
        timezone=timezone,
        content_type=content_type,
        page_token=page_token,
        page_size=page_size,
        sort=sort,
        order=order
    )
    
    with SchedulingService() as service:
        return service.get_recommendations(current_user["id"], request)

@app.post("/api/v1/scheduling/calendar", response_model=ScheduleResponse)
async def create_schedule(
    request: ScheduleCreateRequest,
    idempotency_key: Optional[str] = Header(None),
    current_user: dict = Depends(get_current_user)
):
    """Create a new schedule"""
    with SchedulingService() as service:
        return service.create_schedule(current_user["id"], request, idempotency_key)

@app.get("/api/v1/scheduling/calendar/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: str,
    page_token: Optional[str] = Query(None),
    page_size: int = Query(50, ge=10, le=200),
    state: Optional[List[str]] = Query(None),
    sort: str = Query("created_at", regex="^(created_at|updated_at)$"),
    order: str = Query("asc", regex="^(asc|desc)$"),
    expand: Optional[List[str]] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get schedule details"""
    with SchedulingService() as service:
        return service.get_schedule(
            schedule_id, 
            current_user["id"], 
            page_token, 
            page_size, 
            expand
        )

@app.post("/api/v1/scheduling/optimize", response_model=OptimizationResult)
async def optimize_schedule(
    request: OptimizationRequest,
    idempotency_key: Optional[str] = Header(None),
    current_user: dict = Depends(get_current_user)
):
    """Optimize schedule timing"""
    with SchedulingService() as service:
        return service.optimize_schedule(current_user["id"], request)

# WebSocket endpoint for real-time updates
@app.websocket("/api/v1/scheduling/ws")
async def websocket_endpoint(websocket: WebSocket, schedule_id: Optional[str] = None):
    """WebSocket endpoint for real-time scheduling updates"""
    await scheduling_manager.connect(websocket, schedule_id)
    
    try:
        while True:
            # Handle incoming messages for heartbeat and subscription management
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await scheduling_manager.send_to_connection(websocket, {
                        "type": "pong",
                        "data": {"timestamp": datetime.now(timezone.utc).isoformat()}
                    })
                elif message.get("type") == "subscribe" and message.get("schedule_id"):
                    # Handle dynamic subscription
                    new_schedule_id = message["schedule_id"]
                    await scheduling_manager.connect(websocket, new_schedule_id)
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        scheduling_manager.disconnect(websocket)

# Utility endpoints

@app.get("/api/v1/scheduling/health")
async def scheduling_health():
    """Health check for scheduling service"""
    return {
        "status": "healthy",
        "service": "scheduling_optimization",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/v1/scheduling/platforms")
async def get_supported_platforms():
    """Get list of supported platforms"""
    return {
        "data": [
            {"id": "youtube", "name": "YouTube", "supports": ["long_form", "shorts"]},
            {"id": "tiktok", "name": "TikTok", "supports": ["videos"]},
            {"id": "instagram", "name": "Instagram", "supports": ["posts", "reels", "stories"]},
            {"id": "linkedin", "name": "LinkedIn", "supports": ["posts", "articles"]},
            {"id": "twitter", "name": "X (Twitter)", "supports": ["tweets", "threads"]},
            {"id": "facebook", "name": "Facebook", "supports": ["posts", "videos"]}
        ]
    }