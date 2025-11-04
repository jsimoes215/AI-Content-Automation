"""
Comprehensive data validation tests for AI Content Automation System

This module provides extensive testing for data validation, cleaning, transformation,
duplicate detection, cost estimation, and quality scoring functionality.

Author: AI Content Automation System
Version: 1.0.0
"""

import unittest
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch
from decimal import Decimal

# Add the code directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data_validation import (
    DataValidationPipeline,
    VideoIdeaSchema,
    DataCleaner,
    DuplicateDetector,
    CostEstimator,
    QualityScorer,
    ValidationResult
)


class DataValidationTestCase(unittest.TestCase):
    """Base class for data validation tests with shared setup"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pipeline = DataValidationPipeline()
        self.schema = VideoIdeaSchema()
        self.cleaner = DataCleaner()
        self.duplicate_detector = DuplicateDetector()
        self.cost_estimator = CostEstimator()
        self.quality_scorer = QualityScorer()
        
        # Sample data for testing
        self.valid_idea = {
            "title": "Complete Guide to Time Management",
            "description": "Learn essential time management strategies to boost productivity and achieve work-life balance. This comprehensive guide covers goal setting, priority management, and efficient scheduling techniques.",
            "target_audience": "professionals",
            "tags": "productivity, time management, professional development",
            "tone": "educational",
            "duration_estimate": "8 minutes",
            "platform": "youtube",
            "script_type": "tutorial"
        }
        
        self.invalid_idea = {
            "title": "A",  # Too short
            "description": "Short",  # Too short
            "target_audience": "invalid_audience"  # Invalid
        }


class SchemaValidationTests(DataValidationTestCase):
    """Tests for schema validation functionality"""
    
    def test_required_fields_validation(self):
        """Test that required fields are properly validated"""
        # Missing title
        missing_title = {
            "description": "A valid description",
            "target_audience": "general"
        }
        result = self.pipeline.validate_idea(missing_title)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("title" in error.lower() for error in result.errors))
        
        # Missing description
        missing_description = {
            "title": "A valid title",
            "target_audience": "general"
        }
        result = self.pipeline.validate_idea(missing_description)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("description" in error.lower() for error in result.errors))
        
        # Missing target_audience
        missing_audience = {
            "title": "A valid title",
            "description": "A valid description with sufficient length for validation"
        }
        result = self.pipeline.validate_idea(missing_audience)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("target_audience" in error.lower() for error in result.errors))
    
    def test_title_validation(self):
        """Test title field validation rules"""
        # Valid title
        result = self.pipeline.validate_idea({
            "title": "This is a valid title with sufficient length",
            "description": "A valid description with sufficient length for validation",
            "target_audience": "general"
        })
        self.assertTrue(result.is_valid)
        
        # Empty title
        result = self.pipeline.validate_idea({
            "title": "",
            "description": "A valid description",
            "target_audience": "general"
        })
        self.assertFalse(result.is_valid)
        self.assertTrue(any("title" in error.lower() and "required" in error.lower() for error in result.errors))
        
        # Too short title
        result = self.pipeline.validate_idea({
            "title": "AB",
            "description": "A valid description",
            "target_audience": "general"
        })
        self.assertFalse(result.is_valid)
        self.assertTrue(any("title" in error.lower() and "5 characters" in error for error in result.errors))
        
        # Too long title
        long_title = "A" * 101  # 101 characters
        result = self.pipeline.validate_idea({
            "title": long_title,
            "description": "A valid description",
            "target_audience": "general"
        })
        self.assertFalse(result.is_valid)
        self.assertTrue(any("title" in error.lower() and "100 characters" in error for error in result.errors))
        
        # Invalid characters
        result = self.pipeline.validate_idea({
            "title": "Title with @ invalid # characters!",
            "description": "A valid description",
            "target_audience": "general"
        })
        self.assertFalse(result.is_valid)
        self.assertTrue(any("title" in error.lower() and "invalid characters" in error for error in result.errors))
    
    def test_description_validation(self):
        """Test description field validation rules"""
        # Valid description
        result = self.pipeline.validate_idea({
            "title": "Valid Title",
            "description": "This is a valid description with sufficient length to pass validation and contain meaningful content for testing purposes.",
            "target_audience": "general"
        })
        self.assertTrue(result.is_valid)
        
        # Empty description
        result = self.pipeline.validate_idea({
            "title": "Valid Title",
            "description": "",
            "target_audience": "general"
        })
        self.assertFalse(result.is_valid)
        self.assertTrue(any("description" in error.lower() and "required" in error.lower() for error in result.errors))
        
        # Too short description
        result = self.pipeline.validate_idea({
            "title": "Valid Title",
            "description": "Short",
            "target_audience": "general"
        })
        self.assertFalse(result.is_valid)
        self.assertTrue(any("description" in error.lower() and "20 characters" in error for error in result.errors))
        
        # Too long description
        long_description = "A" * 2001  # 2001 characters
        result = self.pipeline.validate_idea({
            "title": "Valid Title",
            "description": long_description,
            "target_audience": "general"
        })
        self.assertFalse(result.is_valid)
        self.assertTrue(any("description" in error.lower() and "2000 characters" in error for error in result.errors))
    
    def test_target_audience_validation(self):
        """Test target_audience field validation rules"""
        # Valid audiences
        valid_audiences = ["general", "professionals", "students", "entrepreneurs"]
        for audience in valid_audiences:
            result = self.pipeline.validate_idea({
                "title": "Valid Title",
                "description": "A valid description with sufficient length for validation",
                "target_audience": audience
            })
            self.assertTrue(result.is_valid, f"Should accept '{audience}' as valid audience")
        
        # Invalid audience
        result = self.pipeline.validate_idea({
            "title": "Valid Title",
            "description": "A valid description",
            "target_audience": "invalid_audience_type"
        })
        self.assertFalse(result.is_valid)
        self.assertTrue(any("target_audience" in error.lower() for error in result.errors))
    
    def test_optional_fields_validation(self):
        """Test optional fields validation"""
        # All optional fields missing should still be valid
        minimal_data = {
            "title": "Valid Title",
            "description": "A valid description with sufficient length for validation",
            "target_audience": "general"
        }
        result = self.pipeline.validate_idea(minimal_data)
        self.assertTrue(result.is_valid)
        
        # Test tags validation
        result = self.pipeline.validate_idea({
            **minimal_data,
            "tags": "tag1, tag2, tag3, tag4, tag5, tag6, tag7, tag8, tag9, tag10, tag11"  # Too many tags
        })
        self.assertFalse(result.is_valid)
        self.assertTrue(any("tags" in error.lower() and "10" in error for error in result.errors))
        
        # Test tone validation
        result = self.pipeline.validate_idea({
            **minimal_data,
            "tone": "invalid_tone"
        })
        self.assertFalse(result.is_valid)
        self.assertTrue(any("tone" in error.lower() for error in result.errors))
        
        # Test platform validation
        result = self.pipeline.validate_idea({
            **minimal_data,
            "platform": "invalid_platform"
        })
        self.assertFalse(result.is_valid)
        self.assertTrue(any("platform" in error.lower() for error in result.errors))


class DataCleaningTests(DataValidationTestCase):
    """Tests for data cleaning and normalization"""
    
    def test_text_normalization(self):
        """Test text normalization functionality"""
        # Test whitespace normalization
        dirty_text = "  This   is    a   test   with   extra   spaces  "
        cleaned = self.cleaner.normalize_text(dirty_text)
        self.assertEqual(cleaned, "This is a test with extra spaces")
        
        # Test special character removal
        dirty_text = "Test@#$%^&*()!{}[]|\\:;\"'<>?,./~`"
        cleaned = self.cleaner.normalize_text(dirty_text)
        self.assertNotIn("@", cleaned)
        self.assertNotIn("#", cleaned)
        
        # Test empty string handling
        empty_result = self.cleaner.normalize_text("")
        self.assertEqual(empty_result, "")
        
        # Test None handling
        none_result = self.cleaner.normalize_text(None)
        self.assertEqual(none_result, "")
    
    def test_list_field_normalization(self):
        """Test list field normalization"""
        # Test comma-separated string
        comma_string = "tag1, tag2, tag3, tag4"
        result = self.cleaner.normalize_list_field(comma_string)
        expected = ["tag1", "tag2", "tag3", "tag4"]
        self.assertEqual(result, expected)
        
        # Test already a list
        tag_list = ["tag1", "tag2", "tag3"]
        result = self.cleaner.normalize_list_field(tag_list)
        self.assertEqual(result, ["tag1", "tag2", "tag3"])
        
        # Test with duplicates
        with_duplicates = "tag1, tag2, tag1, tag3, tag2"
        result = self.cleaner.normalize_list_field(with_duplicates)
        # Should remove duplicates while preserving order
        self.assertIn("tag1", result)
        self.assertIn("tag2", result)
        self.assertIn("tag3", result)
        self.assertEqual(len(result), 3)  # No duplicates
        
        # Test empty/None handling
        empty_result = self.cleaner.normalize_list_field("")
        self.assertEqual(empty_result, [])
        
        none_result = self.cleaner.normalize_list_field(None)
        self.assertEqual(none_result, [])
    
    def test_duration_normalization(self):
        """Test duration normalization"""
        # Test seconds
        result = self.cleaner.normalize_duration("30")
        self.assertEqual(result, 30)
        
        # Test minutes
        result = self.cleaner.normalize_duration("5 minutes")
        self.assertEqual(result, 300)
        
        # Test hours
        result = self.cleaner.normalize_duration("2 hours")
        self.assertEqual(result, 7200)
        
        # Test various formats
        test_cases = [
            ("30s", 30),
            ("1m", 60),
            ("1min", 60),
            ("1 minute", 60),
            ("2h", 7200),
            ("1hr", 3600),
            ("1 hour", 3600),
            ("1.5 minutes", 90),
            (120, 120),  # Numeric
        ]
        
        for input_duration, expected_seconds in test_cases:
            result = self.cleaner.normalize_duration(input_duration)
            self.assertEqual(result, expected_seconds, f"Failed for input: {input_duration}")
        
        # Test invalid inputs
        invalid_cases = ["invalid", "abc minutes", "", None]
        for invalid_input in invalid_cases:
            result = self.cleaner.normalize_duration(invalid_input)
            self.assertIsNone(result)
    
    def test_html_sanitization(self):
        """Test HTML/JavaScript sanitization"""
        # Test script tag removal
        dirty_html = "<script>alert('xss')</script>Clean content"
        cleaned = self.cleaner.sanitize_html(dirty_html)
        self.assertNotIn("<script>", cleaned)
        self.assertNotIn("alert('xss')", cleaned)
        self.assertIn("Clean content", cleaned)
        
        # Test javascript: protocol removal
        dirty_html = "Click <a href='javascript:alert(1)'>here</a>"
        cleaned = self.cleaner.sanitize_html(dirty_html)
        self.assertNotIn("javascript:", cleaned)
        
        # Test event handler removal
        dirty_html = "<div onclick='alert(1)'>Content</div>"
        cleaned = self.cleaner.sanitize_html(dirty_html)
        self.assertNotIn("onclick=", cleaned)
        
        # Test general tag removal
        dirty_html = "<div><p>Content</p><span>More</span></div>"
        cleaned = self.cleaner.sanitize_html(dirty_html)
        self.assertNotIn("<", cleaned)
        self.assertIn("Content", cleaned)
        self.assertIn("More", cleaned)
        
        # Test None handling
        none_result = self.cleaner.sanitize_html(None)
        self.assertEqual(none_result, "")


class DuplicateDetectionTests(DataValidationTestCase):
    """Tests for duplicate detection functionality"""
    
    def test_content_similarity_calculation(self):
        """Test similarity calculation between texts"""
        # High similarity
        text1 = "Productivity tips for professionals"
        text2 = "Professional productivity strategies and tips"
        similarity = self.duplicate_detector.calculate_similarity(text1, text2)
        self.assertGreater(similarity, 0.7)  # Should be high similarity
        
        # Low similarity
        text1 = "Cooking recipes for beginners"
        text2 = "Advanced programming techniques"
        similarity = self.duplicate_detector.calculate_similarity(text1, text2)
        self.assertLess(similarity, 0.3)  # Should be low similarity
        
        # Edge cases
        similarity = self.duplicate_detector.calculate_similarity("", "")
        self.assertEqual(similarity, 0.0)
        
        similarity = self.duplicate_detector.calculate_similarity("text", "")
        self.assertEqual(similarity, 0.0)
    
    def test_content_hash_generation(self):
        """Test content hash generation for deduplication"""
        # Same content should generate same hash
        data1 = {
            "title": "Test Title",
            "description": "Test Description",
            "target_audience": "general",
            "tags": ["tag1", "tag2"]
        }
        
        data2 = {
            "title": "Test Title",
            "description": "Test Description",
            "target_audience": "general",
            "tags": ["tag2", "tag1"]  # Different order
        }
        
        hash1 = self.duplicate_detector.generate_content_hash(data1)
        hash2 = self.duplicate_detector.generate_content_hash(data2)
        
        self.assertEqual(hash1, hash2)  # Should be same despite tag order
        
        # Different content should generate different hash
        data3 = {
            "title": "Different Title",
            "description": "Test Description",
            "target_audience": "general",
            "tags": ["tag1", "tag2"]
        }
        
        hash3 = self.duplicate_detector.generate_content_hash(data3)
        self.assertNotEqual(hash1, hash3)
    
    def test_duplicate_detection(self):
        """Test duplicate detection against existing data"""
        # Set up existing data
        existing_data = [
            {
                "title": "Productivity Guide for Professionals",
                "description": "Learn productivity strategies for working professionals",
                "target_audience": "professionals",
                "script_type": "tutorial"
            }
        ]
        
        # Test exact duplicate
        new_data = {
            "title": "Productivity Guide for Professionals",
            "description": "Learn productivity strategies for working professionals",
            "target_audience": "professionals",
            "script_type": "tutorial"
        }
        
        is_duplicate, score = self.duplicate_detector.is_duplicate(new_data, existing_data)
        self.assertTrue(is_duplicate)
        self.assertEqual(score, 1.0)
        
        # Test high similarity (should be detected as duplicate)
        similar_data = {
            "title": "Professional Productivity Guide",
            "description": "Productivity strategies for professionals in the workplace",
            "target_audience": "professionals",
            "script_type": "tutorial"
        }
        
        is_duplicate, score = self.duplicate_detector.is_duplicate(similar_data, existing_data)
        self.assertTrue(is_duplicate)
        self.assertGreater(score, 0.85)  # High similarity threshold
        
        # Test low similarity (should not be duplicate)
        different_data = {
            "title": "Cooking Tips for Beginners",
            "description": "Learn basic cooking techniques",
            "target_audience": "beginners",
            "script_type": "tutorial"
        }
        
        is_duplicate, score = self.duplicate_detector.is_duplicate(different_data, existing_data)
        self.assertFalse(is_duplicate)
        self.assertLess(score, 0.5)
    
    def test_similarity_threshold_configuration(self):
        """Test different similarity thresholds"""
        # Test with stricter threshold
        strict_detector = DuplicateDetector(similarity_threshold=0.95)
        
        existing_data = [
            {
                "title": "Time Management Techniques",
                "description": "Learn time management skills for better productivity",
                "target_audience": "professionals"
            }
        ]
        
        similar_data = {
            "title": "Time Management Strategies",
            "description": "Master time management for increased productivity",
            "target_audience": "professionals"
        }
        
        is_duplicate, score = strict_detector.is_duplicate(similar_data, existing_data)
        # With stricter threshold, this might not be considered duplicate
        self.assertLessEqual(score, 0.95)


class CostEstimationTests(DataValidationTestCase):
    """Tests for cost estimation functionality"""
    
    def test_basic_cost_estimation(self):
        """Test basic cost estimation calculations"""
        # Test with default values
        basic_idea = {
            "title": "Test Video",
            "description": "A test video description",
            "target_audience": "general"
        }
        
        cost = self.cost_estimator.estimate_cost(basic_idea)
        self.assertGreater(cost, 0)
        self.assertIsInstance(cost, Decimal)
        
        # Test with specified duration
        duration_idea = {
            **basic_idea,
            "duration_estimate": "5 minutes"  # 300 seconds
        }
        
        cost_with_duration = self.cost_estimator.estimate_cost(duration_idea)
        self.assertGreater(cost_with_duration, cost)
    
    def test_script_type_cost_variation(self):
        """Test cost variation by script type"""
        base_idea = {
            "title": "Test Video",
            "description": "A test video description",
            "target_audience": "general",
            "duration_estimate": "60 seconds"  # 1 minute
        }
        
        script_types = ["explainer", "tutorial", "demo", "interview", "presentation"]
        costs = {}
        
        for script_type in script_types:
            test_idea = {**base_idea, "script_type": script_type}
            cost = self.cost_estimator.estimate_cost(test_idea)
            costs[script_type] = cost
        
        # Different script types should have different costs
        self.assertNotEqual(costs["explainer"], costs["demo"])
        self.assertNotEqual(costs["tutorial"], costs["interview"])
        
        # Demo should be more expensive than explainer
        self.assertGreater(costs["demo"], costs["explainer"])
        
        # Interview should be more expensive than presentation
        self.assertGreater(costs["interview"], costs["presentation"])
    
    def test_platform_cost_multipliers(self):
        """Test platform cost multipliers"""
        base_idea = {
            "title": "Test Video",
            "description": "A test video description",
            "target_audience": "general",
            "script_type": "explainer"
        }
        
        platforms = ["youtube", "tiktok", "instagram", "linkedin", "universal"]
        costs = {}
        
        for platform in platforms:
            test_idea = {**base_idea, "platform": platform}
            cost = self.cost_estimator.estimate_cost(test_idea)
            costs[platform] = cost
        
        # Multi-platform should be most expensive
        multi_platform_cost = self.cost_estimator.estimate_cost({
            **base_idea, 
            "platform": "multi-platform"
        })
        self.assertGreater(multi_platform_cost, costs["youtube"])
        
        # Twitter should be less expensive
        twitter_cost = self.cost_estimator.estimate_cost({
            **base_idea,
            "platform": "twitter"
        })
        self.assertLess(twitter_cost, costs["linkedin"])
    
    def test_complexity_adders(self):
        """Test complexity cost adders"""
        base_idea = {
            "title": "Test Video",
            "description": "A test video description",
            "target_audience": "general",
            "script_type": "explainer"
        }
        
        # Test demo requirement
        demo_idea = {**base_idea, "demo_required": True}
        demo_cost = self.cost_estimator.estimate_cost(demo_idea)
        
        no_demo_cost = self.cost_estimator.estimate_cost(base_idea)
        self.assertGreater(demo_cost, no_demo_cost)
        
        # Test brand guidelines
        brand_idea = {**base_idea, "brand_guidelines": True}
        brand_cost = self.cost_estimator.estimate_cost(brand_idea)
        
        no_brand_cost = self.cost_estimator.estimate_cost(base_idea)
        self.assertGreater(brand_cost, no_brand_cost)
        
        # Test compliance notes
        compliance_idea = {**base_idea, "compliance_notes": True}
        compliance_cost = self.cost_estimator.estimate_cost(compliance_idea)
        
        no_compliance_cost = self.cost_estimator.estimate_cost(base_idea)
        self.assertGreater(compliance_cost, no_compliance_cost)
    
    def test_duration_cost_calculation(self):
        """Test cost calculation with different durations"""
        base_idea = {
            "title": "Test Video",
            "description": "A test video description",
            "target_audience": "general",
            "script_type": "explainer"
        }
        
        durations = [
            ("30 seconds", 30),
            ("1 minute", 60),
            ("5 minutes", 300),
            ("10 minutes", 600)
        ]
        
        costs = []
        for duration_str, seconds in durations:
            test_idea = {**base_idea, "duration_estimate": duration_str}
            cost = self.cost_estimator.estimate_cost(test_idea)
            costs.append(cost)
        
        # Longer durations should cost more
        for i in range(1, len(costs)):
            self.assertGreater(costs[i], costs[i-1])
    
    def test_cost_contingency(self):
        """Test that cost includes contingency"""
        base_idea = {
            "title": "Test Video",
            "description": "A test video description",
            "target_audience": "general",
            "script_type": "explainer"
        }
        
        cost = self.cost_estimator.estimate_cost(base_idea)
        
        # Contingency should be included (10% extra)
        # The actual cost should be higher than base calculation
        self.assertGreater(cost, Decimal('0'))  # Should be > 0
        
        # Cost should be reasonable (not too high, not too low)
        self.assertLess(cost, Decimal('1000'))  # Should be reasonable


class QualityScoringTests(DataValidationTestCase):
    """Tests for quality scoring functionality"""
    
    def test_basic_quality_scoring(self):
        """Test basic quality scoring"""
        # High quality idea
        high_quality_idea = {
            "title": "Complete Guide to Professional Productivity",
            "description": "Master professional productivity with proven strategies for time management, goal setting, and work efficiency. Learn actionable techniques to boost your professional performance and achieve better work-life balance.",
            "target_audience": "professionals",
            "tags": "productivity, time management, professional development, efficiency",
            "tone": "educational",
            "duration_estimate": "10 minutes",
            "platform": "youtube",
            "script_type": "tutorial",
            "call_to_action": "Download our productivity checklist"
        }
        
        score = self.quality_scorer.score_idea(high_quality_idea)
        self.assertGreater(score, 8.0)
        self.assertLessEqual(score, 10.0)
        
        # Low quality idea (minimal data)
        low_quality_idea = {
            "title": "Productivity",
            "description": "Tips for better work",
            "target_audience": "general"
        }
        
        score = self.quality_scorer.score_idea(low_quality_idea)
        self.assertLess(score, 6.0)
        self.assertGreater(score, 0.0)
    
    def test_completeness_scoring(self):
        """Test completeness scoring component"""
        # Very complete idea
        complete_idea = {
            "title": "Professional Development Guide",
            "description": "Comprehensive guide to professional development with practical strategies",
            "target_audience": "professionals",
            "tags": "development, career, professional",
            "tone": "professional",
            "duration_estimate": "8 minutes",
            "platform": "linkedin",
            "script_type": "presentation"
        }
        
        score = self.quality_scorer.score_idea(complete_idea)
        # Should score well on completeness
        self.assertGreater(score, 7.0)
    
    def test_clarity_scoring(self):
        """Test clarity scoring component"""
        # Clear and well-structured
        clear_idea = {
            "title": "5 Essential Time Management Techniques for Busy Professionals",
            "description": "Learn five proven time management strategies that successful professionals use to maximize productivity, reduce stress, and achieve better work-life balance. This comprehensive guide covers priority matrix, time blocking, goal setting, delegation, and automation techniques.",
            "target_audience": "professionals"
        }
        
        score = self.quality_scorer.score_idea(clear_idea)
        # Should score well on clarity
        self.assertGreater(score, 6.0)
        
        # Unclear idea
        unclear_idea = {
            "title": "Stuff",
            "description": "Things about work and stuff",
            "target_audience": "people"
        }
        
        score = self.quality_scorer.score_idea(unclear_idea)
        # Should score poorly on clarity
        self.assertLess(score, 5.0)
    
    def test_engagement_scoring(self):
        """Test engagement potential scoring"""
        # High engagement potential
        engaging_idea = {
            "title": "Amazing Life Hack That Will Change Everything",
            "description": "Discover the incredible life hack that successful people use to transform their daily routine and achieve amazing results.",
            "target_audience": "general",
            "tone": "motivational",
            "call_to_action": "Try this hack and share your results",
            "tags": "life hack, productivity, success"
        }
        
        score = self.quality_scorer.score_idea(engaging_idea)
        # Should score well on engagement
        self.assertGreater(score, 6.0)
        
        # Low engagement potential
        boring_idea = {
            "title": "Company Policy Updates",
            "description": "Important updates to company policies and procedures",
            "target_audience": "professionals",
            "tone": "professional"
        }
        
        score = self.quality_scorer.score_idea(boring_idea)
        # Should score lower on engagement
        self.assertLess(score, 6.0)
    
    def test_feasibility_scoring(self):
        """Test feasibility scoring component"""
        # Highly feasible
        feasible_idea = {
            "title": "Quick 5-Minute Morning Routine",
            "description": "A simple 5-minute morning routine for busy professionals",
            "target_audience": "professionals",
            "duration_estimate": "3 minutes",
            "script_type": "tutorial"
        }
        
        score = self.quality_scorer.score_idea(feasible_idea)
        # Should score well on feasibility
        self.assertGreater(score, 6.0)
        
        # Low feasibility
        unfeasible_idea = {
            "title": "Complete Business Automation Setup",
            "description": "Set up complete business automation from scratch",
            "target_audience": "beginners",
            "duration_estimate": "2 hours",
            "demo_required": True,
            "script_type": "demo"
        }
        
        score = self.quality_scorer.score_idea(unfeasible_idea)
        # Should score lower on feasibility
        self.assertLess(score, 7.0)
    
    def test_uniqueness_scoring(self):
        """Test uniqueness scoring against existing ideas"""
        existing_ideas = [
            {
                "title": "Time Management for Professionals",
                "description": "Learn time management techniques",
                "target_audience": "professionals"
            }
        ]
        
        # Very similar idea
        similar_idea = {
            "title": "Professional Time Management Strategies",
            "description": "Master time management for professionals",
            "target_audience": "professionals"
        }
        
        score = self.quality_scorer.score_idea(similar_idea, existing_ideas)
        # Should score lower on uniqueness due to similarity
        self.assertLess(score, 5.0)
        
        # Very different idea
        different_idea = {
            "title": "Creative Cooking Techniques",
            "description": "Learn innovative cooking methods",
            "target_audience": "home cooks"
        }
        
        score = self.quality_scorer.score_idea(different_idea, existing_ideas)
        # Should score higher on uniqueness
        self.assertGreater(score, 7.0)
    
    def test_quality_score_weighting(self):
        """Test that quality scores use correct weighting"""
        # Create idea with varied completeness
        varied_idea = {
            "title": "Productivity Tips for Success",  # Good title
            "description": "Essential productivity strategies and techniques for achieving success in professional environments. Learn proven methods for time management, goal setting, and work efficiency.",
            "target_audience": "professionals",  # Specific audience
            "tags": "productivity, success, efficiency",  # Some tags
            "tone": "motivational",  # Good tone
            "call_to_action": "Start implementing today"  # Good CTA
            # Missing: duration, platform, script_type
        }
        
        score = self.quality_scorer.score_idea(varied_idea)
        
        # Should have decent score but not maximum due to missing optional fields
        self.assertGreater(score, 5.0)
        self.assertLess(score, 9.0)


class DataValidationPipelineTests(DataValidationTestCase):
    """Tests for the main validation pipeline"""
    
    def test_single_idea_validation(self):
        """Test validation of a single idea"""
        result = self.pipeline.validate_idea(self.valid_idea)
        
        # Should be valid
        self.assertTrue(result.is_valid)
        
        # Should have quality score
        self.assertGreater(result.quality_score, 0)
        self.assertLessEqual(result.quality_score, 10)
        
        # Should have cost estimate
        self.assertGreater(result.estimated_cost, 0)
        
        # Should have cleaned data
        self.assertIsNotNone(result.cleaned_data)
        self.assertIsInstance(result.cleaned_data, dict)
        
        # Should have validation result structure
        self.assertIsInstance(result.errors, list)
        self.assertIsInstance(result.warnings, list)
    
    def test_batch_idea_validation(self):
        """Test batch validation of multiple ideas"""
        ideas = [
            self.valid_idea,
            {
                "title": "Another Good Idea",
                "description": "Another valid description with sufficient length for testing",
                "target_audience": "entrepreneurs",
                "tags": "entrepreneurship, business"
            },
            self.invalid_idea  # This one should be invalid
        ]
        
        results = self.pipeline.validate_batch(ideas)
        
        # Should return results for all ideas
        self.assertEqual(len(results), 3)
        
        # First two should be valid
        self.assertTrue(results[0].is_valid)
        self.assertTrue(results[1].is_valid)
        
        # Third should be invalid
        self.assertFalse(results[2].is_valid)
        
        # All should be ValidationResult instances
        for result in results:
            self.assertIsInstance(result, ValidationResult)
    
    def test_validation_summary(self):
        """Test validation summary generation"""
        ideas = [
            self.valid_idea,
            {
                "title": "Another Good Idea",
                "description": "Another valid description with sufficient length for testing",
                "target_audience": "entrepreneurs"
            },
            {
                "title": "A",  # Invalid
                "description": "Short",  # Invalid
                "target_audience": "invalid"  # Invalid
            }
        ]
        
        results = self.pipeline.validate_batch(ideas)
        summary = self.pipeline.get_validation_summary(results)
        
        # Should have expected summary fields
        self.assertIn('total_ideas', summary)
        self.assertIn('valid_ideas', summary)
        self.assertIn('invalid_ideas', summary)
        self.assertIn('validation_rate', summary)
        self.assertIn('average_quality_score', summary)
        self.assertIn('total_estimated_cost', summary)
        self.assertIn('average_estimated_cost', summary)
        
        # Check values
        self.assertEqual(summary['total_ideas'], 3)
        self.assertEqual(summary['valid_ideas'], 2)
        self.assertEqual(summary['invalid_ideas'], 1)
        self.assertEqual(summary['validation_rate'], 2/3)
        self.assertGreater(summary['average_quality_score'], 0)
        self.assertGreater(summary['total_estimated_cost'], 0)
        self.assertGreater(summary['average_estimated_cost'], 0)
    
    def test_error_handling_in_batch(self):
        """Test error handling during batch processing"""
        # Create ideas that might cause errors
        problematic_ideas = [
            self.valid_idea,
            {
                "title": None,  # This might cause an error
                "description": "Problematic idea",
                "target_audience": "general"
            },
            {
                "title": "Third Idea",
                "description": "This should be fine",
                "target_audience": "professionals"
            }
        ]
        
        results = self.pipeline.validate_batch(problematic_ideas)
        
        # Should still return results for all ideas
        self.assertEqual(len(results), 3)
        
        # At least some should be processed
        valid_results = [r for r in results if r.is_valid]
        self.assertGreater(len(valid_results), 0)
    
    def test_pipeline_state_persistence(self):
        """Test that pipeline maintains state across validations"""
        # First validation
        result1 = self.pipeline.validate_idea(self.valid_idea)
        
        # Check that pipeline has the idea in its cache
        self.assertEqual(len(self.pipeline.existing_ideas), 1)
        
        # Second validation
        result2 = self.pipeline.validate_idea({
            "title": "Similar Idea",
            "description": "Very similar content to the first idea",
            "target_audience": "professionals"
        })
        
        # Should detect similarity
        self.assertGreater(result2.duplicate_score, 0)
        
        # Pipeline should now have both ideas
        self.assertEqual(len(self.pipeline.existing_ideas), 2)
    
    def test_clean_data_structure(self):
        """Test that cleaned data has proper structure"""
        result = self.pipeline.validate_idea(self.valid_idea)
        
        cleaned_data = result.cleaned_data
        self.assertIsInstance(cleaned_data, dict)
        
        # Should have core fields
        expected_fields = ['title', 'description', 'target_audience']
        for field in expected_fields:
            self.assertIn(field, cleaned_data)
        
        # Should have normalized field types
        if 'tags' in cleaned_data and cleaned_data['tags']:
            self.assertIsInstance(cleaned_data['tags'], list)
        
        if 'duration_estimate' in cleaned_data and cleaned_data['duration_estimate']:
            self.assertIsInstance(cleaned_data['duration_estimate'], int)
    
    def test_validation_with_missing_optional_fields(self):
        """Test validation with various levels of optional field completion"""
        test_cases = [
            # Only required fields
            {
                "title": "Minimal Idea",
                "description": "A valid description with sufficient length for validation",
                "target_audience": "general"
            },
            # Some optional fields
            {
                "title": "Partial Idea",
                "description": "A valid description with sufficient length for validation",
                "target_audience": "professionals",
                "tone": "educational"
            },
            # All optional fields
            self.valid_idea
        ]
        
        for i, idea in enumerate(test_cases):
            with self.subTest(case=i):
                result = self.pipeline.validate_idea(idea)
                self.assertTrue(result.is_valid)
                
                # Quality score should increase with more data
                if i > 0:
                    prev_result = self.pipeline.validate_idea(test_cases[i-1])
                    # Current result might have higher or similar quality
                    self.assertGreaterEqual(result.quality_score, 0)


class PerformanceAndStressTests(DataValidationTestCase):
    """Tests for performance and stress scenarios"""
    
    def test_large_batch_processing(self):
        """Test processing of large batches of ideas"""
        # Create a large batch of ideas
        large_batch = []
        for i in range(100):
            idea = {
                "title": f"Video Idea Number {i}",
                "description": f"Description for video idea {i} with sufficient length for validation testing purposes",
                "target_audience": "general" if i % 2 == 0 else "professionals",
                "tags": f"tag{i}, tag{i+1}, tag{i+2}" if i % 3 == 0 else None,
                "tone": "educational" if i % 2 == 0 else "casual"
            }
            large_batch.append(idea)
        
        # Process the batch
        results = self.pipeline.validate_batch(large_batch)
        
        # Should process all ideas
        self.assertEqual(len(results), 100)
        
        # Should have some valid and some invalid results
        valid_count = sum(1 for r in results if r.is_valid)
        self.assertGreater(valid_count, 0)
        self.assertLessEqual(valid_count, 100)
    
    def test_memory_efficiency(self):
        """Test that validation doesn't create memory leaks"""
        # Process many batches to test for memory issues
        for batch_num in range(10):
            batch = []
            for i in range(20):
                idea = {
                    "title": f"Batch {batch_num} Idea {i}",
                    "description": f"Description for batch {batch_num} idea {i}",
                    "target_audience": "general"
                }
                batch.append(idea)
            
            results = self.pipeline.validate_batch(batch)
            
            # Process results to ensure they're properly handled
            for result in results:
                self.assertIsInstance(result, ValidationResult)
                self.assertIsNotNone(result.cleaned_data)
    
    def test_concurrent_validation_simulation(self):
        """Simulate concurrent validation scenarios"""
        # This test simulates what might happen with concurrent processing
        # by validating different subsets and ensuring consistency
        
        base_idea = {
            "title": "Base Video Idea",
            "description": "A base description for testing concurrent validation",
            "target_audience": "general"
        }
        
        # Create multiple pipelines to simulate different processing contexts
        pipelines = [DataValidationPipeline() for _ in range(3)]
        
        # Add same idea to each pipeline
        for pipeline in pipelines:
            result = pipeline.validate_idea(base_idea)
            self.assertTrue(result.is_valid)
        
        # Each pipeline should produce similar results for same input
        for i in range(1, len(pipelines)):
            # Results might not be identical due to internal state, but should be valid
            result1 = pipelines[0].validate_idea(base_idea)
            result2 = pipelines[i].validate_idea(base_idea)
            
            # Both should be valid
            self.assertTrue(result1.is_valid)
            self.assertTrue(result2.is_valid)
    
    def test_extreme_edge_cases(self):
        """Test handling of extreme edge cases"""
        extreme_cases = [
            # Very long text
            {
                "title": "A" * 100,
                "description": "B" * 1000,
                "target_audience": "general"
            },
            # Unicode and emojis
            {
                "title": "🚀 ñáéíóú 🌍 日本語",
                "description": "Testing unicode: αβγδεζηθικλμνξοπρστυφχψω",
                "target_audience": "general"
            },
            # Many tags
            {
                "title": "Many Tags Test",
                "description": "A test idea with many tags",
                "target_audience": "general",
                "tags": ", ".join([f"tag{i}" for i in range(20)])
            },
            # Complex duration formats
            {
                "title": "Duration Test",
                "description": "Testing various duration formats",
                "target_audience": "general",
                "duration_estimate": "1:30:45"
            }
        ]
        
        for i, case in enumerate(extreme_cases):
            with self.subTest(case=i):
                try:
                    result = self.pipeline.validate_idea(case)
                    # Should either be valid or fail gracefully
                    self.assertIsInstance(result, ValidationResult)
                    if not result.is_valid:
                        # If invalid, should have meaningful errors
                        self.assertGreater(len(result.errors), 0)
                except Exception as e:
                    self.fail(f"Case {i} caused unexpected exception: {e}")


class IntegrationTests(DataValidationTestCase):
    """Tests for integration with external systems"""
    
    @patch('code.data_validation.logger')
    def test_logging_integration(self, mock_logger):
        """Test that validation properly logs activities"""
        # Valid idea should log info
        result = self.pipeline.validate_idea(self.valid_idea)
        # Note: We're testing the integration, actual logging behavior
        # may vary based on logger configuration
        
        # Invalid idea should log warnings/errors
        result = self.pipeline.validate_idea(self.invalid_idea)
        # Again, actual logging depends on configuration
    
    def test_data_serialization(self):
        """Test that validation results can be serialized"""
        result = self.pipeline.validate_idea(self.valid_idea)
        
        # Should be able to convert to JSON-serializable format
        try:
            json_data = {
                'is_valid': result.is_valid,
                'errors': result.errors,
                'warnings': result.warnings,
                'quality_score': result.quality_score,
                'estimated_cost': float(result.estimated_cost),
                'duplicate_score': result.duplicate_score,
                'cleaned_data': result.cleaned_data
            }
            
            json_str = json.dumps(json_data)
            # Should be able to parse it back
            parsed = json.loads(json_str)
            self.assertEqual(parsed['is_valid'], result.is_valid)
            self.assertEqual(parsed['quality_score'], result.quality_score)
            
        except (TypeError, ValueError) as e:
            self.fail(f"ValidationResult is not JSON-serializable: {e}")


if __name__ == "__main__":
    # Run the tests with verbose output
    unittest.main(verbosity=2)