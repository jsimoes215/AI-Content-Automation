"""
Quick Example of Sheets Error Handler Usage

Demonstrates basic usage patterns for the error handling system
"""

import asyncio
import json
from sheets_error_handler import SheetsErrorHandler, QuotaExceededError, RetryTemplate

async def example_usage():
    """Example of using the error handler"""
    
    print("=== Google Sheets Error Handler Example ===\n")
    
    # Create error handler with moderate retry settings
    handler = SheetsErrorHandler(
        name="production_sheets",
        retry_template=RetryTemplate(
            initial_delay=0.1,
            max_delay=1.0,
            max_retries=3,
            multiplier=2.0
        )
    )
    
    # Simulated Sheets API function
    async def sheets_read_operation(spreadsheet_id: str):
        print(f"Reading spreadsheet: {spreadsheet_id}")
        
        # Simulate different failure scenarios
        import random
        failure_type = random.choice(['success', 'quota', 'network', 'auth'])
        
        if failure_type == 'quota':
            raise QuotaExceededError("Simulated quota exceeded", quota_type="per_minute")
        elif failure_type == 'network':
            raise NetworkError("Simulated network error")
        elif failure_type == 'auth':
            raise AuthenticationError("Simulated auth error")
        
        return {
            "spreadsheet_id": spreadsheet_id,
            "data": ["row1", "row2", "row3"],
            "status": "success"
        }
    
    # Test with different operations
    test_cases = [
        ("spreadsheet_1", "should_succeed"),
        ("spreadsheet_2", "quota_exceeded"),  
        ("spreadsheet_3", "network_error"),
        ("spreadsheet_4", "auth_error")
    ]
    
    results = []
    for spreadsheet_id, expected in test_cases:
        try:
            result = await handler.execute_operation(
                operation="read_spreadsheet",
                func=sheets_read_operation,
                spreadsheet_id=spreadsheet_id
            )
            results.append(("SUCCESS", spreadsheet_id, result))
        except Exception as e:
            results.append(("FAILED", spreadsheet_id, str(e)))
    
    # Display results
    print("\n=== Results ===")
    for status, sheet_id, result in results:
        print(f"{status}: {sheet_id} - {result}")
    
    # Show final health status
    health = handler.get_health_status()
    print(f"\n=== Health Status ===")
    print(json.dumps(health, indent=2))
    
    # Show available error types
    print(f"\n=== Available Error Types ===")
    from sheets_error_handler import (
        QuotaExceededError, AuthenticationError, NetworkError,
        RateLimitError, PermissionError, NotFoundError,
        MalformedRequestError, ServerError
    )
    
    error_types = [
        "QuotaExceededError - HTTP 429 quota exceeded",
        "AuthenticationError - HTTP 401 authentication failed",
        "NetworkError - Network connectivity issues",
        "RateLimitError - Rate limit exceeded",
        "PermissionError - HTTP 403 permission denied", 
        "NotFoundError - HTTP 404 resource not found",
        "MalformedRequestError - HTTP 400 bad request",
        "ServerError - HTTP 5xx server errors"
    ]
    
    for error_type in error_types:
        print(f"  • {error_type}")
    
    print(f"\n=== Retry Templates ===")
    print(f"MODERATE_PACING: {handler.MODERATE_PACING.__dict__}")
    print(f"AGGRESSIVE: {handler.AGGRESSIVE.__dict__}")

if __name__ == "__main__":
    asyncio.run(example_usage())
