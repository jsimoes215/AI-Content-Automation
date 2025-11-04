"""
Simplified test suite for Sheets Error Handler

Demonstrates and validates the comprehensive error handling system
"""

import asyncio
import json
import logging
from unittest.mock import Mock, AsyncMock, patch

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


async def test_successful_operation():
    """Test successful operation completion"""
    print("Testing successful operation...")
    
    handler = SheetsErrorHandler(name="test_handler")
    
    async def successful_func():
        # Ensure we return a coroutine by awaiting
        await asyncio.sleep(0)  # Make it properly async
        return {"status": "success", "data": "test"}
    
    result = await handler.execute_operation(
        "test_op",
        successful_func
    )
    
    assert result == {"status": "success", "data": "test"}
    assert handler._metrics["total_requests"] == 1
    assert handler._metrics["total_errors"] == 0
    print("✓ Successful operation test passed")


async def test_quota_exceeded_retry():
    """Test retry on quota exceeded error"""
    print("Testing quota exceeded retry...")
    
    handler = SheetsErrorHandler(
        name="test_handler",
        retry_template=RetryTemplate(
            initial_delay=0.1,
            max_delay=1.0,
            max_retries=2,
            multiplier=2.0,
            total_timeout=5.0
        )
    )
    
    call_count = 0
    
    async def failing_func():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0)  # Make it properly async
        if call_count < 3:
            # Simulate quota exceeded using our mock
            raise QuotaExceededError("Simulated quota exceeded", quota_type="test")
        return {"status": "success"}
    
    result = await handler.execute_operation(
        "quota_test",
        failing_func
    )
    
    assert result == {"status": "success"}
    assert call_count == 3
    assert handler._metrics["quota_exceeded"] > 0
    print("✓ Quota exceeded retry test passed")


async def test_authentication_error_no_retry():
    """Test that authentication errors are not retried"""
    print("Testing authentication error handling...")
    
    handler = SheetsErrorHandler(
        retry_template=RetryTemplate(
            initial_delay=0.1,
            max_retries=2
        )
    )
    
    async def auth_failing_func():
        await asyncio.sleep(0)  # Make it properly async
        # Simulate authentication error using our mock
        raise AuthenticationError("Simulated authentication failure")
    
    try:
        await handler.execute_operation(
            "auth_test",
            auth_failing_func
        )
        assert False, "Should have raised AuthenticationError"
    except AuthenticationError:
        pass  # Expected
    
    # Should have failed on first attempt
    assert handler._metrics["retries"] == 0
    print("✓ Authentication error test passed")


async def test_circuit_breaker():
    """Test circuit breaker functionality"""
    print("Testing circuit breaker...")
    
    handler = SheetsErrorHandler()
    
    call_count = 0
    
    async def consistently_failing_func():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0)  # Make it properly async
        # Simulate server error using our mock
        raise ServerError("Simulated server error")
    
    # First few calls should trigger circuit breaker
    for i in range(6):  # 5 failures to open + 1 test call
        try:
            await handler.execute_operation(
                "circuit_test",
                consistently_failing_func,
                use_circuit_breaker=True
            )
        except Exception:
            pass  # Expected to fail
    
    assert handler._metrics["circuit_breaker_trips"] > 0
    
    # Circuit breaker should be open now
    cb = handler._get_circuit_breaker("circuit_test")
    print(f"Circuit breaker state: {cb.state.value}")
    assert cb.state.value in ["open", "half_open"]
    print("✓ Circuit breaker test passed")


async def test_monitoring_callback():
    """Test monitoring callback integration"""
    print("Testing monitoring callback...")
    
    callback_calls = []
    
    def monitoring_callback(data):
        callback_calls.append(data)
    
    handler = SheetsErrorHandler(
        monitoring_callback=monitoring_callback
    )
    
    async def failing_func():
        await asyncio.sleep(0)  # Make it properly async
        # Simulate quota exceeded using our mock
        raise QuotaExceededError("Simulated quota exceeded")
    
    try:
        await handler.execute_operation("monitor_test", failing_func)
    except Exception:
        pass  # Expected to fail after retries
    
    # Should have called monitoring callback
    assert len(callback_calls) > 0
    print(f"Monitoring callback called {len(callback_calls)} times")
    print("✓ Monitoring callback test passed")


async def test_error_classification():
    """Test error classification and normalization"""
    print("Testing error classification...")
    
    handler = SheetsErrorHandler()
    
    # Test 429 - Quota exceeded using our actual error class
    quota_error = QuotaExceededError("Test quota", quota_type="test")
    classified_429 = handler._classify_error(quota_error)
    assert isinstance(classified_429, QuotaExceededError)
    assert classified_429.http_status == 429
    
    # Test 401 - Authentication using our actual error class
    auth_error = AuthenticationError("Test auth")
    classified_401 = handler._classify_error(auth_error)
    assert isinstance(classified_401, AuthenticationError)
    
    # Test 403 - Permission denied using our actual error class
    perm_error = PermissionError("Test permission")
    classified_403 = handler._classify_error(perm_error)
    assert isinstance(classified_403, PermissionError)
    
    # Test network error
    net_error = NetworkError("Test network")
    classified_net = handler._classify_error(net_error)
    assert isinstance(classified_net, NetworkError)
    
    print("✓ Error classification test passed")


async def test_retry_template():
    """Test retry delay calculations"""
    print("Testing retry template...")
    
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
    
    print("✓ Retry template test passed")


async def test_health_status():
    """Test health status reporting"""
    print("Testing health status...")
    
    handler = SheetsErrorHandler()
    
    # Simulate some operations
    async def some_func():
        await asyncio.sleep(0)  # Make it properly async
        return {"status": "ok"}
    
    await handler.execute_operation("health_test", some_func)
    
    health = handler.get_health_status()
    
    assert "handler_name" in health
    assert "total_requests" in health
    assert "error_rate" in health
    assert health["handler_name"] == "health_test"
    
    print("✓ Health status test passed")
    print(f"Health data: {json.dumps(health, indent=2)}")


async def test_fallback_strategies():
    """Test fallback strategy functionality"""
    print("Testing fallback strategies...")
    
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
    
    print("✓ Fallback strategies test passed")


async def test_circuit_breaker_states():
    """Test circuit breaker state transitions"""
    print("Testing circuit breaker states...")
    
    cb = CircuitBreaker("test_cb", failure_threshold=2, timeout=1)
    
    # Initially closed
    assert cb.state.value == "closed"
    assert await cb.can_execute()
    
    # Record failures
    await cb.record_failure()
    assert cb.state.value == "closed"
    assert cb.failure_count == 1
    
    await cb.record_failure()
    assert cb.state.value == "open"
    assert not await cb.can_execute()
    
    # Wait for timeout and test half-open
    await asyncio.sleep(1.1)
    assert await cb.can_execute()
    
    # Record success to reset
    await cb.record_success()
    assert cb.state.value == "closed"
    assert cb.failure_count == 0
    
    print("✓ Circuit breaker states test passed")


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
        await asyncio.sleep(0)  # Make it properly async
        
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
        print(f"✓ Metrics: {json.dumps(handler.get_metrics(), indent=2)}")
        
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
        await asyncio.sleep(delay)  # Make it properly async
        
        if should_fail:
            # Simulate quota exceeded using our mock
            raise QuotaExceededError("Simulated quota exceeded")
        
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
    print(f"✓ Final metrics: {json.dumps(handler.get_metrics(), indent=2)}")
    
    return success_count > 0  # At least some should succeed


async def main():
    """Run all tests"""
    print("Starting Sheets Error Handler Tests")
    print("=" * 50)
    
    # Run individual test functions
    test_functions = [
        test_successful_operation,
        test_quota_exceeded_retry,
        test_authentication_error_no_retry,
        test_circuit_breaker,
        test_monitoring_callback,
        test_error_classification,
        test_retry_template,
        test_health_status,
        test_fallback_strategies,
        test_circuit_breaker_states
    ]
    
    for test_func in test_functions:
        try:
            await test_func()
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            return False
    
    # Run integration test
    integration_passed = await run_integration_test()
    
    # Run performance test
    performance_passed = await run_performance_test()
    
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
