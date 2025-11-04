# Platform Timing Recommendations - Integration Guide

## Overview

This implementation provides AI-powered platform-specific timing recommendations interface with evidence-based scheduling optimization. The system integrates platform research data and optimization algorithms to display data-driven recommendations for optimal content posting times.

## Components

### 1. PlatformRecommendations.tsx

**Purpose**: Main component for showing platform-specific timing suggestions

**Features**:
- Multi-platform timing analysis
- Confidence scoring and explanation
- Best days and optimal hours display
- Audience insights and demographics
- Strategy recommendations
- Real-time data integration

**Props**:
```typescript
interface PlatformRecommendationsProps {
  selectedPlatforms?: string[];
  contentType?: string;
  targetAudience?: string;
  onTimeSlotSelect?: (slot: SchedulingRecommendation) => void;
}
```

**Key Functionality**:
- Platform-specific optimal posting times
- Confidence-based scoring system
- Audience active percentage indicators
- Competition level analysis
- Strategy recommendations

### 2. TimingChart.tsx

**Purpose**: Visual representation of optimal posting times

**Features**:
- Interactive heatmap visualization
- Platform comparison radar charts
- Hourly trend analysis
- Multiple view modes (heatmap, radar, trends)
- Timezone support
- Real-time data filtering

**Props**:
```typescript
interface TimingChartProps {
  platformData: PlatformTimingData[];
  selectedTimezone?: string;
  onTimeSlotSelect?: (slot: SchedulingRecommendation) => void;
  height?: number;
}
```

**Visualization Types**:
- **Heatmap**: Day/hour engagement matrix
- **Radar**: Platform comparison across days
- **Trends**: Hourly engagement and audience activity

### 3. TimingRecommendationsDemo.tsx

**Purpose**: Complete integration example and demo component

**Features**:
- Combined component showcase
- Configuration panel
- Optimization workflow
- Results visualization
- Quick actions interface

## API Integration

### Scheduling Optimization API

The components integrate with the backend scheduling optimization API:

```typescript
// Get timing recommendations
await apiClient.getSchedulingRecommendations({
  platforms: ['youtube', 'tiktok', 'instagram'],
  target_count: 10,
  timezone: 'UTC',
  content_type: 'video'
});

// Create optimized schedule
await apiClient.createSchedule({
  title: 'AI-Optimized Campaign',
  timezone: 'UTC',
  items: [
    {
      content_id: 'video_123',
      platform: 'youtube',
      scheduled_time: '2025-11-06T15:00:00Z'
    }
  ]
});

// Optimize existing schedule
await apiClient.optimizeSchedule({
  schedule_id: 'schedule_456',
  targets: [...],
  apply: true
});
```

### WebSocket Integration

Real-time updates via WebSocket:

```typescript
// Connect to scheduling updates
apiClient.connectSchedulingWebSocket(scheduleId, (data) => {
  if (data.type === 'optimization.completed') {
    // Refresh recommendations
    loadPlatformRecommendations();
  }
});
```

## Data Models

### PlatformTimingRecommendation

```typescript
interface PlatformTimingRecommendation {
  id: string;
  platform: string;
  platformName: string;
  optimalTimes: {
    hour: number;
    confidence: number;
    engagement_score: number;
    audience_active_percentage: number;
  }[];
  contentTypes: string[];
  timezone: string;
  bestDays: {
    day: string;
    score: number;
    engagement_boost: number;
  }[];
  audienceInsights: {
    peak_hours: number[];
    active_demographics: string[];
    weekend_vs_weekday: number;
  };
  competition: {
    level: 'low' | 'medium' | 'high';
    saturation_score: number;
  };
  recommendedStrategy: string[];
}
```

### SchedulingRecommendation

```typescript
interface SchedulingRecommendation {
  id: string;
  window_start: string;
  window_end: string;
  score: number;
  reasons: string[];
  platforms: string[];
  confidence: number;
  content_types: string[];
}
```

## Integration in SchedulingDashboard

The components are integrated into the main SchedulingDashboard:

```tsx
// Add new tab for recommendations
const tabs = [
  { id: 'overview', label: 'Overview', icon: BarChart3 },
  { id: 'schedules', label: 'Schedules', icon: Calendar },
  { id: 'analytics', label: 'Performance', icon: TrendingUp },
  { id: 'recommendations', label: 'AI Recommendations', icon: Target },
  { id: 'optimization', label: 'Optimization', icon: Zap },
];

// Include in tab content
{activeTab === 'recommendations' && (
  <PlatformRecommendations
    selectedPlatforms={['youtube', 'tiktok', 'instagram']}
    contentType="video"
    targetAudience="general"
    onTimeSlotSelect={handleTimeSlotSelect}
  />
)}
```

## Usage Examples

### Basic Usage

```tsx
import PlatformRecommendations from './components/PlatformRecommendations';
import TimingChart from './components/TimingChart';

function MyComponent() {
  const handleTimeSlotSelect = (slot) => {
    console.log('Selected optimal slot:', slot);
    // Create schedule or update existing
  };

  return (
    <div>
      <PlatformRecommendations
        selectedPlatforms={['youtube', 'tiktok']}
        contentType="video"
        onTimeSlotSelect={handleTimeSlotSelect}
      />
      
      <TimingChart
        platformData={platformData}
        selectedTimezone="America/New_York"
        onTimeSlotSelect={handleTimeSlotSelect}
      />
    </div>
  );
}
```

### Advanced Configuration

```tsx
<PlatformRecommendations
  selectedPlatforms={['youtube', 'tiktok', 'instagram', 'linkedin']}
  contentType="short"
  targetAudience="business-professionals"
  onTimeSlotSelect={(slot) => {
    // Custom handling for time slot selection
    apiClient.createSchedule({
      title: 'AI-Recommended Content',
      items: [{
        content_id: 'content_123',
        platform: slot.platforms[0],
        scheduled_time: slot.window_start
      }]
    });
  }}
/>
```

### With Custom Styling

```tsx
<div className="custom-container space-y-6">
  <PlatformRecommendations
    selectedPlatforms={selectedPlatforms}
    contentType={contentType}
    className="custom-recommendations"
  />
</div>
```

## Styling and Theming

The components follow Tailwind CSS patterns and support dark mode:

```css
/* Custom component styling */
.platform-card {
  @apply bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800;
}

.confidence-high {
  @apply text-green-600 dark:text-green-400;
}

.confidence-medium {
  @apply text-yellow-600 dark:text-yellow-400;
}

.confidence-low {
  @apply text-red-600 dark:text-red-400;
}
```

## Error Handling

Components include comprehensive error handling:

```tsx
try {
  const recommendations = await loadPlatformRecommendations();
  setRecommendations(recommendations);
} catch (error) {
  console.error('Failed to load recommendations:', error);
  // Show user-friendly error message
  setError('Unable to load timing recommendations. Please try again.');
}
```

## Performance Considerations

- **Lazy Loading**: Components load data only when visible
- **Caching**: API responses are cached to reduce redundant calls
- **Real-time Updates**: WebSocket connections for live updates
- **Pagination**: Large datasets are paginated for performance

## Testing

Components include comprehensive TypeScript types and can be tested:

```tsx
// Example test
import { render, screen } from '@testing-library/react';
import PlatformRecommendations from './PlatformRecommendations';

test('displays platform recommendations', () => {
  render(<PlatformRecommendations />);
  expect(screen.getByText('Platform Timing Recommendations')).toBeInTheDocument();
});
```

## Browser Support

- Chrome/Edge 88+
- Firefox 85+
- Safari 14+
- Mobile browsers with ES2020 support

## Dependencies

- React 18+
- TypeScript 4.5+
- Tailwind CSS 3+
- Recharts for visualizations
- Lucide React for icons

## Future Enhancements

- **ML Integration**: Enhanced machine learning models for predictions
- **A/B Testing**: Built-in A/B testing for recommendation validation
- **Historical Analysis**: Deep historical performance analysis
- **Custom Audiences**: User-defined audience segments
- **Seasonal Adjustments**: Automatic seasonal timing adjustments
- **Competition Monitoring**: Real-time competitor activity tracking

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Check network connectivity
   - Verify API endpoint configuration
   - Check authentication tokens

2. **Charts Not Rendering**
   - Ensure Recharts is properly installed
   - Check data format compatibility
   - Verify responsive container dimensions

3. **WebSocket Disconnections**
   - Implement reconnection logic
   - Handle network interruptions gracefully
   - Provide fallback polling mechanism

### Debug Mode

Enable debug logging:

```tsx
const DEBUG = process.env.NODE_ENV === 'development';

if (DEBUG) {
  console.log('Platform recommendations loaded:', recommendations);
}
```

## Contributing

When extending the timing recommendations system:

1. Follow existing component patterns
2. Maintain TypeScript type safety
3. Include comprehensive error handling
4. Add proper accessibility attributes
5. Test with multiple platforms and timezones
6. Document new features thoroughly

This implementation provides a robust, scalable foundation for AI-powered content timing optimization across multiple social media platforms.