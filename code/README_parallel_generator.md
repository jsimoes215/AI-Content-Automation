# Parallel Audio/Video Generation System

A comprehensive parallel generation system that handles bulk audio and video generation with sophisticated rate limiting, resource pool management, and cost optimization.

## Features

### 🚀 Core Capabilities
- **Async/await concurrent processing** for audio and video generation
- **Multi-dimensional rate limiting** (sliding window + token bucket)
- **Resource pool management** with dynamic scaling
- **Smart load balancing** across providers and workers
- **Cost optimization** through intelligent batching
- **Multi-layer caching** (memory + Redis + CDN)
- **Real-time progress tracking** and monitoring
- **Comprehensive error handling** with exponential backoff

### 🎯 Key Components

1. **Rate Limiting System**
   - Per-user sliding window limits (60 requests/minute default)
   - Project-level token bucket (300 requests/minute default)
   - Burst protection with cooldown periods
   - Combined enforcement for quota compliance

2. **Resource Pool Management**
   - Dynamic resource allocation and scaling
   - API call concurrency limits
   - Memory and storage tracking
   - Auto-scaling based on utilization

3. **Smart Batching Logic**
   - Similarity-based job grouping
   - Cost optimization (max $300 per batch)
   - Duration-based batching (max 5 minutes)
   - Compatibility validation

4. **Load Balancing**
   - Provider health monitoring
   - Weighted provider selection
   - Error rate tracking
   - Automatic failover

5. **Multi-Layer Caching**
   - LRU memory cache (1000 items)
   - Redis integration
   - Cache hit ratio tracking
   - Automatic invalidation

## Quick Start

### Basic Usage

```python
import asyncio
from parallel_generator import (
    ParallelGenerator, 
    create_audio_request, 
    create_video_request,
    TaskPriority,
    Provider
)

async def generate_content():
    # Initialize generator
    generator = ParallelGenerator()
    await generator.start()
    
    try:
        # Create requests
        audio_request = create_audio_request(
            prompt="Create a relaxing ambient sound for meditation",
            priority=TaskPriority.HIGH,
            duration=30,
            format="mp3"
        )
        
        video_request = create_video_request(
            prompt="Generate a beautiful nature scene with birds flying",
            priority=TaskPriority.NORMAL,
            resolution="1080p", 
            duration=60
        )
        
        # Generate content
        results = await generator.generate([audio_request, video_request])
        
        # Check results
        for result in results:
            if result.success:
                print(f"✅ Generated: {result.output_path}")
            else:
                print(f"❌ Failed: {result.error}")
    
    finally:
        await generator.stop()

# Run the example
asyncio.run(generate_content())
```

### Advanced Configuration

```python
from parallel_generator import (
    RateLimitConfig, 
    BatchingConfig, 
    ResourcePoolConfig
)

# Custom configurations
rate_config = RateLimitConfig(
    per_user_requests_per_minute=30,  # Stricter per-user limit
    per_project_requests_per_minute=200,  # Lower project limit
    token_bucket_capacity=200
)

batch_config = BatchingConfig(
    max_jobs_per_batch=15,  # Smaller batches
    max_total_cost_per_batch=150.0  # Lower cost per batch
)

resource_config = ResourcePoolConfig(
    max_api_calls=50,  # More conservative
    max_concurrent_jobs=25,
    max_memory_mb=1024
)

# Initialize with custom configs
generator = ParallelGenerator(
    rate_limit_config=rate_config,
    batching_config=batch_config,
    resource_config=resource_config
)
```

## Architecture Details

### Rate Limiting Strategy

The system implements a dual-layer rate limiting approach:

1. **Sliding Window (Per-User)**
   - Tracks requests per user over 1-minute windows
   - Prevents individual users from exceeding quotas
   - Automatically cleans old requests

2. **Token Bucket (Project-Level)**
   - Provides burst capacity while maintaining average rate
   - 300 tokens capacity, 5 tokens/second refill rate
   - Smooths traffic and prevents quota violations

```python
# Example of rate limiting in action
async def rate_limited_generation():
    generator = ParallelGenerator()
    await generator.start()
    
    # These will be automatically rate-limited
    for i in range(100):
        request = create_audio_request(f"Audio clip {i}")
        # Rate limiter will ensure compliance with quotas
        result = await generator.generate([request])
```

### Smart Batching

Batches similar requests together to reduce costs and improve efficiency:

- **Compatibility Rules**: Same provider, similar parameters, compatible priorities
- **Cost Optimization**: Limits total batch cost to prevent oversized financial exposure
- **Duration Management**: Ensures batches don't exceed timeouts
- **Similarity Scoring**: Uses weighted similarity to group compatible jobs

```python
# Batching automatically groups compatible requests
requests = [
    create_audio_request("Nature sounds", provider=Provider.MINIMAX),
    create_audio_request("Ocean waves", provider=Provider.MINIMAX),  # Will be batched
    create_video_request("Cityscape", provider=Provider.RUNWAY),     # Separate batch
]

# Results show batching in action
results = await generator.generate(requests)
batcher_stats = generator.batcher.get_batching_stats()
print(f"Batch size: {batcher_stats['recent_avg_batch_size']:.1f}")
```

### Resource Pool Management

Dynamically manages system resources:

- **API Call Pool**: Limits concurrent API requests
- **Job Pool**: Controls parallel generation tasks
- **Memory Tracking**: Monitors memory usage
- **Auto-Scaling**: Adjusts limits based on utilization

```python
# Resource pool automatically scales
resource_stats = generator.resource_pool.get_stats()
print(f"API Call Utilization: {resource_stats['utilization_percentages']['API_CALLS']:.1f}%")
print(f"Memory Usage: {resource_stats['current_usage']['MEMORY']:.0f} MB")
```

### Load Balancing

Distributes load across providers for optimal performance:

- **Health Monitoring**: Continuous provider health checks
- **Weighted Selection**: Favors healthy, efficient providers
- **Error Tracking**: Automatically marks failing providers as unhealthy
- **Cost-Aware**: Considers cost in provider selection

```python
# Load balancer automatically selects best provider
load_stats = generator.load_balancer.get_load_stats()
print("Provider Health:")
for provider, healthy in load_stats['provider_health'].items():
    status = "✅" if healthy else "❌"
    print(f"  {provider}: {status}")
```

## Cost Optimization

### Batching Benefits
- **Reduced per-request overhead**
- **Shared model warm-up**
- **Amortized compute costs**
- **Improved throughput**

### Caching Strategy
- **Memory Cache**: Fast access for hot content
- **Redis Cache**: Cross-instance sharing
- **CDN Integration**: Edge caching for global delivery
- **Deduplication**: Detects and serves similar content

### Cost Monitoring
- **Real-time tracking** of generation costs
- **Budget alerts** at 80% threshold
- **Cost trend analysis** (increasing/decreasing/stable)
- **Provider cost comparison**

```python
# Cost monitoring and optimization
cost_stats = generator.cost_monitor.get_cost_stats()
print(f"Current Spend: ${cost_stats['current_spend']:.2f}")
print(f"Cost Trend: {cost_stats['cost_trend']}")

if cost_stats['cost_trend'] == 'increasing':
    print("⚠️  Consider optimizing batch sizes or caching strategy")
```

## Error Handling & Resilience

### Retry Logic
- **Exponential backoff** with jitter
- **Circuit breaker pattern** for failing providers
- **Idempotency protection** for safe retries
- **Dead letter queue** for terminal failures

### Error Types
- **Quota Exceeded**: Automatic backoff and retry
- **Network Errors**: Connection retry with exponential backoff  
- **Provider Failures**: Automatic failover to healthy providers
- **Resource Exhaustion**: Graceful queuing until resources available

```python
# Automatic error handling
try:
    results = await generator.generate(requests)
except Exception as e:
    # Generator handles errors internally
    # Results contain success/failure status for each request
    for result in results:
        if not result.success:
            print(f"Request {result.request_id} failed: {result.error}")
```

## Progress Tracking

### Real-time Updates
- **Progress callbacks** for live updates
- **Provider status tracking**
- **Batch completion notifications**
- **System health monitoring**

```python
async def progress_callback(request_id: str, progress: float, status: str):
    print(f"[{status}] {request_id}: {progress:.1%}")

# Register progress callback
results = await generator.generate(
    requests, 
    progress_callback=progress_callback
)
```

## Integration Examples

### With Existing Pipeline

```python
# Integration with Google Sheets pipeline
from google_sheets_client import GoogleSheetsClient
from parallel_generator import ParallelGenerator

async def content_generation_pipeline():
    sheets_client = GoogleSheetsClient()
    generator = ParallelGenerator()
    
    await generator.start()
    
    try:
        # Load generation requests from spreadsheet
        requests_data = await sheets_client.get_generation_requests()
        
        # Convert to generation requests
        requests = []
        for item in requests_data:
            if item['type'] == 'audio':
                requests.append(create_audio_request(
                    prompt=item['prompt'],
                    priority=map_priority(item['priority'])
                ))
            elif item['type'] == 'video':
                requests.append(create_video_request(
                    prompt=item['prompt'],
                    priority=map_priority(item['priority'])
                ))
        
        # Generate content
        results = await generator.generate(requests)
        
        # Update spreadsheet with results
        for result in results:
            await sheets_client.update_generation_result(
                result.request_id, 
                result.success, 
                result.output_path, 
                result.actual_cost
            )
    
    finally:
        await generator.stop()
```

### Batch Processing

```python
# Large-scale batch processing
async def process_campaign_content():
    generator = ParallelGenerator()
    await generator.start()
    
    # Load thousands of requests
    all_requests = load_requests_from_database()
    
    # Process in chunks
    chunk_size = 100
    for i in range(0, len(all_requests), chunk_size):
        chunk = all_requests[i:i + chunk_size]
        results = await generator.generate(chunk)
        
        # Update progress in database
        update_batch_progress(i + len(chunk), len(all_requests))
    
    await generator.stop()
```

## Performance Tuning

### Optimization Tips

1. **Batch Size Tuning**
   - Start with 25 jobs per batch
   - Monitor error rates and adjust
   - Consider provider limits

2. **Rate Limit Adjustment**
   - Use conservative limits for new providers
   - Monitor 429 errors and adjust
   - Implement provider-specific limits

3. **Resource Pool Sizing**
   - Monitor memory usage
   - Scale based on job complexity
   - Use auto-scaling when possible

4. **Cache Configuration**
   - Increase memory cache for high hit rates
   - Use Redis for multi-instance setups
   - Set appropriate TTLs

### Monitoring Metrics

```python
# Get comprehensive system stats
stats = await generator.get_system_stats()

print("=== System Statistics ===")
print(f"Cache Hit Ratio: {stats['cache']['hit_ratio_percent']:.1f}%")
print(f"Resource Utilization:")
for resource, utilization in stats['resource_pool']['utilization_percentages'].items():
    print(f"  {resource}: {utilization:.1f}%")
print(f"Provider Health:")
for provider, healthy in stats['load_balancer']['provider_health'].items():
    status = "✅" if healthy else "❌"
    print(f"  {provider}: {status}")
print(f"Current Cost: ${stats['cost_monitor']['current_spend']:.2f}")
print(f"Batch Efficiency: {stats['batcher']['recent_success_rate']:.1%}")
```

## Configuration Reference

### RateLimitConfig

| Parameter | Default | Description |
|-----------|---------|-------------|
| `per_user_requests_per_minute` | 60 | Per-user request limit |
| `per_project_requests_per_minute` | 300 | Project-level request limit |
| `token_bucket_capacity` | 300 | Token bucket size |
| `token_bucket_refill_rate` | 5.0 | Tokens per second |
| `max_burst_size` | 50 | Maximum burst size |
| `cooldown_period_seconds` | 5 | Cooldown after bursts |

### BatchingConfig

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_jobs_per_batch` | 25 | Maximum jobs per batch |
| `max_total_cost_per_batch` | 300.0 | Cost limit per batch |
| `max_batch_duration` | 300.0 | Duration limit per batch |
| `max_concurrent_batches` | 5 | Concurrent batch limit |
| `submission_pacing_ms` | 200 | Jitter between submissions |
| `similarity_threshold` | 0.8 | Similarity threshold for batching |

### ResourcePoolConfig

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_api_calls` | 100 | Maximum API calls |
| `max_concurrent_jobs` | 50 | Maximum concurrent jobs |
| `max_memory_mb` | 2048 | Memory limit in MB |
| `max_storage_gb` | 100 | Storage limit in GB |
| `scale_up_threshold` | 0.8 | Scale up at 80% utilization |
| `scale_down_threshold` | 0.3 | Scale down at 30% utilization |

## Best Practices

### 1. Resource Management
```python
# Always properly start and stop the generator
generator = ParallelGenerator()
await generator.start()
try:
    # Your generation code
    results = await generator.generate(requests)
finally:
    await generator.stop()
```

### 2. Error Handling
```python
# Handle individual request failures
results = await generator.generate(requests)
successful_results = [r for r in results if r.success]
failed_results = [r for r in results if not r.success]

print(f"✅ {len(successful_results)} successful")
print(f"❌ {len(failed_results)} failed")
```

### 3. Cost Monitoring
```python
# Monitor costs in real-time
cost_stats = generator.cost_monitor.get_cost_stats()
if cost_stats['current_spend'] > DAILY_BUDGET * 0.8:
    print("⚠️ Approaching daily budget limit")
    # Consider pausing low-priority jobs
```

### 4. Provider Diversification
```python
# Use multiple providers for resilience
requests = [
    create_video_request("Content 1", provider=Provider.MINIMAX),
    create_video_request("Content 2", provider=Provider.RUNWAY),
    create_video_request("Content 3", provider=Provider.AZURE),
]
```

## Troubleshooting

### Common Issues

1. **Rate Limit Errors (429)**
   - Reduce batch sizes
   - Increase rate limit values
   - Check provider quotas

2. **High Memory Usage**
   - Reduce concurrent batches
   - Increase resource pool limits
   - Check for memory leaks

3. **Low Cache Hit Ratio**
   - Increase memory cache size
   - Optimize cache key generation
   - Check Redis connectivity

4. **Provider Failures**
   - Monitor provider health
   - Implement provider rotation
   - Check API credentials

### Debug Information

```python
# Get detailed system information
stats = await generator.get_system_stats()

# Check specific component health
print("Rate Limiter Stats:", stats.get('rate_limiter', {}))
print("Cache Performance:", stats['cache'])
print("Resource Usage:", stats['resource_pool'])
print("Cost History:", stats['cost_monitor'])
```

## Future Enhancements

- [ ] **Multi-cloud provider support**
- [ ] **Advanced caching strategies** (ML-based deduplication)
- [ ] **Real-time cost optimization**
- [ ] **Auto-scaling infrastructure**
- [ ] **Advanced analytics dashboard**
- [ ] **Webhook notifications**
- [ ] **A/B testing for optimization**
- [ ] **Custom provider integrations**

## Contributing

When contributing to this system:

1. **Follow async/await patterns** throughout
2. **Include comprehensive error handling**
3. **Add proper logging and monitoring**
4. **Test with realistic load scenarios**
5. **Document new features and configurations**

## License

This system is designed to be production-ready and extensible. Modify configurations and components as needed for your specific use case and provider requirements.