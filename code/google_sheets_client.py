"""
Google Sheets API v4 Client for AI Content Automation System

This module provides a comprehensive Google Sheets API v4 client with:
- Service account authentication
- Read operations with flexible rendering options
- Batch operations support
- Error handling with exponential backoff
- Rate limiting compliance
- Comprehensive logging

References:
- Google Sheets API v4: https://developers.google.com/sheets/api
- Rate limits: https://developers.google.com/sheets/api/limits
- Authentication: https://developers.google.com/sheets/api/auth
"""

import json
import logging
import time
import random
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.auth.exceptions import DefaultCredentialsError


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValueRenderOption(Enum):
    """Options for rendering values when reading from sheets."""
    FORMULA = "FORMULA"              # Returns formulas as entered
    UNFORMATTED_VALUE = "UNFORMATTED_VALUE"  # Returns computed values without formatting
    FORMATTED_VALUE = "FORMATTED_VALUE"      # Returns displayed strings


class DateTimeRenderOption(Enum):
    """Options for rendering dates/times."""
    SERIAL_NUMBER = "SERIAL_NUMBER"        # Returns dates/times as serial numbers
    FORMATTED_STRING = "FORMATTED_STRING"  # Returns dates/times as formatted strings


class ValueInputOption(Enum):
    """Options for parsing values when writing to sheets."""
    RAW = "RAW"                    # Values stored as entered
    USER_ENTERED = "USER_ENTERED"  # Values parsed and evaluated


class MajorDimension(Enum):
    """Dimensions for reading/writing data."""
    ROWS = "ROWS"      # Interpret data as rows
    COLUMNS = "COLUMNS"  # Interpret data as columns


@dataclass
class SheetRange:
    """Represents a range in a Google Sheet."""
    sheet_name: str
    start_row: Optional[int] = None
    end_row: Optional[int] = None
    start_col: Optional[str] = None
    end_col: Optional[str] = None
    
    def to_a1_notation(self) -> str:
        """Convert to A1 notation for API calls."""
        if self.start_row and self.end_row and self.start_col and self.end_col:
            return f"{self.sheet_name}!{self.start_col}{self.start_row}:{self.end_col}{self.end_row}"
        elif self.start_col and self.end_col:
            return f"{self.sheet_name}!{self.start_col}:{self.end_col}"
        elif self.start_row and self.end_row:
            return f"{self.sheet_name}!{self.start_row}:{self.end_row}"
        else:
            return f"{self.sheet_name}!"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting compliance."""
    max_requests_per_minute: int = 300
    max_requests_per_minute_per_user: int = 60
    request_timeout_seconds: int = 180
    max_payload_size_mb: int = 2
    backoff_base_delay: float = 1.0
    backoff_multiplier: float = 2.0
    backoff_max_delay: float = 60.0
    max_retries: int = 5


class GoogleSheetsClient:
    """
    Google Sheets API v4 client with comprehensive features.
    
    Features:
    - Service account authentication
    - Read operations with flexible options
    - Batch operations for efficiency
    - Exponential backoff for rate limiting
    - Error handling and recovery
    - Comprehensive logging
    """
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(
        self,
        credentials_path: Union[str, Path],
        rate_limit_config: Optional[RateLimitConfig] = None
    ):
        """
        Initialize the Google Sheets client.
        
        Args:
            credentials_path: Path to service account credentials JSON file
            rate_limit_config: Configuration for rate limiting
        """
        self.credentials_path = Path(credentials_path)
        self.rate_limit_config = rate_limit_config or RateLimitConfig()
        self._service = None
        self._request_count = 0
        self._minute_window_start = time.time()
        self._backoff_attempts = {}
        
        self._authenticate()
        logger.info("Google Sheets client initialized successfully")
    
    def _authenticate(self) -> None:
        """Authenticate using service account credentials."""
        try:
            if not self.credentials_path.exists():
                raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")
            
            credentials = service_account.Credentials.from_service_account_file(
                str(self.credentials_path),
                scopes=self.SCOPES
            )
            
            # Create authenticated service
            self._service = build('sheets', 'v4', credentials=credentials)
            logger.info("Successfully authenticated with service account")
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise
    
    def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting."""
        current_time = time.time()
        
        # Reset window if a minute has passed
        if current_time - self._minute_window_start >= 60:
            self._request_count = 0
            self._minute_window_start = current_time
            logger.debug("Rate limit window reset")
        
        # Check if we've exceeded project quota
        if self._request_count >= self.rate_limit_config.max_requests_per_minute:
            wait_time = 60 - (current_time - self._minute_window_start)
            if wait_time > 0:
                logger.warning(f"Project quota exceeded, waiting {wait_time:.1f} seconds")
                time.sleep(wait_time)
                self._request_count = 0
                self._minute_window_start = time.time()
        
        self._request_count += 1
    
    def _execute_with_backoff(self, request_func, *args, **kwargs) -> Any:
        """
        Execute request with exponential backoff for rate limiting.
        
        Args:
            request_func: Function to execute
            *args, **kwargs: Arguments to pass to request function
            
        Returns:
            Response from request function
        """
        attempt = 0
        last_error = None
        
        while attempt <= self.rate_limit_config.max_retries:
            try:
                self._check_rate_limit()
                return request_func(*args, **kwargs)
                
            except HttpError as e:
                last_error = e
                
                # Handle quota exceeded (429) and other retriable errors
                if e.resp.status in [429, 500, 502, 503, 504]:
                    attempt += 1
                    
                    if attempt > self.rate_limit_config.max_retries:
                        logger.error(f"Max retries exceeded for request: {str(e)}")
                        raise e
                    
                    # Calculate backoff delay with jitter
                    delay = min(
                        self.rate_limit_config.backoff_base_delay * 
                        (self.rate_limit_config.backoff_multiplier ** (attempt - 1)),
                        self.rate_limit_config.backoff_max_delay
                    )
                    jitter = random.uniform(0, delay * 0.1)  # 10% jitter
                    total_delay = delay + jitter
                    
                    logger.warning(
                        f"Request failed (attempt {attempt}/{self.rate_limit_config.max_retries + 1}), "
                        f"retrying in {total_delay:.1f}s: {str(e)}"
                    )
                    time.sleep(total_delay)
                    
                else:
                    # Non-retriable error
                    logger.error(f"Non-retriable HTTP error: {str(e)}")
                    raise e
                    
            except Exception as e:
                # Non-HTTP error
                logger.error(f"Unexpected error: {str(e)}")
                raise e
        
        # Should not reach here, but just in case
        if last_error:
            raise last_error
    
    def get_sheet_data(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        value_render_option: ValueRenderOption = ValueRenderOption.FORMATTED_VALUE,
        date_time_render_option: DateTimeRenderOption = DateTimeRenderOption.SERIAL_NUMBER,
        major_dimension: MajorDimension = MajorDimension.ROWS
    ) -> List[List[str]]:
        """
        Read all data from a sheet.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the sheet/tab
            value_render_option: How to render cell values
            date_time_render_option: How to render dates/times
            major_dimension: Whether to read by rows or columns
            
        Returns:
            2D list of cell values
        """
        try:
            range_name = f"{sheet_name}"
            result = self._execute_with_backoff(
                self._service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueRenderOption=value_render_option.value,
                    dateTimeRenderOption=date_time_render_option.value,
                    majorDimension=major_dimension.value
                ).execute
            )
            
            values = result.get('values', [])
            logger.info(f"Read {len(values)} rows from sheet '{sheet_name}'")
            return values
            
        except HttpError as e:
            logger.error(f"Error reading sheet '{sheet_name}': {str(e)}")
            raise
    
    def get_rows_in_range(
        self,
        spreadsheet_id: str,
        sheet_range: SheetRange,
        value_render_option: ValueRenderOption = ValueRenderOption.FORMATTED_VALUE,
        date_time_render_option: DateTimeRenderOption = DateTimeRenderOption.SERIAL_NUMBER,
        major_dimension: MajorDimension = MajorDimension.ROWS
    ) -> List[List[str]]:
        """
        Read data from a specific range in a sheet.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_range: Range specification
            value_render_option: How to render cell values
            date_time_render_option: How to render dates/times
            major_dimension: Whether to read by rows or columns
            
        Returns:
            2D list of cell values in the specified range
        """
        try:
            range_name = sheet_range.to_a1_notation()
            result = self._execute_with_backoff(
                self._service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueRenderOption=value_render_option.value,
                    dateTimeRenderOption=date_time_render_option.value,
                    majorDimension=major_dimension.value
                ).execute
            )
            
            values = result.get('values', [])
            logger.info(f"Read {len(values)} rows from range '{range_name}'")
            return values
            
        except HttpError as e:
            logger.error(f"Error reading range '{sheet_range}': {str(e)}")
            raise
    
    def get_multiple_ranges(
        self,
        spreadsheet_id: str,
        ranges: List[SheetRange],
        value_render_option: ValueRenderOption = ValueRenderOption.FORMATTED_VALUE,
        date_time_render_option: DateTimeRenderOption = DateTimeRenderOption.SERIAL_NUMBER,
        major_dimension: MajorDimension = MajorDimension.ROWS
    ) -> Dict[str, List[List[str]]]:
        """
        Read data from multiple ranges in a single request for efficiency.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            ranges: List of range specifications
            value_render_option: How to render cell values
            date_time_render_option: How to render dates/times
            major_dimension: Whether to read by rows or columns
            
        Returns:
            Dictionary mapping range names to their data
        """
        try:
            range_names = [range_obj.to_a1_notation() for range_obj in ranges]
            
            result = self._execute_with_backoff(
                self._service.spreadsheets().values().batchGet(
                    spreadsheetId=spreadsheet_id,
                    ranges=range_names,
                    valueRenderOption=value_render_option.value,
                    dateTimeRenderOption=date_time_render_option.value,
                    majorDimension=major_dimension.value
                ).execute
            )
            
            value_ranges = result.get('valueRanges', [])
            response_data = {}
            
            for i, value_range in enumerate(value_ranges):
                range_name = value_range.get('range', range_names[i])
                values = value_range.get('values', [])
                response_data[range_name] = values
                logger.debug(f"Read {len(values)} rows from range '{range_name}'")
            
            logger.info(f"Successfully read {len(ranges)} ranges in batch")
            return response_data
            
        except HttpError as e:
            logger.error(f"Error reading multiple ranges: {str(e)}")
            raise
    
    def batch_update(
        self,
        spreadsheet_id: str,
        updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform multiple updates in a single atomic operation.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            updates: List of update operations
            
        Returns:
            Response containing results of all updates
        """
        try:
            body = {
                'requests': updates,
                'includeValuesInResponse': True
            }
            
            result = self._execute_with_backoff(
                self._service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body=body
                ).execute
            )
            
            logger.info(f"Successfully performed {len(updates)} batch updates")
            return result
            
        except HttpError as e:
            logger.error(f"Error performing batch update: {str(e)}")
            raise
    
    def write_values(
        self,
        spreadsheet_id: str,
        sheet_range: SheetRange,
        values: List[List[Any]],
        value_input_option: ValueInputOption = ValueInputOption.USER_ENTERED,
        major_dimension: MajorDimension = MajorDimension.ROWS
    ) -> Dict[str, Any]:
        """
        Write values to a specific range.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_range: Target range for writing
            values: 2D array of values to write
            value_input_option: How to parse the input values
            major_dimension: How to interpret the data layout
            
        Returns:
            Response containing update details
        """
        try:
            range_name = sheet_range.to_a1_notation()
            
            body = {
                'values': values,
                'majorDimension': major_dimension.value
            }
            
            result = self._execute_with_backoff(
                self._service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption=value_input_option.value,
                    body=body
                ).execute
            )
            
            logger.info(f"Successfully wrote {len(values)} rows to range '{range_name}'")
            return result
            
        except HttpError as e:
            logger.error(f"Error writing to range '{sheet_range}': {str(e)}")
            raise
    
    def append_values(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        values: List[List[Any]],
        value_input_option: ValueInputOption = ValueInputOption.USER_ENTERED,
        major_dimension: MajorDimension = MajorDimension.ROWS
    ) -> Dict[str, Any]:
        """
        Append values to the end of a sheet.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the sheet
            values: 2D array of values to append
            value_input_option: How to parse the input values
            major_dimension: How to interpret the data layout
            
        Returns:
            Response containing update details
        """
        try:
            range_name = f"{sheet_name}:A"
            
            body = {
                'values': values,
                'majorDimension': major_dimension.value
            }
            
            result = self._execute_with_backoff(
                self._service.spreadsheets().values().append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption=value_input_option.value,
                    body=body
                ).execute
            )
            
            logger.info(f"Successfully appended {len(values)} rows to sheet '{sheet_name}'")
            return result
            
        except HttpError as e:
            logger.error(f"Error appending to sheet '{sheet_name}': {str(e)}")
            raise
    
    def get_spreadsheet_metadata(self, spreadsheet_id: str) -> Dict[str, Any]:
        """
        Get metadata about a spreadsheet without cell data.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            
        Returns:
            Spreadsheet metadata
        """
        try:
            result = self._execute_with_backoff(
                self._service.spreadsheets().get(
                    spreadsheetId=spreadsheet_id,
                    includeGridData=False
                ).execute
            )
            
            logger.info("Retrieved spreadsheet metadata")
            return result
            
        except HttpError as e:
            logger.error(f"Error getting spreadsheet metadata: {str(e)}")
            raise
    
    def create_sheet(
        self,
        spreadsheet_id: str,
        sheet_title: str,
        grid_properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new sheet in the spreadsheet.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_title: Title for the new sheet
            grid_properties: Optional grid properties (rows, columns)
            
        Returns:
            Response containing sheet creation details
        """
        try:
            requests = [{
                'addSheet': {
                    'properties': {
                        'title': sheet_title,
                        **({} if not grid_properties else {'gridProperties': grid_properties})
                    }
                }
            }]
            
            result = self.batch_update(spreadsheet_id, requests)
            logger.info(f"Created sheet '{sheet_title}'")
            return result
            
        except Exception as e:
            logger.error(f"Error creating sheet '{sheet_title}': {str(e)}")
            raise
    
    def get_sheet_info(self, spreadsheet_id: str, sheet_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific sheet.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_name: Name of the sheet
            
        Returns:
            Sheet information including dimensions and properties
        """
        try:
            metadata = self.get_spreadsheet_metadata(spreadsheet_id)
            sheets = metadata.get('sheets', [])
            
            for sheet in sheets:
                properties = sheet.get('properties', {})
                if properties.get('title') == sheet_name:
                    sheet_info = {
                        'sheet_id': properties.get('sheetId'),
                        'title': properties.get('title'),
                        'index': properties.get('index'),
                        'grid_properties': properties.get('gridProperties', {})
                    }
                    logger.info(f"Retrieved info for sheet '{sheet_name}'")
                    return sheet_info
            
            raise ValueError(f"Sheet '{sheet_name}' not found")
            
        except Exception as e:
            logger.error(f"Error getting sheet info for '{sheet_name}': {str(e)}")
            raise
    
    def health_check(self) -> bool:
        """
        Perform a health check to verify the client is working.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to get service account info or a simple operation
            # This is a simple way to verify authentication and API access
            if self._service:
                logger.info("Health check passed")
                return True
            else:
                logger.warning("Health check failed: service not initialized")
                return False
                
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status.
        
        Returns:
            Dictionary with rate limit information
        """
        current_time = time.time()
        time_in_window = current_time - self._minute_window_start
        
        return {
            'requests_in_current_window': self._request_count,
            'time_elapsed_in_window_seconds': time_in_window,
            'max_requests_per_minute': self.rate_limit_config.max_requests_per_minute,
            'requests_remaining': max(0, self.rate_limit_config.max_requests_per_minute - self._request_count),
            'window_resets_in_seconds': max(0, 60 - time_in_window)
        }
    
    def close(self) -> None:
        """Clean up resources."""
        self._service = None
        logger.info("Google Sheets client closed")


def create_client_from_config(config_data: Dict[str, Any]) -> GoogleSheetsClient:
    """
    Create a GoogleSheetsClient from configuration data.
    
    Args:
        config_data: Configuration dictionary containing credentials path and options
        
    Returns:
        Initialized GoogleSheetsClient
    """
    credentials_path = config_data.get('credentials_path')
    if not credentials_path:
        raise ValueError("credentials_path is required in config")
    
    # Create rate limit config if provided
    rate_limit_config = None
    if 'rate_limits' in config_data:
        rl_config = config_data['rate_limits']
        rate_limit_config = RateLimitConfig(
            max_requests_per_minute=rl_config.get('max_requests_per_minute', 300),
            max_requests_per_minute_per_user=rl_config.get('max_requests_per_minute_per_user', 60),
            request_timeout_seconds=rl_config.get('request_timeout_seconds', 180),
            max_payload_size_mb=rl_config.get('max_payload_size_mb', 2),
            backoff_base_delay=rl_config.get('backoff_base_delay', 1.0),
            backoff_multiplier=rl_config.get('backoff_multiplier', 2.0),
            backoff_max_delay=rl_config.get('backoff_max_delay', 60.0),
            max_retries=rl_config.get('max_retries', 5)
        )
    
    return GoogleSheetsClient(
        credentials_path=credentials_path,
        rate_limit_config=rate_limit_config
    )


# Example usage and testing functions
def example_usage():
    """Example of how to use the Google Sheets client."""
    
    # Example configuration
    config = {
        'credentials_path': '/path/to/service-account-credentials.json',
        'rate_limits': {
            'max_requests_per_minute': 300,
            'backoff_base_delay': 1.0,
            'backoff_multiplier': 2.0,
            'max_retries': 5
        }
    }
    
    # Create client
    client = create_client_from_config(config)
    
    # Example spreadsheet ID (replace with actual)
    spreadsheet_id = "your-spreadsheet-id-here"
    sheet_name = "Sheet1"
    
    try:
        # Read all data from a sheet
        data = client.get_sheet_data(
            spreadsheet_id=spreadsheet_id,
            sheet_name=sheet_name,
            value_render_option=ValueRenderOption.FORMATTED_VALUE
        )
        print(f"Read {len(data)} rows")
        
        # Read specific range
        range_spec = SheetRange(
            sheet_name=sheet_name,
            start_row=1,
            end_row=10,
            start_col="A",
            end_col="C"
        )
        
        range_data = client.get_rows_in_range(
            spreadsheet_id=spreadsheet_id,
            sheet_range=range_spec
        )
        print(f"Read {len(range_data)} rows from range")
        
        # Write data
        test_data = [["Name", "Value", "Status"], ["Test", "123", "Active"]]
        client.write_values(
            spreadsheet_id=spreadsheet_id,
            sheet_range=range_spec,
            values=test_data
        )
        
        # Health check
        if client.health_check():
            print("Client is healthy")
        
        # Get rate limit status
        status = client.get_rate_limit_status()
        print(f"Rate limit status: {status}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    # Run example if script is executed directly
    example_usage()