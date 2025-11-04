import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Play, Pause, RotateCcw, Settings, Download, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import ProgressDashboard from '../components/ProgressDashboard';
import apiClient from '../lib/api';

interface JobData {
  id: string;
  title?: string;
  state: string;
  created_at: string;
  processing_deadline_ms?: number;
  sheet_source?: {
    sheet_id: string;
    range: string;
  };
  percent_complete: number;
  items_total: number;
  items_completed: number;
  items_failed: number;
  items_pending: number;
}

export default function BulkJobProgress() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [jobData, setJobData] = useState<JobData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authToken] = useState(() => {
    // In a real app, get this from auth context or storage
    return localStorage.getItem('auth_token') || 'demo-token';
  });

  useEffect(() => {
    if (jobId) {
      loadJobData();
      // Set up periodic refresh
      const interval = setInterval(loadJobData, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [jobId]);

  const loadJobData = async () => {
    if (!jobId) return;

    try {
      setError(null);
      const response = await apiClient.getBulkJob(jobId);
      const job = response.data;
      
      setJobData({
        id: job.id,
        title: job.title || `Bulk Job ${job.id}`,
        state: job.state,
        created_at: job.created_at,
        processing_deadline_ms: job.processing_deadline_ms,
        sheet_source: job.sheet_source,
        percent_complete: job.percent_complete,
        items_total: job.items_total,
        items_completed: job.items_completed,
        items_failed: job.items_failed,
        items_pending: job.items_pending,
      });
    } catch (err) {
      console.error('Failed to load job data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load job data');
    } finally {
      setLoading(false);
    }
  };

  const handleJobAction = async (action: 'pause' | 'resume' | 'cancel' | 'retry', jobId: string) => {
    try {
      switch (action) {
        case 'pause':
          // await apiClient.pauseJob(jobId);
          console.log('Pausing job:', jobId);
          break;
        case 'resume':
          // await apiClient.resumeJob(jobId);
          console.log('Resuming job:', jobId);
          break;
        case 'cancel':
          // await apiClient.cancelJob(jobId);
          console.log('Canceling job:', jobId);
          break;
        case 'retry':
          // await apiClient.retryJob(jobId);
          console.log('Retrying job:', jobId);
          break;
      }
      // Reload job data after action
      await loadJobData();
    } catch (err) {
      console.error(`Failed to ${action} job:`, err);
      setError(err instanceof Error ? err.message : `Failed to ${action} job`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !jobData) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <Button
            variant="outline"
            onClick={() => navigate('/projects')}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Projects
          </Button>
        </div>
        
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error || 'Job not found'}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <Button
          variant="outline"
          onClick={() => navigate('/projects')}
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Projects
        </Button>
      </div>

      <ProgressDashboard
        jobId={jobId!}
        token={authToken}
        jobData={jobData}
        onJobAction={handleJobAction}
      />
    </div>
  );
}