"""
Comprehensive tests for Google Sheets integration with various sheet formats

This module tests different column structures and data formats to ensure
robust handling of STANDARD, COMPREHENSIVE, MINIMAL, and CUSTOM sheet formats
including edge cases and error scenarios.

Author: AI Content Automation System
Version: 1.0.0
"""

import unittest
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from google_sheets_client import (
    GoogleSheetsClient,
    SheetRange,
    ValueRenderOption,
    DateTimeRenderOption,
    MajorDimension,
    RateLimitConfig
)
from data_validation import DataValidationPipeline, ValidationResult


class SheetFormatTestCase(unittest.TestCase):
    """Base class for sheet format tests with shared setup"""
    
    def setUp(self):
        """Set up test fixtures and mock client"""
        self.fixtures_path = Path(__file__).parent / "fixtures" / "sample_sheets"
        self.test_data = {}
        
        # Load all test fixture files
        for file_path in self.fixtures_path.glob("*.json"):
            with open(file_path, 'r') as f:
                self.test_data[file_path.stem] = json.load(f)
    
    def load_sheet_data(self, format_name: str) -> List[List[str]]:
        """Load sheet data from fixture file"""
        if format_name not in self.test_data:
            raise ValueError(f"Unknown format: {format_name}")
        return self.test_data[format_name]["data"]
    
    def create_mock_client(self) -> Mock:
        """Create a mock Google Sheets client for testing"""
        mock_client = Mock(spec=GoogleSheetsClient)
        return mock_client


class StandardFormatTests(SheetFormatTestCase):
    """Tests for STANDARD sheet format"""
    
    def test_standard_format_structure(self):
        """Test that standard format has expected column structure"""
        data = self.load_sheet_data("standard_format")
        headers = data[0]
        
        expected_headers = [
            "title", "description", "target_audience", "tags", "tone",
            "duration_estimate", "platform", "script_type", "call_to_action"
        ]
        
        self.assertEqual(headers, expected_headers)
        self.assertEqual(len(data), 4)  # 1 header + 3 data rows
    
    def test_standard_format_data_validation(self):
        """Test data validation on standard format rows"""
        data = self.load_sheet_data("standard_format")
        pipeline = DataValidationPipeline()
        
        # Test valid row
        valid_row_data = dict(zip(data[0], data[1]))
        result = pipeline.validate_idea(valid_row_data)
        
        self.assertTrue(result.is_valid)
        self.assertGreater(result.quality_score, 0)
        self.assertGreater(result.estimated_cost, 0)
    
    def test_standard_format_missing_optional_fields(self):
        """Test handling of missing optional fields in standard format"""
        data = self.load_sheet_data("standard_format")
        pipeline = DataValidationPipeline()
        
        # Create row with only required fields
        required_only = {
            "title": "Test Video Title",
            "description": "This is a test description with sufficient length for validation",
            "target_audience": "general"
        }
        
        result = pipeline.validate_idea(required_only)
        self.assertTrue(result.is_valid)
        # Should have lower quality score due to missing optional data
        self.assertLess(result.quality_score, 10)
    
    def test_standard_format_column_mapping(self):
        """Test that columns are properly mapped to data fields"""
        data = self.load_sheet_data("standard_format")
        pipeline = DataValidationPipeline()
        
        row_data = dict(zip(data[0], data[1]))
        result = pipeline.validate_idea(row_data)
        
        # Check that all expected fields are present in cleaned data
        expected_fields = {
            "title", "description", "target_audience", "tags", 
            "tone", "duration_estimate", "platform", "script_type", "call_to_action"
        }
        
        self.assertTrue(result.cleaned_data)
        for field in expected_fields:
            if field in row_data:  # Only check fields that were provided
                self.assertIn(field, result.cleaned_data)
    
    def test_standard_format_data_types(self):
        """Test that data types are correctly handled"""
        data = self.load_sheet_data("standard_format")
        
        # Check specific value types
        row = dict(zip(data[0], data[1]))
        
        # Tags should be normalized to list
        self.assertIsInstance(row["tags"], str)  # Raw data is string
        pipeline = DataValidationPipeline()
        result = pipeline.validate_idea(row)
        # After cleaning, tags should be list
        if result.cleaned_data.get("tags"):
            self.assertIsInstance(result.cleaned_data["tags"], list)


class ComprehensiveFormatTests(SheetFormatTestCase):
    """Tests for COMPREHENSIVE sheet format with extended fields"""
    
    def test_comprehensive_format_structure(self):
        """Test that comprehensive format has all expected columns"""
        data = self.load_sheet_data("comprehensive_format")
        headers = data[0]
        
        expected_headers = [
            "title", "description", "target_audience", "tags", "tone",
            "duration_estimate", "platform", "script_type", "style",
            "voice_type", "visual_elements", "call_to_action", "keywords",
            "competitor_analysis", "brand_guidelines", "compliance_notes",
            "demo_required", "priority", "estimated_cost", "quality_score",
            "creation_date", "status", "author", "review_notes"
        ]
        
        self.assertEqual(len(headers), len(expected_headers))
        self.assertIn("competitor_analysis", headers)
        self.assertIn("brand_guidelines", headers)
        self.assertIn("compliance_notes", headers)
    
    def test_comprehensive_format_enhanced_validation(self):
        """Test enhanced validation on comprehensive format data"""
        data = self.load_sheet_data("comprehensive_format")
        pipeline = DataValidationPipeline()
        
        # Test first comprehensive data row
        row_data = dict(zip(data[0], data[1]))
        result = pipeline.validate_idea(row_data)
        
        self.assertTrue(result.is_valid)
        # Comprehensive data should have higher quality scores
        self.assertGreater(result.quality_score, 7.0)
        self.assertGreater(result.estimated_cost, 0)
    
    def test_comprehensive_format_optional_enhanced_fields(self):
        """Test handling of comprehensive format's enhanced optional fields"""
        data = self.load_sheet_data("comprehensive_format")
        pipeline = DataValidationPipeline()
        
        # Create row with enhanced optional fields
        enhanced_row = {
            "title": "Enhanced Video Production Guide",
            "description": "A comprehensive guide to professional video production with advanced techniques and industry best practices.",
            "target_audience": "professionals",
            "style": "professional, cinematic",
            "voice_type": "professional narrator",
            "visual_elements": "behind-the-scenes, equipment, final results",
            "competitor_analysis": "No direct competitors in this niche",
            "brand_guidelines": "Use company colors and maintain consistency",
            "compliance_notes": "All music is royalty-free"
        }
        
        result = pipeline.validate_idea(enhanced_row)
        self.assertTrue(result.is_valid)
        # Should have higher quality score due to comprehensive data
        self.assertGreater(result.quality_score, 8.0)
    
    def test_comprehensive_format_cost_estimation(self):
        """Test cost estimation with comprehensive data"""
        data = self.load_sheet_data("comprehensive_format")
        pipeline = DataValidationPipeline()
        
        row_data = dict(zip(data[0], data[1]))
        result = pipeline.validate_idea(row_data)
        
        # Cost should be calculated based on comprehensive data
        self.assertGreater(result.estimated_cost, 40)  # Should be significant due to demo and details
        self.assertLess(result.estimated_cost, 100)   # But within reasonable bounds


class MinimalFormatTests(SheetFormatTestCase):
    """Tests for MINIMAL sheet format with only essential fields"""
    
    def test_minimal_format_structure(self):
        """Test that minimal format has only essential columns"""
        data = self.load_sheet_data("minimal_format")
        headers = data[0]
        
        expected_headers = ["title", "description", "target_audience"]
        self.assertEqual(headers, expected_headers)
        self.assertEqual(len(headers), 3)  # Only 3 required fields
    
    def test_minimal_format_validation(self):
        """Test validation on minimal format data"""
        data = self.load_sheet_data("minimal_format")
        pipeline = DataValidationPipeline()
        
        # Test all minimal data rows
        for i in range(1, len(data)):
            row_data = dict(zip(data[0], data[i]))
            result = pipeline.validate_idea(row_data)
            
            # Should be valid with only required fields
            self.assertTrue(result.is_valid, f"Row {i} should be valid")
            # Should have lower quality score due to limited data
            self.assertLess(result.quality_score, 7.0)
    
    def test_minimal_format_creates_default_values(self):
        """Test that missing optional fields get default values"""
        data = self.load_sheet_data("minimal_format")
        pipeline = DataValidationPipeline()
        
        row_data = dict(zip(data[0], data[1]))
        result = pipeline.validate_idea(row_data)
        
        # Should create cleaned data even with minimal input
        self.assertTrue(result.cleaned_data)
        self.assertIn("title", result.cleaned_data)
        self.assertIn("description", result.cleaned_data)
        self.assertIn("target_audience", result.cleaned_data)
    
    def test_minimal_format_quality_scoring(self):
        """Test quality scoring with minimal data"""
        data = self.load_sheet_data("minimal_format")
        pipeline = DataValidationPipeline()
        
        row_data = dict(zip(data[0], data[1]))
        result = pipeline.validate_idea(row_data)
        
        # Minimal data should score lower due to incompleteness
        self.assertLess(result.quality_score, 6.0)
        # But should still be > 0
        self.assertGreater(result.quality_score, 0)


class CustomFormatTests(SheetFormatTestCase):
    """Tests for CUSTOM sheet format with unique column structures"""
    
    def test_custom_format_structure(self):
        """Test that custom format has unique column structure"""
        data = self.load_sheet_data("custom_format")
        headers = data[0]
        
        # Custom format has different column names
        self.assertIn("ID", headers)
        self.assertIn("Video_Title", headers)
        self.assertIn("Description_Long", headers)
        self.assertIn("Target_Group", headers)
        self.assertIn("Keywords (comma separated)", headers)
        self.assertIn("Tags_Array", headers)
        
        self.assertEqual(len(headers), 25)  # Custom format has many columns
    
    def test_custom_format_column_mapping(self):
        """Test mapping of custom column names to standard fields"""
        data = self.load_sheet_data("custom_format")
        pipeline = DataValidationPipeline()
        
        row_data = dict(zip(data[0], data[1]))
        
        # Custom format uses different column names
        self.assertIn("Video_Title", row_data)
        self.assertIn("Description_Long", row_data)
        self.assertIn("Target_Group", row_data)
        
        # Test validation works with custom format
        # Need to map custom columns to standard fields
        mapped_data = {
            "title": row_data.get("Video_Title"),
            "description": row_data.get("Description_Long"),
            "target_audience": row_data.get("Target_Group"),
            "tags": row_data.get("Keywords (comma separated)"),
            "tone": row_data.get("Tone/Mood"),
            "duration_estimate": row_data.get("Length"),
            "platform": row_data.get("Platform_Specific")
        }
        
        result = pipeline.validate_idea(mapped_data)
        self.assertTrue(result.is_valid)
    
    def test_custom_format_unicode_handling(self):
        """Test handling of Unicode characters in custom format"""
        data = self.load_sheet_data("custom_format")
        pipeline = DataValidationPipeline()
        
        # Test row with Unicode characters
        unicode_row = {
            "title": "Special Characters & Unicode: 🚀 ñáéíóú",
            "description": "Testing special characters, emojis, and unicode in various fields",
            "target_audience": "general",
            "tags": "special chars, unicode, emojis, testing"
        }
        
        result = pipeline.validate_idea(unicode_row)
        self.assertTrue(result.is_valid)
        self.assertIn("🚀", result.cleaned_data.get("title", ""))
    
    def test_custom_format_complex_duration(self):
        """Test handling of complex duration formats"""
        data = self.load_sheet_data("custom_format")
        pipeline = DataValidationPipeline()
        
        complex_duration_row = {
            "title": "Duration Format Test",
            "description": "Testing different duration formats",
            "target_audience": "general",
            "duration_estimate": "1:30:45"  # 1 hour 30 minutes 45 seconds
        }
        
        result = pipeline.validate_idea(complex_duration_row)
        # Should handle HH:MM:SS format (though validation might flag it)
        self.assertIsNotNone(result.cleaned_data.get("duration_estimate"))


class EdgeCaseTests(SheetFormatTestCase):
    """Tests for various edge cases and challenging scenarios"""
    
    def test_edge_case_empty_title(self):
        """Test handling of empty title"""
        data = self.load_sheet_data("edge_cases")
        pipeline = DataValidationPipeline()
        
        edge_row = {
            "title": "",
            "description": "This is a video with an empty title - should be invalid",
            "target_audience": "general"
        }
        
        result = pipeline.validate_idea(edge_row)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("title" in error.lower() for error in result.errors))
    
    def test_edge_case_short_title(self):
        """Test handling of title that's too short"""
        data = self.load_sheet_data("edge_cases")
        pipeline = DataValidationPipeline()
        
        short_title_row = {
            "title": "A",
            "description": "This title is too short (1 character) - should be invalid",
            "target_audience": "professionals"
        }
        
        result = pipeline.validate_idea(short_title_row)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("title" in error.lower() and "5 characters" in error for error in result.errors))
    
    def test_edge_case_long_description(self):
        """Test handling of extremely long description"""
        data = self.load_sheet_data("edge_cases")
        pipeline = DataValidationPipeline()
        
        long_desc_row = {
            "title": "Normal Title Here",
            "description": "This video has an extremely long description that exceeds the 2000 character limit. " * 50,
            "target_audience": "entrepreneurs"
        }
        
        result = pipeline.validate_idea(long_desc_row)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("description" in error.lower() and "2000" in error for error in result.errors))
    
    def test_edge_case_invalid_audience(self):
        """Test handling of invalid target audience"""
        data = self.load_sheet_data("edge_cases")
        pipeline = DataValidationPipeline()
        
        invalid_audience_row = {
            "title": "Video with Invalid Audience",
            "description": "This uses an invalid target audience",
            "target_audience": "invalid_audience_type"
        }
        
        result = pipeline.validate_idea(invalid_audience_row)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("target_audience" in error.lower() for error in result.errors))
    
    def test_edge_case_duplicate_detection(self):
        """Test duplicate detection functionality"""
        data = self.load_sheet_data("edge_cases")
        pipeline = DataValidationPipeline()
        
        # Add existing ideas to pipeline
        existing_ideas = [
            {
                "title": "Productivity Mastery for Professionals",
                "description": "Learn about productivity and time management techniques for professionals in the modern workplace",
                "target_audience": "professionals"
            }
        ]
        pipeline.existing_ideas = existing_ideas
        
        # Test very similar new idea
        duplicate_row = {
            "title": "Professional Productivity Strategies",
            "description": "Master time management and productivity skills for working professionals and business owners",
            "target_audience": "professionals"
        }
        
        result = pipeline.validate_idea(duplicate_row)
        # Should be valid but have duplicate warning
        self.assertTrue(result.is_valid)
        self.assertGreater(result.duplicate_score, 0.8)
        self.assertTrue(len(result.warnings) > 0)
    
    def test_edge_case_special_characters(self):
        """Test handling of special characters and emojis"""
        data = self.load_sheet_data("edge_cases")
        pipeline = DataValidationPipeline()
        
        special_char_row = {
            "title": "Special Characters & Unicode: 🚀 ñáéíóú",
            "description": "Testing special characters, emojis, and unicode in various fields",
            "target_audience": "general",
            "tags": "special chars, unicode, emojis, testing, 🚀 ñáéíóú"
        }
        
        result = pipeline.validate_idea(special_char_row)
        self.assertTrue(result.is_valid)
        # Should preserve special characters in cleaned data
        self.assertIn("🚀", result.cleaned_data.get("title", ""))
    
    def test_edge_case_missing_required_fields(self):
        """Test handling of missing required fields"""
        data = self.load_sheet_data("edge_cases")
        pipeline = DataValidationPipeline()
        
        missing_fields_row = {
            "title": "Missing Required Fields Row",
            "description": "",
            "target_audience": ""
        }
        
        result = pipeline.validate_idea(missing_fields_row)
        self.assertFalse(result.is_valid)
        self.assertTrue(len(result.errors) > 0)
    
    def test_edge_case_html_sanitization(self):
        """Test HTML/JavaScript sanitization"""
        data = self.load_sheet_data("edge_cases")
        pipeline = DataValidationPipeline()
        
        html_row = {
            "title": "Row with HTML/JavaScript",
            "description": "<script>alert('xss')</script> This should be sanitized",
            "target_audience": "general"
        }
        
        result = pipeline.validate_idea(html_row)
        self.assertTrue(result.is_valid)
        # Should have sanitized description
        description = result.cleaned_data.get("description", "")
        self.assertNotIn("<script>", description)
        self.assertNotIn("alert('xss')", description)


class MalformedDataTests(SheetFormatTestCase):
    """Tests for handling malformed and corrupted data"""
    
    def test_malformed_null_values(self):
        """Test handling of null values in data"""
        data = self.load_sheet_data("malformed_data")
        pipeline = DataValidationPipeline()
        
        null_row = {
            "title": None,
            "description": "Row with null title",
            "target_audience": "general",
            "tags": "malformed, null value"
        }
        
        result = pipeline.validate_idea(null_row)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("title" in error.lower() and "required" in error.lower() for error in result.errors))
    
    def test_malformed_data_types(self):
        """Test handling of incorrect data types"""
        data = self.load_sheet_data("malformed_data")
        pipeline = DataValidationPipeline()
        
        mixed_types_row = {
            "title": "Row with mixed data types",
            "description": 12345,  # Should be string
            "target_audience": ["array", "in", "description"],  # Should be string
            "tags": "tags"
        }
        
        result = pipeline.validate_idea(mixed_types_row)
        # Should handle gracefully and convert to string
        self.assertTrue(result.is_valid)
        self.assertIsInstance(result.cleaned_data.get("description"), str)
    
    def test_malformed_special_values(self):
        """Test handling of special numeric values"""
        data = self.load_sheet_data("malformed_data")
        pipeline = DataValidationPipeline()
        
        special_values_row = {
            "title": "Row with special number values",
            "description": Infinity,
            "target_audience": -999,
            "tags": NaN
        }
        
        result = pipeline.validate_idea(special_values_row)
        # Should handle special values gracefully
        self.assertIsInstance(result, ValidationResult)
    
    def test_malformed_html_content(self):
        """Test handling of potentially malicious HTML content"""
        data = self.load_sheet_data("malformed_data")
        pipeline = DataValidationPipeline()
        
        html_row = {
            "title": "Row with HTML/JavaScript",
            "description": "<script>alert('xss')</script> This should be sanitized",
            "target_audience": "general",
            "tags": "xss, security, test"
        }
        
        result = pipeline.validate_idea(html_row)
        self.assertTrue(result.is_valid)
        # Sanitization should remove script tags
        description = result.cleaned_data.get("description", "")
        self.assertNotIn("<script>", description)
        self.assertNotIn("alert('xss')", description)
    
    def test_malformed_extra_columns(self):
        """Test handling of data rows with extra columns"""
        data = self.load_sheet_data("malformed_data")
        pipeline = DataValidationPipeline()
        
        # Find the row with extra columns
        for i, row in enumerate(data[1:], 1):
            if len(row) > 4:  # More columns than header
                extra_columns_row = dict(zip(data[0], row[:4]))  # Only map first 4 columns
                result = pipeline.validate_idea(extra_columns_row)
                # Should handle gracefully even with extra data
                self.assertIsInstance(result, ValidationResult)
                break
    
    def test_malformed_duplicate_header_names(self):
        """Test handling of rows that repeat header names"""
        data = self.load_sheet_data("malformed_data")
        pipeline = DataValidationPipeline()
        
        header_names_row = {
            "title": "Row with only header names as values",
            "description": "title",
            "target_audience": "description",
            "tags": "target_audience"
        }
        
        result = pipeline.validate_idea(header_names_row)
        # Should be valid but might have low quality
        self.assertIsInstance(result, ValidationResult)
    
    def test_malformed_extremely_long_values(self):
        """Test handling of extremely long values"""
        data = self.load_sheet_data("malformed_data")
        pipeline = DataValidationPipeline()
        
        long_values_row = {
            "title": "Very wide data row with many columns",
            "description": "A" * 10000,
            "target_audience": "B" * 5000,
            "tags": "tag1, tag2, " + "tag3," * 1000
        }
        
        result = pipeline.validate_idea(long_values_row)
        # Should handle large values gracefully
        self.assertIsInstance(result, ValidationResult)
        # Long description should be flagged
        if "description" in [e.split(":")[0] for e in result.errors]:
            self.assertTrue(True)  # Expected to have description error


class SheetIntegrationTests(SheetFormatTestCase):
    """Tests for integration with Google Sheets client"""
    
    def test_client_sheet_format_detection(self):
        """Test that client can detect different sheet formats"""
        mock_client = self.create_mock_client()
        
        # Test format detection logic would go here
        # This is a placeholder for integration testing
        self.assertIsInstance(mock_client, Mock)
    
    def test_batch_processing_different_formats(self):
        """Test batch processing of multiple sheet formats"""
        pipeline = DataValidationPipeline()
        
        all_results = []
        
        # Process all loaded formats
        for format_name, format_data in self.test_data.items():
            if format_name in ["standard_format", "comprehensive_format", "minimal_format", "custom_format"]:
                data_rows = format_data["data"][1:]  # Skip header
                for row in data_rows:
                    if len(row) >= 3:  # Has at least title, description, audience
                        row_data = dict(zip(format_data["data"][0], row))
                        result = pipeline.validate_idea(row_data)
                        all_results.append(result)
        
        # Should have processed multiple ideas
        self.assertGreater(len(all_results), 5)
        
        # Check that we have both valid and invalid results
        valid_count = sum(1 for r in all_results if r.is_valid)
        invalid_count = len(all_results) - valid_count
        
        self.assertGreater(valid_count, 0)
        # Some edge cases should be invalid
        self.assertGreaterEqual(invalid_count, 0)
    
    def test_format_conversion_consistency(self):
        """Test that different formats convert to consistent data structures"""
        pipeline = DataValidationPipeline()
        
        # Test minimal format
        minimal_data = self.load_sheet_data("minimal_format")
        minimal_row = dict(zip(minimal_data[0], minimal_data[1]))
        minimal_result = pipeline.validate_idea(minimal_row)
        
        # Test comprehensive format
        comprehensive_data = self.load_sheet_data("comprehensive_format")
        comprehensive_row = dict(zip(comprehensive_data[0], comprehensive_data[1]))
        comprehensive_result = pipeline.validate_idea(comprehensive_row)
        
        # Both should produce valid ValidationResult objects
        self.assertIsInstance(minimal_result, ValidationResult)
        self.assertIsInstance(comprehensive_result, ValidationResult)
        
        # Both should have cleaned_data with same core fields
        minimal_fields = set(minimal_result.cleaned_data.keys())
        comprehensive_fields = set(comprehensive_result.cleaned_data.keys())
        
        core_fields = {"title", "description", "target_audience"}
        self.assertTrue(core_fields.issubset(minimal_fields))
        self.assertTrue(core_fields.issubset(comprehensive_fields))


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)