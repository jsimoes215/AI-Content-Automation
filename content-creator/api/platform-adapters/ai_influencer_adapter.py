"""
AI Influencer Integration Bridge

This module integrates the AI Influencer system with the existing content automation platform,
enabling seamless use of cost-optimized image generation and MiniMax video capabilities.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Import existing platform adapter
from content-creator.api.platform_adapters.platform_adapter import PlatformAdapter, PlatformContentResult

# Import AI Influencer system
from ai_influencer.core.content_generator import ContentGenerator
from ai_influencer.core.database import Database
from ai_influencer.onboarding.influencer_onboarding import InfluencerOnboardingSystem
from ai_influencer.optimization.optimized_image_generator import OptimizedImageGenerator

# Configure logging
logger = logging.getLogger(__name__)

class AIInfluencerPlatformAdapter:
    """
    Integration layer that combines AI Influencer capabilities with existing platform adapter
    """
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        
        # Initialize existing platform adapter
        self.platform_adapter = PlatformAdapter(output_dir)
        
        # Initialize AI Influencer components
        self.content_generator = ContentGenerator()
        self.database = Database()
        self.onboarding_system = InfluencerOnboardingSystem()
        self.optimized_image_generator = OptimizedImageGenerator()
        
        logger.info("🤖 AI Influencer Platform Adapter initialized")
    
    async def generate_ai_influencer_content(self,
                                           influencer_config: Dict[str, Any],
                                           content_request: Dict[str, Any]) -> PlatformContentResult:
        """
        Generate content using AI influencer persona and capabilities
        
        Args:
            influencer_config: AI influencer configuration and persona
            content_request: Content request details (topic, style, etc.)
            
        Returns:
            PlatformContentResult with AI influencer-generated content
        """
        
        logger.info(f"🎭 Generating AI influencer content for: {influencer_config.get('name', 'Unknown')}")
        
        try:
            # Step 1: Check if influencer exists, if not onboard
            influencer_id = await self._ensure_influencer_exists(influencer_config)
            
            # Step 2: Generate content with AI influencer persona
            content_result = await self.content_generator.generate_ai_influencer_content(
                influencer_id=influencer_id,
                topic=content_request.get('topic', ''),
                content_type=content_request.get('content_type', 'educational'),
                platforms=content_request.get('platforms', ['youtube', 'tiktok', 'instagram']),
                style_guide=influencer_config.get('style_guide', {})
            )
            
            # Step 3: Generate cost-optimized images
            if content_request.get('include_images', True):
                image_result = await self._generate_ai_influencer_images(
                    influencer_config=influencer_config,
                    content_topics=content_request.get('image_topics', []),
                    variation_count=content_request.get('image_variations', 5)
                )
                content_result['images'] = image_result
            
            # Step 4: Generate video content if requested
            if content_request.get('include_video', False):
                video_result = await self._generate_ai_influencer_video(
                    influencer_config=influencer_config,
                    content_script=content_result.get('script', ''),
                    video_style=content_request.get('video_style', 'talking_head')
                )
                content_result['video'] = video_result
            
            # Step 5: Convert to platform adapter format and generate multi-platform content
            platform_result = await self._convert_to_platform_format(
                ai_influencer_result=content_result,
                influencer_config=influencer_config
            )
            
            # Step 6: Generate platform-specific content using existing adapter
            final_result = await self.platform_adapter.generate_platform_content(
                script_scenes=platform_result.get('script_scenes', []),
                video_composition=platform_result.get('video_composition'),
                video_metadata=platform_result.get('video_metadata', {}),
                target_platforms=content_request.get('platforms', ['youtube', 'tiktok', 'instagram']),
                content_style=content_request.get('content_style', 'educational')
            )
            
            logger.info("✅ AI influencer content generation completed successfully")
            return final_result
            
        except Exception as e:
            logger.error(f"❌ AI influencer content generation failed: {e}")
            raise
    
    async def onboard_ai_influencer(self, influencer_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Onboard a new AI influencer and set up their persona, visual assets, and style guide
        
        Args:
            influencer_config: Complete influencer configuration
            
        Returns:
            Onboarding result with all generated assets
        """
        
        logger.info(f"👤 Onboarding AI influencer: {influencer_config.get('name', 'Unknown')}")
        
        try:
            # Use existing onboarding system
            onboarding_result = await self.onboarding_system.onboard_influencer(
                name=influencer_config.get('name', ''),
                voice_type=influencer_config.get('voice_type', 'Professional Male'),
                visual_style=influencer_config.get('visual_style', 'Modern Minimal'),
                niche=influencer_config.get('niche', 'Technology'),
                platform_preferences=influencer_config.get('platforms', ['youtube', 'linkedin']),
                personality_traits=influencer_config.get('personality_traits', []),
                content_preferences=influencer_config.get('content_preferences', {})
            )
            
            logger.info("🎯 AI influencer onboarding completed successfully")
            return onboarding_result
            
        except Exception as e:
            logger.error(f"❌ AI influencer onboarding failed: {e}")
            raise
    
    async def _ensure_influencer_exists(self, influencer_config: Dict[str, Any]) -> str:
        """Ensure influencer exists in database, onboard if necessary"""
        
        influencer_name = influencer_config.get('name', '')
        
        # Check if influencer exists
        existing_influencer = await self.database.get_influencer_by_name(influencer_name)
        
        if existing_influencer:
            logger.info(f"📋 Found existing influencer: {influencer_name}")
            return existing_influencer['id']
        
        # Onboard new influencer
        logger.info(f"🆕 Onboarding new influencer: {influencer_name}")
        onboarding_result = await self.onboard_ai_influencer(influencer_config)
        return onboarding_result['influencer_id']
    
    async def _generate_ai_influencer_images(self,
                                           influencer_config: Dict[str, Any],
                                           content_topics: List[str],
                                           variation_count: int) -> Dict[str, Any]:
        """Generate cost-optimized images for AI influencer"""
        
        logger.info(f"🖼️ Generating {variation_count} images for AI influencer")
        
        try:
            # Use optimized image generator for cost efficiency
            image_result = await self.optimized_image_generator.create_cost_optimized_content(
                base_style=influencer_config.get('visual_style', 'Professional'),
                variations_needed=variation_count,
                content_themes=content_topics or ['professional setup', 'tech workspace', 'presentation'],
                influencer_persona=influencer_config.get('personality_traits', [])
            )
            
            return image_result
            
        except Exception as e:
            logger.error(f"❌ Image generation failed: {e}")
            return {'images': [], 'error': str(e)}
    
    async def _generate_ai_influencer_video(self,
                                          influencer_config: Dict[str, Any],
                                          content_script: str,
                                          video_style: str) -> Dict[str, Any]:
        """Generate video content using MiniMax for talking head videos"""
        
        logger.info(f"🎬 Generating {video_style} video for AI influencer")
        
        try:
            # Import image_video_processor
            from ai_influencer.onboarding.image_video_processor import ImageVideoProcessor
            
            video_processor = ImageVideoProcessor()
            
            # Get base image for the influencer
            base_image = await self.database.get_latest_base_image(influencer_config.get('name', ''))
            
            if not base_image:
                logger.warning("⚠️ No base image found, generating one")
                # Generate base image if not exists
                image_result = await self._generate_ai_influencer_images(
                    influencer_config=influencer_config,
                    content_topics=['professional headshot'],
                    variation_count=1
                )
                base_image = image_result.get('images', [{}])[0].get('url', '')
            
            # Generate video using MiniMax (95% consistency for talking head)
            video_result = await video_processor.generate_talking_head_video(
                base_image_url=base_image,
                script_text=content_script,
                video_style=video_style,
                duration_target=30  # 30 seconds default
            )
            
            return video_result
            
        except Exception as e:
            logger.error(f"❌ Video generation failed: {e}")
            return {'video_url': None, 'error': str(e)}
    
    async def _convert_to_platform_format(self,
                                         ai_influencer_result: Dict[str, Any],
                                         influencer_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert AI influencer result to platform adapter format"""
        
        # Extract script scenes
        script_scenes = ai_influencer_result.get('script_scenes', [])
        
        # Create video composition mock (in real implementation, use actual composition)
        video_composition = None  # Placeholder for actual video composition
        
        # Create video metadata
        video_metadata = {
            'title': ai_influencer_result.get('title', ''),
            'main_topic': ai_influencer_result.get('topic', ''),
            'tone': influencer_config.get('voice_type', 'Professional').lower(),
            'target_audience': influencer_config.get('niche', 'general'),
            'duration': ai_influencer_result.get('duration', 60),
            'content_style': ai_influencer_result.get('content_type', 'educational'),
            'influencer_name': influencer_config.get('name', ''),
            'persona_score': ai_influencer_result.get('persona_consistency_score', 8.0)
        }
        
        return {
            'script_scenes': script_scenes,
            'video_composition': video_composition,
            'video_metadata': video_metadata
        }
    
    async def optimize_influencer_persona(self,
                                        influencer_id: str,
                                        performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize influencer persona based on performance data"""
        
        logger.info(f"🔧 Optimizing persona for influencer: {influencer_id}")
        
        try:
            from ai_influencer.optimization.persona_optimizer import AdvancedPersonaOptimizer
            
            optimizer = AdvancedPersonaOptimizer()
            
            # Analyze performance and optimize persona
            optimization_result = await optimizer.optimize_persona(
                influencer_id=influencer_id,
                performance_metrics=performance_data,
                optimization_targets=['engagement_rate', 'followers_growth', 'content_quality']
            )
            
            # Update influencer configuration
            await self.database.update_influencer_persona(influencer_id, optimization_result)
            
            logger.info("✅ Persona optimization completed")
            return optimization_result
            
        except Exception as e:
            logger.error(f"❌ Persona optimization failed: {e}")
            return {'error': str(e)}
    
    async def get_ai_influencer_analytics(self, 
                                        influencer_id: str,
                                        date_range: Dict[str, str]) -> Dict[str, Any]:
        """Get comprehensive analytics for AI influencer"""
        
        try:
            # Get basic analytics from existing platform
            platform_analytics = await self.platform_adapter.get_analytics(influencer_id, date_range)
            
            # Get AI influencer specific metrics
            ai_influencer_metrics = await self.database.get_influencer_metrics(influencer_id, date_range)
            
            # Get cost optimization data
            cost_data = await self.database.get_cost_optimization_metrics(influencer_id, date_range)
            
            # Combine all analytics
            combined_analytics = {
                'influencer_id': influencer_id,
                'date_range': date_range,
                'platform_analytics': platform_analytics,
                'ai_influencer_metrics': ai_influencer_metrics,
                'cost_optimization': cost_data,
                'recommendations': await self._generate_optimization_recommendations(ai_influencer_metrics, cost_data)
            }
            
            return combined_analytics
            
        except Exception as e:
            logger.error(f"❌ Analytics generation failed: {e}")
            return {'error': str(e)}
    
    async def _generate_optimization_recommendations(self,
                                                   metrics: Dict[str, Any],
                                                   cost_data: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on analytics"""
        
        recommendations = []
        
        # Cost optimization recommendations
        if cost_data.get('cost_per_content') > 10:
            recommendations.append("Consider using more cost-optimized image variations to reduce content creation costs")
        
        if cost_data.get('base_image_usage_rate', 0) < 0.5:
            recommendations.append("Increase base image usage for better cost efficiency")
        
        # Performance recommendations
        if metrics.get('engagement_rate', 0) < 0.05:
            recommendations.append("Persona optimization recommended - current engagement is below 5%")
        
        if metrics.get('persona_consistency_score', 0) < 7.0:
            recommendations.append("Improve persona consistency through voice and style optimization")
        
        return recommendations

# Example usage and testing functions
async def test_full_integration():
    """Test the complete AI influencer platform integration"""
    
    print("🧪 Testing AI Influencer Platform Integration")
    print("=" * 60)
    
    # Initialize the integrated adapter
    adapter = AIInfluencerPlatformAdapter("/tmp/ai_influencer_test")
    
    # Test 1: Onboard a new AI influencer
    print("\n1️⃣ Testing AI Influencer Onboarding...")
    test_influencer = {
        'name': 'TechGuru AI',
        'voice_type': 'Professional Male',
        'visual_style': 'Modern Minimal',
        'niche': 'Technology',
        'platforms': ['youtube', 'linkedin'],
        'personality_traits': ['knowledgeable', 'approachable', 'innovative'],
        'content_preferences': {
            'preferred_topics': ['AI', 'productivity', 'tech reviews'],
            'posting_frequency': 'daily',
            'video_length': 'medium'
        }
    }
    
    try:
        onboarding_result = await adapter.onboard_ai_influencer(test_influencer)
        print(f"✅ Onboarding successful: {onboarding_result['influencer_id']}")
    except Exception as e:
        print(f"❌ Onboarding failed: {e}")
        return
    
    # Test 2: Generate content
    print("\n2️⃣ Testing Content Generation...")
    content_request = {
        'topic': 'AI Tools for Productivity',
        'content_type': 'educational',
        'platforms': ['youtube', 'tiktok'],
        'include_images': True,
        'include_video': False,  # Set to True to test video generation
        'image_variations': 3
    }
    
    try:
        content_result = await adapter.generate_ai_influencer_content(test_influencer, content_request)
        print(f"✅ Content generation successful")
        print(f"   📊 Processing time: {content_result.processing_time:.1f}s")
        print(f"   💰 Cost estimate: ${content_result.total_cost_estimate}")
    except Exception as e:
        print(f"❌ Content generation failed: {e}")
        return
    
    # Test 3: Analytics (mock data)
    print("\n3️⃣ Testing Analytics...")
    try:
        analytics = await adapter.get_ai_influencer_analytics(
            onboarding_result['influencer_id'],
            {
                'start_date': '2024-01-01',
                'end_date': '2024-12-31'
            }
        )
        print(f"✅ Analytics generated: {len(analytics.get('recommendations', []))} recommendations")
    except Exception as e:
        print(f"❌ Analytics failed: {e}")
        return
    
    print("\n🎉 All integration tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_full_integration())