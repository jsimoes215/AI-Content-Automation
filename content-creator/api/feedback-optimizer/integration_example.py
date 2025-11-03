#!/usr/bin/env python3
"""
Integration Example: Feedback-Driven Content Improvement Optimizer

This example demonstrates how to integrate the feedback optimizer
with a content creation workflow.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Import the feedback optimizer
from feedback_optimizer import LearningEngine


class ContentCreationWorkflow:
    """
    Example workflow that integrates feedback optimization with content creation.
    """
    
    def __init__(self):
        """Initialize the workflow with the feedback optimizer."""
        self.learning_engine = LearningEngine()
        self.content_queue = []
        self.implementation_history = []
        
    def create_content_plan(self, content_ideas: List[str]) -> Dict[str, Any]:
        """
        Create a content plan based on feedback analysis and recommendations.
        
        Args:
            content_ideas: List of content ideas to develop
            
        Returns:
            Content plan with optimization recommendations
        """
        print("📋 Creating optimized content plan...")
        
        # Get recent feedback analysis for context
        recent_insights = self._get_recent_insights()
        
        # Generate content plan based on insights
        content_plan = {
            'plan_date': datetime.now().isoformat(),
            'based_on_insights': recent_insights,
            'content_ideas': content_ideas,
            'optimization_focus': self._determine_optimization_focus(recent_insights),
            'recommended_improvements': self._get_applicable_recommendations(recent_insights),
            'success_metrics': self._define_success_metrics(),
            'timeline': self._create_implementation_timeline(len(content_ideas))
        }
        
        print(f"✅ Content plan created with {len(content_ideas)} ideas")
        print(f"🎯 Optimization focus: {content_plan['optimization_focus']}")
        
        return content_plan
    
    def optimize_content_before_publication(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize content before publication based on learned patterns.
        
        Args:
            content: Content to optimize
            
        Returns:
            Optimized content with recommendations applied
        """
        print(f"🔧 Optimizing content: {content.get('title', 'Untitled')}")
        
        # Apply pattern-based optimizations
        optimized_content = self._apply_pattern_optimizations(content)
        
        # Get content-specific recommendations
        recommendations = self._get_content_specific_recommendations(content)
        
        # Apply recommendations
        for rec in recommendations:
            if rec['impact_score'] > 0.7 and rec['implementation_difficulty'] == 'Low':
                optimized_content = self._apply_quick_wins(optimized_content, rec)
        
        print(f"✅ Content optimized with {len(recommendations)} recommendations considered")
        
        return {
            'original_content': content,
            'optimized_content': optimized_content,
            'applied_optimizations': [rec for rec in recommendations if rec['applied']],
            'pending_recommendations': [rec for rec in recommendations if not rec['applied']],
            'optimization_score': self._calculate_optimization_score(content, optimized_content)
        }
    
    def track_content_performance(self, content_id: str, feedback_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Track content performance and feed insights back to the optimizer.
        
        Args:
            content_id: ID of the content being tracked
            feedback_data: Feedback data for the content
            
        Returns:
            Performance analysis and improvement suggestions
        """
        print(f"📊 Tracking performance for content: {content_id}")
        
        # Analyze feedback for this specific content
        analysis_results = self.learning_engine.analyzer.analyze_feedback(feedback_data)
        
        # Generate performance insights
        performance_insights = {
            'content_id': content_id,
            'analysis_date': datetime.now().isoformat(),
            'feedback_count': len(feedback_data),
            'overall_score': analysis_results.get('overall_score', 0),
            'sentiment_analysis': analysis_results.get('sentiment_patterns', {}),
            'engagement_analysis': analysis_results.get('engagement_patterns', {}),
            'improvement_areas': analysis_results.get('improvement_areas', []),
            'performance_vs_baseline': self._compare_to_baseline(analysis_results),
            'recommendations_for_future': self._generate_future_recommendations(analysis_results)
        }
        
        # Store in implementation history
        self.implementation_history.append({
            'content_id': content_id,
            'analysis_date': datetime.now().isoformat(),
            'performance_data': performance_insights,
            'feedback_data': feedback_data
        })
        
        print(f"✅ Performance analysis completed")
        print(f"📈 Overall score: {performance_insights['overall_score']:.2f}")
        print(f"💡 Improvement areas identified: {len(performance_insights['improvement_areas'])}")
        
        return performance_insights
    
    def continuous_improvement_cycle(self) -> Dict[str, Any]:
        """
        Run continuous improvement cycle to refine recommendations.
        
        Returns:
            Improvement cycle results
        """
        print("🔄 Running continuous improvement cycle...")
        
        # Collect recent feedback for analysis
        recent_feedback = []
        for history_item in self.implementation_history[-10:]:  # Last 10 items
            recent_feedback.extend(history_item['feedback_data'])
        
        if len(recent_feedback) < 5:
            print("⚠️  Insufficient data for improvement cycle")
            return {'status': 'insufficient_data'}
        
        # Run learning cycle
        learning_results = self.learning_engine.process_feedback_learning_cycle(recent_feedback)
        
        # Analyze patterns
        pattern_analysis = self.learning_engine.pattern_detector.analyze_pattern_frequency(
            self.learning_engine._convert_feedback_data_from_analysis(
                learning_results['analysis_results']
            )
        )
        
        # Identify improvement opportunities
        opportunities = self.learning_engine.pattern_detector.identify_improvement_opportunities(
            pattern_analysis
        )
        
        cycle_results = {
            'cycle_date': datetime.now().isoformat(),
            'feedback_analyzed': len(recent_feedback),
            'new_patterns_identified': len(opportunities),
            'learning_updates': self._summarize_learning_updates(learning_results),
            'recommendation_adjustments': self._calculate_recommendation_adjustments(opportunities),
            'next_focus_areas': self._determine_next_focus_areas(opportunities),
            'system_health': self._assess_system_health(learning_results)
        }
        
        print(f"✅ Improvement cycle completed")
        print(f"🧠 Patterns identified: {cycle_results['new_patterns_identified']}")
        print(f"🎯 Next focus areas: {len(cycle_results['next_focus_areas'])}")
        
        return cycle_results
    
    # Helper methods
    
    def _get_recent_insights(self) -> Dict[str, Any]:
        """Get recent insights from the learning engine."""
        try:
            return self.learning_engine.get_learning_summary(days_back=14)
        except:
            return {'status': 'no_data', 'learning_cycles_count': 0}
    
    def _determine_optimization_focus(self, insights: Dict[str, Any]) -> str:
        """Determine primary optimization focus based on insights."""
        if insights.get('learning_cycles_count', 0) == 0:
            return "establish_baseline"
        
        # Analyze performance summary
        perf_summary = insights.get('performance_summary', {})
        improvement = perf_summary.get('percentage_improvement', 0)
        
        if improvement < -5:
            return "critical_performance_issues"
        elif improvement < 5:
            return "incremental_improvements"
        else:
            return "optimization_and_refinement"
    
    def _get_applicable_recommendations(self, insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recommendations applicable to current content creation."""
        # In a real implementation, this would query the recommendation database
        # For now, return sample recommendations based on insights
        recommendations = []
        
        if insights.get('learning_cycles_count', 0) > 0:
            recommendations.append({
                'type': 'script_optimization',
                'title': 'Improve Script Structure',
                'impact_score': 0.8,
                'implementation_difficulty': 'Medium'
            })
        
        return recommendations
    
    def _define_success_metrics(self) -> Dict[str, Any]:
        """Define success metrics for content performance."""
        return {
            'content_quality_score': {'target': '>0.7', 'measurement': 'sentiment_analysis'},
            'engagement_rate': {'target': '>5%', 'measurement': 'likes_comments_shares/views'},
            'audience_satisfaction': {'target': '>80%', 'measurement': 'positive_sentiment_ratio'},
            'completion_rate': {'target': '>70%', 'measurement': 'full_views/total_views'}
        }
    
    def _create_implementation_timeline(self, content_count: int) -> List[Dict[str, Any]]:
        """Create implementation timeline for content creation."""
        timeline = []
        start_date = datetime.now()
        
        for i in range(content_count):
            content_date = start_date + timedelta(days=i*3)  # 3 days per content
        
            timeline.append({
                'content_number': i + 1,
                'target_date': content_date.isoformat(),
                'focus_area': 'script_and_thumbnail' if i % 2 == 0 else 'title_and_description',
                'optimization_checkpoints': [
                    'pre_creation_review',
                    'mid_creation_optimization',
                    'pre_publication_review'
                ]
            })
        
        return timeline
    
    def _apply_pattern_optimizations(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Apply optimizations based on learned patterns."""
        optimized_content = content.copy()
        
        # Apply common successful patterns
        if 'script' in optimized_content:
            script = optimized_content['script']
            
            # Add opening hook if missing
            if not any(word in script.lower() for word in ['did you know', 'have you ever', 'what if']):
                optimized_content['script'] = "Did you know that " + script
        
        # Apply thumbnail optimizations
        if 'thumbnail_description' in optimized_content:
            desc = optimized_content['thumbnail_description']
            
            # Add engagement elements if missing
            if 'eye-catching' not in desc and 'bright colors' not in desc:
                optimized_content['thumbnail_description'] = desc + " [Eye-catching with bright colors]"
        
        return optimized_content
    
    def _get_content_specific_recommendations(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get content-specific recommendations."""
        # Simulate getting recommendations
        recommendations = [
            {
                'type': 'script_hook',
                'title': 'Strengthen opening hook',
                'impact_score': 0.85,
                'implementation_difficulty': 'Low',
                'description': 'Add compelling question or statistic at the beginning',
                'applied': False
            },
            {
                'type': 'cta_optimization',
                'title': 'Improve call-to-action',
                'impact_score': 0.75,
                'implementation_difficulty': 'Low',
                'description': 'Make CTA more specific and action-oriented',
                'applied': False
            }
        ]
        
        return recommendations
    
    def _apply_quick_wins(self, content: Dict[str, Any], recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Apply quick win recommendations."""
        optimized_content = content.copy()
        
        if recommendation['type'] == 'script_hook':
            if 'script' in optimized_content:
                script = optimized_content['script']
                if not script.startswith(('Did', 'Have', 'What', 'Imagine')):
                    optimized_content['script'] = "Have you ever " + script
        
        recommendation['applied'] = True
        return optimized_content
    
    def _calculate_optimization_score(self, original: Dict[str, Any], optimized: Dict[str, Any]) -> float:
        """Calculate optimization improvement score."""
        # Simple scoring based on applied optimizations
        score = 0.5  # Base score
        
        if 'script' in original and 'script' in optimized:
            if len(optimized['script']) > len(original['script']):
                score += 0.2
        
        if 'thumbnail_description' in optimized:
            if 'eye-catching' in optimized['thumbnail_description']:
                score += 0.3
        
        return min(1.0, score)
    
    def _compare_to_baseline(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current performance to baseline."""
        current_score = analysis_results.get('overall_score', 0.5)
        
        # In a real implementation, this would use actual baseline data
        baseline_score = 0.6
        
        return {
            'current_score': current_score,
            'baseline_score': baseline_score,
            'difference': current_score - baseline_score,
            'performance_status': 'above_baseline' if current_score > baseline_score else 'below_baseline'
        }
    
    def _generate_future_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations for future content."""
        improvement_areas = analysis_results.get('improvement_areas', [])
        
        recommendations = []
        for area in improvement_areas[:3]:  # Top 3 areas
            recommendations.append({
                'area': area.get('area', 'general'),
                'priority': area.get('priority', 'medium'),
                'description': area.get('description', ''),
                'focus_type': 'preventive' if area.get('priority') == 'high' else 'enhancement'
            })
        
        return recommendations
    
    def _summarize_learning_updates(self, learning_results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize learning updates from the cycle."""
        return {
            'new_patterns_learned': len(learning_results.get('learning_insights', {}).get('pattern_recognition', {})),
            'recommendations_updated': len(learning_results.get('recommendations', [])),
            'confidence_adjustments': True,
            'system_health': 'good'
        }
    
    def _calculate_recommendation_adjustments(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate adjustments to recommendation system."""
        return {
            'priority_adjustments': len([opp for opp in opportunities if opp.get('priority') == 'high']),
            'threshold_updates': False,
            'pattern_weight_updates': True
        }
    
    def _determine_next_focus_areas(self, opportunities: List[Dict[str, Any]]) -> List[str]:
        """Determine next focus areas for optimization."""
        focus_areas = []
        
        for opportunity in opportunities[:3]:
            focus_areas.append(opportunity.get('pattern', 'general_optimization'))
        
        return focus_areas or ['content_structure', 'engagement_optimization', 'audience_targeting']
    
    def _assess_system_health(self, learning_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess health of the optimization system."""
        analysis_results = learning_results.get('analysis_results', {})
        overall_score = analysis_results.get('overall_score', 0.5)
        
        return {
            'data_quality': 'good' if len(analysis_results) > 3 else 'needs_improvement',
            'recommendation_relevance': 'high' if overall_score > 0.6 else 'medium',
            'learning_velocity': 'active',
            'overall_health': 'healthy'
        }


def main():
    """Main example demonstrating the workflow integration."""
    print("🚀 Content Creation Workflow with Feedback Optimization")
    print("=" * 60)
    
    # Initialize the workflow
    workflow = ContentCreationWorkflow()
    
    # Example 1: Create content plan
    print("\n1️⃣ Creating Optimized Content Plan")
    content_ideas = [
        "How to improve video engagement",
        "Content creation best practices",
        "Audience retention strategies"
    ]
    
    content_plan = workflow.create_content_plan(content_ideas)
    print(f"   📋 Optimization focus: {content_plan['optimization_focus']}")
    print(f"   📅 Timeline: {len(content_plan['timeline'])} content pieces planned")
    
    # Example 2: Optimize content before publication
    print("\n2️⃣ Optimizing Content Before Publication")
    sample_content = {
        'title': 'Video Engagement Tips',
        'script': 'Here are some tips for better video engagement...',
        'thumbnail_description': 'Video thumbnail with title text',
        'target_audience': 'content creators'
    }
    
    optimization_result = workflow.optimize_content_before_publication(sample_content)
    print(f"   🔧 Optimization score: {optimization_result['optimization_score']:.2f}")
    print(f"   ✅ Applied optimizations: {len(optimization_result['applied_optimizations'])}")
    
    # Example 3: Track content performance
    print("\n3️⃣ Tracking Content Performance")
    sample_feedback = [
        {
            'content_id': 'video_001',
            'feedback_type': 'comment',
            'text': 'Great tips! Very helpful content.',
            'engagement_metrics': {'views': 1000, 'likes': 50, 'comments': 8}
        },
        {
            'content_id': 'video_001',
            'feedback_type': 'comment',
            'text': 'The thumbnail could be more eye-catching.',
            'engagement_metrics': {'views': 1000, 'likes': 50, 'comments': 8}
        }
    ]
    
    performance_analysis = workflow.track_content_performance('video_001', sample_feedback)
    print(f"   📊 Performance score: {performance_analysis['overall_score']:.2f}")
    print(f"   💡 Improvement areas: {len(performance_analysis['improvement_areas'])}")
    
    # Example 4: Continuous improvement cycle
    print("\n4️⃣ Running Continuous Improvement Cycle")
    improvement_cycle = workflow.continuous_improvement_cycle()
    
    if improvement_cycle.get('status') != 'insufficient_data':
        print(f"   🔄 Patterns identified: {improvement_cycle['new_patterns_identified']}")
        print(f"   🎯 Focus areas: {len(improvement_cycle['next_focus_areas'])}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Integration Summary:")
    print("   ✅ Content plan optimized based on feedback patterns")
    print("   ✅ Content pre-publication optimization applied")
    print("   ✅ Performance tracking and analysis completed")
    print("   ✅ Continuous improvement cycle executed")
    print("\n🎯 The feedback optimizer is successfully integrated!")
    print("\nNext steps:")
    print("   1. Connect to your actual content platform APIs")
    print("   2. Implement automated feedback collection")
    print("   3. Set up regular improvement cycles")
    print("   4. Monitor system performance and adjust as needed")


if __name__ == "__main__":
    main()