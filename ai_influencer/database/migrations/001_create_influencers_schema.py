"""
AI Influencer Integration - Database Schema
Extends existing database with influencer management capabilities

Author: MiniMax Agent
Date: 2025-11-07
"""

import sqlite3
from pathlib import Path
from typing import Optional
import json

# Create the database directory
Path("/workspace/ai_influencer_poc/database").mkdir(parents=True, exist_ok=True)

def create_influencer_tables():
    """Create all influencer-related database tables"""
    
    # Database connection
    db_path = "/workspace/ai_influencer_poc/database/influencers.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Create influencers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS influencers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            bio TEXT,
            avatar_path VARCHAR(255),
            voice_type VARCHAR(50) DEFAULT 'professional_male',
            personality_traits TEXT, -- JSON array
            target_audience TEXT, -- JSON object
            branding_guidelines TEXT, -- JSON object
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create niches table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS niches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) UNIQUE NOT NULL,
            description TEXT,
            target_keywords TEXT, -- JSON array
            content_templates TEXT, -- JSON object
            tone_guidelines TEXT, -- JSON object
            performance_benchmarks TEXT, -- JSON object
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create influencer_niches junction table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS influencer_niches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            influencer_id INTEGER NOT NULL,
            niche_id INTEGER NOT NULL,
            expertise_level INTEGER DEFAULT 5, -- 1-10 scale
            content_style TEXT, -- JSON object
            performance_metrics TEXT, -- JSON object
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (influencer_id) REFERENCES influencers(id) ON DELETE CASCADE,
            FOREIGN KEY (niche_id) REFERENCES niches(id) ON DELETE CASCADE,
            UNIQUE(influencer_id, niche_id)
        )
    """)
    
    # Create social accounts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS social_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            influencer_id INTEGER NOT NULL,
            platform VARCHAR(50) NOT NULL, -- 'youtube', 'tiktok', 'instagram', etc.
            account_handle VARCHAR(100),
            platform_user_id VARCHAR(100),
            auth_tokens TEXT, -- JSON object (encrypted)
            follower_count INTEGER DEFAULT 0,
            last_sync TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (influencer_id) REFERENCES influencers(id) ON DELETE CASCADE,
            UNIQUE(influencer_id, platform)
        )
    """)
    
    # Create influencer content history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS influencer_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            influencer_id INTEGER NOT NULL,
            project_id INTEGER, -- Link to existing projects table
            content_type VARCHAR(50), -- 'script', 'video', 'post'
            platform VARCHAR(50),
            content_data TEXT, -- JSON object with content details
            performance_score DECIMAL(5,2) DEFAULT 0.0,
            engagement_metrics TEXT, -- JSON object
            persona_consistency_score DECIMAL(5,2) DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (influencer_id) REFERENCES influencers(id) ON DELETE CASCADE
        )
    """)
    
    # Create niche templates table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS niche_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            niche_id INTEGER NOT NULL,
            template_name VARCHAR(100) NOT NULL,
            content_structure TEXT, -- JSON object
            tone_guidelines TEXT, -- JSON object
            content_length_guidelines TEXT, -- JSON object
            visual_style TEXT, -- JSON object
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (niche_id) REFERENCES niches(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_influencers_active ON influencers(is_active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_influencer_niches_influencer ON influencer_niches(influencer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_influencer_niches_niche ON influencer_niches(niche_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_social_accounts_influencer ON social_accounts(influencer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_social_accounts_platform ON social_accounts(platform)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_influencer_content_influencer ON influencer_content(influencer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_influencer_content_created ON influencer_content(created_at)")
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print("✅ Database schema created successfully!")
    return db_path

def insert_default_data(db_path: str):
    """Insert default niches and sample influencers"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Insert default niches
    default_niches = [
        {
            "name": "personal_finance",
            "description": "Financial advice, investing, budgeting, wealth building",
            "target_keywords": json.dumps(["money", "investing", "saving", "budget", "finance", "wealth", "economic", "financial freedom"]),
            "content_templates": json.dumps({
                "hook": "Financial pain point or goal",
                "education": "Evidence-based information",
                "solution": "Step-by-step financial strategy",
                "example": "Real case study or calculation",
                "action": "Next steps or recommended tools"
            }),
            "tone_guidelines": json.dumps({
                "energy_level": "medium",
                "authority_level": "expert",
                "approachability": "trustworthy",
                "motivation_style": "security_focused"
            }),
            "performance_benchmarks": json.dumps({
                "engagement_rate": 3.5,
                "conversion_rate": 2.1,
                "revenue_per_view": 0.005
            })
        },
        {
            "name": "technology",
            "description": "AI, software, innovation, digital trends",
            "target_keywords": json.dumps(["technology", "AI", "innovation", "software", "digital", "future", "tech", "automation"]),
            "content_templates": json.dumps({
                "hook": "Current tech trend or problem",
                "context": "Why this technology matters",
                "explanation": "How it works simply",
                "implications": "Future impact",
                "insights": "How to use or prepare"
            }),
            "tone_guidelines": json.dumps({
                "energy_level": "medium-high",
                "authority_level": "knowledgeable",
                "approachability": "educational",
                "motivation_style": "innovation_focused"
            }),
            "performance_benchmarks": json.dumps({
                "engagement_rate": 4.2,
                "conversion_rate": 1.8,
                "revenue_per_view": 0.004
            })
        },
        {
            "name": "fitness_health",
            "description": "Workouts, nutrition, wellness, healthy lifestyle",
            "target_keywords": json.dumps(["fitness", "health", "workout", "exercise", "nutrition", "wellness", "healthy", "strength"]),
            "content_templates": json.dumps({
                "hook": "Problem identification with relatable scenario",
                "education": "Evidence-based information delivery",
                "demonstration": "Visual proof or example",
                "action_steps": "Clear, implementable advice",
                "motivation": "Encouraging conclusion"
            }),
            "tone_guidelines": json.dumps({
                "energy_level": "high",
                "authority_level": "confident",
                "approachability": "supportive",
                "motivation_style": "achievement_focused"
            }),
            "performance_benchmarks": json.dumps({
                "engagement_rate": 5.1,
                "conversion_rate": 3.2,
                "revenue_per_view": 0.003
            })
        },
        {
            "name": "career_development",
            "description": "Professional growth, skills, networking, job search",
            "target_keywords": json.dumps(["career", "job", "professional", "skills", "networking", "success", "work", "leadership"]),
            "content_templates": json.dumps({
                "hook": "Career challenge or opportunity",
                "reality": "Why this is important now",
                "strategy": "Practical steps",
                "story": "Real example or case study",
                "implementation": "How to get started"
            }),
            "tone_guidelines": json.dumps({
                "energy_level": "medium",
                "authority_level": "mentor-like",
                "approachability": "encouraging",
                "motivation_style": "growth_focused"
            }),
            "performance_benchmarks": json.dumps({
                "engagement_rate": 3.8,
                "conversion_rate": 2.5,
                "revenue_per_view": 0.004
            })
        }
    ]
    
    for niche in default_niches:
        cursor.execute("""
            INSERT OR IGNORE INTO niches 
            (name, description, target_keywords, content_templates, tone_guidelines, performance_benchmarks)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            niche["name"], niche["description"], niche["target_keywords"],
            niche["content_templates"], niche["tone_guidelines"], niche["performance_benchmarks"]
        ))
    
    # Insert sample influencers
    sample_influencers = [
        {
            "name": "Alex Finance Guru",
            "bio": "Former investment banker teaching practical money management and wealth building strategies for everyday people.",
            "voice_type": "professional_male",
            "personality_traits": json.dumps(["knowledgeable", "trustworthy", "patient", "data-driven"]),
            "target_audience": json.dumps({
                "age_range": "25-45",
                "income_level": "middle_class",
                "interests": ["personal finance", "investing", "financial independence"],
                "demographics": "professionals seeking financial education"
            }),
            "branding_guidelines": json.dumps({
                "visual_style": "professional_clean",
                "color_scheme": ["navy", "gold", "white"],
                "tone": "authoritative but approachable",
                "key_messages": ["practical advice", "proven strategies", "financial education"]
            })
        },
        {
            "name": "Sarah Tech Vision",
            "bio": "AI researcher and technology consultant helping businesses and individuals understand and leverage emerging technologies.",
            "voice_type": "professional_female",
            "personality_traits": json.dumps(["innovative", "analytical", "forward-thinking", "explainer"]),
            "target_audience": json.dumps({
                "age_range": "22-40",
                "income_level": "middle_to_upper",
                "interests": ["technology", "innovation", "AI", "digital transformation"],
                "demographics": "tech-savvy professionals and entrepreneurs"
            }),
            "branding_guidelines": json.dumps({
                "visual_style": "modern_tech",
                "color_scheme": ["electric blue", "silver", "dark gray"],
                "tone": "knowledgeable and inspiring",
                "key_messages": ["tech insights", "future trends", "practical applications"]
            })
        },
        {
            "name": "Mike Fit Coach",
            "bio": "Certified personal trainer and nutrition expert helping people achieve their fitness goals through sustainable methods.",
            "voice_type": "energetic_male",
            "personality_traits": json.dumps(["motivating", "energetic", "supportive", "results-focused"]),
            "target_audience": json.dumps({
                "age_range": "20-50",
                "income_level": "middle_class",
                "interests": ["fitness", "health", "nutrition", "wellness"],
                "demographics": "people starting or improving their fitness journey"
            }),
            "branding_guidelines": json.dumps({
                "visual_style": "high_energy",
                "color_scheme": ["bright green", "orange", "black"],
                "tone": "motivating and encouraging",
                "key_messages": ["achievable goals", "healthy habits", "consistent progress"]
            })
        }
    ]
    
    for influencer in sample_influencers:
        cursor.execute("""
            INSERT OR IGNORE INTO influencers 
            (name, bio, voice_type, personality_traits, target_audience, branding_guidelines)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            influencer["name"], influencer["bio"], influencer["voice_type"],
            influencer["personality_traits"], influencer["target_audience"], influencer["branding_guidelines"]
        ))
    
    # Link influencers to niches
    influencer_niche_links = [
        # Alex Finance Guru -> personal_finance
        (1, 1, 8, json.dumps({"content_focus": "investment_education", "expertise_level": "advanced"})),
        # Sarah Tech Vision -> technology  
        (2, 2, 9, json.dumps({"content_focus": "ai_and_innovation", "expertise_level": "expert"})),
        # Mike Fit Coach -> fitness_health
        (3, 3, 7, json.dumps({"content_focus": "practical_fitness", "expertise_level": "professional"}))
    ]
    
    for influencer_id, niche_id, expertise_level, content_style in influencer_niche_links:
        cursor.execute("""
            INSERT OR IGNORE INTO influencer_niches 
            (influencer_id, niche_id, expertise_level, content_style)
            VALUES (?, ?, ?, ?)
        """, (influencer_id, niche_id, expertise_level, content_style))
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print("✅ Default data inserted successfully!")

if __name__ == "__main__":
    # Create database and schema
    db_path = create_influencer_tables()
    print(f"Database created at: {db_path}")
    
    # Insert default data
    insert_default_data(db_path)
    print("✅ POC database setup complete!")
