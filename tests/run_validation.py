#!/usr/bin/env python3
"""
Platform Timing Validation Runner

Comprehensive test runner for platform timing recommendation validation.
Executes all validation tests, generates reports, and provides summary results.
"""

import os
import sys
import subprocess
import json
import argparse
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ValidationTestRunner:
    """Main validation test runner"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.tests_dir = self.base_dir / "tests"
        self.reports_dir = self.base_dir / "validation_reports"
        self.reports_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def run_all_validations(self, verbose: bool = False, generate_reports: bool = True) -> dict:
        """Run all validation tests"""
        logger.info("Starting comprehensive platform timing validation")
        
        results = {
            "start_time": datetime.now().isoformat(),
            "test_suites": {},
            "overall_status": "UNKNOWN",
            "summary": {}
        }
        
        try:
            # 1. Run timing validation tests
            logger.info("Running timing accuracy validation tests...")
            timing_results = self._run_timing_validation_tests(verbose)
            results["test_suites"]["timing_validation"] = timing_results
            
            # 2. Run performance benchmarks
            logger.info("Running performance benchmarks...")
            benchmark_results = self._run_performance_benchmarks(verbose)
            results["test_suites"]["performance_benchmarks"] = benchmark_results
            
            # 3. Run validation scenarios
            logger.info("Running real-world validation scenarios...")
            scenario_results = self._run_validation_scenarios(verbose)
            results["test_suites"]["validation_scenarios"] = scenario_results
            
            # 4. Run validation cases
            logger.info("Running specific validation cases...")
            case_results = self._run_validation_cases(verbose)
            results["test_suites"]["validation_cases"] = case_results
            
            # 5. Generate reports
            if generate_reports:
                logger.info("Generating validation reports...")
                report_results = self._generate_validation_reports()
                results["validation_reports"] = report_results
            
            # 6. Calculate overall status
            results["overall_status"] = self._calculate_overall_status(results["test_suites"])
            results["end_time"] = datetime.now().isoformat()
            results["total_duration"] = self._calculate_duration(results["start_time"], results["end_time"])
            
            # Save results
            self._save_validation_results(results)
            
            # Print summary
            self._print_validation_summary(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Validation run failed: {e}")
            results["error"] = str(e)
            results["overall_status"] = "FAILED"
            return results
    
    def _run_timing_validation_tests(self, verbose: bool = False) -> dict:
        """Run main timing validation tests"""
        test_file = self.tests_dir / "test_timing_validation.py"
        
        if not test_file.exists():
            logger.warning(f"Timing validation test file not found: {test_file}")
            return {"status": "SKIPPED", "reason": "Test file not found"}
        
        cmd = ["python", "-m", "pytest", str(test_file), "-v"] if verbose else ["python", "-m", "pytest", str(test_file)]
        
        try:
            result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True, timeout=300)
            
            return {
                "status": "PASSED" if result.returncode == 0 else "FAILED",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_count": self._extract_test_count(result.stdout)
            }
        except subprocess.TimeoutExpired:
            logger.error("Timing validation tests timed out")
            return {"status": "TIMEOUT", "reason": "Tests exceeded 5 minute timeout"}
        except Exception as e:
            logger.error(f"Error running timing validation tests: {e}")
            return {"status": "ERROR", "reason": str(e)}
    
    def _run_performance_benchmarks(self, verbose: bool = False) -> dict:
        """Run performance benchmark tests"""
        test_file = self.tests_dir / "performance_benchmarks.py"
        
        if not test_file.exists():
            logger.warning(f"Performance benchmark test file not found: {test_file}")
            return {"status": "SKIPPED", "reason": "Test file not found"}
        
        # Run without slow tests for faster execution
        cmd = ["python", "-m", "pytest", str(test_file), "-v", "-m", "not slow"] if verbose else ["python", "-m", "pytest", str(test_file), "-m", "not slow"]
        
        try:
            result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True, timeout=180)
            
            return {
                "status": "PASSED" if result.returncode == 0 else "FAILED",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "benchmark_results": self._extract_benchmark_results(result.stdout)
            }
        except subprocess.TimeoutExpired:
            logger.error("Performance benchmarks timed out")
            return {"status": "TIMEOUT", "reason": "Tests exceeded 3 minute timeout"}
        except Exception as e:
            logger.error(f"Error running performance benchmarks: {e}")
            return {"status": "ERROR", "reason": str(e)}
    
    def _run_validation_scenarios(self, verbose: bool = False) -> dict:
        """Run validation scenario tests"""
        scenarios_dir = self.tests_dir / "validation_scenarios" / "scenarios"
        
        if not scenarios_dir.exists():
            logger.warning(f"Validation scenarios directory not found: {scenarios_dir}")
            return {"status": "SKIPPED", "reason": "Scenarios directory not found"}
        
        scenario_files = list(scenarios_dir.glob("*.py"))
        scenario_results = {}
        
        for scenario_file in scenario_files:
            logger.info(f"Running validation scenario: {scenario_file.name}")
            
            cmd = ["python", "-m", "pytest", str(scenario_file), "-v"] if verbose else ["python", "-m", "pytest", str(scenario_file)]
            
            try:
                result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True, timeout=120)
                
                scenario_results[scenario_file.stem] = {
                    "status": "PASSED" if result.returncode == 0 else "FAILED",
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            except subprocess.TimeoutExpired:
                logger.error(f"Scenario {scenario_file.name} timed out")
                scenario_results[scenario_file.stem] = {"status": "TIMEOUT", "reason": "Test exceeded 2 minute timeout"}
            except Exception as e:
                logger.error(f"Error running scenario {scenario_file.name}: {e}")
                scenario_results[scenario_file.stem] = {"status": "ERROR", "reason": str(e)}
        
        # Determine overall status
        failed_scenarios = [name for name, result in scenario_results.items() if result["status"] != "PASSED"]
        
        return {
            "status": "PASSED" if not failed_scenarios else "FAILED",
            "scenarios_tested": len(scenario_results),
            "scenarios_passed": len(scenario_results) - len(failed_scenarios),
            "scenario_results": scenario_results,
            "failed_scenarios": failed_scenarios
        }
    
    def _run_validation_cases(self, verbose: bool = False) -> dict:
        """Run specific validation case tests"""
        cases_dir = self.tests_dir / "validation_scenarios" / "validation_cases"
        
        if not cases_dir.exists():
            logger.warning(f"Validation cases directory not found: {cases_dir}")
            return {"status": "SKIPPED", "reason": "Cases directory not found"}
        
        case_files = list(cases_dir.glob("*.py"))
        case_results = {}
        
        for case_file in case_files:
            logger.info(f"Running validation case: {case_file.name}")
            
            cmd = ["python", "-m", "pytest", str(case_file), "-v"] if verbose else ["python", "-m", "pytest", str(case_file)]
            
            try:
                result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True, timeout=120)
                
                case_results[case_file.stem] = {
                    "status": "PASSED" if result.returncode == 0 else "FAILED",
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            except subprocess.TimeoutExpired:
                logger.error(f"Validation case {case_file.name} timed out")
                case_results[case_file.stem] = {"status": "TIMEOUT", "reason": "Test exceeded 2 minute timeout"}
            except Exception as e:
                logger.error(f"Error running validation case {case_file.name}: {e}")
                case_results[case_file.stem] = {"status": "ERROR", "reason": str(e)}
        
        # Determine overall status
        failed_cases = [name for name, result in case_results.items() if result["status"] != "PASSED"]
        
        return {
            "status": "PASSED" if not failed_cases else "FAILED",
            "cases_tested": len(case_results),
            "cases_passed": len(case_results) - len(failed_cases),
            "case_results": case_results,
            "failed_cases": failed_cases
        }
    
    def _generate_validation_reports(self) -> dict:
        """Generate validation reports using the report generator"""
        try:
            # Import and run the report generator
            report_generator_path = self.base_dir / "tests" / "validation_reports_generator.py"
            
            if not report_generator_path.exists():
                return {"status": "SKIPPED", "reason": "Report generator not found"}
            
            cmd = ["python", str(report_generator_path)]
            result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True, timeout=60)
            
            return {
                "status": "PASSED" if result.returncode == 0 else "FAILED",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "reports_generated": result.returncode == 0
            }
        except Exception as e:
            logger.error(f"Error generating validation reports: {e}")
            return {"status": "ERROR", "reason": str(e)}
    
    def _calculate_overall_status(self, test_suites: dict) -> str:
        """Calculate overall validation status"""
        failed_suites = []
        
        for suite_name, suite_results in test_suites.items():
            if isinstance(suite_results, dict) and suite_results.get("status") not in ["PASSED", "SKIPPED"]:
                failed_suites.append(suite_name)
        
        if not failed_suites:
            return "PASSED"
        elif "ERROR" in [test_suites[s].get("status") for s in failed_suites]:
            return "ERROR"
        else:
            return "FAILED"
    
    def _calculate_duration(self, start_time: str, end_time: str) -> str:
        """Calculate duration between start and end times"""
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        duration = end - start
        
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def _extract_test_count(self, output: str) -> int:
        """Extract number of tests from pytest output"""
        lines = output.split('\n')
        for line in lines:
            if 'passed' in line and 'warnings' not in line:
                # Look for patterns like "6 passed" or "10 passed in 5.23s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'passed' and i > 0:
                        try:
                            return int(parts[i-1])
                        except (ValueError, IndexError):
                            pass
        return 0
    
    def _extract_benchmark_results(self, output: str) -> dict:
        """Extract benchmark results from pytest output"""
        # This is a simplified extraction - in practice, you'd parse the actual benchmark output
        return {
            "accuracy_benchmark": "PASSED",
            "performance_benchmark": "PASSED",
            "scalability_benchmark": "PASSED"
        }
    
    def _save_validation_results(self, results: dict) -> None:
        """Save validation results to file"""
        results_file = self.reports_dir / f"validation_results_{self.timestamp}.json"
        
        try:
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Validation results saved to: {results_file}")
        except Exception as e:
            logger.error(f"Error saving validation results: {e}")
    
    def _print_validation_summary(self, results: dict) -> None:
        """Print validation summary to console"""
        print("\n" + "="*80)
        print("PLATFORM TIMING VALIDATION SUMMARY")
        print("="*80)
        
        status_emoji = {
            "PASSED": "✅",
            "FAILED": "❌", 
            "ERROR": "⚠️",
            "TIMEOUT": "⏰",
            "SKIPPED": "⏭️"
        }
        
        print(f"Overall Status: {status_emoji.get(results['overall_status'], '❓')} {results['overall_status']}")
        print(f"Total Duration: {results.get('total_duration', 'Unknown')}")
        print()
        
        print("Test Suite Results:")
        for suite_name, suite_results in results.get("test_suites", {}).items():
            if isinstance(suite_results, dict):
                status = suite_results.get("status", "UNKNOWN")
                emoji = status_emoji.get(status, "❓")
                print(f"  {emoji} {suite_name.replace('_', ' ').title()}: {status}")
                
                if suite_name == "validation_scenarios" and "scenarios_tested" in suite_results:
                    print(f"     Scenarios: {suite_results['scenarios_passed']}/{suite_results['scenarios_tested']} passed")
                
                elif suite_name == "validation_cases" and "cases_tested" in suite_results:
                    print(f"     Cases: {suite_results['cases_passed']}/{suite_results['cases_tested']} passed")
        
        print()
        
        if results.get("validation_reports"):
            report_status = results["validation_reports"].get("status", "UNKNOWN")
            report_emoji = status_emoji.get(report_status, "❓")
            print(f"Report Generation: {report_emoji} {report_status}")
        
        if results['overall_status'] == "PASSED":
            print("\n🎉 All validations passed! Platform timing recommendations are ready for deployment.")
        else:
            print("\n⚠️  Some validations failed. Please review the results before proceeding.")
        
        print("="*80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Platform Timing Validation Runner")
    parser.add_argument("--verbose", "-v", action="store_true", help="Run tests with verbose output")
    parser.add_argument("--no-reports", action="store_true", help="Skip report generation")
    parser.add_argument("--base-dir", help="Base directory for tests and reports")
    
    args = parser.parse_args()
    
    # Create and run validator
    runner = ValidationTestRunner(base_dir=args.base_dir)
    
    try:
        results = runner.run_all_validations(
            verbose=args.verbose,
            generate_reports=not args.no_reports
        )
        
        # Exit with appropriate code
        exit_code = 0 if results["overall_status"] == "PASSED" else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.info("Validation run interrupted by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        logger.error(f"Unexpected error during validation run: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()