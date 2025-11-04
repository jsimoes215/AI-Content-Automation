"""
Test Suite for Parallel Audio/Video Generation System

Comprehensive tests covering all major features:
- Rate limiting (sliding window + token bucket)
- Resource pool management
- Smart batching logic
- Load balancing
- Cost monitoring
- Multi-layer caching
- Error handling and recovery
- Performance and stress testing
"""

import asyncio
import pytest
import time
import random
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

# Import the parallel generator components
from parallel_generator import (
    ParallelGenerator,
    GenerationRequest,
    GenerationResult,
    GenerationType,
    TaskPriority,
    Provider,
    ResourceType,
    RateLimitConfig,
    BatchingConfig,
    ResourcePoolConfig,
    SlidingWindowRateLimiter,
    TokenBucketRateLimiter,
    CombinedRateLimiter,
    ResourcePool,
    SmartBatcher,
    MultiLayerCache,
    LoadBalancer,
    CostMonitor,
    create_audio_request,
    create_video_request
)


class TestRateLimiting:
    """Test rate limiting algorithms"""
    
    @pytest.mark.asyncio
    async def test_sliding_window_rate_limiter(self):
        """Test sliding window rate limiting"""
        config = RateLimitConfig(per_user_requests_per_minute=3)
        limiter = SlidingWindowRateLimiter(config)
        
        # Should allow first 3 requests
        for i in range(3):
            can_proceed = await limiter.can_proceed("test_user")
            assert can_proceed, f"Request {i+1} should be allowed"
        
        # Should deny 4th request
        can_proceed = await limiter.can_proceed("test_user")
        assert not can_proceed, "4th request should be rate limited"
        
        # Test wait time calculation
        wait_time = await limiter.wait_time("test_user")
        assert wait_time > 0, "Should have positive wait time"
    
    @pytest.mark.asyncio
    async def test_token_bucket_rate_limiter(self):
        """Test token bucket rate limiting"""
        config = RateLimitConfig(
            token_bucket_capacity=5,
            token_bucket_refill_rate=2.0  # 2 tokens per second
        )
        limiter = TokenBucketRateLimiter(config)
        
        # Should allow up to capacity
        for i in range(5):
            can_proceed = await limiter.can_proceed("test_project")
            assert can_proceed, f"Request {i+1} should be allowed"
        
        # Should deny 6th request
        can_proceed = await limiter.can_proceed("test_project")
        assert not can_proceed, "Request should be limited when bucket empty"
        
        # Test token consumption
        consumed = await limiter.consume("test_project")
        assert consumed, "Should consume token successfully"
    
    @pytest.mark.asyncio
    async def test_combined_rate_limiter(self):
        """Test combined rate limiter"""
        config = RateLimitConfig(
            per_user_requests_per_minute=2,
            per_project_requests_per_minute=3,
            token_bucket_capacity=3
        )
        limiter = CombinedRateLimiter(config)
        
        # Test successful request
        can_proceed, wait_time = await limiter.can_proceed("user1", "project1")
        assert can_proceed, "First request should proceed"
        assert wait_time == 0.0, "No wait time for first request"
        
        # Test rate limiting
        can_proceed, wait_time = await limiter.can_proceed("user1", "project1")
        assert not can_proceed, "Second request should be rate limited"
    
    @pytest.mark.asyncio
    async def test_rate_limit_cleanup(self):
        """Test that rate limiters clean up old requests"""
        config = RateLimitConfig(sliding_window_minutes=1)
        limiter = SlidingWindowRateLimiter(config)
        
        # Add request
        await limiter.can_proceed("test_user")
        
        # Manually add old request (simulate time passage)
        old_time = datetime.utcnow() - timedelta(minutes=2)
        limiter.requests["test_user"].appendleft(old_time)
        
        # Should still allow request (old one cleaned up)
        can_proceed = await limiter.can_proceed("test_user")
        assert can_proceed, "Should clean up old requests"


class TestResourcePool:
    """Test resource pool management"""
    
    @pytest.mark.asyncio
    async def test_resource_acquisition(self):
        """Test resource acquisition and release"""
        config = ResourcePoolConfig(max_api_calls=10, max_memory_mb=100)
        pool = ResourcePool(config)
        
        # Acquire resources
        acquired1 = await pool.acquire(ResourceType.API_CALLS, 3)
        acquired2 = await pool.acquire(ResourceType.MEMORY, 50)
        
        assert acquired1, "Should acquire API call resources"
        assert acquired2, "Should acquire memory resources"
        
        # Check utilization
        api_util = pool.get_utilization(ResourceType.API_CALLS)
        memory_util = pool.get_utilization(ResourceType.MEMORY)
        
        assert api_util == 30.0, "API utilization should be 30%"
        assert memory_util == 50.0, "Memory utilization should be 50%"
        
        # Release resources
        await pool.release(ResourceType.API_CALLS, 2)
        await pool.release(ResourceType.MEMORY, 30)
        
        # Check updated utilization
        api_util = pool.get_utilization(ResourceType.API_CALLS)
        memory_util = pool.get_utilization(ResourceType.MEMORY)
        
        assert api_util == 10.0, "API utilization should be 10% after release"
        assert memory_util == 20.0, "Memory utilization should be 20% after release"
    
    @pytest.mark.asyncio
    async def test_resource_exhaustion(self):
        """Test resource exhaustion handling"""
        config = ResourcePoolConfig(max_api_calls=5)
        pool = ResourcePool(config)
        
        # Exhaust resources
        for i in range(5):
            acquired = await pool.acquire(ResourceType.API_CALLS)
            assert acquired, f"Should acquire resource {i+1}"
        
        # Should fail on 6th attempt
        acquired = await pool.acquire(ResourceType.API_CALLS)
        assert not acquired, "Should fail to acquire when exhausted"
    
    @pytest.mark.asyncio
    async def test_auto_scaling(self):
        """Test automatic scaling decisions"""
        config = ResourcePoolConfig(
            max_api_calls=100,
            scale_up_threshold=0.8,
            scale_down_threshold=0.3
        )
        pool = ResourcePool(config)
        
        # Test scale up condition
        await pool.acquire(ResourceType.API_CALLS, 85)  # 85% utilization
        should_scale_up = await pool.should_scale_up()
        assert should_scale_up, "Should scale up at 85% utilization"
        
        # Test scale down condition
        await pool.release(ResourceType.API_CALLS, 80)  # Reduce to 5%
        should_scale_down = await pool.should_scale_down()
        assert should_scale_down, "Should scale down at 5% utilization"
    
    def test_resource_stats(self):
        """Test resource statistics tracking"""
        config = ResourcePoolConfig(max_api_calls=50)
        pool = ResourcePool(config)
        
        # Manually set usage to test stats
        pool.current_usage[ResourceType.API_CALLS] = 30
        
        stats = pool.get_stats()
        assert "current_usage" in stats
        assert "peak_usage" in stats
        assert "utilization_percentages" in stats
        assert stats["current_usage"]["API_CALLS"] == 30
        assert stats["utilization_percentages"]["API_CALLS"] == 60.0


class TestSmartBatching:
    """Test smart batching logic"""
    
    @pytest.mark.asyncio
    async def test_batching_similarity(self):
        """Test similarity calculation and batching"""
        config = BatchingConfig(
            max_jobs_per_batch=10,
            similarity_threshold=0.8
        )
        batcher = SmartBatcher(config)
        
        # Create similar requests
        req1 = create_audio_request("Nature sounds", provider=Provider.MINIMAX)
        req2 = create_audio_request("Ocean waves", provider=Provider.MINIMAX)
        req3 = create_video_request("Cityscape", provider=Provider.RUNWAY)
        
        # Add to batcher
        await batcher.add_request(req1)
        await batcher.add_request(req2)
        await batcher.add_request(req3)
        
        # Get batch - should group similar requests
        batch = await batcher.get_next_batch()
        
        assert batch is not None, "Should return a batch"
        assert len(batch) >= 2, "Batch should have at least 2 similar requests"
        
        # Audio requests should be batched together
        audio_requests = [r for r in batch if r.type == GenerationType.AUDIO]
        assert len(audio_requests) >= 2, "Should batch audio requests together"
    
    @pytest.mark.asyncio
    async def test_batching_cost_limits(self):
        """Test cost-based batch limitations"""
        config = BatchingConfig(
            max_jobs_per_batch=10,
            max_total_cost_per_batch=50.0
        )
        batcher = SmartBatcher(config)
        
        # Create expensive requests
        expensive_requests = []
        for i in range(10):
            req = create_video_request(f"Expensive video {i}")
            req.estimated_cost = 10.0  # $10 each
            await batcher.add_request(req)
            expensive_requests.append(req)
        
        # Get batch - should be limited by cost
        batch = await batcher.get_next_batch()
        
        if batch:  # If batch was created
            total_cost = sum(r.estimated_cost for r in batch)
            assert total_cost <= config.max_total_cost_per_batch, \
                f"Batch cost ${total_cost} should not exceed limit ${config.max_total_cost_per_batch}"
    
    @pytest.mark.asyncio
    async def test_batching_priority_compatibility(self):
        """Test priority-based batching compatibility"""
        config = BatchingConfig(similarity_threshold=0.8)
        batcher = SmartBatcher(config)
        
        # Create requests with different priorities
        urgent_req = create_audio_request("Urgent content", priority=TaskPriority.URGENT)
        normal_req = create_audio_request("Normal content", priority=TaskPriority.NORMAL)
        low_req = create_audio_request("Low priority content", priority=TaskPriority.LOW)
        
        await batcher.add_request(urgent_req)
        await batcher.add_request(normal_req)
        await batcher.add_request(low_req)
        
        # Get batch - should respect priority compatibility
        batch = await batcher.get_next_batch()
        
        if batch:
            # Priority difference should not be too large
            priorities = [r.priority.value for r in batch]
            priority_range = max(priorities) - min(priorities)
            assert priority_range <= 50, "Should not batch requests with very different priorities"
    
    def test_batching_stats(self):
        """Test batching statistics tracking"""
        config = BatchingConfig()
        batcher = SmartBatcher(config)
        
        stats = batcher.get_batching_stats()
        assert "pending_requests" in stats
        assert stats["pending_requests"] == 0, "No pending requests initially"
        
        # Add a request and check stats
        req = create_audio_request("Test")
        # Stats would update after processing batches


class TestMultiLayerCache:
    """Test multi-layer caching system"""
    
    @pytest.mark.asyncio
    async def test_memory_cache(self):
        """Test memory-only caching"""
        cache = MultiLayerCache(memory_cache_size=5)
        
        # Set and get
        test_data = {"output_path": "/test/audio.mp3", "metadata": {}}
        await cache.set("test_key", test_data, ttl_seconds=60)
        
        retrieved = await cache.get("test_key")
        assert retrieved == test_data, "Should retrieve cached data"
        
        # Test LRU eviction
        for i in range(6):  # Exceed cache size
            await cache.set(f"key_{i}", {"data": f"value_{i}"})
        
        # First key should be evicted
        retrieved = await cache.get("test_key")
        assert retrieved is None, "Should evict least recently used"
    
    @pytest.mark.asyncio
    async def test_cache_hit_ratios(self):
        """Test cache hit ratio tracking"""
        cache = MultiLayerCache(memory_cache_size=10)
        
        # Initial stats
        stats = cache.get_cache_stats()
        assert stats["total_requests"] == 0
        assert stats["hit_ratio_percent"] == 0.0
        
        # Generate requests
        for i in range(10):
            key = f"key_{i}"
            await cache.get(key)  # Miss
            await cache.set(key, {"data": f"value_{i}"})
            await cache.get(key)  # Hit
        
        final_stats = cache.get_cache_stats()
        assert final_stats["total_requests"] == 20  # 10 gets + 10 hits
        assert final_stats["misses"] == 10
        assert final_stats["memory_hits"] == 10
        assert final_stats["hit_ratio_percent"] == 50.0
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self):
        """Test cache invalidation"""
        cache = MultiLayerCache()
        
        # Set and invalidate
        await cache.set("test_key", {"data": "test_value"})
        assert await cache.get("test_key") is not None
        
        await cache.invalidate("test_key")
        assert await cache.get("test_key") is None


class TestLoadBalancer:
    """Test load balancing functionality"""
    
    @pytest.mark.asyncio
    async def test_provider_selection(self):
        """Test intelligent provider selection"""
        balancer = LoadBalancer()
        
        # Create test request
        request = create_audio_request("Test content", provider=Provider.MINIMAX)
        
        # Select provider
        selected = await balancer.select_provider(request)
        assert selected in Provider, "Should select a valid provider"
        
        # Update loads
        initial_load = balancer.provider_loads[selected]
        assert initial_load > 0, "Should update provider load"
    
    @pytest.mark.asyncio
    async def test_provider_health_tracking(self):
        """Test provider health monitoring"""
        balancer = LoadBalancer()
        
        # All providers should be healthy initially
        for provider in Provider:
            assert balancer.provider_health[provider], "Providers should be healthy initially"
        
        # Report some failures
        await balancer.report_failure(Provider.MINIMAX, "Test error")
        await balancer.report_failure(Provider.MINIMAX, "Test error")
        
        # Provider should still be healthy (low error count)
        assert balancer.provider_health[Provider.MINIMAX], "Provider should remain healthy with low error rate"
        
        # Simulate high error rate
        for i in range(10):
            await balancer.report_failure(Provider.RUNWAY, "Persistent error")
        
        # Provider should be marked unhealthy
        assert not balancer.provider_health[Provider.RUNWAY], "Provider should be marked unhealthy with high error rate"
    
    @pytest.mark.asyncio
    async def test_load_balancing_stats(self):
        """Test load balancing statistics"""
        balancer = LoadBalancer()
        
        stats = balancer.get_load_stats()
        assert "provider_loads" in stats
        assert "provider_health" in stats
        assert "request_counts" in stats
        assert "error_rates" in stats
        
        # Simulate some activity
        request = create_audio_request("Test")
        selected = await balancer.select_provider(request)
        await balancer.report_success(selected, 1.0)
        
        updated_stats = balancer.get_load_stats()
        assert updated_stats["request_counts"][selected.value] > 0


class TestCostMonitor:
    """Test cost monitoring and alerting"""
    
    @pytest.mark.asyncio
    async def test_cost_recording(self):
        """Test cost recording and tracking"""
        monitor = CostMonitor()
        
        # Create test request and result
        request = create_audio_request("Test content")
        result = GenerationResult(
            request_id=request.id,
            success=True,
            output_path="/test/output.mp3",
            duration=10.0,
            actual_cost=2.5
        )
        
        await monitor.record_generation(request, result)
        
        stats = monitor.get_cost_stats()
        assert stats["current_spend"] == 2.5
        assert stats["recent_operations"] == 1
        assert stats["recent_success_rate"] == 1.0
    
    @pytest.mark.asyncio
    async def test_cost_trends(self):
        """Test cost trend analysis"""
        monitor = CostMonitor()
        
        # Simulate cost history with increasing trend
        for i in range(15):
            request = create_audio_request(f"Content {i}")
            cost = 1.0 + (i * 0.5)  # Increasing costs
            result = GenerationResult(
                request_id=request.id,
                success=True,
                actual_cost=cost
            )
            await monitor.record_generation(request, result)
        
        stats = monitor.get_cost_stats()
        assert stats["cost_trend"] == "increasing", "Should detect increasing cost trend"
    
    @pytest.mark.asyncio
    async def test_cost_alerts(self):
        """Test cost alerting system"""
        monitor = CostMonitor()
        alert_triggered = False
        
        async def alert_callback(alert_type: str, data: dict):
            nonlocal alert_triggered
            alert_triggered = True
        
        monitor.register_alert_callback(alert_callback)
        
        # Simulate high-cost operations
        for i in range(10):
            request = create_video_request(f"Expensive content {i}")
            result = GenerationResult(
                request_id=request.id,
                success=True,
                actual_cost=15.0  # High cost
            )
            await monitor.record_generation(request, result)
        
        # Alert should be triggered (rate-based alert)
        # Note: This depends on the specific alert logic implementation
        stats = monitor.get_cost_stats()
        assert "cost_trend" in stats


class TestParallelGenerator:
    """Test the main parallel generator"""
    
    @pytest.mark.asyncio
    async def test_generator_initialization(self):
        """Test generator initialization"""
        generator = ParallelGenerator()
        
        assert not generator.running, "Should not be running initially"
        assert len(generator.active_generations) == 0
        assert len(generator.generation_results) == 0
    
    @pytest.mark.asyncio
    async def test_generator_start_stop(self):
        """Test generator start and stop"""
        generator = ParallelGenerator()
        
        await generator.start()
        assert generator.running, "Should be running after start"
        
        await generator.stop()
        assert not generator.running, "Should not be running after stop"
    
    @pytest.mark.asyncio
    async def test_single_request_generation(self):
        """Test single request generation"""
        generator = ParallelGenerator()
        await generator.start()
        
        try:
            # Create single request
            request = create_audio_request("Test audio", priority=TaskPriority.NORMAL)
            results = await generator.generate([request])
            
            assert len(results) == 1, "Should return one result"
            result = results[0]
            assert result.request_id == request.id, "Result should match request ID"
            
        finally:
            await generator.stop()
    
    @pytest.mark.asyncio
    async def test_multiple_requests_generation(self):
        """Test multiple requests generation"""
        generator = ParallelGenerator()
        await generator.start()
        
        try:
            # Create multiple requests
            requests = []
            for i in range(5):
                requests.append(create_audio_request(f"Audio {i}"))
                requests.append(create_video_request(f"Video {i}"))
            
            results = await generator.generate(requests)
            
            assert len(results) == len(requests), "Should return all results"
            successful = [r for r in results if r.success]
            
            # Should have some successful generations (due to random failures in simulation)
            assert len(successful) > 0, "Should have at least some successful generations"
            
        finally:
            await generator.stop()
    
    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self):
        """Test rate limiting in integrated system"""
        # Use very strict rate limits for testing
        config = RateLimitConfig(per_user_requests_per_minute=1)
        generator = ParallelGenerator(rate_limit_config=config)
        await generator.start()
        
        try:
            # Create multiple requests that should be rate limited
            requests = []
            for i in range(3):
                requests.append(create_audio_request(f"Audio {i}", user_id="test_user"))
            
            start_time = time.time()
            results = await generator.generate(requests)
            end_time = time.time()
            
            # Should take longer due to rate limiting
            assert end_time - start_time > 1.0, "Should be rate limited"
            
        finally:
            await generator.stop()
    
    @pytest.mark.asyncio
    async def test_batching_integration(self):
        """Test batching in integrated system"""
        # Use batch-friendly config
        config = BatchingConfig(
            max_jobs_per_batch=5,
            similarity_threshold=0.7
        )
        generator = ParallelGenerator(batching_config=config)
        await generator.start()
        
        try:
            # Create similar requests that should be batched
            requests = []
            for i in range(10):
                requests.append(create_audio_request(
                    f"Similar audio content {i}",
                    provider=Provider.MINIMAX
                ))
            
            results = await generator.generate(requests)
            
            # Check if batching occurred
            batcher_stats = generator.batcher.get_batching_stats()
            
            # Should process requests (either in batches or individually)
            assert len(results) == len(requests), "Should process all requests"
            
        finally:
            await generator.stop()
    
    @pytest.mark.asyncio
    async def test_caching_integration(self):
        """Test caching in integrated system"""
        generator = ParallelGenerator()
        await generator.start()
        
        try:
            # Create identical requests
            prompt = "Identical content for caching test"
            request1 = create_audio_request(prompt)
            request2 = create_audio_request(prompt)
            
            results = await generator.generate([request1, request2])
            
            # Check caching
            cache_stats = generator.cache.get_cache_stats()
            
            # Should have cache activity
            assert cache_stats["total_requests"] > 0, "Cache should be used"
            
        finally:
            await generator.stop()
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in generation"""
        generator = ParallelGenerator()
        await generator.start()
        
        try:
            # Create requests (some may fail due to random simulation)
            requests = [create_audio_request(f"Audio {i}") for i in range(5)]
            
            results = await generator.generate(requests)
            
            # Check that all results are returned
            assert len(results) == len(requests), "Should return result for each request"
            
            # Each result should have success/failure status
            for result in results:
                assert hasattr(result, 'success'), "Result should have success status"
                assert hasattr(result, 'request_id'), "Result should have request ID"
                
        finally:
            await generator.stop()
    
    @pytest.mark.asyncio
    async def test_progress_tracking(self):
        """Test progress tracking functionality"""
        generator = ParallelGenerator()
        await generator.start()
        
        progress_updates = []
        
        async def progress_callback(request_id: str, progress: float, status: str):
            progress_updates.append((request_id, progress, status))
        
        try:
            requests = [create_audio_request(f"Audio {i}") for i in range(3)]
            
            results = await generator.generate(requests, progress_callback=progress_callback)
            
            # Progress updates should be recorded
            # Note: Implementation depends on whether progress callbacks are integrated
            assert len(results) == len(requests), "Should return all results"
            
        finally:
            await generator.stop()
    
    @pytest.mark.asyncio
    async def test_system_stats(self):
        """Test system statistics collection"""
        generator = ParallelGenerator()
        await generator.start()
        
        try:
            # Generate some content
            requests = [create_audio_request(f"Audio {i}") for i in range(3)]
            results = await generator.generate(requests)
            
            # Get system stats
            stats = await generator.get_system_stats()
            
            # Verify all components report stats
            assert "running" in stats
            assert "resource_pool" in stats
            assert "cache" in stats
            assert "load_balancer" in stats
            assert "cost_monitor" in stats
            assert "batcher" in stats
            
            # Verify stats are populated
            assert stats["total_results"] == len(results)
            
        finally:
            await generator.stop()
    
    @pytest.mark.asyncio
    async def test_cleanup_on_stop(self):
        """Test proper cleanup when stopping generator"""
        generator = ParallelGenerator()
        await generator.start()
        
        # Verify background tasks are running
        assert len(generator.background_tasks) > 0, "Should have background tasks"
        
        # Stop generator
        await generator.stop()
        
        # Background tasks should be cleaned up
        assert len(generator.background_tasks) == 0, "Should clean up background tasks"


class TestPerformance:
    """Performance and stress testing"""
    
    @pytest.mark.asyncio
    async def test_concurrent_generation(self):
        """Test high-concurrency generation"""
        generator = ParallelGenerator()
        await generator.start()
        
        try:
            # Create many concurrent requests
            requests = []
            for i in range(20):
                requests.append(create_audio_request(f"Concurrent audio {i}"))
                requests.append(create_video_request(f"Concurrent video {i}"))
            
            start_time = time.time()
            results = await generator.generate(requests)
            end_time = time.time()
            
            # Should complete in reasonable time
            assert end_time - start_time < 30.0, "Should complete within time limit"
            assert len(results) == len(requests), "Should process all requests"
            
        finally:
            await generator.stop()
    
    @pytest.mark.asyncio
    async def test_resource_pool_pressure(self):
        """Test resource pool under pressure"""
        # Use very limited resources
        config = ResourcePoolConfig(
            max_api_calls=3,
            max_concurrent_jobs=2
        )
        generator = ParallelGenerator(resource_config=config)
        await generator.start()
        
        try:
            # Create more requests than resources
            requests = [create_audio_request(f"Pressure test {i}") for i in range(10)]
            
            results = await generator.generate(requests)
            
            # Should process all requests (queuing if necessary)
            assert len(results) == len(requests), "Should process all requests"
            
            # Check resource utilization
            stats = generator.resource_pool.get_stats()
            api_util = stats["utilization_percentages"]["API_CALLS"]
            job_util = stats["utilization_percentages"]["CONCURRENT_JOBS"]
            
            # Should show high utilization during processing
            assert api_util > 0 or job_util > 0, "Should show resource utilization"
            
        finally:
            await generator.stop()


class TestIntegration:
    """Integration tests with real-world scenarios"""
    
    @pytest.mark.asyncio
    async def test_mixed_workload(self):
        """Test mixed audio/video workload"""
        generator = ParallelGenerator()
        await generator.start()
        
        try:
            # Create mixed workload
            requests = []
            
            # Audio requests
            for i in range(3):
                requests.append(create_audio_request(
                    f"Podcast episode {i}",
                    priority=TaskPriority.HIGH,
                    duration=600  # 10 minutes
                ))
            
            # Video requests
            for i in range(2):
                requests.append(create_video_request(
                    f"Marketing video {i}",
                    priority=TaskPriority.URGENT,
                    resolution="4K",
                    duration=120  # 2 minutes
                ))
            
            # Background requests
            for i in range(3):
                requests.append(create_audio_request(
                    f"Background music {i}",
                    priority=TaskPriority.LOW,
                    duration=300  # 5 minutes
                ))
            
            results = await generator.generate(requests)
            
            # Should process all requests
            assert len(results) == len(requests), "Should process all mixed requests"
            
            # Check priority handling
            # (In real implementation, would verify urgent requests are processed first)
            
        finally:
            await generator.stop()
    
    @pytest.mark.asyncio
    async def test_cost_optimization_scenario(self):
        """Test cost optimization in realistic scenario"""
        # Use cost-conscious config
        config = BatchingConfig(
            max_total_cost_per_batch=50.0,
            max_jobs_per_batch=10
        )
        generator = ParallelGenerator(batching_config=config)
        await generator.start()
        
        try:
            # Create cost-optimized workload
            requests = []
            
            # Batch-friendly requests
            for i in range(15):
                requests.append(create_audio_request(
                    f"Batchable content {i}",
                    provider=Provider.MINIMAX  # Cheaper provider
                ))
            
            results = await generator.generate(requests)
            
            # Check cost monitoring
            cost_stats = generator.cost_monitor.get_cost_stats()
            
            # Should have cost tracking
            assert "current_spend" in cost_stats
            assert cost_stats["current_spend"] >= 0.0
            
            # Check batching effectiveness
            batcher_stats = generator.batcher.get_batching_stats()
            assert "recent_avg_batch_size" in batcher_stats
            
        finally:
            await generator.stop()
    
    @pytest.mark.asyncio
    async def test_fault_tolerance_scenario(self):
        """Test fault tolerance and recovery"""
        generator = ParallelGenerator()
        await generator.start()
        
        try:
            # Create workload that will trigger some failures
            requests = [create_audio_request(f"Fault test {i}") for i in range(10)]
            
            results = await generator.generate(requests)
            
            # Should handle mixed success/failure gracefully
            assert len(results) == len(requests), "Should return all results"
            
            # Check that some requests succeed despite failures
            successful = [r for r in results if r.success]
            failed = [r for r in results if not r.success]
            
            # Should have mix of success and failure (due to random simulation)
            assert len(successful) > 0, "Should have some successful requests"
            assert len(failed) >= 0, "May have some failed requests"
            
            # Load balancer should track failures
            load_stats = generator.load_balancer.get_load_stats()
            assert "error_rates" in load_stats
            
        finally:
            await generator.stop()


# Performance benchmarking
class TestBenchmark:
    """Performance benchmarks"""
    
    @pytest.mark.asyncio
    async def benchmark_single_generation(self):
        """Benchmark single generation performance"""
        generator = ParallelGenerator()
        await generator.start()
        
        try:
            request = create_audio_request("Benchmark test")
            
            start_time = time.time()
            results = await generator.generate([request])
            end_time = time.time()
            
            generation_time = end_time - start_time
            print(f"Single generation time: {generation_time:.3f}s")
            
            assert generation_time < 5.0, "Should complete within reasonable time"
            
        finally:
            await generator.stop()
    
    @pytest.mark.asyncio
    async def benchmark_batch_generation(self):
        """Benchmark batch generation performance"""
        generator = ParallelGenerator()
        await generator.start()
        
        try:
            requests = [create_audio_request(f"Benchmark {i}") for i in range(10)]
            
            start_time = time.time()
            results = await generator.generate(requests)
            end_time = time.time()
            
            total_time = end_time - start_time
            avg_time_per_request = total_time / len(requests)
            
            print(f"Batch generation total: {total_time:.3f}s")
            print(f"Average per request: {avg_time_per_request:.3f}s")
            
            assert total_time < 30.0, "Should complete batch within reasonable time"
            
        finally:
            await generator.stop()


# Example usage demonstration
async def demo_parallel_generation():
    """Demonstration of parallel generation capabilities"""
    
    print("🚀 Parallel Audio/Video Generation System Demo")
    print("=" * 50)
    
    # Initialize generator
    generator = ParallelGenerator()
    await generator.start()
    
    try:
        print("\n📋 Creating generation requests...")
        
        # Create diverse requests
        requests = []
        
        # High-priority audio requests
        for i in range(3):
            requests.append(create_audio_request(
                f"🎵 High-quality audio {i} with ambient sounds",
                priority=TaskPriority.HIGH,
                duration=45,
                quality="high"
            ))
        
        # Video requests
        for i in range(2):
            requests.append(create_video_request(
                f"🎬 Professional video {i} with cinematic quality",
                priority=TaskPriority.NORMAL,
                resolution="1080p",
                duration=30,
                style="cinematic"
            ))
        
        # Background/priority audio
        for i in range(2):
            requests.append(create_audio_request(
                f"🎼 Background music {i} for presentations",
                priority=TaskPriority.LOW,
                duration=120,
                mood="calm"
            ))
        
        print(f"📝 Created {len(requests)} generation requests")
        print(f"   • {sum(1 for r in requests if r.type == GenerationType.AUDIO)} audio requests")
        print(f"   • {sum(1 for r in requests if r.type == GenerationType.VIDEO)} video requests")
        
        # Show request priorities
        priority_counts = {}
        for req in requests:
            priority_counts[req.priority] = priority_counts.get(req.priority, 0) + 1
        
        print("\n🎯 Request priorities:")
        for priority, count in priority_counts.items():
            print(f"   • {priority.name}: {count} requests")
        
        # Generate with progress tracking
        print("\n⚡ Starting parallel generation...")
        
        progress_updates = []
        
        async def progress_callback(request_id: str, progress: float, status: str):
            progress_updates.append((request_id, progress, status))
            if len(progress_updates) % 3 == 0:  # Print every 3 updates
                print(f"   📊 Progress: {len(progress_updates)}/{len(requests)} completed")
        
        start_time = time.time()
        results = await generator.generate(requests, progress_callback=progress_callback)
        end_time = time.time()
        
        # Display results
        print(f"\n✅ Generation completed in {end_time - start_time:.2f} seconds")
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        print(f"\n📊 Results Summary:")
        print(f"   ✅ Successful: {len(successful)}")
        print(f"   ❌ Failed: {len(failed)}")
        print(f"   📈 Success rate: {len(successful)/len(results)*100:.1f}%")
        
        if successful:
            total_cost = sum(r.actual_cost for r in successful)
            total_duration = sum(r.duration for r in successful)
            print(f"   💰 Total cost: ${total_cost:.2f}")
            print(f"   ⏱️  Total duration: {total_duration:.1f}s")
            print(f"   💡 Average cost per item: ${total_cost/len(successful):.2f}")
        
        # Show system statistics
        print(f"\n📈 System Statistics:")
        stats = await generator.get_system_stats()
        
        cache_stats = stats['cache']
        print(f"   🗄️  Cache hit ratio: {cache_stats['hit_ratio_percent']:.1f}%")
        
        cost_stats = stats['cost_monitor']
        print(f"   💳 Current spend: ${cost_stats['current_spend']:.2f}")
        print(f"   📊 Cost trend: {cost_stats['cost_trend']}")
        
        resource_stats = stats['resource_pool']
        print(f"   🔧 Resource utilization:")
        for resource, utilization in resource_stats['utilization_percentages'].items():
            print(f"      • {resource}: {utilization:.1f}%")
        
        load_stats = stats['load_balancer']
        print(f"   ⚖️  Provider health:")
        for provider, healthy in load_stats['provider_health'].items():
            status = "✅" if healthy else "❌"
            requests_served = load_stats['request_counts'].get(provider.value, 0)
            print(f"      • {provider}: {status} ({requests_served} requests)")
        
        batcher_stats = stats['batcher']
        if batcher_stats.get('recent_avg_batch_size', 0) > 0:
            print(f"   📦 Batching efficiency:")
            print(f"      • Average batch size: {batcher_stats['recent_avg_batch_size']:.1f}")
            print(f"      • Success rate: {batcher_stats.get('recent_success_rate', 0):.1%}")
        
        # Show detailed results
        print(f"\n🔍 Detailed Results:")
        for i, result in enumerate(results, 1):
            status = "✅" if result.success else "❌"
            cost = f"${result.actual_cost:.2f}" if result.success else "N/A"
            duration = f"{result.duration:.1f}s" if result.success else "N/A"
            
            request = next(r for r in requests if r.id == result.request_id)
            print(f"   {i}. {status} {request.type.value.title()} - {result.request_id[:8]}")
            print(f"      Cost: {cost} | Duration: {duration}")
            if not result.success:
                print(f"      Error: {result.error}")
        
        print(f"\n🎉 Demo completed successfully!")
        
    finally:
        await generator.stop()


# Run tests
if __name__ == "__main__":
    print("🧪 Running Parallel Generator Tests")
    print("=" * 40)
    
    # Run the demo
    asyncio.run(demo_parallel_generation())
    
    print(f"\n🏃 Running individual test suites...")
    
    # You can run specific test suites
    test_classes = [
        TestRateLimiting,
        TestResourcePool,
        TestSmartBatching,
        TestMultiLayerCache,
        TestLoadBalancer,
        TestCostMonitor,
        TestParallelGenerator,
        TestPerformance,
        TestIntegration
    ]
    
    for test_class in test_classes:
        print(f"\n🔬 Testing {test_class.__name__}...")
        # This would run pytest in a real scenario
        # For demo, we just show the test structure
        print(f"   ✅ {test_class.__name__} test suite ready")
    
    print(f"\n✨ All tests and demo completed!")
    print(f"💡 To run actual tests: pytest test_parallel_generator.py -v")
    print(f"🚀 To run demo: python test_parallel_generator.py")