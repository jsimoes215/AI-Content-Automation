# Retry Handler Implementation

A comprehensive retry logic system for robust job processing with exponential backoff, circuit breaker patterns, dead letter queue, and failure classification.

## 🎯 Overview

The retry handler provides enterprise-grade retry functionality for job processing systems, implementing patterns from the architecture design document and integrating with the existing error handling infrastructure.

## ✨ Key Features

### 1. Exponential Backoff Retry Mechanism
- **Configurable retry strategies**: Exponential backoff, linear backoff, fixed delay, immediate
- **Jitter support**: Prevents thundering herd problems with randomized delays
- **Adaptive timing**: Dynamic delay calculation based on attempt count and error type
- **Timeout protection**: Total timeout limits to prevent infinite retries

### 2. Failure Classification and Handling
- **Smart error categorization**: Transient, permanent, rate-limited, network, validation, authentication, system
- **Retriability determination**: Automatically decides if errors should be retried
- **Integration with SheetsErrorHandler**: Leverages existing error classification infrastructure
- **Context-aware handling**: Considers job type and user context in error handling

### 3. Dead Letter Queue (DLQ)
- **Automatic failure routing**: Unprocessable jobs automatically moved to DLQ
- **Retention management**: Configurable retention periods with automatic cleanup
- **DLQ operations**: List, retrieve, retry, and remove DLQ entries
- **Comprehensive metadata**: Full context, error details, and execution history

### 4. Circuit Breaker Patterns
- **Service protection**: Prevents cascading failures from unstable services
- **State management**: Closed, open, and half-open states with automatic recovery
- **Failure rate monitoring**: Tracks failure rates to make intelligent decisions
- **Per-service isolation**: Separate circuit breakers for different service types

### 5. Integration with Error Handling System
- **Seamless integration**: Works with existing `sheets_error_handler.py` infrastructure
- **Unified error model**: Shared error categories, severity levels, and handling strategies
- **Monitoring integration**: Compatible with existing monitoring and logging systems
- **Metrics compatibility**: Follows established patterns for health scoring and metrics

## 🏗️ Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    RetryHandler                              │
├─────────────────────────────────────────────────────────────┤
│ • Job processing orchestration                              │
│ • Retry logic and backoff calculation                       │
│ • Circuit breaker management                                │
│ • Health monitoring and metrics                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐ ┌───▼───┐ ┌──────▼──────┐
│ JobContext   │ │Job    │ │ Dead Letter │
│              │ │Attempt│ │ Queue       │
│ • Job ID     │ │       │ │             │
│ • User/Proj  │ │ • #   │ │ • Storage   │
│ • Type       │ │ • Err │ │ • Cleanup   │
│ • Priority   │ │ • Time│ │ • Stats     │
└──────────────┘ └───┬───┘ └─────────────┘
                     │
        ┌────────────▼────────────┐
        │  FailureClassifier      │
        │                        │
        │ • Error categorization │
        │ • Retriability logic   │
        │ • DLQ decision making  │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │   ServiceCircuitBreaker │
        │                        │
        │ • State management     │
        │ • Failure rate tracking│
        │ • Recovery detection   │
        └────────────────────────┘
```

### Integration Points

```
┌─────────────────────┐    ┌─────────────────────┐
│   Queue System      │───▶│   Retry Handler     │
│  (queue_system.md)  │    │ (retry_handler.py)  │
└─────────────────────┘    └─────────────────────┘
                                      │
                                      ▼
                          ┌─────────────────────┐
                          │ Error Handler       │
                          │ (sheets_error_      │
                          │  handler.py)        │
                          └─────────────────────┘
```

## 🚀 Quick Start

### Basic Usage

```python
import asyncio
from retry_handler import RetryHandler, JobRetryConfig, RetryStrategy

# Create retry handler
handler = RetryHandler(
    name="my_handler",
    retry_config=JobRetryConfig(
        max_retries=3,
        initial_delay=1.0,
        max_delay=10.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF
    )
)

# Define job processor
async def my_processor(context, payload):
    # Your job processing logic here
    if some_condition:
        raise Exception("Temporary failure")
    return {"status": "success", "data": payload}

# Create and submit job
async def process_jobs():
    job = await handler.create_job(
        payload={"message": "Hello World"},
        job_type="my_job"
    )
    
    result = await handler.submit_job(job, my_processor)
    
    if result.success:
        print(f"Job completed: {result.result}")
    else:
        print(f"Job failed: {result.error}")

# Run
asyncio.run(process_jobs())
```

### Advanced Configuration

```python
# Custom retry configuration
config = JobRetryConfig(
    max_retries=5,
    initial_delay=2.0,
    max_delay=60.0,
    multiplier=3.0,
    jitter=True,  # Enable jitter to prevent thundering herd
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    total_timeout=300.0,  # 5 minute total timeout
    enable_dlq=True,  # Enable dead letter queue
    dlq_retention_days=30  # 30 day retention
)

# Handler with custom configuration and monitoring
def monitoring_callback(metrics):
    # Send metrics to your monitoring system
    print(f"Metrics: {metrics}")

handler = RetryHandler(
    name="advanced_handler",
    retry_config=config,
    monitoring_callback=monitoring_callback
)
```

### Decorator Usage

```python
from retry_handler import retry_operation, JobRetryConfig

@retry_operation(
    job_type="data_processing",
    retry_config=JobRetryConfig(max_retries=3),
    priority=1
)
async def process_data(data):
    # This function will automatically have retry logic applied
    if some_unreliable_operation(data):
        raise Exception("API temporarily unavailable")
    return processed_data

# Usage
result = await process_data({"input": "data"})
```

## 📊 Configuration Options

### Retry Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_retries` | int | 5 | Maximum number of retry attempts |
| `initial_delay` | float | 1.0 | Initial delay between retries (seconds) |
| `max_delay` | float | 60.0 | Maximum delay between retries (seconds) |
| `multiplier` | float | 3.0 | Delay multiplier for exponential backoff |
| `jitter` | bool | True | Enable randomized jitter in delays |
| `strategy` | RetryStrategy | EXPONENTIAL_BACKOFF | Retry strategy to use |
| `total_timeout` | float | 300.0 | Maximum total time for all retries |
| `backoff_factor` | float | 1.5 | Factor for linear backoff |
| `min_delay` | float | 0.1 | Minimum delay between retries |
| `enable_dlq` | bool | True | Enable dead letter queue |
| `dlq_retention_days` | int | 7 | Days to retain DLQ entries |

### Retry Strategies

- **EXPONENTIAL_BACKOFF**: Delay increases exponentially (1s, 3s, 9s, 27s...)
- **LINEAR_BACKOFF**: Delay increases linearly (1s, 2.5s, 4s, 5.5s...)
- **FIXED_DELAY**: Constant delay between retries (1s, 1s, 1s...)
- **IMMEDIATE**: No delay between retries (0s, 0s, 0s...)
- **CUSTOM**: Custom delay calculation logic

## 🛠️ Error Classification

### Failure Types

| Type | Retriable | Description | Examples |
|------|-----------|-------------|----------|
| `TRANSIENT` | ✅ Yes | Temporary failures that may resolve | Server timeouts, temporary unavailable |
| `RATE_LIMITED` | ✅ Yes | Rate limit/quota exceeded | HTTP 429, API quota exceeded |
| `NETWORK` | ✅ Yes | Network connectivity issues | Connection timeout, DNS failure |
| `SYSTEM` | ✅ Yes | System-level temporary issues | Resource constraints, temporary errors |
| `PERMANENT` | ❌ No | Permanent failures that won't resolve | Service discontinued, permanent changes |
| `VALIDATION` | ❌ No | Invalid data or requests | Missing required fields, invalid format |
| `AUTHENTICATION` | ❌ No | Authentication/authorization failures | Invalid credentials, expired tokens |

### Automatic Classification

The system automatically classifies errors based on:

1. **Error type mapping**: Known error classes → failure types
2. **HTTP status codes**: 429 → RATE_LIMITED, 401/403 → AUTHENTICATION, etc.
3. **Exception types**: `ValueError` → VALIDATION, `ConnectionError` → NETWORK
4. **Context information**: Job type, user context, service being called

## 📈 Monitoring and Health

### Health Status

```python
health = await handler.get_health_status()
print(f"Health: {health['status']}")  # healthy, degraded, unhealthy
print(f"Score: {health['health_score']:.2f}")  # 0.0 to 1.0
print(f"Success Rate: {health['success_rate']:.1%}")
```

### Metrics

```python
metrics = await handler.get_metrics()
print(f"Total Jobs: {metrics['metrics']['jobs_received']}")
print(f"Success Rate: {metrics['metrics']['jobs_completed']}")
print(f"DLQ Jobs: {metrics['metrics']['jobs_dlq']}")
print(f"Circuit Breakers: {metrics['circuit_breakers']}")
```

### Circuit Breaker Monitoring

```python
# Check circuit breaker state
for name, stats in metrics['circuit_breakers'].items():
    print(f"{name}: {stats['state']} (failures: {stats['failure_count']})")
```

## 📦 Dead Letter Queue Operations

### Adding Jobs to DLQ

Jobs are automatically added to DLQ when:
- Max retries exceeded for retriable errors
- Non-retriable errors (validation, authentication, permanent)
- Circuit breaker is open and blocking retries

### DLQ Management

```python
# Get DLQ statistics
dlq_stats = await handler.get_dlq_stats()
print(f"Total DLQ entries: {dlq_stats['total_jobs']}")
print(f"Failure types: {dlq_stats['failure_type_counts']}")

# List DLQ jobs
dlq_jobs = await handler.dlq.list_jobs(limit=10, failure_type=FailureType.VALIDATION)
for job in dlq_jobs:
    print(f"Job {job['job_id']}: {job['reason']}")

# Retry a DLQ job
restored_job = await handler.dlq.retry_job(dlq_id)

# Remove from DLQ
await handler.dlq.remove_job(dlq_id)
```

## 🔧 Integration with Existing Systems

### Queue System Integration

The retry handler is designed to work with the queue system architecture from `docs/architecture_design/queue_system.md`:

- **Job states**: Aligns with queue job states (queued, retrying, completed, failed, dead_letter)
- **Rate limiting**: Respects per-user and per-project rate limits
- **Priority handling**: Considers job priority in retry scheduling
- **Monitoring integration**: Compatible with queue system monitoring

### Error Handler Integration

Seamlessly integrates with `code/sheets_error_handler.py`:

- **Error classification**: Uses shared error categories and severity levels
- **Circuit breaker**: Extends existing circuit breaker patterns
- **Monitoring**: Compatible with existing monitoring callbacks
- **Logging**: Follows established logging patterns

## 🧪 Testing and Validation

### Test Suite

Run the comprehensive test suite:

```bash
cd /workspace/code
python test_retry_handler.py
```

### Example Usage

Run the example demonstrations:

```bash
cd /workspace/code
python retry_handler_example.py
```

### Test Coverage

The test suite validates:

- ✅ Basic retry logic with exponential backoff
- ✅ Circuit breaker activation and recovery
- ✅ Dead letter queue operations
- ✅ Failure classification accuracy
- ✅ Job context and configuration
- ✅ Different retry strategies
- ✅ Health monitoring and metrics
- ✅ Integration with error handler

## 📋 Best Practices

### 1. Retry Configuration

```python
# Good: Appropriate retry limits
config = JobRetryConfig(
    max_retries=3,  # Reasonable limit
    total_timeout=300.0,  # 5 minutes
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF
)

# Bad: Unlimited retries
config = JobRetryConfig(max_retries=999)  # Never do this!
```

### 2. Error Classification

```python
# Good: Use specific exceptions
try:
    result = api_call()
except QuotaExceededError as e:
    # Will be classified as RATE_LIMITED
    raise

# Bad: Catch-all exceptions
try:
    result = api_call()
except Exception as e:
    # May be misclassified
    raise
```

### 3. Circuit Breaker Configuration

```python
# Good: Service-appropriate thresholds
breakers = {
    "critical_service": 3,    # Lower threshold for critical services
    "background_service": 10,  # Higher threshold for non-critical
    "user_facing": 5          # Balanced for user-facing services
}
```

### 4. Monitoring and Alerting

```python
# Good: Comprehensive monitoring
def monitoring_callback(metrics):
    if metrics['error_rate'] > 0.1:  # Alert on >10% error rate
        send_alert("High error rate detected")
    
    if metrics['health_score'] < 0.5:  # Alert on poor health
        send_alert("Handler health degraded")

handler = RetryHandler(
    monitoring_callback=monitoring_callback
)
```

## 🚨 Troubleshooting

### Common Issues

1. **Jobs not retrying**: Check `max_retries` and `total_timeout` settings
2. **Circuit breaker opening too quickly**: Adjust `failure_threshold` and `timeout`
3. **High DLQ volume**: Review error classification and job data validation
4. **Memory usage growing**: Ensure DLQ cleanup is working (`dlq_retention_days`)

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('retry_handler').setLevel(logging.DEBUG)
```

### Health Checks

```python
# Check handler health
health = await handler.get_health_status()
if health['status'] == 'unhealthy':
    # Take corrective action
    restart_handler()
```

## 🔮 Future Enhancements

Planned features:

- **Redis integration**: Distributed DLQ and job storage
- **Kafka integration**: Event-driven job processing
- **Advanced metrics**: Prometheus/Grafana integration
- **A/B testing**: Different retry strategies per job type
- **Machine learning**: Adaptive retry parameters based on success patterns
- **Multi-tenant**: Isolated retry handlers per tenant
- **GraphQL API**: Query job status and DLQ management

## 📚 References

- [Queue System Architecture](../docs/architecture_design/queue_system.md)
- [Sheets Error Handler](sheets_error_handler.py)
- [Google Sheets API Rate Limiting](../docs/google_sheets_research/google_sheets_rate_limits.md)
- [Exponential Backoff Patterns](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)

---

**Implementation Status**: ✅ Complete and tested
**Files Created**:
- `retry_handler.py` - Main implementation (1054 lines)
- `test_retry_handler.py` - Comprehensive test suite (592 lines)
- `retry_handler_example.py` - Usage examples (245 lines)