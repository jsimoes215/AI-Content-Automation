import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, RefreshCw, FileSpreadsheet, BarChart3, Clock, AlertCircle, Eye } from 'lucide-react';
import apiClient from '../lib/api';
import BulkJobCard from '../components/BulkJobCard';
import BulkJobCreator from '../components/BulkJobCreator';

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

interface BulkJobsResponse {
  data: BulkJob[];
  page: {
    next_page_token?: string;
    page_size: number;
  };
}

export default function BulkJobs() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<BulkJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showCreator, setShowCreator] = useState(false);
  const [selectedJob, setSelectedJob] = useState<BulkJob | null>(null);
  const [showJobDetails, setShowJobDetails] = useState(false);
  
  // Filters and search
  const [searchQuery, setSearchQuery] = useState('');
  const [filterState, setFilterState] = useState<string>('');
  const [sortBy, setSortBy] = useState<'created_at' | 'updated_at' | 'percent_complete'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [pageToken, setPageToken] = useState<string>('');

  // Analytics
  const [analytics, setAnalytics] = useState({
    total_jobs: 0,
    running_jobs: 0,
    completed_jobs: 0,
    failed_jobs: 0,
    total_items: 0,
    avg_completion_time: 0,
  });

  useEffect(() => {
    loadJobs();
    loadAnalytics();
  }, [filterState, sortBy, sortOrder, pageToken]);

  const loadJobs = async () => {
    try {
      setLoading(true);
      const params: any = {
        page_size: 20,
        sort: sortBy,
        order: sortOrder,
      };
      
      if (filterState) {
        params.state = [filterState];
      }
      
      if (pageToken) {
        params.page_token = pageToken;
      }

      const response = await apiClient.listBulkJobs(params);
      const jobsData = response.data;
      
      if (pageToken) {
        setJobs(prev => [...prev, ...jobsData]);
      } else {
        setJobs(jobsData);
      }
      
      // Update page token for pagination
      if (response.page.next_page_token) {
        setPageToken(response.page.next_page_token);
      } else {
        setPageToken('');
      }
    } catch (error) {
      console.error('Failed to load bulk jobs:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const loadAnalytics = async () => {
    try {
      // Calculate analytics from current jobs data
      const jobStats = {
        total_jobs: jobs.length,
        running_jobs: jobs.filter(j => ['pending', 'running', 'pausing', 'paused', 'completing'].includes(j.state)).length,
        completed_jobs: jobs.filter(j => j.state === 'completed').length,
        failed_jobs: jobs.filter(j => j.state === 'failed').length,
        total_items: jobs.reduce((sum, job) => sum + job.items_total, 0),
        avg_completion_time: jobs
          .filter(j => j.state === 'completed' && j.average_duration_ms_per_item)
          .reduce((sum, job, _, arr) => sum + (job.average_duration_ms_per_item || 0) / arr.length, 0),
      };
      setAnalytics(jobStats);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    setPageToken('');
    loadJobs();
    loadAnalytics();
  };

  const handleJobCreated = (newJob: BulkJob) => {
    setJobs(prev => [newJob, ...prev]);
    loadAnalytics();
  };

  const handleViewDetails = (job: BulkJob) => {
    setSelectedJob(job);
    setShowJobDetails(true);
  };

  const handleViewProgress = (job: BulkJob) => {
    navigate(`/bulk-jobs/${job.id}`);
  };

  const filteredJobs = jobs.filter(job => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      job.id.toLowerCase().includes(query) ||
      job.sheet_source?.sheet_id.toLowerCase().includes(query) ||
      job.sheet_source?.range.toLowerCase().includes(query) ||
      job.callback_url?.toLowerCase().includes(query)
    );
  });

  const loadMore = () => {
    if (pageToken && !loading) {
      loadJobs();
    }
  };

  const formatDuration = (ms: number) => {
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

  const stats = [
    {
      label: 'Total Jobs',
      value: analytics.total_jobs,
      icon: FileSpreadsheet,
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    },
    {
      label: 'Running',
      value: analytics.running_jobs,
      icon: Clock,
      color: 'text-yellow-600 dark:text-yellow-400',
      bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
    },
    {
      label: 'Completed',
      value: analytics.completed_jobs,
      icon: BarChart3,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
    },
    {
      label: 'Failed',
      value: analytics.failed_jobs,
      icon: AlertCircle,
      color: 'text-red-600 dark:text-red-400',
      bgColor: 'bg-red-100 dark:bg-red-900/30',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Bulk Jobs</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Manage and monitor bulk content generation jobs
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center px-4 py-2 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => setShowCreator(true)}
            className="flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg"
          >
            <Plus className="w-5 h-5 mr-2" />
            Create Bulk Job
          </button>
        </div>
      </div>

      {/* Analytics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div
              key={index}
              className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    {stat.label}
                  </p>
                  <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                    {stat.value}
                  </p>
                </div>
                <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                  <Icon className={`w-6 h-6 ${stat.color}`} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Filters and Search */}
      <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search jobs by ID, sheet, or URL..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <select
            value={filterState}
            onChange={(e) => setFilterState(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [field, order] = e.target.value.split('-');
              setSortBy(field as any);
              setSortOrder(order as any);
            }}
            className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="created_at-desc">Newest First</option>
            <option value="created_at-asc">Oldest First</option>
            <option value="updated_at-desc">Recently Updated</option>
            <option value="percent_complete-desc">Most Complete</option>
          </select>
        </div>
      </div>

      {/* Jobs List */}
      {loading && jobs.length === 0 ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : filteredJobs.length > 0 ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredJobs.map((job) => (
              <div key={job.id} className="relative">
                <BulkJobCard
                  job={job}
                  onViewDetails={handleViewDetails}
                  onRefresh={handleRefresh}
                />
                <div className="absolute top-4 right-4">
                  <button
                    onClick={() => handleViewProgress(job)}
                    className="flex items-center px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <Eye className="w-4 h-4 mr-1" />
                    Live Progress
                  </button>
                </div>
              </div>
            ))}
          </div>
          
          {/* Load More */}
          {pageToken && (
            <div className="text-center">
              <button
                onClick={loadMore}
                disabled={loading}
                className="px-6 py-3 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
              >
                {loading ? 'Loading...' : 'Load More'}
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-12 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
          <FileSpreadsheet className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-600 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No bulk jobs found
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            {searchQuery || filterState 
              ? 'No jobs match your current filters.'
              : 'Get started by creating your first bulk job.'
            }
          </p>
          <button
            onClick={() => setShowCreator(true)}
            className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all"
          >
            <Plus className="w-5 h-5 mr-2" />
            Create Bulk Job
          </button>
        </div>
      )}

      {/* Creator Modal */}
      <BulkJobCreator
        isOpen={showCreator}
        onClose={() => setShowCreator(false)}
        onJobCreated={handleJobCreated}
      />

      {/* Job Details Modal */}
      {showJobDetails && selectedJob && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 rounded-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden shadow-2xl">
            {/* Job Details Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-800">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Job Details
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                  {selectedJob.id}
                </p>
              </div>
              <button
                onClick={() => setShowJobDetails(false)}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              >
                <Plus className="w-6 h-6 rotate-45" />
              </button>
            </div>

            {/* Job Details Content */}
            <div className="p-6 max-h-[70vh] overflow-y-auto space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Status & Progress
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">State:</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {selectedJob.state}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Progress:</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {selectedJob.percent_complete.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Items:</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {selectedJob.items_completed}/{selectedJob.items_total}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Failed:</span>
                      <span className="font-medium text-red-600 dark:text-red-400">
                        {selectedJob.items_failed}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Timing
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Created:</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {new Date(selectedJob.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Updated:</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {new Date(selectedJob.updated_at).toLocaleString()}
                      </span>
                    </div>
                    {selectedJob.eta_ms && (
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">ETA:</span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {formatDuration(selectedJob.eta_ms)}
                        </span>
                      </div>
                    )}
                    {selectedJob.average_duration_ms_per_item && (
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Avg Duration:</span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {formatDuration(selectedJob.average_duration_ms_per_item)}/item
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Sheet Source */}
              {selectedJob.sheet_source && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Sheet Source
                  </h3>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Sheet ID:</span>
                      <span className="font-mono text-sm text-gray-900 dark:text-white">
                        {selectedJob.sheet_source.sheet_id}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Range:</span>
                      <span className="font-mono text-sm text-gray-900 dark:text-white">
                        {selectedJob.sheet_source.range}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Connected:</span>
                      <span className="text-sm text-gray-900 dark:text-white">
                        {new Date(selectedJob.sheet_source.connected_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Artifacts */}
              {selectedJob.artifacts && selectedJob.artifacts.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Artifacts
                  </h3>
                  <div className="space-y-3">
                    {selectedJob.artifacts.map((artifact, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                      >
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            {artifact.type}
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {artifact.content_type} • {(artifact.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                        <button className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
                          Download
                        </button>
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
