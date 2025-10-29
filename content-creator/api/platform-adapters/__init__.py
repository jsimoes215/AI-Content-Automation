"""
Platform Adapters Package
"""

"""
Platform Adapters Package

This package contains platform-specific content generators that optimize content 
for different social media platforms and video formats.

Main Components:
- YouTubeLongformProcessor: Optimizes content for YouTube 8-15 minute videos
- ShortformExtractor: Creates TikTok/Instagram vertical videos (15-90 seconds)
- TextContentGenerator: Generates Twitter/LinkedIn text content
- ThumbnailGenerator: Creates platform-specific thumbnails with A/B testing
- PlatformAdapter: Orchestrates all platform-specific generation

Usage:
    from api.platform_adapters.platform_adapter import PlatformAdapter
    
    adapter = PlatformAdapter(output_dir)
    result = await adapter.generate_platform_content(
        script_scenes=scenes,
        video_composition=video_composition,
        video_metadata=metadata,
        target_platforms=["youtube", "tiktok", "instagram"]
    )
"""