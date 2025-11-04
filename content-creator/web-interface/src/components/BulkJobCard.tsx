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
  BarChart3
} from 'lucide-react';
import apiClient from '../lib/api';

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

interface BulkJobCardProps {
  job: BulkJob;
  onViewDetails: (job: BulkJob) => void;
  onRefresh?: () => void;
}

export default function BulkJobCard({ job, onViewDetails, onRefresh }: BulkJobCardProps) {
  const [isWebSocketConnected, setIsWebSocketConnected] = useState(false);
  const [currentJob, setCurrentJob] = useState<BulkJob>(job);

  useEffect(() => {
    // Connect to WebSocket for real-time updates
    const handleWebSocketMessage = (data: any) => {
      if (data.type === 'job.state_changed' || data.type === 'job.progress') {
        setCurrentJob(prevJob => ({ ...prevJob, ...data.data }));
        if (onRefresh) onRefresh();
      }
    };

    // Connect to WebSocket (this would be handled by the parent component in a real app)
    // For now, we'll simulate real-time updates with polling
    const interval = setInterval(() => {
      if (['pending', 'running', 'pausing', 'paused', 'completing'].includes(currentJob.state)) {
        loadJobStatus();
      }
    }, 10000); // Poll every 10 seconds

    return () => {
      clearInterval(interval);
    };
  }, [currentJob.state, onRefresh]);

  const loadJobStatus = async () => {
    try {
      const response = await apiClient.getBulkJob(currentJob.id);
      setCurrentJob(response.data);
    } catch (error) {
      console.error('Failed to load job status:', error);
    }
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

  const canCancel = ['pending', 'running', 'pausing', 'paused'].includes(currentJob.state);
  const canPause = ['running'].includes(currentJob.state);
  const canResume = ['paused'].includes(currentJob.state);

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${getStateColor(currentJob.state)}`}>
              {getStateIcon(currentJob.state)}
              {currentJob.state.charAt(0).toUpperCase() + currentJob.state.slice(1)}
            </span>
            {currentJob.rate_limited && (
              <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">
                <AlertCircle className="w-3 h-3" />
                Rate Limited
              </span>
            )}
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
            {currentJob.sheet_source ? `Sheet Job: ${currentJob.sheet_source.range}` : `Job ${currentJob.id}`}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-1">
            <Calendar className="w-4 h-4" />
            Created {formatDate(currentJob.created_at)}
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => onViewDetails(currentJob)}
            className="p-2 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
            title="View Details"
          >
            <Eye className="w-5 h-5" />
          </button>
          
          {currentJob.artifacts && currentJob.artifacts.length > 0 && (
            <button
              className="p-2 text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors"
              title="Download Artifacts"
            >
              <Download className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Progress Section */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Progress
          </span>
          <span className="text-sm font-bold text-gray-900 dark:text-white">
            {currentJob.percent_complete.toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${Math.min(currentJob.percent_complete, 100)}%` }}
          />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <p className="text-xs text-gray-600 dark:text-gray-400">Completed</p>
          <p className="text-lg font-bold text-green-600 dark:text-green-400">
            {currentJob.items_completed}
          </p>
        </div>
        <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <p className="text-xs text-gray-600 dark:text-gray-400">Failed</p>
          <p className="text-lg font-bold text-red-600 dark:text-red-400">
            {currentJob.items_failed}
          </p>
        </div>
        <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <p className="text-xs text-gray-600 dark:text-gray-400">Pending</p>
          <p className="text-lg font-bold text-yellow-600 dark:text-yellow-400">
            {currentJob.items_pending}
          </p>
        </div>
        <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <p className="text-xs text-gray-600 dark:text-gray-400">Total</p>
          <p className="text-lg font-bold text-gray-900 dark:text-white">
            {currentJob.items_total}
          </p>
        </div>
      </div>

      {/* Time Information */}
      {(currentJob.eta_ms || currentJob.average_duration_ms_per_item) && (
        <div className="flex justify-between items-center text-sm text-gray-600 dark:text-gray-400 mb-4">
          {currentJob.eta_ms && (
            <span>ETA: {formatDuration(currentJob.eta_ms)}</span>
          )}
          {currentJob.average_duration_ms_per_item && (
            <span>Avg: {formatDuration(currentJob.average_duration_ms_per_item)}/item</span>
          )}
        </div>
      )}

      {/* Sheet Source Info */}
      {currentJob.sheet_source && (
        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg mb-4">
          <p className="text-xs text-blue-800 dark:text-blue-300 font-medium">
            Sheet: {currentJob.sheet_source.sheet_id}
          </p>
          <p className="text-xs text-blue-600 dark:text-blue-400">
            Range: {currentJob.sheet_source.range}
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-2">
        {canPause && (
          <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 border border-yellow-300 text-yellow-700 dark:text-yellow-400 dark:border-yellow-600 rounded-lg hover:bg-yellow-50 dark:hover:bg-yellow-900/20 transition-colors">
            <Pause className="w-4 h-4" />
            Pause
          </button>
        )}
        {canResume && (
          <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 border border-green-300 text-green-700 dark:text-green-400 dark:border-green-600 rounded-lg hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors">
            <Play className="w-4 h-4" />
            Resume
          </button>
        )}
        {canCancel && (
          <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 border border-red-300 text-red-700 dark:text-red-400 dark:border-red-600 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
            <XCircle className="w-4 h-4" />
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}
