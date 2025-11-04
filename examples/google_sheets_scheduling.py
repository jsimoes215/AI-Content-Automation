#!/usr/bin/env python3
"""
Google Sheets Scheduling Integration Example
===========================================

This example demonstrates how to integrate Google Sheets with the AI Content
Automation System's scheduling functionality. You'll learn how to:

1. Set up Google Sheets API authentication
2. Read content data from Google Sheets
3. Import and validate content data
4. Generate optimal schedules from sheets data
5. Create schedules using the scheduling API
6. Export results back to Google Sheets
7. Handle real-time synchronization

Prerequisites:
- Google Cloud Project with Sheets API enabled
- Service account JSON credentials file
- Python packages: gspread, google-auth, pandas, aiohttp

Installation:
pip install gspread google-auth google-auth-oauthlib google-auth-httplib2 pandas aiohttp python-dateutil

Setup:
1. Create a Google Cloud Project
2. Enable the Google Sheets API
3. Create a service account and download credentials JSON
4. Share your spreadsheet with the service account email
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import csv

# Google Sheets integration
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Data manipulation
import pandas as pd
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =============================================================================
# GOOGLE SHEETS CLIENT CONFIGURATION
# =============================================================================

@dataclass
class GoogleSheetsConfig:
    """Configuration for Google Sheets integration"""
    credentials_file: str
    spreadsheet_id: str
    sheet_name: str
    range: str = "A:Z"
    permissions: str = "write"  # read, write, admin

@dataclass
class ContentData:
    """Data structure for content imported from sheets"""
    title: str
    content: str
    platform: str
    scheduled_time: str
    target_audience: str
    tone: str
    hashtags: Optional[str] = None
    status: str = "draft"
    row_number: Optional[int] = None
    content_id: Optional[str] = None

# =============================================================================
# GOOGLE SHEETS CLIENT
# =============================================================================

class GoogleSheetsClient:
    """Client for Google Sheets API integration"""
    
    def __init__(self, config: GoogleSheetsConfig):
        """
        Initialize Google Sheets client
        
        Args:
            config: GoogleSheetsConfig with credentials and spreadsheet info
        """
        self.config = config
        self.service = self._authenticate()
        self.client = self._authorize_client()
        self.spreadsheet = self.client.open_by_key(config.spreadsheet_id)
        self.worksheet = self.spreadsheet.worksheet(config.sheet_name)
        
        print(f"✅ Connected to Google Sheets: {config.sheet_name}")
    
    def _authenticate(self):
        """Authenticate with Google Sheets API using service account"""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/spreadsheets'
            ]
            
            credentials = Credentials.from_service_account_file(
                self.config.credentials_file, 
                scopes=scope
            )
            
            return build('sheets', 'v4', credentials=credentials)
        
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    def _authorize_client(self):
        """Authorize gspread client"""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = Credentials.from_service_account_file(
                self.config.credentials_file,
                scopes=scope
            )
            
            return gspread.authorize(credentials)
        
        except Exception as e:
            logger.error(f"gspread authorization failed: {e}")
            raise
    
    def read_data(self) -> List[List[str]]:
        """
        Read all data from the specified range
        
        Returns:
            List of rows, where each row is a list of cell values
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.config.spreadsheet_id,
                range=f"{self.config.sheet_name}!{self.config.range}"
            ).execute()
            
            values = result.get('values', [])
            print(f"📖 Read {len(values)} rows from Google Sheets")
            
            return values
        
        except HttpError as error:
            logger.error(f"Error reading data: {error}")
            raise
    
    def write_data(self, data: List[List[str]], range_name: str = None):
        """
        Write data to Google Sheets
        
        Args:
            data: 2D list of data to write
            range_name: Optional specific range (defaults to config range)
        """
        try:
            range_to_use = range_name or f"{self.config.sheet_name}!{self.config.range}"
            
            body = {
                'values': data
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.config.spreadsheet_id,
                range=range_to_use,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            print(f"✍️  Updated {result.get('updatedCells', 0)} cells in Google Sheets")
            
        except HttpError as error:
            logger.error(f"Error writing data: {error}")
            raise
    
    def append_data(self, data: List[List[str]], range_name: str = None):
        """
        Append data to the end of the sheet
        
        Args:
            data: Data to append
            range_name: Optional range specification
        """
        try:
            range_to_use = range_name or f"{self.config.sheet_name}!A:Z"
            
            body = {
                'values': data
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.config.spreadsheet_id,
                range=range_to_use,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            print(f"➕ Appended {result.get('updates', {}).get('updatedRows', 0)} rows")
            
        except HttpError as error:
            logger.error(f"Error appending data: {error}")
            raise
    
    def create_sheet(self, title: str, rows: int = 1000, cols: int = 26):
        """Create a new worksheet"""
        try:
            worksheet = self.spreadsheet.add_worksheet(title=title, rows=rows, cols=cols)
            print(f"📄 Created new sheet: {title}")
            return worksheet
        
        except Exception as e:
            logger.error(f"Error creating sheet: {e}")
            raise
    
    def clear_sheet(self, range_name: str = None):
        """Clear data from the sheet"""
        try:
            range_to_clear = range_name or f"{self.config.sheet_name}!A:Z"
            
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.config.spreadsheet_id,
                range=range_to_clear
            ).execute()
            
            print(f"🧹 Cleared data from {self.config.sheet_name}")
            
        except HttpError as error:
            logger.error(f"Error clearing sheet: {error}")
            raise

# =============================================================================
# CONTENT DATA PROCESSOR
# =============================================================================

class ContentDataProcessor:
    """Process and validate content data from Google Sheets"""
    
    # Expected column headers and their mappings
    COLUMN_MAPPINGS = {
        'title': ['title', 'name', 'headline', 'video_title', 'post_title'],
        'content': ['content', 'description', 'text', 'script', 'body'],
        'platform': ['platform', 'channel', 'social_media'],
        'scheduled_time': ['scheduled_time', 'publish_time', 'post_time', 'date', 'time'],
        'target_audience': ['target_audience', 'audience', 'demographic'],
        'tone': ['tone', 'style', 'mood', 'voice'],
        'hashtags': ['hashtags', 'tags', 'keywords'],
        'status': ['status', 'state', 'stage']
    }
    
    VALID_PLATFORMS = ['youtube', 'tiktok', 'instagram', 'linkedin', 'twitter', 'facebook']
    VALID_STATUSES = ['draft', 'scheduled', 'published', 'failed', 'canceled']
    
    def __init__(self):
        self.validation_errors = []
        self.processed_items = []
    
    def validate_headers(self, headers: List[str]) -> Dict[str, Optional[int]]:
        """
        Validate and map column headers to expected fields
        
        Args:
            headers: List of column headers from the sheet
            
        Returns:
            Dictionary mapping field names to column indices
        """
        field_mapping = {}
        
        for field, possible_names in self.COLUMN_MAPPINGS.items():
            field_mapping[field] = None
            
            for i, header in enumerate(headers):
                header_lower = header.lower().strip()
                if header_lower in [name.lower() for name in possible_names]:
                    field_mapping[field] = i
                    break
        
        # Check for required fields
        required_fields = ['title', 'content', 'platform', 'scheduled_time']
        missing_required = [field for field in required_fields if field_mapping[field] is None]
        
        if missing_required:
            raise ValueError(f"Missing required columns: {missing_required}")
        
        return field_mapping
    
    def process_data(self, data: List[List[str]]) -> List[ContentData]:
        """
        Process raw sheet data into ContentData objects
        
        Args:
            data: 2D list from Google Sheets (first row should be headers)
            
        Returns:
            List of ContentData objects
        """
        if not data or len(data) < 2:
            raise ValueError("Sheet must contain at least headers and one data row")
        
        headers = data[0]
        rows = data[1:]
        
        # Validate headers and get column mapping
        column_mapping = self.validate_headers(headers)
        
        processed_items = []
        
        for row_index, row in enumerate(rows, start=2):  # Start from row 2 (after headers)
            try:
                content_item = self._process_row(row, row_index, column_mapping)
                processed_items.append(content_item)
            
            except Exception as e:
                self.validation_errors.append({
                    'row': row_index,
                    'error': str(e),
                    'data': row
                })
                logger.warning(f"Row {row_index} validation failed: {e}")
        
        self.processed_items = processed_items
        print(f"✅ Processed {len(processed_items)} valid items from {len(rows)} rows")
        
        if self.validation_errors:
            logger.warning(f"Found {len(self.validation_errors)} validation errors")
            for error in self.validation_errors[:5]:  # Show first 5 errors
                logger.warning(f"Row {error['row']}: {error['error']}")
        
        return processed_items
    
    def _process_row(self, row: List[str], row_number: int, column_mapping: Dict) -> ContentData:
        """Process a single row of data"""
        
        def get_value(field: str, default: str = "") -> str:
            col_index = column_mapping.get(field)
            if col_index is not None and col_index < len(row):
                return str(row[col_index]).strip()
            return default
        
        # Extract data
        title = get_value('title')
        content = get_value('content')
        platform = get_value('platform').lower()
        scheduled_time = get_value('scheduled_time')
        target_audience = get_value('target_audience')
        tone = get_value('tone') or 'professional'
        hashtags = get_value('hashtags')
        status = get_value('status', 'draft').lower()
        
        # Validate required fields
        if not title:
            raise ValueError("Title is required")
        if not content:
            raise ValueError("Content is required")
        if not platform:
            raise ValueError("Platform is required")
        if not scheduled_time:
            raise ValueError("Scheduled time is required")
        
        # Validate platform
        if platform not in self.VALID_PLATFORMS:
            available = ", ".join(self.VALID_PLATFORMS)
            raise ValueError(f"Invalid platform '{platform}'. Valid options: {available}")
        
        # Validate status
        if status not in self.VALID_STATUSES:
            logger.warning(f"Unknown status '{status}', defaulting to 'draft'")
            status = 'draft'
        
        # Generate content ID
        content_id = f"sheet_{row_number}_{platform}"
        
        return ContentData(
            title=title,
            content=content,
            platform=platform,
            scheduled_time=scheduled_time,
            target_audience=target_audience,
            tone=tone,
            hashtags=hashtags,
            status=status,
            row_number=row_number,
            content_id=content_id
        )
    
    def export_to_dataframe(self) -> pd.DataFrame:
        """Export processed data to pandas DataFrame"""
        if not self.processed_items:
            return pd.DataFrame()
        
        data = []
        for item in self.processed_items:
            data.append(asdict(item))
        
        return pd.DataFrame(data)
    
    def get_validation_report(self) -> Dict:
        """Get detailed validation report"""
        total_rows = len(self.processed_items) + len(self.validation_errors)
        
        return {
            'total_rows': total_rows,
            'valid_rows': len(self.processed_items),
            'invalid_rows': len(self.validation_errors),
            'validation_rate': len(self.processed_items) / total_rows * 100 if total_rows > 0 else 0,
            'platforms': list(set(item.platform for item in self.processed_items)),
            'errors': self.validation_errors
        }

# =============================================================================
# SCHEDULING API CLIENT
# =============================================================================

class SchedulingAPIClient:
    """Client for the AI Content Automation scheduling API"""
    
    def __init__(self, api_base_url: str, api_key: str):
        """
        Initialize scheduling API client
        
        Args:
            api_base_url: Base URL of the scheduling API
            api_key: API authentication key
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_recommendations(self, platforms: List[str], count: int = 10) -> List[Dict]:
        """
        Get optimal posting time recommendations
        
        Args:
            platforms: List of platforms to get recommendations for
            count: Number of recommendations to return
            
        Returns:
            List of recommendation dictionaries
        """
        try:
            params = {
                "platforms": ",".join(platforms),
                "target_count": count
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/api/v1/scheduling/recommendations",
                    headers=self.headers,
                    params=params
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to get recommendations: {response.status} - {error_text}")
        
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []
    
    async def create_schedule(self, schedule_data: Dict) -> Optional[str]:
        """
        Create a new content schedule
        
        Args:
            schedule_data: Schedule data in API format
            
        Returns:
            Schedule ID if successful, None otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/api/v1/scheduling/calendar",
                    headers=self.headers,
                    json=schedule_data
                ) as response:
                    
                    if response.status == 201:
                        result = await response.json()
                        schedule_id = result["data"]["id"]
                        logger.info(f"✅ Created schedule: {schedule_id}")
                        return schedule_id
                    
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create schedule: {response.status} - {error_text}")
                        return None
        
        except Exception as e:
            logger.error(f"Error creating schedule: {e}")
            return None
    
    async def get_schedule_status(self, schedule_id: str) -> Optional[Dict]:
        """Get the status of a schedule"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/api/v1/scheduling/calendar/{schedule_id}",
                    headers=self.headers
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return result["data"]
                    else:
                        logger.error(f"Schedule not found: {schedule_id}")
                        return None
        
        except Exception as e:
            logger.error(f"Error getting schedule status: {e}")
            return None

# =============================================================================
# SCHEDULE GENERATOR
# =============================================================================

class ScheduleGenerator:
    """Generate optimized schedules from content data"""
    
    def __init__(self, api_client: SchedulingAPIClient):
        self.api_client = api_client
    
    async def generate_schedules(
        self, 
        content_items: List[ContentData],
        optimize_timing: bool = True
    ) -> List[Dict]:
        """
        Generate schedules from content items
        
        Args:
            content_items: List of ContentData objects
            optimize_timing: Whether to use AI recommendations for timing
            
        Returns:
            List of schedule data dictionaries ready for API submission
        """
        # Group content by platform
        by_platform = {}
        for item in content_items:
            if item.platform not in by_platform:
                by_platform[item.platform] = []
            by_platform[item.platform].append(item)
        
        schedules = []
        
        # Get recommendations for each platform if optimization is enabled
        recommendations = {}
        if optimize_timing:
            for platform in by_platform.keys():
                recs = await self.api_client.get_recommendations([platform], 10)
                recommendations[platform] = recs
        
        # Create schedules for each platform
        for platform, items in by_platform.items():
            schedule_data = self._create_platform_schedule(platform, items, recommendations)
            schedules.append(schedule_data)
        
        return schedules
    
    def _create_platform_schedule(
        self, 
        platform: str, 
        items: List[ContentData],
        recommendations: Dict[str, List[Dict]]
    ) -> Dict:
        """Create schedule data for a specific platform"""
        
        schedule_items = []
        
        for item in items:
            # Parse scheduled time
            scheduled_time = self._parse_datetime(item.scheduled_time)
            
            # Use recommendation if available and optimization is enabled
            if platform in recommendations and recommendations[platform]:
                # Find best recommendation close to the desired time
                recommendation = self._find_best_recommendation(
                    scheduled_time, recommendations[platform]
                )
                
                if recommendation:
                    scheduled_time = recommendation["recommended_time"]
            
            schedule_item = {
                "content_id": item.content_id,
                "platform": item.platform,
                "scheduled_time": scheduled_time,
                "metadata": {
                    "title": item.title,
                    "content": item.content,
                    "target_audience": item.target_audience,
                    "tone": item.tone,
                    "hashtags": item.hashtags,
                    "source": "google_sheets",
                    "row_number": item.row_number
                }
            }
            
            schedule_items.append(schedule_item)
        
        # Create the schedule
        schedule_data = {
            "title": f"Google Sheets Import - {platform.title()}",
            "timezone": "America/New_York",  # You may want to make this configurable
            "description": f"Auto-generated from Google Sheets data for {platform}",
            "items": schedule_items
        }
        
        return schedule_data
    
    def _parse_datetime(self, time_str: str) -> str:
        """Parse datetime string to ISO format"""
        if not time_str:
            # Default to next hour if no time specified
            next_hour = datetime.now() + timedelta(hours=1)
            next_hour = next_hour.replace(minute=0, second=0, microsecond=0)
            return next_hour.isoformat() + "Z"
        
        # Try common formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%m/%d/%Y %H:%M",
            "%m/%d/%Y %H:%M %p",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(time_str.strip(), fmt)
                return dt.isoformat() + "Z"
            except ValueError:
                continue
        
        # Try pandas parser as fallback
        try:
            dt = pd.to_datetime(time_str)
            return dt.isoformat() + "Z"
        except:
            # If all parsing fails, use current time
            logger.warning(f"Could not parse datetime: {time_str}, using current time")
            return datetime.now().isoformat() + "Z"
    
    def _find_best_recommendation(
        self, 
        target_time: str, 
        recommendations: List[Dict]
    ) -> Optional[Dict]:
        """Find the best recommendation close to the target time"""
        try:
            target_dt = datetime.fromisoformat(target_time.replace('Z', '+00:00'))
            
            best_rec = None
            min_diff = float('inf')
            
            for rec in recommendations:
                rec_dt = datetime.fromisoformat(rec['recommended_time'].replace('Z', '+00:00'))
                
                # Calculate time difference in hours
                diff = abs((rec_dt - target_dt).total_seconds() / 3600)
                
                # Prefer recommendations within 2 hours of target time
                if diff <= 2 and diff < min_diff:
                    min_diff = diff
                    best_rec = rec
            
            return best_rec
        
        except Exception as e:
            logger.warning(f"Error finding best recommendation: {e}")
            return recommendations[0] if recommendations else None

# =============================================================================
# MAIN INTEGRATION CLASS
# =============================================================================

class GoogleSheetsSchedulingIntegration:
    """Main class for Google Sheets scheduling integration"""
    
    def __init__(
        self, 
        sheets_config: GoogleSheetsConfig, 
        api_base_url: str, 
        api_key: str
    ):
        """
        Initialize the integration
        
        Args:
            sheets_config: Google Sheets configuration
            api_base_url: Scheduling API base URL
            api_key: Scheduling API key
        """
        self.sheets_config = sheets_config
        self.sheets_client = GoogleSheetsClient(sheets_config)
        self.api_client = SchedulingAPIClient(api_base_url, api_key)
        self.data_processor = ContentDataProcessor()
        self.schedule_generator = ScheduleGenerator(self.api_client)
        
        print("🚀 Google Sheets Scheduling Integration initialized")
    
    async def import_and_schedule_content(
        self,
        optimize_timing: bool = True,
        create_missing_sheets: bool = False
    ) -> Dict:
        """
        Import content from Google Sheets and create schedules
        
        Args:
            optimize_timing: Use AI recommendations for optimal timing
            create_missing_sheets: Create output sheets if they don't exist
            
        Returns:
            Dictionary with import and scheduling results
        """
        print("\n" + "="*80)
        print("📥 IMPORTING AND SCHEDULING CONTENT FROM GOOGLE SHEETS")
        print("="*80)
        
        try:
            # Step 1: Read data from Google Sheets
            print("\n📖 Step 1: Reading data from Google Sheets...")
            raw_data = self.sheets_client.read_data()
            
            if not raw_data:
                raise ValueError("No data found in Google Sheets")
            
            # Step 2: Process and validate data
            print("\n🔍 Step 2: Processing and validating data...")
            content_items = self.data_processor.process_data(raw_data)
            
            if not content_items:
                raise ValueError("No valid content items found")
            
            # Step 3: Generate schedules
            print("\n📅 Step 3: Generating optimized schedules...")
            schedules = await self.schedule_generator.generate_schedules(
                content_items, 
                optimize_timing
            )
            
            # Step 4: Create schedules via API
            print("\n⚡ Step 4: Creating schedules via API...")
            created_schedules = []
            
            for schedule_data in schedules:
                schedule_id = await self.api_client.create_schedule(schedule_data)
                if schedule_id:
                    created_schedules.append({
                        'schedule_id': schedule_id,
                        'platform': schedule_data['items'][0]['platform'],
                        'title': schedule_data['title'],
                        'item_count': len(schedule_data['items'])
                    })
            
            # Step 5: Export results
            print("\n📤 Step 5: Exporting results back to Google Sheets...")
            await self._export_results(content_items, created_schedules, create_missing_sheets)
            
            # Step 6: Generate report
            print("\n📊 Step 6: Generating completion report...")
            report = self._generate_report(content_items, created_schedules)
            
            print("\n✅ Import and scheduling completed successfully!")
            return report
        
        except Exception as e:
            logger.error(f"Import and scheduling failed: {e}")
            raise
    
    async def _export_results(
        self, 
        content_items: List[ContentData], 
        schedules: List[Dict],
        create_missing_sheets: bool = False
    ):
        """Export results back to Google Sheets"""
        
        # Prepare export data
        export_data = []
        
        # Headers for results sheet
        result_headers = [
            'Original Title', 'Platform', 'Original Scheduled Time', 'New Scheduled Time',
            'Schedule ID', 'Status', 'Target Audience', 'Tone', 'Export Timestamp'
        ]
        export_data.append(result_headers)
        
        # Create lookup for schedules
        schedule_lookup = {}
        for schedule in schedules:
            platform = schedule['platform']
            if platform not in schedule_lookup:
                schedule_lookup[platform] = []
            schedule_lookup[platform].append(schedule)
        
        # Add data rows
        for item in content_items:
            # Find corresponding schedule
            new_scheduled_time = item.scheduled_time
            schedule_id = ""
            status = "imported"
            
            if item.platform in schedule_lookup:
                for schedule in schedule_lookup[item.platform]:
                    # Find matching content item (simplified matching)
                    if any(
                        meta.get('row_number') == item.row_number 
                        for meta_item in self.schedule_generator._create_platform_schedule(
                            item.platform, [item], {}
                        )['items']
                        for meta in [meta_item.get('metadata', {})]
                    ):
                        new_scheduled_time = schedule.get('new_scheduled_time', item.scheduled_time)
                        schedule_id = schedule['schedule_id']
                        status = "scheduled"
                        break
            
            export_data.append([
                item.title,
                item.platform,
                item.scheduled_time,
                new_scheduled_time,
                schedule_id,
                status,
                item.target_audience,
                item.tone,
                datetime.now().isoformat()
            ])
        
        # Write to results sheet
        try:
            # Try to use existing sheet
            results_sheet = self.sheets_client.spreadsheet.worksheet("Results")
        except gspread.WorksheetNotFound:
            if create_missing_sheets:
                results_sheet = self.sheets_client.create_sheet("Results", 2000, 26)
            else:
                logger.warning("Results sheet not found and create_missing_sheets=False")
                return
        
        # Write results data
        self.sheets_client.write_data(
            export_data, 
            f"Results!A1"
        )
    
    def _generate_report(self, content_items: List[ContentData], schedules: List[Dict]) -> Dict:
        """Generate a comprehensive report of the import/scheduling process"""
        
        # Platform breakdown
        platform_counts = {}
        for item in content_items:
            platform = item.platform
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        # Status breakdown
        status_counts = {}
        for item in content_items:
            status = item.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Validation report
        validation_report = self.data_processor.get_validation_report()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_items': len(content_items),
                'successful_schedules': len(schedules),
                'success_rate': len(schedules) / len(content_items) * 100 if content_items else 0
            },
            'platform_breakdown': platform_counts,
            'status_breakdown': status_counts,
            'validation': validation_report,
            'schedules_created': schedules,
            'sheets_info': {
                'spreadsheet_id': self.sheets_config.spreadsheet_id,
                'sheet_name': self.sheets_config.sheet_name
            }
        }
        
        return report
    
    async def monitor_schedule_progress(self, schedule_ids: List[str]) -> Dict:
        """Monitor the progress of created schedules"""
        print(f"\n🔍 Monitoring {len(schedule_ids)} schedules...")
        
        monitoring_results = {}
        
        for schedule_id in schedule_ids:
            try:
                status = await self.api_client.get_schedule_status(schedule_id)
                monitoring_results[schedule_id] = status
                
                if status:
                    print(f"   📋 {schedule_id}: {status.get('status', 'unknown')} - "
                          f"{status.get('completedItems', 0)}/{status.get('totalItems', 0)} items")
                else:
                    print(f"   ❌ {schedule_id}: Not found")
                
                await asyncio.sleep(1)  # Avoid overwhelming the API
            
            except Exception as e:
                logger.error(f"Error monitoring {schedule_id}: {e}")
                monitoring_results[schedule_id] = {'error': str(e)}
        
        return monitoring_results
    
    async def export_schedule_results(
        self, 
        schedule_ids: List[str], 
        output_sheet_name: str = "Schedule Results"
    ):
        """Export detailed schedule results to Google Sheets"""
        print(f"\n📤 Exporting detailed results for {len(schedule_ids)} schedules...")
        
        export_data = []
        
        # Headers
        headers = [
            'Schedule ID', 'Title', 'Platform', 'Content Title', 'Scheduled Time',
            'Status', 'Progress', 'Created At', 'Updated At'
        ]
        export_data.append(headers)
        
        # Get detailed info for each schedule
        for schedule_id in schedule_ids:
            status = await self.api_client.get_schedule_status(schedule_id)
            
            if status and 'items' in status:
                for item in status['items']:
                    export_data.append([
                        schedule_id,
                        status.get('title', ''),
                        item.get('platform', ''),
                        item.get('metadata', {}).get('title', ''),
                        item.get('scheduled_time', ''),
                        item.get('status', ''),
                        f"{item.get('progress', 0)}%",
                        status.get('createdAt', ''),
                        status.get('updatedAt', '')
                    ])
        
        # Write to output sheet
        try:
            output_sheet = self.sheets_client.spreadsheet.worksheet(output_sheet_name)
        except gspread.WorksheetNotFound:
            output_sheet = self.sheets_client.create_sheet(output_sheet_name, 10000, 26)
        
        self.sheets_client.write_data(export_data, f"{output_sheet_name}!A1")
        print(f"✅ Exported {len(export_data)-1} records to {output_sheet_name}")

# =============================================================================
# EXAMPLE USAGE AND TUTORIAL FUNCTIONS
# =============================================================================

async def tutorial_basic_integration():
    """
    Tutorial 1: Basic Google Sheets to Scheduling API integration
    """
    print("\n" + "="*80)
    print("🎓 TUTORIAL 1: Basic Google Sheets Integration")
    print("="*80)
    
    # Configuration
    sheets_config = GoogleSheetsConfig(
        credentials_file="path/to/your/service-account.json",
        spreadsheet_id="your-spreadsheet-id",
        sheet_name="Content Schedule",
        range="A:Z"
    )
    
    api_base_url = "http://localhost:8000"
    api_key = "your-api-key-here"
    
    # Initialize integration
    integration = GoogleSheetsSchedulingIntegration(sheets_config, api_base_url, api_key)
    
    # Import and schedule content
    try:
        report = await integration.import_and_schedule_content(optimize_timing=True)
        
        print("\n📊 SUMMARY:")
        print(f"   Total items: {report['summary']['total_items']}")
        print(f"   Schedules created: {report['summary']['successful_schedules']}")
        print(f"   Success rate: {report['summary']['success_rate']:.1f}%")
        
        print(f"\n🎯 PLATFORMS:")
        for platform, count in report['platform_breakdown'].items():
            print(f"   {platform}: {count} items")
        
        print(f"\n✅ Platform breakdown complete!")
        
    except Exception as e:
        print(f"❌ Tutorial failed: {e}")

async def tutorial_batch_processing():
    """
    Tutorial 2: Batch processing multiple spreadsheets
    """
    print("\n" + "="*80)
    print("🎓 TUTORIAL 2: Batch Processing Multiple Spreadsheets")
    print("="*80)
    
    # Configuration for multiple spreadsheets
    spreadsheets = [
        {
            'name': 'Marketing Campaign',
            'config': GoogleSheetsConfig(
                credentials_file="path/to/service-account.json",
                spreadsheet_id="marketing-spreadsheet-id",
                sheet_name="Campaign Content",
                range="A:Z"
            )
        },
        {
            'name': 'Product Launch',
            'config': GoogleSheetsConfig(
                credentials_file="path/to/service-account.json",
                spreadsheet_id="product-spreadsheet-id", 
                sheet_name="Launch Content",
                range="A:Z"
            )
        }
    ]
    
    api_base_url = "http://localhost:8000"
    api_key = "your-api-key-here"
    
    all_reports = []
    
    for spreadsheet in spreadsheets:
        print(f"\n📊 Processing: {spreadsheet['name']}")
        
        try:
            integration = GoogleSheetsSchedulingIntegration(
                spreadsheet['config'], 
                api_base_url, 
                api_key
            )
            
            report = await integration.import_and_schedule_content()
            report['spreadsheet_name'] = spreadsheet['name']
            all_reports.append(report)
            
            print(f"   ✅ {spreadsheet['name']}: {report['summary']['successful_schedules']} schedules created")
        
        except Exception as e:
            print(f"   ❌ {spreadsheet['name']}: Failed - {e}")
    
    # Summary report
    total_items = sum(report['summary']['total_items'] for report in all_reports)
    total_schedules = sum(report['summary']['successful_schedules'] for report in all_reports)
    
    print(f"\n🎉 BATCH PROCESSING COMPLETE!")
    print(f"   Total spreadsheets: {len(spreadsheets)}")
    print(f"   Total items processed: {total_items}")
    print(f"   Total schedules created: {total_schedules}")
    print(f"   Overall success rate: {total_schedules/total_items*100 if total_items > 0 else 0:.1f}%")

async def tutorial_real_time_monitoring():
    """
    Tutorial 3: Real-time monitoring and updates
    """
    print("\n" + "="*80)
    print("🎓 TUTORIAL 3: Real-time Monitoring and Updates")
    print("="*80)
    
    sheets_config = GoogleSheetsConfig(
        credentials_file="path/to/service-account.json",
        spreadsheet_id="your-spreadsheet-id",
        sheet_name="Content Schedule"
    )
    
    api_base_url = "http://localhost:8000"
    api_key = "your-api-key-here"
    
    integration = GoogleSheetsSchedulingIntegration(sheets_config, api_base_url, api_key)
    
    # Import and schedule
    print("📥 Importing and scheduling content...")
    report = await integration.import_and_schedule_content()
    
    # Extract schedule IDs
    schedule_ids = [schedule['schedule_id'] for schedule in report['schedules_created']]
    
    if schedule_ids:
        print(f"\n🔍 Monitoring {len(schedule_ids)} schedules...")
        
        # Monitor progress for a limited time
        monitoring_start = datetime.now()
        timeout_minutes = 10
        
        while (datetime.now() - monitoring_start).total_seconds() < timeout_minutes * 60:
            results = await integration.monitor_schedule_progress(schedule_ids)
            
            # Check if all schedules are complete
            all_complete = all(
                result.get('status') in ['completed', 'failed', 'canceled']
                for result in results.values()
                if isinstance(result, dict) and 'status' in result
            )
            
            if all_complete:
                print("✅ All schedules completed!")
                break
            
            print("⏳ Waiting 30 seconds before next check...")
            await asyncio.sleep(30)
        
        # Export final results
        print("\n📤 Exporting final results...")
        await integration.export_schedule_results(schedule_ids, "Final Results")
        
        print("✅ Real-time monitoring tutorial complete!")
    else:
        print("❌ No schedules created to monitor")

def create_sample_sheets_data():
    """Create sample data for testing (exports to CSV as Google Sheets alternative)"""
    
    sample_data = [
        ["Title", "Content", "Platform", "Scheduled Time", "Target Audience", "Tone", "Hashtags", "Status"],
        ["AI Tutorial Part 1", "Introduction to artificial intelligence concepts for beginners", "youtube", 
         "2025-11-10 15:00:00", "tech beginners", "educational", "#AI #Tutorial #Beginners", "draft"],
        ["Quick AI Tips", "5 essential AI tools every professional should know", "linkedin", 
         "2025-11-11 09:00:00", "business professionals", "professional", "#AI #Productivity #Tools", "draft"],
        ["AI Demo Video", "Live demonstration of AI capabilities", "youtube", 
         "2025-11-12 14:00:00", "visual learners", "demonstrative", "#AI #Demo #Live", "draft"],
        ["Twitter AI Thread", "Thread about latest AI developments", "twitter", 
         "2025-11-11 12:00:00", "tech enthusiasts", "informative", "#AI #News #Tech", "draft"],
        ["Instagram AI Carousel", "Visual guide to AI concepts", "instagram", 
         "2025-11-13 17:00:00", "millennials", "casual", "#AI #Visual #Guide", "draft"]
    ]
    
    # Save as CSV for easy import to Google Sheets
    with open("sample_content_schedule.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(sample_data)
    
    print("✅ Created sample CSV file: sample_content_schedule.csv")
    print("   Import this file into Google Sheets to test the integration")

async def tutorial_complete_workflow():
    """
    Tutorial 4: Complete end-to-end workflow
    """
    print("\n" + "="*80)
    print("🎓 TUTORIAL 4: Complete End-to-End Workflow")
    print("="*80)
    
    sheets_config = GoogleSheetsConfig(
        credentials_file="path/to/service-account.json",
        spreadsheet_id="your-spreadsheet-id",
        sheet_name="Content Calendar"
    )
    
    api_base_url = "http://localhost:8000"
    api_key = "your-api-key-here"
    
    integration = GoogleSheetsSchedulingIntegration(sheets_config, api_base_url, api_key)
    
    try:
        # Step 1: Read and validate existing data
        print("\n📖 Step 1: Reading existing data...")
        raw_data = integration.sheets_client.read_data()
        content_items = integration.data_processor.process_data(raw_data)
        
        if not content_items:
            print("   ❌ No valid content found")
            return
        
        # Step 2: Get recommendations for optimization
        print("\n🎯 Step 2: Getting optimization recommendations...")
        platforms = list(set(item.platform for item in content_items))
        recommendations = await integration.api_client.get_recommendations(platforms, 15)
        
        print(f"   Got {len(recommendations)} recommendations for {len(platforms)} platforms")
        
        # Step 3: Generate optimized schedules
        print("\n📅 Step 3: Generating optimized schedules...")
        schedules = await integration.schedule_generator.generate_schedules(
            content_items, optimize_timing=True
        )
        
        # Step 4: Create schedules with batch processing
        print("\n⚡ Step 4: Creating schedules (batch processing)...")
        created_schedules = []
        
        for i, schedule_data in enumerate(schedules):
            print(f"   Creating schedule {i+1}/{len(schedules)}: {schedule_data['title']}")
            
            schedule_id = await integration.api_client.create_schedule(schedule_data)
            if schedule_id:
                created_schedules.append({
                    'schedule_id': schedule_id,
                    'platform': schedule_data['items'][0]['platform'],
                    'title': schedule_data['title'],
                    'item_count': len(schedule_data['items'])
                })
            
            # Small delay between API calls
            await asyncio.sleep(0.5)
        
        # Step 5: Monitor progress
        if created_schedules:
            print("\n🔍 Step 5: Monitoring progress...")
            schedule_ids = [s['schedule_id'] for s in created_schedules]
            
            # Monitor for 2 minutes
            monitoring_start = datetime.now()
            while (datetime.now() - monitoring_start).total_seconds() < 120:
                results = await integration.monitor_schedule_progress(schedule_ids)
                
                # Check completion status
                completed = sum(1 for r in results.values() 
                              if isinstance(r, dict) and r.get('status') == 'completed')
                
                if completed == len(schedule_ids):
                    print(f"✅ All {len(schedule_ids)} schedules completed!")
                    break
                
                print(f"   Progress: {completed}/{len(schedule_ids)} completed")
                await asyncio.sleep(30)
        
        # Step 6: Export comprehensive results
        print("\n📤 Step 6: Exporting comprehensive results...")
        
        # Generate summary
        summary_report = {
            'total_items': len(content_items),
            'schedules_created': len(created_schedules),
            'platforms': list(set(item.platform for item in content_items)),
            'recommendations_used': len(recommendations),
            'timestamp': datetime.now().isoformat()
        }
        
        # Export to multiple sheets
        try:
            # Summary sheet
            summary_sheet = integration.sheets_client.spreadsheet.worksheet("Import Summary")
        except gspread.WorksheetNotFound:
            summary_sheet = integration.sheets_client.create_sheet("Import Summary")
        
        summary_data = [
            ["Metric", "Value"],
            ["Total Content Items", summary_report['total_items']],
            ["Schedules Created", summary_report['schedules_created']],
            ["Platforms", ", ".join(summary_report['platforms'])],
            ["Recommendations Used", summary_report['recommendations_used']],
            ["Completion Time", summary_report['timestamp']]
        ]
        
        integration.sheets_client.write_data(summary_data, "Import Summary!A1")
        
        # Schedule details sheet
        if created_schedules:
            await integration.export_schedule_results(
                [s['schedule_id'] for s in created_schedules],
                "Schedule Details"
            )
        
        print("\n🎉 COMPLETE WORKFLOW FINISHED!")
        print(f"   📊 Summary: {summary_report['total_items']} items → {summary_report['schedules_created']} schedules")
        print(f"   🎯 Optimization: Used {summary_report['recommendations_used']} AI recommendations")
        print(f"   📁 Exported to: Import Summary, Schedule Details")
        
        return summary_report
    
    except Exception as e:
        logger.error(f"Complete workflow failed: {e}")
        raise

# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """
    Main function demonstrating all tutorials and examples
    """
    print("🚀 Google Sheets Scheduling Integration Examples")
    print("="*80)
    print("\nThis example demonstrates integration between Google Sheets and")
    print("the AI Content Automation System's scheduling API.")
    
    # Check if we should create sample data
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "--create-sample":
            create_sample_sheets_data()
            return
        elif sys.argv[1] == "--tutorial-basic":
            await tutorial_basic_integration()
            return
        elif sys.argv[1] == "--tutorial-batch":
            await tutorial_batch_processing()
            return
        elif sys.argv[1] == "--tutorial-monitoring":
            await tutorial_real_time_monitoring()
            return
        elif sys.argv[1] == "--tutorial-complete":
            await tutorial_complete_workflow()
            return
    
    print("\nAvailable commands:")
    print("  python google_sheets_scheduling.py --create-sample     # Create sample CSV data")
    print("  python google_sheets_scheduling.py --tutorial-basic    # Run basic integration tutorial")
    print("  python google_sheets_scheduling.py --tutorial-batch    # Run batch processing tutorial")
    print("  python google_sheets_scheduling.py --tutorial-monitoring # Run real-time monitoring tutorial")
    print("  python google_sheets_scheduling.py --tutorial-complete # Run complete workflow tutorial")
    
    print("\nOr run all tutorials:")
    tutorials = [
        ("Basic Integration", tutorial_basic_integration),
        ("Batch Processing", tutorial_batch_processing),
        ("Real-time Monitoring", tutorial_real_time_monitoring),
        ("Complete Workflow", tutorial_complete_workflow)
    ]
    
    print("\n" + "="*80)
    print("🎓 RUNNING ALL TUTORIALS")
    print("="*80)
    
    for tutorial_name, tutorial_func in tutorials:
        print(f"\n{'='*20} {tutorial_name} {'='*20}")
        try:
            await tutorial_func()
            print(f"✅ {tutorial_name} completed successfully!")
        except Exception as e:
            print(f"❌ {tutorial_name} failed: {e}")
        
        # Pause between tutorials
        await asyncio.sleep(2)
    
    print(f"\n🎊 ALL TUTORIALS COMPLETED!")
    print("\nNext steps:")
    print("1. Configure your Google Sheets credentials and spreadsheet ID")
    print("2. Set up your scheduling API endpoint and key")
    print("3. Run the tutorials with your actual data")
    print("4. Customize the integration for your specific use case")
    print("\nFor more examples, see:")
    print("• examples/scheduling_tutorial.py")
    print("• examples/react_scheduling_example.tsx")
    print("• docs/integration_examples.md")

if __name__ == "__main__":
    # Install required packages if not available
    try:
        import gspread
        import pandas as pd
        import aiohttp
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Please install required packages:")
        print("pip install gspread pandas aiohttp google-auth google-auth-oauthlib google-auth-httplib2")
        exit(1)
    
    # Run the main function
    asyncio.run(main())
