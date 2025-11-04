import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Slider } from './ui/slider';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Separator } from './ui/separator';
import { 
  DollarSign, 
  Calculator, 
  TrendingUp, 
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Target,
  Zap,
  Clock,
  Database,
  Lightbulb
} from 'lucide-react';

interface CostEstimate {
  contentType: 'video' | 'image' | 'audio';
  resolution: string;
  duration: number;
  engine: string;
  style: string;
  estimatedCost: number;
  costBreakdown: {
    baseCost: number;
    resolutionMultiplier: number;
    durationCost: number;
    enginePremium: number;
  };
  optimizations: {
    batchDiscount: number;
    cacheSavings: number;
    totalSavings: number;
  };
}

interface CostOptimization {
  enabled: boolean;
  targetReduction: number;
  currentSavings: number;
  monthlyBudget: number;
  projectedCosts: number;
  budgetVariance: number;
}

interface ProviderPricing {
  name: string;
  video: {
    sd: number;
    hd: number;
    fhd: number;
    '4k': number;
  };
  image: {
    basic: number;
    premium: number;
    ultra: number;
  };
  audio: {
    basic: number;
    premium: number;
    studio: number;
  };
}

const defaultProviders: ProviderPricing[] = [
  {
    name: 'Runway',
    video: { sd: 0.05, hd: 0.08, fhd: 0.12, '4k': 0.25 },
    image: { basic: 0.01, premium: 0.03, ultra: 0.05 },
    audio: { basic: 0.02, premium: 0.04, studio: 0.08 }
  },
  {
    name: 'OpenAI',
    video: { sd: 0.04, hd: 0.07, fhd: 0.10, '4k': 0.20 },
    image: { basic: 0.01, premium: 0.02, ultra: 0.04 },
    audio: { basic: 0.015, premium: 0.03, studio: 0.06 }
  },
  {
    name: 'Anthropic',
    video: { sd: 0.06, hd: 0.09, fhd: 0.15, '4k': 0.30 },
    image: { basic: 0.015, premium: 0.035, ultra: 0.06 },
    audio: { basic: 0.025, premium: 0.05, studio: 0.09 }
  }
];

const resolutionOptions = {
  video: [
    { value: '480x360', label: '480p SD', multiplier: 0.5 },
    { value: '1280x720', label: '720p HD', multiplier: 1.0 },
    { value: '1920x1080', label: '1080p FHD', multiplier: 1.5 },
    { value: '3840x2160', label: '4K UHD', multiplier: 3.0 }
  ],
  image: [
    { value: '512x512', label: '512x512 (Basic)', multiplier: 0.5 },
    { value: '1024x1024', label: '1024x1024 (Premium)', multiplier: 1.0 },
    { value: '2048x2048', label: '2048x2048 (Ultra)', multiplier: 2.0 }
  ]
};

const engineOptions = [
  { value: 'default', label: 'Standard', premium: 1.0 },
  { value: 'premium', label: 'Premium', premium: 1.5 },
  { value: 'professional', label: 'Professional', premium: 2.0 },
  { value: 'ultra', label: 'Ultra', premium: 3.0 }
];

export default function CostOptimizer() {
  const [estimate, setEstimate] = useState<CostEstimate>({
    contentType: 'video',
    resolution: '1920x1080',
    duration: 30,
    engine: 'default',
    style: 'realistic',
    estimatedCost: 0,
    costBreakdown: {
      baseCost: 0,
      resolutionMultiplier: 1,
      durationCost: 0,
      enginePremium: 1
    },
    optimizations: {
      batchDiscount: 0,
      cacheSavings: 0,
      totalSavings: 0
    }
  });

  const [optimization, setOptimization] = useState<CostOptimization>({
    enabled: true,
    targetReduction: 0.3,
    currentSavings: 0,
    monthlyBudget: 10000,
    projectedCosts: 0,
    budgetVariance: 0
  });

  const [selectedProvider, setSelectedProvider] = useState(0);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('estimate');

  useEffect(() => {
    calculateCost();
  }, [estimate, selectedProvider]);

  const calculateCost = () => {
    const provider = defaultProviders[selectedProvider];
    
    let baseCost = 0;
    let resolutionMultiplier = 1;
    
    if (estimate.contentType === 'video') {
      const resolution = estimate.resolution as keyof typeof provider.video;
      baseCost = provider.video[resolution] || 0.08;
      const resolutionOption = resolutionOptions.video.find(r => r.value === estimate.resolution);
      resolutionMultiplier = resolutionOption?.multiplier || 1.0;
    } else if (estimate.contentType === 'image') {
      const resolution = estimate.resolution as keyof typeof provider.image;
      baseCost = provider.image[resolution] || 0.02;
      const resolutionOption = resolutionOptions.image.find(r => r.value === estimate.resolution);
      resolutionMultiplier = resolutionOption?.multiplier || 1.0;
    } else {
      baseCost = provider.audio.basic;
    }
    
    const engine = engineOptions.find(e => e.value === estimate.engine);
    const enginePremium = engine?.premium || 1.0;
    
    const durationCost = estimate.contentType === 'image' ? 0 : baseCost * estimate.duration;
    const estimatedCost = baseCost * resolutionMultiplier * enginePremium * (estimate.contentType === 'image' ? 1 : estimate.duration);
    
    // Calculate optimizations
    const batchDiscount = optimization.enabled ? estimatedCost * 0.15 : 0;
    const cacheSavings = optimization.enabled ? estimatedCost * 0.1 : 0;
    const totalSavings = batchDiscount + cacheSavings;
    
    setEstimate(prev => ({
      ...prev,
      estimatedCost: estimatedCost - totalSavings,
      costBreakdown: {
        baseCost,
        resolutionMultiplier,
        durationCost,
        enginePremium
      },
      optimizations: {
        batchDiscount,
        cacheSavings,
        totalSavings
      }
    }));
    
    // Update optimization metrics
    setOptimization(prev => ({
      ...prev,
      currentSavings: totalSavings,
      projectedCosts: estimatedCost * 100, // Simulate monthly projection
      budgetVariance: (estimatedCost * 100) - prev.monthlyBudget
    }));
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 4
    }).format(amount);
  };

  const getOptimizationStatus = () => {
    const savings = optimization.currentSavings;
    const target = optimization.targetReduction * estimate.estimatedCost;
    
    if (savings >= target) {
      return { status: 'success', message: 'Target achieved!', color: 'text-green-600' };
    } else if (savings >= target * 0.7) {
      return { status: 'warning', message: 'Close to target', color: 'text-yellow-600' };
    } else {
      return { status: 'error', message: 'Below target', color: 'text-red-600' };
    }
  };

  const getProviderRecommendations = () => {
    const currentProvider = defaultProviders[selectedProvider];
    const recommendations = [];
    
    // Find cheapest provider for current content type
    const providersByCost = defaultProviders
      .map((provider, index) => ({
        name: provider.name,
        index,
        cost: estimate.contentType === 'video' 
          ? provider.video[estimate.resolution as keyof typeof provider.video] || 0.08
          : estimate.contentType === 'image'
          ? provider.image[estimate.resolution as keyof typeof provider.image] || 0.02
          : provider.audio.basic
      }))
      .sort((a, b) => a.cost - b.cost);
    
    if (providersByCost[0].index !== selectedProvider) {
      recommendations.push({
        type: 'provider',
        message: `Switch to ${providersByCost[0].name} to save ${formatCurrency((estimate.estimatedCost - estimate.estimatedCost * (providersByCost[0].cost / (currentProvider.video[estimate.resolution as keyof typeof currentProvider.video] || 0.08))) * (estimate.contentType === 'image' ? 1 : estimate.duration))}`,
        potentialSavings: estimate.estimatedCost * (providersByCost[0].cost / (currentProvider.video[estimate.resolution as keyof typeof currentProvider.video] || 0.08)) - estimate.estimatedCost
      });
    }
    
    // Check resolution optimization
    if (estimate.contentType === 'video' && estimate.resolution === '3840x2160') {
      recommendations.push({
        type: 'resolution',
        message: 'Consider 1080p resolution for 50% cost reduction with minimal quality loss',
        potentialSavings: estimate.estimatedCost * 0.5
      });
    }
    
    // Check engine optimization
    if (estimate.engine === 'ultra') {
      recommendations.push({
        type: 'engine',
        message: 'Default engine offers 70% cost savings for similar quality',
        potentialSavings: estimate.estimatedCost * 0.7
      });
    }
    
    return recommendations;
  };

  const status = getOptimizationStatus();
  const recommendations = getProviderRecommendations();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
            Cost Optimizer
          </h2>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Estimate and optimize content generation costs with smart algorithms
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={status.status === 'success' ? 'success' : status.status === 'warning' ? 'warning' : 'destructive'}>
            {status.message}
          </Badge>
        </div>
      </div>

      {/* Cost Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Current Cost</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {formatCurrency(estimate.estimatedCost)}
                </p>
                <p className="text-sm text-green-600">
                  {formatCurrency(estimate.optimizations.totalSavings)} saved
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Monthly Budget</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {formatCurrency(optimization.monthlyBudget)}
                </p>
                <p className={`text-sm ${optimization.budgetVariance > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {optimization.budgetVariance > 0 ? '+' : ''}{formatCurrency(optimization.budgetVariance)}
                </p>
              </div>
              <Target className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Optimization Rate</p>
                <p className="text-2xl font-bold text-green-600">
                  {((estimate.optimizations.totalSavings / (estimate.estimatedCost + estimate.optimizations.totalSavings)) * 100).toFixed(1)}%
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  of {((optimization.targetReduction) * 100).toFixed(0)}% target
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Provider</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {defaultProviders[selectedProvider].name}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {estimate.contentType} {estimate.resolution}
                </p>
              </div>
              <Zap className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="estimate">Cost Estimate</TabsTrigger>
          <TabsTrigger value="optimization">Optimization</TabsTrigger>
          <TabsTrigger value="providers">Providers</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="estimate" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calculator className="h-5 w-5" />
                Content Cost Estimation
              </CardTitle>
              <CardDescription>
                Calculate the cost for generating content with different parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="contentType">Content Type</Label>
                  <select
                    id="contentType"
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
                    value={estimate.contentType}
                    onChange={(e) => setEstimate(prev => ({ 
                      ...prev, 
                      contentType: e.target.value as 'video' | 'image' | 'audio',
                      resolution: e.target.value === 'image' ? '1024x1024' : '1920x1080'
                    }))}
                  >
                    <option value="video">Video</option>
                    <option value="image">Image</option>
                    <option value="audio">Audio</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="engine">Engine</Label>
                  <select
                    id="engine"
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
                    value={estimate.engine}
                    onChange={(e) => setEstimate(prev => ({ ...prev, engine: e.target.value }))}
                  >
                    {engineOptions.map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label} ({(option.premium * 100 - 100) >= 0 ? '+' : ''}{(option.premium * 100 - 100).toFixed(0)}%)
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="resolution">Resolution</Label>
                  <select
                    id="resolution"
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
                    value={estimate.resolution}
                    onChange={(e) => setEstimate(prev => ({ ...prev, resolution: e.target.value }))}
                  >
                    {resolutionOptions[estimate.contentType as keyof typeof resolutionOptions].map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label} ({option.multiplier}x)
                      </option>
                    ))}
                  </select>
                </div>

                {estimate.contentType !== 'image' && (
                  <div className="space-y-2">
                    <Label htmlFor="duration">Duration (seconds)</Label>
                    <Input
                      id="duration"
                      type="number"
                      min="1"
                      max="3600"
                      value={estimate.duration}
                      onChange={(e) => setEstimate(prev => ({ ...prev, duration: parseInt(e.target.value) || 30 }))}
                    />
                  </div>
                )}
              </div>

              <Separator />

              <div className="space-y-4">
                <h4 className="font-medium">Cost Breakdown</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Base Cost</span>
                      <span className="text-sm font-medium">
                        {formatCurrency(estimate.costBreakdown.baseCost)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Resolution Multiplier</span>
                      <span className="text-sm font-medium">
                        {estimate.costBreakdown.resolutionMultiplier}x
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Engine Premium</span>
                      <span className="text-sm font-medium">
                        {estimate.costBreakdown.enginePremium}x
                      </span>
                    </div>
                    {estimate.contentType !== 'image' && (
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Duration</span>
                        <span className="text-sm font-medium">
                          {estimate.duration}s
                        </span>
                      </div>
                    )}
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-green-600">
                      <span className="text-sm">Batch Discount</span>
                      <span className="text-sm font-medium">
                        -{formatCurrency(estimate.optimizations.batchDiscount)}
                      </span>
                    </div>
                    <div className="flex justify-between text-green-600">
                      <span className="text-sm">Cache Savings</span>
                      <span className="text-sm font-medium">
                        -{formatCurrency(estimate.optimizations.cacheSavings)}
                      </span>
                    </div>
                    <Separator />
                    <div className="flex justify-between font-medium text-lg">
                      <span>Total Cost</span>
                      <span className="text-blue-600">
                        {formatCurrency(estimate.estimatedCost)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="optimization" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Optimization Settings
              </CardTitle>
              <CardDescription>
                Configure optimization parameters and targets
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Enable Cost Optimization</Label>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Apply smart optimization algorithms to reduce costs
                  </p>
                </div>
                <Switch
                  checked={optimization.enabled}
                  onCheckedChange={(checked) => setOptimization(prev => ({ ...prev, enabled: checked }))}
                />
              </div>

              {optimization.enabled && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Target Reduction ({((optimization.targetReduction) * 100).toFixed(0)}%)</Label>
                    <Slider
                      value={[optimization.targetReduction]}
                      onValueChange={(value) => setOptimization(prev => ({ ...prev, targetReduction: value[0] }))}
                      max={0.8}
                      min={0.1}
                      step={0.05}
                      className="w-full"
                    />
                    <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                      <span>10%</span>
                      <span className="font-medium">Target: {((optimization.targetReduction) * 100).toFixed(0)}%</span>
                      <span>80%</span>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="font-medium">Current Performance</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                        <p className="text-2xl font-bold text-blue-600">
                          {((estimate.optimizations.totalSavings / (estimate.estimatedCost + estimate.optimizations.totalSavings)) * 100).toFixed(1)}%
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Current Savings</p>
                      </div>
                      <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                        <p className="text-2xl font-bold text-green-600">
                          {formatCurrency(optimization.currentSavings)}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Per Generation</p>
                      </div>
                      <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                        <p className="text-2xl font-bold text-purple-600">
                          {formatCurrency(optimization.currentSavings * 100)}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Monthly Savings</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="h-5 w-5" />
                  Optimization Recommendations
                </CardTitle>
                <CardDescription>
                  AI-powered suggestions to reduce costs
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {recommendations.map((rec, index) => (
                  <div key={index} className="flex items-start gap-3 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                    <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-yellow-900 dark:text-yellow-100">
                        {rec.message}
                      </p>
                      <p className="text-sm text-yellow-700 dark:text-yellow-200 mt-1">
                        Potential savings: {formatCurrency(rec.potentialSavings)}
                      </p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="providers" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Provider Comparison</CardTitle>
              <CardDescription>
                Compare costs across different content generation providers
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {defaultProviders.map((provider, index) => {
                  const isSelected = index === selectedProvider;
                  const cost = estimate.contentType === 'video' 
                    ? provider.video[estimate.resolution as keyof typeof provider.video] || 0.08
                    : estimate.contentType === 'image'
                    ? provider.image[estimate.resolution as keyof typeof provider.image] || 0.02
                    : provider.audio.basic;
                  
                  const totalCost = cost * estimate.costBreakdown.resolutionMultiplier * 
                    estimate.costBreakdown.enginePremium * (estimate.contentType === 'image' ? 1 : estimate.duration);
                  
                  return (
                    <div
                      key={provider.name}
                      className={`p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                        isSelected 
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                          : 'border-gray-200 dark:border-gray-800 hover:border-gray-300'
                      }`}
                      onClick={() => setSelectedProvider(index)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-4 h-4 rounded-full border-2 ${
                            isSelected ? 'border-blue-500 bg-blue-500' : 'border-gray-300'
                          }`} />
                          <div>
                            <h3 className="font-medium">{provider.name}</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {estimate.contentType} at {estimate.resolution}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold">
                            {formatCurrency(totalCost - estimate.optimizations.totalSavings)}
                          </p>
                          <p className="text-sm text-green-600">
                            Save {formatCurrency(estimate.optimizations.totalSavings)}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Cost Analytics
              </CardTitle>
              <CardDescription>
                Historical cost data and optimization trends
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium">Cost Trends</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Average Cost per Generation</span>
                      <span className="font-medium">{formatCurrency(0.45)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Monthly Cost (Projected)</span>
                      <span className="font-medium">{formatCurrency(optimization.projectedCosts)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Budget Utilization</span>
                      <span className="font-medium">{((optimization.projectedCosts / optimization.monthlyBudget) * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <h4 className="font-medium">Optimization Impact</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Total Savings (Monthly)</span>
                      <span className="font-medium text-green-600">
                        {formatCurrency(optimization.currentSavings * 100)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Optimization Rate</span>
                      <span className="font-medium">{((estimate.optimizations.totalSavings / (estimate.estimatedCost + estimate.optimizations.totalSavings)) * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Target Achievement</span>
                      <span className={`font-medium ${status.color}`}>
                        {((estimate.optimizations.totalSavings / (estimate.estimatedCost + estimate.optimizations.totalSavings)) / optimization.targetReduction * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                <h4 className="font-medium mb-4">Performance Metrics</h4>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Cost Reduction Progress</span>
                      <span>{((estimate.optimizations.totalSavings / (estimate.estimatedCost + estimate.optimizations.totalSavings)) * 100).toFixed(1)}%</span>
                    </div>
                    <Progress 
                      value={(estimate.optimizations.totalSavings / (estimate.estimatedCost + estimate.optimizations.totalSavings)) * 100} 
                      className="h-2"
                    />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Budget Safety Margin</span>
                      <span>{Math.max(0, 100 - (optimization.projectedCosts / optimization.monthlyBudget) * 100).toFixed(0)}%</span>
                    </div>
                    <Progress 
                      value={Math.max(0, 100 - (optimization.projectedCosts / optimization.monthlyBudget) * 100)} 
                      className="h-2"
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