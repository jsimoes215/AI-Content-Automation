"""
Google Sheets Client Configuration and Integration Examples
for AI Content Automation System

This module provides configuration examples and integration patterns
for using the Google Sheets client within the AI Content Automation system.
"""

from typing import Dict, Any
from pathlib import Path
import os


# Example configuration for the AI Content Automation system
GOOGLE_SHEETS_CONFIG = {
    "credentials_path": os.getenv(
        "GOOGLE_SHEETS_CREDENTIALS_PATH", 
        "config/google-sheets-service-account.json"
    ),
    "rate_limits": {
        # Project-level limits (300 requests per minute is typical)
        "max_requests_per_minute": int(os.getenv("GOOGLE_SHEETS_MAX_PER_MINUTE", "300")),
        # User-level limits (60 requests per minute per service account)
        "max_requests_per_minute_per_user": int(os.getenv("GOOGLE_SHEETS_MAX_PER_USER", "60")),
        # Request timeout (180 seconds as per Google limits)
        "request_timeout_seconds": int(os.getenv("GOOGLE_SHEETS_TIMEOUT", "180")),
        # Recommended max payload size in MB
        "max_payload_size_mb": int(os.getenv("GOOGLE_SHEETS_MAX_PAYLOAD_MB", "2")),
        # Exponential backoff configuration
        "backoff_base_delay": float(os.getenv("GOOGLE_SHEETS_BACKOFF_BASE", "1.0")),
        "backoff_multiplier": float(os.getenv("GOOGLE_SHEETS_BACKOFF_MULTIPLIER", "2.0")),
        "backoff_max_delay": float(os.getenv("GOOGLE_SHEETS_BACKOFF_MAX", "60.0")),
        "max_retries": int(os.getenv("GOOGLE_SHEETS_MAX_RETRIES", "5"))
    }
}


# Example integration patterns for AI Content Automation system
INTEGRATION_EXAMPLES = {
    "content_tracking": {
        "description": "Track content generation progress and results",
        "spreadsheet_id": "your-content-tracking-spreadsheet-id",
        "sheets": {
            "projects": "Project tracking with status and metadata",
            "content_library": "Reusable content inventory",
            "analytics": "Performance metrics and insights"
        }
    },
    "batch_job_monitoring": {
        "description": "Monitor batch video generation jobs",
        "spreadsheet_id": "your-batch-monitoring-spreadsheet-id", 
        "sheets": {
            "job_queue": "Current batch jobs with status",
            "job_history": "Historical job performance data",
            "error_log": "Error tracking and resolution"
        }
    },
    "performance_analytics": {
        "description": "Store and analyze content performance data",
        "spreadsheet_id": "your-analytics-spreadsheet-id",
        "sheets": {
            "engagement_metrics": "Views, likes, shares by platform",
            "platform_performance": "Cross-platform comparison data",
            "trend_analysis": "Long-term performance trends"
        }
    }
}


def get_client_config() -> Dict[str, Any]:
    """
    Get the Google Sheets client configuration.
    
    Returns:
        Configuration dictionary for the client
    """
    return GOOGLE_SHEETS_CONFIG.copy()


def get_integration_config(integration_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific integration pattern.
    
    Args:
        integration_name: Name of the integration pattern
        
    Returns:
        Integration configuration dictionary
    """
    if integration_name not in INTEGRATION_EXAMPLES:
        raise ValueError(f"Unknown integration: {integration_name}. "
                        f"Available: {list(INTEGRATION_EXAMPLES.keys())}")
    
    return INTEGRATION_EXAMPLES[integration_name].copy()


# Service account setup instructions
SERVICE_ACCOUNT_SETUP = {
    "step1": "Create a service account in Google Cloud Console",
    "step2": "Download the service account JSON key file",
    "step3": "Store the file securely (e.g., config/google-sheets-service-account.json)",
    "step4": "Set GOOGLE_SHEETS_CREDENTIALS_PATH environment variable",
    "step5": "Share target spreadsheets with the service account email",
    "scopes_required": [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/spreadsheets"
    ]
}


# Environment variables for configuration
ENVIRONMENT_VARIABLES = {
    "GOOGLE_SHEETS_CREDENTIALS_PATH": "Path to service account JSON file",
    "GOOGLE_SHEETS_MAX_PER_MINUTE": "Max requests per minute (default: 300)",
    "GOOGLE_SHEETS_MAX_PER_USER": "Max requests per user per minute (default: 60)",
    "GOOGLE_SHEETS_TIMEOUT": "Request timeout in seconds (default: 180)",
    "GOOGLE_SHEETS_MAX_PAYLOAD_MB": "Max payload size in MB (default: 2)",
    "GOOGLE_SHEETS_BACKOFF_BASE": "Base delay for exponential backoff (default: 1.0)",
    "GOOGLE_SHEETS_BACKOFF_MULTIPLIER": "Backoff multiplier (default: 2.0)",
    "GOOGLE_SHEETS_BACKOFF_MAX": "Max backoff delay in seconds (default: 60.0)",
    "GOOGLE_SHEETS_MAX_RETRIES": "Maximum retry attempts (default: 5)"
}


def create_integration_template(integration_name: str, output_path: str) -> str:
    """
    Create a template file for a specific integration pattern.
    
    Args:
        integration_name: Name of the integration
        output_path: Path where to save the template
        
    Returns:
        Path to the created template file
    """
    config = get_integration_config(integration_name)
    
    template_content = f'''"""
{integration_name.title().replace("_", " ")} Integration for AI Content Automation
Auto-generated integration template
"""

from typing import List, Dict, Any
from google_sheets_client import (
    GoogleSheetsClient, 
    SheetRange, 
    ValueRenderOption, 
    DateTimeRenderOption,
    ValueInputOption,
    MajorDimension
)


class {integration_name.title().replace("_", "")}Integration:
    """
    {config["description"]}
    """
    
    def __init__(self, client: GoogleSheetsClient):
        self.client = client
        self.spreadsheet_id = "{config["spreadsheet_id"]}"
        self.sheet_configs = {config["sheets"]}
    
    def read_project_data(self, sheet_name: str, project_range: str = None) -> List[List[str]]:
        """Read project data from the specified sheet."""
        if project_range:
            range_spec = SheetRange(sheet_name=sheet_name, start_row=1, end_row=100)
            return self.client.get_rows_in_range(
                spreadsheet_id=self.spreadsheet_id,
                sheet_range=range_spec
            )
        else:
            return self.client.get_sheet_data(
                spreadsheet_id=self.spreadsheet_id,
                sheet_name=sheet_name
            )
    
    def write_batch_results(self, sheet_name: str, results: List[List[str]]) -> None:
        """Write batch job results to the specified sheet."""
        range_spec = SheetRange(sheet_name=sheet_name, start_row=1, start_col="A")
        self.client.write_values(
            spreadsheet_id=self.spreadsheet_id,
            sheet_range=range_spec,
            values=results
        )
    
    def get_performance_metrics(self, sheet_name: str) -> List[List[str]]:
        """Get performance metrics data."""
        return self.client.get_sheet_data(
            spreadsheet_id=self.spreadsheet_id,
            sheet_name=sheet_name,
            value_render_option=ValueRenderOption.UNFORMATTED_VALUE
        )


# Example usage
if __name__ == "__main__":
    from google_sheets_client import create_client_from_config
    from config.google_sheets_config import get_client_config
    
    # Initialize client
    config = get_client_config()
    client = create_client_from_config(config)
    
    # Create integration
    integration = {integration_name.title().replace("_", "")}Integration(client)
    
    # Example operations
    data = integration.read_project_data("projects")
    print(f"Read {len(data)} rows of project data")
    
    client.close()
'''
    
    with open(output_path, 'w') as f:
        f.write(template_content)
    
    return output_path


if __name__ == "__main__":
    # Create example integration templates
    for integration_name in INTEGRATION_EXAMPLES.keys():
        output_file = f"code/integration_{integration_name}.py"
        create_integration_template(integration_name, output_file)
        print(f"Created integration template: {output_file}")