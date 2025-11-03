"""
Auto-Optimizer Integration Module

Integrates the auto-optimizer with the existing content creation pipeline.
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio
import logging

from .auto_optimizer import AutoOptimizer
from ..main_pipeline import MainPipeline


class AutoOptimizerIntegration:
    """Integration layer between auto-optimizer and content creation pipeline."""
    
    def __init__(self, pipeline: MainPipeline, db_path: str = "data/content_creator.db"):
        self.pipeline = pipeline
        self.db_path = db_path
        self.auto_optimizer = AutoOptimizer(db_path)
        self.integration_enabled = True
        self.auto_optimization_level = "medium"
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize integration
        self._initialize_integration()
    
    def _initialize_integration(self):
        """Initialize the integration between systems."""
        try:
            # Hook into pipeline events
            self._setup_pipeline_hooks()
            
            # Ensure optimization tables exist
            self._create_integration_tables()
            
            self.logger.info("Auto-optimizer integration initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize auto-optimizer integration: {e}")
            raise
    
    def _create_integration_tables(self):
        """Create additional tables for integration tracking."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Table for tracking optimization-influenced content generation
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS auto_optimization_log (
                        log_id TEXT PRIMARY KEY,
                        content_id TEXT,
                        pipeline_stage TEXT,
                        optimization_applied TEXT,
                        original_data TEXT,
                        optimized_data TEXT,
                        performance_impact REAL,
                        created_at TIMESTAMP,
                        FOREIGN KEY (content_id) REFERENCES content_items (content_id)
                    )
                """)
                
                # Table for storing optimization feedback
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS optimization_feedback (
                        feedback_id TEXT PRIMARY KEY,
                        content_id TEXT,
                        optimization_type TEXT,
                        feedback_score REAL,
                        feedback_source TEXT,
                        created_at TIMESTAMP,
                        FOREIGN KEY (content_id) REFERENCES content_items (content_id)
                    )
                """)
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error creating integration tables: {e}")
            raise
    
    def _setup_pipeline_hooks(self):
        """Set up hooks to intercept pipeline operations."""
        # Store original methods
        self._original_process_content = getattr(self.pipeline, 'process_content', None)
        self._original_generate_content = getattr(self.pipeline, 'generate_content', None)
        
        # Override pipeline methods to include optimization
        if hasattr(self.pipeline, 'process_content'):
            self.pipeline.process_content = self._optimized_process_content
        if hasattr(self.pipeline, 'generate_content'):
            self.pipeline.generate_content = self._optimized_generate_content
    
    def _optimized_process_content(self, content_request: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced process_content with automatic optimization."""
        try:
            # Get optimization recommendations before processing
            context = {
                'content_type': content_request.get('content_type', 'general'),
                'platform': content_request.get('target_platform'),
                'target_audience': content_request.get('target_audience'),
                'performance_score': content_request.get('current_performance', 0.5)
            }
            
            recommendations = self.auto_optimizer.get_optimization_recommendations(context)
            
            # Apply pre-processing optimizations if significant impact expected
            estimated_impact = recommendations.get('estimated_impact', {})
            if estimated_impact.get('estimated_improvement', 0) > 0.1:  # 10% improvement threshold
                # Optimize the request before processing
                optimized_request = self.auto_optimizer.optimize_content(
                    content_request,
                    optimization_level=self.auto_optimization_level,
                    target_platform=content_request.get('target_platform')
                )
                
                if optimized_request['optimization_applied']:
                    self.logger.info(f"Applied pre-processing optimization: {optimized_request['applied_optimizations']}")
                    content_request = optimized_request['content']
            
            # Process with original pipeline
            if self._original_process_content:
                result = self._original_process_content(content_request)
            else:
                result = content_request  # Fallback if original method not available
            
            # Apply post-processing optimizations
            post_optimization_result = self.auto_optimizer.optimize_content(
                result,
                optimization_level=self.auto_optimization_level,
                target_platform=content_request.get('target_platform')
            )
            
            # Log integration event
            self._log_integration_event(
                content_id=result.get('content_id', 'unknown'),
                pipeline_stage='process_content',
                optimization_applied=post_optimization_result['applied_optimizations'],
                original_data=content_request,
                optimized_data=post_optimization_result['content'],
                performance_impact=post_optimization_result['expected_improvement']
            )
            
            return post_optimization_result['content']
            
        except Exception as e:
            self.logger.error(f"Error in optimized process_content: {e}")
            # Fallback to original method
            return self._original_process_content(content_request) if self._original_process_content else content_request
    
    def _optimized_generate_content(self, generation_request: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced generate_content with automatic optimization."""
        try:
            # Pre-generation optimization
            pre_optimization_result = self.auto_optimizer.optimize_content(
                generation_request,
                optimization_level="light",  # Light optimization for generation
                target_platform=generation_request.get('target_platform')
            )
            
            if pre_optimization_result['optimization_applied']:
                self.logger.info(f"Applied pre-generation optimization: {pre_optimization_result['applied_optimizations']}")
                generation_request = pre_optimization_result['content']
            
            # Generate content with optimized parameters
            if self._original_generate_content:
                generated_content = self._original_generate_content(generation_request)
            else:
                # Fallback content generation
                generated_content = {
                    'content_id': generation_request.get('content_id', f"gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                    'title': generation_request.get('title', 'Generated Content'),
                    'content': f"Optimized content for: {generation_request.get('title', 'Unknown')}",
                    'generation_request': generation_request,
                    'generated_at': datetime.now().isoformat()
                }
            
            # Post-generation optimization
            post_optimization_result = self.auto_optimizer.optimize_content(
                generated_content,
                optimization_level=self.auto_optimization_level,
                target_platform=generation_request.get('target_platform')
            )
            
            # Log integration event
            self._log_integration_event(
                content_id=generated_content.get('content_id', 'unknown'),
                pipeline_stage='generate_content',
                optimization_applied=post_optimization_result['applied_optimizations'],
                original_data=generation_request,
                optimized_data=post_optimization_result['content'],
                performance_impact=post_optimization_result['expected_improvement']
            )
            
            return post_optimization_result['content']
            
        except Exception as e:
            self.logger.error(f"Error in optimized generate_content: {e}")
            # Fallback to original method
            return self._original_generate_content(generation_request) if self._original_generate_content else generation_request
    
    def optimize_existing_content(self, 
                                content_id: Optional[str] = None,
                                content_ids: Optional[List[str]] = None,
                                optimization_level: str = "medium") -> Dict[str, Any]:
        """
        Optimize existing content in the system.
        
        Args:
            content_id: Specific content to optimize
            content_ids: List of specific contents to optimize
            optimization_level: Level of optimization to apply
            
        Returns:
            Dictionary containing optimization results
        """
        results = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build query based on parameters
                if content_ids:
                    placeholders = ','.join(['?' for _ in content_ids])
                    query = f"SELECT * FROM content_items WHERE content_id IN ({placeholders})"
                    cursor.execute(query, content_ids)
                elif content_id:
                    query = "SELECT * FROM content_items WHERE content_id = ?"
                    cursor.execute(query, [content_id])
                else:
                    # Get all content without recent optimization
                    query = """
                    SELECT * FROM content_items 
                    WHERE performance_score < 0.8 
                       OR optimized_at IS NULL 
                       OR optimized_at < datetime('now', '-7 days')
                    ORDER BY performance_score ASC
                    LIMIT 20
                    """
                    cursor.execute(query)
                
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                for row in rows:
                    content_data = dict(zip(columns, row))
                    
                    # Parse JSON fields
                    if content_data.get('tags'):
                        try:
                            content_data['tags'] = json.loads(content_data['tags'])
                        except json.JSONDecodeError:
                            content_data['tags'] = []
                    
                    # Optimize the content
                    optimization_result = self.auto_optimizer.optimize_content(
                        content_data,
                        optimization_level=optimization_level,
                        target_platform=None,  # Would need platform detection
                        force_optimization=True
                    )
                    
                    if optimization_result['optimization_applied']:
                        # Update the content in database
                        self._update_content_in_db(content_data['content_id'], optimization_result)
                        
                        results.append({
                            'content_id': content_data['content_id'],
                            'optimization_applied': True,
                            'optimizations': optimization_result['applied_optimizations'],
                            'confidence': optimization_result['confidence_score'],
                            'expected_improvement': optimization_result['expected_improvement']
                        })
                    else:
                        results.append({
                            'content_id': content_data['content_id'],
                            'optimization_applied': False,
                            'reason': optimization_result.get('reason', 'Unknown')
                        })
            
            return {
                'optimization_timestamp': datetime.now().isoformat(),
                'total_content_processed': len(results),
                'optimizations_applied': len([r for r in results if r.get('optimization_applied')]),
                'results': results
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing existing content: {e}")
            return {'error': str(e)}
    
    def track_optimization_performance(self, content_id: str, performance_data: Dict[str, Any]) -> bool:
        """
        Track the performance impact of optimizations.
        
        Args:
            content_id: Content that was optimized
            performance_data: Performance metrics after optimization
            
        Returns:
            Success status
        """
        try:
            feedback_id = f"perf_{content_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO optimization_feedback 
                    (feedback_id, content_id, optimization_type, feedback_score, feedback_source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    feedback_id,
                    content_id,
                    'performance_tracking',
                    performance_data.get('improvement_score', 0),
                    'auto_performance_tracking',
                    datetime.now().isoformat()
                ))
                
                conn.commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error tracking optimization performance: {e}")
            return False
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of the integration between auto-optimizer and pipeline."""
        try:
            # Get auto-optimizer status
            optimizer_status = self.auto_optimizer.get_system_status()
            
            # Get integration-specific metrics
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count recent optimizations
                cursor.execute("""
                    SELECT COUNT(*) FROM auto_optimization_log 
                    WHERE created_at > datetime('now', '-24 hours')
                """)
                daily_optimizations = cursor.fetchone()[0]
                
                # Count total optimizations
                cursor.execute("SELECT COUNT(*) FROM auto_optimization_log")
                total_optimizations = cursor.fetchone()[0]
                
                # Get average performance improvement
                cursor.execute("""
                    SELECT AVG(performance_impact) FROM auto_optimization_log 
                    WHERE performance_impact IS NOT NULL
                """)
                avg_improvement = cursor.fetchone()[0] or 0
            
            return {
                'integration_enabled': self.integration_enabled,
                'auto_optimization_level': self.auto_optimization_level,
                'pipeline_integration': {
                    'process_content_hooked': hasattr(self.pipeline, '_optimized_process_content'),
                    'generate_content_hooked': hasattr(self.pipeline, '_optimized_generate_content')
                },
                'optimization_metrics': {
                    'daily_optimizations': daily_optimizations,
                    'total_optimizations': total_optimizations,
                    'average_performance_impact': avg_improvement
                },
                'auto_optimizer_status': optimizer_status
            }
            
        except Exception as e:
            self.logger.error(f"Error getting integration status: {e}")
            return {
                'integration_enabled': self.integration_enabled,
                'error': str(e)
            }
    
    def configure_integration(self, 
                            enabled: bool = None,
                            optimization_level: str = None,
                            auto_apply_recommendations: bool = None) -> Dict[str, Any]:
        """Configure integration settings."""
        try:
            if enabled is not None:
                self.integration_enabled = enabled
            
            if optimization_level is not None:
                self.auto_optimization_level = optimization_level
            
            # Store configuration in auto-optimizer
            if auto_apply_recommendations is not None:
                self.auto_optimizer.config_manager.set_global_setting(
                    'auto_apply_recommendations', 
                    auto_apply_recommendations
                )
            
            return {
                'integration_enabled': self.integration_enabled,
                'auto_optimization_level': self.auto_optimization_level,
                'configured_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error configuring integration: {e}")
            return {'error': str(e)}
    
    def _log_integration_event(self, 
                             content_id: str,
                             pipeline_stage: str,
                             optimization_applied: List[str],
                             original_data: Dict[str, Any],
                             optimized_data: Dict[str, Any],
                             performance_impact: float):
        """Log integration event to database."""
        try:
            log_id = f"log_{content_id}_{pipeline_stage}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO auto_optimization_log 
                    (log_id, content_id, pipeline_stage, optimization_applied, 
                     original_data, optimized_data, performance_impact, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_id,
                    content_id,
                    pipeline_stage,
                    '; '.join(optimization_applied),
                    json.dumps(original_data, default=str),
                    json.dumps(optimized_data, default=str),
                    performance_impact,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error logging integration event: {e}")
    
    def _update_content_in_db(self, content_id: str, optimization_result: Dict[str, Any]):
        """Update content in database with optimization results."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update the content
                optimized_content = optimization_result['content']
                cursor.execute("""
                    UPDATE content_items 
                    SET title = ?, tags = ?, optimized_at = ?, 
                        optimization_applied = ?, optimization_success = ?
                    WHERE content_id = ?
                """, (
                    optimized_content.get('title', ''),
                    json.dumps(optimized_content.get('tags', [])),
                    optimization_result['applied_at'],
                    '; '.join(optimization_result['applied_optimizations']),
                    optimization_result['confidence_score'],
                    content_id
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error updating content in database: {e}")
    
    def start_continuous_optimization(self, check_interval: int = 300) -> bool:
        """Start continuous optimization in background."""
        try:
            if hasattr(self, '_continuous_task') and not self._continuous_task.done():
                self.logger.warning("Continuous optimization already running")
                return False
            
            # Start background task
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._continuous_task = loop.create_task(
                    self.auto_optimizer.run_continuous_optimization(check_interval)
                )
                self.logger.info(f"Started continuous optimization with {check_interval}s intervals")
                return True
            else:
                self.logger.error("No active event loop for continuous optimization")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting continuous optimization: {e}")
            return False
    
    def stop_continuous_optimization(self) -> bool:
        """Stop continuous optimization."""
        try:
            self.auto_optimizer.stop_continuous_optimization()
            if hasattr(self, '_continuous_task') and not self._continuous_task.done():
                self._continuous_task.cancel()
                self.logger.info("Stopped continuous optimization")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping continuous optimization: {e}")
            return False