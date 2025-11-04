# Idea Data Service

A comprehensive service for reading and processing idea rows from Google Sheets for video generation workflows.

## Features

✅ **Data Validation for Video Idea Formats**
- Validates titles, scripts, voice options, styles, assets, and duration
- Three validation levels: STRICT, MODERATE, LENIENT
- Comprehensive error reporting and warnings

✅ **Transformation Logic to Standardize Input Data**
- Normalizes data to consistent format
- Handles duration parsing (MM:SS, HH:MM:SS, Xm Ys formats)
- Asset parsing and categorization
- Voice and style option validation

✅ **Column Mapping and Parsing**
- Supports multiple sheet formats:
  - STANDARD: Title, Script, Voice, Style, Assets
  - COMPREHENSIVE: Standard + Duration + Metadata
  - MINIMAL: Title, Script only
  - CUSTOM: User-defined column mappings
- Auto-detection of sheet format
- Flexible field name handling (case-insensitive)

✅ **Batch Processing for Multiple Sheets**
- Process single or multiple sheets efficiently
- Progress tracking and error collection
- Performance metrics and timing

✅ **Support for Different Sheet Formats**
- Automatic format detection based on headers
- Custom mapping configuration
- Handles both column letters (A, B, C) and named columns

## Usage

```python
from idea_data_service import IdeaDataService, ValidationLevel, ColumnMapping

# Initialize service
service = IdeaDataService(validation_level=ValidationLevel.MODERATE)

# Process single sheet
result = service.process_sheet_batch("sheet_id_123", "A1:F100")

# Process multiple sheets
configs = [
    {"sheet_id": "sheet_1", "range_spec": "A1:F50"},
    {"sheet_id": "sheet_2", "range_spec": "A1:Z100", 
     "custom_mapping": ColumnMapping(title="Video_Title", script="Content")}
]
results = service.process_multiple_sheets(configs)

# Export results
json_export = service.export_processed_ideas(valid_ideas, "json")
csv_export = service.export_processed_ideas(valid_ideas, "csv")

# Get analytics
analytics = service.get_analytics_summary(results)
```

## Testing

Run the comprehensive test suite:

```bash
python test_idea_data_service.py
```

All tests pass successfully, covering:
- Format detection
- Data validation and normalization
- Duration parsing
- Batch processing
- Multiple sheet processing
- Export functionality
- Analytics and reporting

## Integration

The service is designed to integrate with:
- Database schema (bulk_jobs, video_jobs tables)
- API endpoints for bulk content generation
- Google Sheets API for data ingestion
- Video generation pipelines

## Architecture

Based on the database schema and API design specifications:
- References `docs/architecture_design/database_schema.md`
- References `docs/architecture_design/api_endpoints.md`
- Follows Row-Level Security (RLS) patterns
- Supports multi-tenant operations
- Implements idempotency and error handling