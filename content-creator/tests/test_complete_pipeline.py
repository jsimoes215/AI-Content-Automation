"""
Test Script - Demonstrates the complete content creation pipeline
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.append('/workspace/content-creator')

from api.main_pipeline import PipelineFactory, ContentCreationRequest

async def test_complete_pipeline():
    """Test the complete content creation pipeline"""
    
    print("🚀 Starting Automated Content Creator Test")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = PipelineFactory.get_pipeline()
    
    # Test Case 1: Basic productivity video
    print("\n📝 Test Case 1: AI Productivity Tools")
    print("-" * 40)
    
    request1 = pipeline.create_request_from_idea(
        idea="How to boost your productivity with AI automation tools - save 2 hours daily with these 5 strategies",
        target_audience="busy professionals and entrepreneurs",
        tone="educational",
        platforms=["youtube", "tiktok", "instagram"],
        style_preferences={
            "voice": "professional_female",
            "video_style": "corporate_professional",
            "background_music_style": "upbeat",
            "resolution": "1920x1080",
            "fps": 30,
            "generate_thumbnails": True,
            "energy_level": 0.7
        },
        duration_preferences={
            "youtube": 480,  # 8 minutes
            "tiktok": 45,   # 45 seconds
            "instagram": 60  # 1 minute
        }
    )
    
    print(f"Request ID: {request1.id}")
    print(f"Idea: {request1.original_idea}")
    print(f"Platforms: {request1.platforms}")
    print(f"Target Duration: {request1.duration_preferences}")
    
    try:
        result1 = await pipeline.create_content(request1)
        
        print(f"\n✅ Result Status: {result1.status}")
        print(f"⏱️ Processing Time: {result1.processing_time:.2f} seconds")
        
        if result1.script:
            print(f"📄 Script Generated:")
            print(f"   Title: {result1.script.title}")
            print(f"   Duration: {result1.script.total_duration}s")
            print(f"   Scenes: {len(result1.script.scenes)}")
            print(f"   Word Count: {result1.script.word_count}")
            
            # Display scene breakdown
            print(f"\n🎬 Scene Breakdown:")
            for i, scene in enumerate(result1.script.scenes[:3]):  # Show first 3 scenes
                print(f"   Scene {scene.scene_number}: {scene.scene_type} ({scene.duration}s)")
                print(f"      Voiceover: {scene.voiceover_text[:80]}...")
        
        if result1.video_compositions:
            print(f"\n🎥 Videos Generated:")
            for platform, composition in result1.video_compositions.items():
                print(f"   {platform.title()}: {composition.total_duration}s, {composition.resolution}")
        
        if result1.audio_mixes:
            print(f"\n🎵 Audio Generated:")
            for platform, audio_mix in result1.audio_mixes.items():
                has_music = "with" if audio_mix.background_music else "without"
                print(f"   {platform.title()}: {audio_mix.total_duration}s {has_music} background music")
        
        if result1.platform_content:
            print(f"\n📱 Platform Content:")
            for platform, content in result1.platform_content.items():
                text_preview = content["text_content"][:100] + "..." if len(content["text_content"]) > 100 else content["text_content"]
                print(f"   {platform.title()}: {text_preview}")
        
        if result1.library_scenes:
            print(f"\n📚 Library Scenes Added: {len(result1.library_scenes)}")
            for scene in result1.library_scenes[:3]:  # Show first 3
                print(f"   - {scene.title} ({scene.duration}s)")
        
        if result1.error_message:
            print(f"❌ Error: {result1.error_message}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    
    # Test Case 2: Tutorial with different style
    print(f"\n\n📝 Test Case 2: Tutorial Style Content")
    print("-" * 40)
    
    request2 = pipeline.create_request_from_idea(
        idea="Step-by-step tutorial: How to set up your first AI workflow automation in 15 minutes",
        target_audience="beginners and small business owners",
        tone="casual",
        platforms=["youtube", "linkedin"],
        style_preferences={
            "voice": "casual_female",
            "video_style": "clean_tutorial",
            "background_music_style": "calm",
            "resolution": "1920x1080",
            "generate_thumbnails": True,
            "energy_level": 0.5
        },
        duration_preferences={
            "youtube": 900,  # 15 minutes
            "linkedin": 300  # 5 minutes (text summary)
        }
    )
    
    try:
        result2 = await pipeline.create_content(request2)
        
        print(f"✅ Result Status: {result2.status}")
        print(f"⏱️ Processing Time: {result2.processing_time:.2f} seconds")
        
        if result2.script:
            print(f"📄 Script Title: {result2.script.title}")
            print(f"🎯 Target Audience: {result2.script.target_audience}")
            print(f"💭 Tone: {result2.script.tone}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    
    # Test Case 3: Short-form content
    print(f"\n\n📝 Test Case 3: Short-form Content")
    print("-" * 40)
    
    request3 = pipeline.create_request_from_idea(
        idea="Quick tip: One AI prompt that saves hours of work every week",
        target_audience="content creators and marketers",
        tone="energetic",
        platforms=["tiktok", "instagram", "twitter"],
        style_preferences={
            "voice": "energetic_male",
            "video_style": "dynamic_animated",
            "background_music_style": "energetic",
            "resolution": "1080x1920",  # Vertical for short-form
            "generate_thumbnails": True,
            "energy_level": 0.9
        },
        duration_preferences={
            "tiktok": 30,      # 30 seconds
            "instagram": 45,   # 45 seconds
            "twitter": 15      # 15 seconds
        }
    )
    
    try:
        result3 = await pipeline.create_content(request3)
        
        print(f"✅ Result Status: {result3.status}")
        print(f"⏱️ Processing Time: {result3.processing_time:.2f} seconds")
        
        if result3.platform_content:
            print(f"\n📱 Platform Text Previews:")
            for platform, content in result3.platform_content.items():
                hashtags_count = len(content["hashtags"])
                print(f"   {platform.title()}: {hashtags_count} hashtags")
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    
    # Get pipeline statistics
    print(f"\n\n📊 Pipeline Statistics")
    print("=" * 60)
    
    try:
        stats = await pipeline.get_pipeline_stats()
        
        print(f"📈 Processing Stats:")
        processing = stats.get("processing_stats", {})
        print(f"   Total Requests: {processing.get('total_requests', 0)}")
        print(f"   Successful: {processing.get('successful_requests', 0)}")
        print(f"   Failed: {processing.get('failed_requests', 0)}")
        print(f"   Average Time: {processing.get('average_processing_time', 0):.2f}s")
        print(f"   Error Rate: {processing.get('error_rate', 0)*100:.1f}%")
        
        print(f"\n📚 Content Library:")
        library = stats.get("content_library_stats", {})
        print(f"   Total Scenes: {library.get('total_scenes', 0)}")
        print(f"   Average Quality: {library.get('average_quality', 0):.1f}/10")
        
        if library.get('most_used_scenes'):
            print(f"   Most Used Scene: {library['most_used_scenes'][0].get('title', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Failed to get statistics: {e}")
    
    print(f"\n🎉 Test completed!")
    print("=" * 60)

async def test_content_library_search():
    """Test content library search functionality"""
    
    print("\n🔍 Testing Content Library Search")
    print("=" * 60)
    
    try:
        from api.content_library.library_manager import ContentLibraryFactory, SearchQuery
        
        library = ContentLibraryFactory.get_library()
        
        # Create search query
        search_query = SearchQuery(
            query_text="productivity tools",
            tags=["productivity", "ai-tools", "automation"],
            duration_range=(30, 120),
            content_types=["explainer", "tutorial"],
            quality_threshold=6.0,
            platform=None,
            limit=5,
            similarity_threshold=0.5
        )
        
        # Search for scenes
        results = await library.search_scenes(search_query)
        
        print(f"🔎 Search Results: {len(results)} scenes found")
        
        for i, result in enumerate(results[:3]):
            scene = result.scene
            print(f"\n   Result {i+1}: {scene.title}")
            print(f"   Duration: {scene.duration}s")
            print(f"   Quality: {scene.quality_score}/10")
            print(f"   Similarity: {result.similarity_score:.2f}")
            print(f"   Tags: {', '.join(scene.tags.get('specific_tags', []))}")
            print(f"   Match Reasons: {', '.join(result.match_reasons)}")
        
        # Get library statistics
        stats = await library.get_content_library_stats()
        print(f"\n📚 Library Stats: {stats['total_scenes']} scenes total")
        
    except Exception as e:
        print(f"❌ Content library search test failed: {e}")

async def test_script_generation():
    """Test script generation independently"""
    
    print("\n📄 Testing Script Generation")
    print("=" * 60)
    
    try:
        from api.scripts.script_generator import ScriptGenerator
        
        generator = ScriptGenerator()
        
        # Test different types of content
        test_cases = [
            {
                "idea": "How to double your productivity with AI tools",
                "platform": "youtube",
                "duration": 600
            },
            {
                "idea": "3 AI secrets that will change your workflow forever",
                "platform": "tiktok",
                "duration": 60
            },
            {
                "idea": "Complete guide to AI automation for small businesses",
                "platform": "instagram",
                "duration": 90
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test Case {i}: {test_case['platform'].title()}")
            
            script = generator.generate_script(
                idea=test_case["idea"],
                target_audience="professionals",
                tone="educational",
                platform=test_case["platform"],
                duration_target=test_case["duration"]
            )
            
            print(f"   Title: {script.title}")
            print(f"   Duration: {script.total_duration}s")
            print(f"   Scenes: {len(script.scenes)}")
            print(f"   Word Count: {script.word_count}")
            
            # Show scene breakdown
            for scene in script.scenes:
                print(f"     Scene {scene.scene_number}: {scene.scene_type} ({scene.duration}s)")
            
            # Show platform adaptations
            if script.scenes[0].platform_adaptations:
                print(f"   Platform adaptations: {list(script.scenes[0].platform_adaptations.keys())}")
        
    except Exception as e:
        print(f"❌ Script generation test failed: {e}")

async def run_all_tests():
    """Run all tests"""
    
    print("🧪 Running Complete Test Suite")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test components individually
    await test_script_generation()
    await test_content_library_search()
    
    # Test complete pipeline
    await test_complete_pipeline()
    
    print(f"\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(run_all_tests())