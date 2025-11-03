"""
Base models for the comment scraping system.

This module defines the core data models used across all platforms
for storing and processing scraped comments.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class Platform(str, Enum):
    """Supported social media platforms."""
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class SentimentLabel(str, Enum):
    """Sentiment classification labels."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class ContentType(str, Enum):
    """Type of content being commented on."""
    VIDEO = "video"
    POST = "post"
    REEL = "reel"
    STORY = "story"
    THREAD = "thread"


class CommentBase(BaseModel):
    """Base comment model with common fields."""
    
    # Identifiers
    comment_id: str = Field(..., description="Unique comment identifier")
    platform: Platform = Field(..., description="Platform source")
    content_id: str = Field(..., description="ID of the content being commented on")
    parent_comment_id: Optional[str] = Field(None, description="Parent comment ID for replies")
    
    # Comment Content
    text: str = Field(..., min_length=1, max_length=2000, description="Comment text")
    language: Optional[str] = Field(None, description="Detected language code")
    
    # User Information (minimized for privacy)
    user_id: Optional[str] = Field(None, description="Platform-specific user ID")
    username: Optional[str] = Field(None, description="Display username")
    user_verified: bool = Field(default=False, description="Whether user is verified")
    
    # Engagement Metrics
    like_count: int = Field(default=0, ge=0)
    reply_count: int = Field(default=0, ge=0)
    
    # Timestamps
    created_at: datetime = Field(..., description="Comment creation time")
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="When comment was scraped")
    
    # Status
    is_deleted: bool = Field(default=False, description="Whether comment has been deleted")
    is_spam: bool = Field(default=False, description="Whether comment is flagged as spam")
    
    # Raw data for compliance
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw API response data")


class CommentWithAnalysis(CommentBase):
    """Extended comment model with analysis results."""
    
    # Sentiment Analysis
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1, description="Sentiment score (-1 to 1)")
    sentiment_label: Optional[SentimentLabel] = Field(None, description="Sentiment classification")
    sentiment_confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence in sentiment prediction")
    
    # Topic Modeling
    topics: List[str] = Field(default_factory=list, description="Extracted topics/keywords")
    topic_scores: Optional[Dict[str, float]] = Field(None, description="Topic confidence scores")
    
    # Intent Detection
    intent: Optional[str] = Field(None, description="Detected user intent")
    intent_confidence: Optional[float] = Field(None, ge=0, le=1, description="Intent detection confidence")
    
    # Quality Metrics
    quality_score: Optional[float] = Field(None, ge=0, le=1, description="Comment quality assessment")
    engagement_potential: Optional[float] = Field(None, ge=0, le=1, description="Predicted engagement potential")
    
    # Processing metadata
    analysis_version: str = Field(default="1.0", description="Analysis model version")
    processed_at: Optional[datetime] = Field(None, description="When analysis was performed")


class ScrapingJob(BaseModel):
    """Model for tracking scraping jobs."""
    
    job_id: str = Field(..., description="Unique job identifier")
    platform: Platform = Field(..., description="Platform being scraped")
    content_id: str = Field(..., description="Content ID to scrape comments from")
    content_type: ContentType = Field(..., description="Type of content")
    
    # Job Configuration
    max_comments: int = Field(default=1000, ge=1, le=50000, description="Maximum comments to scrape")
    include_replies: bool = Field(default=True, description="Whether to include reply comments")
    language_filter: Optional[str] = Field(None, description="Filter by language code")
    
    # Job Status
    status: str = Field(default="pending", description="Job status: pending, running, completed, failed")
    progress: float = Field(default=0.0, ge=0, le=1, description="Progress as fraction (0-1)")
    comments_scraped: int = Field(default=0, ge=0, description="Number of comments scraped")
    
    # Timing
    started_at: Optional[datetime] = Field(None, description="When job started")
    completed_at: Optional[datetime] = Field(None, description="When job completed")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if job failed")
    retry_count: int = Field(default=0, ge=0, description="Number of retry attempts")
    
    # Results
    comments: List[CommentWithAnalysis] = Field(default_factory=list, description="Scraped comments")


class RateLimitInfo(BaseModel):
    """Model for tracking rate limit status."""
    
    platform: Platform = Field(..., description="Platform this rate limit applies to")
    endpoint: str = Field(..., description="API endpoint")
    
    # Rate Limit Details
    limit: int = Field(..., description="Request limit")
    remaining: int = Field(..., description="Requests remaining")
    reset_time: datetime = Field(..., description="When rate limit resets")
    
    # Status
    is_limited: bool = Field(default=False, description="Whether currently rate limited")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retry")


class ComplianceRecord(BaseModel):
    """Model for tracking compliance with privacy regulations."""
    
    record_id: str = Field(..., description="Unique compliance record ID")
    job_id: str = Field(..., description="Associated scraping job")
    platform: Platform = Field(..., description="Platform source")
    
    # Data Processing
    purpose: str = Field(..., description="Purpose of data collection")
    lawful_basis: str = Field(..., description="GDPR lawful basis")
    data_categories: List[str] = Field(..., description="Categories of data processed")
    
    # Retention
    collected_at: datetime = Field(..., description="When data was collected")
    retention_until: datetime = Field(..., description="When data should be deleted")
    auto_delete: bool = Field(default=True, description="Whether to auto-delete")
    
    # User Rights
    consent_obtained: bool = Field(default=False, description="Whether explicit consent was obtained")
    user_rights_supported: bool = Field(default=True, description="Whether user rights are supported")
    
    # Audit
    processed_by: str = Field(..., description="System/user that processed the data")
    processing_purposes: List[str] = Field(default_factory=list, description="Specific processing purposes")


class ScrapingStats(BaseModel):
    """Model for tracking scraping statistics."""
    
    platform: Platform = Field(..., description="Platform")
    date: datetime = Field(..., description="Date for statistics")
    
    # Volume Metrics
    total_comments: int = Field(default=0, ge=0, description="Total comments scraped")
    unique_comments: int = Field(default=0, ge=0, description="Unique comments (after deduplication)")
    failed_requests: int = Field(default=0, ge=0, description="Number of failed requests")
    
    # Performance Metrics
    avg_response_time: float = Field(default=0.0, ge=0, description="Average API response time")
    rate_limit_hits: int = Field(default=0, ge=0, description="Number of rate limit encounters")
    
    # Quality Metrics
    spam_comments: int = Field(default=0, ge=0, description="Number of spam comments detected")
    sentiment_distribution: Dict[SentimentLabel, int] = Field(default_factory=dict, description="Sentiment distribution")
    
    # Compliance Metrics
    gdpr_compliant: bool = Field(default=True, description="Whether scraping was GDPR compliant")
    data_retention_applied: bool = Field(default=True, description="Whether retention policies applied")


# Validators
@validator('text')
def validate_comment_text(cls, v):
    """Validate comment text meets content policies."""
    if len(v.strip()) < 3:
        raise ValueError("Comment text too short")
    if len(v) > 2000:
        raise ValueError("Comment text too long")
    return v.strip()


@validator('sentiment_score', 'sentiment_confidence', 'intent_confidence', 'quality_score', 'engagement_potential')
def validate_scores(cls, v):
    """Validate score fields are in valid range."""
    if v is not None and not (0 <= v <= 1):
        raise ValueError("Score must be between 0 and 1")
    return v