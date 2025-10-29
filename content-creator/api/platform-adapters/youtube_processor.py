"""
YouTube Longform Video Processor - Combines scenes and optimizes for 8-15 minute duration
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Import video generation capabilities
import sys
sys.path.append('/workspace')
from content_creator.api.video_generation.video_pipeline import VideoGenerationPipeline, VideoComposition

# Import configuration
from config.settings import VIDEO_SETTINGS, PERFORMANCE_SETTINGS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class YouTubeOptimization:
    """YouTube-specific optimization settings"""
    target_duration_range: Tuple[int, int]  # (min_seconds, max_seconds)
    optimal_engagement_points: List[int]  # seconds for audience retention
    thumbnail_variations: int
    seo_optimization: bool
    auto_chapters: bool
    retention_optimization: bool

@dataclass
class LongformComposition:
    """Complete YouTube video composition"""
    id: str
    title: str
    description: str
    duration: float
    scenes: List[Dict[str, Any]]
    video_composition: VideoComposition
    thumbnail_variations: List[str]
    metadata: Dict[str, Any]
    optimization_score: float
    created_at: str

class YouTubeLongformProcessor:
    """Process and optimize content for YouTube longform videos"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.video_pipeline = VideoGenerationPipeline(f"{output_dir}/youtube")
        self.optimization = YouTubeOptimization(
            target_duration_range=(480, 900),  # 8-15 minutes
            optimal_engagement_points=[30, 90, 180, 360, 540],  # Hook moments
            thumbnail_variations=3,
            seo_optimization=True,
            auto_chapters=True,
            retention_optimization=True
        )
        
    async def process_longform_content(self, 
                                     script_scenes: List[Dict[str, Any]],
                                     video_composition: VideoComposition,
                                     seo_data: Optional[Dict[str, Any]] = None) -> LongformComposition:
        """
        Process script scenes into optimized YouTube longform video
        
        Args:
            script_scenes: Original script scenes
            video_composition: Generated video segments
            seo_data: SEO optimization data
            
        Returns:
            LongformComposition: Optimized YouTube video
        """
        
        logger.info("🎬 Processing YouTube longform video...")
        
        # 1. Optimize scene timing for 8-15 minute target
        optimized_scenes = await self._optimize_scene_timing(script_scenes)
        
        # 2. Enhance scenes with retention hooks
        enhanced_scenes = await self._add_retention_hooks(optimized_scenes)
        
        # 3. Create engaging intro and conclusion
        enhanced_scenes = await self._add_youtube_specific_scenes(enhanced_scenes)
        
        # 4. Generate YouTube-optimized video
        youtube_video = await self._create_longform_video(enhanced_scenes, video_composition)
        
        # 5. Generate multiple thumbnail variations
        thumbnails = await self._generate_thumbnail_variations(
            youtube_video, seo_data or {}
        )
        
        # 6. Create SEO-optimized title and description
        metadata = await self._create_seo_metadata(enhanced_scenes, seo_data)
        
        # 7. Calculate optimization score
        optimization_score = await self._calculate_optimization_score(
            enhanced_scenes, youtube_video
        )
        
        # Create final composition
        composition = LongformComposition(
            id=str(uuid.uuid4()),
            title=metadata['title'],
            description=metadata['description'],
            duration=youtube_video.total_duration,
            scenes=enhanced_scenes,
            video_composition=youtube_video,
            thumbnail_variations=thumbnails,
            metadata=metadata,
            optimization_score=optimization_score,
            created_at=datetime.now().isoformat()
        )
        
        logger.info(f"✅ YouTube longform video processed: {composition.title}")
        logger.info(f"⏱️ Duration: {composition.duration}s")
        logger.info(f"🎯 Optimization Score: {composition.optimization_score:.2f}/10")
        
        return composition
    
    async def _optimize_scene_timing(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize scene timing for 8-15 minute target"""
        
        current_duration = sum(scene.get('duration', 30) for scene in scenes)
        target_min, target_max = self.optimization.target_duration_range
        
        logger.info(f"📏 Current duration: {current_duration}s, Target: {target_min}-{target_max}s")
        
        # If too short, expand key scenes
        if current_duration < target_min:
            missing_time = target_min - current_duration
            return await self._expand_key_scenes(scenes, missing_time)
        
        # If too long, condense content
        elif current_duration > target_max:
            excess_time = current_duration - target_max
            return await self._condense_content(scenes, excess_time)
        
        # Perfect length, just optimize
        else:
            return await self._fine_tune_timing(scenes)
    
    async def _expand_key_scenes(self, scenes: List[Dict[str, Any]], missing_time: int) -> List[Dict[str, Any]]:
        """Expand key scenes to reach target duration"""
        
        # Find most impactful scenes to expand
        key_scenes = [
            scene for scene in scenes 
            if scene.get('scene_type') in ['main_content', 'demo']
        ]
        
        if not key_scenes:
            key_scenes = [max(scenes, key=lambda x: x.get('duration', 0))]
        
        # Distribute additional time
        time_per_scene = missing_time // len(key_scenes)
        
        for scene in key_scenes:
            scene['duration'] += time_per_scene
            scene['voiceover_text'] += f" Let me elaborate on this point further."
        
        logger.info(f"📈 Expanded {len(key_scenes)} scenes by {time_per_scene}s each")
        return scenes
    
    async def _condense_content(self, scenes: List[Dict[str, Any]], excess_time: int) -> List[Dict[str, Any]]:
        """Condense content to fit target duration"""
        
        # Remove less critical scenes or shorten them
        scenes_to_modify = sorted(
            [scene for scene in scenes if scene.get('scene_type') not in ['intro', 'call_to_action']],
            key=lambda x: x.get('duration', 0),
            reverse=True
        )
        
        for scene in scenes_to_modify:
            if excess_time <= 0:
                break
                
            reduction = min(30, scene.get('duration', 30) - 15)  # Don't go below 15s
            scene['duration'] -= reduction
            excess_time -= reduction
            
            # Condense voiceover text
            words = scene.get('voiceover_text', '').split()
            if len(words) > reduction:
                scene['voiceover_text'] = ' '.join(words[:-reduction//5])
        
        logger.info(f"📉 Condensed content by {excess_time}s")
        return scenes
    
    async def _fine_tune_timing(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fine-tune timing for optimal pacing"""
        
        # Add strategic pauses and emphasis
        for scene in scenes:
            if scene.get('scene_type') == 'main_content':
                # Add natural pause points
                scene['voiceover_text'] = scene['voiceover_text'].replace(
                    '. ', '. ... '
                )
                scene['duration'] += 2  # Brief pause
        
        return scenes
    
    async def _add_retention_hooks(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add retention hooks at optimal engagement points"""
        
        current_time = 0
        
        for hook_point in self.optimization.optimal_engagement_points:
            if current_time < hook_point < sum(s.get('duration', 0) for s in scenes):
                
                # Find scene containing this time point
                target_scene = None
                scene_time = 0
                
                for scene in scenes:
                    scene_duration = scene.get('duration', 30)
                    if scene_time <= hook_point < scene_time + scene_duration:
                        target_scene = scene
                        break
                    scene_time += scene_duration
                
                if target_scene:
                    # Add retention hook
                    hook_text = f"🎯 But wait, there's more! Let me show you something incredible."
                    target_scene['voiceover_text'] = target_scene['voiceover_text'] + f" {hook_text}"
                    target_scene['retention_hook'] = True
        
        return scenes
    
    async def _add_youtube_specific_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add YouTube-specific intro, outro, and engagement elements"""
        
        # Enhanced intro with hook
        intro_scene = {
            "scene_number": 0,
            "duration": 15,
            "voiceover_text": "🚨 This will change everything you know about this topic!",
            "visual_description": "Eye-catching intro with title reveal and subscribe prompt",
            "scene_type": "youtube_intro",
            "platform_adaptations": {"youtube": "enhanced_hook"},
            "hooks": {"youtube": "Subscribe for daily tips!"},
            "transition_effects": ["zoom_in", "pop"]
        }
        
        # Outro with engagement
        outro_scene = {
            "scene_number": len(scenes) + 1,
            "duration": 20,
            "voiceover_text": "👍 If this helped you, give it a thumbs up! 🔔 Subscribe for more! 💬 Comment below with your experience!",
            "visual_description": "Subscribe button, like animation, and comment prompt",
            "scene_type": "youtube_outro",
            "platform_adaptations": {"youtube": "full_engagement"},
            "hooks": {},
            "transition_effects": ["slide_in", "bounce"]
        }
        
        scenes.insert(0, intro_scene)
        scenes.append(outro_scene)
        
        return scenes
    
    async def _create_longform_video(self, scenes: List[Dict[str, Any]], 
                                   video_composition: VideoComposition) -> VideoComposition:
        """Create YouTube-optimized video composition"""
        
        # Enhance video composition for YouTube
        youtube_settings = VIDEO_SETTINGS['youtube']
        
        # Re-generate video with YouTube optimization
        enhanced_segments = []
        
        for scene in scenes:
            if scene.get('scene_type') in ['youtube_intro', 'youtube_outro']:
                # Special treatment for intro/outro
                segment = await self._create_youtube_special_segment(scene, youtube_settings)
                enhanced_segments.append(segment)
            else:
                # Enhanced regular scene
                segment = await self._enhance_regular_segment(scene, video_composition)
                enhanced_segments.append(segment)
        
        # Create final composition
        return VideoComposition(
            id=str(uuid.uuid4()),
            segments=enhanced_segments,
            total_duration=sum(seg.duration for seg in enhanced_segments),
            resolution=youtube_settings['resolution'],
            fps=youtube_settings['fps'],
            output_file=f"{self.output_dir}/youtube/enhanced_video.mp4",
            transitions=await self._create_youtube_transitions(),
            effects=await self._create_youtube_effects(),
            created_at=datetime.now().isoformat(),
            metadata={'platform': 'youtube', 'optimized': True}
        )
    
    async def _create_youtube_special_segment(self, scene: Dict[str, Any], 
                                            settings: Dict[str, Any]):
        """Create special intro/outro segments"""
        # Implementation for special YouTube segments
        pass
    
    async def _enhance_regular_segment(self, scene: Dict[str, Any], 
                                     video_composition: VideoComposition):
        """Enhance regular segments with YouTube optimization"""
        # Implementation for enhanced segments
        pass
    
    async def _create_youtube_transitions(self) -> List[Dict[str, Any]]:
        """Create YouTube-optimized transitions"""
        return [
            {"type": "fade", "duration": 0.5, "style": "smooth"},
            {"type": "slide", "duration": 0.3, "style": "professional"},
            {"type": "cut", "duration": 0, "style": "clean"}
        ]
    
    async def _create_youtube_effects(self) -> List[Dict[str, Any]]:
        """Create YouTube-specific visual effects"""
        return [
            {"type": "title_overlay", "style": "modern"},
            {"type": "subscribe_reminder", "position": "corner"},
            {"type": "engagement_prompt", "timing": "end"}
        ]
    
    async def _generate_thumbnail_variations(self, 
                                           video: VideoComposition,
                                           seo_data: Dict[str, Any]) -> List[str]:
        """Generate multiple thumbnail variations for A/B testing"""
        
        thumbnails = []
        
        # Load image generation toolkit
        from content_creator.api.image_gen import gen_images
        
        for i in range(self.optimization.thumbnail_variations):
            prompt = self._create_thumbnail_prompt(video, seo_data, i)
            # Generate thumbnail (mock implementation)
            thumbnail_path = f"{self.output_dir}/youtube/thumbnail_v{i+1}.png"
            thumbnails.append(thumbnail_path)
        
        return thumbnails
    
    def _create_thumbnail_prompt(self, video: VideoComposition, 
                               seo_data: Dict[str, Any], variation: int) -> str:
        """Create thumbnail generation prompt"""
        
        title = seo_data.get('title', 'Amazing Content')
        
        prompts = [
            f"Professional YouTube thumbnail with bold text '{title}', vibrant colors, eye-catching design",
            f"Modern YouTube thumbnail with '{title}' text overlay, bright background, engaging visual",
            f"High-impact YouTube thumbnail featuring '{title}', dynamic layout, click-worthy design"
        ]
        
        return prompts[variation % len(prompts)]
    
    async def _create_seo_metadata(self, scenes: List[Dict[str, Any]], 
                                 seo_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create SEO-optimized title and description"""
        
        # Generate compelling title
        title_templates = [
            "How {topic} Will Change Your Life in 2025",
            "The Ultimate Guide to {topic}: Everything You Need to Know",
            "{topic} Explained: Simple Tips for Amazing Results",
            "Master {topic} in 10 Minutes (Life-Changing Results)",
            "{topic} Secrets Nobody Tells You (Must Watch)"
        ]
        
        topic = seo_data.get('topic', 'This Amazing Topic')
        title = title_templates[0].format(topic=topic)
        
        # Generate description
        description = f"""
🔥 Ready to master {topic}? This comprehensive guide covers everything you need to know!

⏰ TIMESTAMPS:
00:00 Introduction
{(await self._generate_timestamps(scenes))}

💡 What you'll learn:
{self._extract_key_points(scenes)}

👍 If this helped you, please LIKE and SUBSCRIBE for more content like this!

#YourChannel #{topic.replace(' ', '')} #HowTo #Tutorial

📱 Follow me on social media for daily tips!
"""
        
        return {
            "title": title,
            "description": description.strip(),
            "tags": [topic.replace(' ', ''), 'tutorial', 'howto', 'education'],
            "category": "Education",
            "default_language": "en",
            "captions": True
        }
    
    async def _generate_timestamps(self, scenes: List[Dict[str, Any]]) -> str:
        """Generate YouTube timestamps from scenes"""
        
        timestamp_lines = []
        current_time = 0
        
        for scene in scenes:
            scene_name = scene.get('scene_type', 'Content').replace('_', ' ').title()
            timestamp_lines.append(f"{current_time//60:02d}:{current_time%60:02d} {scene_name}")
            current_time += scene.get('duration', 30)
        
        return '\n'.join(timestamp_lines[1:])  # Skip intro timestamp
    
    def _extract_key_points(self, scenes: List[Dict[str, Any]]) -> str:
        """Extract key points for description"""
        
        key_points = []
        for scene in scenes:
            if scene.get('scene_type') in ['main_content', 'demo']:
                point = scene.get('voiceover_text', '')[:100] + "..."
                key_points.append(f"• {point}")
        
        return '\n'.join(key_points[:5])  # Top 5 points
    
    async def _calculate_optimization_score(self, scenes: List[Dict[str, Any]], 
                                          video: VideoComposition) -> float:
        """Calculate YouTube optimization score (1-10)"""
        
        score = 0
        
        # Duration score (5 points)
        duration = video.total_duration
        target_min, target_max = self.optimization.target_duration_range
        if target_min <= duration <= target_max:
            score += 5
        elif duration < target_min:
            score += 3
        else:
            score += 4
        
        # Engagement elements (3 points)
        engagement_count = sum(1 for scene in scenes 
                             if scene.get('retention_hook') or scene.get('scene_type') in ['youtube_intro', 'youtube_outro'])
        score += min(3, engagement_count)
        
        # Technical quality (2 points)
        quality_score = video.fps >= 30 and '1920x1080' in video.resolution
        score += 2 if quality_score else 1
        
        return min(10, score)

# Test function
async def test_youtube_processor():
    """Test the YouTube longform processor"""
    
    processor = YouTubeLongformProcessor("/tmp/youtube_test")
    
    # Mock script scenes
    mock_scenes = [
        {
            "scene_number": 1,
            "duration": 30,
            "voiceover_text": "Welcome to this amazing topic!",
            "visual_description": "Introduction to the topic",
            "scene_type": "intro"
        },
        {
            "scene_number": 2,
            "duration": 120,
            "voiceover_text": "Let's dive deep into the main content with detailed explanations.",
            "visual_description": "Main content explanation",
            "scene_type": "main_content"
        }
    ]
    
    # Test processing
    result = await processor.process_longform_content(
        script_scenes=mock_scenes,
        video_composition=None,  # Mock composition
        seo_data={"topic": "AI Productivity"}
    )
    
    print(f"🎬 YouTube Video Generated:")
    print(f"📝 Title: {result.title}")
    print(f"⏱️ Duration: {result.duration}s")
    print(f"🎯 Score: {result.optimization_score}/10")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_youtube_processor())