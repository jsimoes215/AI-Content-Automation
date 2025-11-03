"""
Learning System Module

Continuously learns from optimization results and feedback to improve future optimizations.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics
import math
import pickle


@dataclass
class LearningEvent:
    """Represents a learning event from optimization and performance."""
    event_id: str
    content_id: str
    optimization_applied: str
    performance_before: float
    performance_after: float
    improvement: float
    timestamp: datetime
    success: bool
    context: Dict[str, Any]  # Additional context like platform, content type, etc.


@dataclass
class ModelParameters:
    """Parameters for the learning model."""
    optimization_type: str
    weights: Dict[str, float]
    bias: float
    success_threshold: float
    total_events: int = 0
    successful_events: int = 0


class LearningSystem:
    """Continuous learning system that improves optimization strategies."""
    
    def __init__(self, db_path: str = "data/content_creator.db"):
        self.db_path = db_path
        self.learning_events = deque(maxlen=1000)  # Keep last 1000 events
        self.model_parameters = {}
        self.performance_history = defaultdict(deque)
        self.update_frequency = 100  # Update model every 100 events
        self.learning_rate = 0.01
        self.min_samples = 10
        
        # Initialize model parameters
        self._initialize_models()
        
    def record_learning_event(self, 
                            content_id: str,
                            optimization_applied: str,
                            performance_before: float,
                            performance_after: float,
                            context: Dict[str, Any] = None) -> str:
        """
        Record a learning event from optimization results.
        
        Args:
            content_id: ID of the content that was optimized
            optimization_applied: Description of optimization applied
            performance_before: Performance score before optimization
            performance_after: Performance score after optimization
            context: Additional context (platform, content type, etc.)
            
        Returns:
            Generated event ID
        """
        event_id = f"event_{len(self.learning_events)}"
        improvement = performance_after - performance_before
        success = improvement > 0.05  # 5% improvement threshold
        
        event = LearningEvent(
            event_id=event_id,
            content_id=content_id,
            optimization_applied=optimization_applied,
            performance_before=performance_before,
            performance_after=performance_after,
            improvement=improvement,
            timestamp=datetime.now(),
            success=success,
            context=context or {}
        )
        
        self.learning_events.append(event)
        self._update_performance_history(event)
        
        # Update model if enough events accumulated
        if len(self.learning_events) % self.update_frequency == 0:
            self._update_models()
        
        return event_id
    
    def get_optimization_recommendations(self, 
                                       content_context: Dict[str, Any],
                                       target_improvement: float = 0.1) -> List[Dict[str, Any]]:
        """
        Get optimization recommendations based on learned patterns.
        
        Args:
            content_context: Context of content to optimize
            target_improvement: Desired improvement target
            
        Returns:
            List of recommended optimizations with confidence scores
        """
        recommendations = []
        
        # Analyze historical performance for similar content
        similar_events = self._find_similar_events(content_context)
        
        if similar_events:
            # Calculate success rates for each optimization type
            optimization_performance = self._calculate_optimization_performance(similar_events)
            
            # Generate recommendations based on learned patterns
            for opt_type, performance in optimization_performance.items():
                if performance['success_rate'] > 0.5 and performance['avg_improvement'] > 0.05:
                    confidence = min(0.95, performance['success_rate'])
                    expected_improvement = performance['avg_improvement']
                    
                    recommendations.append({
                        'optimization_type': opt_type,
                        'confidence': confidence,
                        'expected_improvement': expected_improvement,
                        'success_rate': performance['success_rate'],
                        'sample_size': performance['sample_count'],
                        'evidence': self._generate_evidence_summary(opt_type, similar_events)
                    })
        
        # Sort by confidence and expected improvement
        recommendations.sort(key=lambda x: (x['confidence'] * x['expected_improvement']), reverse=True)
        
        # Limit to top recommendations
        return recommendations[:5]
    
    def update_optimization_strategy(self, 
                                   strategy_name: str,
                                   new_data: Dict[str, Any]) -> bool:
        """
        Update optimization strategy based on new learning data.
        
        Args:
            strategy_name: Name of strategy to update
            new_data: New performance data to incorporate
            
        Returns:
            Success status
        """
        try:
            # Update model parameters based on new data
            if strategy_name in self.model_parameters:
                model = self.model_parameters[strategy_name]
                
                # Incorporate new evidence
                if 'success_rate' in new_data:
                    model.successful_events += 1 if new_data['success'] else 0
                    model.total_events += 1
                    
                    # Update success threshold based on performance
                    if new_data['performance_after'] > new_data['performance_before']:
                        model.success_threshold = min(0.95, model.success_threshold + 0.01)
                    else:
                        model.success_threshold = max(0.1, model.success_threshold - 0.01)
                
                # Adjust weights based on context
                if 'context' in new_data:
                    self._adjust_weights(model, new_data['context'], new_data['improvement'])
                
                return True
        except Exception as e:
            print(f"Error updating strategy: {e}")
            return False
        
        return False
    
    def get_learning_insights(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Generate insights from the learning process.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Dictionary containing learning insights
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_events = [event for event in self.learning_events 
                        if event.timestamp >= cutoff_date]
        
        if not recent_events:
            return {"error": "No recent learning events available"}
        
        # Calculate overall learning metrics
        total_improvements = [event.improvement for event in recent_events]
        success_rate = sum(1 for event in recent_events if event.success) / len(recent_events)
        
        # Analyze by optimization type
        optimization_insights = self._analyze_optimization_types(recent_events)
        
        # Analyze by content context
        context_insights = self._analyze_content_contexts(recent_events)
        
        # Calculate learning trends
        learning_trends = self._calculate_learning_trends(recent_events)
        
        return {
            'analysis_period_days': days_back,
            'total_events': len(recent_events),
            'overall_success_rate': success_rate,
            'average_improvement': statistics.mean(total_improvements),
            'improvement_std': statistics.stdev(total_improvements) if len(total_improvements) > 1 else 0,
            'optimization_insights': optimization_insights,
            'context_insights': context_insights,
            'learning_trends': learning_trends,
            'top_performing_optimizations': self._get_top_optimizations(recent_events),
            'learning_recommendations': self._generate_learning_recommendations(recent_events)
        }
    
    def export_learning_data(self) -> Dict[str, Any]:
        """Export learning data for external analysis."""
        return {
            'model_parameters': {k: asdict(v) for k, v in self.model_parameters.items()},
            'learning_events': [asdict(event) for event in list(self.learning_events)],
            'performance_history': {k: list(v) for k, v in self.performance_history.items()},
            'export_timestamp': datetime.now().isoformat(),
            'total_events': len(self.learning_events)
        }
    
    def import_learning_data(self, learning_data: Dict[str, Any]) -> bool:
        """Import learning data from external source."""
        try:
            if 'model_parameters' in learning_data:
                for name, params_data in learning_data['model_parameters'].items():
                    self.model_parameters[name] = ModelParameters(**params_data)
            
            if 'learning_events' in learning_data:
                for event_data in learning_data['learning_events']:
                    event_data['timestamp'] = datetime.fromisoformat(event_data['timestamp'])
                    self.learning_events.append(LearningEvent(**event_data))
            
            if 'performance_history' in learning_data:
                for key, history in learning_data['performance_history'].items():
                    self.performance_history[key] = deque(history, maxlen=100)
            
            return True
        except Exception as e:
            print(f"Error importing learning data: {e}")
            return False
    
    def _initialize_models(self):
        """Initialize learning models for different optimization types."""
        model_types = [
            'title_optimization',
            'tag_optimization', 
            'timing_optimization',
            'content_length',
            'engagement_hook',
            'platform_specific'
        ]
        
        for model_type in model_types:
            self.model_parameters[model_type] = ModelParameters(
                optimization_type=model_type,
                weights={'confidence': 0.5, 'success_rate': 0.3, 'sample_size': 0.2},
                bias=0.1,
                success_threshold=0.6
            )
    
    def _update_performance_history(self, event: LearningEvent):
        """Update performance history for trend analysis."""
        key = f"{event.optimization_applied}_{event.context.get('platform', 'general')}"
        self.performance_history[key].append({
            'timestamp': event.timestamp,
            'improvement': event.improvement,
            'success': event.success
        })
    
    def _update_models(self):
        """Update learning models based on accumulated events."""
        # Group events by optimization type
        events_by_type = defaultdict(list)
        for event in self.learning_events:
            events_by_type[event.optimization_applied].append(event)
        
        for opt_type, events in events_by_type.items():
            if len(events) >= self.min_samples:
                self._update_single_model(opt_type, events)
    
    def _update_single_model(self, opt_type: str, events: List[LearningEvent]):
        """Update a single optimization model."""
        if opt_type not in self.model_parameters:
            return
        
        model = self.model_parameters[opt_type]
        
        # Calculate new statistics
        improvements = [event.improvement for event in events]
        success_count = sum(1 for event in events if event.success)
        
        # Update success threshold
        if improvements:
            avg_improvement = statistics.mean(improvements)
            model.success_threshold = max(0.1, min(0.95, avg_improvement))
        
        # Adjust weights based on recent performance
        recent_success_rate = success_count / len(events)
        if recent_success_rate > model.success_threshold:
            model.bias = min(0.9, model.bias + self.learning_rate)
        else:
            model.bias = max(0.1, model.bias - self.learning_rate)
    
    def _find_similar_events(self, context: Dict[str, Any]) -> List[LearningEvent]:
        """Find events similar to the given context."""
        similar_events = []
        
        for event in self.learning_events:
            # Calculate similarity score
            similarity = self._calculate_context_similarity(event.context, context)
            
            if similarity > 0.5:  # Threshold for similarity
                similar_events.append(event)
        
        return similar_events
    
    def _calculate_context_similarity(self, event_context: Dict[str, Any], target_context: Dict[str, Any]) -> float:
        """Calculate similarity between contexts."""
        if not event_context or not target_context:
            return 0.0
        
        # Check for exact matches on key attributes
        key_attributes = ['content_type', 'platform', 'target_audience']
        matches = 0
        total_attributes = len(key_attributes)
        
        for attr in key_attributes:
            if (event_context.get(attr) == target_context.get(attr) and
                event_context.get(attr) is not None):
                matches += 1
        
        return matches / total_attributes if total_attributes > 0 else 0.0
    
    def _calculate_optimization_performance(self, events: List[LearningEvent]) -> Dict[str, Any]:
        """Calculate performance statistics for optimizations."""
        performance = {}
        
        # Group by optimization type
        opt_groups = defaultdict(list)
        for event in events:
            opt_groups[event.optimization_applied].append(event)
        
        for opt_type, opt_events in opt_groups.items():
            if len(opt_events) >= 3:  # Minimum sample size
                improvements = [event.improvement for event in opt_events]
                successes = sum(1 for event in opt_events if event.success)
                
                performance[opt_type] = {
                    'avg_improvement': statistics.mean(improvements),
                    'success_rate': successes / len(opt_events),
                    'sample_count': len(opt_events),
                    'max_improvement': max(improvements),
                    'min_improvement': min(improvements),
                    'improvement_std': statistics.stdev(improvements) if len(improvements) > 1 else 0
                }
        
        return performance
    
    def _generate_evidence_summary(self, opt_type: str, events: List[LearningEvent]) -> str:
        """Generate summary of evidence for optimization recommendation."""
        opt_events = [event for event in events if event.optimization_applied == opt_type]
        
        if not opt_events:
            return "No direct evidence available"
        
        successes = sum(1 for event in opt_events if event.success)
        avg_improvement = statistics.mean([event.improvement for event in opt_events])
        sample_size = len(opt_events)
        
        return f"Successful in {successes}/{sample_size} cases, avg improvement: {avg_improvement:.2%}"
    
    def _analyze_optimization_types(self, events: List[LearningEvent]) -> Dict[str, Any]:
        """Analyze performance by optimization type."""
        type_performance = defaultdict(lambda: {'count': 0, 'successes': 0, 'improvements': []})
        
        for event in events:
            type_performance[event.optimization_applied]['count'] += 1
            type_performance[event.optimization_applied]['improvements'].append(event.improvement)
            if event.success:
                type_performance[event.optimization_applied]['successes'] += 1
        
        # Calculate statistics
        type_stats = {}
        for opt_type, stats in type_performance.items():
            if stats['count'] > 0:
                type_stats[opt_type] = {
                    'success_rate': stats['successes'] / stats['count'],
                    'avg_improvement': statistics.mean(stats['improvements']),
                    'sample_count': stats['count']
                }
        
        # Identify best performing optimization types
        best_types = sorted(type_stats.items(), 
                          key=lambda x: x[1]['success_rate'] * x[1]['avg_improvement'], 
                          reverse=True)[:3]
        
        return {
            'best_performing': dict(best_types),
            'total_optimization_types': len(type_stats),
            'consistent_performers': [opt_type for opt_type, stats in type_stats.items() 
                                    if stats['success_rate'] > 0.6 and stats['sample_count'] > 5]
        }
    
    def _analyze_content_contexts(self, events: List[LearningEvent]) -> Dict[str, Any]:
        """Analyze performance by content context."""
        context_performance = defaultdict(lambda: {'count': 0, 'successes': 0, 'improvements': []})
        
        for event in events:
            context_key = f"{event.context.get('content_type', 'unknown')}_{event.context.get('platform', 'unknown')}"
            context_performance[context_key]['count'] += 1
            context_performance[context_key]['improvements'].append(event.improvement)
            if event.success:
                context_performance[context_key]['successes'] += 1
        
        return {
            'context_performance': {k: {
                'success_rate': v['successes'] / v['count'],
                'avg_improvement': statistics.mean(v['improvements']),
                'sample_count': v['count']
            } for k, v in context_performance.items() if v['count'] > 0}
        }
    
    def _calculate_learning_trends(self, events: List[LearningEvent]) -> Dict[str, Any]:
        """Calculate learning trends over time."""
        if len(events) < 10:
            return {"trend": "insufficient_data"}
        
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda x: x.timestamp)
        
        # Calculate trend in success rate over time
        success_rates = []
        window_size = max(1, len(sorted_events) // 10)  # 10 windows
        
        for i in range(0, len(sorted_events), window_size):
            window_events = sorted_events[i:i + window_size]
            if window_events:
                success_rate = sum(1 for e in window_events if e.success) / len(window_events)
                success_rates.append(success_rate)
        
        if len(success_rates) < 2:
            return {"trend": "stable", "confidence": 0.0}
        
        # Calculate trend direction
        recent_avg = statistics.mean(success_rates[-3:])
        early_avg = statistics.mean(success_rates[:3])
        
        if recent_avg > early_avg + 0.1:
            trend = "improving"
        elif recent_avg < early_avg - 0.1:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "confidence": abs(recent_avg - early_avg),
            "recent_success_rate": recent_avg,
            "early_success_rate": early_avg
        }
    
    def _get_top_optimizations(self, events: List[LearningEvent]) -> List[Dict[str, Any]]:
        """Get top performing optimizations."""
        opt_performance = self._calculate_optimization_performance(events)
        
        top_optimizations = sorted(opt_performance.items(), 
                                 key=lambda x: x[1]['success_rate'] * x[1]['avg_improvement'], 
                                 reverse=True)[:5]
        
        return [
            {
                'optimization_type': opt_type,
                'success_rate': stats['success_rate'],
                'avg_improvement': stats['avg_improvement'],
                'sample_count': stats['sample_count']
            }
            for opt_type, stats in top_optimizations
        ]
    
    def _generate_learning_recommendations(self, events: List[LearningEvent]) -> List[str]:
        """Generate recommendations based on learning analysis."""
        recommendations = []
        
        # Analyze success rates
        opt_performance = self._calculate_optimization_performance(events)
        
        low_performers = [(opt_type, stats) for opt_type, stats in opt_performance.items() 
                         if stats['success_rate'] < 0.4 and stats['sample_count'] > 5]
        
        if low_performers:
            recommendations.append(f"Consider refining {len(low_performers)} underperforming optimization strategies")
        
        # Analyze trends
        trends = self._calculate_learning_trends(events)
        if trends.get('trend') == 'declining':
            recommendations.append("Learning curve declining - consider investigating external factors")
        elif trends.get('trend') == 'improving':
            recommendations.append("Strong learning progress - current strategies are effective")
        
        # Sample size recommendations
        if len(events) < 50:
            recommendations.append("Collect more optimization data for better learning accuracy")
        
        return recommendations
    
    def _adjust_weights(self, model: ModelParameters, context: Dict[str, Any], improvement: float):
        """Adjust model weights based on context and performance."""
        # This is a simplified weight adjustment - in practice, this would be more sophisticated
        context_factor = 1.0
        
        if context.get('platform') == 'youtube':
            context_factor = 1.1 if improvement > 0 else 0.9
        
        if context.get('content_type') == 'video':
            context_factor *= 1.05 if improvement > 0 else 0.95
        
        # Adjust bias slightly based on performance
        if improvement > 0.1:  # Significant improvement
            model.bias = min(0.95, model.bias + 0.01)
        elif improvement < -0.05:  # Performance degradation
            model.bias = max(0.05, model.bias - 0.01)
    
    def save_learning_state(self, filepath: str):
        """Save current learning state to file."""
        try:
            learning_data = self.export_learning_data()
            with open(filepath, 'w') as f:
                json.dump(learning_data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving learning state: {e}")
            return False
    
    def load_learning_state(self, filepath: str) -> bool:
        """Load learning state from file."""
        try:
            with open(filepath, 'r') as f:
                learning_data = json.load(f)
            return self.import_learning_data(learning_data)
        except Exception as e:
            print(f"Error loading learning state: {e}")
            return False