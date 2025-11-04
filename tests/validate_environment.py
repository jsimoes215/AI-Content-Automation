#!/usr/bin/env python3
"""
Simple test validator for Google Sheets integration tests

This script validates the test environment without running the full test suite.
"""

import sys
import os
import json
from pathlib import Path

def validate_test_environment():
    """Validate that the test environment is properly set up"""
    print("🔍 Validating test environment...")
    
    try:
        # Check Python path and imports
        sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
        
        # Try importing required modules
        print("  📦 Checking imports...")
        from google_sheets_client import GoogleSheetsClient, SheetRange
        from data_validation import DataValidationPipeline
        print("    ✅ Core modules imported successfully")
        
        # Check test fixtures
        print("  📁 Checking test fixtures...")
        fixtures_path = Path(__file__).parent / "fixtures" / "sample_sheets"
        
        if not fixtures_path.exists():
            print("    ❌ Test fixtures directory not found")
            return False
        
        required_fixtures = [
            "standard_format.json",
            "comprehensive_format.json", 
            "minimal_format.json",
            "custom_format.json",
            "edge_cases.json",
            "malformed_data.json"
        ]
        
        missing_fixtures = []
        for fixture in required_fixtures:
            fixture_path = fixtures_path / fixture
            if not fixture_path.exists():
                missing_fixtures.append(fixture)
            else:
                # Try to load the fixture to check if it's valid JSON
                try:
                    with open(fixture_path, 'r') as f:
                        data = json.load(f)
                    if 'data' not in data:
                        print(f"    ⚠️  Fixture {fixture} missing 'data' field")
                except json.JSONDecodeError:
                    print(f"    ❌ Fixture {fixture} is not valid JSON")
                    missing_fixtures.append(fixture)
        
        if missing_fixtures:
            print(f"    ❌ Missing fixtures: {', '.join(missing_fixtures)}")
            return False
        else:
            print("    ✅ All test fixtures found and valid")
        
        # Check test files exist
        print("  🧪 Checking test files...")
        test_files = [
            Path(__file__).parent / "test_sheet_formats.py",
            Path(__file__).parent / "test_data_validation.py"
        ]
        
        for test_file in test_files:
            if test_file.exists():
                print(f"    ✅ {test_file.name} exists")
            else:
                print(f"    ❌ {test_file.name} missing")
                return False
        
        # Validate fixture data structure
        print("  📊 Validating fixture data structure...")
        for fixture_file in fixtures_path.glob("*.json"):
            try:
                with open(fixture_file, 'r') as f:
                    data = json.load(f)
                
                required_fields = ['sheet_name', 'format_type', 'description', 'data']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"    ⚠️  {fixture_file.name} missing fields: {missing_fields}")
                else:
                    # Check if data is array and has at least header row
                    if isinstance(data['data'], list) and len(data['data']) >= 1:
                        print(f"    ✅ {fixture_file.name} has valid structure")
                    else:
                        print(f"    ❌ {fixture_file.name} has invalid data structure")
                        return False
                        
            except Exception as e:
                print(f"    ❌ Error reading {fixture_file.name}: {e}")
                return False
        
        print("\n✅ Test environment validation PASSED")
        print("🎯 Ready to run comprehensive tests")
        return True
        
    except ImportError as e:
        print(f"    ❌ Import error: {e}")
        print("    💡 Make sure all dependencies are installed:")
        print("       pip install -r code/requirements-google-sheets.txt")
        return False
    except Exception as e:
        print(f"    ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_sample_validation():
    """Run a sample validation to ensure the pipeline works"""
    print("\n🧪 Running sample validation test...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
        from data_validation import DataValidationPipeline
        
        # Create test data
        test_idea = {
            "title": "Sample Video Test",
            "description": "This is a sample video description with sufficient length for validation testing",
            "target_audience": "general",
            "tags": "test, sample, validation"
        }
        
        # Create pipeline and validate
        pipeline = DataValidationPipeline()
        result = pipeline.validate_idea(test_idea)
        
        print(f"    📋 Test idea validated: {result.is_valid}")
        print(f"    ⭐ Quality score: {result.quality_score}/10")
        print(f"    💰 Cost estimate: ${result.estimated_cost}")
        print(f"    📝 Errors: {len(result.errors)}")
        print(f"    ⚠️  Warnings: {len(result.warnings)}")
        
        if result.is_valid:
            print("    ✅ Sample validation PASSED")
            return True
        else:
            print("    ❌ Sample validation FAILED")
            print(f"    Errors: {result.errors}")
            return False
            
    except Exception as e:
        print(f"    ❌ Sample validation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main validation function"""
    print("🚀 Google Sheets Integration Test Environment Validator")
    print("=" * 55)
    
    # Run environment validation
    env_valid = validate_test_environment()
    
    if env_valid:
        # Run sample validation
        sample_valid = run_sample_validation()
        
        if sample_valid:
            print("\n🎉 All validations PASSED!")
            print("\n📖 Next steps:")
            print("   • Run full test suite: python tests/run_tests.py")
            print("   • Run specific tests: python tests/run_tests.py --category sheet_formats")
            print("   • Generate report: python tests/run_tests.py --category all --report")
            print("   • Run quick tests: python tests/run_tests.py --category quick")
            sys.exit(0)
        else:
            print("\n⚠️  Environment valid but sample test failed")
            sys.exit(1)
    else:
        print("\n❌ Environment validation FAILED")
        print("\n🔧 Troubleshooting:")
        print("   1. Check that all test fixture files exist")
        print("   2. Install dependencies: pip install -r code/requirements-google-sheets.txt")
        print("   3. Verify Python path configuration")
        sys.exit(1)

if __name__ == "__main__":
    main()