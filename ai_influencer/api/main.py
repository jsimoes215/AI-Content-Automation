"""
AI Influencer Management API
FastAPI backend for influencer and niche management

Author: MiniMax Agent
Date: 2025-11-07
"""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import uvicorn

# Create the API directory
Path("/workspace/ai_influencer_poc/api").mkdir(parents=True, exist_ok=True)

# Pydantic schemas
class InfluencerBase(BaseModel):
    name: str
    bio: Optional[str] = None
    voice_type: str = "professional_male"
    personality_traits: List[str] = []
    target_audience: Dict[str, Any] = {}
    branding_guidelines: Dict[str, Any] = {}

class InfluencerCreate(InfluencerBase):
    niche_ids: List[int] = []

class Influencer(InfluencerBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    niches: List[Dict[str, Any]] = []
    
    class Config:
        from_attributes = True

class NicheBase(BaseModel):
    name: str
    description: Optional[str] = None
    target_keywords: List[str] = []
    content_templates: Dict[str, Any] = {}
    tone_guidelines: Dict[str, Any] = {}
    performance_benchmarks: Dict[str, Any] = {}

class NicheCreate(NicheBase):
    pass

class Niche(NicheBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class SocialAccountBase(BaseModel):
    platform: str
    account_handle: Optional[str] = None
    platform_user_id: Optional[str] = None
    follower_count: int = 0

class SocialAccountCreate(SocialAccountBase):
    pass

class SocialAccount(SocialAccountBase):
    id: int
    influencer_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Database dependency
def get_db():
    """Database connection dependency - creates new connection for each request"""
    db_path = "/workspace/ai_influencer_poc/database/influencers.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Simplified CRUD functions that create their own database connections
def get_db_connection():
    """Get a new database connection for CRUD operations"""
    db_path = "/workspace/ai_influencer_poc/database/influencers.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# CRUD operations
class InfluencerCRUD:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
    
    def create(self, influencer_data: InfluencerCreate) -> Dict[str, Any]:
        """Create a new influencer"""
        # Insert influencer
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO influencers 
            (name, bio, voice_type, personality_traits, target_audience, branding_guidelines)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            influencer_data.name,
            influencer_data.bio,
            influencer_data.voice_type,
            json.dumps(influencer_data.personality_traits),
            json.dumps(influencer_data.target_audience),
            json.dumps(influencer_data.branding_guidelines)
        ))
        
        influencer_id = cursor.lastrowid
        
        # Link to niches
        for niche_id in influencer_data.niche_ids:
            cursor.execute("""
                INSERT OR IGNORE INTO influencer_niches 
                (influencer_id, niche_id, expertise_level, content_style)
                VALUES (?, ?, ?, ?)
            """, (influencer_id, niche_id, 5, json.dumps({})))
        
        self.db.commit()
        return self.get_by_id(influencer_id)
    
    def get_by_id(self, influencer_id: int) -> Optional[Dict[str, Any]]:
        """Get influencer by ID with niches"""
        cursor = self.db.cursor()
        
        # Get influencer data
        cursor.execute("SELECT * FROM influencers WHERE id = ?", (influencer_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        influencer = dict(row)
        
        # Parse JSON fields
        influencer['personality_traits'] = json.loads(influencer['personality_traits'] or '[]')
        influencer['target_audience'] = json.loads(influencer['target_audience'] or '{}')
        influencer['branding_guidelines'] = json.loads(influencer['branding_guidelines'] or '{}')
        
        # Get associated niches
        cursor.execute("""
            SELECT n.*, inf_n.expertise_level, inf_n.content_style
            FROM influencer_niches inf_n
            JOIN niches n ON inf_n.niche_id = n.id
            WHERE inf_n.influencer_id = ?
        """, (influencer_id,))
        
        niches = []
        for niche_row in cursor.fetchall():
            niche = dict(niche_row)
            niche['content_templates'] = json.loads(niche['content_templates'] or '{}')
            niche['tone_guidelines'] = json.loads(niche['tone_guidelines'] or '{}')
            niche['performance_benchmarks'] = json.loads(niche['performance_benchmarks'] or '{}')
            niche['content_style'] = json.loads(niche['content_style'] or '{}')
            niches.append(niche)
        
        influencer['niches'] = niches
        
        return influencer
    
    def get_all(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all influencers"""
        cursor = self.db.cursor()
        
        if active_only:
            cursor.execute("SELECT * FROM influencers WHERE is_active = 1 ORDER BY created_at DESC")
        else:
            cursor.execute("SELECT * FROM influencers ORDER BY created_at DESC")
        
        influencers = []
        for row in cursor.fetchall():
            influencer = dict(row)
            influencer['personality_traits'] = json.loads(influencer['personality_traits'] or '[]')
            influencer['target_audience'] = json.loads(influencer['target_audience'] or '{}')
            influencer['branding_guidelines'] = json.loads(influencer['branding_guidelines'] or '{}')
            
            # Get niches count for each influencer
            cursor.execute(
                "SELECT COUNT(*) as niche_count FROM influencer_niches WHERE influencer_id = ?",
                (influencer['id'],)
            )
            niche_count = cursor.fetchone()['niche_count']
            influencer['niche_count'] = niche_count
            
            influencers.append(influencer)
        
        return influencers
    
    def update(self, influencer_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update influencer"""
        # Build dynamic update query
        fields = []
        values = []
        
        for field, value in update_data.items():
            if field in ['name', 'bio', 'voice_type']:
                fields.append(f"{field} = ?")
                values.append(value)
            elif field == 'personality_traits':
                fields.append("personality_traits = ?")
                values.append(json.dumps(value))
            elif field in ['target_audience', 'branding_guidelines']:
                fields.append(f"{field} = ?")
                values.append(json.dumps(value))
        
        if not fields:
            return self.get_by_id(influencer_id)
        
        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(influencer_id)
        
        cursor = self.db.cursor()
        query = f"UPDATE influencers SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(query, values)
        
        if cursor.rowcount == 0:
            return None
        
        self.db.commit()
        return self.get_by_id(influencer_id)
    
    def delete(self, influencer_id: int) -> bool:
        """Delete influencer (soft delete)"""
        cursor = self.db.cursor()
        cursor.execute("UPDATE influencers SET is_active = 0 WHERE id = ?", (influencer_id,))
        self.db.commit()
        return cursor.rowcount > 0

class NicheCRUD:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
    
    def create(self, niche_data: NicheCreate) -> Dict[str, Any]:
        """Create a new niche"""
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO niches 
            (name, description, target_keywords, content_templates, tone_guidelines, performance_benchmarks)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            niche_data.name,
            niche_data.description,
            json.dumps(niche_data.target_keywords),
            json.dumps(niche_data.content_templates),
            json.dumps(niche_data.tone_guidelines),
            json.dumps(niche_data.performance_benchmarks)
        ))
        
        niche_id = cursor.lastrowid
        self.db.commit()
        return self.get_by_id(niche_id)
    
    def get_by_id(self, niche_id: int) -> Optional[Dict[str, Any]]:
        """Get niche by ID"""
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM niches WHERE id = ?", (niche_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        niche = dict(row)
        niche['target_keywords'] = json.loads(niche['target_keywords'] or '[]')
        niche['content_templates'] = json.loads(niche['content_templates'] or '{}')
        niche['tone_guidelines'] = json.loads(niche['tone_guidelines'] or '{}')
        niche['performance_benchmarks'] = json.loads(niche['performance_benchmarks'] or '{}')
        
        return niche
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all niches"""
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM niches ORDER BY name")
        
        niches = []
        for row in cursor.fetchall():
            niche = dict(row)
            niche['target_keywords'] = json.loads(niche['target_keywords'] or '[]')
            niche['content_templates'] = json.loads(niche['content_templates'] or '{}')
            niche['tone_guidelines'] = json.loads(niche['tone_guidelines'] or '{}')
            niche['performance_benchmarks'] = json.loads(niche['performance_benchmarks'] or '{}')
            niches.append(niche)
        
        return niches
    
    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get niche by name"""
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM niches WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self.get_by_id(row['id'])

# FastAPI application
app = FastAPI(
    title="AI Influencer Management API",
    description="API for managing AI influencers across multiple niches",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI Influencer Management API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Influencer endpoints
@app.get("/api/v1/influencers", response_model=List[Influencer])
async def get_influencers(
    active_only: bool = Query(True, description="Only return active influencers")
):
    """Get all influencers"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute("SELECT * FROM influencers WHERE is_active = 1 ORDER BY created_at DESC")
        else:
            cursor.execute("SELECT * FROM influencers ORDER BY created_at DESC")
        
        influencers = []
        for row in cursor.fetchall():
            influencer = dict(row)
            influencer['personality_traits'] = json.loads(influencer['personality_traits'] or '[]')
            influencer['target_audience'] = json.loads(influencer['target_audience'] or '{}')
            influencer['branding_guidelines'] = json.loads(influencer['branding_guidelines'] or '{}')
            
            # Get niches count for each influencer
            cursor.execute(
                "SELECT COUNT(*) as niche_count FROM influencer_niches WHERE influencer_id = ?",
                (influencer['id'],)
            )
            niche_count = cursor.fetchone()['niche_count']
            influencer['niche_count'] = niche_count
            influencer['niches'] = []  # Simplified for now
            
            influencers.append(influencer)
        
        return influencers

@app.get("/api/v1/influencers/{influencer_id}", response_model=Influencer)
async def get_influencer(influencer_id: int):
    """Get specific influencer by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get influencer data
        cursor.execute("SELECT * FROM influencers WHERE id = ?", (influencer_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Influencer not found")
        
        influencer = dict(row)
        
        # Parse JSON fields
        influencer['personality_traits'] = json.loads(influencer['personality_traits'] or '[]')
        influencer['target_audience'] = json.loads(influencer['target_audience'] or '{}')
        influencer['branding_guidelines'] = json.loads(influencer['branding_guidelines'] or '{}')
        
        # Get associated niches (simplified)
        influencer['niches'] = []
        
        return influencer

@app.post("/api/v1/influencers", response_model=Influencer)
async def create_influencer(
    influencer: InfluencerCreate,
    db: sqlite3.Connection = Depends(get_db)
):
    """Create a new influencer"""
    crud = InfluencerCRUD(db)
    return crud.create(influencer)

@app.put("/api/v1/influencers/{influencer_id}", response_model=Influencer)
async def update_influencer(
    influencer_id: int,
    update_data: Dict[str, Any],
    db: sqlite3.Connection = Depends(get_db)
):
    """Update influencer"""
    crud = InfluencerCRUD(db)
    updated = crud.update(influencer_id, update_data)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Influencer not found")
    
    return updated

@app.delete("/api/v1/influencers/{influencer_id}")
async def delete_influencer(
    influencer_id: int,
    db: sqlite3.Connection = Depends(get_db)
):
    """Delete influencer (soft delete)"""
    crud = InfluencerCRUD(db)
    success = crud.delete(influencer_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Influencer not found")
    
    return {"message": "Influencer deleted successfully"}

# Niche endpoints
@app.get("/api/v1/niches", response_model=List[Niche])
async def get_niches(db: sqlite3.Connection = Depends(get_db)):
    """Get all niches"""
    crud = NicheCRUD(db)
    return crud.get_all()

@app.get("/api/v1/niches/{niche_id}", response_model=Niche)
async def get_niche(
    niche_id: int,
    db: sqlite3.Connection = Depends(get_db)
):
    """Get specific niche by ID"""
    crud = NicheCRUD(db)
    niche = crud.get_by_id(niche_id)
    
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    
    return niche

@app.get("/api/v1/niches/by-name/{name}", response_model=Niche)
async def get_niche_by_name(
    name: str,
    db: sqlite3.Connection = Depends(get_db)
):
    """Get niche by name"""
    crud = NicheCRUD(db)
    niche = crud.get_by_name(name)
    
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    
    return niche

@app.post("/api/v1/niches", response_model=Niche)
async def create_niche(
    niche: NicheCreate,
    db: sqlite3.Connection = Depends(get_db)
):
    """Create a new niche"""
    crud = NicheCRUD(db)
    return crud.create(niche)

# Analytics endpoint
@app.get("/api/v1/analytics/summary")
async def get_analytics_summary(db: sqlite3.Connection = Depends(get_db)):
    """Get analytics summary"""
    cursor = db.cursor()
    
    # Count influencers
    cursor.execute("SELECT COUNT(*) as count FROM influencers WHERE is_active = 1")
    active_influencers = cursor.fetchone()['count']
    
    # Count niches
    cursor.execute("SELECT COUNT(*) as count FROM niches")
    total_niches = cursor.fetchone()['count']
    
    # Count influencer-niche relationships
    cursor.execute("SELECT COUNT(*) as count FROM influencer_niches")
    total_relationships = cursor.fetchone()['count']
    
    # Get influencer distribution by niche
    cursor.execute("""
        SELECT n.name, COUNT(inf_n.influencer_id) as influencer_count
        FROM niches n
        LEFT JOIN influencer_niches inf_n ON n.id = inf_n.niche_id
        GROUP BY n.id, n.name
        ORDER BY influencer_count DESC
    """)
    niche_distribution = [dict(row) for row in cursor.fetchall()]
    
    return {
        "active_influencers": active_influencers,
        "total_niches": total_niches,
        "total_relationships": total_relationships,
        "niche_distribution": niche_distribution,
        "generated_at": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
