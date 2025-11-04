"""
Smart Batching System for API Cost Optimization

This module implements an advanced batching system that:
1. Groups similar content requests for optimal cost efficiency
2. Dynamically adjusts batch sizes based on content complexity
3. Implements multi-layer cache for repeated content reuse
4. Provides cost-benefit analysis for batching decisions
5. Integrates with priority queue for optimal scheduling

Based on cost optimization algorithms from docs/architecture_design/cost_optimization.md
"""

import asyncio
import hashlib
import json
import logging
import math
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from datetime import datetime, timedelta
import heapq
from concurrent.futures import ThreadPoolExecutor
import weakref
import pickle
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ContentRequest:
    """Represents a content generation request"""
    id: str
    content_type: str  # 'video', 'image', 'audio'
    prompt: str
    reference_images: List[str] = field(default_factory=list)
    resolution: str = "1920x1080"
    duration: float = 30.0
    engine: str = "default"
    style_params: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # 1=urgent, 2=normal, 3=background
    estimated_cost: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Generate content fingerprint for similarity matching"""
        self.fingerprint = self._generate_fingerprint()
        self.estimated_cost = self._estimate_cost()
        # Add sort key for priority queue
        self.sort_key = (self.priority, self.estimated_cost, self.created_at)
    
    def __lt__(self, other):
        """Enable sorting for priority queue"""
        return self.sort_key < other.sort_key
    
    def _generate_fingerprint(self) -> str:
        """Generate content fingerprint for similarity detection"""
        # Create a more flexible fingerprint that allows cache hits for similar content
        prompt_words = ' '.join(sorted(self.prompt.lower().split()[:5]))  # First 5 words, sorted
        
        # Create a semantic key instead of exact match
        semantic_key = f"{self.content_type}:{self.engine}:{prompt_words}"
        
        # Add style parameters in a normalized way
        if 'video_style' in self.style_params:
            semantic_key += f":{self.style_params['video_style']}"
        elif 'style' in self.style_params:
            semantic_key += f":{self.style_params['style']}"
        elif 'category' in self.style_params:
            semantic_key += f":{self.style_params['category']}"
        else:
            semantic_key += ":default"
        
        return semantic_key
    
    def _estimate_cost(self) -> float:
        """Estimate cost based on content type, duration, and resolution"""
        base_costs = {
            'video': 0.10,  # per second
            'image': 0.02,  # per image
            'audio': 0.05   # per second
        }
        
        resolution_multipliers = {
            '1920x1080': 1.0,
            '1080x1920': 1.0,
            '3840x2160': 2.0,  # 4K
            '1024x1024': 0.5
        }
        
        base_cost = base_costs.get(self.content_type, 0.1)
        duration = self.duration if self.content_type != 'image' else 1.0
        resolution_mult = resolution_multipliers.get(self.resolution, 1.0)
        
        return base_cost * duration * resolution_mult

@dataclass
class Batch:
    """Represents a batch of content requests"""
    id: str
    requests: List[ContentRequest]
    created_at: datetime = field(default_factory=datetime.now)
    max_size: int = 25
    max_cost: float = 500.0
    max_duration: float = 1800.0  # 30 minutes
    engine: str = "default"
    resolution: str = "1920x1080"
    similarity_score: float = 0.0
    estimated_total_cost: float = 0.0
    estimated_optimized_cost: float = 0.0  # Cost with batching discounts
    priority_score: float = 0.0
    
    def __post_init__(self):
        individual_cost = sum(req.estimated_cost for req in self.requests)
        self.estimated_total_cost = individual_cost
        self.estimated_optimized_cost = self._calculate_optimized_cost()
        self.similarity_score = self._calculate_similarity()
        self.priority_score = self._calculate_priority()
    
    def _calculate_similarity(self) -> float:
        """Calculate similarity score for the batch"""
        if not self.requests:
            return 0.0
        
        # Check engine consistency
        engines = {req.engine for req in self.requests}
        engine_consistency = 1.0 if len(engines) == 1 else 0.2  # More lenient
        
        # Check resolution consistency
        resolutions = {req.resolution for req in self.requests}
        resolution_consistency = 1.0 if len(resolutions) == 1 else 0.3  # More lenient
        
        # Check content type consistency
        content_types = {req.content_type for req in self.requests}
        content_consistency = 1.0 if len(content_types) == 1 else 0.1  # More lenient
        
        # Calculate prompt similarity
        total_duration = sum(req.duration for req in self.requests)
        avg_duration = total_duration / len(self.requests)
        duration_variance = sum((req.duration - avg_duration) ** 2 for req in self.requests) / len(self.requests)
        
        # Lower variance = higher similarity (with minimum floor)
        if avg_duration > 0:
            duration_similarity = 1.0 / (1.0 + math.sqrt(duration_variance) / max(1, avg_duration))
        else:
            duration_similarity = 1.0
        
        # Check style parameters similarity
        style_params_list = [json.dumps(req.style_params, sort_keys=True) for req in self.requests]
        unique_styles = len(set(style_params_list))
        style_similarity = max(0.1, 1.0 - (unique_styles - 1) / max(1, len(self.requests)))
        
        # Combine all factors with weights
        weights = {'engine': 0.3, 'resolution': 0.25, 'content': 0.25, 'duration': 0.1, 'style': 0.1}
        
        return (
            weights['engine'] * engine_consistency +
            weights['resolution'] * resolution_consistency +
            weights['content'] * content_consistency +
            weights['duration'] * duration_similarity +
            weights['style'] * style_similarity
        )
    
    def _calculate_priority(self) -> float:
        """Calculate priority score for queue ordering"""
        urgency_score = 4.0 - sum(req.priority for req in self.requests) / len(self.requests)
        cost_score = 1.0 / (1.0 + self.estimated_total_cost / 100.0)
        deadline_score = self._calculate_deadline_score()
        
        weights = {'urgency': 0.4, 'cost': 0.3, 'deadline': 0.3}
        return (
            weights['urgency'] * urgency_score +
            weights['cost'] * cost_score +
            weights['deadline'] * deadline_score
        )
    
    def _calculate_deadline_score(self) -> float:
        """Calculate deadline-based priority score"""
        if not any(req.deadline for req in self.requests):
            return 1.0
        
        now = datetime.now()
        time_to_deadline = min(
            (req.deadline - now).total_seconds() 
            for req in self.requests if req.deadline
        )
        
        if time_to_deadline <= 0:
            return 10.0  # Overdue
        
        # Exponential decay based on time remaining
        return 1.0 / (1.0 + time_to_deadline / 3600.0)  # 1 hour half-life
    
    def _calculate_optimized_cost(self) -> float:
        """Calculate cost with batching optimization applied"""
        if not self.requests:
            return 0.0
        
        # Base cost is sum of individual requests
        base_cost = sum(req.estimated_cost for req in self.requests)
        
        # Apply batching discounts based on batch size and similarity
        batch_size = len(self.requests)
        similarity = self.similarity_score
        
        # Volume discount - larger batches get better discounts
        # Changed to more conservative and reliable discounts
        if batch_size >= 20:
            volume_discount = 0.75  # 25% discount for very large batches
        elif batch_size >= 10:
            volume_discount = 0.80  # 20% discount for large batches  
        elif batch_size >= 5:
            volume_discount = 0.85  # 15% discount for medium batches
        elif batch_size >= 2:
            volume_discount = 0.90  # 10% discount for small batches
        else:
            # Single request - no discount but may have processing overhead
            return base_cost * 1.02  # Small overhead for single requests
        
        # Similarity bonus - more similar content can share processing
        similarity_bonus = similarity * 0.10  # Up to 10% additional discount
        
        # API call reduction - one API call instead of many (minimum benefit)
        api_reduction = min(0.25, 0.05 * batch_size)  # Up to 25% reduction, scales with batch size
        
        # Combined optimization - ensure there's always at least some benefit
        total_discount = (1 - volume_discount) + similarity_bonus + api_reduction
        total_discount = min(0.50, max(0.05, total_discount))  # Between 5% and 50% discount
        
        optimized_cost = base_cost * (1 - total_discount)
        
        return max(optimized_cost, base_cost * 0.5)  # Minimum 50% of base cost
    
    def is_compatible(self, request: ContentRequest) -> bool:
        """Check if request is compatible with this batch"""
        return (
            request.engine == self.engine and
            request.resolution == self.resolution and
            request.content_type == self.requests[0].content_type
        )
    
    def can_add(self, request: ContentRequest) -> bool:
        """Check if request can be added to this batch"""
        if not self.is_compatible(request):
            return False
        
        if len(self.requests) >= self.max_size:
            return False
        
        new_cost = self.estimated_total_cost + request.estimated_cost
        if new_cost > self.max_cost:
            return False
        
        new_total_duration = sum(req.duration for req in self.requests) + request.duration
        if new_total_duration > self.max_duration:
            return False
        
        return True

class CacheManager:
    """Multi-layer cache for content reuse"""
    
    def __init__(self, memory_size: int = 1000, redis_config: Optional[Dict] = None):
        self.memory_cache = LRUCache(memory_size)
        self.redis_config = redis_config
        self.local_cache_enabled = True
        self.redis_cache_enabled = redis_config is not None
        
    def get_cache_key(self, request: ContentRequest) -> str:
        """Generate cache key for request"""
        return f"content:{request.fingerprint}"
    
    def get(self, request: ContentRequest) -> Optional[Dict[str, Any]]:
        """Get cached content if available"""
        cache_key = self.get_cache_key(request)
        
        # Try memory cache first
        if self.local_cache_enabled:
            cached = self.memory_cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Memory cache hit: {cache_key}")
                return cached
        
        # Try Redis cache if available
        if self.redis_cache_enabled:
            # Redis implementation would go here
            pass
        
        return None
    
    def set(self, request: ContentRequest, content: Dict[str, Any], ttl: int = 3600):
        """Cache content for request"""
        cache_key = self.get_cache_key(request)
        
        # Store in memory cache
        if self.local_cache_enabled:
            self.memory_cache.set(cache_key, content, ttl)
        
        # Store in Redis cache if available
        if self.redis_cache_enabled:
            # Redis implementation would go here
            pass
    
    def is_near_duplicate(self, request: ContentRequest, threshold: float = 0.8) -> bool:
        """Check if request is near-duplicate of cached content"""
        # Simplified implementation - would use perceptual hashing in production
        cache_key = self.get_cache_key(request)
        return self.memory_cache.get(cache_key) is not None

class LRUCache:
    """Least Recently Used cache implementation"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = {}
        self.access_order = deque()
        self.lock = asyncio.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]['value']  # Return the actual value, not the metadata
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        if key in self.cache:
            # Update existing
            self.cache[key] = {
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl
            }
            self.access_order.remove(key)
            self.access_order.append(key)
        else:
            # Add new item
            if len(self.cache) >= self.max_size:
                # Remove least recently used
                oldest_key = self.access_order.popleft()
                del self.cache[oldest_key]
            
            self.cache[key] = {
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl
            }
            self.access_order.append(key)
    
    def cleanup_expired(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, data in self.cache.items():
            if current_time - data['timestamp'] > data['ttl']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)

class SmartBatcher:
    """Smart batching system with cost optimization"""
    
    def __init__(self, 
                 max_batch_size: int = 25,
                 max_batch_cost: float = 500.0,
                 max_batch_duration: float = 1800.0,
                 similarity_threshold: float = 0.7,
                 cache_manager: Optional[CacheManager] = None):
        
        self.max_batch_size = max_batch_size
        self.max_batch_cost = max_batch_cost
        self.max_batch_duration = max_batch_duration
        self.similarity_threshold = similarity_threshold
        self.cache_manager = cache_manager or CacheManager()
        
        # Batching queues
        self.pending_requests = []  # Heap for priority queue
        self.active_batches = {}
        self.batch_history = []
        
        # Performance metrics
        self.metrics = {
            'total_requests': 0,
            'batched_requests': 0,
            'cached_requests': 0,
            'total_cost_saved': 0.0,
            'average_batch_size': 0.0,
            'cache_hit_ratio': 0.0
        }
        
        # Batching configuration
        self.config = {
            'batch_pacing_interval': 0.5,  # seconds between batch submissions
            'dynamic_sizing': True,
            'cost_optimization': True,
            'similarity_focus': True
        }
    
    async def add_request(self, request: ContentRequest) -> str:
        """Add request to the batching system"""
        self.metrics['total_requests'] += 1
        
        # Check cache first
        cached_content = self.cache_manager.get(request)
        if cached_content:
            self.metrics['cached_requests'] += 1
            logger.info(f"Cache hit for request {request.id}")
            return f"cached:{request.id}"
        
        # Add to priority queue
        priority_score = request.priority * 100 + request.estimated_cost
        heapq.heappush(self.pending_requests, (priority_score, request))
        
        logger.debug(f"Added request {request.id} to batch queue")
        return f"queued:{request.id}"
    
    async def build_optimal_batches(self) -> List[Batch]:
        """Build optimal batches using smart grouping algorithm"""
        if not self.pending_requests:
            return []
        
        # Sort requests by priority
        sorted_requests = sorted(
            self.pending_requests, 
            key=lambda x: x[0]  # priority score
        )
        self.pending_requests = []  # Clear the heap
        
        # Group requests by compatibility
        groups = self._group_by_compatibility([req for _, req in sorted_requests])
        
        batches = []
        for group in groups:
            if len(group) == 1:
                # Single request - create minimal batch
                batch = Batch(
                    id=str(uuid.uuid4()),
                    requests=group,
                    max_size=self.max_batch_size,
                    max_cost=self.max_batch_cost,
                    max_duration=self.max_batch_duration,
                    engine=group[0].engine,
                    resolution=group[0].resolution
                )
                batches.append(batch)
            else:
                # Multiple requests - apply smart batching
                group_batches = self._create_smart_batches(group)
                batches.extend(group_batches)
        
        # Update metrics
        self.metrics['batched_requests'] += sum(len(b.requests) for b in batches)
        total_requests = sum(len(b.requests) for b in batches) if batches else 1
        self.metrics['average_batch_size'] = (
            self.metrics['average_batch_size'] + total_requests / len(batches)
        ) / 2 if batches else 0
        
        logger.info(f"Created {len(batches)} optimal batches from {len(sorted_requests)} requests")
        return batches
    
    def _group_by_compatibility(self, requests: List[ContentRequest]) -> List[List[ContentRequest]]:
        """Group requests by compatibility criteria"""
        groups = defaultdict(list)
        
        for request in requests:
            # Group by engine, resolution, and content type
            key = f"{request.engine}:{request.resolution}:{request.content_type}"
            groups[key].append(request)
        
        return list(groups.values())
    
    def _create_smart_batches(self, requests: List[ContentRequest]) -> List[Batch]:
        """Create smart batches using advanced algorithms"""
        if not requests:
            return []
        
        # Sort by priority and cost to group efficiently
        requests.sort(key=lambda r: (r.priority, r.estimated_cost, r.created_at))
        
        batches = []
        current_batch = None
        
        for request in requests:
            if current_batch is None:
                # Start new batch
                current_batch = Batch(
                    id=str(uuid.uuid4()),
                    requests=[request],
                    max_size=self.max_batch_size,
                    max_cost=self.max_batch_cost,
                    max_duration=self.max_batch_duration,
                    engine=request.engine,
                    resolution=request.resolution
                )
            elif current_batch.can_add(request):
                # Check if adding this request would significantly improve batching efficiency
                temp_batch = Batch(
                    id=current_batch.id,
                    requests=current_batch.requests + [request],
                    max_size=current_batch.max_size,
                    max_cost=current_batch.max_cost,
                    max_duration=current_batch.max_duration,
                    engine=current_batch.engine,
                    resolution=current_batch.resolution
                )
                
                # More lenient similarity checking
                should_add = False
                
                # If batch is small (< 5), be more lenient with similarity
                if len(current_batch.requests) < 5:
                    should_add = True
                # If similarity is still acceptable after adding
                elif temp_batch.similarity_score >= (self.similarity_threshold - 0.2):
                    should_add = True
                # If the request helps fill the batch to a reasonable size
                elif len(current_batch.requests) < 8 and temp_batch.estimated_optimized_cost < current_batch.max_cost * 0.8:
                    should_add = True
                
                if should_add:
                    current_batch = temp_batch
                else:
                    # Finalize current batch and start new one
                    batches.append(current_batch)
                    current_batch = Batch(
                        id=str(uuid.uuid4()),
                        requests=[request],
                        max_size=self.max_batch_size,
                        max_cost=self.max_batch_cost,
                        max_duration=self.max_batch_duration,
                        engine=request.engine,
                        resolution=request.resolution
                    )
            else:
                # Current batch is full, start new one
                batches.append(current_batch)
                current_batch = Batch(
                    id=str(uuid.uuid4()),
                    requests=[request],
                    max_size=self.max_batch_size,
                    max_cost=self.max_batch_cost,
                    max_duration=self.max_batch_duration,
                    engine=request.engine,
                    resolution=request.resolution
                )
        
        # Add final batch
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    async def process_batch(self, batch: Batch) -> Dict[str, Any]:
        """Process a batch of requests"""
        logger.info(f"Processing batch {batch.id} with {len(batch.requests)} requests")
        
        start_time = time.time()
        results = []
        
        try:
            # Group requests by generation type
            by_generation_type = self._group_by_generation_type(batch.requests)
            
            for gen_type, requests in by_generation_type.items():
                # Simulate batch generation (would call actual API)
                batch_result = await self._simulate_batch_generation(gen_type, requests)
                results.extend(batch_result)
            
            # Cache successful results
            await self._cache_results(results)
            
            processing_time = time.time() - start_time
            cost_efficiency = batch.estimated_total_cost / processing_time if processing_time > 0 else 0
            
            return {
                'batch_id': batch.id,
                'requests': len(batch.requests),
                'total_cost': batch.estimated_total_cost,
                'processing_time': processing_time,
                'cost_efficiency': cost_efficiency,
                'results': results,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error processing batch {batch.id}: {e}")
            return {
                'batch_id': batch.id,
                'requests': len(batch.requests),
                'error': str(e),
                'status': 'failed'
            }
    
    def _group_by_generation_type(self, requests: List[ContentRequest]) -> Dict[str, List[ContentRequest]]:
        """Group requests by generation type for API calls"""
        groups = defaultdict(list)
        for request in requests:
            key = f"{request.content_type}_{request.engine}"
            groups[key].append(request)
        return dict(groups)
    
    async def _simulate_batch_generation(self, gen_type: str, requests: List[ContentRequest]) -> List[Dict[str, Any]]:
        """Simulate batch generation (replace with actual API calls)"""
        results = []
        
        for request in requests:
            # Simulate generation time based on complexity
            base_time = {'video': 5.0, 'image': 1.0, 'audio': 3.0}.get(request.content_type, 2.0)
            complexity_factor = 1.0 + (len(request.prompt) / 100.0)
            generation_time = base_time * complexity_factor
            
            await asyncio.sleep(0.1)  # Simulate API call
            
            result = {
                'request_id': request.id,
                'content_type': request.content_type,
                'file_path': f"generated/{request.content_type}/{request.id}.mp4",
                'duration': request.duration,
                'cost': request.estimated_cost,
                'quality_score': 8.5,
                'generation_time': generation_time
            }
            results.append(result)
        
        return results
    
    async def _cache_results(self, results: List[Dict[str, Any]]):
        """Cache successful generation results"""
        for result in results:
            # Find corresponding request using request_id
            request_id = result.get('request_id')
            
            # Look for the request in our active batches or pending requests
            request = None
            for batch in self.active_batches.values():
                for req in batch.requests:
                    if req.id == request_id:
                        request = req
                        break
                if request:
                    break
            
            # If not found in active batches, look in pending requests
            if not request:
                for _, req in self.pending_requests:
                    if req.id == request_id:
                        request = req
                        break
            
            if request and result.get('status') == 'success':
                # Cache the successful result
                cache_data = {
                    'file_path': result.get('file_path'),
                    'duration': result.get('duration'),
                    'cost': result.get('cost'),
                    'quality_score': result.get('quality_score'),
                    'generated_at': datetime.now().isoformat(),
                    'generation_time': result.get('generation_time', 0)
                }
                
                self.cache_manager.set(request, cache_data, ttl=3600)
                logger.debug(f"Cached result for request {request_id}")
    
    def get_cost_benefit_analysis(self, batch: Batch) -> Dict[str, Any]:
        """Perform cost-benefit analysis for a batch"""
        individual_cost = sum(req.estimated_cost for req in batch.requests)
        batch_cost = batch.estimated_total_cost
        
        # Calculate savings
        direct_savings = max(0, individual_cost - batch_cost)
        
        # Calculate overhead costs
        processing_overhead = len(batch.requests) * 0.1  # Per-request overhead
        failure_risk = len(batch.requests) * 0.05 if len(batch.requests) > 10 else 0
        
        # Calculate benefits
        throughput_improvement = len(batch.requests)  # Parallel processing
        resource_efficiency = len(batch.requests) / max(1, len(batch.requests) + processing_overhead)
        
        # Cost-benefit ratio
        benefits = throughput_improvement + resource_efficiency
        costs = processing_overhead + failure_risk
        benefit_ratio = benefits / max(1, costs)
        
        # Recommendation
        if benefit_ratio > 1.5 and direct_savings > 0:
            recommendation = "process_as_batch"
        elif benefit_ratio > 1.0:
            recommendation = "consider_batch"
        else:
            recommendation = "process_individually"
        
        return {
            'individual_cost': individual_cost,
            'batch_cost': batch_cost,
            'direct_savings': direct_savings,
            'throughput_improvement': throughput_improvement,
            'resource_efficiency': resource_efficiency,
            'benefit_ratio': benefit_ratio,
            'recommendation': recommendation,
            'risk_assessment': 'low' if len(batch.requests) <= 10 else 'medium'
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics and analytics"""
        total = max(1, self.metrics['total_requests'])
        cache_hit_ratio = self.metrics['cached_requests'] / total
        batching_efficiency = self.metrics['batched_requests'] / total
        
        # Calculate actual cost savings from batches
        total_individual_cost = 0
        total_optimized_cost = 0
        
        for batch in self.batch_history:
            if hasattr(batch, 'requests') and batch.requests:
                individual_cost = sum(req.estimated_cost for req in batch.requests)
                optimized_cost = batch.estimated_optimized_cost
                total_individual_cost += individual_cost
                total_optimized_cost += optimized_cost
        
        # Also check active batches
        for batch in self.active_batches.values():
            if hasattr(batch, 'requests') and batch.requests:
                individual_cost = sum(req.estimated_cost for req in batch.requests)
                optimized_cost = batch.estimated_optimized_cost
                total_individual_cost += individual_cost
                total_optimized_cost += optimized_cost
        
        if total_individual_cost > 0:
            cost_savings_percentage = ((total_individual_cost - total_optimized_cost) / total_individual_cost) * 100
        else:
            cost_savings_percentage = 0
        
        return {
            **self.metrics,
            'cache_hit_ratio': cache_hit_ratio,
            'batching_efficiency': batching_efficiency,
            'cost_savings_percentage': cost_savings_percentage,
            'total_individual_cost': total_individual_cost,
            'total_optimized_cost': total_optimized_cost,
            'active_batches': len(self.active_batches),
            'queue_size': len(self.pending_requests)
        }
    
    def optimize_configuration(self, recent_metrics: Dict[str, Any]):
        """Dynamically optimize batching configuration based on performance"""
        current_efficiency = recent_metrics.get('batching_efficiency', 0.5)
        current_cache_hit = recent_metrics.get('cache_hit_ratio', 0.3)
        
        # Adjust batch size based on efficiency
        if current_efficiency < 0.3:
            self.max_batch_size = max(5, self.max_batch_size - 2)
            logger.info("Reduced batch size due to low efficiency")
        elif current_efficiency > 0.8:
            self.max_batch_size = min(50, self.max_batch_size + 2)
            logger.info("Increased batch size due to high efficiency")
        
        # Adjust similarity threshold based on cache performance
        if current_cache_hit < 0.2:
            self.similarity_threshold = max(0.5, self.similarity_threshold - 0.1)
            logger.info("Reduced similarity threshold to improve cache hits")
        elif current_cache_hit > 0.6:
            self.similarity_threshold = min(0.9, self.similarity_threshold + 0.05)
            logger.info("Increased similarity threshold to improve quality")

class PriorityQueue:
    """Advanced priority queue with cost-aware scheduling"""
    
    def __init__(self, budget_threshold: float = 0.8):
        self.queue = []
        self.processed = set()
        self.budget_threshold = budget_threshold
        self.current_budget_used = 0.0
        self.total_budget = 10000.0  # Default monthly budget
        
        # Priority weights (configurable)
        self.weights = {
            'urgency': 0.4,
            'cost': 0.25,
            'wait_time': 0.2,
            'error_risk': 0.15
        }
    
    def enqueue(self, batch: Batch):
        """Add batch to priority queue"""
        priority_score = self._calculate_priority_score(batch)
        heapq.heappush(self.queue, (priority_score, batch))
    
    def dequeue(self) -> Optional[Batch]:
        """Get next batch from queue"""
        if not self.queue:
            return None
        
        # Check budget constraints
        priority_score, batch = heapq.heappop(self.queue)
        
        if self._exceeds_budget(batch):
            logger.warning(f"Batch {batch.id} exceeds budget threshold, re-queuing with lower priority")
            # Re-queue with lower priority
            new_score = priority_score * 0.5
            heapq.heappush(self.queue, (new_score, batch))
            return None
        
        self.processed.add(batch.id)
        return batch
    
    def _calculate_priority_score(self, batch: Batch) -> float:
        """Calculate priority score for scheduling"""
        # Urgency component (lower priority number = higher urgency)
        urgency_score = sum(4.0 - req.priority for req in batch.requests) / len(batch.requests)
        
        # Cost component (prefer lower cost)
        cost_score = 1.0 / (1.0 + batch.estimated_total_cost / 100.0)
        
        # Wait time component
        wait_time = (datetime.now() - batch.created_at).total_seconds()
        wait_score = min(1.0, wait_time / 3600.0)  # Cap at 1 hour
        
        # Error risk component (based on batch size and complexity)
        error_risk = min(1.0, len(batch.requests) / 20.0)
        risk_score = 1.0 - error_risk
        
        return (
            self.weights['urgency'] * urgency_score +
            self.weights['cost'] * cost_score +
            self.weights['wait_time'] * wait_score +
            self.weights['error_risk'] * risk_score
        )
    
    def _exceeds_budget(self, batch: Batch) -> bool:
        """Check if batch exceeds budget threshold"""
        projected_cost = self.current_budget_used + batch.estimated_total_cost
        return (projected_cost / self.total_budget) > self.budget_threshold
    
    def update_budget(self, amount: float):
        """Update current budget usage"""
        self.current_budget_used += amount

# Integration functions for existing pipeline
class SmartBatchingIntegration:
    """Integration with existing video generation pipeline"""
    
    def __init__(self, batcher: SmartBatcher):
        self.batcher = batcher
        self.rate_limiter = RateLimiter()
    
    async def process_video_requests(self, requests: List[Dict[str, Any]]) -> List[str]:
        """Process video requests through smart batching"""
        content_requests = []
        
        for req_data in requests:
            request = ContentRequest(
                id=req_data.get('id', str(uuid.uuid4())),
                content_type='video',
                prompt=req_data.get('prompt', ''),
                reference_images=req_data.get('reference_images', []),
                resolution=req_data.get('resolution', '1920x1080'),
                duration=req_data.get('duration', 30.0),
                engine=req_data.get('engine', 'default'),
                style_params=req_data.get('style_params', {}),
                priority=req_data.get('priority', 2),
                deadline=req_data.get('deadline')
            )
            content_requests.append(request)
        
        # Add all requests to batcher
        for request in content_requests:
            await self.batcher.add_request(request)
        
        # Build and process batches
        batches = await self.batcher.build_optimal_batches()
        results = []
        
        for batch in batches:
            # Rate limiting
            await self.rate_limiter.acquire()
            
            # Process batch
            result = await self.batcher.process_batch(batch)
            results.append(result)
        
        return [f"batch_{i+1}:{len(b.requests)}" for i, b in enumerate(batches)]

class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    async def acquire(self):
        """Acquire permission to make a request"""
        now = time.time()
        
        # Remove old requests outside time window
        while self.requests and now - self.requests[0] > self.time_window:
            self.requests.popleft()
        
        # Check if we can make a request
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Add current request
        self.requests.append(now)

# Example usage and testing
async def example_usage():
    """Example usage of the smart batching system"""
    
    # Initialize smart batcher
    cache_manager = CacheManager(memory_size=1000)
    batcher = SmartBatcher(
        max_batch_size=20,
        max_batch_cost=300.0,
        similarity_threshold=0.7,
        cache_manager=cache_manager
    )
    
    integration = SmartBatchingIntegration(batcher)
    
    # Create sample video requests
    video_requests = [
        {
            'id': 'video_1',
            'prompt': 'Professional office workspace with laptop and coffee',
            'resolution': '1920x1080',
            'duration': 30.0,
            'priority': 1,  # Urgent
            'style_params': {'video_style': 'corporate_professional'}
        },
        {
            'id': 'video_2',
            'prompt': 'Modern office setting with team collaboration',
            'resolution': '1920x1080',
            'duration': 45.0,
            'priority': 2,  # Normal
            'style_params': {'video_style': 'corporate_professional'}
        },
        {
            'id': 'video_3',
            'prompt': 'Dynamic tech startup environment',
            'resolution': '1920x1080',
            'duration': 60.0,
            'priority': 2,
            'style_params': {'video_style': 'tech_futuristic'}
        }
    ]
    
    # Process through smart batching
    results = await integration.process_video_requests(video_requests)
    
    # Get performance metrics
    metrics = batcher.get_performance_metrics()
    print(f"Smart Batching Results:")
    print(f"Total requests: {metrics['total_requests']}")
    print(f"Cache hit ratio: {metrics['cache_hit_ratio']:.2%}")
    print(f"Average batch size: {metrics['average_batch_size']:.1f}")
    print(f"Batching efficiency: {metrics['batching_efficiency']:.2%}")
    
    return results

if __name__ == "__main__":
    asyncio.run(example_usage())