# Progress Tracking Dashboard

A comprehensive real-time progress tracking system for bulk content generation operations with WebSocket-based live updates and detailed monitoring capabilities.

## Features

### 🚀 Real-time Updates
- **WebSocket Integration**: Live progress updates via WebSocket connections
- **Real-time State Changes**: Instant notifications for job state transitions
- **Video-level Tracking**: Individual video item progress monitoring
- **Connection Health**: Automatic reconnection and health monitoring

### 📊 Comprehensive Progress Monitoring
- **Job-level Progress**: Overall completion percentage, ETA estimation
- **Item-level Progress**: Individual video processing status
- **Performance Metrics**: Success rates, processing times, throughput
- **Error Handling**: Detailed error reporting and retry mechanisms

### 🎨 Modern UI Components
- **Responsive Dashboard**: Mobile-friendly progress visualization
- **Interactive Charts**: Progress bars, status indicators, and metrics
- **State Management**: Filter, sort, and search capabilities
- **Dark Mode Support**: Full dark/light theme compatibility

## Architecture

### Components

#### 1. `ProgressDashboard.tsx`
The main progress tracking component that provides:
- Real-time job progress visualization
- Video-level progress monitoring
- Job control actions (pause, resume, cancel)
- Connection status monitoring
- Performance metrics display

#### 2. `useWebSocket.ts` Hook
Custom React hook for WebSocket management:
- Automatic connection handling
- Reconnection logic with exponential backoff
- Message processing and event handling
- Connection health monitoring
- Message history tracking

#### 3. API Integration
Extended API client with bulk job methods:
- Job creation and management
- Progress data retrieval
- Job control actions
- Google Sheets integration

### WebSocket Event Types

The system supports the following real-time events:

- `job.state_changed`: Job state transition (pending → running → completed)
- `job.progress`: Periodic progress updates
- `video.created`: New video item created
- `video.updated`: Video progress or metadata change
- `video.completed`: Video successfully completed
- `video.failed`: Video processing failed
- `job.completed`: Job successfully completed
- `job.failed`: Job processing failed
- `job.canceled`: Job was canceled

## Usage

### Basic Setup

1. **Import the Dashboard Component**:
```typescript
import ProgressDashboard from './components/ProgressDashboard';
```

2. **Wrap with Required Props**:
```typescript
<ProgressDashboard
  jobId="job_01HABCDEF0123456789"
  token="your-auth-token"
  jobData={{
    id: "job_01HABCDEF0123456789",
    title: "My Bulk Job",
    state: "running",
    created_at: "2025-11-05T00:52:13Z",
    processing_deadline_ms: 7200000,
    sheet_source: {
      sheet_id: "1A2B3C4D5E6F7G8H9I0J",
      range: "A1:Z1000"
    }
  }}
  onJobAction={(action, jobId) => {
    // Handle job actions
    console.log(`${action} job ${jobId}`);
  }}
/>
```

### WebSocket Hook Usage

For more granular control, use the `useWebSocket` hook:

```typescript
import useWebSocket, { JobProgress, VideoProgress } from './hooks/useWebSocket';

function MyComponent() {
  const {
    connected,
    connecting,
    error,
    connect,
    disconnect,
    getConnectionHealth,
  } = useWebSocket({
    jobId: "job_123",
    token: "auth-token",
    onProgress: (progress: JobProgress) => {
      console.log('Job progress:', progress.percent_complete);
    },
    onVideoCompleted: (video: VideoProgress) => {
      console.log('Video completed:', video.id);
    },
    onJobCompleted: (data) => {
      console.log('Job completed!', data);
    }
  });

  return (
    <div>
      <p>Status: {connected ? 'Connected' : 'Disconnected'}</p>
      <button onClick={connect}>Connect</button>
      <button onClick={disconnect}>Disconnect</button>
    </div>
  );
}
```

### Creating Bulk Jobs

```typescript
import apiClient from './lib/api';

const createJob = async () => {
  try {
    const jobData = {
      title: "Video Generation Campaign",
      priority: "normal",
      processing_deadline_ms: 7200000, // 2 hours
      input_source: {
        type: "sheet" as const,
        sheet_id: "1A2B3C4D5E6F7G8H9I0J",
        range: "A1:Z1000",
      },
      output: {
        format: "mp4" as const,
        video_codec: "h264" as const,
        audio_codec: "aac" as const,
        resolution: "1080p" as const,
        output_bucket: "content-outputs",
      },
      template: {
        template_id: "default_template",
        overrides: {
          style: "modern",
          voice: "female"
        }
      }
    };

    const response = await apiClient.createBulkJob(jobData);
    const newJob = response.data;
    
    // Navigate to progress dashboard
    navigate(`/bulk-jobs/${newJob.id}`);
    
  } catch (error) {
    console.error('Failed to create job:', error);
  }
};
```

## Integration with Progress Monitor

The dashboard integrates with the Python progress monitoring system (`code/progress_monitor.py`):

### Backend Events
The system automatically broadcasts:
- Job state changes
- Progress updates
- Video completion events
- Error notifications
- Final job summaries

### Real-time Data Flow
```
Python Progress Monitor
    ↓ (WebSocket broadcast)
WebSocket Server (port 8765)
    ↓ (real-time events)
React useWebSocket Hook
    ↓ (state updates)
ProgressDashboard Component
    ↓ (UI rendering)
Live Progress Display
```

## API Endpoints

### Bulk Jobs API
- `POST /api/v1/bulk-jobs` - Create new bulk job
- `GET /api/v1/bulk-jobs/{id}` - Get job details
- `GET /api/v1/bulk-jobs/{id}/videos` - List job videos
- `POST /api/v1/bulk-jobs/{id}/pause` - Pause job
- `POST /api/v1/bulk-jobs/{id}/resume` - Resume job
- `POST /api/v1/bulk-jobs/{id}/cancel` - Cancel job

### Google Sheets Integration
- `POST /api/v1/sheets/connect` - Connect Google Sheet
- `GET /api/v1/sheets/connections` - List connections

## Configuration

### Environment Variables
```bash
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8765

# Optional: Custom WebSocket port
WS_PORT=8765
```

### WebSocket Connection
The WebSocket connection uses query parameters:
```
ws://localhost:8765?job_id=job_123&token=auth-token&connection_id=conn_456
```

## Styling and UI Components

### Tailwind CSS Classes
The dashboard uses Tailwind CSS for styling with:
- Dark mode support (`dark:` prefixes)
- Responsive design (mobile-first)
- Custom color schemes for job states
- Animated transitions and loading states

### UI Components
Built on Radix UI primitives:
- `Progress` - Progress bars and indicators
- `Badge` - Status indicators
- `Card` - Layout containers
- `Button` - Action buttons
- `Alert` - Error and status messages
- `ScrollArea` - Scrollable content areas

## State Management

### Job States
- `pending` - Job created, waiting to start
- `running` - Actively processing items
- `pausing` - Transitioning to paused state
- `paused` - Temporarily stopped
- `completing` - Finalizing completed items
- `completed` - Successfully finished
- `canceling` - Stopping in progress
- `canceled` - Stopped by user
- `failed` - Encountered unrecoverable error

### Video States
- `pending` - Created, waiting to process
- `processing` - Currently being worked on
- `completed` - Successfully finished
- `failed` - Processing failed
- `skipped` - Intentionally skipped
- `canceled` - Stopped due to job cancellation

## Error Handling

### WebSocket Errors
- Automatic reconnection with exponential backoff
- Connection health monitoring
- Graceful degradation when offline
- User-friendly error messages

### API Errors
- Standardized error responses
- Retry logic for transient failures
- User notification for critical errors
- Detailed logging for debugging

## Performance Considerations

### Optimization Features
- **Connection Pooling**: Efficient WebSocket management
- **Message Throttling**: Prevents UI flooding
- **Lazy Loading**: Components load on demand
- **Memory Management**: Automatic cleanup of event listeners
- **Efficient Re-renders**: Optimized React state updates

### Monitoring
- Connection health metrics
- Message processing performance
- Memory usage tracking
- Error rate monitoring

## Development

### Adding New Features

1. **New Event Types**:
   - Add to `EventType` enum in `useWebSocket.ts`
   - Implement handler in `ProgressDashboard`
   - Update backend event emission

2. **Custom Metrics**:
   - Extend `JobProgress` and `VideoProgress` interfaces
   - Add calculation logic in progress calculator
   - Update UI components to display new metrics

3. **Job Actions**:
   - Add API endpoint in `apiClient`
   - Implement action handler in dashboard
   - Update WebSocket event handling

### Testing

```bash
# Run component tests
npm run test

# Run WebSocket integration tests
npm run test:websocket

# Build and preview
npm run build
npm run preview
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**:
   - Check if WebSocket server is running on port 8765
   - Verify job ID and token are correct
   - Check network/firewall settings

2. **Progress Not Updating**:
   - Ensure WebSocket connection is established
   - Check browser console for errors
   - Verify backend progress monitor is running

3. **UI Not Responsive**:
   - Check for JavaScript errors
   - Verify all UI components are properly imported
   - Ensure Tailwind CSS is configured correctly

### Debug Mode

Enable debug logging:
```typescript
localStorage.setItem('debug', 'progress-dashboard:*');
```

## License

This progress tracking system is part of the AI Content Automation project.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

For questions or support, please refer to the project documentation or create an issue.