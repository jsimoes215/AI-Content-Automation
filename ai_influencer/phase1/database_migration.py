"""
Phase 1 Database Migration
Creates tables for content campaigns, scheduled posts, and generated content

Author: MiniMax Agent
Date: 2025-11-07
"""

import sqlite3
import json
from datetime import datetime
import os

def create_phase1_tables(db_path: str = "/workspace/ai_influencer_poc/database/influencers.db"):
    """Create Phase 1 database tables"""
    
    print("🚀 Creating Phase 1 database tables...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Content Campaigns Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_campaigns (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                niche TEXT,
                target_platforms TEXT,  -- JSON array
                influencers TEXT,        -- JSON array
                start_date TEXT,
                end_date TEXT,
                total_budget REAL DEFAULT 0.0,
                status TEXT DEFAULT 'planning',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Scheduled Posts Table  
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id TEXT PRIMARY KEY,
                campaign_id TEXT,
                influencer_id INTEGER,
                topic TEXT NOT NULL,
                niche TEXT,
                content_type TEXT DEFAULT 'video',
                platform TEXT,
                scheduled_time TEXT,
                status TEXT DEFAULT 'scheduled',  -- scheduled, generating, ready, posted, failed
                retry_count INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (influencer_id) REFERENCES influencers (id)
            )
        """)
        
        # Generated Content Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generated_content (
                id TEXT PRIMARY KEY,
                post_id TEXT UNIQUE,
                influencer_id INTEGER,
                content TEXT NOT NULL,
                hashtags TEXT,  -- JSON array
                title TEXT,
                description TEXT,
                platform_optimized TEXT,  -- JSON object
                cost_estimate REAL,
                persona_consistency_score REAL,
                generated_at TEXT,
                FOREIGN KEY (post_id) REFERENCES scheduled_posts (id),
                FOREIGN KEY (influencer_id) REFERENCES influencers (id)
            )
        """)
        
        # Content Performance Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_performance (
                id TEXT PRIMARY KEY,
                generated_content_id TEXT,
                platform TEXT,
                post_id TEXT,
                metrics TEXT,  -- JSON object with views, likes, shares, etc.
                recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (generated_content_id) REFERENCES generated_content (id)
            )
        """)
        
        # Social Media Posts Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS social_media_posts (
                id TEXT PRIMARY KEY,
                generated_content_id TEXT,
                platform TEXT,
                platform_post_id TEXT,
                post_url TEXT,
                posting_status TEXT DEFAULT 'pending',  -- pending, posted, failed
                posting_error TEXT,
                posted_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (generated_content_id) REFERENCES generated_content (id)
            )
        """)
        
        # Content Templates Table (expanded from existing niches)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                platform TEXT,
                content_type TEXT,
                template_structure TEXT,  -- JSON template
                variables TEXT,  -- JSON list of variables
                usage_count INTEGER DEFAULT 0,
                avg_performance_score REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_scheduled_posts_status ON scheduled_posts(status)",
            "CREATE INDEX IF NOT EXISTS idx_scheduled_posts_scheduled_time ON scheduled_posts(scheduled_time)",
            "CREATE INDEX IF NOT EXISTS idx_scheduled_posts_platform ON scheduled_posts(platform)",
            "CREATE INDEX IF NOT EXISTS idx_scheduled_posts_influencer ON scheduled_posts(influencer_id)",
            "CREATE INDEX IF NOT EXISTS idx_generated_content_influencer ON generated_content(influencer_id)",
            "CREATE INDEX IF NOT EXISTS idx_content_performance_platform ON content_performance(platform)",
            "CREATE INDEX IF NOT EXISTS idx_social_posts_platform ON social_media_posts(platform)",
            "CREATE INDEX IF NOT EXISTS idx_content_campaigns_status ON content_campaigns(status)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        # Insert sample content templates
        sample_templates = [
            {
                "name": "YouTube Video - Finance Tips",
                "platform": "youtube",
                "content_type": "video",
                "template_structure": json.dumps({
                    "title": "{influencer_intro} {topic} - Quick {niche} Tips",
                    "description": "{influencer_greeting}! {body}\\n\\n💡 {key_points}",
                    "structure": "intro,main_tips,conclusion"
                }),
                "variables": json.dumps(["influencer_intro", "topic", "niche", "body", "key_points"])
            },
            {
                "name": "TikTok Short - Tech Review", 
                "platform": "tiktok",
                "content_type": "short",
                "template_structure": json.dumps({
                    "hook": "{trending_opener}",
                    "content": "{main_points}",
                    "cta": "{engagement_prompt}"
                }),
                "variables": json.dumps(["trending_opener", "main_points", "engagement_prompt"])
            },
            {
                "name": "Instagram Post - Fitness",
                "platform": "instagram", 
                "content_type": "post",
                "template_structure": json.dumps({
                    "caption": "{story} {tips} {hashtags}",
                    "format": "image_text_overlay"
                }),
                "variables": json.dumps(["story", "tips", "hashtags"])
            }
        ]
        
        for template in sample_templates:
            cursor.execute("""
                INSERT OR IGNORE INTO content_templates 
                (name, platform, content_type, template_structure, variables, usage_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                template["name"], template["platform"], template["content_type"],
                template["template_structure"], template["variables"], 0
            ))
        
        conn.commit()
        
        print("✅ Phase 1 database tables created successfully!")
        
        # Print table summary
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📊 Total tables: {len(tables)}")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"   - {table[0]}: {count} records")
        
    except Exception as e:
        print(f"❌ Error creating Phase 1 tables: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def update_existing_influencers_table(db_path: str = "/workspace/ai_influencer_poc/database/influencers.db"):
    """Add new columns to existing influencers table if they don't exist"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get existing columns
        cursor.execute("PRAGMA table_info(influencers)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        new_columns = {
            "is_active": "INTEGER DEFAULT 1",
            "content_voice_prompt": "TEXT",
            "posting_schedule": "TEXT",  # JSON object with preferred posting times
            "brand_partnerships": "TEXT",  # JSON array
            "audience_growth_rate": "REAL DEFAULT 0.0",
            "engagement_rate": "REAL DEFAULT 0.0",
            "total_posts_published": "INTEGER DEFAULT 0"
        }
        
        for column_name, column_def in new_columns.items():
            if column_name not in existing_columns:
                cursor.execute(f"ALTER TABLE influencers ADD COLUMN {column_name} {column_def}")
                print(f"➕ Added column: {column_name}")
        
        conn.commit()
        print("✅ Updated existing influencers table")
        
    except Exception as e:
        print(f"❌ Error updating influencers table: {e}")
        conn.rollback()
    finally:
        conn.close()

def verify_phase1_setup(db_path: str = "/workspace/ai_influencer_poc/database/influencers.db"):
    """Verify Phase 1 setup is complete"""
    
    print("\n🔍 Verifying Phase 1 setup...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check all required tables exist
        required_tables = [
            'influencers', 'niches', 'influencer_niches', 'social_accounts',
            'content_campaigns', 'scheduled_posts', 'generated_content', 
            'content_performance', 'social_media_posts', 'content_templates'
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        else:
            print("✅ All required tables exist")
        
        # Check data integrity
        checks = [
            ("Influencers", "SELECT COUNT(*) FROM influencers"),
            ("Niches", "SELECT COUNT(*) FROM niches"),
            ("Content Campaigns", "SELECT COUNT(*) FROM content_campaigns"),
            ("Scheduled Posts", "SELECT COUNT(*) FROM scheduled_posts"),
            ("Generated Content", "SELECT COUNT(*) FROM generated_content"),
            ("Content Templates", "SELECT COUNT(*) FROM content_templates")
        ]
        
        for name, query in checks:
            cursor.execute(query)
            count = cursor.fetchone()[0]
            print(f"   - {name}: {count} records")
        
        # Test foreign key constraints
        cursor.execute("PRAGMA foreign_key_check")
        violations = cursor.fetchall()
        if violations:
            print(f"⚠️  Foreign key violations: {violations}")
        else:
            print("✅ No foreign key violations")
        
        print("\n🎉 Phase 1 setup verification complete!")
        return True
        
    except Exception as e:
        print(f"❌ Setup verification failed: {e}")
        return False
    finally:
        conn.close()

def main():
    """Main function to run Phase 1 database migration"""
    print("=" * 60)
    print("🤖 AI INFLUENCER MANAGEMENT - PHASE 1 DATABASE SETUP")
    print("=" * 60)
    
    db_path = "/workspace/ai_influencer_poc/database/influencers.db"
    
    try:
        # Create Phase 1 tables
        create_phase1_tables(db_path)
        
        # Update existing influencers table
        update_existing_influencers_table(db_path)
        
        # Verify setup
        if verify_phase1_setup(db_path):
            print("\n🚀 Phase 1 database setup completed successfully!")
            print("Ready for content generation and social media integration.")
        else:
            print("\n❌ Phase 1 database setup completed with issues.")
            print("Please review the errors above.")
            
    except Exception as e:
        print(f"\n💥 Setup failed: {e}")
        print("Please check your database configuration.")

if __name__ == "__main__":
    main()