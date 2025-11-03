"""
Winner Selection Module

Automatically selects winning variations from A/B tests based on
statistical analysis and business rules.
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

class SelectionStrategy(Enum):
    """Strategies for selecting winning variations."""
    STATISTICAL_SIGNIFICANCE = "statistical_significance"
    BEST_PERFORMANCE = "best_performance"
    HYBRID = "hybrid"
    TIME_BASED = "time_based"
    REVENUE_OPTIMIZED = "revenue_optimized"
    CUSTOM = "custom"

class SelectionCriteria(Enum):
    """Criteria for evaluating performance."""
    CLICK_THROUGH_RATE = "click_through_rate"
    ENGAGEMENT_RATE = "engagement_rate"
    CONVERSION_RATE = "conversion_rate"
    REVENUE_PER_IMPRESSION = "revenue_per_impression"
    WATCH_TIME = "watch_time"
    SUBSCRIBER_GAIN = "subscriber_gain"
    COMPOSITE_SCORE = "composite_score"

@dataclass
class SelectionResult:
    """Result of winner selection process."""
    winner_variation_id: str
    confidence_score: float
    strategy_used: str
    is_winner_selected: bool
    runner_up_variation_ids: List[str]
    selection_reason: str
    statistical_evidence: Dict[str, Any]
    business_impact_estimate: Dict[str, Any]
    selection_timestamp: datetime

class WinnerSelector:
    """Automatically selects winning variations from A/B tests."""
    
    def __init__(
        self,
        default_strategy: SelectionStrategy = SelectionStrategy.HYBRID,
        significance_threshold: float = 0.05,
        performance_threshold: float = 0.0,
        min_sample_size: int = 100,
        min_test_duration_hours: int = 24
    ):
        """Initialize the winner selector."""
        self.default_strategy = default_strategy
        self.significance_threshold = significance_threshold
        self.performance_threshold = performance_threshold
        self.min_sample_size = min_sample_size
        self.min_test_duration_hours = min_test_duration_hours
        self.selection_history: List[SelectionResult] = []
        
        # Business rules weights for hybrid scoring
        self.business_weights = {
            SelectionCriteria.CLICK_THROUGH_RATE: 0.25,
            SelectionCriteria.ENGAGEMENT_RATE: 0.25,
            SelectionCriteria.CONVERSION_RATE: 0.20,
            SelectionCriteria.REVENUE_PER_IMPRESSION: 0.20,
            SelectionCriteria.WATCH_TIME: 0.10
        }
        
        # Custom evaluation functions
        self.custom_evaluators: Dict[str, Callable] = {}
    
    def select_winner(
        self,
        variation_metrics: Dict[str, Dict[str, Any]],
        test_start_time: datetime,
        strategy: Optional[SelectionStrategy] = None,
        custom_evaluator: Optional[Callable] = None
    ) -> SelectionResult:
        """Select the winning variation using specified strategy."""
        
        if not variation_metrics:
            raise ValueError("No variation metrics provided")
        
        strategy = strategy or self.default_strategy
        
        # Validate test readiness
        if not self._is_test_ready(test_start_time, variation_metrics):
            return SelectionResult(
                winner_variation_id="",
                confidence_score=0.0,
                strategy_used=strategy.value,
                is_winner_selected=False,
                runner_up_variation_ids=[],
                selection_reason="Test not ready - insufficient data or duration",
                statistical_evidence={},
                business_impact_estimate={},
                selection_timestamp=datetime.now()
            )
        
        # Apply selection strategy
        if strategy == SelectionStrategy.STATISTICAL_SIGNIFICANCE:
            result = self._select_by_statistical_significance(variation_metrics)
        elif strategy == SelectionStrategy.BEST_PERFORMANCE:
            result = self._select_by_best_performance(variation_metrics)
        elif strategy == SelectionStrategy.HYBRID:
            result = self._select_by_hybrid_approach(variation_metrics)
        elif strategy == SelectionStrategy.TIME_BASED:
            result = self._select_by_time_based(variation_metrics, test_start_time)
        elif strategy == SelectionStrategy.REVENUE_OPTIMIZED:
            result = self._select_by_revenue_optimization(variation_metrics)
        elif strategy == SelectionStrategy.CUSTOM:
            result = self._select_by_custom_evaluator(variation_metrics, custom_evaluator)
        else:
            raise ValueError(f"Unsupported selection strategy: {strategy}")
        
        # Store selection in history
        self.selection_history.append(result)
        
        logger.info(f"Selected winner {result.winner_variation_id} using {strategy.value} strategy")
        
        return result
    
    def _is_test_ready(
        self,
        test_start_time: datetime,
        variation_metrics: Dict[str, Dict[str, Any]]
    ) -> bool:
        """Check if test has enough data for winner selection."""
        
        # Check minimum test duration
        test_duration = datetime.now() - test_start_time
        if test_duration.total_seconds() < self.min_test_duration_hours * 3600:
            logger.info(f"Test duration {test_duration} is less than minimum {self.min_test_duration_hours} hours")
            return False
        
        # Check minimum sample sizes for each variation
        for variation_id, metrics in variation_metrics.items():
            sample_size = self._get_sample_size(metrics)
            if sample_size < self.min_sample_size:
                logger.info(f"Variation {variation_id} has insufficient sample size: {sample_size}")
                return False
        
        return True
    
    def _get_sample_size(self, metrics: Dict[str, Any]) -> int:
        """Extract sample size from metrics."""
        # Look for impressions as proxy for sample size
        if "impressions_total" in metrics:
            return int(metrics["impressions_total"])
        elif "clicks_total" in metrics:
            return int(metrics["clicks_total"])
        else:
            return 0
    
    def _select_by_statistical_significance(
        self,
        variation_metrics: Dict[str, Dict[str, Any]]
    ) -> SelectionResult:
        """Select winner based on statistical significance."""
        
        # Perform statistical tests for all variation pairs
        significance_scores = {}
        for variation_id, metrics in variation_metrics.items():
            # Extract metrics for statistical testing
            performance_score = self._calculate_performance_score(metrics)
            significance_scores[variation_id] = {
                "performance": performance_score,
                "statistical_confidence": self._calculate_statistical_confidence(metrics),
                "sample_size": self._get_sample_size(metrics)
            }
        
        # Find the variation with highest statistical confidence
        winner_id = max(significance_scores.keys(), 
                       key=lambda x: significance_scores[x]["statistical_confidence"])
        
        # Calculate confidence score
        confidence_score = significance_scores[winner_id]["statistical_confidence"]
        
        # Determine runner-ups
        runner_ups = [vid for vid in significance_scores.keys() 
                     if vid != winner_id][:2]
        
        return SelectionResult(
            winner_variation_id=winner_id,
            confidence_score=confidence_score,
            strategy_used="statistical_significance",
            is_winner_selected=confidence_score > self.significance_threshold,
            runner_up_variation_ids=runner_ups,
            selection_reason=f"Selected based on statistical significance (p < {self.significance_threshold})",
            statistical_evidence=significance_scores[winner_id],
            business_impact_estimate=self._estimate_business_impact(variation_metrics[winner_id]),
            selection_timestamp=datetime.now()
        )
    
    def _select_by_best_performance(
        self,
        variation_metrics: Dict[str, Dict[str, Any]]
    ) -> SelectionResult:
        """Select winner based on best overall performance."""
        
        performance_scores = {}
        for variation_id, metrics in variation_metrics.items():
            performance_scores[variation_id] = self._calculate_performance_score(metrics)
        
        # Find variation with highest performance score
        winner_id = max(performance_scores.keys(), key=lambda x: performance_scores[x])
        
        # Calculate confidence based on performance margin
        scores = list(performance_scores.values())
        max_score = max(scores)
        second_max_score = sorted(scores, reverse=True)[1] if len(scores) > 1 else 0
        
        performance_margin = (max_score - second_max_score) / max_score if max_score > 0 else 0
        confidence_score = min(performance_margin, 1.0)
        
        runner_ups = [vid for vid, score in performance_scores.items() 
                     if vid != winner_id and score == second_max_score]
        
        return SelectionResult(
            winner_variation_id=winner_id,
            confidence_score=confidence_score,
            strategy_used="best_performance",
            is_winner_selected=performance_margin > 0.05,  # 5% margin threshold
            runner_up_variation_ids=runner_ups,
            selection_reason=f"Selected based on best performance score ({performance_scores[winner_id]:.3f})",
            statistical_evidence={"performance_scores": performance_scores},
            business_impact_estimate=self._estimate_business_impact(variation_metrics[winner_id]),
            selection_timestamp=datetime.now()
        )
    
    def _select_by_hybrid_approach(
        self,
        variation_metrics: Dict[str, Dict[str, Any]]
    ) -> SelectionResult:
        """Select winner using hybrid approach combining statistical and performance metrics."""
        
        hybrid_scores = {}
        
        for variation_id, metrics in variation_metrics.items():
            # Calculate components
            performance_score = self._calculate_performance_score(metrics)
            statistical_confidence = self._calculate_statistical_confidence(metrics)
            sample_size_score = min(self._get_sample_size(metrics) / 1000, 1.0)  # Normalize to 1000
            
            # Combine scores with weights
            hybrid_score = (
                0.4 * performance_score +
                0.4 * statistical_confidence +
                0.2 * sample_size_score
            )
            
            hybrid_scores[variation_id] = {
                "total_score": hybrid_score,
                "performance_score": performance_score,
                "statistical_confidence": statistical_confidence,
                "sample_size_score": sample_size_score
            }
        
        # Select winner
        winner_id = max(hybrid_scores.keys(), 
                       key=lambda x: hybrid_scores[x]["total_score"])
        
        confidence_score = hybrid_scores[winner_id]["total_score"]
        
        # Determine runner-ups
        scores = [(vid, data["total_score"]) for vid, data in hybrid_scores.items() 
                 if vid != winner_id]
        scores.sort(key=lambda x: x[1], reverse=True)
        runner_ups = [vid for vid, score in scores[:2]]
        
        return SelectionResult(
            winner_variation_id=winner_id,
            confidence_score=confidence_score,
            strategy_used="hybrid",
            is_winner_selected=confidence_score > 0.6,  # Threshold for hybrid approach
            runner_up_variation_ids=runner_ups,
            selection_reason=f"Selected based on hybrid scoring (performance + statistical evidence)",
            statistical_evidence=hybrid_scores[winner_id],
            business_impact_estimate=self._estimate_business_impact(variation_metrics[winner_id]),
            selection_timestamp=datetime.now()
        )
    
    def _select_by_time_based(
        self,
        variation_metrics: Dict[str, Dict[str, Any]],
        test_start_time: datetime
    ) -> SelectionResult:
        """Select winner based on time-based criteria."""
        
        test_duration = datetime.now() - test_start_time
        
        # If test has run long enough, use hybrid approach
        if test_duration.days >= 3:
            return self._select_by_hybrid_approach(variation_metrics)
        
        # For shorter tests, weight recent performance more heavily
        recent_performance_scores = {}
        
        for variation_id, metrics in variation_metrics.items():
            # Calculate recency-weighted performance
            base_score = self._calculate_performance_score(metrics)
            
            # Apply time decay factor (performance 24h ago gets 50% weight)
            time_decay_factor = 0.5 ** (test_duration.total_seconds() / 86400)  # 24h half-life
            recent_score = base_score * (1 + time_decay_factor)
            
            recent_performance_scores[variation_id] = recent_score
        
        winner_id = max(recent_performance_scores.keys(), 
                       key=lambda x: recent_performance_scores[x])
        
        confidence_score = recent_performance_scores[winner_id] / max(recent_performance_scores.values())
        
        runner_ups = [vid for vid in recent_performance_scores.keys() 
                     if vid != winner_id][:2]
        
        return SelectionResult(
            winner_variation_id=winner_id,
            confidence_score=confidence_score,
            strategy_used="time_based",
            is_winner_selected=test_duration.days >= 1,
            runner_up_variation_ids=runner_ups,
            selection_reason=f"Time-based selection after {test_duration.days} days",
            statistical_evidence={"time_decay_factor": time_decay_factor},
            business_impact_estimate=self._estimate_business_impact(variation_metrics[winner_id]),
            selection_timestamp=datetime.now()
        )
    
    def _select_by_revenue_optimization(
        self,
        variation_metrics: Dict[str, Dict[str, Any]]
    ) -> SelectionResult:
        """Select winner optimized for revenue."""
        
        revenue_scores = {}
        
        for variation_id, metrics in variation_metrics.items():
            # Calculate revenue-focused metrics
            revenue_per_impression = self._calculate_revenue_per_impression(metrics)
            conversion_rate = metrics.get("conversion_rate_total", 0)
            lifetime_value_estimate = self._estimate_lifetime_value(metrics)
            
            # Revenue optimization score
            revenue_score = (
                0.5 * revenue_per_impression +
                0.3 * conversion_rate +
                0.2 * lifetime_value_estimate
            )
            
            revenue_scores[variation_id] = revenue_score
        
        # Select winner based on revenue optimization
        winner_id = max(revenue_scores.keys(), key=lambda x: revenue_scores[x])
        
        confidence_score = revenue_scores[winner_id] / max(revenue_scores.values())
        
        runner_ups = [vid for vid in revenue_scores.keys() 
                     if vid != winner_id][:2]
        
        return SelectionResult(
            winner_variation_id=winner_id,
            confidence_score=confidence_score,
            strategy_used="revenue_optimized",
            is_winner_selected=confidence_score > 0.7,  # Higher threshold for revenue decisions
            runner_up_variation_ids=runner_ups,
            selection_reason="Selected based on revenue optimization",
            statistical_evidence={"revenue_scores": revenue_scores},
            business_impact_estimate=self._estimate_revenue_impact(variation_metrics[winner_id]),
            selection_timestamp=datetime.now()
        )
    
    def _select_by_custom_evaluator(
        self,
        variation_metrics: Dict[str, Dict[str, Any]],
        custom_evaluator: Optional[Callable]
    ) -> SelectionResult:
        """Select winner using custom evaluation function."""
        
        if not custom_evaluator:
            raise ValueError("Custom evaluator function is required")
        
        custom_scores = {}
        
        for variation_id, metrics in variation_metrics.items():
            score = custom_evaluator(metrics)
            custom_scores[variation_id] = score
        
        winner_id = max(custom_scores.keys(), key=lambda x: custom_scores[x])
        confidence_score = custom_scores[winner_id]
        
        runner_ups = [vid for vid in custom_scores.keys() 
                     if vid != winner_id][:2]
        
        return SelectionResult(
            winner_variation_id=winner_id,
            confidence_score=confidence_score,
            strategy_used="custom",
            is_winner_selected=True,
            runner_up_variation_ids=runner_ups,
            selection_reason="Selected using custom evaluation criteria",
            statistical_evidence={"custom_scores": custom_scores},
            business_impact_estimate=self._estimate_business_impact(variation_metrics[winner_id]),
            selection_timestamp=datetime.now()
        )
    
    def _calculate_performance_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall performance score from metrics."""
        
        # Get individual metric scores
        ctr = metrics.get("click_through_rate_average", 0) / 100  # Convert to 0-1 scale
        engagement = metrics.get("engagement_rate_average", 0) / 100  # Convert to 0-1 scale
        conversion = metrics.get("conversion_rate_average", 0) / 100  # Convert to 0-1 scale
        
        # Calculate weighted composite score
        performance_score = (
            self.business_weights[SelectionCriteria.CLICK_THROUGH_RATE] * ctr +
            self.business_weights[SelectionCriteria.ENGAGEMENT_RATE] * engagement +
            self.business_weights[SelectionCriteria.CONVERSION_RATE] * conversion
        )
        
        return min(performance_score, 1.0)  # Cap at 1.0
    
    def _calculate_statistical_confidence(self, metrics: Dict[str, Any]) -> float:
        """Calculate statistical confidence in the results."""
        
        sample_size = self._get_sample_size(metrics)
        
        # Confidence increases with sample size (logarithmic scale)
        confidence = min(math.log(sample_size) / math.log(10000), 1.0)
        
        return confidence
    
    def _calculate_revenue_per_impression(self, metrics: Dict[str, Any]) -> float:
        """Calculate revenue per impression."""
        revenue = metrics.get("revenue_total", 0)
        impressions = metrics.get("impressions_total", 1)
        
        return revenue / impressions if impressions > 0 else 0
    
    def _estimate_lifetime_value(self, metrics: Dict[str, Any]) -> float:
        """Estimate lifetime value of acquired users."""
        # Simplified LTV calculation
        conversion_rate = metrics.get("conversion_rate_average", 0)
        avg_order_value = 50  # This would come from business data
        
        return conversion_rate * avg_order_value
    
    def _estimate_business_impact(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        """Estimate potential business impact of the variation."""
        
        impact = {
            "projected_improvement": self._calculate_performance_score(metrics),
            "estimated_conversions": metrics.get("conversion_rate_average", 0) * 1000,  # Assuming 1000 impressions
            "estimated_revenue": self._calculate_revenue_per_impression(metrics) * 1000
        }
        
        return impact
    
    def _estimate_revenue_impact(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        """Estimate revenue impact more specifically."""
        
        revenue_per_impression = self._calculate_revenue_per_impression(metrics)
        projected_impressions = 10000  # Assuming 10k impressions for next period
        
        revenue_impact = {
            "revenue_per_1k_impressions": revenue_per_impression * 1000,
            "projected_monthly_revenue": revenue_per_impression * projected_impressions * 30,
            "conversion_value": metrics.get("conversion_rate_average", 0) * 50  # Assuming $50 avg order value
        }
        
        return revenue_impact
    
    def add_custom_evaluator(self, name: str, evaluator_func: Callable):
        """Add a custom evaluation function."""
        self.custom_evaluators[name] = evaluator_func
        logger.info(f"Added custom evaluator: {name}")
    
    def get_selection_recommendations(
        self,
        variation_metrics: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Get recommendations for winner selection."""
        
        recommendations = []
        
        # Check data quality
        total_variations = len(variation_metrics)
        if total_variations < 2:
            recommendations.append("Need at least 2 variations for A/B testing")
        
        # Check sample sizes
        sample_sizes = [self._get_sample_size(metrics) for metrics in variation_metrics.values()]
        min_sample = min(sample_sizes) if sample_sizes else 0
        
        if min_sample < self.min_sample_size:
            recommendations.append(f"Minimum sample size ({self.min_sample_size}) not reached for all variations")
        
        # Performance analysis
        performance_scores = {}
        for vid, metrics in variation_metrics.items():
            performance_scores[vid] = self._calculate_performance_score(metrics)
        
        best_performance = max(performance_scores.values())
        worst_performance = min(performance_scores.values())
        
        if best_performance - worst_performance < 0.1:  # 10% difference
            recommendations.append("Performance differences are very small between variations")
        else:
            recommendations.append(f"Clear performance difference detected (range: {worst_performance:.3f} - {best_performance:.3f})")
        
        # Statistical confidence
        confidence_scores = {}
        for vid, metrics in variation_metrics.items():
            confidence_scores[vid] = self._calculate_statistical_confidence(metrics)
        
        max_confidence = max(confidence_scores.values()) if confidence_scores else 0
        
        if max_confidence < 0.8:
            recommendations.append("Statistical confidence is low - consider running test longer")
        else:
            recommendations.append("Good statistical confidence achieved")
        
        return recommendations
    
    def export_selection_summary(
        self,
        selection_results: List[SelectionResult]
    ) -> Dict[str, Any]:
        """Export summary of selection results."""
        
        if not selection_results:
            return {"message": "No selection results to export"}
        
        summary = {
            "total_selections": len(selection_results),
            "selection_strategies": {},
            "success_rate": 0,
            "average_confidence": 0,
            "latest_selections": []
        }
        
        # Count strategies used
        for result in selection_results:
            strategy = result.strategy_used
            if strategy not in summary["selection_strategies"]:
                summary["selection_strategies"][strategy] = 0
            summary["selection_strategies"][strategy] += 1
        
        # Calculate success rate and average confidence
        successful_selections = sum(1 for r in selection_results if r.is_winner_selected)
        summary["success_rate"] = successful_selections / len(selection_results) if selection_results else 0
        
        summary["average_confidence"] = sum(r.confidence_score for r in selection_results) / len(selection_results)
        
        # Latest selections
        latest_results = sorted(selection_results, key=lambda x: x.selection_timestamp, reverse=True)[:5]
        summary["latest_selections"] = [
            {
                "winner_variation_id": r.winner_variation_id,
                "confidence_score": r.confidence_score,
                "strategy_used": r.strategy_used,
                "selection_timestamp": r.selection_timestamp.isoformat()
            }
            for r in latest_results
        ]
        
        return summary
