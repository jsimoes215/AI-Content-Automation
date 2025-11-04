"""
Parallel Audio/Video Generation System with Rate Limiting

A comprehensive parallel generation system that handles bulk audio and video generation
with sophisticated rate limiting, resource pool management, and cost optimization.

Features:
- Async/await concurrent processing for audio and video generation
- Multi-dimensional rate limiting (sliding window + token bucket)
- Resource pool management with dynamic scaling
- Load balancing across generation tasks
- Cost optimization through smart batching
- Integration with existing content generation pipeline
- Comprehensive error handling and retry logic
- Real-time progress tracking and monitoring
"""

import asyncio
import logging
import json
import hashlib
import time
import random
from datetime import datetime, timedelta
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    Callable,
    Tuple,
    Set,
    AsyncIterator,
    Awaitable
)
from dataclasses import dataclass, field
from collections import defaultdict, deque
import aiohttp
import aiofiles
import uuid
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Enums and Constants
class GenerationType(Enum):
    """Supported generation types"""
    AUDIO = "audio"
    VIDEO = "video"


class TaskPriority(Enum):
    """Task priority levels for scheduling"""
    URGENT = 100      # Immediate processing required
    HIGH = 75         # High priority
    NORMAL = 50       # Standard priority
    LOW = 25          # Background processing
    BACKGROUND = 10   # Deferred processing


class Provider(Enum):
    """Supported AI providers"""
    MINIMAX = "minimax"
    RUNWAY = "runway"
    AZURE = "azure"
    AWS = "aws"


class ResourceType(Enum):
    """Resource pool types"""
    API_CALLS = "api_calls"
    CONCURRENT_JOBS = "concurrent_jobs"
    MEMORY = "memory"
    STORAGE = "storage"


# Data Models
@dataclass
class GenerationRequest:
    """Individual generation request"""
    id: str
    type: GenerationType
    provider: Provider
    prompt: str
    params: Dict[str, Any]
    priority: TaskPriority
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    estimated_cost: float = 0.0
    estimated_duration: float = 0.0
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.estimated_cost:
            self.estimated_cost = self._estimate_cost()
        if not self.estimated_duration:
            self.estimated_duration = self._estimate_duration()

    def _estimate_cost(self) -> float:
        """Estimate generation cost based on parameters"""
        base_cost = {
            GenerationType.AUDIO: 0.1,
            GenerationType.VIDEO: 0.5
        }
        provider_multiplier = {
            Provider.MINIMAX: 1.0,
            Provider.RUNWAY: 1.2,
            Provider.AZURE: 1.1,
            Provider.AWS: 1.15
        }
        return base_cost.get(self.type, 1.0) * provider_multiplier.get(self.provider, 1.0)

    def _estimate_duration(self) -> float:
        """Estimate generation duration in seconds"""
        base_duration = {
            GenerationType.AUDIO: 10.0,
            GenerationType.VIDEO: 60.0
        }
        complexity_factor = self.params.get('complexity', 1.0)
        return base_duration.get(self.type, 30.0) * complexity_factor

    def get_cache_key(self) -> str:
        """Generate cache key for content deduplication"""
        content = f"{self.type.value}:{self.provider.value}:{self.prompt}:{json.dumps(self.params, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class GenerationResult:
    """Generation result with metadata"""
    request_id: str
    success: bool
    output_path: Optional[str] = None
    error: Optional[str] = None
    duration: float = 0.0
    actual_cost: float = 0.0
    provider_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def cacheable(self) -> bool:
        """Whether result can be cached"""
        return self.success and self.output_path is not None


@dataclass
class BatchingConfig:
    """Configuration for smart batching"""
    max_jobs_per_batch: int = 25
    max_total_cost_per_batch: float = 300.0
    max_batch_duration: float = 300.0  # seconds
    max_concurrent_batches: int = 5
    submission_pacing_ms: int = 200  # jitter between submissions
    similarity_threshold: float = 0.8


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    # Sliding window (per-user) limits
    per_user_requests_per_minute: int = 60
    sliding_window_minutes: int = 1
    
    # Token bucket (project-level) limits  
    per_project_requests_per_minute: int = 300
    token_bucket_capacity: int = 300
    token_bucket_refill_rate: float = 5.0  # tokens per second
    
    # Burst protection
    max_burst_size: int = 50
    cooldown_period_seconds: int = 5


@dataclass
class ResourcePoolConfig:
    """Resource pool configuration"""
    max_api_calls: int = 100
    max_concurrent_jobs: int = 50
    max_memory_mb: int = 2048
    max_storage_gb: int = 100
    
    # Scaling parameters
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3
    scale_up_cooldown: int = 60  # seconds
    scale_down_cooldown: int = 300  # seconds


# Rate Limiting Implementations
class SlidingWindowRateLimiter:
    """Per-user sliding window rate limiter"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = asyncio.Lock()
    
    async def can_proceed(self, user_id: str) -> bool:
        """Check if request can proceed under rate limit"""
        async with self.lock:
            now = datetime.utcnow()
            window_start = now - timedelta(minutes=self.config.sliding_window_minutes)
            
            # Clean old requests
            user_requests = self.requests[user_id]
            while user_requests and user_requests[0] < window_start:
                user_requests.popleft()
            
            # Check if under limit
            if len(user_requests) < self.config.per_user_requests_per_minute:
                user_requests.append(now)
                return True
            
            return False
    
    async def wait_time(self, user_id: str) -> float:
        """Calculate wait time if rate limited"""
        async with self.lock:
            now = datetime.utcnow()
            user_requests = self.requests[user_id]
            
            if not user_requests:
                return 0.0
            
            oldest_request = user_requests[0]
            window_start = now - timedelta(minutes=self.config.sliding_window_minutes)
            
            if oldest_request < window_start:
                return 0.0
            
            time_in_window = (now - oldest_request).total_seconds()
            return max(0.0, self.config.sliding_window_minutes * 60 - time_in_window)


class TokenBucketRateLimiter:
    """Project-level token bucket rate limiter"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens: Dict[str, float] = defaultdict(lambda: config.token_bucket_capacity)
        self.last_refill: Dict[str, datetime] = defaultdict(lambda: datetime.utcnow())
        self.lock = asyncio.Lock()
    
    async def can_proceed(self, project_id: str) -> bool:
        """Check if request can proceed under token bucket"""
        async with self.lock:
            await self._refill_tokens(project_id)
            return self.tokens[project_id] >= 1.0
    
    async def _refill_tokens(self, project_id: str) -> None:
        """Refill tokens based on elapsed time"""
        now = datetime.utcnow()
        last_refill = self.last_refill[project_id]
        elapsed = (now - last_refill).total_seconds()
        
        # Calculate tokens to add
        tokens_to_add = elapsed * self.config.token_bucket_refill_rate
        new_tokens = min(
            self.config.token_bucket_capacity,
            self.tokens[project_id] + tokens_to_add
        )
        
        self.tokens[project_id] = new_tokens
        self.last_refill[project_id] = now
    
    async def consume(self, project_id: str) -> bool:
        """Consume one token"""
        async with self.lock:
            await self._refill_tokens(project_id)
            
            if self.tokens[project_id] >= 1.0:
                self.tokens[project_id] -= 1.0
                return True
            return False


class CombinedRateLimiter:
    """Combined rate limiter using both sliding window and token bucket"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.sliding_window = SlidingWindowRateLimiter(config)
        self.token_bucket = TokenBucketRateLimiter(config)
        self.user_cooldowns: Dict[str, datetime] = {}
        self.project_cooldowns: Dict[str, datetime] = {}
        self.lock = asyncio.Lock()
    
    async def can_proceed(self, user_id: str, project_id: str) -> Tuple[bool, float]:
        """Check if request can proceed and return wait time if needed"""
        now = datetime.utcnow()
        
        # Check cooldown periods
        if user_id in self.user_cooldowns:
            if now < self.user_cooldowns[user_id]:
                remaining = (self.user_cooldowns[user_id] - now).total_seconds()
                return False, remaining
        
        if project_id in self.project_cooldowns:
            if now < self.project_cooldowns[project_id]:
                remaining = (self.project_cooldowns[project_id] - now).total_seconds()
                return False, remaining
        
        # Check sliding window
        can_proceed_sliding = await self.sliding_window.can_proceed(user_id)
        if not can_proceed_sliding:
            wait_time = await self.sliding_window.wait_time(user_id)
            return False, wait_time
        
        # Check token bucket
        can_proceed_bucket = await self.token_bucket.can_proceed(project_id)
        if not can_proceed_bucket:
            return False, 0.5  # Short wait for token bucket
        
        return True, 0.0
    
    async def consume(self, user_id: str, project_id: str) -> bool:
        """Consume rate limit tokens"""
        # Only consume if both limiters allow it
        sliding_allowed = await self.sliding_window.can_proceed(user_id)
        bucket_allowed = await self.token_bucket.consume(project_id)
        
        if not sliding_allowed or not bucket_allowed:
            # Reset any consumed tokens if failed
            if bucket_allowed:
                # Re-add token to bucket
                self.token_bucket.tokens[project_id] += 1.0
            return False
        
        return True
    
    def set_cooldown(self, user_id: str = None, project_id: str = None, duration: float = 5.0) -> None:
        """Set cooldown period to prevent burst traffic"""
        now = datetime.utcnow()
        if user_id:
            self.user_cooldowns[user_id] = now + timedelta(seconds=duration)
        if project_id:
            self.project_cooldowns[project_id] = now + timedelta(seconds=duration)


# Resource Pool Management
class ResourcePool:
    """Dynamic resource pool for managing system resources"""
    
    def __init__(self, config: ResourcePoolConfig):
        self.config = config
        self.current_usage = {
            ResourceType.API_CALLS: 0,
            ResourceType.CONCURRENT_JOBS: 0,
            ResourceType.MEMORY: 0,  # MB
            ResourceType.STORAGE: 0  # GB
        }
        self.peak_usage = {
            ResourceType.API_CALLS: 0,
            ResourceType.CONCURRENT_JOBS: 0,
            ResourceType.MEMORY: 0,
            ResourceType.STORAGE: 0
        }
        self.last_scale_up = datetime.utcnow()
        self.last_scale_down = datetime.utcnow()
        self.lock = asyncio.Lock()
    
    async def acquire(self, resource_type: ResourceType, amount: float = 1.0) -> bool:
        """Acquire resource if available"""
        async with self.lock:
            current = self.current_usage[resource_type]
            max_amount = self._get_max_amount(resource_type)
            
            if current + amount <= max_amount:
                self.current_usage[resource_type] += amount
                self.peak_usage[resource_type] = max(self.peak_usage[resource_type], self.current_usage[resource_type])
                return True
            return False
    
    async def release(self, resource_type: ResourceType, amount: float = 1.0) -> None:
        """Release acquired resource"""
        async with self.lock:
            self.current_usage[resource_type] = max(0.0, self.current_usage[resource_type] - amount)
    
    def _get_max_amount(self, resource_type: ResourceType) -> float:
        """Get maximum amount for resource type"""
        mapping = {
            ResourceType.API_CALLS: self.config.max_api_calls,
            ResourceType.CONCURRENT_JOBS: self.config.max_concurrent_jobs,
            ResourceType.MEMORY: self.config.max_memory_mb,
            ResourceType.STORAGE: self.config.max_storage_gb
        }
        return mapping[resource_type]
    
    def get_utilization(self, resource_type: ResourceType) -> float:
        """Get current utilization percentage"""
        current = self.current_usage[resource_type]
        max_amount = self._get_max_amount(resource_type)
        return (current / max_amount) * 100.0 if max_amount > 0 else 0.0
    
    async def should_scale_up(self) -> bool:
        """Check if resources should be scaled up"""
        now = datetime.utcnow()
        if (now - self.last_scale_up).total_seconds() < self.config.scale_up_cooldown:
            return False
        
        # Check overall utilization
        high_utilization_resources = [
            rt for rt in ResourceType 
            if self.get_utilization(rt) > self.config.scale_up_threshold * 100
        ]
        
        return len(high_utilization_resources) > 0
    
    async def should_scale_down(self) -> bool:
        """Check if resources should be scaled down"""
        now = datetime.utcnow()
        if (now - self.last_scale_down).total_seconds() < self.config.scale_down_cooldown:
            return False
        
        # Check overall utilization
        low_utilization_resources = [
            rt for rt in ResourceType
            if self.get_utilization(rt) < self.config.scale_down_threshold * 100
        ]
        
        return len(low_utilization_resources) == len(ResourceType)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get resource pool statistics"""
        return {
            "current_usage": dict(self.current_usage),
            "peak_usage": dict(self.peak_usage),
            "utilization_percentages": {
                rt.name: self.get_utilization(rt) for rt in ResourceType
            },
            "last_scale_up": self.last_scale_up.isoformat(),
            "last_scale_down": self.last_scale_down.isoformat()
        }


# Smart Batching Logic
class SmartBatcher:
    """Intelligent batching system for cost optimization"""
    
    def __init__(self, config: BatchingConfig):
        self.config = config
        self.pending_requests: List[GenerationRequest] = []
        self.batch_history: List[Dict] = []
        self.similarity_cache: Dict[str, float] = {}
        self.lock = asyncio.Lock()
    
    async def add_request(self, request: GenerationRequest) -> None:
        """Add request to batching queue"""
        async with self.lock:
            self.pending_requests.append(request)
    
    async def get_next_batch(self) -> Optional[List[GenerationRequest]]:
        """Get next batch of compatible requests"""
        async with self.lock:
            if len(self.pending_requests) < 2:
                return None
            
            # Sort by priority and creation time
            sorted_requests = sorted(
                self.pending_requests,
                key=lambda r: (r.priority.value, r.created_at)
            )
            
            # Build batch
            batch = []
            anchor_request = sorted_requests[0]
            
            for request in sorted_requests[1:]:
                if self._can_add_to_batch(request, batch, anchor_request):
                    batch.append(request)
                    if len(batch) >= self.config.max_jobs_per_batch:
                        break
            
            if len(batch) >= 2:  # Minimum batch size
                # Remove from pending
                for req in batch:
                    self.pending_requests.remove(req)
                return batch
            return None
    
    def _can_add_to_batch(self, request: GenerationRequest, current_batch: List[GenerationRequest], anchor: GenerationRequest) -> bool:
        """Check if request can be added to current batch"""
        # Priority compatibility
        if abs(request.priority.value - anchor.priority.value) > 50:
            return False
        
        # Cost budget check
        total_cost = sum(r.estimated_cost for r in current_batch) + request.estimated_cost
        if total_cost > self.config.max_total_cost_per_batch:
            return False
        
        # Duration check
        total_duration = max(r.estimated_duration for r in current_batch + [request])
        if total_duration > self.config.max_batch_duration:
            return False
        
        # Similarity check
        if current_batch:
            max_similarity = max(
                self._calculate_similarity(request, r) for r in current_batch
            )
            if max_similarity < self.config.similarity_threshold:
                return False
        
        return True
    
    def _calculate_similarity(self, req1: GenerationRequest, req2: GenerationRequest) -> float:
        """Calculate similarity between two requests"""
        # Check cache
        cache_key = f"{req1.id}_{req2.id}"
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        similarity = 0.0
        factors = 0
        
        # Provider similarity
        if req1.provider == req2.provider:
            similarity += 0.3
        factors += 1
        
        # Type similarity
        if req1.type == req2.type:
            similarity += 0.2
        factors += 1
        
        # Parameter similarity
        common_params = set(req1.params.keys()) & set(req2.params.keys())
        if common_params:
            param_similarity = 0.0
            for param in common_params:
                if req1.params[param] == req2.params[param]:
                    param_similarity += 1.0
            similarity += (param_similarity / len(common_params)) * 0.3
        factors += 1
        
        # Duration similarity
        duration_diff = abs(req1.estimated_duration - req2.estimated_duration)
        duration_similarity = max(0.0, 1.0 - (duration_diff / max(req1.estimated_duration, req2.estimated_duration)))
        similarity += duration_similarity * 0.2
        factors += 1
        
        # Normalize
        final_similarity = similarity / factors if factors > 0 else 0.0
        
        # Cache result
        self.similarity_cache[cache_key] = final_similarity
        return final_similarity
    
    async def record_batch_result(self, batch: List[GenerationRequest], success_count: int, total_cost: float) -> None:
        """Record batch result for learning"""
        async with self.lock:
            self.batch_history.append({
                "batch_size": len(batch),
                "success_count": success_count,
                "total_cost": total_cost,
                "timestamp": datetime.utcnow(),
                "avg_cost_per_job": total_cost / len(batch) if batch else 0
            })
    
    def get_batching_stats(self) -> Dict[str, Any]:
        """Get batching performance statistics"""
        if not self.batch_history:
            return {"status": "no_batches_processed"}
        
        recent_batches = self.batch_history[-10:]  # Last 10 batches
        
        return {
            "total_batches": len(self.batch_history),
            "recent_avg_batch_size": sum(b["batch_size"] for b in recent_batches) / len(recent_batches),
            "recent_success_rate": sum(b["success_count"] for b in recent_batches) / sum(b["batch_size"] for b in recent_batches),
            "recent_avg_cost_per_job": sum(b["avg_cost_per_job"] for b in recent_batches) / len(recent_batches),
            "pending_requests": len(self.pending_requests)
        }


# Multi-Layer Cache
class MultiLayerCache:
    """Multi-layer caching system for generated content"""
    
    def __init__(self, memory_cache_size: int = 1000, redis_url: Optional[str] = None):
        self.memory_cache: Dict[str, Dict] = {}
        self.memory_cache_order = deque()
        self.memory_cache_size = memory_cache_size
        self.redis_url = redis_url
        self.redis_client = None
        self.hit_stats = {
            "memory_hits": 0,
            "redis_hits": 0,
            "misses": 0,
            "total_requests": 0
        }
        self.lock = asyncio.Lock()
    
    async def initialize_redis(self) -> None:
        """Initialize Redis connection if available"""
        if not self.redis_url:
            return
        
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Redis cache initialized")
        except ImportError:
            logger.warning("Redis not available, using memory cache only")
        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
    
    async def get(self, cache_key: str) -> Optional[Dict]:
        """Get cached content from any layer"""
        self.hit_stats["total_requests"] += 1
        
        # Check memory cache first
        async with self.lock:
            if cache_key in self.memory_cache:
                # Move to end (LRU)
                self.memory_cache_order.move_to_end(cache_key)
                self.hit_stats["memory_hits"] += 1
                return self.memory_cache[cache_key]
        
        # Check Redis cache
        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    self.hit_stats["redis_hits"] += 1
                    return json.loads(cached_data)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        self.hit_stats["misses"] += 1
        return None
    
    async def set(self, cache_key: str, data: Dict, ttl_seconds: int = 3600) -> None:
        """Set cached content in all layers"""
        # Store in memory cache
        async with self.lock:
            if cache_key in self.memory_cache:
                self.memory_cache_order.move_to_end(cache_key)
            else:
                # Evict oldest if at capacity
                if len(self.memory_cache) >= self.memory_cache_size:
                    oldest_key = self.memory_cache_order.popleft()
                    del self.memory_cache[oldest_key]
            
            self.memory_cache[cache_key] = data
            self.memory_cache_order.append(cache_key)
        
        # Store in Redis cache
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    cache_key, 
                    ttl_seconds, 
                    json.dumps(data, default=str)
                )
            except Exception as e:
                logger.error(f"Redis set error: {e}")
    
    async def invalidate(self, cache_key: str) -> None:
        """Invalidate cache entry from all layers"""
        # Remove from memory cache
        async with self.lock:
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
            if cache_key in self.memory_cache_order:
                self.memory_cache_order.remove(cache_key)
        
        # Remove from Redis cache
        if self.redis_client:
            try:
                await self.redis_client.delete(cache_key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
    
    def get_hit_ratio(self) -> float:
        """Get cache hit ratio"""
        total = self.hit_stats["total_requests"]
        if total == 0:
            return 0.0
        hits = self.hit_stats["memory_hits"] + self.hit_stats["redis_hits"]
        return (hits / total) * 100.0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics"""
        return {
            **self.hit_stats,
            "hit_ratio_percent": self.get_hit_ratio(),
            "memory_cache_size": len(self.memory_cache),
            "memory_cache_capacity": self.memory_cache_size,
            "redis_available": self.redis_client is not None
        }


# Load Balancer
class LoadBalancer:
    """Load balancer for distributing generation tasks across providers and workers"""
    
    def __init__(self, provider_weights: Dict[Provider, float] = None):
        self.provider_weights = provider_weights or {
            Provider.MINIMAX: 1.0,
            Provider.RUNWAY: 0.8,
            Provider.AZURE: 0.7,
            Provider.AWS: 0.6
        }
        self.provider_loads: Dict[Provider, float] = defaultdict(float)
        self.provider_health: Dict[Provider, bool] = {p: True for p in Provider}
        self.request_counts: Dict[Provider, int] = defaultdict(int)
        self.error_counts: Dict[Provider, int] = defaultdict(int)
        self.lock = asyncio.Lock()
    
    async def select_provider(self, request: GenerationRequest) -> Provider:
        """Select optimal provider for request"""
        async with self.lock:
            # Filter healthy providers
            healthy_providers = [
                p for p, is_healthy in self.provider_health.items() 
                if is_healthy
            ]
            
            if not healthy_providers:
                # All providers unhealthy, use all with reduced weight
                healthy_providers = list(Provider)
            
            # Calculate weighted scores
            provider_scores = {}
            for provider in healthy_providers:
                base_weight = self.provider_weights[provider]
                load_factor = 1.0 / (1.0 + self.provider_loads[provider])
                error_factor = 1.0 - (self.error_counts[provider] / max(1, self.request_counts[provider]))
                request_cost = 1.0 / (request.estimated_cost + 0.1)  # Prefer providers for expensive requests
                
                score = base_weight * load_factor * error_factor * request_cost
                provider_scores[provider] = score
            
            # Select provider with highest score
            selected_provider = max(provider_scores.items(), key=lambda x: x[1])[0]
            
            # Update load
            self.provider_loads[selected_provider] += request.estimated_duration
            self.request_counts[selected_provider] += 1
            
            return selected_provider
    
    async def report_success(self, provider: Provider, cost: float) -> None:
        """Report successful completion"""
        async with self.lock:
            # Update error rate
            if provider in self.error_counts:
                self.error_counts[provider] = max(0, self.error_counts[provider] - 1)
    
    async def report_failure(self, provider: Provider, error: str) -> None:
        """Report failure and update provider health"""
        async with self.lock:
            self.error_counts[provider] += 1
            
            # Mark provider as unhealthy if error rate too high
            total_requests = max(1, self.request_counts[provider])
            error_rate = self.error_counts[provider] / total_requests
            
            if error_rate > 0.5:  # More than 50% error rate
                self.provider_health[provider] = False
                logger.warning(f"Provider {provider.value} marked unhealthy due to high error rate: {error_rate:.2%}")
    
    async def health_check(self) -> None:
        """Perform health check on all providers"""
        async with self.lock:
            for provider in Provider:
                try:
                    # Simple health check (ping provider API)
                    healthy = await self._ping_provider(provider)
                    self.provider_health[provider] = healthy
                    
                    if not healthy:
                        logger.warning(f"Provider {provider.value} health check failed")
                except Exception as e:
                    logger.error(f"Health check error for {provider.value}: {e}")
                    self.provider_health[provider] = False
    
    async def _ping_provider(self, provider: Provider) -> bool:
        """Simple health check for provider"""
        # This would implement actual provider health checking
        # For now, assume all providers are healthy
        return True
    
    def get_load_stats(self) -> Dict[str, Any]:
        """Get load balancing statistics"""
        return {
            "provider_weights": dict(self.provider_weights),
            "provider_loads": dict(self.provider_loads),
            "provider_health": dict(self.provider_health),
            "request_counts": dict(self.request_counts),
            "error_counts": dict(self.error_counts),
            "error_rates": {
                p.name: self.error_counts[p] / max(1, self.request_counts[p])
                for p in Provider
            }
        }


# Cost Monitor
class CostMonitor:
    """Real-time cost monitoring and alerting"""
    
    def __init__(self, budget_threshold: float = 0.8):
        self.budget_threshold = budget_threshold
        self.cost_history: List[Dict] = []
        self.alert_callbacks: List[Callable] = []
        self.current_spend = 0.0
        self.daily_spend = 0.0
        self.monthly_spend = 0.0
        self.lock = asyncio.Lock()
    
    async def record_generation(self, request: GenerationRequest, result: GenerationResult) -> None:
        """Record generation cost"""
        async with self.lock:
            cost_entry = {
                "timestamp": datetime.utcnow(),
                "request_id": request.id,
                "provider": request.provider.value,
                "type": request.type.value,
                "cost": result.actual_cost,
                "duration": result.duration,
                "success": result.success
            }
            
            self.cost_history.append(cost_entry)
            self.current_spend += result.actual_cost
            
            # Update daily/monthly spend
            self.daily_spend += result.actual_cost
            self.monthly_spend += result.actual_cost
            
            # Check for alerts
            await self._check_alerts(cost_entry)
    
    async def _check_alerts(self, cost_entry: Dict) -> None:
        """Check if cost alerts should be triggered"""
        # Check for rapid cost increase
        recent_costs = [
            entry["cost"] for entry in self.cost_history[-10:]
            if (datetime.utcnow() - entry["timestamp"]).total_seconds() < 300  # Last 5 minutes
        ]
        
        if len(recent_costs) > 5:
            avg_recent = sum(recent_costs) / len(recent_costs)
            if avg_recent > 10.0:  # More than $10 per generation
                await self._trigger_alert("HIGH_COST_RATE", {
                    "average_cost": avg_recent,
                    "recent_costs": recent_costs
                })
    
    def register_alert_callback(self, callback: Callable) -> None:
        """Register callback for cost alerts"""
        self.alert_callbacks.append(callback)
    
    async def _trigger_alert(self, alert_type: str, data: Dict) -> None:
        """Trigger cost alert"""
        logger.warning(f"Cost alert: {alert_type} - {data}")
        for callback in self.alert_callbacks:
            try:
                await callback(alert_type, data)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
    
    def get_cost_stats(self) -> Dict[str, Any]:
        """Get cost monitoring statistics"""
        if not self.cost_history:
            return {
                "current_spend": self.current_spend,
                "daily_spend": self.daily_spend,
                "monthly_spend": self.monthly_spend,
                "status": "no_data"
            }
        
        recent_history = self.cost_history[-100:]  # Last 100 operations
        
        return {
            "current_spend": self.current_spend,
            "daily_spend": self.daily_spend,
            "monthly_spend": self.monthly_spend,
            "recent_operations": len(recent_history),
            "recent_success_rate": sum(1 for entry in recent_history if entry["success"]) / len(recent_history),
            "avg_cost_per_operation": sum(entry["cost"] for entry in recent_history) / len(recent_history),
            "total_operations": len(self.cost_history),
            "cost_trend": self._calculate_cost_trend()
        }
    
    def _calculate_cost_trend(self) -> str:
        """Calculate cost trend over time"""
        if len(self.cost_history) < 10:
            return "insufficient_data"
        
        half_point = len(self.cost_history) // 2
        first_half = self.cost_history[:half_point]
        second_half = self.cost_history[half_point:]
        
        first_avg = sum(entry["cost"] for entry in first_half) / len(first_half)
        second_avg = sum(entry["cost"] for entry in second_half) / len(second_half)
        
        change_ratio = (second_avg - first_avg) / first_avg
        
        if change_ratio > 0.1:
            return "increasing"
        elif change_ratio < -0.1:
            return "decreasing"
        else:
            return "stable"


# Main Parallel Generator
class ParallelGenerator:
    """Main parallel generation orchestrator"""
    
    def __init__(
        self,
        rate_limit_config: RateLimitConfig = None,
        batching_config: BatchingConfig = None,
        resource_config: ResourcePoolConfig = None,
        redis_url: str = None
    ):
        # Initialize components
        self.rate_limiter = CombinedRateLimiter(rate_limit_config or RateLimitConfig())
        self.batcher = SmartBatcher(batching_config or BatchingConfig())
        self.resource_pool = ResourcePool(resource_config or ResourcePoolConfig())
        self.cache = MultiLayerCache(redis_url=redis_url)
        self.load_balancer = LoadBalancer()
        self.cost_monitor = CostMonitor()
        
        # Generation state
        self.active_generations: Dict[str, GenerationRequest] = {}
        self.generation_results: Dict[str, GenerationResult] = {}
        self.progress_callbacks: List[Callable] = []
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        self.running = False
        
        logger.info("ParallelGenerator initialized with rate limiting and batching")
    
    async def start(self) -> None:
        """Start the generator system"""
        if self.running:
            return
        
        self.running = True
        await self.cache.initialize_redis()
        
        # Start background tasks
        self.background_tasks.add(asyncio.create_task(self._rate_limit_cleanup_task()))
        self.background_tasks.add(asyncio.create_task(self._resource_monitoring_task()))
        self.background_tasks.add(asyncio.create_task(self._load_balancing_task()))
        self.background_tasks.add(asyncio.create_task(self._cost_monitoring_task()))
        
        logger.info("ParallelGenerator started")
    
    async def stop(self) -> None:
        """Stop the generator system"""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.background_tasks.clear()
        logger.info("ParallelGenerator stopped")
    
    async def generate(
        self,
        requests: List[GenerationRequest],
        progress_callback: Optional[Callable] = None
    ) -> List[GenerationResult]:
        """Generate content from requests with full parallel processing"""
        
        # Register progress callback
        if progress_callback:
            self.progress_callbacks.append(progress_callback)
        
        # Start generator if not running
        if not self.running:
            await self.start()
        
        results = []
        
        # Add requests to batcher
        for request in requests:
            await self.batcher.add_request(request)
        
        # Process batches concurrently
        batch_tasks = []
        max_concurrent_batches = min(
            self.batcher.config.max_concurrent_batches,
            self.resource_pool.config.max_concurrent_jobs
        )
        
        semaphore = asyncio.Semaphore(max_concurrent_batches)
        
        for _ in range(max_concurrent_batches):
            task = asyncio.create_task(self._process_batches(semaphore))
            batch_tasks.append(task)
        
        # Wait for all batches to complete
        batch_results = await asyncio.gather(*batch_tasks)
        
        # Flatten results
        for batch_result_list in batch_results:
            results.extend(batch_result_list)
        
        # Clean up progress callback
        if progress_callback:
            self.progress_callbacks.remove(progress_callback)
        
        return results
    
    async def _process_batches(self, semaphore: asyncio.Semaphore) -> List[GenerationResult]:
        """Process batches with rate limiting and resource management"""
        results = []
        
        while self.running:
            # Get next batch
            batch = await self.batcher.get_next_batch()
            if not batch:
                break
            
            async with semaphore:
                # Process batch with rate limiting
                batch_results = await self._process_batch_with_limits(batch)
                results.extend(batch_results)
        
        return results
    
    async def _process_batch_with_limits(self, batch: List[GenerationRequest]) -> List[GenerationResult]:
        """Process batch with comprehensive rate limiting"""
        results = []
        
        # Apply submission pacing
        await asyncio.sleep(random.uniform(0, self.batcher.config.submission_pacing_ms / 1000.0))
        
        for request in batch:
            try:
                # Check rate limits
                user_id = request.user_id or "anonymous"
                project_id = request.project_id or "default"
                
                can_proceed, wait_time = await self.rate_limiter.can_proceed(user_id, project_id)
                
                if not can_proceed:
                    if wait_time > 0:
                        logger.info(f"Rate limited, waiting {wait_time:.2f}s for request {request.id}")
                        await asyncio.sleep(wait_time)
                    else:
                        await asyncio.sleep(0.5)  # Short wait for token bucket
                    
                    # Recheck after wait
                    can_proceed, _ = await self.rate_limiter.can_proceed(user_id, project_id)
                    if not can_proceed:
                        # Skip this request
                        results.append(GenerationResult(
                            request_id=request.id,
                            success=False,
                            error="Rate limited after wait"
                        ))
                        continue
                
                # Check resource availability
                can_acquire = await self.resource_pool.acquire(ResourceType.API_CALLS)
                if not can_acquire:
                    # Wait and retry
                    await asyncio.sleep(1.0)
                    can_acquire = await self.resource_pool.acquire(ResourceType.API_CALLS)
                    if not can_acquire:
                        results.append(GenerationResult(
                            request_id=request.id,
                            success=False,
                            error="Resource pool exhausted"
                        ))
                        continue
                
                # Process the request
                result = await self._generate_single(request)
                results.append(result)
                
                # Release resources
                await self.resource_pool.release(ResourceType.API_CALLS)
                
                # Record cost
                await self.cost_monitor.record_generation(request, result)
                
            except Exception as e:
                logger.error(f"Error processing request {request.id}: {e}")
                results.append(GenerationResult(
                    request_id=request.id,
                    success=False,
                    error=str(e)
                ))
        
        return results
    
    async def _generate_single(self, request: GenerationRequest) -> GenerationResult:
        """Generate content for a single request"""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = request.get_cache_key()
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return GenerationResult(
                    request_id=request.id,
                    success=True,
                    output_path=cached_result.get("output_path"),
                    duration=0.0,  # Cache hit, no generation time
                    actual_cost=0.0,  # Cache hit, no cost
                    provider_metadata={"source": "cache", "cache_key": cache_key}
                )
            
            # Select optimal provider
            selected_provider = await self.load_balancer.select_provider(request)
            
            # Generate content based on type
            if request.type == GenerationType.AUDIO:
                result = await self._generate_audio(request, selected_provider)
            elif request.type == GenerationType.VIDEO:
                result = await self._generate_video(request, selected_provider)
            else:
                raise ValueError(f"Unsupported generation type: {request.type}")
            
            # Cache successful results
            if result.success and result.output_path:
                cache_data = {
                    "output_path": result.output_path,
                    "metadata": result.provider_metadata,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self.cache.set(cache_key, cache_data, ttl_seconds=3600)
            
            # Update provider stats
            if result.success:
                await self.load_balancer.report_success(selected_provider, result.actual_cost)
            else:
                await self.load_balancer.report_failure(selected_provider, result.error or "Unknown error")
            
            return result
            
        except Exception as e:
            error_result = GenerationResult(
                request_id=request.id,
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )
            await self.load_balancer.report_failure(request.provider, str(e))
            return error_result
    
    async def _generate_audio(self, request: GenerationRequest, provider: Provider) -> GenerationResult:
        """Generate audio using specified provider"""
        # This would integrate with actual audio generation APIs
        # For now, simulate the process
        
        logger.info(f"Generating audio with {provider.value} for request {request.id}")
        
        # Simulate API call with random delay
        await asyncio.sleep(random.uniform(1.0, 3.0))
        
        # Simulate occasional failures
        if random.random() < 0.05:  # 5% failure rate
            raise Exception("Simulated audio generation failure")
        
        # Simulate success
        return GenerationResult(
            request_id=request.id,
            success=True,
            output_path=f"/generated/audio/{request.id}.mp3",
            duration=random.uniform(5.0, 30.0),
            actual_cost=request.estimated_cost,
            provider_metadata={
                "provider": provider.value,
                "model": "audio-gen-v1",
                "quality": "high"
            }
        )
    
    async def _generate_video(self, request: GenerationRequest, provider: Provider) -> GenerationResult:
        """Generate video using specified provider"""
        # This would integrate with actual video generation APIs
        # For now, simulate the process
        
        logger.info(f"Generating video with {provider.value} for request {request.id}")
        
        # Simulate API call with random delay based on estimated duration
        generation_time = min(request.estimated_duration, 30.0)  # Cap at 30s for simulation
        await asyncio.sleep(random.uniform(generation_time * 0.1, generation_time * 0.2))
        
        # Simulate occasional failures
        if random.random() < 0.1:  # 10% failure rate
            raise Exception("Simulated video generation failure")
        
        # Simulate success
        return GenerationResult(
            request_id=request.id,
            success=True,
            output_path=f"/generated/video/{request.id}.mp4",
            duration=request.estimated_duration,
            actual_cost=request.estimated_cost,
            provider_metadata={
                "provider": provider.value,
                "model": "video-gen-v2",
                "resolution": request.params.get("resolution", "1080p"),
                "duration": request.estimated_duration
            }
        )
    
    # Background Tasks
    async def _rate_limit_cleanup_task(self) -> None:
        """Background task to clean up rate limiters"""
        while self.running:
            try:
                # Clean up old cooldown periods
                current_time = datetime.utcnow()
                
                # This would be implemented with proper cleanup logic
                await asyncio.sleep(60)  # Run every minute
            except Exception as e:
                logger.error(f"Rate limit cleanup error: {e}")
                await asyncio.sleep(10)
    
    async def _resource_monitoring_task(self) -> None:
        """Background task to monitor resource usage"""
        while self.running:
            try:
                # Check if scaling is needed
                if await self.resource_pool.should_scale_up():
                    logger.info("Resource pool scale up triggered")
                    # Implementation would adjust resource limits
                
                if await self.resource_pool.should_scale_down():
                    logger.info("Resource pool scale down triggered")
                    # Implementation would adjust resource limits
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def _load_balancing_task(self) -> None:
        """Background task for load balancing"""
        while self.running:
            try:
                await self.load_balancer.health_check()
                await asyncio.sleep(60)  # Health check every minute
            except Exception as e:
                logger.error(f"Load balancing error: {e}")
                await asyncio.sleep(10)
    
    async def _cost_monitoring_task(self) -> None:
        """Background task for cost monitoring"""
        while self.running:
            try:
                # Get current cost stats
                cost_stats = self.cost_monitor.get_cost_stats()
                
                # Log cost warnings if needed
                if cost_stats.get("cost_trend") == "increasing":
                    logger.warning("Cost trend increasing - consider optimization")
                
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Cost monitoring error: {e}")
                await asyncio.sleep(30)
    
    # Public API Methods
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        return {
            "running": self.running,
            "resource_pool": self.resource_pool.get_stats(),
            "cache": self.cache.get_cache_stats(),
            "load_balancer": self.load_balancer.get_load_stats(),
            "cost_monitor": self.cost_monitor.get_cost_stats(),
            "batcher": self.batcher.get_batching_stats(),
            "active_generations": len(self.active_generations),
            "total_results": len(self.generation_results)
        }
    
    def add_progress_callback(self, callback: Callable) -> None:
        """Add progress callback for real-time updates"""
        self.progress_callbacks.append(callback)
    
    def remove_progress_callback(self, callback: Callable) -> None:
        """Remove progress callback"""
        if callback in self.progress_callbacks:
            self.progress_callbacks.remove(callback)


# Helper Functions
def create_audio_request(
    prompt: str,
    provider: Provider = Provider.MINIMAX,
    priority: TaskPriority = TaskPriority.NORMAL,
    **params
) -> GenerationRequest:
    """Create an audio generation request"""
    return GenerationRequest(
        id="",  # Will be auto-generated
        type=GenerationType.AUDIO,
        provider=provider,
        prompt=prompt,
        params=params,
        priority=priority
    )


def create_video_request(
    prompt: str,
    provider: Provider = Provider.MINIMAX,
    priority: TaskPriority = TaskPriority.NORMAL,
    **params
) -> GenerationRequest:
    """Create a video generation request"""
    return GenerationRequest(
        id="",  # Will be auto-generated
        type=GenerationType.VIDEO,
        provider=provider,
        prompt=prompt,
        params=params,
        priority=priority
    )


# Example Usage
async def example_parallel_generation():
    """Example of using the parallel generator"""
    
    # Initialize generator
    generator = ParallelGenerator()
    await generator.start()
    
    try:
        # Create test requests
        requests = []
        
        # Audio requests
        for i in range(5):
            requests.append(create_audio_request(
                prompt=f"Create a relaxing ambient sound {i}",
                priority=TaskPriority.NORMAL,
                duration=10,
                format="mp3"
            ))
        
        # Video requests
        for i in range(3):
            requests.append(create_video_request(
                prompt=f"Generate a nature scene with flowing water {i}",
                priority=TaskPriority.HIGH,
                resolution="1080p",
                duration=30
            ))
        
        # Define progress callback
        async def progress_callback(request_id: str, progress: float, status: str):
            print(f"Progress: {request_id} - {progress:.1%} - {status}")
        
        # Generate with progress tracking
        results = await generator.generate(requests, progress_callback=progress_callback)
        
        # Display results
        print(f"\nGenerated {len(results)} items:")
        for result in results:
            status = "SUCCESS" if result.success else "FAILED"
            cost = f"${result.actual_cost:.3f}" if result.success else "N/A"
            print(f"  {result.request_id}: {status} - {cost}")
        
        # Show system stats
        stats = await generator.get_system_stats()
        print(f"\nSystem Statistics:")
        print(f"Cache hit ratio: {stats['cache']['hit_ratio_percent']:.1f}%")
        print(f"Current spend: ${stats['cost_monitor']['current_spend']:.2f}")
        print(f"Resource utilization: {stats['resource_pool']['utilization_percentages']}")
        
    finally:
        await generator.stop()


if __name__ == "__main__":
    asyncio.run(example_parallel_generation())