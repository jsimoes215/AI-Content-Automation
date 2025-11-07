"""
Advanced Persona Consistency Optimizer
Enhances the existing persona consistency with ML-based scoring

Author: MiniMax Agent
Date: 2025-11-07
"""

import sqlite3
import json
import re
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter
import math
from datetime import datetime

class AdvancedPersonaOptimizer:
    """Advanced persona consistency engine"""
    
    def __init__(self, db_path: str = "/workspace/ai_influencer_poc/database/influencers.db"):
        self.db_path = db_path
        self.voice_patterns = {
            "professional_male": {
                "opening_phrases": ["in my experience", "based on my expertise", "professionally speaking"],
                "language_markers": ["therefore", "consequently", "furthermore", "additionally"],
                "confidence_indicators": ["I recommend", "It is recommended", "Studies show"],
                "sentiment_range": (0.3, 0.8),  # Neutral to positive
                "complexity_score": 0.7  # Higher complexity
            },
            "friendly_female": {
                "opening_phrases": ["hey everyone", "hi friends", "let's talk about"],
                "language_markers": ["you know", "I think", "maybe", "what if"],
                "confidence_indicators": ["I believe", "I feel like", "imagine this"],
                "sentiment_range": (0.4, 0.9),  # More positive
                "complexity_score": 0.5  # Accessible language
            },
            "casual_young": {
                "opening_phrases": ["okay so", "real talk", "honestly", "let's be real"],
                "language_markers": ["like", "literally", "obviously", "basically"],
                "confidence_indicators": ["trust me", "trust me on this", "for real"],
                "sentiment_range": (0.5, 0.95),  # Very positive
                "complexity_score": 0.3  # Simple language
            }
        }
    
    def get_advanced_persona_score(self, content: str, influencer_id: int) -> Dict[str, float]:
        """Get detailed persona consistency analysis"""
        
        influencer = self.get_influencer(influencer_id)
        if not influencer:
            return {"overall_score": 0.0, "detailed_scores": {}}
        
        voice_type = influencer.get('voice_type', 'professional_male')
        personality_traits = influencer.get('personality_traits', [])
        
        # Get voice patterns
        patterns = self.voice_patterns.get(voice_type, self.voice_patterns["professional_male"])
        
        # Calculate component scores
        language_score = self._analyze_language_patterns(content, patterns)
        opening_score = self._analyze_opening_phrases(content, patterns)
        confidence_score = self._analyze_confidence_indicators(content, patterns)
        sentiment_score = self._analyze_sentiment_alignment(content, patterns)
        complexity_score = self._analyze_complexity_match(content, patterns)
        
        # Calculate overall weighted score
        weights = {
            "language": 0.25,
            "opening": 0.15,
            "confidence": 0.20,
            "sentiment": 0.20,
            "complexity": 0.20
        }
        
        detailed_scores = {
            "language_patterns": language_score,
            "opening_phrases": opening_score,
            "confidence_indicators": confidence_score,
            "sentiment_alignment": sentiment_score,
            "complexity_match": complexity_score
        }
        
        overall_score = sum(detailed_scores[key] * weights[key.split("_")[0]] for key in detailed_scores)
        
        return {
            "overall_score": min(overall_score, 1.0),
            "detailed_scores": detailed_scores,
            "voice_type": voice_type,
            "recommendations": self._generate_optimization_recommendations(detailed_scores, influencer)
        }
    
    def optimize_persona_application(self, content: str, influencer_id: int, platform: str) -> str:
        """Apply optimized persona transformations"""
        
        influencer = self.get_influencer(influencer_id)
        if not influencer:
            return content
        
        voice_type = influencer.get('voice_type', 'professional_male')
        personality_traits = influencer.get('personality_traits', [])
        
        # Advanced transformations based on personality depth
        content = self._apply_advanced_personality_transforms(content, personality_traits, platform)
        content = self._apply_voice_type_optimizations(content, voice_type, platform)
        content = self._apply_platform_specific_refinements(content, platform, voice_type)
        
        return content
    
    def _analyze_language_patterns(self, content: str, patterns: Dict) -> float:
        """Analyze language pattern alignment"""
        content_lower = content.lower()
        language_markers = patterns.get("language_markers", [])
        
        if not language_markers:
            return 0.5
        
        matches = sum(1 for marker in language_markers if marker in content_lower)
        return min(matches / len(language_markers) * 2, 1.0)
    
    def _analyze_opening_phrases(self, content: str, patterns: Dict) -> float:
        """Analyze opening phrase alignment"""
        sentences = content.split('.')[:3]  # First 3 sentences
        first_sentence = sentences[0].lower() if sentences else ""
        
        opening_phrases = patterns.get("opening_phrases", [])
        
        if not opening_phrases:
            return 0.5
        
        # Check for direct matches or similar patterns
        match_score = 0.0
        for phrase in opening_phrases:
            if phrase in first_sentence:
                match_score = 1.0
                break
            # Partial match scoring
            words = phrase.split()
            if len(words) >= 2:
                if all(word in first_sentence for word in words[:2]):
                    match_score = max(match_score, 0.7)
        
        return match_score
    
    def _analyze_confidence_indicators(self, content: str, patterns: Dict) -> float:
        """Analyze confidence indicator alignment"""
        content_lower = content.lower()
        confidence_indicators = patterns.get("confidence_indicators", [])
        
        if not confidence_indicators:
            return 0.5
        
        matches = sum(1 for indicator in confidence_indicators if indicator in content_lower)
        return min(matches * 0.3, 1.0)  # Cap at 1.0
    
    def _analyze_sentiment_alignment(self, content: str, patterns: Dict) -> float:
        """Analyze sentiment alignment with expected range"""
        # Simple sentiment analysis
        positive_words = ["good", "great", "amazing", "fantastic", "awesome", "love", "best", "wonderful"]
        negative_words = ["bad", "terrible", "awful", "hate", "worst", "horrible", "disappointing"]
        
        content_lower = content.lower()
        pos_count = sum(1 for word in positive_words if word in content_lower)
        neg_count = sum(1 for word in negative_words if word in content_lower)
        
        sentiment_score = (pos_count - neg_count) / max(len(content.split()), 1)
        sentiment_score = max(0, min(sentiment_score * 10 + 0.5, 1.0))  # Normalize to 0-1
        
        expected_range = patterns.get("sentiment_range", (0.3, 0.8))
        expected_sentiment = sum(expected_range) / 2
        
        # Score based on proximity to expected sentiment
        diff = abs(sentiment_score - expected_sentiment)
        return max(0, 1 - (diff * 2))
    
    def _analyze_complexity_match(self, content: str, patterns: Dict) -> float:
        """Analyze complexity alignment"""
        words = content.split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # Simple complexity metrics
        sentence_lengths = [len(sent.split()) for sent in content.split('.') if sent.strip()]
        avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
        
        expected_complexity = patterns.get("complexity_score", 0.5)
        
        # Calculate complexity score (0-1)
        word_complexity = min(avg_word_length / 10, 1.0)  # Normalize word length
        sentence_complexity = min(avg_sentence_length / 20, 1.0)  # Normalize sentence length
        
        actual_complexity = (word_complexity + sentence_complexity) / 2
        
        # Score based on proximity
        diff = abs(actual_complexity - expected_complexity)
        return max(0, 1 - (diff * 2))
    
    def _generate_optimization_recommendations(self, detailed_scores: Dict[str, float], influencer: Dict) -> List[str]:
        """Generate actionable optimization recommendations"""
        recommendations = []
        
        personality_traits = influencer.get('personality_traits', [])
        voice_type = influencer.get('voice_type', 'professional_male')
        
        # Low scoring components
        if detailed_scores.get("opening_phrases", 0) < 0.6:
            recommendations.append("Add more characteristic opening phrases typical of the voice type")
        
        if detailed_scores.get("language_patterns", 0) < 0.6:
            recommendations.append("Incorporate more language markers that match the voice type")
        
        if detailed_scores.get("confidence_indicators", 0) < 0.6:
            recommendations.append("Strengthen confidence indicators and authority markers")
        
        # Personality-specific recommendations
        if "knowledgeable" in personality_traits and detailed_scores.get("language_patterns", 0) < 0.7:
            recommendations.append("Add more technical terms and evidence-based language")
        
        if "energetic" in personality_traits and detailed_scores.get("sentiment_alignment", 0) < 0.7:
            recommendations.append("Increase enthusiasm and energetic language")
        
        if "trustworthy" in personality_traits and detailed_scores.get("confidence_indicators", 0) < 0.7:
            recommendations.append("Strengthen credibility markers and personal experience references")
        
        return recommendations
    
    def _apply_advanced_personality_transforms(self, content: str, personality_traits: List[str], platform: str) -> str:
        """Apply more sophisticated personality transformations"""
        
        # Enhanced transformations based on depth of personality
        transformations = {
            "knowledgeable": {
                "basic": ["This shows", "Research indicates"],
                "advanced": ["Evidence suggests", "Studies demonstrate", "Data reveals"],
                "context_adaptive": True
            },
            "energetic": {
                "basic": ["amazing", "fantastic", "awesome"],
                "advanced": ["absolutely incredible", "mind-blowing", "game-changing"],
                "context_adaptive": True
            },
            "trustworthy": {
                "basic": ["Based on my experience", "In my years"],
                "advanced": ["Having worked with hundreds of clients", "Through years of testing"],
                "context_adaptive": True
            },
            "data-driven": {
                "basic": ["Generally", "Usually"],
                "advanced": ["Statistically speaking", "According to the data", "Research shows"],
                "context_adaptive": True
            }
        }
        
        for trait in personality_traits:
            if trait in transformations:
                transform_config = transformations[trait]
                
                # Apply context-adaptive transformation
                if transform_config.get("context_adaptive"):
                    # Select appropriate transformation based on content context
                    if "tip" in content.lower() or "advice" in content.lower():
                        content = content.replace("Here is", transform_config["advanced"][0])
                    elif "guide" in content.lower() or "tutorial" in content.lower():
                        content = content.replace("This is", transform_config["advanced"][1])
                    else:
                        content = content.replace("This is", transform_config["basic"][0])
        
        return content
    
    def _apply_voice_type_optimizations(self, content: str, voice_type: str, platform: str) -> str:
        """Apply voice type specific optimizations"""
        
        if voice_type == "professional_male":
            # Enhance professional language
            content = re.sub(r'\bi think\b', 'I believe', content, flags=re.IGNORECASE)
            content = re.sub(r'\bwe should\b', 'it would be beneficial to', content, flags=re.IGNORECASE)
            
        elif voice_type == "friendly_female":
            # Enhance conversational elements
            content = re.sub(r'\bI recommend\b', 'I really think you should', content, flags=re.IGNORECASE)
            content = re.sub(r'\bYou need to\b', 'You might want to', content, flags=re.IGNORECASE)
            
        elif voice_type == "casual_young":
            # Enhance casual language
            content = re.sub(r'\bI recommend\b', 'Trust me on this', content, flags=re.IGNORECASE)
            content = re.sub(r'\bThis is important\b', "This is actually really important", content, flags=re.IGNORECASE)
        
        return content
    
    def _apply_platform_specific_refinements(self, content: str, platform: str, voice_type: str) -> str:
        """Apply final platform-specific refinements"""
        
        if platform == "tiktok":
            # Add TikTok-specific language patterns
            content = re.sub(r'\bMake sure\b', 'Don\'t forget to', content)
            content = re.sub(r'\bRemember\b', 'Pro tip:', content)
            
        elif platform == "linkedin":
            # Enhance professional networking language
            content = re.sub(r'\bI think\b', 'In my professional opinion', content, flags=re.IGNORECASE)
            content = re.sub(r'\bHere\'s what\b', 'Key takeaway:', content, flags=re.IGNORECASE)
            
        elif platform == "instagram":
            # Add Instagram-specific engagement
            if not content.endswith('!'):
                content += " 💙"
        
        return content
    
    def get_influencer(self, influencer_id: int) -> Optional[Dict[str, Any]]:
        """Get influencer data with persona information"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM influencers WHERE id = ? AND is_active = 1", (influencer_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            influencer = dict(row)
            influencer['personality_traits'] = json.loads(influencer['personality_traits'] or '[]')
            influencer['target_audience'] = json.loads(influencer['target_audience'] or '{}')
            influencer['branding_guidelines'] = json.loads(influencer['branding_guidelines'] or '{}')
            
            return influencer
            
        finally:
            conn.close()
    
    def train_persona_model(self, content_samples: List[Dict], influencer_id: int) -> bool:
        """Train persona model based on existing content samples"""
        # This would typically involve ML model training
        # For now, we'll store patterns for future use
        
        influencer = self.get_influencer(influencer_id)
        if not influencer:
            return False
        
        # Extract patterns from successful content
        voice_patterns = self._extract_voice_patterns(content_samples, influencer)
        
        # Update influencer's branding guidelines with learned patterns
        updated_guidelines = influencer.get('branding_guidelines', {})
        updated_guidelines['learned_voice_patterns'] = voice_patterns
        updated_guidelines['last_trained'] = datetime.now().isoformat()
        
        # This would update the database in a real implementation
        return True
    
    def _extract_voice_patterns(self, content_samples: List[Dict], influencer: Dict) -> Dict:
        """Extract voice patterns from content samples"""
        patterns = {
            "common_opening_phrases": [],
            "frequent_transitions": [],
            "signature_phrases": [],
            "closing_patterns": []
        }
        
        for sample in content_samples:
            content = sample.get('content', '').lower()
            sentences = [s.strip() for s in content.split('.') if s.strip()]
            
            if sentences:
                # Extract opening phrases
                first_sentence = sentences[0]
                words = first_sentence.split()[:4]  # First 4 words
                patterns["common_opening_phrases"].append(' '.join(words))
            
            # Extract other patterns...
            # This would be more sophisticated in a real implementation
        
        # Remove duplicates and return top patterns
        for key in patterns:
            patterns[key] = list(set(patterns[key]))[:5]  # Top 5 unique patterns
        
        return patterns
    
    def create_style_guide(self, influencer_id: int) -> Dict:
        """Create visual style guide for influencer"""
        
        influencer = self.get_influencer(influencer_id)
        if not influencer:
            return {}
        
        voice_type = influencer.get('voice_type', 'professional_male')
        personality_traits = influencer.get('personality_traits', [])
        
        style_guide = {
            "color_palette": self._get_color_palette(voice_type, personality_traits),
            "typography": self._get_typography_guidelines(voice_type),
            "mood": self._get_mood_guidelines(personality_traits),
            "prohibited_elements": self._get_prohibited_elements(voice_type, personality_traits)
        }
        
        return style_guide
    
    def _get_color_palette(self, voice_type: str, personality_traits: List[str]) -> List[str]:
        """Get recommended color palette"""
        palettes = {
            "professional_male": ["#2C3E50", "#34495E", "#7F8C8D", "#FFFFFF", "#E8F4FD"],
            "friendly_female": ["#FF6B9D", "#C44569", "#F8B500", "#FFA07A", "#FFFFFF"],
            "casual_young": ["#6C5CE7", "#A29BFE", "#00B894", "#00CEC9", "#FDCB6E"]
        }
        
        base_palette = palettes.get(voice_type, palettes["professional_male"])
        
        # Adjust based on personality
        if "energetic" in personality_traits:
            base_palette[1] = "#FF4757"  # Add more vibrant red
        if "trustworthy" in personality_traits:
            base_palette[0] = "#1B4F72"  # Deeper, more trustworthy blue
        
        return base_palette
    
    def _get_typography_guidelines(self, voice_type: str) -> Dict:
        """Get typography guidelines"""
        return {
            "primary_font": "Open Sans" if voice_type == "professional_male" else "Poppins" if voice_type == "friendly_female" else "Montserrat",
            "secondary_font": "Lato" if voice_type == "professional_male" else "Nunito" if voice_type == "friendly_female" else "Source Sans Pro",
            "font_sizes": {
                "headlines": "32-48px",
                "subheadings": "24-32px",
                "body_text": "16-18px",
                "captions": "14-16px"
            }
        }
    
    def _get_mood_guidelines(self, personality_traits: List[str]) -> Dict:
        """Get mood and emotional guidelines"""
        mood_map = {
            "knowledgeable": {"tone": "authoritative", "energy": "calm", "approach": "educational"},
            "energetic": {"tone": "enthusiastic", "energy": "high", "approach": "motivating"},
            "trustworthy": {"tone": "reliable", "energy": "steady", "approach": "honest"},
            "creative": {"tone": "innovative", "energy": "dynamic", "approach": "inspiring"}
        }
        
        combined_mood = {"tone": "balanced", "energy": "moderate", "approach": "friendly"}
        
        for trait in personality_traits:
            if trait in mood_map:
                trait_mood = mood_map[trait]
                # Combine moods (simple averaging)
                combined_mood["tone"] = self._blend_tones(combined_mood["tone"], trait_mood["tone"])
                combined_mood["energy"] = self._blend_energy(combined_mood["energy"], trait_mood["energy"])
        
        return combined_mood
    
    def _blend_tones(self, tone1: str, tone2: str) -> str:
        """Blend two tones (simplified)"""
        if tone1 == tone2:
            return tone1
        if "authoritative" in [tone1, tone2] and "balanced" in [tone1, tone2]:
            return "semi-authoritative"
        return "balanced"
    
    def _blend_energy(self, energy1: str, energy2: str) -> str:
        """Blend two energy levels (simplified)"""
        if energy1 == energy2:
            return energy1
        if "high" in [energy1, energy2] and "moderate" in [energy1, energy2]:
            return "moderately high"
        return "moderate"
    
    def _get_prohibited_elements(self, voice_type: str, personality_traits: List[str]) -> List[str]:
        """Get list of prohibited visual elements"""
        prohibited = [
            "overly flashy animations",
            "cluttered layouts",
            "inappropriate imagery"
        ]
        
        if voice_type == "professional_male":
            prohibited.extend([
                "excessive neon colors",
                "playful fonts",
                "casual slang in text"
            ])
        elif voice_type == "friendly_female":
            prohibited.extend([
                "aggressive imagery",
                "harsh contrasts",
                "intimidating design"
            ])
        elif voice_type == "casual_young":
            prohibited.extend([
                "corporate stock photos",
                "stiff poses",
                "formal language"
            ])
        
        if "trustworthy" in personality_traits:
            prohibited.append("misleading visuals")
        
        if "professional" in personality_traits:
            prohibited.append("unprofessional humor")
        
        return list(set(prohibited))  # Remove duplicates