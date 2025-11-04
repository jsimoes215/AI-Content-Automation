# Data Validation Pipeline Documentation

## Overview

The Data Validation Pipeline is a comprehensive system for validating, cleaning, and transforming video idea data sourced from Google Sheets. It provides five core functionalities:

1. **Schema Validation** - Ensures data conforms to required structure and formats
2. **Data Cleaning and Normalization** - Cleans and standardizes input data
3. **Duplicate Detection and Handling** - Identifies and flags potential duplicates
4. **Cost Estimation** - Calculates production costs for video ideas
5. **Quality Scoring** - Scores the quality and viability of content ideas

## Architecture

### Core Components

#### 1. VideoIdeaSchema
Defines the expected data structure and validation rules:
- **Required Fields**: title, description, target_audience
- **Optional Fields**: tags, tone, duration_estimate, platform, style, voice_type, visual_elements, call_to_action, keywords, competitor_analysis, script_type, demo_required, brand_guidelines, compliance_notes
- **Field Validators**: Specific validation functions for each field type

#### 2. DataCleaner
Handles data cleaning and normalization:
- Text normalization (whitespace, special characters)
- List field processing (tags, keywords)
- Duration parsing (handles "5 minutes", "2-3 min", "90s" formats)
- HTML/JS sanitization

#### 3. DuplicateDetector
Identifies duplicate content using:
- Jaccard similarity for word sets
- Character n-gram similarity
- Content hashing for exact matches
- Configurable similarity thresholds

#### 4. CostEstimator
Calculates production costs based on:
- Script type complexity (per-minute rates)
- Platform multipliers
- Complexity adders (demo required, brand guidelines, etc.)
- 10% contingency for production variations

#### 5. QualityScorer
Evaluates content quality using weighted metrics:
- **Completeness** (25%): Data completeness scoring
- **Clarity** (20%): Content clarity assessment
- **Engagement** (20%): Engagement potential evaluation
- **Feasibility** (15%): Production feasibility scoring
- **Uniqueness** (20%): Uniqueness compared to existing ideas

## Cost Optimization Integration

The pipeline incorporates cost optimization strategies from the system architecture:

### Smart Batching Logic
- Groups similar ideas to reduce processing overhead
- Identifies compatible content for batch processing
- Implements similarity-based grouping

### Cache Strategy for Repeated Content
- Content-addressable deduplication
- Near-duplicate detection with similarity thresholds
- Multi-layer caching approach

### Dynamic Priority Queue
- Cost-based priority scoring
- Quality-score weighted processing
- Resource optimization

### API Call Reduction
- Batch validation processing
- Efficient similarity calculations
- Optimized content hashing

## Usage Examples

### Basic Usage

```python
from data_validation import DataValidationPipeline

# Initialize pipeline
pipeline = DataValidationPipeline()

# Validate single idea
idea = {
    "title": "How to Build a Successful Online Business",
    "description": "Learn the essential steps to create and grow your online business from scratch. This comprehensive guide covers market research, business planning, digital marketing strategies, and scaling techniques.",
    "target_audience": "entrepreneurs",
    "tags": "business, online, entrepreneurship, marketing",
    "tone": "educational",
    "duration_estimate": "5 minutes",
    "platform": "youtube",
    "script_type": "tutorial"
}

result = pipeline.validate_idea(idea)
print(f"Valid: {result.is_valid}")
print(f"Quality Score: {result.quality_score}/10")
print(f"Estimated Cost: ${result.estimated_cost}")
```

### Batch Processing

```python
# Validate multiple ideas
ideas = [idea1, idea2, idea3, ...]
results = pipeline.validate_batch(ideas)

# Get summary statistics
summary = pipeline.get_validation_summary(results)
print(f"Total ideas: {summary['total_ideas']}")
print(f"Valid ideas: {summary['valid_ideas']}")
print(f"Average quality: {summary['average_quality_score']}/10")
print(f"Total cost: ${summary['total_estimated_cost']:.2f}")
```

## Field Specifications

### Required Fields

| Field | Type | Validation Rules |
|-------|------|------------------|
| title | string | 5-100 characters, alphanumeric + basic punctuation |
| description | string | 20-2000 characters |
| target_audience | string | Must be from predefined list |

### Optional Fields

| Field | Type | Validation Rules | Default |
|-------|------|------------------|---------|
| tags | list/string | Max 10 tags, 30 chars each | [] |
| tone | string | From predefined tone list | None |
| duration_estimate | string/number | 15 seconds - 60 minutes | 60 |
| platform | string | From supported platforms | 'universal' |
| script_type | string | From script type list | 'explainer' |
| call_to_action | string | 0-200 characters | None |
| demo_required | boolean | True/False | False |
| brand_guidelines | boolean | True/False | False |
| compliance_notes | boolean | True/False | False |

## Validation Rules

### Title Validation
- Minimum 5 characters
- Maximum 100 characters
- Alphanumeric with spaces, hyphens, underscores, and periods
- No special characters except basic punctuation

### Description Validation
- Minimum 20 characters
- Maximum 2000 characters
- Plain text only (HTML is sanitized)

### Target Audience
Valid values: `general`, `professionals`, `students`, `entrepreneurs`, `parents`, `seniors`, `teenagers`, `children`, `experts`, `beginners`, `tech-savvy`, `casual users`, `businesses`

### Tags
- Comma-separated string or list
- Maximum 10 tags
- Each tag maximum 30 characters
- Normalized to lowercase

### Tone
Valid values: `professional`, `casual`, `educational`, `entertaining`, `motivational`, `humorous`, `serious`, `friendly`, `authoritative`

### Platform
Valid values: `youtube`, `tiktok`, `instagram`, `linkedin`, `twitter`, `facebook`, `universal`, `multi-platform`

### Duration
Formats supported:
- Seconds: "90s", "90 sec", "90 seconds"
- Minutes: "5 min", "5 minutes"
- Hours: "2 hour", "2 hr", "2 hours"
- Numbers: 90 (assumed seconds)

### Script Type
Valid values: `explainer`, `tutorial`, `story`, `demo`, `testimonial`, `interview`, `presentation`, `review`, `comparison`

## Cost Estimation

### Base Rates (per minute)
| Script Type | Cost |
|-------------|------|
| Explainer | $25.00 |
| Tutorial | $30.00 |
| Story | $20.00 |
| Demo | $40.00 |
| Testimonial | $25.00 |
| Interview | $35.00 |
| Presentation | $30.00 |
| Review | $25.00 |
| Comparison | $30.00 |

### Platform Multipliers
| Platform | Multiplier |
|----------|------------|
| Universal | 1.0 |
| Multi-platform | 1.2 |
| YouTube | 1.0 |
| TikTok | 0.9 |
| Instagram | 1.0 |
| LinkedIn | 1.1 |
| Twitter | 0.8 |
| Facebook | 0.9 |

### Complexity Adders
| Feature | Cost Adder |
|---------|------------|
| Demo Required | $50.00 |
| Brand Guidelines | $25.00 |
| Compliance Notes | $30.00 |

### Total Cost Formula
```
total_cost = ((base_cost_per_min * duration_minutes) * platform_multiplier + complexity_adders) * 1.10
```

## Quality Scoring

### Scoring Breakdown

#### Completeness (25%)
- Required fields presence: 70%
- Optional fields presence: 30%

#### Clarity (20%)
- Title length optimization: 30%
- Description comprehensiveness: 50%
- Audience specificity: 20%

#### Engagement (20%)
- Base score: 5.0
- Tone bonus (humorous/entertaining/motivational): +2.0
- Call to action presence: +1.5
- Tag presence: +1.0
- Platform optimization: +0.5

#### Feasibility (20%)
- Base score: 7.0
- Duration optimization (30-300 seconds): +2.0
- Demo requirement penalty: -1.0
- Script type complexity: varies

#### Uniqueness (20%)
- Based on similarity to existing content
- Higher score for lower similarity

## Duplicate Detection

### Similarity Metrics

#### Jaccard Similarity
- Compares word sets between texts
- Weight: 60%

#### Character N-gram Similarity
- Compares 3-character sequences
- Weight: 40%

### Content Hashing
- MD5 hash of normalized key fields
- Exact match detection
- Efficient lookup

### Threshold Configuration
- Default similarity threshold: 0.85
- High similarity: > 0.8
- Medium similarity: 0.5 - 0.8
- Low similarity: < 0.5

## API Reference

### DataValidationPipeline

#### Constructor
```python
DataValidationPipeline(similarity_threshold: float = 0.85)
```

#### Methods

**validate_idea(idea_data: Dict[str, Any]) -> ValidationResult**
- Validates a single video idea
- Returns ValidationResult with all metrics

**validate_batch(ideas_data: List[Dict[str, Any]]) -> List[ValidationResult]**
- Validates multiple ideas in batch
- Returns list of ValidationResult objects

**get_validation_summary(results: List[ValidationResult]) -> Dict[str, Any]**
- Generates summary statistics
- Returns comprehensive batch report

### ValidationResult

#### Attributes
- `is_valid`: Boolean validation status
- `errors`: List of validation errors
- `warnings`: List of warnings
- `cleaned_data`: Cleaned and normalized data
- `quality_score`: Quality score (0-10)
- `estimated_cost`: Cost estimate (Decimal)
- `duplicate_score`: Duplicate similarity score

## Integration Examples

### Google Sheets Integration

```python
import gspread
from data_validation import DataValidationPipeline

# Connect to Google Sheets
gc = gspread.service_account()
sheet = gc.open("Video Ideas").sheet1

# Get all ideas
ideas = sheet.get_all_records()

# Validate batch
pipeline = DataValidationPipeline()
results = pipeline.validate_batch(ideas)

# Update sheet with validation results
for i, result in enumerate(results, 2):  # Starting from row 2
    sheet.update_cell(i, len(ideas[0]) + 1, result.quality_score)
    sheet.update_cell(i, len(ideas[0]) + 2, float(result.estimated_cost))
    sheet.update_cell(i, len(ideas[0]) + 3, "VALID" if result.is_valid else "INVALID")
```

### Database Integration

```python
from supabase import create_client
from data_validation import DataValidationPipeline

# Initialize Supabase
supabase = create_client(url, key)
pipeline = DataValidationPipeline()

# Process ideas and store validated data
for idea in raw_ideas:
    result = pipeline.validate_idea(idea)
    
    if result.is_valid:
        # Store in database
        supabase.table('video_ideas').insert({
            'original_data': idea,
            'cleaned_data': result.cleaned_data,
            'quality_score': result.quality_score,
            'estimated_cost': float(result.estimated_cost),
            'duplicate_score': result.duplicate_score,
            'status': 'validated'
        }).execute()
```

### Content Calendar Planning

```python
def plan_content_calendar(ideas, max_budget=1000):
    """Plan content calendar with budget constraints"""
    pipeline = DataValidationPipeline()
    results = pipeline.validate_batch(ideas)
    
    # Filter valid ideas
    valid_ideas = [(idea, result) for idea, result in zip(ideas, results) 
                   if result.is_valid]
    
    # Sort by quality score
    valid_ideas.sort(key=lambda x: x[1].quality_score, reverse=True)
    
    # Select ideas within budget
    selected = []
    total_cost = 0
    
    for idea, result in valid_ideas:
        if total_cost + float(result.estimated_cost) <= max_budget:
            selected.append((idea, result))
            total_cost += float(result.estimated_cost)
    
    return selected, total_cost
```

## Error Handling

### Common Validation Errors

| Error | Description | Solution |
|-------|-------------|----------|
| Missing required fields | Required field not present | Add required field |
| Title contains invalid characters | Invalid characters in title | Use alphanumeric + basic punctuation |
| Description too short | Description under 20 characters | Expand description |
| Invalid target audience | Audience not in valid list | Use predefined audience value |
| Duration invalid | Invalid duration format | Use supported time format |
| Too many tags | Over 10 tags provided | Reduce to 10 or fewer |

### Warning Types

| Warning | Description | Action |
|---------|-------------|---------|
| Potential duplicate detected | High similarity to existing content | Review and potentially modify |
| Quality score low | Score below acceptable threshold | Improve content quality |
| High cost estimate | Cost above budget range | Consider optimization |

## Performance Considerations

### Batch Processing
- Process ideas in batches of 50-100 for optimal performance
- Use streaming for large datasets
- Implement progress tracking for UI updates

### Memory Usage
- Content hash cache prevents redundant calculations
- Duplicate detection uses incremental processing
- Clean up caches periodically for long-running processes

### Scalability
- Stateless design supports horizontal scaling
- Configurable similarity thresholds
- Optimized for concurrent processing

## Testing

### Test Coverage
- Unit tests for each component
- Integration tests for full pipeline
- Performance tests for large batches
- Edge case handling

### Test Data
- Sample Google Sheets data
- Various quality levels
- Different content types
- Edge cases and error conditions

Run tests with:
```bash
python test_data_validation.py
```

## Best Practices

### Data Preparation
1. **Clean source data** before feeding to pipeline
2. **Validate input formats** at data entry point
3. **Use consistent naming** conventions
4. **Implement data validation** at source

### Quality Improvement
1. **Set quality thresholds** based on business requirements
2. **Provide feedback** to content creators
3. **Iterate on scoring** based on actual performance
4. **Monitor duplicate rates** and adjust thresholds

### Cost Optimization
1. **Use cost estimates** for budget planning
2. **Implement batching** for similar content
3. **Consider platform-specific** optimization
4. **Track actual vs. estimated** costs

### Monitoring
1. **Track validation rates** over time
2. **Monitor quality score** distributions
3. **Analyze cost accuracy** regularly
4. **Review duplicate detection** effectiveness

## Troubleshooting

### Common Issues

**Issue: High false positive duplicate rate**
- Solution: Adjust similarity_threshold to lower value (0.7-0.8)
- Review content hash generation logic

**Issue: Inaccurate cost estimates**
- Solution: Update cost_per_minute and complexity_adders
- Track actual production costs for calibration

**Issue: Quality scores don't match expectations**
- Solution: Adjust weights in QualityScorer
- Review individual scoring methods

**Issue: Validation too strict/lenient**
- Solution: Adjust field validators
- Modify required vs. optional field definitions

### Debugging Tips

1. **Enable debug logging** for detailed processing info
2. **Check cleaned_data** to see normalization results
3. **Review error messages** for specific validation failures
4. **Examine quality breakdown** for score components
5. **Analyze similarity scores** for duplicate detection

## Future Enhancements

### Planned Features
- **Machine learning** quality scoring
- **Advanced deduplication** using embeddings
- **Real-time cost** estimation updates
- **Integration with production** tracking
- **Automated quality** improvement suggestions

### Extensibility
- **Plugin architecture** for custom validators
- **Configurable scoring** weights
- **Custom cost models** per organization
- **Platform-specific** optimization rules

## Support and Contributions

For issues, questions, or contributions, please refer to the main project repository.

## License

This module is part of the AI Content Automation System.
