import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Calendar,
  Clock,
  Plus,
  PlayCircle,
  PauseCircle,
  RotateCcw,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  XCircle,
  Zap,
  BarChart3,
  Users,
  Globe,
  Filter,
  Search,
  RefreshCw,
  Settings,
  Target
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import apiClient from '../lib/api';
import PlatformRecommendations from '../components/PlatformRecommendations';
import TimingChart from '../components/TimingChart';

interface ScheduledItem {
  id: string;
  content_id: string;
  platform: string;
  state: string;
  scheduled_time: string;
  published_time?: string;
  title?: string;
  engagement_rate?: number;
  views?: number;
  created_at: string;
  updated_at: string;
}

interface Schedule {
  id: string;
  tenant_id: string;
  state: string;
  title: string;
  timezone: string;
  percent_complete: number;
  items_total: number;
  items_completed: number;
  items_failed: number;
  items_skipped: number;
  items_canceled: number;
  items_pending: number;
  created_at: string;
  updated_at: string;
}

interface SchedulingAnalytics {
  total_schedules: number;
  active_schedules: number;
  completed_today: number;
  pending_posts: number;
  platform_breakdown: Record<string, number>;
  performance_metrics: {
    avg_engagement_rate: number;
    total_reach: number;
    success_rate: number;
  };
}

export default function SchedulingDashboard() {
  const navigate = useNavigate();
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [analytics, setAnalytics] = useState<SchedulingAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [filterPlatform, setFilterPlatform] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSchedule, setSelectedSchedule] = useState<Schedule | null>(null);
  const [realTimeUpdates, setRealTimeUpdates] = useState(true);

  // Mock data for charts - in production this would come from the API
  const scheduleActivityData = [
    { time: '00:00', posts: 2 },
    { time: '04:00', posts: 1 },
    { time: '08:00', posts: 5 },
    { time: '12:00', posts: 8 },
    { time: '16:00', posts: 12 },
    { time: '20:00', posts: 15 },
  ];

  const platformPerformance = [
    { platform: 'YouTube', scheduled: 25, completed: 23, engagement: 8.2 },
    { platform: 'TikTok', scheduled: 45, completed: 42, engagement: 12.8 },
    { platform: 'Instagram', scheduled: 38, completed: 35, engagement: 9.5 },
    { platform: 'LinkedIn', scheduled: 18, completed: 16, engagement: 5.3 },
    { platform: 'Twitter', scheduled: 32, completed: 29, engagement: 6.7 },
  ];

  const supportedPlatforms = [
    { id: 'youtube', name: 'YouTube', icon: '🎥' },
    { id: 'tiktok', name: 'TikTok', icon: '🎵' },
    { id: 'instagram', name: 'Instagram', icon: '📸' },
    { id: 'linkedin', name: 'LinkedIn', icon: '💼' },
    { id: 'twitter', name: 'Twitter/X', icon: '🐦' },
    { id: 'facebook', name: 'Facebook', icon: '📘' },
  ];

  useEffect(() => {
    loadSchedulingData();
    connectToRealTimeUpdates();
  }, []);

  const loadSchedulingData = async () => {
    try {
      setLoading(true);
      
      // Mock analytics data - in production, this would be from the API
      const mockAnalytics: SchedulingAnalytics = {
        total_schedules: 47,
        active_schedules: 12,
        completed_today: 156,
        pending_posts: 89,
        platform_breakdown: {
          youtube: 25,
          tiktok: 45,
          instagram: 38,
          linkedin: 18,
          twitter: 32,
          facebook: 20
        },
        performance_metrics: {
          avg_engagement_rate: 8.7,
          total_reach: 125000,
          success_rate: 94.8
        }
      };
      
      // Mock schedules data
      const mockSchedules: Schedule[] = [
        {
          id: '1',
          tenant_id: 'user1',
          state: 'running',
          title: 'Product Launch Campaign',
          timezone: 'UTC',
          percent_complete: 65.0,
          items_total: 20,
          items_completed: 13,
          items_failed: 1,
          items_skipped: 2,
          items_canceled: 0,
          items_pending: 4,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: '2',
          tenant_id: 'user1',
          state: 'completed',
          title: 'Weekly Content Batch',
          timezone: 'UTC',
          percent_complete: 100.0,
          items_total: 15,
          items_completed: 15,
          items_failed: 0,
          items_skipped: 0,
          items_canceled: 0,
          items_pending: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ];

      setAnalytics(mockAnalytics);
      setSchedules(mockSchedules);
    } catch (error) {
      console.error('Failed to load scheduling data:', error);
    } finally {
      setLoading(false);
    }
  };

  const connectToRealTimeUpdates = () => {
    if (!realTimeUpdates) return;

    // In a real implementation, this would connect to the scheduling WebSocket
    // apiClient.connectBulkJobWebSocket('scheduling', handleRealTimeUpdate);
    
    // Mock real-time updates
    const interval = setInterval(() => {
      if (realTimeUpdates) {
        // Simulate real-time updates
        loadSchedulingData();
      }
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  };

  const handleRealTimeUpdate = (data: any) => {
    if (data.type === 'schedule.updated' || data.type === 'optimization.completed') {
      loadSchedulingData();
    }
  };

  const getStatusColor = (state: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
      running: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
      completed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
      paused: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
      canceled: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
    };
    return colors[state] || colors.pending;
  };

  const getPlatformIcon = (platformId: string) => {
    const platform = supportedPlatforms.find(p => p.id === platformId);
    return platform?.icon || '📱';
  };

  const stats = [
    {
      label: 'Active Schedules',
      value: analytics?.active_schedules || 0,
      change: '+12%',
      trend: 'up',
      icon: Calendar,
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    },
    {
      label: 'Completed Today',
      value: analytics?.completed_today || 0,
      change: '+8%',
      trend: 'up',
      icon: CheckCircle,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
    },
    {
      label: 'Pending Posts',
      value: analytics?.pending_posts || 0,
      change: '-5%',
      trend: 'down',
      icon: Clock,
      color: 'text-orange-600 dark:text-orange-400',
      bgColor: 'bg-orange-100 dark:bg-orange-900/30',
    },
    {
      label: 'Success Rate',
      value: `${analytics?.performance_metrics.success_rate || 0}%`,
      change: '+2.1%',
      trend: 'up',
      icon: TrendingUp,
      color: 'text-purple-600 dark:text-purple-400',
      bgColor: 'bg-purple-100 dark:bg-purple-900/30',
    },
  ];

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'schedules', label: 'Schedules', icon: Calendar },
    { id: 'analytics', label: 'Performance', icon: TrendingUp },
    { id: 'recommendations', label: 'AI Recommendations', icon: Target },
    { id: 'optimization', label: 'Optimization', icon: Zap },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Scheduling Dashboard</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Manage and optimize your content scheduling across platforms
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setRealTimeUpdates(!realTimeUpdates)}
            className={`flex items-center px-4 py-2 rounded-lg font-medium transition-colors ${
              realTimeUpdates
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
            }`}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${realTimeUpdates ? 'animate-spin' : ''}`} />
            Real-time {realTimeUpdates ? 'ON' : 'OFF'}
          </button>
          <button
            onClick={() => navigate('/projects')}
            className="flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg"
          >
            <Plus className="w-5 h-5 mr-2" />
            New Schedule
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-800">
        <nav className="flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  isActive
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <Icon className="w-5 h-5 mr-2" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <div
                  key={index}
                  className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                      <Icon className={`w-6 h-6 ${stat.color}`} />
                    </div>
                    <span
                      className={`text-sm font-medium ${
                        stat.trend === 'up'
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}
                    >
                      {stat.change}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    {stat.label}
                  </p>
                  <p className="mt-1 text-3xl font-bold text-gray-900 dark:text-white">
                    {stat.value}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
                Schedule Activity
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={scheduleActivityData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
                  <XAxis dataKey="time" stroke="#9CA3AF" />
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
                    dataKey="posts"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    dot={{ fill: '#3B82F6', r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
                Platform Distribution
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={platformPerformance}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
                  <XAxis dataKey="platform" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F2937',
                      border: 'none',
                      borderRadius: '8px',
                      color: '#fff',
                    }}
                  />
                  <Bar dataKey="scheduled" fill="#8B5CF6" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Platform Performance */}
          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
              Platform Performance
            </h2>
            <div className="space-y-4">
              {platformPerformance.map((platform, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-800 rounded-lg"
                >
                  <div className="flex items-center gap-4">
                    <div className="text-2xl">{getPlatformIcon(platform.platform.toLowerCase())}</div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {platform.platform}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {platform.scheduled} scheduled • {platform.completed} completed
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Success Rate
                    </p>
                    <p className="text-lg font-bold text-gray-900 dark:text-white">
                      {Math.round((platform.completed / platform.scheduled) * 100)}%
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'schedules' && (
        <div className="space-y-6">
          {/* Filters and Search */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search schedules..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 w-full border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            <select
              value={filterPlatform}
              onChange={(e) => setFilterPlatform(e.target.value)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Platforms</option>
              {supportedPlatforms.map(platform => (
                <option key={platform.id} value={platform.id}>
                  {platform.name}
                </option>
              ))}
            </select>
            <button className="flex items-center px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800">
              <Filter className="w-4 h-4 mr-2" />
              Filters
            </button>
          </div>

          {/* Schedules List */}
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800">
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                Active Schedules
              </h2>
              {schedules.length > 0 ? (
                <div className="space-y-4">
                  {schedules.map((schedule) => (
                    <div
                      key={schedule.id}
                      className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-800 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                      onClick={() => setSelectedSchedule(schedule)}
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-medium text-gray-900 dark:text-white">
                            {schedule.title}
                          </h3>
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                              schedule.state
                            )}`}
                          >
                            {schedule.state}
                          </span>
                        </div>
                        <div className="flex items-center gap-6 text-sm text-gray-600 dark:text-gray-400">
                          <span>{schedule.items_total} items</span>
                          <span>{schedule.items_completed} completed</span>
                          <span>{schedule.items_failed} failed</span>
                          <span>{schedule.items_pending} pending</span>
                        </div>
                        <div className="mt-2">
                          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full transition-all"
                              style={{ width: `${schedule.percent_complete}%` }}
                            ></div>
                          </div>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            {schedule.percent_complete.toFixed(1)}% complete
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {schedule.state === 'running' && (
                          <button className="p-2 text-gray-400 hover:text-orange-600 transition-colors">
                            <PauseCircle className="w-5 h-5" />
                          </button>
                        )}
                        {schedule.state === 'paused' && (
                          <button className="p-2 text-gray-400 hover:text-green-600 transition-colors">
                            <PlayCircle className="w-5 h-5" />
                          </button>
                        )}
                        <button className="p-2 text-gray-400 hover:text-blue-600 transition-colors">
                          <RotateCcw className="w-5 h-5" />
                        </button>
                        <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
                          <Settings className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Calendar className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-600 mb-4" />
                  <p className="text-gray-600 dark:text-gray-400">No schedules found</p>
                  <button
                    onClick={() => navigate('/projects')}
                    className="mt-4 text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    Create your first schedule
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'analytics' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
              <div className="text-center">
                <TrendingUp className="w-12 h-12 text-green-600 dark:text-green-400 mx-auto mb-4" />
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {analytics?.performance_metrics.avg_engagement_rate}%
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Avg Engagement Rate</p>
                <p className="text-sm text-green-600 dark:text-green-400 mt-1">+2.1% improvement</p>
              </div>
            </div>
            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
              <div className="text-center">
                <Users className="w-12 h-12 text-blue-600 dark:text-blue-400 mx-auto mb-4" />
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {(analytics?.performance_metrics.total_reach || 0).toLocaleString()}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Reach</p>
                <p className="text-sm text-green-600 dark:text-green-400 mt-1">+15.3% growth</p>
              </div>
            </div>
            <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
              <div className="text-center">
                <Globe className="w-12 h-12 text-purple-600 dark:text-purple-400 mx-auto mb-4" />
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {analytics?.performance_metrics.success_rate}%
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Success Rate</p>
                <p className="text-sm text-green-600 dark:text-green-400 mt-1">+0.8% improvement</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
              Detailed Performance Analysis
            </h2>
            <div className="space-y-4">
              {platformPerformance.map((platform, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="flex items-center gap-4">
                    <span className="text-2xl">{getPlatformIcon(platform.platform.toLowerCase())}</span>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{platform.platform}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {platform.engagement}% engagement rate
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Completion Rate
                    </p>
                    <p className="text-lg font-bold text-gray-900 dark:text-white">
                      {Math.round((platform.completed / platform.scheduled) * 100)}%
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'recommendations' && (
        <PlatformRecommendations
          selectedPlatforms={['youtube', 'tiktok', 'instagram']}
          contentType="video"
          targetAudience="general"
          onTimeSlotSelect={(slot) => {
            console.log('Selected time slot:', slot);
            // Handle time slot selection
            // Could open a modal to create a schedule with this recommendation
          }}
        />
      )}

      {activeTab === 'optimization' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              AI-Powered Schedule Optimization
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Optimize your posting schedule based on audience behavior and platform analytics
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                <Zap className="w-8 h-8 text-yellow-500 mb-3" />
                <h3 className="font-medium text-gray-900 dark:text-white mb-2">
                  Smart Recommendations
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Get AI-powered suggestions for optimal posting times across platforms
                </p>
                <button className="mt-4 w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                  Get Recommendations
                </button>
              </div>
              
              <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                <BarChart3 className="w-8 h-8 text-green-500 mb-3" />
                <h3 className="font-medium text-gray-900 dark:text-white mb-2">
                  Performance Analysis
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Analyze historical performance to improve future scheduling
                </p>
                <button className="mt-4 w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
                  Analyze Performance
                </button>
              </div>
            </div>
            
            <div className="mt-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
              <div className="flex items-start">
                <AlertCircle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5 mr-3" />
                <div>
                  <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                    Optimization Benefits
                  </p>
                  <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                    Our AI optimization can increase engagement by up to 23% and reduce manual scheduling time by 67%.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Schedule Detail Modal */}
      {selectedSchedule && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                {selectedSchedule.title}
              </h2>
              <button
                onClick={() => setSelectedSchedule(null)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Status:</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(selectedSchedule.state)}`}>
                  {selectedSchedule.state}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-gray-600 dark:text-gray-400 text-sm">Total Items</span>
                  <p className="text-xl font-bold text-gray-900 dark:text-white">{selectedSchedule.items_total}</p>
                </div>
                <div>
                  <span className="text-gray-600 dark:text-gray-400 text-sm">Progress</span>
                  <p className="text-xl font-bold text-gray-900 dark:text-white">{selectedSchedule.percent_complete.toFixed(1)}%</p>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Completed</span>
                  <span className="text-green-600 dark:text-green-400">{selectedSchedule.items_completed}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Failed</span>
                  <span className="text-red-600 dark:text-red-400">{selectedSchedule.items_failed}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Pending</span>
                  <span className="text-orange-600 dark:text-orange-400">{selectedSchedule.items_pending}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}