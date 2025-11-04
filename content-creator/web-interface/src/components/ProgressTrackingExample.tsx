import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Play, 
  Plus, 
  AlertCircle, 
  CheckCircle, 
  Clock, 
  Loader2,
  ArrowRight,
  Zap,
  Activity
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import ProgressDashboard from '../components/ProgressDashboard';
import useWebSocket from '../hooks/useWebSocket';
import apiClient from '../lib/api';

/**
 * Complete example showing:
 * 1. Creating a bulk job
 * 2. Monitoring progress in real-time
 * 3. Handling job completion
 * 4. Viewing detailed progress dashboard
 */
export default function ProgressTrackingExample() {
  const navigate = useNavigate();
  const [currentJob, setCurrentJob] = useState<any>(null);
  const [showProgressDashboard, setShowProgressDashboard] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [wsStatus, setWsStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');

  // WebSocket connection for real-time updates
  const {
    connected,
    connecting,
    error: wsError,
    connect,
    disconnect,
  } = useWebSocket({
    jobId: currentJob?.id,
    token: 'demo-token', // In production, get from auth context
    onProgress: (progress) => {
      console.log('Real-time progress update:', progress);
      setCurrentJob(prev => prev ? { ...prev, progress } : null);
    },
    onStateChange: (stateChange) => {
      console.log('Job state changed:', stateChange);
      setCurrentJob(prev => prev ? { ...prev, state: stateChange.new_state } : null);
    },
    onJobCompleted: (data) => {
      console.log('Job completed!', data);
      // You could trigger a notification here
    },
    onJobFailed: (data) => {
      console.error('Job failed!', data);
      setError('Job processing failed. Please check the logs.');
    },
  });

  // Update WebSocket status
  useEffect(() => {
    if (connecting) setWsStatus('connecting');
    else if (connected) setWsStatus('connected');
    else setWsStatus('disconnected');
  }, [connected, connecting]);

  // Example: Create a bulk job with Google Sheets integration
  const createExampleJob = async () => {
    try {
      setCreating(true);
      setError(null);

      const jobData = {
        title: 'AI Content Generation Campaign',
        priority: 'normal' as const,
        processing_deadline_ms: 3600000, // 1 hour
        input_source: {
          type: 'sheet' as const,
          sheet_id: '1A2B3C4D5E6F7G8H9I0J', // Example sheet ID
          range: 'A1:Z100',
        },
        output: {
          format: 'mp4' as const,
          video_codec: 'h264' as const,
          audio_codec: 'aac' as const,
          resolution: '1080p' as const,
          output_bucket: 'content-outputs',
        },
        template: {
          template_id: 'default_video_template',
          overrides: {
            style: 'modern',
            voice: 'professional',
            music_background: 'upbeat'
          }
        },
        idempotency_key: crypto.randomUUID(),
      };

      const response = await apiClient.createBulkJob(jobData);
      const newJob = response.data;
      
      setCurrentJob(newJob);
      
      // Automatically connect to WebSocket for real-time updates
      setTimeout(() => {
        connect();
      }, 1000);
      
    } catch (err) {
      console.error('Failed to create job:', err);
      setError(err instanceof Error ? err.message : 'Failed to create job');
    } finally {
      setCreating(false);
    }
  };

  // Example: Simulate job creation and progress monitoring
  const simulateJobCreation = () => {
    const mockJob = {
      id: 'job_demo_001',
      title: 'Demo Content Generation',
      state: 'pending',
      percent_complete: 0,
      items_total: 10,
      items_completed: 0,
      items_failed: 0,
      items_pending: 10,
      created_at: new Date().toISOString(),
      processing_deadline_ms: 1800000,
      sheet_source: {
        sheet_id: 'demo_sheet_123',
        range: 'A1:C10'
      }
    };
    
    setCurrentJob(mockJob);
    
    // Simulate connection
    setTimeout(() => {
      connect();
    }, 500);
    
    // Simulate job progression
    setTimeout(() => {
      setCurrentJob(prev => prev ? { ...prev, state: 'running' } : null);
    }, 2000);
    
    // Simulate progress updates
    let progress = 0;
    const progressInterval = setInterval(() => {
      progress += Math.random() * 15;
      if (progress > 100) progress = 100;
      
      setCurrentJob(prev => prev ? {
        ...prev,
        percent_complete: progress,
        items_completed: Math.floor((progress / 100) * prev.items_total),
        items_pending: prev.items_total - Math.floor((progress / 100) * prev.items_total)
      } : null);
      
      if (progress >= 100) {
        clearInterval(progressInterval);
        setCurrentJob(prev => prev ? { ...prev, state: 'completed' } : null);
      }
    }, 1000);
  };

  const handleViewProgress = () => {
    if (currentJob) {
      setShowProgressDashboard(true);
    }
  };

  const getStatusIcon = () => {
    switch (wsStatus) {
      case 'connected':
        return <Activity className="w-4 h-4 text-green-500" />;
      case 'connecting':
        return <Loader2 className="w-4 h-4 text-yellow-500 animate-spin" />;
      default:
        return <AlertCircle className="w-4 h-4 text-red-500" />;
    }
  };

  const getStatusColor = () => {
    switch (wsStatus) {
      case 'connected':
        return 'text-green-600 dark:text-green-400';
      case 'connecting':
        return 'text-yellow-600 dark:text-yellow-400';
      default:
        return 'text-red-600 dark:text-red-400';
    }
  };

  if (showProgressDashboard && currentJob) {
    return (
      <ProgressDashboard
        jobId={currentJob.id}
        token="demo-token"
        jobData={{
          id: currentJob.id,
          title: currentJob.title,
          state: currentJob.state,
          created_at: currentJob.created_at,
          processing_deadline_ms: currentJob.processing_deadline_ms,
          sheet_source: currentJob.sheet_source,
        }}
        onJobAction={(action, jobId) => {
          console.log(`Job action: ${action} for job ${jobId}`);
          // In a real app, you would call the API here
        }}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
          Progress Tracking Dashboard
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
          Real-time monitoring and control of bulk content generation jobs with 
          WebSocket-based live updates and comprehensive progress tracking.
        </p>
      </div>

      {/* Features Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Zap className="w-5 h-5 text-blue-500" />
              <span>Real-time Updates</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 dark:text-gray-400">
              WebSocket-powered live progress updates with automatic reconnection 
              and connection health monitoring.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="w-5 h-5 text-green-500" />
              <span>Comprehensive Monitoring</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 dark:text-gray-400">
              Job-level and item-level progress tracking with ETA estimation, 
              performance metrics, and error handling.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Play className="w-5 h-5 text-purple-500" />
              <span>Job Control</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 dark:text-gray-400">
              Pause, resume, cancel, and retry job operations with instant 
              state feedback and user-friendly controls.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Demo Section */}
      <Card>
        <CardHeader>
          <CardTitle>Interactive Demo</CardTitle>
          <CardDescription>
            Try the progress tracking system with a simulated job or create a real one
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* WebSocket Status */}
          <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="flex items-center space-x-3">
              {getStatusIcon()}
              <div>
                <p className="font-medium text-gray-900 dark:text-white">
                  WebSocket Status: 
                  <span className={`ml-2 ${getStatusColor()}`}>
                    {wsStatus.charAt(0).toUpperCase() + wsStatus.slice(1)}
                  </span>
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {currentJob ? `Monitoring job: ${currentJob.id}` : 'No active job'}
                </p>
              </div>
            </div>
            
            {currentJob && (
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={connected ? disconnect : connect}
                  disabled={connecting}
                >
                  {connected ? 'Disconnect' : 'Connect'}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleViewProgress}
                >
                  <ArrowRight className="w-4 h-4 mr-1" />
                  View Dashboard
                </Button>
              </div>
            )}
          </div>

          {/* Current Job Progress */}
          {currentJob && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {currentJob.title}
                </h3>
                <Badge 
                  variant="outline" 
                  className={
                    currentJob.state === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                    currentJob.state === 'running' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' :
                    currentJob.state === 'failed' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                    'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
                  }
                >
                  {currentJob.state}
                </Badge>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Progress</span>
                  <span>{currentJob.percent_complete.toFixed(1)}%</span>
                </div>
                <Progress value={currentJob.percent_complete} className="w-full" />
              </div>

              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="text-center">
                  <p className="font-semibold text-green-600 dark:text-green-400">
                    {currentJob.items_completed}
                  </p>
                  <p className="text-gray-600 dark:text-gray-400">Completed</p>
                </div>
                <div className="text-center">
                  <p className="font-semibold text-gray-600 dark:text-gray-400">
                    {currentJob.items_pending}
                  </p>
                  <p className="text-gray-600 dark:text-gray-400">Pending</p>
                </div>
                <div className="text-center">
                  <p className="font-semibold text-red-600 dark:text-red-400">
                    {currentJob.items_failed}
                  </p>
                  <p className="text-gray-600 dark:text-gray-400">Failed</p>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-4">
            <Button
              onClick={simulateJobCreation}
              disabled={!!currentJob}
              className="flex items-center"
            >
              <Play className="w-4 h-4 mr-2" />
              Start Demo Job
            </Button>

            <Button
              onClick={createExampleJob}
              disabled={creating || !!currentJob}
              variant="outline"
              className="flex items-center"
            >
              {creating ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Plus className="w-4 h-4 mr-2" />
              )}
              Create Real Job
            </Button>

            {currentJob && (
              <Button
                onClick={() => setCurrentJob(null)}
                variant="ghost"
                className="text-red-600 hover:text-red-700"
              >
                Reset Demo
              </Button>
            )}
          </div>

          {/* Error Display */}
          {(error || wsError) && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {error || wsError}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Code Examples */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Start Examples</CardTitle>
          <CardDescription>
            Integration examples for your applications
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">1. Basic Progress Dashboard</h4>
              <pre className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg text-sm overflow-x-auto">
{`<ProgressDashboard
  jobId="job_123"
  token="your-auth-token"
  jobData={jobData}
  onJobAction={handleJobAction}
/>`}
              </pre>
            </div>

            <div>
              <h4 className="font-semibold mb-2">2. WebSocket Hook Usage</h4>
              <pre className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg text-sm overflow-x-auto">
{`const { connected, connect } = useWebSocket({
  jobId: "job_123",
  onProgress: (progress) => updateUI(progress),
  onJobCompleted: (data) => handleCompletion(data)
});`}
              </pre>
            </div>

            <div>
              <h4 className="font-semibold mb-2">3. Create Bulk Job</h4>
              <pre className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg text-sm overflow-x-auto">
{`const job = await apiClient.createBulkJob({
  title: "Content Campaign",
  input_source: { type: "sheet", sheet_id: "...", range: "A1:Z100" },
  output: { format: "mp4", resolution: "1080p", ... },
  template: { template_id: "default" }
});`}
              </pre>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}