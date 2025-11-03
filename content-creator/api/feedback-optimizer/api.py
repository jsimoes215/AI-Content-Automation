"""
Feedback Optimizer API Endpoints

Provides REST API endpoints for the feedback-driven content improvement system.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from .engine import LearningEngine
from .models.feedback_data import FeedbackData
from .models.recommendation import Recommendation


# Pydantic models for API requests/responses
class FeedbackItem(BaseModel):
    """Individual feedback item for API."""
    content_id: str
    feedback_type: str = "comment"
    text: str = ""
    engagement_metrics: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None
    content_type: Optional[str] = None
    platform: Optional[str] = None


class AnalysisRequest(BaseModel):
    """Request model for analysis."""
    feedback_data: List[FeedbackItem]
    include_predictive_insights: bool = True
    optimization_level: str = "standard"  # "basic", "standard", "advanced"
    learning_enabled: bool = True


class ImplementationResult(BaseModel):
    """Model for tracking implementation results."""
    recommendation_id: str
    implementation_date: datetime
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float]
    notes: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Response model for analysis."""
    analysis_results: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    learning_insights: Dict[str, Any]
    comprehensive_report: Dict[str, Any]
    processing_time_seconds: float
    timestamp: datetime


class RecommendationResponse(BaseModel):
    """Response model for recommendations."""
    recommendations: List[Dict[str, Any]]
    summary: Dict[str, Any]
    action_plan: Optional[Dict[str, Any]] = None


class LearningSummaryResponse(BaseModel):
    """Response model for learning summary."""
    summary_period: str
    learning_cycles_count: int
    progress_analysis: Dict[str, Any]
    pattern_summary: Dict[str, Any]
    performance_summary: Dict[str, Any]
    key_learnings: List[str]
    enhancement_recommendations: List[Dict[str, Any]]
    learning_engine_health: Dict[str, Any]


# Initialize FastAPI app
app = FastAPI(
    title="Feedback-Driven Content Improvement Optimizer API",
    description="AI-powered system for analyzing feedback and generating content improvement recommendations",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the learning engine
learning_engine = LearningEngine()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Feedback-Driven Content Improvement Optimizer",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "/analyze": "POST - Analyze feedback and generate recommendations",
            "/recommendations": "GET - Get current recommendations",
            "/learning-summary": "GET - Get learning engine summary",
            "/predictive-insights": "POST - Generate predictive insights",
            "/implementation-tracking": "POST - Track implementation results",
            "/health": "GET - System health check"
        }
    }


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_feedback(request: AnalysisRequest):
    """
    Analyze feedback data and generate improvement recommendations.
    
    This endpoint processes feedback data using AI-powered sentiment analysis,
    pattern detection, and generates actionable recommendations for content improvement.
    """
    start_time = datetime.now()
    
    try:
        # Convert Pydantic models to dictionaries
        feedback_data = [item.dict() for item in request.feedback_data]
        
        # Run complete learning cycle
        learning_results = learning_engine.process_feedback_learning_cycle(feedback_data)
        
        # Extract results
        analysis_results = learning_results['analysis_results']
        recommendations = learning_results['recommendations']
        learning_insights = learning_results['learning_insights']
        comprehensive_report = learning_results['comprehensive_report']
        
        # Convert recommendations to dictionary format for JSON response
        recommendations_dict = [rec.to_dict() for rec in recommendations]
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return AnalysisResponse(
            analysis_results=analysis_results,
            recommendations=recommendations_dict,
            learning_insights=learning_insights,
            comprehensive_report=comprehensive_report,
            processing_time_seconds=processing_time,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    priority_filter: Optional[str] = None,
    content_type_filter: Optional[str] = None,
    limit: int = 20
):
    """
    Get current recommendations with optional filtering.
    
    Args:
        priority_filter: Filter by priority ("high", "medium", "low")
        content_type_filter: Filter by content type ("script", "thumbnail", "title", etc.)
        limit: Maximum number of recommendations to return
    """
    try:
        # This would typically retrieve from a database
        # For now, we'll return a placeholder response
        sample_recommendations = [
            {
                "id": "rec_001",
                "title": "Improve Script Opening Hook",
                "description": "Current script openings lack strong hooks to capture audience attention",
                "recommendation_type": "content_optimization",
                "priority": "high",
                "impact_score": 0.85,
                "estimated_time_hours": 3,
                "implementation_difficulty": "Medium"
            }
        ]
        
        summary = {
            "total_recommendations": len(sample_recommendations),
            "priority_distribution": {"high": 1, "medium": 0, "low": 0},
            "average_impact_score": 0.85,
            "high_impact_count": 1
        }
        
        return RecommendationResponse(
            recommendations=sample_recommendations,
            summary=summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recommendations: {str(e)}")


@app.get("/learning-summary", response_model=LearningSummaryResponse)
async def get_learning_summary(days_back: int = 30):
    """
    Get summary of learning engine performance and insights.
    
    Args:
        days_back: Number of days to look back for summary
    """
    try:
        summary = learning_engine.get_learning_summary(days_back)
        return LearningSummaryResponse(**summary)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate learning summary: {str(e)}")


@app.post("/predictive-insights")
async def generate_predictive_insights(request: AnalysisRequest):
    """
    Generate predictive insights based on current feedback and learning history.
    
    This endpoint uses learned patterns to predict future performance
    and recommend proactive actions.
    """
    try:
        # Convert Pydantic models to dictionaries
        feedback_data = [item.dict() for item in request.feedback_data]
        
        # Generate predictive insights
        insights = learning_engine.generate_predictive_insights(feedback_data)
        
        return {
            "predictive_insights": insights,
            "generated_at": datetime.now().isoformat(),
            "confidence_level": insights.get('confidence_levels', {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate predictive insights: {str(e)}")


@app.post("/implementation-tracking")
async def track_implementation_results(result: ImplementationResult):
    """
    Track results of recommendation implementation for learning.
    
    This endpoint allows the system to learn from implementation success/failure
    and improve future recommendations.
    """
    try:
        # Convert to dictionary format
        result_dict = result.dict()
        
        # Feed results to learning engine
        learning_feedback = learning_engine.learn_from_implementation_results(
            result.recommendation_id,
            result_dict
        )
        
        return {
            "status": "success",
            "learning_feedback": learning_feedback,
            "tracked_at": datetime.now().isoformat(),
            "message": "Implementation results tracked successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track implementation: {str(e)}")


@app.get("/health")
async def health_check():
    """
    System health check endpoint.
    
    Returns system status and key metrics.
    """
    try:
        # Basic health check
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Feedback Optimizer",
            "version": "1.0.0",
            "components": {
                "learning_engine": "active",
                "sentiment_analyzer": "active",
                "pattern_detector": "active",
                "recommendation_engine": "active"
            },
            "performance": {
                "learning_cycles_today": 0,  # Would be calculated from actual data
                "recommendations_generated_today": 0,
                "average_processing_time": 0.5  # Would be calculated from actual metrics
            }
        }
        
        return health_status
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.get("/patterns")
async def get_detected_patterns():
    """
    Get currently detected patterns and their statistics.
    
    This endpoint provides insight into what patterns the system has learned.
    """
    try:
        # Get pattern library from learning engine
        pattern_library = learning_engine.pattern_library
        
        # Convert to response format
        patterns = []
        for pattern_type, pattern_data in pattern_library.items():
            patterns.append({
                "pattern_type": pattern_type,
                "frequency": pattern_data.get('frequency', 0),
                "confidence": pattern_data.get('confidence', 0.0),
                "success_rate": pattern_data.get('success_rate', 0.0),
                "last_updated": pattern_data.get('last_updated'),
                "sentiment_impact": pattern_data.get('sentiment_impact', 0.0)
            })
        
        return {
            "patterns": patterns,
            "total_patterns": len(patterns),
            "high_confidence_patterns": len([p for p in patterns if p['confidence'] > 0.7]),
            "successful_patterns": len([p for p in patterns if p['success_rate'] > 0.6])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve patterns: {str(e)}")


@app.get("/performance-metrics")
async def get_performance_metrics():
    """
    Get performance metrics and trends.
    
    This endpoint provides insights into content performance over time.
    """
    try:
        # This would typically aggregate metrics from a database
        # For now, returning sample metrics
        metrics = {
            "overall_performance": {
                "content_quality_score": 0.72,
                "sentiment_score": 0.65,
                "engagement_rate": 0.045,
                "trend": "improving"
            },
            "content_type_performance": {
                "script": {"score": 0.75, "trend": "stable"},
                "thumbnail": {"score": 0.68, "trend": "improving"},
                "title": {"score": 0.80, "trend": "stable"}
            },
            "platform_performance": {
                "youtube": {"score": 0.70, "engagement": 0.052},
                "instagram": {"score": 0.73, "engagement": 0.038},
                "tiktok": {"score": 0.69, "engagement": 0.041}
            },
            "time_period": "last_30_days",
            "generated_at": datetime.now().isoformat()
        }
        
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve performance metrics: {str(e)}")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "available_endpoints": ["/", "/analyze", "/recommendations", "/health"]}


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "detail": str(exc)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)