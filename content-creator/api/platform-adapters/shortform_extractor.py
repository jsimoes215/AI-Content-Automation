"""
TikTok/Instagram Short-Form Extractor - Selects best scenes and creates vertical 9:16 format
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
class ShortformOptimization:
    """Short-form specific optimization settings"""
    target_durations: Dict[str, Tuple[int, int]]  # platform -> (min, max)
    vertical_format: str  # 9:16 aspect ratio
    hook_timing: int  # seconds for hook
    cta_timing: int  # seconds for call-to-action
    max_scenes: int  # maximum scenes per video
    trending_elements: List[str]  # trending visual/audio elements

@dataclass
class ShortformComposition:
    """Complete short-form video composition"""
    id: str
    platform: str  # 'tiktok' or 'instagram'
    duration: float
    hook_text: str
    scenes: List[Dict[str, Any]]
    video_composition: VideoComposition
    captions: List[Dict[str, Any]]
    trending_tags: List[str]
    engagement_elements: Dict[str, Any]
    created_at: str

class ShortformExtractor:
    """Extract and optimize content for TikTok and Instagram Reels"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.tiktok_pipeline = VideoGenerationPipeline(f"{output_dir}/tiktok")
        self.instagram_pipeline = VideoGenerationPipeline(f"{output_dir}/instagram")
        
        self.optimization = ShortformOptimization(
            target_durations={
                'tiktok': (15, 60),
                'instagram': (15, 90)
            },
            vertical_format="1080x1920",
            hook_timing=3,  # Hook within first 3 seconds
            cta_timing=-5,  # CTA 5 seconds before end
            max_scenes=5,  # Maximum scenes for short-form
            trending_elements=[
                "fast_cuts", "trending_music", "text_overlays", 
                "emoji_transitions", "zoom_effects", "quick_facts"
            ]
        )
    
    async def extract_shortform_content(self, 
                                      script_scenes: List[Dict[str, Any]],
                                      video_composition: VideoComposition,
                                      platform: str = "tiktok",
                                      content_style: str = "educational") -> ShortformComposition:
        """
        Extract short-form content optimized for TikTok or Instagram
        
        Args:
            script_scenes: Original script scenes
            video_composition: Generated video segments
            platform: Target platform ('tiktok' or 'instagram')
            content_style: Content style ('educational', 'entertaining', 'motivational')
            
        Returns:
            ShortformComposition: Optimized short-form video
        """
        
        logger.info(f"📱 Extracting {platform} short-form content...")
        
        # 1. Analyze and select best scenes for short-form
        selected_scenes = await self._select_best_scenes(script_scenes, platform)
        
        # 2. Adapt scenes for vertical format and short attention span
        adapted_scenes = await self._adapt_scenes_for_shortform(selected_scenes, platform)
        
        # 3. Add trending elements and viral hooks
        enhanced_scenes = await self._add_viral_elements(adapted_scenes, content_style)
        
        # 4. Create engaging hook and CTA
        hook_data = await self._create_engaging_hook(enhanced_scenes, content_style)
        cta_data = await self._create_call_to_action(enhanced_scenes, platform)
        
        # 5. Generate vertical video
        shortform_video = await self._create_vertical_video(enhanced_scenes, platform)
        
        # 6. Add captions and text overlays
        captions = await self._generate_captions(enhanced_scenes, hook_data)
        
        # 7. Generate trending hashtags
        trending_tags = await self._generate_trending_tags(enhanced_scenes, platform)
        
        # 8. Create engagement elements
        engagement_elements = await self._create_engagement_elements(shortform_video, platform)
        
        # Create final composition
        composition = ShortformComposition(
            id=str(uuid.uuid4()),
            platform=platform,
            duration=shortform_video.total_duration,
            hook_text=hook_data['text'],
            scenes=enhanced_scenes,
            video_composition=shortform_video,
            captions=captions,
            trending_tags=trending_tags,
            engagement_elements=engagement_elements,
            created_at=datetime.now().isoformat()
        )
        
        logger.info(f"✅ {platform} video created: {composition.duration}s")
        logger.info(f"🎯 Hook: {composition.hook_text}")
        logger.info(f"🏷️ Tags: {', '.join(trending_tags[:5])}")
        
        return composition
    
    async def _select_best_scenes(self, scenes: List[Dict[str, Any]], platform: str) -> List[Dict[str, Any]]:
        """Select the most engaging scenes for short-form"""
        
        target_durations = self.optimization.target_durations[platform]
        target_duration = (target_durations[0] + target_durations[1]) // 2
        
        # Score scenes for short-form appeal
        scored_scenes = []
        
        for scene in scenes:
            score = self._calculate_scene_score(scene, platform)
            scene['shortform_score'] = score
            scene['selected_reason'] = self._get_selection_reason(score)
            scored_scenes.append(scene)
        
        # Sort by score and select best ones
        scored_scenes.sort(key=lambda x: x['shortform_score'], reverse=True)
        
        # Select scenes until we reach target duration
        selected = []
        total_duration = 0
        
        for scene in scored_scenes:
            scene_duration = min(scene.get('duration', 30), 20)  # Cap individual scenes
            
            if total_duration + scene_duration <= target_duration or len(selected) < 2:
                selected.append(scene)
                total_duration += scene_duration
                
                if total_duration >= target_durations[0]:  # Minimum duration reached
                    break
        
        # Ensure we have a good mix
        selected = await self._balance_scene_selection(selected, platform)
        
        logger.info(f"📝 Selected {len(selected)} scenes for {platform}")
        return selected
    
    def _calculate_scene_score(self, scene: Dict[str, Any], platform: str) -> float:
        """Calculate short-form appeal score for a scene"""
        
        score = 0
        
        # Scene type scoring
        scene_type = scene.get('scene_type', '')
        if scene_type == 'intro':
            score += 3  # Good for hooks
        elif scene_type == 'main_content':
            score += 4  # Most important
        elif scene_type == 'demo':
            score += 5  # Highly visual
        elif scene_type == 'call_to_action':
            score += 2  # Good for ending
        
        # Visual elements scoring
        visual_desc = scene.get('visual_description', '').lower()
        visual_keywords = ['demonstration', 'show', 'example', 'step', 'tutorial', 'quick']
        score += sum(2 for keyword in visual_keywords if keyword in visual_desc)
        
        # Platform-specific scoring
        if platform == 'tiktok':
            # TikTok loves quick, engaging content
            duration = scene.get('duration', 30)
            if duration <= 20:
                score += 2  # Prefer shorter scenes
        elif platform == 'instagram':
            # Instagram Reels can be slightly longer
            duration = scene.get('duration', 30)
            if duration <= 30:
                score += 1
        
        return score
    
    def _get_selection_reason(self, score: float) -> str:
        """Get human-readable reason for scene selection"""
        
        if score >= 8:
            return "High engagement potential"
        elif score >= 6:
            return "Strong visual appeal"
        elif score >= 4:
            return "Good content value"
        else:
            return "Supporting content"
    
    async def _balance_scene_selection(self, scenes: List[Dict[str, Any]], platform: str) -> List[Dict[str, Any]]:
        """Ensure balanced scene selection"""
        
        # Priority: intro/main/demo/cta
        priority_order = ['intro', 'main_content', 'demo', 'call_to_action']
        
        balanced = []
        used_types = set()
        
        # First pass: get one of each priority type
        for scene_type in priority_order:
            for scene in scenes:
                if scene.get('scene_type') == scene_type and scene_type not in used_types:
                    balanced.append(scene)
                    used_types.add(scene_type)
                    break
        
        # Second pass: fill remaining slots with highest scored scenes
        for scene in scenes:
            if scene not in balanced and len(balanced) < self.optimization.max_scenes:
                balanced.append(scene)
        
        return balanced[:self.optimization.max_scenes]
    
    async def _adapt_scenes_for_shortform(self, scenes: List[Dict[str, Any]], platform: str) -> List[Dict[str, Any]]:
        """Adapt scenes for short-form consumption"""
        
        adapted_scenes = []
        
        for i, scene in enumerate(scenes):
            adapted_scene = scene.copy()
            
            # Optimize timing for short-form
            if platform == 'tiktok':
                # TikTok: very fast pacing
                adapted_scene['duration'] = min(scene.get('duration', 30), 15)
                adapted_scene['pace'] = 'fast'
            else:
                # Instagram: moderate pacing
                adapted_scene['duration'] = min(scene.get('duration', 30), 20)
                adapted_scene['pace'] = 'medium'
            
            # Compress voiceover for quick consumption
            voiceover = scene.get('voiceover_text', '')
            if len(voiceover) > 100:
                # Extract key phrases
                words = voiceover.split()
                key_words = [w for w in words if w.lower() in ['here', 'how', 'why', 'what', 'step', 'tip']]
                if key_words:
                    adapted_scene['voiceover_text'] = ' '.join(words[:50]) + "..."
                else:
                    adapted_scene['voiceover_text'] = ' '.join(words[:30]) + "..."
            
            # Add vertical optimization
            adapted_scene['vertical_optimized'] = True
            adapted_scene['platform'] = platform
            adapted_scene['scene_number'] = i + 1
            
            adapted_scenes.append(adapted_scene)
        
        return adapted_scenes
    
    async def _add_viral_elements(self, scenes: List[Dict[str, Any]], 
                                content_style: str) -> List[Dict[str, Any]]:
        """Add trending and viral elements to scenes"""
        
        enhanced_scenes = []
        
        # Content style mapping to viral elements
        style_elements = {
            'educational': ['quick_facts', 'step_indicators', 'progress_bars'],
            'entertaining': ['emoji_transitions', 'quick_cuts', 'fun_facts'],
            'motivational': ['inspiring_quotes', 'success_indicators', 'uplifting_music']
        }
        
        viral_elements = style_elements.get(content_style, ['quick_facts'])
        
        for scene in scenes:
            enhanced_scene = scene.copy()
            
            # Add viral elements
            enhanced_scene['viral_elements'] = viral_elements[:2]  # Max 2 per scene
            
            # Add trending transitions
            if scene.get('scene_number', 1) > 1:
                enhanced_scene['transition_effects'] = ['quick_cut', 'zoom']
            
            # Add text overlays for mobile viewing
            enhanced_scene['text_overlays'] = [
                {
                    "text": self._create_text_overlay(scene),
                    "timing": "start",
                    "style": "bold"
                }
            ]
            
            enhanced_scenes.append(enhanced_scene)
        
        return enhanced_scenes
    
    def _create_text_overlay(self, scene: Dict[str, Any]) -> str:
        """Create engaging text overlay for scene"""
        
        scene_type = scene.get('scene_type', '')
        voiceover = scene.get('voiceover_text', '')
        
        if scene_type == 'intro':
            return "WAIT FOR IT ⏰"
        elif scene_type == 'main_content':
            return "PRO TIP 💡"
        elif scene_type == 'demo':
            return "TRY THIS 🔥"
        elif scene_type == 'call_to_action':
            return "FOLLOW FOR MORE! 📱"
        else:
            # Extract key phrase from voiceover
            words = voiceover.split()
            if len(words) > 3:
                return ' '.join(words[:3]).upper() + "..."
            return voiceover[:20] + "..."
    
    async def _create_engaging_hook(self, scenes: List[Dict[str, Any]], 
                                  content_style: str) -> Dict[str, Any]:
        """Create viral hook for the video"""
        
        hook_templates = {
            'educational': [
                "You won't believe this simple trick! 🤯",
                "This will blow your mind! 💥",
                "Everyone should know this! 👀",
                "The secret nobody tells you! 🤫"
            ],
            'entertaining': [
                "POV: You just discovered this! 😱",
                "When you realize... 😮",
                "This is too real! 😂",
                "Main character energy! ✨"
            ],
            'motivational': [
                "Your life is about to change! 🚀",
                "This is your sign! ⭐",
                "Success starts here! 💪",
                "You got this! 🔥"
            ]
        }
        
        hooks = hook_templates.get(content_style, hook_templates['educational'])
        
        # Select hook based on content
        scene_content = ' '.join(scene.get('voiceover_text', '') for scene in scenes[:2])
        
        if any(word in scene_content.lower() for word in ['hack', 'trick', 'secret']):
            hook = hooks[0]
        elif any(word in scene_content.lower() for word in ['easy', 'simple', 'quick']):
            hook = hooks[1]
        else:
            hook = hooks[2]
        
        return {
            "text": hook,
            "timing": "immediate",
            "visual_style": "eye_catching",
            "audio_style": "attention_grabbing"
        }
    
    async def _create_call_to_action(self, scenes: List[Dict[str, Any]], 
                                   platform: str) -> Dict[str, Any]:
        """Create platform-specific call-to-action"""
        
        cta_templates = {
            'tiktok': [
                "Follow for daily tips! 🔔",
                "Save this for later! 💾",
                "Comment 'YES' if this helped! 💬",
                "Tag someone who needs this! 👥"
            ],
            'instagram': [
                "Double tap if this helped! ❤️",
                "Save this post! 🔖",
                "Share with your story! 📱",
                "Tag a friend who needs this! 🏷️"
            ]
        }
        
        ctas = cta_templates.get(platform, cta_templates['tiktok'])
        
        return {
            "text": ctas[0],
            "timing": self.optimization.cta_timing,
            "visual_style": "prominent",
            "platform_optimized": True
        }
    
    async def _create_vertical_video(self, scenes: List[Dict[str, Any]], 
                                   platform: str) -> VideoComposition:
        """Create vertical video optimized for the platform"""
        
        platform_settings = VIDEO_SETTINGS[platform]
        
        # Generate vertical video segments
        vertical_segments = []
        
        for scene in scenes:
            segment = await self._create_vertical_segment(scene, platform_settings)
            vertical_segments.append(segment)
        
        # Create composition
        return VideoComposition(
            id=str(uuid.uuid4()),
            segments=vertical_segments,
            total_duration=sum(seg.duration for seg in vertical_segments),
            resolution=platform_settings['resolution'],
            fps=platform_settings['fps'],
            output_file=f"{self.output_dir}/{platform}/shortform_video.mp4",
            transitions=[{"type": "quick_cut", "duration": 0}],
            effects=[{"type": "vertical_optimization", "platform": platform}],
            created_at=datetime.now().isoformat(),
            metadata={'platform': platform, 'format': 'vertical'}
        )
    
    async def _create_vertical_segment(self, scene: Dict[str, Any], 
                                     settings: Dict[str, Any]):
        """Create individual vertical video segment"""
        
        # Mock implementation - would generate actual video
        return {
            "id": str(uuid.uuid4()),
            "scene_id": scene.get('id', str(uuid.uuid4())),
            "prompt": f"Vertical video: {scene.get('visual_description', '')}",
            "duration": scene.get('duration', 15),
            "resolution": settings['resolution'],
            "file_path": f"temp_segment_{scene.get('scene_number', 1)}.mp4",
            "start_time": 0,
            "end_time": scene.get('duration', 15),
            "quality_score": 8.5,
            "generation_method": "text_to_video",
            "reference_images": [],
            "style_settings": {
                "aspect_ratio": "9:16",
                "vertical_optimized": True,
                "mobile_first": True
            }
        }
    
    async def _generate_captions(self, scenes: List[Dict[str, Any]], 
                               hook_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate subtitles and text overlays"""
        
        captions = []
        
        # Add hook caption
        captions.append({
            "type": "hook",
            "text": hook_data['text'],
            "timing": 0,
            "duration": 3,
            "style": "bold_yellow",
            "position": "center_top"
        })
        
        # Add scene captions
        current_time = 0
        for scene in scenes:
            # Auto-caption the voiceover
            voiceover = scene.get('voiceover_text', '')
            if voiceover:
                captions.append({
                    "type": "subtitle",
                    "text": voiceover,
                    "timing": current_time,
                    "duration": scene.get('duration', 15),
                    "style": "clean_white",
                    "position": "center_bottom"
                })
            
            # Add text overlay if specified
            text_overlays = scene.get('text_overlays', [])
            for overlay in text_overlays:
                captions.append({
                    "type": "overlay",
                    "text": overlay['text'],
                    "timing": current_time + 1,
                    "duration": 3,
                    "style": overlay['style'],
                    "position": "center_top"
                })
            
            current_time += scene.get('duration', 15)
        
        return captions
    
    async def _generate_trending_tags(self, scenes: List[Dict[str, Any]], 
                                    platform: str) -> List[str]:
        """Generate trending hashtags for the platform"""
        
        # Extract content themes
        themes = set()
        for scene in scenes:
            voiceover = scene.get('voiceover_text', '').lower()
            visual_desc = scene.get('visual_description', '').lower()
            
            # Simple keyword extraction
            keywords = ['tutorial', 'howto', 'tips', 'hack', 'productivity', 'ai', 'tech']
            for keyword in keywords:
                if keyword in voiceover or keyword in visual_desc:
                    themes.add(keyword)
        
        # Platform-specific trending tags
        if platform == 'tiktok':
            base_tags = ['#fyp', '#foryou', '#viral', '#trending']
            theme_tags = [f"#{theme}" for theme in themes][:3]
            content_tags = ['#learnontiktok', '#educational', '#howto'][:2]
        else:  # instagram
            base_tags = ['#reels', '#explore', '#discover']
            theme_tags = [f"#{theme}" for theme in themes][:3]
            content_tags = ['#instagramReels', '#reelit', '#learn'][:2]
        
        # Combine and limit
        all_tags = base_tags + theme_tags + content_tags
        return all_tags[:8]  # Platform optimal number
    
    async def _create_engagement_elements(self, video: VideoComposition, 
                                        platform: str) -> Dict[str, Any]:
        """Create platform-specific engagement elements"""
        
        elements = {
            'interactive_elements': [],
            'music_cues': [],
            'visual_effects': [],
            'engagement_triggers': []
        }
        
        if platform == 'tiktok':
            elements['interactive_elements'] = [
                {'type': 'poll', 'timing': 'middle'},
                {'type': 'question_sticker', 'timing': 'end'}
            ]
            elements['music_cues'] = [
                {'type': 'beat_drop', 'timing': '3s'},
                {'type': 'upbeat', 'timing': 'start'}
            ]
        else:  # instagram
            elements['interactive_elements'] = [
                {'type': 'quiz', 'timing': 'middle'},
                {'type': 'swipe_up', 'timing': 'end'}
            ]
            elements['music_cues'] = [
                {'type': 'trending_audio', 'timing': 'start'},
                {'type': 'viral_sound', 'timing': 'peak'}
            ]
        
        return elements

# Test function
async def test_shortform_extractor():
    """Test the short-form extractor"""
    
    extractor = ShortformExtractor("/tmp/shortform_test")
    
    # Mock script scenes
    mock_scenes = [
        {
            "scene_number": 1,
            "duration": 30,
            "voiceover_text": "Here's an amazing productivity hack that will change your life!",
            "visual_description": "Person demonstrating productivity technique",
            "scene_type": "intro"
        },
        {
            "scene_number": 2,
            "duration": 45,
            "voiceover_text": "Step 1: Organize your workspace. Step 2: Use the 2-minute rule.",
            "visual_description": "Clean workspace with organized items",
            "scene_type": "main_content"
        },
        {
            "scene_number": 3,
            "duration": 30,
            "voiceover_text": "Try this method and watch your productivity soar!",
            "visual_description": "Before and after productivity comparison",
            "scene_type": "conclusion"
        }
    ]
    
    # Test TikTok extraction
    tiktok_result = await extractor.extract_shortform_content(
        script_scenes=mock_scenes,
        video_composition=None,
        platform="tiktok",
        content_style="educational"
    )
    
    print(f"📱 TikTok Video:")
    print(f"⏱️ Duration: {tiktok_result.duration}s")
    print(f"🎯 Hook: {tiktok_result.hook_text}")
    print(f"🏷️ Tags: {tiktok_result.trending_tags}")
    
    # Test Instagram extraction
    instagram_result = await extractor.extract_shortform_content(
        script_scenes=mock_scenes,
        video_composition=None,
        platform="instagram",
        content_style="educational"
    )
    
    print(f"\n📸 Instagram Reels:")
    print(f"⏱️ Duration: {instagram_result.duration}s")
    print(f"🎯 Hook: {instagram_result.hook_text}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_shortform_extractor())