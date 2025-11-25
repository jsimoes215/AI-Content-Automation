-- Database schema for AI Content Automation System

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    platform TEXT,
    target_audience TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scripts table
CREATE TABLE IF NOT EXISTS scripts (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    platform TEXT,
    duration INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id)
);

-- Audio files table
CREATE TABLE IF NOT EXISTS audio_files (
    id TEXT PRIMARY KEY,
    script_id TEXT,
    file_path TEXT,
    duration REAL,
    voice_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (script_id) REFERENCES scripts (id)
);

-- Video files table
CREATE TABLE IF NOT EXISTS video_files (
    id TEXT PRIMARY KEY,
    script_id TEXT,
    file_path TEXT,
    resolution TEXT,
    duration REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (script_id) REFERENCES scripts (id)
);

-- Content variations for A/B testing
CREATE TABLE IF NOT EXISTS content_variations (
    id TEXT PRIMARY KEY,
    original_content_id TEXT,
    variation_type TEXT,
    content TEXT,
    performance_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance analytics
CREATE TABLE IF NOT EXISTS performance_analytics (
    id TEXT PRIMARY KEY,
    content_id TEXT,
    platform TEXT,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    engagement_rate REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User feedback and sentiment analysis
CREATE TABLE IF NOT EXISTS user_feedback (
    id TEXT PRIMARY KEY,
    content_id TEXT,
    platform TEXT,
    sentiment_score REAL,
    feedback_text TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_projects_created ON projects (created_at);
CREATE INDEX IF NOT EXISTS idx_scripts_project ON scripts (project_id);
CREATE INDEX IF NOT EXISTS idx_scripts_created ON scripts (created_at);
CREATE INDEX IF NOT EXISTS idx_audio_script ON audio_files (script_id);
CREATE INDEX IF NOT EXISTS idx_video_script ON video_files (script_id);
CREATE INDEX IF NOT EXISTS idx_performance_content ON performance_analytics (content_id);
CREATE INDEX IF NOT EXISTS idx_feedback_content ON user_feedback (content_id);