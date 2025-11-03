"""
Data model for content improvement recommendations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from enum import Enum
import uuid


class RecommendationType(Enum):
    """Types of recommendations."""
    CONTENT_OPTIMIZATION = "content_optimization"
    CONTENT_TONE = "content_tone"
    ENGAGEMENT_STRATEGY = "engagement_strategy"
    STRATEGY_OPTIMIZATION = "strategy_optimization"
    QUALITY_IMPROVEMENT = "quality_improvement"
    PERFORMANCE_BOOST = "performance_boost"
    AUDIENCE_TARGETING = "audience_targeting"
    PLATFORM_SPECIFIC = "platform_specific"
    TIMING_OPTIMIZATION = "timing_optimization"


class Priority(Enum):
    """Priority levels for recommendations."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ContentType(Enum):
    """Content types that can be recommended for improvement."""
    SCRIPT = "script"
    THUMBNAIL = "thumbnail"
    TITLE = "title"
    DESCRIPTION = "description"
    HASHTAGS = "hashtags"
    STRUCTURE = "structure"
    TONE = "tone"
    CALL_TO_ACTION = "call_to_action"
    VISUALS = "visuals"
    AUDIO = "audio"
    PACING = "pacing"


class ImplementationStatus(Enum):
    """Implementation status tracking."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"


@dataclass
class Recommendation:
    """
    Comprehensive recommendation for content improvement.
    """
    # Core identification
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    
    # Classification
    recommendation_type: RecommendationType = RecommendationType.CONTENT_OPTIMIZATION
    priority: Priority = Priority.MEDIUM
    impact_score: float = 0.0  # 0.0 to 1.0
    
    # Targeting
    target_content_types: List[ContentType] = field(default_factory=list)
    target_platforms: List[str] = field(default_factory=list)
    target_audience_segments: List[str] = field(default_factory=list)
    
    # Action items and guidance
    action_items: List[str] = field(default_factory=list)
    implementation_steps: List[Dict[str, Any]] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    expected_outcome: str = ""
    
    # Resources and estimates
    implementation_difficulty: str = "Medium"  # "Low", "Medium", "High", "Very High"
    estimated_time_hours: float = 0.0
    required_resources: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    # Context and data
    analysis_basis: str = ""  # What analysis led to this recommendation
    related_feedback_ids: List[str] = field(default_factory=list)
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    
    # Tracking
    created_date: datetime = field(default_factory=datetime.now)
    implementation_status: ImplementationStatus = ImplementationStatus.PENDING
    implementation_start_date: Optional[datetime] = None
    implementation_end_date: Optional[datetime] = None
    completion_percentage: float = 0.0
    
    # Results and validation
    results: Dict[str, Any] = field(default_factory=dict)
    validation_metrics: Dict[str, float] = field(default_factory=dict)
    lessons_learned: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate and set defaults after initialization."""
        if not self.title:
            raise ValueError("title is required for recommendation")
        if not self.description:
            raise ValueError("description is required for recommendation")
        if not 0.0 <= self.impact_score <= 1.0:
            raise ValueError("impact_score must be between 0.0 and 1.0")
    
    def get_priority_score(self) -> float:
        """Get numerical priority score for sorting."""
        priority_scores = {
            Priority.HIGH: 3.0,
            Priority.MEDIUM: 2.0,
            Priority.LOW: 1.0
        }
        return priority_scores[self.priority]
    
    def get_effectiveness_score(self) -> float:
        """Calculate effectiveness score based on impact and priority."""
        priority_weight = self.get_priority_score() / 3.0
        return (self.impact_score * 0.7) + (priority_weight * 0.3)
    
    def is_high_impact(self) -> bool:
        """Check if recommendation is high impact."""
        return self.impact_score >= 0.8
    
    def is_immediate_action(self) -> bool:
        """Check if recommendation requires immediate action."""
        return self.priority == Priority.HIGH or self.impact_score >= 0.9
    
    def get_implementation_complexity(self) -> str:
        """Get implementation complexity level."""
        if self.estimated_time_hours <= 2:
            return "Low"
        elif self.estimated_time_hours <= 6:
            return "Medium"
        elif self.estimated_time_hours <= 15:
            return "High"
        else:
            return "Very High"
    
    def add_action_item(self, action: str) -> None:
        """Add a new action item."""
        if action not in self.action_items:
            self.action_items.append(action)
    
    def add_success_criterion(self, criterion: str) -> None:
        """Add a success criterion."""
        if criterion not in self.success_criteria:
            self.success_criteria.append(criterion)
    
    def mark_in_progress(self) -> None:
        """Mark recommendation as in progress."""
        self.implementation_status = ImplementationStatus.IN_PROGRESS
        if not self.implementation_start_date:
            self.implementation_start_date = datetime.now()
    
    def mark_completed(self, results: Optional[Dict[str, Any]] = None) -> None:
        """Mark recommendation as completed."""
        self.implementation_status = ImplementationStatus.COMPLETED
        self.completion_percentage = 100.0
        self.implementation_end_date = datetime.now()
        if results:
            self.results.update(results)
    
    def update_progress(self, percentage: float) -> None:
        """Update implementation progress."""
        self.completion_percentage = max(0.0, min(100.0, percentage))
        
        if self.completion_percentage > 0 and self.implementation_status == ImplementationStatus.PENDING:
            self.mark_in_progress()
        elif self.completion_percentage >= 100.0 and self.implementation_status != ImplementationStatus.COMPLETED:
            self.mark_completed()
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get current status summary."""
        return {
            'status': self.implementation_status.value,
            'progress': self.completion_percentage,
            'days_since_created': (datetime.now() - self.created_date).days,
            'estimated_hours': self.estimated_time_hours,
            'complexity': self.get_implementation_complexity(),
            'is_high_impact': self.is_high_impact(),
            'is_immediate': self.is_immediate_action()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'recommendation_type': self.recommendation_type.value,
            'priority': self.priority.value,
            'impact_score': self.impact_score,
            'target_content_types': [ct.value for ct in self.target_content_types],
            'target_platforms': self.target_platforms,
            'target_audience_segments': self.target_audience_segments,
            'action_items': self.action_items,
            'implementation_steps': self.implementation_steps,
            'success_criteria': self.success_criteria,
            'expected_outcome': self.expected_outcome,
            'implementation_difficulty': self.implementation_difficulty,
            'estimated_time_hours': self.estimated_time_hours,
            'required_resources': self.required_resources,
            'dependencies': self.dependencies,
            'analysis_basis': self.analysis_basis,
            'related_feedback_ids': self.related_feedback_ids,
            'supporting_data': self.supporting_data,
            'created_date': self.created_date.isoformat() if isinstance(self.created_date, datetime) else self.created_date,
            'implementation_status': self.implementation_status.value,
            'implementation_start_date': self.implementation_start_date.isoformat() if self.implementation_start_date else None,
            'implementation_end_date': self.implementation_end_date.isoformat() if self.implementation_end_date else None,
            'completion_percentage': self.completion_percentage,
            'results': self.results,
            'validation_metrics': self.validation_metrics,
            'lessons_learned': self.lessons_learned
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Recommendation':
        """Create Recommendation from dictionary."""
        # Convert enum fields
        if 'recommendation_type' in data and isinstance(data['recommendation_type'], str):
            data['recommendation_type'] = RecommendationType(data['recommendation_type'])
        
        if 'priority' in data and isinstance(data['priority'], str):
            data['priority'] = Priority(data['priority'])
        
        if 'implementation_status' in data and isinstance(data['implementation_status'], str):
            data['implementation_status'] = ImplementationStatus(data['implementation_status'])
        
        if 'target_content_types' in data:
            data['target_content_types'] = [ContentType(ct) for ct in data['target_content_types']]
        
        # Convert datetime fields
        for date_field in ['created_date', 'implementation_start_date', 'implementation_end_date']:
            if date_field in data and isinstance(data[date_field], str):
                data[date_field] = datetime.fromisoformat(data[date_field])
        
        return cls(**data)
    
    def generate_implementation_plan(self) -> Dict[str, Any]:
        """Generate detailed implementation plan."""
        return {
            'overview': {
                'title': self.title,
                'priority': self.priority.value,
                'estimated_time': f"{self.estimated_time_hours} hours",
                'complexity': self.get_implementation_complexity()
            },
            'phases': self._generate_implementation_phases(),
            'action_items': self.action_items,
            'success_criteria': self.success_criteria,
            'resource_requirements': self.required_resources,
            'expected_outcome': self.expected_outcome,
            'timeline': self._generate_timeline()
        }
    
    def _generate_implementation_phases(self) -> List[Dict[str, Any]]:
        """Generate implementation phases based on action items."""
        phases = []
        
        if len(self.action_items) <= 3:
            # Simple implementation
            phases.append({
                'phase': 'Implementation',
                'duration_hours': self.estimated_time_hours,
                'tasks': self.action_items,
                'deliverables': [self.expected_outcome]
            })
        else:
            # Phased implementation
            phase_size = max(1, len(self.action_items) // 3)
            
            phases.extend([
                {
                    'phase': 'Planning & Preparation',
                    'duration_hours': self.estimated_time_hours * 0.2,
                    'tasks': self.action_items[:phase_size],
                    'deliverables': ['Implementation plan', 'Resource allocation']
                },
                {
                    'phase': 'Core Implementation',
                    'duration_hours': self.estimated_time_hours * 0.6,
                    'tasks': self.action_items[phase_size:phase_size*2],
                    'deliverables': [f'{self.title} implementation']
                },
                {
                    'phase': 'Testing & Validation',
                    'duration_hours': self.estimated_time_hours * 0.2,
                    'tasks': self.action_items[phase_size*2:],
                    'deliverables': ['Validated implementation', 'Success metrics']
                }
            ])
        
        return phases
    
    def _generate_timeline(self) -> Dict[str, Any]:
        """Generate implementation timeline."""
        start_date = self.implementation_start_date or datetime.now()
        
        if self.implementation_status == ImplementationStatus.COMPLETED:
            duration_days = (self.implementation_end_date - start_date).days if self.implementation_end_date else 0
        else:
            estimated_hours_per_day = 4  # Assuming 4 hours per day
            duration_days = max(1, int(self.estimated_time_hours / estimated_hours_per_day))
        
        return {
            'start_date': start_date.isoformat(),
            'estimated_duration_days': duration_days,
            'milestones': [
                {
                    'name': 'Planning Complete',
                    'day': max(1, duration_days // 4),
                    'completion_percentage': 25
                },
                {
                    'name': 'Core Implementation',
                    'day': max(1, duration_days // 2),
                    'completion_percentage': 60
                },
                {
                    'name': 'Testing & Validation',
                    'day': max(1, (duration_days * 3) // 4),
                    'completion_percentage': 85
                },
                {
                    'name': 'Implementation Complete',
                    'day': duration_days,
                    'completion_percentage': 100
                }
            ]
        }