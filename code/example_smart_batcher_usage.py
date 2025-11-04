"""
Simple Example: Smart Batching System Usage

This example demonstrates the core functionality of the smart batching system
for API cost optimization in a production-ready scenario.
"""

import asyncio
import json
from datetime import datetime, timedelta
from smart_batcher import (
    ContentRequest, SmartBatcher, CacheManager, 
    SmartBatchingIntegration, PriorityQueue
)

async def example_basic_batching():
    """Demonstrate basic smart batching functionality"""
    print("🎬 Smart Batching System - Basic Example")
    print("=" * 50)
    
    # Initialize the system
    cache_manager = CacheManager(memory_size=100)
    batcher = SmartBatcher(
        max_batch_size=10,
        max_batch_cost=200.0,
        similarity_threshold=0.7,
        cache_manager=cache_manager
    )
    
    # Create sample video requests
    print("📋 Creating video generation requests...")
    requests = [
        ContentRequest(
            id=f"video_{i}",
            content_type="video",
            prompt=f"Professional office video {i}: workspace with laptop and coffee",
            resolution="1920x1080",
            duration=30.0,
            priority=2,  # Normal priority
            style_params={"video_style": "corporate_professional"}
        )
        for i in range(5)
    ]
    
    print(f"Created {len(requests)} video requests")
    
    # Add requests to the batching system
    print("\n🚀 Adding requests to smart batcher...")
    for request in requests:
        result = await batcher.add_request(request)
        print(f"  - {request.id}: {result}")
    
    # Build optimal batches
    print("\n📦 Building optimal batches...")
    batches = await batcher.build_optimal_batches()
    
    print(f"Created {len(batches)} batch(es):")
    for i, batch in enumerate(batches, 1):
        print(f"  Batch {i}:")
        print(f"    - Requests: {len(batch.requests)}")
        print(f"    - Total cost: ${batch.estimated_total_cost:.2f}")
        print(f"    - Similarity score: {batch.similarity_score:.2f}")
        print(f"    - Priority score: {batch.priority_score:.2f}")
    
    # Process batches
    print("\n⚙️ Processing batches...")
    for i, batch in enumerate(batches, 1):
        print(f"Processing batch {i}...")
        result = await batcher.process_batch(batch)
        print(f"  Status: {result['status']}")
        print(f"  Processing time: {result['processing_time']:.2f}s")
        print(f"  Cost efficiency: {result['cost_efficiency']:.2f}")
    
    # Get performance metrics
    print("\n📊 Performance Metrics:")
    metrics = batcher.get_performance_metrics()
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    return batches, metrics

async def example_cache_reuse():
    """Demonstrate cache reuse for repeated content"""
    print("\n" + "=" * 50)
    print("💾 Cache Reuse Example")
    print("=" * 50)
    
    cache_manager = CacheManager(memory_size=100)
    batcher = SmartBatcher(cache_manager=cache_manager)
    
    # Create original request
    original_request = ContentRequest(
        id="original_video",
        content_type="video",
        prompt="Modern office workspace with laptop and plants",
        resolution="1920x1080",
        duration=30.0
    )
    
    # Simulate storing result in cache
    mock_result = {
        "file_path": "cached/office_workspace.mp4",
        "quality_score": 8.5,
        "generation_time": 45.2
    }
    cache_manager.set(original_request, mock_result)
    print(f"📁 Stored result in cache: {original_request.id}")
    
    # Create near-duplicate request
    duplicate_request = ContentRequest(
        id="duplicate_video",
        content_type="video",
        prompt="Modern office workspace with laptop and plants",  # Identical prompt
        resolution="1920x1080",
        duration=30.0
    )
    
    # Check cache for duplicate
    cached_result = cache_manager.get(duplicate_request)
    is_duplicate = cache_manager.is_near_duplicate(duplicate_request)
    
    print(f"🔍 Duplicate detection:")
    print(f"  Original: {original_request.id}")
    print(f"  Duplicate: {duplicate_request.id}")
    print(f"  Cache hit: {'✅ Yes' if cached_result else '❌ No'}")
    print(f"  Near-duplicate: {'✅ Yes' if is_duplicate else '❌ No'}")
    
    if cached_result:
        cost_saved = duplicate_request.estimated_cost
        print(f"  💰 Cost saved: ${cost_saved:.2f}")
        print(f"  📈 Quality score: {cached_result['quality_score']}")
    
    return cached_result is not None

async def example_priority_scheduling():
    """Demonstrate priority-based scheduling"""
    print("\n" + "=" * 50)
    print("⏰ Priority Scheduling Example")
    print("=" * 50)
    
    priority_queue = PriorityQueue(budget_threshold=0.8)
    
    # Create batches with different priorities
    urgent_batch_content = ContentRequest(
        id="urgent_req",
        content_type="video",
        prompt="Urgent product launch video",
        priority=1,  # High priority
        estimated_cost=75.0
    )
    
    normal_batch_content = [
        ContentRequest(
            id=f"normal_req_{i}",
            content_type="video",
            prompt=f"Tutorial video {i+1}",
            priority=2,  # Normal priority
            estimated_cost=50.0
        ) for i in range(2)
    ]
    
    background_batch_content = [
        ContentRequest(
            id=f"bg_req_{i}",
            content_type="video",
            prompt=f"Background content {i+1}",
            priority=3,  # Low priority
            estimated_cost=25.0
        ) for i in range(3)
    ]
    
    # Create batches
    batches = [
        ("urgent", [urgent_batch_content]),
        ("normal", normal_batch_content),
        ("background", background_batch_content)
    ]
    
    for batch_type, requests in batches:
        batch_id = f"{batch_type}_batch"
        from smart_batcher import Batch
        batch = Batch(
            id=batch_id,
            requests=requests,
            max_size=10,
            max_cost=200.0,
            max_duration=60.0,
            engine="default",
            resolution="1920x1080"
        )
        priority_queue.enqueue(batch)
        avg_priority = sum(req.priority for req in requests) / len(requests)
        print(f"  Added {batch_type} batch: {len(requests)} requests, avg priority {avg_priority:.1f}")
    
    # Process in priority order
    print("\n⏱️ Processing order (by priority):")
    processed = []
    while priority_queue.queue:
        batch = priority_queue.dequeue()
        if batch:
            processed.append(batch)
            avg_priority = sum(req.priority for req in batch.requests) / len(batch.requests)
            print(f"  {batch.id}: Priority {avg_priority:.1f}, Cost ${batch.estimated_total_cost:.2f}")
    
    return processed

async def example_cost_analysis():
    """Demonstrate cost-benefit analysis"""
    print("\n" + "=" * 50)
    print("💰 Cost-Benefit Analysis Example")
    print("=" * 50)
    
    batcher = SmartBatcher()
    
    # Create a batch for analysis
    requests = [
        ContentRequest(
            id=f"analysis_req_{i}",
            content_type="video",
            prompt=f"Cost analysis video {i+1}",
            duration=30.0 + i * 10,
            estimated_cost=30.0 + i * 5
        ) for i in range(4)
    ]
    
    from smart_batcher import Batch
    batch = Batch(
        id="cost_analysis_batch",
        requests=requests,
        max_size=10,
        max_cost=200.0,
        max_duration=120.0,
        engine="default",
        resolution="1920x1080"
    )
    
    # Get cost-benefit analysis
    analysis = batcher.get_cost_benefit_analysis(batch)
    
    print("📊 Cost Analysis Results:")
    print(f"  Individual processing cost: ${analysis['individual_cost']:.2f}")
    print(f"  Batched processing cost: ${analysis['batch_cost']:.2f}")
    print(f"  Direct savings: ${analysis['direct_savings']:.2f}")
    print(f"  Throughput improvement: {analysis['throughput_improvement']:.1f}x")
    print(f"  Resource efficiency: {analysis['resource_efficiency']:.2f}")
    print(f"  Benefit ratio: {analysis['benefit_ratio']:.2f}")
    print(f"  Risk assessment: {analysis['risk_assessment']}")
    print(f"  📋 Recommendation: {analysis['recommendation']}")
    
    return analysis

async def main():
    """Run all examples"""
    print("🚀 Smart Batching System - Complete Examples")
    print("=" * 60)
    
    # Run all example scenarios
    examples = [
        ("Basic Batching", example_basic_batching),
        ("Cache Reuse", example_cache_reuse),
        ("Priority Scheduling", example_priority_scheduling),
        ("Cost Analysis", example_cost_analysis)
    ]
    
    results = {}
    for name, example_func in examples:
        try:
            result = await example_func()
            results[name] = {"status": "success", "result": result}
            print(f"✅ {name} completed successfully")
        except Exception as e:
            results[name] = {"status": "failed", "error": str(e)}
            print(f"❌ {name} failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 EXAMPLE SUMMARY")
    print("=" * 60)
    successful = sum(1 for r in results.values() if r["status"] == "success")
    total = len(results)
    print(f"Examples completed: {successful}/{total}")
    
    if successful == total:
        print("🎉 All examples ran successfully!")
        print("💡 Smart batching system is working correctly")
    else:
        print("⚠️ Some examples failed - check the output above")
    
    # Save results
    with open('/workspace/code/example_results.json', 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "examples": results,
            "status": "completed" if successful == total else "partial"
        }, f, indent=2, default=str)
    
    print(f"\n📄 Results saved to: /workspace/code/example_results.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())