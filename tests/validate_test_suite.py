#!/usr/bin/env python3
"""
Test Suite Validation Script

This script validates the test suite structure and dependencies without running
the actual tests. It checks imports, fixtures, and overall test framework setup.

Usage:
    python validate_test_suite.py

Author: AI Content Automation System
Version: 1.0.0
Date: 2025-11-05
"""

import os
import sys
import importlib.util
from pathlib import Path
from typing import List, Dict, Tuple

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))


class TestSuiteValidator:
    """Validates test suite structure and dependencies."""
    
    def __init__(self):
        self.results = {
            "imports": {},
            "file_structure": {},
            "fixtures": {},
            "test_files": {},
            "overall_status": "UNKNOWN"
        }
    
    def validate_all(self) -> Dict:
        """Run all validation checks."""
        print("🔍 Validating Scheduling Optimization Test Suite")
        print("=" * 60)
        
        # Check file structure
        self.validate_file_structure()
        
        # Check core imports
        self.validate_core_imports()
        
        # Check test file structure
        self.validate_test_files()
        
        # Check conftest.py
        self.validate_conftest()
        
        # Generate overall status
        self.generate_status()
        
        # Print results
        self.print_results()
        
        return self.results
    
    def validate_file_structure(self):
        """Validate test file structure."""
        print("\\n📁 Validating file structure...")
        
        required_files = [
            "test_scheduling_optimization.py",
            "test_platform_timing.py", 
            "test_content_calendar.py",
            "test_automated_suggestions.py",
            "conftest.py",
            "run_scheduling_tests.py",
            "TEST_SUITE_COMPLETION_SUMMARY.md"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = Path(__file__).parent / file_path
            if full_path.exists():
                size = full_path.stat().st_size
                print(f"  ✅ {file_path} ({size:,} bytes)")
                self.results["file_structure"][file_path] = {"exists": True, "size": size}
            else:
                print(f"  ❌ {file_path} (missing)")
                missing_files.append(file_path)
                self.results["file_structure"][file_path] = {"exists": False}
        
        if not missing_files:
            print("  ✅ All required test files present")
        else:
            print(f"  ⚠️  Missing {len(missing_files)} files")
    
    def validate_core_imports(self):
        """Validate core module imports."""
        print("\\n📦 Validating core imports...")
        
        core_modules = {
            "scheduling_optimizer": ["Platform", "ContentType", "AudienceProfile"],
            "content_calendar": ["ContentCalendar", "ScheduleStatus"], 
            "automated_suggestions": ["SuggestionEngine", "UserPreferences"]
        }
        
        for module_name, expected_classes in core_modules.items():
            try:
                module = importlib.import_module(module_name)
                available_classes = []
                missing_classes = []
                
                for class_name in expected_classes:
                    if hasattr(module, class_name):
                        available_classes.append(class_name)
                    else:
                        missing_classes.append(class_name)
                
                if not missing_classes:
                    print(f"  ✅ {module_name}: All classes available")
                    self.results["imports"][module_name] = {
                        "status": "SUCCESS",
                        "available": available_classes,
                        "missing": []
                    }
                else:
                    print(f"  ⚠️  {module_name}: Missing {missing_classes}")
                    self.results["imports"][module_name] = {
                        "status": "PARTIAL",
                        "available": available_classes,
                        "missing": missing_classes
                    }
                    
            except ImportError as e:
                print(f"  ❌ {module_name}: Import failed - {str(e)}")
                self.results["imports"][module_name] = {
                    "status": "FAILED", 
                    "error": str(e),
                    "available": [],
                    "missing": expected_classes
                }
    
    def validate_test_files(self):
        """Validate test file structure."""
        print("\\n🧪 Validating test files...")
        
        test_files = {
            "test_scheduling_optimization.py": [
                "TestSchedulingOptimizationAlgorithms",
                "TestConstraintSatisfaction"
            ],
            "test_platform_timing.py": [
                "TestPlatformTimingCalculations",
                "TestTimingValidationAgainstResearch"
            ],
            "test_content_calendar.py": [
                "TestContentCalendarOperations",
                "TestCalendarViewsAndFiltering"
            ],
            "test_automated_suggestions.py": [
                "TestAutomatedSuggestionEngine",
                "TestBayesianUpdaterComponent",
                "TestConstraintResolverComponent"
            ]
        }
        
        for file_name, expected_classes in test_files.items():
            file_path = Path(__file__).parent / file_name
            
            if not file_path.exists():
                print(f"  ❌ {file_name}: File not found")
                self.results["test_files"][file_name] = {"status": "FILE_NOT_FOUND"}
                continue
            
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for expected test classes
                found_classes = []
                for class_name in expected_classes:
                    if f"class {class_name}" in content:
                        found_classes.append(class_name)
                
                if len(found_classes) == len(expected_classes):
                    print(f"  ✅ {file_name}: All test classes found")
                    self.results["test_files"][file_name] = {
                        "status": "SUCCESS",
                        "classes_found": found_classes
                    }
                else:
                    missing = set(expected_classes) - set(found_classes)
                    print(f"  ⚠️  {file_name}: Missing classes {missing}")
                    self.results["test_files"][file_name] = {
                        "status": "PARTIAL",
                        "classes_found": found_classes,
                        "classes_missing": list(missing)
                    }
                    
            except Exception as e:
                print(f"  ❌ {file_name}: Error reading file - {str(e)}")
                self.results["test_files"][file_name] = {"status": "ERROR", "error": str(e)}
    
    def validate_conftest(self):
        """Validate conftest.py structure."""
        print("\\n⚙️  Validating conftest.py...")
        
        conftest_path = Path(__file__).parent / "conftest.py"
        
        if not conftest_path.exists():
            print("  ❌ conftest.py: File not found")
            self.results["conftest"] = {"status": "FILE_NOT_FOUND"}
            return
        
        try:
            with open(conftest_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for key components
            expected_components = [
                "@pytest.fixture",
                "def scheduling_optimizer(",
                "def content_calendar(",
                "def suggestion_engine(",
                "class TestConfig:",
                "TestSchedulingAssertions"
            ]
            
            found_components = []
            missing_components = []
            
            for component in expected_components:
                if component in content:
                    found_components.append(component)
                else:
                    missing_components.append(component)
            
            if not missing_components:
                print("  ✅ conftest.py: All key components found")
                self.results["conftest"] = {
                    "status": "SUCCESS",
                    "components_found": found_components,
                    "file_size": conftest_path.stat().st_size
                }
            else:
                print(f"  ⚠️  conftest.py: Missing components {missing_components}")
                self.results["conftest"] = {
                    "status": "PARTIAL",
                    "components_found": found_components,
                    "components_missing": missing_components,
                    "file_size": conftest_path.stat().st_size
                }
                
        except Exception as e:
            print(f"  ❌ conftest.py: Error reading file - {str(e)}")
            self.results["conftest"] = {"status": "ERROR", "error": str(e)}
    
    def generate_status(self):
        """Generate overall test suite status."""
        # Count successes and failures
        file_success = sum(1 for v in self.results["file_structure"].values() if v.get("exists", False))
        import_success = sum(1 for v in self.results["imports"].values() if v.get("status") == "SUCCESS")
        test_success = sum(1 for v in self.results["test_files"].values() if v.get("status") == "SUCCESS")
        conftest_success = self.results.get("conftest", {}).get("status") == "SUCCESS"
        
        total_areas = 4
        successful_areas = sum([file_success > 0, import_success > 0, test_success > 0, conftest_success])
        
        if successful_areas == total_areas:
            self.results["overall_status"] = "READY"
            status_msg = "✅ Test suite ready for execution"
        elif successful_areas >= total_areas * 0.75:
            self.results["overall_status"] = "MOSTLY_READY"
            status_msg = "⚠️  Test suite mostly ready, some issues present"
        else:
            self.results["overall_status"] = "NEEDS_WORK"
            status_msg = "❌ Test suite needs significant work"
        
        self.results["summary"] = {
            "file_success": file_success,
            "import_success": import_success,
            "test_success": test_success, 
            "conftest_success": conftest_success,
            "status_message": status_msg
        }
    
    def print_results(self):
        """Print validation results."""
        print("\\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        summary = self.results.get("summary", {})
        print(f"Overall Status: {summary.get('status_message', 'Unknown')}")
        print(f"File Structure: {'✅' if summary.get('file_success', 0) > 0 else '❌'}")
        print(f"Core Imports: {'✅' if summary.get('import_success', 0) > 0 else '❌'}")
        print(f"Test Files: {'✅' if summary.get('test_success', 0) > 0 else '❌'}")
        print(f"Configuration: {'✅' if summary.get('conftest_success', False) else '❌'}")
        
        # Print specific issues
        issues = []
        
        # Check import issues
        for module, info in self.results.get("imports", {}).items():
            if info.get("status") != "SUCCESS":
                issues.append(f"Import issue in {module}: {info.get('missing', [])}")
        
        # Check test file issues
        for file_name, info in self.results.get("test_files", {}).items():
            if info.get("status") != "SUCCESS":
                issues.append(f"Test file issue in {file_name}: {info.get('status', 'unknown')}")
        
        if issues:
            print("\\n🚨 Issues Found:")
            for issue in issues[:5]:  # Show first 5 issues
                print(f"  - {issue}")
            if len(issues) > 5:
                print(f"  ... and {len(issues) - 5} more issues")
        
        # Next steps
        print("\\n📋 Next Steps:")
        if self.results["overall_status"] == "READY":
            print("  ✅ Test suite is ready for execution!")
            print("  🚀 Run with: python run_scheduling_tests.py")
        elif self.results["overall_status"] == "MOSTLY_READY":
            print("  ⚠️  Address the issues above before running tests")
            print("  🔧 Fix imports and missing components")
        else:
            print("  ❌ Significant work needed before tests can run")
            print("  📚 Review TEST_SUITE_COMPLETION_SUMMARY.md for guidance")


def main():
    """Main entry point."""
    validator = TestSuiteValidator()
    results = validator.validate_all()
    
    # Return appropriate exit code
    if results["overall_status"] == "READY":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()