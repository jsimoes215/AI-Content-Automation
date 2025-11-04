import { useState, useEffect } from 'react';
import { 
  Clock, 
  Play, 
  Pause, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Filter,
  Download,
  RefreshCw,
  Calendar,
  TrendingUp,
  FileText,
  Activity
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import apiClient from '../lib/api';

interface Job {
  id: string;
  title: string;
  state: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'canceled' | 'pausing' | 'completing' | 'canceling';
  percent_complete: number;
  items_total: number;
  items_completed: number;
  items_failed: number;
  items_skipped: number;
  items_canceled: number;
  items_pending: number;
  time_to_start_ms?: number;
  time_processing_ms: number;
  average_duration_ms_per_item?: number;
  eta_ms?: number;
  rate_limited: boolean;
  processing_deadline_ms?: number;
  callback_url?: string;
  created_at: string;
  updated_at: string;
  sheet_source?: {
    sheet_id: string;
    range: string;
    connected_at: string;
  };
  artifacts?: Array<{
    type: string;
    content_type: string;
    size: number;
    url: string;
  }>;
}

interface JobHistoryFilters {
  state?: string;
  dateRange: string;
  search: string;
}

export default function JobHistory() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [filters, setFilters] = useState<JobHistoryFilters>({
    dateRange: '30d',
    search: ''
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    loadJobs();
  }, [filters, currentPage]);

  const loadJobs = async (reset = false) => {
    try {
      setLoading(true);
      if (reset) {
        setJobs([]);
        setCurrentPage(1);
        setHasMore(true);
      }
      
      // Mock data for now - in production, this would use the actual API
      const mockJobs: Job[] = [
        {
          id: 'job_01HABCDEF0123456789',
          title: 'Campaign Spring Launch',
          state: 'completed',
          percent_complete: 100.0,
          items_total: 1000,
          items_completed: 950,
          items_failed: 25,
          items_skipped: 25,
          items_canceled: 0,
          items_pending: 0,
          time_to_start_ms: 2100,
          time_processing_ms: 1800000,
          average_duration_ms_per_item: 1895,
          eta_ms: 0,
          rate_limited: false,
          processing_deadline_ms: 7200000,
          created_at: '2025-11-05T00:52:13Z',
          updated_at: '2025-11-05T01:22:13Z',
          sheet_source: {
            sheet_id: '1A2B3C4D5E6F7G8H9I0J',
            range: 'A1:Z1000',
            connected_at: '2025-11-05T00:51:10Z'
          },
          artifacts: [
            {
              type: 'manifest',
              content_type: 'application/json',
              size: 4096,
              url: 'https://storage.example.com/manifest.json'
            }
          ]
        },
        {
          id: 'job_01HXYZ1234567890',
          title: 'Product Demo Videos',
          state: 'running',
          percent_complete: 45.8,
          items_total: 500,
          items_completed: 229,
          items_failed: 3,
          items_skipped: 0,
          items_canceled: 0,
          items_pending: 268,
          time_to_start_ms: 1500,
          time_processing_ms: 450000,
          average_duration_ms_per_item: 1965,
          eta_ms: 532000,
          rate_limited: false,
          processing_deadline_ms: 7200000,
          created_at: '2025-11-04T15:30:22Z',
          updated_at: '2025-11-05T01:35:45Z'
        },
        {
          id: 'job_01HDEF4567890123',
          title: 'Social Media Content Batch',
          state: 'failed',
          percent_complete: 12.5,
          items_total: 800,
          items_completed: 100,
          items_failed: 150,
          items_skipped: 0,
          items_canceled: 0,
          items_pending: 550,
          time_to_start_ms: 3200,
          time_processing_ms: 300000,
          average_duration_ms_per_item: 3000,
          eta_ms: null,
          rate_limited: true,
          processing_deadline_ms: 3600000,
          created_at: '2025-11-04T10:15:00Z',
          updated_at: '2025-11-04T11:20:00Z',
          artifacts: []
        }
      ];

      if (reset) {
        setJobs(mockJobs);
      } else {
        setJobs(prev => [...prev, ...mockJobs]);
      }
      setHasMore(false); // Mock no more data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  const getStateIcon = (state: string) => {
    switch (state) {
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      case 'running':
        return <Play className="w-5 h-5 text-blue-500" />;
      case 'paused':
        return <Pause className="w-5 h-5 text-orange-500" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'canceled':
        return <XCircle className="w-5 h-5 text-gray-500" />;
      case 'pausing':
      case 'completing':
      case 'canceling':
        return <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStateColor = (state: string) => {
    switch (state) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'running':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
      case 'paused':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400';
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      case 'canceled':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400';
      case 'pausing':
      case 'completing':
      case 'canceling':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400';
    }
  };

  const formatDuration = (ms: number | null | undefined) => {
    if (!ms) return 'N/A';
    const hours = Math.floor(ms / 3600000);
    const minutes = Math.floor((ms % 3600000) / 60000);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Analytics data
  const stateDistribution = [
    { name: 'Completed', value: 45, color: '#10B981' },
    { name: 'Running', value: 12, color: '#3B82F6' },
    { name: 'Failed', value: 8, color: '#EF4444' },
    { name: 'Pending', value: 15, color: '#F59E0B' },
    { name: 'Paused', value: 5, color: '#F97316' },
    { name: 'Canceled', value: 3, color: '#6B7280' }
  ];

  const jobsOverTime = [
    { date: 'Mon', jobs: 8, cost: 45.60 },
    { date: 'Tue', jobs: 12, cost: 68.40 },
    { date: 'Wed', jobs: 6, cost: 34.20 },
    { date: 'Thu', jobs: 15, cost: 85.50 },
    { date: 'Fri', jobs: 18, cost: 102.60 },
    { date: 'Sat', jobs: 10, cost: 57.00 },
    { date: 'Sun', jobs: 7, cost: 39.90 }
  ];

  const performanceMetrics = [
    { metric: 'Average Completion Time', value: '2.3 hours', change: '-12%', trend: 'down' },
    { metric: 'Success Rate', value: '94.2%', change: '+2.1%', trend: 'up' },
    { metric: 'Cost per Video', value: '$0.19', change: '-5%', trend: 'down' },
    { metric: 'Daily Throughput', value: '156 videos', change: '+8%', trend: 'up' }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Job History</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Track and analyze your bulk content generation jobs
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => loadJobs(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
          <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center">
            <Download className="w-4 h-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {performanceMetrics.map((metric, index) => (
          <div
            key={index}
            className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {metric.metric}
              </h3>
              <TrendingUp className="w-5 h-5 text-gray-400" />
            </div>
            <div className="mt-2">
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {metric.value}
              </p>
              <p className={`text-sm mt-1 ${
                metric.trend === 'up' 
                  ? 'text-green-600 dark:text-green-400' 
                  : 'text-red-600 dark:text-red-400'
              }`}>
                {metric.change} from last week
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
            Job State Distribution
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={stateDistribution}
                cx="50%"
                cy="50%"
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}`}
              >
                {stateDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
            Jobs Created Over Time
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={jobsOverTime}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
              <XAxis dataKey="date" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Line
                type="monotone"
                dataKey="jobs"
                stroke="#3B82F6"
                strokeWidth={2}
                dot={{ fill: '#3B82F6', r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center space-x-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Filters:</span>
          </div>
          <select
            value={filters.state || ''}
            onChange={(e) => setFilters(prev => ({ ...prev, state: e.target.value || undefined }))}
            className="px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All States</option>
            <option value="pending">Pending</option>
            <option value="running">Running</option>
            <option value="paused">Paused</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="canceled">Canceled</option>
          </select>
          <select
            value={filters.dateRange}
            onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value }))}
            className="px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="1y">Last year</option>
          </select>
          <input
            type="text"
            placeholder="Search jobs..."
            value={filters.search}
            onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
            className="flex-1 min-w-64 px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Jobs Table */}
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Recent Jobs ({jobs.length})
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Job
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Progress
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Items
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Duration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
              {jobs.map((job) => (
                <tr 
                  key={job.id} 
                  className="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                  onClick={() => setSelectedJob(job)}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10">
                        <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                          <FileText className="w-5 h-5 text-white" />
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {job.title}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {job.id}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStateIcon(job.state)}
                      <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${getStateColor(job.state)}`}>
                        {job.state.charAt(0).toUpperCase() + job.state.slice(1)}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2 mr-3">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${job.percent_complete}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-900 dark:text-white">
                        {job.percent_complete.toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    <div>
                      <div>Total: {job.items_total}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        ✓ {job.items_completed} | ✗ {job.items_failed}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    <div>
                      <div>{formatDuration(job.time_processing_ms)}</div>
                      {job.average_duration_ms_per_item && (
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          Avg: {formatDuration(job.average_duration_ms_per_item)}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {formatDate(job.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedJob(job);
                      }}
                      className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300"
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}

        {hasMore && !loading && (
          <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-800">
            <button
              onClick={() => setCurrentPage(prev => prev + 1)}
              className="w-full py-2 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium"
            >
              Load More Jobs
            </button>
          </div>
        )}
      </div>

      {/* Job Details Modal */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-900 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800 flex justify-between items-center">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Job Details: {selectedJob.title}
              </h2>
              <button
                onClick={() => setSelectedJob(null)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <XCircle className="w-6 h-6" />
              </button>
            </div>
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    General Information
                  </h3>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Job ID</label>
                      <p className="text-sm text-gray-900 dark:text-white">{selectedJob.id}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Status</label>
                      <div className="flex items-center mt-1">
                        {getStateIcon(selectedJob.state)}
                        <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${getStateColor(selectedJob.state)}`}>
                          {selectedJob.state.charAt(0).toUpperCase() + selectedJob.state.slice(1)}
                        </span>
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Progress</label>
                      <div className="flex items-center mt-1">
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-3 mr-3">
                          <div
                            className="bg-blue-600 h-3 rounded-full"
                            style={{ width: `${selectedJob.percent_complete}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {selectedJob.percent_complete.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Performance Metrics
                  </h3>
                  <div className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Items Completed</label>
                      <p className="text-sm text-gray-900 dark:text-white">
                        {selectedJob.items_completed} / {selectedJob.items_total}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Success Rate</label>
                      <p className="text-sm text-gray-900 dark:text-white">
                        {((selectedJob.items_completed / selectedJob.items_total) * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Processing Time</label>
                      <p className="text-sm text-gray-900 dark:text-white">
                        {formatDuration(selectedJob.time_processing_ms)}
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Average per Item</label>
                      <p className="text-sm text-gray-900 dark:text-white">
                        {formatDuration(selectedJob.average_duration_ms_per_item)}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {selectedJob.sheet_source && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Input Source
                  </h3>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Sheet ID</label>
                        <p className="text-sm text-gray-900 dark:text-white font-mono">
                          {selectedJob.sheet_source.sheet_id}
                        </p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Range</label>
                        <p className="text-sm text-gray-900 dark:text-white">
                          {selectedJob.sheet_source.range}
                        </p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Connected</label>
                        <p className="text-sm text-gray-900 dark:text-white">
                          {formatDate(selectedJob.sheet_source.connected_at)}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {selectedJob.artifacts && selectedJob.artifacts.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Artifacts
                  </h3>
                  <div className="space-y-2">
                    {selectedJob.artifacts.map((artifact, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                      >
                        <div className="flex items-center">
                          <FileText className="w-5 h-5 text-gray-400 mr-3" />
                          <div>
                            <p className="text-sm font-medium text-gray-900 dark:text-white">
                              {artifact.type}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {artifact.content_type} • {(artifact.size / 1024).toFixed(1)} KB
                            </p>
                          </div>
                        </div>
                        <a
                          href={artifact.url}
                          className="px-3 py-1 bg-blue-600 text-white text-xs rounded-md hover:bg-blue-700"
                        >
                          Download
                        </a>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}