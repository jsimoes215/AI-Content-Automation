"""
Cost optimization tests for smart batching and cost algorithms.

This module tests:
- Smart batching algorithms
- Cost estimation models
- Rate limiting cost optimization
- Resource allocation strategies
- Parallel processing cost analysis
- Quality vs cost trade-offs

Author: AI Content Automation System
Version: 1.0.0
"""

import asyncio
import math
import time
import uuid
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, patch, AsyncMock

import pytest
import numpy as np

# Import system components
from parallel_generator import (
    ParallelGenerator, GenerationRequest, GenerationType, Provider,
    TaskPriority, ResourcePool, ResourceType
)
from batch_processor import (
    BatchProcessor, RateLimiter, VideoJob, JobPriority
)
from data_validation import DataValidationPipeline, ValidationResult


class TestCostOptimizationAlgorithms:
    """Test cost optimization algorithms and smart batching."""
    
    def test_cost_estimation_accuracy(self, data_validator):
        """Test accuracy of cost estimation algorithms."""
        
        # Test data with known cost characteristics
        test_cases = [
            {
                "data": {
                    "title": "Short Video",
                    "description": "Brief description",
                    "target_audience": "general",
                    "duration_estimate": 30
                },
                "expected_cost_range": (0.5, 1.5)
            },
            {
                "data": {
                    "title": "Medium Length Video",
                    "description": "A more detailed description that should increase processing time and cost. " * 5,
                    "target_audience": "professionals",
                    "duration_estimate": 120,
                    "style": "high_quality"
                },
                "expected_cost_range": (2.0, 5.0)
            },
            {
                "data": {
                    "title": "Long Complex Video",
                    "description": "Complex description with multiple elements. " * 20,
                    "target_audience": "specialists",
                    "duration_estimate": 300,
                    "style": "premium",
                    "voice_type": "premium",
                    "visual_elements": "complex"
                },
                "expected_cost_range": (5.0, 15.0)
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            # Validate data
            result = data_validator.validate(test_case["data"])
            
            # Verify cost estimation
            min_cost, max_cost = test_case["expected_cost_range"]
            assert min_cost <= float(result.estimated_cost) <= max_cost, \
                f"Test case {i+1}: Estimated cost {result.estimated_cost} not in range [{min_cost}, {max_cost}]"
            
            # Verify quality scoring
            assert 0.0 <= result.quality_score <= 1.0, \
                f"Test case {i+1}: Quality score {result.quality_score} not in [0, 1] range"
    
    def test_smart_batching_algorithm(self):
        """Test smart batching algorithm for cost optimization."""
        
        # Create test requests with different characteristics
        requests = []
        for i in range(10):
            request = GenerationRequest(
                id=str(uuid.uuid4()),
                type=GenerationType.AUDIO,
                provider=Provider.MINIMAX,
                prompt=f"Generate audio for video {i+1}",
                params={
                    "duration": 30 + (i * 10),  # Different durations
                    "quality": "standard" if i < 5 else "premium"
                },
                priority=TaskPriority.NORMAL,
                estimated_cost=Decimal(str(0.5 + (i * 0.3))),
                estimated_duration=30 + (i * 10)
            )
            requests.append(request)
        
        # Test batching algorithm
        batched_requests = smart_batch_requests(requests, max_batch_size=5, max_total_cost=10.0)
        
        # Verify batching logic
        assert len(batched_requests) > 0, "Batching should produce at least one batch"
        
        for batch in batched_requests:
            # Verify batch size constraints
            assert len(batch) <= 5, f"Batch size {len(batch)} exceeds maximum of 5"
            
            # Verify cost constraints
            total_cost = sum(req.estimated_cost for req in batch)
            assert total_cost <= Decimal("10.0"), f"Batch total cost {total_cost} exceeds limit"
            
            # Verify cost efficiency (similar cost items should be grouped)
            if len(batch) > 1:
                costs = [float(req.estimated_cost) for req in batch]
                cost_variance = np.var(costs)
                assert cost_variance < 2.0, f"Batch cost variance {cost_variance} too high (should group similar costs)"
    
    def test_rate_limiting_cost_optimization(self, rate_limiter):
        """Test rate limiting strategies for cost optimization."""
        
        # Test different rate limiting scenarios
        scenarios = [
            {"requests": 50, "per_user_limit": 10, "per_project_limit": 30, "expected_blocks": 20},
            {"requests": 20, "per_user_limit": 15, "per_project_limit": 25, "expected_blocks": 0},
            {"requests": 100, "per_user_limit": 5, "per_project_limit": 20, "expected_blocks": 80}
        ]
        
        for scenario in scenarios:
            # Configure rate limiter
            rate_limiter.per_user_limit = scenario["per_user_limit"]
            rate_limiter.per_project_limit = scenario["per_project_limit"]
            
            # Simulate requests
            allowed_requests = 0
            blocked_requests = 0
            
            for i in range(scenario["requests"]):
                user_id = f"user_{i % 5}"  # 5 different users
                project_id = "test_project"
                
                if rate_limiter.can_proceed(user_id, project_id):
                    allowed_requests += 1
                else:
                    blocked_requests += 1
            
            # Verify rate limiting behavior
            assert blocked_requests >= scenario["expected_blocks"], \
                f"Scenario {scenario}: Expected at least {scenario['expected_blocks']} blocks, got {blocked_requests}"
            
            # Verify cost efficiency (less blocks = better cost efficiency)
            efficiency = allowed_requests / scenario["requests"]
            if scenario["per_user_limit"] >= scenario["per_project_limit"]:
                # When per-user limit is higher, should have reasonable efficiency
                assert efficiency > 0.1, f"Efficiency too low: {efficiency}"
    
    def test_resource_pool_cost_efficiency(self):
        """Test resource pool allocation for cost optimization."""
        
        # Create resource pools
        api_pool = ResourcePool(
            pool_type=ResourceType.API_CALLS,
            capacity=10,
            current_usage=0,
            cost_per_unit=Decimal("0.01")
        )
        
        memory_pool = ResourcePool(
            pool_type=ResourceType.MEMORY,
            capacity=1000,  # MB
            current_usage=0,
            cost_per_unit=Decimal("0.001")
        )
        
        # Test resource allocation algorithm
        def allocate_resources(requests: List[GenerationRequest]) -> Dict[str, Any]:
            allocation = {
                "api_allocation": 0,
                "memory_allocation": 0,
                "total_cost": Decimal("0.0"),
                "efficiency_score": 0.0
            }
            
            for request in requests:
                # Simulate resource requirements
                api_needed = 1  # One API call per request
                memory_needed = 50  # 50MB per request
                cost = request.estimated_cost
                
                # Check if resources are available
                if (api_pool.available_capacity() >= api_needed and 
                    memory_pool.available_capacity() >= memory_needed):
                    
                    # Allocate resources
                    api_pool.allocate(api_needed)
                    memory_pool.allocate(memory_needed)
                    
                    allocation["api_allocation"] += api_needed
                    allocation["memory_allocation"] += memory_needed
                    allocation["total_cost"] += cost
                else:
                    # Skip if resources not available
                    continue
            
            # Calculate efficiency
            if len(requests) > 0:
                allocation["efficiency_score"] = (
                    allocation["api_allocation"] / len(requests) +
                    allocation["memory_allocation"] / (len(requests) * 100)  # Normalize
                ) / 2
            
            return allocation
        
        # Create test requests
        test_requests = [
            GenerationRequest(
                id=str(uuid.uuid4()),
                type=GenerationType.AUDIO,
                provider=Provider.MINIMAX,
                prompt=f"Request {i}",
                params={},
                priority=TaskPriority.NORMAL,
                estimated_cost=Decimal(str(0.5 + i * 0.1))
            )
            for i in range(15)
        ]
        
        # Test allocation
        result = allocate_resources(test_requests)
        
        # Verify allocation results
        assert result["api_allocation"] <= api_pool.capacity
        assert result["memory_allocation"] <= memory_pool.capacity
        assert 0.0 <= result["efficiency_score"] <= 1.0
        assert result["total_cost"] > 0
    
    def test_parallel_processing_cost_analysis(self):
        """Test cost analysis for parallel processing strategies."""
        
        # Simulate different parallel processing strategies
        strategies = [
            {
                "name": "sequential",
                "workers": 1,
                "batch_size": 1,
                "overhead_per_batch": Decimal("0.0")
            },
            {
                "name": "small_batches",
                "workers": 4,
                "batch_size": 2,
                "overhead_per_batch": Decimal("0.1")
            },
            {
                "name": "large_batches",
                "workers": 4,
                "batch_size": 8,
                "overhead_per_batch": Decimal("0.3")
            },
            {
                "name": "optimal",
                "workers": 4,
                "batch_size": 4,
                "overhead_per_batch": Decimal("0.15")
            }
        ]
        
        # Test scenarios
        scenarios = [
            {"requests": 10, "avg_request_cost": Decimal("1.0")},
            {"requests": 50, "avg_request_cost": Decimal("1.0")},
            {"requests": 100, "avg_request_cost": Decimal("1.0")}
        ]
        
        results = {}
        
        for scenario in scenarios:
            scenario_results = {}
            
            for strategy in strategies:
                # Calculate processing time
                total_batches = math.ceil(scenario["requests"] / strategy["batch_size"])
                batches_per_worker = math.ceil(total_batches / strategy["workers"])
                
                # Simulate processing time (base cost + overhead)
                base_cost = scenario["requests"] * scenario["avg_request_cost"]
                overhead_cost = total_batches * strategy["overhead_per_batch"]
                
                # Add worker coordination cost
                worker_cost = strategy["workers"] * Decimal("0.1")
                
                total_cost = base_cost + overhead_cost + worker_cost
                
                # Calculate efficiency metrics
                processing_time = total_batches  # Simplified time estimation
                cost_per_request = total_cost / scenario["requests"]
                
                scenario_results[strategy["name"]] = {
                    "total_cost": total_cost,
                    "processing_time": processing_time,
                    "cost_per_request": cost_per_request,
                    "overhead_percentage": (overhead_cost / total_cost * 100) if total_cost > 0 else 0
                }
            
            results[f"scenario_{scenario['requests']}_requests"] = scenario_results
        
        # Verify results make sense
        for scenario_name, scenario_results in results.items():
            # Sequential should have no overhead
            assert scenario_results["sequential"]["overhead_percentage"] == 0
            
            # Large batches should have lower overhead percentage
            large_batch_overhead = scenario_results["large_batches"]["overhead_percentage"]
            small_batch_overhead = scenario_results["small_batches"]["overhead_percentage"]
            assert large_batch_overhead <= small_batch_overhead
            
            # Optimal should balance cost and time
            optimal_cost = scenario_results["optimal"]["total_cost"]
            sequential_cost = scenario_results["sequential"]["total_cost"]
            assert optimal_cost < sequential_cost  # Should be more efficient
    
    @pytest.mark.asyncio
    async def test_async_cost_optimization(self, mock_aiohttp_session):
        """Test cost optimization in async processing."""
        
        # Create generator with cost tracking
        generator = ParallelGenerator(
            max_concurrent_jobs=2,
            cost_tracking_enabled=True
        )
        
        # Mock aiohttp session
        generator.session = mock_aiohttp_session
        
        # Create requests with different costs
        requests = []
        for i in range(5):
            request = GenerationRequest(
                id=str(uuid.uuid4()),
                type=GenerationType.AUDIO,
                provider=Provider.MINIMAX,
                prompt=f"Generate audio for prompt {i+1}",
                params={"cost_level": "standard" if i < 3 else "premium"},
                priority=TaskPriority.NORMAL,
                estimated_cost=Decimal(str(0.5 + i * 0.3))
            )
            requests.append(request)
        
        # Process requests with cost optimization
        with patch.object(generator, '_make_api_request') as mock_request:
            mock_request.return_value = AsyncMock(return_value={
                "success": True,
                "url": f"https://example.com/audio_{i}.mp3",
                "cost": 0.5 + i * 0.3
            })
            
            # Process requests
            results = await generator.process_batch(requests)
            
            # Verify cost optimization worked
            assert len(results) == len(requests)
            
            total_estimated_cost = sum(req.estimated_cost for req in requests)
            total_actual_cost = sum(result.get("cost", 0) for result in results)
            
            # Actual cost should be close to estimated (within 20% variance)
            cost_variance = abs(total_actual_cost - float(total_estimated_cost)) / float(total_estimated_cost)
            assert cost_variance <= 0.2, f"Cost variance {cost_variance} exceeds 20%"
    
    def test_quality_cost_tradeoff_analysis(self, data_validator):
        """Test quality vs cost trade-off analysis."""
        
        # Create test data with different quality characteristics
        test_data_variants = [
            {
                "basic": {
                    "title": "Basic Video",
                    "description": "Simple video description",
                    "target_audience": "general",
                    "style": "basic"
                }
            },
            {
                "standard": {
                    "title": "Standard Video",
                    "description": "Standard video description with moderate complexity",
                    "target_audience": "professionals",
                    "style": "standard"
                }
            },
            {
                "premium": {
                    "title": "Premium Video",
                    "description": "Premium video with complex requirements and high quality standards",
                    "target_audience": "experts",
                    "style": "premium",
                    "voice_type": "premium",
                    "visual_elements": "high_quality"
                }
            }
        ]
        
        results = []
        
        for quality_level, data in test_data_variants.items():
            validation_result = data_validator.validate(data)
            
            results.append({
                "quality_level": quality_level,
                "cost": validation_result.estimated_cost,
                "quality_score": validation_result.quality_score,
                "efficiency": validation_result.quality_score / float(validation_result.estimated_cost)
            })
        
        # Verify trade-offs
        assert len(results) == 3
        
        # Basic should have lowest cost
        assert results[0]["cost"] < results[1]["cost"] < results[2]["cost"]
        
        # Premium should have highest quality
        assert results[0]["quality_score"] < results[1]["quality_score"] < results[2]["quality_score"]
        
        # Calculate efficiency ratios
        for result in results:
            assert result["efficiency"] > 0, f"Efficiency should be positive for {result['quality_level']}"
            assert result["cost"] > 0, f"Cost should be positive for {result['quality_level']}"
    
    def test_bulk_job_cost_aggregation(self, processed_ideas_sample):
        """Test cost aggregation for bulk jobs."""
        
        # Calculate individual costs
        individual_costs = []
        for idea in processed_ideas_sample:
            # Simulate cost calculation based on idea characteristics
            base_cost = Decimal("1.0")
            duration_multiplier = Decimal(str(idea.normalized_data.get("duration_estimate", 60))) / Decimal("60")
            quality_multiplier = Decimal("1.2") if len(idea.normalized_data.get("tags", [])) > 3 else Decimal("1.0")
            
            total_cost = base_cost * duration_multiplier * quality_multiplier
            individual_costs.append(total_cost)
        
        # Calculate bulk discount
        total_individual_cost = sum(individual_costs)
        bulk_discount_rate = calculate_bulk_discount(len(processed_ideas_sample))
        discounted_cost = total_individual_cost * (Decimal("1.0") - bulk_discount_rate)
        
        # Calculate efficiency metrics
        average_cost_per_item = discounted_cost / len(processed_ideas_sample)
        cost_per_minute = discounted_cost / sum(
            idea.normalized_data.get("duration_estimate", 60) for idea in processed_ideas_sample
        )
        
        # Verify cost calculations
        assert total_individual_cost > 0
        assert discounted_cost < total_individual_cost  # Discount should reduce cost
        assert average_cost_per_item > 0
        assert cost_per_minute > 0
        
        # Verify bulk discount scaling
        if len(processed_ideas_sample) >= 10:
            assert bulk_discount_rate >= Decimal("0.1")  # At least 10% discount for large batches
        
        return {
            "total_cost": discounted_cost,
            "bulk_discount": bulk_discount_rate,
            "cost_per_item": average_cost_per_item,
            "cost_per_minute": cost_per_minute
        }
    
    def test_cost_prediction_model(self):
        """Test cost prediction model accuracy."""
        
        # Historical data for training
        historical_data = [
            {
                "input_features": {
                    "duration": 60,
                    "complexity": "medium",
                    "quality": "standard",
                    "provider": "minimax"
                },
                "actual_cost": Decimal("1.50")
            },
            {
                "input_features": {
                    "duration": 120,
                    "complexity": "high",
                    "quality": "premium",
                    "provider": "minimax"
                },
                "actual_cost": Decimal("3.00")
            },
            {
                "input_features": {
                    "duration": 30,
                    "complexity": "low",
                    "quality": "basic",
                    "provider": "minimax"
                },
                "actual_cost": Decimal("0.75")
            }
        ]
        
        # Simple prediction model (linear regression approximation)
        def predict_cost(features):
            base_cost = Decimal("0.5")
            
            # Duration factor
            duration_factor = features["duration"] / 60
            
            # Complexity factor
            complexity_factors = {"low": 0.8, "medium": 1.0, "high": 1.5}
            complexity_factor = complexity_factors.get(features["complexity"], 1.0)
            
            # Quality factor
            quality_factors = {"basic": 0.8, "standard": 1.0, "premium": 1.3}
            quality_factor = quality_factors.get(features["quality"], 1.0)
            
            predicted_cost = base_cost * duration_factor * complexity_factor * quality_factor
            return predicted_cost
        
        # Test predictions
        predictions = []
        for data_point in historical_data:
            predicted = predict_cost(data_point["input_features"])
            actual = data_point["actual_cost"]
            error = abs(predicted - actual) / actual
            
            predictions.append({
                "predicted": predicted,
                "actual": actual,
                "error_percentage": float(error * 100)
            })
        
        # Verify prediction accuracy
        avg_error = sum(p["error_percentage"] for p in predictions) / len(predictions)
        assert avg_error <= 20.0, f"Average prediction error {avg_error}% exceeds 20%"
        
        for prediction in predictions:
            assert prediction["error_percentage"] <= 30.0, \
                f"Individual prediction error {prediction['error_percentage']}% exceeds 30%"


# Helper functions for cost optimization tests
def smart_batch_requests(requests: List[GenerationRequest], max_batch_size: int, max_total_cost: Decimal) -> List[List[GenerationRequest]]:
    """Smart batching algorithm for cost optimization."""
    
    # Sort requests by estimated cost (ascending)
    sorted_requests = sorted(requests, key=lambda r: r.estimated_cost)
    
    batches = []
    current_batch = []
    current_cost = Decimal("0.0")
    
    for request in sorted_requests:
        # Check if adding this request would exceed limits
        new_cost = current_cost + request.estimated_cost
        
        if (len(current_batch) < max_batch_size and 
            new_cost <= max_total_cost):
            
            current_batch.append(request)
            current_cost = new_cost
        else:
            # Start new batch
            if current_batch:
                batches.append(current_batch)
            
            current_batch = [request]
            current_cost = request.estimated_cost
    
    # Add last batch if not empty
    if current_batch:
        batches.append(current_batch)
    
    return batches


def calculate_bulk_discount(batch_size: int) -> Decimal:
    """Calculate bulk discount rate based on batch size."""
    
    if batch_size < 5:
        return Decimal("0.0")
    elif batch_size < 10:
        return Decimal("0.05")  # 5% discount
    elif batch_size < 20:
        return Decimal("0.10")  # 10% discount
    elif batch_size < 50:
        return Decimal("0.15")  # 15% discount
    else:
        return Decimal("0.20")  # 20% discount


def analyze_cost_efficiency(requests: List[GenerationRequest], results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze cost efficiency of processing results."""
    
    if not requests or not results:
        return {"efficiency_score": 0.0}
    
    total_estimated = sum(req.estimated_cost for req in requests)
    total_actual = sum(result.get("cost", 0) for result in results)
    
    cost_accuracy = 1.0 - abs(total_actual - float(total_estimated)) / float(total_estimated)
    processing_efficiency = len(results) / len(requests) if requests else 0
    
    overall_efficiency = (cost_accuracy + processing_efficiency) / 2
    
    return {
        "cost_accuracy": cost_accuracy,
        "processing_efficiency": processing_efficiency,
        "overall_efficiency": overall_efficiency,
        "total_estimated": total_estimated,
        "total_actual": Decimal(str(total_actual))
    }


if __name__ == "__main__":
    # Run specific cost optimization test
    import sys
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        pytest.main([__file__, f"-k {test_name}", "-v"])