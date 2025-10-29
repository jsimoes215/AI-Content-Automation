import { useState, useEffect } from 'react';
import {
  TrendingUp,
  Eye,
  ThumbsUp,
  MessageCircle,
  Share2,
  Calendar,
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import apiClient from '../lib/api';

interface Analytics {
  total_projects: number;
  status_breakdown: Record<string, number>;
}

export default function Analytics() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState('7d');

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getAnalyticsOverview();
      setAnalytics(response.data);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  // Mock data for charts - in production, this would come from the API
  const projectsOverTime = [
    { date: 'Mon', projects: 2 },
    { date: 'Tue', projects: 3 },
    { date: 'Wed', projects: 1 },
    { date: 'Thu', projects: 4 },
    { date: 'Fri', projects: 5 },
    { date: 'Sat', projects: 3 },
    { date: 'Sun', projects: 2 },
  ];

  const platformPerformance = [
    { platform: 'YouTube', views: 12500, engagement: 7.2 },
    { platform: 'TikTok', views: 45600, engagement: 12.8 },
    { platform: 'Instagram', views: 23400, engagement: 9.5 },
    { platform: 'LinkedIn', views: 8900, engagement: 5.3 },
  ];

  const stats = [
    {
      label: 'Total Views',
      value: '90.5K',
      change: '+12.5%',
      trend: 'up',
      icon: Eye,
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    },
    {
      label: 'Total Engagement',
      value: '8.7K',
      change: '+8.2%',
      trend: 'up',
      icon: ThumbsUp,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
    },
    {
      label: 'Total Comments',
      value: '2.1K',
      change: '+15.3%',
      trend: 'up',
      icon: MessageCircle,
      color: 'text-purple-600 dark:text-purple-400',
      bgColor: 'bg-purple-100 dark:bg-purple-900/30',
    },
    {
      label: 'Total Shares',
      value: '892',
      change: '+5.7%',
      trend: 'up',
      icon: Share2,
      color: 'text-orange-600 dark:text-orange-400',
      bgColor: 'bg-orange-100 dark:bg-orange-900/30',
    },
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
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Analytics</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Track your content performance across platforms
          </p>
        </div>
        <select
          value={timeframe}
          onChange={(e) => setTimeframe(e.target.value)}
          className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
          <option value="90d">Last 90 days</option>
          <option value="1y">Last year</option>
        </select>
      </div>

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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
            Projects Created
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={projectsOverTime}>
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
                dataKey="projects"
                stroke="#3B82F6"
                strokeWidth={2}
                dot={{ fill: '#3B82F6', r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
            Platform Performance
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
              <Bar dataKey="views" fill="#8B5CF6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
          Top Performing Content
        </h2>
        <div className="space-y-4">
          {platformPerformance.map((platform, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-800 rounded-lg"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {platform.platform}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {platform.views.toLocaleString()} views
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Engagement Rate
                </p>
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {platform.engagement}%
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {analytics && (
        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
            Project Status Breakdown
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.entries(analytics.status_breakdown).map(([status, count]) => (
              <div key={status} className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <p className="text-3xl font-bold text-gray-900 dark:text-white">{count}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 capitalize">
                  {status}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
