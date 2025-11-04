import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Slider } from './ui/slider';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { 
  Settings, 
  Zap, 
  DollarSign, 
  Clock, 
  TrendingUp, 
  Database,
  AlertCircle,
  CheckCircle,
  BarChart3
} from 'lucide-react';

interface BatchingConfig {
  maxBatchSize: number;
  maxBatchCost: number;
  maxBatchDuration: number;
  similarityThreshold: number;
  costOptimization: boolean;
  dynamicSizing: boolean;
  cacheEnabled: boolean;
  priorityWeights: {
    urgency: number;
    cost: number;
    waitTime: number;
    errorRisk: number;
  };
  rateLimiting: {
    maxRequests: number;
    timeWindow: number;
    enabled: boolean;
  };
  budget: {
    monthlyBudget: number;
    budgetThreshold: number;
    alertEnabled: boolean;
  };
}

interface BatchingMetrics {
  totalRequests: number;
  batchedRequests: number;
  cachedRequests: number;
  totalCostSaved: number;
  averageBatchSize: number;
  cacheHitRatio: number;
  batchingEfficiency: number;
  activeBatches: number;
  queueSize: number;
}

const defaultConfig: BatchingConfig = {
  maxBatchSize: 25,
  maxBatchCost: 500.0,
  maxBatchDuration: 1800.0, // 30 minutes
  similarityThreshold: 0.7,
  costOptimization: true,
  dynamicSizing: true,
  cacheEnabled: true,
  priorityWeights: {
    urgency: 0.4,
    cost: 0.25,
    waitTime: 0.2,
    errorRisk: 0.15,
  },
  rateLimiting: {
    maxRequests: 10,
    timeWindow: 60,
    enabled: true,
  },
  budget: {
    monthlyBudget: 10000.0,
    budgetThreshold: 0.8,
    alertEnabled: true,
  },
};

export default function SmartBatchingSettings() {
  const [config, setConfig] = useState<BatchingConfig>(defaultConfig);
  const [metrics, setMetrics] = useState<BatchingMetrics>({
    totalRequests: 0,
    batchedRequests: 0,
    cachedRequests: 0,
    totalCostSaved: 0,
    averageBatchSize: 0,
    cacheHitRatio: 0,
    batchingEfficiency: 0,
    activeBatches: 0,
    queueSize: 0,
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadConfiguration();
    loadMetrics();
  }, []);

  const loadConfiguration = async () => {
    try {
      setLoading(true);
      // Simulate API call - would fetch from backend
      await new Promise(resolve => setTimeout(resolve, 500));
      setConfig(defaultConfig);
    } catch (error) {
      console.error('Failed to load batching configuration:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMetrics = async () => {
    try {
      // Simulate API call - would fetch from backend
      await new Promise(resolve => setTimeout(resolve, 300));
      setMetrics({
        totalRequests: 1250,
        batchedRequests: 980,
        cachedRequests: 420,
        totalCostSaved: 2350.75,
        averageBatchSize: 18.5,
        cacheHitRatio: 0.33,
        batchingEfficiency: 0.78,
        activeBatches: 3,
        queueSize: 12,
      });
    } catch (error) {
      console.error('Failed to load metrics:', error);
    }
  };

  const saveConfiguration = async () => {
    try {
      setSaving(true);
      // Simulate API call - would save to backend
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log('Saving configuration:', config);
    } catch (error) {
      console.error('Failed to save configuration:', error);
    } finally {
      setSaving(false);
    }
  };

  const updateConfig = (path: string, value: any) => {
    setConfig(prev => {
      const newConfig = { ...prev };
      const keys = path.split('.');
      let current: any = newConfig;
      
      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }
      current[keys[keys.length - 1]] = value;
      
      return newConfig;
    });
  };

  const getConfigStatus = (key: string, value: any) => {
    // Add validation logic
    switch (key) {
      case 'maxBatchSize':
        return value >= 1 && value <= 100 ? 'success' : 'error';
      case 'maxBatchCost':
        return value > 0 && value <= 10000 ? 'success' : 'error';
      case 'similarityThreshold':
        return value >= 0 && value <= 1 ? 'success' : 'error';
      default:
        return 'success';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return null;
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
            Smart Batching Settings
          </h2>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Configure intelligent batching algorithms to optimize costs and performance
          </p>
        </div>
        <Button 
          onClick={saveConfiguration} 
          disabled={saving}
          className="flex items-center gap-2"
        >
          <Settings className="h-4 w-4" />
          {saving ? 'Saving...' : 'Save Configuration'}
        </Button>
      </div>

      {/* Performance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Total Requests
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {metrics.totalRequests.toLocaleString()}
                </p>
              </div>
              <BarChart3 className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Cost Saved
                </p>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(metrics.totalCostSaved)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Cache Hit Rate
                </p>
                <p className="text-2xl font-bold text-purple-600">
                  {formatPercentage(metrics.cacheHitRatio)}
                </p>
              </div>
              <Database className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Active Batches
                </p>
                <p className="text-2xl font-bold text-orange-600">
                  {metrics.activeBatches}
                </p>
              </div>
              <Zap className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="batch" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="batch">Batch Settings</TabsTrigger>
          <TabsTrigger value="priority">Priority Queue</TabsTrigger>
          <TabsTrigger value="cache">Cache Strategy</TabsTrigger>
          <TabsTrigger value="rate">Rate Limiting</TabsTrigger>
          <TabsTrigger value="budget">Budget Control</TabsTrigger>
        </TabsList>

        <TabsContent value="batch" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Batch Processing Configuration
              </CardTitle>
              <CardDescription>
                Configure batch size limits and similarity thresholds
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="maxBatchSize">Max Batch Size</Label>
                  <div className="flex items-center gap-2">
                    <Input
                      id="maxBatchSize"
                      type="number"
                      min="1"
                      max="100"
                      value={config.maxBatchSize}
                      onChange={(e) => updateConfig('maxBatchSize', parseInt(e.target.value))}
                    />
                    {getStatusIcon(getConfigStatus('maxBatchSize', config.maxBatchSize))}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Maximum number of requests per batch
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="maxBatchCost">Max Batch Cost ($)</Label>
                  <div className="flex items-center gap-2">
                    <Input
                      id="maxBatchCost"
                      type="number"
                      min="1"
                      max="10000"
                      step="0.01"
                      value={config.maxBatchCost}
                      onChange={(e) => updateConfig('maxBatchCost', parseFloat(e.target.value))}
                    />
                    {getStatusIcon(getConfigStatus('maxBatchCost', config.maxBatchCost))}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Maximum estimated cost per batch
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="maxBatchDuration">Max Batch Duration (seconds)</Label>
                  <Input
                    id="maxBatchDuration"
                    type="number"
                    min="60"
                    max="3600"
                    value={config.maxBatchDuration}
                    onChange={(e) => updateConfig('maxBatchDuration', parseInt(e.target.value))}
                  />
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Maximum time budget for batch processing
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>Similarity Threshold</Label>
                  <div className="space-y-2">
                    <Slider
                      value={[config.similarityThreshold]}
                      onValueChange={(value) => updateConfig('similarityThreshold', value[0])}
                      max={1}
                      min={0}
                      step={0.05}
                      className="w-full"
                    />
                    <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                      <span>0</span>
                      <span className="font-medium">{config.similarityThreshold.toFixed(2)}</span>
                      <span>1</span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Minimum similarity score for batch inclusion
                  </p>
                </div>
              </div>

              <Separator />

              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Dynamic Batch Sizing</Label>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Automatically adjust batch sizes based on performance
                    </p>
                  </div>
                  <Switch
                    checked={config.dynamicSizing}
                    onCheckedChange={(checked) => updateConfig('dynamicSizing', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>Cost Optimization</Label>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Prioritize cost reduction in batch decisions
                    </p>
                  </div>
                  <Switch
                    checked={config.costOptimization}
                    onCheckedChange={(checked) => updateConfig('costOptimization', checked)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="priority" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Priority Queue Weights
              </CardTitle>
              <CardDescription>
                Configure how requests are prioritized in the processing queue
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>Urgency Weight</Label>
                  <div className="space-y-2">
                    <Slider
                      value={[config.priorityWeights.urgency]}
                      onValueChange={(value) => updateConfig('priorityWeights.urgency', value[0])}
                      max={1}
                      min={0}
                      step={0.05}
                      className="w-full"
                    />
                    <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                      <span>0</span>
                      <span className="font-medium">{config.priorityWeights.urgency.toFixed(2)}</span>
                      <span>1</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Cost Weight</Label>
                  <div className="space-y-2">
                    <Slider
                      value={[config.priorityWeights.cost]}
                      onValueChange={(value) => updateConfig('priorityWeights.cost', value[0])}
                      max={1}
                      min={0}
                      step={0.05}
                      className="w-full"
                    />
                    <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                      <span>0</span>
                      <span className="font-medium">{config.priorityWeights.cost.toFixed(2)}</span>
                      <span>1</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Wait Time Weight</Label>
                  <div className="space-y-2">
                    <Slider
                      value={[config.priorityWeights.waitTime]}
                      onValueChange={(value) => updateConfig('priorityWeights.waitTime', value[0])}
                      max={1}
                      min={0}
                      step={0.05}
                      className="w-full"
                    />
                    <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                      <span>0</span>
                      <span className="font-medium">{config.priorityWeights.waitTime.toFixed(2)}</span>
                      <span>1</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Error Risk Weight</Label>
                  <div className="space-y-2">
                    <Slider
                      value={[config.priorityWeights.errorRisk]}
                      onValueChange={(value) => updateConfig('priorityWeights.errorRisk', value[0])}
                      max={1}
                      min={0}
                      step={0.05}
                      className="w-full"
                    />
                    <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                      <span>0</span>
                      <span className="font-medium">{config.priorityWeights.errorRisk.toFixed(2)}</span>
                      <span>1</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
                  Current Configuration
                </h4>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(config.priorityWeights).map(([key, value]) => (
                    <Badge key={key} variant="secondary">
                      {key}: {value.toFixed(2)}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="cache" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Cache Strategy
              </CardTitle>
              <CardDescription>
                Configure multi-layer caching for content reuse
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Enable Caching</Label>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Enable multi-layer content caching
                  </p>
                </div>
                <Switch
                  checked={config.cacheEnabled}
                  onCheckedChange={(checked) => updateConfig('cacheEnabled', checked)}
                />
              </div>

              {config.cacheEnabled && (
                <div className="space-y-4">
                  <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                    <h4 className="font-medium mb-3">Cache Performance</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center">
                        <p className="text-2xl font-bold text-purple-600">
                          {formatPercentage(metrics.cacheHitRatio)}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Hit Rate</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-green-600">
                          {formatCurrency(metrics.totalCostSaved * 0.4)}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Cache Savings</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-blue-600">
                          {metrics.cachedRequests}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Cached Items</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="rate" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Rate Limiting
              </CardTitle>
              <CardDescription>
                Configure API rate limiting to respect provider limits
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Enable Rate Limiting</Label>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Control request rate to avoid provider limits
                  </p>
                </div>
                <Switch
                  checked={config.rateLimiting.enabled}
                  onCheckedChange={(checked) => updateConfig('rateLimiting.enabled', checked)}
                />
              </div>

              {config.rateLimiting.enabled && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="maxRequests">Max Requests</Label>
                    <Input
                      id="maxRequests"
                      type="number"
                      min="1"
                      max="100"
                      value={config.rateLimiting.maxRequests}
                      onChange={(e) => updateConfig('rateLimiting.maxRequests', parseInt(e.target.value))}
                    />
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Maximum requests per time window
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="timeWindow">Time Window (seconds)</Label>
                    <Input
                      id="timeWindow"
                      type="number"
                      min="10"
                      max="3600"
                      value={config.rateLimiting.timeWindow}
                      onChange={(e) => updateConfig('rateLimiting.timeWindow', parseInt(e.target.value))}
                    />
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Time window for rate limiting
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="budget" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5" />
                Budget Control
              </CardTitle>
              <CardDescription>
                Configure budget limits and alerting thresholds
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="monthlyBudget">Monthly Budget ($)</Label>
                  <Input
                    id="monthlyBudget"
                    type="number"
                    min="100"
                    max="100000"
                    step="0.01"
                    value={config.budget.monthlyBudget}
                    onChange={(e) => updateConfig('budget.monthlyBudget', parseFloat(e.target.value))}
                  />
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Monthly spending limit
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>Alert Threshold</Label>
                  <div className="space-y-2">
                    <Slider
                      value={[config.budget.budgetThreshold]}
                      onValueChange={(value) => updateConfig('budget.budgetThreshold', value[0])}
                      max={1}
                      min={0}
                      step={0.05}
                      className="w-full"
                    />
                    <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                      <span>0%</span>
                      <span className="font-medium">{formatPercentage(config.budget.budgetThreshold)}</span>
                      <span>100%</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Budget Alerts</Label>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Receive alerts when approaching budget limits
                  </p>
                </div>
                <Switch
                  checked={config.budget.alertEnabled}
                  onCheckedChange={(checked) => updateConfig('budget.alertEnabled', checked)}
                />
              </div>

              <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
                <h4 className="font-medium text-yellow-900 dark:text-yellow-100 mb-2">
                  Current Budget Status
                </h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Used: {formatCurrency(metrics.totalCostSaved * 2)}</span>
                    <span>Limit: {formatCurrency(config.budget.monthlyBudget)}</span>
                  </div>
                  <div className="w-full bg-yellow-200 dark:bg-yellow-800 rounded-full h-2">
                    <div 
                      className="bg-yellow-500 h-2 rounded-full transition-all"
                      style={{ width: '47%' }}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}