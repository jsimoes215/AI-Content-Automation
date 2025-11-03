"""
Auto-Optimizer API Wrapper

Provides a simple API interface for the automated content optimization system.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import asyncio

from .auto_optimizer import AutoOptimizer
from .integration import AutoOptimizerIntegration
from ..main_pipeline import MainPipeline


class AutoOptimizerAPI:
    """API wrapper for the auto-optimizer system."""
    
    def __init__(self, pipeline: Optional[MainPipeline] = None, db_path: str = "data/content_creator.db"):
        self.db_path = db_path
        self.auto_optimizer = AutoOptimizer(db_path)
        self.integration = None
        
        # Initialize integration if pipeline provided
        if pipeline:
            self.integration = AutoOptimizerIntegration(pipeline, db_path)
        
        self.api_version = "1.0.0"
    
    def optimize_content(self, 
                        content_data: Dict[str, Any],
                        optimization_level: str = "medium",
                        platform: Optional[str] = None,
                        force_optimization: bool = False) -> Dict[str, Any]:
        """
        Optimize content using the auto-optimizer.
        
        Args:
            content_data: Content to optimize
            optimization_level: "light", "medium", or "aggressive"
            platform: Target platform (youtube, instagram, tiktok, etc.)
            force_optimization: Force optimization even if limits reached
            
        Returns:
            API response with optimized content and metadata
        """
        try:
            result = self.auto_optimizer.optimize_content(
                content_request=content_data,
                optimization_level=optimization_level,
                target_platform=platform,
                force_optimization=force_optimization
            )
            
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "data": result
            }
            
        except Exception as e:
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e),
                "data": content_data
            }
    
    def get_optimization_recommendations(self, 
                                       content_context: Dict[str, Any],
                                       include_suggestions: bool = True) -> Dict[str, Any]:
        """
        Get optimization recommendations for content.
        
        Args:
            content_context: Context of content to analyze
            include_suggestions: Include specific optimization suggestions
            
        Returns:
            API response with recommendations
        """
        try:
            result = self.auto_optimizer.get_optimization_recommendations(
                content_context=content_context,
                include_suggestions=include_suggestions
            )
            
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "data": result
            }
            
        except Exception as e:
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    def analyze_content_patterns(self, 
                               days_back: int = 30,
                               content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze content performance patterns.
        
        Args:
            days_back: Number of days to analyze
            content_type: Specific content type to analyze
            
        Returns:
            API response with pattern analysis
        """
        try:
            result = self.auto_optimizer.pattern_analyzer.analyze_performance_patterns(
                days_back=days_back,
                content_type=content_type
            )
            
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "data": result
            }
            
        except Exception as e:
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    def process_feedback_data(self, 
                            content_id: Optional[str] = None,
                            days_back: int = 30) -> Dict[str, Any]:
        """
        Process feedback data for optimization insights.
        
        Args:
            content_id: Specific content to analyze
            days_back: Number of days to analyze
            
        Returns:
            API response with feedback analysis
        """
        try:
            result = self.auto_optimizer.feedback_processor.process_feedback_data(
                content_id=content_id,
                days_back=days_back
            )
            
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "data": result
            }
            
        except Exception as e:
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    def get_learning_insights(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Get insights from the learning system.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            API response with learning insights
        """
        try:
            result = self.auto_optimizer.learning_system.get_learning_insights(days_back=days_back)
            
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "data": result
            }
            
        except Exception as e:
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        try:
            result = self.auto_optimizer.get_system_status()
            
            # Add integration status if available
            if self.integration:
                result['integration_status'] = self.integration.get_integration_status()
            
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "data": result
            }
            
        except Exception as e:
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    def optimize_existing_content(self,
                                content_id: Optional[str] = None,
                                content_ids: Optional[List[str]] = None,
                                optimization_level: str = "medium") -> Dict[str, Any]:
        """
        Optimize existing content in the system.
        
        Args:
            content_id: Specific content to optimize
            content_ids: List of contents to optimize
            optimization_level: Level of optimization to apply
            
        Returns:
            API response with optimization results
        """
        try:
            if not self.integration:
                return {
                    "api_version": self.api_version,
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": "Integration not available. Pipeline instance required.",
                    "data": {}
                }
            
            result = self.integration.optimize_existing_content(
                content_id=content_id,
                content_ids=content_ids,
                optimization_level=optimization_level
            )
            
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "data": result
            }
            
        except Exception as e:
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    def start_continuous_optimization(self, check_interval: int = 300) -> Dict[str, Any]:
        """Start continuous optimization."""
        try:
            if not self.integration:
                return {
                    "api_version": self.api_version,
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": "Integration not available. Pipeline instance required.",
                    "data": {}
                }
            
            success = self.integration.start_continuous_optimization(check_interval=check_interval)
            
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": success,
                "data": {
                    "continuous_optimization_started": success,
                    "check_interval": check_interval
                }
            }
            
        except Exception as e:
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    def stop_continuous_optimization(self) -> Dict[str, Any]:
        """Stop continuous optimization."""
        try:
            if not self.integration:
                return {
                    "api_version": self.api_version,
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": "Integration not available. Pipeline instance required.",
                    "data": {}
                }
            
            success = self.integration.stop_continuous_optimization()
            
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": success,
                "data": {
                    "continuous_optimization_stopped": success
                }
            }
            
        except Exception as e:
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    def configure_optimization(self,
                             enabled: bool = None,
                             optimization_level: str = None,
                             auto_apply: bool = None,
                             global_settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """Configure optimization system settings."""
        try:
            # Configure auto-optimizer
            if global_settings:
                for key, value in global_settings.items():
                    self.auto_optimizer.config_manager.set_global_setting(key, value)
            
            # Configure integration if available
            integration_config = {}
            if self.integration and (enabled is not None or optimization_level is not None):
                integration_config = self.integration.configure_integration(
                    enabled=enabled,
                    optimization_level=optimization_level
                )
            
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "data": {
                    "auto_optimizer_configured": True,
                    "integration_configured": integration_config,
                    "global_settings_updated": list(global_settings.keys()) if global_settings else []
                }
            }
            
        except Exception as e:
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    def export_optimization_data(self, filepath: str) -> Dict[str, Any]:
        """Export optimization system data."""
        try:
            success = self.auto_optimizer.export_system_data(filepath)
            
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": success,
                "data": {
                    "data_exported": success,
                    "export_path": filepath
                }
            }
            
        except Exception as e:
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    def import_optimization_data(self, filepath: str) -> Dict[str, Any]:
        """Import optimization system data."""
        try:
            success = self.auto_optimizer.import_system_data(filepath)
            
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": success,
                "data": {
                    "data_imported": success,
                    "import_path": filepath
                }
            }
            
        except Exception as e:
            return {
                "api_version": self.api_version,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    def get_optimization_tips(self, content_type: str = "general") -> Dict[str, Any]:
        """Get general optimization tips."""
        tips = {
            "general": [
                "Keep titles between 50-80 characters for optimal engagement",
                "Use 5-10 relevant tags to improve discoverability",
                "Post during peak hours for your audience",
                "Include a clear call-to-action in your content",
                "Test different content formats and measure performance"
            ],
            "video": [
                "Hook viewers in the first 5 seconds",
                "Use engaging thumbnails with faces and bright colors",
                "Keep videos between 3-10 minutes for best retention",
                "Add captions for accessibility",
                "End with a strong call-to-action"
            ],
            "text": [
                "Start with an attention-grabbing headline",
                "Use bullet points and short paragraphs",
                "Include relevant keywords naturally",
                "Add images or visual elements when possible",
                "End with a compelling conclusion"
            ],
            "social": [
                "Post consistently at optimal times",
                "Use trending hashtags appropriately",
                "Engage with your audience's comments",
                "Share behind-the-scenes content",
                "Cross-promote on multiple platforms"
            ]
        }
        
        content_tips = tips.get(content_type.lower(), tips["general"])
        
        return {
            "api_version": self.api_version,
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "data": {
                "content_type": content_type,
                "tips": content_tips,
                "tip_count": len(content_tips)
            }
        }


# Convenience functions for easy usage
def create_auto_optimizer(pipeline: Optional[MainPipeline] = None) -> AutoOptimizerAPI:
    """Create a new AutoOptimizerAPI instance."""
    return AutoOptimizerAPI(pipeline=pipeline)


def quick_optimize(content_data: Dict[str, Any], 
                  optimization_level: str = "medium") -> Dict[str, Any]:
    """Quick optimization without pipeline integration."""
    api = AutoOptimizerAPI()
    return api.optimize_content(content_data, optimization_level)


def get_optimization_recommendations(context: Dict[str, Any]) -> Dict[str, Any]:
    """Get quick optimization recommendations."""
    api = AutoOptimizerAPI()
    return api.get_optimization_recommendations(context)


# Example usage
if __name__ == "__main__":
    # Example content to optimize
    sample_content = {
        "content_id": "example_001",
        "title": "Basic Video",
        "content_type": "video",
        "tags": ["content", "video"],
        "platform": "youtube"
    }
    
    # Create API instance
    api = AutoOptimizerAPI()
    
    # Optimize content
    result = api.optimize_content(sample_content)
    print(json.dumps(result, indent=2))
    
    # Get recommendations
    recommendations = api.get_optimization_recommendations({
        "content_type": "video",
        "platform": "youtube"
    })
    print(json.dumps(recommendations, indent=2))