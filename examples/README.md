# AI Content Automation System - Integration Examples

This directory contains comprehensive integration examples and tutorials for the AI Content Automation System, demonstrating various integration patterns across different platforms and use cases.

## 📁 Directory Structure

```
examples/
├── README.md                          # This file
├── scheduling_tutorial.py            # Python backend integration tutorial
├── react_scheduling_example.tsx      # React frontend components
└── google_sheets_scheduling.py       # Google Sheets integration examples
```

## 🚀 Quick Start

### Prerequisites

Before running any examples, ensure you have:

- **Python 3.8+** for backend examples
- **Node.js 16+** and **React 18+** for frontend examples
- **Access to the AI Content Automation API**
- **Google Cloud Project** (for Google Sheets integration)

### Installation

```bash
# Backend dependencies
pip install aiohttp pandas gspread google-auth google-auth-oauthlib google-auth-httplib2 python-dateutil

# Frontend dependencies (for React examples)
npm install lucide-react date-fns
```

## 📖 Available Examples

### 1. Python Backend Integration (`scheduling_tutorial.py`)

Comprehensive tutorial demonstrating backend API integration.

**Features:**
- Authentication and connection setup
- Getting optimal posting time recommendations
- Creating and managing content schedules
- Real-time progress monitoring
- Error handling and best practices
- Bulk operations with retry logic
- Multi-platform scheduling

**Usage:**
```bash
# Run complete tutorial
python scheduling_tutorial.py --full-tutorial

# Run specific examples
python scheduling_tutorial.py --basic-example
python scheduling_tutorial.py --schedule-example
python scheduling_tutorial.py --sample-data
```

**What you'll learn:**
- How to authenticate with the scheduling API
- How to get AI-generated optimal posting times
- How to create multi-platform content schedules
- How to monitor schedule progress in real-time
- How to handle errors and implement retry logic
- How to process data from Google Sheets
- How to implement batch operations

### 2. React Frontend Components (`react_scheduling_example.tsx`)

Complete React component library for frontend integration.

**Components included:**
- `SchedulingDashboard` - Main dashboard interface
- `ScheduleCreator` - Form for creating new schedules
- `RecommendationViewer` - Display optimal posting recommendations
- `ProgressMonitor` - Real-time progress tracking
- `ScheduleList` - List and manage existing schedules
- `PlatformSelector` - Multi-platform selection component
- Custom hooks and utilities

**Features:**
- Modern React with TypeScript
- Tailwind CSS styling
- Real-time WebSocket connections
- Responsive design
- Form validation
- Error handling
- Loading states

**Usage:**
```typescript
import SchedulingDashboard from './react_scheduling_example';

// Basic usage
function App() {
  return <SchedulingDashboard />;
}

// Advanced usage with custom API
import { useSchedulingAPI } from './react_scheduling_example';

function CustomComponent() {
  const api = useSchedulingAPI();
  
  const handleGetRecommendations = async () => {
    const recommendations = await api.getRecommendations(['youtube', 'linkedin']);
    console.log(recommendations);
  };
  
  return <button onClick={handleGetRecommendations}>Get Recommendations</button>;
}
```

**What you'll learn:**
- How to integrate React components with the scheduling API
- How to implement real-time progress monitoring
- How to create responsive scheduling interfaces
- How to handle form validation and user input
- How to manage application state with custom hooks
- How to implement WebSocket connections for real-time updates

### 3. Google Sheets Integration (`google_sheets_scheduling.py`)

Examples for integrating Google Sheets with the scheduling system.

**Features:**
- Google Sheets API authentication
- Reading and validating content data from sheets
- Generating optimized schedules from sheet data
- Creating schedules via the API
- Exporting results back to sheets
- Real-time synchronization
- Batch processing of multiple spreadsheets
- Comprehensive reporting

**Usage:**
```bash
# Create sample data
python google_sheets_scheduling.py --create-sample

# Run specific tutorials
python google_sheets_scheduling.py --tutorial-basic
python google_sheets_scheduling.py --tutorial-batch
python google_sheets_scheduling.py --tutorial-monitoring
python google_sheets_scheduling.py --tutorial-complete
```

**What you'll learn:**
- How to set up Google Sheets API authentication
- How to read and validate content data from spreadsheets
- How to integrate AI recommendations with existing data
- How to create schedules programmatically
- How to export scheduling results back to Google Sheets
- How to implement real-time monitoring and updates
- How to process multiple spreadsheets in batch mode

## 🏗️ Complete Integration Examples

### Content Agency Integration

Real-world example of a content agency using the system for multiple clients:

```python
from scheduling_tutorial import ContentAgencyScheduler

# Register clients
tech_client = Client(
    id="client_001",
    name="TechStartup Inc",
    platforms=["youtube", "linkedin", "twitter"],
    scheduling_preferences={"timezone": "America/Los_Angeles"}
)

# Create campaign
ai_campaign = Campaign(
    id="campaign_001",
    client_id="client_001",
    name="AI Revolution 2025",
    platforms=["youtube", "linkedin", "twitter"],
    frequency={"youtube": 1, "linkedin": 2, "twitter": 5}
)

scheduler = ContentAgencyScheduler("http://localhost:8000", "api-key")
result = await scheduler.execute_campaign("campaign_001")
```

### E-commerce Brand Integration

E-commerce brand using the system for product launches:

```python
from google_sheets_scheduling import EcommerceContentScheduler

product = Product(
    id="prod_001",
    name="Smart Home Hub Pro",
    category="tech",
    launch_date="2025-12-01T00:00:00"
)

scheduler = EcommerceContentScheduler("http://localhost:8000", "api-key")
campaign = await scheduler.create_product_launch_campaign(product)
```

## 🛠️ Configuration

### API Configuration

Create a configuration file or set environment variables:

```bash
# .env file
API_BASE_URL=http://localhost:8000
API_KEY=your-api-key-here

# Google Sheets (for sheets integration)
GOOGLE_CREDENTIALS_FILE=path/to/service-account.json
GOOGLE_SPREADSHEET_ID=your-spreadsheet-id
```

### React Configuration

Update API endpoints in your React application:

```typescript
// api.ts
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export const apiClient = {
  async getRecommendations(platforms: string[]) {
    const response = await fetch(`${API_BASE_URL}/api/v1/scheduling/recommendations`);
    return response.json();
  }
};
```

## 📋 Use Case Examples

### 1. Multi-Platform Content Calendar

```python
# Create a content calendar across multiple platforms
content_items = [
    ContentItem(
        title="AI Tutorial Part 1",
        platform="youtube",
        scheduled_time="2025-11-10T15:00:00"
    ),
    ContentItem(
        title="AI Career Tips",
        platform="linkedin", 
        scheduled_time="2025-11-11T09:00:00"
    )
]

scheduler = MultiPlatformScheduler("http://localhost:8000", "api-key")
results = await scheduler.schedule_content_batch(content_items)
```

### 2. Bulk Content Processing

```python
# Process large amounts of content from various sources
import pandas as pd

# Read from CSV/Excel
df = pd.read_csv("content_data.csv")
schedules = []

for _, row in df.iterrows():
    schedule_data = {
        "title": row['title'],
        "platform": row['platform'],
        "scheduled_time": row['scheduled_time']
    }
    schedules.append(schedule_data)

# Create all schedules with batch processing
robust_client = RobustSchedulingClient("http://localhost:8000", "api-key")
created_ids = await robust_client.batch_create_schedules(schedules, batch_size=10)
```

### 3. Real-time Campaign Monitoring

```typescript
// React component for real-time monitoring
const CampaignMonitor: React.FC<{ campaignId: string }> = ({ campaignId }) => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('pending');

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws?campaign_id=${campaignId}`);
    
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setProgress(update.progress);
      setStatus(update.status);
    };

    return () => ws.close();
  }, [campaignId]);

  return (
    <div>
      <h3>Campaign Progress: {progress}%</h3>
      <p>Status: {status}</p>
    </div>
  );
};
```

## 🧪 Testing

### Unit Testing Example

```python
import unittest
from scheduling_tutorial import SchedulingClient

class TestSchedulingClient(unittest.TestCase):
    def setUp(self):
        self.client = SchedulingClient("http://localhost:8000", "test-key")
    
    async def test_get_recommendations(self):
        recommendations = await self.client.get_recommendations(["youtube"], 5)
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
    
    async def test_create_schedule(self):
        schedule_data = {
            "title": "Test Schedule",
            "timezone": "UTC",
            "items": [{
                "content_id": "test_001",
                "platform": "youtube",
                "scheduled_time": "2025-11-10T15:00:00Z"
            }]
        }
        
        schedule_id = await self.client.create_schedule(schedule_data)
        self.assertIsNotNone(schedule_id)

if __name__ == '__main__':
    unittest.main()
```

### React Component Testing

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import ScheduleCreator from './react_scheduling_example';

test('creates schedule successfully', async () => {
  render(<ScheduleCreator onScheduleCreated={jest.fn()} onCancel={jest.fn()} />);
  
  // Fill form
  fireEvent.change(screen.getByLabelText(/title/i), {
    target: { value: 'Test Schedule' }
  });
  
  // Submit form
  fireEvent.click(screen.getByText(/create schedule/i));
  
  // Verify success
  expect(screen.getByText(/creating schedule/i)).toBeInTheDocument();
});
```

## 🔧 Troubleshooting

### Common Issues

**1. Authentication Errors**
```python
# Ensure API key is valid and not expired
client = SchedulingClient("http://localhost:8000", "valid-api-key")
connected = await client.test_connection()
```

**2. Rate Limiting**
```python
# Implement retry with exponential backoff
@retry_with_backoff(max_retries=3, base_delay=1.0)
async def create_schedule_with_retry(schedule_data):
    return await create_schedule(schedule_data)
```

**3. Google Sheets Permissions**
```bash
# Share your spreadsheet with the service account email
# Grant appropriate permissions (Editor for write access)
```

**4. WebSocket Connection Issues**
```typescript
// Implement reconnection logic
const ws = new WebSocket(wsUrl);
ws.onclose = () => {
  setTimeout(() => connectWebSocket(), 3000); // Retry after 3 seconds
};
```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Additional Resources

- [Complete Integration Documentation](../docs/integration_examples.md)
- [API Reference](../docs/api_specification.md)
- [System Architecture](../docs/system_architecture.md)
- [Google Sheets Setup Guide](../docs/google_sheets_authentication.md)

## 🤝 Contributing

When contributing examples:

1. Follow the existing code patterns and structure
2. Include comprehensive error handling
3. Add detailed comments and documentation
4. Test examples with various data sets
5. Update this README with new examples

## 📄 License

These examples are part of the AI Content Automation System and follow the same license terms.
