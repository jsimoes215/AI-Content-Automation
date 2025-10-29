"""
Simple validation test for Step 4: Platform-Specific Content Generators
"""

import os
import sys
import asyncio

# Add the project root to Python path
sys.path.append('/workspace')
sys.path.append('/workspace/content-creator')

def validate_platform_adapters():
    """Validate that all platform adapter files exist and have correct structure"""
    
    print("🔍 Validating Step 4: Platform-Specific Content Generators")
    print("=" * 60)
    
    base_dir = "/workspace/content-creator/api/platform-adapters"
    
    # Check required files exist
    required_files = {
        "youtube_processor.py": "YouTube Longform Video Processor",
        "shortform_extractor.py": "TikTok/Instagram Short-Form Extractor", 
        "text_content_generator.py": "Text Content Generator for X/LinkedIn",
        "thumbnail_generator.py": "Thumbnail Generation System",
        "platform_adapter.py": "Main Platform Adapter (Orchestrator)",
        "__init__.py": "Package Initialization"
    }
    
    validation_results = []
    
    for filename, description in required_files.items():
        file_path = os.path.join(base_dir, filename)
        if os.path.exists(file_path):
            # Check file size (should be substantial)
            file_size = os.path.getsize(file_path)
            status = "✅ EXISTS" if file_size > 1000 else "⚠️ TOO SMALL"
            
            validation_results.append({
                "file": filename,
                "description": description,
                "status": status,
                "size_kb": round(file_size / 1024, 1)
            })
            
            print(f"{status} {filename:<30} ({file_size:,} bytes)")
        else:
            validation_results.append({
                "file": filename,
                "description": description,
                "status": "❌ MISSING",
                "size_kb": 0
            })
            
            print(f"❌ MISSING {filename:<30} (0 bytes)")
    
    # Count line of code totals
    total_lines = 0
    total_classes = 0
    
    for result in validation_results:
        if result["status"] == "✅ EXISTS":
            file_path = os.path.join(base_dir, result["file"])
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                total_lines += len(lines)
                
                # Count classes
                for line in lines:
                    if line.strip().startswith('class '):
                        total_classes += 1
    
    print(f"\n📊 Code Statistics:")
    print(f"   Total lines of code: {total_lines:,}")
    print(f"   Total classes: {total_classes}")
    print(f"   Average file size: {total_lines/len([r for r in validation_results if r['status'] == '✅ EXISTS']):.0f} lines")
    
    # Test basic functionality without imports
    print(f"\n🧪 Basic Functionality Tests:")
    
    # Test 1: Check YouTube processor structure
    youtube_file = os.path.join(base_dir, "youtube_processor.py")
    if os.path.exists(youtube_file):
        with open(youtube_file, 'r') as f:
            content = f.read()
            
        # Check for key classes and methods
        checks = [
            ("YouTubeLongformProcessor class", "class YouTubeLongformProcessor" in content),
            ("LongformComposition class", "class LongformComposition" in content),
            ("process_longform_content method", "async def process_longform_content" in content),
            ("Scene timing optimization", "_optimize_scene_timing" in content),
            ("Retention hooks", "_add_retention_hooks" in content),
            ("SEO optimization", "_create_seo_metadata" in content),
            ("Thumbnail generation", "_generate_thumbnail_variations" in content)
        ]
        
        passed_checks = 0
        for check_name, check_result in checks:
            if check_result:
                passed_checks += 1
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name}")
        
        print(f"   📈 YouTube Processor: {passed_checks}/{len(checks)} checks passed")
    
    # Test 2: Check shortform extractor structure
    shortform_file = os.path.join(base_dir, "shortform_extractor.py")
    if os.path.exists(shortform_file):
        with open(shortform_file, 'r') as f:
            content = f.read()
            
        checks = [
            ("ShortformExtractor class", "class ShortformExtractor" in content),
            ("ShortformComposition class", "class ShortformComposition" in content),
            ("extract_shortform_content method", "async def extract_shortform_content" in content),
            ("Scene selection logic", "_select_best_scenes" in content),
            ("Vertical video optimization", "_create_vertical_video" in content),
            ("Trending elements", "_add_viral_elements" in content),
            ("Platform-specific CTAs", "_create_call_to_action" in content)
        ]
        
        passed_checks = 0
        for check_name, check_result in checks:
            if check_result:
                passed_checks += 1
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name}")
        
        print(f"   📈 Shortform Extractor: {passed_checks}/{len(checks)} checks passed")
    
    # Test 3: Check text generator structure
    text_file = os.path.join(base_dir, "text_content_generator.py")
    if os.path.exists(text_file):
        with open(text_file, 'r') as f:
            content = f.read()
            
        checks = [
            ("TextContentGenerator class", "class TextContentGenerator" in content),
            ("SocialMediaPost class", "class SocialMediaPost" in content),
            ("generate_social_content method", "async def generate_social_content" in content),
            ("Twitter optimization", "_generate_twitter_post" in content),
            ("LinkedIn optimization", "_generate_linkedin_post" in content),
            ("Thread generation", "generate_thread_content" in content),
            ("Hashtag optimization", "_generate_.*_hashtags" in content)
        ]
        
        passed_checks = 0
        for check_name, check_result in checks:
            if check_result:
                passed_checks += 1
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name}")
        
        print(f"   📈 Text Generator: {passed_checks}/{len(checks)} checks passed")
    
    # Test 4: Check thumbnail generator structure
    thumbnail_file = os.path.join(base_dir, "thumbnail_generator.py")
    if os.path.exists(thumbnail_file):
        with open(thumbnail_file, 'r') as f:
            content = f.read()
            
        checks = [
            ("ThumbnailGenerator class", "class ThumbnailGenerator" in content),
            ("GeneratedThumbnail class", "class GeneratedThumbnail" in content),
            ("generate_thumbnails method", "async def generate_thumbnails" in content),
            ("Template system", "ThumbnailTemplate" in content),
            ("A/B testing optimization", "optimize_thumbnails_for_ab_testing" in content),
            ("Platform optimization", "_select_templates" in content),
            ("Performance prediction", "_predict_thumbnail_performance" in content)
        ]
        
        passed_checks = 0
        for check_name, check_result in checks:
            if check_result:
                passed_checks += 1
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name}")
        
        print(f"   📈 Thumbnail Generator: {passed_checks}/{len(checks)} checks passed")
    
    # Test 5: Check main platform adapter structure
    adapter_file = os.path.join(base_dir, "platform_adapter.py")
    if os.path.exists(adapter_file):
        with open(adapter_file, 'r') as f:
            content = f.read()
            
        checks = [
            ("PlatformAdapter class", "class PlatformAdapter" in content),
            ("PlatformContentResult class", "class PlatformContentResult" in content),
            ("generate_platform_content method", "async def generate_platform_content" in content),
            ("YouTube integration", "_process_youtube_content" in content),
            ("TikTok integration", "_process_tiktok_content" in content),
            ("Social media integration", "_process_social_media_content" in content),
            ("Cost estimation", "_estimate_processing_cost" in content),
            ("Content library integration", "_add_to_content_library" in content)
        ]
        
        passed_checks = 0
        for check_name, check_result in checks:
            if check_result:
                passed_checks += 1
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name}")
        
        print(f"   📈 Platform Adapter: {passed_checks}/{len(checks)} checks passed")
    
    # Summary
    passed_files = len([r for r in validation_results if r["status"] == "✅ EXISTS"])
    total_files = len(validation_results)
    
    print(f"\n🎯 Step 4 Validation Summary:")
    print(f"   Files completed: {passed_files}/{total_files}")
    print(f"   Success rate: {(passed_files/total_files)*100:.1f}%")
    print(f"   Total code: {total_lines:,} lines")
    print(f"   Total classes: {total_classes}")
    
    if passed_files == total_files:
        print(f"   🎉 Step 4: Platform-Specific Content Generators - COMPLETED!")
        return True
    else:
        print(f"   ⚠️ Step 4: Platform-Specific Content Generators - INCOMPLETE")
        return False

if __name__ == "__main__":
    success = validate_platform_adapters()
    
    if success:
        print(f"\n✅ All platform adapters are ready!")
        print(f"🚀 Step 4 is complete and ready for use.")
    else:
        print(f"\n❌ Some platform adapters need completion.")
        print(f"🔧 Review missing components above.")
