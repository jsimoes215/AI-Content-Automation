# A/B Testing System

A comprehensive A/B testing system for content variations supporting titles, thumbnails, scripts, and posting times.

## Features

### Content Variation Management
- **Title Variations**: Generate emotional, question-based, how-to, numbered, and custom title styles
- **Thumbnail Variations**: Create different visual styles with customizable color palettes
- **Script Variations**: Generate scripts with different hooks, pacing, and structures
- **Posting Time Variations**: Test different optimal posting times across time zones

### Performance Tracking
- Multi-platform support (YouTube, TikTok, Instagram)
- Real-time metrics collection
- Support for key metrics:
  - Impressions, Clicks, Likes, Shares, Comments
  - Engagement Rate, Conversion Rate, Click-Through Rate
  - Watch Time, Revenue, Subscriber Gains

### Statistical Analysis
- Multiple statistical tests:
  - T-Test for comparing means
  - Z-Test for large samples
  - Chi-Square for categorical data
  - Mann-Whitney U (non-parametric)
  - Kolmogorov-Smirnov for distribution comparison
  - Bayesian analysis for conversion rates
- Multiple comparison corrections (Bonferroni, Holm, Benjamini-Hochberg)
- Sample size calculations
- Sequential testing capabilities

### Automatic Winner Selection
- **Statistical Significance**: Select based on p-values and confidence intervals
- **Best Performance**: Choose variation with highest performance metrics
- **Hybrid Approach**: Combine statistical evidence with performance scores
- **Time-Based**: Weight recent performance more heavily
- **Revenue Optimization**: Focus on monetization metrics
- **Custom Evaluation**: Use business-specific criteria

## Quick Start

```python
from ab_testing import (
    ABTestManager, ContentType, ABTestConfig, 
    SignificanceLevel, SelectionStrategy
)

# Create test configuration
config = ABTestConfig(
    min_sample_size=100,
    significance_level=SignificanceLevel.P05,
    test_duration_days=7,
    auto_stop_enabled=True
)

# Initialize A/B test manager
manager = ABTestManager(config=config)

# Create title A/B test
test_id = manager.create_test(
    name="Video Title Optimization",
    description="Testing different title formats",
    content_type=ContentType.TITLE,
    base_content="10 Tips for Better Video Editing",
    variation_count=3
)

# Start the test
manager.start_test(test_id)

# Track performance metrics
from ab_testing.performance_tracker import MetricType

manager.performance_tracker.track_metric(
    variation_id=variation_id,
    metric_type=MetricType.CLICKS,
    value=150,
    platform="youtube"
)

# Analyze results and select winner
analysis = manager.analyze_test(test_id)
if analysis.get("should_stop"):
    print(f"Winner selected: {analysis['winner_selection']['winner_variation_id']}")
```

## Detailed Usage Examples

### 1. Title A/B Testing

```python
# Generate different title variations
base_title = "Ultimate Guide to Video Marketing"

variations = variation_manager.generate_title_variations(
    base_title=base_title,
    experiment_id=test_id,
    count=3,
    style="emotional"  # Options: emotional, question, how_to, numbered
)

# Each variation gets unique styling
print(f"Original: {base_title}")
for variation in variations:
    print(f"Variation: {variation.content}")
```

### 2. Thumbnail Testing

```python
# Define base thumbnail configuration
base_config = {
    "style": "text_overlay",
    "colors": ["#FF0000", "#FFFFFF"],
    "text_position": "center"
}

# Generate different visual styles
variations = variation_manager.generate_thumbnail_variations(
    base_thumbnail_config=base_config,
    experiment_id=test_id,
    count=4  # text_overlay, colorful_background, minimalist, high_contrast
)
```

### 3. Performance Tracking

```python
# Track multiple metrics
tracker.track_metric(
    variation_id="var_123",
    metric_type=MetricType.IMPRESSIONS,
    value=1000,
    platform="youtube"
)

tracker.track_metric(
    variation_id="var_123",
    metric_type=MetricType.CLICKS,
    value=50,
    platform="youtube"
)

# Batch tracking
metrics_data = [
    {
        "variation_id": "var_123",
        "metric_type": "likes",
        "value": 25,
        "platform": "youtube"
    },
    {
        "variation_id": "var_123",
        "metric_type": "comments",
        "value": 5,
        "platform": "youtube"
    }
]

tracker.batch_track_metrics(metrics_data)
```

### 4. Statistical Analysis

```python
from ab_testing.statistical_tests import StatisticalAnalyzer

analyzer = StatisticalAnalyzer()

# Extract performance data for testing
group_a_data = [engagement_rate_var_a]  # List of engagement rates
group_b_data = [engagement_rate_var_b]  # List of engagement rates

# Perform statistical test
result = analyzer.analyze_ab_test(
    group_a_data,
    group_b_data,
    test_type=StatisticalTest.T_TEST,
    significance_level=SignificanceLevel.P05
)

print(f"P-value: {result.p_value}")
print(f"Significant: {result.is_significant}")
print(f"Effect size: {result.effect_size}")
```

### 5. Winner Selection

```python
from ab_testing.winner_selector import WinnerSelector

selector = WinnerSelector()

# Get aggregated metrics for variations
variation_metrics = {}
for variation_id in test.variation_ids:
    metrics = tracker.get_aggregated_metrics(variation_id)
    variation_metrics[variation_id] = metrics

# Select winner using hybrid approach
result = selector.select_winner(
    variation_metrics,
    test_start_time,
    SelectionStrategy.HYBRID
)

print(f"Winner: {result.winner_variation_id}")
print(f"Confidence: {result.confidence_score}")
print(f"Reason: {result.selection_reason}")
```

## Configuration Options

### ABTestConfig

```python
config = ABTestConfig(
    min_sample_size=100,           # Minimum sample size per variation
    significance_level=SignificanceLevel.P05,  # Statistical significance level
    test_duration_days=7,          # Default test duration
    auto_stop_enabled=True,        # Automatically stop when winner found
    auto_stop_threshold=0.95,      # Confidence threshold for auto-stop
    performance_tracking_interval_minutes=60  # How often to collect metrics
)
```

### Selection Strategies

- **STATISTICAL_SIGNIFICANCE**: Select based on statistical tests
- **BEST_PERFORMANCE**: Choose highest performing variation
- **HYBRID**: Combine statistical and performance factors
- **TIME_BASED**: Weight recent performance more heavily
- **REVENUE_OPTIMIZED**: Focus on revenue metrics
- **CUSTOM**: Use business-specific evaluation function

### Statistical Tests

- **T_TEST**: Independent samples t-test
- **Z_TEST**: Z-test for large samples
- **CHI_SQUARE**: Chi-square test for categorical data
- **MANN_WHITNEY_U**: Non-parametric test for non-normal distributions
- **KOLMOGOROV_SMIRNOV**: Test for distribution differences
- **BAYESIAN**: Bayesian analysis for conversion rates

## Metrics Tracking

### Supported Platforms
- YouTube Analytics
- TikTok Insights  
- Instagram Metrics

### Key Metrics
- **Impressions**: Number of times content was shown
- **Clicks**: Number of clicks on content
- **Likes/Shares/Comments**: Engagement interactions
- **Engagement Rate**: (Likes + Comments + Shares) / Impressions
- **Conversion Rate**: Percentage of viewers who take desired action
- **Click-Through Rate**: Clicks / Impressions
- **Revenue**: Revenue generated from the content
- **Watch Time**: Average viewing duration

### Sample Size Calculations

```python
# Calculate required sample size
required_n = analyzer.sample_size_calculation(
    baseline_rate=0.03,              # 3% baseline conversion rate
    minimum_detectable_effect=0.01,   # Want to detect 1% improvement
    alpha=0.05,                      # 95% confidence level
    power=0.8                       # 80% power
)

print(f"Need {required_n} samples per variation")
```

## Best Practices

### 1. Test Design
- Run tests for at least 7 days to account for weekly patterns
- Ensure equal traffic distribution between variations
- Test one variable at a time for clear attribution
- Use minimum sample sizes for statistical power

### 2. Metrics Selection
- Choose primary metrics aligned with business goals
- Track secondary metrics for additional insights
- Consider both leading (CTR) and lagging (Revenue) indicators
- Use conversion rates for monetization-focused tests

### 3. Statistical Rigor
- Set significance levels appropriately (p < 0.05 for most tests)
- Account for multiple testing when comparing many variations
- Consider practical significance alongside statistical significance
- Use sequential testing for longer-running tests

### 4. Business Context
- Weight metrics according to business priorities
- Consider long-term impact vs. short-term gains
- Factor in implementation costs and complexity
- Set clear decision criteria before starting tests

## Error Handling

The system includes comprehensive error handling:

```python
try:
    result = manager.analyze_test(test_id)
    if result.get("should_stop"):
        # Proceed with implementation
        pass
except ValueError as e:
    print(f"Invalid input: {e}")
except Exception as e:
    print(f"Analysis failed: {e}")
```

## Exporting Results

Export comprehensive test data for external analysis:

```python
# Export test data
export_data = manager.export_test_data(test_id)

# Save to file
import json
with open(f"test_{test_id}_results.json", "w") as f:
    json.dump(export_data, f, indent=2)

# Export summary report
summary = selector.export_selection_summary(selection_history)
print(f"Selection Summary: {summary}")
```

## Integration with Content Pipeline

The A/B testing system integrates seamlessly with the content creation pipeline:

```python
# In content creation workflow
def create_content_with_testing():
    # Generate initial content
    content = generate_video_content()
    
    # Create A/B test for titles
    test_id = ab_manager.create_test(
        name="Video Title Test",
        content_type=ContentType.TITLE,
        base_content=content["title"]
    )
    
    # Create variations
    variations = generate_title_variations(content["title"], test_id)
    
    # Start test and monitor
    ab_manager.start_test(test_id)
    
    # Winner gets implemented in final video
    return test_id, variations
```

## Support and Documentation

For detailed API documentation and advanced usage, see:

- `content_variations.py` - Content variation management
- `performance_tracker.py` - Metrics collection and analysis
- `statistical_tests.py` - Statistical analysis methods
- `winner_selector.py` - Winner selection algorithms
- `ab_test_manager.py` - Main orchestration class
- `example_usage.py` - Complete usage examples

## License

This A/B testing system is part of the AI Content Automation platform.
