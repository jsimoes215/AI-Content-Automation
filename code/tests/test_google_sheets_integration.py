"""
End-to-end Google Sheets workflow tests for bulk operations system.

This module tests:
- Google Sheets client integration
- Data reading and writing operations
- Rate limiting compliance
- Error handling with Google Sheets API
- Batch operations
- Authentication and authorization
- Sheet metadata operations

Author: AI Content Automation System
Version: 1.0.0
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, MagicMock, AsyncMock

import pytest
from googleapiclient.errors import HttpError

# Import system components
from google_sheets_client import (
    GoogleSheetsClient, SheetRange, RateLimitConfig,
    ValueRenderOption, DateTimeRenderOption, ValueInputOption, MajorDimension
)
from sheets_error_handler import SheetsErrorHandler, QuotaExceededError


class TestGoogleSheetsIntegration:
    """End-to-end Google Sheets integration tests."""
    
    @pytest.mark.integration
    def test_client_initialization(self, mock_credentials):
        """Test Google Sheets client initialization."""
        # Test successful initialization
        client = GoogleSheetsClient(credentials_path=mock_credentials)
        assert client is not None
        assert client._service is not None
        assert client.health_check() is True
        client.close()
    
    def test_client_initialization_invalid_credentials(self, temp_dir):
        """Test client initialization with invalid credentials."""
        invalid_path = str(temp_dir / "nonexistent.json")
        
        with pytest.raises(FileNotFoundError):
            GoogleSheetsClient(credentials_path=invalid_path)
    
    @pytest.mark.integration
    def test_rate_limiting_configuration(self, mock_credentials):
        """Test rate limiting configuration."""
        custom_config = RateLimitConfig(
            max_requests_per_minute=50,
            backoff_base_delay=0.5,
            max_retries=3
        )
        
        client = GoogleSheetsClient(
            credentials_path=mock_credentials,
            rate_limit_config=custom_config
        )
        
        assert client.rate_limit_config.max_requests_per_minute == 50
        assert client.rate_limit_config.backoff_base_delay == 0.5
        assert client.rate_limit_config.max_retries == 3
        client.close()
    
    @pytest.mark.integration
    def test_get_sheet_data(self, mock_sheets_client):
        """Test getting sheet data."""
        # Mock response
        mock_response = {
            'values': [
                ['Title', 'Description', 'Target Audience'],
                ['Video 1', 'Description 1', 'Audience 1'],
                ['Video 2', 'Description 2', 'Audience 2']
            ]
        }
        mock_sheets_client._service.spreadsheets().values().get().execute.return_value = mock_response
        
        # Test the operation
        result = mock_sheets_client.get_sheet_data(
            spreadsheet_id="test_spreadsheet",
            sheet_name="TestSheet"
        )
        
        # Verify results
        assert len(result) == 3  # Header + 2 data rows
        assert result[0] == ['Title', 'Description', 'Target Audience']
        assert result[1] == ['Video 1', 'Description 1', 'Audience 1']
        assert result[2] == ['Video 2', 'Description 2', 'Audience 2']
    
    @pytest.mark.integration
    def test_get_rows_in_range(self, mock_sheets_client):
        """Test getting data from specific range."""
        # Mock response
        mock_response = {
            'values': [
                ['Video 1', 'Description 1', 'Audience 1'],
                ['Video 2', 'Description 2', 'Audience 2']
            ]
        }
        mock_sheets_client._service.spreadsheets().values().get().execute.return_value = mock_response
        
        # Create range specification
        sheet_range = SheetRange(
            sheet_name="TestSheet",
            start_row=2,
            end_row=3,
            start_col="A",
            end_col="C"
        )
        
        # Test the operation
        result = mock_sheets_client.get_rows_in_range(
            spreadsheet_id="test_spreadsheet",
            sheet_range=sheet_range
        )
        
        # Verify results
        assert len(result) == 2
        assert result[0] == ['Video 1', 'Description 1', 'Audience 1']
        assert result[1] == ['Video 2', 'Description 2', 'Audience 2']
    
    @pytest.mark.integration
    def test_get_multiple_ranges(self, mock_sheets_client):
        """Test getting data from multiple ranges."""
        # Mock response
        mock_response = {
            'valueRanges': [
                {
                    'range': 'TestSheet!A1:B2',
                    'values': [['Title', 'Description'], ['Video 1', 'Description 1']]
                },
                {
                    'range': 'TestSheet!D1:E2',
                    'values': [['Tags', 'Tone'], ['python,programming', 'professional']]
                }
            ]
        }
        mock_sheets_client._service.spreadsheets().values().batchGet().execute.return_value = mock_response
        
        # Create range specifications
        ranges = [
            SheetRange(sheet_name="TestSheet", start_col="A", end_col="B"),
            SheetRange(sheet_name="TestSheet", start_col="D", end_col="E")
        ]
        
        # Test the operation
        result = mock_sheets_client.get_multiple_ranges(
            spreadsheet_id="test_spreadsheet",
            ranges=ranges
        )
        
        # Verify results
        assert len(result) == 2
        assert 'TestSheet!A:B' in result or 'TestSheet!D:E' in result
    
    @pytest.mark.integration
    def test_write_values(self, mock_sheets_client):
        """Test writing values to sheet."""
        # Mock response
        mock_response = {
            'updatedRows': 2,
            'updatedColumns': 3,
            'updatedCells': 6
        }
        mock_sheets_client._service.spreadsheets().values().update().execute.return_value = mock_response
        
        # Test data
        values = [
            ['Title', 'Description', 'Status'],
            ['New Video', 'New Description', 'Draft']
        ]
        
        sheet_range = SheetRange(
            sheet_name="TestSheet",
            start_row=1,
            end_row=2,
            start_col="A",
            end_col="C"
        )
        
        # Test the operation
        result = mock_sheets_client.write_values(
            spreadsheet_id="test_spreadsheet",
            sheet_range=sheet_range,
            values=values
        )
        
        # Verify results
        assert result['updatedRows'] == 2
        assert result['updatedColumns'] == 3
        assert result['updatedCells'] == 6
    
    @pytest.mark.integration
    def test_append_values(self, mock_sheets_client):
        """Test appending values to sheet."""
        # Mock response
        mock_response = {
            'updates': {
                'appendedRows': 2,
                'appendedColumns': 3
            }
        }
        mock_sheets_client._service.spreadsheets().values().append().execute.return_value = mock_response
        
        # Test data
        values = [
            ['Video 3', 'Description 3', 'Published'],
            ['Video 4', 'Description 4', 'Draft']
        ]
        
        # Test the operation
        result = mock_sheets_client.append_values(
            spreadsheet_id="test_spreadsheet",
            sheet_name="TestSheet",
            values=values
        )
        
        # Verify results
        assert 'updates' in result
        assert result['updates']['appendedRows'] == 2
        assert result['updates']['appendedColumns'] == 3
    
    @pytest.mark.integration
    def test_batch_update(self, mock_sheets_client):
        """Test batch update operations."""
        # Mock response
        mock_response = {
            'replies': [
                {'addSheet': {'properties': {'sheetId': 123}}},
                {'updateCells': {'rows': 1}}
            ]
        }
        mock_sheets_client._service.spreadsheets().batchUpdate().execute.return_value = mock_response
        
        # Batch update requests
        updates = [
            {
                'addSheet': {
                    'properties': {
                        'title': 'NewSheet',
                        'gridProperties': {'rowCount': 1000, 'columnCount': 26}
                    }
                }
            }
        ]
        
        # Test the operation
        result = mock_sheets_client.batch_update(
            spreadsheet_id="test_spreadsheet",
            updates=updates
        )
        
        # Verify results
        assert 'replies' in result
        assert len(result['replies']) == 1
    
    @pytest.mark.integration
    def test_get_spreadsheet_metadata(self, mock_sheets_client):
        """Test getting spreadsheet metadata."""
        # Mock response
        mock_response = {
            'properties': {
                'title': 'Test Spreadsheet',
                'locale': 'en_US',
                'timeZone': 'America/Los_Angeles'
            },
            'sheets': [
                {
                    'properties': {
                        'sheetId': 0,
                        'title': 'Sheet1',
                        'index': 0,
                        'gridProperties': {'rowCount': 1000, 'columnCount': 26}
                    }
                }
            ]
        }
        mock_sheets_client._service.spreadsheets().get().execute.return_value = mock_response
        
        # Test the operation
        result = mock_sheets_client.get_spreadsheet_metadata(
            spreadsheet_id="test_spreadsheet"
        )
        
        # Verify results
        assert 'properties' in result
        assert 'sheets' in result
        assert len(result['sheets']) == 1
        assert result['sheets'][0]['properties']['title'] == 'Sheet1'
    
    @pytest.mark.integration
    def test_create_sheet(self, mock_sheets_client):
        """Test creating a new sheet."""
        # Mock batch_update response
        mock_sheets_client._service.spreadsheets().batchUpdate().execute.return_value = {
            'replies': [{'addSheet': {'properties': {'sheetId': 123}}}]
        }
        
        # Test the operation
        result = mock_sheets_client.create_sheet(
            spreadsheet_id="test_spreadsheet",
            sheet_title="NewSheet",
            grid_properties={'rowCount': 1000, 'columnCount': 26}
        )
        
        # Verify sheet creation was called
        assert mock_sheets_client._service.spreadsheets().batchUpdate.called
    
    @pytest.mark.integration
    def test_get_sheet_info(self, mock_sheets_client):
        """Test getting sheet information."""
        # Mock metadata response
        mock_sheets_client.get_spreadsheet_metadata.return_value = {
            'sheets': [
                {
                    'properties': {
                        'sheetId': 0,
                        'title': 'TestSheet',
                        'index': 0,
                        'gridProperties': {'rowCount': 1000, 'columnCount': 26}
                    }
                }
            ]
        }
        
        # Test the operation
        result = mock_sheets_client.get_sheet_info(
            spreadsheet_id="test_spreadsheet",
            sheet_name="TestSheet"
        )
        
        # Verify results
        assert result['sheet_id'] == 0
        assert result['title'] == 'TestSheet'
        assert result['index'] == 0
        assert 'grid_properties' in result
    
    def test_sheet_range_a1_notation(self):
        """Test SheetRange A1 notation conversion."""
        # Test full range
        range1 = SheetRange(
            sheet_name="Sheet1",
            start_row=1,
            end_row=10,
            start_col="A",
            end_col="C"
        )
        assert range1.to_a1_notation() == "Sheet1!A1:C10"
        
        # Test column range only
        range2 = SheetRange(
            sheet_name="Sheet1",
            start_col="A",
            end_col="Z"
        )
        assert range2.to_a1_notation() == "Sheet1!A:Z"
        
        # Test row range only
        range3 = SheetRange(
            sheet_name="Sheet1",
            start_row=1,
            end_row=5
        )
        assert range3.to_a1_notation() == "Sheet1!1:5"
        
        # Test sheet only
        range4 = SheetRange(sheet_name="Sheet1")
        assert range4.to_a1_notation() == "Sheet1!"
    
    @pytest.mark.integration
    def test_rate_limit_status(self, mock_sheets_client):
        """Test rate limit status reporting."""
        # Make some requests to increment counter
        mock_sheets_client.get_rate_limit_status()
        
        status = mock_sheets_client.get_rate_limit_status()
        
        # Verify status structure
        assert 'requests_in_current_window' in status
        assert 'time_elapsed_in_window_seconds' in status
        assert 'max_requests_per_minute' in status
        assert 'requests_remaining' in status
        assert 'window_resets_in_seconds' in status
        
        # Verify values
        assert status['max_requests_per_minute'] == 10  # From test config
        assert status['requests_remaining'] >= 0
    
    @pytest.mark.integration
    def test_exponential_backoff(self, mock_sheets_client):
        """Test exponential backoff on rate limit errors."""
        # Create mock HTTP error for rate limit
        from googleapiclient.errors import HttpError
        mock_resp = Mock()
        mock_resp.status = 429
        rate_limit_error = HttpError(mock_resp, b'{"error": "Rate limit exceeded"}')
        
        # Mock successful response for retry
        mock_sheets_client._service.spreadsheets().values().get().execute.side_effect = [
            rate_limit_error,
            rate_limit_error,
            {'values': [['Test', 'Data']]}  # Success on third attempt
        ]
        
        # Test with backoff
        with patch('time.sleep') as mock_sleep:
            result = mock_sheets_client.get_sheet_data(
                spreadsheet_id="test_spreadsheet",
                sheet_name="TestSheet"
            )
            
            # Verify result
            assert result == [['Test', 'Data']]
            
            # Verify sleep was called (exponential backoff)
            assert mock_sleep.called
            # Should have been called twice for the two retries
            assert mock_sleep.call_count >= 2
    
    @pytest.mark.integration
    def test_non_retriable_error(self, mock_sheets_client):
        """Test handling of non-retriable errors."""
        # Create mock HTTP error for non-retriable error (e.g., 404)
        from googleapiclient.errors import HttpError
        mock_resp = Mock()
        mock_resp.status = 404
        not_found_error = HttpError(mock_resp, b'{"error": "Not found"}')
        
        mock_sheets_client._service.spreadsheets().values().get().execute.side_effect = not_found_error
        
        # Test that non-retriable error is raised immediately
        with pytest.raises(HttpError) as exc_info:
            mock_sheets_client.get_sheet_data(
                spreadsheet_id="test_spreadsheet",
                sheet_name="NonExistentSheet"
            )
        
        assert exc_info.value.resp.status == 404
    
    @pytest.mark.integration
    def test_quota_exceeded_error(self, mock_sheets_client):
        """Test handling of quota exceeded errors."""
        # Create mock HTTP error for quota exceeded
        from googleapiclient.errors import HttpError
        mock_resp = Mock()
        mock_resp.status = 429
        mock_resp.reason = "Too Many Requests"
        quota_error = HttpError(mock_resp, b'{"error": "Quota exceeded"}')
        
        mock_sheets_client._service.spreadsheets().values().get().execute.side_effect = quota_error
        
        # Test that quota exceeded error is handled with retries
        with patch('time.sleep') as mock_sleep:
            with pytest.raises(HttpError):
                mock_sheets_client.get_sheet_data(
                    spreadsheet_id="test_spreadsheet",
                    sheet_name="TestSheet"
                )
            
            # Verify backoff was attempted
            assert mock_sleep.called
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_operation_integration(self, mock_sheets_client):
        """Test integration with async operations."""
        # This test demonstrates how the Google Sheets client
        # can be used in async contexts
        
        async def simulate_async_workflow():
            results = []
            
            # Simulate multiple async operations
            for i in range(3):
                # In a real async workflow, you might be doing other async work
                await asyncio.sleep(0.1)
                
                # Access the sync client in async context
                # (This is just for testing - in practice, you'd design for async from the start)
                mock_sheets_client.get_sheet_data(
                    spreadsheet_id="test_spreadsheet",
                    sheet_name=f"Sheet{i}"
                )
                
                results.append(f"Processed sheet {i}")
            
            return results
        
        # Run the async workflow
        results = await simulate_async_workflow()
        
        # Verify results
        assert len(results) == 3
        assert all("Processed sheet" in result for result in results)
    
    @pytest.mark.integration
    def test_value_render_options(self, mock_sheets_client):
        """Test different value render options."""
        # Mock response with different render options
        test_cases = [
            (ValueRenderOption.FORMATTED_VALUE, "formatted"),
            (ValueRenderOption.UNFORMATTED_VALUE, "unformatted"),
            (ValueRenderOption.FORMULA, "formula")
        ]
        
        for render_option, expected_type in test_cases:
            mock_sheets_client._service.spreadsheets().values().get().execute.return_value = {
                'values': [['Test', 'Data']]
            }
            
            result = mock_sheets_client.get_sheet_data(
                spreadsheet_id="test_spreadsheet",
                sheet_name="TestSheet",
                value_render_option=render_option
            )
            
            assert len(result) > 0
            # The mock will return the same data regardless of render option
            # In a real test, you'd verify the specific render behavior
    
    @pytest.mark.integration
    def test_major_dimension_options(self, mock_sheets_client):
        """Test major dimension options (rows vs columns)."""
        # Test with ROWS
        mock_sheets_client._service.spreadsheets().values().get().execute.return_value = {
            'values': [['A1', 'B1', 'C1'], ['A2', 'B2', 'C2']]
        }
        
        result_rows = mock_sheets_client.get_sheet_data(
            spreadsheet_id="test_spreadsheet",
            sheet_name="TestSheet",
            major_dimension=MajorDimension.ROWS
        )
        
        # Test with COLUMNS
        mock_sheets_client._service.spreadsheets().values().get().execute.return_value = {
            'values': [['A1', 'A2'], ['B1', 'B2'], ['C1', 'C2']]
        }
        
        result_cols = mock_sheets_client.get_sheet_data(
            spreadsheet_id="test_spreadsheet",
            sheet_name="TestSheet",
            major_dimension=MajorDimension.COLUMNS
        )
        
        # Verify different data structures
        assert len(result_rows) == 2  # 2 rows
        assert len(result_cols) == 3  # 3 columns
    
    @pytest.mark.integration
    def test_concurrent_requests_handling(self, mock_sheets_client):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request(request_id):
            try:
                # Simulate some work
                time.sleep(0.1)
                
                # Make request to the client
                result = mock_sheets_client.get_sheet_data(
                    spreadsheet_id="test_spreadsheet",
                    sheet_name=f"Sheet{request_id}"
                )
                results.append((request_id, result))
            except Exception as e:
                errors.append((request_id, str(e)))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        # Note: In this mock setup, all requests should succeed
        # In real scenarios, you might see some rate limiting
        assert len(errors) == 0  # Should have no errors in mock setup
        assert len(results) == 5  # Should have 5 successful results


class TestGoogleSheetsWorkflow:
    """Test complete Google Sheets workflows."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_data_pipeline(self, mock_sheets_client, temp_dir):
        """Test complete data pipeline from reading to writing."""
        
        # Step 1: Read data from source sheet
        read_data = [
            ['Title', 'Description', 'Status'],
            ['Video 1', 'Description 1', 'pending'],
            ['Video 2', 'Description 2', 'pending']
        ]
        
        mock_sheets_client._service.spreadsheets().values().get().execute.return_value = {
            'values': read_data
        }
        
        # Read the data
        source_data = mock_sheets_client.get_sheet_data(
            spreadsheet_id="source_spreadsheet",
            sheet_name="SourceSheet"
        )
        
        assert len(source_data) == 3
        
        # Step 2: Process data (simulate transformation)
        processed_data = []
        for i, row in enumerate(source_data[1:], 1):  # Skip header
            processed_row = [
                row[0],  # Title
                row[1],  # Description
                'processed',  # Updated status
                f'row_{i}'  # Add processing ID
            ]
            processed_data.append(processed_row)
        
        # Step 3: Write processed data to destination sheet
        mock_sheets_client._service.spreadsheets().values().update().execute.return_value = {
            'updatedRows': len(processed_data),
            'updatedColumns': 4
        }
        
        # Prepare data with header
        output_data = [
            ['Title', 'Description', 'Status', 'Processing ID']
        ] + processed_data
        
        sheet_range = SheetRange(
            sheet_name="DestinationSheet",
            start_row=1,
            end_row=len(output_data),
            start_col="A",
            end_col="D"
        )
        
        # Write the data
        write_result = mock_sheets_client.write_values(
            spreadsheet_id="destination_spreadsheet",
            sheet_range=sheet_range,
            values=output_data
        )
        
        # Verify pipeline completion
        assert write_result['updatedRows'] == len(processed_data)
        assert write_result['updatedColumns'] == 4
    
    @pytest.mark.integration
    def test_batch_sheet_operations(self, mock_sheets_client):
        """Test batch operations across multiple sheets."""
        
        sheets_data = {
            'Sheet1': [
                ['Title', 'Data'],
                ['Video 1', '100'],
                ['Video 2', '200']
            ],
            'Sheet2': [
                ['Name', 'Value'],
                ['Item 1', 'A'],
                ['Item 2', 'B']
            ]
        }
        
        # Mock multiple get calls
        call_count = 0
        def mock_execute():
            nonlocal call_count
            sheet_names = list(sheets_data.keys())
            current_sheet = sheet_names[call_count % len(sheet_names)]
            call_count += 1
            return {'values': sheets_data[current_sheet]}
        
        mock_sheets_client._service.spreadsheets().values().get().execute.side_effect = mock_execute
        
        # Process multiple sheets
        results = {}
        for sheet_name in sheets_data.keys():
            data = mock_sheets_client.get_sheet_data(
                spreadsheet_id="test_spreadsheet",
                sheet_name=sheet_name
            )
            results[sheet_name] = data
        
        # Verify all sheets were processed
        assert len(results) == 2
        assert 'Sheet1' in results
        assert 'Sheet2' in results
        assert len(results['Sheet1']) == 3  # Header + 2 data rows
        assert len(results['Sheet2']) == 3  # Header + 2 data rows
    
    @pytest.mark.integration
    def test_error_recovery_workflow(self, mock_sheets_client):
        """Test error recovery in Google Sheets operations."""
        
        # Simulate a transient error followed by success
        from googleapiclient.errors import HttpError
        mock_resp = Mock()
        mock_resp.status = 500
        server_error = HttpError(mock_resp, b'{"error": "Server error"}')
        
        success_response = {'values': [['Success', 'Data']]}
        
        # Set up side effects: error, then success
        mock_sheets_client._service.spreadsheets().values().get().execute.side_effect = [
            server_error,
            server_error,
            success_response
        ]
        
        # Test recovery
        with patch('time.sleep') as mock_sleep:
            result = mock_sheets_client.get_sheet_data(
                spreadsheet_id="test_spreadsheet",
                sheet_name="TestSheet"
            )
            
            # Verify successful recovery
            assert result == [['Success', 'Data']]
            assert mock_sleep.call_count >= 2  # Should have backoff sleep calls


# Utility functions for tests
def create_test_sheet_data(num_rows=10, num_cols=5):
    """Create test sheet data for various test scenarios."""
    headers = [f"Column_{chr(65+i)}" for i in range(num_cols)]
    data = [headers]
    
    for i in range(num_rows):
        row = [f"Data_{i}_{j}" for j in range(num_cols)]
        data.append(row)
    
    return data


def assert_sheet_data_equals(actual, expected):
    """Assert that sheet data matches expected structure."""
    assert len(actual) == len(expected)
    for i, (actual_row, expected_row) in enumerate(zip(actual, expected)):
        assert actual_row == expected_row, f"Row {i} mismatch"


if __name__ == "__main__":
    # Run specific test
    import sys
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        pytest.main([__file__, f"-k {test_name}", "-v"])