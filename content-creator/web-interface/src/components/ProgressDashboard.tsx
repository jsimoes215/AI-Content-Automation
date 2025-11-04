import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  Activity, 
  AlertCircle, 
  CheckCircle, 
  Clock, 
  Download, 
  Pause, 
  Play, 
  RefreshCw, 
  Settings, 
  TrendingUp,
  XCircle,
  Loader2,
  Eye,
  EyeOff,
  Filter,
  SortAsc,
  SortDesc
} from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Tooltip, 
  TooltipContent, 
  TooltipProvider, 
  TooltipTrigger 
} from '@/components/ui/tooltip';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import useWebSocket, { JobProgress, VideoProgress, JobState } from '../hooks/useWebSocket';
import { format } from 'date-fns';

interface ProgressDashboardProps {
  jobId: string;
  token?: string;
  jobData?: {
    id: string;
    title?: string;
    state: string;
    created_at: string;
    processing_deadline_ms?: number;
    sheet_source?: {
      sheet_id: string;
      range: string;
    };
  };
  onJobAction?: (action: 'pause' | 'resume' | 'cancel' | 'retry', jobId: string) => void;
}

interface DashboardState {
  jobProgress: JobProgress | null;
  jobState: JobState | null;
  videos: VideoProgress[];
  connectionState: {
    connected: boolean;
    error: string | null;
    lastUpdate: Date | null;
  };
  filters: {
    videoState: string;
    sortBy: string;
    sortOrder: 'asc' | 'desc';
    showErrors: boolean;
  };
  expandedVideos: Set<string>;
}

const jobStateColors: Record<string, { bg: string; text: string; border: string }> = {
  pending: { bg: 'bg-gray-100 dark:bg-gray-800', text: 'text-gray-800 dark:text-gray-300', border: 'border-gray-300' },
  running: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-800 dark:text-blue-400', border: 'border-blue-300' },
  pausing: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-800 dark:text-yellow-400', border: 'border-yellow-300' },
  paused: { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-800 dark:text-orange-400', border: 'border-orange-300' },
  completing: { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-800 dark:text-purple-400', border: 'border-purple-300' },
  completed: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-800 dark:text-green-400', border: 'border-green-300' },
  canceling: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-800 dark:text-red-400', border: 'border-red-300' },
  canceled: { bg: 'bg-gray-100 dark:bg-gray-800', text: 'text-gray-800 dark:text-gray-300', border: 'border-gray-300' },
  failed: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-800 dark:text-red-400', border: 'border-red-300' },
};

const videoStateIcons: Record<string, React.ComponentType<any>> = {
  pending: Clock,
  processing: Loader2,
  completed: CheckCircle,
  failed: XCircle,
  skipped: AlertCircle,
  canceled: XCircle,
};

export function ProgressDashboard({ 
  jobId, 
  token, 
  jobData,
  onJobAction 
}: ProgressDashboardProps) {
  const [state, setState] = useState<DashboardState>({
    jobProgress: null,
    jobState: null,
    videos: [],
    connectionState: {
      connected: false,
      error: null,
      lastUpdate: null,
    },
    filters: {
      videoState: 'all',
      sortBy: 'created_at',
      sortOrder: 'desc',
      showErrors: false,
    },
    expandedVideos: new Set(),
  });

  // WebSocket event handlers
  const handleProgress = useCallback((progress: JobProgress) => {
    setState(prev => ({
      ...prev,
      jobProgress: progress,
      connectionState: {
        ...prev.connectionState,
        lastUpdate: new Date(),
      },
    }));
  }, []);

  const handleStateChange = useCallback((jobState: JobState) => {
    setState(prev => ({
      ...prev,
      jobState,
      connectionState: {
        ...prev.connectionState,
        lastUpdate: new Date(),
      },
    }));
  }, []);

  const handleVideoUpdate = useCallback((video: VideoProgress) => {
    setState(prev => ({
      ...prev,
      videos: (() => {
        const existing = prev.videos.find(v => v.id === video.id);
        if (existing) {
          return prev.videos.map(v => v.id === video.id ? video : v);
        } else {
          return [...prev.videos, video];
        }
      })(),
      connectionState: {
        ...prev.connectionState,
        lastUpdate: new Date(),
      },
    }));
  }, []);

  const handleVideoCompleted = useCallback((video: VideoProgress) => {
    handleVideoUpdate(video);
  }, [handleVideoUpdate]);

  const handleVideoFailed = useCallback((video: VideoProgress) => {
    handleVideoUpdate(video);
  }, [handleVideoUpdate]);

  const handleJobCompleted = useCallback((data: any) => {
    console.log('Job completed:', data);
    // You could trigger a notification or redirect here
  }, []);

  const handleJobFailed = useCallback((data: any) => {
    console.error('Job failed:', data);
    // You could trigger an error notification here
  }, []);

  const handleJobCanceled = useCallback((data: any) => {
    console.log('Job canceled:', data);
  }, []);

  // WebSocket connection
  const {
    connected,
    connecting,
    error: wsError,
    lastMessage,
    connect,
    disconnect,
    getConnectionHealth,
  } = useWebSocket({
    jobId,
    token,
    onProgress: handleProgress,
    onStateChange: handleStateChange,
    onVideoUpdate: handleVideoUpdate,
    onVideoCompleted: handleVideoCompleted,
    onVideoFailed: handleVideoFailed,
    onJobCompleted: handleJobCompleted,
    onJobFailed: handleJobFailed,
    onJobCanceled: handleJobCanceled,
  });

  // Filter and sort videos
  const filteredAndSortedVideos = useMemo(() => {
    let filtered = state.videos;

    if (state.filters.videoState !== 'all') {
      filtered = filtered.filter(video => video.state === state.filters.videoState);
    }

    if (state.filters.showErrors) {
      filtered = filtered.filter(video => video.errors && video.errors.length > 0);
    }

    // Sort videos
    filtered.sort((a, b) => {
      const factor = state.filters.sortOrder === 'asc' ? 1 : -1;
      
      switch (state.filters.sortBy) {
        case 'row_index':
          return factor * (a.row_index - b.row_index);
        case 'title':
          return factor * a.title.localeCompare(b.title);
        case 'state':
          return factor * a.state.localeCompare(b.state);
        case 'created_at':
        default:
          return factor * (new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
      }
    });

    return filtered;
  }, [state.videos, state.filters]);

  // Toggle video expansion
  const toggleVideoExpansion = useCallback((videoId: string) => {
    setState(prev => {
      const newExpanded = new Set(prev.expandedVideos);
      if (newExpanded.has(videoId)) {
        newExpanded.delete(videoId);
      } else {
        newExpanded.add(videoId);
      }
      return { ...prev, expandedVideos: newExpanded };
    });
  }, []);

  // Get status color for job
  const getJobStatusColor = useCallback((stateValue: string) => {
    return jobStateColors[stateValue] || jobStateColors.pending;
  }, []);

  // Format time
  const formatDuration = useCallback((ms: number | null) => {
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
  }, []);

  // Format ETA
  const formatETA = useCallback((etaMs: number | null) => {
    if (!etaMs) return 'Calculating...';
    return formatDuration(etaMs);
  }, [formatDuration]);

  // Job actions
  const handleJobAction = useCallback((action: 'pause' | 'resume' | 'cancel' | 'retry') => {
    if (onJobAction) {
      onJobAction(action, jobId);
    }
  }, [jobId, onJobAction]);

  // Calculate progress statistics
  const progressStats = useMemo(() => {
    const progress = state.jobProgress;
    if (!progress) return null;

    return {
      successRate: progress.items_total > 0 
        ? (progress.items_completed / progress.items_total * 100).toFixed(1)
        : '0.0',
      failureRate: progress.items_total > 0 
        ? (progress.items_failed / progress.items_total * 100).toFixed(1)
        : '0.0',
      averageDuration: progress.average_duration_ms_per_item 
        ? formatDuration(progress.average_duration_ms_per_item)
        : 'Calculating...',
      estimatedCompletion: progress.eta_ms 
        ? new Date(Date.now() + progress.eta_ms)
        : null,
    };
  }, [state.jobProgress, formatDuration]);

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              {jobData?.title || `Job ${jobId}`}
            </h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Created {jobData?.created_at ? format(new Date(jobData.created_at), 'PPp') : 'Unknown date'}
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Connection Status */}
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                connected ? 'bg-green-500' : connecting ? 'bg-yellow-500' : 'bg-red-500'
              }`} />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {connected ? 'Live' : connecting ? 'Connecting...' : 'Disconnected'}
              </span>
            </div>

            {/* Job Actions */}
            <div className="flex space-x-2">
              {state.jobState?.new_state === 'running' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleJobAction('pause')}
                >
                  <Pause className="w-4 h-4 mr-2" />
                  Pause
                </Button>
              )}
              
              {state.jobState?.new_state === 'paused' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleJobAction('resume')}
                >
                  <Play className="w-4 h-4 mr-2" />
                  Resume
                </Button>
              )}
              
              {(state.jobState?.new_state === 'running' || state.jobState?.new_state === 'paused') && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleJobAction('cancel')}
                >
                  <XCircle className="w-4 h-4 mr-2" />
                  Cancel
                </Button>
              )}

              <Button
                variant="outline"
                size="sm"
                onClick={() => window.location.reload()}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </div>

        {/* Connection Error Alert */}
        {wsError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              WebSocket connection error: {wsError}
            </AlertDescription>
          </Alert>
        )}

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Progress Overview */}
          <div className="lg:col-span-2 space-y-6">
            {/* Job Status Card */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center space-x-2">
                    <Activity className="w-5 h-5" />
                    <span>Job Progress</span>
                  </CardTitle>
                  {state.jobState && (
                    <Badge 
                      variant="outline" 
                      className={`${getJobStatusColor(state.jobState.new_state).bg} ${getJobStatusColor(state.jobState.new_state).text} ${getJobStatusColor(state.jobState.new_state).border}`}
                    >
                      {state.jobState.new_state}
                    </Badge>
                  )}
                </div>
                {state.jobState && (
                  <CardDescription>
                    {state.jobState.reason || `State changed from ${state.jobState.prior_state} to ${state.jobState.new_state}`}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent className="space-y-4">
                {state.jobProgress ? (
                  <>
                    {/* Progress Bar */}
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Overall Progress</span>
                        <span>{state.jobProgress.percent_complete.toFixed(1)}%</span>
                      </div>
                      <Progress 
                        value={state.jobProgress.percent_complete} 
                        className="w-full"
                      />
                    </div>

                    {/* Progress Statistics */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                          {state.jobProgress.items_completed}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Completed</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                          {state.jobProgress.items_failed}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Failed</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                          {state.jobProgress.items_pending}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Pending</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-gray-600 dark:text-gray-400">
                          {state.jobProgress.items_total}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Total</p>
                      </div>
                    </div>

                    {/* Additional Metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
                      <div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">ETA</p>
                        <p className="font-medium">
                          {formatETA(state.jobProgress.eta_ms)}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Avg Duration</p>
                        <p className="font-medium">
                          {formatDuration(state.jobProgress.average_duration_ms_per_item)}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Processing Time</p>
                        <p className="font-medium">
                          {formatDuration(state.jobProgress.time_processing_ms)}
                        </p>
                      </div>
                    </div>

                    {/* Rate Limiting Indicator */}
                    {state.jobProgress.rate_limited && (
                      <Alert>
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                          Job is currently rate limited. Processing may be slower.
                        </AlertDescription>
                      </Alert>
                    )}
                  </>
                ) : (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span className="ml-2">Loading progress data...</span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Video Progress */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>Video Progress</span>
                  <div className="flex items-center space-x-2">
                    <Select
                      value={state.filters.videoState}
                      onValueChange={(value) =>
                        setState(prev => ({
                          ...prev,
                          filters: { ...prev.filters, videoState: value }
                        }))
                      }
                    >
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All States</SelectItem>
                        <SelectItem value="pending">Pending</SelectItem>
                        <SelectItem value="processing">Processing</SelectItem>
                        <SelectItem value="completed">Completed</SelectItem>
                        <SelectItem value="failed">Failed</SelectItem>
                        <SelectItem value="skipped">Skipped</SelectItem>
                      </SelectContent>
                    </Select>
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setState(prev => ({
                          ...prev,
                          filters: { ...prev.filters, showErrors: !prev.filters.showErrors }
                        }))
                      }
                    >
                      {state.filters.showErrors ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </Button>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-96">
                  {filteredAndSortedVideos.length > 0 ? (
                    <div className="space-y-2">
                      {filteredAndSortedVideos.map((video) => {
                        const StateIcon = videoStateIcons[video.state] || Clock;
                        const isExpanded = state.expandedVideos.has(video.id);
                        
                        return (
                          <div
                            key={video.id}
                            className="border rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800"
                          >
                            <div 
                              className="flex items-center justify-between cursor-pointer"
                              onClick={() => toggleVideoExpansion(video.id)}
                            >
                              <div className="flex items-center space-x-3">
                                <StateIcon 
                                  className={`w-4 h-4 ${
                                    video.state === 'completed' ? 'text-green-500' :
                                    video.state === 'failed' ? 'text-red-500' :
                                    video.state === 'processing' ? 'text-blue-500 animate-spin' :
                                    'text-gray-400'
                                  }`}
                                />
                                <div>
                                  <p className="font-medium">Video {video.row_index}</p>
                                  <p className="text-sm text-gray-600 dark:text-gray-400">
                                    {video.title || `Item ${video.row_index}`}
                                  </p>
                                </div>
                              </div>
                              
                              <div className="flex items-center space-x-4">
                                <div className="text-right">
                                  <p className="text-sm font-medium">{video.percent_complete.toFixed(0)}%</p>
                                  <p className="text-xs text-gray-500">{video.state}</p>
                                </div>
                                <Badge variant="outline">{video.state}</Badge>
                              </div>
                            </div>

                            {/* Expanded Details */}
                            {isExpanded && (
                              <div className="mt-4 pt-4 border-t space-y-3">
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                  <div>
                                    <p className="text-gray-600 dark:text-gray-400">Created</p>
                                    <p>{format(new Date(video.created_at), 'PPp')}</p>
                                  </div>
                                  <div>
                                    <p className="text-gray-600 dark:text-gray-400">Updated</p>
                                    <p>{format(new Date(video.updated_at), 'PPp')}</p>
                                  </div>
                                </div>

                                {video.percent_complete > 0 && (
                                  <div>
                                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                                      Progress
                                    </p>
                                    <Progress value={video.percent_complete} className="w-full" />
                                  </div>
                                )}

                                {video.artifacts && video.artifacts.length > 0 && (
                                  <div>
                                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                                      Artifacts
                                    </p>
                                    <div className="space-y-1">
                                      {video.artifacts.map((artifact, index) => (
                                        <div
                                          key={index}
                                          className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded"
                                        >
                                          <span className="text-sm">{artifact.type}</span>
                                          <Button variant="ghost" size="sm">
                                            <Download className="w-4 h-4" />
                                          </Button>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {video.errors && video.errors.length > 0 && (
                                  <div>
                                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                                      Errors
                                    </p>
                                    <div className="space-y-2">
                                      {video.errors.map((error, index) => (
                                        <Alert key={index} variant="destructive">
                                          <AlertCircle className="h-4 w-4" />
                                          <AlertDescription>
                                            <strong>{error.error_code}</strong>: {error.error_message}
                                          </AlertDescription>
                                        </Alert>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                      {state.videos.length === 0 
                        ? 'No videos processed yet' 
                        : 'No videos match the current filters'
                      }
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Status and Details */}
          <div className="space-y-6">
            {/* Job Details */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Settings className="w-5 h-5" />
                  <span>Job Details</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Job ID</p>
                  <p className="font-mono text-sm">{jobId}</p>
                </div>
                
                {jobData?.sheet_source && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Source Sheet</p>
                    <p className="font-mono text-sm">{jobData.sheet_source.sheet_id}</p>
                    <p className="text-xs text-gray-500">{jobData.sheet_source.range}</p>
                  </div>
                )}

                {jobData?.processing_deadline_ms && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Processing Deadline</p>
                    <p className="text-sm">{formatDuration(jobData.processing_deadline_ms)}</p>
                  </div>
                )}

                {state.connectionState.lastUpdate && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Last Update</p>
                    <p className="text-sm">{format(state.connectionState.lastUpdate, 'PPp')}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Performance Metrics */}
            {progressStats && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <TrendingUp className="w-5 h-5" />
                    <span>Performance</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Success Rate</span>
                      <span className="font-medium">{progressStats.successRate}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Failure Rate</span>
                      <span className="font-medium">{progressStats.failureRate}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Avg Duration</span>
                      <span className="font-medium">{progressStats.averageDuration}</span>
                    </div>
                    {progressStats.estimatedCompletion && (
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Est. Completion</span>
                        <span className="font-medium">
                          {format(progressStats.estimatedCompletion, 'PPp')}
                        </span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Connection Health */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Activity className="w-5 h-5" />
                  <span>Connection Health</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Status</span>
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${
                      connected ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                    <span className="text-sm font-medium">
                      {connected ? 'Connected' : 'Disconnected'}
                    </span>
                  </div>
                </div>
                
                {lastMessage && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Last Message</span>
                    <span className="text-sm">
                      {format(new Date(lastMessage.ts), 'HH:mm:ss')}
                    </span>
                  </div>
                )}

                <Button
                  variant="outline"
                  size="sm"
                  onClick={connected ? disconnect : connect}
                  className="w-full"
                >
                  {connected ? 'Disconnect' : 'Reconnect'}
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}

export default ProgressDashboard;