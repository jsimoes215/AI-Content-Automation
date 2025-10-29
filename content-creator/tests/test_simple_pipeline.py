"""
Simplified Main Pipeline - For testing without complex dependencies
"""

import uuid
from datetime import datetime

# Simplified imports
import sys
sys.path.append('/workspace/content-creator')

from api.scripts.simple_generator import SimpleScriptGenerator

class SimpleContentPipeline:
    """Simplified content pipeline for testing"""
    
    def __init__(self):
        self.script_generator = SimpleScriptGenerator()
        self.stats = {"requests_processed": 0}
    
    async def create_content(self, idea, target_audience="general", platforms=None, style_preferences=None):
        """Create content from idea - simplified version"""
        
        if platforms is None:
            platforms = ["youtube"]
        
        self.stats["requests_processed"] += 1
        
        # Generate script
        script = self.script_generator.generate_script(
            idea=idea,
            target_audience=target_audience,
            platform=platforms[0]  # Use first platform for script generation
        )
        
        # Mock video generation
        video_compositions = {}
        for platform in platforms:
            video_compositions[platform] = {
                "output_file": f"/mock/videos/{platform}_video.mp4",
                "total_duration": script["total_duration"],
                "resolution": "1920x1080" if platform == "youtube" else "1080x1920"
            }
        
        # Mock audio generation
        audio_mixes = {}
        for platform in platforms:
            audio_mixes[platform] = {
                "output_file": f"/mock/audio/{platform}_audio.mp3",
                "total_duration": script["total_duration"],
                "background_music": True
            }
        
        # Mock platform content
        platform_content = {}
        for platform in platforms:
            platform_content[platform] = {
                "text_content": f"Check out this amazing content about {idea}!",
                "hashtags": script["hashtags"].get(platform, []),
                "description": f"Learn about {idea} in this {platform} video",
                "thumbnail": f"/mock/thumbnails/{platform}_thumb.jpg"
            }
        
        # Mock result
        result = {
            "id": str(uuid.uuid4()),
            "status": "completed",
            "script": script,
            "video_compositions": video_compositions,
            "audio_mixes": audio_mixes,
            "platform_content": platform_content,
            "processing_time": 15.5,
            "created_at": datetime.now().isoformat()
        }
        
        return result
    
    def get_stats(self):
        """Get pipeline statistics"""
        return {
            "requests_processed": self.stats["requests_processed"],
            "pipeline_version": "1.0-simplified"
        }

# Test function
async def test_simple_pipeline():
    """Test the simplified pipeline"""
    
    print("🚀 Testing Simplified Content Pipeline")
    print("=" * 50)
    
    pipeline = SimpleContentPipeline()
    
    # Test case 1
    print("\n📝 Test Case 1: AI Productivity")
    result1 = await pipeline.create_content(
        idea="How to boost productivity with AI automation tools",
        target_audience="busy professionals",
        platforms=["youtube", "tiktok"]
    )
    
    print(f"✅ Status: {result1['status']}")
    print(f"📄 Title: {result1['script']['title']}")
    print(f"⏱️ Duration: {result1['script']['total_duration']}s")
    print(f"🎬 Scenes: {len(result1['script']['scenes'])}")
    print(f"📱 Platforms: {list(result1['video_compositions'].keys())}")
    print(f"⏱️ Processing: {result1['processing_time']}s")
    
    # Test case 2
    print("\n📝 Test Case 2: Quick TikTok Tutorial")
    result2 = await pipeline.create_content(
        idea="One AI trick that saves hours daily",
        target_audience="content creators",
        platforms=["tiktok", "instagram"],
        style_preferences={"voice": "energetic"}
    )
    
    print(f"✅ Status: {result2['status']}")
    print(f"📱 Platform: {list(result2['video_compositions'].keys())}")
    print(f"📝 Text Preview: {result2['platform_content']['tiktok']['text_content'][:50]}...")
    
    # Show statistics
    print(f"\n📊 Pipeline Stats:")
    stats = pipeline.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print(f"\n🎉 Pipeline test completed!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_simple_pipeline())
