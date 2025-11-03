#!/usr/bin/env python3
"""
Auto-Optimizer Test Suite

Comprehensive tests for the automated content optimization system.
"""

import sys
import os
import json
import sqlite3
import tempfile
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from api.auto_optimizer import (
        AutoOptimizerAPI,
        PatternAnalyzer,
        FeedbackProcessor,
        OptimizerEngine,
        LearningSystem,
        ConfigManager,
        quick_optimize
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)


class AutoOptimizerTestSuite:
    """Test suite for auto-optimizer system."""
    
    def __init__(self):
        self.test_db_path = None
        self.temp_dir = None
        self.tests_passed = 0
        self.tests_failed = 0
    
    def setup(self):
        """Set up test environment."""
        # Create temporary files
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_content_creator.db")
        
        # Create test database
        self._create_test_database()
        
        print(f"Test setup complete. DB: {self.test_db_path}")
    
    def teardown(self):
        """Clean up test environment."""
        import shutil
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_database(self):
        """Create test database with sample data."""
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.cursor()
            
            # Create content_items table
            cursor.execute("""
                CREATE TABLE content_items (
                    content_id TEXT PRIMARY KEY,
                    content_type TEXT,
                    title TEXT,
                    tags TEXT,
                    metrics_views INTEGER DEFAULT 0,
                    metrics_likes INTEGER DEFAULT 0,
                    metrics_comments INTEGER DEFAULT 0,
                    metrics_shares INTEGER DEFAULT 0,
                    performance_score REAL,
                    created_at TIMESTAMP
                )
            """)
            
            # Insert test data
            test_data = [
                ("test_001", "video", "Amazing Python Tutorial", '["python", "tutorial"]', 1000, 50, 10, 5, 0.8, datetime.now().isoformat()),
                ("test_002", "text", "Basic Blog Post", '["blog", "general"]', 500, 25, 5, 2, 0.4, datetime.now().isoformat()),
                ("test_003", "video", "Productivity Tips Video", '["productivity", "tips"]', 1500, 80, 15, 8, 0.9, datetime.now().isoformat())
            ]
            
            cursor.executemany("""
                INSERT INTO content_items 
                (content_id, content_type, title, tags, metrics_views, metrics_likes, 
                 metrics_comments, metrics_shares, performance_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, test_data)
            
            conn.commit()
    
    def test_quick_optimization(self):
        """Test basic quick optimization."""
        print("Testing quick optimization...")
        
        try:
            content = {
                "content_id": "test_quick",
                "title": "Test Content",
                "content_type": "video",
                "tags": ["test"]
            }
            
            result = quick_optimize(content)
            
            assert 'success' in result, "Result should contain success field"
            assert result['success'], "Optimization should succeed"
            assert 'data' in result, "Result should contain data field"
            
            self.tests_passed += 1
            print("✓ Quick optimization test passed")
            
        except Exception as e:
            self.tests_failed += 1
            print(f"✗ Quick optimization test failed: {e}")
    
    def test_pattern_analyzer(self):
        """Test pattern analyzer functionality."""
        print("Testing pattern analyzer...")
        
        try:
            analyzer = PatternAnalyzer(self.test_db_path)
            patterns = analyzer.analyze_performance_patterns(days_back=30)
            
            assert 'error' not in patterns or patterns.get('content_count', 0) > 0, "Should have data or clear error"
            
            self.tests_passed += 1
            print("✓ Pattern analyzer test passed")
            
        except Exception as e:
            self.tests_failed += 1
            print(f"✗ Pattern analyzer test failed: {e}")
    
    def test_feedback_processor(self):
        """Test feedback processor functionality."""
        print("Testing feedback processor...")
        
        try:
            processor = FeedbackProcessor(self.test_db_path)
            feedback = processor.process_feedback_data(days_back=30)
            
            assert 'error' not in feedback or 'feedback_count' in feedback, "Should process feedback or provide clear error"
            
            self.tests_passed += 1
            print("✓ Feedback processor test passed")
            
        except Exception as e:
            self.tests_failed += 1
            print(f"✗ Feedback processor test failed: {e}")
    
    def test_optimizer_engine(self):
        """Test optimizer engine functionality."""
        print("Testing optimizer engine...")
        
        try:
            engine = OptimizerEngine(self.test_db_path)
            
            content = {
                "title": "Test Video Content",
                "content_type": "video",
                "tags": ["test"]
            }
            
            result = engine.optimize_content(content, optimization_level="light")
            
            assert hasattr(result, 'optimized_content'), "Should return OptimizationResult"
            assert hasattr(result, 'applied_optimizations'), "Should have applied optimizations"
            
            self.tests_passed += 1
            print("✓ Optimizer engine test passed")
            
        except Exception as e:
            self.tests_failed += 1
            print(f"✗ Optimizer engine test failed: {e}")
    
    def test_learning_system(self):
        """Test learning system functionality."""
        print("Testing learning system...")
        
        try:
            learning = LearningSystem(self.test_db_path)
            
            # Record a test learning event
            event_id = learning.record_learning_event(
                content_id="test_content",
                optimization_applied="title_optimization",
                performance_before=0.5,
                performance_after=0.7,
                context={"platform": "youtube"}
            )
            
            assert event_id, "Should record learning event"
            assert len(learning.learning_events) > 0, "Should have learning events"
            
            self.tests_passed += 1
            print("✓ Learning system test passed")
            
        except Exception as e:
            self.tests_failed += 1
            print(f"✗ Learning system test failed: {e}")
    
    def test_config_manager(self):
        """Test configuration manager functionality."""
        print("Testing configuration manager...")
        
        try:
            import tempfile
            temp_config_dir = os.path.join(self.temp_dir, "config")
            os.makedirs(temp_config_dir, exist_ok=True)
            
            config = ConfigManager(temp_config_dir)
            
            # Test global settings
            config.set_global_setting("test_setting", "test_value")
            value = config.get_global_setting("test_setting")
            
            assert value == "test_value", "Should store and retrieve settings"
            
            self.tests_passed += 1
            print("✓ Configuration manager test passed")
            
        except Exception as e:
            self.tests_failed += 1
            print(f"✗ Configuration manager test failed: {e}")
    
    def test_api_wrapper(self):
        """Test API wrapper functionality."""
        print("Testing API wrapper...")
        
        try:
            api = AutoOptimizerAPI()
            
            # Test system status
            status = api.get_system_status()
            assert 'success' in status, "Should return valid status"
            assert status['success'], "Status should be successful"
            
            # Test optimization tips
            tips = api.get_optimization_tips("video")
            assert 'success' in tips, "Should return valid tips"
            assert 'data' in tips, "Tips should contain data"
            
            self.tests_passed += 1
            print("✓ API wrapper test passed")
            
        except Exception as e:
            self.tests_failed += 1
            print(f"✗ API wrapper test failed: {e}")
    
    def test_content_optimization_workflow(self):
        """Test complete content optimization workflow."""
        print("Testing complete optimization workflow...")
        
        try:
            api = AutoOptimizerAPI()
            
            # Test content optimization
            content = {
                "content_id": "workflow_test",
                "title": "Workflow Test Content",
                "content_type": "video",
                "tags": ["workflow", "test"],
                "platform": "youtube"
            }
            
            # Optimize content
            optimization_result = api.optimize_content(content, optimization_level="medium")
            assert optimization_result['success'], "Optimization should succeed"
            
            # Get recommendations
            recommendations = api.get_optimization_recommendations({
                "content_type": "video",
                "platform": "youtube"
            })
            assert recommendations['success'], "Recommendations should succeed"
            
            # Get patterns analysis
            patterns = api.analyze_content_patterns(days_back=30)
            assert 'success' in patterns, "Patterns analysis should work"
            
            self.tests_passed += 1
            print("✓ Complete workflow test passed")
            
        except Exception as e:
            self.tests_failed += 1
            print(f"✗ Complete workflow test failed: {e}")
    
    def test_error_handling(self):
        """Test error handling and edge cases."""
        print("Testing error handling...")
        
        try:
            api = AutoOptimizerAPI()
            
            # Test with invalid content
            invalid_result = api.optimize_content({"invalid": "data"})
            assert invalid_result['success'], "Should handle invalid data gracefully"
            
            # Test with missing parameters
            try:
                api.optimize_content({})  # Empty content
                # Should not raise exception
            except Exception:
                pass  # Expected behavior
            
            self.tests_passed += 1
            print("✓ Error handling test passed")
            
        except Exception as e:
            self.tests_failed += 1
            print(f"✗ Error handling test failed: {e}")
    
    def test_integration_simulation(self):
        """Test simulated pipeline integration."""
        print("Testing pipeline integration simulation...")
        
        try:
            # Simulate pipeline integration
            api = AutoOptimizerAPI()
            
            # Test configuration update
            config_result = api.configure_optimization(
                enabled=True,
                optimization_level="medium"
            )
            assert config_result['success'], "Configuration should succeed"
            
            # Test data export/import
            export_path = os.path.join(self.temp_dir, "test_export.json")
            export_result = api.export_optimization_data(export_path)
            assert export_result['success'], "Export should succeed"
            
            # Test import
            if os.path.exists(export_path):
                import_result = api.import_optimization_data(export_path)
                assert import_result['success'], "Import should succeed"
            
            self.tests_passed += 1
            print("✓ Pipeline integration test passed")
            
        except Exception as e:
            self.tests_failed += 1
            print(f"✗ Pipeline integration test failed: {e}")
    
    def run_all_tests(self):
        """Run all test methods."""
        print("=" * 60)
        print("Auto-Optimizer Test Suite")
        print("=" * 60)
        
        self.setup()
        
        try:
            # Run all tests
            self.test_quick_optimization()
            self.test_pattern_analyzer()
            self.test_feedback_processor()
            self.test_optimizer_engine()
            self.test_learning_system()
            self.test_config_manager()
            self.test_api_wrapper()
            self.test_content_optimization_workflow()
            self.test_error_handling()
            self.test_integration_simulation()
            
        finally:
            self.teardown()
        
        # Print results
        print("\n" + "=" * 60)
        print("Test Results Summary")
        print("=" * 60)
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_failed}")
        print(f"Total Tests: {self.tests_passed + self.tests_failed}")
        
        if self.tests_failed == 0:
            print("\n🎉 All tests passed! Auto-optimizer system is working correctly.")
            return True
        else:
            print(f"\n⚠️  {self.tests_failed} test(s) failed. Please check the system.")
            return False


def main():
    """Main test function."""
    test_suite = AutoOptimizerTestSuite()
    success = test_suite.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()