"""
Google Sheets API Error Handler

Comprehensive error handling system for Google Sheets API failures with:
- Specific error types for different failure modes
- Exponential backoff retry logic with jitter
- Circuit breaker pattern for system protection
- Logging and monitoring integration
- Fallback strategies for degraded operation
"""

import asyncio
import logging
import json
import random
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    Union,
    Awaitable,
    TypeVar
)
from dataclasses import dataclass, field
from collections import defaultdict
import functools

# Mock error classes for environments without google-api-python-client
class MockHttpError(Exception):
    """Mock HttpError for environments without google-api-python-client"""
    def __init__(self, message: str, status: int = 500):
        self.status = status
        self.message = message
        super().__init__(f"HTTP {status}: {message}")

# Use mock if googleapiclient is not available
try:
    from googleapiclient.errors import HttpError
    _HttpError = HttpError
except ImportError:
    HttpError = MockHttpError
    _HttpError = MockHttpError

try:
    import aiohttp
    _aiohttp_available = True
except ImportError:
    # Mock aiohttp for environments without it
    class aiohttp:
        class ClientError(Exception): pass
        class ServerTimeoutError(Exception): pass
        ClientConnectionError = ClientError
    _aiohttp_available = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Type variable for generic function
F = TypeVar('F', bound=Callable[..., Any])


class ErrorSeverity(Enum):
    """Error severity levels for classification and handling"""
    LOW = "low"           # Non-critical, can retry
    MEDIUM = "medium"     # Important but recoverable
    HIGH = "high"         # Critical, may need escalation
    CRITICAL = "critical" # System-threatening


class ErrorCategory(Enum):
    """Error categories for organized handling"""
    QUOTA_EXCEEDED = "quota_exceeded"
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    PERMISSION = "permission"
    NOT_FOUND = "not_found"
    MALFORMED_REQUEST = "malformed_request"
    SERVER_ERROR = "server_error"
    UNKNOWN = "unknown"


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryTemplate:
    """Retry strategy template with exponential backoff and jitter"""
    initial_delay: float = 1.0
    max_delay: float = 60.0
    max_retries: int = 5
    multiplier: float = 3.0
    jitter: bool = True
    total_timeout: float = 500.0
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt with jitter"""
        delay = min(self.initial_delay * (self.multiplier ** attempt), self.max_delay)
        
        if self.jitter:
            # Full jitter as recommended in the architecture
            jitter_range = delay * 0.1
            delay = delay + random.uniform(-jitter_range, jitter_range)
        
        return max(delay, 0.1)
    
    def should_retry(self, attempt: int, elapsed_time: float, error: Exception) -> bool:
        """Determine if we should retry based on limits"""
        if attempt >= self.max_retries:
            return False
        if elapsed_time > self.total_timeout:
            return False
        
        # Retry specific Google Sheets API error types
        retriable_errors = (
            QuotaExceededError, 
            NetworkError, 
            RateLimitError, 
            ServerError
        )
        
        return isinstance(error, retriable_errors)


class SheetsAPIError(Exception):
    """Base exception for Google Sheets API errors"""
    def __init__(
        self,
        message: str,
        error_category: ErrorCategory,
        severity: ErrorSeverity,
        http_status: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.error_category = error_category
        self.severity = severity
        self.http_status = http_status
        self.details = details or {}
        self.original_error = original_error
        self.timestamp = datetime.now()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/monitoring"""
        return {
            "error_type": self.__class__.__name__,
            "category": self.error_category.value,
            "severity": self.severity.value,
            "message": self.message,
            "http_status": self.http_status,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class QuotaExceededError(SheetsAPIError):
    """Raised when API quota is exceeded (HTTP 429)"""
    def __init__(self, message: str, quota_type: str = "unknown", **kwargs):
        super().__init__(
            message=message,
            error_category=ErrorCategory.QUOTA_EXCEEDED,
            severity=ErrorSeverity.MEDIUM,
            http_status=429,
            details={"quota_type": quota_type, **kwargs.get("details", {})},
            original_error=kwargs.get("original_error")
        )


class AuthenticationError(SheetsAPIError):
    """Raised when authentication fails (HTTP 401/403)"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            http_status=kwargs.get("http_status", 403),
            details=kwargs.get("details", {}),
            original_error=kwargs.get("original_error")
        )


class PermissionError(SheetsAPIError):
    """Raised when permission is denied (HTTP 403)"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_category=ErrorCategory.PERMISSION,
            severity=ErrorSeverity.HIGH,
            http_status=403,
            details=kwargs.get("details", {}),
            original_error=kwargs.get("original_error")
        )


class NetworkError(SheetsAPIError):
    """Raised when network issues occur"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            http_status=None,
            details=kwargs.get("details", {}),
            original_error=kwargs.get("original_error")
        )


class RateLimitError(SheetsAPIError):
    """Raised when rate limit is exceeded"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            http_status=429,
            details=kwargs.get("details", {}),
            original_error=kwargs.get("original_error")
        )


class NotFoundError(SheetsAPIError):
    """Raised when resource is not found (HTTP 404)"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.MEDIUM,
            http_status=404,
            details=kwargs.get("details", {}),
            original_error=kwargs.get("original_error")
        )


class MalformedRequestError(SheetsAPIError):
    """Raised when request is malformed (HTTP 400)"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_category=ErrorCategory.MALFORMED_REQUEST,
            severity=ErrorSeverity.HIGH,
            http_status=400,
            details=kwargs.get("details", {}),
            original_error=kwargs.get("original_error")
        )


class ServerError(SheetsAPIError):
    """Raised when server errors occur (HTTP 5xx)"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_category=ErrorCategory.SERVER_ERROR,
            severity=ErrorSeverity.MEDIUM,
            http_status=kwargs.get("http_status", 500),
            details=kwargs.get("details", {}),
            original_error=kwargs.get("original_error")
        )


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for Google Sheets API protection
    
    Implements the three states: CLOSED (normal), OPEN (blocking), HALF_OPEN (testing)
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitBreakerState.CLOSED
        self._lock = asyncio.Lock()
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type and issubclass(exc_type, self.expected_exception):
            await self.record_failure()
        else:
            await self.record_success()
    
    async def record_success(self):
        """Record a successful operation"""
        async with self._lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                logger.info(f"Circuit breaker '{self.name}' recovered")
                self._reset()
            elif self.state == CircuitBreakerState.CLOSED:
                self.failure_count = max(0, self.failure_count - 1)
    
    async def record_failure(self):
        """Record a failed operation"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitBreakerState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    logger.warning(f"Circuit breaker '{self.name}' opened due to failures")
                    self.state = CircuitBreakerState.OPEN
            elif self.state == CircuitBreakerState.HALF_OPEN:
                logger.warning(f"Circuit breaker '{self.name}' reopened")
                self.state = CircuitBreakerState.OPEN
    
    async def _reset(self):
        """Reset circuit breaker to initial state"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
    
    async def can_execute(self) -> bool:
        """Check if operation can be executed based on circuit state"""
        async with self._lock:
            if self.state == CircuitBreakerState.CLOSED:
                return True
            elif self.state == CircuitBreakerState.OPEN:
                if self.last_failure_time and time.time() - self.last_failure_time >= self.timeout:
                    logger.info(f"Circuit breaker '{self.name}' moved to half-open")
                    self.state = CircuitBreakerState.HALF_OPEN
                    return True
                return False
            else:  # HALF_OPEN
                return True


class SheetsErrorHandler:
    """
    Comprehensive error handler for Google Sheets API operations
    
    Provides:
    - Error classification and normalization
    - Retry logic with exponential backoff and jitter
    - Circuit breaker protection
    - Rate limiting and quota management
    - Logging and monitoring
    - Fallback strategies
    """
    
    # Template configurations as defined in architecture
    MODERATE_PACING = RetryTemplate(
        initial_delay=1.0,
        max_delay=60.0,
        max_retries=5,
        multiplier=3.0,
        jitter=True,
        total_timeout=500.0
    )
    
    AGGRESSIVE = RetryTemplate(
        initial_delay=1.0,
        max_delay=64.0,
        max_retries=10,
        multiplier=2.0,
        jitter=False,
        total_timeout=300.0
    )
    
    def __init__(
        self,
        name: str = "sheets_api",
        retry_template: RetryTemplate = None,
        enable_circuit_breaker: bool = True,
        enable_fallback: bool = True,
        monitoring_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.name = name
        self.retry_template = retry_template or self.MODERATE_PACING
        self.enable_circuit_breaker = enable_circuit_breaker
        self.enable_fallback = enable_fallback
        self.monitoring_callback = monitoring_callback
        
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._metrics = {
            "total_requests": 0,
            "total_errors": 0,
            "retries": 0,
            "circuit_breaker_trips": 0,
            "fallback_activations": 0,
            "quota_exceeded": 0,
            "auth_failures": 0
        }
        logger.info(f"SheetsErrorHandler '{self.name}' initialized")
    
    def _classify_error(self, error: Exception) -> SheetsAPIError:
        """Classify and normalize various error types to SheetsAPIError"""
        
        # If already a SheetsAPIError, return as-is
        if isinstance(error, SheetsAPIError):
            return error
        
        # Handle HttpError from google-api-python-client
        if isinstance(error, _HttpError):
            # Handle different HttpError implementations
            if hasattr(error, 'resp') and hasattr(error.resp, 'status'):
                status = error.resp.status
            elif hasattr(error, 'status'):
                status = error.status
            else:
                status = None
            
            reason = getattr(error, 'reason', 'Unknown')
            
            if status == 429:
                return QuotaExceededError(
                    f"Quota exceeded: {error}",
                    quota_type="per_minute",
                    original_error=error
                )
            elif status == 401:
                return AuthenticationError(
                    f"Authentication failed: {error}",
                    http_status=401,
                    original_error=error
                )
            elif status == 403:
                # Check if it's quota vs permission
                if "quota" in str(error).lower():
                    return QuotaExceededError(
                        f"Quota exceeded: {error}",
                        quota_type="permission_denied_quota",
                        original_error=error
                    )
                else:
                    return PermissionError(
                        f"Permission denied: {error}",
                        original_error=error
                    )
            elif status == 404:
                return NotFoundError(
                    f"Resource not found: {error}",
                    original_error=error
                )
            elif status == 400:
                return MalformedRequestError(
                    f"Malformed request: {error}",
                    original_error=error
                )
            elif status and 500 <= status < 600:
                return ServerError(
                    f"Server error: {error}",
                    http_status=status,
                    original_error=error
                )
        
        # Handle network errors
        network_error_types = (ConnectionError,)
        if _aiohttp_available:
            network_error_types = (aiohttp.ClientError, ConnectionError)
        
        if isinstance(error, network_error_types):
            return NetworkError(
                f"Network error: {error}",
                original_error=error
            )
        
        # Handle asyncio timeouts
        if isinstance(error, asyncio.TimeoutError):
            return NetworkError(
                f"Request timeout: {error}",
                original_error=error
            )
        
        # Handle aiohttp timeouts (only if aiohttp is available)
        if _aiohttp_available and isinstance(error, aiohttp.ServerTimeoutError):
            return NetworkError(
                f"Server timeout: {error}",
                original_error=error
            )
        
        # Return generic error for unknown types
        return SheetsAPIError(
            message=f"Unknown error: {error}",
            error_category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            original_error=error
        )
    
    async def _retry_with_backoff(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with exponential backoff retry logic"""
        start_time = time.time()
        attempt = 0
        
        while True:
            try:
                result = await func(*args, **kwargs)
                self._metrics["retries"] = attempt
                
                if attempt > 0:
                    logger.info(f"Function succeeded after {attempt} retries")
                
                return result
                
            except Exception as e:
                attempt += 1
                elapsed = time.time() - start_time
                
                # Classify the error
                sheets_error = self._classify_error(e)
                self._log_error(sheets_error, attempt)
                
                # Update metrics
                self._update_metrics(sheets_error, attempt)
                
                # Check if we should retry
                if not self.retry_template.should_retry(attempt, elapsed, sheets_error):
                    logger.error(
                        f"Function failed after {attempt} attempts, "
                        f"elapsed: {elapsed:.2f}s"
                    )
                    raise sheets_error
                
                # Calculate and apply backoff delay
                delay = self.retry_template.calculate_delay(attempt)
                
                logger.warning(
                    f"Function failed with {sheets_error.error_category.value} "
                    f"(attempt {attempt}/{self.retry_template.max_retries}). "
                    f"Retrying in {delay:.2f}s"
                )
                
                await asyncio.sleep(delay)
    
    def _get_circuit_breaker(self, operation: str) -> CircuitBreaker:
        """Get or create circuit breaker for operation"""
        if operation not in self.circuit_breakers:
            self.circuit_breakers[operation] = CircuitBreaker(
                name=f"{self.name}_{operation}",
                failure_threshold=5,
                timeout=60
            )
        return self.circuit_breakers[operation]
    
    def _log_error(self, error: SheetsAPIError, attempt: int = 0):
        """Log error with appropriate level and context"""
        log_data = {
            "handler": self.name,
            "category": error.error_category.value,
            "severity": error.severity.value,
            "attempt": attempt,
            **error.to_dict()
        }
        
        if error.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]:
            logger.warning(f"Sheets API Error: {log_data}")
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(f"Sheets API Error: {log_data}")
        else:  # CRITICAL
            logger.critical(f"Sheets API Critical Error: {log_data}")
    
    def _update_metrics(self, error: SheetsAPIError, attempt: int):
        """Update internal metrics"""
        self._metrics["total_errors"] += 1
        
        if error.error_category == ErrorCategory.QUOTA_EXCEEDED:
            self._metrics["quota_exceeded"] += 1
        elif error.error_category == ErrorCategory.AUTHENTICATION:
            self._metrics["auth_failures"] += 1
        elif error.error_category == ErrorCategory.PERMISSION:
            self._metrics["circuit_breaker_trips"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        return self._metrics.copy()
    
    def _monitor(self, data: Dict[str, Any]):
        """Send monitoring data if callback is configured"""
        if self.monitoring_callback:
            try:
                self.monitoring_callback(data)
            except Exception as e:
                logger.error(f"Monitoring callback failed: {e}")
    
    async def execute_with_circuit_breaker(
        self,
        operation: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with circuit breaker protection"""
        if not self.enable_circuit_breaker:
            return await func(*args, **kwargs)
        
        circuit_breaker = self._get_circuit_breaker(operation)
        
        if not await circuit_breaker.can_execute():
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{operation}' is open"
            )
        
        try:
            async with circuit_breaker:
                result = await func(*args, **kwargs)
                return result
        except Exception as e:
            if isinstance(e, circuit_breaker.expected_exception):
                # Log circuit breaker trip
                logger.warning(f"Circuit breaker '{operation}' tripped")
                self._metrics["circuit_breaker_trips"] += 1
            raise
    
    async def execute_operation(
        self,
        operation: str,
        func: Callable,
        *args,
        use_retry: bool = True,
        use_circuit_breaker: bool = True,
        use_fallback: bool = True,
        **kwargs
    ) -> Any:
        """
        Execute a Sheets API operation with comprehensive error handling
        
        Args:
            operation: Name of the operation (for circuit breaker tracking)
            func: Async function to execute
            *args, **kwargs: Arguments to pass to function
            use_retry: Whether to use retry logic
            use_circuit_breaker: Whether to use circuit breaker protection
            use_fallback: Whether to use fallback strategies
        
        Returns:
            Result from the function
            
        Raises:
            SheetsAPIError: Classified and normalized API errors
            CircuitBreakerOpenError: When circuit breaker is open
        """
        self._metrics["total_requests"] += 1
        
        try:
            # If using retry logic, use _retry_with_backoff
            if use_retry:
                # Create a wrapped function that handles circuit breaker
                async def wrapped_func():
                    if use_circuit_breaker and self.enable_circuit_breaker:
                        return await self.execute_with_circuit_breaker(operation, func, *args, **kwargs)
                    else:
                        return await func(*args, **kwargs)
                
                result = await self._retry_with_backoff(wrapped_func)
            else:
                # Direct execution without retry
                if use_circuit_breaker and self.enable_circuit_breaker:
                    result = await self.execute_with_circuit_breaker(operation, func, *args, **kwargs)
                else:
                    result = await func(*args, **kwargs)
            
            logger.info(f"Operation '{operation}' completed successfully")
            return result
            
        except Exception as e:
            if isinstance(e, SheetsAPIError):
                # Already classified error
                raise
            else:
                # Classify unknown error
                sheets_error = self._classify_error(e)
                raise sheets_error
    
    async def get_cached_result(
        self,
        cache_key: str,
        func: Callable,
        *args,
        max_age_seconds: int = 300,
        **kwargs
    ) -> Any:
        """
        Get result with caching for resilience
        
        Args:
            cache_key: Cache key for the operation
            func: Function to execute
            *args, **kwargs: Arguments for the function
            max_age_seconds: Maximum age of cached data in seconds
        
        Returns:
            Result from function or cache
        """
        # In a real implementation, this would use Redis or similar
        # For now, we'll return a simple fallback behavior
        try:
            result = await self.execute_operation(f"cached_{cache_key}", func, *args, **kwargs)
            return result
        except (QuotaExceededError, NetworkError) as e:
            # Try to return stale cached data if operation fails
            logger.warning(f"Using cached data for {cache_key} due to {e.error_category.value}")
            return await self._get_stale_cache(cache_key, max_age_seconds)
    
    async def _get_stale_cache(self, cache_key: str, max_age_seconds: int) -> Any:
        """
        Get stale cached data as fallback
        
        In a real implementation, this would retrieve from Redis
        For now, raise the original error to maintain strict behavior
        """
        raise CacheMissError(f"No cached data available for {cache_key}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the error handler"""
        circuit_breaker_states = {
            name: cb.state.value
            for name, cb in self.circuit_breakers.items()
        }
        
        return {
            "handler_name": self.name,
            "total_requests": self._metrics["total_requests"],
            "total_errors": self._metrics["total_errors"],
            "error_rate": (
                self._metrics["total_errors"] / max(1, self._metrics["total_requests"])
            ),
            "circuit_breaker_states": circuit_breaker_states,
            "metrics": self._metrics,
            "retry_template": {
                "initial_delay": self.retry_template.initial_delay,
                "max_retries": self.retry_template.max_retries,
                "multiplier": self.retry_template.multiplier
            }
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CacheMissError(Exception):
    """Raised when cached data is not available"""
    pass


class FallbackStrategy:
    """
    Fallback strategies for degraded operation
    """
    
    @staticmethod
    async def use_partial_data(partial_data: Any) -> Any:
        """Use partial/cached data as fallback"""
        logger.info("Using partial data fallback strategy")
        return partial_data
    
    @staticmethod
    async def skip_operation(operation: str) -> None:
        """Skip operation as fallback"""
        logger.info(f"Skipping operation '{operation}' as fallback")
        return None
    
    @staticmethod
    async def queue_for_later(operation: str, data: Any) -> str:
        """Queue operation for later processing"""
        queue_id = f"deferred_{operation}_{int(time.time())}"
        logger.info(f"Queuing operation '{operation}' for later processing: {queue_id}")
        return queue_id
    
    @staticmethod
    async def degrade_functionality(operation: str, data: Any) -> Any:
        """Provide degraded functionality"""
        logger.warning(f"Operating in degraded mode for '{operation}'")
        return {
            "status": "degraded",
            "message": "Operating with reduced functionality",
            "operation": operation,
            "data": data
        }


# Decorator for automatic error handling
def sheets_api_operation(
    operation: str,
    error_handler: Optional[SheetsErrorHandler] = None,
    use_retry: bool = True,
    use_circuit_breaker: bool = True
):
    """
    Decorator for automatically applying error handling to Sheets API operations
    
    Usage:
        @sheets_api_operation("read_spreadsheet", error_handler)
        async def read_spreadsheet(spreadsheet_id):
            # API call here
            pass
    """
    def decorator(func: F) -> F:
        handler = error_handler or SheetsErrorHandler()
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await handler.execute_operation(
                operation=operation,
                func=func,
                *args,
                use_retry=use_retry,
                use_circuit_breaker=use_circuit_breaker,
                **kwargs
            )
        
        return wrapper
    return decorator


# Example usage and testing
if __name__ == "__main__":
    async def example_usage():
        """Example of using the error handler"""
        
        # Create error handler
        handler = SheetsErrorHandler(
            name="production_sheets",
            retry_template=SheetsErrorHandler.MODERATE_PACING,
            enable_circuit_breaker=True,
            enable_fallback=True
        )
        
        # Example API call function
        async def example_sheets_call(spreadsheet_id: str) -> Dict[str, Any]:
            # This would be a real Google Sheets API call
            # For demo, we'll simulate various errors
            import random
            if random.random() < 0.7:  # 70% chance of failure
                raise HttpError(
                    resp=type('obj', (object,), {'status': 429})(),
                    content=b'Quota exceeded'
                )
            return {"spreadsheet_id": spreadsheet_id, "status": "success"}
        
        # Execute with error handling
        try:
            result = await handler.execute_operation(
                operation="read_spreadsheet",
                func=example_sheets_call,
                spreadsheet_id="example_id"
            )
            print(f"Success: {result}")
        except SheetsAPIError as e:
            print(f"Error handled: {e.to_dict()}")
        
        # Get health status
        health = handler.get_health_status()
        print(f"Health status: {json.dumps(health, indent=2)}")
    
    # Run example
    # asyncio.run(example_usage())
