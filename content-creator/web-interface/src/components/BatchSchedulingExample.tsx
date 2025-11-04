/**
 * Batch Scheduling Integration Example
 * 
 * This file demonstrates how to integrate the new BatchScheduler and SchedulingProgress
 * components with the existing bulk job system and Google Sheets.
 */

import React, { useState } from 'react';
import BatchScheduler from './BatchScheduler';
import SchedulingProgress from './SchedulingProgress';
import BulkJobCard from './BulkJobCard';
import { Button } from './ui/button';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Plus, Calendar, Settings, BarChart3 } from 'lucide-react';

// Example parent component that integrates both scheduling components
export default function BatchSchedulingExample() {
  const [showScheduler, setShowScheduler] = useState(false);
  const [showProgress, setShowProgress] = useState(true);
  const [recentJobs, setRecentJobs] = useState<any[]>([]);
  const [selectedJob, setSelectedJob] = useState<any>(null);

  const handleJobScheduled = (job: any) => {
    console.log('Job scheduled successfully:', job);
    setRecentJobs(prev => [job, ...prev]);
    setShowScheduler(false);
    
    // Optional: Show success notification
    showNotification('Batch job scheduled successfully!', 'success');
  };

  const handleViewJobDetails = (job: any) => {
    setSelectedJob(job);
    console.log('Viewing job details:', job);
  };

  const showNotification = (message: string, type: 'success' | 'error' | 'info') => {
    // In a real app, you would use a toast library like react-hot-toast
    console.log(`[${type.toUpperCase()}] ${message}`);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Batch Content Scheduling
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              Manage and monitor bulk content generation with intelligent scheduling
            </p>
          </div>
          
          <div className="flex gap-3">
            <Button
              onClick={() => setShowScheduler(true)}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Schedule Batch Job
            </Button>
            
            <Button
              variant="outline"
              onClick={() => setShowProgress(!showProgress)}
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              {showProgress ? 'Hide Progress' : 'Show Progress'}
            </Button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Scheduled Jobs</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{recentJobs.length}</div>
              <p className="text-xs text-muted-foreground">
                +2 from last week
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Processing</CardTitle>
              <Settings className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {recentJobs.filter(job => ['pending', 'running', 'completing'].includes(job.state)).length}
              </div>
              <p className="text-xs text-muted-foreground">
                Currently processing
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">94.2%</div>
              <p className="text-xs text-muted-foreground">
                Last 30 days
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Recent Jobs */}
        {recentJobs.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Recent Scheduled Jobs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentJobs.slice(0, 3).map((job) => (
                  <div key={job.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <h3 className="font-medium">{job.title || `Job ${job.id.slice(0, 8)}`}</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Scheduled for {job.scheduling?.mode || 'immediate'} processing
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleViewJobDetails(job)}
                      >
                        View Details
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Scheduling Progress Dashboard */}
        {showProgress && (
          <Card>
            <CardHeader>
              <CardTitle>Batch Job Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <SchedulingProgress
                onViewDetails={handleViewJobDetails}
                refreshInterval={5000} // Refresh every 5 seconds for active jobs
              />
            </CardContent>
          </Card>
        )}

        {/* Usage Examples */}
        <Card>
          <CardHeader>
            <CardTitle>Integration Examples</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-3">1. Basic Scheduling</h3>
              <pre className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg text-sm overflow-x-auto">
{`import BatchScheduler from './BatchScheduler';
import SchedulingProgress from './SchedulingProgress';

function MyComponent() {
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
        refreshInterval={10000}
      />
    </>
  );
}`}
              </pre>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-3">2. Advanced Configuration</h3>
              <pre className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg text-sm overflow-x-auto">
{`// Configure smart scheduling with optimization
const schedulingConfig = {
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
    }
  ]
};

// The BatchScheduler component will handle this automatically
// when users select the appropriate options in the UI`}
              </pre>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-3">3. Google Sheets Integration</h3>
              <pre className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg text-sm overflow-x-auto">
{`// Google Sheets is integrated automatically through the API
// Users just need to provide:
// 1. Sheet ID (from Google Sheets URL)
// 2. Data range (e.g., "A1:Z1000")
// 3. Appropriate permissions

// The system will:
// - Validate sheet connectivity
// - Preview data structure
// - Configure optimal scheduling based on content
// - Monitor progress with real-time updates`}
              </pre>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-3">4. Custom Scheduling Rules</h3>
              <pre className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg text-sm overflow-x-auto">
{`// Example scheduling rule for content-based optimization
const contentRule = {
  id: 'complex-content-priority',
  name: 'Process Complex Content First',
  type: 'content_based',
  enabled: true,
  settings: {
    complexity_threshold: 'high',
    priority_boost: true,
    max_concurrent_complex: 2
  }
};

// This rule will be applied automatically when
// users configure content-based scheduling`}
              </pre>
            </div>
          </CardContent>
        </Card>

        {/* Batch Scheduler Modal */}
        <BatchScheduler
          isOpen={showScheduler}
          onClose={() => setShowScheduler(false)}
          onJobScheduled={handleJobScheduled}
        />

        {/* Job Details Modal (placeholder) */}
        {selectedJob && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-900 rounded-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden">
              <div className="flex items-center justify-between p-6 border-b">
                <h2 className="text-xl font-bold">Job Details</h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedJob(null)}
                >
                  Close
                </Button>
              </div>
              <div className="p-6">
                <pre className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg text-sm overflow-auto">
                  {JSON.stringify(selectedJob, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Additional Integration Patterns
 */

// Pattern 1: Integration with existing project management
export const integrateWithProjectManagement = async (projectId: string) => {
  // Example: Auto-schedule content based on project milestones
  const batchJob = await apiClient.createBulkJob({
    title: `Project ${projectId} Content Batch`,
    priority: 'high',
    scheduling: {
      mode: 'smart',
      optimization_level: 'quality',
      max_concurrent_jobs: 3,
    },
    // ... other config
  });

  return batchJob;
};

// Pattern 2: Automated scheduling based on content library
export const scheduleFromContentLibrary = async (contentIds: string[]) => {
  // Example: Schedule content generation based on library analysis
  const optimization = await apiClient.optimizeBatchScheduling({
    content_ids: contentIds,
    constraints: {
      deadline: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24 hours
      priority: 'normal'
    }
  });

  return optimization;
};

// Pattern 3: Integration with Google Calendar
export const scheduleWithCalendarIntegration = async (eventId: string) => {
  // Example: Sync with external calendar for content publishing
  const calendarEvent = await apiClient.getCalendarEvent(eventId);
  
  const scheduledJob = await apiClient.createBulkJob({
    title: `Scheduled for ${calendarEvent.title}`,
    scheduling: {
      mode: 'time_based',
      schedule_start_time: calendarEvent.start_time,
      optimization_level: 'speed'
    },
    // ... other config
  });

  return scheduledJob;
};

// Pattern 4: Bulk scheduling with template presets
export const createSchedulingTemplate = (templateName: string, config: any) => {
  // Store reusable scheduling configurations
  localStorage.setItem(`scheduling-template-${templateName}`, JSON.stringify(config));
};

export const loadSchedulingTemplate = (templateName: string) => {
  const stored = localStorage.getItem(`scheduling-template-${templateName}`);
  return stored ? JSON.parse(stored) : null;
};

export { BatchScheduler, SchedulingProgress };
