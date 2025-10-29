"""
Text Content Generator - Creates social media posts for X (Twitter) and LinkedIn
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Import configuration
from config.settings import SOCIAL_MEDIA_SETTINGS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SocialMediaPost:
    """Social media post with platform-specific optimization"""
    id: str
    platform: str  # 'twitter' or 'linkedin'
    content: str
    hashtags: List[str]
    engagement_elements: Dict[str, Any]
    character_count: int
    optimal_timing: Dict[str, Any]
    call_to_action: str
    media_mentions: List[str]
    created_at: str

@dataclass
class TextContentConfig:
    """Configuration for text content generation"""
    platforms: List[str]
    tone_mapping: Dict[str, str]  # video tone -> social tone
    engagement_strategies: Dict[str, List[str]]
    hashtag_limits: Dict[str, int]
    character_limits: Dict[str, int]

class TextContentGenerator:
    """Generate platform-optimized text content from video scripts"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.config = TextContentConfig(
            platforms=['twitter', 'linkedin'],
            tone_mapping={
                'educational': 'informative',
                'professional': 'thought_leadership',
                'casual': 'conversational',
                'motivational': 'inspirational',
                'entertaining': 'engaging'
            },
            engagement_strategies={
                'twitter': [
                    'ask_question', 'share_stat', 'create_thread', 
                    'use_trending_hashtags', 'mention_influencers'
                ],
                'linkedin': [
                    'share_insight', 'tell_story', 'provide_value',
                    'ask_for_opinion', 'start_discussion'
                ]
            },
            hashtag_limits={
                'twitter': 2,
                'linkedin': 3,
                'instagram': 10
            },
            character_limits={
                'twitter': 280,
                'linkedin': 3000
            }
        )
    
    async def generate_social_content(self,
                                    script_scenes: List[Dict[str, Any]],
                                    video_metadata: Dict[str, Any],
                                    platforms: List[str] = None) -> Dict[str, SocialMediaPost]:
        """
        Generate social media content for multiple platforms
        
        Args:
            script_scenes: Script scenes from video
            video_metadata: Video metadata (title, duration, key points)
            platforms: Target platforms (default: twitter, linkedin)
            
        Returns:
            Dict[str, SocialMediaPost]: Posts for each platform
        """
        
        if platforms is None:
            platforms = ['twitter', 'linkedin']
        
        logger.info(f"📝 Generating social content for: {', '.join(platforms)}")
        
        # Extract content themes
        themes = await self._extract_content_themes(script_scenes)
        
        # Generate posts for each platform
        posts = {}
        for platform in platforms:
            post = await self._generate_platform_post(
                platform=platform,
                themes=themes,
                script_scenes=script_scenes,
                video_metadata=video_metadata
            )
            posts[platform] = post
        
        logger.info(f"✅ Generated {len(posts)} social media posts")
        return posts
    
    async def _extract_content_themes(self, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract key themes and insights from script scenes"""
        
        themes = {
            'main_topic': '',
            'key_points': [],
            'emotional_tone': 'neutral',
            'target_audience': 'general',
            'call_to_action': '',
            'unique_insights': [],
            'statistics': [],
            'examples': []
        }
        
        # Aggregate text content
        all_text = ' '.join([
            scene.get('voiceover_text', '') + ' ' + scene.get('visual_description', '')
            for scene in scenes
        ]).lower()
        
        # Extract main topic (simplified)
        if 'productivity' in all_text:
            themes['main_topic'] = 'productivity'
        elif 'ai' in all_text:
            themes['main_topic'] = 'artificial intelligence'
        elif 'business' in all_text:
            themes['main_topic'] = 'business strategy'
        elif 'technology' in all_text:
            themes['main_topic'] = 'technology'
        else:
            themes['main_topic'] = 'general knowledge'
        
        # Extract key points
        for scene in scenes:
            voiceover = scene.get('voiceover_text', '')
            if len(voiceover) > 30:  # Meaningful content
                # Extract first sentence or main point
                sentences = voiceover.split('.')
                if sentences:
                    point = sentences[0].strip()
                    if len(point) > 10:
                        themes['key_points'].append(point)
        
        # Determine emotional tone
        if any(word in all_text for word in ['amazing', 'incredible', 'life-changing']):
            themes['emotional_tone'] = 'excited'
        elif any(word in all_text for word in ['important', 'crucial', 'essential']):
            themes['emotional_tone'] = 'serious'
        elif any(word in all_text for word in ['easy', 'simple', 'quick']):
            themes['emotional_tone'] = 'enthusiastic'
        
        # Extract call to action
        for scene in scenes:
            if scene.get('scene_type') == 'call_to_action':
                cta = scene.get('voiceover_text', '')
                if cta:
                    themes['call_to_action'] = cta[:100]  # Truncate
                    break
        
        return themes
    
    async def _generate_platform_post(self, 
                                     platform: str,
                                     themes: Dict[str, Any],
                                     script_scenes: List[Dict[str, Any]],
                                     video_metadata: Dict[str, Any]) -> SocialMediaPost:
        """Generate optimized post for specific platform"""
        
        if platform == 'twitter':
            return await self._generate_twitter_post(themes, script_scenes, video_metadata)
        elif platform == 'linkedin':
            return await self._generate_linkedin_post(themes, script_scenes, video_metadata)
        else:
            raise ValueError(f"Unsupported platform: {platform}")
    
    async def _generate_twitter_post(self,
                                   themes: Dict[str, Any],
                                   scenes: List[Dict[str, Any]],
                                   video_metadata: Dict[str, Any]) -> SocialMediaPost:
        """Generate Twitter-optimized post"""
        
        char_limit = self.config.character_limits['twitter']
        hashtag_limit = self.config.hashtag_limits['twitter']
        
        # Create engaging hook
        hooks = [
            f"🧵 Thread: {themes['main_topic'].title()} secrets nobody tells you",
            f"💡 Just discovered this {themes['main_topic']} hack and it's mind-blowing",
            f"🚀 {themes['main_topic'].title()} tip that changed everything for me",
            f"⚡ Quick {themes['main_topic']} insight that 99% of people miss",
            f"🔥 {themes['main_topic'].title()} breakdown in under 30 seconds"
        ]
        
        hook = hooks[0]  # Default to thread format
        
        # Create main content
        main_point = themes['key_points'][0] if themes['key_points'] else f"Amazing insights about {themes['main_topic']}"
        
        # Truncate main point for Twitter
        if len(main_point) > 150:
            main_point = main_point[:147] + "..."
        
        # Create call to action
        cta = "Watch the full breakdown 👇"
        
        # Generate hashtags
        hashtags = self._generate_twitter_hashtags(themes, hashtag_limit)
        
        # Combine content
        content_parts = [hook, "", main_point, "", cta]
        content = " ".join(content_parts)
        
        # Add hashtags
        hashtag_text = " ".join(hashtags)
        final_content = f"{content}\n\n{hashtag_text}"
        
        # Check character limit
        if len(final_content) > char_limit:
            # Reduce content to fit
            main_point = main_point[:100] + "..."
            content = f"{hook}\n\n{main_point}\n\n{cta}\n\n{hashtag_text}"
        
        return SocialMediaPost(
            id=str(uuid.uuid4()),
            platform='twitter',
            content=content,
            hashtags=hashtags,
            engagement_elements={
                'thread_starter': True,
                'question_engagement': f"What {themes['main_topic']} tip has worked best for you?",
                'retweet_prompt': "RT if this helped you!",
                'engagement_rate_optimization': True
            },
            character_count=len(content),
            optimal_timing={
                'best_times': ['9am', '12pm', '5pm', '9pm'],
                'timezone': 'UTC',
                'posting_frequency': '1-3 times per day'
            },
            call_to_action=cta,
            media_mentions=['video_link', 'thread_continuation'],
            created_at=datetime.now().isoformat()
        )
    
    def _generate_twitter_hashtags(self, themes: Dict[str, Any], limit: int) -> List[str]:
        """Generate Twitter hashtags"""
        
        # Base hashtags for engagement
        base_tags = ['#productivity', '#success', '#growth']
        
        # Topic-specific hashtags
        topic = themes['main_topic']
        if topic == 'productivity':
            topic_tags = ['#productivity', '#efficiency', '#workflow']
        elif topic == 'artificial intelligence':
            topic_tags = ['#AI', '#technology', '#future']
        elif topic == 'business strategy':
            topic_tags = ['#business', '#strategy', '#entrepreneurship']
        else:
            topic_tags = ['#tips', '#learning', '#knowledge']
        
        # Trending hashtags
        trending_tags = ['#LearnOnTwitter', '#DailyTips', '#Motivation']
        
        # Combine and limit
        all_tags = base_tags + topic_tags + trending_tags
        return all_tags[:limit]
    
    async def _generate_linkedin_post(self,
                                    themes: Dict[str, Any],
                                    scenes: List[Dict[str, Any]],
                                    video_metadata: Dict[str, Any]) -> SocialMediaPost:
        """Generate LinkedIn-optimized post"""
        
        char_limit = self.config.character_limits['linkedin']
        hashtag_limit = self.config.hashtag_limits['linkedin']
        
        # Professional hook
        hooks = [
            f"💼 Professional insight: The {themes['main_topic']} mistake everyone makes",
            f"📊 Data-driven perspective on {themes['main_topic']} in 2025",
            f"🎯 Strategic approach to {themes['main_topic']} that delivers results",
            f"💡 Industry insight: Transforming {themes['main_topic']} challenges into opportunities",
            f"🔍 Leadership lesson: What {themes['main_topic']} teaches us about growth"
        ]
        
        hook = hooks[0]
        
        # Create value-driven content
        key_insights = []
        
        # Add main insight
        if themes['key_points']:
            main_insight = themes['key_points'][0]
            key_insights.append(f"✨ Key insight: {main_insight}")
        
        # Add supporting points
        for point in themes['key_points'][1:3]:  # Max 2 additional points
            key_insights.append(f"→ {point}")
        
        # Add professional take
        professional_take = f"From a {themes['main_topic']} perspective, this approach offers significant value for professionals looking to optimize their workflow."
        
        # Create call to action
        cta_options = [
            "What's your experience with this approach? I'd love to hear your thoughts in the comments.",
            "How do you approach this in your organization? Share your insights below.",
            "Has this strategy worked for you? Let's discuss in the comments.",
            "What additional strategies have you found effective? Please share your experience."
        ]
        
        cta = cta_options[0]
        
        # Generate professional hashtags
        hashtags = self._generate_linkedin_hashtags(themes, hashtag_limit)
        
        # Combine content
        content_lines = [
            hook,
            "",
            professional_take,
            "",
            *key_insights,
            "",
            cta
        ]
        
        content = "\n".join(content_lines)
        
        # Add hashtags
        if hashtags:
            content += "\n\n" + " ".join(hashtags)
        
        return SocialMediaPost(
            id=str(uuid.uuid4()),
            platform='linkedin',
            content=content,
            hashtags=hashtags,
            engagement_elements={
                'professional_tone': True,
                'discussion_starter': True,
                'value_proposition': themes['main_topic'],
                'networking_opportunity': True,
                'thought_leadership': True
            },
            character_count=len(content),
            optimal_timing={
                'best_times': ['8am', '12pm', '5pm', '6pm'],
                'timezone': 'local_business_hours',
                'posting_frequency': '1-2 times per day'
            },
            call_to_action=cta,
            media_mentions=['video_attachment', 'link_preview'],
            created_at=datetime.now().isoformat()
        )
    
    def _generate_linkedin_hashtags(self, themes: Dict[str, Any], limit: int) -> List[str]:
        """Generate LinkedIn hashtags"""
        
        # Professional hashtags
        base_tags = ['#leadership', '#professionaldevelopment', '#business']
        
        # Topic-specific professional hashtags
        topic = themes['main_topic']
        if topic == 'productivity':
            topic_tags = ['#efficiency', '#workplaceperformance', '#timemanagement']
        elif topic == 'artificial intelligence':
            topic_tags = ['#AITransformation', '#digitalinnovation', '#futureofwork']
        elif topic == 'business strategy':
            topic_tags = ['#businessstrategy', '#corporategyrowth', '#strategicplanning']
        else:
            topic_tags = ['#continuouslearning', '#skilldevelopment', '#careergrowth']
        
        # Industry hashtags
        industry_tags = ['#professionalgrowth', '#careeradvancement', '#industryinsights']
        
        # Combine and limit
        all_tags = base_tags + topic_tags + industry_tags
        return all_tags[:limit]
    
    async def generate_thread_content(self, 
                                    themes: Dict[str, Any],
                                    scenes: List[Dict[str, Any]]) -> List[str]:
        """Generate Twitter thread content"""
        
        thread_posts = []
        
        # Thread overview
        overview = f"🧵 THREAD: {len(scenes)} insights about {themes['main_topic']} that will transform how you think about this topic 👇"
        thread_posts.append(overview)
        
        # Individual insights
        for i, scene in enumerate(scenes[:7], 1):  # Max 7 tweets
            insight = scene.get('voiceover_text', '')
            
            # Clean and format insight
            if len(insight) > 200:
                insight = insight[:197] + "..."
            
            # Add numbering and emoji
            emoji_options = ['⚡', '💡', '🎯', '🚀', '🔥', '✨', '💪']
            emoji = emoji_options[(i-1) % len(emoji_options)]
            
            tweet = f"{i}/{len(scenes)} {emoji} {insight}"
            
            # Add hashtag for context
            hashtag = f"#{themes['main_topic'].replace(' ', '')}"
            if len(tweet + f" {hashtag}") <= 280:
                tweet += f" {hashtag}"
            
            thread_posts.append(tweet)
        
        # Call to action
        cta = f"🎬 Which insight resonated most with you? Drop a number in the comments! #learnontiktok"
        thread_posts.append(cta)
        
        return thread_posts
    
    async def generate_linkedin_article_outline(self,
                                              themes: Dict[str, Any],
                                              scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate LinkedIn article outline for longer content"""
        
        article = {
            'title': f"The Complete Guide to {themes['main_topic'].title()}: A Data-Driven Approach",
            'subtitle': f"Professional insights and actionable strategies for {themes['main_topic']}",
            'sections': [],
            'key_takeaways': [],
            'call_to_action': "Connect with me to discuss these strategies and share your experience."
        }
        
        # Create sections
        for i, scene in enumerate(scenes):
            section_title = f"Section {i+1}: {self._extract_section_title(scene)}"
            section_content = scene.get('voiceover_text', '')[:300] + "..."
            
            article['sections'].append({
                'title': section_title,
                'content': section_content,
                'key_points': self._extract_key_points_from_scene(scene)
            })
        
        # Extract key takeaways
        for scene in scenes[:3]:
            takeaway = self._create_takeaway(scene)
            if takeaway:
                article['key_takeaways'].append(takeaway)
        
        return article
    
    def _extract_section_title(self, scene: Dict[str, Any]) -> str:
        """Extract section title from scene"""
        
        voiceover = scene.get('voiceover_text', '')
        scene_type = scene.get('scene_type', '')
        
        if 'intro' in scene_type.lower():
            return 'Introduction'
        elif 'main' in scene_type.lower():
            return 'Core Strategy'
        elif 'demo' in scene_type.lower():
            return 'Practical Application'
        elif 'conclusion' in scene_type.lower():
            return 'Key Takeaways'
        else:
            # Extract from content
            words = voiceover.split()[:6]
            return ' '.join(words)
    
    def _extract_key_points_from_scene(self, scene: Dict[str, Any]) -> List[str]:
        """Extract key points from scene for article"""
        
        voiceover = scene.get('voiceover_text', '')
        
        # Simple sentence extraction
        sentences = [s.strip() for s in voiceover.split('.') if len(s.strip()) > 20]
        return sentences[:3]  # Max 3 points
    
    def _create_takeaway(self, scene: Dict[str, Any]) -> str:
        """Create a key takeaway from scene"""
        
        voiceover = scene.get('voiceover_text', '')
        
        if len(voiceover) > 50:
            return f"• {voiceover[:80]}..."
        return ""

# Test function
async def test_text_generator():
    """Test the text content generator"""
    
    generator = TextContentGenerator("/tmp/social_test")
    
    # Mock script scenes
    mock_scenes = [
        {
            "scene_number": 1,
            "duration": 30,
            "voiceover_text": "Welcome to this productivity guide that will transform your workflow.",
            "visual_description": "Professional introduction with productivity tools",
            "scene_type": "intro"
        },
        {
            "scene_number": 2,
            "duration": 60,
            "voiceover_text": "The 2-minute rule is simple: if something takes less than 2 minutes, do it immediately.",
            "visual_description": "Demonstration of the 2-minute rule in action",
            "scene_type": "main_content"
        },
        {
            "scene_number": 3,
            "duration": 30,
            "voiceover_text": "Try this method and watch your productivity soar!",
            "visual_description": "Before and after productivity comparison",
            "scene_type": "call_to_action"
        }
    ]
    
    mock_metadata = {
        'title': 'Productivity Hack That Changed Everything',
        'duration': 120,
        'key_points': ['2-minute rule', 'Task prioritization', 'Time blocking']
    }
    
    # Test social content generation
    posts = await generator.generate_social_content(
        script_scenes=mock_scenes,
        video_metadata=mock_metadata,
        platforms=['twitter', 'linkedin']
    )
    
    print("📝 Generated Social Media Posts:")
    print("=" * 50)
    
    for platform, post in posts.items():
        print(f"\n🐦 {platform.upper()}:")
        print(f"📄 Content: {post.content[:100]}...")
        print(f"📊 Character count: {post.character_count}")
        print(f"🏷️ Hashtags: {post.hashtags}")
        print(f"🎯 Call to action: {post.call_to_action}")
    
    # Test thread generation
    print(f"\n🧵 TWITTER THREAD:")
    thread = await generator.generate_thread_content(
        themes={'main_topic': 'productivity'},
        scenes=mock_scenes
    )
    
    for i, tweet in enumerate(thread[:3], 1):
        print(f"{i}. {tweet}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_text_generator())