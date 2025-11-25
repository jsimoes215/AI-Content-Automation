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

# ==========================================
# AI INFLUENCER SYSTEM CONFIGURATION
# ==========================================

# AI Influencer System Settings
AI_INFLUENCER_SETTINGS = {
    "system_version": "2.0.0",
    "cost_optimization_enabled": True,
    "base_image_provider": "dalle3",
    "variation_providers": ["qwen", "gemini"],
    "video_provider": "minimax",
    "consistency_target": 0.95
}

# Voice Types for AI Influencers
VOICE_TYPES = [
    "Professional Male",
    "Friendly Female", 
    "Casual Young",
    "Expert Female",
    "Energetic Male"
]

# Visual Styles for AI Influencers
VISUAL_STYLES = [
    "Corporate",
    "Modern Minimal", 
    "Vibrant Energetic",
    "Warm Approachable",
    "Trendy Youthful",
    "Sophisticated"
]

# Content Niches for AI Influencers
CONTENT_NICHES = [
    "Finance",
    "Tech", 
    "Fitness",
    "Career",
    "Lifestyle"
]

# Image Generation Settings
IMAGE_GENERATION_SETTINGS = {
    "dalle3": {
        "model": "dall-e-3",
        "quality": "hd",
        "size": "1024x1024",
        "cost_per_image": 0.04
    },
    "qwen": {
        "model": "qwen-vl",
        "cost_per_image": 0.005
    },
    "gemini": {
        "model": "gemini-2.5-flash",
        "cost_per_image": 0.005
    }
}

# Video Generation Settings
VIDEO_GENERATION_SETTINGS = {
    "minimax": {
        "model": "minimax-video",
        "cost_per_second": 0.12,
        "consistency_score": 0.95,
        "optimal_for": "talking_head"
    },
    "runway": {
        "model": "runway-gen3",
        "cost_per_second": 0.05,
        "consistency_score": 0.88,
        "optimal_for": "cinematic"
    },
    "stability": {
        "model": "stable-video",
        "cost_per_second": 0.04,
        "consistency_score": 0.80,
        "optimal_for": "animated"
    }
}

# Cost Optimization Settings
COST_OPTIMIZATION_SETTINGS = {
    "enable_base_variation_strategy": True,
    "base_image_cost": 0.04,  # DALL-E 3
    "variation_image_cost": 0.005,  # Qwen/Gemini
    "savings_threshold": 0.7,  # 70% savings target
    "max_variations_per_base": 20,
    "quality_fallback": True
}

# Persona Optimization Settings
PERSONA_OPTIMIZATION_SETTINGS = {
    "consistency_weight": 0.3,
    "engagement_weight": 0.25,
    "growth_weight": 0.25,
    "quality_weight": 0.2,
    "optimization_frequency": "weekly",
    "min_performance_threshold": 6.0
}

# Database Configuration for AI Influencer
AI_INFLUENCER_DB = {
    "tables": {
        "influencers": "ai_influencers",
        "visual_assets": "influencer_visual_assets", 
        "onboarding": "influencer_onboarding",
        "content_generation": "generated_content",
        "cost_tracking": "cost_optimization_logs"
    }
}

# API Key Requirements
REQUIRED_API_KEYS = {
    "essential": [
        "OPENAI_API_KEY",      # DALL-E 3, GPT-4
        "MINIMAX_API_KEY",     # Video generation
        "QWEN_API_KEY"         # Cost-optimized image variations
    ],
    "important": [
        "GOOGLE_API_KEY",      # Gemini 2.5 Flash (alternative image)
        "YOUTUBE_API_KEY",     # Already in existing system
        "TWITTER_BEARER_TOKEN" # Already in existing system
    ],
    "optional": [
        "RUNWAY_API_KEY",      # Cinematic videos
        "STABILITY_API_KEY"    # Animated videos
    ]
}

# Performance Thresholds
PERFORMANCE_THRESHOLDS = {
    "persona_consistency": {
        "excellent": 9.0,
        "good": 7.0,
        "acceptable": 6.0,
        "needs_improvement": 4.0
    },
    "engagement_rate": {
        "excellent": 0.10,
        "good": 0.05,
        "acceptable": 0.03,
        "needs_improvement": 0.01
    },
    "cost_per_content": {
        "excellent": 2.0,
        "good": 5.0,
        "acceptable": 10.0,
        "needs_improvement": 20.0
    }
}

def get_ai_influencer_config() -> Dict[str, Any]:
    """Get complete AI Influencer system configuration"""
    return {
        "system": AI_INFLUENCER_SETTINGS,
        "voice_types": VOICE_TYPES,
        "visual_styles": VISUAL_STYLES,
        "content_niches": CONTENT_NICHES,
        "image_generation": IMAGE_GENERATION_SETTINGS,
        "video_generation": VIDEO_GENERATION_SETTINGS,
        "cost_optimization": COST_OPTIMIZATION_SETTINGS,
        "persona_optimization": PERSONA_OPTIMIZATION_SETTINGS,
        "database": AI_INFLUENCER_DB,
        "api_requirements": REQUIRED_API_KEYS,
        "performance_thresholds": PERFORMANCE_THRESHOLDS
    }

def get_image_generation_config(provider: str) -> Dict[str, Any]:
    """Get image generation configuration for specific provider"""
    return IMAGE_GENERATION_SETTINGS.get(provider, IMAGE_GENERATION_SETTINGS["dalle3"])

def get_video_generation_config(provider: str) -> Dict[str, Any]:
    """Get video generation configuration for specific provider"""
    return VIDEO_GENERATION_SETTINGS.get(provider, VIDEO_GENERATION_SETTINGS["minimax"])

def validate_api_keys() -> Dict[str, bool]:
    """Validate that required API keys are available"""
    validation_results = {}
    
    for category, keys in REQUIRED_API_KEYS.items():
        for key in keys:
            validation_results[key] = os.environ.get(key) is not None
    
    return validation_results

# Environment-specific AI Influencer overrides
if ENVIRONMENT == "production":
    # Production settings for AI Influencer
    AI_INFLUENCER_SETTINGS["consistency_target"] = 0.98
    COST_OPTIMIZATION_SETTINGS["savings_threshold"] = 0.75
elif ENVIRONMENT == "development":
    # Development settings for AI Influencer
    AI_INFLUENCER_SETTINGS["consistency_target"] = 0.90
    COST_OPTIMIZATION_SETTINGS["savings_threshold"] = 0.60

# ========================================
# REAL API INTEGRATIONS CONFIGURATION
# ========================================

# Amazon Polly Audio Configuration
AMAZON_POLLY_CONFIG = {
    "enabled": True,
    "aws_region": os.environ.get("AWS_REGION", "us-east-1"),
    "default_engine": "neural",
    "default_format": "mp3",
    "default_sample_rate": "22050",
    "cost_per_character": {
        "standard": 4.00 / 1_000_000,  # $4 per 1M characters
        "neural": 16.00 / 1_000_000    # $16 per 1M characters
    },
    "free_tier": {
        "standard": 5_000_000,  # 5M characters/month
        "neural": 1_000_000     # 1M characters/month
    }
}

# MiniMax Video Configuration
MINIMAX_VIDEO_CONFIG = {
    "enabled": True,
    "base_url": "https://api.minimax.chat/v1",
    "default_model": "minimax-talkinghead",
    "default_resolution": "1280x720",
    "default_duration": 10,
    "max_duration": 60,
    "cost_per_second": 0.032,  # $0.032 per second
    "supported_resolutions": ["1280x720", "1920x1080"]
}

# Updated API Requirements
REAL_API_REQUIREMENTS = {
    "audio_generation": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"],
    "video_generation": ["MINIMAX_API_KEY"],
    "image_generation": ["OPENAI_API_KEY"],  # DALL-E 3 or use Qwen/Gemini
    "social_media": ["YOUTUBE_API_KEY", "TWITTER_BEARER_TOKEN", "INSTAGRAM_ACCESS_TOKEN"]
}

# Update existing REQUIRED_API_KEYS with real implementations
for category, keys in REAL_API_REQUIREMENTS.items():
    if category in REQUIRED_API_KEYS:
        REQUIRED_API_KEYS[category].extend(keys)
    else:
        REQUIRED_API_KEYS[category] = keys

def get_audio_config() -> Dict[str, Any]:
    """Get Amazon Polly audio configuration"""
    return AMAZON_POLLY_CONFIG

def get_video_config() -> Dict[str, Any]:
    """Get MiniMax Video configuration"""
    return MINIMAX_VIDEO_CONFIG

def validate_real_api_keys() -> Dict[str, bool]:
    """Validate real API keys are available"""
    validation_results = {}
    
    # Check AWS credentials
    validation_results["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID") is not None
    validation_results["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY") is not None
    validation_results["AWS_REGION"] = os.environ.get("AWS_REGION", "us-east-1") is not None
    
    # Check MiniMax API key
    validation_results["MINIMAX_API_KEY"] = os.environ.get("MINIMAX_API_KEY") is not None
    
    return validation_results
