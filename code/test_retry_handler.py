"""
Test suite for retry_handler.py

Demonstrates and validates the retry functionality including:
- Basic retry operations
- Exponential backoff with jitter
- Circuit breaker patterns
- Dead letter queue operations
- Failure classification
- Integration with error handling system
"""

import asyncio
import json
import random
import time
from datetime import datetime
from typing import Dict, Any

# Import the retry handler
from retry_handler import (
    RetryHandler,
    RetryableJob,
    JobContext,
    JobRetryConfig,
    JobExecutionResult,
    FailureType,
    RetryStrategy,
    retry_operation
)


class TestRetryHandler:
    """Test suite for retry handler functionality"""
    
    def __init__(self):
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "PASS" if passed else "FAIL"
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if passed:
            self.passed_tests += 1
            print(f"✓ {test_name}: {status}")
        else:
            self.failed_tests += 1
            print(f"✗ {test_name}: {status}")
            if details:
                print(f"  Details: {details}")
    
    async def test_basic_retry_logic(self):
        """Test basic retry logic with exponential backoff"""
        print("\n=== Testing Basic Retry Logic ===")
        
        handler = RetryHandler(
            name="test_handler",
            retry_config=JobRetryConfig(
                max_retries=3,
                initial_delay=0.1,
                max_delay=1.0,
                multiplier=2.0
            )
        )
        
        call_count = 0
        
        async def flaky_processor(context: JobContext, data: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal call_count
            call_count += 1
            
            # Fail first 2 times, succeed on 3rd
            if call_count <= 2:
                raise Exception(f"Simulated failure #{call_count}")
            
            return {
                "job_id": context.job_id,
                "attempts": call_count,
                "status": "success"
            }
        
        # Create and process job
        job = await handler.create_job(
            payload={"test": "basic_retry"},
            job_type="test_job"
        )
        
        start_time = time.time()
        result = await handler.submit_job(job, flaky_processor)
        elapsed = time.time() - start_time
        
        # Verify results
        self.log_test(
            "Basic retry logic",
            result.success and result.attempts[2].attempt_number == 3,
            f"Success: {result.success}, Attempts: {len(result.attempts)}"
        )
        
        self.log_test(
            "Exponential backoff timing",
            elapsed >= 0.3,  # Should have waited for retries
            f"Elapsed: {elapsed:.2f}s"
        )
        
        metrics = await handler.get_metrics()
        self.log_test(
            "Metrics tracking",
            metrics["metrics"]["total_attempts"] == 3,
            f"Total attempts tracked: {metrics['metrics']['total_attempts']}"
        )
    
    async def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        print("\n=== Testing Circuit Breaker ===")
        
        handler = RetryHandler(
            name="circuit_test",
            retry_config=JobRetryConfig(max_retries=1)
        )
        
        failure_count = 0
        
        async def failing_processor(context: JobContext, data: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal failure_count
            failure_count += 1
            raise Exception(f"Persistent failure #{failure_count}")
        
        # Create multiple jobs that will fail
        results = []
        for i in range(6):  # More than failure threshold
            job = await handler.create_job(
                payload={"test": f"circuit_breaker_{i}"},
                job_type="failing_job"
            )
            result = await handler.submit_job(job, failing_processor)
            results.append(result)
        
        # Check circuit breaker state
        health = await handler.get_health_status()
        open_breakers = health.get("open_circuit_breakers", [])
        
        self.log_test(
            "Circuit breaker activation",
            len(open_breakers) > 0,
            f"Open breakers: {open_breakers}"
        )
        
        # Check that some jobs were blocked by circuit breaker
        cb_stats = health["metrics"]["circuit_breakers"]
        if "circuit_test_failing_job" in cb_stats:
            failure_rate = cb_stats["circuit_test_failing_job"]["failure_rate"]
            self.log_test(
                "Circuit breaker failure tracking",
                failure_rate > 0,
                f"Failure rate: {failure_rate}"
            )
    
    async def test_dead_letter_queue(self):
        """Test dead letter queue functionality"""
        print("\n=== Testing Dead Letter Queue ===")
        
        handler = RetryHandler(
            name="dlq_test",
            retry_config=JobRetryConfig(
                max_retries=2,
                enable_dlq=True
            )
        )
        
        async def permanent_failure_processor(context: JobContext, data: Dict[str, Any]) -> Dict[str, Any]:
            raise ValueError("Permanent validation error")
        
        async def timeout_processor(context: JobContext, data: Dict[str, Any]) -> Dict[str, Any]:
            # Simulate a long-running job that times out
            await asyncio.sleep(0.2)
            raise Exception("Network timeout")
        
        # Test permanent failure
        job1 = await handler.create_job(
            payload={"test": "permanent_failure"},
            job_type="validation_job"
        )
        result1 = await handler.submit_job(job1, permanent_failure_processor)
        
        # Test timeout (max retries exceeded)
        timeout_handler = RetryHandler(
            name="timeout_test",
            retry_config=JobRetryConfig(
                max_retries=1,
                initial_delay=0.1,
                total_timeout=0.15  # Very short timeout
            )
        )
        
        job2 = await timeout_handler.create_job(
            payload={"test": "timeout"},
            job_type="timeout_job"
        )
        result2 = await timeout_handler.submit_job(job2, timeout_processor)
        
        # Check DLQ stats
        dlq_stats = await handler.get_dlq_stats()
        
        self.log_test(
            "DLQ permanent failure",
            result1.state.value == "dead_letter",
            f"State: {result1.state.value}"
        )
        
        self.log_test(
            "DLQ timeout handling",
            result2.state.value == "dead_letter",
            f"State: {result2.state.value}"
        )
        
        self.log_test(
            "DLQ stats tracking",
            dlq_stats["total_jobs"] >= 2,
            f"Total DLQ jobs: {dlq_stats['total_jobs']}"
        )
        
        # Test DLQ operations
        dlq_jobs = await handler.dlq.list_jobs(limit=10)
        self.log_test(
            "DLQ list operations",
            len(dlq_jobs) >= 2,
            f"Listed jobs: {len(dlq_jobs)}"
        )
    
    async def test_failure_classification(self):
        """Test failure classification system"""
        print("\n=== Testing Failure Classification ===")
        
        from retry_handler import FailureClassifier
        
        # Test different error types
        test_cases = [
            (ValueError("Invalid data"), FailureType.VALIDATION),
            (ConnectionError("Network error"), FailureType.NETWORK),
            (Exception("Unknown error"), FailureType.SYSTEM),
        ]
        
        for error, expected_type in test_cases:
            context = JobContext(job_id="test", job_type="test")
            classified = FailureClassifier.classify_error(error, context)
            
            self.log_test(
                f"Classification of {error.__class__.__name__}",
                classified == expected_type,
                f"Expected: {expected_type.value}, Got: {classified.value}"
            )
        
        # Test retriability
        retriable_tests = [
            (FailureType.TRANSIENT, True),
            (FailureType.RATE_LIMITED, True),
            (FailureType.NETWORK, True),
            (FailureType.PERMANENT, False),
            (FailureType.VALIDATION, False),
            (FailureType.AUTHENTICATION, False),
        ]
        
        for failure_type, expected_retriable in retriable_tests:
            is_retriable = FailureClassifier.is_retriable(failure_type)
            self.log_test(
                f"Retriability of {failure_type.value}",
                is_retriable == expected_retriable,
                f"Expected: {expected_retriable}, Got: {is_retriable}"
            )
    
    async def test_job_context_and_config(self):
        """Test job context and configuration"""
        print("\n=== Testing Job Context and Configuration ===")
        
        # Test default job creation
        job = await RetryableJob(
            context=JobContext(job_id="test", job_type="test"),
            payload={"test": "data"},
            retry_config=JobRetryConfig(),
            processor_func=lambda ctx, data: asyncio.sleep(0)
        )
        
        self.log_test(
            "Default job creation",
            job.context.job_id is not None,
            f"Job ID: {job.context.job_id}"
        )
        
        # Test job configuration
        config = JobRetryConfig(
            max_retries=10,
            initial_delay=2.0,
            max_delay=60.0,
            multiplier=3.0
        )
        
        delay = config.calculate_delay(2)
        expected_delay = min(2.0 * (3.0 ** 2), 60.0)  # 18.0
        
        self.log_test(
            "Delay calculation",
            17.0 <= delay <= 19.0,  # Allow for jitter
            f"Calculated delay: {delay:.2f}s"
        )
        
        # Test job serialization
        job_dict = job.to_dict()
        self.log_test(
            "Job serialization",
            "context" in job_dict and "payload" in job_dict,
            f"Serialized keys: {list(job_dict.keys())}"
        )
    
    async def test_retry_strategies(self):
        """Test different retry strategies"""
        print("\n=== Testing Retry Strategies ===")
        
        strategies = [
            RetryStrategy.EXPONENTIAL_BACKOFF,
            RetryStrategy.LINEAR_BACKOFF,
            RetryStrategy.FIXED_DELAY,
            RetryStrategy.IMMEDIATE
        ]
        
        for strategy in strategies:
            config = JobRetryConfig(
                strategy=strategy,
                initial_delay=1.0,
                max_delay=10.0,
                multiplier=2.0
            )
            
            # Calculate delays for different attempts
            delays = [config.calculate_delay(i) for i in range(4)]
            
            # Verify strategy behavior
            if strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
                increasing = all(delays[i] >= delays[i-1] for i in range(1, len(delays)))
                self.log_test(
                    f"Exponential backoff for {strategy.value}",
                    increasing and delays[2] > delays[0],
                    f"Delays: {[f'{d:.2f}' for d in delays]}"
                )
            elif strategy == RetryStrategy.LINEAR_BACKOFF:
                increasing = all(delays[i] >= delays[i-1] for i in range(1, len(delays)))
                self.log_test(
                    f"Linear backoff for {strategy.value}",
                    increasing,
                    f"Delays: {[f'{d:.2f}' for d in delays]}"
                )
            elif strategy == RetryStrategy.IMMEDIATE:
                self.log_test(
                    f"Immediate retry for {strategy.value}",
                    all(d == 0 for d in delays),
                    f"Delays: {[f'{d:.2f}' for d in delays]}"
                )
    
    async def test_health_monitoring(self):
        """Test health monitoring and metrics"""
        print("\n=== Testing Health Monitoring ===")
        
        handler = RetryHandler(name="health_test")
        
        # Process a few jobs to generate metrics
        async def success_processor(context: JobContext, data: Dict[str, Any]) -> Dict[str, Any]:
            return {"status": "success"}
        
        async def failure_processor(context: JobContext, data: Dict[str, Any]) -> Dict[str, Any]:
            raise Exception("Test failure")
        
        # Process some successful jobs
        for i in range(3):
            job = await handler.create_job(payload={"test": f"success_{i}"})
            await handler.submit_job(job, success_processor)
        
        # Process some failed jobs
        for i in range(2):
            job = await handler.create_job(payload={"test": f"failure_{i}"})
            await handler.submit_job(job, failure_processor)
        
        # Check health status
        health = await handler.get_health_status()
        metrics = await handler.get_metrics()
        
        self.log_test(
            "Health score calculation",
            "health_score" in health and 0 <= health["health_score"] <= 1,
            f"Health score: {health['health_score']}"
        )
        
        self.log_test(
            "Metrics aggregation",
            metrics["metrics"]["jobs_received"] == 5,
            f"Jobs received: {metrics['metrics']['jobs_received']}"
        )
        
        success_rate = health["total_jobs"] and (3 / 5) or 0
        self.log_test(
            "Success rate tracking",
            abs(health["success_rate"] - success_rate) < 0.01,
            f"Success rate: {health['success_rate']}"
        )
    
    async def test_integration_with_error_handler(self):
        """Test integration with SheetsErrorHandler"""
        print("\n=== Testing Error Handler Integration ===")
        
        from sheets_error_handler import QuotaExceededError, AuthenticationError
        
        handler = RetryHandler(name="integration_test")
        
        async def api_failure_processor(context: JobContext, data: Dict[str, Any]) -> Dict[str, Any]:
            error_type = data.get("error_type", "quota")
            
            if error_type == "quota":
                raise QuotaExceededError("Quota exceeded")
            elif error_type == "auth":
                raise AuthenticationError("Authentication failed")
            else:
                raise Exception("Unknown error")
        
        # Test quota exceeded (should be retriable)
        job1 = await handler.create_job(payload={"error_type": "quota"})
        result1 = await handler.submit_job(job1, api_failure_processor)
        
        # Test authentication error (should go to DLQ)
        job2 = await handler.create_job(payload={"error_type": "auth"})
        result2 = await handler.submit_job(job2, api_failure_processor)
        
        self.log_test(
            "Quota error classification",
            result1.attempts[0].error_classification == FailureType.RATE_LIMITED,
            f"Classification: {result1.attempts[0].error_classification}"
        )
        
        self.log_test(
            "Auth error classification",
            result2.state.value == "dead_letter",
            f"State: {result2.state.value}"
        )
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n=== Test Summary ===")
        print(f"Total tests: {self.passed_tests + self.failed_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Success rate: {self.passed_tests / max(1, self.passed_tests + self.failed_tests) * 100:.1f}%")
        
        if self.failed_tests > 0:
            print(f"\nFailed tests:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test']}: {result['details']}")
    
    async def run_all_tests(self):
        """Run all test methods"""
        print("Running Retry Handler Test Suite")
        print("=" * 50)
        
        test_methods = [
            self.test_basic_retry_logic,
            self.test_circuit_breaker,
            self.test_dead_letter_queue,
            self.test_failure_classification,
            self.test_job_context_and_config,
            self.test_retry_strategies,
            self.test_health_monitoring,
            self.test_integration_with_error_handler
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                test_name = test_method.__name__
                self.log_test(test_name, False, f"Test exception: {str(e)}")
                print(f"Exception in {test_name}: {e}")
        
        self.print_summary()
        return self.failed_tests == 0


async def demo_usage():
    """Demonstrate retry handler usage"""
    print("\n" + "=" * 60)
    print("RETRY HANDLER DEMO")
    print("=" * 60)
    
    # Create retry handler with custom configuration
    handler = RetryHandler(
        name="demo_handler",
        retry_config=JobRetryConfig(
            max_retries=3,
            initial_delay=0.5,
            max_delay=5.0,
            multiplier=2.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF
        )
    )
    
    # Example 1: Basic job processing
    print("\n1. Basic Job Processing")
    print("-" * 30)
    
    attempt_count = 0
    
    async def demo_processor(context, data):
        nonlocal attempt_count
        attempt_count += 1
        
        print(f"  Attempt {attempt_count} for job {context.job_id}")
        
        if attempt_count < 3:
            raise Exception(f"Simulated failure on attempt {attempt_count}")
        
        return {
            "job_id": context.job_id,
            "message": data.get("message", "Hello World"),
            "attempts": attempt_count,
            "timestamp": datetime.now().isoformat()
        }
    
    job = await handler.create_job(
        payload={"message": "This will succeed after retries"},
        job_type="demo_job"
    )
    
    result = await handler.submit_job(job, demo_processor)
    print(f"  Result: {result.state.value}")
    print(f"  Attempts: {len(result.attempts)}")
    print(f"  Final result: {result.result}")
    
    # Example 2: Dead Letter Queue
    print("\n2. Dead Letter Queue Example")
    print("-" * 30)
    
    async def permanent_failure_processor(context, data):
        raise ValueError("This error cannot be retried - invalid data format")
    
    job2 = await handler.create_job(
        payload={"data": "invalid"},
        job_type="validation_job"
    )
    
    result2 = await handler.submit_job(job2, permanent_failure_processor)
    print(f"  Job {job2.context.job_id} moved to DLQ: {result2.state.value}")
    print(f"  DLQ reason: {result2.dlq_reason}")
    
    # Example 3: Health monitoring
    print("\n3. Health Monitoring")
    print("-" * 30)
    
    health = await handler.get_health_status()
    metrics = await handler.get_metrics()
    
    print(f"  Handler health: {health['status']}")
    print(f"  Health score: {health['health_score']:.2f}")
    print(f"  Total jobs: {health['total_jobs']}")
    print(f"  Success rate: {health['success_rate']:.2%}")
    print(f"  DLQ jobs: {health['dlq_jobs']}")
    
    # Example 4: DLQ statistics
    print("\n4. DLQ Statistics")
    print("-" * 30)
    
    dlq_stats = await handler.get_dlq_stats()
    print(f"  Total DLQ entries: {dlq_stats['total_jobs']}")
    print(f"  Failure type counts: {dlq_stats['failure_type_counts']}")
    
    print(f"\nDemo completed successfully!")


if __name__ == "__main__":
    async def main():
        # Run tests
        test_suite = TestRetryHandler()
        tests_passed = await test_suite.run_all_tests()
        
        # Run demo
        await demo_usage()
        
        return tests_passed
    
    # Run the complete test suite and demo
    success = asyncio.run(main())