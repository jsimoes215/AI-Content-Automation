"""
Trend Analyzer Module

Identifies and analyzes trends in content performance over time.
Provides forecasting and pattern recognition capabilities.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

import asyncpg
import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings('ignore')


class TrendDirection(Enum):
    """Trend direction indicators"""
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    VOLATILE = "volatile"
    CYCLICAL = "cyclical"
    SEASONAL = "seasonal"


class TrendStrength(Enum):
    """Strength of trend indicators"""
    VERY_WEAK = "very_weak"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


@dataclass
class TrendPoint:
    """A point in a trend analysis"""
    timestamp: datetime
    value: float
    trend_type: str
    significance: float


@dataclass
class TrendAnalysis:
    """Complete trend analysis result"""
    metric_name: str
    time_period: Tuple[datetime, datetime]
    overall_direction: TrendDirection
    strength: TrendStrength
    trend_points: List[TrendPoint]
    seasonality_patterns: List[Dict[str, Any]]
    change_points: List[Dict[str, Any]]
    predictions: List[Dict[str, Any]]
    key_insights: List[str]
    statistical_metrics: Dict[str, float]


@dataclass
class SeasonalPattern:
    """Seasonal pattern detected in data"""
    period: str  # 'daily', 'weekly', 'monthly'
    peak_times: List[str]
    low_times: List[str]
    amplitude: float
    reliability: float


@dataclass
class ForecastPoint:
    """Single forecast point"""
    timestamp: datetime
    predicted_value: float
    confidence_interval: Tuple[float, float]
    prediction_confidence: float


class TrendAnalyzer:
    """Analyzes trends and patterns in performance data"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.logger = logging.getLogger(__name__)
        self._trend_cache = {}
        self._cache_duration = timedelta(hours=2)
        
    async def analyze_trend(
        self,
        content_id: str,
        metric_name: str,
        time_period_days: int = 90,
        forecast_days: int = 30
    ) -> Optional[TrendAnalysis]:
        """Analyze trend for a specific metric of content"""
        
        cache_key = f"trend:{content_id}:{metric_name}:{time_period_days}:{forecast_days}"
        
        if cache_key in self._trend_cache:
            cached_entry = self._trend_cache[cache_key]
            if datetime.now() - cached_entry['timestamp'] < self._cache_duration:
                return cached_entry['data']
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=time_period_days)
            
            # Get time series data
            query = """
            SELECT 
                DATE_TRUNC('day', timestamp) as date,
                AVG((metrics->>$1)::float) as avg_value,
                SUM((metrics->>$1)::float) as total_value,
                COUNT(*) as data_points
            FROM engagement_snapshots 
            WHERE content_id = $2 
            AND timestamp >= $3 
            AND timestamp <= $4
            AND metrics ? $1
            GROUP BY DATE_TRUNC('day', timestamp)
            ORDER BY date
            """
            
            rows = await self.db_pool.fetch(
                query, metric_name, content_id, start_date, end_date
            )
            
            if len(rows) < 7:  # Need at least a week of data
                return None
            
            # Prepare data for analysis
            dates = []
            values = []
            
            for row in rows:
                dates.append(row['date'])
                values.append(float(row['avg_value'] or 0))
            
            # Perform trend analysis
            trend_analysis = await self._perform_trend_analysis(
                dates, values, metric_name, time_period_days, forecast_days
            )
            
            # Cache result
            self._trend_cache[cache_key] = {
                'data': trend_analysis,
                'timestamp': datetime.now()
            }
            
            return trend_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing trend: {e}")
            raise
    
    async def _perform_trend_analysis(
        self,
        dates: List[datetime],
        values: List[float],
        metric_name: str,
        time_period_days: int,
        forecast_days: int
    ) -> TrendAnalysis:
        """Perform comprehensive trend analysis"""
        
        try:
            # Convert to pandas for easier analysis
            df = pd.DataFrame({
                'date': dates,
                'value': values
            }).set_index('date').sort_index()
            
            # Smooth data using moving average
            df['smoothed'] = df['value'].rolling(window=min(7, len(df)//3), center=True).mean()
            
            # Calculate overall trend using linear regression
            x = np.arange(len(df))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, df['value'].fillna(method='bfill'))
            
            # Determine trend direction and strength
            if p_value > 0.05:  # Not statistically significant
                direction = TrendDirection.STABLE
                strength = TrendStrength.WEAK
            elif abs(slope) < 0.01:
                direction = TrendDirection.STABLE
                strength = TrendStrength.WEAK
            elif slope > 0:
                direction = TrendDirection.RISING
            else:
                direction = TrendDirection.FALLING
            
            # Determine strength based on R-squared
            r_squared = r_value ** 2
            if r_squared >= 0.81:
                strength = TrendStrength.VERY_STRONG
            elif r_squared >= 0.64:
                strength = TrendStrength.STRONG
            elif r_squared >= 0.36:
                strength = TrendStrength.MODERATE
            elif r_squared >= 0.16:
                strength = TrendStrength.WEAK
            else:
                strength = TrendStrength.VERY_WEAK
            
            # Detect change points using statistical methods
            change_points = await self._detect_change_points(df['value'].fillna(0))
            
            # Detect seasonal patterns
            seasonal_patterns = await self._detect_seasonal_patterns(df)
            
            # Generate predictions
            predictions = await self._generate_forecasts(
                df, forecast_days, slope, intercept, r_squared
            )
            
            # Extract trend points
            trend_points = []
            for i, (date, value) in enumerate(zip(df.index, df['value'])):
                trend_type = await self._classify_trend_point(
                    i, df['value'].tolist(), slope
                )
                
                trend_points.append(TrendPoint(
                    timestamp=date,
                    value=value,
                    trend_type=trend_type,
                    significance=abs(r_value) if i < len(df) * 0.8 else abs(r_value) * 0.8  # Reduce confidence for recent points
                ))
            
            # Generate insights
            insights = self._generate_trend_insights(
                direction, strength, r_squared, seasonal_patterns, change_points
            )
            
            # Calculate statistical metrics
            statistical_metrics = {
                'mean': float(df['value'].mean()),
                'median': float(df['value'].median()),
                'std_dev': float(df['value'].std()),
                'min_value': float(df['value'].min()),
                'max_value': float(df['value'].max()),
                'coefficient_of_variation': float(df['value'].std() / df['value'].mean()) if df['value'].mean() > 0 else 0,
                'trend_slope': float(slope),
                'r_squared': float(r_squared),
                'p_value': float(p_value),
                'volatility': await self._calculate_volatility(df['value'].fillna(0))
            }
            
            return TrendAnalysis(
                metric_name=metric_name,
                time_period=(dates[0], dates[-1]),
                overall_direction=direction,
                strength=strength,
                trend_points=trend_points,
                seasonality_patterns=[asdict(pattern) for pattern in seasonal_patterns],
                change_points=change_points,
                predictions=predictions,
                key_insights=insights,
                statistical_metrics=statistical_metrics
            )
            
        except Exception as e:
            self.logger.error(f"Error performing trend analysis: {e}")
            raise
    
    async def _detect_change_points(self, values: pd.Series) -> List[Dict[str, Any]]:
        """Detect points where the trend changes significantly"""
        
        try:
            change_points = []
            
            # Use rolling statistics to detect changes
            window_size = min(7, len(values) // 4)
            
            for i in range(window_size, len(values) - window_size):
                before_window = values.iloc[i-window_size:i].mean()
                after_window = values.iloc[i:i+window_size].mean()
                
                # Calculate change magnitude
                if before_window > 0:
                    change_magnitude = abs(after_window - before_window) / before_window
                else:
                    change_magnitude = abs(after_window - before_window)
                
                # Significant change threshold
                if change_magnitude > 0.2:  # 20% change
                    change_points.append({
                        'index': i,
                        'timestamp': values.index[i].isoformat(),
                        'change_magnitude': change_magnitude,
                        'change_direction': 'increase' if after_window > before_window else 'decrease',
                        'before_value': before_window,
                        'after_value': after_window
                    })
            
            return change_points
            
        except Exception as e:
            self.logger.error(f"Error detecting change points: {e}")
            return []
    
    async def _detect_seasonal_patterns(self, df: pd.DataFrame) -> List[SeasonalPattern]:
        """Detect seasonal patterns in the data"""
        
        patterns = []
        
        try:
            # Daily patterns (if enough data)
            if len(df) >= 14:
                daily_pattern = await self._analyze_daily_patterns(df)
                if daily_pattern:
                    patterns.append(daily_pattern)
            
            # Weekly patterns (if enough data)
            if len(df) >= 28:
                weekly_pattern = await self._analyze_weekly_patterns(df)
                if weekly_pattern:
                    patterns.append(weekly_pattern)
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting seasonal patterns: {e}")
            return []
    
    async def _analyze_daily_patterns(self, df: pd.DataFrame) -> Optional[SeasonalPattern]:
        """Analyze daily patterns in the data"""
        
        try:
            # Group by hour of day (if timestamps have time info)
            df_reset = df.reset_index()
            df_reset['hour'] = df_reset['date'].dt.hour
            
            hourly_avg = df_reset.groupby('hour')['value'].mean()
            
            if len(hourly_avg) > 0:
                peak_hour = hourly_avg.idxmax()
                low_hour = hourly_avg.idxmin()
                
                # Calculate amplitude
                amplitude = (hourly_avg.max() - hourly_avg.min()) / hourly_avg.mean()
                
                # Calculate reliability based on data consistency
                reliability = 1 - (hourly_avg.std() / hourly_avg.mean()) if hourly_avg.mean() > 0 else 0
                reliability = max(0, min(1, reliability))
                
                if amplitude > 0.1:  # Only if pattern is significant
                    return SeasonalPattern(
                        period='daily',
                        peak_times=[f"{peak_hour:02d}:00"],
                        low_times=[f"{low_hour:02d}:00"],
                        amplitude=amplitude,
                        reliability=reliability
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing daily patterns: {e}")
            return None
    
    async def _analyze_weekly_patterns(self, df: pd.DataFrame) -> Optional[SeasonalPattern]:
        """Analyze weekly patterns in the data"""
        
        try:
            df_reset = df.reset_index()
            df_reset['day_of_week'] = df_reset['date'].dt.dayofweek  # 0=Monday
            
            daily_avg = df_reset.groupby('day_of_week')['value'].mean()
            
            if len(daily_avg) > 0:
                peak_day = daily_avg.idxmax()
                low_day = daily_avg.idxmin()
                
                # Map to day names
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                amplitude = (daily_avg.max() - daily_avg.min()) / daily_avg.mean()
                reliability = 1 - (daily_avg.std() / daily_avg.mean()) if daily_avg.mean() > 0 else 0
                reliability = max(0, min(1, reliability))
                
                if amplitude > 0.1:
                    return SeasonalPattern(
                        period='weekly',
                        peak_times=[day_names[peak_day]],
                        low_times=[day_names[low_day]],
                        amplitude=amplitude,
                        reliability=reliability
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing weekly patterns: {e}")
            return None
    
    async def _generate_forecasts(
        self,
        df: pd.DataFrame,
        forecast_days: int,
        slope: float,
        intercept: float,
        r_squared: float
    ) -> List[Dict[str, Any]]:
        """Generate forecasts using linear trend and confidence intervals"""
        
        try:
            predictions = []
            last_index = len(df) - 1
            last_value = df['value'].iloc[-1]
            
            # Forecast confidence based on R-squared
            base_confidence = min(0.9, max(0.1, r_squared))
            
            for i in range(1, forecast_days + 1):
                # Linear extrapolation
                predicted_value = last_value + (slope * i)
                
                # Expand confidence interval over time
                time_factor = i / forecast_days
                confidence_interval_expansion = 0.1 + (0.4 * time_factor)
                
                lower_bound = predicted_value * (1 - confidence_interval_expansion)
                upper_bound = predicted_value * (1 + confidence_interval_expansion)
                
                # Reduce confidence over time
                prediction_confidence = base_confidence * (1 - time_factor * 0.5)
                
                forecast_date = df.index[-1] + timedelta(days=i)
                
                predictions.append({
                    'timestamp': forecast_date.isoformat(),
                    'predicted_value': float(predicted_value),
                    'confidence_interval': [float(lower_bound), float(upper_bound)],
                    'prediction_confidence': float(prediction_confidence),
                    'forecast_day': i
                })
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error generating forecasts: {e}")
            return []
    
    async def _classify_trend_point(self, index: int, values: List[float], slope: float) -> str:
        """Classify the type of trend point"""
        
        if index < 2 or index >= len(values) - 2:
            return "boundary"
        
        # Calculate local trend
        before_avg = np.mean(values[max(0, index-2):index])
        after_avg = np.mean(values[index:min(len(values), index+3)])
        
        local_slope = after_avg - before_avg
        
        # Compare with overall trend
        if abs(local_slope - slope) < 0.1 * abs(slope):
            return "consistent"
        elif local_slope > slope:
            return "acceleration"
        else:
            return "deceleration"
    
    def _generate_trend_insights(
        self,
        direction: TrendDirection,
        strength: TrendStrength,
        r_squared: float,
        seasonal_patterns: List[SeasonalPattern],
        change_points: List[Dict]
    ) -> List[str]:
        """Generate insights based on trend analysis"""
        
        insights = []
        
        # Direction and strength insights
        if direction == TrendDirection.RISING:
            insights.append(f"Strong upward trend detected (R² = {r_squared:.3f})")
        elif direction == TrendDirection.FALLING:
            insights.append(f"Declining trend detected (R² = {r_squared:.3f})")
        elif direction == TrendDirection.STABLE:
            insights.append("Performance appears stable over the analyzed period")
        
        # Strength insights
        if strength in [TrendStrength.STRONG, TrendStrength.VERY_STRONG]:
            insights.append("Trend shows high predictability and consistency")
        elif strength in [TrendStrength.VERY_WEAK, TrendStrength.WEAK]:
            insights.append("Trend shows high variability and low predictability")
        
        # Seasonality insights
        for pattern in seasonal_patterns:
            if pattern.period == 'weekly' and pattern.reliability > 0.6:
                insights.append(f"Strong weekly pattern detected: peaks on {', '.join(pattern.peak_times)}")
            elif pattern.period == 'daily' and pattern.reliability > 0.6:
                insights.append(f"Daily performance varies significantly with peak at {pattern.peak_times[0]}")
        
        # Change points insights
        if change_points:
            significant_changes = [cp for cp in change_points if cp['change_magnitude'] > 0.3]
            if significant_changes:
                insights.append(f"{len(significant_changes)} major performance shifts detected")
                latest_change = max(change_points, key=lambda x: x['change_magnitude'])
                insights.append(f"Largest change occurred on {latest_change['timestamp'][:10]} with {latest_change['change_direction']}")
        
        return insights
    
    async def _calculate_volatility(self, values: pd.Series) -> float:
        """Calculate volatility as coefficient of variation"""
        
        try:
            if len(values) < 2:
                return 0.0
            
            mean_val = values.mean()
            if mean_val == 0:
                return 0.0
            
            return float(values.std() / mean_val)
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility: {e}")
            return 0.0
    
    async def get_trending_content(
        self,
        platform: str,
        time_period_days: int = 7,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """Get content with strongest upward trends"""
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=time_period_days)
            
            query = """
            SELECT 
                es.content_id,
                COUNT(*) as data_points,
                AVG((metrics->>'engagement_rate')::float) as avg_engagement,
                STDDEV((metrics->>'engagement_rate')::float) as engagement_std,
                MIN(timestamp) as first_data,
                MAX(timestamp) as last_data
            FROM engagement_snapshots es
            JOIN generated_content gc ON es.content_id = gc.id
            WHERE es.platform = $1 
            AND es.timestamp >= $2 
            AND es.timestamp <= $3
            AND metrics ? 'engagement_rate'
            GROUP BY es.content_id
            HAVING COUNT(*) >= 5
            ORDER BY avg_engagement DESC
            """
            
            rows = await self.db_pool.fetch(query, platform, start_date, end_date)
            
            trending_content = []
            
            for row in rows:
                # Analyze trend for this content
                trend_analysis = await self.analyze_trend(
                    str(row['content_id']),
                    'engagement_rate',
                    time_period_days,
                    0  # No forecasting needed
                )
                
                if trend_analysis and trend_analysis.overall_direction == TrendDirection.RISING:
                    trending_content.append({
                        'content_id': str(row['content_id']),
                        'current_engagement': float(row['avg_engagement'] or 0),
                        'trend_direction': trend_analysis.overall_direction.value,
                        'trend_strength': trend_analysis.strength.value,
                        'r_squared': trend_analysis.statistical_metrics['r_squared'],
                        'volatility': trend_analysis.statistical_metrics['volatility']
                    })
            
            # Sort by trend strength and current performance
            trending_content.sort(key=lambda x: (x['r_squared'], x['current_engagement']), reverse=True)
            
            return trending_content[:top_n]
            
        except Exception as e:
            self.logger.error(f"Error getting trending content: {e}")
            raise
    
    async def compare_content_trends(
        self,
        content_ids: List[str],
        metric_name: str = 'engagement_rate',
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """Compare trends across multiple content pieces"""
        
        try:
            comparisons = []
            
            for content_id in content_ids:
                trend_analysis = await self.analyze_trend(
                    content_id, metric_name, time_period_days, 0
                )
                
                if trend_analysis:
                    comparisons.append({
                        'content_id': content_id,
                        'direction': trend_analysis.overall_direction.value,
                        'strength': trend_analysis.strength.value,
                        'r_squared': trend_analysis.statistical_metrics['r_squared'],
                        'slope': trend_analysis.statistical_metrics['trend_slope'],
                        'mean_value': trend_analysis.statistical_metrics['mean'],
                        'volatility': trend_analysis.statistical_metrics['volatility']
                    })
            
            if not comparisons:
                return {'comparison': [], 'summary': 'no_data'}
            
            # Generate comparison insights
            best_trend = max(comparisons, key=lambda x: x['slope'])
            most_stable = min(comparisons, key=lambda x: x['volatility'])
            highest_performance = max(comparisons, key=lambda x: x['mean_value'])
            
            return {
                'comparison': comparisons,
                'insights': {
                    'best_trending_content': best_trend['content_id'],
                    'most_stable_content': most_stable['content_id'],
                    'highest_performing_content': highest_performance['content_id'],
                    'trend_summary': f"Trends range from {min(c['slope'] for c in comparisons):.3f} to {max(c['slope'] for c in comparisons):.3f}",
                    'performance_summary': f"Average performance: {np.mean([c['mean_value'] for c in comparisons]):.3f}"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error comparing content trends: {e}")
            raise
    
    async def clear_cache(self):
        """Clear cached trend analyses"""
        self._trend_cache.clear()