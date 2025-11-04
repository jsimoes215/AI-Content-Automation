"""
Test Suite for Smart Batching System

This test file demonstrates and validates the smart batching system
for API cost optimization with various scenarios and edge cases.
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from smart_batcher import (
    ContentRequest, Batch, SmartBatcher, CacheManager, 
    PriorityQueue, SmartBatchingIntegration, RateLimiter
)

class SmartBatcherTestSuite:
    """Comprehensive test suite for smart batching system"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = time.time()
    
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        self.test_results.append({
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        status_symbol = "✅" if status == "PASS" else "❌"
        print(f"{status_symbol} {test_name}: {status} {details}")
    
    async def test_basic_batching(self) -> bool:
        """Test basic batching functionality"""
        try:
            batcher = SmartBatcher(max_batch_size=5, max_batch_cost=100.0)
            
            # Create test requests
            requests = [
                ContentRequest(
                    id=f"req_{i}",
                    content_type="video",
                    prompt=f"Test video prompt {i}",
                    resolution="1920x1080",
                    duration=30.0,
                    priority=2
                ) for i in range(3)
            ]
            
            # Add requests
            for request in requests:
                await batcher.add_request(request)
            
            # Build batches
            batches = await batcher.build_optimal_batches()
            
            # Validate results
            assert len(batches) == 1, f"Expected 1 batch, got {len(batches)}"
            assert len(batches[0].requests) == 3, f"Expected 3 requests, got {len(batches[0].requests)}"
            
            self.log_test("Basic Batching", "PASS", f"Created {len(batches)} batch(es)")
            return True
            
        except Exception as e:
            self.log_test("Basic Batching", "FAIL", str(e))
            return False
    
    async def test_similarity_grouping(self) -> bool:
        """Test similarity-based grouping"""
        try:
            batcher = SmartBatcher(similarity_threshold=0.7)
            
            # Create requests with different characteristics
            requests = [
                # Similar requests (same engine, resolution, style)
                ContentRequest(
                    id="req_1",
                    content_type="video",
                    prompt="Professional office workspace",
                    resolution="1920x1080",
                    engine="default",
                    style_params={"video_style": "corporate_professional"},
                    priority=2
                ),
                ContentRequest(
                    id="req_2",
                    content_type="video", 
                    prompt="Clean office environment",
                    resolution="1920x1080",
                    engine="default",
                    style_params={"video_style": "corporate_professional"},
                    priority=2
                ),
                # Different request
                ContentRequest(
                    id="req_3",
                    content_type="video",
                    prompt="Futuristic tech environment",
                    resolution="1080x1920",  # Different resolution
                    engine="default",
                    style_params={"video_style": "tech_futuristic"},
                    priority=2
                )
            ]
            
            # Add requests
            for request in requests:
                await batcher.add_request(request)
            
            # Build batches
            batches = await batcher.build_optimal_batches()
            
            # Should create 2 batches: 1 for similar requests, 1 for different
            assert len(batches) == 2, f"Expected 2 batches, got {len(batches)}"
            
            # Find batches by characteristics
            similar_batch = None
            different_batch = None
            
            for batch in batches:
                if len(batch.requests) == 2:
                    similar_batch = batch
                elif len(batch.requests) == 1:
                    different_batch = batch
            
            assert similar_batch is not None, "Should have batch with 2 similar requests"
            assert different_batch is not None, "Should have batch with 1 different request"
            assert similar_batch.similarity_score > 0.7, "Similar batch should have high similarity"
            
            self.log_test("Similarity Grouping", "PASS", 
                         f"Grouped {len(requests)} requests into {len(batches)} batches")
            return True
            
        except Exception as e:
            self.log_test("Similarity Grouping", "FAIL", str(e))
            return False
    
    async def test_cache_functionality(self) -> bool:
        """Test cache reuse functionality"""
        try:
            cache_manager = CacheManager(memory_size=100)
            
            # Create identical requests
            request1 = ContentRequest(
                id="req_1",
                content_type="video",
                prompt="Test prompt for caching",
                resolution="1920x1080",
                duration=30.0
            )
            
            request2 = ContentRequest(
                id="req_2",
                content_type="video",
                prompt="Test prompt for caching",  # Same prompt
                resolution="1920x1080",
                duration=30.0
            )
            
            # Store result in cache
            mock_result = {"file_path": "cached/video.mp4", "quality_score": 8.5}
            cache_manager.set(request1, mock_result)
            
            # Try to retrieve from cache
            cached_result = cache_manager.get(request2)
            
            assert cached_result is not None, "Cache should return result for similar request"
            assert cached_result == mock_result, "Cached result should match stored result"
            
            # Test near-duplicate detection
            is_duplicate = cache_manager.is_near_duplicate(request2)
            assert is_duplicate, "Should detect near-duplicate request"
            
            self.log_test("Cache Functionality", "PASS", "Cache reuse working correctly")
            return True
            
        except Exception as e:
            self.log_test("Cache Functionality", "FAIL", str(e))
            return False
    
    async def test_cost_benefit_analysis(self) -> bool:
        """Test cost-benefit analysis for batching decisions"""
        try:
            batcher = SmartBatcher()
            
            # Create requests with different costs
            requests = [
                ContentRequest(
                    id=f"req_{i}",
                    content_type="video",
                    prompt=f"Test video {i}",
                    resolution="1920x1080",
                    duration=30.0 + i * 10,  # Increasing duration
                    priority=2
                ) for i in range(5)
            ]
            
            # Create batch
            batch = Batch(
                id="test_batch",
                requests=requests,
                max_size=10,
                max_cost=1000.0,
                max_duration=300.0,
                engine="default",
                resolution="1920x1080"
            )
            
            # Get cost-benefit analysis
            analysis = batcher.get_cost_benefit_analysis(batch)
            
            # Validate analysis components
            assert 'individual_cost' in analysis, "Analysis should include individual cost"
            assert 'batch_cost' in analysis, "Analysis should include batch cost"
            assert 'benefit_ratio' in analysis, "Analysis should include benefit ratio"
            assert 'recommendation' in analysis, "Analysis should include recommendation"
            
            # Check recommendation is valid
            valid_recommendations = ['process_as_batch', 'consider_batch', 'process_individually']
            assert analysis['recommendation'] in valid_recommendations, \
                f"Invalid recommendation: {analysis['recommendation']}"
            
            self.log_test("Cost-Benefit Analysis", "PASS", 
                         f"Benefit ratio: {analysis['benefit_ratio']:.2f}, "
                         f"Recommendation: {analysis['recommendation']}")
            return True
            
        except Exception as e:
            self.log_test("Cost-Benefit Analysis", "FAIL", str(e))
            return False
    
    async def test_priority_queue(self) -> bool:
        """Test priority queue with cost-aware scheduling"""
        try:
            priority_queue = PriorityQueue(budget_threshold=0.9)
            
            # Create batches with different priorities and costs
            batches = [
                Batch(
                    id=f"batch_{i}",
                    requests=[ContentRequest(
                        id=f"req_{i}_{j}",
                        content_type="video",
                        prompt=f"Test {i}_{j}",
                        priority=3-i,  # Different priorities
                        estimated_cost=50.0 + i * 25
                    ) for j in range(2)],
                    max_size=5,
                    max_cost=200.0,
                    max_duration=100.0,
                    engine="default",
                    resolution="1920x1080"
                ) for i in range(3)
            ]
            
            # Add batches to queue
            for batch in batches:
                priority_queue.enqueue(batch)
            
            # Dequeue batches (should be ordered by priority)
            dequeued_batches = []
            while priority_queue.queue:
                batch = priority_queue.dequeue()
                if batch:
                    dequeued_batches.append(batch)
            
            # Validate ordering (higher priority should come first)
            assert len(dequeued_batches) == 3, f"Expected 3 batches, got {len(dequeued_batches)}"
            
            # Check that batch order respects priority (lower priority number = higher urgency)
            # In our test, priority 2 (batch_1) should come before priority 3 (batch_2)
            batch_priorities = [min(req.priority for req in batch.requests) for batch in dequeued_batches]
            assert batch_priorities == sorted(batch_priorities), \
                f"Batch priorities should be ordered: {batch_priorities}"
            
            self.log_test("Priority Queue", "PASS", 
                         f"Processed {len(dequeued_batches)} batches in priority order")
            return True
            
        except Exception as e:
            self.log_test("Priority Queue", "FAIL", str(e))
            return False
    
    async def test_dynamic_batch_sizing(self) -> bool:
        """Test dynamic batch sizing based on content complexity"""
        try:
            batcher = SmartBatcher(
                max_batch_size=10,
                max_batch_cost=500.0,
                similarity_threshold=0.7
            )
            
            # Create requests with varying complexity
            complex_requests = [
                ContentRequest(
                    id=f"complex_{i}",
                    content_type="video",
                    prompt="A" * (100 + i * 50),  # Increasing prompt length
                    resolution="1920x1080",
                    duration=30.0,
                    style_params={"video_style": "corporate_professional", "effects": ["color_correction", "sound_enhancement"]},
                    priority=2
                ) for i in range(5)
            ]
            
            # Add requests
            for request in complex_requests:
                await batcher.add_request(request)
            
            # Build batches
            batches = await batcher.build_optimal_batches()
            
            # Complex requests should create smaller, more focused batches
            assert len(batches) >= 1, f"Should create at least 1 batch, got {len(batches)}"
            
            # Verify batch composition
            total_requests = sum(len(batch.requests) for batch in batches)
            assert total_requests == 5, f"Should process all 5 requests, got {total_requests}"
            
            self.log_test("Dynamic Batch Sizing", "PASS", 
                         f"Created {len(batches)} batches for {len(complex_requests)} complex requests")
            return True
            
        except Exception as e:
            self.log_test("Dynamic Batch Sizing", "FAIL", str(e))
            return False
    
    async def test_integration_with_existing_pipeline(self) -> bool:
        """Test integration with existing video generation pipeline"""
        try:
            cache_manager = CacheManager(memory_size=100)
            batcher = SmartBatcher(cache_manager=cache_manager)
            integration = SmartBatchingIntegration(batcher)
            
            # Create test video requests matching pipeline format
            video_requests = [
                {
                    'id': 'video_1',
                    'prompt': 'Professional office with laptop and coffee',
                    'resolution': '1920x1080',
                    'duration': 30.0,
                    'priority': 1,
                    'style_params': {'video_style': 'corporate_professional'},
                    'reference_images': []
                },
                {
                    'id': 'video_2',
                    'prompt': 'Modern workspace setup',
                    'resolution': '1920x1080',
                    'duration': 45.0,
                    'priority': 2,
                    'style_params': {'video_style': 'modern_clean'},
                    'reference_images': []
                }
            ]
            
            # Process through integration
            results = await integration.process_video_requests(video_requests)
            
            # Validate results
            assert len(results) > 0, "Should return processing results"
            assert all('batch_' in result for result in results), "Results should indicate batch processing"
            
            # Check that requests were added to batcher
            metrics = batcher.get_performance_metrics()
            assert metrics['total_requests'] == 2, f"Expected 2 total requests, got {metrics['total_requests']}"
            
            self.log_test("Pipeline Integration", "PASS", 
                         f"Processed {len(video_requests)} requests, created {len(results)} batch results")
            return True
            
        except Exception as e:
            self.log_test("Pipeline Integration", "FAIL", str(e))
            return False
    
    async def test_performance_metrics(self) -> bool:
        """Test performance metrics collection and reporting"""
        try:
            cache_manager = CacheManager(memory_size=100)
            batcher = SmartBatcher(cache_manager=cache_manager)
            
            # Add some requests
            requests = [
                ContentRequest(
                    id=f"metric_req_{i}",
                    content_type="video",
                    prompt=f"Metric test {i}",
                    priority=2
                ) for i in range(3)
            ]
            
            for request in requests:
                await batcher.add_request(request)
            
            # Build batches
            await batcher.build_optimal_batches()
            
            # Get metrics
            metrics = batcher.get_performance_metrics()
            
            # Validate metrics structure
            required_metrics = [
                'total_requests', 'batched_requests', 'cached_requests',
                'average_batch_size', 'cache_hit_ratio', 'batching_efficiency'
            ]
            
            for metric in required_metrics:
                assert metric in metrics, f"Missing metric: {metric}"
                assert isinstance(metrics[metric], (int, float)), \
                    f"Metric {metric} should be numeric, got {type(metrics[metric])}"
            
            # Test configuration optimization
            batcher.optimize_configuration(metrics)
            
            self.log_test("Performance Metrics", "PASS", 
                         f"Collected {len(metrics)} metrics successfully")
            return True
            
        except Exception as e:
            self.log_test("Performance Metrics", "FAIL", str(e))
            return False
    
    async def test_rate_limiting(self) -> bool:
        """Test rate limiting functionality"""
        try:
            rate_limiter = RateLimiter(max_requests=2, time_window=1)
            
            # Test acquiring multiple slots
            start_time = time.time()
            
            # First request should succeed immediately
            await rate_limiter.acquire()
            first_request_time = time.time() - start_time
            
            # Second request should also succeed
            await rate_limiter.acquire()
            second_request_time = time.time() - start_time
            
            # Third request should be rate limited
            start_time = time.time()
            await rate_limiter.acquire()
            third_request_time = time.time() - start_time
            
            # Third request should take longer due to rate limiting
            assert third_request_time >= 0.5, \
                f"Rate-limited request should take at least 0.5s, took {third_request_time:.2f}s"
            
            self.log_test("Rate Limiting", "PASS", 
                         f"Rate limiting working: {first_request_time:.2f}s, "
                         f"{second_request_time:.2f}s, {third_request_time:.2f}s")
            return True
            
        except Exception as e:
            self.log_test("Rate Limiting", "FAIL", str(e))
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        print("🧪 Running Smart Batching System Test Suite\n")
        
        test_methods = [
            self.test_basic_batching,
            self.test_similarity_grouping,
            self.test_cache_functionality,
            self.test_cost_benefit_analysis,
            self.test_priority_queue,
            self.test_dynamic_batch_sizing,
            self.test_integration_with_existing_pipeline,
            self.test_performance_metrics,
            self.test_rate_limiting
        ]
        
        passed = 0
        failed = 0
        
        for test_method in test_methods:
            try:
                result = await test_method()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log_test(test_method.__name__, "ERROR", str(e))
                failed += 1
            print()  # Add spacing between tests
        
        # Generate summary report
        total_time = time.time() - self.start_time
        
        summary = {
            'total_tests': len(test_methods),
            'passed': passed,
            'failed': failed,
            'success_rate': passed / len(test_methods) * 100,
            'total_time': total_time,
            'test_results': self.test_results
        }
        
        return summary

async def main():
    """Main test runner"""
    test_suite = SmartBatcherTestSuite()
    results = await test_suite.run_all_tests()
    
    print("=" * 60)
    print("SMART BATCHING SYSTEM TEST RESULTS")
    print("=" * 60)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Success Rate: {results['success_rate']:.1f}%")
    print(f"Total Time: {results['total_time']:.2f} seconds")
    print("=" * 60)
    
    if results['failed'] == 0:
        print("🎉 All tests passed! Smart batching system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the test results.")
    
    # Save detailed results
    with open('/workspace/code/test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: /workspace/code/test_results.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())