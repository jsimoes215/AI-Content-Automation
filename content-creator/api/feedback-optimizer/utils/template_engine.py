"""
Template Engine Utility Module

Provides template-based generation and formatting for recommendations and reports.
"""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from string import Template
from dataclasses import asdict

from ..models.recommendation import Recommendation
from ..models.feedback_data import FeedbackData


class TemplateEngine:
    """
    Template engine for generating structured reports and recommendations.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the template engine."""
        self.config = config or self._default_config()
        self.templates = self._load_templates()
        
    def _default_config(self) -> Dict:
        """Default configuration for template engine."""
        return {
            'default_date_format': '%Y-%m-%d %H:%M:%S',
            'timezone': 'UTC',
            'template_variables': {
                'company_name': 'Content Creator',
                'app_name': 'Feedback Optimizer'
            }
        }
    
    def generate_improvement_report(self, analysis_results: Dict[str, Any], recommendations: List[Recommendation]) -> Dict[str, Any]:
        """
        Generate comprehensive improvement report.
        
        Args:
            analysis_results: Results from feedback analyzer
            recommendations: List of recommendations to include
            
        Returns:
            Structured improvement report
        """
        report = {
            'report_metadata': self._generate_report_metadata(),
            'executive_summary': self._generate_executive_summary(analysis_results, recommendations),
            'analysis_overview': self._generate_analysis_overview(analysis_results),
            'recommendations_summary': self._generate_recommendations_summary(recommendations),
            'detailed_recommendations': self._generate_detailed_recommendations(recommendations),
            'implementation_roadmap': self._generate_implementation_roadmap(recommendations),
            'success_metrics': self._define_success_metrics(recommendations),
            'next_steps': self._generate_next_steps(recommendations)
        }
        
        return report
    
    def format_recommendation_card(self, recommendation: Recommendation) -> Dict[str, Any]:
        """
        Format single recommendation as a card/summary.
        
        Args:
            recommendation: Recommendation object to format
            
        Returns:
            Formatted recommendation card
        """
        card = {
            'id': recommendation.id,
            'title': recommendation.title,
            'summary': recommendation.description,
            'priority': recommendation.priority.value,
            'impact_score': recommendation.impact_score,
            'difficulty': recommendation.implementation_difficulty,
            'estimated_time': f"{recommendation.estimated_time_hours} hours",
            'type': recommendation.recommendation_type.value,
            'target_content': [ct.value for ct in recommendation.target_content_types],
            'action_items': recommendation.action_items[:3],  # Top 3 action items
            'expected_outcome': recommendation.expected_outcome,
            'urgency_indicator': self._calculate_urgency_indicator(recommendation),
            'quick_wins': self._identify_quick_wins(recommendation),
            'resources_needed': recommendation.required_resources[:3]  # Top 3 resources
        }
        
        return card
    
    def generate_action_plan(self, recommendations: List[Recommendation], timeframe_days: int = 30) -> Dict[str, Any]:
        """
        Generate detailed action plan based on recommendations.
        
        Args:
            recommendations: List of recommendations
            timeframe_days: Planning timeframe in days
            
        Returns:
            Detailed action plan
        """
        # Categorize recommendations by priority and complexity
        categorized_recs = self._categorize_recommendations(recommendations)
        
        # Create phased implementation plan
        action_plan = {
            'plan_metadata': {
                'timeframe_days': timeframe_days,
                'generated_date': datetime.now().isoformat(),
                'total_recommendations': len(recommendations),
                'high_priority_count': len([r for r in recommendations if r.priority.value == 'high'])
            },
            'phases': self._create_implementation_phases(categorized_recs, timeframe_days),
            'weekly_breakdown': self._create_weekly_breakdown(categorized_recs, timeframe_days),
            'resource_allocation': self._plan_resource_allocation(recommendations),
            'milestones': self._define_milestones(categorized_recs),
            'risk_assessment': self._assess_implementation_risks(recommendations)
        }
        
        return action_plan
    
    def generate_performance_dashboard_data(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate data for performance dashboard visualization.
        
        Args:
            analysis_results: Results from feedback analyzer
            
        Returns:
            Dashboard-ready data structure
        """
        dashboard_data = {
            'overview_metrics': self._extract_overview_metrics(analysis_results),
            'trend_data': self._generate_trend_data(analysis_results),
            'content_performance': self._generate_content_performance_data(analysis_results),
            'recommendation_impact': self._generate_recommendation_impact_data(analysis_results),
            'alerts': self._generate_performance_alerts(analysis_results)
        }
        
        return dashboard_data
    
    def format_notification_message(self, recommendations: List[Recommendation], alert_type: str = 'new_recommendations') -> Dict[str, Any]:
        """
        Format notification message for recommendations.
        
        Args:
            recommendations: Recommendations to include in notification
            alert_type: Type of alert
            
        Returns:
            Formatted notification message
        """
        if alert_type == 'new_recommendations':
            high_priority_count = len([r for r in recommendations if r.priority.value == 'high'])
            total_count = len(recommendations)
            
            message = {
                'type': 'recommendations_available',
                'priority': 'high' if high_priority_count > 0 else 'medium',
                'title': f"New Content Improvement Recommendations Available",
                'summary': f"{high_priority_count} high-priority and {total_count} total recommendations ready for review",
                'action_required': high_priority_count > 0,
                'quick_actions': [
                    {
                        'label': 'View High Priority',
                        'action': 'view_high_priority_recommendations',
                        'count': high_priority_count
                    },
                    {
                        'label': 'View All',
                        'action': 'view_all_recommendations',
                        'count': total_count
                    }
                ],
                'recommendations_preview': [self._format_recommendation_preview(r) for r in recommendations[:3]]
            }
            
        elif alert_type == 'performance_decline':
            message = {
                'type': 'performance_alert',
                'priority': 'high',
                'title': 'Content Performance Decline Detected',
                'summary': 'Performance metrics show declining trend requiring attention',
                'action_required': True,
                'recommended_action': 'Review latest feedback analysis and implement priority recommendations'
            }
        
        return message
    
    def generate_email_summary(self, recommendations: List[Recommendation], analysis_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate email summary for stakeholders.
        
        Args:
            recommendations: Top recommendations to include
            analysis_summary: Brief analysis summary
            
        Returns:
            Email summary data
        """
        email_data = {
            'subject': f"Content Improvement Update - {len(recommendations)} New Recommendations",
            'preview_text': f"Focus on {len([r for r in recommendations if r.priority.value == 'high'])} high-priority improvements",
            'executive_summary': analysis_summary.get('overall_score', 0),
            'key_recommendations': [self._format_recommendation_preview(r) for r in recommendations[:3]],
            'implementation_priority': {
                'immediate_actions': [r.title for r in recommendations if r.priority.value == 'high'][:3],
                'this_week_focus': [r.title for r in recommendations if r.implementation_difficulty == 'Low'][:2]
            },
            'expected_impact': self._calculate_expected_impact(recommendations),
            'call_to_action': {
                'primary': 'Review and approve priority recommendations',
                'secondary': 'Schedule implementation planning session'
            }
        }
        
        return email_data
    
    # Core formatting methods
    def _generate_report_metadata(self) -> Dict[str, Any]:
        """Generate report metadata."""
        return {
            'generated_date': datetime.now().isoformat(),
            'report_version': '1.0',
            'analysis_period': self._get_analysis_period(),
            'report_type': 'content_improvement_analysis',
            'confidence_level': 'high'
        }
    
    def _generate_executive_summary(self, analysis_results: Dict[str, Any], recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Generate executive summary."""
        overall_score = analysis_results.get('overall_score', 0)
        sentiment_patterns = analysis_results.get('sentiment_patterns', {})
        improvement_areas = analysis_results.get('improvement_areas', [])
        
        # Determine summary tone
        if overall_score >= 0.7:
            tone = 'positive'
            status = 'performing well'
        elif overall_score >= 0.5:
            tone = 'neutral'
            status = 'meeting expectations'
        else:
            tone = 'attention_needed'
            status = 'requires improvement'
        
        return {
            'overall_assessment': status,
            'content_score': round(overall_score, 2),
            'sentiment_trend': sentiment_patterns.get('trending_direction', 'stable'),
            'priority_improvements': len([r for r in recommendations if r.priority.value == 'high']),
            'key_insights': self._extract_key_insights(analysis_results),
            'recommended_focus': self._determine_recommended_focus(improvement_areas),
            'tone': tone,
            'urgency_level': 'high' if overall_score < 0.4 else 'medium' if overall_score < 0.6 else 'low'
        }
    
    def _generate_analysis_overview(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis overview section."""
        return {
            'analysis_scope': {
                'sentiment_analysis': 'Completed',
                'pattern_detection': 'Completed',
                'content_quality_assessment': 'Completed',
                'engagement_analysis': 'Completed'
            },
            'data_points_analyzed': self._estimate_data_points_analyzed(analysis_results),
            'key_findings': self._summarize_key_findings(analysis_results),
            'confidence_levels': {
                'sentiment_analysis': 'high',
                'pattern_detection': 'medium',
                'content_quality': 'high',
                'recommendations': 'high'
            }
        }
    
    def _generate_recommendations_summary(self, recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Generate recommendations summary."""
        total_recs = len(recommendations)
        priority_counts = {'high': 0, 'medium': 0, 'low': 0}
        type_counts = {}
        total_impact = 0
        total_time = 0
        
        for rec in recommendations:
            priority_counts[rec.priority.value] += 1
            type_counts[rec.recommendation_type.value] = type_counts.get(rec.recommendation_type.value, 0) + 1
            total_impact += rec.impact_score
            total_time += rec.estimated_time_hours
        
        return {
            'total_recommendations': total_recs,
            'priority_distribution': priority_counts,
            'recommendation_types': type_counts,
            'average_impact_score': round(total_impact / total_recs, 2) if total_recs > 0 else 0,
            'total_estimated_hours': round(total_time, 1),
            'quick_wins_count': len([r for r in recommendations if r.implementation_difficulty == 'Low']),
            'high_impact_count': len([r for r in recommendations if r.impact_score >= 0.8])
        }
    
    def _generate_detailed_recommendations(self, recommendations: List[Recommendation]) -> List[Dict[str, Any]]:
        """Generate detailed recommendations section."""
        return [self.format_recommendation_card(rec) for rec in recommendations]
    
    def _generate_implementation_roadmap(self, recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Generate implementation roadmap."""
        # Sort recommendations by priority and impact
        sorted_recs = sorted(recommendations, key=lambda x: (x.priority.value == 'high', x.impact_score), reverse=True)
        
        roadmap = {
            'immediate_actions': [],
            'short_term_goals': [],
            'medium_term_goals': [],
            'long_term_vision': []
        }
        
        for rec in sorted_recs:
            rec_summary = {
                'title': rec.title,
                'priority': rec.priority.value,
                'timeline': self._estimate_implementation_timeline(rec),
                'resources': rec.required_resources
            }
            
            if rec.priority.value == 'high':
                roadmap['immediate_actions'].append(rec_summary)
            elif rec.estimated_time_hours <= 8:
                roadmap['short_term_goals'].append(rec_summary)
            elif rec.estimated_time_hours <= 20:
                roadmap['medium_term_goals'].append(rec_summary)
            else:
                roadmap['long_term_vision'].append(rec_summary)
        
        return roadmap
    
    def _define_success_metrics(self, recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Define success metrics for tracking progress."""
        metrics = {
            'overall_metrics': {
                'content_quality_score': 'Target: >0.7',
                'sentiment_score': 'Target: >0.6',
                'engagement_rate': 'Target: >5%',
                'audience_satisfaction': 'Target: >80%'
            },
            'recommendation_metrics': {
                'implementation_rate': 'Target: >80% of high-priority recommendations',
                'impact_realization': 'Target: measurable improvement within 30 days',
                'content_optimization': 'Target: 15% improvement in key metrics'
            },
            'tracking_schedule': {
                'weekly': ['sentiment_score', 'engagement_rate'],
                'monthly': ['content_quality_score', 'recommendation_implementation'],
                'quarterly': ['overall_performance', 'strategic_goals']
            }
        }
        
        return metrics
    
    def _generate_next_steps(self, recommendations: List[Recommendation]) -> List[Dict[str, Any]]:
        """Generate actionable next steps."""
        next_steps = []
        
        # Immediate priorities
        high_priority_recs = [r for r in recommendations if r.priority.value == 'high']
        if high_priority_recs:
            next_steps.append({
                'priority': 'immediate',
                'action': f"Review and approve {len(high_priority_recs)} high-priority recommendations",
                'timeline': 'Within 24 hours',
                'owner': 'Content Strategy Lead',
                'success_criteria': 'All high-priority recommendations approved for implementation'
            })
        
        # Quick wins
        quick_wins = [r for r in recommendations if r.implementation_difficulty == 'Low'][:2]
        if quick_wins:
            next_steps.append({
                'priority': 'this_week',
                'action': f"Implement quick wins: {', '.join([r.title for r in quick_wins])}",
                'timeline': 'This week',
                'owner': 'Content Team',
                'success_criteria': 'Quick win recommendations implemented and tested'
            })
        
        # Strategic planning
        next_steps.append({
            'priority': 'this_month',
            'action': 'Schedule comprehensive implementation planning session',
            'timeline': 'Within 1 week',
            'owner': 'Content Strategy Lead',
            'success_criteria': 'Implementation plan created with resource allocation'
        })
        
        return next_steps
    
    # Helper methods for template generation
    def _calculate_urgency_indicator(self, recommendation: Recommendation) -> str:
        """Calculate urgency indicator for recommendation."""
        if recommendation.priority.value == 'high' or recommendation.impact_score >= 0.9:
            return 'critical'
        elif recommendation.priority.value == 'medium':
            return 'important'
        else:
            return 'standard'
    
    def _identify_quick_wins(self, recommendation: Recommendation) -> List[str]:
        """Identify quick wins within recommendation."""
        if recommendation.implementation_difficulty == 'Low':
            return recommendation.action_items[:2]
        else:
            return []
    
    def _categorize_recommendations(self, recommendations: List[Recommendation]) -> Dict[str, List[Recommendation]]:
        """Categorize recommendations by priority and complexity."""
        categorized = {
            'urgent_high_impact': [],
            'important_medium_impact': [],
            'enhancement_low_impact': [],
            'quick_wins': [],
            'complex_projects': []
        }
        
        for rec in recommendations:
            if rec.priority.value == 'high' and rec.impact_score >= 0.8:
                categorized['urgent_high_impact'].append(rec)
            elif rec.priority.value == 'medium' and rec.impact_score >= 0.6:
                categorized['important_medium_impact'].append(rec)
            elif rec.impact_score >= 0.4:
                categorized['enhancement_low_impact'].append(rec)
            
            if rec.implementation_difficulty == 'Low':
                categorized['quick_wins'].append(rec)
            elif rec.estimated_time_hours > 15:
                categorized['complex_projects'].append(rec)
        
        return categorized
    
    def _create_implementation_phases(self, categorized_recs: Dict[str, List[Recommendation]], timeframe_days: int) -> List[Dict[str, Any]]:
        """Create phased implementation plan."""
        phases = []
        
        # Phase 1: Immediate actions (Week 1-2)
        if categorized_recs['urgent_high_impact']:
            phases.append({
                'phase': 'Critical Implementation',
                'duration': min(14, timeframe_days // 3),
                'recommendations': [r.title for r in categorized_recs['urgent_high_impact'][:3]],
                'focus': 'Address critical issues and implement high-impact changes',
                'success_criteria': 'All critical issues resolved, measurable improvement in key metrics'
            })
        
        # Phase 2: Quick wins (Week 2-4)
        if categorized_recs['quick_wins']:
            phases.append({
                'phase': 'Quick Wins & Optimizations',
                'duration': min(14, timeframe_days // 3),
                'recommendations': [r.title for r in categorized_recs['quick_wins'][:4]],
                'focus': 'Implement easy wins and immediate optimizations',
                'success_criteria': 'Quick wins implemented, foundation for larger changes established'
            })
        
        # Phase 3: Strategic improvements (Week 3-4)
        remaining_time = timeframe_days - sum(phase['duration'] for phase in phases)
        if remaining_time > 0 and categorized_recs['important_medium_impact']:
            phases.append({
                'phase': 'Strategic Improvements',
                'duration': remaining_time,
                'recommendations': [r.title for r in categorized_recs['important_medium_impact'][:3]],
                'focus': 'Implement strategic improvements and process optimizations',
                'success_criteria': 'Strategic improvements in place, improved content creation process'
            })
        
        return phases
    
    def _create_weekly_breakdown(self, categorized_recs: Dict[str, List[Recommendation]], timeframe_days: int) -> List[Dict[str, Any]]:
        """Create weekly breakdown of implementation."""
        weeks = []
        current_date = datetime.now()
        
        for week_num in range(1, (timeframe_days // 7) + 1):
            week_start = current_date + timedelta(days=(week_num - 1) * 7)
            week_end = week_start + timedelta(days=6)
            
            # Assign recommendations to weeks based on priority
            week_recs = []
            if week_num <= 2 and categorized_recs['urgent_high_impact']:
                week_recs.extend(categorized_recs['urgent_high_impact'][:2])
            elif week_num <= 3 and categorized_recs['quick_wins']:
                week_recs.extend(categorized_recs['quick_wins'][:2])
            elif categorized_recs['important_medium_impact']:
                week_recs.extend(categorized_recs['important_medium_impact'][:1])
            
            weeks.append({
                'week_number': week_num,
                'date_range': f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}",
                'focus_area': self._determine_week_focus(week_num, categorized_recs),
                'recommendations': [r.title for r in week_recs],
                'estimated_hours': sum(r.estimated_time_hours for r in week_recs),
                'milestones': self._define_week_milestones(week_num)
            })
        
        return weeks
    
    def _plan_resource_allocation(self, recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Plan resource allocation for recommendations."""
        total_hours = sum(r.estimated_time_hours for r in recommendations)
        
        # Estimate team allocation
        allocation = {
            'total_estimated_hours': total_hours,
            'team_allocation': {
                'content_creators': total_hours * 0.6,
                'strategists': total_hours * 0.25,
                'analysts': total_hours * 0.15
            },
            'external_resources': list(set(
                resource for rec in recommendations for resource in rec.required_resources
                if 'external' in resource.lower() or 'consultant' in resource.lower()
            )),
            'tools_required': list(set(
                resource for rec in recommendations for resource in rec.required_resources
                if 'tool' in resource.lower() or 'software' in resource.lower()
            ))
        }
        
        return allocation
    
    def _define_milestones(self, categorized_recs: Dict[str, List[Recommendation]]) -> List[Dict[str, Any]]:
        """Define key milestones for implementation."""
        milestones = []
        
        # First milestone: Critical issues addressed
        if categorized_recs['urgent_high_impact']:
            milestones.append({
                'milestone': 'Critical Issues Resolved',
                'description': 'All high-priority recommendations implemented',
                'timeline': 'Week 2',
                'success_criteria': 'Content quality score improved by 20%'
            })
        
        # Second milestone: Quick wins completed
        if categorized_recs['quick_wins']:
            milestones.append({
                'milestone': 'Quick Wins Implemented',
                'description': 'All easy-to-implement recommendations completed',
                'timeline': 'Week 3',
                'success_criteria': 'Engagement rate improved by 10%'
            })
        
        # Final milestone: Overall improvement
        milestones.append({
            'milestone': 'Strategic Goals Achieved',
            'description': 'Comprehensive content improvement completed',
            'timeline': 'Week 4',
            'success_criteria': 'Overall content score >0.7, sentiment improvement >15%'
        })
        
        return milestones
    
    def _assess_implementation_risks(self, recommendations: List[Recommendation]) -> List[Dict[str, Any]]:
        """Assess implementation risks."""
        risks = []
        
        # High complexity recommendations
        complex_recs = [r for r in recommendations if r.estimated_time_hours > 20]
        if complex_recs:
            risks.append({
                'risk': 'Implementation Complexity',
                'description': f'{len(complex_recs)} recommendations require significant time investment',
                'mitigation': 'Break complex projects into smaller phases',
                'probability': 'medium',
                'impact': 'high'
            })
        
        # Resource availability
        total_hours = sum(r.estimated_time_hours for r in recommendations)
        if total_hours > 100:
            risks.append({
                'risk': 'Resource Constraints',
                'description': 'High total time requirement may strain resources',
                'mitigation': 'Prioritize high-impact recommendations and consider external support',
                'probability': 'medium',
                'impact': 'medium'
            })
        
        # Implementation dependencies
        dependency_recs = [r for r in recommendations if r.dependencies]
        if dependency_recs:
            risks.append({
                'risk': 'Implementation Dependencies',
                'description': f'{len(dependency_recs)} recommendations have dependencies',
                'mitigation': 'Carefully plan implementation order and coordinate dependencies',
                'probability': 'low',
                'impact': 'medium'
            })
        
        return risks
    
    # Data extraction and formatting helpers
    def _extract_overview_metrics(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics for dashboard overview."""
        return {
            'content_score': analysis_results.get('overall_score', 0),
            'sentiment_trend': analysis_results.get('sentiment_patterns', {}).get('trending_direction', 'stable'),
            'engagement_rate': analysis_results.get('engagement_patterns', {}).get('average_engagement_rate', 0),
            'improvement_areas_count': len(analysis_results.get('improvement_areas', []))
        }
    
    def _generate_trend_data(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate trend data for visualization."""
        temporal_trends = analysis_results.get('temporal_trends', {})
        
        trend_data = []
        sentiment_trends = temporal_trends.get('sentiment_trends', {})
        engagement_trends = temporal_trends.get('engagement_trends', {})
        
        # Combine trends into daily data points
        all_dates = set(sentiment_trends.keys()) | set(engagement_trends.keys())
        
        for date in sorted(all_dates):
            trend_data.append({
                'date': date,
                'sentiment_score': sentiment_trends.get(date, 0),
                'engagement_rate': engagement_trends.get(date, 0)
            })
        
        return trend_data
    
    def _generate_content_performance_data(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content performance breakdown."""
        content_quality = analysis_results.get('content_quality', {})
        
        performance_data = {}
        for content_type, quality_data in content_quality.items():
            performance_data[content_type] = {
                'quality_score': quality_data.get('average_quality', 0),
                'trend': quality_data.get('quality_trend', 'stable'),
                'common_issues': quality_data.get('common_issues', [])[:3]
            }
        
        return performance_data
    
    def _generate_recommendation_impact_data(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendation impact visualization data."""
        return {
            'impact_distribution': {
                'high_impact': len(analysis_results.get('improvement_areas', [])) * 0.7,
                'medium_impact': len(analysis_results.get('improvement_areas', [])) * 0.2,
                'low_impact': len(analysis_results.get('improvement_areas', [])) * 0.1
            },
            'implementation_complexity': {
                'low': 0.4,  # Placeholder - would calculate from actual recommendations
                'medium': 0.4,
                'high': 0.2
            }
        }
    
    def _generate_performance_alerts(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate performance alerts for dashboard."""
        alerts = []
        
        overall_score = analysis_results.get('overall_score', 0)
        if overall_score < 0.4:
            alerts.append({
                'type': 'performance_decline',
                'severity': 'high',
                'message': 'Content performance requires immediate attention',
                'action_required': True
            })
        
        sentiment_patterns = analysis_results.get('sentiment_patterns', {})
        if sentiment_patterns.get('trending_direction') == 'declining':
            alerts.append({
                'type': 'sentiment_decline',
                'severity': 'medium',
                'message': 'Audience sentiment showing declining trend',
                'action_required': True
            })
        
        return alerts
    
    def _format_recommendation_preview(self, recommendation: Recommendation) -> Dict[str, Any]:
        """Format recommendation for preview/notification."""
        return {
            'title': recommendation.title,
            'priority': recommendation.priority.value,
            'impact_score': recommendation.impact_score,
            'estimated_time': f"{recommendation.estimated_time_hours}h",
            'summary': recommendation.description[:100] + "..." if len(recommendation.description) > 100 else recommendation.description
        }
    
    def _calculate_expected_impact(self, recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Calculate expected impact from recommendations."""
        total_impact = sum(r.impact_score for r in recommendations)
        high_impact_count = len([r for r in recommendations if r.impact_score >= 0.8])
        
        return {
            'total_potential_impact': round(total_impact, 2),
            'high_impact_recommendations': high_impact_count,
            'expected_improvement': '15-25% improvement in content metrics',
            'implementation_timeline': '4-6 weeks for full impact realization'
        }
    
    def _get_analysis_period(self) -> str:
        """Get the analysis period for the report."""
        # This would typically be derived from the actual data
        return "Last 30 days"
    
    def _extract_key_insights(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Extract key insights from analysis results."""
        insights = []
        
        # Extract sentiment insights
        sentiment_patterns = analysis_results.get('sentiment_patterns', {})
        if sentiment_patterns.get('trending_direction') == 'improving':
            insights.append("Audience sentiment is trending positively")
        elif sentiment_patterns.get('trending_direction') == 'declining':
            insights.append("Audience sentiment requires attention")
        
        # Extract engagement insights
        engagement_patterns = analysis_results.get('engagement_patterns', {})
        avg_engagement = engagement_patterns.get('average_engagement_rate', 0)
        if avg_engagement > 0.05:
            insights.append("Strong engagement rates indicate audience interest")
        elif avg_engagement < 0.02:
            insights.append("Engagement rates suggest content optimization opportunities")
        
        return insights
    
    def _determine_recommended_focus(self, improvement_areas: List[Dict[str, Any]]) -> str:
        """Determine recommended focus areas."""
        if not improvement_areas:
            return "Continue current strategy with minor optimizations"
        
        high_priority_areas = [area for area in improvement_areas if area.get('priority') == 'high']
        if high_priority_areas:
            return f"Focus on {', '.join([area.get('area', '').replace('_', ' ') for area in high_priority_areas[:2]])}"
        
        return "Implement recommended improvements across identified areas"
    
    def _estimate_data_points_analyzed(self, analysis_results: Dict[str, Any]) -> int:
        """Estimate number of data points analyzed."""
        # This would be calculated based on actual feedback data
        return 1000  # Placeholder
    
    def _summarize_key_findings(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Summarize key findings from analysis."""
        findings = []
        
        overall_score = analysis_results.get('overall_score', 0)
        findings.append(f"Overall content quality score: {overall_score:.2f}")
        
        sentiment_patterns = analysis_results.get('sentiment_patterns', {})
        avg_sentiment = sentiment_patterns.get('average_score', 0.5)
        findings.append(f"Average audience sentiment: {avg_sentiment:.2f}")
        
        return findings
    
    def _determine_week_focus(self, week_num: int, categorized_recs: Dict[str, List[Recommendation]]) -> str:
        """Determine focus area for specific week."""
        if week_num <= 2:
            return "Critical Issues & Quick Wins"
        elif week_num <= 4:
            return "Strategic Improvements"
        else:
            return "Optimization & Fine-tuning"
    
    def _define_week_milestones(self, week_num: int) -> List[str]:
        """Define milestones for specific week."""
        if week_num == 1:
            return ["Critical recommendations approved", "Implementation planning completed"]
        elif week_num == 2:
            return ["High-priority changes implemented", "Initial results measured"]
        elif week_num == 3:
            return ["Quick wins implemented", "Process improvements in place"]
        else:
            return ["Strategic goals achieved", "Performance metrics improved"]
    
    def _estimate_implementation_timeline(self, recommendation: Recommendation) -> str:
        """Estimate implementation timeline for recommendation."""
        hours = recommendation.estimated_time_hours
        
        if hours <= 2:
            return "Same day"
        elif hours <= 8:
            return "This week"
        elif hours <= 20:
            return "This month"
        else:
            return "Next quarter"
    
    def _load_templates(self) -> Dict[str, Any]:
        """Load template definitions."""
        return {
            'recommendation_card': {
                'template': 'card_template_v1',
                'format': 'structured'
            },
            'email_summary': {
                'template': 'email_summary_v1',
                'format': 'email_compatible'
            },
            'dashboard_data': {
                'template': 'dashboard_v1',
                'format': 'json_compatible'
            }
        }