# Google Sheets Integration Test Suite

This directory contains comprehensive tests for Google Sheets integration and data validation in the AI Content Automation System.

## Overview

The test suite validates:
- **Sheet Formats**: STANDARD, COMPREHENSIVE, MINIMAL, and CUSTOM formats
- **Data Validation**: Schema validation, cleaning, and transformation
- **Edge Cases**: Error handling, malformed data, and special scenarios
- **Performance**: Large batch processing and memory efficiency
- **Integration**: Google Sheets client integration and external system compatibility

## Test Structure

```
tests/
├── fixtures/sample_sheets/          # Test data files
│   ├── standard_format.json        # Standard video idea format
│   ├── comprehensive_format.json   # Extended format with metadata
│   ├── minimal_format.json         # Minimal required fields only
│   ├── custom_format.json          # Custom column structure
│   ├── edge_cases.json             # Challenging edge cases
│   └── malformed_data.json         # Corrupted/invalid data
├── test_sheet_formats.py           # Sheet format validation tests
├── test_data_validation.py         # Data validation pipeline tests
├── test_scheduling_optimization.py # Scheduling algorithm tests
├── test_platform_timing.py         # Platform timing validation tests
├── test_content_calendar.py        # Content calendar operation tests
├── test_automated_suggestions.py   # Automated suggestion engine tests
├── conftest.py                     # Test configuration and fixtures
├── run_tests.py                    # Test runner for Google Sheets tests
├── run_scheduling_tests.py         # Test runner for scheduling tests
└── README.md                       # This documentation
```

## Scheduling Optimization Test Suite

The test suite also includes comprehensive tests for scheduling optimization algorithms covering:

### Core Components Tested
- **Scheduling Optimizer**: Multi-platform scheduling algorithms with constraint satisfaction
- **Platform Timing**: Evidence-based timing calculations for YouTube, Instagram, TikTok, LinkedIn, Facebook
- **Content Calendar**: CRUD operations, analytics, and integration workflows
- **Automated Suggestions**: Real-time suggestion generation with Bayesian learning

### Quick Start for Scheduling Tests
```bash
# Run all scheduling tests
python run_scheduling_tests.py

# Run with coverage and performance tests
python run_scheduling_tests.py --verbose --coverage --performance

# Run specific scheduling module
pytest test_scheduling_optimization.py -v

# Run platform timing tests
pytest test_platform_timing.py -v
```

### Test Categories for Scheduling
- **unit**: Individual algorithm tests
- **integration**: Component interaction tests
- **performance**: Performance and stress tests
- **scheduling**: Core scheduling algorithm tests
- **calendar**: Content calendar tests
- **suggestions**: Suggestion engine tests

See [TEST_SUITE_COMPLETION_SUMMARY.md](./TEST_SUITE_COMPLETION_SUMMARY.md) for detailed documentation.

## Sheet Format Types

### 1. STANDARD Format
**Purpose**: Standard video idea format with essential fields
**Columns**:
- `title`: Video title (5-100 characters)
- `description`: Video description (20-2000 characters)
- `target_audience`: Target audience (predefined options)
- `tags`: Comma-separated tags (max 10)
- `tone`: Video tone/mood
- `duration_estimate`: Video length
- `platform`: Target platform
- `script_type`: Content type
- `call_to_action`: CTA text

### 2. COMPREHENSIVE Format
**Purpose**: Extended format with detailed metadata and analysis
**Additional Columns**:
- `style`: Visual style description
- `voice_type`: Narrator type
- `visual_elements`: Visual requirements
- `keywords`: SEO keywords
- `competitor_analysis`: Competition research
- `brand_guidelines`: Brand compliance
- `compliance_notes`: Legal requirements
- `demo_required`: Demo flag
- `priority`: Content priority
- `estimated_cost`: Cost estimate
- `quality_score`: Quality rating
- `creation_date`: Creation timestamp
- `status`: Current status
- `author`: Content creator
- `review_notes`: Review comments

### 3. MINIMAL Format
**Purpose**: Quick entry with only required fields
**Columns**:
- `title`: Video title
- `description`: Video description
- `target_audience`: Target audience

### 4. CUSTOM Format
**Purpose**: Flexible format with custom column names
**Features**:
- Different column naming conventions
- Unicode character support
- Complex duration formats (HH:MM:SS)
- Array field support
- Extended metadata fields

## Running Tests

### Quick Start
```bash
# Run all tests
python tests/run_tests.py

# Run specific test category
python tests/run_tests.py --category sheet_formats
python tests/run_tests.py --category data_validation

# Quick validation (subset of critical tests)
python tests/run_tests.py --category quick

# Stress/performance tests only
python tests/run_tests.py --category stress

# Generate test report
python tests/run_tests.py --category all --report
```

### Test Categories

#### Sheet Format Tests (`test_sheet_formats.py`)
- **StandardFormatTests**: Validates standard format structure and data
- **ComprehensiveFormatTests**: Tests extended format with metadata
- **MinimalFormatTests**: Validates minimal required fields
- **CustomFormatTests**: Tests custom column structures and Unicode
- **EdgeCaseTests**: Handles empty titles, invalid data, duplicates
- **MalformedDataTests**: Tests error handling for corrupted data
- **SheetIntegrationTests**: Integration with Google Sheets client

#### Data Validation Tests (`test_data_validation.py`)
- **SchemaValidationTests**: Field validation rules
- **DataCleaningTests**: Text normalization and sanitization
- **DuplicateDetectionTests**: Similarity detection and content hashing
- **CostEstimationTests**: Production cost calculations
- **QualityScoringTests**: Content quality assessment
- **DataValidationPipelineTests**: End-to-end validation pipeline
- **PerformanceAndStressTests**: Large batch processing
- **IntegrationTests**: External system integration

## Test Data Examples

### Standard Format Sample
```json
{
  "title": "5 Tips for Better Sleep",
  "description": "Learn evidence-based strategies to improve your sleep quality...",
  "target_audience": "general",
  "tags": "health, wellness, sleep, lifestyle",
  "tone": "educational",
  "duration_estimate": "3 minutes",
  "platform": "youtube",
  "script_type": "tutorial",
  "call_to_action": "Subscribe for more health tips"
}
```

### Edge Case Examples
- **Empty Title**: `"title": ""`
- **Short Title**: `"title": "A"`
- **Long Description**: 2000+ character description
- **Invalid Audience**: Non-standard audience type
- **Duplicate Content**: Similar titles and descriptions
- **Special Characters**: Unicode, emojis, HTML/JavaScript
- **Malformed Data**: Null values, wrong data types, script tags

## Validation Rules

### Required Fields
- **title**: 5-100 characters, alphanumeric + spaces/symbols
- **description**: 20-2000 characters
- **target_audience**: Must be from predefined list

### Optional Fields
- **tags**: Max 10 tags, 30 characters each
- **tone**: Must be from predefined tone list
- **platform**: Must be from supported platforms
- **script_type**: Must be from valid script types
- **duration_estimate**: Various time formats supported

### Data Cleaning
- Text normalization (whitespace, special characters)
- HTML/JavaScript sanitization
- List field normalization (comma-separated to arrays)
- Duration parsing (seconds, minutes, hours, HH:MM:SS)
- Unicode character handling

### Quality Scoring (0-10)
- **Completeness** (25%): Field completion rate
- **Clarity** (20%): Content clarity metrics
- **Engagement** (20%): Engagement potential factors
- **Feasibility** (15%): Production feasibility
- **Uniqueness** (20%): Content similarity analysis

### Cost Estimation
- Base cost per minute by script type
- Platform complexity multipliers
- Complexity adders (demo, brand guidelines, compliance)
- 10% contingency factor

## Test Environment Setup

### Prerequisites
```bash
# Install required dependencies
pip install -r code/requirements-google-sheets.txt

# Ensure test fixtures are present
ls tests/fixtures/sample_sheets/
```

### Validation
```bash
# Validate test environment
python tests/run_tests.py --validate-env
```

## Test Results

### Success Criteria
- **80%+ success rate** for production readiness
- **100% coverage** of critical validation paths
- **Proper error handling** for all edge cases
- **Memory efficiency** for large batch processing

### Test Report
```bash
# Generate comprehensive test report
python tests/run_tests.py --category all --report

# Report includes:
# - Test execution summary
# - Failure details and error messages
# - Performance metrics
# - Test coverage analysis
# - Recommendations
```

## Continuous Integration

### Pre-commit Checks
```bash
# Run quick validation before commits
python tests/run_tests.py --category quick
```

### Full Validation
```bash
# Complete test suite for releases
python tests/run_tests.py --category all --report
```

### Performance Baseline
```bash
# Establish performance benchmarks
python tests/run_tests.py --category stress
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure code directory is in Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/code"
   ```

2. **Missing Fixtures**
   ```bash
   # Check fixture files exist
   ls tests/fixtures/sample_sheets/
   ```

3. **Test Failures**
   ```bash
   # Run with detailed output
   python tests/run_tests.py --category quick --verbosity 2
   ```

4. **Performance Issues**
   ```bash
   # Run stress tests to identify bottlenecks
   python tests/run_tests.py --category stress --verbosity 2
   ```

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Extending Tests

### Adding New Test Cases
1. Add test data to appropriate fixture file
2. Create test method in relevant test class
3. Follow naming convention: `test_feature_scenario`
4. Include docstring explaining the test case

### Adding New Sheet Formats
1. Create new fixture file in `fixtures/sample_sheets/`
2. Add test class for the new format
3. Update test runner to include new tests
4. Document format in this README

### Performance Testing
```python
# Add performance benchmarks
def test_large_batch_performance(self):
    large_batch = create_test_data(1000)  # 1000 ideas
    start_time = time.time()
    results = pipeline.validate_batch(large_batch)
    execution_time = time.time() - start_time
    
    # Assert performance requirements
    self.assertLess(execution_time, 30)  # 30 seconds max
```

## Contributing

When adding new tests:
1. Follow existing test patterns and naming conventions
2. Include both positive and negative test cases
3. Add appropriate edge cases
4. Update documentation
5. Run full test suite before submitting

## License

Part of the AI Content Automation System test suite.