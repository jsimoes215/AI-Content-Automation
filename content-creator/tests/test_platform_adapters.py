"""
Test Suite for Platform-Specific Content Generators
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Any

# Add the project root to Python path
sys.path.append('/workspace')
sys.path.append('/workspace/content-creator')

# Import platform adapters
from api.platform_adapters.platform_adapter import PlatformAdapter, PlatformContentResult
from api.platform_adapters.youtube_processor import YouTubeLongformProcessor
from api.platform_adapters.shortform_extractor import ShortformExtractor
from api.platform_adapters.text_content_generator import TextContentGenerator
from api.platform_adapters.thumbnail_generator import ThumbnailGenerator

# Import core pipeline
from api.scripts.simple_generator import SimpleScriptGenerator

class PlatformTestSuite:
    """Comprehensive test suite for platform adapters"""
    
    def __init__(self):
        self.test_results = []
        self.output_dir = "/tmp/platform_tests"
        
    async def run_all_tests(self):
        """Run all platform adapter tests"""
        
        print("🚀 Starting Platform Adapter Test Suite")
        print("=" * 60)
        
        # Create test directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Test 1: Individual Component Tests
        await self.test_individual_components()
        
        # Test 2: Integration Tests
        await self.test_platform_integration()
        
        # Test 3: End-to-End Pipeline Test
        await self.test_end_to_end_pipeline()
        
        # Test 4: Performance Tests
        await self.test_performance_benchmarks()
        
        # Test 5: Content Quality Tests
        await self.test_content_quality()
        
        # Generate test report
        await self.generate_test_report()
    
    async def test_individual_components(self):
        """Test individual platform components"""
        
        print("\n📋 Testing Individual Components")
        print("-" * 40)
        
        # Test 1.1: YouTube Longform Processor
        await self._test_youtube_processor()
        
        # Test 1.2: Short-form Extractor
        await self._test_shortform_extractor()
        
        # Test 1.3: Text Content Generator
        await self._test_text_generator()
        
        # Test 1.4: Thumbnail Generator
        await self._test_thumbnail_generator()
    
    async def _test_youtube_processor(self):
        """Test YouTube longform processor"""
        
        try:
            processor = YouTubeLongformProcessor(f"{self.output_dir}/youtube")
            
            # Mock script scenes
            mock_scenes = [
                {
                    "scene_number": 1,
                    "duration": 30,
                    "voiceover_text": "Welcome to this amazing topic that will change your life!",
                    "visual_description": "Professional introduction",
                    "scene_type": "intro"
                },
                {
                    "scene_number": 2,
                    "duration": 120,
                    "voiceover_text": "Here's the main content with detailed explanations and examples.",
                    "visual_description": "Main content demonstration",
                    "scene_type": "main_content"
                },
                {
                    "scene_number": 3,
                    "duration": 60,
                    "voiceover_text": "Try this method and watch your results improve dramatically!",
                    "visual_description": "Results demonstration",
                    "scene_type": "conclusion"
                }
            ]
            
            # Test processing
            result = await processor.process_longform_content(
                script_scenes=mock_scenes,
                video_composition=None,
                seo_data={"topic": "Productivity Mastery", "title": "Productivity Tips"}
            )
            
            # Validate results
            assert result.duration >= 480, f"Duration {result.duration}s too short for YouTube"
            assert result.duration <= 900, f"Duration {result.duration}s too long for YouTube"
            assert result.title, "Title should not be empty"
            assert len(result.scenes) >= len(mock_scenes), "Should have enhanced scenes"
            
            self.test_results.append({
                "test": "YouTube Processor",
                "status": "PASSED",
                "duration": result.duration,
                "scenes": len(result.scenes),
                "optimization_score": result.optimization_score
            })
            
            print(f"✅ YouTube Processor: {result.duration}s, {result.optimization_score:.1f} score")
            
        except Exception as e:
            self.test_results.append({
                "test": "YouTube Processor",
                "status": "FAILED",
                "error": str(e)
            })
            print(f"❌ YouTube Processor: {e}")
    
    async def _test_shortform_extractor(self):
        """Test short-form extractor for TikTok and Instagram"""
        
        try:
            extractor = ShortformExtractor(f"{self.output_dir}/shortform")
            
            # Mock script scenes
            mock_scenes = [
                {
                    "scene_number": 1,
                    "duration": 30,
                    "voiceover_text": "This productivity hack will blow your mind!",
                    "visual_description": "Eye-catching intro",
                    "scene_type": "intro"
                },
                {
                    "scene_number": 2,
                    "duration": 45,
                    "voiceover_text": "The 2-minute rule: if it takes less than 2 minutes, do it now!",
                    "visual_description": "Rule demonstration",
                    "scene_type": "main_content"
                }
            ]
            
            # Test TikTok extraction
            tiktok_result = await extractor.extract_shortform_content(
                script_scenes=mock_scenes,
                video_composition=None,
                platform="tiktok",
                content_style="educational"
            )
            
            # Test Instagram extraction
            instagram_result = await extractor.extract_shortform_content(
                script_scenes=mock_scenes,
                video_composition=None,
                platform="instagram",
                content_style="educational"
            )
            
            # Validate TikTok results
            assert 15 <= tiktok_result.duration <= 60, f"TikTok duration {tiktok_result.duration}s invalid"
            assert tiktok_result.hook_text, "TikTok should have hook text"
            assert len(tiktok_result.trending_tags) <= 8, "Too many TikTok tags"
            
            # Validate Instagram results
            assert 15 <= instagram_result.duration <= 90, f"Instagram duration {instagram_result.duration}s invalid"
            assert instagram_result.hook_text, "Instagram should have hook text"
            
            self.test_results.append({
                "test": "Shortform Extractor",
                "status": "PASSED",
                "tiktok_duration": tiktok_result.duration,
                "instagram_duration": instagram_result.duration,
                "tiktok_hooks": len(tiktok_result.trending_tags),
                "instagram_hooks": len(instagram_result.trending_tags)
            })
            
            print(f"✅ Shortform Extractor: TikTok {tiktok_result.duration}s, Instagram {instagram_result.duration}s")
            
        except Exception as e:
            self.test_results.append({
                "test": "Shortform Extractor",
                "status": "FAILED",
                "error": str(e)
            })
            print(f"❌ Shortform Extractor: {e}")
    
    async def _test_text_generator(self):
        """Test text content generator for social media"""
        
        try:
            generator = TextContentGenerator(f"{self.output_dir}/text")
            
            # Mock script scenes
            mock_scenes = [
                {
                    "scene_number": 1,
                    "duration": 30,
                    "voiceover_text": "Productivity can be transformed with simple techniques.",
                    "visual_description": "Productivity concepts",
                    "scene_type": "intro"
                },
                {
                    "scene_number": 2,
                    "duration": 60,
                    "voiceover_text": "The 2-minute rule states: if something takes less than 2 minutes, do it immediately.",
                    "visual_description": "2-minute rule explanation",
                    "scene_type": "main_content"
                }
            ]
            
            mock_metadata = {
                "title": "Productivity Hacks That Work",
                "main_topic": "productivity",
                "tone": "educational"
            }
            
            # Generate social content
            posts = await generator.generate_social_content(
                script_scenes=mock_scenes,
                video_metadata=mock_metadata,
                platforms=["twitter", "linkedin"]
            )
            
            # Validate Twitter post
            twitter_post = posts["twitter"]
            assert twitter_post.character_count <= 280, "Twitter post too long"
            assert len(twitter_post.hashtags) <= 2, "Too many Twitter hashtags"
            
            # Validate LinkedIn post
            linkedin_post = posts["linkedin"]
            assert linkedin_post.character_count <= 3000, "LinkedIn post too long"
            assert len(linkedin_post.hashtags) <= 3, "Too many LinkedIn hashtags"
            
            # Test thread generation
            thread = await generator.generate_thread_content(
                themes={"main_topic": "productivity"},
                scenes=mock_scenes
            )
            assert len(thread) >= 3, "Thread should have at least 3 tweets"
            
            self.test_results.append({
                "test": "Text Content Generator",
                "status": "PASSED",
                "twitter_chars": twitter_post.character_count,
                "linkedin_chars": linkedin_post.character_count,
                "thread_length": len(thread),
                "hashtags": {
                    "twitter": len(twitter_post.hashtags),
                    "linkedin": len(linkedin_post.hashtags)
                }
            })
            
            print(f"✅ Text Generator: Twitter {twitter_post.character_count} chars, LinkedIn {linkedin_post.character_count} chars")
            
        except Exception as e:
            self.test_results.append({
                "test": "Text Content Generator",
                "status": "FAILED",
                "error": str(e)
            })
            print(f"❌ Text Content Generator: {e}")
    
    async def _test_thumbnail_generator(self):
        """Test thumbnail generation system"""
        
        try:
            generator = ThumbnailGenerator(f"{self.output_dir}/thumbnails")
            
            # Mock video metadata
            video_metadata = {
                "title": "5 Productivity Hacks That Will Transform Your Life",
                "main_topic": "productivity",
                "content_type": "educational",
                "duration": 600
            }
            
            # Test thumbnail generation
            thumbnails = await generator.generate_thumbnails(
                video_metadata=video_metadata,
                platform="youtube",
                variation_count=3
            )
            
            # Validate thumbnails
            assert len(thumbnails) == 3, "Should generate 3 thumbnail variations"
            
            for thumbnail in thumbnails:
                assert thumbnail.platform == "youtube", "Platform mismatch"
                assert thumbnail.template_id, "Should have template ID"
                assert thumbnail.performance_prediction > 0, "Should have performance score"
                assert thumbnail.file_path, "Should have file path"
            
            # Test A/B testing groups
            test_groups = await generator.optimize_thumbnails_for_ab_testing(thumbnails)
            assert len(test_groups) >= 2, "Should create at least 2 A/B test groups"
            
            # Test template recommendations
            recommendations = generator.recommend_thumbnails_for_content_type("educational", "youtube")
            assert len(recommendations) > 0, "Should recommend templates"
            
            self.test_results.append({
                "test": "Thumbnail Generator",
                "status": "PASSED",
                "thumbnails_generated": len(thumbnails),
                "ab_test_groups": len(test_groups),
                "template_recommendations": len(recommendations),
                "avg_performance": sum(t.performance_prediction for t in thumbnails) / len(thumbnails)
            })
            
            print(f"✅ Thumbnail Generator: {len(thumbnails)} variations, {len(test_groups)} A/B groups")
            
        except Exception as e:
            self.test_results.append({
                "test": "Thumbnail Generator",
                "status": "FAILED",
                "error": str(e)
            })
            print(f"❌ Thumbnail Generator: {e}")
    
    async def test_platform_integration(self):
        """Test integration between platform components"""
        
        print("\n🔗 Testing Platform Integration")
        print("-" * 40)
        
        try:
            # Create platform adapter
            adapter = PlatformAdapter(f"{self.output_dir}/integration")
            
            # Mock script scenes
            mock_scenes = [
                {
                    "scene_number": 1,
                    "duration": 30,
                    "voiceover_text": "Welcome to this incredible productivity guide!",
                    "visual_description": "Professional introduction",
                    "scene_type": "intro"
                },
                {
                    "scene_number": 2,
                    "duration": 90,
                    "voiceover_text": "The secret to productivity lies in the 2-minute rule and smart task prioritization.",
                    "visual_description": "Core concept explanation",
                    "scene_type": "main_content"
                },
                {
                    "scene_number": 3,
                    "duration": 30,
                    "voiceover_text": "Apply these techniques and watch your productivity soar!",
                    "visual_description": "Motivational conclusion",
                    "scene_type": "call_to_action"
                }
            ]
            
            # Mock video metadata
            video_metadata = {
                "title": "Productivity Secrets Nobody Tells You",
                "main_topic": "productivity",
                "tone": "educational",
                "target_audience": "professionals",
                "content_style": "educational"
            }
            
            # Test full platform content generation
            result = await adapter.generate_platform_content(
                script_scenes=mock_scenes,
                video_composition=None,
                video_metadata=video_metadata,
                target_platforms=["youtube", "tiktok", "instagram", "twitter", "linkedin"],
                content_style="educational"
            )
            
            # Validate integration results
            assert isinstance(result, PlatformContentResult), "Should return PlatformContentResult"
            assert result.processing_time > 0, "Should have processing time"
            assert result.total_cost_estimate > 0, "Should have cost estimate"
            assert len(result.content_library_additions) > 0, "Should add to content library"
            
            # Check platform-specific content
            platforms_with_content = []
            if result.youtube_content:
                platforms_with_content.append("youtube")
                assert result.youtube_content.duration >= 300, "YouTube content too short"
            
            if result.tiktok_content:
                platforms_with_content.append("tiktok")
                assert result.tiktok_content.duration <= 60, "TikTok content too long"
            
            if result.instagram_content:
                platforms_with_content.append("instagram")
                assert result.instagram_content.duration <= 90, "Instagram content too long"
            
            if result.social_posts:
                platforms_with_content.extend(result.social_posts.keys())
            
            # Get content summary
            summary = adapter.get_platform_content_summary(result)
            
            assert len(summary["platforms_generated"]) >= 3, "Should generate content for multiple platforms"
            assert summary["total_thumbnails"] > 0, "Should generate thumbnails"
            
            self.test_results.append({
                "test": "Platform Integration",
                "status": "PASSED",
                "processing_time": result.processing_time,
                "estimated_cost": result.total_cost_estimate,
                "platforms_generated": summary["platforms_generated"],
                "content_library_additions": len(result.content_library_additions),
                "total_thumbnails": summary["total_thumbnails"]
            })
            
            print(f"✅ Platform Integration: {len(platforms_with_content)} platforms, ${result.total_cost_estimate:.2f} cost")
            
        except Exception as e:
            self.test_results.append({
                "test": "Platform Integration",
                "status": "FAILED",
                "error": str(e)
            })
            print(f"❌ Platform Integration: {e}")
    
    async def test_end_to_end_pipeline(self):
        """Test complete end-to-end pipeline from idea to platform content"""
        
        print("\n🎯 Testing End-to-End Pipeline")
        print("-" * 40)
        
        try:
            # Step 1: Generate script from idea
            script_generator = SimpleScriptGenerator()
            script = script_generator.generate_script(
                idea="AI-powered productivity tools for remote workers",
                target_audience="remote professionals",
                tone="educational",
                platform="youtube",
                duration_target=600  # 10 minutes
            )
            
            # Step 2: Create platform adapter
            adapter = PlatformAdapter(f"{self.output_dir}/e2e")
            
            # Step 3: Generate platform content
            result = await adapter.generate_platform_content(
                script_scenes=script["scenes"],
                video_composition=None,
                video_metadata={
                    "title": script["title"],
                    "main_topic": "AI productivity",
                    "tone": script["tone"],
                    "target_audience": script["target_audience"],
                    "duration": script["total_duration"]
                },
                target_platforms=["youtube", "tiktok", "instagram", "twitter"],
                content_style="educational"
            )
            
            # Step 4: Validate complete pipeline
            assert script["total_duration"] >= 300, "Original script should be at least 5 minutes"
            assert result.processing_time > 0, "Pipeline should have processing time"
            assert result.total_cost_estimate > 0, "Pipeline should have cost estimate"
            
            # Validate content variety
            content_types = []
            if result.youtube_content:
                content_types.append("youtube_longform")
            if result.tiktok_content:
                content_types.append("tiktok_shortform")
            if result.instagram_content:
                content_types.append("instagram_reels")
            if result.social_posts:
                content_types.extend(result.social_posts.keys())
            
            assert len(content_types) >= 3, "Should produce diverse content types"
            
            self.test_results.append({
                "test": "End-to-End Pipeline",
                "status": "PASSED",
                "original_script_duration": script["total_duration"],
                "final_processing_time": result.processing_time,
                "content_types": content_types,
                "platforms_generated": len(content_types),
                "total_cost": result.total_cost_estimate
            })
            
            print(f"✅ End-to-End Pipeline: {script['total_duration']}s → {len(content_types)} content types")
            
        except Exception as e:
            self.test_results.append({
                "test": "End-to-End Pipeline",
                "status": "FAILED",
                "error": str(e)
            })
            print(f"❌ End-to-End Pipeline: {e}")
    
    async def test_performance_benchmarks(self):
        """Test performance benchmarks for platform adapters"""
        
        print("\n⚡ Testing Performance Benchmarks")
        print("-" * 40)
        
        try:
            # Test with different content sizes
            test_sizes = [
                {"scenes": 3, "name": "Small"},
                {"scenes": 8, "name": "Medium"},
                {"scenes": 15, "name": "Large"}
            ]
            
            adapter = PlatformAdapter(f"{self.output_dir}/performance")
            performance_results = []
            
            for size in test_sizes:
                start_time = datetime.now()
                
                # Generate mock scenes
                mock_scenes = [
                    {
                        "scene_number": i + 1,
                        "duration": 30,
                        "voiceover_text": f"Content point {i+1} for testing performance.",
                        "visual_description": f"Visual for scene {i+1}",
                        "scene_type": "main_content" if i % 3 == 0 else "supporting"
                    }
                    for i in range(size["scenes"])
                ]
                
                # Test processing
                result = await adapter.generate_platform_content(
                    script_scenes=mock_scenes,
                    video_composition=None,
                    video_metadata={"title": "Performance Test", "main_topic": "testing"},
                    target_platforms=["youtube", "tiktok", "instagram"],
                    content_style="educational"
                )
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                performance_results.append({
                    "size": size["name"],
                    "scenes": size["scenes"],
                    "processing_time": processing_time,
                    "cost_estimate": result.total_cost_estimate,
                    "platforms": 3
                })
            
            # Validate performance
            for perf in performance_results:
                assert perf["processing_time"] < 30, f"Processing time {perf['processing_time']}s too slow"
                assert perf["cost_estimate"] < 5.0, f"Cost estimate ${perf['cost_estimate']} too high"
            
            self.test_results.append({
                "test": "Performance Benchmarks",
                "status": "PASSED",
                "performance_results": performance_results
            })
            
            print(f"✅ Performance Benchmarks: All sizes processed in <30s")
            
        except Exception as e:
            self.test_results.append({
                "test": "Performance Benchmarks",
                "status": "FAILED",
                "error": str(e)
            })
            print(f"❌ Performance Benchmarks: {e}")
    
    async def test_content_quality(self):
        """Test content quality metrics"""
        
        print("\n🎨 Testing Content Quality")
        print("-" * 40)
        
        try:
            # Test different content styles
            content_styles = ["educational", "entertaining", "motivational"]
            quality_results = []
            
            for style in content_styles:
                adapter = PlatformAdapter(f"{self.output_dir}/quality")
                
                # Generate test content
                mock_scenes = [
                    {
                        "scene_number": 1,
                        "duration": 30,
                        "voiceover_text": f"Welcome to this {style} content about amazing productivity techniques!",
                        "visual_description": f"Professional {style} introduction",
                        "scene_type": "intro"
                    },
                    {
                        "scene_number": 2,
                        "duration": 60,
                        "voiceover_text": f"Here are the key {style} insights that will transform your approach.",
                        "visual_description": f"Main {style} content demonstration",
                        "scene_type": "main_content"
                    }
                ]
                
                result = await adapter.generate_platform_content(
                    script_scenes=mock_scenes,
                    video_composition=None,
                    video_metadata={
                        "title": f"{style.title()} Productivity Guide",
                        "main_topic": "productivity",
                        "content_style": style
                    },
                    target_platforms=["youtube", "tiktok"],
                    content_style=style
                )
                
                # Quality checks
                quality_metrics = {
                    "style": style,
                    "youtube_optimization": result.youtube_content.optimization_score if result.youtube_content else 0,
                    "tiktok_engagement": len(result.tiktok_content.trending_tags) if result.tiktok_content else 0,
                    "content_consistency": self._check_content_consistency(mock_scenes, result),
                    "platform_adaptation": self._check_platform_adaptation(result)
                }
                
                quality_results.append(quality_metrics)
            
            # Validate quality
            for metrics in quality_results:
                assert metrics["youtube_optimization"] >= 6.0, f"YouTube optimization too low for {metrics['style']}"
                assert metrics["content_consistency"], f"Content consistency failed for {metrics['style']}"
            
            self.test_results.append({
                "test": "Content Quality",
                "status": "PASSED",
                "quality_results": quality_results
            })
            
            print(f"✅ Content Quality: All styles passed quality checks")
            
        except Exception as e:
            self.test_results.append({
                "test": "Content Quality",
                "status": "FAILED",
                "error": str(e)
            })
            print(f"❌ Content Quality: {e}")
    
    def _check_content_consistency(self, original_scenes: List[Dict], result: PlatformContentResult) -> bool:
        """Check if adapted content maintains consistency with original"""
        
        # Simple consistency check - in real implementation, would use NLP
        if result.youtube_content:
            youtube_scenes = result.youtube_content.scenes
            # Check that main content is preserved
            return len(youtube_scenes) >= len(original_scenes)
        return True
    
    def _check_platform_adaptation(self, result: PlatformContentResult) -> bool:
        """Check if content is properly adapted for each platform"""
        
        adaptations = []
        
        # Check YouTube adaptation
        if result.youtube_content:
            youtube_ok = (
                result.youtube_content.duration >= 300 and
                len(result.youtube_content.scenes) >= 3
            )
            adaptations.append(youtube_ok)
        
        # Check TikTok adaptation
        if result.tiktok_content:
            tiktok_ok = (
                15 <= result.tiktok_content.duration <= 60 and
                bool(result.tiktok_content.hook_text)
            )
            adaptations.append(tiktok_ok)
        
        return len(adaptations) > 0 and all(adaptations)
    
    async def generate_test_report(self):
        """Generate comprehensive test report"""
        
        print("\n📊 Generating Test Report")
        print("-" * 40)
        
        # Calculate summary statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test["status"] == "PASSED")
        failed_tests = total_tests - passed_tests
        
        report = {
            "test_suite": "Platform Adapter Test Suite",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "test_results": self.test_results,
            "recommendations": self._generate_recommendations()
        }
        
        # Save report
        report_path = f"{self.output_dir}/test_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Test Report: {passed_tests}/{total_tests} tests passed ({report['summary']['success_rate']:.1f}%)")
        print(f"📁 Report saved: {report_path}")
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        
        recommendations = []
        
        failed_tests = [test for test in self.test_results if test["status"] == "FAILED"]
        
        if failed_tests:
            recommendations.append("🔧 Fix failed tests before production deployment")
        
        slow_tests = [test for test in self.test_results if test.get("processing_time", 0) > 20]
        if slow_tests:
            recommendations.append("⚡ Optimize performance for slow-running tests")
        
        high_cost_tests = [test for test in self.test_results if test.get("estimated_cost", 0) > 3.0]
        if high_cost_tests:
            recommendations.append("💰 Review cost estimation for high-cost operations")
        
        return recommendations

# Main test execution
async def main():
    """Main test execution function"""
    
    print("🎬 Platform Adapter Test Suite")
    print("Testing Step 4: Platform-Specific Content Generators")
    print("=" * 60)
    
    test_suite = PlatformTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())