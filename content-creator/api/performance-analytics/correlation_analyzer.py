"""
Correlation Analyzer Module

Analyzes correlations between content features and performance metrics.
Uses statistical methods to identify patterns and relationships.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

import asyncpg
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import pearsonr, spearmanr
import warnings
warnings.filterwarnings('ignore')


class ContentFeature(Enum):
    """Types of content features to analyze"""
    DURATION = "duration"
    TITLE_LENGTH = "title_length"
    DESCRIPTION_LENGTH = "description_length"
    HAS_THUMBNAIL = "has_thumbnail"
    VIDEO_QUALITY = "video_quality"
    AUDIO_QUALITY = "audio_quality"
    SCENE_COUNT = "scene_count"
    TEXT_DENSITY = "text_density"
    CAMERA_MOVEMENT = "camera_movement"
    TRANSITION_FREQUENCY = "transition_frequency"
    COLOR_PALETTE = "color_palette"
    MUSIC_STYLE = "music_style"
    TONE = "tone"
    TOPIC = "topic"
    TARGET_AUDIENCE = "target_audience"


class PerformanceMetric(Enum):
    """Performance metrics to correlate with features"""
    VIEWS = "views"
    LIKES = "likes"
    COMMENTS = "comments"
    SHARES = "shares"
    ENGAGEMENT_RATE = "engagement_rate"
    WATCH_TIME = "watch_time"
    CLICK_THROUGH_RATE = "click_through_rate"
    PERFORMANCE_SCORE = "performance_score"
    SENTIMENT_SCORE = "sentiment_score"


@dataclass
class CorrelationResult:
    """Result of correlation analysis"""
    feature: ContentFeature
    metric: PerformanceMetric
    correlation_coefficient: float
    p_value: float
    strength: str  # 'weak', 'moderate', 'strong'
    direction: str  # 'positive', 'negative'
    significance_level: float
    sample_size: int
    confidence_interval: Tuple[float, float]
    interpretation: str


@dataclass
class FeatureImportance:
    """Feature importance ranking for predicting performance"""
    feature: ContentFeature
    importance_score: float
    rank: int
    correlation_with_target: float
    predictive_power: str


class CorrelationAnalyzer:
    """Analyzes correlations between content features and performance"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)
        self._cached_analysis = {}
        self._cache_duration = timedelta(hours=1)
        
    async def analyze_feature_correlations(
        self,
        content_ids: Optional[List[str]] = None,
        platforms: Optional[List[str]] = None,
        time_period_days: int = 90,
        significance_threshold: float = 0.05
    ) -> List[CorrelationResult]:
        """Analyze correlations between features and performance metrics"""
        
        cache_key = f"correlations:{hash(str(content_ids))}:{hash(str(platforms))}:{time_period_days}"
        
        if cache_key in self._cached_analysis:
            cached_entry = self._cached_analysis[cache_key]
            if datetime.now() - cached_entry['timestamp'] < self._cache_duration:
                return cached_entry['data']
        
        try:
            # Build base query
            end_date = datetime.now()
            start_date = end_date - timedelta(days=time_period_days)
            
            query = """
            SELECT 
                gc.id as content_id,
                gc.platform,
                gc.duration,
                gc.quality_score,
                COUNT(s.id) as scene_count,
                s.voiceover_text,
                s.visual_description,
                p.target_audience,
                p.tone,
                pm.views,
                pm.likes,
                pm.comments_count,
                pm.engagement_rate,
                pm.watch_time,
                pm.performance_score,
                ca.avg_sentiment_score
            FROM generated_content gc
            LEFT JOIN scenes s ON gc.scene_id = s.id
            LEFT JOIN scripts sc ON s.script_id = sc.id
            LEFT JOIN projects p ON sc.project_id = p.id
            LEFT JOIN performance_metrics pm ON gc.id = pm.content_id
            LEFT JOIN (
                SELECT content_id, AVG(sentiment_score) as avg_sentiment_score
                FROM comments_analysis
                GROUP BY content_id
            ) ca ON gc.id = ca.content_id
            WHERE gc.created_at >= $1 
            AND gc.created_at <= $2
            """
            
            params = [start_date, end_date]
            param_count = 2
            
            if content_ids:
                param_count += 1
                query += f" AND gc.id = ANY(${param_count})"
                params.append(content_ids)
            
            if platforms:
                param_count += 1
                query += f" AND gc.platform = ANY(${param_count})"
                params.append(platforms)
            
            query += " GROUP BY gc.id, gc.platform, gc.duration, gc.quality_score, s.voiceover_text, s.visual_description, p.target_audience, p.tone, pm.views, pm.likes, pm.comments_count, pm.engagement_rate, pm.watch_time, pm.performance_score, ca.avg_sentiment_score"
            
            rows = await self.db_pool.fetch(query, *params)
            
            if len(rows) < 10:
                self.logger.warning("Insufficient data for correlation analysis")
                return []
            
            # Convert to DataFrame for analysis
            data = []
            for row in rows:
                # Extract and calculate features
                features = self._extract_content_features(row)
                performance = self._extract_performance_metrics(row)
                
                if features and performance:
                    combined = {**features, **performance, 'content_id': row['content_id']}
                    data.append(combined)
            
            if len(data) < 10:
                return []
            
            df = pd.DataFrame(data)
            correlations = []
            
            # Define feature-metric pairs to analyze
            feature_metric_pairs = [
                (ContentFeature.DURATION, PerformanceMetric.ENGAGEMENT_RATE),
                (ContentFeature.DURATION, PerformanceMetric.VIEWS),
                (ContentFeature.VIDEO_QUALITY, PerformanceMetric.PERFORMANCE_SCORE),
                (ContentFeature.SCENE_COUNT, PerformanceMetric.ENGAGEMENT_RATE),
                (ContentFeature.TEXT_DENSITY, PerformanceMetric.WATCH_TIME),
                (ContentFeature.TONE, PerformanceMetric.SENTIMENT_SCORE),
                (ContentFeature.TARGET_AUDIENCE, PerformanceMetric.VIEWS),
            ]
            
            for feature, metric in feature_metric_pairs:
                correlation_result = await self._calculate_correlation(
                    df, feature, metric, significance_threshold
                )
                if correlation_result:
                    correlations.append(correlation_result)
            
            # Cache results
            self._cached_analysis[cache_key] = {
                'data': correlations,
                'timestamp': datetime.now()
            }
            
            return correlations
            
        except Exception as e:
            self.logger.error(f"Error analyzing correlations: {e}")
            raise
    
    async def _calculate_correlation(
        self,
        df: pd.DataFrame,
        feature: ContentFeature,
        metric: PerformanceMetric,
        significance_threshold: float
    ) -> Optional[CorrelationResult]:
        """Calculate correlation between a feature and metric"""
        
        try:
            feature_col = feature.value
            metric_col = metric.value
            
            if feature_col not in df.columns or metric_col not in df.columns:
                return None
            
            # Clean data
            clean_df = df[[feature_col, metric_col]].dropna()
            
            if len(clean_df) < 10:
                return None
            
            # Calculate correlation
            x = clean_df[feature_col].values
            y = clean_df[metric_col].values
            
            # Handle different data types
            if feature in [ContentFeature.TONE, ContentFeature.TARGET_AUDIENCE]:
                # Categorical variables - use one-hot encoding or label encoding
                if feature == ContentFeature.TONE:
                    x_encoded = pd.get_dummies(x).values.flatten()
                else:
                    # Label encode
                    from sklearn.preprocessing import LabelEncoder
                    le = LabelEncoder()
                    x_encoded = le.fit_transform(x.astype(str))
            else:
                x_encoded = x
            
            # Calculate Pearson correlation
            if len(x_encoded) == len(y):
                corr_coef, p_value = pearsonr(x_encoded, y)
                
                # Calculate confidence interval
                n = len(x_encoded)
                if n > 2:
                    # Fisher's z-transformation for confidence interval
                    z_score = 0.5 * np.log((1 + corr_coef) / (1 - corr_coef))
                    se = 1 / np.sqrt(n - 3)
                    z_critical = stats.norm.ppf(0.975)  # 95% CI
                    
                    z_lower = z_score - z_critical * se
                    z_upper = z_score + z_critical * se
                    
                    # Transform back
                    ci_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
                    ci_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
                    confidence_interval = (ci_lower, ci_upper)
                else:
                    confidence_interval = (corr_coef, corr_coef)
            else:
                corr_coef = 0
                p_value = 1.0
                confidence_interval = (0, 0)
            
            # Determine strength and direction
            abs_corr = abs(corr_coef)
            if abs_corr >= 0.7:
                strength = 'strong'
            elif abs_corr >= 0.3:
                strength = 'moderate'
            else:
                strength = 'weak'
            
            direction = 'positive' if corr_coef > 0 else 'negative'
            
            # Generate interpretation
            interpretation = self._generate_correlation_interpretation(
                feature, metric, corr_coef, p_value, strength, direction
            )
            
            return CorrelationResult(
                feature=feature,
                metric=metric,
                correlation_coefficient=corr_coef,
                p_value=p_value,
                strength=strength,
                direction=direction,
                significance_level=significance_threshold,
                sample_size=len(clean_df),
                confidence_interval=confidence_interval,
                interpretation=interpretation
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating correlation: {e}")
            return None
    
    def _extract_content_features(self, row) -> Optional[Dict[str, float]]:
        """Extract content features from database row"""
        try:
            features = {}
            
            # Basic features
            features[ContentFeature.DURATION.value] = float(row['duration'] or 0)
            features[ContentFeature.VIDEO_QUALITY.value] = float(row['quality_score'] or 0)
            features[ContentFeature.SCENE_COUNT.value] = float(row['scene_count'] or 0)
            
            # Text features
            if row['voiceover_text']:
                text_length = len(row['voiceover_text'])
                features[ContentFeature.TEXT_DENSITY.value] = text_length / (row['duration'] or 1)
            
            # Categorical features (will be handled differently)
            if row['tone']:
                features[ContentFeature.TONE.value] = str(row['tone'])
            
            if row['target_audience']:
                features[ContentFeature.TARGET_AUDIENCE.value] = str(row['target_audience'])
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error extracting features: {e}")
            return None
    
    def _extract_performance_metrics(self, row) -> Optional[Dict[str, float]]:
        """Extract performance metrics from database row"""
        try:
            metrics = {}
            
            # Engagement metrics
            metrics[PerformanceMetric.VIEWS.value] = float(row['views'] or 0)
            metrics[PerformanceMetric.LIKES.value] = float(row['likes'] or 0)
            metrics[PerformanceMetric.COMMENTS.value] = float(row['comments_count'] or 0)
            metrics[PerformanceMetric.ENGAGEMENT_RATE.value] = float(row['engagement_rate'] or 0)
            metrics[PerformanceMetric.WATCH_TIME.value] = float(row['watch_time'] or 0)
            metrics[PerformanceMetric.PERFORMANCE_SCORE.value] = float(row['performance_score'] or 0)
            
            # Sentiment
            if row['avg_sentiment_score'] is not None:
                metrics[PerformanceMetric.SENTIMENT_SCORE.value] = float(row['avg_sentiment_score'])
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error extracting performance metrics: {e}")
            return None
    
    def _generate_correlation_interpretation(
        self,
        feature: ContentFeature,
        metric: PerformanceMetric,
        correlation: float,
        p_value: float,
        strength: str,
        direction: str
    ) -> str:
        """Generate human-readable interpretation of correlation"""
        
        significance = "statistically significant" if p_value < 0.05 else "not statistically significant"
        
        interpretation_templates = {
            ContentFeature.DURATION: {
                PerformanceMetric.ENGAGEMENT_RATE: f"Video duration shows a {strength} {direction} correlation with engagement rate",
                PerformanceMetric.VIEWS: f"Video duration shows a {strength} {direction} correlation with views"
            },
            ContentFeature.VIDEO_QUALITY: {
                PerformanceMetric.PERFORMANCE_SCORE: f"Video quality shows a {strength} {direction} correlation with overall performance"
            },
            ContentFeature.SCENE_COUNT: {
                PerformanceMetric.ENGAGEMENT_RATE: f"Scene count shows a {strength} {direction} correlation with engagement rate"
            }
        }
        
        base_interpretation = interpretation_templates.get(feature, {}).get(
            metric, 
            f"{feature.value} shows a {strength} {direction} correlation with {metric.value}"
        )
        
        return f"{base_interpretation} (r={correlation:.3f}, p={p_value:.3f}, {significance})"
    
    async def get_feature_importance(
        self,
        target_metric: PerformanceMetric,
        content_ids: Optional[List[str]] = None,
        top_n: int = 10
    ) -> List[FeatureImportance]:
        """Get feature importance ranking for predicting a target metric"""
        
        try:
            # Get data for analysis
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            query = """
            SELECT 
                gc.id,
                gc.duration,
                gc.quality_score,
                COUNT(s.id) as scene_count,
                s.voiceover_text,
                p.tone,
                p.target_audience,
                pm.engagement_rate,
                pm.views,
                pm.performance_score
            FROM generated_content gc
            LEFT JOIN scenes s ON gc.scene_id = s.id
            LEFT JOIN scripts sc ON s.script_id = sc.id
            LEFT JOIN projects p ON sc.project_id = p.id
            LEFT JOIN performance_metrics pm ON gc.id = pm.content_id
            WHERE gc.created_at >= $1 AND gc.created_at <= $2
            """
            
            params = [start_date, end_date]
            
            if content_ids:
                query += " AND gc.id = ANY($3)"
                params.append(content_ids)
            
            rows = await self.db_pool.fetch(query, *params)
            
            if len(rows) < 20:
                return []
            
            # Convert to DataFrame
            data = []
            for row in rows:
                feature_data = {
                    'duration': row['duration'] or 0,
                    'quality_score': row['quality_score'] or 0,
                    'scene_count': row['scene_count'] or 0,
                    'text_length': len(row['voiceover_text']) if row['voiceover_text'] else 0,
                }
                
                # Encode categorical variables
                tone_encoding = {'professional': 1, 'casual': 2, 'educational': 3, 'entertaining': 4, 'motivational': 5}
                feature_data['tone_encoded'] = tone_encoding.get(row['tone'], 3)
                
                audience_encoding = {'general': 1, 'professional': 2, 'students': 3, 'entrepreneurs': 4}
                feature_data['audience_encoded'] = audience_encoding.get(row['target_audience'], 1)
                
                # Target variable
                target_value = getattr(row, target_metric.value) or 0
                feature_data['target'] = target_value
                
                if target_value > 0:  # Only include content with performance data
                    data.append(feature_data)
            
            if len(data) < 20:
                return []
            
            df = pd.DataFrame(data)
            
            # Calculate feature importance using correlation with target
            feature_importance = []
            features = ['duration', 'quality_score', 'scene_count', 'text_length', 'tone_encoded', 'audience_encoded']
            
            for feature in features:
                if feature in df.columns and 'target' in df.columns:
                    correlation = abs(df[feature].corr(df['target']))
                    if not np.isnan(correlation):
                        importance_score = correlation
                        
                        # Categorize predictive power
                        if importance_score >= 0.7:
                            predictive_power = 'high'
                        elif importance_score >= 0.3:
                            predictive_power = 'medium'
                        else:
                            predictive_power = 'low'
                        
                        feature_importance.append(FeatureImportance(
                            feature=ContentFeature(feature.split('_')[0]) if feature in [f.value for f in ContentFeature] else ContentFeature.TEXT_DENSITY,
                            importance_score=importance_score,
                            rank=0,  # Will be set after sorting
                            correlation_with_target=correlation,
                            predictive_power=predictive_power
                        ))
            
            # Sort by importance and assign ranks
            feature_importance.sort(key=lambda x: x.importance_score, reverse=True)
            for i, item in enumerate(feature_importance):
                item.rank = i + 1
            
            return feature_importance[:top_n]
            
        except Exception as e:
            self.logger.error(f"Error calculating feature importance: {e}")
            return []
    
    async def analyze_platform_differences(
        self,
        metric: PerformanceMetric,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """Analyze performance differences across platforms"""
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=time_period_days)
            
            query = """
            SELECT 
                gc.platform,
                AVG(pm.engagement_rate) as avg_engagement,
                AVG(pm.views) as avg_views,
                AVG(pm.likes) as avg_likes,
                AVG(pm.performance_score) as avg_performance,
                COUNT(gc.id) as content_count,
                STDDEV(pm.engagement_rate) as engagement_std,
                STDDEV(pm.views) as views_std
            FROM generated_content gc
            JOIN performance_metrics pm ON gc.id = pm.content_id
            WHERE gc.created_at >= $1 AND gc.created_at <= $2
            GROUP BY gc.platform
            HAVING COUNT(gc.id) >= 5
            ORDER BY avg_performance DESC
            """
            
            rows = await self.db_pool.fetch(query, start_date, end_date)
            
            if len(rows) < 2:
                return {'platforms': [], 'analysis': 'insufficient_data'}
            
            # Analyze differences
            platforms_data = []
            for row in rows:
                platforms_data.append({
                    'platform': row['platform'],
                    'avg_engagement_rate': float(row['avg_engagement'] or 0),
                    'avg_views': float(row['avg_views'] or 0),
                    'avg_likes': float(row['avg_likes'] or 0),
                    'avg_performance_score': float(row['avg_performance'] or 0),
                    'content_count': int(row['content_count']),
                    'engagement_std': float(row['engagement_std'] or 0),
                    'views_std': float(row['views_std'] or 0)
                })
            
            # Statistical tests
            best_platform = platforms_data[0]['platform']
            worst_platform = platforms_data[-1]['platform']
            
            return {
                'platforms': platforms_data,
                'best_performing_platform': best_platform,
                'worst_performing_platform': worst_platform,
                'analysis_period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'key_insights': self._generate_platform_insights(platforms_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing platform differences: {e}")
            raise
    
    def _generate_platform_insights(self, platforms_data: List[Dict]) -> List[str]:
        """Generate insights about platform performance differences"""
        insights = []
        
        if len(platforms_data) >= 2:
            best = platforms_data[0]
            worst = platforms_data[-1]
            
            performance_gap = best['avg_performance_score'] - worst['avg_performance_score']
            if performance_gap > 0.5:
                insights.append(f"{best['platform']} significantly outperforms {worst['platform']} by {performance_gap:.2f} points")
            
            engagement_gap = best['avg_engagement_rate'] - worst['avg_engagement_rate']
            if engagement_gap > 0.1:
                insights.append(f"{best['platform']} has {engagement_gap:.1%} higher engagement rate than {worst['platform']}")
            
            # Consistency analysis
            most_consistent = min(platforms_data, key=lambda x: x['engagement_std'])
            insights.append(f"{most_consistent['platform']} shows the most consistent performance (lowest variation)")
        
        return insights
    
    async def clear_cache(self):
        """Clear cached analysis results"""
        self._cached_analysis.clear()