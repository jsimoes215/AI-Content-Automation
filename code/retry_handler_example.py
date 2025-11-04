"""
Simple example demonstrating the key features of retry_handler.py

This example shows:
1. Basic job retry with exponential backoff
2. Circuit breaker protection
3. Dead letter queue for failed jobs
4. Health monitoring and metrics
"""

import asyncio
import json
from datetime import datetime

# Import the retry handler
from retry_handler import (
    RetryHandler,
    JobRetryConfig,
    RetryStrategy,
    FailureType,
    FailureClassifier
)


async def example_api_call(context, data):
    """Simulate an API call that might fail"""
    import random
    
    # Simulate different failure scenarios based on data
    failure_scenario = data.get("scenario", "random")
    
    if failure_scenario == "quota_exceeded":
        # Simulate quota exceeded (should be retriable)
        if random.random() < 0.7:  # 70% chance of quota error
            from sheets_error_handler import QuotaExceededError
            raise QuotaExceededError("API quota exceeded")
    
    elif failure_scenario == "validation_error":
        # Simulate validation error (should go to DLQ)
        raise ValueError("Invalid request format: missing required field 'name'")
    
    elif failure_scenario == "network_error":
        # Simulate network error (should be retriable)
        if random.random() < 0.5:  # 50% chance of network error
            raise ConnectionError("Network timeout connecting to service")
    
    elif failure_scenario == "always_fail":
        # Always fail to test DLQ
        raise Exception("Service is permanently down")
    
    else:  # random
        # Random failures for testing retry logic
        if random.random() < 0.4:  # 40% chance of failure
            raise Exception("Random temporary failure")
    
    # Success case
    return {
        "status": "success",
        "job_id": context.job_id,
        "data": data,
        "processed_at": datetime.now().isoformat()
    }


async def main():
    """Main example demonstrating retry handler features"""
    
    print("🚀 Retry Handler Example")
    print("=" * 50)
    
    # Create retry handler with custom configuration
    handler = RetryHandler(
        name="example_handler",
        retry_config=JobRetryConfig(
            max_retries=3,
            initial_delay=1.0,
            max_delay=10.0,
            multiplier=2.0,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF
        )
    )
    
    print(f"✅ Retry handler initialized: {handler.name}")
    
    # Example 1: Job that succeeds after retries
    print("\n📋 Example 1: Job with Retry Logic")
    print("-" * 30)
    
    job1 = await handler.create_job(
        payload={
            "scenario": "random",
            "message": "This job will retry on failures"
        },
        job_type="example_job"
    )
    
    result1 = await handler.submit_job(job1, example_api_call)
    
    print(f"   Job ID: {job1.context.job_id}")
    print(f"   Status: {result1.state.value}")
    print(f"   Attempts: {len(result1.attempts)}")
    print(f"   Success: {result1.success}")
    
    if result1.success:
        print(f"   Result: {result1.result['status']}")
    else:
        print(f"   Final error: {result1.error}")
    
    # Example 2: Job with quota exceeded (retriable)
    print("\n📊 Example 2: Quota Exceeded (Retriable)")
    print("-" * 30)
    
    job2 = await handler.create_job(
        payload={
            "scenario": "quota_exceeded",
            "message": "This job hits quota limits"
        },
        job_type="quota_job"
    )
    
    result2 = await handler.submit_job(job2, example_api_call)
    
    print(f"   Job ID: {job2.context.job_id}")
    print(f"   Status: {result2.state.value}")
    print(f"   Success: {result2.success}")
    
    if not result2.success and result2.attempts:
        first_attempt = result2.attempts[0]
        print(f"   Error type: {first_attempt.error_classification}")
        print(f"   Retriable: {FailureClassifier.is_retriable(first_attempt.error_classification) if first_attempt.error_classification else 'N/A'}")
    
    # Example 3: Job with validation error (goes to DLQ)
    print("\n❌ Example 3: Validation Error (Dead Letter Queue)")
    print("-" * 30)
    
    job3 = await handler.create_job(
        payload={
            "scenario": "validation_error",
            "message": "This job has invalid data"
        },
        job_type="validation_job"
    )
    
    result3 = await handler.submit_job(job3, example_api_call)
    
    print(f"   Job ID: {job3.context.job_id}")
    print(f"   Status: {result3.state.value}")
    print(f"   DLQ reason: {result3.dlq_reason}")
    print(f"   Should be in DLQ: {result3.state.value == 'dead_letter'}")
    
    # Example 4: Network error (retriable)
    print("\n🌐 Example 4: Network Error (Retriable)")
    print("-" * 30)
    
    job4 = await handler.create_job(
        payload={
            "scenario": "network_error",
            "message": "This job has network issues"
        },
        job_type="network_job"
    )
    
    result4 = await handler.submit_job(job4, example_api_call)
    
    print(f"   Job ID: {job4.context.job_id}")
    print(f"   Status: {result4.state.value}")
    print(f"   Success: {result4.success}")
    
    if result4.attempts:
        first_attempt = result4.attempts[0]
        print(f"   Error type: {first_attempt.error_classification}")
    
    # Example 5: Health monitoring
    print("\n📈 Example 5: Health Monitoring")
    print("-" * 30)
    
    health = await handler.get_health_status()
    metrics = await handler.get_metrics()
    
    print(f"   Overall health: {health['status']}")
    print(f"   Health score: {health['health_score']:.2f}")
    print(f"   Total jobs processed: {health['total_jobs']}")
    print(f"   Success rate: {health['success_rate']:.1%}")
    print(f"   Jobs in DLQ: {health['dlq_jobs']}")
    
    # Show circuit breaker status
    cb_stats = metrics['circuit_breakers']
    print(f"   Circuit breakers active: {len(cb_stats)}")
    for name, stats in cb_stats.items():
        print(f"     - {name}: {stats['state']} (failures: {stats['failure_count']})")
    
    # Example 6: DLQ operations
    print("\n📦 Example 6: Dead Letter Queue Management")
    print("-" * 30)
    
    dlq_stats = await handler.get_dlq_stats()
    print(f"   Total DLQ entries: {dlq_stats['total_jobs']}")
    print(f"   Failure types: {dlq_stats['failure_type_counts']}")
    
    # List DLQ jobs
    dlq_jobs = await handler.dlq.list_jobs(limit=5)
    if dlq_jobs:
        print(f"   Recent DLQ entries:")
        for job in dlq_jobs[:3]:  # Show first 3
            print(f"     - {job['job_id']}: {job['reason']}")
    else:
        print("   No jobs in DLQ")
    
    # Example 7: Job configuration comparison
    print("\n⚙️  Example 7: Retry Configuration")
    print("-" * 30)
    
    # Show different retry strategies
    strategies = [
        ("Exponential Backoff", RetryStrategy.EXPONENTIAL_BACKOFF),
        ("Linear Backoff", RetryStrategy.LINEAR_BACKOFF),
        ("Fixed Delay", RetryStrategy.FIXED_DELAY),
        ("Immediate Retry", RetryStrategy.IMMEDIATE)
    ]
    
    for name, strategy in strategies:
        config = JobRetryConfig(
            strategy=strategy,
            initial_delay=1.0,
            max_delay=8.0,
            multiplier=2.0
        )
        
        # Calculate delays for 4 attempts
        delays = [config.calculate_delay(i) for i in range(4)]
        delay_str = ", ".join([f"{d:.1f}s" for d in delays])
        
        print(f"   {name}: {delay_str}")
    
    print(f"\n✨ Example completed successfully!")
    print(f"   The retry handler demonstrates robust job processing with:")
    print(f"   - Automatic retry with exponential backoff")
    print(f"   - Circuit breaker protection")
    print(f"   - Dead letter queue for failed jobs")
    print(f"   - Comprehensive error classification")
    print(f"   - Health monitoring and metrics")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())