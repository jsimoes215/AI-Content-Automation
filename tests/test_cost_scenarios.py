"""
Cost Optimization Scenario Tests

This module validates the cost optimization algorithms with real-world scenarios,
testing different content types and validating the 20-50% cost reduction claims.
"""

import asyncio
import time
import json
import math
import random
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import pytest
import sys
import os

# Add the code directory to path to import the smart batcher
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'code'))

from smart_batcher import SmartBatcher, ContentRequest, CacheManager, Batch


@dataclass
class CostTestResult:
    """Results from a cost optimization test"""
    scenario_name: str
    total_requests: int
    baseline_cost: float
    optimized_cost: float
    cost_reduction_percentage: float
    api_calls_baseline: int
    api_calls_optimized: int
    api_reduction_percentage: float
    cache_hit_ratio: float
    average_batch_size: float
    processing_time: float
    error_rate: float
    throughput: float
    cost_per_unit: float


class CostScenarioValidator:
    """Validates cost optimization across different scenarios"""
    
    def __init__(self):
        self.results = []
        self.baseline_costs = {
            'video': 0.10,  # per second
            'image': 0.02,  # per image
            'audio': 0.05   # per second
        }
        self.resolution_multipliers = {
            '1920x1080': 1.0,
            '1080x1920': 1.0,
            '3840x2160': 2.0,
            '1024x1024': 0.5
        }
        
    def calculate_baseline_cost(self, requests: List[Dict]) -> Tuple[float, int]:
        """Calculate baseline cost (no optimization)"""
        total_cost = 0
        api_calls = 0
        
        for req in requests:
            content_type = req['content_type']
            duration = req.get('duration', 30.0)
            resolution = req.get('resolution', '1920x1080')
            
            base_cost = self.baseline_costs.get(content_type, 0.1)
            resolution_mult = self.resolution_multipliers.get(resolution, 1.0)
            
            # For images, duration doesn't apply
            if content_type == 'image':
                duration = 1.0
                
            cost = base_cost * duration * resolution_mult
            total_cost += cost
            api_calls += 1  # One API call per request without batching
            
        return total_cost, api_calls
    
    async def test_video_content_scenarios(self) -> List[CostTestResult]:
        """Test cost optimization for video content scenarios"""
        print("\n=== Video Content Scenarios ===")
        results = []
        
        # Scenario 1: Corporate Training Videos (High Similarity)
        print("Testing corporate training videos...")
        corporate_requests = self._generate_corporate_videos(50)
        result = await self._run_scenario_test(
            "Corporate Training Videos",
            corporate_requests,
            content_type='video'
        )
        results.append(result)
        
        # Scenario 2: Social Media Content (Medium Similarity) 
        print("Testing social media content...")
        social_requests = self._generate_social_videos(75)
        result = await self._run_scenario_test(
            "Social Media Content",
            social_requests,
            content_type='video'
        )
        results.append(result)
        
        # Scenario 3: Product Marketing Videos (Low Similarity)
        print("Testing product marketing videos...")
        marketing_requests = self._generate_marketing_videos(30)
        result = await self._run_scenario_test(
            "Product Marketing Videos",
            marketing_requests,
            content_type='video'
        )
        results.append(result)
        
        return results
    
    async def test_image_content_scenarios(self) -> List[CostTestResult]:
        """Test cost optimization for image content scenarios"""
        print("\n=== Image Content Scenarios ===")
        results = []
        
        # Scenario 1: E-commerce Product Images (High Similarity)
        print("Testing e-commerce product images...")
        ecommerce_requests = self._generate_ecommerce_images(100)
        result = await self._run_scenario_test(
            "E-commerce Product Images",
            ecommerce_requests,
            content_type='image'
        )
        results.append(result)
        
        # Scenario 2: Stock Photography (Medium Similarity)
        print("Testing stock photography...")
        stock_requests = self._generate_stock_images(60)
        result = await self._run_scenario_test(
            "Stock Photography",
            stock_requests,
            content_type='image'
        )
        results.append(result)
        
        # Scenario 3: Custom Artwork (Low Similarity)
        print("Testing custom artwork...")
        custom_requests = self._generate_custom_images(25)
        result = await self._run_scenario_test(
            "Custom Artwork",
            custom_requests,
            content_type='image'
        )
        results.append(result)
        
        return results
    
    async def test_audio_content_scenarios(self) -> List[CostTestResult]:
        """Test cost optimization for audio content scenarios"""
        print("\n=== Audio Content Scenarios ===")
        results = []
        
        # Scenario 1: Podcast Episodes (High Similarity)
        print("Testing podcast episodes...")
        podcast_requests = self._generate_podcast_audio(40)
        result = await self._run_scenario_test(
            "Podcast Episodes",
            podcast_requests,
            content_type='audio'
        )
        results.append(result)
        
        # Scenario 2: Voice-over Content (Medium Similarity)
        print("Testing voice-over content...")
        voice_requests = self._generate_voiceover_audio(80)
        result = await self._run_scenario_test(
            "Voice-over Content",
            voice_requests,
            content_type='audio'
        )
        results.append(result)
        
        # Scenario 3: Music Production (Low Similarity)
        print("Testing music production...")
        music_requests = self._generate_music_audio(20)
        result = await self._run_scenario_test(
            "Music Production",
            music_requests,
            content_type='audio'
        )
        results.append(result)
        
        return results
    
    async def test_mixed_content_scenarios(self) -> List[CostTestResult]:
        """Test cost optimization for mixed content scenarios"""
        print("\n=== Mixed Content Scenarios ===")
        results = []
        
        # Scenario 1: Multi-format Campaign (High Volume)
        print("Testing multi-format campaign...")
        campaign_requests = self._generate_mixed_campaign(150)
        result = await self._run_scenario_test(
            "Multi-format Campaign",
            campaign_requests,
            content_type='mixed'
        )
        results.append(result)
        
        # Scenario 2: Content Library Expansion
        print("Testing content library expansion...")
        library_requests = self._generate_library_expansion(120)
        result = await self._run_scenario_test(
            "Content Library Expansion",
            library_requests,
            content_type='mixed'
        )
        results.append(result)
        
        return results
    
    async def test_stress_scenarios(self) -> List[CostTestResult]:
        """Test cost optimization under stress conditions"""
        print("\n=== Stress Test Scenarios ===")
        results = []
        
        # Scenario 1: High Volume Burst
        print("Testing high volume burst...")
        burst_requests = self._generate_burst_load(500)
        result = await self._run_scenario_test(
            "High Volume Burst",
            burst_requests,
            content_type='mixed',
            stress_test=True
        )
        results.append(result)
        
        # Scenario 2: Complex Content Mix
        print("Testing complex content mix...")
        complex_requests = self._generate_complex_mix(200)
        result = await self._run_scenario_test(
            "Complex Content Mix",
            complex_requests,
            content_type='mixed',
            stress_test=True
        )
        results.append(result)
        
        return results
    
    async def _run_scenario_test(
        self, 
        scenario_name: str, 
        requests: List[Dict], 
        content_type: str,
        stress_test: bool = False
    ) -> CostTestResult:
        """Run a cost optimization test for a specific scenario"""
        
        # Calculate baseline cost
        baseline_cost, baseline_api_calls = self.calculate_baseline_cost(requests)
        
        # Set up smart batcher with different configurations for stress tests
        if stress_test:
            batcher = SmartBatcher(
                max_batch_size=50,  # Larger batches for stress
                max_batch_cost=1000.0,
                similarity_threshold=0.3,  # Much more lenient for stress
                cache_manager=CacheManager(memory_size=2000)
            )
        else:
            batcher = SmartBatcher(
                max_batch_size=25,
                max_batch_cost=500.0,
                similarity_threshold=0.4,  # More lenient for better batching
                cache_manager=CacheManager(memory_size=1000)
            )
        
        # Pre-populate cache with some common content to simulate real-world usage
        await self._prepopulate_cache(batcher, content_type)
        
        # Convert requests to ContentRequest objects
        content_requests = []
        for i, req_data in enumerate(requests):
            request = ContentRequest(
                id=req_data.get('id', f"{content_type}_{i}"),
                content_type=content_type,
                prompt=req_data.get('prompt', ''),
                reference_images=req_data.get('reference_images', []),
                resolution=req_data.get('resolution', '1920x1080'),
                duration=req_data.get('duration', 30.0),
                engine=req_data.get('engine', 'default'),
                style_params=req_data.get('style_params', {}),
                priority=req_data.get('priority', 2)
            )
            content_requests.append(request)
        
        # Run optimization
        start_time = time.time()
        
        # Add requests to batcher
        for request in content_requests:
            await batcher.add_request(request)
        
        # Build and process batches
        batches = await batcher.build_optimal_batches()
        total_processed = 0
        total_errors = 0
        
        for batch in batches:
            result = await batcher.process_batch(batch)
            total_processed += result.get('requests', 0)
            if result.get('status') == 'failed':
                total_errors += 1
            # Add batch to history for metrics calculation
            batcher.batch_history.append(batch)
        
        processing_time = time.time() - start_time
        
        # Calculate optimized cost (with batching savings)
        optimized_cost = sum(b.estimated_optimized_cost for b in batches) if batches else baseline_cost
        optimized_api_calls = len(batches)  # One API call per batch
        
        # Get performance metrics
        metrics = batcher.get_performance_metrics()
        
        # Calculate cost reduction
        cost_reduction = ((baseline_cost - optimized_cost) / baseline_cost) * 100
        api_reduction = ((baseline_api_calls - optimized_api_calls) / baseline_api_calls) * 100
        
        # Create result
        result = CostTestResult(
            scenario_name=scenario_name,
            total_requests=len(requests),
            baseline_cost=baseline_cost,
            optimized_cost=optimized_cost,
            cost_reduction_percentage=cost_reduction,
            api_calls_baseline=baseline_api_calls,
            api_calls_optimized=optimized_api_calls,
            api_reduction_percentage=api_reduction,
            cache_hit_ratio=metrics.get('cache_hit_ratio', 0.0),
            average_batch_size=metrics.get('average_batch_size', 0.0),
            processing_time=processing_time,
            error_rate=(total_errors / len(batches)) * 100 if batches else 0,
            throughput=total_processed / processing_time if processing_time > 0 else 0,
            cost_per_unit=optimized_cost / total_processed if total_processed > 0 else 0
        )
        
        self.results.append(result)
        return result
    
    # Request generation methods
    def _generate_corporate_videos(self, count: int) -> List[Dict]:
        """Generate corporate training video requests"""
        templates = [
            "Professional office workspace with laptop and documents",
            "Team meeting in modern conference room",
            "Employee training session in classroom setting",
            "Business presentation with charts and graphs",
            "Workplace safety demonstration in office"
        ]
        
        requests = []
        for i in range(count):
            template = random.choice(templates)
            requests.append({
                'id': f'corp_vid_{i}',
                'content_type': 'video',
                'prompt': f"{template} - Part {i % 10}",
                'resolution': '1920x1080',
                'duration': random.uniform(30, 120),
                'engine': 'default',
                'style_params': {'video_style': 'corporate_professional'},
                'priority': 2
            })
        return requests
    
    def _generate_social_videos(self, count: int) -> List[Dict]:
        """Generate social media video requests"""
        templates = [
            "Dynamic tech startup environment with young professionals",
            "Creative workspace with artists and designers",
            "Urban lifestyle content with modern architecture",
            "Fitness and wellness content in gym setting",
            "Food and cooking content in kitchen"
        ]
        
        requests = []
        for i in range(count):
            template = random.choice(templates)
            requests.append({
                'id': f'social_vid_{i}',
                'content_type': 'video',
                'prompt': f"{template} - Episode {i % 15}",
                'resolution': '1080x1920',  # Vertical for social
                'duration': random.uniform(15, 60),
                'engine': 'social_optimized',
                'style_params': {'video_style': 'social_trendy'},
                'priority': random.choice([1, 2, 3])  # Mixed priorities
            })
        return requests
    
    def _generate_marketing_videos(self, count: int) -> List[Dict]:
        """Generate product marketing video requests"""
        templates = [
            "Premium product showcase with luxury aesthetic",
            "Tech gadget demonstration with clean background",
            "Fashion brand commercial with models",
            "Automotive commercial with vehicle in motion",
            "Lifestyle product integration in home setting"
        ]
        
        requests = []
        for i in range(count):
            template = random.choice(templates)
            requests.append({
                'id': f'marketing_vid_{i}',
                'content_type': 'video',
                'prompt': f"{template} - Campaign {i // 5 + 1}",
                'resolution': random.choice(['1920x1080', '3840x2160']),
                'duration': random.uniform(20, 90),
                'engine': 'marketing_premium',
                'style_params': {'video_style': 'high_end_commercial'},
                'priority': 1  # High priority for marketing
            })
        return requests
    
    def _generate_ecommerce_images(self, count: int) -> List[Dict]:
        """Generate e-commerce product image requests"""
        categories = ['electronics', 'clothing', 'home', 'beauty', 'sports']
        
        requests = []
        for i in range(count):
            category = random.choice(categories)
            requests.append({
                'id': f'ecom_img_{i}',
                'content_type': 'image',
                'prompt': f"Professional product photo of {category} item on white background",
                'resolution': '1024x1024',
                'duration': 1.0,
                'engine': 'ecommerce_optimized',
                'style_params': {'style': 'product_photography'},
                'priority': 2
            })
        return requests
    
    def _generate_stock_images(self, count: int) -> List[Dict]:
        """Generate stock photography requests"""
        subjects = [
            "business person in office",
            "family enjoying outdoor activity",
            "modern cityscape at sunset",
            "fresh food and ingredients",
            "technology and innovation concept"
        ]
        
        requests = []
        for i in range(count):
            subject = random.choice(subjects)
            requests.append({
                'id': f'stock_img_{i}',
                'content_type': 'image',
                'prompt': f"High quality stock photo of {subject}",
                'resolution': '1920x1080',
                'duration': 1.0,
                'engine': 'stock_photography',
                'style_params': {'style': 'stock_photo'},
                'priority': 3  # Lower priority
            })
        return requests
    
    def _generate_custom_images(self, count: int) -> List[Dict]:
        """Generate custom artwork requests"""
        styles = ['abstract', 'realistic', 'cartoon', 'watercolor', 'digital_art']
        
        requests = []
        for i in range(count):
            style = random.choice(styles)
            requests.append({
                'id': f'custom_img_{i}',
                'content_type': 'image',
                'prompt': f"Custom {style} artwork with unique design elements",
                'resolution': '1920x1080',
                'duration': 1.0,
                'engine': 'custom_creative',
                'style_params': {'style': style},
                'priority': 2
            })
        return requests
    
    def _generate_podcast_audio(self, count: int) -> List[Dict]:
        """Generate podcast episode requests"""
        topics = [
            "technology trends and innovation",
            "business strategy and leadership",
            "health and wellness advice",
            "creative arts and culture",
            "science and education"
        ]
        
        requests = []
        for i in range(count):
            topic = random.choice(topics)
            requests.append({
                'id': f'podcast_{i}',
                'content_type': 'audio',
                'prompt': f"Professional podcast discussion about {topic}",
                'resolution': 'standard',
                'duration': random.uniform(1800, 3600),  # 30-60 minutes
                'engine': 'podcast_voice',
                'style_params': {'voice_style': 'conversational'},
                'priority': 2
            })
        return requests
    
    def _generate_voiceover_audio(self, count: int) -> List[Dict]:
        """Generate voice-over content requests"""
        types = [
            "corporate training narration",
            "commercial advertisement voice",
            "documentary narration",
            "audiobook reading",
            "educational content explanation"
        ]
        
        requests = []
        for i in range(count):
            vo_type = random.choice(types)
            requests.append({
                'id': f'voiceover_{i}',
                'content_type': 'audio',
                'prompt': f"Professional voice-over for {vo_type}",
                'resolution': 'standard',
                'duration': random.uniform(60, 300),  # 1-5 minutes
                'engine': 'voice_over_pro',
                'style_params': {'voice_style': 'professional_narration'},
                'priority': random.choice([1, 2, 3])
            })
        return requests
    
    def _generate_music_audio(self, count: int) -> List[Dict]:
        """Generate music production requests"""
        genres = ['electronic', 'ambient', 'corporate', 'cinematic', 'acoustic']
        
        requests = []
        for i in range(count):
            genre = random.choice(genres)
            requests.append({
                'id': f'music_{i}',
                'content_type': 'audio',
                'prompt': f"Original {genre} music composition",
                'resolution': 'high_quality',
                'duration': random.uniform(120, 480),  # 2-8 minutes
                'engine': 'music_composition',
                'style_params': {'genre': genre, 'mood': 'uplifting'},
                'priority': 3
            })
        return requests
    
    def _generate_mixed_campaign(self, count: int) -> List[Dict]:
        """Generate mixed content campaign requests"""
        content_types = ['video', 'image', 'audio']
        requests = []
        
        for i in range(count):
            content_type = random.choice(content_types)
            
            if content_type == 'video':
                requests.append({
                    'id': f'campaign_vid_{i}',
                    'content_type': 'video',
                    'prompt': f"Campaign video for product launch - variation {i}",
                    'resolution': '1920x1080',
                    'duration': random.uniform(30, 90),
                    'engine': 'campaign_video',
                    'style_params': {'brand_style': 'corporate'},
                    'priority': 1
                })
            elif content_type == 'image':
                requests.append({
                    'id': f'campaign_img_{i}',
                    'content_type': 'image',
                    'prompt': f"Campaign image for social media - product {i % 10}",
                    'resolution': '1080x1080',
                    'duration': 1.0,
                    'engine': 'campaign_image',
                    'style_params': {'brand_style': 'corporate'},
                    'priority': 2
                })
            else:  # audio
                requests.append({
                    'id': f'campaign_audio_{i}',
                    'content_type': 'audio',
                    'prompt': f"Campaign audio jingle - brand theme {i % 5}",
                    'resolution': 'standard',
                    'duration': random.uniform(15, 60),
                    'engine': 'campaign_audio',
                    'style_params': {'brand_style': 'corporate'},
                    'priority': 2
                })
        
        return requests
    
    def _generate_library_expansion(self, count: int) -> List[Dict]:
        """Generate content library expansion requests"""
        content_types = ['video', 'image', 'audio']
        categories = ['business', 'lifestyle', 'technology', 'education', 'entertainment']
        
        requests = []
        for i in range(count):
            content_type = random.choice(content_types)
            category = random.choice(categories)
            
            if content_type == 'video':
                requests.append({
                    'id': f'lib_vid_{i}',
                    'content_type': 'video',
                    'prompt': f"Library video content - {category} category",
                    'resolution': '1920x1080',
                    'duration': random.uniform(60, 300),
                    'engine': 'library_content',
                    'style_params': {'category': category},
                    'priority': 3
                })
            elif content_type == 'image':
                requests.append({
                    'id': f'lib_img_{i}',
                    'content_type': 'image',
                    'prompt': f"Library image - {category} themed content",
                    'resolution': '1920x1080',
                    'duration': 1.0,
                    'engine': 'library_content',
                    'style_params': {'category': category},
                    'priority': 3
                })
            else:
                requests.append({
                    'id': f'lib_audio_{i}',
                    'content_type': 'audio',
                    'prompt': f"Library audio content - {category} background music",
                    'resolution': 'standard',
                    'duration': random.uniform(180, 600),
                    'engine': 'library_content',
                    'style_params': {'category': category},
                    'priority': 3
                })
        
        return requests
    
    def _generate_burst_load(self, count: int) -> List[Dict]:
        """Generate high-volume burst load requests"""
        content_types = ['video', 'image', 'audio']
        requests = []
        
        # Mix of urgent, normal, and background priority
        priorities = [1, 2, 3]
        priority_weights = [0.2, 0.6, 0.2]  # 20% urgent, 60% normal, 20% background
        
        for i in range(count):
            content_type = random.choice(content_types)
            priority = random.choices(priorities, weights=priority_weights)[0]
            
            if content_type == 'video':
                requests.append({
                    'id': f'burst_vid_{i}',
                    'content_type': 'video',
                    'prompt': f"Burst load video content - batch {i // 25 + 1}",
                    'resolution': '1920x1080',
                    'duration': random.uniform(30, 180),
                    'engine': 'burst_optimized',
                    'style_params': {'batch': i // 25 + 1},
                    'priority': priority
                })
            elif content_type == 'image':
                requests.append({
                    'id': f'burst_img_{i}',
                    'content_type': 'image',
                    'prompt': f"Burst load image - batch {i // 25 + 1}",
                    'resolution': '1024x1024',
                    'duration': 1.0,
                    'engine': 'burst_optimized',
                    'style_params': {'batch': i // 25 + 1},
                    'priority': priority
                })
            else:
                requests.append({
                    'id': f'burst_audio_{i}',
                    'content_type': 'audio',
                    'prompt': f"Burst load audio - batch {i // 25 + 1}",
                    'resolution': 'standard',
                    'duration': random.uniform(60, 240),
                    'engine': 'burst_optimized',
                    'style_params': {'batch': i // 25 + 1},
                    'priority': priority
                })
        
        return requests
    
    def _generate_complex_mix(self, count: int) -> List[Dict]:
        """Generate complex content mix for stress testing"""
        # Various resolutions, engines, and styles
        resolutions = ['1920x1080', '1080x1920', '3840x2160', '1024x1024']
        engines = ['default', 'premium', 'social', 'ecommerce', 'custom']
        styles = ['corporate', 'creative', 'artistic', 'minimalist', 'vibrant']
        
        requests = []
        for i in range(count):
            content_type = random.choice(['video', 'image', 'audio'])
            
            request = {
                'id': f'complex_{i}',
                'content_type': content_type,
                'prompt': f"Complex content with varied parameters {i}",
                'resolution': random.choice(resolutions),
                'duration': random.uniform(10, 300) if content_type == 'video' else 1.0,
                'engine': random.choice(engines),
                'style_params': {
                    'style': random.choice(styles),
                    'complexity': 'high',
                    'variations': random.randint(1, 5)
                },
                'priority': random.choice([1, 2, 3])
            }
            
            if content_type == 'audio':
                request['resolution'] = 'standard'
                request['duration'] = random.uniform(30, 600)
            
            requests.append(request)
        
        return requests
    
    async def _prepopulate_cache(self, batcher: SmartBatcher, content_type: str):
        """Pre-populate cache with common content to simulate real-world usage"""
        cache_manager = batcher.cache_manager
        
        # Add some common cached content based on content type
        if content_type == 'video':
            common_requests = [
                ContentRequest(
                    id='cached_office_1',
                    content_type='video',
                    prompt='Professional office workspace with laptop and documents',
                    resolution='1920x1080',
                    duration=30.0,
                    engine='default',
                    style_params={'video_style': 'corporate_professional'},
                    priority=2
                ),
                ContentRequest(
                    id='cached_meeting_1',
                    content_type='video',
                    prompt='Team meeting in modern conference room',
                    resolution='1920x1080',
                    duration=45.0,
                    engine='default',
                    style_params={'video_style': 'corporate_professional'},
                    priority=2
                )
            ]
        elif content_type == 'image':
            common_requests = [
                ContentRequest(
                    id='cached_product_1',
                    content_type='image',
                    prompt='Professional product photo of electronics item on white background',
                    resolution='1024x1024',
                    duration=1.0,
                    engine='ecommerce_optimized',
                    style_params={'style': 'product_photography'},
                    priority=2
                )
            ]
        else:  # audio
            common_requests = [
                ContentRequest(
                    id='cached_podcast_1',
                    content_type='audio',
                    prompt='Professional podcast discussion about technology trends and innovation',
                    resolution='standard',
                    duration=1800.0,
                    engine='podcast_voice',
                    style_params={'voice_style': 'conversational'},
                    priority=2
                )
            ]
        
        # Cache these common requests
        for request in common_requests:
            cache_data = {
                'file_path': f"cached/{request.content_type}/{request.id}.mp4",
                'duration': request.duration,
                'cost': request.estimated_cost * 0.1,  # Much cheaper since cached
                'quality_score': 8.5,
                'generated_at': datetime.now().isoformat(),
                'generation_time': 0.5  # Instant
            }
            cache_manager.set(request, cache_data, ttl=3600)
        
        print(f"Pre-populated cache with {len(common_requests)} common {content_type} requests")
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics across all test results"""
        if not self.results:
            return {}
        
        avg_cost_reduction = statistics.mean([r.cost_reduction_percentage for r in self.results])
        avg_api_reduction = statistics.mean([r.api_reduction_percentage for r in self.results])
        avg_cache_hit_ratio = statistics.mean([r.cache_hit_ratio for r in self.results])
        avg_batch_size = statistics.mean([r.average_batch_size for r in self.results])
        total_baseline_cost = sum([r.baseline_cost for r in self.results])
        total_optimized_cost = sum([r.optimized_cost for r in self.results])
        total_savings = total_baseline_cost - total_optimized_cost
        
        # Scenarios meeting 20% cost reduction target
        cost_target_met = sum(1 for r in self.results if r.cost_reduction_percentage >= 20.0)
        success_rate = (cost_target_met / len(self.results)) * 100
        
        return {
            'total_scenarios': len(self.results),
            'average_cost_reduction_percent': avg_cost_reduction,
            'average_api_reduction_percent': avg_api_reduction,
            'average_cache_hit_ratio': avg_cache_hit_ratio,
            'average_batch_size': avg_batch_size,
            'total_baseline_cost': total_baseline_cost,
            'total_optimized_cost': total_optimized_cost,
            'total_savings': total_savings,
            'scenarios_meeting_20_percent_target': cost_target_met,
            'success_rate_percent': success_rate,
            'min_cost_reduction': min([r.cost_reduction_percentage for r in self.results]),
            'max_cost_reduction': max([r.cost_reduction_percentage for r in self.results]),
            'total_requests_processed': sum([r.total_requests for r in self.results])
        }


async def run_all_cost_scenario_tests():
    """Run all cost optimization scenario tests"""
    print("=== Cost Optimization Validation Tests ===")
    print("Testing 20-50% cost reduction and API call reduction claims")
    
    validator = CostScenarioValidator()
    all_results = []
    
    # Run all test categories
    video_results = await validator.test_video_content_scenarios()
    all_results.extend(video_results)
    
    image_results = await validator.test_image_content_scenarios()
    all_results.extend(image_results)
    
    audio_results = await validator.test_audio_content_scenarios()
    all_results.extend(audio_results)
    
    mixed_results = await validator.test_mixed_content_scenarios()
    all_results.extend(mixed_results)
    
    stress_results = await validator.test_stress_scenarios()
    all_results.extend(stress_results)
    
    # Generate summary statistics
    summary = validator.get_summary_statistics()
    
    print("\n=== Cost Optimization Test Summary ===")
    print(f"Total scenarios tested: {summary['total_scenarios']}")
    print(f"Average cost reduction: {summary['average_cost_reduction_percent']:.1f}%")
    print(f"Average API call reduction: {summary['average_api_reduction_percent']:.1f}%")
    print(f"Average cache hit ratio: {summary['average_cache_hit_ratio']:.1%}")
    print(f"Average batch size: {summary['average_batch_size']:.1f}")
    print(f"Total baseline cost: ${summary['total_baseline_cost']:.2f}")
    print(f"Total optimized cost: ${summary['total_optimized_cost']:.2f}")
    print(f"Total savings: ${summary['total_savings']:.2f}")
    print(f"Success rate (20%+ cost reduction): {summary['success_rate_percent']:.1f}%")
    print(f"Cost reduction range: {summary['min_cost_reduction']:.1f}% - {summary['max_cost_reduction']:.1f}%")
    
    # Validate against targets
    print("\n=== Target Validation ===")
    if summary['average_cost_reduction_percent'] >= 20.0:
        print("✅ PASS: Average cost reduction meets 20% target")
    else:
        print("❌ FAIL: Average cost reduction below 20% target")
    
    if summary['success_rate_percent'] >= 80.0:
        print("✅ PASS: Success rate meets 80% target")
    else:
        print("❌ FAIL: Success rate below 80% target")
    
    if summary['average_api_reduction_percent'] >= 30.0:
        print("✅ PASS: API call reduction meets 30% target")
    else:
        print("❌ FAIL: API call reduction below 30% target")
    
    return {
        'results': validator.results,
        'summary': summary,
        'timestamp': datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Run the tests
    test_data = asyncio.run(run_all_cost_scenario_tests())
    
    # Save results to JSON for analysis
    results_data = {
        'test_metadata': {
            'test_suite': 'Cost Optimization Validation',
            'timestamp': test_data['timestamp'],
            'total_scenarios': len(test_data['results'])
        },
        'summary_statistics': test_data['summary'],
        'detailed_results': [
            {
                'scenario': result.scenario_name,
                'total_requests': result.total_requests,
                'baseline_cost': result.baseline_cost,
                'optimized_cost': result.optimized_cost,
                'cost_reduction_percent': result.cost_reduction_percentage,
                'api_reduction_percent': result.api_reduction_percentage,
                'cache_hit_ratio': result.cache_hit_ratio,
                'average_batch_size': result.average_batch_size,
                'processing_time': result.processing_time,
                'error_rate': result.error_rate,
                'throughput': result.throughput,
                'cost_per_unit': result.cost_per_unit
            }
            for result in test_data['results']
        ]
    }
    
    with open('/workspace/tests/cost_scenario_test_results.json', 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\nDetailed results saved to: /workspace/tests/cost_scenario_test_results.json")