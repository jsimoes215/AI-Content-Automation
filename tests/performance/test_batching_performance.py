"""
Performance Benchmarks for Batching Efficiency

This module provides comprehensive performance benchmarks for the smart batching system,
testing throughput, latency, and resource utilization across different scenarios.
"""

import asyncio
import time
import statistics
import psutil
import threading
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

# Add the code directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'code'))

from smart_batcher import SmartBatcher, ContentRequest, CacheManager


@dataclass
class PerformanceBenchmark:
    """Results from a performance benchmark"""
    benchmark_name: str
    total_requests: int
    batch_configuration: Dict[str, Any]
    throughput_rps: float  # Requests per second
    latency_p50_ms: float  # 50th percentile latency
    latency_p95_ms: float  # 95th percentile latency
    latency_p99_ms: float  # 99th percentile latency
    cpu_usage_percent: float
    memory_usage_mb: float
    batch_utilization: float  # Average batch utilization percentage
    cache_hit_ratio: float
    error_rate_percent: float
    cost_efficiency: float  # Cost per processed request
    resource_efficiency: float  # Requests per CPU second


@dataclass
class LoadTestResult:
    """Results from load testing"""
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time_seconds: float
    requests_per_second: float
    error_rate_percent: float
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float


class BatchingPerformanceBenchmarks:
    """Performance benchmarks for batching efficiency"""
    
    def __init__(self):
        self.benchmark_results = []
        self.load_test_results = []
        self.system_metrics = {
            'cpu_cores': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'available_memory_gb': psutil.virtual_memory().available / (1024**3)
        }
    
    async def run_throughput_benchmarks(self) -> List[PerformanceBenchmark]:
        """Run throughput benchmarks for different batch sizes"""
        print("\n=== Throughput Benchmarks ===")
        results = []
        
        batch_sizes = [5, 10, 20, 25, 35, 50]
        requests_per_test = 500
        
        for batch_size in batch_sizes:
            print(f"Testing batch size: {batch_size}")
            
            # Generate test requests
            requests = self._generate_test_requests(requests_per_test)
            
            # Run benchmark
            result = await self._run_throughput_benchmark(
                f"Throughput_BatchSize_{batch_size}",
                requests,
                {
                    'max_batch_size': batch_size,
                    'max_batch_cost': 500.0,
                    'similarity_threshold': 0.7
                }
            )
            results.append(result)
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        return results
    
    async def run_latency_benchmarks(self) -> List[PerformanceBenchmark]:
        """Run latency benchmarks for different similarity thresholds"""
        print("\n=== Latency Benchmarks ===")
        results = []
        
        similarity_thresholds = [0.3, 0.5, 0.7, 0.9]
        requests_per_test = 300
        
        for threshold in similarity_thresholds:
            print(f"Testing similarity threshold: {threshold}")
            
            requests = self._generate_test_requests(requests_per_test)
            
            result = await self._run_throughput_benchmark(
                f"Latency_Threshold_{threshold}",
                requests,
                {
                    'max_batch_size': 25,
                    'max_batch_cost': 500.0,
                    'similarity_threshold': threshold
                }
            )
            results.append(result)
        
        return results
    
    async def run_cache_efficiency_benchmarks(self) -> List[PerformanceBenchmark]:
        """Run benchmarks testing cache efficiency"""
        print("\n=== Cache Efficiency Benchmarks ===")
        results = []
        
        cache_sizes = [100, 500, 1000, 2000]
        requests_per_test = 400
        
        # Generate some duplicate content for cache testing
        base_requests = self._generate_test_requests(100)
        duplicate_requests = self._duplicate_requests(base_requests, 3)  # Create 3x duplicates
        
        for cache_size in cache_sizes:
            print(f"Testing cache size: {cache_size}")
            
            # Mix of original and duplicate requests
            test_requests = base_requests + duplicate_requests[:300]
            
            result = await self._run_throughput_benchmark(
                f"Cache_Size_{cache_size}",
                test_requests,
                {
                    'max_batch_size': 25,
                    'max_batch_cost': 500.0,
                    'similarity_threshold': 0.7,
                    'cache_size': cache_size
                }
            )
            results.append(result)
        
        return results
    
    async def run_resource_utilization_benchmarks(self) -> List[PerformanceBenchmark]:
        """Run benchmarks for resource utilization"""
        print("\n=== Resource Utilization Benchmarks ===")
        results = []
        
        test_scenarios = [
            {
                'name': 'CPU_Intensive',
                'requests': self._generate_cpu_intensive_requests(200),
                'config': {'max_batch_size': 10, 'similarity_threshold': 0.8}
            },
            {
                'name': 'Memory_Intensive',
                'requests': self._generate_memory_intensive_requests(200),
                'config': {'max_batch_size': 50, 'similarity_threshold': 0.6}
            },
            {
                'name': 'Balanced',
                'requests': self._generate_balanced_requests(300),
                'config': {'max_batch_size': 25, 'similarity_threshold': 0.7}
            }
        ]
        
        for scenario in test_scenarios:
            print(f"Testing scenario: {scenario['name']}")
            
            result = await self._run_throughput_benchmark(
                f"Resource_{scenario['name']}",
                scenario['requests'],
                scenario['config']
            )
            results.append(result)
        
        return results
    
    async def run_concurrent_load_tests(self) -> List[LoadTestResult]:
        """Run concurrent load tests"""
        print("\n=== Concurrent Load Tests ===")
        results = []
        
        concurrency_levels = [1, 5, 10, 20, 50]
        total_requests = 1000
        
        for concurrency in concurrency_levels:
            print(f"Testing concurrency level: {concurrency}")
            
            result = await self._run_concurrent_load_test(
                f"LoadTest_Concurrency_{concurrency}",
                total_requests,
                concurrency
            )
            results.append(result)
            
            # Cool down period between tests
            await asyncio.sleep(2)
        
        return results
    
    async def run_scalability_benchmarks(self) -> List[PerformanceBenchmark]:
        """Run scalability benchmarks for different request volumes"""
        print("\n=== Scalability Benchmarks ===")
        results = []
        
        request_counts = [100, 500, 1000, 2000, 5000]
        
        for request_count in request_counts:
            print(f"Testing request volume: {request_count}")
            
            requests = self._generate_test_requests(request_count)
            
            result = await self._run_throughput_benchmark(
                f"Scalability_Volume_{request_count}",
                requests,
                {
                    'max_batch_size': 25,
                    'max_batch_cost': 1000.0,
                    'similarity_threshold': 0.7
                }
            )
            results.append(result)
        
        return results
    
    async def _run_throughput_benchmark(
        self, 
        benchmark_name: str, 
        requests: List[Dict], 
        batch_config: Dict[str, Any]
    ) -> PerformanceBenchmark:
        """Run a throughput benchmark"""
        
        # Initialize batcher with config
        cache_size = batch_config.get('cache_size', 1000)
        cache_manager = CacheManager(memory_size=cache_size)
        
        batcher = SmartBatcher(
            max_batch_size=batch_config.get('max_batch_size', 25),
            max_batch_cost=batch_config.get('max_batch_cost', 500.0),
            similarity_threshold=batch_config.get('similarity_threshold', 0.7),
            cache_manager=cache_manager
        )
        
        # Convert requests to ContentRequest objects
        content_requests = []
        for i, req_data in enumerate(requests):
            request = ContentRequest(
                id=f"bench_{i}",
                content_type=req_data.get('content_type', 'video'),
                prompt=req_data.get('prompt', ''),
                reference_images=req_data.get('reference_images', []),
                resolution=req_data.get('resolution', '1920x1080'),
                duration=req_data.get('duration', 30.0),
                engine=req_data.get('engine', 'default'),
                style_params=req_data.get('style_params', {}),
                priority=req_data.get('priority', 2)
            )
            content_requests.append(request)
        
        # Measure system metrics before
        process = psutil.Process()
        cpu_before = process.cpu_percent()
        memory_before = process.memory_info().rss / (1024 * 1024)  # MB
        
        # Track latency
        latency_measurements = []
        
        # Run benchmark
        start_time = time.time()
        total_batches = 0
        total_processed = 0
        total_errors = 0
        total_cost = 0.0
        
        # Add requests with latency tracking
        request_start_time = time.time()
        for request in content_requests:
            req_start = time.time()
            await batcher.add_request(request)
            req_end = time.time()
            latency_measurements.append((req_end - req_start) * 1000)  # Convert to ms
        
        add_requests_time = time.time() - request_start_time
        
        # Build batches
        batches_start_time = time.time()
        batches = await batcher.build_optimal_batches()
        batch_build_time = time.time() - batches_start_time
        
        # Process batches
        batch_start_time = time.time()
        for batch in batches:
            batch_result = await batcher.process_batch(batch)
            total_batches += 1
            total_processed += batch_result.get('requests', 0)
            total_cost += batch_result.get('total_cost', 0)
            if batch_result.get('status') == 'failed':
                total_errors += 1
        
        batch_processing_time = time.time() - batch_start_time
        total_time = time.time() - start_time
        
        # Measure system metrics after
        cpu_after = process.cpu_percent()
        memory_after = process.memory_info().rss / (1024 * 1024)  # MB
        
        # Calculate metrics
        throughput = total_processed / total_time
        cpu_usage = cpu_after
        memory_usage = memory_after - memory_before
        
        # Calculate batch utilization
        avg_batch_size = sum(len(b.requests) for b in batches) / len(batches) if batches else 0
        batch_utilization = (avg_batch_size / batch_config.get('max_batch_size', 25)) * 100
        
        # Get performance metrics
        metrics = batcher.get_performance_metrics()
        
        # Create benchmark result
        result = PerformanceBenchmark(
            benchmark_name=benchmark_name,
            total_requests=len(requests),
            batch_configuration=batch_config,
            throughput_rps=throughput,
            latency_p50_ms=statistics.median(latency_measurements) if latency_measurements else 0,
            latency_p95_ms=np.percentile(latency_measurements, 95) if latency_measurements else 0,
            latency_p99_ms=np.percentile(latency_measurements, 99) if latency_measurements else 0,
            cpu_usage_percent=cpu_usage,
            memory_usage_mb=memory_usage,
            batch_utilization=batch_utilization,
            cache_hit_ratio=metrics.get('cache_hit_ratio', 0.0),
            error_rate_percent=(total_errors / total_batches) * 100 if total_batches > 0 else 0,
            cost_efficiency=total_cost / total_processed if total_processed > 0 else 0,
            resource_efficiency=throughput / max(cpu_usage, 1)  # Requests per CPU percent
        )
        
        self.benchmark_results.append(result)
        return result
    
    async def _run_concurrent_load_test(
        self, 
        test_name: str, 
        total_requests: int, 
        concurrency: int
    ) -> LoadTestResult:
        """Run a concurrent load test"""
        
        batcher = SmartBatcher(
            max_batch_size=25,
            max_batch_cost=500.0,
            similarity_threshold=0.7,
            cache_manager=CacheManager(memory_size=1000)
        )
        
        # Generate requests
        requests = self._generate_test_requests(total_requests)
        
        # Track metrics
        request_times = []
        successful_requests = 0
        failed_requests = 0
        lock = threading.Lock()
        
        async def process_batch(request_batch: List[ContentRequest]):
            nonlocal successful_requests, failed_requests
            
            try:
                # Add requests
                batch_start = time.time()
                for request in request_batch:
                    start = time.time()
                    await batcher.add_request(request)
                    end = time.time()
                    request_times.append(end - start)
                
                # Build and process batches
                batches = await batcher.build_optimal_batches()
                for batch in batches:
                    result = await batcher.process_batch(batch)
                    if result.get('status') == 'success':
                        with lock:
                            successful_requests += len(batch.requests)
                    else:
                        with lock:
                            failed_requests += len(batch.requests)
                            
            except Exception as e:
                with lock:
                    failed_requests += len(request_batch)
                print(f"Error in batch processing: {e}")
        
        # Split requests into concurrent batches
        batch_size = total_requests // concurrency
        request_batches = []
        for i in range(0, len(requests), batch_size):
            batch = requests[i:i + batch_size]
            # Convert to ContentRequest objects
            content_batch = []
            for j, req_data in enumerate(batch):
                request = ContentRequest(
                    id=f"load_test_{i+j}",
                    content_type=req_data.get('content_type', 'video'),
                    prompt=req_data.get('prompt', ''),
                    reference_images=req_data.get('reference_images', []),
                    resolution=req_data.get('resolution', '1920x1080'),
                    duration=req_data.get('duration', 30.0),
                    engine=req_data.get('engine', 'default'),
                    style_params=req_data.get('style_params', {}),
                    priority=req_data.get('priority', 2)
                )
                content_batch.append(request)
            request_batches.append(content_batch)
        
        # Run concurrent load test
        start_time = time.time()
        tasks = [process_batch(batch) for batch in request_batches]
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Calculate metrics
        requests_per_second = total_requests / total_time
        error_rate = (failed_requests / total_requests) * 100 if total_requests > 0 else 0
        avg_response_time = statistics.mean([rt * 1000 for rt in request_times]) if request_times else 0
        p95_response_time = np.percentile([rt * 1000 for rt in request_times], 95) if request_times else 0
        p99_response_time = np.percentile([rt * 1000 for rt in request_times], 99) if request_times else 0
        
        result = LoadTestResult(
            concurrent_users=concurrency,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_time_seconds=total_time,
            requests_per_second=requests_per_second,
            error_rate_percent=error_rate,
            avg_response_time_ms=avg_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time
        )
        
        self.load_test_results.append(result)
        return result
    
    # Request generation methods
    def _generate_test_requests(self, count: int) -> List[Dict]:
        """Generate test requests for benchmarking"""
        content_types = ['video', 'image', 'audio']
        requests = []
        
        for i in range(count):
            content_type = random.choice(content_types)
            
            if content_type == 'video':
                requests.append({
                    'content_type': 'video',
                    'prompt': f'Benchmark video content {i} - test scenario',
                    'resolution': '1920x1080',
                    'duration': random.uniform(30, 120),
                    'engine': 'benchmark_default',
                    'style_params': {'test': True},
                    'priority': 2
                })
            elif content_type == 'image':
                requests.append({
                    'content_type': 'image',
                    'prompt': f'Benchmark image {i} - performance test',
                    'resolution': '1024x1024',
                    'duration': 1.0,
                    'engine': 'benchmark_default',
                    'style_params': {'test': True},
                    'priority': 2
                })
            else:  # audio
                requests.append({
                    'content_type': 'audio',
                    'prompt': f'Benchmark audio {i} - latency test',
                    'resolution': 'standard',
                    'duration': random.uniform(60, 300),
                    'engine': 'benchmark_default',
                    'style_params': {'test': True},
                    'priority': 2
                })
        
        return requests
    
    def _duplicate_requests(self, base_requests: List[Dict], multiplier: int) -> List[Dict]:
        """Create duplicate requests for cache testing"""
        duplicated = []
        for i, req in enumerate(base_requests):
            for j in range(multiplier):
                # Create slightly varied duplicates
                duplicate = req.copy()
                duplicate['prompt'] = f"{req['prompt']} (duplicate {j+1})"
                duplicate['id'] = f"duplicate_{i}_{j}"
                duplicated.append(duplicate)
        return duplicated
    
    def _generate_cpu_intensive_requests(self, count: int) -> List[Dict]:
        """Generate requests that are CPU intensive"""
        requests = []
        for i in range(count):
            requests.append({
                'content_type': 'video',
                'prompt': f'CPU intensive video {i} with complex processing requirements',
                'resolution': '3840x2160',  # 4K for CPU intensity
                'duration': random.uniform(120, 300),
                'engine': 'cpu_intensive',
                'style_params': {'complexity': 'high', 'effects': True},
                'priority': 2
            })
        return requests
    
    def _generate_memory_intensive_requests(self, count: int) -> List[Dict]:
        """Generate requests that are memory intensive"""
        requests = []
        for i in range(count):
            requests.append({
                'content_type': 'video',
                'prompt': f'Memory intensive video {i} with large reference images',
                'resolution': '1920x1080',
                'duration': random.uniform(30, 180),
                'engine': 'memory_intensive',
                'style_params': {'memory_usage': 'high', 'references': 10},
                'priority': 2
            })
        return requests
    
    def _generate_balanced_requests(self, count: int) -> List[Dict]:
        """Generate balanced requests across content types"""
        content_types = ['video', 'image', 'audio']
        requests = []
        
        for i in range(count):
            content_type = random.choice(content_types)
            
            if content_type == 'video':
                requests.append({
                    'content_type': 'video',
                    'prompt': f'Balanced video content {i} for performance testing',
                    'resolution': '1920x1080',
                    'duration': random.uniform(60, 120),
                    'engine': 'balanced',
                    'style_params': {'balanced': True},
                    'priority': random.choice([1, 2, 3])
                })
            elif content_type == 'image':
                requests.append({
                    'content_type': 'image',
                    'prompt': f'Balanced image {i} for throughput testing',
                    'resolution': '1920x1080',
                    'duration': 1.0,
                    'engine': 'balanced',
                    'style_params': {'balanced': True},
                    'priority': random.choice([1, 2, 3])
                })
            else:
                requests.append({
                    'content_type': 'audio',
                    'prompt': f'Balanced audio {i} for latency testing',
                    'resolution': 'standard',
                    'duration': random.uniform(120, 240),
                    'engine': 'balanced',
                    'style_params': {'balanced': True},
                    'priority': random.choice([1, 2, 3])
                })
        
        return requests
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.benchmark_results:
            return {}
        
        # Throughput analysis
        throughput_values = [r.throughput_rps for r in self.benchmark_results]
        latency_values = [r.latency_p95_ms for r in self.benchmark_results]
        cpu_values = [r.cpu_usage_percent for r in self.benchmark_results]
        memory_values = [r.memory_usage_mb for r in self.benchmark_results]
        
        # Load test analysis
        load_test_throughput = [r.requests_per_second for r in self.load_test_results]
        load_test_errors = [r.error_rate_percent for r in self.load_test_results]
        
        report = {
            'performance_summary': {
                'total_benchmarks': len(self.benchmark_results),
                'total_load_tests': len(self.load_test_results),
                'max_throughput_rps': max(throughput_values),
                'min_latency_p95_ms': min(latency_values),
                'max_latency_p95_ms': max(latency_values),
                'avg_cpu_usage_percent': statistics.mean(cpu_values),
                'avg_memory_usage_mb': statistics.mean(memory_values)
            },
            'throughput_analysis': {
                'min_rps': min(throughput_values),
                'max_rps': max(throughput_values),
                'avg_rps': statistics.mean(throughput_values),
                'std_dev_rps': statistics.stdev(throughput_values) if len(throughput_values) > 1 else 0
            },
            'latency_analysis': {
                'min_p95_ms': min(latency_values),
                'max_p95_ms': max(latency_values),
                'avg_p95_ms': statistics.mean(latency_values),
                'median_p95_ms': statistics.median(latency_values)
            },
            'load_test_analysis': {
                'max_concurrent_rps': max(load_test_throughput) if load_test_throughput else 0,
                'min_error_rate_percent': min(load_test_errors) if load_test_errors else 0,
                'max_error_rate_percent': max(load_test_errors) if load_test_errors else 0,
                'avg_error_rate_percent': statistics.mean(load_test_errors) if load_test_errors else 0
            },
            'resource_efficiency': {
                'avg_batch_utilization': statistics.mean([r.batch_utilization for r in self.benchmark_results]),
                'avg_cache_hit_ratio': statistics.mean([r.cache_hit_ratio for r in self.benchmark_results]),
                'avg_cost_efficiency': statistics.mean([r.cost_efficiency for r in self.benchmark_results]),
                'avg_resource_efficiency': statistics.mean([r.resource_efficiency for r in self.benchmark_results])
            }
        }
        
        return report


# Import random at the module level
import random


async def run_all_performance_benchmarks():
    """Run all performance benchmarks"""
    print("=== Batching Performance Benchmarks ===")
    print(f"System specs: {psutil.cpu_count()} CPU cores, {psutil.virtual_memory().total / (1024**3):.1f} GB RAM")
    
    benchmarker = BatchingPerformanceBenchmarks()
    
    # Run all benchmark categories
    throughput_results = await benchmarker.run_throughput_benchmarks()
    latency_results = await benchmarker.run_latency_benchmarks()
    cache_results = await benchmarker.run_cache_efficiency_benchmarks()
    resource_results = await benchmarker.run_resource_utilization_benchmarks()
    load_test_results = await benchmarker.run_concurrent_load_tests()
    scalability_results = await benchmarker.run_scalability_benchmarks()
    
    # Generate report
    report = benchmarker.generate_performance_report()
    
    print("\n=== Performance Benchmark Summary ===")
    print(f"Total benchmarks run: {len(benchmarker.benchmark_results)}")
    print(f"Total load tests: {len(benchmarker.load_test_results)}")
    print(f"Max throughput: {report['performance_summary']['max_throughput_rps']:.1f} requests/sec")
    print(f"Min P95 latency: {report['performance_summary']['min_latency_p95_ms']:.1f} ms")
    print(f"Max P95 latency: {report['performance_summary']['max_latency_p95_ms']:.1f} ms")
    print(f"Avg CPU usage: {report['performance_summary']['avg_cpu_usage_percent']:.1f}%")
    print(f"Avg memory usage: {report['performance_summary']['avg_memory_usage_mb']:.1f} MB")
    print(f"Max concurrent throughput: {report['load_test_analysis']['max_concurrent_rps']:.1f} requests/sec")
    
    # Prepare detailed results
    detailed_results = {
        'benchmark_metadata': {
            'timestamp': datetime.now().isoformat(),
            'system_specs': benchmarker.system_metrics,
            'total_benchmarks': len(benchmarker.benchmark_results),
            'total_load_tests': len(benchmarker.load_test_results)
        },
        'performance_report': report,
        'detailed_benchmarks': [
            {
                'name': r.benchmark_name,
                'total_requests': r.total_requests,
                'throughput_rps': r.throughput_rps,
                'latency_p50_ms': r.latency_p50_ms,
                'latency_p95_ms': r.latency_p95_ms,
                'latency_p99_ms': r.latency_p99_ms,
                'cpu_usage_percent': r.cpu_usage_percent,
                'memory_usage_mb': r.memory_usage_mb,
                'batch_utilization_percent': r.batch_utilization,
                'cache_hit_ratio': r.cache_hit_ratio,
                'error_rate_percent': r.error_rate_percent,
                'cost_efficiency': r.cost_efficiency,
                'resource_efficiency': r.resource_efficiency,
                'configuration': r.batch_configuration
            }
            for r in benchmarker.benchmark_results
        ],
        'detailed_load_tests': [
            {
                'concurrent_users': r.concurrent_users,
                'total_requests': r.total_requests,
                'successful_requests': r.successful_requests,
                'failed_requests': r.failed_requests,
                'total_time_seconds': r.total_time_seconds,
                'requests_per_second': r.requests_per_second,
                'error_rate_percent': r.error_rate_percent,
                'avg_response_time_ms': r.avg_response_time_ms,
                'p95_response_time_ms': r.p95_response_time_ms,
                'p99_response_time_ms': r.p99_response_time_ms
            }
            for r in benchmarker.load_test_results
        ]
    }
    
    return detailed_results


if __name__ == "__main__":
    # Install required packages if not available
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'matplotlib', 'numpy'])
        import matplotlib.pyplot as plt
        import numpy as np
    
    # Run benchmarks
    benchmark_data = asyncio.run(run_all_performance_benchmarks())
    
    # Save results
    with open('/workspace/tests/performance/benchmark_results.json', 'w') as f:
        json.dump(benchmark_data, f, indent=2, default=str)
    
    print(f"\nDetailed benchmark results saved to: /workspace/tests/performance/benchmark_results.json")