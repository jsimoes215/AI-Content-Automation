# Automated Content Creator API Specification

## Overview

RESTful API for the Automated Content Creator system that handles video idea processing, script generation, content creation, and multi-platform adaptation.

## Base URL

```
Development: http://localhost:54321/functions/v1
Production: https://your-project.supabase.co/functions/v1
```

## Authentication

All endpoints require JWT authentication via Supabase Auth:

```javascript
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

## Core Endpoints

### 1. Idea Processing

#### Submit Video Idea
```http
POST /api/ideas
```

**Request Body:**
```json
{
  "original_idea": "How to improve productivity with AI tools",
  "target_audience": "busy professionals",
  "tone": "educational",
  "platform_preferences": ["youtube", "tiktok"],
  "duration_preference": "medium",
  "key_points": [
    "AI can automate repetitive tasks",
    "Time management benefits",
    "Specific tool recommendations"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "processing",
    "message": "Idea submitted successfully. Script generation in progress.",
    "estimated_completion": "2025-10-30T01:00:00Z"
  }
}
```

#### Get Idea Status
```http
GET /api/ideas/{id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "original_idea": "How to improve productivity with AI tools",
    "status": "completed",
    "progress": {
      "script_generated": true,
      "scenes_created": 5,
      "videos_generated": 5,
      "platform_adaptations": 3
    },
    "created_at": "2025-10-29T23:30:00Z",
    "updated_at": "2025-10-29T23:45:00Z"
  }
}
```

### 2. Script Generation

#### Generate Script from Idea
```http
POST /api/scripts/generate
```

**Request Body:**
```json
{
  "idea_id": "uuid",
  "script_type": "explainer",
  "target_duration": 300,  // 5 minutes
  "scene_count": 5,
  "platform_optimization": {
    "youtube": {"style": "comprehensive"},
    "tiktok": {"style": "concise", "hook_focused": true}
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "script": {
      "title": "Boost Your Productivity with AI Tools",
      "total_duration": 285,
      "word_count": 750,
      "scenes": [
        {
          "scene_number": 1,
          "duration": 45,
          "voiceover_text": "Imagine saving 2 hours every day...",
          "visual_description": "Split screen showing busy person vs. organized person with AI tools",
          "scene_type": "intro",
          "hooks": {
            "youtube": "Hook: Time-saving potential",
            "tiktok": "Hook: 'Save 2 hours daily'"
          }
        }
        // ... more scenes
      ]
    }
  }
}
```

### 3. Content Library Management

#### Search Scenes by Tags
```http
GET /api/library/scenes?tags=productivity,tutorial&platform=youtube&limit=10
```

**Query Parameters:**
- `tags`: Comma-separated specific tags
- `generic_tags`: Comma-separated generic tags
- `platform`: Filter by target platform
- `duration_min`: Minimum duration in seconds
- `duration_max`: Maximum duration in seconds
- `limit`: Number of results (default: 20, max: 100)

**Response:**
```json
{
  "success": true,
  "data": {
    "scenes": [
      {
        "id": "uuid",
        "scene_number": 3,
        "duration": 60,
        "voiceover_text": "Let me show you the top 3 AI tools...",
        "visual_description": "Screen recording of AI tool interface",
        "specific_tags": ["productivity", "ai-tools", "tutorial"],
        "generic_tags": ["tech", "education", "how-to"],
        "performance_score": 8.5,
        "usage_count": 12,
        "similarity_score": 0.92
      }
    ],
    "total_count": 15,
    "search_vector": "productivity tutorial ai tools"
  }
}
```

#### Add Scene to Library
```http
POST /api/library/scenes
```

**Request Body:**
```json
{
  "scene_id": "uuid",
  "specific_tags": ["productivity", "ai-tools", "tutorial"],
  "generic_tags": ["tech", "education", "how-to"],
  "library_category": "experimental"
}
```

#### Update Scene Tags
```http
PUT /api/library/scenes/{id}/tags
```

**Request Body:**
```json
{
  "specific_tags": ["productivity", "ai-tools", "tutorial", "automation"],
  "generic_tags": ["tech", "education", "how-to", "advanced"],
  "performance_score": 9.2
}
```

### 4. Video Generation

#### Generate Video from Script
```http
POST /api/videos/generate
```

**Request Body:**
```json
{
  "script_id": "uuid",
  "generation_options": {
    "voice": "professional_female",
    "background_music": "upbeat_corporate",
    "video_style": "modern_clean",
    "quality": "high",
    "platform_specific": {
      "youtube": {"resolution": "1920x1080", "fps": 30},
      "tiktok": {"resolution": "1080x1920", "fps": 30}
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "processing",
    "estimated_completion": "2025-10-30T00:30:00Z",
    "progress": {
      "total_scenes": 5,
      "completed_scenes": 0,
      "failed_scenes": 0
    }
  }
}
```

#### Get Video Generation Status
```http
GET /api/videos/{id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "completed",
    "scenes": [
      {
        "scene_id": "uuid",
        "status": "completed",
        "file_path": "/generated/videos/scene_1.mp4",
        "duration": 45,
        "quality_score": 8.7
      }
    ],
    "full_video_path": "/generated/videos/complete_video.mp4",
    "total_duration": 285,
    "generation_metadata": {
      "processing_time": 1800,
      "voice_used": "professional_female",
      "music_track": "upbeat_corporate_001"
    }
  }
}
```

### 5. Platform-Specific Adaptation

#### Adapt Content for Platform
```http
POST /api/adapt/{platform}
```

**Request Body:**
```json
{
  "content_id": "uuid",
  "adaptation_options": {
    "target_duration": 60,
    "aspect_ratio": "9:16",
    "style_preferences": {
      "hook_focused": true,
      "trending_elements": true
    }
  }
}
```

**Supported Platforms:** `youtube`, `tiktok`, `instagram`, `linkedin`, `twitter`

**Response:**
```json
{
  "success": true,
  "data": {
    "adapted_content_id": "uuid",
    "platform": "tiktok",
    "original_duration": 285,
    "adapted_duration": 58,
    "adaptations_made": [
      "trimmed_to_hook",
      "converted_to_vertical",
      "added_trending_music",
      "optimized_for_mobile"
    ],
    "file_path": "/generated/tiktok/adapted_video.mp4",
    "estimated_performance": {
      "engagement_rate": 0.075,
      "completion_rate": 0.82
    }
  }
}
```

#### Preview Platform Adaptation
```http
GET /api/adapt/{id}/preview
```

### 6. Comment Analysis

#### Scrape Comments for Content
```http
POST /api/comments/scrape
```

**Request Body:**
```json
{
  "content_id": "uuid",
  "platforms": ["youtube", "twitter"],
  "options": {
    "max_comments": 500,
    "include_replies": true,
    "filter_bot_comments": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "processing",
    "estimated_completion": "2025-10-30T02:00:00Z",
    "platforms": ["youtube", "twitter"],
    "total_comments_collected": 0
  }
}
```

#### Get Comment Analysis Results
```http
GET /api/comments/analysis/{content_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "content_id": "uuid",
    "analysis_summary": {
      "total_comments": 1247,
      "sentiment_distribution": {
        "positive": 0.68,
        "neutral": 0.22,
        "negative": 0.10
      },
      "top_topics": [
        {"topic": "tool_recommendations", "mentions": 89, "sentiment": 0.85},
        {"topic": "time_saving_benefits", "mentions": 156, "sentiment": 0.92},
        {"topic": "implementation_difficulty", "mentions": 34, "sentiment": -0.23}
      ]
    },
    "insights": [
      {
        "type": "positive_feedback",
        "description": "Users love specific tool recommendations",
        "action_suggestion": "Create follow-up content with detailed tool walkthroughs"
      },
      {
        "type": "improvement_area",
        "description": "Some users find implementation challenging",
        "action_suggestion": "Add beginner-friendly version or step-by-step guide"
      }
    ],
    "performance_correlation": {
      "engagement_vs_sentiment": 0.78,
      "comment_count_vs_views": 0.65
    }
  }
}
```

### 7. Performance Analytics

#### Get Content Performance
```http
GET /api/analytics/performance/{content_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "content_id": "uuid",
    "platform_breakdown": {
      "youtube": {
        "views": 15420,
        "likes": 892,
        "comments": 156,
        "shares": 23,
        "engagement_rate": 0.069,
        "watch_time_avg": 142
      },
      "tiktok": {
        "views": 45600,
        "likes": 3200,
        "comments": 445,
        "shares": 178,
        "engagement_rate": 0.084,
        "completion_rate": 0.78
      }
    },
    "trend_analysis": {
      "performance_trend": "increasing",
      "peak_performance_day": "Friday",
      "optimal_post_time": "14:00 UTC"
    },
    "comparison_benchmarks": {
      "industry_average_engagement": 0.045,
      "your_performance_vs_average": "+127%",
      "content_type_ranking": "top_5_percent"
    }
  }
}
```

### 8. A/B Testing

#### Create A/B Test
```http
POST /api/ab-tests
```

**Request Body:**
```json
{
  "name": "Thumbnail Test - AI Tools Video",
  "description": "Testing different thumbnail styles for AI productivity video",
  "test_type": "thumbnail",
  "variants": [
    {
      "content_id": "uuid_variant_a",
      "traffic_percentage": 0.5,
      "description": "Clean minimalist thumbnail"
    },
    {
      "content_id": "uuid_variant_b", 
      "traffic_percentage": 0.5,
      "description": "Colorful engaging thumbnail"
    }
  ],
  "success_metrics": ["engagement_rate", "click_through_rate"],
  "duration_days": 7
}
```

#### Get A/B Test Results
```http
GET /api/ab-tests/{id}
```

### 9. Content Feedback

#### Submit Content Feedback
```http
POST /api/feedback
```

**Request Body:**
```json
{
  "content_id": "uuid",
  "feedback_type": "quality_rating",
  "rating": 4,
  "feedback_text": "Great content but could use more specific examples",
  "category": "content_suggestion"
}
```

#### Get Feedback Summary
```http
GET /api/feedback/summary/{content_id}
```

## Error Handling

### Standard Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "original_idea",
      "issue": "Field is required and cannot be empty"
    }
  },
  "timestamp": "2025-10-29T23:45:00Z"
}
```

### Common Error Codes
- `VALIDATION_ERROR`: Request validation failed
- `AUTHENTICATION_ERROR`: Invalid or missing authentication
- `RESOURCE_NOT_FOUND`: Requested resource doesn't exist
- `PROCESSING_ERROR`: Content processing failed
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INSUFFICIENT_CREDITS`: Not enough credits/quota

## Rate Limiting

- **General API**: 1000 requests per hour per user
- **Video Generation**: 10 requests per hour per user
- **Comment Scraping**: 5 requests per hour per user
- **A/B Testing**: 3 requests per hour per user

## Webhooks

### Content Generation Complete
```http
POST /webhook/content-generation
```

**Payload:**
```json
{
  "event": "content_generation_complete",
  "data": {
    "project_id": "uuid",
    "content_id": "uuid",
    "platforms": ["youtube", "tiktok"],
    "status": "completed"
  }
}
```

### Comment Analysis Complete
```http
POST /webhook/comment-analysis
```

**Payload:**
```json
{
  "event": "comment_analysis_complete",
  "data": {
    "content_id": "uuid",
    "analysis_id": "uuid",
    "total_comments": 1247,
    "sentiment_summary": {
      "positive": 0.68,
      "negative": 0.10,
      "neutral": 0.22
    }
  }
}
```

## SDK Integration

### JavaScript/TypeScript SDK

```javascript
import { ContentCreator } from '@automated-content-creator/sdk';

const client = new ContentCreator({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.contentcreator.com'
});

// Submit video idea
const idea = await client.ideas.create({
  original_idea: "How to improve productivity with AI",
  target_audience: "professionals",
  tone: "educational"
});

// Generate script
const script = await client.scripts.generate({
  ideaId: idea.id,
  targetDuration: 300
});

// Generate videos
const videos = await client.videos.generate({
  scriptId: script.id,
  options: {
    voice: 'professional_female',
    quality: 'high'
  }
});
```

This API specification provides comprehensive documentation for all core functionality of the Automated Content Creator system, ensuring easy integration and development.