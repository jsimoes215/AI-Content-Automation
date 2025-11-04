#!/usr/bin/env python3
"""
Test Runner for Scheduling Optimization Algorithm Suite

This script runs all scheduling optimization tests and generates comprehensive reports.

Usage:
    python run_scheduling_tests.py [--verbose] [--coverage] [--performance]

Author: AI Content Automation System
Version: 1.0.0
Date: 2025-11-05
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Test configurations
TEST_MODULES = [
    "test_scheduling_optimization.py",
    "test_platform_timing.py", 
    "test_content_calendar.py",
    "test_automated_suggestions.py"
]

TEST_CATEGORIES = {
    "unit": "Unit tests for individual components",
    "integration": "Integration tests for component interactions", 
    "performance": "Performance and stress tests",
    "scheduling": "Scheduling algorithm tests",
    "calendar": "Content calendar tests",
    "suggestions": "Suggestion engine tests"
}


class SchedulingTestRunner:
    """Main test runner for scheduling optimization suite."""
    
    def __init__(self, verbose: bool = False, coverage: bool = False, 
                 performance: bool = False, output_dir: str = "test_reports"):
        self.verbose = verbose
        self.coverage = coverage
        self.performance = performance
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.results = {
            "start_time": datetime.now().isoformat(),
            "test_runs": [],
            "summary": {},
            "performance_metrics": {},
            "errors": []
        }
    
    def run_all_tests(self) -> Dict:
        """Run all scheduling optimization tests."""
        print("🚀 Starting Scheduling Optimization Test Suite")
        print("=" * 60)
        
        # Set up test environment
        self.setup_test_environment()
        
        # Run each test module
        for test_module in TEST_MODULES:
            print(f"\\n📋 Running {test_module}...")
            test_result = self.run_test_module(test_module)
            self.results["test_runs"].append(test_result)
        
        # Run performance tests if requested
        if self.performance:
            print("\\n⚡ Running performance tests...")
            perf_result = self.run_performance_tests()
            self.results["test_runs"].append(perf_result)
        
        # Generate summary
        self.generate_summary()
        
        # Generate reports
        self.generate_reports()
        
        print("\\n🎉 Test suite completed!")
        return self.results
    
    def setup_test_environment(self):
        """Set up test environment variables."""
        os.environ["TEST_MODE"] = "true"
        os.environ["LOG_LEVEL"] = "INFO"
        os.environ["PYTHONPATH"] = str(Path.cwd() / "code") + ":" + os.environ.get("PYTHONPATH", "")
        
        # Create test database directories
        test_data_dir = Path("test_data")
        test_data_dir.mkdir(exist_ok=True)
        
        for subdir in ["fixtures", "research_data", "temp"]:
            (test_data_dir / subdir).mkdir(exist_ok=True)
    
    def run_test_module(self, test_module: str) -> Dict:
        """Run a specific test module."""
        start_time = time.time()
        
        # Build pytest command
        cmd = [
            "python", "-m", "pytest",
            f"tests/{test_module}",
            "--tb=short",
            "--durations=10"
        ]
        
        if self.verbose:
            cmd.append("-v")
        
        if self.coverage:
            cmd.extend([
                "--cov=code",
                f"--cov-report=html:{self.output_dir}/coverage",
                f"--cov-report=json:{self.output_dir}/coverage.json"
            ])
        
        # Add performance markers if running performance tests
        if self.performance and "performance" in test_module:
            cmd.extend(["-m", "performance"])
        
        try:
            # Run the tests
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            
            elapsed_time = time.time() - start_time
            
            # Parse results
            test_result = {
                "module": test_module,
                "start_time": datetime.now().isoformat(),
                "elapsed_time": elapsed_time,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_skipped": 0,
                "errors": []
            }
            
            # Parse test counts from output
            if "passed" in result.stdout:
                # Extract numbers from output like "5 passed, 2 failed, 1 skipped"
                import re
                passed_match = re.search(r'(\\d+) passed', result.stdout)
                failed_match = re.search(r'(\\d+) failed', result.stdout)
                skipped_match = re.search(r'(\\d+) skipped', result.stdout)
                
                if passed_match:
                    test_result["tests_passed"] = int(passed_match.group(1))
                if failed_match:
                    test_result["tests_failed"] = int(failed_match.group(1))
                if skipped_match:
                    test_result["tests_skipped"] = int(skipped_match.group(1))
            
            # Check for errors
            if result.returncode != 0:
                test_result["errors"].append(f"Test execution failed with code {result.returncode}")
                if result.stderr:
                    test_result["errors"].append(result.stderr)
            
            # Print results
            if result.returncode == 0:
                print(f"✅ {test_module}: PASSED ({test_result['tests_passed']} tests)")
            else:
                print(f"❌ {test_module}: FAILED ({test_result['tests_failed']} failures)")
                if self.verbose:
                    print(f"   Error: {result.stderr}")
            
            return test_result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_result = {
                "module": test_module,
                "start_time": datetime.now().isoformat(),
                "elapsed_time": elapsed_time,
                "return_code": -1,
                "error": str(e),
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_skipped": 0,
                "errors": [f"Test execution failed: {str(e)}"]
            }
            print(f"💥 {test_module}: ERROR - {str(e)}")
            return error_result
    
    def run_performance_tests(self) -> Dict:
        """Run performance-specific tests."""
        start_time = time.time()
        
        perf_tests = [
            ("test_large_scale_schedule_generation", "Scheduling"),
            ("test_database_performance", "Database"),
            ("test_time_complexity_performance", "Algorithms"),
            ("test_concurrent_user_handling", "Concurrency"),
            ("test_real_time_suggestion_generation", "Real-time")
        ]
        
        performance_results = {}
        
        for test_name, category in perf_tests:
            print(f"  🏃 Running {test_name}...")
            test_start = time.time()
            
            # Run specific performance test
            cmd = [
                "python", "-m", "pytest",
                "tests/test_scheduling_optimization.py",
                f"tests/test_automated_suggestions.py", 
                "-k", test_name,
                "-v",
                "--tb=no"
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                elapsed = time.time() - test_start
                
                performance_results[test_name] = {
                    "category": category,
                    "elapsed_time": elapsed,
                    "status": "PASSED" if result.returncode == 0 else "FAILED",
                    "output": result.stdout if self.verbose else ""
                }
                
                status_icon = "✅" if result.returncode == 0 else "❌"
                print(f"    {status_icon} {test_name}: {elapsed:.3f}s")
                
            except Exception as e:
                elapsed = time.time() - test_start
                performance_results[test_name] = {
                    "category": category,
                    "elapsed_time": elapsed,
                    "status": "ERROR",
                    "error": str(e)
                }
                print(f"    💥 {test_name}: ERROR - {str(e)}")
        
        return {
            "module": "performance_tests",
            "start_time": datetime.now().isoformat(),
            "elapsed_time": time.time() - start_time,
            "performance_results": performance_results,
            "return_code": 0
        }
    
    def generate_summary(self):
        """Generate test summary."""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_errors = 0
        total_time = 0
        
        for test_run in self.results["test_runs"]:
            if "tests_passed" in test_run:
                total_tests += test_run["tests_passed"] + test_run["tests_failed"] + test_run["tests_skipped"]
                total_passed += test_run["tests_passed"]
                total_failed += test_run["tests_failed"]
            total_time += test_run["elapsed_time"]
            
            if test_run.get("errors"):
                total_errors += len(test_run["errors"])
        
        self.results["summary"] = {
            "end_time": datetime.now().isoformat(),
            "total_duration": total_time,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_errors": total_errors,
            "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
            "modules_tested": len(TEST_MODULES),
            "categories": TEST_CATEGORIES
        }
        
        # Print summary
        print("\\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed} ✅")
        print(f"Failed: {total_failed} ❌")
        print(f"Success Rate: {self.results['summary']['success_rate']:.1f}%")
        print(f"Total Duration: {total_time:.2f}s")
        print(f"Modules Tested: {len(TEST_MODULES)}")
        
        if total_failed > 0:
            print(f"\\n⚠️  {total_failed} tests failed - review output above")
        if total_errors > 0:
            print(f"\\n🚨 {total_errors} errors encountered - check error logs")
    
    def generate_reports(self):
        """Generate comprehensive test reports."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Main JSON report
        report_path = self.output_dir / f"scheduling_tests_report_{timestamp}.json"
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # HTML report
        self.generate_html_report(timestamp)
        
        # Performance report
        if self.performance:
            self.generate_performance_report(timestamp)
        
        # Coverage report (if available)
        if self.coverage:
            self.generate_coverage_report(timestamp)
        
        print(f"\\n📄 Reports generated in: {self.output_dir}")
        print(f"   Main report: {report_path}")
    
    def generate_html_report(self, timestamp: str):
        """Generate HTML test report."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Scheduling Optimization Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ background-color: #e8f5e8; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .module {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .error {{ color: #fd7e14; }}
        .performance {{ background-color: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Scheduling Optimization Test Report</h1>
        <p>Generated: {self.results['summary']['end_time']}</p>
        <p>Test Environment: {os.environ.get('TEST_MODE', 'unknown')}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Summary</h2>
        <p><strong>Total Tests:</strong> {self.results['summary']['total_tests']}</p>
        <p><strong>Passed:</strong> <span class="passed">{self.results['summary']['total_passed']}</span></p>
        <p><strong>Failed:</strong> <span class="failed">{self.results['summary']['total_failed']}</span></p>
        <p><strong>Success Rate:</strong> {self.results['summary']['success_rate']:.1f}%</p>
        <p><strong>Total Duration:</strong> {self.results['summary']['total_duration']:.2f}s</p>
    </div>
    
    <h2>📋 Test Module Results</h2>
"""
        
        for test_run in self.results["test_runs"]:
            status_class = "passed" if test_run["return_code"] == 0 else "failed"
            status_icon = "✅" if test_run["return_code"] == 0 else "❌"
            
            html_content += f"""
    <div class="module">
        <h3>{status_icon} {test_run['module']}</h3>
        <p><strong>Duration:</strong> {test_run['elapsed_time']:.2f}s</p>
        <p><strong>Status:</strong> <span class="{status_class}">{'PASSED' if test_run['return_code'] == 0 else 'FAILED'}</span></p>
"""
            
            if "tests_passed" in test_run:
                html_content += f"""
        <p><strong>Tests Passed:</strong> {test_run['tests_passed']}</p>
        <p><strong>Tests Failed:</strong> {test_run['tests_failed']}</p>
        <p><strong>Tests Skipped:</strong> {test_run['tests_skipped']}</p>
"""
            
            if test_run.get("errors"):
                html_content += "<p><strong>Errors:</strong></p><ul>"
                for error in test_run["errors"]:
                    html_content += f"<li class='error'>{error}</li>"
                html_content += "</ul>"
            
            html_content += "    </div>"
        
        html_content += """
</body>
</html>
"""
        
        html_path = self.output_dir / f"scheduling_tests_report_{timestamp}.html"
        with open(html_path, 'w') as f:
            f.write(html_content)
    
    def generate_performance_report(self, timestamp: str):
        """Generate performance test report."""
        perf_run = None
        for test_run in self.results["test_runs"]:
            if test_run["module"] == "performance_tests":
                perf_run = test_run
                break
        
        if not perf_run or "performance_results" not in perf_run:
            return
        
        perf_data = perf_run["performance_results"]
        
        perf_report = {
            "performance_summary": {
                "total_perf_tests": len(perf_data),
                "categories_tested": list(set(result["category"] for result in perf_data.values())),
                "total_perf_duration": sum(result["elapsed_time"] for result in perf_data.values())
            },
            "detailed_results": perf_data
        }
        
        perf_path = self.output_dir / f"performance_report_{timestamp}.json"
        with open(perf_path, 'w') as f:
            json.dump(perf_report, f, indent=2, default=str)
    
    def generate_coverage_report(self, timestamp: str):
        """Generate coverage report information."""
        coverage_info = {
            "coverage_enabled": True,
            "coverage_reports": [
                f"HTML: {self.output_dir}/coverage/index.html",
                f"JSON: {self.output_dir}/coverage.json"
            ],
            "note": "Coverage reports require pytest-cov to be installed"
        }
        
        coverage_path = self.output_dir / f"coverage_info_{timestamp}.json"
        with open(coverage_path, 'w') as f:
            json.dump(coverage_info, f, indent=2)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run scheduling optimization test suite")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true",
                       help="Generate coverage reports")
    parser.add_argument("--performance", "-p", action="store_true",
                       help="Include performance tests")
    parser.add_argument("--output", "-o", default="test_reports",
                       help="Output directory for reports")
    
    args = parser.parse_args()
    
    # Create test runner
    runner = SchedulingTestRunner(
        verbose=args.verbose,
        coverage=args.coverage,
        performance=args.performance,
        output_dir=args.output
    )
    
    try:
        # Run all tests
        results = runner.run_all_tests()
        
        # Exit with appropriate code
        if results["summary"]["total_failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\\n⚠️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\\n💥 Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()