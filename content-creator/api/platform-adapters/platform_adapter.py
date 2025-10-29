"""
Main Platform Adapter - Orchestrates all platform-specific content generators
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Import platform adapters
from api.platform_adapters.youtube_processor import YouTubeLongformProcessor, LongformComposition
from api.platform_adapters.shortform_extractor import ShortformExtractor, ShortformComposition  
from api.platform_adapters.text_content_generator import TextContentGenerator, SocialMediaPost
from api.platform_adapters.thumbnail_generator import ThumbnailGenerator, GeneratedThumbnail

# Import core pipeline components
from api.video_generation.video_pipeline import VideoGenerationPipeline, VideoComposition
from api.content_library.library_manager import ContentLibraryManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PlatformContentRequest:
    """Request for platform-specific content generation"""
    id: str
    original_idea: str
    script_scenes: List[Dict[str, Any]]
    video_composition: VideoComposition
    target_platforms: List[str]
    content_style: str
    metadata: Dict[str, Any]
    created_at: str

@dataclass
class PlatformContentResult:
    """Complete platform-specific content result"""
    id: str
    request_id: str
    youtube_content: Optional[LongformComposition]
    tiktok_content: Optional[ShortformComposition]
    instagram_content: Optional[ShortformComposition]
    social_posts: Dict[str, SocialMediaPost]
    thumbnails: Dict[str, List[GeneratedThumbnail]]
    content_library_additions: List[Dict[str, Any]]
    processing_time: float
    total_cost_estimate: float
    created_at: str

class PlatformAdapter:
    """Main orchestrator for platform-specific content generation"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        
        # Initialize platform-specific processors
        self.youtube_processor = YouTubeLongformProcessor(f"{output_dir}/youtube")
        self.shortform_extractor = ShortformExtractor(f"{output_dir}/social")
        self.text_generator = TextContentGenerator(f"{output_dir}/social")
        self.thumbnail_generator = ThumbnailGenerator(f"{output_dir}/thumbnails")
        
        # Initialize content library for scene re-use
        self.content_library = ContentLibraryManager(f"{output_dir}/content_library")
        
    async def generate_platform_content(self, 
                                      script_scenes: List[Dict[str, Any]],
                                      video_composition: VideoComposition,
                                      video_metadata: Dict[str, Any],
                                      target_platforms: List[str] = None,
                                      content_style: str = "educational") -> PlatformContentResult:
        """
        Generate complete platform-specific content from script and video
        
        Args:
            script_scenes: Script scenes from main pipeline
            video_composition: Generated video composition
            video_metadata: Video metadata (title, duration, themes)
            target_platforms: Target platforms (default: all)
            content_style: Content style (educational, entertaining, etc.)
            
        Returns:
            PlatformContentResult: Complete platform-specific content
        """
        
        if target_platforms is None:
            target_platforms = ["youtube", "tiktok", "instagram", "twitter", "linkedin"]
        
        request_id = str(uuid.uuid4())
        logger.info(f"🎯 Generating platform content for: {', '.join(target_platforms)}")
        
        start_time = datetime.now()
        
        # Extract content themes for all platforms
        content_themes = await self._extract_content_themes(script_scenes, video_metadata)
        
        # Initialize results
        results = {
            "youtube_content": None,
            "tiktok_content": None,
            "instagram_content": None,
            "social_posts": {},
            "thumbnails": {},
            "content_library_additions": []
        }
        
        # Process each platform
        tasks = []
        
        if "youtube" in target_platforms:
            tasks.append(self._process_youtube_content(
                script_scenes, video_composition, video_metadata, content_themes
            ))
        
        if "tiktok" in target_platforms:
            tasks.append(self._process_tiktok_content(
                script_scenes, video_composition, video_metadata, content_themes
            ))
        
        if "instagram" in target_platforms:
            tasks.append(self._process_instagram_content(
                script_scenes, video_composition, video_metadata, content_themes
            ))
        
        if any(p in target_platforms for p in ["twitter", "linkedin"]):
            tasks.append(self._process_social_media_content(
                script_scenes, video_metadata, content_themes, target_platforms
            ))
        
        # Execute all platform processing in parallel
        platform_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        result_index = 0
        for task_result in platform_results:
            if isinstance(task_result, Exception):
                logger.error(f"Platform processing failed: {task_result}")
                continue
            
            # Unpack task result based on type
            if "youtube" in target_platforms and result_index < len(platform_results):
                results["youtube_content"] = task_result.get("youtube")
                result_index += 1
            elif "tiktok" in target_platforms:
                results["tiktok_content"] = task_result.get("tiktok")
            elif "instagram" in target_platforms:
                results["instagram_content"] = task_result.get("instagram")
            elif "social" in task_result:
                results["social_posts"] = task_result["social"]
        
        # Generate thumbnails for all content
        thumbnail_tasks = []
        for platform in target_platforms:
            thumbnail_tasks.append(self._generate_platform_thumbnails(
                platform, video_metadata, results
            ))
        
        thumbnail_results = await asyncio.gather(*thumbnail_tasks, return_exceptions=True)
        
        # Process thumbnail results
        for thumbnail_result in thumbnail_results:
            if isinstance(thumbnail_result, Exception):
                logger.error(f"Thumbnail generation failed: {thumbnail_result}")
                continue
            
            for platform, thumbnails in thumbnail_result.items():
                results["thumbnails"][platform] = thumbnails
        
        # Add scenes to content library for future re-use
        library_additions = await self._add_to_content_library(
            script_scenes, video_metadata, target_platforms
        )
        results["content_library_additions"] = library_additions
        
        # Calculate processing time and cost estimate
        processing_time = (datetime.now() - start_time).total_seconds()
        cost_estimate = self._estimate_processing_cost(script_scenes, target_platforms)
        
        # Create final result
        final_result = PlatformContentResult(
            id=str(uuid.uuid4()),
            request_id=request_id,
            youtube_content=results["youtube_content"],
            tiktok_content=results["tiktok_content"],
            instagram_content=results["instagram_content"],
            social_posts=results["social_posts"],
            thumbnails=results["thumbnails"],
            content_library_additions=library_additions,
            processing_time=processing_time,
            total_cost_estimate=cost_estimate,
            created_at=datetime.now().isoformat()
        )
        
        logger.info(f"✅ Platform content generation completed in {processing_time:.1f}s")
        logger.info(f"💰 Estimated cost: ${cost_estimate:.2f}")
        
        return final_result
    
    async def _extract_content_themes(self, 
                                    scenes: List[Dict[str, Any]], 
                                    video_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract consistent themes for all platforms"""
        
        themes = {
            "main_topic": video_metadata.get("main_topic", "general"),
            "tone": video_metadata.get("tone", "educational"),
            "target_audience": video_metadata.get("target_audience", "general"),
            "key_insights": [],
            "emotional_hooks": [],
            "visual_elements": [],
            "content_style": video_metadata.get("content_style", "educational")
        }
        
        # Extract themes from scenes
        for scene in scenes:
            # Key insights
            voiceover = scene.get("voiceover_text", "")
            if len(voiceover) > 30:
                themes["key_insights"].append(voiceover[:100])
            
            # Emotional hooks
            if scene.get("hooks"):
                themes["emotional_hooks"].extend(scene["hooks"].values())
            
            # Visual elements
            visual_desc = scene.get("visual_description", "")
            if visual_desc:
                themes["visual_elements"].append(visual_desc)
        
        return themes
    
    async def _process_youtube_content(self,
                                     scenes: List[Dict[str, Any]],
                                     video_composition: VideoComposition,
                                     video_metadata: Dict[str, Any],
                                     themes: Dict[str, Any]) -> Dict[str, Any]:
        """Process content specifically for YouTube"""
        
        logger.info("🎬 Processing YouTube longform content...")
        
        youtube_content = await self.youtube_processor.process_longform_content(
            script_scenes=scenes,
            video_composition=video_composition,
            seo_data=themes
        )
        
        return {"youtube": youtube_content}
    
    async def _process_tiktok_content(self,
                                    scenes: List[Dict[str, Any]],
                                    video_composition: VideoComposition,
                                    video_metadata: Dict[str, Any],
                                    themes: Dict[str, Any]) -> Dict[str, Any]:
        """Process content specifically for TikTok"""
        
        logger.info("📱 Processing TikTok short-form content...")
        
        tiktok_content = await self.shortform_extractor.extract_shortform_content(
            script_scenes=scenes,
            video_composition=video_composition,
            platform="tiktok",
            content_style=themes["content_style"]
        )
        
        return {"tiktok": tiktok_content}
    
    async def _process_instagram_content(self,
                                       scenes: List[Dict[str, Any]],
                                       video_composition: VideoComposition,
                                       video_metadata: Dict[str, Any],
                                       themes: Dict[str, Any]) -> Dict[str, Any]:
        """Process content specifically for Instagram"""
        
        logger.info("📸 Processing Instagram Reels content...")
        
        instagram_content = await self.shortform_extractor.extract_shortform_content(
            script_scenes=scenes,
            video_composition=video_composition,
            platform="instagram",
            content_style=themes["content_style"]
        )
        
        return {"instagram": instagram_content}
    
    async def _process_social_media_content(self,
                                          scenes: List[Dict[str, Any]],
                                          video_metadata: Dict[str, Any],
                                          themes: Dict[str, Any],
                                          target_platforms: List[str]) -> Dict[str, Any]:
        """Process text content for social media platforms"""
        
        logger.info("📝 Processing social media text content...")
        
        social_platforms = [p for p in target_platforms if p in ["twitter", "linkedin"]]
        
        social_posts = await self.text_generator.generate_social_content(
            script_scenes=scenes,
            video_metadata=video_metadata,
            platforms=social_platforms
        )
        
        return {"social": social_posts}
    
    async def _generate_platform_thumbnails(self,
                                          platform: str,
                                          video_metadata: Dict[str, Any],
                                          results: Dict[str, Any]) -> Dict[str, List[GeneratedThumbnail]]:
        """Generate thumbnails for a specific platform"""
        
        logger.info(f"🖼️ Generating {platform} thumbnails...")
        
        # Determine if we have content for this platform
        has_content = False
        if platform == "youtube" and results.get("youtube_content"):
            has_content = True
        elif platform == "tiktok" and results.get("tiktok_content"):
            has_content = True
        elif platform == "instagram" and results.get("instagram_content"):
            has_content = True
        
        if not has_content:
            # Generate generic thumbnails based on video metadata
            thumbnails = await self.thumbnail_generator.generate_thumbnails(
                video_metadata=video_metadata,
                platform=platform,
                variation_count=3
            )
        else:
            # Generate thumbnails based on platform-specific content
            content = results.get(f"{platform}_content")
            if content:
                # Use content-specific metadata for thumbnail generation
                content_metadata = {
                    **video_metadata,
                    "title": getattr(content, 'title', video_metadata.get('title', '')),
                    "main_topic": themes.get('main_topic', 'general')
                }
                
                thumbnails = await self.thumbnail_generator.generate_thumbnails(
                    video_metadata=content_metadata,
                    platform=platform,
                    variation_count=3
                )
            else:
                thumbnails = []
        
        return {platform: thumbnails}
    
    async def _add_to_content_library(self,
                                    scenes: List[Dict[str, Any]],
                                    video_metadata: Dict[str, Any],
                                    platforms: List[str]) -> List[Dict[str, Any]]:
        """Add scenes to content library for future re-use"""
        
        logger.info("📚 Adding scenes to content library...")
        
        additions = []
        
        for i, scene in enumerate(scenes):
            # Create scene metadata
            scene_metadata = {
                "id": str(uuid.uuid4()),
                "original_idea": video_metadata.get("title", ""),
                "scene_content": scene.get("voiceover_text", ""),
                "visual_description": scene.get("visual_description", ""),
                "scene_type": scene.get("scene_type", "general"),
                "duration": scene.get("duration", 30),
                "platforms": platforms,
                "performance_score": 8.0,  # Default score
                "usage_count": 0,
                "tags": self._generate_scene_tags(scene, video_metadata),
                "created_at": datetime.now().isoformat(),
                "reusable": True
            }
            
            additions.append(scene_metadata)
        
        # In a real implementation, this would save to the content library
        logger.info(f"📝 Added {len(additions)} scenes to content library")
        return additions
    
    def _generate_scene_tags(self, scene: Dict[str, Any], video_metadata: Dict[str, Any]) -> List[str]:
        """Generate tags for scene in content library"""
        
        tags = []
        
        # Scene type tags
        scene_type = scene.get("scene_type", "")
        if scene_type:
            tags.append(scene_type.replace("_", "-"))
        
        # Content-based tags
        voiceover = scene.get("voiceover_text", "").lower()
        visual_desc = scene.get("visual_description", "").lower()
        combined_text = f"{voiceover} {visual_desc}"
        
        # Extract keywords
        keywords = {
            "tutorial": ["how", "step", "guide", "tutorial"],
            "tips": ["tip", "hack", "advice", "recommendation"],
            "demo": ["show", "demonstrate", "example", "practice"],
            "explanation": ["explain", "what", "why", "how"],
            "motivation": ["amazing", "incredible", "life-changing", "success"]
        }
        
        for tag, tag_keywords in keywords.items():
            if any(keyword in combined_text for keyword in tag_keywords):
                tags.append(tag)
        
        # Platform tags
        if "youtube" in video_metadata.get("platforms", []):
            tags.append("youtube-optimized")
        if "tiktok" in video_metadata.get("platforms", []):
            tags.append("tiktok-optimized")
        
        return list(set(tags))  # Remove duplicates
    
    def _estimate_processing_cost(self, 
                                scenes: List[Dict[str, Any]], 
                                platforms: List[str]) -> float:
        """Estimate processing cost for content generation"""
        
        # Base cost per scene
        base_cost_per_scene = 0.05  # $0.05 per scene
        
        # Platform multipliers
        platform_multipliers = {
            "youtube": 3.0,      # Most expensive (long-form processing)
            "tiktok": 2.0,       # Moderate cost
            "instagram": 2.0,    # Moderate cost
            "twitter": 0.5,      # Low cost (text only)
            "linkedin": 0.5      # Low cost (text only)
        }
        
        # Calculate base cost
        base_cost = len(scenes) * base_cost_per_scene
        
        # Add platform costs
        total_cost = base_cost
        for platform in platforms:
            multiplier = platform_multipliers.get(platform, 1.0)
            total_cost += multiplier * 0.10  # $0.10 per platform
        
        return round(total_cost, 2)
    
    async def regenerate_platform_content(self,
                                        request_id: str,
                                        regeneration_options: Dict[str, Any]) -> PlatformContentResult:
        """Regenerate specific platform content with new parameters"""
        
        logger.info(f"🔄 Regenerating content for request: {request_id}")
        
        # In a real implementation, this would:
        # 1. Retrieve original request data
        # 2. Apply regeneration options
        # 3. Re-run specific platform generators
        # 4. Update content library
        
        # Mock implementation
        raise NotImplementedError("Content regeneration not yet implemented")
    
    def get_platform_content_summary(self, result: PlatformContentResult) -> Dict[str, Any]:
        """Get summary of generated platform content"""
        
        summary = {
            "request_id": result.request_id,
            "processing_time": result.processing_time,
            "estimated_cost": result.total_cost_estimate,
            "platforms_generated": [],
            "content_counts": {},
            "total_thumbnails": 0
        }
        
        # Count content by platform
        if result.youtube_content:
            summary["platforms_generated"].append("youtube")
            summary["content_counts"]["youtube"] = {
                "duration": result.youtube_content.duration,
                "scenes": len(result.youtube_content.scenes),
                "optimization_score": result.youtube_content.optimization_score
            }
        
        if result.tiktok_content:
            summary["platforms_generated"].append("tiktok")
            summary["content_counts"]["tiktok"] = {
                "duration": result.tiktok_content.duration,
                "hook": result.tiktok_content.hook_text
            }
        
        if result.instagram_content:
            summary["platforms_generated"].append("instagram")
            summary["content_counts"]["instagram"] = {
                "duration": result.instagram_content.duration,
                "hook": result.instagram_content.hook_text
            }
        
        # Social media posts
        for platform in result.social_posts:
            summary["platforms_generated"].append(platform)
            summary["content_counts"][platform] = {
                "character_count": result.social_posts[platform].character_count,
                "hashtags": len(result.social_posts[platform].hashtags)
            }
        
        # Count thumbnails
        total_thumbnails = sum(len(thumbnails) for thumbnails in result.thumbnails.values())
        summary["total_thumbnails"] = total_thumbnails
        summary["thumbnail_breakdown"] = {
            platform: len(thumbnails) 
            for platform, thumbnails in result.thumbnails.items()
        }
        
        return summary

# Test function
async def test_platform_adapter():
    """Test the platform adapter"""
    
    adapter = PlatformAdapter("/tmp/platform_test")
    
    # Mock script scenes
    mock_scenes = [
        {
            "scene_number": 1,
            "duration": 30,
            "voiceover_text": "Welcome to this amazing productivity guide!",
            "visual_description": "Professional introduction with productivity tools",
            "scene_type": "intro"
        },
        {
            "scene_number": 2,
            "duration": 60,
            "voiceover_text": "The 2-minute rule will transform your productivity forever.",
            "visual_description": "Demonstration of 2-minute rule application",
            "scene_type": "main_content"
        }
    ]
    
    mock_metadata = {
        "title": "Productivity Hack That Changed Everything",
        "main_topic": "productivity",
        "tone": "educational",
        "target_audience": "professionals",
        "duration": 120
    }
    
    # Test platform content generation
    result = await adapter.generate_platform_content(
        script_scenes=mock_scenes,
        video_composition=None,  # Mock composition
        video_metadata=mock_metadata,
        target_platforms=["youtube", "tiktok", "instagram", "twitter"],
        content_style="educational"
    )
    
    # Get summary
    summary = adapter.get_platform_content_summary(result)
    
    print("🎯 Platform Content Generation Summary:")
    print("=" * 50)
    print(f"📊 Processing Time: {summary['processing_time']:.1f}s")
    print(f"💰 Estimated Cost: ${summary['estimated_cost']}")
    print(f"📱 Platforms: {', '.join(summary['platforms_generated'])}")
    print(f"🖼️ Total Thumbnails: {summary['total_thumbnails']}")
    print(f"📝 Content Library Additions: {len(result.content_library_additions)}")
    
    # Show detailed breakdown
    for platform, counts in summary["content_counts"].items():
        print(f"\n{platform.upper()}:")
        for key, value in counts.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_platform_adapter())