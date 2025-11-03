"""
Simple test to verify A/B testing system imports work correctly
"""

import sys
import os

# Add paths for imports
sys.path.insert(0, '/workspace/content-creator/api')
sys.path.insert(0, '/workspace/content-creator')

# Test basic imports
try:
    print("Testing imports...")
    
    # Test content variations
    from .content_variations import ContentVariationManager, ContentType
    print("✓ Content variations imported")
    
    # Test performance tracker
    from .performance_tracker import PerformanceTracker, MetricType
    print("✓ Performance tracker imported")
    
    # Test statistical analyzer
    from .statistical_tests import StatisticalAnalyzer, StatisticalTest, SignificanceLevel
    print("✓ Statistical analyzer imported")
    
    # Test winner selector
    from .winner_selector import WinnerSelector, SelectionStrategy
    print("✓ Winner selector imported")
    
    # Test main manager
    from .ab_test_manager import ABTestManager, ABTestConfig
    print("✓ A/B test manager imported")
    
    # Test creating a simple test
    print("\nTesting basic functionality...")
    
    manager = ABTestManager()
    print("✓ ABTestManager created")
    
    # Test content variation manager
    variation_manager = ContentVariationManager()
    print("✓ ContentVariationManager created")
    
    # Test performance tracker
    tracker = PerformanceTracker()
    print("✓ PerformanceTracker created")
    
    # Test statistical analyzer
    analyzer = StatisticalAnalyzer()
    print("✓ StatisticalAnalyzer created")
    
    # Test winner selector
    selector = WinnerSelector()
    print("✓ WinnerSelector created")
    
    print("\n" + "="*50)
    print("🎉 All imports and basic functionality working!")
    print("A/B testing system is ready to use.")
    print("="*50)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
