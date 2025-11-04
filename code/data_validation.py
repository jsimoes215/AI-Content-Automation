"""
Data Validation and Transformation Pipeline for Video Idea Data

This module provides comprehensive data validation, cleaning, and transformation
capabilities for video idea data sourced from Google Sheets. It implements:

1. Schema validation for video idea data
2. Data cleaning and normalization
3. Duplicate detection and handling
4. Cost estimation for ideas
5. Quality scoring for content ideas

Author: AI Content Automation System
Version: 1.0.0
"""

import re
import json
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import numpy as np
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of data validation process"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    cleaned_data: Optional[Dict[str, Any]] = None
    quality_score: float = 0.0
    estimated_cost: Decimal = Decimal('0.00')
    duplicate_score: float = 0.0


@dataclass
class VideoIdeaSchema:
    """Schema definition for video idea data"""
    required_fields: Set[str] = field(default_factory=lambda: {
        'title', 'description', 'target_audience'
    })
    
    optional_fields: Set[str] = field(default_factory=lambda: {
        'tags', 'tone', 'duration_estimate', 'platform', 'style',
        'voice_type', 'visual_elements', 'call_to_action', 'keywords',
        'competitor_analysis', 'script_type', 'demo_required',
        'brand_guidelines', 'compliance_notes'
    })
    
    field_validators: Dict[str, callable] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize field validators"""
        self.field_validators = {
            'title': self._validate_title,
            'description': self._validate_description,
            'target_audience': self._validate_target_audience,
            'tags': self._validate_tags,
            'tone': self._validate_tone,
            'duration_estimate': self._validate_duration,
            'platform': self._validate_platform,
            'script_type': self._validate_script_type,
        }
    
    @staticmethod
    def _validate_title(title: str) -> Tuple[bool, str]:
        """Validate video title"""
        if not title or not isinstance(title, str):
            return False, "Title is required and must be a string"
        
        title = title.strip()
        if len(title) < 5:
            return False, "Title must be at least 5 characters long"
        if len(title) > 100:
            return False, "Title must not exceed 100 characters"
        if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', title):
            return False, "Title contains invalid characters"
        return True, ""
    
    @staticmethod
    def _validate_description(description: str) -> Tuple[bool, str]:
        """Validate video description"""
        if not description or not isinstance(description, str):
            return False, "Description is required and must be a string"
        
        desc = description.strip()
        if len(desc) < 20:
            return False, "Description must be at least 20 characters long"
        if len(desc) > 2000:
            return False, "Description must not exceed 2000 characters"
        return True, ""
    
    @staticmethod
    def _validate_target_audience(audience: str) -> Tuple[bool, str]:
        """Validate target audience"""
        valid_audiences = {
            'general', 'professionals', 'students', 'entrepreneurs', 
            'parents', 'seniors', 'teenagers', 'children', 'experts',
            'beginners', 'tech-savvy', 'casual users', 'businesses'
        }
        
        if not audience or not isinstance(audience, str):
            return False, "Target audience is required"
        
        audience_lower = audience.lower().strip()
        if audience_lower not in valid_audiences:
            return False, f"Target audience must be one of: {', '.join(valid_audiences)}"
        return True, ""
    
    @staticmethod
    def _validate_tags(tags: Any) -> Tuple[bool, str]:
        """Validate tags"""
        if tags is None:
            return True, ""
        
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]
        elif isinstance(tags, list):
            tags = [str(t).strip() for t in tags]
        else:
            return False, "Tags must be a string (comma-separated) or list"
        
        if len(tags) > 10:
            return False, "Maximum 10 tags allowed"
        
        for tag in tags:
            if len(tag) > 30:
                return False, f"Tag '{tag}' exceeds 30 character limit"
        return True, ""
    
    @staticmethod
    def _validate_tone(tone: str) -> Tuple[bool, str]:
        """Validate tone"""
        valid_tones = {
            'professional', 'casual', 'educational', 'entertaining',
            'motivational', 'humorous', 'serious', 'friendly', 'authoritative'
        }
        
        if not tone or not isinstance(tone, str):
            return True, ""
        
        tone_lower = tone.lower().strip()
        if tone_lower not in valid_tones:
            return False, f"Tone must be one of: {', '.join(valid_tones)}"
        return True, ""
    
    @staticmethod
    def _validate_duration(duration: Any) -> Tuple[bool, str]:
        """Validate duration estimate"""
        if duration is None:
            return True, ""
        
        try:
            normalized_duration = DataCleaner.normalize_duration(duration)
            if normalized_duration is None:
                return False, "Invalid duration format"
            
            if normalized_duration < 15:
                return False, "Duration must be at least 15 seconds"
            if normalized_duration > 3600:
                return False, "Duration must not exceed 60 minutes"
            return True, ""
        except (ValueError, TypeError):
            return False, "Duration must be a number or valid time string"
    
    @staticmethod
    def _validate_platform(platform: str) -> Tuple[bool, str]:
        """Validate platform"""
        valid_platforms = {
            'youtube', 'tiktok', 'instagram', 'linkedin', 'twitter',
            'facebook', 'universal', 'multi-platform'
        }
        
        if not platform or not isinstance(platform, str):
            return True, ""
        
        platform_lower = platform.lower().strip()
        if platform_lower not in valid_platforms:
            return False, f"Platform must be one of: {', '.join(valid_platforms)}"
        return True, ""
    
    @staticmethod
    def _validate_script_type(script_type: str) -> Tuple[bool, str]:
        """Validate script type"""
        valid_types = {
            'explainer', 'tutorial', 'story', 'demo', 'testimonial',
            'interview', 'presentation', 'review', 'comparison'
        }
        
        if not script_type or not isinstance(script_type, str):
            return True, ""
        
        script_lower = script_type.lower().strip()
        if script_lower not in valid_types:
            return False, f"Script type must be one of: {', '.join(valid_types)}"
        return True, ""


class DataCleaner:
    """Handles data cleaning and normalization"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text by removing extra whitespace and special characters"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters except common ones
        text = re.sub(r'[^\w\s\-_\.,!?@#$%&*()+=\[\]{}|\\:";\'<>]', '', text)
        
        return text
    
    @staticmethod
    def normalize_list_field(value: Any) -> List[str]:
        """Normalize list fields (tags, keywords, etc.)"""
        if not value:
            return []
        
        if isinstance(value, str):
            items = [item.strip().lower() for item in value.split(',')]
        elif isinstance(value, list):
            items = [str(item).strip().lower() for item in value]
        else:
            return []
        
        # Remove duplicates and empty items
        return list(dict.fromkeys([item for item in items if item]))
    
    @staticmethod
    def normalize_duration(duration: Any) -> Optional[int]:
        """Normalize duration to seconds"""
        if not duration:
            return None
        
        try:
            if isinstance(duration, str):
                # Handle various time formats
                duration = duration.lower().strip()
                
                # Extract numbers
                numbers = re.findall(r'\d+', duration)
                if not numbers:
                    return None
                
                value = int(numbers[0])
                
                # Determine unit
                if 'min' in duration or 'minute' in duration:
                    return value * 60
                elif 'hour' in duration or 'hr' in duration:
                    return value * 3600
                elif 'sec' in duration or 's' in duration:
                    return value
                else:
                    # Assume seconds if no unit specified
                    return value
            else:
                return int(duration)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove potentially dangerous HTML/JS from text"""
        if not text:
            return ""
        
        # Remove script tags and javascript
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
        
        # Remove other potentially dangerous elements
        text = re.sub(r'<[^>]+>', '', text)
        
        return text.strip()


class DuplicateDetector:
    """Detects and handles duplicate content"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.content_cache: Dict[str, float] = {}
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using multiple metrics"""
        if not text1 or not text2:
            return 0.0
        
        # Normalize texts
        text1 = DataCleaner.normalize_text(text1.lower())
        text2 = DataCleaner.normalize_text(text2.lower())
        
        # Jaccard similarity for word sets
        words1 = set(text1.split())
        words2 = set(text2.split())
        jaccard = len(words1 & words2) / len(words1 | words2) if words1 | words2 else 0
        
        # Character-level similarity
        char_similarity = self._char_ngram_similarity(text1, text2, 3)
        
        # Combined similarity score
        return (jaccard * 0.6 + char_similarity * 0.4)
    
    def _char_ngram_similarity(self, text1: str, text2: str, n: int = 3) -> float:
        """Calculate character n-gram similarity"""
        def get_ngrams(text, n):
            return set(text[i:i+n] for i in range(len(text) - n + 1))
        
        ngrams1 = get_ngrams(text1, n)
        ngrams2 = get_ngrams(text2, n)
        
        if not ngrams1 and not ngrams2:
            return 1.0
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)
        
        return intersection / union if union > 0 else 0.0
    
    def generate_content_hash(self, data: Dict[str, Any]) -> str:
        """Generate a hash for content deduplication"""
        # Use key fields for hash generation
        hash_input = {
            'title': data.get('title', '').lower().strip(),
            'description': data.get('description', '').lower().strip(),
            'target_audience': data.get('target_audience', '').lower().strip(),
            'script_type': data.get('script_type', '').lower().strip(),
        }
        
        # Add normalized tags if present
        tags = data.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip().lower() for t in tags.split(',')]
        elif isinstance(tags, list):
            tags = [str(t).strip().lower() for t in tags]
        
        hash_input['tags'] = sorted(tags)
        
        # Generate hash
        hash_string = json.dumps(hash_input, sort_keys=True)
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def is_duplicate(self, new_data: Dict[str, Any], existing_data: List[Dict[str, Any]]) -> Tuple[bool, float]:
        """Check if new data is duplicate of existing data"""
        new_hash = self.generate_content_hash(new_data)
        
        best_similarity = 0.0
        for existing in existing_data:
            existing_hash = self.generate_content_hash(existing)
            
            if new_hash == existing_hash:
                return True, 1.0
            
            # Check title similarity
            title_sim = self.calculate_similarity(
                new_data.get('title', ''),
                existing.get('title', '')
            )
            
            if title_sim > best_similarity:
                best_similarity = title_sim
        
        return best_similarity >= self.similarity_threshold, best_similarity


class CostEstimator:
    """Estimates production costs for video ideas"""
    
    def __init__(self):
        # Cost per minute by script type (in USD)
        self.cost_per_minute = {
            'explainer': Decimal('25.00'),
            'tutorial': Decimal('30.00'),
            'story': Decimal('20.00'),
            'demo': Decimal('40.00'),
            'testimonial': Decimal('25.00'),
            'interview': Decimal('35.00'),
            'presentation': Decimal('30.00'),
            'review': Decimal('25.00'),
            'comparison': Decimal('30.00'),
        }
        
        # Platform complexity multipliers
        self.platform_multipliers = {
            'universal': Decimal('1.0'),
            'multi-platform': Decimal('1.2'),
            'youtube': Decimal('1.0'),
            'tiktok': Decimal('0.9'),
            'instagram': Decimal('1.0'),
            'linkedin': Decimal('1.1'),
            'twitter': Decimal('0.8'),
            'facebook': Decimal('0.9'),
        }
        
        # Complexity adders
        self.complexity_adders = {
            'demo_required': Decimal('50.00'),
            'brand_guidelines': Decimal('25.00'),
            'compliance_notes': Decimal('30.00'),
        }
    
    def estimate_cost(self, idea_data: Dict[str, Any]) -> Decimal:
        """Estimate total production cost for a video idea"""
        # Get base duration
        duration = idea_data.get('duration_estimate', 60)  # Default 60 seconds
        if isinstance(duration, str):
            duration = DataCleaner.normalize_duration(duration) or 60
        duration = max(15, int(duration))  # Minimum 15 seconds
        duration_minutes = Decimal(duration) / Decimal('60')
        
        # Get script type cost
        script_type = idea_data.get('script_type', 'explainer').lower()
        base_cost_per_min = self.cost_per_minute.get(script_type, self.cost_per_minute['explainer'])
        
        # Calculate base cost
        base_cost = duration_minutes * base_cost_per_min
        
        # Apply platform multiplier
        platform = idea_data.get('platform', 'universal').lower()
        platform_mult = self.platform_multipliers.get(platform, self.platform_multipliers['universal'])
        
        # Calculate complexity adders
        complexity_cost = Decimal('0.00')
        for complexity, cost in self.complexity_adders.items():
            if idea_data.get(complexity, False):
                complexity_cost += cost
        
        # Total estimated cost
        total_cost = (base_cost * platform_mult) + complexity_cost
        
        # Add contingency (10% for production variations)
        total_cost = total_cost * Decimal('1.10')
        
        return total_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class QualityScorer:
    """Scores quality of video ideas"""
    
    def __init__(self):
        self.weights = {
            'completeness': 0.25,
            'clarity': 0.20,
            'engagement': 0.20,
            'feasibility': 0.15,
            'uniqueness': 0.20
        }
    
    def score_idea(self, idea_data: Dict[str, Any], existing_ideas: List[Dict[str, Any]] = None) -> float:
        """Calculate quality score for a video idea (0-10)"""
        scores = {}
        
        # Completeness score
        scores['completeness'] = self._score_completeness(idea_data)
        
        # Clarity score
        scores['clarity'] = self._score_clarity(idea_data)
        
        # Engagement score
        scores['engagement'] = self._score_engagement(idea_data)
        
        # Feasibility score
        scores['feasibility'] = self._score_feasibility(idea_data)
        
        # Uniqueness score
        if existing_ideas:
            scores['uniqueness'] = self._score_uniqueness(idea_data, existing_ideas)
        else:
            scores['uniqueness'] = 5.0  # Neutral score if no existing data
        
        # Calculate weighted average
        total_score = sum(
            score * self.weights[category] 
            for category, score in scores.items()
        )
        
        return round(total_score, 1)
    
    def _score_completeness(self, idea_data: Dict[str, Any]) -> float:
        """Score based on data completeness"""
        required_fields = {'title', 'description', 'target_audience'}
        optional_fields = {
            'tags', 'tone', 'duration_estimate', 'platform', 'script_type'
        }
        
        # Check required fields
        missing_required = len(required_fields - set(idea_data.keys()))
        required_score = max(0, 1 - (missing_required / len(required_fields)))
        
        # Check optional fields
        present_optional = sum(1 for field in optional_fields if idea_data.get(field))
        optional_score = present_optional / len(optional_fields)
        
        return (required_score * 0.7 + optional_score * 0.3) * 10
    
    def _score_clarity(self, idea_data: Dict[str, Any]) -> float:
        """Score based on content clarity"""
        title = idea_data.get('title', '')
        description = idea_data.get('description', '')
        
        # Title clarity
        title_score = min(10, len(title) / 5)  # Optimal length around 50 chars
        
        # Description clarity
        desc_words = len(description.split())
        desc_score = min(10, desc_words / 20) * 10  # Optimal around 200 words
        
        # Target audience specificity
        audience = idea_data.get('target_audience', '')
        audience_score = 10 if audience in ['professionals', 'entrepreneurs', 'parents', 'students'] else 5
        
        return (title_score * 0.3 + desc_score * 0.5 + audience_score * 0.2)
    
    def _score_engagement(self, idea_data: Dict[str, Any]) -> float:
        """Score based on engagement potential"""
        score = 5.0  # Base score
        
        # Tone analysis
        tone = idea_data.get('tone', '').lower()
        if tone in ['humorous', 'entertaining', 'motivational']:
            score += 2.0
        
        # Call to action present
        if idea_data.get('call_to_action'):
            score += 1.5
        
        # Tags presence
        tags = idea_data.get('tags', [])
        if tags:
            score += 1.0
        
        # Platform optimization
        platform = idea_data.get('platform', '').lower()
        if platform in ['tiktok', 'instagram', 'youtube']:
            score += 0.5
        
        return min(10, score)
    
    def _score_feasibility(self, idea_data: Dict[str, Any]) -> float:
        """Score based on production feasibility"""
        score = 7.0  # Base score
        
        duration = idea_data.get('duration_estimate', 60)
        if isinstance(duration, str):
            duration = DataCleaner.normalize_duration(duration) or 60
        
        # Duration feasibility
        if 30 <= int(duration) <= 300:  # 5-5 minutes
            score += 2.0
        elif int(duration) < 15 or int(duration) > 600:
            score -= 3.0
        
        # Demo requirements
        if idea_data.get('demo_required', False):
            score -= 1.0
        
        # Script type complexity
        script_type = idea_data.get('script_type', '').lower()
        if script_type in ['interview', 'demo', 'comparison']:
            score += 1.0
        elif script_type in ['story', 'presentation']:
            score -= 0.5
        
        return max(0, min(10, score))
    
    def _score_uniqueness(self, idea_data: Dict[str, Any], existing_ideas: List[Dict[str, Any]]) -> float:
        """Score based on uniqueness compared to existing ideas"""
        detector = DuplicateDetector()
        
        max_similarity = 0.0
        for existing in existing_ideas:
            similarity = detector.calculate_similarity(
                idea_data.get('title', ''),
                existing.get('title', '')
            )
            max_similarity = max(max_similarity, similarity)
        
        # Higher uniqueness score for lower similarity
        uniqueness_score = (1 - max_similarity) * 10
        return uniqueness_score


class DataValidationPipeline:
    """Main data validation and transformation pipeline"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.schema = VideoIdeaSchema()
        self.cleaner = DataCleaner()
        self.duplicate_detector = DuplicateDetector(similarity_threshold)
        self.cost_estimator = CostEstimator()
        self.quality_scorer = QualityScorer()
        
        # Cache for duplicate detection
        self.existing_ideas: List[Dict[str, Any]] = []
    
    def validate_idea(self, idea_data: Dict[str, Any]) -> ValidationResult:
        """Validate a single video idea"""
        errors = []
        warnings = []
        cleaned_data = idea_data.copy()
        
        # 1. Schema validation
        field_errors = self._validate_schema(cleaned_data)
        errors.extend(field_errors)
        
        # 2. Data cleaning and normalization
        cleaned_data = self._clean_data(cleaned_data)
        
        # 3. Duplicate detection
        is_duplicate, duplicate_score = self.duplicate_detector.is_duplicate(
            cleaned_data, self.existing_ideas
        )
        
        if is_duplicate:
            warnings.append(f"Potential duplicate detected (similarity: {duplicate_score:.2f})")
        
        # 4. Quality scoring
        quality_score = self.quality_scorer.score_idea(cleaned_data, self.existing_ideas)
        
        # 5. Cost estimation
        estimated_cost = self.cost_estimator.estimate_cost(cleaned_data)
        
        # Final validation result
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            cleaned_data=cleaned_data,
            quality_score=quality_score,
            estimated_cost=estimated_cost,
            duplicate_score=duplicate_score
        )
    
    def validate_batch(self, ideas_data: List[Dict[str, Any]]) -> List[ValidationResult]:
        """Validate a batch of video ideas"""
        results = []
        
        # Update existing ideas cache for duplicate detection
        self.existing_ideas = ideas_data[:-1] if len(ideas_data) > 1 else []
        
        for i, idea_data in enumerate(ideas_data):
            try:
                result = self.validate_idea(idea_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Error validating idea at index {i}: {str(e)}")
                results.append(ValidationResult(
                    is_valid=False,
                    errors=[f"Validation error: {str(e)}"]
                ))
        
        return results
    
    def _validate_schema(self, data: Dict[str, Any]) -> List[str]:
        """Validate data against schema"""
        errors = []
        
        # Check required fields
        missing_required = self.schema.required_fields - set(data.keys())
        if missing_required:
            errors.append(f"Missing required fields: {', '.join(missing_required)}")
        
        # Validate individual fields
        for field, validator in self.schema.field_validators.items():
            if field in data and data[field] is not None:
                is_valid, error_msg = validator(data[field])
                if not is_valid:
                    errors.append(f"{field}: {error_msg}")
        
        return errors
    
    def _clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize data"""
        cleaned = {}
        
        for key, value in data.items():
            if value is None:
                cleaned[key] = None
                continue
            
            # Apply appropriate cleaning based on field type
            if key in ['title', 'description', 'target_audience', 'tone', 'platform', 'script_type']:
                cleaned[key] = self.cleaner.normalize_text(str(value))
            elif key in ['tags', 'keywords']:
                cleaned[key] = self.cleaner.normalize_list_field(value)
            elif key in ['duration_estimate']:
                cleaned[key] = self.cleaner.normalize_duration(value)
            else:
                # Generic cleaning for other fields
                if isinstance(value, str):
                    cleaned[key] = self.cleaner.normalize_text(value)
                else:
                    cleaned[key] = value
        
        return cleaned
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Get summary statistics for validation results"""
        if not results:
            return {}
        
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        invalid = total - valid
        
        avg_quality = sum(r.quality_score for r in results) / total
        total_cost = sum(r.estimated_cost for r in results)
        avg_cost = total_cost / total
        
        duplicate_count = sum(1 for r in results if r.duplicate_score > 0.85)
        
        # Collect all errors and warnings
        all_errors = []
        all_warnings = []
        for r in results:
            all_errors.extend(r.errors)
            all_warnings.extend(r.warnings)
        
        # Error frequency analysis
        error_counts = defaultdict(int)
        for error in all_errors:
            error_type = error.split(':')[0] if ':' in error else error
            error_counts[error_type] += 1
        
        return {
            'total_ideas': total,
            'valid_ideas': valid,
            'invalid_ideas': invalid,
            'validation_rate': valid / total if total > 0 else 0,
            'average_quality_score': round(avg_quality, 2),
            'total_estimated_cost': float(total_cost),
            'average_estimated_cost': round(float(avg_cost), 2),
            'duplicate_count': duplicate_count,
            'unique_ideas': total - duplicate_count,
            'error_summary': dict(error_counts),
            'common_warnings': list(set(all_warnings))
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize pipeline
    pipeline = DataValidationPipeline()
    
    # Sample data
    sample_ideas = [
        {
            "title": "How to Build a Successful Online Business",
            "description": "Learn the essential steps to create and grow your online business from scratch. This comprehensive guide covers market research, business planning, digital marketing strategies, and scaling techniques.",
            "target_audience": "entrepreneurs",
            "tags": "business, online, entrepreneurship, marketing",
            "tone": "educational",
            "duration_estimate": "5 minutes",
            "platform": "youtube",
            "script_type": "tutorial",
            "call_to_action": "Subscribe for more business tips"
        },
        {
            "title": "Quick Business Tips",
            "description": "Learn essential steps to create and grow your online business from scratch. This comprehensive guide covers market research, business planning, digital marketing strategies, and scaling techniques.",
            "target_audience": "entrepreneurs",
            "tags": "business, online, entrepreneurship",
            "tone": "educational",
            "platform": "youtube",
            "script_type": "tutorial"
        }
    ]
    
    # Validate batch
    results = pipeline.validate_batch(sample_ideas)
    
    # Print results
    for i, result in enumerate(results):
        print(f"\n=== Idea {i+1} ===")
        print(f"Valid: {result.is_valid}")
        print(f"Quality Score: {result.quality_score}/10")
        print(f"Estimated Cost: ${result.estimated_cost}")
        print(f"Duplicate Score: {result.duplicate_score}")
        if result.errors:
            print(f"Errors: {result.errors}")
        if result.warnings:
            print(f"Warnings: {result.warnings}")
    
    # Get summary
    summary = pipeline.get_validation_summary(results)
    print(f"\n=== Summary ===")
    for key, value in summary.items():
        print(f"{key}: {value}")
