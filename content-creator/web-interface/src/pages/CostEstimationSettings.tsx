import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import CostOptimizer from './components/CostOptimizer';
import SmartBatchingSettings from './components/SmartBatchingSettings';
import { 
  DollarSign, 
  Settings, 
  TrendingUp, 
  Zap,
  BarChart3,
  Target
} from 'lucide-react';

interface QuickStats {
  totalSavings: number;
  monthlyBudget: number;
  activeOptimizations: number;
  costEfficiency: number;
}

export default function CostEstimationSettings() {
  const [activeTab, setActiveTab] = useState('overview');

  // Mock data - would be fetched from backend
  const stats: QuickStats = {
    totalSavings: 4560.75,
    monthlyBudget: 10000,
    activeOptimizations: 12,
    costEfficiency: 0.78
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
            Cost Optimization Suite
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Comprehensive cost estimation and optimization tools for intelligent content generation
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Total Savings
                  </p>
                  <p className="text-3xl font-bold text-green-600">
                    {formatCurrency(stats.totalSavings)}
                  </p>
                  <p className="text-sm text-gray-500">
                    +15% from last month
                  </p>
                </div>
                <DollarSign className="h-12 w-12 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Monthly Budget
                  </p>
                  <p className="text-3xl font-bold text-blue-600">
                    {formatCurrency(stats.monthlyBudget)}
                  </p>
                  <p className="text-sm text-gray-500">
                    45% utilized
                  </p>
                </div>
                <Target className="h-12 w-12 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Active Optimizations
                  </p>
                  <p className="text-3xl font-bold text-purple-600">
                    {stats.activeOptimizations}
                  </p>
                  <p className="text-sm text-gray-500">
                    Running efficiently
                  </p>
                </div>
                <Zap className="h-12 w-12 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    Cost Efficiency
                  </p>
                  <p className="text-3xl font-bold text-orange-600">
                    {(stats.costEfficiency * 100).toFixed(0)}%
                  </p>
                  <p className="text-sm text-gray-500">
                    +8% improvement
                  </p>
                </div>
                <TrendingUp className="h-12 w-12 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="optimizer" className="flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              Cost Optimizer
            </TabsTrigger>
            <TabsTrigger value="batching" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Batching Settings
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                  <CardDescription>
                    Common optimization tasks
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <button
                    onClick={() => setActiveTab('optimizer')}
                    className="w-full p-4 text-left rounded-lg border-2 border-dashed border-gray-300 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <DollarSign className="h-6 w-6 text-blue-500" />
                      <div>
                        <h3 className="font-medium">Calculate Cost Estimate</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Estimate costs for new content generation
                        </p>
                      </div>
                    </div>
                  </button>
                  
                  <button
                    onClick={() => setActiveTab('batching')}
                    className="w-full p-4 text-left rounded-lg border-2 border-dashed border-gray-300 hover:border-purple-500 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <Settings className="h-6 w-6 text-purple-500" />
                      <div>
                        <h3 className="font-medium">Configure Batching</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Optimize batch processing settings
                        </p>
                      </div>
                    </div>
                  </button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>System Status</CardTitle>
                  <CardDescription>
                    Current optimization system health
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      <span className="font-medium">Smart Batching</span>
                    </div>
                    <span className="text-sm text-green-600">Active</span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      <span className="font-medium">Cache System</span>
                    </div>
                    <span className="text-sm text-green-600">Running</span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                      <span className="font-medium">Rate Limiter</span>
                    </div>
                    <span className="text-sm text-yellow-600">At 80%</span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      <span className="font-medium">Budget Monitor</span>
                    </div>
                    <span className="text-sm text-blue-600">Monitoring</span>
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Recent Optimizations</CardTitle>
                <CardDescription>
                  Latest cost optimization activities
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <div>
                        <p className="font-medium">Batch Processing Optimization</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Reduced batch size to improve efficiency
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-green-600">-15% cost</p>
                      <p className="text-xs text-gray-500">2 hours ago</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <div>
                        <p className="font-medium">Provider Switch</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Migrated to Runway for video content
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-blue-600">-22% cost</p>
                      <p className="text-xs text-gray-500">1 day ago</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                      <div>
                        <p className="font-medium">Cache Optimization</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Increased cache TTL for static content
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-purple-600">+30% hits</p>
                      <p className="text-xs text-gray-500">3 days ago</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="optimizer">
            <CostOptimizer />
          </TabsContent>

          <TabsContent value="batching">
            <SmartBatchingSettings />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}