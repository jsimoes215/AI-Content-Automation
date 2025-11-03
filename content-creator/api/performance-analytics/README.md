# Performance Analytics Dashboard System

A comprehensive analytics system for tracking, analyzing, and optimizing content performance across multiple platforms. This system provides real-time engagement tracking, correlation analysis between content features and performance, trend identification, and actionable optimization recommendations.

## 🚀 Features

### Core Analytics Modules

#### 📊 Engagement Tracker
- **Real-time Metrics Collection**: Track views, likes, comments, shares, engagement rates, and watch time
- **Multi-platform Support**: YouTube, TikTok, Instagram, LinkedIn, Twitter
- **Batch Processing**: Handle large volumes of engagement data efficiently
- **Anomaly Detection**: Identify statistical anomalies using Z-score analysis
- **Caching Layer**: Optimized performance with intelligent caching

#### 🔗 Correlation Analyzer
- **Feature-Performance Analysis**: Analyze correlations between content features and performance metrics
- **Statistical Significance Testing**: Pearson correlation with confidence intervals
- **Feature Importance Ranking**: Identify most predictive content characteristics
- **Platform Comparison**: Compare performance patterns across platforms
- **Categorical & Continuous Variables**: Handle both types of data appropriately

#### 📈 Trend Analyzer
- **Trend Detection**: Identify rising, falling, stable, and cyclical trends
- **Seasonal Pattern Recognition**: Detect daily, weekly, and monthly patterns
- **Change Point Detection**: Find significant performance shifts
- **Forecasting**: Generate predictions with confidence intervals
- **Volatility Analysis**: Measure performance consistency

#### 📋 Analytics Dashboard
- **Unified Interface**: Access all analytics features through one dashboard
- **Real-time Overview**: High-level performance summary with key metrics
- **Content Performance Summaries**: Detailed analysis for individual content
- **Platform Analytics**: Platform-specific insights and comparisons
- **Optimization Insights**: Actionable recommendations with impact predictions

### Advanced Features

- **A/B Testing Analysis**: Enhanced statistical analysis for content variations
- **Performance Benchmarks**: Industry and platform-specific benchmarks
- **Data Export**: JSON, CSV, and Excel export capabilities
- **Real-time APIs**: RESTful endpoints for integration
- **Background Processing**: Efficient handling of large-scale analytics
- **Error Handling & Logging**: Comprehensive error tracking and reporting

## 📁 Project Structure

```
api/performance-analytics/
├── __init__.py                 # Module initialization
├── engagement_tracker.py       # Engagement metrics tracking
├── correlation_analyzer.py     # Feature-performance correlation analysis
├── trend_analyzer.py          # Trend detection and forecasting
├── analytics_dashboard.py     # Unified dashboard interface
├── integration.py             # Integration manager and examples
├── config.py                  # Configuration settings
├── api_endpoints.py           # FastAPI endpoints
└── README.md                  # This file
```

## 🗄️ Database Schema

The system requires several new tables for comprehensive analytics:

### Core Tables

- **`engagement_snapshots`**: Real-time engagement metrics
- **`content_performance_history`**: Aggregated historical data
- **`content_feature_analysis`**: Extracted content features
- **`correlation_analysis_results`**: Statistical correlation results
- **`trend_analysis_results`**: Trend analysis with forecasts
- **`optimization_insights`**: Actionable optimization recommendations

### Supporting Tables

- **`ab_test_performance`**: Enhanced A/B testing analytics
- **`performance_benchmarks`**: Platform and industry benchmarks

### Key Features

- **Comprehensive Indexing**: Optimized for analytics queries
- **Materialized Views**: Pre-calculated common analytics views
- **Analytics Functions**: Built-in SQL functions for trend analysis
- **Row Level Security**: Secure data access patterns

## 🚀 Quick Start

### 1. Database Setup

Run the performance analytics migration:

```sql
-- Apply the migration
\i database/migrations/performance_analytics_migration.sql

-- Verify tables were created
\dt engagement_snapshots
\dt content_feature_analysis
\dt correlation_analysis_results
\dt trend_analysis_results
\dt optimization_insights
```

### 2. Initialize Analytics System

```python
import asyncio
from api.performance_analytics.integration import PerformanceAnalyticsManager

async def initialize_analytics():
    # Initialize with database pool
    manager = PerformanceAnalyticsManager(db_pool)
    await manager.initialize_system()
    
    print("Analytics system initialized!")

# Run initialization
asyncio.run(initialize_analytics())
```

### 3. Track Content Performance

```python
# Track engagement metrics
metrics = {
    'views': 1500,
    'likes': 120,
    'comments': 25,
    'shares': 8,
    'engagement_rate': 0.085,
    'watch_time': 1200
}

snapshot_id = await manager.track_content_performance(
    content_id="content-123",
    platform="youtube", 
    metrics=metrics,
    metadata={'title': 'My Great Video'}
)
```

### 4. Analyze Performance

```python
# Comprehensive content analysis
analysis = await manager.analyze_content_performance(
    content_id="content-123",
    analysis_type="comprehensive"
)

# Get platform insights
platform_insights = await manager.get_platform_insights(
    platform="youtube",
    timeframe="30d"
)

# Generate optimization recommendations
recommendations = await manager.generate_optimization_recommendations(
    platforms=["youtube", "tiktok"],
    content_ids=["content-123", "content-456"]
)
```

### 5. Compare Content Performance

```python
# Compare multiple content pieces
comparison = await manager.compare_content_performance(
    content_ids=["content-1", "content-2", "content-3"],
    metrics=["views", "engagement_rate", "performance_score"]
)
```

## 🌐 API Endpoints

The system provides RESTful API endpoints through FastAPI:

### Core Endpoints

```
POST /analytics/engagement/track          # Track engagement metrics
POST /analytics/engagement/batch-track    # Batch track multiple metrics
POST /analytics/content/analyze           # Analyze content performance
POST /analytics/platform/insights         # Get platform insights
POST /analytics/optimization/recommendations # Get optimization insights
POST /analytics/content/compare           # Compare content performance
```

### Dashboard Endpoints

```
GET /analytics/dashboard/overview         # Get dashboard overview
GET /analytics/dashboard/trending         # Get trending content
```

### Real-time Endpoints

```
GET /analytics/realtime/metrics/{id}      # Get real-time metrics
GET /analytics/realtime/platform-metrics/{platform} # Platform metrics
```

### System Endpoints

```
GET /analytics/health                     # Health check
GET /analytics/system/status             # System status
DELETE /analytics/admin/cleanup          # Clean up old data
POST /analytics/admin/recalculate        # Recalculate analytics
```

### Example API Usage

```bash
# Track engagement
curl -X POST "http://localhost:8000/analytics/engagement/track" \
     -H "Content-Type: application/json" \
     -d '{
       "content_id": "content-123",
       "platform": "youtube",
       "metrics": {
         "views": 1500,
         "likes": 120,
         "engagement_rate": 0.085
       }
     }'

# Get dashboard overview
curl "http://localhost:8000/analytics/dashboard/overview?timeframe=30d"

# Get platform insights
curl -X POST "http://localhost:8000/analytics/platform/insights" \
     -H "Content-Type: application/json" \
     -d '{"platform": "youtube", "timeframe": "30d"}'
```

## 📊 Configuration

### Environment Configuration

```python
from api.performance_analytics.config import get_config_for_environment

# Get configuration for different environments
dev_config = get_config_for_environment('development')
prod_config = get_config_for_environment('production')

# Access configuration values
cache_ttl = dev_config.CACHE_TTL_SECONDS
min_data_points = dev_config.MIN_DATA_POINTS_FOR_ANALYSIS
correlation_threshold = dev_config.CORRELATION_SIGNIFICANCE_THRESHOLD
```

### Platform-Specific Configuration

```python
config = AnalyticsConfig()

# Get YouTube configuration
youtube_config = config.get_platform_config('youtube')
print(f"YouTube engagement benchmark: {youtube_config['benchmark_engagement_rate']}")

# Get TikTok configuration  
tiktok_config = config.get_platform_config('tiktok')
print(f"TikTok update frequency: {tiktok_config['update_frequency_minutes']} minutes")
```

### Custom Configuration

```python
# Create custom configuration
class CustomConfig(AnalyticsConfig):
    CACHE_TTL_SECONDS = 600  # 10 minutes
    CORRELATION_SIGNIFICANCE_THRESHOLD = 0.01  # More strict
    MIN_DATA_POINTS_FOR_ANALYSIS = 15
    
    # Custom thresholds
    LOW_PERFORMANCE_THRESHOLD = 2.5
    HIGH_PERFORMANCE_THRESHOLD = 7.5
```

## 📈 Analytics Features

### Engagement Tracking

- **Real-time Metrics**: Track multiple metrics simultaneously
- **Batch Processing**: Handle thousands of metrics efficiently
- **Anomaly Detection**: Statistical outlier identification
- **Platform Aggregation**: Cross-platform metric comparison
- **Historical Analysis**: Time-series trend analysis

### Correlation Analysis

```python
# Analyze feature-performance correlations
correlations = await manager.correlation_analyzer.analyze_feature_correlations(
    content_ids=["content-1", "content-2", "content-3"],
    platforms=["youtube", "tiktok"],
    time_period_days=90
)

for correlation in correlations:
    print(f"{correlation.feature.value} → {correlation.metric.value}")
    print(f"  Correlation: {correlation.correlation_coefficient:.3f}")
    print(f"  Significance: p={correlation.p_value:.3f}")
    print(f"  Interpretation: {correlation.interpretation}")
```

### Trend Analysis

```python
# Analyze content trends
trend_analysis = await manager.trend_analyzer.analyze_trend(
    content_id="content-123",
    metric_name="engagement_rate",
    time_period_days=30,
    forecast_days=30
)

print(f"Trend Direction: {trend_analysis.overall_direction.value}")
print(f"Trend Strength: {trend_analysis.strength.value}")
print(f"R-squared: {trend_analysis.statistical_metrics['r_squared']:.3f}")

# Get trend insights
for insight in trend_analysis.key_insights:
    print(f"  - {insight}")
```

### Optimization Insights

```python
# Generate optimization recommendations
insights = await manager.dashboard.get_optimization_insights(
    timeframe=DashboardTimeframe.LAST_30_DAYS,
    platforms=["youtube", "tiktok"],
    top_n=10
)

for insight in insights:
    print(f"[{insight.priority.upper()}] {insight.title}")
    print(f"  {insight.description}")
    print(f"  Impact: {insight.impact_prediction}")
    print(f"  Difficulty: {insight.implementation_difficulty}")
```

## 🔧 Integration Examples

### Webhook Integration

```python
# Handle platform webhooks
from fastapi import FastAPI, WebSocket
import json

app = FastAPI()

@app.post("/webhook/youtube")
async def youtube_webhook(request: dict):
    # Extract metrics from webhook
    content_id = request['content_id']
    metrics = {
        'views': request['statistics']['viewCount'],
        'likes': request['statistics']['likeCount'],
        'engagement_rate': calculate_engagement_rate(request['statistics'])
    }
    
    # Track metrics
    await manager.track_content_performance(
        content_id=content_id,
        platform="youtube",
        metrics=metrics,
        metadata={'source': 'webhook'}
    )
    
    return {"status": "processed"}
```

### Cron Job Integration

```python
# Scheduled analytics updates
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

async def daily_analytics_update():
    """Run daily analytics calculations"""
    await manager.generate_optimization_recommendations()
    await manager.cleanup_old_data(retention_days=365)

# Schedule daily updates
scheduler = AsyncIOScheduler()
scheduler.add_job(daily_analytics_update, 'cron', hour=2)
scheduler.start()
```

### Background Task Integration

```python
# Background analytics processing
from celery import Celery

celery_app = Celery('analytics')

@celery_app.task
def process_analytics_batch(content_ids: list):
    """Process analytics for a batch of content"""
    loop = asyncio.get_event_loop()
    
    for content_id in content_ids:
        # Analyze content
        analysis = loop.run_until_complete(
            manager.analyze_content_performance(content_id)
        )
        
        # Store results
        store_analysis_results(content_id, analysis)
```

## 📊 Data Export

### Export Formats

```python
# JSON Export
json_export = await manager.export_analytics_data(
    format_type="json",
    timeframe="30d",
    platforms=["youtube", "tiktok"]
)

# CSV Export (processed in background)
await manager.export_analytics_data(
    format_type="csv",
    timeframe="90d"
)

# Excel Export (with metadata)
excel_export = await manager.export_analytics_data(
    format_type="excel",
    timeframe="1y",
    include_metadata=True
)
```

### Custom Exports

```python
# Export specific content analysis
specific_content = ["content-1", "content-2", "content-3"]
export_data = {
    "content_analysis": [],
    "optimization_insights": [],
    "performance_trends": []
}

for content_id in specific_content:
    analysis = await manager.analyze_content_performance(content_id)
    export_data["content_analysis"].append(analysis)

# Save to file
with open("content_analysis_export.json", "w") as f:
    json.dump(export_data, f, indent=2, default=str)
```

## 🧪 Testing

### Unit Tests

```python
import pytest
from api.performance_analytics.integration import PerformanceAnalyticsManager

@pytest.mark.asyncio
async def test_engagement_tracking():
    """Test engagement tracking functionality"""
    manager = PerformanceAnalyticsManager(db_pool)
    
    metrics = {'views': 1000, 'likes': 50, 'engagement_rate': 0.05}
    snapshot_id = await manager.track_content_performance(
        content_id="test-content",
        platform="youtube",
        metrics=metrics
    )
    
    assert snapshot_id is not None
    assert len(snapshot_id) > 0

@pytest.mark.asyncio
async def test_correlation_analysis():
    """Test correlation analysis"""
    manager = PerformanceAnalyticsManager(db_pool)
    
    correlations = await manager.correlation_analyzer.analyze_feature_correlations(
        time_period_days=30
    )
    
    assert isinstance(correlations, list)
    assert len(correlations) >= 0

@pytest.mark.asyncio
async def test_trend_analysis():
    """Test trend analysis"""
    manager = PerformanceAnalyticsManager(db_pool)
    
    trend_analysis = await manager.trend_analyzer.analyze_trend(
        content_id="test-content",
        metric_name="engagement_rate"
    )
    
    # Should return None for insufficient data
    assert trend_analysis is None or hasattr(trend_analysis, 'overall_direction')
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_analytics_pipeline():
    """Test complete analytics pipeline"""
    manager = PerformanceAnalyticsManager(db_pool)
    
    # 1. Track engagement
    await manager.track_content_performance(
        content_id="pipeline-test",
        platform="youtube",
        metrics={'views': 500, 'engagement_rate': 0.03}
    )
    
    # 2. Get dashboard overview
    overview = await manager.get_dashboard_overview(timeframe="7d")
    assert overview['total_content_pieces'] >= 1
    
    # 3. Generate insights
    insights = await manager.get_optimization_insights()
    assert isinstance(insights, list)
```

## 🔍 Monitoring and Logging

### Logging Configuration

```python
import logging
from api.performance_analytics.config import get_config_for_environment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analytics.log'),
        logging.StreamHandler()
    ]
)

# Set analytics-specific logging
analytics_logger = logging.getLogger('api.performance.analytics')
analytics_logger.setLevel(logging.DEBUG)
```

### Health Checks

```python
# Check system health
health_check = await manager.get_system_status()
print(f"Database: {health_check['database']}")
print(f"Cache Size: {health_check['cache']['size']}")
print(f"Supported Platforms: {len(health_check['configuration']['supported_platforms'])}")
```

### Performance Monitoring

```python
# Monitor cache performance
cache_stats = await manager.engagement_tracker.get_cache_stats()
print(f"Cache hit ratio would be calculated here")

# Monitor query performance
import time
start_time = time.time()
await manager.dashboard.get_dashboard_overview()
query_time = time.time() - start_time
print(f"Dashboard overview query took {query_time:.2f} seconds")
```

## 🚀 Deployment

### Production Deployment

```python
# Production configuration
from api.performance_analytics.config import ProductionConfig

config = ProductionConfig()

# Database configuration
DATABASE_URL = "postgresql://user:pass@localhost:5432/analytics_db"

# Cache configuration
REDIS_URL = "redis://localhost:6379/0"

# Analytics configuration
analytics_config = {
    'cache_ttl': config.CACHE_TTL_SECONDS,
    'db_pool_size': config.DB_POOL_SIZE,
    'retention_days': config.ENGAGEMENT_DATA_RETENTION_DAYS
}
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Deployment

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analytics-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: analytics-service
  template:
    metadata:
      labels:
        app: analytics-service
    spec:
      containers:
      - name: analytics
        image: analytics-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: analytics-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Issues

```python
# Check database connectivity
try:
    async with db_pool.acquire() as conn:
        result = await conn.fetchval("SELECT 1")
        print("Database connection successful")
except Exception as e:
    print(f"Database connection failed: {e}")
```

#### 2. Cache Issues

```python
# Clear cache if needed
await manager.engagement_tracker.clear_cache()
await manager.correlation_analyzer.clear_cache()
await manager.trend_analyzer.clear_cache()

# Check cache stats
cache_stats = await manager.engagement_tracker.get_cache_stats()
print(f"Cache entries: {cache_stats['cache_size']}")
```

#### 3. Performance Issues

```python
# Monitor query performance
import time

start = time.time()
result = await manager.get_dashboard_overview()
duration = time.time() - start

if duration > 5.0:
    print(f"Slow query detected: {duration:.2f} seconds")
    # Consider indexing or query optimization
```

#### 4. Memory Issues

```python
# Monitor memory usage
import psutil
import gc

# Force garbage collection
gc.collect()

# Check memory usage
process = psutil.Process()
memory_info = process.memory_info()
print(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")

# Reduce batch sizes if needed
batch_size = 100  # Default
if memory_info.rss > 1000 * 1024 * 1024:  # 1GB
    batch_size = 50
```

## 📚 API Reference

### Core Classes

#### PerformanceAnalyticsManager
Main manager class that orchestrates all analytics functionality.

```python
manager = PerformanceAnalyticsManager(db_pool)

# Core methods:
- track_content_performance()
- analyze_content_performance()  
- get_platform_insights()
- generate_optimization_recommendations()
- compare_content_performance()
- get_dashboard_overview()
- export_analytics_data()
```

#### EngagementTracker
Handles real-time engagement metrics tracking.

```python
tracker = EngagementTracker(db_pool)

# Methods:
- track_engagement()
- get_engagement_summary()
- batch_track_engagement()
- get_platform_metrics()
- detect_anomalies()
```

#### CorrelationAnalyzer
Analyzes correlations between content features and performance.

```python
analyzer = CorrelationAnalyzer(db_pool)

# Methods:
- analyze_feature_correlations()
- get_feature_importance()
- analyze_platform_differences()
```

#### TrendAnalyzer
Analyzes trends and patterns in performance data.

```python
trend_analyzer = TrendAnalyzer(db_pool)

# Methods:
- analyze_trend()
- get_trending_content()
- compare_content_trends()
```

#### AnalyticsDashboard
Provides unified interface to all analytics features.

```python
dashboard = AnalyticsDashboard(db_pool)

# Methods:
- get_dashboard_overview()
- get_content_performance_summary()
- get_platform_analytics()
- get_optimization_insights()
- get_comparative_analysis()
- export_dashboard_data()
```

### Data Models

#### EngagementSnapshot
```python
@dataclass
class EngagementSnapshot:
    content_id: str
    platform: Platform
    timestamp: datetime
    metrics: Dict[MetricType, float]
    metadata: Dict[str, Any]
```

#### CorrelationResult
```python
@dataclass
class CorrelationResult:
    feature: ContentFeature
    metric: PerformanceMetric
    correlation_coefficient: float
    p_value: float
    strength: str
    direction: str
    significance_level: float
    sample_size: int
    confidence_interval: Tuple[float, float]
    interpretation: str
```

#### TrendAnalysis
```python
@dataclass
class TrendAnalysis:
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
```

#### OptimizationInsight
```python
@dataclass
class OptimizationInsight:
    insight_type: str
    priority: str
    title: str
    description: str
    impact_prediction: str
    implementation_difficulty: str
    affected_content: List[str]
    data_supporting: Dict[str, Any]
```

## 🤝 Contributing

### Development Setup

1. **Clone and setup**:
```bash
git clone <repository>
cd content-creator
pip install -r requirements.txt
```

2. **Database setup**:
```bash
# Run the performance analytics migration
psql -d your_database -f database/migrations/performance_analytics_migration.sql
```

3. **Run tests**:
```bash
pytest tests/test_performance_analytics.py -v
```

### Adding New Features

1. **Add new analytics type**:
```python
# In correlation_analyzer.py or trend_analyzer.py
async def analyze_new_metric(self, content_id: str, metric_name: str):
    # Implementation here
    pass
```

2. **Extend dashboard**:
```python
# In analytics_dashboard.py
async def get_new_insight(self):
    # Implementation here
    pass
```

3. **Add API endpoints**:
```python
# In api_endpoints.py
@router.get("/new-feature", response_model=APIResponse)
async def new_feature():
    # Implementation here
    pass
```

## 📄 License

This performance analytics system is part of the Content Creator project. See the main project license for details.

## 🆘 Support

For questions, issues, or feature requests:

1. Check the troubleshooting section above
2. Review the API reference documentation
3. Check the integration examples
4. Open an issue in the project repository

---

**Performance Analytics Dashboard System v1.0.0**

*Comprehensive analytics for content performance optimization across multiple platforms.*