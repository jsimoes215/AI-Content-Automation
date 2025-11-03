"""
A/B Test Manager

Main orchestration class that coordinates all A/B testing components.
Provides a unified interface for creating, running, and analyzing tests.
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .content_variations import (
    ContentVariationManager, ContentType, VariationStatus, ContentVariation
)
from .performance_tracker import (
    PerformanceTracker, MetricType, PerformanceMetric
)
from .statistical_tests import (
    StatisticalAnalyzer, StatisticalTest, SignificanceLevel, StatisticalResult
)
from .winner_selector import (
    WinnerSelector, SelectionStrategy, SelectionCriteria, SelectionResult
)

logger = logging.getLogger(__name__)

class TestStatus(Enum):
    """Status of A/B tests."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ABTestConfig:
    """Configuration for A/B tests."""
    
    def __init__(
        self,
        min_sample_size: int = 100,
        significance_level: SignificanceLevel = SignificanceLevel.P05,
        test_duration_days: int = 7,
        auto_stop_enabled: bool = True,
        auto_stop_threshold: float = 0.95,
        performance_tracking_interval_minutes: int = 60
    ):
        """Initialize test configuration."""
        self.min_sample_size = min_sample_size
        self.significance_level = significance_level
        self.test_duration_days = test_duration_days
        self.auto_stop_enabled = auto_stop_enabled
        self.auto_stop_threshold = auto_stop_threshold
        self.performance_tracking_interval_minutes = performance_tracking_interval_minutes

@dataclass
class ABTest:
    """Represents an A/B test."""
    test_id: str
    name: str
    description: str
    content_type: ContentType
    status: TestStatus
    config: ABTestConfig
    variation_ids: List[str]
    created_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    winner_variation_id: Optional[str] = None
    results: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert test to dictionary."""
        data = asdict(self)
        data['content_type'] = self.content_type.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.ended_at:
            data['ended_at'] = self.ended_at.isoformat()
        return data

class ABTestManager:
    """Main manager for A/B testing operations."""
    
    def __init__(
        self,
        storage_backend: Optional[Any] = None,
        config: Optional[ABTestConfig] = None
    ):
        """Initialize the A/B test manager."""
        self.tests: Dict[str, ABTest] = {}
        self.variation_manager = ContentVariationManager(storage_backend)
        self.performance_tracker = PerformanceTracker(storage_backend)
        self.statistical_analyzer = StatisticalAnalyzer()
        self.winner_selector = WinnerSelector()
        self.config = config or ABTestConfig()
        
        # Register platform adapters
        self._register_platform_adapters()
        
        # Load existing tests
        self._load_existing_tests()
    
    def create_test(
        self,
        name: str,
        description: str,
        content_type: ContentType,
        base_content: Union[str, Dict, List],
        variation_count: int = 2,
        custom_config: Optional[ABTestConfig] = None
    ) -> str:
        """Create a new A/B test."""
        
        test_id = str(uuid.uuid4())
        config = custom_config or self.config
        
        # Create test object
        test = ABTest(
            test_id=test_id,
            name=name,
            description=description,
            content_type=content_type,
            status=TestStatus.DRAFT,
            config=config,
            variation_ids=[],
            created_at=datetime.now()
        )
        
        # Generate variations based on content type
        variations = self._generate_variations(content_type, base_content, test_id, variation_count)
        
        # Store variation IDs in test
        test.variation_ids = [v.variation_id for v in variations]
        
        # Save test
        self.tests[test_id] = test
        self._save_test(test)
        
        logger.info(f"Created A/B test '{name}' with {len(variations)} variations")
        
        return test_id
    
    def start_test(self, test_id: str) -> bool:
        """Start an A/B test."""
        
        if test_id not in self.tests:
            logger.error(f"Test {test_id} not found")
            return False
        
        test = self.tests[test_id]
        
        if test.status != TestStatus.DRAFT:
            logger.warning(f"Test {test_id} cannot be started - status: {test.status}")
            return False
        
        # Update test status
        test.status = TestStatus.RUNNING
        test.started_at = datetime.now()
        
        # Activate all variations
        for variation_id in test.variation_ids:
            self.variation_manager.update_variation_status(variation_id, VariationStatus.ACTIVE)
        
        # Set up performance tracking
        self._setup_performance_tracking(test)
        
        self._save_test(test)
        
        logger.info(f"Started A/B test {test_id}")
        return True
    
    def stop_test(self, test_id: str, force: bool = False) -> bool:
        """Stop an A/B test."""
        
        if test_id not in self.tests:
            logger.error(f"Test {test_id} not found")
            return False
        
        test = self.tests[test_id]
        
        if test.status not in [TestStatus.RUNNING, TestStatus.PAUSED]:
            logger.warning(f"Test {test_id} cannot be stopped - status: {test.status}")
            return False
        
        # Check if we should analyze results
        if not force and test.status == TestStatus.RUNNING:
            analysis_result = self.analyze_test(test_id)
            if analysis_result and analysis_result.get("should_stop", False):
                logger.info(f"Stopping test {test_id} based on analysis results")
            else:
                logger.warning("Test stopping requested but analysis suggests continuing")
        
        # Update test status
        test.status = TestStatus.COMPLETED
        test.ended_at = datetime.now()
        
        # Perform final analysis and winner selection
        final_results = self.analyze_test(test_id)
        if final_results:
            test.results = final_results
            
            if final_results.get("winner_selected"):
                test.winner_variation_id = final_results["winner_variation_id"]
                
                # Update variation statuses
                for variation_id in test.variation_ids:
                    if variation_id == test.winner_variation_id:
                        self.variation_manager.update_variation_status(variation_id, VariationStatus.WINNING)
                    else:
                        self.variation_manager.update_variation_status(variation_id, VariationStatus.LOSING)
        
        # Deactivate all variations
        for variation_id in test.variation_ids:
            self.variation_manager.update_variation_status(variation_id, VariationStatus.PAUSED)
        
        self._save_test(test)
        
        logger.info(f"Stopped A/B test {test_id}")
        return True
    
    def pause_test(self, test_id: str) -> bool:
        """Pause an A/B test."""
        
        if test_id not in self.tests:
            return False
        
        test = self.tests[test_id]
        
        if test.status != TestStatus.RUNNING:
            return False
        
        test.status = TestStatus.PAUSED
        
        # Pause variations
        for variation_id in test.variation_ids:
            self.variation_manager.update_variation_status(variation_id, VariationStatus.PAUSED)
        
        self._save_test(test)
        
        logger.info(f"Paused A/B test {test_id}")
        return True
    
    def resume_test(self, test_id: str) -> bool:
        """Resume a paused A/B test."""
        
        if test_id not in self.tests:
            return False
        
        test = self.tests[test_id]
        
        if test.status != TestStatus.PAUSED:
            return False
        
        test.status = TestStatus.RUNNING
        
        # Resume variations
        for variation_id in test.variation_ids:
            self.variation_manager.update_variation_status(variation_id, VariationStatus.ACTIVE)
        
        self._save_test(test)
        
        logger.info(f"Resumed A/B test {test_id}")
        return True
    
    def analyze_test(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Analyze test results and determine if we should stop."""
        
        if test_id not in self.tests:
            return None
        
        test = self.tests[test_id]
        
        # Collect metrics for all variations
        variation_metrics = {}
        for variation_id in test.variation_ids:
            metrics = self.performance_tracker.get_aggregated_metrics(variation_id)
            if metrics:  # Only include variations with metrics
                variation_metrics[variation_id] = metrics
        
        if not variation_metrics:
            logger.info(f"No metrics available for test {test_id} yet")
            return {"should_stop": False, "reason": "No metrics available"}
        
        # Perform statistical analysis
        if len(variation_metrics) >= 2:
            statistical_results = self._perform_statistical_analysis(variation_metrics)
        else:
            statistical_results = None
        
        # Check if we should stop the test
        should_stop, stop_reason = self._should_stop_test(test, variation_metrics, statistical_results)
        
        # Select winner if ready
        winner_selected = False
        winner_selection = None
        
        if should_stop and test.config.auto_stop_enabled:
            winner_selection = self.winner_selector.select_winner(
                variation_metrics,
                test.started_at or test.created_at,
                SelectionStrategy.HYBRID
            )
            
            winner_selected = winner_selection.is_winner_selected
        
        analysis_result = {
            "test_id": test_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "should_stop": should_stop,
            "stop_reason": stop_reason,
            "variation_count": len(variation_metrics),
            "metrics": variation_metrics,
            "statistical_analysis": statistical_results,
            "winner_selected": winner_selected,
            "winner_selection": winner_selection.to_dict() if winner_selection else None,
            "recommendations": self._get_analysis_recommendations(test, variation_metrics, statistical_results)
        }
        
        return analysis_result
    
    def get_test_status(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a test."""
        
        if test_id not in self.tests:
            return None
        
        test = self.tests[test_id]
        
        # Get current metrics
        current_metrics = {}
        for variation_id in test.variation_ids:
            metrics = self.performance_tracker.get_aggregated_metrics(variation_id)
            if metrics:
                current_metrics[variation_id] = metrics
        
        # Calculate progress
        test_duration = None
        if test.started_at:
            test_duration = datetime.now() - test.started_at
        
        status_info = {
            "test": test.to_dict(),
            "current_metrics": current_metrics,
            "test_duration_hours": test_duration.total_seconds() / 3600 if test_duration else 0,
            "variation_statuses": {
                vid: self.variation_manager.get_variation(vid).status.value
                for vid in test.variation_ids
            }
        }
        
        return status_info
    
    def get_all_tests(self, status_filter: Optional[TestStatus] = None) -> List[ABTest]:
        """Get all tests, optionally filtered by status."""
        
        tests = list(self.tests.values())
        
        if status_filter:
            tests = [t for t in tests if t.status == status_filter]
        
        return sorted(tests, key=lambda x: x.created_at, reverse=True)
    
    def delete_test(self, test_id: str) -> bool:
        """Delete a test and all its variations."""
        
        if test_id not in self.tests:
            return False
        
        test = self.tests[test_id]
        
        # Delete variations
        for variation_id in test.variation_ids:
            self.variation_manager.delete_variation(variation_id)
        
        # Remove test
        del self.tests[test_id]
        
        self._delete_test(test_id)
        
        logger.info(f"Deleted A/B test {test_id}")
        return True
    
    def export_test_data(self, test_id: str, format: str = "json") -> Dict[str, Any]:
        """Export test data for analysis."""
        
        if test_id not in self.tests:
            return {}
        
        test = self.tests[test_id]
        
        # Get all variation metrics
        variation_metrics = {}
        for variation_id in test.variation_ids:
            metrics = self.performance_tracker.get_variation_metrics(variation_id)
            variation_metrics[variation_id] = {
                "variation_details": self.variation_manager.get_variation(variation_id).to_dict(),
                "raw_metrics": [m.to_dict() for m in metrics],
                "aggregated_metrics": self.performance_tracker.get_aggregated_metrics(variation_id)
            }
        
        export_data = {
            "test_info": test.to_dict(),
            "variations": variation_metrics,
            "analysis_results": test.results,
            "export_timestamp": datetime.now().isoformat()
        }
        
        return export_data
    
    def _generate_variations(
        self,
        content_type: ContentType,
        base_content: Union[str, Dict, List],
        test_id: str,
        variation_count: int
    ) -> List[ContentVariation]:
        """Generate variations based on content type."""
        
        if content_type == ContentType.TITLE:
            return self.variation_manager.generate_title_variations(
                base_content, test_id, variation_count
            )
        elif content_type == ContentType.THUMBNAIL:
            return self.variation_manager.generate_thumbnail_variations(
                base_content, test_id, variation_count
            )
        elif content_type == ContentType.SCRIPT:
            return self.variation_manager.generate_script_variations(
                base_content, test_id, variation_count
            )
        elif content_type == ContentType.POSTING_TIME:
            base_time = datetime.fromisoformat(base_content) if isinstance(base_content, str) else base_content
            return self.variation_manager.generate_posting_time_variations(
                base_time, test_id, variation_count
            )
        else:
            raise ValueError(f"Unsupported content type: {content_type}")
    
    def _register_platform_adapters(self):
        """Register platform adapters for performance tracking."""
        
        from .performance_tracker import YouTubeAdapter, TikTokAdapter, InstagramAdapter
        
        self.performance_tracker.register_platform_adapter("youtube", YouTubeAdapter())
        self.performance_tracker.register_platform_adapter("tiktok", TikTokAdapter())
        self.performance_tracker.register_platform_adapter("instagram", InstagramAdapter())
    
    def _setup_performance_tracking(self, test: ABTest):
        """Set up automatic performance tracking for a test."""
        
        # Schedule metric collection for each platform
        platforms = ["youtube", "tiktok", "instagram"]  # This would come from test config
        
        for platform in platforms:
            self.performance_tracker.schedule_metric_collection(
                platform, test.variation_ids, test.config.performance_tracking_interval_minutes
            )
    
    def _perform_statistical_analysis(
        self,
        variation_metrics: Dict[str, Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Perform statistical analysis on variation metrics."""
        
        try:
            # Extract performance data for statistical testing
            if len(variation_metrics) < 2:
                return None
            
            # Get performance scores for each variation
            performance_data = []
            variation_ids = list(variation_metrics.keys())
            
            # Use engagement rate as primary metric for testing
            for variation_id in variation_ids:
                metrics = variation_metrics[variation_id]
                engagement_rate = metrics.get("engagement_rate_average", 0)
                
                # Generate synthetic data points based on aggregate metrics
                # In real implementation, you'd use raw data points
                data_points = [engagement_rate] * max(int(metrics.get("impressions_total", 1)), 10)
                performance_data.append(data_points)
            
            # Perform t-test between first two variations
            if len(performance_data) >= 2:
                result = self.statistical_analyzer.analyze_ab_test(
                    performance_data[0],
                    performance_data[1],
                    StatisticalTest.T_TEST,
                    self.config.significance_level
                )
                
                return {
                    "test_type": result.test_type,
                    "p_value": result.p_value,
                    "is_significant": result.is_significant,
                    "effect_size": result.effect_size,
                    "confidence_interval": result.confidence_interval
                }
            
        except Exception as e:
            logger.error(f"Statistical analysis failed: {e}")
        
        return None
    
    def _should_stop_test(
        self,
        test: ABTest,
        variation_metrics: Dict[str, Dict[str, Any]],
        statistical_results: Optional[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """Determine if test should be stopped."""
        
        # Check minimum duration
        if test.started_at:
            test_duration = datetime.now() - test.started_at
            min_duration = timedelta(days=1)  # Minimum 1 day
            
            if test_duration < min_duration:
                return False, f"Test duration ({test_duration.days} days) is less than minimum"
        
        # Check sample sizes
        for variation_id, metrics in variation_metrics.items():
            sample_size = self.performance_tracker._get_sample_size(metrics)
            if sample_size < test.config.min_sample_size:
                return False, f"Minimum sample size ({test.config.min_sample_size}) not reached"
        
        # Check statistical significance
        if statistical_results and statistical_results.get("is_significant"):
            return True, "Statistical significance achieved"
        
        # Check auto-stop criteria
        if test.config.auto_stop_enabled:
            # If we have clear performance winner
            if len(variation_metrics) >= 2:
                performance_scores = []
                for metrics in variation_metrics.values():
                    ctr = metrics.get("click_through_rate_average", 0)
                    engagement = metrics.get("engagement_rate_average", 0)
                    combined_score = (ctr + engagement) / 2
                    performance_scores.append(combined_score)
                
                max_score = max(performance_scores)
                min_score = min(performance_scores)
                
                if max_score > 0:
                    performance_margin = (max_score - min_score) / max_score
                    if performance_margin > test.config.auto_stop_threshold:
                        return True, f"Clear performance winner detected (margin: {performance_margin:.3f})"
        
        return False, "Test should continue"
    
    def _get_analysis_recommendations(
        self,
        test: ABTest,
        variation_metrics: Dict[str, Dict[str, Any]],
        statistical_results: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Get recommendations based on analysis."""
        
        recommendations = []
        
        # Check data quality
        if len(variation_metrics) < 2:
            recommendations.append("Need at least 2 variations with metrics")
        
        # Check sample sizes
        for variation_id, metrics in variation_metrics.items():
            sample_size = self.performance_tracker._get_sample_size(metrics)
            if sample_size < test.config.min_sample_size:
                recommendations.append(f"Increase sample size for variation {variation_id}")
        
        # Check statistical confidence
        if statistical_results:
            if not statistical_results.get("is_significant"):
                recommendations.append("Results not statistically significant - consider running longer")
            else:
                recommendations.append("Statistical significance achieved - consider stopping test")
        
        # Check performance differences
        if len(variation_metrics) >= 2:
            performance_scores = []
            for metrics in variation_metrics.values():
                ctr = metrics.get("click_through_rate_average", 0)
                engagement = metrics.get("engagement_rate_average", 0)
                score = (ctr + engagement) / 2
                performance_scores.append(score)
            
            max_score = max(performance_scores)
            min_score = min(performance_scores)
            
            if max_score - min_score < 0.1:  # Less than 10% difference
                recommendations.append("Performance differences are very small")
            else:
                recommendations.append("Clear performance differences detected")
        
        return recommendations
    
    def _save_test(self, test: ABTest):
        """Save test to storage backend."""
        # Implementation depends on storage backend
        logger.debug(f"Saved test {test.test_id}")
    
    def _delete_test(self, test_id: str):
        """Delete test from storage backend."""
        # Implementation depends on storage backend
        logger.debug(f"Deleted test {test_id}")
    
    def _load_existing_tests(self):
        """Load existing tests from storage backend."""
        # Implementation for loading from storage backend
        logger.debug("Loading existing tests")
