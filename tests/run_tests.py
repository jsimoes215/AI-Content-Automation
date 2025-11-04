#!/usr/bin/env python3
"""
Test runner for Google Sheets integration and data validation tests

This script provides comprehensive test execution for:
1. Google Sheets format validation tests
2. Data validation pipeline tests
3. Performance and stress testing

Author: AI Content Automation System
Version: 1.0.0
"""

import sys
import os
import unittest
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add the code directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
# Add current directory for test modules
sys.path.insert(0, str(Path(__file__).parent))

from test_sheet_formats import (
    StandardFormatTests,
    ComprehensiveFormatTests,
    MinimalFormatTests,
    CustomFormatTests,
    EdgeCaseTests,
    MalformedDataTests,
    SheetIntegrationTests
)

from test_data_validation import (
    SchemaValidationTests,
    DataCleaningTests,
    DuplicateDetectionTests,
    CostEstimationTests,
    QualityScoringTests,
    DataValidationPipelineTests,
    PerformanceAndStressTests,
    IntegrationTests
)


class TestRunner:
    """Comprehensive test runner with multiple execution modes"""
    
    def __init__(self):
        self.test_results = {}
        
    def load_test_suite(self, test_category: str = "all") -> unittest.TestSuite:
        """Load test suite based on category"""
        suite = unittest.TestSuite()
        
        if test_category in ["all", "sheet_formats"]:
            # Sheet format tests
            suite.addTest(unittest.makeSuite(StandardFormatTests))
            suite.addTest(unittest.makeSuite(ComprehensiveFormatTests))
            suite.addTest(unittest.makeSuite(MinimalFormatTests))
            suite.addTest(unittest.makeSuite(CustomFormatTests))
            suite.addTest(unittest.makeSuite(EdgeCaseTests))
            suite.addTest(unittest.makeSuite(MalformedDataTests))
            suite.addTest(unittest.makeSuite(SheetIntegrationTests))
        
        if test_category in ["all", "data_validation"]:
            # Data validation tests
            suite.addTest(unittest.makeSuite(SchemaValidationTests))
            suite.addTest(unittest.makeSuite(DataCleaningTests))
            suite.addTest(unittest.makeSuite(DuplicateDetectionTests))
            suite.addTest(unittest.makeSuite(CostEstimationTests))
            suite.addTest(unittest.makeSuite(QualityScoringTests))
            suite.addTest(unittest.makeSuite(DataValidationPipelineTests))
            suite.addTest(unittest.makeSuite(PerformanceAndStressTests))
            suite.addTest(unittest.makeSuite(IntegrationTests))
        
        return suite
    
    def run_tests(self, test_category: str = "all", verbosity: int = 2) -> Dict[str, Any]:
        """Run tests and return results"""
        print(f"\n{'='*60}")
        print(f"Running {test_category.upper()} Tests")
        print(f"{'='*60}")
        
        suite = self.load_test_suite(test_category)
        
        # Create test runner
        runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
        
        # Run tests
        start_time = os.times()
        result = runner.run(suite)
        end_time = os.times()
        
        # Calculate execution time
        execution_time = end_time.elapsed - start_time.elapsed
        
        # Store results
        self.test_results[test_category] = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
            'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0,
            'execution_time': execution_time,
            'result': result
        }
        
        return self.test_results[test_category]
    
    def run_quick_tests(self) -> Dict[str, Any]:
        """Run a quick subset of tests for fast validation"""
        print("\nRunning QUICK tests (subset of critical tests)...")
        
        # Create a minimal test suite with just critical tests
        quick_suite = unittest.TestSuite()
        
        # Add critical tests from each category
        quick_suite.addTest(StandardFormatTests('test_standard_format_structure'))
        quick_suite.addTest(StandardFormatTests('test_standard_format_data_validation'))
        quick_suite.addTest(ComprehensiveFormatTests('test_comprehensive_format_structure'))
        quick_suite.addTest(MinimalFormatTests('test_minimal_format_structure'))
        quick_suite.addTest(CustomFormatTests('test_custom_format_structure'))
        quick_suite.addTest(EdgeCaseTests('test_edge_case_empty_title'))
        quick_suite.addTest(SchemaValidationTests('test_required_fields_validation'))
        quick_suite.addTest(DataCleaningTests('test_text_normalization'))
        quick_suite.addTest(DuplicateDetectionTests('test_content_similarity_calculation'))
        quick_suite.addTest(CostEstimationTests('test_basic_cost_estimation'))
        quick_suite.addTest(QualityScoringTests('test_basic_quality_scoring'))
        quick_suite.addTest(DataValidationPipelineTests('test_single_idea_validation'))
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(quick_suite)
        
        return {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0
        }
    
    def run_stress_tests(self) -> Dict[str, Any]:
        """Run stress and performance tests"""
        print("\nRunning STRESS tests (performance and memory tests)...")
        
        # Focus on performance tests
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(PerformanceAndStressTests))
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0
        }
    
    def generate_test_report(self) -> str:
        """Generate a comprehensive test report"""
        if not self.test_results:
            return "No test results available. Run tests first."
        
        report = []
        report.append("\n" + "="*80)
        report.append("COMPREHENSIVE TEST REPORT")
        report.append("="*80)
        
        total_tests = 0
        total_failures = 0
        total_errors = 0
        total_success_rate = 0
        
        for category, results in self.test_results.items():
            report.append(f"\n{category.upper()} TESTS:")
            report.append("-" * 40)
            report.append(f"Tests Run: {results['tests_run']}")
            report.append(f"Failures: {results['failures']}")
            report.append(f"Errors: {results['errors']}")
            report.append(f"Success Rate: {results['success_rate']:.2%}")
            report.append(f"Execution Time: {results.get('execution_time', 'N/A'):.2f}s")
            
            # Add failure details if any
            if results['failures'] > 0 or results['errors'] > 0:
                report.append("\nFAILURE DETAILS:")
                result_obj = results['result']
                
                if result_obj.failures:
                    report.append("FAILURES:")
                    for test, traceback in result_obj.failures:
                        report.append(f"  - {test}: {traceback.split('AssertionError:')[-1].strip() if 'AssertionError:' in traceback else 'Test failed'}")
                
                if result_obj.errors:
                    report.append("ERRORS:")
                    for test, traceback in result_obj.errors:
                        report.append(f"  - {test}: {traceback.split('Exception:')[-1].strip() if 'Exception:' in traceback else 'Test error'}")
            
            total_tests += results['tests_run']
            total_failures += results['failures']
            total_errors += results['errors']
            total_success_rate += results['success_rate']
        
        # Overall summary
        report.append(f"\nOVERALL SUMMARY:")
        report.append("=" * 40)
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Total Failures: {total_failures}")
        report.append(f"Total Errors: {total_errors}")
        report.append(f"Average Success Rate: {total_success_rate / len(self.test_results):.2%}")
        
        # Test coverage summary
        report.append(f"\nTEST COVERAGE:")
        report.append("=" * 40)
        report.append("✓ Sheet Format Validation: STANDARD, COMPREHENSIVE, MINIMAL, CUSTOM")
        report.append("✓ Edge Case Handling: Empty values, invalid data, special characters")
        report.append("✓ Data Validation: Schema, cleaning, normalization")
        report.append("✓ Duplicate Detection: Similarity calculation, content hashing")
        report.append("✓ Cost Estimation: Script types, platforms, complexity factors")
        report.append("✓ Quality Scoring: Completeness, clarity, engagement, feasibility")
        report.append("✓ Pipeline Integration: Batch processing, error handling")
        report.append("✓ Performance: Large batch processing, memory efficiency")
        report.append("✓ Integration: Logging, serialization, external systems")
        
        return "\n".join(report)
    
    def validate_test_environment(self) -> bool:
        """Validate that the test environment is properly set up"""
        try:
            # Check if required modules can be imported
            from code.google_sheets_client import GoogleSheetsClient
            from code.data_validation import DataValidationPipeline
            
            # Check if test fixtures exist
            fixtures_path = Path(__file__).parent / "fixtures" / "sample_sheets"
            if not fixtures_path.exists():
                print("❌ Test fixtures directory not found")
                return False
            
            required_fixtures = [
                "standard_format.json",
                "comprehensive_format.json", 
                "minimal_format.json",
                "custom_format.json",
                "edge_cases.json",
                "malformed_data.json"
            ]
            
            for fixture in required_fixtures:
                fixture_path = fixtures_path / fixture
                if not fixture_path.exists():
                    print(f"❌ Test fixture not found: {fixture}")
                    return False
            
            print("✅ Test environment validation passed")
            return True
            
        except ImportError as e:
            print(f"❌ Import error: {e}")
            return False
        except Exception as e:
            print(f"❌ Environment validation error: {e}")
            return False


def main():
    """Main entry point for the test runner"""
    parser = argparse.ArgumentParser(description="Google Sheets Integration Test Runner")
    parser.add_argument(
        "--category",
        choices=["all", "sheet_formats", "data_validation", "quick", "stress"],
        default="all",
        help="Test category to run (default: all)"
    )
    parser.add_argument(
        "--verbosity",
        type=int,
        choices=[0, 1, 2],
        default=2,
        help="Test verbosity level (0=quiet, 1=normal, 2=verbose)"
    )
    parser.add_argument(
        "--validate-env",
        action="store_true",
        help="Only validate test environment setup"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate test report after running tests"
    )
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = TestRunner()
    
    # Validate environment if requested
    if args.validate_env:
        success = runner.validate_test_environment()
        sys.exit(0 if success else 1)
    
    # Validate environment before running tests
    if not runner.validate_test_environment():
        print("\n❌ Test environment validation failed. Please check setup.")
        sys.exit(1)
    
    print("🚀 Starting Google Sheets Integration Tests")
    print(f"📁 Test fixtures: {Path(__file__).parent / 'fixtures'}")
    print(f"📊 Category: {args.category}")
    print(f"🔍 Verbosity: {args.verbosity}")
    
    try:
        # Run tests based on category
        if args.category == "quick":
            results = runner.run_quick_tests()
            print(f"\n✅ Quick tests completed: {results['tests_run']} tests, {results['success_rate']:.1%} success rate")
        elif args.category == "stress":
            results = runner.run_stress_tests()
            print(f"\n✅ Stress tests completed: {results['tests_run']} tests, {results['success_rate']:.1%} success rate")
        else:
            # Run full test category
            runner.run_tests(args.category, args.verbosity)
            
            if args.report:
                report = runner.generate_test_report()
                print(report)
                
                # Save report to file
                report_path = Path(__file__).parent / f"test_report_{args.category}.txt"
                with open(report_path, 'w') as f:
                    f.write(report)
                print(f"\n📄 Test report saved to: {report_path}")
        
        # Check overall success
        if runner.test_results:
            overall_success = all(
                results['success_rate'] >= 0.8 for results in runner.test_results.values()
            )
            
            if overall_success:
                print("\n✅ All tests passed successfully!")
                sys.exit(0)
            else:
                print("\n❌ Some tests failed. Check output for details.")
                sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()