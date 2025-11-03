"""
Content Variations Manager

Handles creation and management of content variations for A/B testing.
Supports titles, thumbnails, scripts, and posting times.
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ContentType(Enum):
    """Types of content that can be varied in A/B tests."""
    TITLE = "title"
    THUMBNAIL = "thumbnail"
    SCRIPT = "script"
    POSTING_TIME = "posting_time"

class VariationStatus(Enum):
    """Status of content variations."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    WINNING = "winning"
    LOSING = "losing"

class ContentVariation:
    """Represents a single content variation."""
    
    def __init__(
        self,
        variation_id: str,
        content_type: ContentType,
        content: Union[str, Dict, List],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.variation_id = variation_id
        self.content_type = content_type
        self.content = content
        self.metadata = metadata or {}
        self.status = VariationStatus.DRAFT
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.metrics = {
            "impressions": 0,
            "clicks": 0,
            "engagement_rate": 0.0,
            "conversion_rate": 0.0,
            "revenue": 0.0
        }
    
    def update_metrics(self, metrics: Dict[str, float]):
        """Update performance metrics for this variation."""
        self.metrics.update(metrics)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert variation to dictionary."""
        return {
            "variation_id": self.variation_id,
            "content_type": self.content_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metrics": self.metrics
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentVariation':
        """Create variation from dictionary."""
        variation = cls(
            variation_id=data["variation_id"],
            content_type=ContentType(data["content_type"]),
            content=data["content"],
            metadata=data.get("metadata", {})
        )
        variation.status = VariationStatus(data["status"])
        variation.created_at = datetime.fromisoformat(data["created_at"])
        variation.updated_at = datetime.fromisoformat(data["updated_at"])
        variation.metrics = data["metrics"]
        return variation

class ContentVariationManager:
    """Manages content variations for A/B testing."""
    
    def __init__(self, storage_backend: Optional[Any] = None):
        """Initialize the variation manager."""
        self.variations: Dict[str, ContentVariation] = {}
        self.experiments: Dict[str, List[str]] = {}  # experiment_id -> variation_ids
        self.storage_backend = storage_backend
        self._load_existing_variations()
    
    def create_variation(
        self,
        content_type: ContentType,
        content: Union[str, Dict, List],
        experiment_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContentVariation:
        """Create a new content variation."""
        variation_id = str(uuid.uuid4())
        variation = ContentVariation(
            variation_id=variation_id,
            content_type=content_type,
            content=content,
            metadata=metadata
        )
        
        self.variations[variation_id] = variation
        
        if experiment_id not in self.experiments:
            self.experiments[experiment_id] = []
        self.experiments[experiment_id].append(variation_id)
        
        self._save_variation(variation)
        logger.info(f"Created variation {variation_id} for experiment {experiment_id}")
        
        return variation
    
    def get_variation(self, variation_id: str) -> Optional[ContentVariation]:
        """Get a variation by ID."""
        return self.variations.get(variation_id)
    
    def get_experiment_variations(self, experiment_id: str) -> List[ContentVariation]:
        """Get all variations for an experiment."""
        variation_ids = self.experiments.get(experiment_id, [])
        return [self.variations[vid] for vid in variation_ids if vid in self.variations]
    
    def update_variation_status(self, variation_id: str, status: VariationStatus):
        """Update the status of a variation."""
        if variation_id in self.variations:
            self.variations[variation_id].status = status
            self.variations[variation_id].updated_at = datetime.now()
            self._save_variation(self.variations[variation_id])
    
    def generate_title_variations(
        self,
        base_title: str,
        experiment_id: str,
        count: int = 3,
        style: str = "default"
    ) -> List[ContentVariation]:
        """Generate multiple title variations."""
        variations = []
        
        # Different title variation strategies
        strategies = {
            "emotional": self._generate_emotional_variations,
            "question": self._generate_question_variations,
            "how_to": self._generate_how_to_variations,
            "numbered": self._generate_numbered_variations,
            "default": self._generate_default_variations
        }
        
        strategy_func = strategies.get(style, strategies["default"])
        titles = strategy_func(base_title, count)
        
        for title in titles:
            variation = self.create_variation(
                content_type=ContentType.TITLE,
                content=title,
                experiment_id=experiment_id,
                metadata={"base_title": base_title, "style": style}
            )
            variations.append(variation)
        
        return variations
    
    def generate_thumbnail_variations(
        self,
        base_thumbnail_config: Dict[str, Any],
        experiment_id: str,
        count: int = 3
    ) -> List[ContentVariation]:
        """Generate thumbnail configuration variations."""
        variations = []
        
        # Generate different thumbnail styles
        styles = [
            "text_overlay",
            "colorful_background",
            "minimalist",
            "high_contrast",
            "bright_colors"
        ]
        
        for i, style in enumerate(styles[:count]):
            config = base_thumbnail_config.copy()
            config["style"] = style
            config["color_palette"] = self._get_color_palette(style)
            
            variation = self.create_variation(
                content_type=ContentType.THUMBNAIL,
                content=config,
                experiment_id=experiment_id,
                metadata={"base_config": base_thumbnail_config}
            )
            variations.append(variation)
        
        return variations
    
    def generate_script_variations(
        self,
        base_script: Dict[str, Any],
        experiment_id: str,
        count: int = 3
    ) -> List[ContentVariation]:
        """Generate script variations with different hooks, pacing, etc."""
        variations = []
        
        # Different script variation strategies
        strategies = [
            self._generate_fast_paced_script,
            self._generate_story_driven_script,
            self._generate_educational_script,
            self._generate_entertainment_script
        ]
        
        for i, strategy in enumerate(strategies[:count]):
            script = strategy(base_script)
            
            variation = self.create_variation(
                content_type=ContentType.SCRIPT,
                content=script,
                experiment_id=experiment_id,
                metadata={"base_script": base_script}
            )
            variations.append(variation)
        
        return variations
    
    def generate_posting_time_variations(
        self,
        base_time: datetime,
        experiment_id: str,
        count: int = 3,
        timezone: str = "UTC"
    ) -> List[ContentVariation]:
        """Generate different posting time variations."""
        variations = []
        
        # Generate times at different hours of the day
        target_hours = [9, 12, 15, 18, 21]  # Different posting times
        
        for i, hour in enumerate(target_hours[:count]):
            post_time = base_time.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            variation = self.create_variation(
                content_type=ContentType.POSTING_TIME,
                content=post_time.isoformat(),
                experiment_id=experiment_id,
                metadata={
                    "base_time": base_time.isoformat(),
                    "timezone": timezone,
                    "hour": hour
                }
            )
            variations.append(variation)
        
        return variations
    
    def delete_variation(self, variation_id: str) -> bool:
        """Delete a variation."""
        if variation_id in self.variations:
            variation = self.variations[variation_id]
            del self.variations[variation_id]
            
            # Remove from experiment
            for exp_id, var_ids in self.experiments.items():
                if variation_id in var_ids:
                    var_ids.remove(variation_id)
                    break
            
            self._delete_variation(variation_id)
            return True
        return False
    
    def get_all_variations(self) -> List[ContentVariation]:
        """Get all variations."""
        return list(self.variations.values())
    
    def _generate_emotional_variations(self, base_title: str, count: int) -> List[str]:
        """Generate emotionally charged title variations."""
        # Simple emotional keywords to add
        emotional_words = ["Amazing", "Incredible", "Shocking", "Unbelievable", "Mind-Blowing"]
        
        variations = []
        for i in range(count):
            if i < len(emotional_words):
                variations.append(f"{emotional_words[i]} {base_title}")
            else:
                variations.append(f"🔥 {base_title}")
        
        return variations
    
    def _generate_question_variations(self, base_title: str, count: int) -> List[str]:
        """Generate question-based title variations."""
        variations = [
            f"What if {base_title.lower()}?",
            f"Does {base_title.lower()} really work?",
            f"Why everyone should know about {base_title.lower()}?",
            f"How {base_title.lower()} changed everything?",
            f"Ready for {base_title.lower()}?"
        ]
        return variations[:count]
    
    def _generate_how_to_variations(self, base_title: str, count: int) -> List[str]:
        """Generate how-to style title variations."""
        variations = [
            f"How to Master {base_title}",
            f"Step-by-Step Guide to {base_title}",
            f"Learn {base_title} in 5 Minutes",
            f"Ultimate Guide: {base_title}",
            f"Everything You Need to Know About {base_title}"
        ]
        return variations[:count]
    
    def _generate_numbered_variations(self, base_title: str, count: int) -> List[str]:
        """Generate numbered title variations."""
        variations = [
            f"5 {base_title} You Should Know",
            f"Top 10 {base_title} Tips",
            f"3 Secrets About {base_title}",
            f"7 Ways to Improve {base_title}",
            f"The Ultimate {base_title} Guide"
        ]
        return variations[:count]
    
    def _generate_default_variations(self, base_title: str, count: int) -> List[str]:
        """Generate default title variations."""
        variations = []
        
        for i in range(count):
            if i == 0:
                variations.append(f"Pro: {base_title}")
            elif i == 1:
                variations.append(f"Essential {base_title}")
            else:
                variations.append(f"Advanced {base_title}")
        
        return variations
    
    def _get_color_palette(self, style: str) -> Dict[str, str]:
        """Get color palette for thumbnail style."""
        palettes = {
            "text_overlay": {"primary": "#FFFFFF", "secondary": "#000000", "accent": "#FF0000"},
            "colorful_background": {"primary": "#FF6B6B", "secondary": "#4ECDC4", "accent": "#45B7D1"},
            "minimalist": {"primary": "#F8F9FA", "secondary": "#212529", "accent": "#007BFF"},
            "high_contrast": {"primary": "#FFFFFF", "secondary": "#000000", "accent": "#FFFF00"},
            "bright_colors": {"primary": "#FF4500", "secondary": "#32CD32", "accent": "#FF1493"}
        }
        return palettes.get(style, palettes["colorful_background"])
    
    def _generate_fast_paced_script(self, base_script: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fast-paced script variation."""
        script = base_script.copy()
        if "hook" in script:
            script["hook"] = "Fast-paced intro with immediate value"
        if "pacing" in script:
            script["pacing"] = "rapid"
        return script
    
    def _generate_story_driven_script(self, base_script: Dict[str, Any]) -> Dict[str, Any]:
        """Generate story-driven script variation."""
        script = base_script.copy()
        if "hook" in script:
            script["hook"] = "Story-driven opening with narrative hook"
        if "structure" in script:
            script["structure"] = "storytelling"
        return script
    
    def _generate_educational_script(self, base_script: Dict[str, Any]) -> Dict[str, Any]:
        """Generate educational script variation."""
        script = base_script.copy()
        if "hook" in script:
            script["hook"] = "Educational intro with learning promise"
        if "style" in script:
            script["style"] = "educational"
        return script
    
    def _generate_entertainment_script(self, base_script: Dict[str, Any]) -> Dict[str, Any]:
        """Generate entertainment-focused script variation."""
        script = base_script.copy()
        if "hook" in script:
            script["hook"] = "Entertainment-focused opening with humor"
        if "style" in script:
            script["style"] = "entertainment"
        return script
    
    def _save_variation(self, variation: ContentVariation):
        """Save variation to storage backend."""
        if self.storage_backend:
            # Implementation depends on storage backend
            pass
        # For now, just log
        logger.debug(f"Saved variation {variation.variation_id}")
    
    def _delete_variation(self, variation_id: str):
        """Delete variation from storage backend."""
        if self.storage_backend:
            # Implementation depends on storage backend
            pass
        # For now, just log
        logger.debug(f"Deleted variation {variation_id}")
    
    def _load_existing_variations(self):
        """Load existing variations from storage."""
        # Implementation for loading from storage backend
        logger.debug("Loading existing variations")
