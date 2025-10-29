"""
Script Generator - Converts video ideas into structured scripts with scenes
"""

import json
import re
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class Scene:
    """Individual scene structure"""
    scene_number: int
    duration: int  # seconds
    voiceover_text: str
    visual_description: str
    scene_type: str  # intro, main_content, demo, testimonial, conclusion, call_to_action
    platform_adaptations: Dict[str, Dict[str, Any]]
    hooks: Dict[str, str]  # platform-specific hooks
    transition_effects: List[str]
    background_music: Optional[str] = None

@dataclass
class Script:
    """Complete script structure"""
    id: str
    title: str
    description: str
    target_audience: str
    tone: str
    total_duration: int
    word_count: int
    scenes: List[Scene]
    key_points: List[str]
    call_to_action: str
    hashtags: Dict[str, List[str]]
    created_at: str
    metadata: Dict[str, Any]

class ScriptGenerator:
    """AI-powered script generation from video ideas"""
    
    def __init__(self):
        self.platform_requirements = {
            "youtube": {
                "optimal_length": (420, 840),  # 7-14 minutes
                "engagement_techniques": ["hook", "preview", "chapter_markers", "visual_examples"],
                "structure": "problem_solution_demo_impact"
            },
            "tiktok": {
                "optimal_length": (15, 45),  # 15-45 seconds
                "engagement_techniques": ["immediate_hook", "quick_value", "trend_elements"],
                "structure": "hook_value_call_to_action"
            },
            "instagram": {
                "optimal_length": (30, 90),  # 30-90 seconds
                "engagement_techniques": ["visual_hook", "storytelling", "aesthetic"],
                "structure": "hook_story_value_benefit"
            }
        }
        
        self.scene_templates = {
            "intro": {
                "duration_range": (15, 30),
                "purpose": "Grab attention and introduce topic",
                "elements": ["hook", "problem_statement", "preview"]
            },
            "main_content": {
                "duration_range": (30, 60),
                "purpose": "Deliver core value and information",
                "elements": ["explanation", "examples", "demonstration"]
            },
            "demo": {
                "duration_range": (45, 90),
                "purpose": "Show practical application or tool usage",
                "elements": ["step_by_step", "screenshots", "real_examples"]
            },
            "testimonial": {
                "duration_range": (20, 45),
                "purpose": "Build trust and credibility",
                "elements": ["success_story", "specific_results", "authenticity"]
            },
            "conclusion": {
                "duration_range": (15, 30),
                "purpose": "Summarize key points and reinforce message",
                "elements": ["summary", "key_benefits", "reinforcement"]
            },
            "call_to_action": {
                "duration_range": (10, 20),
                "purpose": "Drive specific user action",
                "elements": ["clear_instruction", "urgency", "next_steps"]
            }
        }

    def generate_script(self, 
                       idea: str, 
                       target_audience: str = "general audience",
                       tone: str = "educational",
                       platform: str = "youtube",
                       duration_target: Optional[int] = None) -> Script:
        """
        Generate a structured script from a video idea
        
        Args:
            idea: The core video idea/concept
            target_audience: Target demographic
            tone: Communication tone (professional, casual, etc.)
            platform: Target platform (youtube, tiktok, instagram)
            duration_target: Desired duration in seconds
            
        Returns:
            Script object with structured content
        """
        
        # Determine optimal duration if not specified
        if not duration_target:
            duration_range = self.platform_requirements[platform]["optimal_length"]
            duration_target = sum(duration_range) // 2
        
        # Analyze idea and extract key components
        idea_analysis = self._analyze_idea(idea, target_audience)
        
        # Generate script structure
        structure = self._generate_structure(idea_analysis, platform, duration_target)
        
        # Create scenes based on structure
        scenes = self._create_scenes(structure, idea_analysis, platform)
        
        # Generate platform-specific adaptations
        scenes = self._add_platform_adaptations(scenes, platform)
        
        # Calculate metrics
        total_duration = sum(scene.duration for scene in scenes)
        word_count = sum(len(scene.voiceover_text.split()) for scene in scenes)
        
        # Create script object
        script = Script(
            id=str(uuid.uuid4()),
            title=self._generate_title(idea_analysis),
            description=self._generate_description(idea_analysis),
            target_audience=target_audience,
            tone=tone,
            total_duration=total_duration,
            word_count=word_count,
            scenes=scenes,
            key_points=idea_analysis["key_points"],
            call_to_action=self._generate_cta(idea_analysis, platform),
            hashtags=self._generate_hashtags(idea_analysis, platform),
            created_at=datetime.now().isoformat(),
            metadata={
                "platform": platform,
                "target_duration": duration_target,
                "actual_duration": total_duration,
                "structure_type": self.platform_requirements[platform]["structure"],
                "generation_version": "1.0"
            }
        )
        
        return script

    def _analyze_idea(self, idea: str, target_audience: str) -> Dict[str, Any]:
        """Analyze the video idea and extract key components"""
        
        # Extract key topics and concepts
        key_topics = self._extract_topics(idea)
        
        # Identify pain points and benefits
        pain_points = self._extract_pain_points(idea)
        benefits = self._extract_benefits(idea)
        
        # Determine content type
        content_type = self._determine_content_type(idea)
        
        # Extract actionable insights
        actionable_insights = self._extract_actionable_insights(idea)
        
        return {
            "original_idea": idea,
            "target_audience": target_audience,
            "key_topics": key_topics,
            "pain_points": pain_points,
            "benefits": benefits,
            "content_type": content_type,
            "actionable_insights": actionable_insights,
            "key_points": key_topics + benefits,
            "story_arc": self._create_story_arc(idea, pain_points, benefits)
        }

    def _generate_structure(self, analysis: Dict[str, Any], platform: str, duration: int) -> Dict[str, Any]:
        """Generate the overall script structure"""
        
        structure_type = self.platform_requirements[platform]["structure"]
        
        if structure_type == "problem_solution_demo_impact":
            return {
                "type": "problem_solution_demo_impact",
                "scenes": [
                    {"type": "intro", "weight": 0.15},
                    {"type": "main_content", "weight": 0.35},
                    {"type": "demo", "weight": 0.25},
                    {"type": "testimonial", "weight": 0.15},
                    {"type": "conclusion", "weight": 0.10}
                ]
            }
        elif structure_type == "hook_value_call_to_action":
            return {
                "type": "hook_value_call_to_action",
                "scenes": [
                    {"type": "intro", "weight": 0.30},
                    {"type": "main_content", "weight": 0.50},
                    {"type": "call_to_action", "weight": 0.20}
                ]
            }
        elif structure_type == "hook_story_value_benefit":
            return {
                "type": "hook_story_value_benefit",
                "scenes": [
                    {"type": "intro", "weight": 0.25},
                    {"type": "main_content", "weight": 0.40},
                    {"type": "demo", "weight": 0.20},
                    {"type": "conclusion", "weight": 0.15}
                ]
            }

    def _create_scenes(self, structure: Dict[str, Any], analysis: Dict[str, Any], platform: str) -> List[Scene]:
        """Create individual scenes based on structure"""
        
        scenes = []
        scene_number = 1
        
        for scene_config in structure["scenes"]:
            scene_type = scene_config["type"]
            weight = scene_config["weight"]
            
            # Calculate duration for this scene
            scene_duration = self._calculate_scene_duration(
                scene_type, weight, analysis, platform
            )
            
            # Generate scene content
            scene_content = self._generate_scene_content(
                scene_type, scene_duration, analysis, platform
            )
            
            # Create scene object
            scene = Scene(
                scene_number=scene_number,
                duration=scene_duration,
                voiceover_text=scene_content["voiceover"],
                visual_description=scene_content["visual"],
                scene_type=scene_type,
                platform_adaptations={},
                hooks={},
                transition_effects=scene_content.get("transitions", []),
                background_music=scene_content.get("music")
            )
            
            scenes.append(scene)
            scene_number += 1
        
        return scenes

    def _calculate_scene_duration(self, scene_type: str, weight: float, analysis: Dict[str, Any], platform: str) -> int:
        """Calculate appropriate duration for a scene"""
        
        template = self.scene_templates[scene_type]
        min_duration, max_duration = template["duration_range"]
        
        # Calculate base duration
        target_duration = weight * 600  # Assume 10-minute base for calculation
        
        # Apply platform-specific adjustments
        platform_range = self.platform_requirements[platform]["optimal_length"]
        platform_adjustment = (sum(platform_range) / 2) / 600  # Normalize to base
        
        adjusted_duration = int(target_duration * platform_adjustment)
        
        # Ensure within template bounds
        return max(min_duration, min(adjusted_duration, max_duration))

    def _generate_scene_content(self, scene_type: str, duration: int, analysis: Dict[str, Any], platform: str) -> Dict[str, str]:
        """Generate content for a specific scene"""
        
        content_templates = {
            "intro": self._generate_intro_content,
            "main_content": self._generate_main_content,
            "demo": self._generate_demo_content,
            "testimonial": self._generate_testimonial_content,
            "conclusion": self._generate_conclusion_content,
            "call_to_action": self._generate_cta_content
        }
        
        generator = content_templates.get(scene_type, self._generate_main_content)
        return generator(duration, analysis, platform)

    def _generate_intro_content(self, duration: int, analysis: Dict[str, Any], platform: str) -> Dict[str, str]:
        """Generate intro scene content"""
        
        # Create compelling hook
        hook = self._create_hook(analysis, platform)
        
        # Build voiceover text
        voiceover = f"""{hook}

In the next {duration//15} minutes, I'll show you {analysis.get('benefits', [''])[0] if analysis.get('benefits') else 'how to solve this problem'}."""

        # Visual description
        visual = f"""Dynamic opening with bold text overlay: '{analysis.get('key_topics', ['Main Topic'])[0] if analysis.get('key_topics') else 'Main Topic'}'.
Animation: Quick cuts of problem scenarios transitioning to solution preview.
Background: Vibrant gradient with modern typography."""

        return {
            "voiceover": voiceover,
            "visual": visual,
            "transitions": ["zoom_in", "fade_in", "slide_in"],
            "music": "upbeat_intro_001"
        }

    def _generate_main_content(self, duration: int, analysis: Dict[str, Any], platform: str) -> Dict[str, str]:
        """Generate main content scene"""
        
        # Distribute key points across the duration
        points_per_minute = len(analysis["key_points"]) / (duration / 60)
        
        voiceover_parts = []
        for i, point in enumerate(analysis["key_points"][:3]):  # Limit to 3 main points
            time_allocation = duration // min(3, len(analysis["key_points"]))
            
            voiceover_parts.append(f"""Point {i+1}: {point}

Let me explain this step by step.""")
        
        voiceover = " ".join(voiceover_parts)
        
        visual = f"""Screen recording style with point-by-point breakdowns.
Elements: Text overlays, bullet points, illustrations.
Flow: Sequential reveal of each key point with visual examples.
Style: Clean, professional with brand colors."""

        return {
            "voiceover": voiceover,
            "visual": visual,
            "transitions": ["fade", "slide"],
            "music": "neutral_background_001"
        }

    def _generate_demo_content(self, duration: int, analysis: Dict[str, Any], platform: str) -> Dict[str, str]:
        """Generate demonstration scene"""
        
        voiceover = f"""Now let me show you exactly how this works in practice.

I'll walk you through each step so you can implement this immediately.

First, we'll start with the basics and then build up to more advanced techniques."""

        visual = f"""Step-by-step screen recording or live demonstration.
Elements: Cursor movements, highlight boxes, step numbers.
Style: Clear, instructional with pause points for absorption.
Props: Real tools, interfaces, or examples being demonstrated."""

        return {
            "voiceover": voiceover,
            "visual": visual,
            "transitions": ["cut", "zoom"],
            "music": "focused_ambient_001"
        }

    def _generate_testimonial_content(self, duration: int, analysis: Dict[str, Any], platform: str) -> Dict[str, str]:
        """Generate testimonial/case study scene"""
        
        voiceover = f"""Here's what happened when Sarah implemented this strategy.

She went from struggling with {analysis['pain_points'][0] if analysis['pain_points'] else 'the same challenges'} to achieving remarkable results.

Within just 30 days, she saw a 40% improvement in her daily productivity."""

        visual = f"""Split screen showing before/after results.
Elements: Metrics, graphs, user photo with quote overlay.
Style: Trustworthy, professional with social proof elements.
Colors: Green for positive results, blue for stability."""

        return {
            "voiceover": voiceover,
            "visual": visual,
            "transitions": ["fade", "split"],
            "music": "inspiring_testimonial_001"
        }

    def _generate_conclusion_content(self, duration: int, analysis: Dict[str, Any], platform: str) -> Dict[str, str]:
        """Generate conclusion scene"""
        
        voiceover = f"""To recap what we've covered today:

First, {analysis['key_points'][0] if analysis['key_points'] else 'The main solution'}.
Second, {analysis['benefits'][0] if analysis['benefits'] else 'The key benefits'}.
And finally, how you can implement this starting today.

Remember, the best strategy is the one you actually execute."""

        visual = f"""Summary slide with key points highlighted.
Elements: Numbered list, checkmarks, call-to-action button.
Style: Clean, memorable with final branding.
Animation: Points appearing one by one."""

        return {
            "voiceover": voiceover,
            "visual": visual,
            "transitions": ["fade", "zoom_out"],
            "music": "conclusive_resolution_001"
        }

    def _generate_cta_content(self, duration: int, analysis: Dict[str, Any], platform: str) -> Dict[str, str]:
        """Generate call-to-action scene"""
        
        voiceover = f"""Ready to get started? 

Click the link in the description to access the complete guide.

And if this video helped you, please give it a thumbs up and subscribe for more content like this.

I'd love to hear about your results in the comments below."""

        visual = f"""Call-to-action screen with button highlights.
Elements: Subscribe button, description link, like button.
Style: Eye-catching with clear next steps.
Animation: Button pulses, arrow indicators."""

        return {
            "voiceover": voiceover,
            "visual": visual,
            "transitions": ["pop", "highlight"],
            "music": "energetic_ending_001"
        }

    def _create_hook(self, analysis: Dict[str, Any], platform: str) -> str:
        """Create platform-specific hooks"""
        
        hooks = {
            "youtube": f"""Did you know that {analysis['benefits'][0] if analysis['benefits'] else 'most people struggle with this problem'}?""",
            
            "tiktok": f"""POV: You just discovered {analysis['benefits'][0] if analysis['benefits'] else 'the secret to solving this problem'}""",
            
            "instagram": f"""This {analysis['content_type']} will change how you think about {analysis['key_topics'][0] if analysis['key_topics'] else 'this topic'}"""
        }
        
        return hooks.get(platform, hooks["youtube"])

    def _extract_topics(self, idea: str) -> List[str]:
        """Extract key topics from the idea"""
        # Simple keyword extraction - in production, this would use NLP
        topics = []
        keywords = ["ai", "productivity", "automation", "tools", "tips", "guide", "tutorial", "strategy"]
        
        for keyword in keywords:
            if keyword.lower() in idea.lower():
                topics.append(keyword)
        
        return topics if topics else ["main topic"]

    def _extract_pain_points(self, idea: str) -> List[str]:
        """Extract pain points from the idea"""
        # Placeholder implementation
        pain_indicators = ["problem", "struggle", "difficult", "challenge", "waste", "frustrating"]
        
        for indicator in pain_indicators:
            if indicator in idea.lower():
                return ["time waste", "efficiency problems", "manual processes"]
        
        return ["common challenges"]

    def _extract_benefits(self, idea: str) -> List[str]:
        """Extract benefits from the idea"""
        # Placeholder implementation
        benefit_indicators = ["improve", "better", "faster", "easier", "save", "optimize"]
        
        for indicator in benefit_indicators:
            if indicator in idea.lower():
                return ["increased productivity", "time savings", "better results"]
        
        return ["key improvements"]

    def _determine_content_type(self, idea: str) -> str:
        """Determine the content type based on the idea"""
        if "tutorial" in idea.lower() or "how to" in idea.lower():
            return "tutorial"
        elif "review" in idea.lower() or "comparison" in idea.lower():
            return "review"
        elif "story" in idea.lower() or "case study" in idea.lower():
            return "story"
        else:
            return "explainer"

    def _extract_actionable_insights(self, idea: str) -> List[str]:
        """Extract actionable insights"""
        return ["step 1: understand the problem", "step 2: apply the solution", "step 3: measure results"]

    def _create_story_arc(self, idea: str, pain_points: List[str], benefits: List[str]) -> Dict[str, str]:
        """Create story arc for the content"""
        return {
            "setup": f"Introduce the problem: {pain_points[0] if pain_points else 'the challenge'}",
            "conflict": "Explain why traditional approaches don't work",
            "resolution": f"Present the solution and benefits: {benefits[0] if benefits else 'the improvement'}",
            "climax": "Demonstrate the results",
            "conclusion": "Provide next steps and call to action"
        }

    def _add_platform_adaptations(self, scenes: List[Scene], platform: str) -> List[Scene]:
        """Add platform-specific adaptations to scenes"""
        
        for scene in scenes:
            if platform == "tiktok":
                # Add trending elements and quick hooks
                scene.platform_adaptations["tiktok"] = {
                    "trending_sounds": True,
                    "quick_cuts": True,
                    "text_overlays": True,
                    "hashtag_focus": True
                }
                scene.hooks["tiktok"] = self._create_trending_hook(scene, "tiktok")
                
            elif platform == "instagram":
                # Add aesthetic and story elements
                scene.platform_adaptations["instagram"] = {
                    "story_friendly": True,
                    "aesthetic_focus": True,
                    "carousel_ready": True
                }
                scene.hooks["instagram"] = self._create_aesthetic_hook(scene, "instagram")
                
            elif platform == "youtube":
                # Add chapter markers and engagement elements
                scene.platform_adaptations["youtube"] = {
                    "chapter_marker": True,
                    "cards_enabled": True,
                    "end_screen": True
                }
                scene.hooks["youtube"] = self._create_detailed_hook(scene, "youtube")
        
        return scenes

    def _create_trending_hook(self, scene: Scene, platform: str) -> str:
        """Create TikTok-style trending hook"""
        return "This hack will blow your mind 🤯 #productivity #ai #fyp"

    def _create_aesthetic_hook(self, scene: Scene, platform: str) -> str:
        """Create Instagram-style aesthetic hook"""
        return "Clean, minimal design meets powerful functionality ✨"

    def _create_detailed_hook(self, scene: Scene, platform: str) -> str:
        """Create YouTube-style detailed hook"""
        return f"In this comprehensive guide, we'll explore {scene.voiceover_text[:100]}..."

    def _generate_title(self, analysis: Dict[str, Any]) -> str:
        """Generate engaging title based on analysis"""
        topic = analysis["key_topics"][0] if analysis["key_topics"] else "Topic"
        benefit = analysis["benefits"][0] if analysis["benefits"] else "Benefits"
        
        return f"How to {benefit.replace(' ', ' ').title()} with {topic.title()}"

    def _generate_description(self, analysis: Dict[str, Any]) -> str:
        """Generate video description"""
        return f"""In this {analysis['content_type']}, you'll learn {', '.join(analysis['key_points'][:3])}.

🎯 What you'll get:
{chr(10).join([f"• {point}" for point in analysis['benefits']])}

⏰ Timestamps:
00:00 Introduction
01:30 Main Content
03:00 Demo
04:30 Results
05:30 Conclusion

💡 Key takeaways:
{chr(10).join([f"• {point}" for point in analysis['key_points']])}

🔗 Resources mentioned in the video"""

    def _generate_cta(self, analysis: Dict[str, Any], platform: str) -> str:
        """Generate platform-specific call to action"""
        ctas = {
            "youtube": "Subscribe for more productivity tips and hit the bell for notifications!",
            "tiktok": "Follow for daily productivity hacks! 💪",
            "instagram": "Save this post and share with someone who needs to see it! ✨"
        }
        return ctas.get(platform, ctas["youtube"])

    def _generate_hashtags(self, analysis: Dict[str, Any], platform: str) -> Dict[str, List[str]]:
        """Generate platform-specific hashtags"""
        
        base_tags = analysis["key_topics"] + ["productivity", "tips", "guide"]
        
        hashtags = {
            "youtube": base_tags[:5] + ["#ProductivityTips", "#HowTo", "#Tutorial"],
            "tiktok": base_tags[:3] + ["#fyp", "#productivity", "#ai"],
            "instagram": base_tags[:10] + ["#productivity", "#lifestyle", "#inspiration"]
        }
        
        return hashtags.get(platform, hashtags["youtube"])

    def export_script(self, script: Script, format: str = "json") -> str:
        """Export script to specified format"""
        
        if format == "json":
            return json.dumps(asdict(script), indent=2)
        elif format == "yaml":
            # Would implement YAML export
            return "# YAML export not implemented yet"
        else:
            raise ValueError(f"Unsupported export format: {format}")

# Example usage and testing
if __name__ == "__main__":
    generator = ScriptGenerator()
    
    # Test with sample idea
    test_idea = "How to improve productivity using AI automation tools for busy professionals"
    
    script = generator.generate_script(
        idea=test_idea,
        target_audience="busy professionals",
        tone="educational",
        platform="youtube"
    )
    
    print("Generated Script:")
    print(f"Title: {script.title}")
    print(f"Duration: {script.total_duration} seconds")
    print(f"Scenes: {len(script.scenes)}")
    
    for scene in script.scenes:
        print(f"\nScene {scene.scene_number}: {scene.scene_type}")
        print(f"Duration: {scene.duration}s")
        print(f"Voiceover: {scene.voiceover_text[:100]}...")