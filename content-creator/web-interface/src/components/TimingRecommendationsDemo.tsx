import { useState } from 'react';
import {
  Calendar,
  Clock,
  Target,
  TrendingUp,
  Users,
  Zap,
  BarChart3,
  Filter,
  RefreshCw,
  Settings,
  CheckCircle,
  ArrowRight
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import PlatformRecommendations from './PlatformRecommendations';
import TimingChart from './TimingChart';

interface SchedulingRecommendation {
  id: string;
  window_start: string;
  window_end: string;
  score: number;
  reasons: string[];
  platforms: string[];
  confidence: number;
  content_types: string[];
}

interface OptimizationResult {
  id: string;
  changes_made: number;
  average_score_improvement: number;
  confidence: number;
  applied: boolean;
}

export default function TimingRecommendationsDemo() {
  const [selectedPlatforms, setSelectedPlatforms] = useState(['youtube', 'tiktok', 'instagram']);
  const [contentType, setContentType] = useState('video');
  const [optimizing, setOptimizing] = useState(false);
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResult | null>(null);
  const [activeTab, setActiveTab] = useState('recommendations');

  const platformOptions = [
    { value: 'youtube', label: 'YouTube' },
    { value: 'tiktok', label: 'TikTok' },
    { value: 'instagram', label: 'Instagram' },
    { value: 'linkedin', label: 'LinkedIn' },
    { value: 'twitter', label: 'Twitter/X' },
    { value: 'facebook', label: 'Facebook' }
  ];

  const contentTypeOptions = [
    { value: 'video', label: 'Videos' },
    { value: 'short', label: 'Shorts/Reels' },
    { value: 'post', label: 'Posts' },
    { value: 'story', label: 'Stories' },
    { value: 'article', label: 'Articles' }
  ];

  const handleTimeSlotSelect = (slot: SchedulingRecommendation) => {
    console.log('Selected optimal time slot:', slot);
    // Here you could:
    // 1. Create a new schedule with this timing
    // 2. Update an existing schedule
    // 3. Show a confirmation dialog
  };

  const handleOptimizeSchedule = async () => {
    setOptimizing(true);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Mock optimization result
    const result: OptimizationResult = {
      id: 'opt_' + Date.now(),
      changes_made: 8,
      average_score_improvement: 23.5,
      confidence: 0.87,
      applied: true
    };
    
    setOptimizationResult(result);
    setOptimizing(false);
  };

  const handleApplyRecommendations = () => {
    console.log('Applying AI recommendations to schedules');
    // Here you would integrate with the scheduling API
    // to actually apply the recommendations
  };

  const stats = [
    {
      label: 'Optimal Slots Found',
      value: '24',
      change: '+8 this week',
      icon: Target,
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    },
    {
      label: 'Avg Engagement Boost',
      value: '+18.5%',
      change: '+2.3% vs last month',
      icon: TrendingUp,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
    },
    {
      label: 'AI Confidence',
      value: '92%',
      change: 'High accuracy',
      icon: CheckCircle,
      color: 'text-purple-600 dark:text-purple-400',
      bgColor: 'bg-purple-100 dark:bg-purple-900/30',
    },
    {
      label: 'Time Saved',
      value: '6.5h',
      change: 'Per week',
      icon: Clock,
      color: 'text-orange-600 dark:text-orange-400',
      bgColor: 'bg-orange-100 dark:bg-orange-900/30',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            AI-Powered Timing Recommendations
          </h2>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Evidence-based posting recommendations using platform analytics and audience insights
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button onClick={handleOptimizeSchedule} disabled={optimizing}>
            {optimizing ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Optimizing...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 mr-2" />
                Optimize Schedule
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Configuration Panel */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Recommendation Settings
          </CardTitle>
          <CardDescription>
            Customize the AI recommendations based on your specific needs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Target Platforms
              </label>
              <div className="flex flex-wrap gap-2">
                {platformOptions.map((platform) => (
                  <Badge
                    key={platform.value}
                    variant={selectedPlatforms.includes(platform.value) ? "default" : "outline"}
                    className="cursor-pointer"
                    onClick={() => {
                      setSelectedPlatforms(prev => 
                        prev.includes(platform.value)
                          ? prev.filter(p => p !== platform.value)
                          : [...prev, platform.value]
                      );
                    }}
                  >
                    {platform.label}
                  </Badge>
                ))}
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Content Type
              </label>
              <Select value={contentType} onValueChange={setContentType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {contentTypeOptions.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-end">
              <Button 
                onClick={() => window.location.reload()} 
                variant="outline" 
                className="w-full"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh Data
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Overview */}
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
                <span className="text-sm text-green-600 dark:text-green-400 font-medium">
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

      {/* Optimization Results */}
      {optimizationResult && (
        <Card className="border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-800 dark:text-green-200">
              <CheckCircle className="w-5 h-5" />
              Optimization Complete
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-green-700 dark:text-green-300">
                  {optimizationResult.changes_made}
                </p>
                <p className="text-sm text-green-600 dark:text-green-400">Changes Applied</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-700 dark:text-green-300">
                  +{optimizationResult.average_score_improvement}%
                </p>
                <p className="text-sm text-green-600 dark:text-green-400">Score Improvement</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-700 dark:text-green-300">
                  {Math.round(optimizationResult.confidence * 100)}%
                </p>
                <p className="text-sm text-green-600 dark:text-green-400">Confidence Level</p>
              </div>
            </div>
            <div className="mt-4 flex gap-3">
              <Button onClick={handleApplyRecommendations} className="flex-1">
                <CheckCircle className="w-4 h-4 mr-2" />
                Apply All Recommendations
              </Button>
              <Button variant="outline">
                View Details
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="recommendations">Platform Recommendations</TabsTrigger>
          <TabsTrigger value="analytics">Timing Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="recommendations" className="space-y-6">
          <PlatformRecommendations
            selectedPlatforms={selectedPlatforms}
            contentType={contentType}
            targetAudience="general"
            onTimeSlotSelect={handleTimeSlotSelect}
          />
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <TimingChart
            platformData={[]} // This would be populated with real data in production
            selectedTimezone="UTC"
            onTimeSlotSelect={handleTimeSlotSelect}
          />
        </TabsContent>
      </Tabs>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5" />
            Quick Actions
          </CardTitle>
          <CardDescription>
            Fast access to common optimization tasks
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="h-auto p-4 flex flex-col items-center gap-2">
              <Calendar className="w-6 h-6" />
              <span>Create Optimal Schedule</span>
            </Button>
            <Button variant="outline" className="h-auto p-4 flex flex-col items-center gap-2">
              <BarChart3 className="w-6 h-6" />
              <span>Analyze Performance</span>
            </Button>
            <Button variant="outline" className="h-auto p-4 flex flex-col items-center gap-2">
              <Users className="w-6 h-6" />
              <span>Audience Insights</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}