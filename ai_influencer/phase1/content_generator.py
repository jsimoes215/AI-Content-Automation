"""
AI Influencer Content Generator - Phase 1 Integration
Integrates the influencer personas with existing content generation pipeline

Author: MiniMax Agent  
Date: 2025-11-07
"""

import json
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime
import random
from dataclasses import dataclass

@dataclass
class ContentRequest:
    """Request for content generation with influencer persona"""
    topic: str
    niche: str
    influencer_id: int
    content_type: str = "video"  # video, post, article
    platform: str = "youtube"   # youtube, tiktok, instagram, linkedin, twitter
    tone: str = "professional"
    length: str = "medium"      # short, medium, long
    include_hashtags: bool = True

@dataclass
class GeneratedContent:
    """Generated content with influencer persona applied"""
    id: str
    influencer_id: int
    influencer_name: str
    content: str
    hashtags: List[str]
    title: str
    description: str
    platform_optimized: Dict[str, Any]
    generated_at: datetime
    cost_estimate: float
    persona_consistency_score: float

class InfluencerContentGenerator:
    """
    Core content generation engine that applies influencer personas
    to the existing content generation pipeline
    """
    
    def __init__(self, db_path: str = "/workspace/ai_influencer_poc/database/influencers.db"):
        self.db_path = db_path
        self.base_content_cost = 2.40  # Your existing pipeline cost per video
        
        # Content templates by platform and type
        self.content_templates = {
            "youtube": {
                "video": {
                    "short": {
                        "title_template": "{influencer_intro} {topic} - Quick {niche} Tips",
                        "description_template": "{influencer_greeting}! {body}\n\n💡 {key_points}\n\n🔥 Subscribe for more {niche} content!\n\n#Topics: {hashtags}\n\n{influencer_signoff}",
                        "body_template": "Today I'm sharing my {length} {topic} advice. {main_points}"
                    },
                    "medium": {
                        "title_template": "{influencer_intro} Complete Guide: {topic} | {niche} Mastery",
                        "description_template": "{influencer_greeting}! {body}\n\n📋 TIMESTAMPS:\n00:00 Introduction\n{timestamp_sections}\n\n💡 KEY TAKEAWAYS:\n{key_points}\n\n🎯 RESOURCES MENTIONED:\n{resources}\n\n📱 Follow for more {niche} content!\n#Topics: {hashtags}",
                        "body_template": "This is my complete {topic} guide. {main_points}\n\n{additional_details}"
                    }
                }
            },
            "tiktok": {
                "short": {
                    "title_template": "{influencer_intro} {topic} 🔥",
                    "description_template": "POV: You need {topic} advice\n\n{body}\n\n{niche} tips | #fyp #trending #lifestyle #school #tips #advice #life #motivational #inspiration #viral #reels #memes #funny #ai #technology #future #motivation #success #fitness #health #mental #mindset #productivity #work #money #finance #investing #real #raw #honest #authentic #vulnerable #truth",
                    "body_template": "{main_points}\n\n{key_tip}\n\n{influencer_closing}"
                }
            },
            "instagram": {
                "post": {
                    "title_template": "{influencer_intro} {topic} ✨",
                    "description_template": "{body}\n\n{key_points}\n\n#Topics: {hashtags}\n\n{influencer_engagement}",
                    "body_template": "Let's talk {topic} 🗣️\n\n{main_points}\n\n{closing_statement}"
                }
            },
            "linkedin": {
                "post": {
                    "title_template": "{influencer_intro} {topic}",
                    "description_template": "{body}\n\n{key_points}\n\n#Topics: {hashtags}\n\n{professional_closing}",
                    "body_template": "{main_points}\n\n{professional_insights}\n\n{actionable_advice}"
                }
            }
        }
    
    def get_db_connection(self):
        """Get database connection for influencer data"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_influencer_by_id(self, influencer_id: int) -> Optional[Dict[str, Any]]:
        """Get influencer data with persona information"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM influencers WHERE id = ? AND is_active = 1", (influencer_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            influencer = dict(row)
            
            # Parse JSON fields
            influencer['personality_traits'] = json.loads(influencer['personality_traits'] or '[]')
            influencer['target_audience'] = json.loads(influencer['target_audience'] or '{}')
            influencer['branding_guidelines'] = json.loads(influencer['branding_guidelines'] or '{}')
            
            return influencer
    
    def get_niche_content_guidelines(self, niche: str) -> Dict[str, Any]:
        """Get content guidelines for specific niche"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM niches WHERE name = ?", (niche,))
            row = cursor.fetchone()
            
            if not row:
                return {
                    "tone": "professional",
                    "content_style": {},
                    "target_keywords": [],
                    "content_templates": {}
                }
            
            niche_data = dict(row)
            niche_data['content_templates'] = json.loads(niche_data['content_templates'] or '{}')
            niche_data['tone_guidelines'] = json.loads(niche_data['tone_guidelines'] or '{}')
            niche_data['performance_benchmarks'] = json.loads(niche_data['performance_benchmarks'] or '{}')
            
            return niche_data
    
    def apply_influencer_persona(self, content: str, influencer: Dict[str, Any], platform: str) -> str:
        """Apply influencer personality to content"""
        personality = influencer.get('personality_traits', [])
        voice_type = influencer.get('voice_type', 'professional')
        
        # Voice type transformations
        voice_transformations = {
            "professional_male": {
                "opening": ["In my professional experience", "From my industry knowledge", "Based on my expertise"],
                "tone": "authoritative",
                "language": "formal"
            },
            "friendly_female": {
                "opening": ["Hey everyone!", "Hi friends!", "Let's chat about"],
                "tone": "conversational",
                "language": "informal"
            },
            "casual_young": {
                "opening": ["Okay so", "Real talk", "Let's be honest"],
                "tone": "casual",
                "language": "slang-friendly"
            }
        }
        
        voice_config = voice_transformations.get(voice_type, voice_transformations["professional_male"])
        
        # Apply personality traits
        if "knowledgeable" in personality:
            content = content.replace("This is", "Here's what I know about")
        
        if "energetic" in personality:
            content = content.replace("You can", "You absolutely can!")
            
        if "trustworthy" in personality:
            content = content.replace("I think", "Based on my experience, I believe")
            
        if "data-driven" in personality:
            content = content.replace("Generally", "Based on the data, generally")
        
        # Platform-specific voice adaptations
        if platform == "tiktok":
            content = content.replace("I recommend", "Trust me on this")
        elif platform == "linkedin":
            content = content.replace("I think", "In my professional opinion")
        
        return content
    
    def generate_content(self, request: ContentRequest) -> GeneratedContent:
        """Generate content with influencer persona applied"""
        
        # Get influencer data
        influencer = self.get_influencer_by_id(request.influencer_id)
        if not influencer:
            raise ValueError(f"Influencer {request.influencer_id} not found or inactive")
        
        # Get niche guidelines
        niche_guidelines = self.get_niche_content_guidelines(request.niche)
        
        # Generate base content (simulating your existing $2.40 pipeline)
        base_content = self._generate_base_content(request.topic, request.niche, request.content_type)
        
        # Apply influencer persona
        persona_content = self.apply_influencer_persona(base_content, influencer, request.platform)
        
        # Generate platform-specific elements
        title = self._generate_title(request, influencer, niche_guidelines)
        hashtags = self._generate_hashtags(request, influencer, niche_guidelines)
        description = self._generate_description(request, influencer, niche_guidelines, persona_content)
        
        # Calculate cost estimate (maintaining $2.40 base + influencer persona cost)
        cost_estimate = self.base_content_cost + (len(influencer.get('personality_traits', [])) * 0.10)
        
        # Calculate persona consistency score
        consistency_score = self._calculate_persona_consistency(persona_content, influencer, request.platform)
        
        # Create generated content
        content_id = f"{request.influencer_id}_{request.platform}_{int(datetime.now().timestamp())}"
        
        generated_content = GeneratedContent(
            id=content_id,
            influencer_id=request.influencer_id,
            influencer_name=influencer['name'],
            content=persona_content,
            hashtags=hashtags,
            title=title,
            description=description,
            platform_optimized=self._optimize_for_platform(persona_content, request.platform, request.length),
            generated_at=datetime.now(),
            cost_estimate=cost_estimate,
            persona_consistency_score=consistency_score
        )
        
        return generated_content
    
    def _generate_base_content(self, topic: str, niche: str, content_type: str) -> str:
        """Generate base content (simulating existing $2.40 pipeline)"""
        # This represents your existing content generation logic
        content_map = {
            ("finance", "saving money"): "Start by creating a detailed budget and tracking every expense. Set up automatic transfers to your savings account each month.",
            ("tech", "productivity"): "Use the Pomodoro technique with these productivity apps: Notion for planning, Grammarly for writing, and Focus Keeper for time management.",
            ("fitness", "workout routine"): "Begin with bodyweight exercises: push-ups, squats, and planks. Start with 3 sets of 10 reps and gradually increase intensity.",
            ("career", "networking"): "Attend industry events, join professional groups, and always follow up with a personalized message within 24 hours."
        }
        
        return content_map.get((topic.lower(), niche.lower()), 
                              f"Here are my top strategies for {topic} in the {niche} space.")
    
    def _generate_title(self, request: ContentRequest, influencer: Dict[str, Any], niche_guidelines: Dict) -> str:
        """Generate optimized title based on platform and influencer persona"""
        templates = self.content_templates.get(request.platform, {}).get(request.content_type, {}).get(request.length, {})
        template = templates.get('title_template', "{influencer_intro} {topic}")
        
        # Apply template
        persona_traits = influencer.get('personality_traits', [])
        intro_phrase = "Let's talk" if "friendly" in persona_traits else "Dive into" if "energetic" in persona_traits else "Explore"
        
        title = template.format(
            influencer_intro=intro_phrase,
            topic=request.topic,
            niche=request.niche
        )
        
        return title
    
    def _generate_hashtags(self, request: ContentRequest, influencer: Dict[str, Any], niche_guidelines: Dict) -> List[str]:
        """Generate platform-specific hashtags"""
        base_hashtags = {
            "youtube": ["#lifehacks", "#motivational", "#education", "#tips", "#advice"],
            "tiktok": ["#fyp", "#trending", "#lifestyle", "#tips", "#viral", "#ai", "#technology"],
            "instagram": ["#inspiration", "#motivation", "#lifestyle", "#goals", "#mindset"],
            "linkedin": ["#professional", "#career", "#business", "#leadership", "#success"],
            "twitter": ["#tips", "#life", "#advice", "#productivity", "#motivation"]
        }
        
        niche_hashtags = {
            "finance": ["#money", "#saving", "#investing", "#budget", "#wealth"],
            "tech": ["#innovation", "#startup", "#technology", "#productivity", "#future"],
            "fitness": ["#health", "#workout", "#fitness", "#lifestyle", "#wellness"],
            "career": ["#networking", "#career", "#professional", "#business", "#growth"]
        }
        
        platform_tags = base_hashtags.get(request.platform, [])
        niche_tags = niche_hashtags.get(request.niche.lower(), [])
        
        # Combine and limit based on platform
        max_tags = {"youtube": 5, "tiktok": 20, "instagram": 10, "linkedin": 8, "twitter": 3}
        limit = max_tags.get(request.platform, 10)
        
        hashtags = platform_tags[:3] + niche_tags[:3] + (["#ai", "#content"] if "ai" in request.topic.lower() else [])
        return hashtags[:limit]
    
    def _generate_description(self, request: ContentRequest, influencer: Dict[str, Any], 
                             niche_guidelines: Dict, content: str) -> str:
        """Generate platform-optimized description"""
        templates = self.content_templates.get(request.platform, {}).get(request.content_type, {}).get(request.length, {})
        template = templates.get('description_template', "{body}\n\n{hashtags}")
        
        # Extract key points from content
        key_points = [f"• {point}" for point in content.split('.') if point.strip()][:3]
        
        # Platform-specific engagement
        engagement_texts = {
            "youtube": "🔥 Subscribe for more content like this!",
            "tiktok": "💬 Drop your thoughts below!",
            "instagram": "💙 Double tap if this helped!",
            "linkedin": "💼 Connect with me for more insights!",
            "twitter": "🔄 RT if this resonates!"
        }
        
        hashtags = self._generate_hashtags(request, influencer, niche_guidelines)
        description = template.format(
            influencer_greeting=f"Hi everyone, I'm {influencer['name']}!",
            body=content,
            key_points='\n'.join(key_points),
            hashtags=' '.join(hashtags),
            influencer_signoff=engagement_texts.get(request.platform, "Thanks for reading!"),
            influencer_engagement=engagement_texts.get(request.platform, "Thanks for reading!"),
            professional_closing="Follow me for more professional insights!",
            timestamp_sections="00:30 Main Tips\n01:00 Key Takeaways",
            resources="📚 Links in description below"
        )
        
        return description
    
    def _optimize_for_platform(self, content: str, platform: str, length: str) -> Dict[str, Any]:
        """Generate platform-specific optimizations"""
        optimizations = {
            "youtube": {
                "max_title_length": 60,
                "max_description_length": 5000,
                "optimal_length": "medium"
            },
            "tiktok": {
                "max_title_length": 100,
                "optimal_length": "short",
                "engagement_elements": ["trending_sounds", "visual_effects", "hashtags"]
            },
            "instagram": {
                "max_title_length": 30,
                "max_description_length": 2200,
                "optimal_format": "visual_text"
            },
            "linkedin": {
                "max_title_length": 70,
                "max_description_length": 1300,
                "optimal_format": "professional"
            }
        }
        
        return optimizations.get(platform, {
            "max_title_length": 50,
            "max_description_length": 2000
        })
    
    def _calculate_persona_consistency(self, content: str, influencer: Dict[str, Any], platform: str) -> float:
        """Calculate how well the content matches the influencer persona"""
        persona_traits = influencer.get('personality_traits', [])
        voice_type = influencer.get('voice_type', 'professional')
        
        # Scoring based on persona alignment
        score = 0.5  # Base score
        
        # Voice type alignment
        if voice_type == "professional_male" and any(word in content.lower() for word in ["professionally", "experience", "based on"]):
            score += 0.2
        elif voice_type == "friendly_female" and any(word in content.lower() for word in ["hey", "everyone", "let's", "you know"]):
            score += 0.2
        elif voice_type == "casual_young" and any(word in content.lower() for word in ["okay so", "real talk", "honestly"]):
            score += 0.2
        
        # Personality trait alignment
        if "knowledgeable" in persona_traits and any(word in content.lower() for word in ["know", "experience", "research", "data"]):
            score += 0.1
        if "energetic" in persona_traits and any(word in content.lower() for word in ["amazing", "fantastic", "awesome", "love"]):
            score += 0.1
        if "trustworthy" in persona_traits and any(word in content.lower() for word in ["honestly", "truth", "real", "authentic"]):
            score += 0.1
        
        return min(score, 1.0)
    
    def batch_generate_content(self, requests: List[ContentRequest]) -> List[GeneratedContent]:
        """Generate multiple pieces of content with different influencer personas"""
        results = []
        for request in requests:
            try:
                content = self.generate_content(request)
                results.append(content)
            except Exception as e:
                print(f"Error generating content for request {request}: {e}")
                continue
        return results