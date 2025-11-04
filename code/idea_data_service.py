"""
Idea Data Service for processing Google Sheets data.

This service handles reading, validating, and transforming idea rows from Google Sheets
for video generation workflows. It provides batch processing capabilities and supports
different sheet formats and column mappings.
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SheetFormat(Enum):
    """Supported sheet format types."""
    STANDARD = "standard"  # A: Title, B: Script, C: Voice, D: Style, E: Assets
    MINIMAL = "minimal"    # A: Title, B: Content
    COMPREHENSIVE = "comprehensive"  # Extended format with metadata
    CUSTOM = "custom"      # Custom column mapping


class ValidationLevel(Enum):
    """Data validation strictness levels."""
    STRICT = "strict"      # All fields required, strict validation
    MODERATE = "moderate"  # Required fields + warnings for missing optional
    LENIENT = "lenient"    # Only critical fields required


@dataclass
class ColumnMapping:
    """Defines column mapping for sheet parsing."""
    title: str
    script: Optional[str] = None
    voice: Optional[str] = None
    style: Optional[str] = None
    assets: Optional[str] = None
    duration: Optional[str] = None
    metadata: List[str] = field(default_factory=list)


@dataclass
class IdeaValidationResult:
    """Result of idea data validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    normalized_data: Optional[Dict[str, Any]] = None


@dataclass
class ProcessedIdea:
    """Processed and validated idea data."""
    id: str
    row_index: int
    raw_data: Dict[str, Any]
    normalized_data: Dict[str, Any]
    validation_result: IdeaValidationResult
    sheet_format: SheetFormat
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BatchProcessingResult:
    """Result of batch processing a sheet."""
    sheet_id: str
    total_rows: int
    processed_rows: int
    successful_validations: int
    failed_validations: int
    processed_ideas: List[ProcessedIdea]
    errors: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    format_detected: Optional[SheetFormat] = None


class IdeaDataService:
    """
    Service for reading and processing idea rows from Google Sheets.
    
    Features:
    - Data validation for video idea formats
    - Transformation logic to standardize input data
    - Column mapping and parsing
    - Batch processing for multiple sheets
    - Support for different sheet formats
    """
    
    # Default column mappings for different formats
    DEFAULT_MAPPINGS = {
        SheetFormat.STANDARD: ColumnMapping(
            title="A",
            script="B", 
            voice="C",
            style="D",
            assets="E",
            duration="F"
        ),
        SheetFormat.MINIMAL: ColumnMapping(
            title="A",
            script="B"
        ),
        SheetFormat.COMPREHENSIVE: ColumnMapping(
            title="A",
            script="B",
            voice="C", 
            style="D",
            assets="E",
            duration="F",
            metadata=["G", "H", "I", "J"]  # Additional metadata columns
        )
    }
    
    # Required fields by validation level
    REQUIRED_FIELDS = {
        ValidationLevel.STRICT: ["title", "script"],
        ValidationLevel.MODERATE: ["title", "script"],
        ValidationLevel.LENIENT: ["title"]
    }
    
    # Valid value patterns
    VOICE_OPTIONS = ["male", "female", "neutral", "narrator"]
    STYLE_OPTIONS = ["casual", "professional", "energetic", "calm", "dramatic", "educational"]
    ASSET_TYPES = ["image", "video", "audio", "text", "url", "reference"]
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.MODERATE):
        """
        Initialize the idea data service.
        
        Args:
            validation_level: Validation strictness level
        """
        self.validation_level = validation_level
        self.sheet_mappings: Dict[str, ColumnMapping] = {}
        self._initialize_google_sheets_client()
    
    def _initialize_google_sheets_client(self):
        """Initialize Google Sheets API client (placeholder for actual implementation)."""
        # TODO: Implement actual Google Sheets API client initialization
        # This would involve setting up credentials and service discovery
        logger.info("Initializing Google Sheets client...")
    
    def detect_sheet_format(self, headers: List[str], sample_rows: List[Dict[str, Any]]) -> SheetFormat:
        """
        Detect the format of a Google Sheet based on headers and sample data.
        
        Args:
            headers: Column headers from the sheet
            sample_rows: Sample data rows for format detection
            
        Returns:
            Detected sheet format
        """
        logger.info(f"Detecting sheet format for headers: {headers}")
        
        # Check for comprehensive format
        if self._is_comprehensive_format(headers):
            return SheetFormat.COMPREHENSIVE
        
        # Check for standard format
        if self._is_standard_format(headers):
            return SheetFormat.STANDARD
        
        # Check for minimal format
        if self._is_minimal_format(headers):
            return SheetFormat.MINIMAL
        
        # Default to custom if no standard pattern matches
        return SheetFormat.CUSTOM
    
    def _is_comprehensive_format(self, headers: List[str]) -> bool:
        """Check if headers match comprehensive format."""
        required_cols = ['title', 'script', 'voice', 'style', 'assets', 'duration']
        return all(col.lower() in [h.lower() for h in headers] for col in required_cols)
    
    def _is_standard_format(self, headers: List[str]) -> bool:
        """Check if headers match standard format."""
        required_cols = ['title', 'script', 'voice', 'style', 'assets']
        return all(col.lower() in [h.lower() for h in headers] for col in required_cols)
    
    def _is_minimal_format(self, headers: List[str]) -> bool:
        """Check if headers match minimal format."""
        required_cols = ['title', 'script']
        return all(col.lower() in [h.lower() for h in headers] for col in required_cols)
    
    def set_custom_mapping(self, sheet_id: str, mapping: ColumnMapping):
        """
        Set custom column mapping for a specific sheet.
        
        Args:
            sheet_id: Google Sheet ID
            mapping: Column mapping configuration
        """
        self.sheet_mappings[sheet_id] = mapping
        logger.info(f"Set custom mapping for sheet {sheet_id}: {mapping}")
    
    def get_column_mapping(self, sheet_id: str, detected_format: SheetFormat) -> ColumnMapping:
        """
        Get column mapping for a sheet.
        
        Args:
            sheet_id: Google Sheet ID
            detected_format: Detected sheet format
            
        Returns:
            Column mapping for the sheet
        """
        # Check for custom mapping first
        if sheet_id in self.sheet_mappings:
            return self.sheet_mappings[sheet_id]
        
        # Return default mapping for detected format
        return self.DEFAULT_MAPPINGS.get(detected_format, self.DEFAULT_MAPPINGS[SheetFormat.STANDARD])
    
    def read_sheet_data(self, sheet_id: str, range_spec: str = "A:Z") -> List[Dict[str, Any]]:
        """
        Read data from a Google Sheet.
        
        Args:
            sheet_id: Google Sheet ID
            range_spec: Cell range to read (default: A:Z for all columns)
            
        Returns:
            List of row data as dictionaries
        """
        # TODO: Implement actual Google Sheets API call
        # This is a placeholder implementation
        logger.info(f"Reading sheet {sheet_id} with range {range_spec}")
        
        # Placeholder data structure
        sample_data = [
            {"A": "Video Title 1", "B": "Script content 1", "C": "female", "D": "energetic", "E": "image1.jpg"},
            {"A": "Video Title 2", "B": "Script content 2", "C": "male", "D": "professional", "E": "video1.mp4"},
            {"A": "Video Title 3", "B": "Script content 3", "C": "neutral", "D": "calm", "E": "audio1.mp3"}
        ]
        
        logger.info(f"Read {len(sample_data)} rows from sheet {sheet_id}")
        return sample_data
    
    def validate_and_normalize_idea(self, row_data: Dict[str, Any], row_index: int) -> IdeaValidationResult:
        """
        Validate and normalize a single idea row.
        
        Args:
            row_data: Raw row data from the sheet
            row_index: Row index (1-based)
            
        Returns:
            Validation result with normalized data
        """
        errors = []
        warnings = []
        normalized = {}
        
        # Extract fields based on validation level
        required_fields = self.REQUIRED_FIELDS[self.validation_level]
        
        # Validate and normalize each field
        title = self._validate_title(row_data, row_index)
        if title is not None:
            normalized["title"] = title
        elif "title" in required_fields:
            errors.append(f"Row {row_index}: Title is required but missing or invalid")
        
        script = self._validate_script(row_data, row_index)
        if script is not None:
            normalized["script"] = script
        elif "script" in required_fields:
            errors.append(f"Row {row_index}: Script is required but missing or invalid")
        
        # Optional fields
        voice = self._validate_voice(row_data, row_index)
        if voice is not None:
            normalized["voice"] = voice
        
        style = self._validate_style(row_data, row_index)
        if style is not None:
            normalized["style"] = style
        
        assets = self._validate_assets(row_data, row_index)
        if assets is not None:
            normalized["assets"] = assets
        
        duration = self._validate_duration(row_data, row_index)
        if duration is not None:
            normalized["duration"] = duration
        
        # Add metadata
        metadata = self._extract_metadata(row_data, row_index)
        if metadata:
            normalized["metadata"] = metadata
        
        # Check for validation issues
        is_valid = len(errors) == 0
        
        if warnings:
            logger.warning(f"Row {row_index} validation warnings: {warnings}")
        
        return IdeaValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            normalized_data=normalized if is_valid else None
        )
    
    def _validate_title(self, row_data: Dict[str, Any], row_index: int) -> Optional[str]:
        """Validate and clean title field."""
        title = self._get_field_value(row_data, ["title", "Title", "A", "0"])
        
        if not title or not isinstance(title, str):
            return None
        
        title = title.strip()
        if len(title) < 3:
            return None
        
        if len(title) > 200:
            return title[:200]  # Truncate to max length
        
        return title
    
    def _validate_script(self, row_data: Dict[str, Any], row_index: int) -> Optional[str]:
        """Validate and clean script field."""
        script = self._get_field_value(row_data, ["script", "Script", "B", "1"])
        
        if not script or not isinstance(script, str):
            return None
        
        script = script.strip()
        if len(script) < 10:
            return None
        
        return script
    
    def _validate_voice(self, row_data: Dict[str, Any], row_index: int) -> Optional[str]:
        """Validate voice field."""
        voice = self._get_field_value(row_data, ["voice", "Voice", "C", "2"])
        
        if not voice or not isinstance(voice, str):
            return None
        
        voice = voice.lower().strip()
        
        if voice in self.VOICE_OPTIONS:
            return voice
        
        # Try to match common variations
        voice_mapping = {
            "f": "female", "woman": "female", "girl": "female",
            "m": "male", "man": "male", "boy": "male",
            "n": "neutral", "none": "neutral", "default": "neutral"
        }
        
        return voice_mapping.get(voice)
    
    def _validate_style(self, row_data: Dict[str, Any], row_index: int) -> Optional[str]:
        """Validate style field."""
        style = self._get_field_value(row_data, ["style", "Style", "D", "3"])
        
        if not style or not isinstance(style, str):
            return None
        
        style = style.lower().strip()
        
        if style in self.STYLE_OPTIONS:
            return style
        
        return None
    
    def _validate_assets(self, row_data: Dict[str, Any], row_index: int) -> Optional[List[Dict[str, str]]]:
        """Validate and parse assets field."""
        assets_raw = self._get_field_value(row_data, ["assets", "Assets", "E", "4"])
        
        if not assets_raw or not isinstance(assets_raw, str):
            return None
        
        assets = []
        asset_items = [item.strip() for item in assets_raw.split(",")]
        
        for item in asset_items:
            if not item:
                continue
            
            # Parse asset (format: type:reference)
            if ":" in item:
                asset_type, reference = item.split(":", 1)
                asset_type = asset_type.lower().strip()
                if asset_type in self.ASSET_TYPES:
                    assets.append({
                        "type": asset_type,
                        "reference": reference.strip()
                    })
            else:
                # Assume image if no type specified
                assets.append({
                    "type": "image",
                    "reference": item.strip()
                })
        
        return assets if assets else None
    
    def _validate_duration(self, row_data: Dict[str, Any], row_index: int) -> Optional[int]:
        """Validate duration field (in seconds)."""
        duration = self._get_field_value(row_data, ["duration", "Duration", "F", "5"])
        
        if not duration:
            return None
        
        try:
            if isinstance(duration, str):
                # Parse duration strings (e.g., "30", "1:30", "2m 30s")
                duration = self._parse_duration_string(duration)
            
            duration = int(duration)
            if 1 <= duration <= 600:  # 1 second to 10 minutes
                return duration
        except (ValueError, TypeError):
            pass
        
        return None
    
    def _parse_duration_string(self, duration_str: str) -> int:
        """Parse duration string to seconds."""
        duration_str = duration_str.lower().strip()
        
        # Handle HH:MM:SS format
        if ":" in duration_str:
            parts = duration_str.split(":")
            if len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:  # MM:SS
                minutes, seconds = int(parts[0]), int(parts[1])
                return minutes * 60 + seconds
        
        # Handle Xm Ys format
        total_seconds = 0
        time_pattern = re.findall(r'(\d+)([mns])', duration_str)
        for value, unit in time_pattern:
            value = int(value)
            if unit == 'm':
                total_seconds += value * 60
            elif unit == 's':
                total_seconds += value
            elif unit == 'n':  # seconds abbreviation
                total_seconds += value
        
        return total_seconds if total_seconds > 0 else int(duration_str)
    
    def _extract_metadata(self, row_data: Dict[str, Any], row_index: int) -> Dict[str, Any]:
        """Extract additional metadata from row data."""
        metadata = {}
        
        # Look for common metadata fields
        for key in ["category", "tags", "priority", "target_audience", "notes"]:
            if key in row_data and row_data[key]:
                metadata[key] = row_data[key]
        
        # Add any remaining columns as additional metadata
        standard_fields = ["title", "script", "voice", "style", "assets", "duration"]
        for col, value in row_data.items():
            if col not in standard_fields and value:
                metadata[col] = value
        
        return metadata
    
    def _get_field_value(self, row_data: Dict[str, Any], possible_keys: List[str]) -> Any:
        """Get field value using multiple possible key formats."""
        for key in possible_keys:
            if key in row_data and row_data[key] is not None:
                return row_data[key]
        return None
    
    def generate_idea_id(self, raw_data: Dict[str, Any], sheet_id: str, row_index: int) -> str:
        """
        Generate unique ID for an idea based on sheet and row.
        
        Args:
            raw_data: Raw row data
            sheet_id: Google Sheet ID
            row_index: Row index
            
        Returns:
            Unique idea ID
        """
        # Create deterministic ID based on sheet, row, and content
        content = f"{sheet_id}_{row_index}_{json.dumps(raw_data, sort_keys=True)}"
        hash_obj = hashlib.md5(content.encode())
        return f"idea_{hash_obj.hexdigest()[:12]}"
    
    def process_sheet_batch(
        self, 
        sheet_id: str, 
        range_spec: str = "A:Z",
        custom_mapping: Optional[ColumnMapping] = None
    ) -> BatchProcessingResult:
        """
        Process a complete sheet in batch mode.
        
        Args:
            sheet_id: Google Sheet ID
            range_spec: Cell range to process
            custom_mapping: Optional custom column mapping
            
        Returns:
            Batch processing result
        """
        start_time = datetime.now()
        logger.info(f"Starting batch processing for sheet {sheet_id}")
        
        try:
            # Read sheet data
            sheet_data = self.read_sheet_data(sheet_id, range_spec)
            
            if not sheet_data:
                return BatchProcessingResult(
                    sheet_id=sheet_id,
                    total_rows=0,
                    processed_rows=0,
                    successful_validations=0,
                    failed_validations=0,
                    processed_ideas=[],
                    errors=["No data found in sheet"]
                )
            
            # Detect format
            headers = list(sheet_data[0].keys()) if sheet_data else []
            detected_format = self.detect_sheet_format(headers, sheet_data[:5])
            
            # Get column mapping
            if custom_mapping:
                column_mapping = custom_mapping
                detected_format = SheetFormat.CUSTOM
            else:
                column_mapping = self.get_column_mapping(sheet_id, detected_format)
            
            # Process each row
            processed_ideas = []
            successful_validations = 0
            failed_validations = 0
            errors = []
            
            for row_index, row_data in enumerate(sheet_data, 1):
                try:
                    # Validate and normalize
                    validation_result = self.validate_and_normalize_idea(row_data, row_index)
                    
                    if validation_result.is_valid:
                        successful_validations += 1
                        
                        # Create processed idea
                        idea_id = self.generate_idea_id(row_data, sheet_id, row_index)
                        processed_idea = ProcessedIdea(
                            id=idea_id,
                            row_index=row_index,
                            raw_data=row_data,
                            normalized_data=validation_result.normalized_data,
                            validation_result=validation_result,
                            sheet_format=detected_format
                        )
                        processed_ideas.append(processed_idea)
                    else:
                        failed_validations += 1
                        errors.extend(validation_result.errors)
                        
                        # Create failed idea record
                        idea_id = self.generate_idea_id(row_data, sheet_id, row_index)
                        processed_idea = ProcessedIdea(
                            id=idea_id,
                            row_index=row_index,
                            raw_data=row_data,
                            normalized_data={},
                            validation_result=validation_result,
                            sheet_format=detected_format
                        )
                        processed_ideas.append(processed_idea)
                
                except Exception as e:
                    failed_validations += 1
                    error_msg = f"Row {row_index}: Processing error - {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result = BatchProcessingResult(
                sheet_id=sheet_id,
                total_rows=len(sheet_data),
                processed_rows=len(processed_ideas),
                successful_validations=successful_validations,
                failed_validations=failed_validations,
                processed_ideas=processed_ideas,
                errors=errors,
                processing_time_ms=processing_time,
                format_detected=detected_format
            )
            
            logger.info(f"Batch processing completed: {successful_validations} successful, {failed_validations} failed")
            return result
        
        except Exception as e:
            error_msg = f"Batch processing failed: {str(e)}"
            logger.error(error_msg)
            return BatchProcessingResult(
                sheet_id=sheet_id,
                total_rows=0,
                processed_rows=0,
                successful_validations=0,
                failed_validations=0,
                processed_ideas=[],
                errors=[error_msg]
            )
    
    def process_multiple_sheets(
        self, 
        sheet_configs: List[Dict[str, Any]]
    ) -> List[BatchProcessingResult]:
        """
        Process multiple sheets in batch mode.
        
        Args:
            sheet_configs: List of sheet configuration dictionaries
            Each config should contain: sheet_id, range_spec (optional), custom_mapping (optional)
            
        Returns:
            List of batch processing results
        """
        logger.info(f"Starting batch processing for {len(sheet_configs)} sheets")
        results = []
        
        for config in sheet_configs:
            sheet_id = config["sheet_id"]
            range_spec = config.get("range_spec", "A:Z")
            custom_mapping = config.get("custom_mapping")
            
            try:
                result = self.process_sheet_batch(sheet_id, range_spec, custom_mapping)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process sheet {sheet_id}: {str(e)}")
                results.append(BatchProcessingResult(
                    sheet_id=sheet_id,
                    total_rows=0,
                    processed_rows=0,
                    successful_validations=0,
                    failed_validations=0,
                    processed_ideas=[],
                    errors=[f"Sheet processing failed: {str(e)}"]
                ))
        
        logger.info(f"Batch processing completed for {len(results)} sheets")
        return results
    
    def export_processed_ideas(
        self, 
        processed_ideas: List[ProcessedIdea], 
        format_type: str = "json"
    ) -> str:
        """
        Export processed ideas in specified format.
        
        Args:
            processed_ideas: List of processed ideas
            format_type: Export format (json, csv)
            
        Returns:
            Exported data as string
        """
        if format_type.lower() == "json":
            return self._export_as_json(processed_ideas)
        elif format_type.lower() == "csv":
            return self._export_as_csv(processed_ideas)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def _export_as_json(self, processed_ideas: List[ProcessedIdea]) -> str:
        """Export processed ideas as JSON."""
        export_data = {
            "exported_at": datetime.utcnow().isoformat(),
            "total_ideas": len(processed_ideas),
            "ideas": []
        }
        
        for idea in processed_ideas:
            idea_data = {
                "id": idea.id,
                "row_index": idea.row_index,
                "sheet_format": idea.sheet_format.value,
                "is_valid": idea.validation_result.is_valid,
                "normalized_data": idea.normalized_data,
                "errors": idea.validation_result.errors,
                "warnings": idea.validation_result.warnings,
                "created_at": idea.created_at.isoformat()
            }
            export_data["ideas"].append(idea_data)
        
        return json.dumps(export_data, indent=2)
    
    def _export_as_csv(self, processed_ideas: List[ProcessedIdea]) -> str:
        """Export processed ideas as CSV."""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "ID", "Row Index", "Format", "Valid", "Title", "Script", 
            "Voice", "Style", "Duration", "Assets", "Errors", "Warnings"
        ])
        
        # Write data
        for idea in processed_ideas:
            data = idea.normalized_data
            errors = "; ".join(idea.validation_result.errors)
            warnings = "; ".join(idea.validation_result.warnings)
            assets = json.dumps(data.get("assets", [])) if data.get("assets") else ""
            
            writer.writerow([
                idea.id,
                idea.row_index,
                idea.sheet_format.value,
                "Yes" if idea.validation_result.is_valid else "No",
                data.get("title", ""),
                data.get("script", ""),
                data.get("voice", ""),
                data.get("style", ""),
                data.get("duration", ""),
                assets,
                errors,
                warnings
            ])
        
        return output.getvalue()
    
    def get_analytics_summary(self, results: List[BatchProcessingResult]) -> Dict[str, Any]:
        """
        Generate analytics summary for batch processing results.
        
        Args:
            results: List of batch processing results
            
        Returns:
            Analytics summary dictionary
        """
        total_sheets = len(results)
        total_rows = sum(r.total_rows for r in results)
        total_processed = sum(r.processed_rows for r in results)
        total_successful = sum(r.successful_validations for r in results)
        total_failed = sum(r.failed_validations for r in results)
        total_errors = sum(len(r.errors) for r in results)
        avg_processing_time = sum(r.processing_time_ms for r in results) / total_sheets if total_sheets > 0 else 0
        
        # Format distribution
        format_counts = {}
        for result in results:
            if result.format_detected:
                format_name = result.format_detected.value
                format_counts[format_name] = format_counts.get(format_name, 0) + 1
        
        summary = {
            "total_sheets": total_sheets,
            "total_rows": total_rows,
            "total_processed": total_processed,
            "total_successful": total_successful,
            "total_failed": total_failed,
            "success_rate": (total_successful / total_processed * 100) if total_processed > 0 else 0,
            "total_errors": total_errors,
            "average_processing_time_ms": avg_processing_time,
            "format_distribution": format_counts,
            "processed_at": datetime.utcnow().isoformat()
        }
        
        return summary


# Example usage and testing functions
def example_usage():
    """Example of how to use the IdeaDataService."""
    
    # Initialize service
    service = IdeaDataService(validation_level=ValidationLevel.MODERATE)
    
    # Example sheet processing
    sheet_configs = [
        {
            "sheet_id": "1A2B3C4D5E6F7G8H9I0J",
            "range_spec": "A1:F100"
        },
        {
            "sheet_id": "2B3C4D5E6F7G8H9I0J1K",
            "range_spec": "A1:Z50",
            "custom_mapping": ColumnMapping(
                title="Title",
                script="Content",
                voice="Audio",
                style="Theme"
            )
        }
    ]
    
    # Process multiple sheets
    results = service.process_multiple_sheets(sheet_configs)
    
    # Generate analytics
    analytics = service.get_analytics_summary(results)
    print(json.dumps(analytics, indent=2))
    
    # Export valid ideas
    valid_ideas = []
    for result in results:
        valid_ideas.extend([idea for idea in result.processed_ideas if idea.validation_result.is_valid])
    
    exported_json = service.export_processed_ideas(valid_ideas, "json")
    print("\nExported JSON:")
    print(exported_json)


if __name__ == "__main__":
    example_usage()