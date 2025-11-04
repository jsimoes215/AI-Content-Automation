#!/usr/bin/env python3
"""
Test suite for IdeaDataService to verify functionality.

This test file demonstrates the core features of the idea data service
and provides examples of how to use it for processing Google Sheets data.
"""

import json
import sys
from datetime import datetime
from typing import List, Dict, Any

# Import the service
from idea_data_service import (
    IdeaDataService,
    SheetFormat,
    ValidationLevel,
    ColumnMapping,
    BatchProcessingResult,
    ProcessedIdea
)


def create_sample_sheet_data() -> List[Dict[str, Any]]:
    """Create sample sheet data for testing."""
    return [
        {
            "Title": "Getting Started with Python",
            "Script": "Welcome to our comprehensive Python tutorial. Today we'll cover the basics of Python programming including variables, functions, and control structures.",
            "Voice": "female",
            "Style": "educational",
            "Assets": "image:python-logo.png,video:intro-demo.mp4",
            "Duration": "3:30"
        },
        {
            "Title": "Data Structures Explained",
            "Script": "Understanding data structures is crucial for efficient programming. We'll explore lists, dictionaries, sets, and tuples with practical examples.",
            "Voice": "male", 
            "Style": "professional",
            "Assets": "image:data-structures.jpg,audio:background-music.mp3",
            "Duration": "2:45"
        },
        {
            "Title": "Web Development Basics",
            "Script": "Learn the fundamentals of web development including HTML, CSS, and JavaScript. Perfect for beginners looking to start their web dev journey.",
            "Style": "energetic",
            "Assets": "code:example.html,image:web-layout.png"
        },
        {
            "Title": "Machine Learning Intro",
            "Script": "Introduction to machine learning concepts, algorithms, and practical applications. We'll cover supervised and unsupervised learning with real-world examples.",
            "Voice": "neutral",
            "Style": "professional", 
            "Assets": "image:ml-concepts.jpg,video:algorithm-demo.mp4,audio:tech-background.mp3",
            "Duration": "4:15",
            "Category": "Technology",
            "Priority": "high"
        }
    ]


def test_format_detection():
    """Test sheet format detection functionality."""
    print("=== Testing Format Detection ===")
    
    service = IdeaDataService()
    
    # Test standard format detection
    standard_headers = ["Title", "Script", "Voice", "Style", "Assets"]
    sample_rows = [{}]
    detected = service.detect_sheet_format(standard_headers, sample_rows)
    print(f"Standard format detected: {detected}")
    assert detected == SheetFormat.STANDARD
    
    # Test comprehensive format detection
    comprehensive_headers = ["Title", "Script", "Voice", "Style", "Assets", "Duration"]
    detected = service.detect_sheet_format(comprehensive_headers, sample_rows)
    print(f"Comprehensive format detected: {detected}")
    assert detected == SheetFormat.COMPREHENSIVE
    
    # Test minimal format detection
    minimal_headers = ["Title", "Script"]
    detected = service.detect_sheet_format(minimal_headers, sample_rows)
    print(f"Minimal format detected: {detected}")
    assert detected == SheetFormat.MINIMAL
    
    print("✓ Format detection tests passed\n")


def test_data_validation():
    """Test data validation and normalization."""
    print("=== Testing Data Validation ===")
    
    service = IdeaDataService(ValidationLevel.MODERATE)
    
    # Test valid data
    valid_data = {
        "A": "Test Video Title",
        "B": "This is a test script for our video content. It should be long enough to pass validation.",
        "C": "female",
        "D": "professional",
        "E": "image:test.jpg,video:demo.mp4",
        "F": "2:30"
    }
    
    result = service.validate_and_normalize_idea(valid_data, 1)
    print(f"Valid data result: {result.is_valid}")
    print(f"Normalized data: {json.dumps(result.normalized_data, indent=2)}")
    assert result.is_valid
    assert result.normalized_data["title"] == "Test Video Title"
    assert result.normalized_data["voice"] == "female"
    assert result.normalized_data["style"] == "professional"
    assert len(result.normalized_data["assets"]) == 2
    assert result.normalized_data["duration"] == 150
    
    # Test invalid data (missing required fields)
    invalid_data = {
        "A": "Short",  # Too short
        "B": "Short"   # Too short
    }
    
    result = service.validate_and_normalize_idea(invalid_data, 2)
    print(f"Invalid data result: {result.is_valid}")
    print(f"Validation errors: {result.errors}")
    assert not result.is_valid
    assert len(result.errors) > 0
    
    # Test partial data
    partial_data = {
        "A": "Valid Title Here",
        "B": "This is a valid script content for our video that should pass validation requirements.",
        "C": "male"
    }
    
    result = service.validate_and_normalize_idea(partial_data, 3)
    print(f"Partial data result: {result.is_valid}")
    print(f"Normalized data: {json.dumps(result.normalized_data, indent=2)}")
    assert result.is_valid
    assert result.normalized_data["title"] == "Valid Title Here"
    assert result.normalized_data["voice"] == "male"
    
    print("✓ Data validation tests passed\n")


def test_duration_parsing():
    """Test duration parsing functionality."""
    print("=== Testing Duration Parsing ===")
    
    service = IdeaDataService()
    
    test_cases = [
        ("30", 30),
        ("1:30", 90),
        ("2:45", 165),
        ("5m 30s", 330),
        ("2m", 120),
        ("45s", 45),
        ("1:23", 83)  # MM:SS format (1 minute 23 seconds)
    ]
    
    for duration_str, expected_seconds in test_cases:
        result = service._validate_duration({"F": duration_str}, 1)
        print(f"Duration '{duration_str}' -> {result} seconds (expected: {expected_seconds})")
        assert result == expected_seconds
    
    print("✓ Duration parsing tests passed\n")


def test_batch_processing():
    """Test batch processing functionality."""
    print("=== Testing Batch Processing ===")
    
    service = IdeaDataService()
    
    # Override the read method to return our sample data
    original_read = service.read_sheet_data
    service.read_sheet_data = lambda sheet_id, range_spec: create_sample_sheet_data()
    
    try:
        # Test single sheet processing
        result = service.process_sheet_batch("test_sheet_123", "A1:F10")
        
        print(f"Batch processing results:")
        print(f"  Total rows: {result.total_rows}")
        print(f"  Processed rows: {result.processed_rows}")
        print(f"  Successful validations: {result.successful_validations}")
        print(f"  Failed validations: {result.failed_validations}")
        print(f"  Format detected: {result.format_detected}")
        print(f"  Processing time: {result.processing_time_ms:.2f}ms")
        
        assert result.total_rows == 4
        assert result.processed_rows == 4
        assert result.successful_validations >= 2  # At least 2 should be valid
        assert result.format_detected == SheetFormat.COMPREHENSIVE
        
        # Check some processed ideas
        valid_ideas = [idea for idea in result.processed_ideas if idea.validation_result.is_valid]
        if valid_ideas:
            first_idea = valid_ideas[0]
            print(f"First valid idea: {first_idea.normalized_data.get('title')}")
            assert first_idea.normalized_data["title"]
        
        print("✓ Batch processing tests passed\n")
        
    finally:
        # Restore original method
        service.read_sheet_data = original_read


def test_multiple_sheets():
    """Test processing multiple sheets."""
    print("=== Testing Multiple Sheet Processing ===")
    
    service = IdeaDataService()
    
    # Mock the read method
    original_read = service.read_sheet_data
    call_count = 0
    
    def mock_read(sheet_id, range_spec):
        nonlocal call_count
        call_count += 1
        return create_sample_sheet_data()
    
    service.read_sheet_data = mock_read
    
    try:
        # Configure multiple sheets
        sheet_configs = [
            {
                "sheet_id": "sheet_1",
                "range_spec": "A1:F5"
            },
            {
                "sheet_id": "sheet_2", 
                "range_spec": "A1:Z10",
                "custom_mapping": ColumnMapping(
                    title="Title",
                    script="Content", 
                    voice="Audio",
                    style="Theme"
                )
            }
        ]
        
        # Process multiple sheets
        results = service.process_multiple_sheets(sheet_configs)
        
        print(f"Processed {len(results)} sheets")
        assert len(results) == 2
        
        # Check results
        total_rows = sum(r.total_rows for r in results)
        total_successful = sum(r.successful_validations for r in results)
        
        print(f"  Total rows across all sheets: {total_rows}")
        print(f"  Total successful validations: {total_successful}")
        
        assert total_rows == 8  # 4 rows per sheet
        assert total_successful >= 4  # At least 4 valid ideas
        
        print("✓ Multiple sheet processing tests passed\n")
        
    finally:
        service.read_sheet_data = original_read


def test_export_functionality():
    """Test export functionality."""
    print("=== Testing Export Functionality ===")
    
    service = IdeaDataService()
    
    # Create sample processed ideas
    processed_ideas = []
    
    for i, data in enumerate(create_sample_sheet_data()):
        # Make some valid and some invalid
        is_valid = i % 2 == 0
        
        validation_result = type('ValidationResult', (), {
            'is_valid': is_valid,
            'errors': [] if is_valid else ['Missing required field'],
            'warnings': ['Optional field missing'] if not is_valid else [],
            'normalized_data': {
                'title': data.get('A', ''),
                'script': data.get('B', ''),
                'voice': data.get('C', ''),
                'style': data.get('D', ''),
                'duration': 150,
                'assets': [{'type': 'image', 'reference': 'test.jpg'}]
            } if is_valid else {}
        })()
        
        idea = ProcessedIdea(
            id=f"idea_{i+1}",
            row_index=i+1,
            raw_data=data,
            normalized_data=validation_result.normalized_data,
            validation_result=validation_result,
            sheet_format=SheetFormat.STANDARD
        )
        processed_ideas.append(idea)
    
    # Test JSON export
    json_export = service.export_processed_ideas(processed_ideas, "json")
    print("JSON export generated successfully")
    print(f"Export length: {len(json_export)} characters")
    
    # Verify JSON is valid
    parsed = json.loads(json_export)
    assert parsed["total_ideas"] == 4
    assert "ideas" in parsed
    
    # Test CSV export
    csv_export = service.export_processed_ideas(processed_ideas, "csv")
    print("CSV export generated successfully")
    print(f"CSV has {len(csv_export.split('\\n'))} lines")
    
    assert "ID,Row Index" in csv_export  # Check header
    
    print("✓ Export functionality tests passed\\n")


def test_analytics():
    """Test analytics and reporting."""
    print("=== Testing Analytics ===")
    
    service = IdeaDataService()
    
    # Create sample results
    results = []
    
    for i in range(3):
        result = BatchProcessingResult(
            sheet_id=f"sheet_{i+1}",
            total_rows=10,
            processed_rows=10,
            successful_validations=8,
            failed_validations=2,
            processed_ideas=[],
            errors=[f"Error {j}" for j in range(2)],
            processing_time_ms=1500.0,
            format_detected=SheetFormat.STANDARD
        )
        results.append(result)
    
    # Generate analytics
    analytics = service.get_analytics_summary(results)
    
    print("Analytics Summary:")
    for key, value in analytics.items():
        print(f"  {key}: {value}")
    
    # Verify analytics
    assert analytics["total_sheets"] == 3
    assert analytics["total_rows"] == 30
    assert analytics["total_successful"] == 24
    assert analytics["success_rate"] == 80.0
    assert analytics["format_distribution"]["standard"] == 3
    
    print("✓ Analytics tests passed\\n")


def run_all_tests():
    """Run all tests."""
    print("Running IdeaDataService Test Suite\\n")
    print("=" * 50)
    
    try:
        test_format_detection()
        test_data_validation() 
        test_duration_parsing()
        test_batch_processing()
        test_multiple_sheets()
        test_export_functionality()
        test_analytics()
        
        print("🎉 All tests passed successfully!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)