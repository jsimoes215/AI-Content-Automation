#!/usr/bin/env python3
"""
Test script for data validation pipeline

This script demonstrates the complete functionality of the data validation
and transformation pipeline for video idea data.
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_validation import DataValidationPipeline, ValidationResult
from decimal import Decimal


def print_separator(title: str = ""):
    """Print a visual separator"""
    if title:
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")
    else:
        print(f"{'-'*60}")


def print_result(result: ValidationResult, index: int):
    """Pretty print validation result"""
    print(f"\n--- Idea {index} ---")
    print(f"Status: {'✅ VALID' if result.is_valid else '❌ INVALID'}")
    print(f"Quality Score: {result.quality_score}/10")
    print(f"Estimated Cost: ${result.estimated_cost}")
    print(f"Duplicate Score: {result.duplicate_score:.2f}")
    
    if result.errors:
        print(f"Errors: {len(result.errors)}")
        for error in result.errors:
            print(f"  • {error}")
    
    if result.warnings:
        print(f"Warnings: {len(result.warnings)}")
        for warning in result.warnings:
            print(f"  ⚠ {warning}")
    
    if result.cleaned_data:
        print(f"Cleaned Data Keys: {list(result.cleaned_data.keys())}")


def test_basic_validation():
    """Test basic validation functionality"""
    print_separator("Basic Validation Test")
    
    pipeline = DataValidationPipeline()
    
    # Test valid idea
    valid_idea = {
        "title": "10 Productivity Tips for Remote Workers",
        "description": "Discover essential productivity strategies to maximize your efficiency while working from home. Learn about time management, workspace optimization, and tools that can help you stay focused and productive in a remote work environment.",
        "target_audience": "professionals",
        "tags": "productivity, remote work, time management, work from home",
        "tone": "educational",
        "duration_estimate": "3 minutes",
        "platform": "youtube",
        "script_type": "tutorial",
        "call_to_action": "Subscribe for more productivity tips"
    }
    
    # Test invalid idea (missing required fields)
    invalid_idea = {
        "title": "Short",
        "description": "Too short"
    }
    
    print("Testing valid idea...")
    result1 = pipeline.validate_idea(valid_idea)
    print_result(result1, 1)
    
    print("\nTesting invalid idea...")
    result2 = pipeline.validate_idea(invalid_idea)
    print_result(result2, 2)


def test_duplicate_detection():
    """Test duplicate detection functionality"""
    print_separator("Duplicate Detection Test")
    
    pipeline = DataValidationPipeline()
    
    # Ideas with high similarity (potential duplicates)
    similar_ideas = [
        {
            "title": "How to Start a YouTube Channel",
            "description": "Complete guide to starting your own YouTube channel from scratch. Learn about equipment, content planning, SEO optimization, and growing your subscriber base.",
            "target_audience": "content creators",
            "script_type": "tutorial"
        },
        {
            "title": "Starting a YouTube Channel Guide",
            "description": "Step-by-step guide to launching your YouTube channel. Covers equipment, content strategy, SEO, and subscriber growth techniques.",
            "target_audience": "creators",
            "script_type": "tutorial"
        },
        {
            "title": "Complete Guide to YouTube Success",
            "description": "Everything you need to know to build a successful YouTube presence. Detailed coverage of equipment, content creation, optimization, and audience growth.",
            "target_audience": "entrepreneurs",
            "script_type": "explainer"
        }
    ]
    
    results = pipeline.validate_batch(similar_ideas)
    
    for i, result in enumerate(results):
        print_result(result, i + 1)
    
    print(f"\nDuplicate Detection Results:")
    for i, result in enumerate(results):
        similarity = result.duplicate_score
        if similarity > 0.8:
            print(f"  Idea {i+1}: High similarity ({similarity:.2f}) - Likely duplicate")
        elif similarity > 0.5:
            print(f"  Idea {i+1}: Medium similarity ({similarity:.2f}) - Review recommended")
        else:
            print(f"  Idea {i+1}: Low similarity ({similarity:.2f}) - Appears unique")


def test_cost_estimation():
    """Test cost estimation functionality"""
    print_separator("Cost Estimation Test")
    
    pipeline = DataValidationPipeline()
    
    # Different types of ideas with varying complexity
    test_ideas = [
        {
            "title": "Simple Tip Video",
            "description": "Quick productivity tip that can be implemented immediately.",
            "target_audience": "professionals",
            "script_type": "explainer",
            "duration_estimate": "60 seconds",
            "platform": "tiktok"
        },
        {
            "title": "Complex Tutorial",
            "description": "Comprehensive tutorial covering advanced topics with detailed explanations and examples.",
            "target_audience": "experts",
            "script_type": "tutorial",
            "duration_estimate": "10 minutes",
            "platform": "youtube",
            "demo_required": True
        },
        {
            "title": "Interview Style Content",
            "description": "Professional interview with industry expert discussing current trends.",
            "target_audience": "entrepreneurs",
            "script_type": "interview",
            "duration_estimate": "15 minutes",
            "platform": "linkedin",
            "brand_guidelines": True
        }
    ]
    
    for i, idea in enumerate(test_ideas):
        result = pipeline.validate_idea(idea)
        print(f"\nIdea {i+1}: {idea['title']}")
        print(f"  Script Type: {idea['script_type']}")
        print(f"  Duration: {idea['duration_estimate']}")
        print(f"  Platform: {idea['platform']}")
        print(f"  Estimated Cost: ${result.estimated_cost}")
        
        if idea.get('demo_required'):
            print(f"  + Demo complexity adder")
        if idea.get('brand_guidelines'):
            print(f"  + Brand guidelines adder")


def test_quality_scoring():
    """Test quality scoring functionality"""
    print_separator("Quality Scoring Test")
    
    pipeline = DataValidationPipeline()
    
    # Ideas with varying quality levels
    quality_test_ideas = [
        {
            "title": "A",  # Poor quality - very short title
            "description": "Short",  # Poor quality - very short description
            "target_audience": "people"  # Invalid audience
        },
        {
            "title": "Complete Guide to Starting a Successful Online Business in 2025",
            "description": """Learn the essential steps to create and grow a profitable online business. This comprehensive guide covers market research, business model selection, digital marketing strategies, e-commerce setup, customer acquisition, and scaling techniques. Perfect for aspiring entrepreneurs and small business owners looking to establish their online presence.""",
            "target_audience": "entrepreneurs",
            "tags": "business, online, entrepreneurship, marketing, e-commerce",
            "tone": "educational",
            "duration_estimate": "8 minutes",
            "platform": "youtube",
            "script_type": "tutorial",
            "call_to_action": "Download our free business plan template"
        },
        {
            "title": "Productivity Hack",
            "description": "Quick tip to be more productive",
            "target_audience": "professionals"
        }
    ]
    
    results = pipeline.validate_batch(quality_test_ideas)
    
    for i, result in enumerate(results):
        print(f"\nIdea {i+1} Quality Analysis:")
        print(f"  Overall Score: {result.quality_score}/10")
        print(f"  Title: '{quality_test_ideas[i]['title']}'")
        print(f"  Valid: {'Yes' if result.is_valid else 'No'}")
        
        # Calculate individual quality metrics
        idea = quality_test_ideas[i]
        title_len = len(idea.get('title', ''))
        desc_len = len(idea.get('description', ''))
        tag_count = len(idea.get('tags', []))
        
        print(f"  Metrics:")
        print(f"    - Title length: {title_len} chars")
        print(f"    - Description length: {desc_len} chars")
        print(f"    - Tag count: {tag_count}")


def test_data_cleaning():
    """Test data cleaning and normalization"""
    print_separator("Data Cleaning Test")
    
    pipeline = DataValidationPipeline()
    
    # Dirty data with various issues
    dirty_idea = {
        "title": "  How to   Build   a    Website  ",
        "description": "Learn how to build a website...!!! Visit our site at <script>alert('xss')</script>www.example.com",
        "target_audience": "  BEGINNERS  ",
        "tags": "  web development,  coding,  HTML, CSS,   JavaScript,  programming  ",
        "tone": "  Educational  ",
        "duration_estimate": "5 min",
        "platform": "  YOUTUBE  ",
        "script_type": "  Tutorial  "
    }
    
    print("Original (dirty) data:")
    for key, value in dirty_idea.items():
        print(f"  {key}: {repr(value)}")
    
    result = pipeline.validate_idea(dirty_idea)
    
    print("\nCleaned data:")
    if result.cleaned_data:
        for key, value in result.cleaned_data.items():
            print(f"  {key}: {repr(value)}")
    
    print(f"\nCleaning result: {'Success' if result.is_valid else 'Failed'}")
    if result.errors:
        print("Errors:", result.errors)


def test_batch_processing():
    """Test batch processing with summary statistics"""
    print_separator("Batch Processing Test")
    
    pipeline = DataValidationPipeline()
    
    # Generate a larger batch of test ideas
    batch_ideas = []
    
    # High quality ideas
    for i in range(3):
        batch_ideas.append({
            "title": f"Advanced {['Marketing', 'Productivity', 'Technology']} Strategies",
            "description": f"Comprehensive guide covering advanced strategies for modern professionals. Learn cutting-edge techniques and proven methods to achieve outstanding results in your field.",
            "target_audience": "professionals",
            "tags": f"business, strategy, advanced, {['marketing', 'productivity', 'technology'][i]}",
            "tone": "educational",
            "duration_estimate": "5 minutes",
            "platform": "youtube",
            "script_type": "tutorial"
        })
    
    # Medium quality ideas
    for i in range(3):
        batch_ideas.append({
            "title": f"Quick Tips for {['Busy Professionals', 'Entrepreneurs', 'Students']}",
            "description": "Useful tips to improve your daily workflow and achieve better results.",
            "target_audience": ["professionals", "entrepreneurs", "students"][i],
            "tags": "tips, productivity",
            "tone": "casual",
            "duration_estimate": "2 minutes",
            "platform": "tiktok"
        })
    
    # Lower quality ideas (missing fields)
    for i in range(2):
        batch_ideas.append({
            "title": f"Video {i+1}",
            "description": "Brief description"
        })
    
    print(f"Processing batch of {len(batch_ideas)} ideas...")
    
    results = pipeline.validate_batch(batch_ideas)
    
    # Print individual results
    for i, result in enumerate(results):
        print_result(result, i + 1)
    
    # Get and print summary
    summary = pipeline.get_validation_summary(results)
    
    print(f"\n{'='*60}")
    print("BATCH SUMMARY")
    print(f"{'='*60}")
    print(f"Total Ideas Processed: {summary['total_ideas']}")
    print(f"Valid Ideas: {summary['valid_ideas']} ({summary['validation_rate']*100:.1f}%)")
    print(f"Invalid Ideas: {summary['invalid_ideas']}")
    print(f"Average Quality Score: {summary['average_quality_score']}/10")
    print(f"Total Estimated Cost: ${summary['total_estimated_cost']:.2f}")
    print(f"Average Cost per Idea: ${summary['average_estimated_cost']:.2f}")
    print(f"Unique Ideas: {summary['unique_ideas']}")
    print(f"Potential Duplicates: {summary['duplicate_count']}")
    
    if summary['error_summary']:
        print(f"\nMost Common Errors:")
        for error_type, count in sorted(summary['error_summary'].items(), 
                                       key=lambda x: x[1], reverse=True):
            print(f"  • {error_type}: {count} occurrence(s)")


def test_integration_scenarios():
    """Test real-world integration scenarios"""
    print_separator("Integration Scenarios")
    
    pipeline = DataValidationPipeline()
    
    # Scenario 1: Content calendar planning
    print("\nScenario 1: Content Calendar Planning")
    content_calendar = [
        {
            "title": "Monday Motivation: Success Stories",
            "description": "Inspiring stories of successful entrepreneurs to start the week with motivation",
            "target_audience": "entrepreneurs",
            "tags": "motivation, success, stories, monday",
            "tone": "motivational",
            "duration_estimate": "3 minutes",
            "platform": "linkedin",
            "script_type": "story"
        },
        {
            "title": "Tuesday Tutorial: Excel Shortcuts",
            "description": "Essential Excel shortcuts to boost your productivity and save time",
            "target_audience": "professionals",
            "tags": "excel, productivity, shortcuts, tutorial",
            "tone": "educational",
            "duration_estimate": "4 minutes",
            "platform": "youtube",
            "script_type": "tutorial"
        },
        {
            "title": "Wednesday Wisdom: Industry Insights",
            "description": "Current trends and insights from industry experts",
            "target_audience": "experts",
            "tags": "insights, trends, industry, expert",
            "tone": "authoritative",
            "duration_estimate": "5 minutes",
            "platform": "linkedin",
            "script_type": "interview"
        }
    ]
    
    calendar_results = pipeline.validate_batch(content_calendar)
    calendar_summary = pipeline.get_validation_summary(calendar_results)
    
    print(f"  • Total videos planned: {calendar_summary['total_ideas']}")
    print(f"  • Ready to produce: {calendar_summary['valid_ideas']}")
    print(f"  • Need refinement: {calendar_summary['invalid_ideas']}")
    print(f"  • Estimated total cost: ${calendar_summary['total_estimated_cost']:.2f}")
    print(f"  • Average quality score: {calendar_summary['average_quality_score']}/10")
    
    # Scenario 2: A/B testing ideas
    print("\nScenario 2: A/B Testing Content Variants")
    ab_test_ideas = [
        {
            "title": "How to Save Money on Software Subscriptions",
            "description": "Practical tips to reduce your software costs and get more value from your subscriptions",
            "target_audience": "professionals",
            "tone": "casual",
            "script_type": "explainer",
            "platform": "tiktok"
        },
        {
            "title": "Cut Your Software Costs in Half",
            "description": "Discover proven strategies to dramatically reduce your monthly software expenses",
            "target_audience": "professionals",
            "tone": "professional",
            "script_type": "demo",
            "platform": "youtube"
        }
    ]
    
    ab_results = pipeline.validate_batch(ab_test_ideas)
    print(f"  • Test variants: {len(ab_test_ideas)}")
    for i, result in enumerate(ab_results):
        print(f"    Variant {i+1}: Quality {result.quality_score}/10, Cost ${result.estimated_cost}")


def main():
    """Run all tests"""
    print("Data Validation Pipeline - Comprehensive Test Suite")
    print("=" * 60)
    
    try:
        test_basic_validation()
        test_duplicate_detection()
        test_cost_estimation()
        test_quality_scoring()
        test_data_cleaning()
        test_batch_processing()
        test_integration_scenarios()
        
        print(f"\n{'='*60}")
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
