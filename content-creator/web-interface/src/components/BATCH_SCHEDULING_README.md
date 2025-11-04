# Batch Scheduling Interface Documentation

## Overview

The Batch Scheduling Interface provides a comprehensive solution for managing bulk content generation with intelligent scheduling optimization. It extends the existing bulk job system with advanced scheduling features and integrates seamlessly with Google Sheets.

## Components

### 1. BatchScheduler (`BatchScheduler.tsx`)

A multi-step modal component for creating and configuring batch jobs with scheduling optimization.

#### Features:
- **5-Step Workflow**: Connect Sheet → Output Config → Job Details → Scheduling → Review
- **Smart Scheduling Modes**:
  - **Smart**: AI-powered optimization based on system load and content complexity
  - **Time-based**: Schedule jobs for specific time windows
  - **Content-based**: Prioritize jobs based on content tags and metadata
  - **Manual**: Full control over scheduling parameters
- **Optimization Levels**: Speed, Balanced, Quality
- **Concurrent Job Management**: Configurable parallel processing limits
- **Priority Queue Support**: Enhanced processing for high-priority content
- **Scheduling Rules Engine**: Customizable rules for advanced scheduling logic

#### Key Props:
```typescript
interface BatchSchedulerProps {
  isOpen: boolean;
  onClose: () => void;
  onJobScheduled: (job: any) => void;
}
```

### 2. SchedulingProgress (`SchedulingProgress.tsx`)

A comprehensive progress tracking component for monitoring batch operations.

#### Features:
- **Real-time Dashboard**: Summary statistics and key metrics
- **Tabbed Interface**: Filter jobs by status (Active, Completed, Failed, All)
- **Multiple View Modes**: Grid and list views
- **Sorting & Filtering**: Advanced job organization
- **Job Expansion**: Detailed progress information
- **Scheduling-specific Metrics**: Display optimization level, concurrent jobs, etc.
- **Performance Analytics**: Success rates, processing speed, ETA calculations
- **Action Controls**: Pause, resume, cancel operations

#### Key Props:
```typescript
interface SchedulingProgressProps {
  onViewDetails?: (job: BulkJob) => void;
  refreshInterval?: number;
}
```

## Integration with Existing System

### API Updates

The `apiClient` has been updated to support new scheduling properties:

```typescript
async createBulkJob(data: {
  // ... existing properties
  scheduling?: {
    mode: 'smart' | 'time_based' | 'content_based' | 'manual';
    start_immediately?: boolean;
    schedule_start_time?: string | null;
    schedule_end_time?: string | null;
    optimization_level?: 'speed' | 'balanced' | 'quality';
    max_concurrent_jobs?: number;
    priority_queue?: boolean;
    scheduling_rules?: SchedulingRule[];
  };
})
```

### Google Sheets Integration

- **Seamless Connection**: Direct integration with Google Sheets API
- **Data Validation**: Automatic validation of sheet structure and permissions
- **Sample Preview**: Preview data structure before scheduling
- **Range Configuration**: Flexible data range selection
- **Real-time Sync**: Progress updates linked to sheet data

## Scheduling Modes

### 1. Smart Scheduling
- **AI-Powered Optimization**: Automatically balances system load and content complexity
- **Dynamic Load Balancing**: Distributes jobs across available resources
- **Content Complexity Analysis**: Processes items in optimal order
- **Automatic Retry Logic**: Handles failed items intelligently
- **Real-time Performance Monitoring**: Adjusts strategy based on system performance

### 2. Time-based Scheduling
- **Immediate Start**: Option to start processing immediately
- **Scheduled Start**: Configure specific start and end times
- **Time Window Processing**: Process jobs within defined time periods
- **Deadline Management**: Set processing deadlines for time-sensitive content

### 3. Content-based Scheduling
- **Priority Thresholds**: Process content based on priority levels
- **Tag-based Filtering**: Schedule content using metadata tags
- **Complexity-based Ordering**: Process simple content first or complex content first
- **Custom Rules**: Define custom scheduling logic based on content attributes

### 4. Manual Scheduling
- **Full Control**: Manual configuration of all scheduling parameters
- **Concurrent Job Limits**: Set maximum parallel processing jobs
- **Optimization Preferences**: Choose between speed, balanced, or quality optimization
- **Custom Rules Engine**: Apply custom scheduling logic

## Advanced Features

### Scheduling Rules Engine

```typescript
interface SchedulingRule {
  id: string;
  name: string;
  type: 'time_based' | 'content_based' | 'priority_based';
  enabled: boolean;
  settings: {
    time_window?: string;
    days_of_week?: number[];
    max_concurrent?: number;
    min_interval_ms?: number;
    content_tags?: string[];
    priority_threshold?: 'low' | 'normal' | 'high';
  };
}
```

### Optimization Levels

- **Speed**: Maximum parallel processing, lower quality settings
- **Balanced**: Recommended settings for most use cases
- **Quality**: Maximum quality settings, may take longer

### Performance Monitoring

- **Real-time Progress Tracking**: Live updates of job status and completion
- **Performance Metrics**: Success rates, processing speed, ETA calculations
- **Resource Usage**: Monitor concurrent job limits and system load
- **Rate Limiting**: Automatic handling of API rate limits

## Usage Examples

### Basic Integration

```tsx
import BatchScheduler from './components/BatchScheduler';
import SchedulingProgress from './components/SchedulingProgress';

function BatchContentManager() {
  const [showScheduler, setShowScheduler] = useState(false);

  return (
    <>
      <Button onClick={() => setShowScheduler(true)}>
        Schedule Batch Job
      </Button>
      
      <BatchScheduler
        isOpen={showScheduler}
        onClose={() => setShowScheduler(false)}
        onJobScheduled={(job) => {
          console.log('Job scheduled:', job);
          setShowScheduler(false);
        }}
      />
      
      <SchedulingProgress
        onViewDetails={(job) => console.log('Job details:', job)}
        refreshInterval={5000}
      />
    </>
  );
}
```

### Advanced Configuration

```tsx
// Smart scheduling with custom rules
const smartJobConfig = {
  scheduling: {
    mode: 'smart',
    optimization_level: 'balanced',
    max_concurrent_jobs: 5,
    priority_queue: true,
    scheduling_rules: [
      {
        id: 'peak-hours-avoid',
        type: 'time_based',
        enabled: true,
        settings: {
          time_window: '09:00-17:00',
          action: 'delay'
        }
      },
      {
        id: 'high-priority-first',
        type: 'priority_based',
        enabled: true,
        settings: {
          priority_threshold: 'high'
        }
      }
    ]
  }
};
```

### Google Sheets Integration

```tsx
// The system automatically handles Google Sheets integration
// Users only need to provide:
// 1. Sheet ID (from Google Sheets URL)
// 2. Data range (e.g., "A1:Z1000")
// 3. Appropriate permissions

const sheetConfig = {
  input_source: {
    type: 'sheet',
    sheet_id: '1A2B3C4D5E6F7G8H9I0J...',
    range: 'A1:Z1000'
  }
};
```

## UI Patterns

### Design Consistency
- **Modal-based Interface**: Consistent with existing BulkJobCreator pattern
- **Step-by-step Workflow**: Clear progress indication through steps
- **Form Validation**: Real-time validation with error messages
- **Loading States**: Visual feedback during API operations
- **Dark Mode Support**: Full dark/light theme compatibility

### Component Architecture
- **Reusable Components**: Built on shadcn/ui component library
- **TypeScript Support**: Full type safety throughout
- **Responsive Design**: Mobile and desktop optimized
- **Accessibility**: ARIA labels and keyboard navigation
- **Error Boundaries**: Graceful error handling

## Performance Considerations

### Optimization Strategies
- **Efficient Polling**: Configurable refresh intervals based on job state
- **WebSocket Integration**: Real-time updates for active jobs
- **Lazy Loading**: Components load data only when needed
- **Debounced Updates**: Prevent excessive API calls
- **Caching**: Smart caching of scheduling configurations

### Resource Management
- **Concurrent Job Limits**: Prevent system overload
- **Rate Limiting**: Automatic handling of API limits
- **Memory Optimization**: Efficient state management
- **Background Processing**: Non-blocking UI updates

## Future Enhancements

### Planned Features
- **Advanced Analytics**: Detailed performance insights and trends
- **Template System**: Reusable scheduling configurations
- **Calendar Integration**: Sync with external calendar systems
- **Webhook Notifications**: Custom notification systems
- **A/B Testing**: Scheduling optimization through testing
- **Machine Learning**: Enhanced smart scheduling algorithms

### Extension Points
- **Custom Scheduling Rules**: Plugin architecture for custom logic
- **External Integrations**: API extensions for third-party services
- **Advanced Analytics**: Custom metrics and reporting
- **Multi-tenant Support**: Enhanced organization and permissions

## Error Handling

### Common Error Scenarios
1. **Sheet Connection Issues**: Network problems, permission errors
2. **Scheduling Conflicts**: Overlapping scheduled jobs, resource constraints
3. **API Rate Limits**: Excessive concurrent requests
4. **Invalid Configurations**: Malformed scheduling rules
5. **System Overload**: Resource exhaustion during peak usage

### Best Practices
- **Retry Logic**: Automatic retry with exponential backoff
- **Graceful Degradation**: Fallback to simpler scheduling modes
- **User Feedback**: Clear error messages and recovery suggestions
- **Monitoring**: Comprehensive logging and alerting
- **Validation**: Pre-flight checks before job creation

## Security Considerations

### Data Protection
- **Sheet Permissions**: Minimal required permissions for Google Sheets
- **API Key Management**: Secure storage of authentication tokens
- **Input Validation**: Sanitization of all user inputs
- **Rate Limiting**: Protection against abuse and DoS attacks

### Access Control
- **Role-based Permissions**: User access control for scheduling features
- **Audit Logging**: Track all scheduling actions and changes
- **Data Encryption**: Secure transmission of sensitive data
- **Session Management**: Secure session handling for API access
