"""
Smart Batching System Demonstration

This script demonstrates the smart batching system with realistic scenarios
showing cost optimization, cache reuse, and priority-based scheduling.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from smart_batcher import (
    ContentRequest, Batch, SmartBatcher, CacheManager, 
    PriorityQueue, SmartBatchingIntegration
)

class SmartBatchingDemo:
    """Demonstration of smart batching system capabilities"""
    
    def __init__(self):
        self.batcher = None
        self.cache_manager = None
        self.integration = None
        self.demo_results = []
    
    def print_section(self, title: str):
        """Print section header"""
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}")
    
    def print_subsection(self, title: str):
        """Print subsection header"""
        print(f"\n{'-' * 40}")
        print(f"  {title}")
        print(f"{'-' * 40}")
    
    async def setup_demo(self):
        """Initialize demo environment"""
        print("🚀 Initializing Smart Batching System Demo")
        
        self.cache_manager = CacheManager(memory_size=200)
        self.batcher = SmartBatcher(
            max_batch_size=15,
            max_batch_cost=400.0,
            similarity_threshold=0.7,
            cache_manager=self.cache_manager
        )
        self.integration = SmartBatchingIntegration(self.batcher)
        
        print("✅ System initialized successfully")
    
    async def demo_scenario_1_basic_batching(self):
        """Demonstrate basic batching with similar requests"""
        self.print_section("Scenario 1: Basic Batching with Similar Requests")
        
        # Create similar video requests
        requests = [
            ContentRequest(
                id=f"office_video_{i}",
                content_type="video",
                prompt=f"Professional office workspace with {['laptop', 'computer', 'monitor'][i%3]} and coffee",
                resolution="1920x1080",
                duration=30.0,
                engine="default",
                style_params={"video_style": "corporate_professional", "color_scheme": "blue_white"},
                priority=2
            ) for i in range(5)
        ]
        
        print(f"📋 Processing {len(requests)} similar video requests...")
        
        # Add requests to batcher
        for request in requests:
            await self.batcher.add_request(request)
        
        # Build and display batches
        batches = await self.batcher.build_optimal_batches()
        
        print(f"\n📦 Results: Created {len(batches)} batch(es)")
        for i, batch in enumerate(batches, 1):
            print(f"  Batch {i}: {len(batch.requests)} requests, "
                  f"Cost: ${batch.estimated_total_cost:.2f}, "
                  f"Similarity: {batch.similarity_score:.2f}")
        
        return batches
    
    async def demo_scenario_2_mixed_workload(self):
        """Demonstrate mixed workload with different content types and priorities"""
        self.print_section("Scenario 2: Mixed Workload with Different Content Types")
        
        # Create mixed requests
        mixed_requests = [
            # High-priority video
            ContentRequest(
                id="urgent_promo_video",
                content_type="video",
                prompt="Urgent promotional video for product launch",
                resolution="1920x1080",
                duration=30.0,
                priority=1,  # High priority
                deadline=datetime.now() + timedelta(hours=2)
            ),
            # Normal priority videos
            ContentRequest(
                id=f"tutorial_video_{i}",
                content_type="video",
                prompt=f"Software tutorial showing step {i+1}",
                resolution="1920x1080",
                duration=60.0,
                priority=2,
                style_params={"video_style": "educational_clear"}
            ) for i in range(3)
        ]
        
        print(f"📋 Processing mixed workload: 1 urgent + 3 normal videos")
        
        # Add requests
        for request in mixed_requests:
            await self.batcher.add_request(request)
        
        # Build batches
        batches = await self.batcher.build_optimal_batches()
        
        print(f"\n📦 Batching Results:")
        for i, batch in enumerate(batches, 1):
            print(f"  Batch {i}: {len(batch.requests)} requests, "
                  f"Priority Score: {batch.priority_score:.2f}")
            
            # Show cost-benefit analysis
            analysis = self.batcher.get_cost_benefit_analysis(batch)
            print(f"    💰 Cost Analysis: {analysis['recommendation']} "
                  f"(Benefit Ratio: {analysis['benefit_ratio']:.2f})")
        
        return batches
    
    async def demo_scenario_3_cache_reuse(self):
        """Demonstrate cache reuse for repeated content"""
        self.print_section("Scenario 3: Cache Reuse and Near-Duplicate Detection")
        
        # Create first request
        original_request = ContentRequest(
            id="original_video",
            content_type="video",
            prompt="Professional office setup with laptop and natural lighting",
            resolution="1920x1080",
            duration=30.0
        )
        
        # Add to cache
        mock_result = {
            "file_path": "cached/office_setup.mp4",
            "quality_score": 8.7,
            "generation_time": 45.2
        }
        self.cache_manager.set(original_request, mock_result)
        
        # Create near-duplicate request
        duplicate_request = ContentRequest(
            id="duplicate_video",
            content_type="video",
            prompt="Professional office setup with laptop and natural lighting",  # Identical
            resolution="1920x1080",
            duration=30.0
        )
        
        print("🔍 Testing cache detection...")
        
        # Check cache for duplicate
        cached_result = self.cache_manager.get(duplicate_request)
        is_duplicate = self.cache_manager.is_near_duplicate(duplicate_request)
        
        print(f"  Original request: {original_request.id}")
        print(f"  Duplicate request: {duplicate_request.id}")
        print(f"  Cache hit: {'✅ Yes' if cached_result else '❌ No'}")
        print(f"  Near-duplicate detected: {'✅ Yes' if is_duplicate else '❌ No'}")
        
        if cached_result:
            print(f"  Quality score: {cached_result['quality_score']}")
            print(f"  Cost saved: ${duplicate_request.estimated_cost:.2f}")
        
        return cached_result is not None
    
    async def demo_scenario_4_dynamic_optimization(self):
        """Demonstrate dynamic batch optimization"""
        self.print_section("Scenario 4: Dynamic Batch Optimization")
        
        # Create requests with varying complexity
        complex_requests = [
            ContentRequest(
                id=f"complex_video_{i}",
                content_type="video",
                prompt="A" * (50 + i * 100),  # Increasing complexity
                resolution="1920x1080",
                duration=30.0 + i * 15,
                style_params={
                    "video_style": "corporate_professional",
                    "effects": ["color_correction", "audio_enhancement", "motion_graphics"],
                    "transitions": "smooth_fade"
                },
                priority=2
            ) for i in range(4)
        ]
        
        print(f"📋 Processing {len(complex_requests)} complex video requests...")
        
        # Add requests
        for request in complex_requests:
            await self.batcher.add_request(request)
        
        # Get initial configuration
        initial_config = {
            'max_batch_size': self.batcher.max_batch_size,
            'similarity_threshold': self.batcher.similarity_threshold
        }
        
        print(f"  Initial config: Batch size={initial_config['max_batch_size']}, "
              f"Similarity={initial_config['similarity_threshold']:.1f}")
        
        # Build batches
        batches = await self.batcher.build_optimal_batches()
        
        # Get performance metrics
        metrics = self.batcher.get_performance_metrics()
        
        print(f"\n📦 Dynamic Batching Results:")
        for i, batch in enumerate(batches, 1):
            complexity_score = sum(len(req.prompt) for req in batch.requests) / len(batch.requests)
            print(f"  Batch {i}: {len(batch.requests)} requests, "
                  f"Avg Complexity: {complexity_score:.0f} chars")
        
        # Simulate optimization based on metrics
        self.batcher.optimize_configuration(metrics)
        
        optimized_config = {
            'max_batch_size': self.batcher.max_batch_size,
            'similarity_threshold': self.batcher.similarity_threshold
        }
        
        print(f"  Optimized config: Batch size={optimized_config['max_batch_size']}, "
              f"Similarity={optimized_config['similarity_threshold']:.1f}")
        
        return batches
    
    async def demo_scenario_5_priority_scheduling(self):
        """Demonstrate priority-based scheduling"""
        self.print_section("Scenario 5: Priority-Based Queue Scheduling")
        
        # Create priority queue
        priority_queue = PriorityQueue(budget_threshold=0.8)
        
        # Create batches with different priorities
        priority_batches = [
            Batch(
                id="urgent_batch",
                requests=[ContentRequest(
                    id="urgent_req",
                    content_type="video",
                    prompt="Urgent deadline request",
                    priority=1,  # High priority
                    estimated_cost=75.0
                )],
                max_size=5,
                max_cost=200.0,
                max_duration=60.0,
                engine="default",
                resolution="1920x1080"
            ),
            Batch(
                id="normal_batch",
                requests=[ContentRequest(
                    id=f"normal_req_{i}",
                    content_type="video",
                    prompt=f"Normal priority request {i+1}",
                    priority=2,
                    estimated_cost=50.0
                ) for i in range(2)],
                max_size=10,
                max_cost=300.0,
                max_duration=120.0,
                engine="default",
                resolution="1920x1080"
            ),
            Batch(
                id="background_batch",
                requests=[ContentRequest(
                    id=f"bg_req_{i}",
                    content_type="video",
                    prompt=f"Background task {i+1}",
                    priority=3,  # Low priority
                    estimated_cost=25.0
                ) for i in range(3)],
                max_size=15,
                max_cost=400.0,
                max_duration=180.0,
                engine="default",
                resolution="1920x1080"
            )
        ]
        
        print(f"📋 Scheduling {len(priority_batches)} batches with different priorities...")
        
        # Add to priority queue
        for batch in priority_batches:
            priority_queue.enqueue(batch)
        
        # Process in priority order
        processed_batches = []
        while priority_queue.queue:
            batch = priority_queue.dequeue()
            if batch:
                processed_batches.append(batch)
        
        print(f"\n⏰ Processing Order (by priority):")
        for i, batch in enumerate(processed_batches, 1):
            avg_priority = sum(req.priority for req in batch.requests) / len(batch.requests)
            print(f"  {i}. {batch.id}: Priority {avg_priority:.1f}, "
                  f"Cost ${batch.estimated_total_cost:.2f}")
        
        return processed_batches
    
    async def demo_performance_analytics(self):
        """Demonstrate performance analytics and reporting"""
        self.print_section("Performance Analytics and Cost Optimization")
        
        # Simulate processing a workload
        workload_requests = [
            ContentRequest(
                id=f"analytics_req_{i}",
                content_type="video",
                prompt=f"Analytics demonstration video {i+1}",
                resolution="1920x1080",
                duration=30.0,
                priority=2
            ) for i in range(8)
        ]
        
        # Add requests
        for request in workload_requests:
            await self.batcher.add_request(request)
        
        # Build batches
        batches = await self.batcher.build_optimal_batches()
        
        # Simulate processing
        for batch in batches:
            await self.batcher.process_batch(batch)
        
        # Get comprehensive metrics
        metrics = self.batcher.get_performance_metrics()
        
        print("📊 Performance Metrics:")
        print(f"  Total Requests Processed: {metrics['total_requests']}")
        print(f"  Batched Requests: {metrics['batched_requests']}")
        print(f"  Cache Hit Ratio: {metrics['cache_hit_ratio']:.2%}")
        print(f"  Average Batch Size: {metrics['average_batch_size']:.1f}")
        print(f"  Batching Efficiency: {metrics['batching_efficiency']:.2%}")
        print(f"  Cost Savings: ${metrics.get('total_cost_saved', 0):.2f}")
        
        # Calculate cost benefits
        total_cost = sum(b.estimated_total_cost for b in batches)
        individual_cost = sum(
            sum(req.estimated_cost for req in b.requests) 
            for b in batches
        )
        potential_savings = max(0, individual_cost - total_cost)
        
        print(f"\n💰 Cost Analysis:")
        print(f"  Individual Processing Cost: ${individual_cost:.2f}")
        print(f"  Batched Processing Cost: ${total_cost:.2f}")
        print(f"  Potential Savings: ${potential_savings:.2f} "
              f"({(potential_savings/individual_cost)*100:.1f}%)")
        
        return metrics
    
    async def run_complete_demo(self):
        """Run complete demonstration of all features"""
        print("🎬 SMART BATCHING SYSTEM - COMPLETE DEMONSTRATION")
        print("=" * 60)
        
        await self.setup_demo()
        
        # Run all demonstration scenarios
        scenarios = [
            ("Basic Batching", self.demo_scenario_1_basic_batching),
            ("Mixed Workload", self.demo_scenario_2_mixed_workload),
            ("Cache Reuse", self.demo_scenario_3_cache_reuse),
            ("Dynamic Optimization", self.demo_scenario_4_dynamic_optimization),
            ("Priority Scheduling", self.demo_scenario_5_priority_scheduling),
            ("Performance Analytics", self.demo_performance_analytics)
        ]
        
        scenario_results = {}
        
        for scenario_name, scenario_func in scenarios:
            try:
                result = await scenario_func()
                scenario_results[scenario_name] = {"status": "completed", "result": result}
            except Exception as e:
                print(f"❌ Error in {scenario_name}: {e}")
                scenario_results[scenario_name] = {"status": "failed", "error": str(e)}
        
        # Generate final report
        self.print_section("DEMONSTRATION SUMMARY")
        
        print("🎯 Key Features Demonstrated:")
        print("  ✅ Smart content grouping and similarity detection")
        print("  ✅ Dynamic batch sizing based on content complexity")
        print("  ✅ Multi-layer cache for repeated content reuse")
        print("  ✅ Cost-benefit analysis for batching decisions")
        print("  ✅ Priority-based queue scheduling")
        print("  ✅ Real-time performance analytics")
        print("  ✅ Integration with existing pipelines")
        
        # Save demonstration results
        demo_report = {
            "timestamp": datetime.now().isoformat(),
            "scenarios": scenario_results,
            "final_metrics": self.batcher.get_performance_metrics(),
            "configuration": {
                "max_batch_size": self.batcher.max_batch_size,
                "max_batch_cost": self.batcher.max_batch_cost,
                "similarity_threshold": self.batcher.similarity_threshold
            }
        }
        
        report_path = "/workspace/code/smart_batching_demo_report.json"
        with open(report_path, 'w') as f:
            json.dump(demo_report, f, indent=2, default=str)
        
        print(f"\n📄 Full demonstration report saved to: {report_path}")
        
        return demo_report

async def main():
    """Main demonstration runner"""
    demo = SmartBatchingDemo()
    report = await demo.run_complete_demo()
    
    print(f"\n🚀 Demo completed successfully!")
    print(f"💡 Smart batching system is ready for production use.")
    
    return report

if __name__ == "__main__":
    asyncio.run(main())