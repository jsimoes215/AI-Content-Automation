"""
Simplified Script Generator - Basic script generation without complex f-strings
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any

class SimpleScriptGenerator:
    """Simplified script generator for testing"""
    
    def __init__(self):
        self.platform_requirements = {
            "youtube": {"optimal_length": 600, "style": "comprehensive"},
            "tiktok": {"optimal_length": 60, "style": "quick"},
            "instagram": {"optimal_length": 90, "style": "visual"}
        }

    def generate_script(self, idea, target_audience="general", tone="educational", platform="youtube", duration_target=None):
        """Generate a simple script from an idea"""
        
        # Basic script structure
        scenes = self._create_scenes(idea, platform, duration_target, target_audience)
        
        # Create script object
        script = {
            "id": str(uuid.uuid4()),
            "title": f"Understanding {idea}",
            "description": f"Learn about {idea} for {target_audience}",
            "target_audience": target_audience,
            "tone": tone,
            "total_duration": sum(scene["duration"] for scene in scenes),
            "word_count": sum(len(scene["voiceover_text"].split()) for scene in scenes),
            "scenes": scenes,
            "key_points": [f"Key point about {idea}"],
            "call_to_action": "Subscribe for more content!",
            "hashtags": {"youtube": ["#education", "#tutorial"], "tiktok": ["#fyp", "#education"]},
            "created_at": datetime.now().isoformat(),
            "metadata": {
                "platform": platform,
                "target_duration": duration_target or 300,
                "generation_version": "1.0-simple"
            }
        }
        
        return script

    def _create_scenes(self, idea, platform, duration_target, target_audience):
        """Create simple scenes for the script"""
        
        if platform == "tiktok":
            # Short form: intro + main + CTA
            scenes = [
                {
                    "scene_number": 1,
                    "duration": 15,
                    "voiceover_text": f"Here's how {idea} can change your life!",
                    "visual_description": f"Dynamic intro showing {idea} benefits",
                    "scene_type": "intro",
                    "platform_adaptations": {},
                    "hooks": {"tiktok": f"POV: You just learned about {idea}"},
                    "transition_effects": ["zoom_in"]
                },
                {
                    "scene_number": 2,
                    "duration": 30,
                    "voiceover_text": f"Follow these 3 steps to master {idea}",
                    "visual_description": f"Step-by-step guide for {idea}",
                    "scene_type": "main_content",
                    "platform_adaptations": {},
                    "hooks": {},
                    "transition_effects": ["slide"]
                },
                {
                    "scene_number": 3,
                    "duration": 15,
                    "voiceover_text": "Try this and let me know how it works!",
                    "visual_description": "Call-to-action with subscribe button",
                    "scene_type": "call_to_action",
                    "platform_adaptations": {},
                    "hooks": {},
                    "transition_effects": ["fade"]
                }
            ]
        else:
            # Long form: intro + main + demo + conclusion + CTA
            scenes = [
                {
                    "scene_number": 1,
                    "duration": 30,
                    "voiceover_text": f"Welcome! Today we'll explore {idea} and how it can benefit you.",
                    "visual_description": f"Professional introduction to {idea}",
                    "scene_type": "intro",
                    "platform_adaptations": {},
                    "hooks": {"youtube": f"Discover the power of {idea}"},
                    "transition_effects": ["fade_in"]
                },
                {
                    "scene_number": 2,
                    "duration": 120,
                    "voiceover_text": f"Let's dive deep into {idea}. First, we'll cover the basics, then move to advanced concepts.",
                    "visual_description": f"Detailed explanation of {idea} concepts",
                    "scene_type": "main_content",
                    "platform_adaptations": {},
                    "hooks": {},
                    "transition_effects": ["slide"]
                },
                {
                    "scene_number": 3,
                    "duration": 90,
                    "voiceover_text": f"Now I'll show you a practical example of {idea} in action.",
                    "visual_description": f"Hands-on demonstration of {idea}",
                    "scene_type": "demo",
                    "platform_adaptations": {},
                    "hooks": {},
                    "transition_effects": ["cut"]
                },
                {
                    "scene_number": 4,
                    "duration": 60,
                    "voiceover_text": f"In conclusion, {idea} offers tremendous value for {target_audience}.",
                    "visual_description": f"Summary and key takeaways for {idea}",
                    "scene_type": "conclusion",
                    "platform_adaptations": {},
                    "hooks": {},
                    "transition_effects": ["fade"]
                },
                {
                    "scene_number": 5,
                    "duration": 30,
                    "voiceover_text": "If this helped you, please like and subscribe for more content like this!",
                    "visual_description": "Subscribe button and like animation",
                    "scene_type": "call_to_action",
                    "platform_adaptations": {},
                    "hooks": {},
                    "transition_effects": ["pop"]
                }
            ]
        
        return scenes

# Test function
def test_simple_generator():
    """Test the simple script generator"""
    generator = SimpleScriptGenerator()
    
    # Test different platforms
    test_cases = [
        {"idea": "AI productivity tools", "platform": "youtube"},
        {"idea": "Quick productivity hack", "platform": "tiktok"},
        {"idea": "Visual productivity guide", "platform": "instagram"}
    ]
    
    for test_case in test_cases:
        script = generator.generate_script(
            idea=test_case["idea"],
            platform=test_case["platform"]
        )
        
        print(f"\nScript for {test_case['platform']}:")
        print(f"Title: {script['title']}")
        print(f"Duration: {script['total_duration']}s")
        print(f"Scenes: {len(script['scenes'])}")
        print(f"Word count: {script['word_count']}")

if __name__ == "__main__":
    test_simple_generator()
