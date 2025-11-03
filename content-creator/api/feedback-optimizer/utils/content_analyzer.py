"""
Content Analysis Utility Module

Analyzes content quality and characteristics for targeted improvements.
"""

import re
import math
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict

from ..models.feedback_data import FeedbackData


class ContentAnalyzer:
    """
    Analyzes content quality, structure, and characteristics for improvement targeting.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the content analyzer."""
        self.config = config or self._default_config()
        self.quality_metrics = self._load_quality_metrics()
        self.content_benchmarks = self._load_content_benchmarks()
        
    def _default_config(self) -> Dict:
        """Default configuration for content analysis."""
        return {
            'readability_weight': 0.2,
            'engagement_weight': 0.3,
            'quality_weight': 0.3,
            'structure_weight': 0.2,
            'quality_thresholds': {
                'excellent': 0.8,
                'good': 0.6,
                'average': 0.4,
                'poor': 0.2
            }
        }
    
    def analyze_content(self, content: str, content_type: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Comprehensive content analysis.
        
        Args:
            content: Content to analyze
            content_type: Type of content ('script', 'thumbnail', 'title', etc.)
            metadata: Additional content metadata
            
        Returns:
            Dictionary containing comprehensive analysis results
        """
        if not content:
            return self._empty_analysis()
        
        # Base analysis
        structure_analysis = self._analyze_structure(content, content_type)
        quality_analysis = self._analyze_quality(content, content_type)
        readability_analysis = self._analyze_readability(content)
        engagement_analysis = self._analyze_engagement_potential(content, content_type)
        
        # Content-specific analysis
        specific_analysis = self._perform_content_specific_analysis(content, content_type)
        
        # Calculate overall scores
        overall_scores = self._calculate_overall_scores({
            'structure': structure_analysis,
            'quality': quality_analysis,
            'readability': readability_analysis,
            'engagement': engagement_analysis,
            'specific': specific_analysis
        })
        
        return {
            'content_type': content_type,
            'analysis_timestamp': self._get_current_timestamp(),
            'overall_scores': overall_scores,
            'structure_analysis': structure_analysis,
            'quality_analysis': quality_analysis,
            'readability_analysis': readability_analysis,
            'engagement_analysis': engagement_analysis,
            'content_specific': specific_analysis,
            'improvement_suggestions': self._generate_improvement_suggestions(overall_scores, specific_analysis),
            'benchmark_comparison': self._compare_to_benchmarks(overall_scores, content_type)
        }
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure."""
        return {
            'content_type': 'unknown',
            'analysis_timestamp': self._get_current_timestamp(),
            'overall_scores': {},
            'structure_analysis': {},
            'quality_analysis': {},
            'readability_analysis': {},
            'engagement_analysis': {},
            'content_specific': {},
            'improvement_suggestions': [],
            'benchmark_comparison': {}
        }
    
    def _analyze_structure(self, content: str, content_type: str) -> Dict[str, Any]:
        """Analyze content structure and organization."""
        analysis = {}
        
        if content_type == 'script':
            analysis = self._analyze_script_structure(content)
        elif content_type == 'title':
            analysis = self._analyze_title_structure(content)
        elif content_type == 'thumbnail':
            analysis = self._analyze_thumbnail_structure(content)
        else:
            analysis = self._analyze_general_structure(content)
        
        # Calculate structure score
        structure_score = self._calculate_structure_score(analysis, content_type)
        analysis['structure_score'] = structure_score
        analysis['structure_quality'] = self._get_quality_rating(structure_score)
        
        return analysis
    
    def _analyze_quality(self, content: str, content_type: str) -> Dict[str, Any]:
        """Analyze content quality indicators."""
        quality_indicators = {
            'grammar_score': self._check_grammar(content),
            'spelling_score': self._check_spelling(content),
            'coherence_score': self._check_coherence(content),
            'completeness_score': self._check_completeness(content, content_type),
            'originality_score': self._check_originality(content),
            'accuracy_score': self._check_accuracy(content, content_type)
        }
        
        # Weighted quality score
        weights = self.quality_metrics.get('weights', {})
        quality_score = sum(
            quality_indicators[key] * weights.get(key, 0.16) 
            for key in quality_indicators.keys()
        )
        
        # Identify quality issues
        issues = []
        for indicator, score in quality_indicators.items():
            if score < 0.6:
                issues.append({
                    'issue': indicator,
                    'severity': 'high' if score < 0.3 else 'medium',
                    'score': score
                })
        
        return {
            'quality_indicators': quality_indicators,
            'overall_quality_score': quality_score,
            'quality_rating': self._get_quality_rating(quality_score),
            'quality_issues': issues,
            'quality_strengths': [key for key, score in quality_indicators.items() if score > 0.8]
        }
    
    def _analyze_readability(self, content: str) -> Dict[str, Any]:
        """Analyze content readability and comprehension."""
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        
        # Basic readability metrics
        avg_word_length = sum(len(word.strip('.,!?;:"()[]')) for word in words) / len(words) if words else 0
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        # Flesch Reading Ease (simplified)
        syllable_count = self._estimate_syllable_count(content)
        if len(words) > 0 and len(sentences) > 0:
            flesch_score = 206.835 - (1.015 * (len(words) / len(sentences))) - (84.6 * (syllable_count / len(words)))
            flesch_score = max(0, min(100, flesch_score))  # Clamp to 0-100
        else:
            flesch_score = 0
        
        # Readability grade level
        grade_level = self._estimate_grade_level(flesch_score)
        
        # Comprehension factors
        complexity_score = self._calculate_complexity_score(avg_word_length, avg_sentence_length)
        
        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'average_word_length': round(avg_word_length, 2),
            'average_sentence_length': round(avg_sentence_length, 2),
            'flesch_reading_ease': round(flesch_score, 1),
            'grade_level': grade_level,
            'complexity_score': round(complexity_score, 2),
            'readability_rating': self._get_readability_rating(flesch_score),
            'comprehension_difficulty': 'easy' if flesch_score > 60 else 'medium' if flesch_score > 30 else 'hard'
        }
    
    def _analyze_engagement_potential(self, content: str, content_type: str) -> Dict[str, Any]:
        """Analyze potential for audience engagement."""
        engagement_factors = {
            'hook_strength': self._analyze_hook_strength(content, content_type),
            'emotional_appeal': self._analyze_emotional_appeal(content),
            'curiosity_factor': self._analyze_curiosity_factor(content),
            'call_to_action_strength': self._analyze_cta_strength(content, content_type),
            'storytelling_elements': self._analyze_storytelling_elements(content),
            'interactive_elements': self._analyze_interactive_elements(content)
        }
        
        # Engagement score
        engagement_score = sum(engagement_factors.values()) / len(engagement_factors)
        
        # Engagement type classification
        engagement_type = self._classify_engagement_type(engagement_factors)
        
        return {
            'engagement_factors': engagement_factors,
            'overall_engagement_score': round(engagement_score, 3),
            'engagement_type': engagement_type,
            'engagement_potential': 'high' if engagement_score > 0.7 else 'medium' if engagement_score > 0.4 else 'low',
            'recommended_improvements': self._suggest_engagement_improvements(engagement_factors)
        }
    
    def _perform_content_specific_analysis(self, content: str, content_type: str) -> Dict[str, Any]:
        """Perform content-type specific analysis."""
        if content_type == 'script':
            return self._analyze_script_specific(content)
        elif content_type == 'title':
            return self._analyze_title_specific(content)
        elif content_type == 'thumbnail':
            return self._analyze_thumbnail_specific(content)
        elif content_type == 'description':
            return self._analyze_description_specific(content)
        else:
            return self._analyze_general_specific(content)
    
    def _calculate_overall_scores(self, analyses: Dict[str, Any]) -> Dict[str, float]:
        """Calculate weighted overall scores."""
        weights = {
            'structure': self.config['structure_weight'],
            'quality': self.config['quality_weight'],
            'readability': self.config['readability_weight'],
            'engagement': self.config['engagement_weight']
        }
        
        scores = {}
        for category, weight in weights.items():
            category_analysis = analyses.get(category, {})
            if isinstance(category_analysis, dict) and 'score' in category_analysis:
                scores[f"{category}_score"] = category_analysis['score']
            elif isinstance(category_analysis, dict) and 'overall_quality_score' in category_analysis:
                scores[f"{category}_score"] = category_analysis['overall_quality_score']
            elif isinstance(category_analysis, dict) and 'overall_engagement_score' in category_analysis:
                scores[f"{category}_score"] = category_analysis['overall_engagement_score']
            else:
                scores[f"{category}_score"] = 0.5  # Default neutral score
        
        # Overall content score
        overall_score = sum(
            scores[f"{category}_score"] * weight 
            for category, weight in weights.items()
        )
        
        scores['overall_content_score'] = round(overall_score, 3)
        
        return scores
    
    def _generate_improvement_suggestions(self, overall_scores: Dict[str, float], specific_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific improvement suggestions."""
        suggestions = []
        
        # Score-based suggestions
        for score_name, score_value in overall_scores.items():
            if 'score' in score_name and score_value < 0.5:
                category = score_name.replace('_score', '')
                suggestions.append({
                    'category': category,
                    'current_score': score_value,
                    'suggestion': f"Improve {category.replace('_', ' ')} aspects",
                    'priority': 'high' if score_value < 0.3 else 'medium',
                    'impact_potential': 'high'
                })
        
        # Content-specific suggestions
        if 'script_analysis' in specific_analysis:
            script_issues = specific_analysis['script_analysis'].get('issues', [])
            for issue in script_issues[:3]:  # Top 3 issues
                suggestions.append({
                    'category': 'script_specific',
                    'issue': issue,
                    'suggestion': f"Address script {issue}",
                    'priority': 'medium',
                    'impact_potential': 'medium'
                })
        
        return sorted(suggestions, key=lambda x: (x['priority'] == 'high', x['current_score'] if isinstance(x.get('current_score'), (int, float)) else 0.5))
    
    def _compare_to_benchmarks(self, scores: Dict[str, float], content_type: str) -> Dict[str, Any]:
        """Compare content scores to industry benchmarks."""
        benchmarks = self.content_benchmarks.get(content_type, {})
        
        comparison = {}
        for score_name, score_value in scores.items():
            if score_name in benchmarks:
                benchmark_value = benchmarks[score_name]
                performance_vs_benchmark = 'above' if score_value > benchmark_value else 'below' if score_value < benchmark_value else 'at'
                difference = score_value - benchmark_value
                
                comparison[score_name] = {
                    'score': score_value,
                    'benchmark': benchmark_value,
                    'performance': performance_vs_benchmark,
                    'difference': round(difference, 3)
                }
        
        return comparison
    
    # Content-type specific analysis methods
    def _analyze_script_structure(self, content: str) -> Dict[str, Any]:
        """Analyze script-specific structure."""
        # Check for typical script elements
        has_intro = bool(re.search(r'(intro|introduction|welcome|hello|hi)', content.lower()))
        has_outro = bool(re.search(r'(outro|conclusion|thanks|bye|goodbye)', content.lower()))
        has_transitions = bool(re.search(r'(now|next|then|after that|meanwhile)', content.lower()))
        
        # Structure flow analysis
        paragraphs = content.split('\n\n')
        logical_flow = self._assess_logical_flow(paragraphs)
        
        return {
            'has_intro': has_intro,
            'has_outro': has_outro,
            'has_transitions': has_transitions,
            'paragraph_count': len(paragraphs),
            'logical_flow_score': logical_flow,
            'structure_elements_present': sum([has_intro, has_outro, has_transitions])
        }
    
    def _analyze_title_structure(self, content: str) -> Dict[str, Any]:
        """Analyze title-specific structure."""
        length = len(content)
        word_count = len(content.split())
        
        # Title structure indicators
        has_question = '?' in content
        has_numbers = bool(re.search(r'\d', content))
        has_power_words = bool(re.search(r'(amazing|incredible|secret|ultimate|perfect|best)', content.lower()))
        
        return {
            'character_length': length,
            'word_count': word_count,
            'has_question': has_question,
            'has_numbers': has_numbers,
            'has_power_words': has_power_words,
            'length_assessment': self._assess_title_length(length, word_count)
        }
    
    def _analyze_thumbnail_structure(self, content: str) -> Dict[str, Any]:
        """Analyze thumbnail-specific structure (metadata-based)."""
        # This would typically analyze image metadata, colors, etc.
        # For text-based analysis, we'll focus on descriptive elements
        
        has_colors_mentioned = bool(re.search(r'(red|blue|green|yellow|orange|purple|pink|brown)', content.lower()))
        has_design_elements = bool(re.search(r'(text|image|photo|picture|graphic|design)', content.lower()))
        
        return {
            'descriptive_content': content,
            'mentions_colors': has_colors_mentioned,
            'mentions_design_elements': has_design_elements,
            'visual_complexity': 'medium'  # Placeholder - would analyze actual image
        }
    
    def _analyze_general_structure(self, content: str) -> Dict[str, Any]:
        """Analyze general content structure."""
        paragraphs = content.split('\n\n')
        sentences = re.split(r'[.!?]+', content)
        
        return {
            'paragraph_count': len(paragraphs),
            'sentence_count': len(sentences),
            'structure_complexity': 'simple' if len(paragraphs) <= 3 else 'moderate' if len(paragraphs) <= 6 else 'complex'
        }
    
    # Individual analysis helper methods
    def _check_grammar(self, content: str) -> float:
        """Check grammar quality (simplified)."""
        # This is a simplified check - in reality, you'd use a proper grammar checker
        common_errors = ['their', 'there', 'theyre', 'its', 'its', 'your', 'youre']
        words = content.lower().split()
        
        error_count = sum(1 for word in words if word in common_errors)
        total_words = len(words)
        
        if total_words == 0:
            return 1.0
        
        accuracy = 1 - (error_count / total_words)
        return max(0.0, min(1.0, accuracy))
    
    def _check_spelling(self, content: str) -> float:
        """Check spelling quality (simplified)."""
        # This is a placeholder - in reality, you'd use a spell checker
        words = content.split()
        suspicious_words = [word for word in words if len(word) > 15 or '999' in word]
        
        if len(words) == 0:
            return 1.0
        
        spelling_accuracy = 1 - (len(suspicious_words) / len(words))
        return max(0.0, min(1.0, spelling_accuracy))
    
    def _check_coherence(self, content: str) -> float:
        """Check content coherence and flow."""
        sentences = re.split(r'[.!?]+', content)
        
        if len(sentences) < 2:
            return 0.8  # Single sentence content is assumed coherent
        
        # Simple coherence check based on sentence length variation
        lengths = [len(s.strip()) for s in sentences if s.strip()]
        if not lengths:
            return 0.5
        
        avg_length = sum(lengths) / len(lengths)
        variation = sum(abs(l - avg_length) for l in lengths) / len(lengths)
        variation_ratio = variation / avg_length if avg_length > 0 else 0
        
        # Lower variation ratio indicates better coherence
        coherence = 1 - min(variation_ratio, 1.0)
        return max(0.0, min(1.0, coherence))
    
    def _check_completeness(self, content: str, content_type: str) -> float:
        """Check if content is complete for its type."""
        if not content:
            return 0.0
        
        word_count = len(content.split())
        
        if content_type == 'title':
            return 1.0 if 3 <= word_count <= 12 else 0.6
        elif content_type == 'script':
            return 1.0 if word_count >= 100 else max(0.2, word_count / 100)
        elif content_type == 'description':
            return 1.0 if word_count >= 50 else max(0.3, word_count / 50)
        else:
            return 0.8  # Default assumption
    
    def _check_originality(self, content: str) -> float:
        """Check content originality (simplified)."""
        # This is a placeholder - in reality, you'd check against existing content
        # Simple uniqueness check based on repetition
        words = content.lower().split()
        word_freq = Counter(words)
        
        if not words:
            return 0.0
        
        unique_words = len(set(words))
        total_words = len(words)
        uniqueness_ratio = unique_words / total_words
        
        return max(0.0, min(1.0, uniqueness_ratio))
    
    def _check_accuracy(self, content: str, content_type: str) -> float:
        """Check content accuracy (simplified)."""
        # This is highly simplified - real accuracy checking would be very complex
        # Check for common factual indicators
        
        accuracy_indicators = ['fact', 'study', 'research', 'according to', 'statistics', 'data']
        words = content.lower().split()
        
        indicator_count = sum(1 for indicator in accuracy_indicators if any(indicator in word for word in words))
        
        # More accuracy indicators suggest potentially more accurate content
        accuracy_score = min(0.9, 0.5 + (indicator_count * 0.1))
        
        return accuracy_score
    
    def _assess_logical_flow(self, paragraphs: List[str]) -> float:
        """Assess logical flow between paragraphs."""
        if len(paragraphs) < 2:
            return 0.8
        
        # Simple flow assessment based on transition words
        transition_indicators = ['however', 'therefore', 'furthermore', 'moreover', 'consequently', 'meanwhile']
        
        flow_score = 0.5  # Base score
        for paragraph in paragraphs:
            for indicator in transition_indicators:
                if indicator in paragraph.lower():
                    flow_score += 0.1
                    break
        
        return min(1.0, flow_score)
    
    def _estimate_syllable_count(self, text: str) -> int:
        """Estimate syllable count in text."""
        words = text.lower().split()
        syllable_count = 0
        
        for word in words:
            # Simple syllable estimation
            vowels = 'aeiouy'
            syllables = 0
            prev_was_vowel = False
            
            for char in word:
                if char in vowels:
                    if not prev_was_vowel:
                        syllables += 1
                    prev_was_vowel = True
                else:
                    prev_was_vowel = False
            
            # Handle silent e
            if word.endswith('e') and syllables > 1:
                syllables -= 1
            
            # Minimum one syllable per word
            syllables = max(1, syllables)
            syllable_count += syllables
        
        return syllable_count
    
    def _estimate_grade_level(self, flesch_score: float) -> str:
        """Estimate grade level from Flesch score."""
        if flesch_score >= 90:
            return "5th grade"
        elif flesch_score >= 80:
            return "6th grade"
        elif flesch_score >= 70:
            return "7th grade"
        elif flesch_score >= 60:
            return "8th-9th grade"
        elif flesch_score >= 50:
            return "10th-12th grade"
        elif flesch_score >= 30:
            return "College level"
        else:
            return "College graduate level"
    
    def _calculate_complexity_score(self, avg_word_length: float, avg_sentence_length: float) -> float:
        """Calculate text complexity score."""
        # Normalize and combine complexity factors
        word_complexity = min(avg_word_length / 10, 1.0)  # Word length complexity
        sentence_complexity = min(avg_sentence_length / 30, 1.0)  # Sentence length complexity
        
        complexity_score = (word_complexity + sentence_complexity) / 2
        return complexity_score
    
    def _get_readability_rating(self, flesch_score: float) -> str:
        """Get readability rating from Flesch score."""
        if flesch_score >= 80:
            return "Very Easy"
        elif flesch_score >= 70:
            return "Easy"
        elif flesch_score >= 60:
            return "Fairly Easy"
        elif flesch_score >= 50:
            return "Standard"
        elif flesch_score >= 30:
            return "Fairly Difficult"
        elif flesch_score >= 0:
            return "Difficult"
        else:
            return "Very Difficult"
    
    # Engagement analysis methods
    def _analyze_hook_strength(self, content: str, content_type: str) -> float:
        """Analyze how strong the content hook is."""
        hooks = [
            r'^did you know',
            r'^have you ever',
            r'^what if',
            r'^imagine',
            r'^picture this',
            r'^here\'s the thing',
            r'^let me tell you',
            r'^everyone thinks',
            r'^the secret',
            r'^nobody talks about'
        ]
        
        content_lower = content.lower().strip()
        hook_score = 0.0
        
        for hook in hooks:
            if re.search(hook, content_lower):
                hook_score = 0.8
                break
        
        # Bonus for questions in first sentence
        if '?' in content.split('\n')[0] if content_type == 'script' else '?' in content[:50]:
            hook_score = max(hook_score, 0.6)
        
        return hook_score
    
    def _analyze_emotional_appeal(self, content: str) -> float:
        """Analyze emotional appeal of content."""
        emotional_words = [
            'amazing', 'incredible', 'shocking', 'devastating', 'heartwarming', 'exciting',
            'frustrating', 'disappointing', 'thrilling', 'boring', 'fascinating', 'outrageous'
        ]
        
        content_lower = content.lower()
        emotional_word_count = sum(1 for word in emotional_words if word in content_lower)
        
        # Normalize by content length
        word_count = len(content.split())
        if word_count == 0:
            return 0.0
        
        emotional_density = emotional_word_count / word_count
        return min(1.0, emotional_density * 10)  # Scale factor
    
    def _analyze_curiosity_factor(self, content: str) -> float:
        """Analyze curiosity-inducing elements."""
        curiosity_triggers = [
            r'secret',
            r'hidden',
            r'unknown',
            r'surprising',
            r' unexpected',
            r'little-known',
            r'shocking truth',
            r'nobody tells you',
            r'what happens next',
            r'the real reason'
        ]
        
        content_lower = content.lower()
        trigger_count = sum(1 for trigger in curiosity_triggers if trigger in content_lower)
        
        return min(1.0, trigger_count * 0.2)
    
    def _analyze_cta_strength(self, content: str, content_type: str) -> float:
        """Analyze call-to-action strength."""
        cta_phrases = [
            'subscribe', 'like', 'comment', 'share', 'follow', 'click', 'visit',
            'learn more', 'find out', 'check out', 'try', 'download', 'sign up'
        ]
        
        content_lower = content.lower()
        cta_count = sum(1 for cta in cta_phrases if cta in content_lower)
        
        return min(1.0, cta_count * 0.3)
    
    def _analyze_storytelling_elements(self, content: str) -> float:
        """Analyze storytelling elements."""
        story_indicators = [
            r'once upon',
            r'first',
            r'then',
            r'after',
            r'suddenly',
            r'finally',
            r'story',
            r'experience',
            r'happened',
            r'journey'
        ]
        
        content_lower = content.lower()
        story_elements = sum(1 for indicator in story_indicators if re.search(indicator, content_lower))
        
        return min(1.0, story_elements * 0.15)
    
    def _analyze_interactive_elements(self, content: str) -> float:
        """Analyze interactive elements that encourage engagement."""
        interactive_triggers = [
            r'what do you think',
            r'comment below',
            r'let me know',
            r'do you agree',
            r'would you',
            r'can you',
            r'question',
            r'poll',
            r'vote'
        ]
        
        content_lower = content.lower()
        interactive_count = sum(1 for trigger in interactive_triggers if re.search(trigger, content_lower))
        
        return min(1.0, interactive_count * 0.25)
    
    def _classify_engagement_type(self, factors: Dict[str, float]) -> str:
        """Classify the primary engagement type."""
        factor_scores = [(name, score) for name, score in factors.items()]
        factor_scores.sort(key=lambda x: x[1], reverse=True)
        
        primary_factor = factor_scores[0][0] if factor_scores else 'general'
        
        type_mapping = {
            'hook_strength': 'hook-based',
            'emotional_appeal': 'emotion-driven',
            'curiosity_factor': 'curiosity-driven',
            'call_to_action_strength': 'action-oriented',
            'storytelling_elements': 'story-based',
            'interactive_elements': 'interactive'
        }
        
        return type_mapping.get(primary_factor, 'general')
    
    def _suggest_engagement_improvements(self, factors: Dict[str, float]) -> List[str]:
        """Suggest specific engagement improvements."""
        suggestions = []
        
        for factor_name, score in factors.items():
            if score < 0.4:
                if factor_name == 'hook_strength':
                    suggestions.append("Add a compelling hook at the beginning")
                elif factor_name == 'emotional_appeal':
                    suggestions.append("Include more emotional language and storytelling")
                elif factor_name == 'curiosity_factor':
                    suggestions.append("Add elements that create curiosity and anticipation")
                elif factor_name == 'call_to_action_strength':
                    suggestions.append("Strengthen your call-to-action with specific requests")
                elif factor_name == 'storytelling_elements':
                    suggestions.append("Incorporate narrative elements and personal experiences")
                elif factor_name == 'interactive_elements':
                    suggestions.append("Add questions and interactive elements for audience participation")
        
        return suggestions
    
    def _calculate_structure_score(self, analysis: Dict[str, Any], content_type: str) -> float:
        """Calculate overall structure score."""
        if content_type == 'script':
            elements_present = analysis.get('structure_elements_present', 0)
            total_elements = 3  # intro, outro, transitions
            logical_flow = analysis.get('logical_flow_score', 0.5)
            
            structure_score = (elements_present / total_elements * 0.6) + (logical_flow * 0.4)
            return min(1.0, structure_score)
        
        elif content_type == 'title':
            length_assessment = analysis.get('length_assessment', 'poor')
            length_scores = {'excellent': 1.0, 'good': 0.8, 'average': 0.6, 'poor': 0.3}
            return length_scores.get(length_assessment, 0.5)
        
        else:
            # Generic structure score
            complexity = analysis.get('structure_complexity', 'moderate')
            complexity_scores = {'simple': 0.8, 'moderate': 0.7, 'complex': 0.9}
            return complexity_scores.get(complexity, 0.6)
    
    def _get_quality_rating(self, score: float) -> str:
        """Get quality rating from score."""
        thresholds = self.config['quality_thresholds']
        
        if score >= thresholds['excellent']:
            return 'excellent'
        elif score >= thresholds['good']:
            return 'good'
        elif score >= thresholds['average']:
            return 'average'
        elif score >= thresholds['poor']:
            return 'poor'
        else:
            return 'very_poor'
    
    def _assess_title_length(self, char_length: int, word_count: int) -> str:
        """Assess title length appropriateness."""
        if 30 <= char_length <= 60 and 4 <= word_count <= 8:
            return 'excellent'
        elif 20 <= char_length <= 70 and 3 <= word_count <= 10:
            return 'good'
        elif 15 <= char_length <= 80 and 2 <= word_count <= 12:
            return 'average'
        else:
            return 'poor'
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _load_quality_metrics(self) -> Dict[str, Any]:
        """Load quality assessment metrics and weights."""
        return {
            'weights': {
                'grammar_score': 0.2,
                'spelling_score': 0.15,
                'coherence_score': 0.2,
                'completeness_score': 0.2,
                'originality_score': 0.15,
                'accuracy_score': 0.1
            }
        }
    
    def _load_content_benchmarks(self) -> Dict[str, Any]:
        """Load industry benchmarks for content types."""
        return {
            'script': {
                'structure_score': 0.7,
                'quality_score': 0.75,
                'readability_score': 0.6,
                'engagement_score': 0.7
            },
            'title': {
                'structure_score': 0.8,
                'quality_score': 0.9,
                'readability_score': 0.9,
                'engagement_score': 0.8
            },
            'thumbnail': {
                'structure_score': 0.7,
                'quality_score': 0.8,
                'readability_score': 0.7,
                'engagement_score': 0.85
            }
        }
    
    # Content-specific analysis stubs (would be expanded in real implementation)
    def _analyze_script_specific(self, content: str) -> Dict[str, Any]:
        """Analyze script-specific content quality."""
        issues = []
        
        # Check for common script issues
        if len(content.split()) < 50:
            issues.append('too_short')
        
        if not re.search(r'(intro|introduction)', content.lower()):
            issues.append('missing_intro')
        
        if not re.search(r'(conclusion|outro|thanks)', content.lower()):
            issues.append('missing_outro')
        
        return {
            'script_analysis': {
                'word_count': len(content.split()),
                'issues': issues,
                'estimated_duration_minutes': len(content.split()) / 150,  # ~150 WPM
                'sections_present': self._identify_script_sections(content)
            }
        }
    
    def _analyze_title_specific(self, content: str) -> Dict[str, Any]:
        """Analyze title-specific content quality."""
        return {
            'title_analysis': {
                'character_length': len(content),
                'word_count': len(content.split()),
                'has_power_words': bool(re.search(r'(amazing|incredible|secret|ultimate)', content.lower())),
                'has_numbers': bool(re.search(r'\d', content)),
                'seo_score': self._calculate_simple_seo_score(content)
            }
        }
    
    def _analyze_thumbnail_specific(self, content: str) -> Dict[str, Any]:
        """Analyze thumbnail-specific content quality."""
        return {
            'thumbnail_analysis': {
                'has_color_description': bool(re.search(r'(red|blue|green|yellow)', content.lower())),
                'has_text_mention': 'text' in content.lower(),
                'visual_complexity': 'medium'  # Placeholder
            }
        }
    
    def _analyze_description_specific(self, content: str) -> Dict[str, Any]:
        """Analyze description-specific content quality."""
        return {
            'description_analysis': {
                'word_count': len(content.split()),
                'has_hashtags': '#' in content,
                'has_links': 'http' in content,
                'keyword_density': self._calculate_keyword_density(content)
            }
        }
    
    def _analyze_general_specific(self, content: str) -> Dict[str, Any]:
        """Analyze general content quality."""
        return {
            'general_analysis': {
                'content_length': len(content),
                'word_count': len(content.split()),
                'formatting_score': self._assess_formatting(content)
            }
        }
    
    def _identify_script_sections(self, content: str) -> List[str]:
        """Identify script sections present in content."""
        sections = []
        content_lower = content.lower()
        
        if re.search(r'(intro|introduction)', content_lower):
            sections.append('intro')
        if re.search(r'(main|body|content)', content_lower):
            sections.append('main_content')
        if re.search(r'(conclusion|outro|summary)', content_lower):
            sections.append('conclusion')
        if re.search(r'(cta|call to action)', content_lower):
            sections.append('cta')
        
        return sections
    
    def _calculate_simple_seo_score(self, title: str) -> float:
        """Calculate simple SEO score for title."""
        score = 0.5  # Base score
        
        # Length optimization
        if 30 <= len(title) <= 60:
            score += 0.2
        
        # Word count optimization
        word_count = len(title.split())
        if 4 <= word_count <= 8:
            score += 0.2
        
        # Power words
        if re.search(r'(best|ultimate|complete|ultimate)', title.lower()):
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_keyword_density(self, content: str) -> float:
        """Calculate keyword density in content."""
        words = content.lower().split()
        if not words:
            return 0.0
        
        # Simple keyword density (this would be more sophisticated in reality)
        keyword_indicators = ['content', 'video', 'video', 'channel', 'subscribe']
        keyword_count = sum(1 for word in words if word in keyword_indicators)
        
        return keyword_count / len(words)
    
    def _assess_formatting(self, content: str) -> float:
        """Assess formatting quality of content."""
        score = 0.5  # Base score
        
        # Check for basic formatting elements
        if '\n\n' in content:  # Paragraphs
            score += 0.2
        
        if len(content.split('\n')) > 3:  # Multiple lines
            score += 0.1
        
        if len(content) > 100:  # Substantial content
            score += 0.1
        
        return min(1.0, score)