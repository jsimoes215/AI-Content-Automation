"""
Comprehensive Retry Handler for Job Processing Systems

Implements robust retry logic with:
- Exponential backoff retry mechanism with jitter
- Failure classification and handling
- Dead letter queue (DLQ) for unprocessable jobs
- Circuit breaker patterns for failing services
- Integration with error handling system
- Job state management and persistence
- Rate limiting and quota management
- Metrics and monitoring

Reference implementation based on:
- docs/architecture_design/queue_system.md (retry mechanisms)
- code/sheets_error_handler.py (error handling patterns)
"""

import asyncio
import json
import logging
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
    TypeVar,
    Generic,
    Tuple
)
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import uuid
import hashlib
import copy
import functools

# Import error handling components
from sheets_error_handler import (
    SheetsAPIError,
    SheetsErrorHandler,
    ErrorSeverity,
    ErrorCategory,
    CircuitBreaker,
    CircuitBreakerState,
    RetryTemplate
)

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic function
F = TypeVar('F', bound=Callable[..., Any])


class JobState(Enum):
    """Job states in the retry system"""
    QUEUED = "queued"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RETRYING = "retrying"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


class RetryStrategy(Enum):
    """Retry strategy types"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"
    CUSTOM = "custom"


class FailureType(Enum):
    """Types of failures for classification"""
    TRANSIENT = "transient"          # Temporary, retriable
    PERMANENT = "permanent"          # Cannot be retried
    RATE_LIMITED = "rate_limited"    # Quota exceeded
    NETWORK = "network"              # Network issues
    AUTHENTICATION = "authentication" # Auth failures
    VALIDATION = "validation"        # Invalid data/requests
    SYSTEM = "system"                # System-level failures


@dataclass
class JobRetryConfig:
    """Configuration for job retry behavior"""
    max_retries: int = 5
    initial_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 3.0
    jitter: bool = True
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    total_timeout: float = 300.0
    backoff_factor: float = 1.5
    min_delay: float = 0.1
    enable_dlq: bool = True
    dlq_retention_days: int = 7
    
    def calculate_delay(self, attempt: int, error: Optional[Exception] = None) -> float:
        """Calculate retry delay based on strategy"""
        if self.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = min(
                self.initial_delay * (self.multiplier ** attempt),
                self.max_delay
            )
        elif self.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = min(
                self.initial_delay * (1 + self.backoff_factor * attempt),
                self.max_delay
            )
        elif self.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.initial_delay
        elif self.strategy == RetryStrategy.IMMEDIATE:
            delay = 0
        else:  # CUSTOM
            delay = self.initial_delay
        
        # Apply jitter if enabled
        if self.jitter and delay > 0:
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(delay, self.min_delay)


@dataclass
class JobContext:
    """Context information for job processing"""
    job_id: str
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    job_type: str = "generic"
    priority: int = 1
    max_execution_time: float = 300.0
    idempotency_key: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.job_id:
            self.job_id = str(uuid.uuid4())
        if not self.idempotency_key:
            self.idempotency_key = hashlib.md5(
                f"{self.job_type}:{self.created_at.isoformat()}".encode()
            ).hexdigest()


@dataclass
class JobAttempt:
    """Information about a single job attempt"""
    attempt_number: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    error: Optional[Exception] = None
    error_classification: Optional[FailureType] = None
    delay_before_retry: Optional[float] = None
    circuit_breaker_state: Optional[str] = None
    execution_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "attempt_number": self.attempt_number,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "error": str(self.error) if self.error else None,
            "error_classification": self.error_classification.value if self.error_classification else None,
            "delay_before_retry": self.delay_before_retry,
            "circuit_breaker_state": self.circuit_breaker_state,
            "execution_time": self.execution_time
        }


@dataclass
class JobExecutionResult:
    """Result of job execution"""
    job_id: str
    success: bool
    state: JobState
    result: Optional[Any] = None
    error: Optional[Exception] = None
    attempts: List[JobAttempt] = field(default_factory=list)
    total_execution_time: float = 0.0
    final_delay: Optional[float] = None
    dlq_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "success": self.success,
            "state": self.state.value,
            "result": self.result,
            "error": str(self.error) if self.error else None,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "total_execution_time": self.total_execution_time,
            "final_delay": self.final_delay,
            "dlq_reason": self.dlq_reason
        }


class FailureClassifier:
    """
    Classifies failures into types to determine retry behavior
    """
    
    # Mapping of error types to failure classifications
    FAILURE_MAPPINGS = {
        # Transient/retriable errors
        ErrorCategory.QUOTA_EXCEEDED: FailureType.RATE_LIMITED,
        ErrorCategory.RATE_LIMIT: FailureType.RATE_LIMITED,
        ErrorCategory.NETWORK: FailureType.NETWORK,
        ErrorCategory.SERVER_ERROR: FailureType.TRANSIENT,
        
        # Permanent/non-retriable errors
        ErrorCategory.AUTHENTICATION: FailureType.AUTHENTICATION,
        ErrorCategory.PERMISSION: FailureType.PERMANENT,
        ErrorCategory.NOT_FOUND: FailureType.PERMANENT,
        ErrorCategory.MALFORMED_REQUEST: FailureType.VALIDATION,
        
        # System errors (might be retriable)
        ErrorCategory.UNKNOWN: FailureType.SYSTEM
    }
    
    @staticmethod
    def classify_error(error: Exception, context: JobContext) -> FailureType:
        """
        Classify error into failure type
        
        Args:
            error: The exception to classify
            context: Job context for additional classification
        
        Returns:
            FailureType indicating how to handle the error
        """
        # If it's already a SheetsAPIError, use its category
        if isinstance(error, SheetsAPIError):
            category = error.error_category
            return FailureClassifier.FAILURE_MAPPINGS.get(
                category, 
                FailureType.SYSTEM
            )
        
        # Handle common exception types
        error_name = error.__class__.__name__
        
        # Network-related errors
        if error_name in ('ConnectionError', 'TimeoutError', 'NetworkError'):
            return FailureType.NETWORK
        
        # HTTP errors
        if hasattr(error, 'status'):
            status = error.status
            if status == 429:
                return FailureType.RATE_LIMITED
            elif status in (401, 403):
                return FailureType.AUTHENTICATION
            elif status == 404:
                return FailureType.PERMANENT
            elif status == 400:
                return FailureType.VALIDATION
            elif 500 <= status < 600:
                return FailureType.TRANSIENT
        
        # Timeouts
        if error_name in ('TimeoutError', 'asyncio.TimeoutError'):
            return FailureType.NETWORK
        
        # Default to system error
        return FailureType.SYSTEM
    
    @staticmethod
    def is_retriable(failure_type: FailureType) -> bool:
        """Determine if failure type is retriable"""
        return failure_type in (
            FailureType.TRANSIENT,
            FailureType.RATE_LIMITED,
            FailureType.NETWORK,
            FailureType.SYSTEM
        )
    
    @staticmethod
    def should_consider_dlq(failure_type: FailureType, attempt: int, max_retries: int) -> bool:
        """Determine if failure should be sent to DLQ"""
        # Always DLQ permanent errors
        if failure_type == FailureType.PERMANENT:
            return True
        
        # DLQ validation errors immediately
        if failure_type == FailureType.VALIDATION:
            return True
        
        # DLQ authentication errors
        if failure_type == FailureType.AUTHENTICATION:
            return True
        
        # After max retries for retriable errors
        if attempt >= max_retries and FailureClassifier.is_retriable(failure_type):
            return True
        
        return False


class DeadLetterQueue:
    """
    Dead Letter Queue for unprocessable jobs
    """
    
    def __init__(self, max_retention_days: int = 7):
        self.max_retention_days = max_retention_days
        self._queue: deque = deque()
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        
        logger.info(f"Dead Letter Queue initialized with {max_retention_days} day retention")
    
    async def add_job(
        self,
        job: 'RetryableJob',
        error: Exception,
        failure_type: FailureType,
        reason: str
    ) -> str:
        """
        Add job to dead letter queue
        
        Args:
            job: The failed job
            error: The error that caused failure
            failure_type: Type of failure
            reason: Reason for DLQ
        
        Returns:
            DLQ entry ID
        """
        async with self._lock:
            dlq_id = str(uuid.uuid4())
            
            dlq_entry = {
                "dlq_id": dlq_id,
                "job_id": job.context.job_id,
                "job_context": asdict(job.context),
                "job_payload": job.payload,
                "error": str(error),
                "error_details": error.to_dict() if hasattr(error, 'to_dict') else {"type": error.__class__.__name__, "message": str(error)},
                "failure_type": failure_type.value,
                "reason": reason,
                "failed_at": datetime.now().isoformat(),
                "retry_count": job.attempt_count,
                "total_execution_time": job.total_execution_time,
                "execution_history": [attempt.to_dict() for attempt in job.attempts],
                "dql_created_at": datetime.now().isoformat()
            }
            
            self._storage[dlq_id] = dlq_entry
            self._queue.append(dlq_id)
            
            # Clean up old entries
            await self._cleanup_expired()
            
            logger.warning(
                f"Job {job.context.job_id} added to DLQ (ID: {dlq_id}): {reason}"
            )
            
            return dlq_id
    
    async def get_job(self, dlq_id: str) -> Optional[Dict[str, Any]]:
        """Get job from DLQ by ID"""
        return self._storage.get(dlq_id)
    
    async def list_jobs(
        self,
        limit: int = 100,
        failure_type: Optional[FailureType] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """List jobs in DLQ with optional filtering"""
        jobs = list(self._storage.values())
        
        # Filter by failure type
        if failure_type:
            jobs = [j for j in jobs if j["failure_type"] == failure_type.value]
        
        # Filter by date
        if since:
            jobs = [j for j in jobs if datetime.fromisoformat(j["failed_at"]) >= since]
        
        # Sort by failed_at descending
        jobs.sort(key=lambda x: x["failed_at"], reverse=True)
        
        return jobs[:limit]
    
    async def retry_job(self, dlq_id: str) -> Optional[Dict[str, Any]]:
        """Move job from DLQ back to main queue (for manual retry)"""
        job_data = self._storage.get(dlq_id)
        if not job_data:
            return None
        
        # Remove from DLQ
        async with self._lock:
            self._storage.pop(dlq_id, None)
            if dlq_id in self._queue:
                self._queue.remove(dlq_id)
        
        logger.info(f"Job {dlq_id} moved from DLQ back to main queue")
        return job_data
    
    async def remove_job(self, dlq_id: str) -> bool:
        """Remove job from DLQ permanently"""
        async with self._lock:
            if dlq_id in self._storage:
                self._storage.pop(dlq_id)
                if dlq_id in self._queue:
                    self._queue.remove(dlq_id)
                return True
            return False
    
    async def _cleanup_expired(self):
        """Remove expired DLQ entries"""
        cutoff = datetime.now() - timedelta(days=self.max_retention_days)
        
        expired_ids = []
        for dlq_id, entry in self._storage.items():
            if datetime.fromisoformat(entry["dql_created_at"]) < cutoff:
                expired_ids.append(dlq_id)
        
        for dlq_id in expired_ids:
            await self.remove_job(dlq_id)
        
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired DLQ entries")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get DLQ statistics"""
        await self._cleanup_expired()
        
        failure_counts = defaultdict(int)
        for entry in self._storage.values():
            failure_counts[entry["failure_type"]] += 1
        
        return {
            "total_jobs": len(self._storage),
            "failure_type_counts": dict(failure_counts),
            "oldest_entry": min(
                (datetime.fromisoformat(e["dql_created_at"]) for e in self._storage.values()),
                default=None
            ),
            "newest_entry": max(
                (datetime.fromisoformat(e["dql_created_at"]) for e in self._storage.values()),
                default=None
            )
        }


class ServiceCircuitBreaker(CircuitBreaker):
    """
    Extended circuit breaker for service protection in retry scenarios
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: int = 60,
        recovery_timeout: int = 30,
        expected_exception: Type[Exception] = Exception
    ):
        super().__init__(name, failure_threshold, timeout, expected_exception)
        self.recovery_timeout = recovery_timeout
        self._failure_timestamps = deque(maxlen=failure_threshold)
    
    async def record_failure(self):
        """Record failure with timestamp tracking"""
        await super().record_failure()
        self._failure_timestamps.append(time.time())
    
    async def get_failure_rate(self) -> float:
        """Get recent failure rate"""
        if len(self._failure_timestamps) < 2:
            return 0.0
        
        now = time.time()
        recent_failures = [
            ts for ts in self._failure_timestamps
            if now - ts <= 60  # Last minute
        ]
        
        return len(recent_failures) / min(len(self._failure_timestamps), 1)
    
    async def should_allow_retry(self) -> bool:
        """Determine if retry should be attempted based on circuit state and rate"""
        can_execute = await self.can_execute()
        if not can_execute:
            return False
        
        # Additional rate limiting check
        failure_rate = await self.get_failure_rate()
        if failure_rate > 0.8:  # 80% failure rate threshold
            logger.warning(f"Circuit breaker '{self.name}' blocking retry due to high failure rate")
            return False
        
        return True


class RetryableJob:
    """
    A job that can be retried with exponential backoff
    """
    
    def __init__(
        self,
        context: JobContext,
        payload: Dict[str, Any],
        retry_config: JobRetryConfig,
        processor_func: Callable[[JobContext, Dict[str, Any]], Awaitable[Any]]
    ):
        self.context = context
        self.payload = payload
        self.retry_config = retry_config
        self.processor_func = processor_func
        
        self.attempt_count = 0
        self.attempts: List[JobAttempt] = []
        self.state = JobState.QUEUED
        self.result: Optional[Any] = None
        self.error: Optional[Exception] = None
        self.total_execution_time = 0.0
        self.next_attempt_at: Optional[datetime] = None
        self.created_at = datetime.now()
        
        # Circuit breaker for this job
        self.circuit_breaker: Optional[ServiceCircuitBreaker] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for persistence"""
        return {
            "context": asdict(self.context),
            "payload": self.payload,
            "retry_config": asdict(self.retry_config),
            "attempt_count": self.attempt_count,
            "state": self.state.value,
            "result": self.result,
            "error": str(self.error) if self.error else None,
            "total_execution_time": self.total_execution_time,
            "next_attempt_at": self.next_attempt_at.isoformat() if self.next_attempt_at else None,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], processor_func: Callable) -> 'RetryableJob':
        """Create job from dictionary (persistence recovery)"""
        # Reconstruct context
        context = JobContext(**data["context"])
        
        # Reconstruct retry config
        retry_config = JobRetryConfig(**data["retry_config"])
        
        job = cls(context, data["payload"], retry_config, processor_func)
        job.attempt_count = data["attempt_count"]
        job.state = JobState(data["state"])
        job.result = data.get("result")
        job.error = data.get("error")
        job.total_execution_time = data.get("total_execution_time", 0.0)
        job.created_at = datetime.fromisoformat(data["created_at"])
        
        if data.get("next_attempt_at"):
            job.next_attempt_at = datetime.fromisoformat(data["next_attempt_at"])
        
        # Reconstruct attempts
        for attempt_data in data.get("attempts", []):
            attempt = JobAttempt(
                attempt_number=attempt_data["attempt_number"],
                started_at=datetime.fromisoformat(attempt_data["started_at"]),
            )
            if attempt_data.get("ended_at"):
                attempt.ended_at = datetime.fromisoformat(attempt_data["ended_at"])
            attempt.error = attempt_data.get("error")
            if attempt_data.get("error_classification"):
                attempt.error_classification = FailureType(attempt_data["error_classification"])
            attempt.delay_before_retry = attempt_data.get("delay_before_retry")
            attempt.circuit_breaker_state = attempt_data.get("circuit_breaker_state")
            attempt.execution_time = attempt_data.get("execution_time")
            job.attempts.append(attempt)
        
        return job


class RetryHandler:
    """
    Main retry handler orchestrating job execution with retry logic
    """
    
    def __init__(
        self,
        name: str = "retry_handler",
        retry_config: Optional[JobRetryConfig] = None,
        error_handler: Optional[SheetsErrorHandler] = None,
        dlq_retention_days: int = 7,
        monitoring_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.name = name
        self.retry_config = retry_config or JobRetryConfig()
        self.error_handler = error_handler or SheetsErrorHandler(name="retry_handler_error")
        self.dlq = DeadLetterQueue(dlq_retention_days)
        self.monitoring_callback = monitoring_callback
        
        # Circuit breakers for different services
        self.circuit_breakers: Dict[str, ServiceCircuitBreaker] = {}
        
        # Metrics
        self._metrics = {
            "jobs_received": 0,
            "jobs_completed": 0,
            "jobs_failed": 0,
            "jobs_dlq": 0,
            "total_attempts": 0,
            "successful_retries": 0,
            "circuit_breaker_trips": 0,
            "dlq_operations": 0
        }
        
        logger.info(f"RetryHandler '{name}' initialized")
    
    def _get_circuit_breaker(self, service_name: str) -> ServiceCircuitBreaker:
        """Get or create circuit breaker for service"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = ServiceCircuitBreaker(
                name=f"{self.name}_{service_name}",
                failure_threshold=5,
                timeout=60,
                recovery_timeout=30
            )
        return self.circuit_breakers[service_name]
    
    async def process_job(
        self,
        job: RetryableJob
    ) -> JobExecutionResult:
        """
        Process a job with retry logic
        
        Args:
            job: The job to process
        
        Returns:
            JobExecutionResult with outcome details
        """
        self._metrics["jobs_received"] += 1
        
        logger.info(f"Starting job {job.context.job_id} (attempt {job.attempt_count + 1})")
        
        result = JobExecutionResult(
            job_id=job.context.job_id,
            success=False,
            state=JobState.QUEUED
        )
        
        # Create circuit breaker for this job
        job.circuit_breaker = self._get_circuit_breaker(job.context.job_type)
        
        while True:
            # Check if we should attempt this job
            if not await job.circuit_breaker.should_allow_retry():
                error = Exception(f"Circuit breaker for {job.context.job_type} is open")
                classification = FailureType.SYSTEM
                break
            
            # Create attempt record
            attempt = JobAttempt(
                attempt_number=job.attempt_count + 1,
                started_at=datetime.now()
            )
            
            try:
                job.state = JobState.IN_PROGRESS
                result.state = job.state
                
                # Execute the job
                start_time = time.time()
                result.result = await job.processor_func(job.context, job.payload)
                attempt.execution_time = time.time() - start_time
                
                # Success!
                job.state = JobState.COMPLETED
                result.state = job.state
                result.success = True
                attempt.ended_at = datetime.now()
                
                job.attempts.append(attempt)
                job.total_execution_time += attempt.execution_time
                result.total_execution_time = job.total_execution_time
                
                logger.info(
                    f"Job {job.context.job_id} completed successfully "
                    f"after {job.attempt_count + 1} attempts"
                )
                
                self._metrics["jobs_completed"] += 1
                if job.attempt_count > 0:
                    self._metrics["successful_retries"] += 1
                
                break
                
            except Exception as e:
                # Record the failure
                attempt.ended_at = datetime.now()
                attempt.error = e
                
                # Classify the error
                classification = FailureClassifier.classify_error(e, job.context)
                attempt.error_classification = classification
                attempt.circuit_breaker_state = job.circuit_breaker.state.value
                
                job.attempts.append(attempt)
                job.attempt_count += 1
                job.total_execution_time += attempt.execution_time or 0
                
                logger.warning(
                    f"Job {job.context.job_id} failed (attempt {job.attempt_count}): "
                    f"{classification.value} - {str(e)}"
                )
                
                # Record failure in circuit breaker
                await job.circuit_breaker.record_failure()
                self._metrics["total_attempts"] += 1
                
                # Check if should retry
                if not FailureClassifier.is_retriable(classification):
                    # Permanent failure
                    error = e
                    break
                
                if job.attempt_count >= job.retry_config.max_retries:
                    # Max retries exceeded
                    error = e
                    break
                
                # Calculate retry delay
                delay = job.retry_config.calculate_delay(job.attempt_count - 1, e)
                attempt.delay_before_retry = delay
                
                # Schedule next attempt
                job.state = JobState.RETRYING
                result.state = job.state
                job.next_attempt_at = datetime.now() + timedelta(seconds=delay)
                
                logger.info(
                    f"Job {job.context.job_id} will retry in {delay:.2f}s "
                    f"(attempt {job.attempt_count + 1}/{job.retry_config.max_retries})"
                )
                
                # Wait before retry
                await asyncio.sleep(delay)
                
                # Check timeout
                elapsed = (datetime.now() - job.created_at).total_seconds()
                if elapsed > job.retry_config.total_timeout:
                    error = Exception(f"Job timeout after {elapsed:.2f}s")
                    break
        
        # Handle final result
        if not result.success:
            result.error = error if 'error' in locals() else e
            job.error = result.error
            job.state = JobState.FAILED
            result.state = job.state
            
            # Check if should go to DLQ
            classification = FailureClassifier.classify_error(result.error, job.context)
            should_dlq = FailureClassifier.should_consider_dlq(
                classification, 
                job.attempt_count, 
                job.retry_config.max_retries
            )
            
            if should_dlq and job.retry_config.enable_dlq:
                # Move to DLQ
                dlq_reason = self._get_dlq_reason(classification, job.attempt_count)
                dlq_id = await self.dlq.add_job(job, result.error, classification, dlq_reason)
                
                job.state = JobState.DEAD_LETTER
                result.state = job.state
                result.dlq_reason = dlq_reason
                result.final_delay = dlq_id
                
                self._metrics["jobs_dlq"] += 1
                self._metrics["dlq_operations"] += 1
                
                logger.warning(
                    f"Job {job.context.job_id} moved to DLQ (ID: {dlq_id}): {dlq_reason}"
                )
            else:
                logger.error(
                    f"Job {job.context.job_id} failed permanently after "
                    f"{job.attempt_count} attempts: {result.error}"
                )
                self._metrics["jobs_failed"] += 1
        
        # Finalize result
        result.attempts = job.attempts
        result.total_execution_time = job.total_execution_time
        
        # Update metrics
        self._update_metrics(result, classification if 'classification' in locals() else None)
        
        return result
    
    def _get_dlq_reason(self, failure_type: FailureType, attempt_count: int) -> str:
        """Get reason for DLQ based on failure type"""
        if failure_type == FailureType.PERMANENT:
            return "Permanent failure - cannot be retried"
        elif failure_type == FailureType.VALIDATION:
            return "Validation error - job data is invalid"
        elif failure_type == FailureType.AUTHENTICATION:
            return "Authentication failure - credentials invalid"
        elif attempt_count >= 5:
            return f"Max retries exceeded ({attempt_count} attempts)"
        else:
            return f"Non-retriable error: {failure_type.value}"
    
    def _update_metrics(self, result: JobExecutionResult, failure_type: Optional[FailureType]):
        """Update internal metrics"""
        if failure_type == FailureType.RATE_LIMITED:
            self._metrics["rate_limit_failures"] = self._metrics.get("rate_limit_failures", 0) + 1
        elif failure_type == FailureType.NETWORK:
            self._metrics["network_failures"] = self._metrics.get("network_failures", 0) + 1
        elif failure_type == FailureType.AUTHENTICATION:
            self._metrics["auth_failures"] = self._metrics.get("auth_failures", 0) + 1
    
    async def create_job(
        self,
        payload: Dict[str, Any],
        job_type: str = "generic",
        priority: int = 1,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        max_execution_time: float = 300.0
    ) -> RetryableJob:
        """Create a new retryable job"""
        context = JobContext(
            job_id=str(uuid.uuid4()),
            user_id=user_id,
            project_id=project_id,
            job_type=job_type,
            priority=priority,
            max_execution_time=max_execution_time
        )
        
        # This will be set when processor is provided
        async def default_processor(ctx: JobContext, data: Dict[str, Any]) -> Any:
            raise NotImplementedError("No processor function provided")
        
        job = RetryableJob(context, payload, self.retry_config, default_processor)
        
        logger.info(f"Created job {context.job_id} of type '{job_type}'")
        return job
    
    async def submit_job(
        self,
        job: RetryableJob,
        processor_func: Optional[Callable[[JobContext, Dict[str, Any]], Awaitable[Any]]] = None
    ) -> JobExecutionResult:
        """Submit job for processing"""
        if processor_func:
            job.processor_func = processor_func
        
        # Check if job has a real processor function
        if not job.processor_func or hasattr(job.processor_func, '__code__') and 'default_processor' in str(job.processor_func):
            raise ValueError("No processor function provided for job")
        
        return await self.process_job(job)
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job (would need job storage in real implementation)"""
        # In a real implementation, this would query persistent storage
        logger.info(f"Job status query for {job_id} (not implemented in demo)")
        return None
    
    async def get_dlq_stats(self) -> Dict[str, Any]:
        """Get DLQ statistics"""
        return await self.dlq.get_stats()
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        circuit_breaker_stats = {}
        for name, cb in self.circuit_breakers.items():
            circuit_breaker_stats[name] = {
                "state": cb.state.value,
                "failure_count": cb.failure_count,
                "failure_rate": await cb.get_failure_rate()
            }
        
        return {
            "handler_name": self.name,
            "metrics": self._metrics,
            "circuit_breakers": circuit_breaker_stats,
            "dlq_stats": await self.get_dlq_stats()
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of retry handler"""
        metrics = await self.get_metrics()
        
        # Calculate health score
        total_jobs = metrics["metrics"]["jobs_received"]
        if total_jobs == 0:
            success_rate = 1.0
        else:
            success_rate = metrics["metrics"]["jobs_completed"] / total_jobs
        
        # Check circuit breaker health
        open_breakers = [
            name for name, stats in metrics["circuit_breakers"].items()
            if stats["state"] == "open"
        ]
        
        health_score = 1.0
        if len(open_breakers) > 0:
            health_score -= 0.3
        
        if success_rate < 0.5:
            health_score -= 0.3
        elif success_rate < 0.8:
            health_score -= 0.1
        
        return {
            "handler_name": self.name,
            "health_score": health_score,
            "status": "healthy" if health_score >= 0.7 else "degraded",
            "total_jobs": total_jobs,
            "success_rate": success_rate,
            "open_circuit_breakers": open_breakers,
            "dlq_jobs": metrics["dlq_stats"]["total_jobs"],
            "metrics": metrics
        }


# Decorator for automatic retry handling
def retry_operation(
    job_type: str,
    retry_config: Optional[JobRetryConfig] = None,
    retry_handler: Optional[RetryHandler] = None,
    priority: int = 1,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None
):
    """
    Decorator for automatically applying retry logic to operations
    
    Usage:
        @retry_operation("data_processing", priority=1)
        async def process_data(data):
            # Processing logic here
            return result
    """
    def decorator(func: F) -> F:
        handler = retry_handler or RetryHandler()
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create job context
            context = JobContext(
                job_id=str(uuid.uuid4()),
                user_id=user_id,
                project_id=project_id,
                job_type=job_type,
                priority=priority
            )
            
            # Create payload from function arguments
            payload = {
                "function": func.__name__,
                "args": args,
                "kwargs": kwargs
            }
            
            # Create and submit job
            job = RetryableJob(context, payload, retry_config or JobRetryConfig(), func)
            result = await handler.process_job(job)
            
            if not result.success:
                raise result.error
            
            return result.result
        
        return wrapper
    return decorator


# Example usage and testing
if __name__ == "__main__":
    async def example_usage():
        """Example of using the retry handler"""
        
        # Create retry handler
        handler = RetryHandler(
            name="production_handler",
            retry_config=JobRetryConfig(
                max_retries=3,
                initial_delay=1.0,
                max_delay=30.0,
                multiplier=2.0,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF
            )
        )
        
        # Example processor function
        async def example_processor(context: JobContext, data: Dict[str, Any]) -> Dict[str, Any]:
            import random
            
            # Simulate processing with occasional failures
            if random.random() < 0.6:  # 60% chance of failure
                raise Exception(f"Random failure for job {context.job_id}")
            
            return {
                "job_id": context.job_id,
                "status": "processed",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
        
        # Create and process job
        job = await handler.create_job(
            payload={"message": "Hello, retry world!"},
            job_type="example_job"
        )
        
        result = await handler.submit_job(job, example_processor)
        
        print(f"Job result: {json.dumps(result.to_dict(), indent=2)}")
        
        # Get health status
        health = await handler.get_health_status()
        print(f"\nHealth status: {json.dumps(health, indent=2)}")
        
        # Get DLQ stats
        dlq_stats = await handler.get_dlq_stats()
        print(f"\nDLQ stats: {json.dumps(dlq_stats, indent=2)}")
    
    # Run example
    # asyncio.run(example_usage())