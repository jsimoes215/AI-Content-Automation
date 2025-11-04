# Scheduling Optimizer with AI Recommendations

A comprehensive AI-powered scheduling optimization system for social media content that calculates optimal posting times, coordinates multi-platform scheduling, and provides machine learning-based timing recommendations.

## Features

### 🎯 Core Functionality
- **Optimal Time Calculation**: Evidence-based algorithm using 2025 platform research
- **Multi-Platform Coordination**: Intelligent scheduling across YouTube, TikTok, Instagram, X/Twitter, LinkedIn, and Facebook
- **Machine Learning Predictions**: ML models trained on historical performance data
- **Adaptive Optimization**: Real-time performance tracking and parameter adjustment
- **Batch Processing Integration**: Seamless integration with existing content pipelines

### 📊 Platforms Supported
- **YouTube** (Long-form & Shorts)
- **TikTok** (Video content)
- **Instagram** (Feed, Reels, Stories, Carousels)
- **X/Twitter** (Posts & Threads)
- **LinkedIn** (Posts & Carousels)
- **Facebook** (Posts & Reels)

### 🤖 AI Capabilities
- RandomForest-based timing predictions
- Bayesian optimization with adaptive parameters
- Platform-specific KPI tracking and analysis
- Automated performance feedback loops

## Quick Start

### Installation

```bash
# Required dependencies (install with pip)
pip install numpy scikit-learn
```

### Basic Usage

```python
from scheduling_optimizer import (
    SchedulingOptimizer, Platform, ContentType, AudienceProfile
)

# Initialize optimizer
optimizer = SchedulingOptimizer()

# Create audience profile
audience = AudienceProfile(
    age_cohorts={'25-34': 0.4, '35-44': 0.3, '18-24': 0.3},
    device_split={'mobile': 0.7, 'desktop': 0.3},
    time_zone_weights={'UTC-5': 0.5, 'UTC-8': 0.3}
)

# Calculate optimal posting times
scores = optimizer.calculate_timing_scores(
    platform=Platform.INSTAGRAM,
    content_type=ContentType.INSTAGRAM_REELS,
    audience_profile=audience,
    day_of_week=2  # Wednesday
)

# Get top 5 hours
top_hours = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
for hour, score in top_hours:
    print(f"Hour {hour:02d}: {score:.3f}")
```

### Generate Multi-Platform Schedule

```python
from scheduling_optimizer import SchedulingConstraint, PriorityTier

# Define posts
posts = [
    {
        'id': 'post_1',
        'platform': 'instagram',
        'content_type': 'instagram_reels',
        'priority': PriorityTier.NORMAL.value,
        'title': 'Product Demo'
    },
    {
        'id': 'post_2',
        'platform': 'tiktok',
        'content_type': 'tiktok_video',
        'priority': PriorityTier.URGENT.value,
        'title': 'Behind the Scenes'
    }
]

# Define constraints
constraints = [
    SchedulingConstraint(Platform.INSTAGRAM, min_gap_hours=18.0),
    SchedulingConstraint(Platform.TIKTOK, min_gap_hours=12.0)
]

# Generate schedule
schedule = optimizer.generate_optimal_schedule(
    posts=posts,
    constraints=constraints,
    audience_profiles={Platform.INSTAGRAM: audience, Platform.TIKTOK: audience},
    start_date=datetime.now(),
    end_date=datetime.now() + timedelta(days=7)
)
```

### ML-Based Predictions

```python
# Train models (requires historical data)
model_scores = await optimizer.train_ml_models()

# Get predictions
predictions = optimizer.predict_optimal_times(
    platform=Platform.TIKTOK,
    content_type=ContentType.TIKTOK_VIDEO,
    audience_profile=audience,
    num_predictions=5
)
```

## Evidence-Based Algorithm

The system uses 2025 research-backed posting windows:

| Platform | Peak Times | Notes |
|----------|------------|-------|
| **YouTube** | Wed 4PM, Weekday 3-5PM | Shorts less time-sensitive |
| **TikTok** | Wed 5-6PM, Sun 8PM | Avoid Saturday |
| **Instagram** | Mon-Thu 10AM-3PM | Reels: 6-9AM, 6-9PM |
| **X/Twitter** | Tue-Thu 8AM-12PM | Weekends underperform |
| **LinkedIn** | Tue-Thu 8-11AM, 12-2PM | Business hours focus |
| **Facebook** | Mon-Thu Mid-day | Reels prioritized |

## Architecture

### Core Components

1. **TimingScoreCalculator**: Computes platform-specific posting scores
2. **ScheduleGenerator**: Creates optimal multi-platform schedules
3. **MLPredictor**: Machine learning-based timing predictions
4. **AdaptiveOptimizer**: Performance tracking and parameter adjustment
5. **BatchIntegrator**: Integration with batch processing systems

### Database Schema

The system uses SQLite with tables for:
- `performance_history`: Historical performance metrics
- `schedule_plans`: Generated scheduling plans
- `adaptive_params`: Learning parameters
- `ml_training_data`: Training datasets

## Integration with Batch Processing

### API Methods

```python
# Integrate with batch system
schedule_plan = optimizer.integrate_with_batch_system(
    bulk_job_id="job_123",
    posts=posts,
    scheduling_metadata={
        'start_after': '2025-11-05T10:00:00Z',
        'deadline': '2025-11-12T23:59:59Z',
        'suggested_concurrency': 3,
        'max_parallelism': 3
    }
)

# Record performance metrics
metrics = PerformanceMetrics(
    platform=Platform.INSTAGRAM,
    content_type=ContentType.INSTAGRAM_REELS,
    posted_at=datetime.now(),
    reach=1500,
    engagement_rate=0.045,
    is_successful=True
)
optimizer.record_performance_metrics(metrics)
```

### Constraints and Policies

- **Intra-platform spacing**: Minimum gaps between posts
- **Concurrency limits**: Maximum simultaneous posts
- **Rate limiting**: Integration with external API quotas
- **Compliance**: Platform-specific posting rules

## Performance Optimization

### Adaptive Learning Cycle

1. **Measure**: Collect throughput, error rates, latency metrics
2. **Analyze**: Detect trends and threshold breaches
3. **Adjust**: Update parameters based on performance
4. **Validate**: Monitor improvements and rollback if needed

### KPI Tracking

- **Throughput**: Jobs per hour, completion rates
- **Rate Limits**: 429 error rates, quota compliance
- **Latency**: Job start times (p50/p95)
- **Adherence**: Schedule execution vs plan

### Machine Learning

- **Models**: RandomForestRegressor per platform
- **Features**: Time-based, demographic, platform encodings
- **Training**: 80/20 split with R² evaluation
- **Predictions**: Top-N optimal times with confidence scores

## Configuration

### Hyperparameters

```python
# Scoring model weights
w_demo = 0.3      # Demographic adjustments
w_fmt = 0.2       # Format adjustments  
w_seas = 0.1      # Seasonality adjustments

# ML parameters
epsilon = 0.1     # Exploration rate for multi-armed bandit
smoothing = 0.2   # Exponential smoothing for weight updates

# Rate limiting
initial_backoff = 1.0    # Initial retry delay (seconds)
backoff_multiplier = 2.0  # Exponential backoff factor
max_backoff = 60.0       # Maximum retry delay
```

### Platform-Specific Settings

```python
# Spacing requirements (hours)
LINKEDIN_SPACING = 24.0
INSTAGRAM_SPACING = 18.0
YOUTUBE_SPACING = 48.0
TIKTOK_SPACING = 12.0

# Concurrency limits
MAX_CONCURRENT_POSTS = 3
MAX_URGENT_CONCURRENT = 5
```

## Examples

Run the complete example:

```bash
python example_scheduling_optimizer.py
```

This demonstrates:
- Basic timing score calculation
- Multi-platform schedule generation
- ML-based predictions
- Batch system integration
- Performance tracking
- Platform-specific recommendations

## API Reference

### Classes

#### `SchedulingOptimizer`
Main optimization engine.

**Methods:**
- `calculate_timing_scores()` - Compute posting scores
- `generate_optimal_schedule()` - Create multi-platform schedules
- `predict_optimal_times()` - ML-based predictions
- `train_ml_models()` - Train prediction models
- `adaptive_optimization_cycle()` - Performance optimization
- `integrate_with_batch_system()` - Batch integration
- `get_schedule_recommendations()` - Platform insights

#### `AudienceProfile`
Audience demographics and device information.

**Fields:**
- `age_cohorts`: Dictionary of age group shares
- `device_split`: Mobile/desktop distribution
- `time_zone_weights`: Geographic time zone distribution

#### `SchedulingConstraint`
Multi-platform coordination constraints.

**Fields:**
- `platform`: Target platform
- `min_gap_hours`: Minimum spacing between posts
- `max_concurrent_posts`: Concurrency limit
- `preferred_windows`: Preferred posting times
- `prohibited_windows`: Blocked posting times

#### `PerformanceMetrics`
Platform-specific performance data.

**Fields:**
- Platform KPIs (reach, engagement, watch time, etc.)
- Success classification
- Metadata for platform-specific analysis

## Troubleshooting

### Common Issues

1. **Insufficient Training Data**
   - Need minimum 50 samples per platform for ML training
   - Use rule-based predictions as fallback

2. **High 429 Error Rates**
   - Reduce concurrency settings
   - Increase backoff parameters
   - Check rate limiting integration

3. **Poor Schedule Adherence**
   - Review constraint definitions
   - Adjust minimum spacing requirements
   - Check audience profile accuracy

### Logging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Database Issues

Reset database:

```python
import os
os.remove("scheduling_optimizer.db")  # Removes all data
optimizer = SchedulingOptimizer()    # Recreates empty database
```

## Contributing

### Development Setup

1. Install dependencies:
   ```bash
   pip install numpy scikit-learn pytest
   ```

2. Run tests:
   ```bash
   pytest tests/
   ```

3. Run examples:
   ```bash
   python example_scheduling_optimizer.py
   ```

### Adding New Platforms

1. Add platform to `Platform` enum
2. Define baseline windows in `_init_platform_windows()`
3. Add content types to `ContentType` enum
4. Update constraint mapping in `_get_min_gap_hours()`
5. Add platform-specific KPI logic

## License

This implementation is based on the scheduling optimization algorithms specification and batch integration requirements documented in `/docs/scheduling_system/`.

## Support

For questions and support:
1. Review the implementation summary: `SCHEDULING_OPTIMIZER_SUMMARY.md`
2. Check example usage: `example_scheduling_optimizer.py`
3. Examine the source code documentation in `scheduling_optimizer.py`

---

**Built with evidence-based algorithms, machine learning, and production-ready integration patterns.**