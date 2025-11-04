import { useState, useEffect } from 'react';
import {
  Calendar,
  Clock,
  Target,
  TrendingUp,
  Users,
  Zap,
  BarChart3,
  RefreshCw,
  Settings,
  CheckCircle,
  ArrowRight,
  Star,
  Globe,
  Filter,
  Play,
  Pause,
  MoreHorizontal
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Progress } from './ui/progress';
import PlatformRecommendations from './PlatformRecommendations';
import TimingChart from './TimingChart';

// Mock data for demonstration
const mockPlatformData = [
  {
    id: '1',
    platform: 'youtube',
    platformName: 'YouTube',
    optimalTimes: [
      { hour: 14, confidence: 0.92, engagement_score: 87, audience_active_percentage: 78 },
      { hour: 15, confidence: 0.89, engagement_score: 84, audience_active_percentage: 75 },
      { hour: 20, confidence: 0.91, engagement_score: 89, audience_active_percentage: 82 },
      { hour: 21, confidence: 0.94, engagement_score: 91, audience_active_percentage: 85 }
    ],
    contentTypes: ['long_form', 'shorts'],
    timezone: 'UTC',
    bestDays: [
      { day: 'Thursday', score: 89, engagement_boost: 15 },
      { day: 'Friday', score: 92, engagement_boost: 18 },
      { day: 'Saturday', score: 85, engagement_boost: 12 }
    ],
    audienceInsights: {
      peak_hours: [14, 15, 20, 21],
      active_demographics: ['18-34', '25-44'],
      weekend_vs_weekday: 12
    },
    competition: {
      level: 'medium' as const,
      saturation_score: 67
    },
    recommendedStrategy: [
      'Post 2-4 hours before prime viewing time',
      'Target Thursday-Saturday for higher engagement',
      'Consider weekend morning uploads for family content'
    ]
  },
  {
    id: '2',
    platform: 'tiktok',
    platformName: 'TikTok',
    optimalTimes: [
      { hour: 18, confidence: 0.95, engagement_score: 93, audience_active_percentage: 88 },
      { hour: 19, confidence: 0.97, engagement_score: 95, audience_active_percentage: 91 },
      { hour: 20, confidence: 0.94, engagement_score: 92, audience_active_percentage: 87 },
      { hour: 21, confidence: 0.91, engagement_score: 89, audience_active_percentage: 84 }
    ],
    contentTypes: ['videos', 'trending'],
    timezone: 'UTC',
    bestDays: [
      { day: 'Tuesday', score: 88, engagement_boost: 14 },
      { day: 'Thursday', score: 91, engagement_boost: 16 },
      { day: 'Friday', score: 94, engagement_boost: 19 }
    ],
    audienceInsights: {
      peak_hours: [18, 19, 20, 21],
      active_demographics: ['16-24', '18-34'],
      weekend_vs_weekday: 22
    },
    competition: {
      level: 'high' as const,
      saturation_score: 82
    },
    recommendedStrategy: [
      'Post during evening commute hours (6-9 PM)',
      'Leverage trending hashtags within first hour',
      'Test multiple short-form videos per day'
    ]
  }
];

interface Schedule {
  id: string;
  title: string;
  platform: string;
  optimalTime: string;
  confidence: number;
  status: 'pending' | 'scheduled' | 'published' | 'failed';
  engagementPrediction: number;
}

export default function TimingRecommendationsExample() {
  const [selectedPlatforms, setSelectedPlatforms] = useState(['youtube', 'tiktok', 'instagram']);
  const [contentType, setContentType] = useState('video');
  const [timezone, setTimezone] = useState('UTC');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [schedules, setSchedules] = useState<Schedule[]>([
    {
      id: '1',
      title: 'Product Demo Video',
      platform: 'youtube',
      optimalTime: '2025-11-06T15:00:00Z',
      confidence: 0.92,
      status: 'scheduled',
      engagementPrediction: 87
    },
    {
      id: '2',
      title: 'Behind the Scenes',
      platform: 'tiktok',
      optimalTime: '2025-11-06T20:00:00Z',
      confidence: 0.95,
      status: 'pending',
      engagementPrediction: 93
    },
    {
      id: '3',
      title: 'Industry Insights',
      platform: 'linkedin',
      optimalTime: '2025-11-07T09:00:00Z',
      confidence: 0.88,
      status: 'scheduled',
      engagementPrediction: 76
    }
  ]);

  const platformOptions = [
    { value: 'youtube', label: 'YouTube', color: 'bg-red-100 text-red-800' },
    { value: 'tiktok', label: 'TikTok', color: 'bg-black text-white' },
    { value: 'instagram', label: 'Instagram', color: 'bg-pink-100 text-pink-800' },
    { value: 'linkedin', label: 'LinkedIn', color: 'bg-blue-100 text-blue-800' },
    { value: 'twitter', label: 'Twitter/X', color: 'bg-sky-100 text-sky-800' },
    { value: 'facebook', label: 'Facebook', color: 'bg-blue-100 text-blue-800' }
  ];

  const handleTimeSlotSelect = (slot: any) => {
    console.log('Selected optimal time slot:', slot);
    
    // Create a new schedule from the selected slot
    const newSchedule: Schedule = {
      id: Date.now().toString(),
      title: 'AI-Recommended Post',
      platform: slot.platforms[0],
      optimalTime: slot.window_start,
      confidence: slot.confidence,
      status: 'pending',
      engagementPrediction: Math.round(slot.score * 100)
    };
    
    setSchedules(prev => [newSchedule, ...prev]);
  };

  const handleOptimizeSchedules = async () => {
    setLoading(true);
    // Simulate API optimization
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Update schedules with optimization results
    setSchedules(prev => prev.map(schedule => ({
      ...schedule,
      confidence: Math.min(schedule.confidence + 0.05, 0.98),
      engagementPrediction: Math.min(schedule.engagementPrediction + 3, 95)
    })));
    
    setLoading(false);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'scheduled': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
      case 'pending': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'failed': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
    }
  };

  const getPlatformIcon = (platform: string) => {
    const icons: Record<string, string> = {
      youtube: '🎥',
      tiktok: '🎵',
      instagram: '📸',
      linkedin: '💼',
      twitter: '🐦',
      facebook: '📘'
    };
    return icons[platform] || '📱';
  };

  const stats = [
    {
      label: 'Optimal Schedules',
      value: schedules.length.toString(),
      change: '+3 this week',
      icon: Target,
      color: 'text-blue-600 dark:text-blue-400',
    },
    {
      label: 'Avg Confidence',
      value: `${Math.round(schedules.reduce((sum, s) => sum + s.confidence, 0) / schedules.length * 100)}%`,
      change: '+5% improvement',
      icon: TrendingUp,
      color: 'text-green-600 dark:text-green-400',
    },
    {
      label: 'Predicted Engagement',
      value: `${Math.round(schedules.reduce((sum, s) => sum + s.engagementPrediction, 0) / schedules.length)}%`,
      change: '+12% vs manual',
      icon: Users,
      color: 'text-purple-600 dark:text-purple-400',
    },
    {
      label: 'Time Saved',
      value: '8.2h',
      change: 'This month',
      icon: Clock,
      color: 'text-orange-600 dark:text-orange-400',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            AI Timing Recommendations Demo
          </h2>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            Complete example integrating platform recommendations with scheduling
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Select value={timezone} onValueChange={setTimezone}>
            <SelectTrigger className="w-40">
              <Globe className="w-4 h-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="UTC">UTC</SelectItem>
              <SelectItem value="America/New_York">Eastern</SelectItem>
              <SelectItem value="America/Los_Angeles">Pacific</SelectItem>
              <SelectItem value="Europe/London">GMT</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={handleOptimizeSchedules} disabled={loading}>
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Optimizing...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 mr-2" />
                Optimize All
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card key={index}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      {stat.label}
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {stat.value}
                    </p>
                    <p className="text-sm text-green-600 dark:text-green-400">
                      {stat.change}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-100 dark:bg-gray-800">
                    <Icon className={`w-6 h-6 ${stat.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Quick Schedule List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            AI-Optimized Schedules
          </CardTitle>
          <CardDescription>
            Content scheduled based on AI timing recommendations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {schedules.map((schedule) => (
              <div
                key={schedule.id}
                className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="text-2xl">
                    {getPlatformIcon(schedule.platform)}
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">
                      {schedule.title}
                    </h4>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge className={platformOptions.find(p => p.value === schedule.platform)?.color}>
                        {schedule.platform}
                      </Badge>
                      <Badge variant="outline">
                        {new Date(schedule.optimalTime).toLocaleDateString()}
                      </Badge>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="flex items-center gap-2">
                      <Star className="w-4 h-4 text-yellow-500" />
                      <span className="text-sm font-medium">
                        {Math.round(schedule.confidence * 100)}% confidence
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {schedule.engagementPrediction}% predicted engagement
                    </p>
                  </div>
                  
                  <Badge className={getStatusColor(schedule.status)}>
                    {schedule.status}
                  </Badge>
                  
                  <Button variant="ghost" size="sm">
                    <MoreHorizontal className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Recommendations</TabsTrigger>
          <TabsTrigger value="analytics">Timing Analysis</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <PlatformRecommendations
            selectedPlatforms={selectedPlatforms}
            contentType={contentType}
            targetAudience="general"
            onTimeSlotSelect={handleTimeSlotSelect}
          />
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <TimingChart
            platformData={mockPlatformData}
            selectedTimezone={timezone}
            onTimeSlotSelect={handleTimeSlotSelect}
          />
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          <div className="grid gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Optimization Results</CardTitle>
                <CardDescription>
                  AI-powered schedule optimization performance metrics
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {schedules.map((schedule) => (
                  <div key={schedule.id} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {schedule.title} - {schedule.platform}
                      </span>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {schedule.engagementPrediction}% predicted engagement
                      </span>
                    </div>
                    <Progress value={schedule.engagementPrediction} className="h-2" />
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Success Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                      94.2%
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      Recommendation Accuracy
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                      +18.5%
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      Engagement Improvement
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                      6.2h
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      Time Saved per Week
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Action Panel */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Button className="h-20 flex flex-col items-center gap-2">
              <Play className="w-6 h-6" />
              <span>Auto-Schedule</span>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col items-center gap-2">
              <Target className="w-6 h-6" />
              <span>Find Optimal Times</span>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col items-center gap-2">
              <BarChart3 className="w-6 h-6" />
              <span>Analyze Performance</span>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col items-center gap-2">
              <Settings className="w-6 h-6" />
              <span>Configure AI</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}