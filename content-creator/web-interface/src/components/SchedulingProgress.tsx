import { useState, useEffect } from 'react';
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  Pause, 
  Play, 
  Trash2, 
  Eye,
  AlertCircle,
  Download,
  Calendar,
  BarChart3,
  TrendingUp,
  Zap,
  RefreshCw,
  FileText,
  Activity,
  Timer,
  Target,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Filter,
  SortAsc,
  SortDesc,
  Grid,
  List
} from 'lucide-react';
import apiClient from '../lib/api';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Progress } from './ui/progress';

interface BulkJob {
  id: string;
  tenant_id: string;
  state: 'pending' | 'running' | 'pausing' | 'paused' | 'completing' | 'completed' | 'canceling' | 'canceled' | 'failed';
  percent_complete: number;
  items_total: number;
  items_completed: number;
  items_failed: number;
  items_skipped: number;
  items_canceled: number;
  items_pending: number;
  time_to_start_ms: number | null;
  time_processing_ms: number;
  average_duration_ms_per_item: number | null;
  eta_ms: number | null;
  rate_limited: boolean;
  processing_deadline_ms: number;
  callback_url: string | null;
  created_at: string;
  updated_at: string;
  idempotency_key: string | null;
  scheduling?: {
    mode: string;
    optimization_level: string;
    max_concurrent_jobs: number;
    priority_queue: boolean;
  };
  sheet_source?: {
    sheet_id: string;
    range: string;
    connected_at: string;
  } | null;
  artifacts?: Array<{
    type: string;
    content_type: string;
    size: number;
    url: string;
  }>;
}

interface SchedulingProgressProps {
  onViewDetails?: (job: BulkJob) => void;
  refreshInterval?: number;
}

export default function SchedulingProgress({ onViewDetails, refreshInterval = 10000 }: SchedulingProgressProps) {
  const [jobs, setJobs] = useState<BulkJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('active');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState<'created_at' | 'updated_at' | 'percent_complete'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [expandedJobs, setExpandedJobs] = useState<Set<string>>(new Set());

  // Filter jobs based on active tab
  const filteredJobs = jobs.filter(job => {
    switch (activeTab) {
      case 'active':
        return ['pending', 'running', 'pausing', 'paused', 'completing'].includes(job.state);
      case 'completed':
        return job.state === 'completed';
      case 'failed':
        return job.state === 'failed' || job.state === 'canceled';
      default:
        return true;
    }
  });

  // Sort jobs
  const sortedJobs = [...filteredJobs].sort((a, b) => {
    let aValue = a[sortBy];
    let bValue = b[sortBy];
    
    if (sortBy === 'created_at' || sortBy === 'updated_at') {
      aValue = new Date(aValue as string).getTime();
      bValue = new Date(bValue as string).getTime();
    }
    
    if (sortOrder === 'asc') {
      return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
    } else {
      return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
    }
  });

  useEffect(() => {
    loadJobs();
    
    // Set up auto-refresh for active jobs
    const interval = setInterval(() => {
      if (jobs.some(job => ['pending', 'running', 'pausing', 'paused', 'completing'].includes(job.state))) {
        loadJobs();
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  const loadJobs = async () => {
    try {
      setLoading(true);
      const response = await apiClient.listBulkJobs({
        page_size: 50,
        sort: sortBy,
        order: sortOrder,
      });
      
      if (response.data && Array.isArray(response.data.jobs)) {
        setJobs(response.data.jobs);
        setError(null);
      }
    } catch (err) {
      console.error('Failed to load jobs:', err);
      setError('Failed to load batch jobs. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleJobAction = async (jobId: string, action: 'pause' | 'resume' | 'cancel') => {
    try {
      switch (action) {
        case 'pause':
          // Implementation would depend on API endpoint
          console.log('Pause job:', jobId);
          break;
        case 'resume':
          console.log('Resume job:', jobId);
          break;
        case 'cancel':
          console.log('Cancel job:', jobId);
          break;
      }
      
      // Refresh jobs after action
      await loadJobs();
    } catch (err) {
      console.error(`Failed to ${action} job:`, err);
      setError(`Failed to ${action} job. Please try again.`);
    }
  };

  const toggleJobExpansion = (jobId: string) => {
    setExpandedJobs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(jobId)) {
        newSet.delete(jobId);
      } else {
        newSet.add(jobId);
      }
      return newSet;
    });
  };

  const getStateColor = (state: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
      running: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
      pausing: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
      paused: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
      completing: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
      completed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      canceling: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
      canceled: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
      failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    };
    return colors[state] || colors.pending;
  };

  const getStateIcon = (state: string) => {
    const icons: Record<string, React.ReactNode> = {
      pending: <Clock className="w-4 h-4" />,
      running: <Play className="w-4 h-4" />,
      pausing: <Pause className="w-4 h-4" />,
      paused: <Pause className="w-4 h-4" />,
      completing: <BarChart3 className="w-4 h-4" />,
      completed: <CheckCircle className="w-4 h-4" />,
      canceling: <XCircle className="w-4 h-4" />,
      canceled: <XCircle className="w-4 h-4" />,
      failed: <AlertCircle className="w-4 h-4" />,
    };
    return icons[state] || icons.pending;
  };

  const formatDuration = (ms: number | null) => {
    if (!ms) return 'N/A';
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Calculate summary statistics
  const summaryStats = {
    total: jobs.length,
    active: jobs.filter(j => ['pending', 'running', 'pausing', 'paused', 'completing'].includes(j.state)).length,
    completed: jobs.filter(j => j.state === 'completed').length,
    failed: jobs.filter(j => j.state === 'failed' || j.state === 'canceled').length,
    totalItems: jobs.reduce((sum, job) => sum + job.items_total, 0),
    completedItems: jobs.reduce((sum, job) => sum + job.items_completed, 0),
  };

  const renderJobCard = (job: BulkJob) => {
    const isExpanded = expandedJobs.has(job.id);
    const canPause = ['running'].includes(job.state);
    const canResume = ['paused'].includes(job.state);
    const canCancel = ['pending', 'running', 'pausing', 'paused'].includes(job.state);

    return (
      <Card key={job.id} className="hover:shadow-lg transition-shadow">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="outline" className={getStateColor(job.state)}>
                  {getStateIcon(job.state)}
                  {job.state.charAt(0).toUpperCase() + job.state.slice(1)}
                </Badge>
                {job.rate_limited && (
                  <Badge variant="outline" className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">
                    <AlertTriangle className="w-3 h-3 mr-1" />
                    Rate Limited
                  </Badge>
                )}
                {job.scheduling && (
                  <Badge variant="outline" className="bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
                    <Target className="w-3 h-3 mr-1" />
                    {job.scheduling.mode}
                  </Badge>
                )}
              </div>
              
              <CardTitle className="text-lg mb-1">
                {job.sheet_source ? `Sheet Job: ${job.sheet_source.range}` : `Job ${job.id.slice(0, 8)}`}
              </CardTitle>
              
              <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                <span className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  {formatDate(job.created_at)}
                </span>
                {job.eta_ms && (
                  <span className="flex items-center gap-1">
                    <Timer className="w-4 h-4" />
                    ETA: {formatDuration(job.eta_ms)}
                  </span>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => onViewDetails?.(job)}
                className="p-2 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                title="View Details"
              >
                <Eye className="w-5 h-5" />
              </button>
              
              <button
                onClick={() => toggleJobExpansion(job.id)}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                title={isExpanded ? "Collapse" : "Expand"}
              >
                {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Progress</span>
              <span className="text-sm font-bold text-gray-900 dark:text-white">
                {job.percent_complete.toFixed(1)}%
              </span>
            </div>
            <Progress value={Math.min(job.percent_complete, 100)} className="h-2" />
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-xs text-gray-600 dark:text-gray-400">Completed</p>
              <p className="text-lg font-bold text-green-600 dark:text-green-400">
                {job.items_completed}
              </p>
            </div>
            <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-xs text-gray-600 dark:text-gray-400">Failed</p>
              <p className="text-lg font-bold text-red-600 dark:text-red-400">
                {job.items_failed}
              </p>
            </div>
            <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-xs text-gray-600 dark:text-gray-400">Pending</p>
              <p className="text-lg font-bold text-yellow-600 dark:text-yellow-400">
                {job.items_pending}
              </p>
            </div>
            <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-xs text-gray-600 dark:text-gray-400">Total</p>
              <p className="text-lg font-bold text-gray-900 dark:text-white">
                {job.items_total}
              </p>
            </div>
          </div>

          {/* Scheduling Info */}
          {job.scheduling && (
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <h4 className="text-sm font-medium text-blue-900 dark:text-blue-300 mb-2">
                Scheduling Configuration
              </h4>
              <div className="grid grid-cols-2 gap-2 text-xs text-blue-800 dark:text-blue-400">
                <div>Mode: <span className="font-medium">{job.scheduling.mode}</span></div>
                <div>Optimization: <span className="font-medium">{job.scheduling.optimization_level}</span></div>
                <div>Max Concurrent: <span className="font-medium">{job.scheduling.max_concurrent_jobs}</span></div>
                <div>Priority Queue: <span className="font-medium">{job.scheduling.priority_queue ? 'Yes' : 'No'}</span></div>
              </div>
            </div>
          )}

          {/* Sheet Source Info */}
          {job.sheet_source && (
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Source</h4>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Sheet: {job.sheet_source.sheet_id}<br />
                Range: {job.sheet_source.range}
              </p>
            </div>
          )}

          {/* Expanded Details */}
          {isExpanded && (
            <div className="border-t border-gray-200 dark:border-gray-700 pt-4 space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Average Duration:</span>
                  <span className="ml-2 font-medium text-gray-900 dark:text-white">
                    {formatDuration(job.average_duration_ms_per_item)}/item
                  </span>
                </div>
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Time Processing:</span>
                  <span className="ml-2 font-medium text-gray-900 dark:text-white">
                    {formatDuration(job.time_processing_ms)}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Last Updated:</span>
                  <span className="ml-2 font-medium text-gray-900 dark:text-white">
                    {formatDate(job.updated_at)}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Items Skipped:</span>
                  <span className="ml-2 font-medium text-gray-900 dark:text-white">
                    {job.items_skipped}
                  </span>
                </div>
              </div>

              {/* Performance Metrics */}
              <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <h4 className="text-sm font-medium text-green-900 dark:text-green-300 mb-2">Performance</h4>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-xs text-green-800 dark:text-green-400">Success Rate</p>
                    <p className="text-lg font-bold text-green-900 dark:text-green-300">
                      {job.items_total > 0 
                        ? ((job.items_completed / job.items_total) * 100).toFixed(1)
                        : '0'}%
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-green-800 dark:text-green-400">Failure Rate</p>
                    <p className="text-lg font-bold text-red-600 dark:text-red-400">
                      {job.items_total > 0 
                        ? ((job.items_failed / job.items_total) * 100).toFixed(1)
                        : '0'}%
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-green-800 dark:text-green-400">Items/Hour</p>
                    <p className="text-lg font-bold text-green-900 dark:text-green-300">
                      {job.average_duration_ms_per_item 
                        ? Math.round(3600000 / job.average_duration_ms_per_item)
                        : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-2 pt-2">
            {canPause && (
              <button 
                onClick={() => handleJobAction(job.id, 'pause')}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 border border-yellow-300 text-yellow-700 dark:text-yellow-400 dark:border-yellow-600 rounded-lg hover:bg-yellow-50 dark:hover:bg-yellow-900/20 transition-colors"
              >
                <Pause className="w-4 h-4" />
                Pause
              </button>
            )}
            {canResume && (
              <button 
                onClick={() => handleJobAction(job.id, 'resume')}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 border border-green-300 text-green-700 dark:text-green-400 dark:border-green-600 rounded-lg hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
              >
                <Play className="w-4 h-4" />
                Resume
              </button>
            )}
            {canCancel && (
              <button 
                onClick={() => handleJobAction(job.id, 'cancel')}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 border border-red-300 text-red-700 dark:text-red-400 dark:border-red-600 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              >
                <XCircle className="w-4 h-4" />
                Cancel
              </button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderJobListItem = (job: BulkJob) => {
    const canPause = ['running'].includes(job.state);
    const canResume = ['paused'].includes(job.state);
    const canCancel = ['pending', 'running', 'pausing', 'paused'].includes(job.state);

    return (
      <div key={job.id} className="flex items-center gap-4 p-4 border border-gray-200 dark:border-gray-800 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="outline" className={getStateColor(job.state)}>
              {getStateIcon(job.state)}
              {job.state.charAt(0).toUpperCase() + job.state.slice(1)}
            </Badge>
            {job.rate_limited && (
              <Badge variant="outline" className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">
                <AlertTriangle className="w-3 h-3 mr-1" />
                Rate Limited
              </Badge>
            )}
          </div>
          <h3 className="font-medium text-gray-900 dark:text-white mb-1">
            {job.sheet_source ? `Sheet Job: ${job.sheet_source.range}` : `Job ${job.id.slice(0, 8)}`}
          </h3>
          <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
            <span>{formatDate(job.created_at)}</span>
            <span>{job.items_completed}/{job.items_total} completed</span>
            {job.eta_ms && <span>ETA: {formatDuration(job.eta_ms)}</span>}
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Progress value={Math.min(job.percent_complete, 100)} className="w-24 h-2" />
          <span className="text-sm font-medium text-gray-900 dark:text-white w-12">
            {job.percent_complete.toFixed(0)}%
          </span>
        </div>

        <div className="flex items-center gap-2">
          {canPause && (
            <button 
              onClick={() => handleJobAction(job.id, 'pause')}
              className="p-2 text-yellow-600 hover:text-yellow-700 transition-colors"
              title="Pause"
            >
              <Pause className="w-4 h-4" />
            </button>
          )}
          {canResume && (
            <button 
              onClick={() => handleJobAction(job.id, 'resume')}
              className="p-2 text-green-600 hover:text-green-700 transition-colors"
              title="Resume"
            >
              <Play className="w-4 h-4" />
            </button>
          )}
          {canCancel && (
            <button 
              onClick={() => handleJobAction(job.id, 'cancel')}
              className="p-2 text-red-600 hover:text-red-700 transition-colors"
              title="Cancel"
            >
              <XCircle className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => onViewDetails?.(job)}
            className="p-2 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
            title="View Details"
          >
            <Eye className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  };

  if (loading && jobs.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex items-center gap-2">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-600" />
          <span className="text-gray-600 dark:text-gray-400">Loading batch jobs...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Dashboard */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-600" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Jobs</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{summaryStats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-orange-600" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Active</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{summaryStats.active}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Completed</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{summaryStats.completed}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <XCircle className="w-5 h-5 text-red-600" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Failed</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{summaryStats.failed}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-purple-600" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Items</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{summaryStats.totalItems}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Processed</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{summaryStats.completedItems}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-red-800 dark:text-red-400 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            {error}
          </p>
        </div>
      )}

      {/* Controls */}
      <div className="flex items-center justify-between gap-4">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-auto">
          <TabsList>
            <TabsTrigger value="active" className="flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Active ({summaryStats.active})
            </TabsTrigger>
            <TabsTrigger value="completed" className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4" />
              Completed ({summaryStats.completed})
            </TabsTrigger>
            <TabsTrigger value="failed" className="flex items-center gap-2">
              <XCircle className="w-4 h-4" />
              Failed ({summaryStats.failed})
            </TabsTrigger>
            <TabsTrigger value="all" className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              All ({summaryStats.total})
            </TabsTrigger>
          </TabsList>
        </Tabs>

        <div className="flex items-center gap-2">
          {/* Sort Controls */}
          <select
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [field, order] = e.target.value.split('-');
              setSortBy(field as typeof sortBy);
              setSortOrder(order as typeof sortOrder);
            }}
            className="px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="created_at-desc">Newest First</option>
            <option value="created_at-asc">Oldest First</option>
            <option value="updated_at-desc">Recently Updated</option>
            <option value="percent_complete-desc">Progress High-Low</option>
            <option value="percent_complete-asc">Progress Low-High</option>
          </select>

          {/* View Mode Toggle */}
          <div className="flex border border-gray-300 dark:border-gray-700 rounded-lg overflow-hidden">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 transition-colors ${
                viewMode === 'grid' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
              title="Grid View"
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 transition-colors ${
                viewMode === 'list' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
              title="List View"
            >
              <List className="w-4 h-4" />
            </button>
          </div>

          {/* Refresh Button */}
          <button
            onClick={loadJobs}
            disabled={loading}
            className="p-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors disabled:opacity-50"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Jobs Display */}
      <div className="min-h-[400px]">
        {sortedJobs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <FileText className="w-12 h-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No {activeTab === 'all' ? '' : activeTab} batch jobs found
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              {activeTab === 'active' 
                ? 'No jobs are currently running or pending.'
                : `No ${activeTab} jobs to display.`}
            </p>
          </div>
        ) : (
          <div className={
            viewMode === 'grid' 
              ? 'grid grid-cols-1 lg:grid-cols-2 gap-6'
              : 'space-y-4'
          }>
            {sortedJobs.map(job => 
              viewMode === 'grid' ? renderJobCard(job) : renderJobListItem(job)
            )}
          </div>
        )}
      </div>
    </div>
  );
}
