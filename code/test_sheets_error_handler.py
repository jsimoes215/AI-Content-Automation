"""
Test suite for Sheets Error Handler

Demonstrates and validates the comprehensive error handling system
"""

import asyncio
import json
import logging
from unittest.mock import Mock, AsyncMock, patch
import pytest

from sheets_error_handler import (
    SheetsErrorHandler,
    SheetsAPIError,
    QuotaExceededError,
    AuthenticationError,
    NetworkError,
    RateLimitError,
    CircuitBreaker,
    ErrorSeverity,
    ErrorCategory,
    RetryTemplate,
    sheets_api_operation
)

# Configure test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestSheetsErrorHandler:
    """Test cases for SheetsErrorHandler"""
    
    def setup_method(self):
        """Setup for each test"""
        self.handler = SheetsErrorHandler(
            name="test_handler",
            retry_template=RetryTemplate(
                initial_delay=0.1,
                max_delay=1.0,
                max_retries=2,
                multiplier=2.0,
                total_timeout=5.0
            )
        )
    
    @pytest.mark.asyncio
    async def test_successful_operation(self):
        """Test successful operation completion"""
        async def successful_func():
            return {"status": "success", "data": "test"}
        
        result = await self.handler.execute_operation(
            "test_op",
            successful_func
        )
        
        assert result == {"status": "success", "data": "test"}
        assert self.handler._metrics["total_requests"] == 1
        assert self.handler._metrics["total_errors"] == 0
    
    @pytest.mark.asyncio
    async def test_quota_exceeded_retry(self):
        """Test retry on quota exceeded error"""
        call_count = 0
        
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                # Simulate quota exceeded
                error = Mock()
                error.resp.status = 429
                from googleapiclient.errors import HttpError
                raise HttpError(resp=error.resp, content=b'Quota exceeded')
            return {"status": "success"}
        
        result = await self.handler.execute_operation(
            "quota_test",
            failing_func
        )
        
        assert result == {"status": "success"}
        assert call_count == 3
        assert self.handler._metrics["quota_exceeded"] > 0
    
    @pytest.mark.asyncio
    async def test_authentication_error_no_retry(self):
        """Test that authentication errors are not retried"""
        async def auth_failing_func():
            error = Mock()
            error.resp.status = 401
            from googleapiclient.errors import HttpError
            raise HttpError(resp=error.resp, content=b'Unauthorized')
        
        with pytest.raises(AuthenticationError):
            await self.handler.execute_operation(
                "auth_test",
                auth_failing_func
            )
        
        # Should have failed on first attempt
        assert self.handler._metrics["retries"] == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        from googleapiclient.errors import HttpError
        
        call_count = 0
        
        async def consistently_failing_func():
            nonlocal call_count
            call_count += 1
            error = Mock()
            error.resp.status = 500
            raise HttpError(resp=error.resp, content=b'Server Error')
        
        # First few calls should trigger circuit breaker
        for i in range(6):  # 5 failures to open + 1 test call
            try:
                await self.handler.execute_operation(
                    "circuit_test",
                    consistently_failing_func,
                    use_circuit_breaker=True
                )
            except Exception:
                pass  # Expected to fail
        
        assert self.handler._metrics["circuit_breaker_trips"] > 0
        
        # Circuit breaker should be open now
        cb = self.handler._get_circuit_breaker("circuit_test")
        assert cb.state.value in ["open", "half_open"]
    
    @pytest.mark.asyncio
    async def test_monitoring_callback(self):
        """Test monitoring callback integration"""
        callback_calls = []
        
        def monitoring_callback(data):
            callback_calls.append(data)
        
        handler = SheetsErrorHandler(
            monitoring_callback=monitoring_callback
        )
        
        async def failing_func():
            from googleapiclient.errors import HttpError
            error = Mock()
            error.resp.status = 429
            raise HttpError(resp=error.resp, content=b'Quota exceeded')
        
        try:
            await handler.execute_operation("monitor_test", failing_func)
        except Exception:
            pass  # Expected to fail after retries
        
        # Should have called monitoring callback
        assert len(callback_calls) > 0
        assert any("quota_exceeded" in str(call) for call in callback_calls)
    
    def test_metrics_collection(self):
        """Test metrics collection"""
        # Simulate various errors
        errors = [
            QuotaExceededError("Test quota"),
            AuthenticationError("Test auth"),
            NetworkError("Test network")
        ]
        
        for error in errors:
            self.handler._log_error(error)
        
        assert self.handler._metrics["total_errors"] >= 3
        assert self.handler._metrics["quota_exceeded"] >= 1
        assert self.handler._metrics["auth_failures"] >= 1
    
    def test_retry_template_calculation(self):
        """Test retry delay calculations"""
        template = RetryTemplate(
            initial_delay=1.0,
            max_delay=60.0,
            multiplier=2.0,
            jitter=True
        )
        
        # Test delay calculation
        delay1 = template.calculate_delay(0)  # First attempt
        delay2 = template.calculate_delay(1)  # Second attempt
        delay3 = template.calculate_delay(2)  # Third attempt
        
        assert delay1 >= 0.1
        assert delay2 > delay1
        assert delay3 > delay2
        
        # Test with high attempt number
        delay_high = template.calculate_delay(10)
        assert delay_high <= template.max_delay


class TestDecorators:
    """Test error handling decorators"""
    
    @pytest.mark.asyncio
    async def test_sheets_api_operation_decorator(self):
        """Test the @sheets_api_operation decorator"""
        call_count = 0
        
        @sheets_api_operation("decorated_test")
        async def decorated_func(value: str):
            nonlocal call_count
            call_count += 1
            
            if call_count < 2:
                # Simulate retryable error
                error = Mock()
                error.resp.status = 429
                from googleapiclient.errors import HttpError
                raise HttpError(resp=error.resp, content=b'Quota exceeded')
            
            return {"result": value}
        
        result = await decorated_func("test_value")
        
        assert result == {"result": "test_value"}
        assert call_count == 2


class TestErrorClassification:
    """Test error classification and normalization"""
    
    def setup_method(self):
        self.handler = SheetsErrorHandler()
    
    def test_http_error_classification(self):
        """Test classification of HttpError types"""
        from googleapiclient.errors import HttpError
        
        # Test 429 - Quota exceeded
        error_429 = Mock()
        error_429.resp.status = 429
        classified_429 = self.handler._classify_error(
            HttpError(resp=error_429.resp, content=b'Quota exceeded')
        )
        assert isinstance(classified_429, QuotaExceededError)
        assert classified_429.http_status == 429
        
        # Test 401 - Authentication
        error_401 = Mock()
        error_401.resp.status = 401
        classified_401 = self.handler._classify_error(
            HttpError(resp=error_401.resp, content=b'Unauthorized')
        )
        assert isinstance(classified_401, AuthenticationError)
        
        # Test 403 - Permission denied
        error_403 = Mock()
        error_403.resp.status = 403
        classified_403 = self.handler._classify_error(
            HttpError(resp=error_403.resp, content=b'Forbidden')
        )
        assert isinstance(classified_403, AuthenticationError)
    
    def test_network_error_classification(self):
        """Test classification of network errors"""
        import aiohttp
        
        # Test aiohttp ClientError
        client_error = aiohttp.ClientError("Connection failed")
        classified = self.handler._classify_error(client_error)
        assert isinstance(classified, NetworkError)
        assert classified.error_category == ErrorCategory.NETWORK
    
    def test_unknown_error_classification(self):
        """Test classification of unknown errors"""
        unknown_error = ValueError("Unknown error type")
        classified = self.handler._classify_error(unknown_error)
        assert isinstance(classified, SheetsAPIError)
        assert classified.error_category == ErrorCategory.UNKNOWN


class TestFallbackStrategies:
    """Test fallback strategy functionality"""
    
    @pytest.mark.asyncio
    async def test_fallback_operations(self):
        """Test various fallback operations"""
        from sheets_error_handler import FallbackStrategy
        
        # Test partial data fallback
        partial_data = {"key": "cached_value", "stale": True}
        result = await FallbackStrategy.use_partial_data(partial_data)
        assert result == partial_data
        
        # Test skip operation
        result = await FallbackStrategy.skip_operation("test_op")
        assert result is None
        
        # Test queue for later
        queue_id = await FallbackStrategy.queue_for_later("test_op", {"data": "test"})
        assert "deferred" in queue_id
        
        # Test degraded functionality
        result = await FallbackStrategy.degrade_functionality("test_op", {"data": "test"})
        assert "degraded" in result["status"]


class TestCircuitBreaker:
    """Test circuit breaker functionality"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_states(self):
        """Test circuit breaker state transitions"""
        cb = CircuitBreaker("test_cb", failure_threshold=2, timeout=1)
        
        # Initially closed
        assert cb.state == CircuitBreakerState.CLOSED
        assert await cb.can_execute()
        
        # Record failures
        await cb.record_failure()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 1
        
        await cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        assert not await cb.can_execute()
        
        # Wait for timeout and test half-open
        await asyncio.sleep(1.1)
        assert await cb.can_execute()
        
        # Record success to reset
        await cb.record_success()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0


async def run_integration_test():
    """Run a comprehensive integration test"""
    print("\n=== Running Integration Test ===")
    
    # Create handler with aggressive retry settings
    handler = SheetsErrorHandler(
        name="integration_test",
        retry_template=SheetsErrorHandler.AGGRESSIVE
    )
    
    # Simulate a function that fails initially then succeeds
    call_count = 0
    async def test_function(spreadsheet_id: str):
        nonlocal call_count
        call_count += 1
        
        if call_count < 3:
            # Simulate network timeout
            raise asyncio.TimeoutError("Simulated network timeout")
        
        return {
            "spreadsheet_id": spreadsheet_id,
            "status": "success",
            "attempts": call_count
        }
    
    # Execute with comprehensive error handling
    try:
        result = await handler.execute_operation(
            "integration_test",
            test_function,
            spreadsheet_id="test_spreadsheet"
        )
        
        print(f"✓ Test passed: {result}")
        print(f"✓ Attempts: {call_count}")
        print(f"✓ Metrics: {handler.get_metrics()}")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False
    
    # Test health status
    health = handler.get_health_status()
    print(f"✓ Health status: {json.dumps(health, indent=2)}")
    
    print("✓ Integration test completed successfully")
    return True


async def run_performance_test():
    """Run performance test with concurrent operations"""
    print("\n=== Running Performance Test ===")
    
    handler = SheetsErrorHandler("performance_test")
    
    # Create multiple concurrent operations
    async def slow_operation(delay: float, should_fail: bool = False):
        if should_fail:
            await asyncio.sleep(delay)
            from googleapiclient.errors import HttpError
            error = Mock()
            error.resp.status = 429
            raise HttpError(resp=error.resp, content=b'Quota exceeded')
        
        await asyncio.sleep(delay)
        return {"delay": delay, "status": "success"}
    
    # Test concurrent operations
    tasks = [
        handler.execute_operation(f"op_{i}", slow_operation, 0.1, should_fail=(i % 2 == 0))
        for i in range(10)
    ]
    
    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = asyncio.get_event_loop().time()
    
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    failure_count = len(results) - success_count
    
    print(f"✓ Completed {len(tasks)} operations in {end_time - start_time:.2f}s")
    print(f"✓ Success: {success_count}, Failures: {failure_count}")
    print(f"✓ Final metrics: {handler.get_metrics()}")
    
    return success_count > 0  # At least some should succeed


async def main():
    """Run all tests"""
    print("Starting Sheets Error Handler Tests")
    print("=" * 50)
    
    # Run integration test
    integration_passed = await run_integration_test()
    
    # Run performance test
    performance_passed = await run_performance_test()
    
    # Run specific test cases
    print("\n=== Running Unit Tests ===")
    test_handler = TestSheetsErrorHandler()
    test_handler.setup_method()
    
    try:
        # Note: In a real test environment, you would run pytest
        # For this demo, we'll run a simplified test
        await test_handler.test_successful_operation()
        print("✓ Successful operation test passed")
        
        await test_handler.test_quota_exceeded_retry()
        print("✓ Quota exceeded retry test passed")
        
        print("✓ Unit tests completed")
        
    except Exception as e:
        print(f"✗ Unit test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    if integration_passed and performance_passed:
        print("✓ All tests passed successfully!")
        return True
    else:
        print("✗ Some tests failed")
        return False


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    exit(0 if success else 1)
