"""
Configuration settings for Automated Content Creator
"""

import os
from typing import Dict, List, Any

# Project Structure
PROJECT_ROOT = "/workspace/content-creator"
GENERATED_CONTENT_DIR = f"{PROJECT_ROOT}/generated-content"
CONTENT_LIBRARY_DIR = f"{PROJECT_ROOT}/content-library"
DATABASE_DIR = f"{PROJECT_ROOT}/data/database"

# Generated Content Paths
VIDEOS_DIR = f"{GENERATED_CONTENT_DIR}/videos"
AUDIO_DIR = f"{GENERATED_CONTENT_DIR}/audio"
THUMBNAILS_DIR = f"{GENERATED_CONTENT_DIR}/thumbnails"
SOCIAL_MEDIA_DIR = f"{GENERATED_CONTENT_DIR}/social-media"

# Content Library Paths
SCENES_DIR = f"{CONTENT_LIBRARY_DIR}/scenes"
TAGS_DIR = f"{CONTENT_LIBRARY_DIR}/tags"
EMBEDDINGS_DIR = f"{CONTENT_LIBRARY_DIR}/embeddings"

# Video Generation Settings
VIDEO_SETTINGS = {
    "youtube": {
        "resolution": "1920x1080",
        "aspect_ratio": "16:9",
        "duration_range": (300, 900),  # 5-15 minutes
        "fps": 30,
        "quality": "high"
    },
    "tiktok": {
        "resolution": "1080x1920", 
        "aspect_ratio": "9:16",
        "duration_range": (15, 60),  # 15-60 seconds
        "fps": 30,
        "quality": "high"
    },
    "instagram": {
        "resolution": "1080x1920",
        "aspect_ratio": "9:16", 
        "duration_range": (15, 90),  # 15-90 seconds
        "fps": 30,
        "quality": "high"
    }
}

# Audio Settings
AUDIO_SETTINGS = {
    "default_voice": "professional_female",
    "sample_rate": 44100,
    "format": "mp3",
    "background_music_volume": 0.3,
    "voice_volume": 0.8,
    "noise_reduction": True,
    "normalization": True
}

# Script Generation Settings
SCRIPT_SETTINGS = {
    "max_scenes": 10,
    "min_scene_duration": 15,  # seconds
    "max_scene_duration": 120,  # seconds
    "target_audience_tags": ["beginners", "professionals", "general"],
    "tone_options": ["professional", "casual", "educational", "entertaining", "motivational"],
    "content_types": ["explainer", "tutorial", "story", "demo", "testimonial"]
}

# Meta-tagging Settings
TAGGING_SETTINGS = {
    "specific_tags": [
        "productivity", "ai-tools", "marketing", "technology", "business",
        "education", "tutorial", "how-to", "tips", "guide", "review",
        "comparison", "trends", "strategy", "automation", "workflow"
    ],
    "generic_tags": [
        "tech", "business", "lifestyle", "education", "health", "finance",
        "entertainment", "news", "sports", "travel", "food", "fashion"
    ],
    "mood_tags": [
        "inspiring", "informative", "motivational", "technical", "casual",
        "professional", "entertaining", "educational", "practical", "theoretical"
    ],
    "style_tags": [
        "modern", "minimal", "colorful", "professional", "dynamic",
        "static", "animated", "realistic", "abstract", "clean"
    ]
}

# Platform-specific Text Content Settings
SOCIAL_MEDIA_SETTINGS = {
    "linkedin": {
        "max_characters": 3000,
        "optimal_hashtags": 3,
        "engagement_elements": ["question", "statistic", "call_to_action"],
        "tone": "professional"
    },
    "twitter": {
        "max_characters": 280,
        "optimal_hashtags": 2,
        "engagement_elements": ["question", "thread", "poll"],
        "tone": "conversational"
    },
    "instagram": {
        "max_characters": 2200,
        "optimal_hashtags": 10,
        "engagement_elements": ["question", "story", "behind_scenes"],
        "tone": "visual_focused"
    }
}

# Content Library Settings
LIBRARY_SETTINGS = {
    "similarity_threshold": 0.8,
    "max_embedding_distance": 0.3,
    "auto_tagging": True,
    "performance_weight": {
        "engagement_rate": 0.4,
        "sentiment_score": 0.3,
        "completion_rate": 0.2,
        "click_through_rate": 0.1
    },
    "usage_tracking": True,
    "version_control": True
}

# Comment Analysis Settings
ANALYSIS_SETTINGS = {
    "sentiment_models": {
        "primary": "cardiffnlp/twitter-roberta-base-sentiment-latest",
        "fallback": "distilbert-base-uncased-finetuned-sst-2-english"
    },
    "topic_modeling": {
        "algorithm": " LDA",
        "num_topics": 5,
        "passes": 10
    },
    "confidence_threshold": 0.7,
    "minimum_comments": 10,
    "rate_limits": {
        "youtube": {"requests_per_hour": 100, "max_results": 100},
        "twitter": {"requests_per_hour": 300, "max_results": 100},
        "instagram": {"requests_per_hour": 200, "max_results": 50}
    }
}

# Performance Settings
PERFORMANCE_SETTINGS = {
    "batch_sizes": {
        "video_generation": 5,
        "audio_generation": 10,
        "image_generation": 10,
        "text_processing": 50
    },
    "concurrency_limits": {
        "video_generation": 2,
        "audio_generation": 5,
        "image_generation": 5,
        "api_requests": 10
    },
    "timeout_seconds": {
        "video_generation": 300,
        "audio_generation": 120,
        "image_generation": 60,
        "api_requests": 30
    }
}

# Quality Assurance Settings
QA_SETTINGS = {
    "minimum_quality_score": 6.0,
    "auto_retry_failed_generations": True,
    "max_retries": 3,
    "validation_checks": {
        "audio_duration_match": True,
        "video_audio_sync": True,
        "content_safety": True,
        "platform_compliance": True
    }
}

# File Management Settings
FILE_SETTINGS = {
    "backup_enabled": True,
    "compression": {
        "videos": "mp4",  # Already compressed format
        "audio": "mp3",
        "images": "webp"
    },
    "naming_convention": "{content_type}_{platform}_{timestamp}_{id}",
    "cleanup_old_files": True,
    "retention_days": 90
}

# API Settings (for external integrations)
API_SETTINGS = {
    "youtube_data_api": {
        "base_url": "https://www.googleapis.com/youtube/v3",
        "rate_limit": 10000,  # units per day
        "quota_cost_per_request": 1
    },
    "twitter_api": {
        "base_url": "https://api.twitter.com/2",
        "rate_limit": 300,  # requests per 15 minutes
        "bearer_token_required": True
    },
    "openai_api": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4",
        "max_tokens": 4000,
        "temperature": 0.7
    }
}

# Environment-specific overrides
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    # Production-specific settings
    VIDEO_SETTINGS["youtube"]["quality"] = "ultra"
    PERFORMANCE_SETTINGS["concurrency_limits"]["video_generation"] = 5
    FILE_SETTINGS["backup_enabled"] = True
elif ENVIRONMENT == "development":
    # Development-specific settings
    VIDEO_SETTINGS["youtube"]["quality"] = "medium"
    PERFORMANCE_SETTINGS["timeout_seconds"]["video_generation"] = 180
    
def get_video_settings(platform: str) -> Dict[str, Any]:
    """Get video settings for a specific platform"""
    return VIDEO_SETTINGS.get(platform, VIDEO_SETTINGS["youtube"])

def get_social_media_settings(platform: str) -> Dict[str, Any]:
    """Get social media settings for a specific platform"""
    return SOCIAL_MEDIA_SETTINGS.get(platform, SOCIAL_MEDIA_SETTINGS["linkedin"])

def get_platform_config(platform: str) -> Dict[str, Any]:
    """Get complete configuration for a platform"""
    return {
        "video": get_video_settings(platform),
        "social_media": get_social_media_settings(platform)
    }