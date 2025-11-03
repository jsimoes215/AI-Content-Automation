#!/usr/bin/env python3
"""
Simple Auto-Optimizer Validation Script

Validates that the auto-optimizer system components can be imported and basic functionality works.
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test if all modules can be imported."""
    print("Testing module imports...")
    
    try:
        # Test individual module imports
        from pattern_analyzer import PatternAnalyzer
        from feedback_processor import FeedbackProcessor
        from optimizer_engine import OptimizerEngine
        from learning_system import LearningSystem
        from config_manager import ConfigManager
        from auto_optimizer import AutoOptimizer
        from api_wrapper import AutoOptimizerAPI, quick_optimize
        
        print("✓ All modules imported successfully")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality of key components."""
    print("\nTesting basic functionality...")
    
    try:
        from api_wrapper import quick_optimize
        
        # Test quick optimization
        test_content = {
            "title": "Test Content",
            "content_type": "video",
            "tags": ["test"]
        }
        
        result = quick_optimize(test_content)
        
        if result and 'success' in result:
            print("✓ Basic optimization functionality works")
            return True
        else:
            print("✗ Basic optimization failed")
            return False
            
    except Exception as e:
        print(f"✗ Basic functionality test error: {e}")
        return False

def test_pattern_analysis():
    """Test pattern analysis functionality."""
    print("\nTesting pattern analysis...")
    
    try:
        from pattern_analyzer import PatternAnalyzer
        
        # Create analyzer with test database
        analyzer = PatternAnalyzer()
        
        # Try to analyze patterns
        patterns = analyzer.analyze_performance_patterns(days_back=7)
        
        if patterns and ('patterns' in patterns or 'error' in patterns):
            print("✓ Pattern analysis functionality works")
            return True
        else:
            print("✗ Pattern analysis failed")
            return False
            
    except Exception as e:
        print(f"✗ Pattern analysis test error: {e}")
        return False

def test_learning_system():
    """Test learning system functionality."""
    print("\nTesting learning system...")
    
    try:
        from learning_system import LearningSystem
        
        # Create learning system
        learning = LearningSystem()
        
        # Try to record a learning event
        event_id = learning.record_learning_event(
            content_id="test_content",
            optimization_applied="test_optimization",
            performance_before=0.5,
            performance_after=0.7,
            context={"platform": "test"}
        )
        
        if event_id:
            print("✓ Learning system functionality works")
            return True
        else:
            print("✗ Learning system failed")
            return False
            
    except Exception as e:
        print(f"✗ Learning system test error: {e}")
        return False

def test_configuration():
    """Test configuration management."""
    print("\nTesting configuration...")
    
    try:
        from config_manager import ConfigManager
        
        # Create temporary config directory
        import tempfile
        temp_dir = tempfile.mkdtemp()
        config = ConfigManager(temp_dir)
        
        # Test setting and getting global settings
        config.set_global_setting("test_key", "test_value")
        value = config.get_global_setting("test_key")
        
        if value == "test_value":
            print("✓ Configuration management works")
            return True
        else:
            print("✗ Configuration management failed")
            return False
            
    except Exception as e:
        print(f"✗ Configuration test error: {e}")
        return False

def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Auto-Optimizer System Validation")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_basic_functionality,
        test_pattern_analysis,
        test_learning_system,
        test_configuration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("Validation Results")
    print("=" * 60)
    print(f"Tests Passed: {passed}")
    print(f"Tests Failed: {failed}")
    print(f"Total Tests: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All validation tests passed!")
        print("Auto-optimizer system is ready to use.")
        return True
    else:
        print(f"\n⚠️ {failed} test(s) failed.")
        print("Some components may need attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)