"""SQLite database connection and utilities."""
import sqlite3
import json
import os
from pathlib import Path
from typing import Optional, Dict, List, Any
from contextlib import contextmanager
import uuid
from datetime import datetime

DATABASE_PATH = Path(__file__).parent.parent.parent / "data" / "content_creator.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize the database with schema."""
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path) as f:
        schema_sql = f.read()
    
    with get_db() as conn:
        conn.executescript(schema_sql)
    
    print("Database initialized successfully")


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def dict_from_row(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert SQLite Row to dictionary."""
    if row is None:
        return None
    return dict(row)


def parse_json_field(value: Optional[str], default=None) -> Any:
    """Parse JSON field from TEXT storage."""
    if value is None:
        return default if default is not None else {}
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else {}


def serialize_json_field(value: Any) -> str:
    """Serialize Python object to JSON TEXT."""
    if value is None:
        return "{}"
    return json.dumps(value)


class Database:
    """Database operations wrapper."""
    
    def __init__(self):
        self.conn = get_connection()
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    # Projects
    def create_project(self, original_idea: str, target_audience: str = None, 
                      tone: str = None, metadata: Dict = None) -> str:
        """Create a new project."""
        project_id = generate_id()
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO projects (id, original_idea, target_audience, tone, metadata, status)
               VALUES (?, ?, ?, ?, ?, 'draft')""",
            (project_id, original_idea, target_audience, tone, serialize_json_field(metadata))
        )
        self.conn.commit()
        return project_id
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project by ID."""
        cursor = self.conn.cursor()
        row = cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if row:
            project = dict_from_row(row)
            project['metadata'] = parse_json_field(project.get('metadata'))
            return project
        return None
    
    def list_projects(self, status: str = None, limit: int = 50) -> List[Dict]:
        """List projects with optional status filter."""
        cursor = self.conn.cursor()
        if status:
            rows = cursor.execute(
                "SELECT * FROM projects WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit)
            ).fetchall()
        else:
            rows = cursor.execute(
                "SELECT * FROM projects ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
        
        projects = []
        for row in rows:
            project = dict_from_row(row)
            project['metadata'] = parse_json_field(project.get('metadata'))
            projects.append(project)
        return projects
    
    def update_project_status(self, project_id: str, status: str) -> None:
        """Update project status."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE projects SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, project_id)
        )
        self.conn.commit()
    
    # Generation Jobs
    def create_job(self, project_id: str, job_type: str, total_steps: int = 0) -> str:
        """Create a new generation job."""
        job_id = generate_id()
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO generation_jobs (id, project_id, job_type, status, total_steps)
               VALUES (?, ?, ?, 'pending', ?)""",
            (job_id, project_id, job_type, total_steps)
        )
        self.conn.commit()
        return job_id
    
    def update_job_progress(self, job_id: str, current_step: int, 
                           status: str = 'processing') -> None:
        """Update job progress."""
        cursor = self.conn.cursor()
        cursor.execute(
            """UPDATE generation_jobs 
               SET current_step = ?, status = ?, 
                   progress = CAST((current_step * 100.0 / NULLIF(total_steps, 0)) AS INTEGER)
               WHERE id = ?""",
            (current_step, status, job_id)
        )
        self.conn.commit()
    
    def complete_job(self, job_id: str, result_data: Dict = None, 
                    error_message: str = None) -> None:
        """Mark job as completed or failed."""
        status = 'failed' if error_message else 'completed'
        cursor = self.conn.cursor()
        cursor.execute(
            """UPDATE generation_jobs 
               SET status = ?, result_data = ?, error_message = ?, 
                   completed_at = CURRENT_TIMESTAMP, progress = ?
               WHERE id = ?""",
            (status, serialize_json_field(result_data), error_message, 
             100 if status == 'completed' else 0, job_id)
        )
        self.conn.commit()
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job by ID."""
        cursor = self.conn.cursor()
        row = cursor.execute("SELECT * FROM generation_jobs WHERE id = ?", (job_id,)).fetchone()
        if row:
            job = dict_from_row(row)
            job['result_data'] = parse_json_field(job.get('result_data'))
            return job
        return None
    
    def list_project_jobs(self, project_id: str) -> List[Dict]:
        """List all jobs for a project."""
        cursor = self.conn.cursor()
        rows = cursor.execute(
            "SELECT * FROM generation_jobs WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,)
        ).fetchall()
        
        jobs = []
        for row in rows:
            job = dict_from_row(row)
            job['result_data'] = parse_json_field(job.get('result_data'))
            jobs.append(job)
        return jobs
    
    # Scripts
    def create_script(self, project_id: str, content: Dict, 
                     total_duration: int = 0, word_count: int = 0,
                     script_type: str = 'explainer') -> str:
        """Create a new script."""
        script_id = generate_id()
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO scripts (id, project_id, content, total_duration, word_count, script_type)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (script_id, project_id, serialize_json_field(content), 
             total_duration, word_count, script_type)
        )
        self.conn.commit()
        return script_id
    
    def get_script(self, script_id: str) -> Optional[Dict]:
        """Get script by ID."""
        cursor = self.conn.cursor()
        row = cursor.execute("SELECT * FROM scripts WHERE id = ?", (script_id,)).fetchone()
        if row:
            script = dict_from_row(row)
            script['content'] = parse_json_field(script.get('content'))
            return script
        return None
    
    # Content Library
    def add_to_library(self, scene_id: str, specific_tags: List[str] = None,
                      generic_tags: List[str] = None, 
                      library_category: str = 'experimental') -> str:
        """Add scene to content library."""
        library_id = generate_id()
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO content_library (id, scene_id, specific_tags, generic_tags, library_category)
               VALUES (?, ?, ?, ?, ?)""",
            (library_id, scene_id, 
             serialize_json_field(specific_tags or []),
             serialize_json_field(generic_tags or []),
             library_category)
        )
        self.conn.commit()
        return library_id
    
    def search_library(self, tags: List[str] = None, limit: int = 20) -> List[Dict]:
        """Search content library by tags."""
        cursor = self.conn.cursor()
        
        if tags:
            # Simple search - check if any tag is in the JSON arrays
            rows = cursor.execute(
                """SELECT cl.*, s.voiceover_text, s.visual_description, s.duration
                   FROM content_library cl
                   JOIN scenes s ON cl.scene_id = s.id
                   ORDER BY cl.performance_score DESC, cl.usage_count DESC
                   LIMIT ?""",
                (limit,)
            ).fetchall()
            
            # Filter by tags in Python (SQLite JSON functions are limited)
            filtered = []
            for row in rows:
                item = dict_from_row(row)
                item['specific_tags'] = parse_json_field(item.get('specific_tags'), [])
                item['generic_tags'] = parse_json_field(item.get('generic_tags'), [])
                
                all_tags = item['specific_tags'] + item['generic_tags']
                if any(tag in all_tags for tag in tags):
                    filtered.append(item)
            
            return filtered[:limit]
        else:
            rows = cursor.execute(
                """SELECT cl.*, s.voiceover_text, s.visual_description, s.duration
                   FROM content_library cl
                   JOIN scenes s ON cl.scene_id = s.id
                   ORDER BY cl.performance_score DESC
                   LIMIT ?""",
                (limit,)
            ).fetchall()
            
            library_items = []
            for row in rows:
                item = dict_from_row(row)
                item['specific_tags'] = parse_json_field(item.get('specific_tags'), [])
                item['generic_tags'] = parse_json_field(item.get('generic_tags'), [])
                library_items.append(item)
            return library_items
    
    # Analytics
    def get_project_analytics(self, project_id: str) -> Dict:
        """Get analytics for a project."""
        cursor = self.conn.cursor()
        
        # Get total metrics
        row = cursor.execute(
            """SELECT 
                SUM(views) as total_views,
                SUM(likes) as total_likes,
                SUM(comments_count) as total_comments,
                AVG(engagement_rate) as avg_engagement
               FROM performance_metrics pm
               JOIN generated_content gc ON pm.content_id = gc.id
               JOIN scenes s ON gc.scene_id = s.id
               JOIN scripts sc ON s.script_id = sc.id
               WHERE sc.project_id = ?""",
            (project_id,)
        ).fetchone()
        
        if row:
            return dict_from_row(row)
        return {
            'total_views': 0,
            'total_likes': 0,
            'total_comments': 0,
            'avg_engagement': 0
        }
