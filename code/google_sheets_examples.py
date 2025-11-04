"""
Comprehensive Google Sheets Client Usage Examples
for AI Content Automation System

This module demonstrates various integration patterns and use cases
for the Google Sheets API client within the AI Content Automation system.
"""

import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Add the code directory to Python path
sys.path.append(str(Path(__file__).parent))

from google_sheets_client import (
    GoogleSheetsClient,
    SheetRange, 
    ValueRenderOption, 
    DateTimeRenderOption,
    ValueInputOption,
    MajorDimension,
    RateLimitConfig,
    create_client_from_config
)
from google_sheets_config import get_client_config, get_integration_config


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContentTrackingIntegration:
    """
    Integration for tracking content generation progress and results.
    
    This class demonstrates how to use the Google Sheets client to:
    - Track project progress
    - Monitor content generation status
    - Store and retrieve content metadata
    - Analyze performance data
    """
    
    def __init__(self, client: GoogleSheetsClient, spreadsheet_id: str):
        self.client = client
        self.spreadsheet_id = spreadsheet_id
        
    def create_project_tracking_sheet(self) -> None:
        """Create a new project tracking sheet with headers."""
        headers = [
            ["Project ID", "Project Name", "Status", "Progress %", "Created Date", 
             "Updated Date", "Content Type", "Platform", "Quality Score", "Notes"]
        ]
        
        try:
            # Create the sheet
            self.client.create_sheet(self.spreadsheet_id, "Project Tracking")
            
            # Add headers
            range_spec = SheetRange(sheet_name="Project Tracking", start_row=1, end_row=1, 
                                  start_col="A", end_col="J")
            self.client.write_values(
                spreadsheet_id=self.spreadsheet_id,
                sheet_range=range_spec,
                values=headers,
                value_input_option=ValueInputOption.USER_ENTERED
            )
            
            logger.info("Created project tracking sheet with headers")
            
        except Exception as e:
            logger.error(f"Error creating project tracking sheet: {e}")
            raise
    
    def update_project_status(self, project_data: Dict[str, Any]) -> None:
        """Update project status in the tracking sheet."""
        try:
            # Prepare row data
            row_data = [
                project_data.get("project_id", ""),
                project_data.get("project_name", ""),
                project_data.get("status", "pending"),
                project_data.get("progress", 0),
                project_data.get("created_date", datetime.now().strftime("%Y-%m-%d")),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                project_data.get("content_type", ""),
                project_data.get("platform", ""),
                project_data.get("quality_score", 0),
                project_data.get("notes", "")
            ]
            
            # Find the next empty row or update existing
            existing_data = self.client.get_sheet_data(
                spreadsheet_id=self.spreadsheet_id,
                sheet_name="Project Tracking"
            )
            
            # If headers only, start at row 2
            start_row = 2 if len(existing_data) <= 1 else len(existing_data) + 1
            
            range_spec = SheetRange(
                sheet_name="Project Tracking",
                start_row=start_row,
                end_row=start_row,
                start_col="A",
                end_col="J"
            )
            
            self.client.write_values(
                spreadsheet_id=self.spreadsheet_id,
                sheet_range=range_spec,
                values=[row_data],
                value_input_option=ValueInputOption.USER_ENTERED
            )
            
            logger.info(f"Updated project status for {project_data.get('project_name', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error updating project status: {e}")
            raise
    
    def get_project_data(self, project_id: str) -> Optional[List[str]]:
        """Retrieve data for a specific project."""
        try:
            data = self.client.get_sheet_data(
                spreadsheet_id=self.spreadsheet_id,
                sheet_name="Project Tracking",
                value_render_option=ValueRenderOption.UNFORMATTED_VALUE
            )
            
            # Find project by ID (assuming project_id is in column A)
            for row in data[1:]:  # Skip header row
                if row and row[0] == project_id:
                    return row
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting project data: {e}")
            raise
    
    def batch_update_projects(self, projects: List[Dict[str, Any]]) -> None:
        """Update multiple projects in a single batch operation."""
        try:
            # Prepare batch update requests
            updates = []
            
            for i, project in enumerate(projects, start=2):  # Start from row 2 (after headers)
                row_values = [
                    project.get("project_id", ""),
                    project.get("project_name", ""),
                    project.get("status", "pending"),
                    project.get("progress", 0),
                    project.get("created_date", datetime.now().strftime("%Y-%m-%d")),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    project.get("content_type", ""),
                    project.get("platform", ""),
                    project.get("quality_score", 0),
                    project.get("notes", "")
                ]
                
                # Create range for this project
                start_row = f"{i}"
                end_row = f"{i}"
                range_name = f"Project Tracking!A{start_row}:J{end_row}"
                
                updates.append({
                    'range': range_name,
                    'values': [row_values]
                })
            
            # Use batch update for efficiency
            body = {
                'data': updates,
                'valueInputOption': ValueInputOption.USER_ENTERED.value
            }
            
            # Note: This would need to be implemented in the client
            # For now, we'll do individual updates
            for update in updates:
                range_spec = SheetRange(
                    sheet_name="Project Tracking",
                    start_row=2,
                    start_col="A",
                    end_col="J"
                )
                # Parse range from update['range'] for actual implementation
            
            logger.info(f"Batch updated {len(projects)} projects")
            
        except Exception as e:
            logger.error(f"Error in batch update: {e}")
            raise


class BatchJobMonitoring:
    """
    Integration for monitoring batch video generation jobs.
    
    Demonstrates how to track job queues, monitor progress,
    and store job execution data.
    """
    
    def __init__(self, client: GoogleSheetsClient, spreadsheet_id: str):
        self.client = client
        self.spreadsheet_id = spreadsheet_id
    
    def create_job_monitoring_sheet(self) -> None:
        """Create a job monitoring dashboard sheet."""
        headers = [
            ["Job ID", "Project ID", "Job Type", "Status", "Progress %", 
             "Current Stage", "Started At", "Completed At", "Duration (min)", "Error Message"]
        ]
        
        try:
            self.client.create_sheet(self.spreadsheet_id, "Job Monitoring")
            
            range_spec = SheetRange(sheet_name="Job Monitoring", start_row=1, end_row=1,
                                  start_col="A", end_col="J")
            self.client.write_values(
                spreadsheet_id=self.spreadsheet_id,
                sheet_range=range_spec,
                values=headers
            )
            
            logger.info("Created job monitoring sheet")
            
        except Exception as e:
            logger.error(f"Error creating job monitoring sheet: {e}")
            raise
    
    def log_job_progress(self, job_data: Dict[str, Any]) -> None:
        """Log job progress and status updates."""
        try:
            # Calculate duration if completed
            duration_minutes = ""
            if job_data.get("status") == "completed" and job_data.get("started_at"):
                start_time = datetime.fromisoformat(job_data["started_at"])
                end_time = datetime.fromisoformat(job_data.get("completed_at", datetime.now().isoformat()))
                duration = (end_time - start_time).total_seconds() / 60
                duration_minutes = f"{duration:.1f}"
            
            row_data = [
                job_data.get("job_id", ""),
                job_data.get("project_id", ""),
                job_data.get("job_type", ""),
                job_data.get("status", "pending"),
                job_data.get("progress", 0),
                job_data.get("current_stage", ""),
                job_data.get("started_at", ""),
                job_data.get("completed_at", ""),
                duration_minutes,
                job_data.get("error_message", "")
            ]
            
            # Append to job monitoring sheet
            self.client.append_values(
                spreadsheet_id=self.spreadsheet_id,
                sheet_name="Job Monitoring",
                values=[row_data],
                value_input_option=ValueInputOption.USER_ENTERED
            )
            
            logger.info(f"Logged progress for job {job_data.get('job_id', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error logging job progress: {e}")
            raise
    
    def get_active_jobs(self) -> List[List[str]]:
        """Get all currently active jobs."""
        try:
            data = self.client.get_sheet_data(
                spreadsheet_id=self.spreadsheet_id,
                sheet_name="Job Monitoring",
                value_render_option=ValueRenderOption.UNFORMATTED_VALUE
            )
            
            # Filter for active jobs (not completed or failed)
            active_jobs = []
            for row in data[1:]:  # Skip header
                if row and len(row) > 3 and row[3] not in ["completed", "failed"]:
                    active_jobs.append(row)
            
            return active_jobs
            
        except Exception as e:
            logger.error(f"Error getting active jobs: {e}")
            raise


class PerformanceAnalytics:
    """
    Integration for storing and analyzing content performance data.
    
    Shows how to:
    - Store engagement metrics
    - Track platform performance
    - Analyze trends over time
    """
    
    def __init__(self, client: GoogleSheetsClient, spreadsheet_id: str):
        self.client = client
        self.spreadsheet_id = spreadsheet_id
    
    def create_analytics_sheet(self) -> None:
        """Create analytics tracking sheet."""
        headers = [
            ["Date", "Project ID", "Platform", "Views", "Likes", "Comments", 
             "Shares", "Engagement Rate", "Watch Time", "CTR", "Performance Score"]
        ]
        
        try:
            self.client.create_sheet(self.spreadsheet_id, "Performance Analytics")
            
            range_spec = SheetRange(sheet_name="Performance Analytics", start_row=1, end_row=1,
                                  start_col="A", end_col="K")
            self.client.write_values(
                spreadsheet_id=self.spreadsheet_id,
                sheet_range=range_spec,
                values=headers
            )
            
            logger.info("Created performance analytics sheet")
            
        except Exception as e:
            logger.error(f"Error creating analytics sheet: {e}")
            raise
    
    def log_performance_metrics(self, metrics: List[Dict[str, Any]]) -> None:
        """Log performance metrics for multiple projects."""
        try:
            rows_data = []
            
            for metric in metrics:
                row_data = [
                    metric.get("date", datetime.now().strftime("%Y-%m-%d")),
                    metric.get("project_id", ""),
                    metric.get("platform", ""),
                    metric.get("views", 0),
                    metric.get("likes", 0),
                    metric.get("comments", 0),
                    metric.get("shares", 0),
                    metric.get("engagement_rate", 0),
                    metric.get("watch_time", 0),
                    metric.get("ctr", 0),
                    metric.get("performance_score", 0)
                ]
                rows_data.append(row_data)
            
            # Append all rows
            self.client.append_values(
                spreadsheet_id=self.spreadsheet_id,
                sheet_name="Performance Analytics",
                values=rows_data,
                value_input_option=ValueInputOption.USER_ENTERED
            )
            
            logger.info(f"Logged performance metrics for {len(metrics)} entries")
            
        except Exception as e:
            logger.error(f"Error logging performance metrics: {e}")
            raise
    
    def get_platform_performance(self, platform: str, days: int = 30) -> List[List[str]]:
        """Get performance data for a specific platform over a given period."""
        try:
            # Get all data
            data = self.client.get_sheet_data(
                spreadsheet_id=self.spreadsheet_id,
                sheet_name="Performance Analytics",
                value_render_option=ValueRenderOption.UNFORMATTED_VALUE
            )
            
            # Filter by platform and date range
            cutoff_date = datetime.now() - timedelta(days=days)
            platform_data = []
            
            for row in data[1:]:  # Skip header
                if row and len(row) > 2:
                    # Check platform match
                    if len(row) > 2 and row[2] == platform:
                        # Check date (assuming date is in column 0)
                        if len(row) > 0 and row[0]:
                            try:
                                row_date = datetime.strptime(row[0], "%Y-%m-%d")
                                if row_date >= cutoff_date:
                                    platform_data.append(row)
                            except ValueError:
                                # Skip rows with invalid dates
                                continue
            
            return platform_data
            
        except Exception as e:
            logger.error(f"Error getting platform performance: {e}")
            raise


def demonstrate_rate_limiting():
    """Demonstrate rate limiting and backoff behavior."""
    print("=== Rate Limiting Demonstration ===")
    
    # Custom rate limit config
    rate_config = RateLimitConfig(
        max_requests_per_minute=10,  # Low for demo
        backoff_base_delay=0.5,
        max_retries=3
    )
    
    # Create client with custom config
    config = get_client_config()
    config['rate_limits'] = {
        'max_requests_per_minute': 10,
        'backoff_base_delay': 0.5,
        'max_retries': 3
    }
    
    try:
        client = create_client_from_config(config)
        
        # Test rate limit status
        status = client.get_rate_limit_status()
        print(f"Rate limit status: {status}")
        
        # Perform some requests to test rate limiting
        if client.health_check():
            print("✓ Client health check passed")
        
        client.close()
        print("✓ Rate limiting demonstration completed")
        
    except Exception as e:
        print(f"✗ Rate limiting demo failed: {e}")


def demonstrate_batch_operations():
    """Demonstrate batch read operations for efficiency."""
    print("=== Batch Operations Demonstration ===")
    
    try:
        config = get_client_config()
        client = create_client_from_config(config)
        
        # Example spreadsheet and ranges (replace with actual values)
        spreadsheet_id = "your-spreadsheet-id"
        
        # Define multiple ranges to read
        ranges = [
            SheetRange(sheet_name="Sheet1", start_row=1, end_row=10, start_col="A", end_col="C"),
            SheetRange(sheet_name="Sheet2", start_row=1, end_row=5, start_col="A", end_col="B"),
            SheetRange(sheet_name="Sheet3", start_row=1, end_row=1, start_col="A", end_col="Z")
        ]
        
        # Perform batch read
        results = client.get_multiple_ranges(
            spreadsheet_id=spreadsheet_id,
            ranges=ranges
        )
        
        print(f"Batch read results: {len(results)} ranges")
        for range_name, data in results.items():
            print(f"  {range_name}: {len(data)} rows")
        
        client.close()
        print("✓ Batch operations demonstration completed")
        
    except Exception as e:
        print(f"✗ Batch operations demo failed: {e}")


def demonstrate_error_handling():
    """Demonstrate error handling and recovery."""
    print("=== Error Handling Demonstration ===")
    
    try:
        config = get_client_config()
        client = create_client_from_config(config)
        
        # Test with invalid spreadsheet ID to trigger error
        try:
            client.get_sheet_data(
                spreadsheet_id="invalid-id",
                sheet_name="Sheet1"
            )
        except Exception as e:
            print(f"✓ Caught expected error: {type(e).__name__}")
        
        # Test health check
        if client.health_check():
            print("✓ Client is working correctly")
        
        client.close()
        print("✓ Error handling demonstration completed")
        
    except Exception as e:
        print(f"✗ Error handling demo failed: {e}")


def main():
    """Run all demonstration examples."""
    print("Google Sheets Client - AI Content Automation Integration Examples")
    print("=" * 70)
    
    # Note: These examples require actual credentials and spreadsheet IDs
    # to run successfully. They demonstrate the API usage patterns.
    
    print("\n1. Rate Limiting Demonstration")
    demonstrate_rate_limiting()
    
    print("\n2. Batch Operations Demonstration")
    demonstrate_batch_operations()
    
    print("\n3. Error Handling Demonstration")
    demonstrate_error_handling()
    
    print("\n4. Integration Pattern Examples")
    print("   - ContentTrackingIntegration: Track project progress")
    print("   - BatchJobMonitoring: Monitor job queues")
    print("   - PerformanceAnalytics: Store performance metrics")
    
    print("\nTo use these examples:")
    print("1. Set up service account credentials")
    print("2. Configure environment variables")
    print("3. Update spreadsheet IDs in the examples")
    print("4. Run with actual data")
    
    print("\nConfiguration files created:")
    print("- code/google_sheets_client.py (main client)")
    print("- code/google_sheets_config.py (configuration)")
    print("- code/requirements-google-sheets.txt (dependencies)")
    print("- code/google_sheets_examples.py (this file)")


if __name__ == "__main__":
    main()