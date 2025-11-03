"""
Main Content Creation Pipeline - Coordinates all components for end-to-end content generation
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Import pipeline components
from api.scripts.script_generator import ScriptGenerator, Script
from api.audio_processing.audio_pipeline import AudioPipeline, AudioMix
from api.video_generation.video_pipeline import VideoGenerationPipeline, VideoComposition
from api.content_library.library_manager import ContentLibraryManager, SceneMetadata, SearchQuery
from api.sentiment_analysis import SentimentAnalysisPipeline, SentimentAnalysisPipelineFactory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ContentCreationRequest:
    """Request for content creation"""
    id: str
    original_idea: str
    target_audience: str
    tone: str
    platforms: List[str]
    style_preferences: Dict[str, Any]
    duration_preferences: Dict[str, int]
    include_background_music: bool
    auto_optimize: bool
    add_to_library: bool
    created_at: str

@dataclass
class ContentCreationResult:
    """Result of content creation process"""
    id: str
    request_id: str
    status: str
    script: Optional[Script]
    video_compositions: Dict[str, VideoComposition]  # platform -> composition
    audio_mixes: Dict[str, AudioMix]  # platform -> audio mix
    platform_content: Dict[str, Dict[str, Any]]  # platform -> content variations
    library_scenes: List[SceneMetadata]
    processing_time: float
    error_message: Optional[str]
    created_at: str

class ContentCreationPipeline:
    """Main pipeline that orchestrates all content creation steps"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.generated_content_dir = f"{project_root}/generated-content"
        self.config_dir = f"{project_root}/config"
        
        # Initialize components
        self.script_generator = ScriptGenerator()
        self.audio_pipeline = None  # Will be initialized per request
        self.video_pipeline = None  # Will be initialized per request
        self.content_library = ContentLibraryManager(f"{project_root}/content-library")
        self.sentiment_pipeline = SentimentAnalysisPipelineFactory.get_pipeline()
        
        # Processing statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_processing_time": 0.0,
            "popular_platforms": {},
            "error_rate": 0.0
        }
    
    async def create_content(self, request: ContentCreationRequest) -> ContentCreationResult:
        """
        Main method to create content from idea to final output
        
        Args:
            request: ContentCreationRequest with all requirements
            
        Returns:
            ContentCreationResult with all generated content
        """
        
        start_time = datetime.now()
        logger.info(f"Starting content creation for request: {request.id}")
        
        try:
            # Update statistics
            self.stats["total_requests"] += 1
            
            # Step 1: Generate script from idea
            script = await self._generate_script(request)
            
            # Step 2: Generate audio (voiceover + background music)
            audio_mixes = await self._generate_audio(request, script)
            
            # Step 3: Generate videos
            video_compositions = await self._generate_videos(request, script)
            
            # Step 4: Create platform-specific adaptations
            platform_content = await self._create_platform_adaptations(
                request, script, video_compositions, audio_mixes
            )
            
            # Step 5: Add to content library if requested
            library_scenes = []
            if request.add_to_library:
                library_scenes = await self._add_to_content_library(request, script, video_compositions)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Update success statistics
            self.stats["successful_requests"] += 1
            self._update_processing_stats(processing_time)
            
            # Create result
            result = ContentCreationResult(
                id=str(uuid.uuid4()),
                request_id=request.id,
                status="completed",
                script=script,
                video_compositions=video_compositions,
                audio_mixes=audio_mixes,
                platform_content=platform_content,
                library_scenes=library_scenes,
                processing_time=processing_time,
                error_message=None,
                created_at=datetime.now().isoformat()
            )
            
            logger.info(f"Content creation completed in {processing_time:.2f} seconds")
            return result
            
        except Exception as e:
            # Update failure statistics
            self.stats["failed_requests"] += 1
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.error(f"Content creation failed: {e}")
            
            return ContentCreationResult(
                id=str(uuid.uuid4()),
                request_id=request.id,
                status="failed",
                script=None,
                video_compositions={},
                audio_mixes={},
                platform_content={},
                library_scenes=[],
                processing_time=processing_time,
                error_message=str(e),
                created_at=datetime.now().isoformat()
            )
    
    async def _generate_script(self, request: ContentCreationRequest) -> Script:
        """Generate script from the original idea"""
        
        logger.info("Generating script from idea...")
        
        # Determine target duration (use average of platform preferences)
        avg_duration = sum(request.duration_preferences.values()) / len(request.duration_preferences)
        
        # Determine primary platform for script optimization
        primary_platform = max(request.platforms, key=lambda p: request.duration_preferences.get(p, 0))
        
        # Generate script
        script = self.script_generator.generate_script(
            idea=request.original_idea,
            target_audience=request.target_audience,
            tone=request.tone,
            platform=primary_platform,
            duration_target=int(avg_duration)
        )
        
        logger.info(f"Script generated: {script.title} ({script.total_duration}s)")
        return script
    
    async def _generate_audio(self, request: ContentCreationRequest, script: Script) -> Dict[str, AudioMix]:
        """Generate audio for all platforms"""
        
        logger.info("Generating audio content...")
        
        # Initialize audio pipeline for this request
        audio_pipeline = AudioPipeline(f"{self.generated_content_dir}/audio/{request.id}")
        await audio_pipeline.initialize()
        
        self.audio_pipeline = audio_pipeline
        
        # Convert script scenes to audio pipeline format
        script_scenes = []
        for scene in script.scenes:
            scene_data = {
                "id": f"scene_{scene.scene_number}",
                "scene_number": scene.scene_number,
                "voiceover_text": scene.voiceover_text,
                "duration": scene.duration
            }
            script_scenes.append(scene_data)
        
        # Generate voiceover
        voice_segments = await audio_pipeline.generate_voiceover(
            script_scenes=script_scenes,
            voice_id=request.style_preferences.get("voice", "professional_female"),
            style_preferences=request.style_preferences
        )
        
        # Generate background music if requested
        background_music = None
        if request.include_background_music:
            background_music = await audio_pipeline.generate_background_music(
                duration=script.total_duration,
                style=request.style_preferences.get("background_music_style", "neutral"),
                mood=request.style_preferences.get("mood", "professional"),
                energy_level=request.style_preferences.get("energy_level", 0.5)
            )
        
        # Create audio mix
        audio_mix = await audio_pipeline.create_audio_mix(
            voice_segments=voice_segments,
            background_music=background_music,
            mix_settings=request.style_preferences.get("audio_settings", {})
        )
        
        # Optimize for each platform
        audio_mixes = {}
        for platform in request.platforms:
            optimized_mix = audio_pipeline.optimize_audio_for_platform(audio_mix, platform)
            audio_mixes[platform] = optimized_mix
        
        logger.info(f"Audio generated for {len(audio_mixes)} platforms")
        return audio_mixes
    
    async def _generate_videos(self, request: ContentCreationRequest, script: Script) -> Dict[str, VideoComposition]:
        """Generate videos for all platforms"""
        
        logger.info("Generating video content...")
        
        # Initialize video pipeline for this request
        video_pipeline = VideoGenerationPipeline(f"{self.generated_content_dir}/videos/{request.id}")
        self.video_pipeline = video_pipeline
        
        # Convert script scenes to video pipeline format
        script_scenes = []
        for scene in script.scenes:
            scene_data = {
                "id": f"scene_{scene.scene_number}",
                "scene_number": scene.scene_number,
                "visual_description": scene.visual_description,
                "duration": scene.duration
            }
            script_scenes.append(scene_data)
        
        # Generate videos
        video_segments = await video_pipeline.generate_video_from_script(
            script_scenes=script_scenes,
            resolution=request.style_preferences.get("resolution", "1920x1080"),
            fps=request.style_preferences.get("fps", 30),
            style_preferences=request.style_preferences
        )
        
        # Add transitions
        transitions = video_pipeline.add_transitions(video_segments, "fade", 1.0)
        
        # Create video composition
        composition = await video_pipeline.create_video_composition(
            video_segments=video_segments,
            transitions=transitions
        )
        
        # Optimize for each platform
        video_compositions = {}
        for platform in request.platforms:
            optimized_composition = video_pipeline.optimize_video_for_platform(composition, platform)
            video_compositions[platform] = optimized_composition
        
        logger.info(f"Videos generated for {len(video_compositions)} platforms")
        return video_compositions
    
    async def _create_platform_adaptations(self, 
                                          request: ContentCreationRequest,
                                          script: Script,
                                          video_compositions: Dict[str, VideoComposition],
                                          audio_mixes: Dict[str, AudioMix]) -> Dict[str, Dict[str, Any]]:
        """Create platform-specific content adaptations"""
        
        logger.info("Creating platform-specific adaptations...")
        
        platform_content = {}
        
        for platform in request.platforms:
            platform_data = {
                "video": {
                    "file_path": video_compositions[platform].output_file,
                    "duration": video_compositions[platform].total_duration,
                    "resolution": video_compositions[platform].resolution,
                    "thumbnail": None  # Will generate if requested
                },
                "audio": {
                    "file_path": audio_mixes[platform].output_file,
                    "duration": audio_mixes[platform].total_duration,
                    "has_background_music": audio_mixes[platform].background_music is not None
                },
                "text_content": self._generate_social_media_text(script, platform),
                "hashtags": script.hashtags.get(platform, []),
                "description": self._generate_platform_description(script, platform),
                "call_to_action": self._generate_platform_cta(script, platform)
            }
            
            # Generate thumbnail if requested
            if request.style_preferences.get("generate_thumbnails", True):
                thumbnail_path = await self.video_pipeline.generate_thumbnail(
                    video_compositions[platform]
                )
                platform_data["video"]["thumbnail"] = thumbnail_path
            
            platform_content[platform] = platform_data
        
        logger.info(f"Platform adaptations created for {len(platform_content)} platforms")
        return platform_content
    
    def _generate_social_media_text(self, script: Script, platform: str) -> str:
        """Generate platform-specific social media text"""
        
        if platform == "linkedin":
            return f"""🚀 {script.title}

{script.description}

In this comprehensive guide, we cover:
{chr(10).join([f"• {point}" for point in script.key_points[:3]])}

What are your thoughts on this approach? 👇

#Productivity #AI #Innovation"""
        
        elif platform == "twitter":
            return f"""💡 {script.title}

{script.description[:100]}...

Read more insights in the thread below 👇

#Productivity #AI #Tips"""
        
        elif platform == "instagram":
            return f"""✨ {script.title} ✨

{script.description}

Swipe to see the key points ➡️

Save this post for later! 📌

{chr(10).join([f"#{tag.replace(' ', '')}" for tag in script.hashtags.get(platform, [])[:5]])}"""
        
        else:
            return f"{script.title}\n\n{script.description}"
    
    def _generate_platform_description(self, script: Script, platform: str) -> str:
        """Generate platform-specific video descriptions"""
        
        if platform == "youtube":
            return f"""{script.description}

🎯 Timestamps:
00:00 Introduction
{self._generate_youtube_timestamps(script)}

💡 What you'll learn:
{chr(10).join([f"• {point}" for point in script.key_points])}

🔗 Resources mentioned:
• [Tool 1]: [Link]
• [Tool 2]: [Link]

💬 Let me know in the comments:
What's your biggest productivity challenge?

👍 Like this video if it helped you!
🔔 Subscribe for more productivity tips!

#Productivity #AI #Tools"""
        
        elif platform == "tiktok":
            return f"""{script.title}

Watch till the end for the best tips! 🔥

#FYP #Productivity #AI #Tips #HowTo"""
        
        else:
            return script.description
    
    def _generate_youtube_timestamps(self, script: Script) -> str:
        """Generate YouTube chapter timestamps"""
        
        timestamps = []
        current_time = 0
        
        for i, scene in enumerate(script.scenes):
            if i == 0:
                timestamps.append("00:00 Introduction")
            elif scene.scene_type == "main_content":
                minutes = int(current_time // 60)
                seconds = int(current_time % 60)
                timestamps.append(f"{minutes:02d}:{seconds:02d} {scene.scene_type.replace('_', ' ').title()}")
            current_time += scene.duration
        
        return "\n".join(timestamps)
    
    def _generate_platform_cta(self, script: Script, platform: str) -> str:
        """Generate platform-specific call-to-action"""
        
        ctas = {
            "youtube": "Subscribe for more productivity content! 🔔",
            "tiktok": "Follow for daily productivity tips! 💪",
            "instagram": "Save this and share with someone who needs it! ✨",
            "linkedin": "Connect with me for more insights! 🤝",
            "twitter": "Follow for more productivity tips! 🧵"
        }
        
        return ctas.get(platform, "Check out the full content!")
    
    async def _add_to_content_library(self, 
                                     request: ContentCreationRequest,
                                     script: Script,
                                     video_compositions: Dict[str, VideoComposition]) -> List[SceneMetadata]:
        """Add generated scenes to content library"""
        
        logger.info("Adding scenes to content library...")
        
        library_scenes = []
        
        # Add each scene to library
        for scene in script.scenes:
            scene_data = {
                "id": f"{request.id}_scene_{scene.scene_number}",
                "title": f"Scene {scene.scene_number}: {scene.scene_type.title()}",
                "description": scene.voiceover_text,
                "duration": scene.duration,
                "content_type": scene.scene_type,
                "style": request.style_preferences.get("video_style", "professional"),
                "mood": request.tone,
                "quality_score": 8.0,  # Default quality
                "performance_metrics": {}
            }
            
            # Create tags from script analysis
            tags = {
                "specific_tags": [scene.scene_type, request.tone, "script_scene"],
                "generic_tags": [request.target_audience.replace(" ", "-").lower()],
                "mood_tags": [request.tone],
                "style_tags": [request.style_preferences.get("video_style", "professional")]
            }
            
            # File paths (would be actual paths in production)
            file_paths = {
                "video": f"{self.generated_content_dir}/videos/{request.id}/scene_{scene.scene_number}.mp4",
                "audio": f"{self.generated_content_dir}/audio/{request.id}/scene_{scene.scene_number}.mp3",
                "thumbnail": f"{self.generated_content_dir}/thumbnails/{request.id}_scene_{scene.scene_number}.jpg"
            }
            
            # Add to library
            metadata = await self.content_library.add_scene_to_library(
                scene_data=scene_data,
                tags=tags,
                file_paths=file_paths,
                auto_tagging=True,
                generate_embedding=True
            )
            
            library_scenes.append(metadata)
        
        logger.info(f"Added {len(library_scenes)} scenes to library")
        return library_scenes
    
    def _update_processing_stats(self, processing_time: float):
        """Update processing time statistics"""
        
        current_avg = self.stats["average_processing_time"]
        total_requests = self.stats["successful_requests"]
        
        if total_requests == 1:
            self.stats["average_processing_time"] = processing_time
        else:
            # Calculate new average
            total_time = current_avg * (total_requests - 1) + processing_time
            self.stats["average_processing_time"] = total_time / total_requests
        
        # Update error rate
        self.stats["error_rate"] = self.stats["failed_requests"] / self.stats["total_requests"]
    
    async def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline processing statistics"""
        
        # Update with content library stats
        library_stats = await self.content_library.get_content_library_stats()
        
        return {
            "processing_stats": self.stats,
            "content_library_stats": library_stats,
            "pipeline_version": "1.0",
            "last_updated": datetime.now().isoformat()
        }
    
    def create_request_from_idea(self, 
                                idea: str,
                                target_audience: str = "general audience",
                                tone: str = "educational",
                                platforms: Optional[List[str]] = None,
                                style_preferences: Optional[Dict[str, Any]] = None,
                                duration_preferences: Optional[Dict[str, int]] = None,
                                include_background_music: bool = True,
                                auto_optimize: bool = True,
                                add_to_library: bool = True) -> ContentCreationRequest:
        """Create a ContentCreationRequest from basic parameters"""
        
        if platforms is None:
            platforms = ["youtube"]
        
        if style_preferences is None:
            style_preferences = {
                "voice": "professional_female",
                "video_style": "modern_clean",
                "background_music_style": "neutral",
                "resolution": "1920x1080",
                "fps": 30,
                "generate_thumbnails": True,
                "energy_level": 0.6
            }
        
        if duration_preferences is None:
            duration_preferences = {
                "youtube": 480,  # 8 minutes
                "tiktok": 45,    # 45 seconds
                "instagram": 60  # 1 minute
            }
        
        return ContentCreationRequest(
            id=str(uuid.uuid4()),
            original_idea=idea,
            target_audience=target_audience,
            tone=tone,
            platforms=platforms,
            style_preferences=style_preferences,
            duration_preferences=duration_preferences,
            include_background_music=include_background_music,
            auto_optimize=auto_optimize,
            add_to_library=add_to_library,
            created_at=datetime.now().isoformat()
        )

# Factory class for pipeline management
class PipelineFactory:
    """Factory for creating and managing pipeline instances"""
    
    _pipelines = {}
    
    @classmethod
    def get_pipeline(cls, pipeline_id: str = "default") -> ContentCreationPipeline:
        """Get or create pipeline instance"""
        
        if pipeline_id not in cls._pipelines:
            project_root = "/workspace/content-creator"
            cls._pipelines[pipeline_id] = ContentCreationPipeline(project_root)
        
        return cls._pipelines[pipeline_id]

# Example usage
async def main():
    """Example usage of the main content creation pipeline"""
    
    # Get pipeline instance
    pipeline = PipelineFactory.get_pipeline()
    
    # Create request from idea
    request = pipeline.create_request_from_idea(
        idea="How to improve productivity using AI automation tools for busy professionals",
        target_audience="busy professionals",
        tone="educational",
        platforms=["youtube", "tiktok", "instagram"],
        style_preferences={
            "voice": "professional_female",
            "video_style": "corporate_professional",
            "background_music_style": "neutral",
            "resolution": "1920x1080",
            "generate_thumbnails": True
        },
        duration_preferences={
            "youtube": 600,   # 10 minutes
            "tiktok": 60,     # 1 minute
            "instagram": 90   # 1.5 minutes
        }
    )
    
    # Create content
    result = await pipeline.create_content(request)
    
    print(f"Content creation result:")
    print(f"Status: {result.status}")
    print(f"Processing time: {result.processing_time:.2f} seconds")
    
    if result.script:
        print(f"Script title: {result.script.title}")
        print(f"Total duration: {result.script.total_duration} seconds")
        print(f"Number of scenes: {len(result.script.scenes)}")
    
    print(f"Platforms generated: {list(result.video_compositions.keys())}")
    print(f"Scenes added to library: {len(result.library_scenes)}")
    
    if result.error_message:
        print(f"Error: {result.error_message}")
    
    # Get pipeline statistics
    stats = await pipeline.get_pipeline_stats()
    print(f"Pipeline statistics: {stats}")

if __name__ == "__main__":
    asyncio.run(main())