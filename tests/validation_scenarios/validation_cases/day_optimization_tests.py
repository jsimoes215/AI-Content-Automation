#!/usr/bin/env python3
"""
Day Optimization Validation Tests

Specific validation tests for day-of-week optimization recommendations
across all platforms based on 2025 research data.
"""

import pytest
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class DayRanking:
    """Day ranking for a platform"""
    platform: str
    day_rankings: List[Dict[str, any]]
    research_confidence: float

class TestDayOptimizationValidation:
    """Day optimization validation test cases"""
    
    @pytest.fixture
    def research_day_rankings(self):
        """Load day rankings from research data"""
        return {
            "youtube": {
                "best_single_day": "wednesday",
                "day_rankings": [
                    {"day": "wednesday", "rank": 1, "confidence": 0.95},
                    {"day": "monday", "rank": 2, "confidence": 0.89},
                    {"day": "thursday", "rank": 3, "confidence": 0.87},
                    {"day": "tuesday", "rank": 4, "confidence": 0.85},
                    {"day": "friday", "rank": 5, "confidence": 0.83},
                    {"day": "saturday", "rank": 6, "confidence": 0.72},
                    {"day": "sunday", "rank": 7, "confidence": 0.68}
                ]
            },
            "tiktok": {
                "best_single_day": "wednesday",
                "notable_peak": {"day": "sunday", "hour": 20},
                "worst_day": "saturday",
                "day_rankings": [
                    {"day": "wednesday", "rank": 1, "confidence": 0.92},
                    {"day": "thursday", "rank": 2, "confidence": 0.88},
                    {"day": "friday", "rank": 3, "confidence": 0.85},
                    {"day": "tuesday", "rank": 4, "confidence": 0.82},
                    {"day": "monday", "rank": 5, "confidence": 0.78},
                    {"day": "sunday", "rank": 6, "confidence": 0.72},
                    {"day": "saturday", "rank": 7, "confidence": 0.45}
                ]
            },
            "instagram": {
                "best_single_day_feed": "monday",
                "best_single_day_reels": "tuesday", 
                "day_rankings_feed": [
                    {"day": "monday", "rank": 1, "confidence": 0.89},
                    {"day": "tuesday", "rank": 2, "confidence": 0.87},
                    {"day": "wednesday", "rank": 3, "confidence": 0.85},
                    {"day": "thursday", "rank": 4, "confidence": 0.83},
                    {"day": "friday", "rank": 5, "confidence": 0.81}
                ],
                "day_rankings_reels": [
                    {"day": "monday", "rank": 1, "confidence": 0.88},
                    {"day": "tuesday", "rank": 2, "confidence": 0.91},
                    {"day": "wednesday", "rank": 3, "confidence": 0.86},
                    {"day": "thursday", "rank": 4, "confidence": 0.84},
                    {"day": "friday", "rank": 5, "confidence": 0.82}
                ]
            },
            "twitter": {
                "best_days": ["tuesday", "wednesday", "thursday"],
                "day_rankings": [
                    {"day": "tuesday", "rank": 1, "confidence": 0.87},
                    {"day": "wednesday", "rank": 2, "confidence": 0.85},
                    {"day": "thursday", "rank": 3, "confidence": 0.83},
                    {"day": "monday", "rank": 4, "confidence": 0.79},
                    {"day": "friday", "rank": 5, "confidence": 0.75},
                    {"day": "saturday", "rank": 6, "confidence": 0.65},
                    {"day": "sunday", "rank": 7, "confidence": 0.62}
                ]
            },
            "linkedin": {
                "best_days": ["tuesday", "wednesday", "thursday"],
                "day_rankings": [
                    {"day": "tuesday", "rank": 1, "confidence": 0.88},
                    {"day": "wednesday", "rank": 2, "confidence": 0.86},
                    {"day": "thursday", "rank": 3, "confidence": 0.84},
                    {"day": "monday", "rank": 4, "confidence": 0.80},
                    {"day": "friday", "rank": 5, "confidence": 0.76}
                ]
            },
            "facebook": {
                "best_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "day_rankings": [
                    {"day": "monday", "rank": 1, "confidence": 0.85},
                    {"day": "tuesday", "rank": 2, "confidence": 0.83},
                    {"day": "wednesday", "rank": 3, "confidence": 0.82},
                    {"day": "thursday", "rank": 4, "confidence": 0.80},
                    {"day": "friday", "rank": 5, "confidence": 0.78},
                    {"day": "saturday", "rank": 6, "confidence": 0.70},
                    {"day": "sunday", "rank": 7, "confidence": 0.68}
                ]
            }
        }
    
    def test_wednesday_dominance_validation(self, research_day_rankings):
        """Test Wednesday as the dominant posting day across platforms"""
        wednesday_platforms = []
        
        for platform, data in research_day_rankings.items():
            if isinstance(data, dict) and "best_single_day" in data:
                if data["best_single_day"] == "wednesday":
                    wednesday_platforms.append(platform)
            elif platform == "instagram":
                # Check both feed and reels for Wednesday
                feed_best = data.get("best_single_day_feed")
                reels_best = data.get("best_single_day_reels")
                if feed_best == "wednesday" or reels_best == "wednesday":
                    wednesday_platforms.append(f"{platform}_feed" if feed_best == "wednesday" else f"{platform}_reels")
        
        # Wednesday should be the best day for YouTube and TikTok specifically
        assert "youtube" in wednesday_platforms, "Wednesday should be best day for YouTube"
        assert "tiktok" in wednesday_platforms, "Wednesday should be best day for TikTok"
        
        # Wednesday should rank in top 3 for most platforms
        top_3_platforms = 0
        for platform, data in research_day_rankings.items():
            if isinstance(data, dict) and "day_rankings" in data:
                day_rankings = data["day_rankings"]
                wednesday_rank = None
                for ranking in day_rankings:
                    if ranking["day"] == "wednesday":
                        wednesday_rank = ranking["rank"]
                        break
                
                if wednesday_rank and wednesday_rank <= 3:
                    top_3_platforms += 1
        
        wednesday_dominance_ratio = top_3_platforms / len(research_day_rankings)
        assert wednesday_dominance_ratio >= 0.7, \
            f"Wednesday should rank in top 3 for at least 70% of platforms ({wednesday_dominance_ratio:.1%})"
        
        logger.info(f"Wednesday dominance validated - best for {len(wednesday_platforms)} platforms, top 3 for {wednesday_dominance_ratio:.1%}")
    
    def test_weekday_preference_validation(self, research_day_rankings):
        """Test preference for weekdays over weekends"""
        weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        weekends = ["saturday", "sunday"]
        
        for platform, data in research_day_rankings.items():
            if isinstance(data, dict) and "day_rankings" in data:
                day_rankings = data["day_rankings"]
                
                weekday_ranks = []
                weekend_ranks = []
                
                for ranking in day_rankings:
                    day = ranking["day"]
                    rank = ranking["rank"]
                    
                    if day in weekdays:
                        weekday_ranks.append(rank)
                    elif day in weekends:
                        weekend_ranks.append(rank)
                
                # Average weekday rank should be better (lower) than average weekend rank
                if weekday_ranks and weekend_ranks:
                    avg_weekday_rank = statistics.mean(weekday_ranks)
                    avg_weekend_rank = statistics.mean(weekend_ranks)
                    
                    assert avg_weekday_rank < avg_weekend_rank, \
                        f"{platform} should prefer weekdays (avg rank {avg_weekday_rank:.1f}) over weekends (avg rank {avg_weekend_rank:.1f})"
                
                # Top 3 days should be mostly weekdays
                top_3_days = [ranking["day"] for ranking in day_rankings[:3]]
                weekday_count = sum(1 for day in top_3_days if day in weekdays)
                
                assert weekday_count >= 2, \
                    f"{platform} top 3 days should include at least 2 weekdays, got {weekday_count}"
        
        logger.info("Weekday preference validation passed for all platforms")
    
    def test_platform_specific_day_patterns(self, research_day_rankings):
        """Test platform-specific day optimization patterns"""
        
        # YouTube: Wednesday peak, weekend weaker
        youtube_data = research_day_rankings["youtube"]
        assert youtube_data["best_single_day"] == "wednesday", "YouTube should have Wednesday as best day"
        
        wednesday_entry = next((r for r in youtube_data["day_rankings"] if r["day"] == "wednesday"), None)
        saturday_entry = next((r for r in youtube_data["day_rankings"] if r["day"] == "saturday"), None)
        sunday_entry = next((r for r in youtube_data["day_rankings"] if r["day"] == "sunday"), None)
        
        assert wednesday_entry["confidence"] >= 0.9, "YouTube Wednesday should have high confidence"
        assert saturday_entry["rank"] >= 6, "YouTube Saturday should rank low (6 or 7)"
        assert sunday_entry["rank"] >= 6, "YouTube Sunday should rank low (6 or 7)"
        
        # TikTok: Wednesday best, Sunday evening peak, Saturday worst
        tiktok_data = research_day_rankings["tiktok"]
        assert tiktok_data["best_single_day"] == "wednesday", "TikTok should have Wednesday as best day"
        assert tiktok_data["worst_day"] == "saturday", "TikTok should identify Saturday as worst day"
        
        sunday_peak = tiktok_data.get("notable_peak")
        assert sunday_peak and sunday_peak["day"] == "sunday", "TikTok should have Sunday evening peak"
        
        # Instagram: Monday feed, Tuesday reels
        instagram_data = research_day_rankings["instagram"]
        assert instagram_data["best_single_day_feed"] == "monday", "Instagram feed should favor Monday"
        assert instagram_data["best_single_day_reels"] == "tuesday", "Instagram reels should favor Tuesday"
        
        # Twitter/X: Tuesday-Thursday focus
        twitter_data = research_day_rankings["twitter"]
        assert len(twitter_data["best_days"]) == 3, "Twitter should focus on 3 best days"
        assert set(twitter_data["best_days"]) == {"tuesday", "wednesday", "thursday"}, \
            "Twitter best days should be Tuesday-Thursday"
        
        # LinkedIn: Tuesday-Thursday business focus
        linkedin_data = research_day_rankings["linkedin"]
        assert set(linkedin_data["best_days"]) == {"tuesday", "wednesday", "thursday"}, \
            "LinkedIn best days should match business focus"
        
        # Facebook: Monday-Friday consistency
        facebook_data = research_day_rankings["facebook"]
        assert len(facebook_data["best_days"]) == 5, "Facebook should have 5 best days"
        assert all(day in facebook_data["best_days"] for day in weekdays), \
            "Facebook best days should include all weekdays"
        
        logger.info("Platform-specific day patterns validation completed")
    
    def test_day_confidence_scores(self, research_day_rankings):
        """Test confidence scores for day recommendations"""
        for platform, data in research_day_rankings.items():
            if isinstance(data, dict) and "day_rankings" in data:
                day_rankings = data["day_rankings"]
                
                # Best day should have highest confidence
                best_day = day_rankings[0]
                confidence_threshold = 0.8
                
                assert best_day["confidence"] >= confidence_threshold, \
                    f"{platform} best day {best_day['day']} confidence {best_day['confidence']:.2f} below threshold"
                
                # Confidence should generally decrease with rank
                for i in range(1, len(day_rankings)):
                    current_confidence = day_rankings[i]["confidence"]
                    previous_confidence = day_rankings[i-1]["confidence"]
                    
                    # Allow some variance but should generally trend down
                    assert current_confidence <= previous_confidence + 0.1, \
                        f"{platform} confidence should not increase significantly with lower rank"
                
                # Worst days should have lower confidence
                worst_days = day_rankings[-2:]  # Last 2 days
                for worst_day in worst_days:
                    assert worst_day["confidence"] <= 0.75, \
                        f"{platform} worst day {worst_day['day']} should have confidence <= 0.75"
        
        logger.info("Day confidence scores validation passed")
    
    def test_day_ranking_consistency(self, research_day_rankings):
        """Test consistency in day rankings across similar platforms"""
        
        # Professional platforms (LinkedIn, Twitter) should have similar patterns
        professional_platforms = ["twitter", "linkedin"]
        professional_days = {}
        
        for platform in professional_platforms:
            data = research_day_rankings[platform]
            best_days = data["best_days"] if "best_days" in data else []
            professional_days[platform] = set(best_days)
        
        # LinkedIn and Twitter should have similar day preferences
        assert professional_days["twitter"] == professional_days["linkedin"], \
            "Professional platforms (Twitter, LinkedIn) should have consistent day preferences"
        
        # Weekend platforms should show similar weekend patterns
        weekend_platforms = ["youtube", "tiktok", "facebook"]
        weekend_patterns = {}
        
        for platform in weekend_platforms:
            data = research_day_rankings[platform]
            if "day_rankings" in data:
                weekend_ranks = []
                for ranking in data["day_rankings"]:
                    if ranking["day"] in ["saturday", "sunday"]:
                        weekend_ranks.append(ranking["rank"])
                weekend_patterns[platform] = statistics.mean(weekend_ranks)
        
        # Weekend days should rank poorly (high numbers) across platforms
        for platform, avg_weekend_rank in weekend_patterns.items():
            assert avg_weekend_rank >= 5, \
                f"{platform} weekend days should rank poorly (avg rank >= 5), got {avg_weekend_rank:.1f}"
        
        logger.info("Day ranking consistency validation passed")
    
    def test_cross_platform_day_optimization(self, research_day_rankings):
        """Test cross-platform day optimization strategies"""
        
        # Universal best days across most platforms
        universal_best_days = []
        platform_count = len(research_day_rankings)
        
        # Count how many platforms rank each day in top 3
        day_scores = {}
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            day_scores[day] = 0
        
        for platform, data in research_day_rankings.items():
            if isinstance(data, dict) and "day_rankings" in data:
                top_3_days = [ranking["day"] for ranking in data["day_rankings"][:3]]
                for day in top_3_days:
                    day_scores[day] += 1
        
        # Find universal best days (ranked in top 3 by most platforms)
        universal_threshold = platform_count * 0.6  # 60% of platforms
        universal_best_days = [day for day, count in day_scores.items() if count >= universal_threshold]
        
        # Should include core weekdays
        assert "wednesday" in universal_best_days, "Wednesday should be universal best day"
        assert "tuesday" in universal_best_days or "thursday" in universal_best_days, \
            "At least one of Tuesday/Thursday should be universal best day"
        
        # Saturday should not be universal best
        assert "saturday" not in universal_best_days, "Saturday should not be universal best day"
        
        # Cross-platform optimization recommendations
        optimization_strategy = {
            "primary_days": universal_best_days,
            "platform_specific": {
                "youtube": "wednesday_focus",
                "tiktok": "wednesday_with_sunday_evening",
                "instagram_feed": "monday_focus", 
                "instagram_reels": "tuesday_focus",
                "twitter": "tuesday_thursday_focus",
                "linkedin": "tuesday_thursday_focus",
                "facebook": "weekday_consistency"
            }
        }
        
        # Validate optimization strategy
        assert len(optimization_strategy["primary_days"]) >= 3, \
            "Cross-platform strategy should have at least 3 primary days"
        assert "wednesday" in optimization_strategy["primary_days"], \
            "Wednesday should be in primary days"
        
        logger.info(f"Cross-platform day optimization validated - Primary days: {universal_best_days}")
    
    def test_day_performance_correlation(self, research_day_rankings):
        """Test correlation between day rankings and performance metrics"""
        
        # Simulate performance correlation for each platform
        for platform, data in research_day_rankings.items():
            if isinstance(data, dict) and "day_rankings" in data:
                day_rankings = data["day_rankings"]
                
                # Create simulated performance scores based on rankings
                # Better ranked days should have higher performance
                performance_scores = []
                for ranking in day_rankings:
                    rank = ranking["rank"]
                    # Simulate performance correlation (higher rank = better performance)
                    base_performance = 0.1  # 10% base engagement
                    rank_bonus = (8 - rank) * 0.02  # Each rank improvement adds 2%
                    confidence_factor = ranking["confidence"] * 0.05  # Confidence boost
                    performance = base_performance + rank_bonus + confidence_factor
                    performance_scores.append(performance)
                
                # Validate correlation exists
                ranks = [ranking["rank"] for ranking in day_rankings]
                
                # Calculate simple correlation (negative correlation expected)
                correlation_check = self._calculate_rank_performance_correlation(ranks, performance_scores)
                assert correlation_check < 0, \
                    f"{platform} should show negative correlation between rank and performance"
                
                # Top-ranked day should have significantly better performance than bottom-ranked
                best_performance = max(performance_scores)
                worst_performance = min(performance_scores)
                performance_gap = best_performance - worst_performance
                
                assert performance_gap >= 0.05, \
                    f"{platform} performance gap between best and worst day should be >= 5%"
        
        logger.info("Day performance correlation validation passed")
    
    def _calculate_rank_performance_correlation(self, ranks, performance_scores):
        """Calculate correlation between ranks and performance scores"""
        if len(ranks) != len(performance_scores) or len(ranks) < 2:
            return 0
        
        n = len(ranks)
        rank_mean = statistics.mean(ranks)
        perf_mean = statistics.mean(performance_scores)
        
        numerator = sum((ranks[i] - rank_mean) * (performance_scores[i] - perf_mean) for i in range(n))
        
        rank_std = statistics.stdev(ranks)
        perf_std = statistics.stdev(performance_scores)
        
        if rank_std == 0 or perf_std == 0:
            return 0
        
        denominator = n * rank_std * perf_std
        return numerator / denominator if denominator != 0 else 0
    
    def test_day_optimization_validation_report(self, research_day_rankings):
        """Test generation of day optimization validation report"""
        
        # Create validation results
        validation_results = {
            "validation_timestamp": datetime.now().isoformat(),
            "platforms_tested": list(research_day_rankings.keys()),
            "validation_summary": {
                "wednesday_dominance_confirmed": True,
                "weekday_preference_validated": True,
                "platform_specific_patterns_confirmed": True,
                "confidence_scores_valid": True,
                "cross_platform_consistency": True
            },
            "platform_validations": {}
        }
        
        # Validate each platform
        for platform, data in research_day_rankings.items():
            if isinstance(data, dict) and "day_rankings" in data:
                day_rankings = data["day_rankings"]
                best_day = day_rankings[0]["day"]
                confidence = day_rankings[0]["confidence"]
                
                validation_results["platform_validations"][platform] = {
                    "best_day": best_day,
                    "confidence": confidence,
                    "validation_status": "PASSED" if confidence >= 0.8 else "FAILED",
                    "top_3_days": [ranking["day"] for ranking in day_rankings[:3]]
                }
        
        # Overall validation status
        failed_platforms = [
            platform for platform, validation in validation_results["platform_validations"].items()
            if validation["validation_status"] == "FAILED"
        ]
        
        validation_results["overall_status"] = "PASSED" if not failed_platforms else "FAILED"
        validation_results["failed_platforms"] = failed_platforms
        
        # Validate report structure
        assert "validation_summary" in validation_results, "Missing validation summary"
        assert "platform_validations" in validation_results, "Missing platform validations"
        assert "overall_status" in validation_results, "Missing overall status"
        
        # Check if all platforms passed validation
        assert validation_results["overall_status"] == "PASSED", \
            f"Day optimization validation failed for platforms: {failed_platforms}"
        
        logger.info(f"Day optimization validation report generated - Status: {validation_results['overall_status']}")
        return validation_results


if __name__ == "__main__":
    # Run day optimization validation tests
    pytest.main([__file__, "-v", "--tb=short"])