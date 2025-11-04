#!/usr/bin/env python3
"""
Test runner for bulk operations system.

This script provides convenient ways to run the comprehensive test suite.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --integration      # Run integration tests only
    python run_tests.py --cost             # Run cost optimization tests only
    python run_tests.py --sheets           # Run Google Sheets tests only
    python run_tests.py --verbose          # Run with verbose output
    python run_tests.py --coverage         # Run with coverage report

Author: AI Content Automation System
Version: 1.0.0
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path


def run_tests(test_pattern="", verbose=False, coverage=False, integration_only=False, 
              cost_only=False, sheets_only=False, slow_tests=False):
    """Run the test suite with specified options."""
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test directory
    test_dir = Path(__file__).parent / "tests"
    cmd.append(str(test_dir))
    
    # Add test pattern
    if test_pattern:
        cmd.extend(["-k", test_pattern])
    
    # Add verbose flag
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add coverage
    if coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-config=.coveragerc"
        ])
    
    # Add markers
    markers = []
    if integration_only:
        markers.append("integration")
    if slow_tests:
        markers.append("slow")
    
    if markers:
        cmd.extend(["-m", " or ".join(markers)])
    
    # Add specific test files
    if cost_only:
        cmd = ["python", "-m", "pytest", str(test_dir / "test_cost_optimization.py"), "-v"]
    elif sheets_only:
        cmd = ["python", "-m", "pytest", str(test_dir / "test_google_sheets_integration.py"), "-v"]
    
    print(f"Running command: {' '.join(cmd)}")
    print("-" * 50)
    
    # Run the tests
    try:
        result = subprocess.run(cmd, check=False, cwd=Path(__file__).parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def setup_test_environment():
    """Setup the test environment."""
    
    # Create necessary directories
    test_data_dir = Path(__file__).parent / "tests" / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    
    # Create coverage config if it doesn't exist
    coveragerc_path = Path(__file__).parent / ".coveragerc"
    if not coveragerc_path.exists():
        coverage_config = """
[run]
source = .
omit = 
    */tests/*
    */test_*
    */__pycache__/*
    */venv/*
    */.git/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod

[html]
directory = htmlcov
"""
        with open(coveragerc_path, 'w') as f:
            f.write(coverage_config.strip())
    
    print("Test environment setup complete")


def check_dependencies():
    """Check if required dependencies are installed."""
    
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "pytest-mock",
        "google-api-python-client",
        "google-auth",
        "google-auth-oauthlib",
        "google-auth-httplib2"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Warning: Some required packages are not installed:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        print("Or install all test dependencies with:")
        print("pip install -r requirements-google-sheets.txt")
        return False
    
    return True


def main():
    """Main entry point for test runner."""
    
    parser = argparse.ArgumentParser(description="Run bulk operations system tests")
    parser.add_argument("--integration", action="store_true", 
                       help="Run integration tests only")
    parser.add_argument("--cost", action="store_true",
                       help="Run cost optimization tests only")
    parser.add_argument("--sheets", action="store_true",
                       help="Run Google Sheets integration tests only")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Run with verbose output")
    parser.add_argument("--coverage", action="store_true",
                       help="Run with coverage report")
    parser.add_argument("--slow", action="store_true",
                       help="Include slow running tests")
    parser.add_argument("--setup", action="store_true",
                       help="Setup test environment only")
    parser.add_argument("--check-deps", action="store_true",
                       help="Check dependencies only")
    
    args = parser.parse_args()
    
    # Handle setup and dependency check first
    if args.setup:
        setup_test_environment()
        return 0
    
    if args.check_deps:
        if check_dependencies():
            print("All required dependencies are installed ✓")
            return 0
        else:
            return 1
    
    # Check dependencies
    if not check_dependencies():
        print("Please install missing dependencies before running tests")
        return 1
    
    # Setup environment
    setup_test_environment()
    
    # Run tests
    print("Bulk Operations System - Test Runner")
    print("=" * 50)
    
    if args.cost:
        print("Running cost optimization tests...")
    elif args.sheets:
        print("Running Google Sheets integration tests...")
    elif args.integration:
        print("Running integration tests...")
    else:
        print("Running all tests...")
    
    return run_tests(
        verbose=args.verbose,
        coverage=args.coverage,
        integration_only=args.integration,
        cost_only=args.cost,
        sheets_only=args.sheets,
        slow_tests=args.slow
    )


if __name__ == "__main__":
    sys.exit(main())