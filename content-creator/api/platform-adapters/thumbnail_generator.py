"""
Thumbnail Generation System - Creates platform-specific thumbnails for video content
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Import image generation capabilities
import sys
sys.path.append('/workspace')
from content_creator.api.image_gen import gen_images

# Import configuration
from config.settings import VIDEO_SETTINGS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ThumbnailTemplate:
    """Thumbnail template configuration"""
    id: str
    name: str
    style: str
    color_scheme: List[str]
    text_elements: Dict[str, Any]
    visual_elements: List[str]
    platform_optimized: bool
    performance_score: float

@dataclass
class GeneratedThumbnail:
    """Generated thumbnail with metadata"""
    id: str
    platform: str
    template_id: str
    file_path: str
    resolution: str
    size_kb: float
    prompt_used: str
    variation_number: int
    ab_test_group: Optional[str]
    performance_prediction: float
    metadata: Dict[str, Any]
    created_at: str

class ThumbnailGenerator:
    """Generate platform-optimized thumbnails for video content"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.templates = self._load_thumbnail_templates()
        
    def _load_thumbnail_templates(self) -> List[ThumbnailTemplate]:
        """Load thumbnail template configurations"""
        
        return [
            ThumbnailTemplate(
                id="bold_text",
                name="Bold Text Overlay",
                style="modern_bold",
                color_scheme=["#FF0000", "#FFFFFF", "#000000"],
                text_elements={
                    "primary_text": {"font_size": 48, "color": "#FFFFFF", "effect": "stroke"},
                    "secondary_text": {"font_size": 24, "color": "#FFFF00", "effect": "shadow"}
                },
                visual_elements=["arrow_pointing", "highlight_box", "celebration_elements"],
                platform_optimized=True,
                performance_score=8.5
            ),
            ThumbnailTemplate(
                id="split_screen",
                name="Before/After Split",
                style="comparison",
                color_scheme=["#00FF00", "#FF0000", "#FFFFFF"],
                text_elements={
                    "before_label": {"font_size": 32, "color": "#FF0000", "effect": "bold"},
                    "after_label": {"font_size": 32, "color": "#00FF00", "effect": "bold"}
                },
                visual_elements=["split_line", "arrow_transformation", "progress_indicator"],
                platform_optimized=True,
                performance_score=9.0
            ),
            ThumbnailTemplate(
                id="emotional_reaction",
                name="Emotional Reaction",
                style="expressive",
                color_scheme=["#FF6B6B", "#4ECDC4", "#FFFFFF"],
                text_elements={
                    "reaction_text": {"font_size": 36, "color": "#FFFFFF", "effect": "pop"},
                    "context_text": {"font_size": 20, "color": "#000000", "effect": "normal"}
                },
                visual_elements=["expressive_face", "emotion_arrows", "colorful_background"],
                platform_optimized=True,
                performance_score=8.8
            ),
            ThumbnailTemplate(
                id="minimal_clean",
                name="Minimal Clean",
                style="professional",
                color_scheme=["#2C3E50", "#ECF0F1", "#3498DB"],
                text_elements={
                    "title_text": {"font_size": 40, "color": "#2C3E50", "effect": "clean"},
                    "subtitle_text": {"font_size": 24, "color": "#7F8C8D", "effect": "thin"}
                },
                visual_elements=["clean_background", "geometric_shapes", "subtle_gradient"],
                platform_optimized=True,
                performance_score=7.5
            ),
            ThumbnailTemplate(
                id="trending_viral",
                name="Trending Viral Style",
                style="trending",
                color_scheme=["#FF9500", "#FF2D55", "#007AFF", "#FFFFFF"],
                text_elements={
                    "viral_text": {"font_size": 44, "color": "#FFFFFF", "effect": "3d_glow"},
                    "trending_element": {"font_size": 28, "color": "#FF9500", "effect": "pulse"}
                },
                visual_elements=["viral_arrow", "trending_icon", "colorful_burst", "social_elements"],
                platform_optimized=True,
                performance_score=9.2
            )
        ]
    
    async def generate_thumbnails(self,
                                video_metadata: Dict[str, Any],
                                platform: str = "youtube",
                                template_preferences: Optional[List[str]] = None,
                                variation_count: int = 3) -> List[GeneratedThumbnail]:
        """
        Generate thumbnails for video content
        
        Args:
            video_metadata: Video metadata (title, content themes, style)
            platform: Target platform (youtube, tiktok, instagram)
            template_preferences: Preferred template IDs
            variation_count: Number of thumbnail variations to generate
            
        Returns:
            List[GeneratedThumbnail]: Generated thumbnails
        """
        
        logger.info(f"🖼️ Generating {variation_count} thumbnails for {platform}")
        
        # Select templates
        selected_templates = self._select_templates(
            platform, template_preferences, variation_count
        )
        
        # Generate thumbnails
        thumbnails = []
        for i, template in enumerate(selected_templates):
            thumbnail = await self._generate_thumbnail(
                template=template,
                video_metadata=video_metadata,
                platform=platform,
                variation_number=i + 1
            )
            thumbnails.append(thumbnail)
        
        logger.info(f"✅ Generated {len(thumbnails)} thumbnails")
        return thumbnails
    
    def _select_templates(self, 
                        platform: str, 
                        preferences: Optional[List[str]], 
                        count: int) -> List[ThumbnailTemplate]:
        """Select appropriate templates for platform and preferences"""
        
        if preferences:
            # Use specified templates
            selected = [t for t in self.templates if t.id in preferences]
        else:
            # Select best performing templates for platform
            if platform == "youtube":
                # YouTube prefers bold, clear thumbnails
                selected = [t for t in self.templates if t.performance_score >= 8.0]
            elif platform in ["tiktok", "instagram"]:
                # Social platforms prefer trending, emotional styles
                selected = [t for t in self.templates if "trending" in t.style or "emotional" in t.style]
            else:
                selected = self.templates
        
        # Sort by performance score and take top templates
        selected.sort(key=lambda t: t.performance_score, reverse=True)
        return selected[:count]
    
    async def _generate_thumbnail(self,
                                template: ThumbnailTemplate,
                                video_metadata: Dict[str, Any],
                                platform: str,
                                variation_number: int) -> GeneratedThumbnail:
        """Generate single thumbnail using template"""
        
        # Create thumbnail prompt
        prompt = self._create_thumbnail_prompt(template, video_metadata, platform)
        
        # Get platform settings
        platform_settings = VIDEO_SETTINGS[platform]
        
        # Generate thumbnail
        thumbnail_filename = f"thumbnail_{template.id}_v{variation_number}_{platform}.png"
        thumbnail_path = f"{self.output_dir}/{platform}/thumbnails/{thumbnail_filename}"
        
        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
            
            # Generate image (mock implementation - would use actual image generation)
            # result = await gen_images(prompt=prompt, output_file=thumbnail_path)
            
            # For now, create placeholder thumbnail
            await self._create_placeholder_thumbnail(thumbnail_path, prompt)
            
            # Calculate file size (placeholder)
            file_size_kb = 125.5  # Mock size
            
            # Predict performance score
            performance_score = self._predict_thumbnail_performance(
                template, video_metadata, platform
            )
            
            thumbnail = GeneratedThumbnail(
                id=str(uuid.uuid4()),
                platform=platform,
                template_id=template.id,
                file_path=thumbnail_path,
                resolution=platform_settings['resolution'].replace('x', 'x'),
                size_kb=file_size_kb,
                prompt_used=prompt,
                variation_number=variation_number,
                ab_test_group=f"group_{template.id}",
                performance_prediction=performance_score,
                metadata={
                    'template_name': template.name,
                    'style': template.style,
                    'color_scheme': template.color_scheme,
                    'platform_optimized': template.platform_optimized
                },
                created_at=datetime.now().isoformat()
            )
            
            logger.info(f"🖼️ Generated {template.name} (score: {performance_score:.1f})")
            return thumbnail
            
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            raise
    
    def _create_thumbnail_prompt(self,
                               template: ThumbnailTemplate,
                               video_metadata: Dict[str, Any],
                               platform: str) -> str:
        """Create detailed prompt for thumbnail generation"""
        
        title = video_metadata.get('title', 'Amazing Content')
        topic = video_metadata.get('main_topic', 'general')
        
        # Base prompt structure
        prompt_parts = [
            f"Professional {platform} thumbnail",
            f"Style: {template.style}",
            f"Title text: '{title}'",
            f"Topic: {topic}",
            f"Color scheme: {', '.join(template.color_scheme)}",
            "High quality, eye-catching design"
        ]
        
        # Add platform-specific elements
        if platform == "youtube":
            prompt_parts.extend([
                "16:9 aspect ratio",
                "Bold, readable text overlay",
                "Compelling visual elements",
                "Professional lighting"
            ])
        elif platform in ["tiktok", "instagram"]:
            prompt_parts.extend([
                "9:16 vertical aspect ratio",
                "Trendy, viral design elements",
                "Mobile-optimized layout",
                "High contrast colors"
            ])
        
        # Add template-specific elements
        for element in template.visual_elements:
            prompt_parts.append(f"Include: {element}")
        
        # Add text specifications
        for text_key, text_config in template.text_elements.items():
            prompt_parts.append(f"Text '{text_key}': {text_config['font_size']}px, {text_config['color']}")
        
        return ", ".join(prompt_parts)
    
    async def _create_placeholder_thumbnail(self, path: str, prompt: str):
        """Create placeholder thumbnail (for testing)"""
        
        # This would be replaced with actual image generation
        # For now, create a simple text file as placeholder
        with open(path, 'w') as f:
            f.write(f"THUMBNAIL PLACEHOLDER\n")
            f.write(f"Prompt: {prompt}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
    
    def _predict_thumbnail_performance(self,
                                     template: ThumbnailTemplate,
                                     video_metadata: Dict[str, Any],
                                     platform: str) -> float:
        """Predict thumbnail performance score (1-10)"""
        
        score = template.performance_score
        
        # Platform-specific adjustments
        if platform == "youtube":
            if template.style in ["bold_text", "comparison"]:
                score += 0.5  # Good for YouTube
        elif platform in ["tiktok", "instagram"]:
            if template.style in ["trending", "emotional"]:
                score += 0.7  # Good for social media
        
        # Content-based adjustments
        topic = video_metadata.get('main_topic', '').lower()
        if 'productivity' in topic and 'minimal' in template.style:
            score += 0.3  # Professional content likes clean design
        elif 'amazing' in str(video_metadata.get('title', '')).lower() and 'emotional' in template.style:
            score += 0.4  # Emotional content works well with expressive thumbnails
        
        return min(10.0, score)
    
    async def optimize_thumbnails_for_ab_testing(self,
                                               thumbnails: List[GeneratedThumbnail],
                                               test_groups: int = 2) -> Dict[str, List[GeneratedThumbnail]]:
        """Optimize thumbnails for A/B testing"""
        
        test_groups_dict = {}
        
        # Sort thumbnails by performance score
        sorted_thumbnails = sorted(thumbnails, key=lambda t: t.performance_prediction, reverse=True)
        
        # Distribute into test groups
        for i in range(test_groups):
            group_name = f"test_group_{i+1}"
            group_thumbnails = sorted_thumbnails[i::test_groups]
            test_groups_dict[group_name] = group_thumbnails
        
        logger.info(f"📊 Created {test_groups} A/B test groups")
        return test_groups_dict
    
    async def generate_thumbnail_variations(self,
                                          base_thumbnail: GeneratedThumbnail,
                                          content_changes: Dict[str, Any]) -> List[GeneratedThumbnail]:
        """Generate variations of existing thumbnail with content changes"""
        
        variations = []
        base_template = next(t for t in self.templates if t.id == base_thumbnail.template_id)
        
        # Create variations with different text or colors
        variation_configs = [
            {"text_color": "#FF0000", "background_color": "#FFFFFF"},
            {"text_color": "#0000FF", "background_color": "#FFFF00"},
            {"text_color": "#00FF00", "background_color": "#000000"},
            {"text_color": "#FF00FF", "background_color": "#00FFFF"}
        ]
        
        for i, config in enumerate(variation_configs):
            variation = base_thumbnail.copy()
            variation.id = str(uuid.uuid4())
            variation.variation_number = i + 1
            variation.file_path = variation.file_path.replace(
                f"_v{base_thumbnail.variation_number}",
                f"_v{base_thumbnail.variation_number}_var{i+1}"
            )
            
            # Update color scheme
            variation.metadata['color_variation'] = config
            variation.performance_prediction += (i - 1) * 0.1  # Small variation in predicted performance
            
            variations.append(variation)
        
        return variations
    
    async def create_thumbnail_series(self,
                                    video_metadata: Dict[str, Any],
                                    series_concept: str,
                                    episode_count: int) -> List[List[GeneratedThumbnail]]:
        """Create thumbnail series for multi-part content"""
        
        series_thumbnails = []
        
        for episode in range(1, episode_count + 1):
            episode_metadata = video_metadata.copy()
            episode_metadata['episode'] = episode
            episode_metadata['title'] = f"{video_metadata['title']} - Episode {episode}"
            
            # Generate thumbnails for this episode
            episode_thumbnails = await self.generate_thumbnails(
                video_metadata=episode_metadata,
                platform="youtube",
                variation_count=3
            )
            
            # Add episode-specific branding
            for thumbnail in episode_thumbnails:
                thumbnail.metadata['series_concept'] = series_concept
                thumbnail.metadata['episode_number'] = episode
                thumbnail.file_path = thumbnail.file_path.replace(
                    "thumbnail_", f"episode_{episode}_thumbnail_"
                )
            
            series_thumbnails.append(episode_thumbnails)
        
        logger.info(f"🎬 Created thumbnail series: {len(series_thumbnails)} episodes")
        return series_thumbnails
    
    def get_best_performing_template(self, platform: str) -> ThumbnailTemplate:
        """Get best performing template for platform"""
        
        platform_templates = [t for t in self.templates if t.platform_optimized]
        return max(platform_templates, key=lambda t: t.performance_score)
    
    def recommend_thumbnails_for_content_type(self, content_type: str, platform: str) -> List[str]:
        """Recommend thumbnail templates based on content type"""
        
        recommendations = {
            'educational': ['bold_text', 'minimal_clean'],
            'entertainment': ['emotional_reaction', 'trending_viral'],
            'tutorial': ['bold_text', 'split_screen'],
            'motivation': ['emotional_reaction', 'trending_viral'],
            'news': ['bold_text', 'minimal_clean'],
            'review': ['split_screen', 'minimal_clean']
        }
        
        content_recommendations = recommendations.get(content_type, ['bold_text', 'emotional_reaction'])
        
        # Filter by platform compatibility
        if platform in ['tiktok', 'instagram']:
            # Social platforms prefer trending styles
            return [t for t in content_recommendations if 'trending' in t or 'emotional' in t]
        else:
            return content_recommendations

# Test function
async def test_thumbnail_generator():
    """Test the thumbnail generator"""
    
    generator = ThumbnailGenerator("/tmp/thumbnail_test")
    
    # Mock video metadata
    video_metadata = {
        'title': '5 Productivity Hacks That Will Change Your Life',
        'main_topic': 'productivity',
        'content_type': 'educational',
        'duration': 600,
        'key_points': ['2-minute rule', 'Time blocking', 'Task prioritization']
    }
    
    # Test thumbnail generation
    thumbnails = await generator.generate_thumbnails(
        video_metadata=video_metadata,
        platform="youtube",
        variation_count=3
    )
    
    print(f"🖼️ Generated {len(thumbnails)} thumbnails:")
    for i, thumbnail in enumerate(thumbnails, 1):
        print(f"{i}. Template: {thumbnail.template_id}")
        print(f"   Performance Score: {thumbnail.performance_prediction:.1f}")
        print(f"   File: {thumbnail.file_path}")
        print(f"   AB Test Group: {thumbnail.ab_test_group}")
    
    # Test A/B testing optimization
    test_groups = await generator.optimize_thumbnails_for_ab_testing(thumbnails)
    print(f"\n📊 A/B Test Groups: {list(test_groups.keys())}")
    
    # Test template recommendations
    recommendations = generator.recommend_thumbnails_for_content_type('educational', 'youtube')
    print(f"\n💡 Recommended templates for educational content: {recommendations}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_thumbnail_generator())