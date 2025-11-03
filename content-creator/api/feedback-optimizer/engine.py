"""
Learning Engine Module

Central orchestrator that learns from feedback patterns and coordinates the optimization system.
"""

import json
import pickle
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

from .analyzer import FeedbackAnalyzer
from .recommender import ContentImprovementRecommender
from .processor import SentimentProcessor
from .utils.template_engine import TemplateEngine
from .models.feedback_data import FeedbackData
from .models.recommendation import Recommendation
from .utils.pattern_detector import PatternDetector


class LearningEngine:
    """
    AI-powered learning engine that improves recommendations based on feedback patterns.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the learning engine."""
        self.config = config or self._default_config()
        self.analyzer = FeedbackAnalyzer(self.config)
        self.recommender = ContentImprovementRecommender(self.config)
        self.processor = SentimentProcessor(self.config)
        self.template_engine = TemplateEngine(self.config)
        self.pattern_detector = PatternDetector(self.config)
        
        # Learning data stores
        self.learning_history: List[Dict[str, Any]] = []
        self.pattern_library: Dict[str, Any] = {}
        self.success_metrics: Dict[str, float] = {}
        self.implementation_tracking: Dict[str, Dict[str, Any]] = {}
        
        # Performance baselines
        self.baselines = self._initialize_baselines()
        self.adaptation_thresholds = self._initialize_adaptation_thresholds()
        
    def _default_config(self) -> Dict:
        """Default configuration for the learning engine."""
        return {
            'learning_rate': 0.1,
            'adaptation_frequency': 'weekly',
            'min_data_points': 10,
            'confidence_threshold': 0.7,
            'performance_window_days': 30,
            'pattern_recognition_sensitivity': 0.8,
            'success_measurement_window': 14,
            'feedback_loop_enabled': True,
            'auto_optimization': False,
            'learning_retention_days': 90
        }
    
    def process_feedback_learning_cycle(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Complete learning cycle: analyze feedback, generate recommendations, learn from results.
        
        Args:
            feedback_data: List of feedback data to process
            
        Returns:
            Complete learning results with recommendations and insights
        """
        # Step 1: Analyze current feedback
        analysis_results = self.analyzer.analyze_feedback(feedback_data)
        
        # Step 2: Generate recommendations
        recommendations = self.recommender.generate_recommendations(analysis_results)
        
        # Step 3: Learn from historical patterns
        learning_insights = self._extract_learning_insights(analysis_results)
        
        # Step 4: Update pattern library
        self._update_pattern_library(analysis_results, recommendations)
        
        # Step 5: Generate comprehensive report
        comprehensive_report = self._generate_comprehensive_report(
            analysis_results, recommendations, learning_insights
        )
        
        # Step 6: Update learning history
        learning_cycle = {
            'timestamp': datetime.now().isoformat(),
            'feedback_count': len(feedback_data),
            'analysis_results': analysis_results,
            'recommendations_count': len(recommendations),
            'learning_insights': learning_insights,
            'report': comprehensive_report
        }
        
        self.learning_history.append(learning_cycle)
        
        # Step 7: Clean old learning data if needed
        self._cleanup_old_learning_data()
        
        return {
            'analysis_results': analysis_results,
            'recommendations': recommendations,
            'learning_insights': learning_insights,
            'comprehensive_report': comprehensive_report,
            'pattern_updates': self._get_recent_pattern_updates(),
            'next_learning_cycle': self._suggest_next_cycle_timing()
        }
    
    def learn_from_implementation_results(self, recommendation_id: str, implementation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Learn from the results of recommendation implementation.
        
        Args:
            recommendation_id: ID of the implemented recommendation
            implementation_results: Results from implementation
            
        Returns:
            Learning insights from implementation
        """
        # Track implementation results
        self.implementation_tracking[recommendation_id] = {
            'implementation_date': datetime.now().isoformat(),
            'results': implementation_results,
            'learning_applied': True
        }
        
        # Analyze success metrics
        success_analysis = self._analyze_implementation_success(
            recommendation_id, implementation_results
        )
        
        # Update pattern library based on results
        pattern_updates = self._update_patterns_from_results(
            recommendation_id, implementation_results
        )
        
        # Adapt recommendation generation for future cycles
        adaptation_results = self._adapt_recommendation_system(success_analysis)
        
        return {
            'success_analysis': success_analysis,
            'pattern_updates': pattern_updates,
            'system_adaptations': adaptation_results,
            'confidence_adjustments': self._adjust_confidence_levels(success_analysis)
        }
    
    def generate_predictive_insights(self, current_feedback: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate predictive insights based on current feedback and learning history.
        
        Args:
            current_feedback: Current feedback data
            
        Returns:
            Predictive insights and recommendations
        """
        # Analyze current feedback patterns
        current_analysis = self.analyzer.analyze_feedback(current_feedback)
        
        # Apply learned patterns
        pattern_insights = self._apply_learned_patterns(current_analysis)
        
        # Generate predictions
        predictions = self._generate_performance_predictions(current_analysis)
        
        # Identify emerging trends
        emerging_trends = self._identify_emerging_trends(current_analysis)
        
        # Recommend proactive actions
        proactive_recommendations = self._generate_proactive_recommendations(
            predictions, emerging_trends
        )
        
        return {
            'current_analysis': current_analysis,
            'pattern_insights': pattern_insights,
            'performance_predictions': predictions,
            'emerging_trends': emerging_trends,
            'proactive_recommendations': proactive_recommendations,
            'confidence_levels': self._calculate_prediction_confidence(current_analysis)
        }
    
    def optimize_recommendation_priorities(self, recommendations: List[Recommendation]) -> List[Recommendation]:
        """
        Optimize recommendation priorities based on learned patterns and success rates.
        
        Args:
            recommendations: Raw recommendations to optimize
            
        Returns:
            Prioritized recommendations with learning adjustments
        """
        # Calculate historical success rates for recommendation types
        success_rates = self._calculate_recommendation_success_rates()
        
        # Adjust priorities based on learning
        optimized_recommendations = []
        
        for rec in recommendations:
            # Base priority
            adjusted_priority = rec.priority
            
            # Learning-based adjustments
            type_success_rate = success_rates.get(rec.recommendation_type.value, 0.5)
            historical_success = self._get_historical_success_for_content_types(rec.target_content_types)
            
            # Boost priority for historically successful types
            if type_success_rate > 0.7:
                if adjusted_priority.value == 'low':
                    adjusted_priority = rec.priority.__class__('medium')
            
            # Consider implementation feasibility
            implementation_feasibility = self._assess_implementation_feasibility(rec)
            if implementation_feasibility < 0.3:
                adjusted_priority = rec.priority.__class__('low')
            
            # Create optimized recommendation
            optimized_rec = rec
            optimized_rec.priority = adjusted_priority
            
            # Add learning metadata
            optimized_rec.supporting_data['learning_metadata'] = {
                'type_success_rate': type_success_rate,
                'historical_success': historical_success,
                'implementation_feasibility': implementation_feasibility,
                'optimization_date': datetime.now().isoformat()
            }
            
            optimized_recommendations.append(optimized_rec)
        
        # Re-sort by optimized priority
        optimized_recommendations.sort(
            key=lambda x: (x.priority.value == 'high', x.impact_score),
            reverse=True
        )
        
        return optimized_recommendations
    
    def get_learning_summary(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Generate summary of learning engine performance and insights.
        
        Args:
            days_back: Number of days to look back for summary
            
        Returns:
            Comprehensive learning summary
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Filter recent learning cycles
        recent_cycles = [
            cycle for cycle in self.learning_history
            if datetime.fromisoformat(cycle['timestamp']) >= cutoff_date
        ]
        
        if not recent_cycles:
            return {'status': 'insufficient_data', 'message': 'No learning data available for specified period'}
        
        # Analyze learning progress
        progress_analysis = self._analyze_learning_progress(recent_cycles)
        
        # Summarize pattern evolution
        pattern_summary = self._summarize_pattern_evolution(recent_cycles)
        
        # Calculate performance improvements
        performance_summary = self._calculate_performance_improvements(recent_cycles)
        
        # Identify key learnings
        key_learnings = self._extract_key_learnings(recent_cycles)
        
        # Generate recommendations for learning enhancement
        enhancement_recommendations = self._generate_learning_enhancement_recommendations(recent_cycles)
        
        return {
            'summary_period': f"Last {days_back} days",
            'learning_cycles_count': len(recent_cycles),
            'progress_analysis': progress_analysis,
            'pattern_summary': pattern_summary,
            'performance_summary': performance_summary,
            'key_learnings': key_learnings,
            'enhancement_recommendations': enhancement_recommendations,
            'learning_engine_health': self._assess_learning_engine_health(recent_cycles)
        }
    
    # Core learning methods
    def _extract_learning_insights(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights for learning from analysis results."""
        insights = {
            'pattern_recognition': self._recognize_patterns(analysis_results),
            'performance_correlations': self._identify_performance_correlations(analysis_results),
            'optimization_opportunities': self._identify_optimization_opportunities(analysis_results),
            'success_indicators': self._identify_success_indicators(analysis_results)
        }
        
        return insights
    
    def _update_pattern_library(self, analysis_results: Dict[str, Any], recommendations: List[Recommendation]) -> None:
        """Update pattern library with new insights."""
        # Extract new patterns
        new_patterns = self.pattern_detector.analyze_pattern_frequency(
            self._convert_feedback_data_from_analysis(analysis_results)
        )
        
        # Update library with high-confidence patterns
        for pattern_type, pattern_data in new_patterns.get('pattern_statistics', {}).items():
            if pattern_data['confidence'] >= self.config['confidence_threshold']:
                self.pattern_library[pattern_type] = {
                    'frequency': pattern_data['frequency'],
                    'sentiment_impact': pattern_data['average_sentiment_impact'],
                    'confidence': pattern_data['confidence'],
                    'last_updated': datetime.now().isoformat(),
                    'success_rate': 0.5  # Initial success rate
                }
    
    def _generate_comprehensive_report(self, analysis_results: Dict[str, Any], 
                                     recommendations: List[Recommendation], 
                                     learning_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive report combining analysis, recommendations, and learning."""
        return self.template_engine.generate_improvement_report(analysis_results, recommendations)
    
    def _analyze_implementation_success(self, recommendation_id: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze success of recommendation implementation."""
        # Extract success metrics
        before_metrics = results.get('before_metrics', {})
        after_metrics = results.get('after_metrics', {})
        
        success_analysis = {
            'recommendation_id': recommendation_id,
            'implementation_date': results.get('implementation_date'),
            'success_score': 0.0,
            'metrics_improved': [],
            'metrics_degraded': [],
            'overall_impact': 'unknown',
            'lessons_learned': []
        }
        
        # Calculate improvement scores for each metric
        improvement_scores = {}
        for metric in before_metrics.keys():
            if metric in after_metrics:
                before_value = before_metrics[metric]
                after_value = after_metrics[metric]
                
                if before_value != 0:
                    improvement_score = (after_value - before_value) / abs(before_value)
                    improvement_scores[metric] = improvement_score
                    
                    if improvement_score > 0.1:  # 10% improvement threshold
                        success_analysis['metrics_improved'].append(metric)
                    elif improvement_score < -0.1:  # 10% degradation threshold
                        success_analysis['metrics_degraded'].append(metric)
        
        # Calculate overall success score
        if improvement_scores:
            success_analysis['success_score'] = statistics.mean(improvement_scores.values())
        
        # Determine overall impact
        if success_analysis['success_score'] > 0.2:
            success_analysis['overall_impact'] = 'positive'
        elif success_analysis['success_score'] < -0.1:
            success_analysis['overall_impact'] = 'negative'
        else:
            success_analysis['overall_impact'] = 'neutral'
        
        # Extract lessons learned
        success_analysis['lessons_learned'] = self._extract_lessons_learned(results)
        
        return success_analysis
    
    def _update_patterns_from_results(self, recommendation_id: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Update patterns based on implementation results."""
        updates = {}
        
        # Find the original recommendation pattern
        for pattern_type, pattern_data in self.pattern_library.items():
            # Check if this pattern was used in the recommendation
            # This would be more sophisticated in a real implementation
            if 'pattern' in pattern_data:
                # Update success rate
                if results.get('success_score', 0) > 0:
                    current_success_rate = pattern_data.get('success_rate', 0.5)
                    # Exponential moving average for success rate
                    new_success_rate = current_success_rate + self.config['learning_rate'] * (
                        results['success_score'] - current_success_rate
                    )
                    pattern_data['success_rate'] = max(0.0, min(1.0, new_success_rate))
                    pattern_data['last_success_update'] = datetime.now().isoformat()
                    
                    updates[pattern_type] = {
                        'success_rate': new_success_rate,
                        'update_type': 'success_rate_adjusted'
                    }
        
        return updates
    
    def _adapt_recommendation_system(self, success_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt recommendation system based on success analysis."""
        adaptations = {
            'priority_adjustments': {},
            'threshold_updates': {},
            'pattern_weight_updates': {}
        }
        
        # If recommendations are consistently successful, lower thresholds
        if success_analysis.get('overall_impact') == 'positive':
            # Could lower impact thresholds, adjust confidence requirements, etc.
            adaptations['threshold_updates']['min_impact_score'] = 0.6  # Lower from 0.7
        
        # If recommendations are failing, raise thresholds
        elif success_analysis.get('overall_impact') == 'negative':
            adaptations['threshold_updates']['min_impact_score'] = 0.8  # Raise from 0.7
            adaptations['confidence_requirement'] = 0.8  # Increase confidence requirement
        
        return adaptations
    
    # Predictive and proactive methods
    def _apply_learned_patterns(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Apply previously learned patterns to current analysis."""
        pattern_insights = {
            'applicable_patterns': [],
            'pattern_confidence': 0.0,
            'prediction_accuracy': 0.0
        }
        
        # Find applicable patterns
        for pattern_type, pattern_data in self.pattern_library.items():
            if pattern_data.get('confidence', 0) >= self.config['confidence_threshold']:
                # Check if this pattern applies to current analysis
                applicability_score = self._calculate_pattern_applicability(
                    pattern_type, pattern_data, analysis_results
                )
                
                if applicability_score > 0.5:
                    pattern_insights['applicable_patterns'].append({
                        'pattern_type': pattern_type,
                        'applicability_score': applicability_score,
                        'historical_success_rate': pattern_data.get('success_rate', 0.5),
                        'confidence': pattern_data.get('confidence', 0.0)
                    })
        
        if pattern_insights['applicable_patterns']:
            # Calculate weighted confidence
            total_weight = sum(p['applicability_score'] * p['confidence'] 
                             for p in pattern_insights['applicable_patterns'])
            total_applicability = sum(p['applicability_score'] 
                                    for p in pattern_insights['applicable_patterns'])
            
            if total_applicability > 0:
                pattern_insights['pattern_confidence'] = total_weight / total_applicability
        
        return pattern_insights
    
    def _generate_performance_predictions(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance predictions based on patterns and trends."""
        predictions = {
            'sentiment_prediction': 'stable',
            'engagement_prediction': 'stable',
            'overall_performance_prediction': 'stable',
            'confidence_level': 0.5,
            'prediction_horizon_days': 7
        }
        
        # Use historical patterns to make predictions
        temporal_trends = analysis_results.get('temporal_trends', {})
        sentiment_trends = temporal_trends.get('sentiment_trends', {})
        
        if len(sentiment_trends) >= 3:
            # Simple trend analysis
            trend_values = list(sentiment_trends.values())
            recent_trend = statistics.mean(trend_values[-3:])
            historical_trend = statistics.mean(trend_values[:-3]) if len(trend_values) > 3 else recent_trend
            
            if recent_trend > historical_trend + 0.1:
                predictions['sentiment_prediction'] = 'improving'
                predictions['confidence_level'] += 0.2
            elif recent_trend < historical_trend - 0.1:
                predictions['sentiment_prediction'] = 'declining'
                predictions['confidence_level'] += 0.2
        
        return predictions
    
    def _identify_emerging_trends(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify emerging trends in current data."""
        emerging_trends = []
        
        # Pattern frequency analysis
        pattern_analysis = self.pattern_detector.analyze_pattern_frequency(
            self._convert_feedback_data_from_analysis(analysis_results)
        )
        
        # Find emerging patterns (increasing frequency)
        for pattern_type, pattern_data in pattern_analysis.get('pattern_statistics', {}).items():
            trend = pattern_data.get('trend', 'stable')
            
            if trend == 'increasing':
                emerging_trends.append({
                    'pattern': pattern_type,
                    'trend': 'emerging',
                    'frequency': pattern_data['frequency'],
                    'impact_potential': 'high' if pattern_data['average_sentiment_impact'] < -0.3 else 'medium',
                    'confidence': pattern_data['confidence']
                })
        
        return emerging_trends
    
    def _generate_proactive_recommendations(self, predictions: Dict[str, Any], 
                                          emerging_trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate proactive recommendations based on predictions and trends."""
        proactive_recs = []
        
        # Address declining sentiment prediction
        if predictions.get('sentiment_prediction') == 'declining':
            proactive_recs.append({
                'type': 'preventive_sentiment_action',
                'title': 'Prevent Sentiment Decline',
                'description': 'Proactive measures to prevent further sentiment decline',
                'urgency': 'high',
                'estimated_impact': 0.7
            })
        
        # Address emerging negative patterns
        for trend in emerging_trends:
            if trend.get('impact_potential') == 'high':
                proactive_recs.append({
                    'type': 'emerging_pattern_mitigation',
                    'title': f'Address Emerging {trend["pattern"]} Pattern',
                    'description': f'Proactive mitigation of emerging {trend["pattern"]} pattern',
                    'urgency': 'medium',
                    'estimated_impact': 0.6
                })
        
        return proactive_recs
    
    # Utility and helper methods
    def _initialize_baselines(self) -> Dict[str, float]:
        """Initialize performance baselines."""
        return {
            'content_quality': 0.6,
            'sentiment_score': 0.5,
            'engagement_rate': 0.03,
            'recommendation_success_rate': 0.6
        }
    
    def _initialize_adaptation_thresholds(self) -> Dict[str, float]:
        """Initialize adaptation thresholds."""
        return {
            'minimum_data_points': 10,
            'confidence_threshold': 0.7,
            'performance_window': 30,
            'learning_stability_period': 7
        }
    
    def _cleanup_old_learning_data(self) -> None:
        """Clean up old learning data to maintain performance."""
        cutoff_date = datetime.now() - timedelta(days=self.config['learning_retention_days'])
        
        # Clean learning history
        self.learning_history = [
            cycle for cycle in self.learning_history
            if datetime.fromisoformat(cycle['timestamp']) >= cutoff_date
        ]
    
    def _get_recent_pattern_updates(self) -> List[Dict[str, Any]]:
        """Get recent pattern library updates."""
        recent_updates = []
        
        for pattern_type, pattern_data in self.pattern_library.items():
            if 'last_updated' in pattern_data:
                last_updated = datetime.fromisoformat(pattern_data['last_updated'])
                if (datetime.now() - last_updated).days <= 7:
                    recent_updates.append({
                        'pattern': pattern_type,
                        'last_updated': pattern_data['last_updated'],
                        'confidence': pattern_data.get('confidence', 0.0),
                        'success_rate': pattern_data.get('success_rate', 0.0)
                    })
        
        return recent_updates
    
    def _suggest_next_cycle_timing(self) -> Dict[str, Any]:
        """Suggest timing for next learning cycle."""
        return {
            'recommended_interval_hours': 24,
            'next_cycle_suggested': (datetime.now() + timedelta(hours=24)).isoformat(),
            'data_requirements': 'At least 10 new feedback items for optimal analysis'
        }
    
    def _convert_feedback_data_from_analysis(self, analysis_results: Dict[str, Any]) -> List[FeedbackData]:
        """Convert analysis results back to feedback data for pattern analysis."""
        # This is a simplified conversion - in reality, you'd maintain the original feedback data
        return []
    
    def _calculate_prediction_confidence(self, analysis_results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence levels for predictions."""
        return {
            'sentiment_prediction': 0.7,
            'engagement_prediction': 0.6,
            'pattern_recognition': 0.8
        }
    
    def _calculate_recommendation_success_rates(self) -> Dict[str, float]:
        """Calculate historical success rates for recommendation types."""
        success_rates = {}
        
        for pattern_type, pattern_data in self.pattern_library.items():
            if 'success_rate' in pattern_data:
                success_rates[pattern_type] = pattern_data['success_rate']
            else:
                success_rates[pattern_type] = 0.5  # Default
        
        return success_rates
    
    def _get_historical_success_for_content_types(self, content_types: List) -> float:
        """Get historical success rate for specific content types."""
        # This would analyze historical success rates for the specific content types
        return 0.6  # Placeholder
    
    def _assess_implementation_feasibility(self, recommendation: Recommendation) -> float:
        """Assess feasibility of implementing a recommendation."""
        # Consider implementation difficulty, time requirements, resources needed
        difficulty_score = {
            'Low': 0.9,
            'Medium': 0.6,
            'High': 0.3,
            'Very High': 0.1
        }.get(recommendation.implementation_difficulty, 0.5)
        
        # Adjust for time requirements
        time_factor = min(1.0, 10.0 / recommendation.estimated_time_hours) if recommendation.estimated_time_hours > 0 else 1.0
        
        # Adjust for resource availability
        resource_factor = 0.8 if len(recommendation.required_resources) <= 2 else 0.5
        
        return difficulty_score * time_factor * resource_factor
    
    def _adjust_confidence_levels(self, success_analysis: Dict[str, Any]) -> Dict[str, float]:
        """Adjust confidence levels based on implementation success."""
        adjustments = {}
        
        # If implementation was successful, slightly reduce confidence requirements
        if success_analysis.get('overall_impact') == 'positive':
            adjustments['recommendation_confidence'] = -0.05  # Reduce by 5%
            adjustments['pattern_confidence'] = -0.03  # Reduce by 3%
        
        # If implementation failed, increase confidence requirements
        elif success_analysis.get('overall_impact') == 'negative':
            adjustments['recommendation_confidence'] = 0.1  # Increase by 10%
            adjustments['pattern_confidence'] = 0.05  # Increase by 5%
        
        return adjustments
    
    # Learning summary methods
    def _analyze_learning_progress(self, recent_cycles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze learning progress over recent cycles."""
        if len(recent_cycles) < 2:
            return {'status': 'insufficient_data'}
        
        # Track improvement in recommendation quality
        cycle_scores = []
        for cycle in recent_cycles:
            recommendations = cycle.get('recommendations_count', 0)
            analysis_quality = cycle.get('analysis_results', {}).get('overall_score', 0.5)
            cycle_scores.append(analysis_quality)
        
        # Calculate trend
        if len(cycle_scores) >= 3:
            recent_avg = statistics.mean(cycle_scores[-3:])
            earlier_avg = statistics.mean(cycle_scores[:-3]) if len(cycle_scores) > 3 else recent_avg
            trend = 'improving' if recent_avg > earlier_avg else 'declining' if recent_avg < earlier_avg else 'stable'
        else:
            trend = 'stable'
        
        return {
            'cycles_analyzed': len(recent_cycles),
            'quality_trend': trend,
            'average_quality': statistics.mean(cycle_scores) if cycle_scores else 0.5,
            'consistency': 1.0 - (statistics.stdev(cycle_scores) if len(cycle_scores) > 1 else 0)
        }
    
    def _summarize_pattern_evolution(self, recent_cycles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize how patterns have evolved."""
        pattern_counts = Counter()
        
        for cycle in recent_cycles:
            analysis_results = cycle.get('analysis_results', {})
            # Extract patterns from each cycle (simplified)
            pattern_counts['high_impact_patterns'] += len(analysis_results.get('improvement_areas', []))
        
        return {
            'total_patterns_identified': sum(pattern_counts.values()),
            'dominant_patterns': dict(pattern_counts.most_common(3)),
            'pattern_diversity': len(pattern_counts),
            'evolution_status': 'active' if pattern_counts else 'stable'
        }
    
    def _calculate_performance_improvements(self, recent_cycles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance improvements over time."""
        if len(recent_cycles) < 2:
            return {'status': 'insufficient_data'}
        
        # Compare first and last cycles
        first_cycle = recent_cycles[0]
        last_cycle = recent_cycles[-1]
        
        first_score = first_cycle.get('analysis_results', {}).get('overall_score', 0.5)
        last_score = last_cycle.get('analysis_results', {}).get('overall_score', 0.5)
        
        improvement = last_score - first_score
        
        return {
            'initial_score': first_score,
            'current_score': last_score,
            'absolute_improvement': improvement,
            'percentage_improvement': (improvement / first_score * 100) if first_score > 0 else 0,
            'improvement_direction': 'up' if improvement > 0 else 'down' if improvement < 0 else 'stable'
        }
    
    def _extract_key_learnings(self, recent_cycles: List[Dict[str, Any]]) -> List[str]:
        """Extract key learnings from recent cycles."""
        learnings = []
        
        # Analyze patterns across cycles
        all_improvement_areas = []
        for cycle in recent_cycles:
            improvement_areas = cycle.get('analysis_results', {}).get('improvement_areas', [])
            all_improvement_areas.extend(improvement_areas)
        
        # Find recurring themes
        area_counts = Counter([area.get('area', 'unknown') for area in all_improvement_areas])
        
        for area, count in area_counts.most_common(3):
            if count >= 2:
                learnings.append(f"Recurring issue in {area.replace('_', ' ')} identified ({count} times)")
        
        # Performance insights
        performance_improvements = self._calculate_performance_improvements(recent_cycles)
        if performance_improvements.get('percentage_improvement', 0) > 10:
            learnings.append("Significant performance improvement achieved through optimization")
        
        return learnings
    
    def _generate_learning_enhancement_recommendations(self, recent_cycles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations to enhance learning engine performance."""
        recommendations = []
        
        # Check data sufficiency
        if len(recent_cycles) < 4:
            recommendations.append({
                'type': 'data_volume',
                'title': 'Increase Data Collection',
                'description': 'More learning cycles needed for better pattern recognition',
                'priority': 'medium'
            })
        
        # Check pattern confidence
        pattern_confidence = self._calculate_average_pattern_confidence(recent_cycles)
        if pattern_confidence < 0.7:
            recommendations.append({
                'type': 'confidence_improvement',
                'title': 'Improve Pattern Confidence',
                'description': 'Increase pattern detection sensitivity or data quality',
                'priority': 'high'
            })
        
        return recommendations
    
    def _assess_learning_engine_health(self, recent_cycles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall health of the learning engine."""
        if not recent_cycles:
            return {'status': 'no_data'}
        
        # Calculate health metrics
        cycle_frequency = len(recent_cycles) / 30  # Cycles per day over last 30 days
        data_volume = sum(cycle.get('feedback_count', 0) for cycle in recent_cycles)
        recommendation_quality = statistics.mean([
            cycle.get('analysis_results', {}).get('overall_score', 0.5)
            for cycle in recent_cycles
        ])
        
        # Determine health status
        if cycle_frequency >= 0.5 and data_volume >= 100 and recommendation_quality >= 0.6:
            health_status = 'excellent'
        elif cycle_frequency >= 0.2 and data_volume >= 50 and recommendation_quality >= 0.5:
            health_status = 'good'
        elif cycle_frequency >= 0.1 and data_volume >= 20:
            health_status = 'fair'
        else:
            health_status = 'needs_attention'
        
        return {
            'health_status': health_status,
            'cycle_frequency': cycle_frequency,
            'total_data_points': data_volume,
            'average_quality_score': recommendation_quality,
            'recommendations': self._generate_learning_enhancement_recommendations(recent_cycles)
        }
    
    def _calculate_average_pattern_confidence(self, recent_cycles: List[Dict[str, Any]]) -> float:
        """Calculate average pattern confidence across recent cycles."""
        confidence_scores = []
        
        for cycle in recent_cycles:
            analysis_results = cycle.get('analysis_results', {})
            # This would extract actual pattern confidence values
            # For now, using a placeholder
            confidence_scores.append(0.7)
        
        return statistics.mean(confidence_scores) if confidence_scores else 0.0
    
    def _extract_lessons_learned(self, results: Dict[str, Any]) -> List[str]:
        """Extract lessons learned from implementation results."""
        lessons = []
        
        # Analyze what worked
        success_score = results.get('success_score', 0)
        if success_score > 0.2:
            lessons.append("Implementation approach was effective")
        
        # Analyze what didn't work
        metrics_degraded = results.get('metrics_degraded', [])
        if metrics_degraded:
            lessons.append(f"Degradation in {', '.join(metrics_degraded)} requires attention")
        
        # Time-based lessons
        implementation_time = results.get('actual_time_hours', 0)
        estimated_time = results.get('estimated_time_hours', 0)
        
        if implementation_time > estimated_time * 1.5:
            lessons.append("Time estimates may need adjustment for future similar implementations")
        elif implementation_time < estimated_time * 0.8:
            lessons.append("Implementation was more efficient than estimated")
        
        return lessons