"""
Auto Optimizer Main Module

Main orchestrator for the automated content optimization system.
Integrates pattern analysis, feedback processing, optimization engine, 
learning system, and configuration management.
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from .pattern_analyzer import PatternAnalyzer
from .feedback_processor import FeedbackProcessor
from .optimizer_engine import OptimizerEngine, OptimizationResult
from .learning_system import LearningSystem
from .config_manager import ConfigManager


class AutoOptimizer:
    """Main auto-optimizer class that orchestrates the entire system."""
    
    def __init__(self, db_path: str = "data/content_creator.db", config_dir: str = "config"):
        self.db_path = db_path
        self.pattern_analyzer = PatternAnalyzer(db_path)
        self.feedback_processor = FeedbackProcessor(db_path)
        self.optimizer_engine = OptimizerEngine(db_path)
        self.learning_system = LearningSystem(db_path)
        self.config_manager = ConfigManager(config_dir)
        
        # System state
        self.is_running = False
        self.last_analysis_time = None
        self.optimization_history = []
        self.performance_metrics = {}
        
        # Initialize system
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the auto-optimizer system."""
        try:
            # Ensure database tables exist
            self._ensure_database_tables()
            
            # Load configurations
            self._load_system_configurations()
            
            # Run initial analysis
            self._run_initial_analysis()
            
            print("Auto-optimizer system initialized successfully")
            
        except Exception as e:
            print(f"Error initializing auto-optimizer: {e}")
            raise
    
    def _ensure_database_tables(self):
        """Ensure necessary database tables exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create content_items table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS content_items (
                        content_id TEXT PRIMARY KEY,
                        content_type TEXT,
                        title TEXT,
                        tags TEXT,
                        metrics_views INTEGER DEFAULT 0,
                        metrics_likes INTEGER DEFAULT 0,
                        metrics_comments INTEGER DEFAULT 0,
                        metrics_shares INTEGER DEFAULT 0,
                        performance_score REAL,
                        created_at TIMESTAMP,
                        optimized_at TIMESTAMP,
                        optimization_applied TEXT,
                        optimization_success REAL
                    )
                """)
                
                # Create optimization_events table for learning
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS optimization_events (
                        event_id TEXT PRIMARY KEY,
                        content_id TEXT,
                        optimization_type TEXT,
                        optimization_details TEXT,
                        performance_before REAL,
                        performance_after REAL,
                        improvement REAL,
                        success BOOLEAN,
                        created_at TIMESTAMP,
                        FOREIGN KEY (content_id) REFERENCES content_items (content_id)
                    )
                """)
                
                # Create feedback_data table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS feedback_data (
                        feedback_id TEXT PRIMARY KEY,
                        content_id TEXT,
                        feedback_type TEXT,
                        sentiment_score REAL,
                        feedback_text TEXT,
                        created_at TIMESTAMP,
                        FOREIGN KEY (content_id) REFERENCES content_items (content_id)
                    )
                """)
                
                conn.commit()
                
        except Exception as e:
            print(f"Error creating database tables: {e}")
            raise
    
    def _load_system_configurations(self):
        """Load system configurations and settings."""
        # Set global settings based on configuration manager
        global_settings = self.config_manager.global_settings
        
        # Apply global settings to system components
        self.pattern_analyzer.cache_duration = global_settings.get('pattern_cache_duration', 3600)
        self.learning_system.learning_rate = global_settings.get('learning_rate', 0.01)
        self.optimizer_engine.default_optimization_level = global_settings.get('default_optimization_level', 'medium')
        
    def _run_initial_analysis(self):
        """Run initial pattern analysis and feedback processing."""
        try:
            # Analyze patterns
            patterns = self.pattern_analyzer.get_pattern_update()
            
            # Process feedback
            feedback = self.feedback_processor.process_feedback_data()
            
            self.last_analysis_time = datetime.now()
            
            print("Initial analysis completed")
            
        except Exception as e:
            print(f"Error in initial analysis: {e}")
    
    def optimize_content(self, 
                        content_request: Dict[str, Any],
                        optimization_level: str = "medium",
                        target_platform: Optional[str] = None,
                        force_optimization: bool = False) -> Dict[str, Any]:
        """
        Optimize content using the complete optimization pipeline.
        
        Args:
            content_request: Content to optimize
            optimization_level: Level of optimization (light, medium, aggressive)
            target_platform: Target platform for optimization
            force_optimization: Force optimization even if limits are reached
            
        Returns:
            Dictionary containing optimized content and optimization metadata
        """
        try:
            # Prepare context for optimization
            context = self._prepare_optimization_context(content_request, target_platform)
            
            # Check if optimization should proceed
            if not force_optimization and not self._should_optimize(context):
                return {
                    "content": content_request,
                    "optimization_applied": False,
                    "reason": "Optimization criteria not met or limits reached",
                    "context": context
                }
            
            # Run optimization
            optimization_result = self.optimizer_engine.optimize_content(
                content_request=content_request,
                target_platform=target_platform,
                optimization_level=optimization_level
            )
            
            # Record learning event
            if self.config_manager.get_global_setting('auto_learning_enabled', True):
                self._record_learning_event(optimization_result, context)
            
            # Update usage counters
            self._update_usage_counters(context)
            
            # Prepare response
            response = {
                "content": optimization_result.optimized_content,
                "optimization_applied": True,
                "applied_optimizations": optimization_result.applied_optimizations,
                "confidence_score": optimization_result.confidence_score,
                "expected_improvement": optimization_result.expected_improvement,
                "applied_at": optimization_result.applied_at.isoformat(),
                "context": context,
                "recommendations": self.optimizer_engine.get_optimization_suggestions(content_request)
            }
            
            # Log optimization
            self.optimization_history.append({
                "timestamp": optimization_result.applied_at.isoformat(),
                "content_id": content_request.get('content_id', 'unknown'),
                "optimizations": optimization_result.applied_optimizations,
                "confidence": optimization_result.confidence_score,
                "expected_improvement": optimization_result.expected_improvement
            })
            
            return response
            
        except Exception as e:
            return {
                "content": content_request,
                "optimization_applied": False,
                "error": f"Optimization failed: {str(e)}",
                "context": context if 'context' in locals() else {}
            }
    
    def get_optimization_recommendations(self, 
                                       content_context: Dict[str, Any],
                                       include_suggestions: bool = True) -> Dict[str, Any]:
        """
        Get optimization recommendations based on learned patterns.
        
        Args:
            content_context: Context of content to analyze
            include_suggestions: Include specific optimization suggestions
            
        Returns:
            Dictionary containing recommendations and insights
        """
        try:
            # Get recommendations from learning system
            recommendations = self.learning_system.get_optimization_recommendations(content_context)
            
            # Get pattern-based insights
            patterns = self.pattern_analyzer.get_pattern_update()
            
            # Get feedback insights
            feedback = self.feedback_processor.process_feedback_data()
            
            # Generate combined response
            response = {
                "analysis_timestamp": datetime.now().isoformat(),
                "content_context": content_context,
                "recommendations": recommendations,
                "pattern_insights": patterns.get('insights', []) if patterns else [],
                "feedback_insights": feedback.get('actionable_insights', []) if 'actionable_insights' in feedback else [],
                "optimization_priority": self._calculate_optimization_priority(content_context),
                "estimated_impact": self._estimate_optimization_impact(content_context, recommendations)
            }
            
            # Include specific suggestions if requested
            if include_suggestions and hasattr(self.optimizer_engine, 'get_optimization_suggestions'):
                mock_content = {"title": "", "tags": [], "content_type": content_context.get('content_type', 'general')}
                response["specific_suggestions"] = self.optimizer_engine.get_optimization_suggestions(mock_content)
            
            return response
            
        except Exception as e:
            return {
                "error": f"Failed to generate recommendations: {str(e)}",
                "content_context": content_context
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and performance metrics."""
        try:
            # Get configuration summary
            config_summary = self.config_manager.get_configuration_summary()
            
            # Get learning insights
            learning_insights = self.learning_system.get_learning_insights()
            
            # Get recent optimization history
            recent_optimizations = self.optimization_history[-10:] if self.optimization_history else []
            
            # Calculate performance metrics
            if recent_optimizations:
                avg_confidence = sum(opt['confidence'] for opt in recent_optimizations) / len(recent_optimizations)
                avg_improvement = sum(opt['expected_improvement'] for opt in recent_optimizations) / len(recent_optimizations)
            else:
                avg_confidence = 0
                avg_improvement = 0
            
            return {
                "system_status": {
                    "is_running": self.is_running,
                    "last_analysis": self.last_analysis_time.isoformat() if self.last_analysis_time else None,
                    "total_optimizations": len(self.optimization_history),
                    "average_confidence": avg_confidence,
                    "average_expected_improvement": avg_improvement
                },
                "configuration": config_summary,
                "learning_insights": learning_insights,
                "recent_optimizations": recent_optimizations,
                "system_health": self._assess_system_health()
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get system status: {str(e)}",
                "system_status": {"is_running": self.is_running, "error": True}
            }
    
    async def run_continuous_optimization(self, 
                                        check_interval: int = 300,
                                        max_optimizations_per_hour: int = 10):
        """
        Run continuous optimization in the background.
        
        Args:
            check_interval: Seconds between optimization checks
            max_optimizations_per_hour: Maximum optimizations per hour
        """
        self.is_running = True
        print(f"Starting continuous optimization with {check_interval}s intervals")
        
        optimization_count_this_hour = 0
        hour_start = datetime.now()
        
        try:
            while self.is_running:
                current_time = datetime.now()
                
                # Reset hourly counter if needed
                if (current_time - hour_start).total_seconds() >= 3600:
                    optimization_count_this_hour = 0
                    hour_start = current_time
                
                # Check if we can perform more optimizations this hour
                if optimization_count_this_hour < max_optimizations_per_hour:
                    # Find content that needs optimization
                    candidates = self._find_optimization_candidates()
                    
                    for candidate in candidates:
                        if optimization_count_this_hour >= max_optimizations_per_hour:
                            break
                        
                        try:
                            result = self.optimize_content(candidate, optimization_level="medium")
                            
                            if result["optimization_applied"]:
                                optimization_count_this_hour += 1
                                print(f"Optimized content: {candidate.get('content_id', 'unknown')}")
                            
                        except Exception as e:
                            print(f"Error optimizing content: {e}")
                            continue
                
                # Wait for next check
                await asyncio.sleep(check_interval)
                
        except Exception as e:
            print(f"Error in continuous optimization: {e}")
        finally:
            self.is_running = False
            print("Continuous optimization stopped")
    
    def stop_continuous_optimization(self):
        """Stop continuous optimization."""
        self.is_running = False
    
    def export_system_data(self, filepath: str) -> bool:
        """Export all system data for backup or analysis."""
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "system_configurations": self.config_manager.export_configuration(filepath + "_configs.json"),
                "learning_data": self.learning_system.export_learning_data(),
                "optimization_history": self.optimization_history,
                "performance_metrics": self.performance_metrics
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting system data: {e}")
            return False
    
    def import_system_data(self, filepath: str) -> bool:
        """Import system data from backup."""
        try:
            with open(filepath, 'r') as f:
                import_data = json.load(f)
            
            # Import configurations
            if "system_configurations" in import_data:
                self.config_manager.import_configuration(filepath + "_configs.json")
            
            # Import learning data
            if "learning_data" in import_data:
                self.learning_system.import_learning_data(import_data["learning_data"])
            
            # Import optimization history
            if "optimization_history" in import_data:
                self.optimization_history = import_data["optimization_history"]
            
            # Import performance metrics
            if "performance_metrics" in import_data:
                self.performance_metrics = import_data["performance_metrics"]
            
            return True
        except Exception as e:
            print(f"Error importing system data: {e}")
            return False
    
    def _prepare_optimization_context(self, content_request: Dict[str, Any], platform: Optional[str]) -> Dict[str, Any]:
        """Prepare context for optimization decisions."""
        context = {
            "content_id": content_request.get('content_id', f"content_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            "content_type": content_request.get('content_type', 'general'),
            "platform": platform,
            "timestamp": datetime.now().isoformat(),
            "current_performance": content_request.get('performance_score', 0.5)
        }
        
        return context
    
    def _should_optimize(self, context: Dict[str, Any]) -> bool:
        """Determine if content should be optimized."""
        # Check if optimization is enabled globally
        if not self.config_manager.get_global_setting('optimization_enabled', True):
            return False
        
        # Check optimization limits
        active_configs = self.config_manager.get_active_optimizations(context)
        if not active_configs:
            return False
        
        # Check daily limits
        daily_limit = self.config_manager.get_global_setting('daily_optimization_limit', 50)
        current_daily = len([h for h in self.optimization_history 
                           if h['timestamp'].startswith(datetime.now().strftime('%Y-%m-%d'))])
        
        if current_daily >= daily_limit:
            return False
        
        # Check if content performance is low (needs improvement)
        performance_score = context.get('current_performance', 0.5)
        min_performance_threshold = self.config_manager.get_global_setting('min_improvement_threshold', 0.05)
        
        return performance_score < (1.0 - min_performance_threshold)
    
    def _record_learning_event(self, optimization_result: OptimizationResult, context: Dict[str, Any]):
        """Record learning event for the learning system."""
        try:
            # For demonstration, we'll use mock before/after performance
            performance_before = context.get('current_performance', 0.5)
            performance_after = min(1.0, performance_before + optimization_result.expected_improvement)
            
            # Record the event
            event_id = self.learning_system.record_learning_event(
                content_id=context['content_id'],
                optimization_applied="; ".join(optimization_result.applied_optimizations),
                performance_before=performance_before,
                performance_after=performance_after,
                context=context
            )
            
        except Exception as e:
            print(f"Error recording learning event: {e}")
    
    def _update_usage_counters(self, context: Dict[str, Any]):
        """Update usage counters for optimization configurations."""
        try:
            active_configs = self.config_manager.get_active_optimizations(context)
            
            for config in active_configs:
                if config.auto_apply:
                    self.config_manager.increment_usage(config.name)
                    
        except Exception as e:
            print(f"Error updating usage counters: {e}")
    
    def _find_optimization_candidates(self) -> List[Dict[str, Any]]:
        """Find content that would benefit from optimization."""
        candidates = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Find content with low performance that hasn't been optimized recently
                cursor.execute("""
                    SELECT content_id, content_type, title, tags, performance_score, created_at
                    FROM content_items 
                    WHERE performance_score < 0.6 
                      AND (optimized_at IS NULL OR optimized_at < datetime('now', '-7 days'))
                    ORDER BY performance_score ASC
                    LIMIT 10
                """)
                
                rows = cursor.fetchall()
                
                for row in rows:
                    candidate = {
                        'content_id': row[0],
                        'content_type': row[1],
                        'title': row[2],
                        'tags': json.loads(row[3]) if row[3] else [],
                        'performance_score': row[4] or 0.5,
                        'created_at': row[5]
                    }
                    candidates.append(candidate)
                    
        except Exception as e:
            print(f"Error finding optimization candidates: {e}")
        
        return candidates
    
    def _calculate_optimization_priority(self, context: Dict[str, Any]) -> str:
        """Calculate optimization priority for content."""
        performance_score = context.get('current_performance', 0.5)
        
        if performance_score < 0.3:
            return "critical"
        elif performance_score < 0.5:
            return "high"
        elif performance_score < 0.7:
            return "medium"
        else:
            return "low"
    
    def _estimate_optimization_impact(self, context: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate potential impact of optimizations."""
        if not recommendations:
            return {"estimated_improvement": 0, "confidence": 0}
        
        total_expected_improvement = sum(rec.get('expected_improvement', 0) for rec in recommendations)
        avg_confidence = sum(rec.get('confidence', 0) for rec in recommendations) / len(recommendations)
        
        return {
            "estimated_improvement": min(0.5, total_expected_improvement),  # Cap at 50%
            "confidence": avg_confidence,
            "recommendation_count": len(recommendations)
        }
    
    def _assess_system_health(self) -> Dict[str, Any]:
        """Assess the overall health of the optimization system."""
        health_status = {
            "status": "healthy",
            "components": {},
            "issues": [],
            "recommendations": []
        }
        
        # Check component health
        try:
            # Check pattern analyzer
            patterns = self.pattern_analyzer.get_pattern_update()
            health_status["components"]["pattern_analyzer"] = "healthy" if patterns else "warning"
            
            # Check feedback processor
            feedback = self.feedback_processor.process_feedback_data()
            health_status["components"]["feedback_processor"] = "healthy" if "error" not in feedback else "warning"
            
            # Check learning system
            if hasattr(self.learning_system, 'learning_events'):
                event_count = len(self.learning_system.learning_events)
                health_status["components"]["learning_system"] = "healthy" if event_count > 0 else "warning"
            
            # Check configuration manager
            config_summary = self.config_manager.get_configuration_summary()
            health_status["components"]["config_manager"] = "healthy" if config_summary else "warning"
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["issues"].append(f"Component check failed: {e}")
        
        # Overall assessment
        warning_components = [name for name, status in health_status["components"].items() if status == "warning"]
        error_components = [name for name, status in health_status["components"].items() if status == "error"]
        
        if error_components:
            health_status["status"] = "unhealthy"
            health_status["issues"].extend([f"{comp} is in error state" for comp in error_components])
        elif warning_components:
            health_status["status"] = "warning"
            health_status["issues"].extend([f"{comp} needs attention" for comp in warning_components])
        
        # Generate recommendations
        if health_status["status"] == "warning":
            health_status["recommendations"].append("Review system logs for detailed error information")
        elif health_status["status"] == "unhealthy":
            health_status["recommendations"].append("Check database connectivity and configuration files")
        
        return health_status