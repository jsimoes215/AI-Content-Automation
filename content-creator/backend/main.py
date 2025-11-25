"""
FastAPI Backend for AI Content Automation System
Provides REST API and WebSocket support for real-time updates
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import asyncio
from pathlib import Path
import sys

# Add parent directory to path to import from api/
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from backend.database.db import Database, init_database
from dataclasses import asdict

# Import scheduling API routes
from api.scheduling_api import app as scheduling_app

app = FastAPI(title="AI Content Automation API", version="1.0.0")

# Include scheduling API routes
app.include_router(scheduling_app, prefix="/api/v1", tags=["scheduling"])

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for generated content
GENERATED_CONTENT_DIR = Path(__file__).parent.parent / "data" / "generated-content"
GENERATED_CONTENT_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(GENERATED_CONTENT_DIR)), name="media")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Pydantic models
class ProjectCreate(BaseModel):
    original_idea: str
    target_audience: Optional[str] = None
    tone: Optional[str] = None
    metadata: Optional[Dict] = None


class ScriptGenerateRequest(BaseModel):
    project_id: str
    target_duration: Optional[int] = 300
    scene_count: Optional[int] = 5


class LibrarySearchRequest(BaseModel):
    tags: Optional[List[str]] = None
    duration_min: Optional[int] = None
    duration_max: Optional[int] = None
    limit: int = 20


class LibraryAddRequest(BaseModel):
    scene_id: str
    specific_tags: List[str] = []
    generic_tags: List[str] = []
    library_category: str = "experimental"


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_database()
    print("AI Content Automation API started successfully")


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "AI Content Automation API"}


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_json({"type": "pong", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Projects endpoints
@app.post("/api/projects")
async def create_project(project: ProjectCreate):
    """Create a new project."""
    db = Database()
    try:
        project_id = db.create_project(
            original_idea=project.original_idea,
            target_audience=project.target_audience,
            tone=project.tone,
            metadata=project.metadata
        )
        
        result = db.get_project(project_id)
        await manager.broadcast({
            "type": "project_created",
            "data": result
        })
        
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/projects")
async def list_projects(status: Optional[str] = None, limit: int = 50):
    """List all projects."""
    db = Database()
    try:
        projects = db.list_projects(status=status, limit=limit)
        return {"success": True, "data": projects, "count": len(projects)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get project by ID."""
    db = Database()
    try:
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get associated jobs
        jobs = db.list_project_jobs(project_id)
        project['jobs'] = jobs
        
        # Get analytics
        analytics = db.get_project_analytics(project_id)
        project['analytics'] = analytics
        
        return {"success": True, "data": project}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project."""
    db = Database()
    try:
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        cursor = db.conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        db.conn.commit()
        
        await manager.broadcast({
            "type": "project_deleted",
            "data": {"project_id": project_id}
        })
        
        return {"success": True, "message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# Script generation endpoints
async def generate_script_task(project_id: str, target_duration: int, scene_count: int):
    """Background task for script generation."""
    db = Database()
    try:
        # Create job
        job_id = db.create_job(project_id, 'script_generation', total_steps=3)
        
        await manager.broadcast({
            "type": "job_started",
            "data": {"job_id": job_id, "project_id": project_id, "job_type": "script_generation"}
        })
        
        # Import full pipeline
        from api.api.main_pipeline import PipelineFactory
        
        # Step 1: Initialize
        db.update_job_progress(job_id, 1)
        await manager.broadcast({
            "type": "job_progress",
            "data": {"job_id": job_id, "progress": 20, "step": "Initializing content creation pipeline"}
        })
        
        project = db.get_project(project_id)
        pipeline = PipelineFactory.get_pipeline()
        
        # Step 2: Create request
        db.update_job_progress(job_id, 2)
        await manager.broadcast({
            "type": "job_progress",
            "data": {"job_id": job_id, "progress": 40, "step": "Preparing content generation request"}
        })
        
        request = pipeline.create_request_from_idea(
            idea=project['original_idea'],
            target_audience=project.get('target_audience', 'general audience'),
            tone=project.get('tone', 'educational'),
            platforms=['youtube'],
            duration_preferences={'youtube': target_duration},
            add_to_library=True
        )
        
        # Step 3: Generate content
        db.update_job_progress(job_id, 3)
        await manager.broadcast({
            "type": "job_progress",
            "data": {"job_id": job_id, "progress": 60, "step": "Generating script, audio, and video"}
        })
        
        result = await pipeline.create_content(request)
        
        # Step 4: Save results to database
        db.update_job_progress(job_id, 4)
        await manager.broadcast({
            "type": "job_progress",
            "data": {"job_id": job_id, "progress": 80, "step": "Saving generated content"}
        })
        
        if result.status == "completed" and result.script:
            # Save script
            script_dict = {
                'title': result.script.title,
                'description': result.script.description,
                'scenes': [asdict(scene) for scene in result.script.scenes],
                'key_points': result.script.key_points,
                'hashtags': result.script.hashtags
            }
            
            script_id = db.create_script(
                project_id=project_id,
                content=script_dict,
                total_duration=result.script.total_duration,
                word_count=result.script.word_count
            )
            
            # Save scenes and generated content
            await save_generated_content_to_db(db, script_id, result)
            
            db.update_job_progress(job_id, 5)
            db.complete_job(job_id, result_data={
                "script_id": script_id,
                "processing_time": result.processing_time,
                "platforms": list(result.video_compositions.keys())
            })
            db.update_project_status(project_id, 'completed')
        else:
            raise Exception(result.error_message or "Content generation failed")
        
        await manager.broadcast({
            "type": "job_completed",
            "data": {
                "job_id": job_id,
                "project_id": project_id,
                "script_id": script_id,
                "progress": 100
            }
        })
        
    except Exception as e:
        db.complete_job(job_id, error_message=str(e))
        await manager.broadcast({
            "type": "job_failed",
            "data": {"job_id": job_id, "error": str(e)}
        })
    finally:
        db.close()


@app.post("/api/scripts/generate")
async def generate_script(request: ScriptGenerateRequest, background_tasks: BackgroundTasks):
    """Generate script from project idea."""
    db = Database()
    try:
        project = db.get_project(request.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update project status
        db.update_project_status(request.project_id, 'processing')
        
        # Start background task
        background_tasks.add_task(
            generate_script_task,
            request.project_id,
            request.target_duration,
            request.scene_count
        )
        
        return {
            "success": True,
            "message": "Script generation started",
            "project_id": request.project_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/scripts/{script_id}")
async def get_script(script_id: str):
    """Get script by ID."""
    db = Database()
    try:
        script = db.get_script(script_id)
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        return {"success": True, "data": script}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# Jobs endpoints
@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job status by ID."""
    db = Database()
    try:
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"success": True, "data": job}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/projects/{project_id}/jobs")
async def list_project_jobs(project_id: str):
    """List all jobs for a project."""
    db = Database()
    try:
        jobs = db.list_project_jobs(project_id)
        return {"success": True, "data": jobs, "count": len(jobs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# Content Library endpoints
@app.post("/api/library/search")
async def search_library(request: LibrarySearchRequest):
    """Search content library."""
    db = Database()
    try:
        results = db.search_library(tags=request.tags, limit=request.limit)
        return {"success": True, "data": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.post("/api/library/add")
async def add_to_library(request: LibraryAddRequest):
    """Add scene to content library."""
    db = Database()
    try:
        library_id = db.add_to_library(
            scene_id=request.scene_id,
            specific_tags=request.specific_tags,
            generic_tags=request.generic_tags,
            library_category=request.library_category
        )
        return {"success": True, "data": {"library_id": library_id}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# Analytics endpoints
@app.get("/api/analytics/overview")
async def get_analytics_overview():
    """Get overall analytics dashboard data."""
    db = Database()
    try:
        cursor = db.conn.cursor()
        
        # Total projects
        total_projects = cursor.execute("SELECT COUNT(*) as count FROM projects").fetchone()['count']
        
        # Projects by status
        status_counts = {}
        rows = cursor.execute(
            "SELECT status, COUNT(*) as count FROM projects GROUP BY status"
        ).fetchall()
        for row in rows:
            status_counts[row['status']] = row['count']
        
        # Recent activity
        recent_projects = cursor.execute(
            "SELECT id, original_idea, status, created_at FROM projects ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        
        return {
            "success": True,
            "data": {
                "total_projects": total_projects,
                "status_breakdown": status_counts,
                "recent_projects": [dict(row) for row in recent_projects]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/analytics/projects/{project_id}")
async def get_project_analytics(project_id: str):
    """Get analytics for specific project."""
    db = Database()
    try:
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        analytics = db.get_project_analytics(project_id)
        return {"success": True, "data": analytics}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# Helper function for saving generated content
async def save_generated_content_to_db(db: Database, script_id: str, result):
    """Save generated content (scenes, videos, audio) to database"""
    from api.main_pipeline import ContentCreationResult
    
    cursor = db.conn.cursor()
    
    # Save scenes
    for scene in result.script.scenes:
        scene_id = db.generate_id()
        cursor.execute(
            """INSERT INTO scenes (id, script_id, scene_number, duration, voiceover_text, 
               visual_description, scene_type)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (scene_id, script_id, scene.scene_number, scene.duration,
             scene.voiceover_text, scene.visual_description, scene.scene_type)
        )
        
        # Save generated content for this scene
        for platform, video_comp in result.video_compositions.items():
            content_id = db.generate_id()
            cursor.execute(
                """INSERT INTO generated_content (id, scene_id, content_type, file_path,
                   platform, resolution, format)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (content_id, scene_id, 'video', video_comp.output_file,
                 platform, video_comp.resolution, 'mp4')
            )
        
        # Save audio if available
        for platform, audio_mix in result.audio_mixes.items():
            content_id = db.generate_id()
            cursor.execute(
                """INSERT INTO generated_content (id, scene_id, content_type, file_path,
                   platform, duration, format)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (content_id, scene_id, 'audio', audio_mix.output_file,
                 platform, int(audio_mix.total_duration), 'mp3')
            )
    
    db.conn.commit()


# Preview endpoints
@app.get("/api/preview/script/{script_id}")
async def preview_script(script_id: str):
    """Get script content for preview"""
    db = Database()
    try:
        script = db.get_script(script_id)
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        
        return {"success": True, "data": script}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/preview/content/{content_id}")
async def preview_content(content_id: str):
    """Get generated content details for preview"""
    db = Database()
    try:
        cursor = db.conn.cursor()
        row = cursor.execute(
            "SELECT * FROM generated_content WHERE id = ?",
            (content_id,)
        ).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Content not found")
        
        from database.db import dict_from_row
        content = dict_from_row(row)
        
        # Add media URL
        if content.get('file_path'):
            content['media_url'] = f"/media/{Path(content['file_path']).name}"
        
        return {"success": True, "data": content}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/scripts/{script_id}/scenes")
async def get_script_scenes(script_id: str):
    """Get all scenes for a script with generated content"""
    db = Database()
    try:
        cursor = db.conn.cursor()
        
        # Get all scenes for this script
        scene_rows = cursor.execute(
            """SELECT s.*, 
                      (SELECT COUNT(*) FROM generated_content WHERE scene_id = s.id) as content_count
               FROM scenes s
               WHERE s.script_id = ?
               ORDER BY s.scene_number""",
            (script_id,)
        ).fetchall()
        
        scenes = []
        for row in scene_rows:
            from database.db import dict_from_row, parse_json_field
            scene = dict_from_row(row)
            scene['platform_specific'] = parse_json_field(scene.get('platform_specific'))
            
            # Get generated content for this scene
            content_rows = cursor.execute(
                "SELECT * FROM generated_content WHERE scene_id = ?",
                (scene['id'],)
            ).fetchall()
            
            scene['generated_content'] = []
            for content_row in content_rows:
                content = dict_from_row(content_row)
                content['generation_metadata'] = parse_json_field(content.get('generation_metadata'))
                if content.get('file_path'):
                    content['media_url'] = f"/media/{Path(content['file_path']).name}"
                scene['generated_content'].append(content)
            
            scenes.append(scene)
        
        return {"success": True, "data": scenes, "count": len(scenes)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# Download and export endpoints
@app.get("/api/download/content/{content_id}")
async def download_content(content_id: str):
    """Download generated content file"""
    from fastapi.responses import FileResponse
    
    db = Database()
    try:
        cursor = db.conn.cursor()
        row = cursor.execute(
            "SELECT file_path, content_type, format FROM generated_content WHERE id = ?",
            (content_id,)
        ).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Content not found")
        
        file_path = row['file_path']
        
        if not file_path or not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=file_path,
            filename=Path(file_path).name,
            media_type=f"{row['content_type']}/{row['format']}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


class ExportRequest(BaseModel):
    project_id: str
    content_types: List[str]  # ['video', 'audio', 'script', 'thumbnail']
    platforms: Optional[List[str]] = None
    format: str = "zip"


@app.post("/api/export/project")
async def export_project(request: ExportRequest, background_tasks: BackgroundTasks):
    """Export all project content as a zip file"""
    import zipfile
    import tempfile
    from datetime import datetime
    
    db = Database()
    try:
        project = db.get_project(request.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Create temporary zip file
        temp_dir = Path(tempfile.mkdtemp())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"project_{request.project_id[:8]}_{timestamp}.zip"
        zip_path = temp_dir / zip_filename
        
        cursor = db.conn.cursor()
        
        # Get all content for the project
        content_rows = cursor.execute(
            """SELECT gc.* FROM generated_content gc
               JOIN scenes s ON gc.scene_id = s.id
               JOIN scripts sc ON s.script_id = sc.id
               WHERE sc.project_id = ? AND gc.content_type IN ({})
               {}""".format(
                   ','.join('?' * len(request.content_types)),
                   'AND gc.platform IN ({})'.format(','.join('?' * len(request.platforms))) if request.platforms else ''
               ),
            (request.project_id, *request.content_types, *(request.platforms or []))
        ).fetchall()
        
        # Create zip file
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add project info
            project_info = {
                'project_id': project['id'],
                'idea': project['original_idea'],
                'created_at': project['created_at'],
                'export_date': datetime.now().isoformat()
            }
            zipf.writestr('project_info.json', json.dumps(project_info, indent=2))
            
            # Add content files
            for row in content_rows:
                from database.db import dict_from_row
                content = dict_from_row(row)
                file_path = content.get('file_path')
                
                if file_path and Path(file_path).exists():
                    arcname = f"{content['content_type']}s/{Path(file_path).name}"
                    zipf.write(file_path, arcname)
        
        # Return zip file
        from fastapi.responses import FileResponse
        return FileResponse(
            path=str(zip_path),
            filename=zip_filename,
            media_type="application/zip"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# Real analytics endpoints (replace mock data)
@app.get("/api/analytics/realtime")
async def get_realtime_analytics():
    """Get real-time analytics from database"""
    db = Database()
    try:
        cursor = db.conn.cursor()
        
        # Get total content generated
        total_content = cursor.execute(
            "SELECT COUNT(*) as count FROM generated_content"
        ).fetchone()['count']
        
        # Get content by type
        content_by_type = {}
        type_rows = cursor.execute(
            "SELECT content_type, COUNT(*) as count FROM generated_content GROUP BY content_type"
        ).fetchall()
        for row in type_rows:
            content_by_type[row['content_type']] = row['count']
        
        # Get content by platform
        content_by_platform = {}
        platform_rows = cursor.execute(
            "SELECT platform, COUNT(*) as count FROM generated_content GROUP BY platform"
        ).fetchall()
        for row in platform_rows:
            content_by_platform[row['platform']] = row['count']
        
        # Get performance metrics summary
        perf_summary = cursor.execute(
            """SELECT 
                SUM(views) as total_views,
                SUM(likes) as total_likes,
                SUM(comments_count) as total_comments,
                SUM(shares) as total_shares,
                AVG(engagement_rate) as avg_engagement
               FROM performance_metrics"""
        ).fetchone()
        
        return {
            "success": True,
            "data": {
                "total_content": total_content,
                "content_by_type": content_by_type,
                "content_by_platform": content_by_platform,
                "performance_summary": dict(perf_summary) if perf_summary else {
                    "total_views": 0,
                    "total_likes": 0,
                    "total_comments": 0,
                    "total_shares": 0,
                    "avg_engagement": 0
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.post("/api/analytics/performance")
async def record_performance(data: Dict[str, Any]):
    """Record performance metrics for content"""
    db = Database()
    try:
        cursor = db.conn.cursor()
        metric_id = db.generate_id()
        
        cursor.execute(
            """INSERT INTO performance_metrics 
               (id, content_id, platform, views, likes, comments_count, shares,
                engagement_rate, performance_score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (metric_id, data.get('content_id'), data.get('platform'),
             data.get('views', 0), data.get('likes', 0), data.get('comments_count', 0),
             data.get('shares', 0), data.get('engagement_rate', 0),
             data.get('performance_score', 0))
        )
        db.conn.commit()
        
        return {"success": True, "message": "Performance recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

