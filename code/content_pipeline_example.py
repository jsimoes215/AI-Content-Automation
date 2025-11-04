"""
Integration Example: Parallel Generator with Content Pipeline

This example demonstrates how to integrate the parallel generator with
existing content generation systems, including Google Sheets workflow.
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any

# Import existing pipeline components
from google_sheets_client import GoogleSheetsClient
from parallel_generator import (
    ParallelGenerator,
    create_audio_request,
    create_video_request,
    TaskPriority,
    Provider,
    GenerationType,
    RateLimitConfig,
    BatchingConfig,
    ResourcePoolConfig
)


class ContentPipeline:
    """
    Main content pipeline that orchestrates:
    1. Loading requests from data sources (Google Sheets, APIs, etc.)
    2. Processing with parallel generator
    3. Saving results back to data sources
    """
    
    def __init__(self, sheets_config: Dict[str, Any] = None, generator_config: Dict[str, Any] = None):
        # Initialize Google Sheets client
        self.sheets_client = GoogleSheetsClient(**(sheets_config or {}))
        
        # Initialize parallel generator with optimized config
        generator_config = generator_config or {}
        
        # Configure for production workload
        rate_config = RateLimitConfig(
            per_user_requests_per_minute=generator_config.get('per_user_limit', 50),
            per_project_requests_per_minute=generator_config.get('per_project_limit', 200),
            token_bucket_capacity=generator_config.get('token_bucket_capacity', 200)
        )
        
        batch_config = BatchingConfig(
            max_jobs_per_batch=generator_config.get('max_batch_size', 20),
            max_total_cost_per_batch=generator_config.get('max_batch_cost', 200.0),
            similarity_threshold=generator_config.get('similarity_threshold', 0.75)
        )
        
        resource_config = ResourcePoolConfig(
            max_api_calls=generator_config.get('max_api_calls', 75),
            max_concurrent_jobs=generator_config.get('max_concurrent_jobs', 30)
        )
        
        self.generator = ParallelGenerator(
            rate_limit_config=rate_config,
            batching_config=batch_config,
            resource_config=resource_config
        )
        
        # Pipeline state
        self.processed_count = 0
        self.error_count = 0
        self.total_cost = 0.0
        
        logger.info("ContentPipeline initialized with parallel generator")
    
    async def start(self) -> None:
        """Start the content pipeline"""
        await self.generator.start()
        logger.info("Content pipeline started")
    
    async def stop(self) -> None:
        """Stop the content pipeline"""
        await self.generator.stop()
        logger.info("Content pipeline stopped")
    
    async def process_content_requests(self, 
                                     source_type: str = "sheets",
                                     source_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process content requests from various sources
        
        Args:
            source_type: Type of source ('sheets', 'api', 'database')
            source_config: Source-specific configuration
        
        Returns:
            Processing summary with statistics
        """
        logger.info(f"Processing content requests from {source_type}")
        
        try:
            # Load requests based on source type
            if source_type == "sheets":
                requests = await self._load_from_sheets(source_config)
            elif source_type == "api":
                requests = await self._load_from_api(source_config)
            elif source_type == "database":
                requests = await self._load_from_database(source_config)
            else:
                raise ValueError(f"Unsupported source type: {source_type}")
            
            if not requests:
                return {"status": "no_requests", "message": "No content requests found"}
            
            logger.info(f"Loaded {len(requests)} content requests")
            
            # Process with parallel generator
            results = await self.generator.generate(requests)
            
            # Update results back to source
            await self._update_source_results(source_type, source_config, requests, results)
            
            # Generate summary
            summary = self._generate_processing_summary(requests, results)
            
            logger.info(f"Processing completed: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _load_from_sheets(self, config: Dict[str, Any] = None) -> List:
        """Load content requests from Google Sheets"""
        try:
            # Default sheet configuration
            sheets_config = {
                "spreadsheet_id": config.get("spreadsheet_id") if config else None,
                "requests_range": config.get("requests_range", "Content_Requests!A:H"),
                "results_range": config.get("results_range", "Content_Results!A:J")
            }
            
            # Load requests from sheets
            requests_data = await self.sheets_client.get_generation_requests(
                range_name=sheets_config["requests_range"]
            )
            
            # Convert to generation requests
            requests = []
            for item in requests_data:
                try:
                    # Map sheet data to generation request
                    if item.get("type", "").lower() == "audio":
                        request = create_audio_request(
                            prompt=item.get("prompt", ""),
                            provider=self._map_provider(item.get("provider", "minimax")),
                            priority=self._map_priority(item.get("priority", "normal")),
                            duration=float(item.get("duration", 30)),
                            quality=item.get("quality", "standard"),
                            user_id=item.get("user_id"),
                            project_id=item.get("project_id")
                        )
                        requests.append(request)
                    
                    elif item.get("type", "").lower() == "video":
                        request = create_video_request(
                            prompt=item.get("prompt", ""),
                            provider=self._map_provider(item.get("provider", "minimax")),
                            priority=self._map_priority(item.get("priority", "normal")),
                            duration=float(item.get("duration", 60)),
                            resolution=item.get("resolution", "1080p"),
                            style=item.get("style", "standard"),
                            user_id=item.get("user_id"),
                            project_id=item.get("project_id")
                        )
                        requests.append(request)
                
                except Exception as e:
                    logger.warning(f"Failed to process request item {item}: {e}")
                    continue
            
            logger.info(f"Loaded {len(requests)} valid requests from sheets")
            return requests
            
        except Exception as e:
            logger.error(f"Failed to load from sheets: {e}")
            return []
    
    async def _load_from_api(self, config: Dict[str, Any] = None) -> List:
        """Load content requests from API endpoints"""
        # This would implement loading from REST APIs
        # For now, return empty list as placeholder
        logger.info("API loading not implemented in this example")
        return []
    
    async def _load_from_database(self, config: Dict[str, Any] = None) -> List:
        """Load content requests from database"""
        # This would implement loading from databases
        # For now, return empty list as placeholder
        logger.info("Database loading not implemented in this example")
        return []
    
    async def _update_source_results(self, source_type: str, source_config: Dict, 
                                   requests: List, results: List) -> None:
        """Update results back to the source system"""
        try:
            if source_type == "sheets":
                await self._update_sheets_results(source_config, requests, results)
            elif source_type == "api":
                await self._update_api_results(source_config, requests, results)
            elif source_type == "database":
                await self._update_database_results(source_config, requests, results)
        
        except Exception as e:
            logger.error(f"Failed to update results to {source_type}: {e}")
    
    async def _update_sheets_results(self, config: Dict, requests: List, results: List) -> None:
        """Update results to Google Sheets"""
        try:
            results_data = []
            
            for i, (request, result) in enumerate(zip(requests, results)):
                # Create result row
                result_row = {
                    "request_id": request.id,
                    "type": request.type.value,
                    "prompt": request.prompt,
                    "success": result.success,
                    "output_path": result.output_path or "",
                    "actual_cost": result.actual_cost,
                    "duration": result.duration,
                    "error": result.error or "",
                    "provider": request.provider.value,
                    "processed_at": datetime.utcnow().isoformat()
                }
                results_data.append(result_row)
            
            # Update sheets with results
            await self.sheets_client.update_generation_results(
                results_data,
                range_name=config.get("results_range", "Content_Results!A:J")
            )
            
            logger.info(f"Updated {len(results_data)} results to sheets")
            
        except Exception as e:
            logger.error(f"Failed to update sheets results: {e}")
    
    async def _update_api_results(self, config: Dict, requests: List, results: List) -> None:
        """Update results to API endpoints"""
        # Placeholder for API updates
        logger.info("API result updates not implemented")
    
    async def _update_database_results(self, config: Dict, requests: List, results: List) -> None:
        """Update results to database"""
        # Placeholder for database updates
        logger.info("Database result updates not implemented")
    
    def _map_provider(self, provider_str: str) -> Provider:
        """Map provider string to Provider enum"""
        mapping = {
            "minimax": Provider.MINIMAX,
            "runway": Provider.RUNWAY,
            "azure": Provider.AZURE,
            "aws": Provider.AWS
        }
        return mapping.get(provider_str.lower(), Provider.MINIMAX)
    
    def _map_priority(self, priority_str: str) -> TaskPriority:
        """Map priority string to TaskPriority enum"""
        mapping = {
            "urgent": TaskPriority.URGENT,
            "high": TaskPriority.HIGH,
            "normal": TaskPriority.NORMAL,
            "low": TaskPriority.LOW,
            "background": TaskPriority.BACKGROUND
        }
        return mapping.get(priority_str.lower(), TaskPriority.NORMAL)
    
    def _generate_processing_summary(self, requests: List, results: List) -> Dict[str, Any]:
        """Generate processing summary statistics"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        # Count by type
        audio_count = len([r for r in requests if r.type == GenerationType.AUDIO])
        video_count = len([r for r in requests if r.type == GenerationType.VIDEO])
        
        # Count by priority
        priority_counts = {}
        for req in requests:
            priority_counts[req.priority] = priority_counts.get(req.priority, 0) + 1
        
        # Cost analysis
        total_cost = sum(r.actual_cost for r in successful)
        avg_cost_per_item = total_cost / len(successful) if successful else 0
        
        # Get system stats
        system_stats = asyncio.create_task(self.generator.get_system_stats())
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_requests": len(requests),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results) if results else 0,
            "audio_requests": audio_count,
            "video_requests": video_count,
            "priority_breakdown": {p.name: count for p, count in priority_counts.items()},
            "total_cost": total_cost,
            "average_cost": avg_cost_per_item,
            "processing_time": "N/A",  # Would be calculated if needed
            "system_stats": system_stats  # Async task for system stats
        }


# Example usage and demonstration
async def example_content_pipeline():
    """Example of using the content pipeline"""
    
    print("🎬 Content Pipeline with Parallel Generator")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline = ContentPipeline()
    await pipeline.start()
    
    try:
        print("\n📋 Processing content from Google Sheets...")
        
        # Example sheet configuration (would be real in production)
        sheets_config = {
            "requests_range": "Content_Requests!A:H",
            "results_range": "Content_Results!A:J"
        }
        
        # Process content requests
        summary = await pipeline.process_content_requests(
            source_type="sheets",
            source_config=sheets_config
        )
        
        # Display results
        print(f"\n✅ Processing completed!")
        print(f"   📊 Total requests: {summary.get('total_requests', 0)}")
        print(f"   ✅ Successful: {summary.get('successful', 0)}")
        print(f"   ❌ Failed: {summary.get('failed', 0)}")
        print(f"   📈 Success rate: {summary.get('success_rate', 0):.1%}")
        print(f"   💰 Total cost: ${summary.get('total_cost', 0):.2f}")
        
        if summary.get('priority_breakdown'):
            print(f"\n🎯 Priority breakdown:")
            for priority, count in summary['priority_breakdown'].items():
                print(f"   • {priority}: {count} requests")
        
        if summary.get('audio_requests', 0) > 0 or summary.get('video_requests', 0) > 0:
            print(f"\n🎵 Content type breakdown:")
            print(f"   • Audio: {summary.get('audio_requests', 0)} requests")
            print(f"   • Video: {summary.get('video_requests', 0)} requests")
        
        print(f"\n🔧 System performance:")
        system_stats = await summary['system_stats']
        
        # Resource utilization
        resource_stats = system_stats.get('resource_pool', {})
        if 'utilization_percentages' in resource_stats:
            print(f"   🔧 Resource utilization:")
            for resource, utilization in resource_stats['utilization_percentages'].items():
                print(f"      • {resource}: {utilization:.1f}%")
        
        # Cache performance
        cache_stats = system_stats.get('cache', {})
        if 'hit_ratio_percent' in cache_stats:
            print(f"   🗄️  Cache hit ratio: {cache_stats['hit_ratio_percent']:.1f}%")
        
        # Provider health
        load_stats = system_stats.get('load_balancer', {})
        if 'provider_health' in load_stats:
            print(f"   ⚖️  Provider health:")
            for provider, healthy in load_stats['provider_health'].items():
                status = "✅" if healthy else "❌"
                print(f"      • {provider}: {status}")
        
        print(f"\n🎉 Content pipeline processing completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Pipeline processing failed: {e}")
    
    finally:
        await pipeline.stop()


# Production configuration example
def get_production_config() -> Dict[str, Any]:
    """Get production-ready configuration"""
    
    return {
        # Google Sheets configuration
        "sheets_config": {
            "spreadsheet_id": "your_production_spreadsheet_id",
            "requests_range": "Production_Requests!A:H",
            "results_range": "Production_Results!A:J"
        },
        
        # Parallel generator configuration
        "generator_config": {
            # Rate limiting (tuned for production)
            "per_user_limit": 45,          # Conservative per-user limit
            "per_project_limit": 180,      # Conservative project limit
            "token_bucket_capacity": 180,  # Match project limit
            
            # Batching (optimized for cost)
            "max_batch_size": 18,          # Leave headroom
            "max_batch_cost": 180.0,       # Match project limit
            "similarity_threshold": 0.8,   # High similarity requirement
            
            # Resource management
            "max_api_calls": 60,           # Conservative API usage
            "max_concurrent_jobs": 25      # Reasonable concurrency
        }
    }


# Monitoring and alerting setup
class PipelineMonitor:
    """Monitor pipeline performance and health"""
    
    def __init__(self, pipeline: ContentPipeline):
        self.pipeline = pipeline
        self.alerts = []
    
    async def check_health(self) -> Dict[str, Any]:
        """Check pipeline health"""
        try:
            stats = await self.pipeline.generator.get_system_stats()
            
            # Check various health metrics
            health_checks = {
                "generator_running": self.pipeline.generator.running,
                "cache_performance": stats['cache']['hit_ratio_percent'] > 50,
                "resource_health": all(
                    util < 90 for util in stats['resource_pool']['utilization_percentages'].values()
                ),
                "cost_within_budget": stats['cost_monitor']['current_spend'] < 100.0,
                "provider_health": any(stats['load_balancer']['provider_health'].values())
            }
            
            overall_health = all(health_checks.values())
            
            return {
                "overall_health": overall_health,
                "checks": health_checks,
                "stats": stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "overall_health": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def add_alert(self, alert_type: str, message: str, severity: str = "info"):
        """Add alert to monitoring system"""
        self.alerts.append({
            "type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.warning(f"Alert [{severity.upper()}] {alert_type}: {message}")


# Main entry point
async def main():
    """Main entry point for content pipeline"""
    
    print("🎬 Content Pipeline with Parallel Generator")
    print("=" * 50)
    
    # Get production configuration
    config = get_production_config()
    
    # Initialize pipeline with production config
    pipeline = ContentPipeline(
        sheets_config=config["sheets_config"],
        generator_config=config["generator_config"]
    )
    
    # Initialize monitoring
    monitor = PipelineMonitor(pipeline)
    
    # Start pipeline
    await pipeline.start()
    
    try:
        # Check initial health
        health = await monitor.check_health()
        print(f"\n🏥 Initial health check: {'✅ Healthy' if health['overall_health'] else '❌ Unhealthy'}")
        
        if not health['overall_health']:
            print("⚠️  Pipeline health issues detected:")
            for check, status in health['checks'].items():
                if not status:
                    print(f"   ❌ {check}: Failed")
        
        # Process content (example)
        summary = await pipeline.process_content_requests(
            source_type="sheets",
            source_config=config["sheets_config"]
        )
        
        # Final health check
        final_health = await monitor.check_health()
        print(f"\n🏥 Final health check: {'✅ Healthy' if final_health['overall_health'] else '❌ Unhealthy'}")
        
        # Display alerts if any
        if monitor.alerts:
            print(f"\n🚨 Alerts ({len(monitor.alerts)}):")
            for alert in monitor.alerts:
                print(f"   [{alert['severity'].upper()}] {alert['type']}: {alert['message']}")
        
        print(f"\n🎉 Pipeline execution completed!")
        
    except Exception as e:
        monitor.add_alert("PIPELINE_ERROR", str(e), "critical")
        print(f"\n❌ Pipeline execution failed: {e}")
    
    finally:
        await pipeline.stop()


if __name__ == "__main__":
    # Run the example
    asyncio.run(example_content_pipeline())
    
    print(f"\n" + "="*50)
    print(f"🚀 For production use, run: python content_pipeline_example.py main")
    print(f"📚 See README_parallel_generator.md for full documentation")
    print(f"🧪 Run tests: python test_parallel_generator.py")