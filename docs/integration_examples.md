# Integration Examples and Tutorials

This comprehensive guide provides practical integration examples for the AI Content Automation System, covering backend integration, frontend components, Google Sheets connectivity, and real-world use cases.

## Table of Contents

1. [Quick Start Guide](#quick-start-guide)
2. [Backend Integration Examples](#backend-integration-examples)
3. [Frontend Integration Examples](#frontend-integration-examples)
4. [Google Sheets Integration](#google-sheets-integration)
5. [Platform-Specific Integrations](#platform-specific-integrations)
6. [Real-World Use Cases](#real-world-use-cases)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Quick Start Guide

### Prerequisites

Before integrating with the AI Content Automation System, ensure you have:

- Python 3.8+ for backend integration
- Node.js 16+ for frontend integration
- Supabase project with proper schema setup
- Google Cloud Project for Sheets integration
- API credentials and authentication tokens

### Basic Setup

```bash
# Clone the system
git clone <repository-url>
cd content-creator

# Backend setup
cd backend
pip install -r requirements.txt

# Frontend setup
cd ../web-interface
npm install
npm run dev
```

## Backend Integration Examples

### 1. Scheduling Optimization Integration

```python
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Optional
import aiohttp

class SchedulingClient:
    """Client for scheduling optimization API integration"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_recommendations(self, platforms: List[str], target_count: int = 10):
        """Get optimal posting time recommendations"""
        url = f"{self.base_url}/api/v1/scheduling/recommendations"
        params = {
            "platforms": ",".join(platforms),
            "target_count": target_count
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status}")
    
    async def create_calendar_schedule(self, schedule_data: Dict):
        """Create a new content schedule"""
        url = f"{self.base_url}/api/v1/scheduling/calendar"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=schedule_data) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"Failed to create schedule: {error}")

# Example usage
async def main():
    client = SchedulingClient("http://localhost:8000", "your-api-key")
    
    # Get recommendations for multiple platforms
    recommendations = await client.get_recommendations(
        platforms=["youtube", "tiktok", "instagram"],
        target_count=15
    )
    
    print("Recommendations:", recommendations)
    
    # Create a schedule
    schedule = {
        "title": "Weekly Content Series",
        "timezone": "America/New_York",
        "items": [
            {
                "content_id": "content_123",
                "platform": "youtube",
                "scheduled_time": "2025-11-07T15:00:00-05:00",
                "metadata": {"campaign_id": "summer_launch"}
            }
        ]
    }
    
    created_schedule = await client.create_calendar_schedule(schedule)
    print("Schedule created:", created_schedule)

# Run the example
asyncio.run(main())
```

### 2. Content Generation Integration

```python
from dataclasses import dataclass
from typing import List, Optional, Dict
import aiohttp

@dataclass
class ContentRequest:
    """Content generation request model"""
    original_idea: str
    target_audience: Optional[str] = "general audience"
    tone: Optional[str] = "educational"
    platforms: Optional[List[str]] = None
    duration_preferences: Optional[Dict[str, int]] = None
    metadata: Optional[Dict] = None

class ContentGenerationClient:
    """Client for content generation API"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_project(self, content_request: ContentRequest):
        """Create a new content project"""
        url = f"{self.base_url}/api/projects"
        
        project_data = {
            "original_idea": content_request.original_idea,
            "target_audience": content_request.target_audience,
            "tone": content_request.tone,
            "metadata": content_request.metadata or {}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=project_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to create project: {await response.text()}")
    
    async def generate_script(self, project_id: str, target_duration: int = 300, scene_count: int = 5):
        """Generate script for a project"""
        url = f"{self.base_url}/api/scripts/generate"
        
        request_data = {
            "project_id": project_id,
            "target_duration": target_duration,
            "scene_count": scene_count
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=request_data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to generate script: {await response.text()}")
    
    async def monitor_progress(self, job_id: str):
        """Monitor job progress via WebSocket"""
        import websockets
        import json
        
        ws_url = f"ws://localhost:8000/ws"
        
        async with websockets.connect(ws_url) as websocket:
            await websocket.send(json.dumps({"job_id": job_id}))
            
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                
                if data.get("type") == "job_completed":
                    return data
                elif data.get("type") == "job_failed":
                    raise Exception(f"Job failed: {data.get('error')}")

# Example usage
async def content_generation_example():
    client = ContentGenerationClient("http://localhost:8000", "your-api-key")
    
    # Create content project
    request = ContentRequest(
        original_idea="How to build a successful blog in 2025",
        target_audience="aspiring bloggers",
        tone="friendly and encouraging",
        platforms=["youtube", "instagram"],
        duration_preferences={"youtube": 480, "instagram": 60}
    )
    
    project = await client.create_project(request)
    print("Project created:", project)
    
    # Generate script
    generation = await client.generate_script(project["data"]["id"])
    print("Script generation started:", generation)
    
    # Monitor progress
    job_id = generation["project_id"]
    final_result = await client.monitor_progress(job_id)
    print("Content generation completed:", final_result)

# Run the example
asyncio.run(content_generation_example())
```

### 3. Bulk Operations Integration

```python
import asyncio
from typing import List, Dict, Any
import aiohttp

class BulkOperationsClient:
    """Client for bulk operations API"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_bulk_job(self, job_data: Dict):
        """Create a new bulk processing job"""
        url = f"{self.base_url}/api/v1/bulk/jobs"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=job_data) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"Bulk job creation failed: {error}")
    
    async def get_bulk_job_status(self, job_id: str):
        """Get status of a bulk job"""
        url = f"{self.base_url}/api/v1/bulk/jobs/{job_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get job status: {await response.text()}")
    
    async def list_bulk_jobs(self, status: Optional[str] = None, limit: int = 50):
        """List all bulk jobs"""
        url = f"{self.base_url}/api/v1/bulk/jobs"
        params = {}
        
        if status:
            params["status"] = status
        if limit:
            params["limit"] = limit
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to list jobs: {await response.text()}")

# Example: Bulk content scheduling
async def bulk_scheduling_example():
    client = BulkOperationsClient("http://localhost:8000", "your-api-key")
    
    # Create bulk scheduling job
    bulk_job = {
        "name": "Weekly Multi-Platform Campaign",
        "operation_type": "schedule_content",
        "priority": "high",
        "data": {
            "content_items": [
                {
                    "title": "Tutorial 1",
                    "platforms": ["youtube", "tiktok"],
                    "scheduled_times": {
                        "youtube": "2025-11-10T15:00:00-05:00",
                        "tiktok": "2025-11-10T16:00:00-05:00"
                    }
                },
                {
                    "title": "Tutorial 2", 
                    "platforms": ["instagram", "linkedin"],
                    "scheduled_times": {
                        "instagram": "2025-11-11T10:00:00-05:00",
                        "linkedin": "2025-11-11T11:00:00-05:00"
                    }
                }
            ]
        }
    }
    
    # Create the job
    job_result = await client.create_bulk_job(bulk_job)
    print("Bulk job created:", job_result)
    
    # Monitor progress
    job_id = job_result["data"]["id"]
    while True:
        status = await client.get_bulk_job_status(job_id)
        print(f"Job status: {status['data']['status']}")
        
        if status["data"]["status"] in ["completed", "failed"]:
            break
        
        await asyncio.sleep(5)  # Wait 5 seconds before checking again
    
    print("Bulk job completed!")

# Run the example
asyncio.run(bulk_scheduling_example())
```

## Frontend Integration Examples

### 1. React Scheduling Components

```typescript
// SchedulingDashboard.tsx
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Clock, Plus, Calendar, BarChart3 } from 'lucide-react';

interface ScheduleItem {
  id: string;
  content_id: string;
  platform: string;
  scheduled_time: string;
  status: 'pending' | 'scheduled' | 'published' | 'failed';
  metadata?: any;
}

interface Recommendation {
  platform: string;
  recommended_time: string;
  confidence_score: number;
  reason: string;
}

const SchedulingDashboard: React.FC = () => {
  const [schedules, setSchedules] = useState<ScheduleItem[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState('all');

  useEffect(() => {
    loadSchedules();
    loadRecommendations();
  }, [selectedPlatform]);

  const loadSchedules = async () => {
    try {
      const response = await fetch(`/api/v1/scheduling/calendar?platform=${selectedPlatform}`);
      const data = await response.json();
      setSchedules(data.data || []);
    } catch (error) {
      console.error('Failed to load schedules:', error);
    }
  };

  const loadRecommendations = async () => {
    try {
      const response = await fetch(`/api/v1/scheduling/recommendations?platforms=${selectedPlatform}&target_count=5`);
      const data = await response.json();
      setRecommendations(data.data || []);
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    }
  };

  const createSchedule = async (scheduleData: any) => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/scheduling/calendar', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(scheduleData)
      });

      if (response.ok) {
        await loadSchedules();
        alert('Schedule created successfully!');
      }
    } catch (error) {
      console.error('Failed to create schedule:', error);
      alert('Failed to create schedule');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'scheduled': return 'bg-blue-100 text-blue-800';
      case 'published': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Content Scheduling</h1>
        <div className="flex gap-2">
          <Button onClick={() => loadSchedules()} variant="outline">
            <BarChart3 className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Platform Filter */}
      <Card>
        <CardHeader>
          <CardTitle>Platform Filter</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            {['all', 'youtube', 'tiktok', 'instagram', 'linkedin', 'twitter'].map((platform) => (
              <Button
                key={platform}
                variant={selectedPlatform === platform ? 'default' : 'outline'}
                onClick={() => setSelectedPlatform(platform)}
                className="capitalize"
              >
                {platform}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            AI Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recommendations.map((rec, index) => (
              <div key={index} className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <Badge variant="outline" className="capitalize">
                    {rec.platform}
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    {Math.round(rec.confidence_score * 100)}% confidence
                  </span>
                </div>
                <p className="font-medium">{formatDateTime(rec.recommended_time)}</p>
                <p className="text-sm text-muted-foreground mt-1">{rec.reason}</p>
                <Button 
                  className="w-full mt-3" 
                  size="sm"
                  onClick={() => createSchedule({
                    title: `Recommended ${rec.platform} post`,
                    timezone: 'America/New_York',
                    items: [{
                      content_id: `generated_${Date.now()}`,
                      platform: rec.platform,
                      scheduled_time: rec.recommended_time,
                      metadata: { auto_generated: true, confidence: rec.confidence_score }
                    }]
                  })}
                >
                  Schedule
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Scheduled Content */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Scheduled Content
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {schedules.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">
                No scheduled content found
              </p>
            ) : (
              schedules.map((schedule) => (
                <div key={schedule.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Badge variant="outline" className="capitalize">
                        {schedule.platform}
                      </Badge>
                      <Badge className={getStatusColor(schedule.status)}>
                        {schedule.status}
                      </Badge>
                    </div>
                    <p className="font-medium">{formatDateTime(schedule.scheduled_time)}</p>
                    {schedule.metadata && (
                      <p className="text-sm text-muted-foreground">
                        Campaign: {schedule.metadata.campaign_id || 'N/A'}
                      </p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline">Edit</Button>
                    <Button size="sm" variant="destructive">Cancel</Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Create New Schedule */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="w-5 h-5" />
            Create New Schedule
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScheduleForm onSubmit={createSchedule} loading={loading} />
        </CardContent>
      </Card>
    </div>
  );
};

// ScheduleForm.tsx
const ScheduleForm: React.FC<{
  onSubmit: (data: any) => void;
  loading: boolean;
}> = ({ onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    title: '',
    timezone: 'America/New_York',
    items: [{
      content_id: '',
      platform: 'youtube',
      scheduled_time: '',
      metadata: {}
    }]
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const addItem = () => {
    setFormData(prev => ({
      ...prev,
      items: [...prev.items, {
        content_id: '',
        platform: 'youtube',
        scheduled_time: '',
        metadata: {}
      }]
    }));
  };

  const removeItem = (index: number) => {
    setFormData(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index)
    }));
  };

  const updateItem = (index: number, field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      items: prev.items.map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Title</label>
          <Input
            value={formData.title}
            onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
            placeholder="Schedule title"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Timezone</label>
          <Input
            value={formData.timezone}
            onChange={(e) => setFormData(prev => ({ ...prev, timezone: e.target.value }))}
            placeholder="America/New_York"
          />
        </div>
      </div>

      <div className="space-y-4">
        {formData.items.map((item, index) => (
          <div key={index} className="p-4 border rounded-lg space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-medium">Content Item {index + 1}</h4>
              {formData.items.length > 1 && (
                <Button
                  type="button"
                  variant="destructive"
                  size="sm"
                  onClick={() => removeItem(index)}
                >
                  Remove
                </Button>
              )}
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Content ID</label>
                <Input
                  value={item.content_id}
                  onChange={(e) => updateItem(index, 'content_id', e.target.value)}
                  placeholder="content_123"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Platform</label>
                <select
                  value={item.platform}
                  onChange={(e) => updateItem(index, 'platform', e.target.value)}
                  className="w-full p-2 border rounded"
                  required
                >
                  <option value="youtube">YouTube</option>
                  <option value="tiktok">TikTok</option>
                  <option value="instagram">Instagram</option>
                  <option value="linkedin">LinkedIn</option>
                  <option value="twitter">Twitter/X</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Scheduled Time</label>
                <Input
                  type="datetime-local"
                  value={item.scheduled_time}
                  onChange={(e) => updateItem(index, 'scheduled_time', e.target.value)}
                  required
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <Button type="button" variant="outline" onClick={addItem}>
          Add Content Item
        </Button>
        <Button type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Create Schedule'}
        </Button>
      </div>
    </form>
  );
};

export default SchedulingDashboard;
```

### 2. Real-time Progress Monitoring

```typescript
// WebSocketProgressMonitor.tsx
import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Activity, CheckCircle, XCircle, Clock } from 'lucide-react';

interface ProgressUpdate {
  type: 'job_progress' | 'job_completed' | 'job_failed';
  data: {
    job_id: string;
    progress: number;
    step?: string;
    error?: string;
  };
}

interface JobStatus {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  step: string;
  startTime: Date;
  endTime?: Date;
}

const WebSocketProgressMonitor: React.FC = () => {
  const [jobs, setJobs] = useState<Record<string, JobStatus>>({});
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const token = localStorage.getItem('token');
    if (!token) {
      console.error('No authentication token found');
      return;
    }

    const wsUrl = `ws://localhost:8000/ws?token=${token}`;
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      
      // Subscribe to progress updates
      wsRef.current?.send(JSON.stringify({
        type: 'subscribe',
        channels: ['job_progress']
      }));
    };

    wsRef.current.onmessage = (event) => {
      const data: ProgressUpdate = JSON.parse(event.data);
      handleProgressUpdate(data);
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      
      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        if (!isConnected) {
          connectWebSocket();
        }
      }, 3000);
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };
  };

  const handleProgressUpdate = (update: ProgressUpdate) => {
    setJobs(prev => {
      const updated = { ...prev };
      
      if (!updated[update.data.job_id]) {
        updated[update.data.job_id] = {
          id: update.data.job_id,
          status: 'pending',
          progress: 0,
          step: '',
          startTime: new Date()
        };
      }

      const job = updated[update.data.job_id];
      
      switch (update.type) {
        case 'job_progress':
          job.status = 'running';
          job.progress = update.data.progress;
          job.step = update.data.step || job.step;
          break;
        case 'job_completed':
          job.status = 'completed';
          job.progress = 100;
          job.endTime = new Date();
          break;
        case 'job_failed':
          job.status = 'failed';
          job.endTime = new Date();
          break;
      }
      
      return updated;
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'running': return <Activity className="w-4 h-4 text-blue-500" />;
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed': return <XCircle className="w-4 h-4 text-red-500" />;
      default: return null;
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'pending': return 'secondary';
      case 'running': return 'default';
      case 'completed': return 'outline';
      case 'failed': return 'destructive';
      default: return 'outline';
    }
  };

  const formatDuration = (start: Date, end?: Date) => {
    const duration = end ? end.getTime() - start.getTime() : Date.now() - start.getTime();
    const seconds = Math.floor(duration / 1000);
    const minutes = Math.floor(seconds / 60);
    
    if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    }
    return `${seconds}s`;
  };

  return (
    <div className="space-y-4 p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Job Progress Monitor</h2>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-muted-foreground">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {Object.values(jobs).map(job => (
          <Card key={job.id}>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center justify-between text-sm">
                <span className="truncate">Job {job.id.slice(-8)}</span>
                {getStatusIcon(job.status)}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Status</span>
                  <Badge variant={getStatusBadgeVariant(job.status)} className="text-xs">
                    {job.status}
                  </Badge>
                </div>
                
                {job.status === 'running' && (
                  <div className="space-y-1">
                    <Progress value={job.progress} className="h-2" />
                    <p className="text-xs text-center text-muted-foreground">
                      {job.progress}% - {job.step}
                    </p>
                  </div>
                )}
                
                {job.status === 'completed' && (
                  <div className="space-y-1">
                    <Progress value={100} className="h-2" />
                    <p className="text-xs text-center text-green-600 font-medium">
                      Completed successfully
                    </p>
                  </div>
                )}
                
                {job.status === 'failed' && (
                  <div className="space-y-1">
                    <Progress value={job.progress} className="h-2" />
                    <p className="text-xs text-center text-red-600 font-medium">
                      Failed to complete
                    </p>
                  </div>
                )}
                
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>Duration</span>
                  <span>{formatDuration(job.startTime, job.endTime)}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {Object.keys(jobs).length === 0 && (
        <Card>
          <CardContent className="text-center py-8">
            <p className="text-muted-foreground">
              No active jobs. Start generating content to see progress updates.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default WebSocketProgressMonitor;
```

## Google Sheets Integration

### 1. Python Google Sheets Scheduling Integration

```python
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Optional
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from dataclasses import dataclass

@dataclass
class SheetsConfig:
    """Google Sheets configuration"""
    credentials_path: str
    spreadsheet_id: str
    sheet_name: str
    credentials_json: Optional[str] = None

@dataclass
class ContentScheduleItem:
    """Content schedule item for sheets"""
    title: str
    content: str
    target_audience: str
    tone: str
    platform: str
    scheduled_time: str
    status: str = "draft"
    generated_content_url: Optional[str] = None

class GoogleSheetsSchedulingClient:
    """Google Sheets integration for content scheduling"""
    
    def __init__(self, config: SheetsConfig):
        self.config = config
        self.client = self._authenticate()
        self.spreadsheet = self.client.open_by_key(config.spreadsheet_id)
        self.worksheet = self.spreadsheet.worksheet(config.sheet_name)
    
    def _authenticate(self):
        """Authenticate with Google Sheets API"""
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        if self.config.credentials_json:
            # Use JSON credentials
            credentials = Credentials.from_service_account_info(
                self.config.credentials_json, scopes=scope
            )
        else:
            # Use service account file
            credentials = Credentials.from_service_account_file(
                self.config.credentials_path, scopes=scope
            )
        
        return gspread.authorize(credentials)
    
    def read_content_data(self) -> List[ContentScheduleItem]:
        """Read content data from Google Sheets"""
        try:
            # Get all values from the sheet
            values = self.worksheet.get_all_values()
            
            if not values:
                return []
            
            # Assume first row contains headers
            headers = values[0]
            content_items = []
            
            for row in values[1:]:
                if len(row) >= 7:  # Ensure we have all required columns
                    item = ContentScheduleItem(
                        title=row[0],
                        content=row[1],
                        target_audience=row[2],
                        tone=row[3],
                        platform=row[4],
                        scheduled_time=row[5],
                        status=row[6] if len(row) > 6 else "draft",
                        generated_content_url=row[7] if len(row) > 7 else None
                    )
                    content_items.append(item)
            
            return content_items
        
        except Exception as e:
            print(f"Error reading sheet data: {e}")
            return []
    
    def write_scheduled_content(self, schedule_data: List[Dict]):
        """Write scheduled content back to Google Sheets"""
        try:
            # Clear the sheet first
            self.worksheet.clear()
            
            # Write headers
            headers = [
                'Title', 'Content', 'Target Audience', 'Tone', 
                'Platform', 'Scheduled Time', 'Status', 'Generated Content URL'
            ]
            self.worksheet.update('A1:H1', [headers])
            
            # Write data
            data = []
            for item in schedule_data:
                row = [
                    item.get('title', ''),
                    item.get('content', ''),
                    item.get('target_audience', ''),
                    item.get('tone', ''),
                    item.get('platform', ''),
                    item.get('scheduled_time', ''),
                    item.get('status', 'scheduled'),
                    item.get('generated_content_url', '')
                ]
                data.append(row)
            
            if data:
                self.worksheet.update('A2:H' + str(len(data) + 1), data)
            
            print(f"Successfully wrote {len(data)} items to Google Sheets")
        
        except Exception as e:
            print(f"Error writing to sheet: {e}")
    
    def update_content_status(self, row_index: int, status: str, content_url: str = None):
        """Update content status in a specific row"""
        try:
            # Update status column (column G)
            self.worksheet.update(f'G{row_index}', [[status]])
            
            # Update content URL if provided (column H)
            if content_url:
                self.worksheet.update(f'H{row_index}', [[content_url]])
            
        except Exception as e:
            print(f"Error updating row {row_index}: {e}")
    
    def create_sheet_from_template(self, title: str = "Content Schedule"):
        """Create a new sheet from template"""
        try:
            worksheet = self.spreadsheet.add_worksheet(title=title, rows="1000", cols="10")
            
            # Add template headers and sample data
            headers = [
                'Title', 'Content', 'Target Audience', 'Tone', 
                'Platform', 'Scheduled Time', 'Status', 'Generated Content URL'
            ]
            
            sample_data = [
                ["Example Tutorial", "How to start coding", "beginners", "friendly", 
                 "youtube", "2025-11-10T15:00:00", "draft", ""],
                ["Quick Tip", "Productivity hack", "professionals", "concise", 
                 "linkedin", "2025-11-11T09:00:00", "draft", ""]
            ]
            
            worksheet.update('A1:H1', [headers])
            worksheet.update('A2:H3', sample_data)
            
            return worksheet
            
        except Exception as e:
            print(f"Error creating sheet: {e}")
            return None

class SheetsSchedulingIntegration:
    """Main integration class for Google Sheets scheduling"""
    
    def __init__(self, sheets_config: SheetsConfig, scheduling_api_url: str, api_key: str):
        self.sheets_client = GoogleSheetsSchedulingClient(sheets_config)
        self.scheduling_api_url = scheduling_api_url
        self.api_key = api_key
    
    async def import_and_schedule_content(self) -> List[Dict]:
        """Import content from sheets and create schedules"""
        try:
            # Read content from Google Sheets
            content_items = self.sheets_client.read_content_data()
            
            if not content_items:
                print("No content found in Google Sheets")
                return []
            
            scheduled_items = []
            
            for item in content_items:
                try:
                    # Create schedule item for API
                    schedule_data = {
                        "title": item.title,
                        "timezone": "America/New_York",
                        "items": [{
                            "content_id": f"sheets_{item.title.replace(' ', '_').lower()}",
                            "platform": item.platform,
                            "scheduled_time": item.scheduled_time,
                            "metadata": {
                                "source": "google_sheets",
                                "target_audience": item.target_audience,
                                "tone": item.tone,
                                "content": item.content
                            }
                        }]
                    }
                    
                    # Make API call to create schedule
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{self.scheduling_api_url}/api/v1/scheduling/calendar",
                            headers={"Authorization": f"Bearer {self.api_key}"},
                            json=schedule_data
                        ) as response:
                            if response.status == 201:
                                result = await response.json()
                                scheduled_items.append({
                                    "title": item.title,
                                    "platform": item.platform,
                                    "scheduled_time": item.scheduled_time,
                                    "status": "scheduled",
                                    "schedule_id": result["data"]["id"]
                                })
                                
                                # Update status in sheets
                                self.sheets_client.update_content_status(
                                    len(scheduled_items), "scheduled"
                                )
                            else:
                                print(f"Failed to schedule {item.title}: {response.status}")
                
                except Exception as e:
                    print(f"Error scheduling {item.title}: {e}")
                    continue
            
            return scheduled_items
        
        except Exception as e:
            print(f"Error in import_and_schedule_content: {e}")
            return []
    
    async def export_scheduled_results(self, schedule_ids: List[str]):
        """Export scheduling results back to sheets"""
        try:
            export_data = []
            
            for schedule_id in schedule_ids:
                # Get schedule details from API
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.scheduling_api_url}/api/v1/scheduling/calendar/{schedule_id}",
                        headers={"Authorization": f"Bearer {self.api_key}"}
                    ) as response:
                        if response.status == 200:
                            schedule = await response.json()
                            export_data.append({
                                "title": schedule["data"]["title"],
                                "content": schedule["data"]["items"][0]["metadata"]["content"],
                                "target_audience": schedule["data"]["items"][0]["metadata"]["target_audience"],
                                "tone": schedule["data"]["items"][0]["metadata"]["tone"],
                                "platform": schedule["data"]["items"][0]["platform"],
                                "scheduled_time": schedule["data"]["items"][0]["scheduled_time"],
                                "status": "completed"
                            })
            
            # Write to sheets
            self.sheets_client.write_scheduled_content(export_data)
            print(f"Exported {len(export_data)} scheduled items to Google Sheets")
        
        except Exception as e:
            print(f"Error exporting results: {e}")

# Example usage
async def main():
    # Configure Google Sheets
    sheets_config = SheetsConfig(
        credentials_path="path/to/service-account.json",
        spreadsheet_id="your-spreadsheet-id",
        sheet_name="Content Schedule"
    )
    
    # Configure API
    scheduling_api_url = "http://localhost:8000"
    api_key = "your-api-key"
    
    # Initialize integration
    integration = SheetsSchedulingIntegration(sheets_config, scheduling_api_url, api_key)
    
    # Import and schedule content
    scheduled = await integration.import_and_schedule_content()
    print(f"Scheduled {len(scheduled)} content items")
    
    # Export results
    schedule_ids = [item["schedule_id"] for item in scheduled]
    await integration.export_scheduled_results(schedule_ids)

# Run the example
asyncio.run(main())
```

### 2. React Google Sheets Connection Component

```typescript
// GoogleSheetsConnection.tsx
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Spreadsheet, Link, CheckCircle, AlertCircle, Plus } from 'lucide-react';
import { gapi } from 'gapi';

interface GoogleSheetConnection {
  id: string;
  name: string;
  spreadsheet_id: string;
  sheet_name: string;
  range: string;
  permissions: 'read' | 'write' | 'admin';
  last_sync?: string;
  status: 'connected' | 'error' | 'syncing';
}

interface SpreadsheetInfo {
  id: string;
  name: string;
  modifiedTime: string;
}

const GoogleSheetsConnection: React.FC = () => {
  const [connections, setConnections] = useState<GoogleSheetConnection[]>([]);
  const [spreadsheets, setSpreadsheets] = useState<SpreadsheetInfo[]>([]);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(false);
  const [newConnectionDialogOpen, setNewConnectionDialogOpen] = useState(false);

  useEffect(() => {
    initializeGoogleAPI();
    loadConnections();
  }, []);

  const initializeGoogleAPI = async () => {
    try {
      await gapi.load('auth2', async () => {
        await gapi.auth2.init({
          client_id: 'your-google-client-id.apps.googleusercontent.com'
        });
        
        const isSignedIn = gapi.auth2.getAuthInstance().isSignedIn.get();
        setIsAuthenticated(isSignedIn);
        
        if (isSignedIn) {
          await loadSpreadsheets();
        }
      });
    } catch (error) {
      console.error('Failed to initialize Google API:', error);
    }
  };

  const signIn = async () => {
    try {
      await gapi.auth2.getAuthInstance().signIn();
      setIsAuthenticated(true);
      await loadSpreadsheets();
    } catch (error) {
      console.error('Sign in failed:', error);
    }
  };

  const signOut = async () => {
    try {
      await gapi.auth2.getAuthInstance().signOut();
      setIsAuthenticated(false);
      setSpreadsheets([]);
    } catch (error) {
      console.error('Sign out failed:', error);
    }
  };

  const loadSpreadsheets = async () => {
    try {
      const response = await gapi.client.drive.files.list({
        q: "mimeType='application/vnd.google-apps.spreadsheet'",
        pageSize: 10,
        fields: 'files(id,name,modifiedTime)'
      });
      
      setSpreadsheets(response.result.files || []);
    } catch (error) {
      console.error('Failed to load spreadsheets:', error);
    }
  };

  const loadConnections = async () => {
    try {
      const response = await fetch('/api/google-sheets/connections');
      const data = await response.json();
      setConnections(data.data || []);
    } catch (error) {
      console.error('Failed to load connections:', error);
    }
  };

  const createConnection = async (spreadsheetId: string, sheetName: string, range: string) => {
    setLoading(true);
    try {
      const response = await fetch('/api/google-sheets/connections', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          spreadsheet_id: spreadsheetId,
          name: `Connection to ${sheetName}`,
          sheet_name: sheetName,
          range: range,
          permissions: 'write'
        })
      });

      if (response.ok) {
        await loadConnections();
        setNewConnectionDialogOpen(false);
      }
    } catch (error) {
      console.error('Failed to create connection:', error);
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async (connectionId: string) => {
    try {
      const response = await fetch(`/api/google-sheets/connections/${connectionId}/test`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        alert('Connection test successful!');
        await loadConnections();
      } else {
        alert('Connection test failed!');
      }
    } catch (error) {
      console.error('Connection test failed:', error);
      alert('Connection test failed!');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'syncing':
        return <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />;
      default:
        return null;
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'connected':
        return 'outline';
      case 'error':
        return 'destructive';
      case 'syncing':
        return 'default';
      default:
        return 'secondary';
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Spreadsheet className="w-5 h-5" />
              Connect Google Sheets
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              Connect your Google Sheets to import and export content data for automated scheduling.
            </p>
            <Button onClick={signIn} className="w-full">
              <Link className="w-4 h-4 mr-2" />
              Connect Google Sheets
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Google Sheets Integration</h1>
        <div className="flex gap-2">
          <Button onClick={signOut} variant="outline">Sign Out</Button>
          <Dialog open={newConnectionDialogOpen} onOpenChange={setNewConnectionDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                New Connection
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Connection</DialogTitle>
              </DialogHeader>
              <NewConnectionForm 
                spreadsheets={spreadsheets}
                onCreate={createConnection}
                loading={loading}
              />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Existing Connections */}
      <Card>
        <CardHeader>
          <CardTitle>Active Connections</CardTitle>
        </CardHeader>
        <CardContent>
          {connections.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground mb-4">No active connections found</p>
              <Button onClick={() => setNewConnectionDialogOpen(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Create First Connection
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {connections.map((connection) => (
                <div key={connection.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Spreadsheet className="w-4 h-4" />
                      <span className="font-medium">{connection.name}</span>
                      {getStatusIcon(connection.status)}
                      <Badge variant={getStatusBadgeVariant(connection.status)}>
                        {connection.status}
                      </Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      <p>Sheet: {connection.sheet_name} | Range: {connection.range}</p>
                      <p>Permissions: {connection.permissions}</p>
                      {connection.last_sync && (
                        <p>Last sync: {new Date(connection.last_sync).toLocaleString()}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline">
                      Sync
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => testConnection(connection.id)}>
                      Test
                    </Button>
                    <Button size="sm" variant="destructive">
                      Delete
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Available Spreadsheets */}
      <Card>
        <CardHeader>
          <CardTitle>Your Spreadsheets</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {spreadsheets.map((sheet) => (
              <div key={sheet.id} className="p-4 border rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Spreadsheet className="w-4 h-4" />
                  <span className="font-medium">{sheet.name}</span>
                </div>
                <p className="text-sm text-muted-foreground mb-3">
                  Modified: {new Date(sheet.modifiedTime).toLocaleDateString()}
                </p>
                <Button 
                  size="sm" 
                  onClick={() => setNewConnectionDialogOpen(true)}
                  className="w-full"
                >
                  Connect
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const NewConnectionForm: React.FC<{
  spreadsheets: SpreadsheetInfo[];
  onCreate: (spreadsheetId: string, sheetName: string, range: string) => void;
  loading: boolean;
}> = ({ spreadsheets, onCreate, loading }) => {
  const [formData, setFormData] = useState({
    spreadsheet_id: '',
    sheet_name: '',
    range: 'A:Z',
    name: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onCreate(formData.spreadsheet_id, formData.sheet_name, formData.range);
  };

  const selectedSpreadsheet = spreadsheets.find(s => s.id === formData.spreadsheet_id);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-1">Spreadsheet</label>
        <select
          value={formData.spreadsheet_id}
          onChange={(e) => setFormData(prev => ({ 
            ...prev, 
            spreadsheet_id: e.target.value,
            name: selectedSpreadsheet?.name || prev.name
          }))}
          className="w-full p-2 border rounded"
          required
        >
          <option value="">Select a spreadsheet</option>
          {spreadsheets.map(sheet => (
            <option key={sheet.id} value={sheet.id}>
              {sheet.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Sheet Name</label>
        <Input
          value={formData.sheet_name}
          onChange={(e) => setFormData(prev => ({ ...prev, sheet_name: e.target.value }))}
          placeholder="Sheet1"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Data Range</label>
        <Input
          value={formData.range}
          onChange={(e) => setFormData(prev => ({ ...prev, range: e.target.value }))}
          placeholder="A:Z"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Connection Name</label>
        <Input
          value={formData.name}
          onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
          placeholder="Content Schedule"
          required
        />
      </div>

      <Button type="submit" disabled={loading} className="w-full">
        {loading ? 'Creating...' : 'Create Connection'}
      </Button>
    </form>
  );
};

export default GoogleSheetsConnection;
```

## Platform-Specific Integrations

### 1. YouTube Integration

```python
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timezone
import aiohttp

class YouTubeSchedulingClient:
    """YouTube-specific scheduling integration"""
    
    def __init__(self, api_key: str, channel_id: str):
        self.api_key = api_key
        self.channel_id = channel_id
        self.base_url = "https://www.googleapis.com/youtube/v3"
    
    async def get_channel_info(self) -> Dict:
        """Get channel information"""
        url = f"{self.base_url}/channels"
        params = {
            'part': 'snippet,statistics',
            'id': self.channel_id,
            'key': self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                return data['items'][0] if data.get('items') else {}
    
    async def schedule_video_upload(self, video_data: Dict) -> Dict:
        """Schedule video upload using YouTube Data API"""
        # This would integrate with YouTube's upload API
        # For now, we'll simulate the integration
        upload_data = {
            'title': video_data.get('title'),
            'description': video_data.get('description'),
            'tags': video_data.get('tags', []),
            'scheduled_publish_time': video_data.get('scheduled_time'),
            'privacy_status': 'private'
        }
        
        # Simulate API call
        return {
            'status': 'scheduled',
            'video_id': f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'scheduled_publish_time': video_data.get('scheduled_time'),
            'url': f"https://youtube.com/watch?v=video_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
    
    async def get_optimal_upload_times(self) -> List[Dict]:
        """Get optimal upload times based on analytics"""
        # This would use YouTube Analytics API
        # For now, return recommended times
        return [
            {
                'day_of_week': 'Tuesday',
                'time': '15:00',
                'timezone': 'America/New_York',
                'audience_activity': 'high',
                'estimated_performance': 0.85
            },
            {
                'day_of_week': 'Thursday', 
                'time': '15:00',
                'timezone': 'America/New_York',
                'audience_activity': 'high',
                'estimated_performance': 0.82
            }
        ]

# Usage example
async def youtube_integration_example():
    client = YouTubeSchedulingClient("your-api-key", "your-channel-id")
    
    # Get channel info
    channel_info = await client.get_channel_info()
    print("Channel:", channel_info.get('snippet', {}).get('title'))
    
    # Get optimal times
    optimal_times = await client.get_optimal_upload_times()
    print("Optimal upload times:", optimal_times)
    
    # Schedule video
    video_data = {
        'title': 'How to Start Coding in 2025',
        'description': 'Complete beginner guide...',
        'tags': ['coding', 'tutorial', 'programming'],
        'scheduled_time': '2025-11-10T15:00:00-05:00'
    }
    
    scheduled = await client.schedule_video_upload(video_data)
    print("Video scheduled:", scheduled)

# Run example
asyncio.run(youtube_integration_example())
```

### 2. Multi-Platform Scheduling Service

```python
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp

class Platform(Enum):
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    FACEBOOK = "facebook"

@dataclass
class ContentItem:
    title: str
    content: str
    platform: Platform
    scheduled_time: str
    metadata: Dict = None

@dataclass
class SchedulingResult:
    platform: Platform
    status: str
    content_id: str
    scheduled_time: str
    url: Optional[str] = None
    error: Optional[str] = None

class MultiPlatformScheduler:
    """Multi-platform content scheduling service"""
    
    def __init__(self, api_base_url: str, api_key: str):
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def schedule_content_batch(self, content_items: List[ContentItem]) -> List[SchedulingResult]:
        """Schedule content across multiple platforms"""
        results = []
        
        # Group by platform for efficient processing
        platform_groups = {}
        for item in content_items:
            if item.platform not in platform_groups:
                platform_groups[item.platform] = []
            platform_groups[item.platform].append(item)
        
        # Process each platform concurrently
        tasks = []
        for platform, items in platform_groups.items():
            task = self._schedule_for_platform(platform, items)
            tasks.append(task)
        
        # Execute all platform schedules concurrently
        platform_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        for result_group in platform_results:
            if isinstance(result_group, Exception):
                # Handle platform-level errors
                for platform in platform_groups.keys():
                    results.append(SchedulingResult(
                        platform=platform,
                        status="error",
                        content_id="",
                        scheduled_time="",
                        error=str(result_group)
                    ))
            else:
                results.extend(result_group)
        
        return results
    
    async def _schedule_for_platform(self, platform: Platform, items: List[ContentItem]) -> List[SchedulingResult]:
        """Schedule content for a specific platform"""
        results = []
        
        for item in items:
            try:
                # Create schedule entry
                schedule_data = {
                    "title": item.title,
                    "timezone": "America/New_York",
                    "items": [{
                        "content_id": f"{platform.value}_{item.title.replace(' ', '_').lower()}",
                        "platform": platform.value,
                        "scheduled_time": item.scheduled_time,
                        "metadata": {
                            "source": "multi_platform_scheduler",
                            "content": item.content,
                            **(item.metadata or {})
                        }
                    }]
                }
                
                # Call scheduling API
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.api_base_url}/api/v1/scheduling/calendar",
                        headers=self.headers,
                        json=schedule_data
                    ) as response:
                        if response.status == 201:
                            result_data = await response.json()
                            results.append(SchedulingResult(
                                platform=platform,
                                status="scheduled",
                                content_id=result_data["data"]["id"],
                                scheduled_time=item.scheduled_time,
                                url=result_data["data"].get("url")
                            ))
                        else:
                            error_text = await response.text()
                            results.append(SchedulingResult(
                                platform=platform,
                                status="failed",
                                content_id="",
                                scheduled_time=item.scheduled_time,
                                error=f"API Error {response.status}: {error_text}"
                            ))
                
                # Add small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                results.append(SchedulingResult(
                    platform=platform,
                    status="error",
                    content_id="",
                    scheduled_time=item.scheduled_time,
                    error=str(e)
                ))
        
        return results
    
    async def optimize_schedule_timing(self, content_items: List[ContentItem]) -> List[ContentItem]:
        """Optimize schedule timing based on platform analytics"""
        optimized_items = []
        
        for item in content_items:
            # Get recommendations for the platform
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/api/v1/scheduling/recommendations",
                    headers=self.headers,
                    params={
                        "platforms": item.platform.value,
                        "target_count": 1
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        recommendations = data.get("data", [])
                        
                        if recommendations:
                            # Use the first recommendation
                            optimized_time = recommendations[0]["recommended_time"]
                            item.scheduled_time = optimized_time
            
            optimized_items.append(item)
        
        return optimized_items
    
    async def get_schedule_status(self, content_id: str) -> Dict:
        """Get status of scheduled content"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_base_url}/api/v1/scheduling/calendar/{content_id}",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get status for {content_id}")

# Usage example
async def multi_platform_example():
    scheduler = MultiPlatformScheduler("http://localhost:8000", "your-api-key")
    
    # Create content for multiple platforms
    content_items = [
        ContentItem(
            title="YouTube Tutorial: AI in 2025",
            content="Complete guide to artificial intelligence...",
            platform=Platform.YOUTUBE,
            scheduled_time="2025-11-10T15:00:00-05:00"
        ),
        ContentItem(
            title="Quick AI Tips",
            content="5 AI tools you need to know...",
            platform=Platform.TIKTOK,
            scheduled_time="2025-11-10T16:00:00-05:00"
        ),
        ContentItem(
            title="AI Career Advice",
            content="How to prepare for AI jobs...",
            platform=Platform.LINKEDIN,
            scheduled_time="2025-11-11T09:00:00-05:00"
        )
    ]
    
    # Optimize timing first
    optimized_items = await scheduler.optimize_schedule_timing(content_items)
    print("Optimized scheduling times")
    
    # Schedule across platforms
    results = await scheduler.schedule_content_batch(optimized_items)
    
    # Print results
    for result in results:
        print(f"{result.platform.value}: {result.status} - {result.content_id}")
        if result.error:
            print(f"  Error: {result.error}")

# Run example
asyncio.run(multi_platform_example())
```

## Real-World Use Cases

### 1. Content Agency Integration

```python
"""
Real-world example: Content Agency using the system for multiple clients
"""
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

@dataclass
class Client:
    id: str
    name: str
    industry: str
    platforms: List[str]
    scheduling_preferences: Dict

@dataclass
class Campaign:
    id: str
    client_id: str
    name: str
    start_date: str
    end_date: str
    content_brief: str
    target_audience: str
    tone: str
    platforms: List[str]
    frequency: Dict[str, int]  # platform -> posts per week

class ContentAgencyScheduler:
    """Content agency multi-client scheduling system"""
    
    def __init__(self, api_base_url: str, api_key: str):
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.clients: Dict[str, Client] = {}
        self.campaigns: Dict[str, Campaign] = {}
    
    def register_client(self, client: Client):
        """Register a new client"""
        self.clients[client.id] = client
        print(f"Registered client: {client.name}")
    
    def create_campaign(self, campaign: Campaign):
        """Create a new content campaign"""
        self.campaigns[campaign.id] = campaign
        print(f"Created campaign: {campaign.name} for {self.clients[campaign.client_id].name}")
    
    async def generate_campaign_schedule(self, campaign_id: str) -> List[Dict]:
        """Generate complete schedule for a campaign"""
        campaign = self.campaigns[campaign_id]
        client = self.clients[campaign.client_id]
        
        schedules = []
        
        # Generate content for each platform
        for platform in campaign.platforms:
            frequency = campaign.frequency.get(platform, 1)
            
            # Get platform-specific recommendations
            recommendations = await self._get_platform_recommendations(platform, frequency)
            
            # Generate content ideas for this platform
            content_ideas = await self._generate_content_ideas(
                campaign.content_brief,
                campaign.target_audience,
                campaign.tone,
                platform,
                frequency
            )
            
            # Create schedule entries
            for i, (idea, recommendation) in enumerate(zip(content_ideas, recommendations)):
                schedule_data = {
                    "title": f"{campaign.name} - {platform.title()} - Episode {i+1}",
                    "timezone": client.scheduling_preferences.get("timezone", "America/New_York"),
                    "items": [{
                        "content_id": f"campaign_{campaign_id}_{platform}_{i+1}",
                        "platform": platform,
                        "scheduled_time": recommendation["recommended_time"],
                        "metadata": {
                            "campaign_id": campaign_id,
                            "client_id": campaign.client_id,
                            "content_idea": idea,
                            "target_audience": campaign.target_audience,
                            "tone": campaign.tone,
                            "episode": i+1
                        }
                    }]
                }
                schedules.append(schedule_data)
        
        return schedules
    
    async def _get_platform_recommendations(self, platform: str, count: int) -> List[Dict]:
        """Get optimal timing recommendations for platform"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_base_url}/api/v1/scheduling/recommendations",
                headers=self.headers,
                params={
                    "platforms": platform,
                    "target_count": count
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                return []
    
    async def _generate_content_ideas(self, brief: str, audience: str, tone: str, platform: str, count: int) -> List[str]:
        """Generate content ideas (simplified - would integrate with AI service)"""
        # This would integrate with your AI content generation service
        ideas = []
        for i in range(count):
            if platform == "youtube":
                ideas.append(f"Comprehensive {brief} guide - Part {i+1}")
            elif platform == "tiktok":
                ideas.append(f"Quick {brief} tips #{i+1}")
            elif platform == "linkedin":
                ideas.append(f"Professional insights on {brief}")
            else:
                ideas.append(f"{brief} content piece {i+1}")
        return ideas
    
    async def execute_campaign(self, campaign_id: str) -> Dict:
        """Execute entire campaign"""
        try:
            # Generate schedule
            schedules = await self.generate_campaign_schedule(campaign_id)
            
            # Create all schedules
            created_schedules = []
            for schedule_data in schedules:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.api_base_url}/api/v1/scheduling/calendar",
                        headers=self.headers,
                        json=schedule_data
                    ) as response:
                        if response.status == 201:
                            result = await response.json()
                            created_schedules.append(result["data"]["id"])
                        else:
                            print(f"Failed to create schedule: {response.status}")
            
            return {
                "campaign_id": campaign_id,
                "total_schedules": len(created_schedules),
                "schedule_ids": created_schedules,
                "status": "executed"
            }
            
        except Exception as e:
            return {
                "campaign_id": campaign_id,
                "status": "failed",
                "error": str(e)
            }

# Example usage
async def agency_example():
    scheduler = ContentAgencyScheduler("http://localhost:8000", "agency-api-key")
    
    # Register clients
    tech_client = Client(
        id="client_001",
        name="TechStartup Inc",
        industry="technology",
        platforms=["youtube", "linkedin", "twitter"],
        scheduling_preferences={
            "timezone": "America/Los_Angeles",
            "work_days_only": True
        }
    )
    
    ecommerce_client = Client(
        id="client_002", 
        name="Fashion Brand",
        industry="fashion",
        platforms=["instagram", "tiktok", "pinterest"],
        scheduling_preferences={
            "timezone": "America/New_York",
            "work_days_only": False
        }
    )
    
    scheduler.register_client(tech_client)
    scheduler.register_client(ecommerce_client)
    
    # Create campaigns
    ai_campaign = Campaign(
        id="campaign_001",
        client_id="client_001",
        name="AI Revolution 2025",
        start_date="2025-11-01",
        end_date="2025-12-31",
        content_brief="Artificial Intelligence trends and tools",
        target_audience="tech professionals and entrepreneurs",
        tone="educational and inspiring",
        platforms=["youtube", "linkedin", "twitter"],
        frequency={"youtube": 1, "linkedin": 2, "twitter": 5}
    )
    
    fashion_campaign = Campaign(
        id="campaign_002",
        client_id="client_002",
        name="Holiday Collection Launch",
        start_date="2025-11-15",
        end_date="2026-01-15",
        content_brief="Holiday fashion trends and collection showcase",
        target_audience="fashion enthusiasts",
        tone="trendy and aspirational",
        platforms=["instagram", "tiktok", "pinterest"],
        frequency={"instagram": 3, "tiktok": 4, "pinterest": 2}
    )
    
    scheduler.create_campaign(ai_campaign)
    scheduler.create_campaign(fashion_campaign)
    
    # Execute campaigns
    ai_result = await scheduler.execute_campaign("campaign_001")
    fashion_result = await scheduler.execute_campaign("campaign_002")
    
    print("Campaign Results:")
    print(f"AI Campaign: {ai_result['status']} - {ai_result['total_schedules']} schedules")
    print(f"Fashion Campaign: {fashion_result['status']} - {fashion_result['total_schedules']} schedules")

# Run example
asyncio.run(agency_example())
```

### 2. E-commerce Brand Integration

```python
"""
Real-world example: E-commerce brand using the system for product launches
"""
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class Product:
    id: str
    name: str
    category: str
    price: float
    launch_date: str
    description: str
    target_audience: str
    hashtags: List[str]

class EcommerceContentScheduler:
    """E-commerce brand content scheduling system"""
    
    def __init__(self, api_base_url: str, api_key: str):
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_product_launch_campaign(self, product: Product) -> Dict:
        """Create comprehensive product launch content campaign"""
        
        # Define content strategy based on product category
        content_strategy = self._get_content_strategy(product.category)
        
        # Generate content ideas for each platform
        platform_content = {}
        for platform in content_strategy["platforms"]:
            platform_content[platform] = await self._generate_product_content(
                product, platform, content_strategy[platform]
            )
        
        # Create schedules for each platform
        campaign_schedules = []
        for platform, content_items in platform_content.items():
            for item in content_items:
                schedule_data = {
                    "title": f"{product.name} - {item['type']}",
                    "timezone": "America/New_York",
                    "items": [{
                        "content_id": f"product_{product.id}_{platform}_{item['type']}",
                        "platform": platform,
                        "scheduled_time": item["scheduled_time"],
                        "metadata": {
                            "product_id": product.id,
                            "product_name": product.name,
                            "content_type": item["type"],
                            "hashtags": product.hashtags,
                            "target_audience": product.target_audience,
                            "campaign_phase": item["phase"]
                        }
                    }]
                }
                campaign_schedules.append(schedule_data)
        
        # Execute all schedules
        created_schedules = await self._execute_schedule_batch(campaign_schedules)
        
        return {
            "product_id": product.id,
            "campaign_name": f"{product.name} Launch Campaign",
            "total_content_pieces": len(created_schedules),
            "platforms_covered": list(platform_content.keys()),
            "schedule_ids": created_schedules,
            "status": "launch_campaign_created"
        }
    
    def _get_content_strategy(self, category: str) -> Dict:
        """Get content strategy based on product category"""
        strategies = {
            "tech": {
                "platforms": ["youtube", "linkedin", "twitter"],
                "content_timeline": {
                    "teaser": {"days_before": 14},
                    "announcement": {"days_before": 7},
                    "demo": {"days_before": 3},
                    "launch": {"days_before": 0},
                    "follow_up": {"days_after": 7}
                }
            },
            "fashion": {
                "platforms": ["instagram", "tiktok", "pinterest"],
                "content_timeline": {
                    "behind_scenes": {"days_before": 10},
                    "sneak_peek": {"days_before": 5},
                    "launch": {"days_before": 0},
                    "styling": {"days_after": 2},
                    "customer_feature": {"days_after": 14}
                }
            },
            "home": {
                "platforms": ["pinterest", "instagram", "youtube"],
                "content_timeline": {
                    "inspiration": {"days_before": 12},
                    "how_to": {"days_before": 7},
                    "launch": {"days_before": 0},
                    "before_after": {"days_after": 5},
                    "customer_stories": {"days_after": 21}
                }
            }
        }
        
        return strategies.get(category, strategies["tech"])
    
    async def _generate_product_content(self, product: Product, platform: str, strategy: Dict) -> List[Dict]:
        """Generate content ideas for specific product and platform"""
        content_items = []
        timeline = strategy["content_timeline"]
        
        for phase, timing in timeline.items():
            if platform == "youtube":
                content_items.append({
                    "type": f"{phase}_video",
                    "scheduled_time": self._calculate_scheduled_time(product.launch_date, timing),
                    "title": f"{product.name} - {phase.replace('_', ' ').title()}",
                    "description": self._generate_description(product, phase, platform)
                })
            elif platform == "instagram":
                content_items.append({
                    "type": f"{phase}_post",
                    "scheduled_time": self._calculate_scheduled_time(product.launch_date, timing),
                    "caption": self._generate_caption(product, phase),
                    "hashtags": product.hashtags
                })
            elif platform == "linkedin":
                content_items.append({
                    "type": f"{phase}_article",
                    "scheduled_time": self._calculate_scheduled_time(product.launch_date, timing),
                    "title": f"Innovative {product.category}: {product.name}",
                    "content": self._generate_linkedin_content(product, phase)
                })
        
        return content_items
    
    def _calculate_scheduled_time(self, launch_date: str, timing: Dict) -> str:
        """Calculate actual scheduled time"""
        base_date = datetime.fromisoformat(launch_date)
        
        if "days_before" in timing:
            scheduled_date = base_date - timedelta(days=timing["days_before"])
        elif "days_after" in timing:
            scheduled_date = base_date + timedelta(days=timing["days_after"])
        else:
            scheduled_date = base_date
        
        # Set optimal time based on platform (simplified)
        if "youtube" in timing.get("content_type", ""):
            hour = 15  # 3 PM
        elif "linkedin" in timing.get("content_type", ""):
            hour = 9   # 9 AM
        else:
            hour = 12  # Noon
        
        return scheduled_date.replace(hour=hour, minute=0, second=0, tzinfo=timezone.utc).isoformat()
    
    def _generate_description(self, product: Product, phase: str, platform: str) -> str:
        """Generate content description"""
        descriptions = {
            "teaser": f"Get ready for something amazing! {product.name} is coming soon. #ComingSoon",
            "announcement": f"Introducing {product.name} - the {product.category} that will change everything!",
            "demo": f"See {product.name} in action! Here's how it works and why you'll love it.",
            "launch": f"It's here! {product.name} is now available. Order yours today!",
            "follow_up": f"Join thousands of satisfied customers who love {product.name}!"
        }
        return descriptions.get(phase, f"Discover {product.name} - your new favorite {product.category}!")
    
    def _generate_caption(self, product: Product, phase: str) -> str:
        """Generate Instagram caption"""
        base_captions = {
            "behind_scenes": f"Take a peek behind the scenes of creating {product.name}! ✨",
            "sneak_peek": f"Sneak peek at {product.name}! What do you think? 🤩",
            "launch": f"The moment we've all been waiting for! {product.name} is LIVE! 🎉",
            "styling": f"Styling inspiration with {product.name}. How would you wear it? 💫",
            "customer_feature": f"Customer feature: Look amazing in {product.name}! 📸"
        }
        return base_captions.get(phase, f"Love {product.name}! What's your favorite feature?")
    
    def _generate_linkedin_content(self, product: Product, phase: str) -> str:
        """Generate LinkedIn article content"""
        content_templates = {
            "announcement": f"""
I'm excited to announce the launch of {product.name}, a revolutionary {product.category} designed specifically for {product.target_audience}.

After months of development and testing, we're finally ready to share this innovative solution that addresses real challenges in the {product.category} space.

Key features include:
• [Feature 1]
• [Feature 2]  
• [Feature 3]

What challenges does {product.name} solve for your business?

#Innovation #{product.category.replace(' ', '')} #ProductLaunch
            """,
            "how_to": f"""
As professionals in the {product.category} space, we understand the challenges you face daily. That's why we developed {product.name} - a solution designed to streamline your workflow and increase efficiency.

Here's how {product.name} can transform your approach to {product.category}:

1. Streamlined process
2. Enhanced productivity
3. Better results

Have you experienced similar challenges? I'd love to hear about your experiences in the comments.

#Productivity #{product.category.replace(' ', '')} #BusinessSolutions
            """
        }
        return content_templates.get(phase, f"Discover how {product.name} is revolutionizing the {product.category} industry.")
    
    async def _execute_schedule_batch(self, schedules: List[Dict]) -> List[str]:
        """Execute batch schedule creation"""
        created_ids = []
        
        for schedule in schedules:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.api_base_url}/api/v1/scheduling/calendar",
                        headers=self.headers,
                        json=schedule
                    ) as response:
                        if response.status == 201:
                            result = await response.json()
                            created_ids.append(result["data"]["id"])
                        else:
                            print(f"Failed to create schedule: {response.status}")
            except Exception as e:
                print(f"Error creating schedule: {e}")
        
        return created_ids

# Example usage
async def ecommerce_example():
    scheduler = EcommerceContentScheduler("http://localhost:8000", "ecommerce-api-key")
    
    # Create product
    product = Product(
        id="prod_001",
        name="Smart Home Hub Pro",
        category="tech",
        price=299.99,
        launch_date="2025-12-01T00:00:00",
        description="AI-powered smart home hub with voice control",
        target_audience="tech-savvy homeowners",
        hashtags=["#smarthome", "#tech", "#homeautomation", "#AI"]
    )
    
    # Create launch campaign
    campaign = await scheduler.create_product_launch_campaign(product)
    
    print("E-commerce Campaign Created:")
    print(f"Product: {product.name}")
    print(f"Total Content Pieces: {campaign['total_content_pieces']}")
    print(f"Platforms: {', '.join(campaign['platforms_covered'])}")
    print(f"Schedule IDs: {campaign['schedule_ids']}")

# Run example
asyncio.run(ecommerce_example())
```

## Best Practices

### 1. Error Handling and Resilience

```python
import asyncio
import logging
from functools import wraps
from typing import Any, Callable

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retrying failed operations with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        logger.error(f"Max retries reached for {func.__name__}: {e}")
                        raise
                    
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay}s")
                    await asyncio.sleep(delay)
            
        return wrapper
    return decorator

class ResilientSchedulingClient:
    """Resilient scheduling client with proper error handling"""
    
    def __init__(self, api_base_url: str, api_key: str):
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self._rate_limit_remaining = float('inf')
        self._rate_limit_reset = 0
    
    @retry_with_backoff(max_retries=3, base_delay=2.0)
    async def create_schedule_with_retry(self, schedule_data: Dict) -> Dict:
        """Create schedule with retry and rate limiting"""
        
        # Check rate limits
        if self._rate_limit_remaining <= 0:
            wait_time = max(0, self._rate_limit_reset - time.time())
            if wait_time > 0:
                logger.info(f"Rate limit hit, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/api/v1/scheduling/calendar",
                    headers=self.headers,
                    json=schedule_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    # Update rate limit info
                    if 'x-ratelimit-remaining' in response.headers:
                        self._rate_limit_remaining = int(response.headers['x-ratelimit-remaining'])
                    if 'x-ratelimit-reset' in response.headers:
                        self._rate_limit_reset = int(response.headers['x-ratelimit-reset'])
                    
                    if response.status == 429:  # Rate limited
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"Rate limited, retrying after {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        raise Exception("Rate limited")
                    
                    if response.status >= 400:
                        error_text = await response.text()
                        logger.error(f"API error {response.status}: {error_text}")
                        raise Exception(f"API Error {response.status}: {error_text}")
                    
                    return await response.json()
        
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise
    
    async def batch_create_schedules(self, schedules: List[Dict], batch_size: int = 5) -> List[Dict]:
        """Create schedules in batches with concurrency control"""
        results = []
        
        # Process in batches to avoid overwhelming the API
        for i in range(0, len(schedules), batch_size):
            batch = schedules[i:i + batch_size]
            batch_tasks = []
            
            # Create concurrent tasks for the batch
            for schedule in batch:
                task = self.create_schedule_with_retry(schedule)
                batch_tasks.append(task)
            
            # Execute batch with concurrency control
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Schedule creation failed: {result}")
                    results.append({"error": str(result)})
                else:
                    results.append(result)
            
            # Add delay between batches
            if i + batch_size < len(schedules):
                await asyncio.sleep(1)
        
        return results
```

### 2. Data Validation and Sanitization

```python
from typing import List, Dict, Optional, Union
from datetime import datetime
import re
import html

def validate_schedule_data(data: Dict) -> Dict:
    """Validate and sanitize schedule data"""
    
    # Required fields validation
    required_fields = ['title', 'items']
    for field in required_fields:
        if field not in data or not data[field]:
            raise ValueError(f"Missing required field: {field}")
    
    # Title validation
    title = data['title'].strip()
    if len(title) > 100:
        raise ValueError("Title too long (max 100 characters)")
    if len(title) < 3:
        raise ValueError("Title too short (min 3 characters)")
    
    # Items validation
    if not isinstance(data['items'], list) or len(data['items']) == 0:
        raise ValueError("Items must be a non-empty list")
    
    for i, item in enumerate(data['items']):
        validate_schedule_item(item, i)
    
    # Sanitize data
    sanitized = {
        'title': html.escape(title),
        'timezone': data.get('timezone', 'America/New_York'),
        'items': [sanitize_schedule_item(item) for item in data['items']]
    }
    
    return sanitized

def validate_schedule_item(item: Dict, index: int) -> None:
    """Validate individual schedule item"""
    
    # Required fields
    if 'content_id' not in item or not item['content_id']:
        raise ValueError(f"Item {index}: Missing content_id")
    
    if 'platform' not in item or not item['platform']:
        raise ValueError(f"Item {index}: Missing platform")
    
    # Platform validation
    valid_platforms = ['youtube', 'tiktok', 'instagram', 'linkedin', 'twitter', 'facebook']
    if item['platform'] not in valid_platforms:
        raise ValueError(f"Item {index}: Invalid platform '{item['platform']}'")
    
    # Scheduled time validation
    if 'scheduled_time' not in item or not item['scheduled_time']:
        raise ValueError(f"Item {index}: Missing scheduled_time")
    
    try:
        # Validate datetime format
        datetime.fromisoformat(item['scheduled_time'].replace('Z', '+00:00'))
    except ValueError:
        raise ValueError(f"Item {index}: Invalid datetime format")

def sanitize_schedule_item(item: Dict) -> Dict:
    """Sanitize schedule item data"""
    
    sanitized = {
        'content_id': item['content_id'].strip(),
        'platform': item['platform'].strip().lower(),
        'scheduled_time': item['scheduled_time'],
        'metadata': item.get('metadata', {})
    }
    
    # Sanitize metadata if present
    if isinstance(sanitized['metadata'], dict):
        for key, value in sanitized['metadata'].items():
            if isinstance(value, str):
                sanitized['metadata'][key] = value.strip()
    
    return sanitized

def validate_google_sheets_data(data: List[List[str]]) -> List[Dict]:
    """Validate Google Sheets data format"""
    
    if not data or len(data) < 2:
        raise ValueError("Data must have at least 2 rows (header + data)")
    
    headers = data[0]
    rows = data[1:]
    
    # Define required columns
    required_columns = ['title', 'content', 'platform', 'scheduled_time']
    
    # Validate headers
    for col in required_columns:
        if col not in headers:
            raise ValueError(f"Missing required column: {col}")
    
    # Validate data rows
    validated_rows = []
    for i, row in enumerate(rows, 1):
        if len(row) < len(headers):
            # Pad row with empty strings if too short
            row.extend([''] * (len(headers) - len(row)))
        
        validated_row = {}
        for j, header in enumerate(headers):
            validated_row[header] = row[j].strip() if j < len(row) else ''
        
        # Additional validation for key fields
        if validated_row.get('title') and len(validated_row['title']) > 200:
            validated_row['title'] = validated_row['title'][:200]
        
        validated_rows.append(validated_row)
    
    return validated_rows
```

### 3. Performance Optimization

```python
import asyncio
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
import asyncpg
import redis
import json

class OptimizedSchedulingService:
    """High-performance scheduling service with caching and connection pooling"""
    
    def __init__(self, database_url: str, redis_url: str, api_base_url: str, api_key: str):
        self.database_url = database_url
        self.redis_client = redis.from_url(redis_url)
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Connection pools
        self.db_pool = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Cache settings
        self.cache_ttl = 300  # 5 minutes
        self.recommendation_cache_key = "recommendations:{platforms}:{count}"
    
    async def initialize(self):
        """Initialize connection pools"""
        self.db_pool = await asyncpg.create_pool(
            self.database_url,
            min_size=10,
            max_size=20,
            command_timeout=60
        )
    
    async def get_cached_recommendations(self, platforms: List[str], count: int) -> List[Dict]:
        """Get recommendations with Redis caching"""
        
        # Generate cache key
        cache_key = self.recommendation_cache_key.format(
            platforms=",".join(sorted(platforms)),
            count=count
        )
        
        # Try to get from cache first
        cached_data = self.redis_client.get(cache_key)
        if cached_data:
            try:
                return json.loads(cached_data)
            except json.JSONDecodeError:
                pass  # Invalid cache data, proceed to fetch
        
        # Fetch from API if not cached
        recommendations = await self._fetch_recommendations(platforms, count)
        
        # Cache the results
        if recommendations:
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(recommendations)
            )
        
        return recommendations
    
    async def _fetch_recommendations(self, platforms: List[str], count: int) -> List[Dict]:
        """Fetch recommendations from API"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_base_url}/api/v1/scheduling/recommendations",
                headers=self.headers,
                params={
                    "platforms": ",".join(platforms),
                    "target_count": count
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                else:
                    raise Exception(f"Failed to fetch recommendations: {response.status}")
    
    async def create_schedules_with_transaction(self, schedules: List[Dict]) -> List[str]:
        """Create schedules using database transaction for consistency"""
        
        created_ids = []
        
        async with self.db_pool.acquire() as connection:
            async with connection.transaction():
                try:
                    # Create schedules in the database first
                    for schedule_data in schedules:
                        schedule_id = await self._create_schedule_in_db(connection, schedule_data)
                        created_ids.append(schedule_id)
                    
                    # Then sync with external API (non-blocking)
                    api_tasks = [
                        self._sync_schedule_with_api(schedule_data, schedule_id)
                        for schedule_data, schedule_id in zip(schedules, created_ids)
                    ]
                    
                    # Run API syncs in background
                    asyncio.create_task(asyncio.gather(*api_tasks, return_exceptions=True))
                    
                    return created_ids
                
                except Exception as e:
                    # Transaction will rollback automatically
                    logger.error(f"Transaction failed: {e}")
                    raise
    
    async def _create_schedule_in_db(self, connection, schedule_data: Dict) -> str:
        """Create schedule record in database"""
        
        schedule_id = f"sched_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        await connection.execute("""
            INSERT INTO content_calendar (id, title, timezone, status, created_at)
            VALUES ($1, $2, $3, $4, NOW())
        """, schedule_id, schedule_data['title'], schedule_data.get('timezone', 'UTC'), 'pending')
        
        # Insert schedule items
        for item in schedule_data['items']:
            await connection.execute("""
                INSERT INTO content_schedule_items (
                    id, calendar_id, content_id, platform, scheduled_time, 
                    metadata, status, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, NOW()
                )
            """, f"item_{schedule_id}_{item['content_id']}", schedule_id,
               item['content_id'], item['platform'], item['scheduled_time'],
               json.dumps(item.get('metadata', {})), 'pending')
        
        return schedule_id
    
    async def _sync_schedule_with_api(self, schedule_data: Dict, schedule_id: str):
        """Sync schedule with external API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/api/v1/scheduling/calendar",
                    headers=self.headers,
                    json=schedule_data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 201:
                        logger.info(f"Successfully synced schedule {schedule_id} with API")
                    else:
                        logger.error(f"Failed to sync schedule {schedule_id} with API: {response.status}")
        except Exception as e:
            logger.error(f"API sync error for schedule {schedule_id}: {e}")
    
    async def get_performance_metrics(self, schedule_ids: List[str]) -> Dict:
        """Get performance metrics for schedules"""
        
        metrics = {}
        
        # Get metrics from database
        async with self.db_pool.acquire() as connection:
            rows = await connection.fetch("""
                SELECT 
                    calendar_id,
                    COUNT(*) as total_items,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_items,
                    AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_processing_time
                FROM content_schedule_items
                WHERE calendar_id = ANY($1)
                GROUP BY calendar_id
            """, schedule_ids)
            
            for row in rows:
                metrics[row['calendar_id']] = {
                    'total_items': row['total_items'],
                    'completed_items': row['completed_items'],
                    'completion_rate': row['completed_items'] / row['total_items'],
                    'avg_processing_time': row['avg_processing_time']
                }
        
        return metrics
    
    async def cleanup_old_schedules(self, days_old: int = 30) -> int:
        """Cleanup old completed schedules"""
        
        async with self.db_pool.acquire() as connection:
            result = await connection.execute("""
                DELETE FROM content_schedule_items 
                WHERE calendar_id IN (
                    SELECT id FROM content_calendar 
                    WHERE status = 'completed' 
                    AND created_at < NOW() - INTERVAL '%s days'
                )
            """, days_old)
            
            return int(result.split()[-1])  # Return number of deleted rows
    
    async def close(self):
        """Clean up resources"""
        if self.db_pool:
            await self.db_pool.close()
        self.executor.shutdown(wait=True)
```

## Troubleshooting

### Common Issues and Solutions

1. **Authentication Errors**
   - Verify API key is valid and not expired
   - Check CORS settings for frontend integration
   - Ensure proper OAuth configuration for Google Sheets

2. **Rate Limiting**
   - Implement exponential backoff
   - Use connection pooling
   - Cache frequently accessed data

3. **Data Format Issues**
   - Validate all input data before processing
   - Use proper timezone handling
   - Sanitize user inputs to prevent injection attacks

4. **Network Connectivity**
   - Implement retry mechanisms
   - Use proper timeout settings
   - Monitor network health

### Debugging Tools

```python
import logging
import asyncio
from functools import wraps

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def debug_api_calls(func):
    """Decorator to log API calls"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"{func.__name__} succeeded: {result}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}")
            raise
    return wrapper

class APIDebugger:
    """API call debugger for troubleshooting"""
    
    def __init__(self):
        self.call_log = []
    
    def log_call(self, method: str, url: str, response_time: float, status_code: int):
        """Log API call details"""
        call_info = {
            'timestamp': datetime.now(),
            'method': method,
            'url': url,
            'response_time': response_time,
            'status_code': status_code
        }
        self.call_log.append(call_info)
        
        # Alert on slow calls or errors
        if response_time > 5.0:
            logger.warning(f"Slow API call detected: {url} took {response_time:.2f}s")
        
        if status_code >= 400:
            logger.error(f"API error: {url} returned {status_code}")
    
    def get_stats(self) -> Dict:
        """Get API call statistics"""
        if not self.call_log:
            return {}
        
        total_calls = len(self.call_log)
        avg_response_time = sum(call['response_time'] for call in self.call_log) / total_calls
        error_rate = sum(1 for call in self.call_log if call['status_code'] >= 400) / total_calls
        
        return {
            'total_calls': total_calls,
            'avg_response_time': avg_response_time,
            'error_rate': error_rate,
            'recent_calls': self.call_log[-10:]  # Last 10 calls
        }
```

This comprehensive integration guide provides practical examples for integrating with the AI Content Automation System across multiple platforms and use cases. Each example includes proper error handling, performance optimization, and best practices for production use.
