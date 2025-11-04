import { useState, useEffect } from 'react';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Clock,
  Activity,
  Zap,
  Target,
  BarChart3,
  PieChart,
  Download,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Play,
  Pause
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
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from 'recharts';

interface CostData {
  date: string;
  totalCost: number;
  videoCost: number;
  processingCost: number;
  storageCost: number;
}

interface PerformanceData {
  date: string;
  avgProcessingTime: number;
  successRate: number;
  throughput: number;
  errorRate: number;
}

interface BulkOperationMetrics {
  totalJobs: number;
  totalVideos: number;
  totalCost: number;
  avgCostPerVideo: number;
  successRate: number;
  avgProcessingTime: number;
  totalProcessingTime: number;
  peakConcurrency: number;
  costSavings: number;
}

interface CostBreakdown {
  category: string;
  amount: number;
  percentage: number;
  color: string;
}

interface TimeSeriesData {
  name: string;
  value: number;
  change?: number;
}

interface AnalyticsDashboardProps {
  timeframe?: string;
  showBulkOperations?: boolean;
}

export default function AnalyticsDashboard({ 
  timeframe = '30d', 
  showBulkOperations = true 
}: AnalyticsDashboardProps) {
  const [loading, setLoading] = useState(true);
  const [costData, setCostData] = useState<CostData[]>([]);
  const [performanceData, setPerformanceData] = useState<PerformanceData[]>([]);
  const [metrics, setMetrics] = useState<BulkOperationMetrics | null>(null);
  const [costBreakdown, setCostBreakdown] = useState<CostBreakdown[]>([]);

  useEffect(() => {
    loadAnalyticsData();
  }, [timeframe]);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      
      // Mock data for cost analysis
      const mockCostData: CostData[] = [
        { date: 'Mon', totalCost: 45.60, videoCost: 28.50, processingCost: 12.10, storageCost: 5.00 },
        { date: 'Tue', totalCost: 68.40, videoCost: 42.80, processingCost: 18.60, storageCost: 7.00 },
        { date: 'Wed', totalCost: 34.20, videoCost: 21.40, processingCost: 9.80, storageCost: 3.00 },
        { date: 'Thu', totalCost: 85.50, videoCost: 53.40, processingCost: 24.10, storageCost: 8.00 },
        { date: 'Fri', totalCost: 102.60, videoCost: 64.20, processingCost: 28.40, storageCost: 10.00 },
        { date: 'Sat', totalCost: 57.00, videoCost: 35.60, processingCost: 15.80, storageCost: 5.60 },
        { date: 'Sun', totalCost: 39.90, videoCost: 24.90, processingCost: 11.10, storageCost: 3.90 }
      ];

      // Mock data for performance metrics
      const mockPerformanceData: PerformanceData[] = [
        { date: 'Mon', avgProcessingTime: 2.3, successRate: 94.2, throughput: 156, errorRate: 5.8 },
        { date: 'Tue', avgProcessingTime: 2.1, successRate: 95.8, throughput: 168, errorRate: 4.2 },
        { date: 'Wed', avgProcessingTime: 2.5, successRate: 93.1, throughput: 142, errorRate: 6.9 },
        { date: 'Thu', avgProcessingTime: 2.0, successRate: 96.4, throughput: 184, errorRate: 3.6 },
        { date: 'Fri', avgProcessingTime: 1.9, successRate: 97.1, throughput: 201, errorRate: 2.9 },
        { date: 'Sat', avgProcessingTime: 2.2, successRate: 94.7, throughput: 163, errorRate: 5.3 },
        { date: 'Sun', avgProcessingTime: 2.4, successRate: 92.8, throughput: 147, errorRate: 7.2 }
      ];

      // Mock bulk operation metrics
      const mockMetrics: BulkOperationMetrics = {
        totalJobs: 47,
        totalVideos: 8940,
        totalCost: 1247.50,
        avgCostPerVideo: 0.139,
        successRate: 94.8,
        avgProcessingTime: 2.15,
        totalProcessingTime: 19226, // minutes
        peakConcurrency: 12,
        costSavings: 18.3 // percentage
      };

      // Cost breakdown
      const mockCostBreakdown: CostBreakdown[] = [
        { category: 'Video Generation', amount: 780.20, percentage: 62.5, color: '#3B82F6' },
        { category: 'Processing', amount: 280.60, percentage: 22.5, color: '#10B981' },
        { category: 'Storage', amount: 124.80, percentage: 10.0, color: '#F59E0B' },
        { category: 'API Calls', amount: 61.90, percentage: 5.0, color: '#EF4444' }
      ];

      setCostData(mockCostData);
      setPerformanceData(mockPerformanceData);
      setMetrics(mockMetrics);
      setCostBreakdown(mockCostBreakdown);
    } catch (error) {
      console.error('Failed to load analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatPercentage = (value: number, decimals = 1) => {
    return `${value.toFixed(decimals)}%`;
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

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
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Cost & Performance Analytics</h2>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Detailed analysis of bulk operations cost and performance metrics
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={loadAnalyticsData}
            className="px-3 py-2 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors flex items-center text-sm"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
          <button className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center text-sm">
            <Download className="w-4 h-4 mr-2" />
            Export Report
          </button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Cost</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {formatCurrency(metrics?.totalCost || 0)}
              </p>
              <p className="text-sm text-green-600 dark:text-green-400 flex items-center mt-1">
                <TrendingDown className="w-3 h-3 mr-1" />
                -8.2% vs last period
              </p>
            </div>
            <div className="p-3 rounded-lg bg-green-100 dark:bg-green-900/30">
              <DollarSign className="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Success Rate</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {formatPercentage(metrics?.successRate || 0)}
              </p>
              <p className="text-sm text-green-600 dark:text-green-400 flex items-center mt-1">
                <TrendingUp className="w-3 h-3 mr-1" />
                +2.1% vs last period
              </p>
            </div>
            <div className="p-3 rounded-lg bg-blue-100 dark:bg-blue-900/30">
              <Target className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Avg Processing Time</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {formatDuration((metrics?.avgProcessingTime || 0) * 60)}
              </p>
              <p className="text-sm text-green-600 dark:text-green-400 flex items-center mt-1">
                <TrendingDown className="w-3 h-3 mr-1" />
                -12% vs last period
              </p>
            </div>
            <div className="p-3 rounded-lg bg-purple-100 dark:bg-purple-900/30">
              <Clock className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Cost per Video</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {formatCurrency(metrics?.avgCostPerVideo || 0)}
              </p>
              <p className="text-sm text-green-600 dark:text-green-400 flex items-center mt-1">
                <TrendingDown className="w-3 h-3 mr-1" />
                -5.3% vs last period
              </p>
            </div>
            <div className="p-3 rounded-lg bg-orange-100 dark:bg-orange-900/30">
              <BarChart3 className="w-6 h-6 text-orange-600 dark:text-orange-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Cost Analysis Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Daily Cost Trends
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={costData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
              <XAxis dataKey="date" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" tickFormatter={(value) => `$${value}`} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                }}
                formatter={(value: number) => [formatCurrency(value), '']}
              />
              <Area
                type="monotone"
                dataKey="totalCost"
                stroke="#3B82F6"
                fill="#3B82F6"
                fillOpacity={0.2}
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Cost Breakdown
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <RechartsPieChart>
              <Pie
                data={costBreakdown}
                cx="50%"
                cy="50%"
                outerRadius={80}
                fill="#8884d8"
                dataKey="amount"
                label={({ category, percentage }) => `${category}: ${percentage}%`}
              >
                {costBreakdown.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                }}
                formatter={(value: number) => [formatCurrency(value), 'Cost']}
              />
            </RechartsPieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Processing Time Trends
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
              <XAxis dataKey="date" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" tickFormatter={(value) => `${value}h`} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                }}
                formatter={(value: number) => [`${value}h`, 'Avg Processing Time']}
              />
              <Line
                type="monotone"
                dataKey="avgProcessingTime"
                stroke="#10B981"
                strokeWidth={2}
                dot={{ fill: '#10B981', r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Success Rate vs Error Rate
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
              <XAxis dataKey="date" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" tickFormatter={(value) => `${value}%`} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                }}
                formatter={(value: number) => [`${value}%`, '']}
              />
              <Line
                type="monotone"
                dataKey="successRate"
                stroke="#10B981"
                strokeWidth={2}
                dot={{ fill: '#10B981', r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="errorRate"
                stroke="#EF4444"
                strokeWidth={2}
                dot={{ fill: '#EF4444', r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Throughput Analysis */}
      <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Daily Throughput
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={performanceData}>
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
              formatter={(value: number) => [value, 'Videos Processed']}
            />
            <Bar dataKey="throughput" fill="#8B5CF6" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Bulk Operations Summary */}
      {showBulkOperations && metrics && (
        <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
            Bulk Operations Summary
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="p-3 rounded-lg bg-blue-100 dark:bg-blue-900/30 w-fit mx-auto mb-3">
                <Activity className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {metrics.totalJobs}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Jobs</p>
            </div>

            <div className="text-center">
              <div className="p-3 rounded-lg bg-green-100 dark:bg-green-900/30 w-fit mx-auto mb-3">
                <Zap className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {metrics.totalVideos.toLocaleString()}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Videos Generated</p>
            </div>

            <div className="text-center">
              <div className="p-3 rounded-lg bg-purple-100 dark:bg-purple-900/30 w-fit mx-auto mb-3">
                <Clock className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {formatDuration(metrics.totalProcessingTime)}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Processing Time</p>
            </div>

            <div className="text-center">
              <div className="p-3 rounded-lg bg-orange-100 dark:bg-orange-900/30 w-fit mx-auto mb-3">
                <TrendingUp className="w-6 h-6 text-orange-600 dark:text-orange-400" />
              </div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {metrics.peakConcurrency}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Peak Concurrency</p>
            </div>
          </div>

          <div className="mt-6 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <div className="flex items-center">
              <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 mr-2" />
              <span className="text-sm font-medium text-green-800 dark:text-green-200">
                Cost Optimization: You've saved {metrics.costSavings}% compared to individual processing
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Cost Optimization Insights */}
      <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-800">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Cost Optimization Insights
        </h3>
        <div className="space-y-4">
          <div className="flex items-start space-x-3 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <TrendingUp className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
                Peak Performance Hours
              </p>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                Processing during off-peak hours (11 PM - 6 AM) can reduce costs by up to 15%
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-green-800 dark:text-green-200">
                Batch Size Optimization
              </p>
              <p className="text-sm text-green-700 dark:text-green-300">
                Your current batch sizes are optimal. Consider 500-1000 items per job for best cost efficiency
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                Storage Optimization
              </p>
              <p className="text-sm text-yellow-700 dark:text-yellow-300">
                Consider implementing automated cleanup for completed jobs to reduce storage costs
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}