import { useState, useEffect } from 'react';
import {
  Clock,
  TrendingUp,
  Calendar,
  Target,
  Zap,
  Globe,
  BarChart3,
  Users,
  Star,
  ArrowRight,
  RefreshCw,
  Filter,
  ChevronDown,
  CheckCircle,
  AlertTriangle,
  Info
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import TimingChart from './TimingChart';

interface PlatformTimingRecommendation {
  id: string;
  platform: string;
  platformName: string;
  optimalTimes: {
    hour: number;
    confidence: number;
    engagement_score: number;
    audience_active_percentage: number;
  }[];
  contentTypes: string[];
  timezone: string;
  bestDays: {
    day: string;
    score: number;
    engagement_boost: number;
  }[];
  audienceInsights: {
    peak_hours: number[];
    active_demographics: string[];
    weekend_vs_weekday: number;
  };
  competition: {
    level: 'low' | 'medium' | 'high';
    saturation_score: number;
  };
  recommendedStrategy: string[];
}

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

interface PlatformRecommendationsProps {
  selectedPlatforms?: string[];
  contentType?: string;
  targetAudience?: string;
  onTimeSlotSelect?: (slot: SchedulingRecommendation) => void;
}

export default function PlatformRecommendations({
  selectedPlatforms = ['youtube', 'tiktok', 'instagram'],
  contentType = 'video',
  targetAudience = 'general',
  onTimeSlotSelect
}: PlatformRecommendationsProps) {
  const [recommendations, setRecommendations] = useState<PlatformTimingRecommendation[]>([]);
  const [schedulingRecommendations, setSchedulingRecommendations] = useState<SchedulingRecommendation[]>([]);
  const [selectedTimezone, setSelectedTimezone] = useState('UTC');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('platforms');

  const platformNames: Record<string, string> = {
    youtube: 'YouTube',
    tiktok: 'TikTok',
    instagram: 'Instagram',
    linkedin: 'LinkedIn',
    twitter: 'Twitter/X',
    facebook: 'Facebook'
  };

  const contentTypeOptions = [
    { value: 'video', label: 'Videos' },
    { value: 'short', label: 'Shorts/Reels' },
    { value: 'post', label: 'Posts' },
    { value: 'story', label: 'Stories' },
    { value: 'article', label: 'Articles' }
  ];

  const timezoneOptions = [
    { value: 'UTC', label: 'UTC' },
    { value: 'America/New_York', label: 'Eastern Time' },
    { value: 'America/Chicago', label: 'Central Time' },
    { value: 'America/Denver', label: 'Mountain Time' },
    { value: 'America/Los_Angeles', label: 'Pacific Time' },
    { value: 'Europe/London', label: 'GMT' },
    { value: 'Europe/Paris', label: 'CET' },
    { value: 'Asia/Tokyo', label: 'JST' },
    { value: 'Asia/Shanghai', label: 'CST' }
  ];

  useEffect(() => {
    loadPlatformRecommendations();
    loadSchedulingRecommendations();
  }, [selectedPlatforms, contentType, targetAudience, selectedTimezone]);

  const loadPlatformRecommendations = async () => {
    setLoading(true);
    try {
      // Mock data - in real implementation, this would call the scheduling API
      const mockRecommendations: PlatformTimingRecommendation[] = [
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
          timezone: selectedTimezone,
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
            level: 'medium',
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
          timezone: selectedTimezone,
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
            level: 'high',
            saturation_score: 82
          },
          recommendedStrategy: [
            'Post during evening commute hours (6-9 PM)',
            'Leverage trending hashtags within first hour',
            'Test multiple short-form videos per day'
          ]
        },
        {
          id: '3',
          platform: 'instagram',
          platformName: 'Instagram',
          optimalTimes: [
            { hour: 11, confidence: 0.88, engagement_score: 82, audience_active_percentage: 73 },
            { hour: 13, confidence: 0.91, engagement_score: 86, audience_active_percentage: 78 },
            { hour: 19, confidence: 0.93, engagement_score: 90, audience_active_percentage: 84 },
            { hour: 20, confidence: 0.89, engagement_score: 85, audience_active_percentage: 79 }
          ],
          contentTypes: ['posts', 'reels', 'stories'],
          timezone: selectedTimezone,
          bestDays: [
            { day: 'Monday', score: 86, engagement_boost: 13 },
            { day: 'Wednesday', score: 89, engagement_boost: 15 },
            { day: 'Friday', score: 93, engagement_boost: 20 }
          ],
          audienceInsights: {
            peak_hours: [11, 13, 19, 20],
            active_demographics: ['18-29', '25-34'],
            weekend_vs_weekday: 18
          },
          competition: {
            level: 'high',
            saturation_score: 79
          },
          recommendedStrategy: [
            'Post during lunch breaks and evening leisure time',
            'Use Instagram Stories for real-time engagement',
            'Leverage Friday momentum for higher reach'
          ]
        }
      ];

      setRecommendations(mockRecommendations);
    } catch (error) {
      console.error('Failed to load platform recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSchedulingRecommendations = async () => {
    try {
      // Mock scheduling recommendations based on platform data
      const mockScheduling: SchedulingRecommendation[] = [
        {
          id: 'rec_1',
          window_start: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
          window_end: new Date(Date.now() + 25 * 60 * 60 * 1000).toISOString(),
          score: 0.94,
          reasons: ['audience_active_peak', 'low_competition', 'optimal_engagement'],
          platforms: ['tiktok'],
          confidence: 0.92,
          content_types: ['videos']
        },
        {
          id: 'rec_2',
          window_start: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
          window_end: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000 + 60 * 60 * 1000).toISOString(),
          score: 0.91,
          reasons: ['prime_time', 'weekend_boost'],
          platforms: ['youtube', 'instagram'],
          confidence: 0.89,
          content_types: ['long_form', 'reels']
        }
      ];

      setSchedulingRecommendations(mockScheduling);
    } catch (error) {
      console.error('Failed to load scheduling recommendations:', error);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600 dark:text-green-400';
    if (confidence >= 0.8) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getConfidenceIcon = (confidence: number) => {
    if (confidence >= 0.9) return <CheckCircle className="w-4 h-4" />;
    if (confidence >= 0.8) return <Info className="w-4 h-4" />;
    return <AlertTriangle className="w-4 h-4" />;
  };

  const getCompetitionColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/30';
      case 'medium': return 'text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/30';
      case 'high': return 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30';
      default: return 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-900/30';
    }
  };

  const formatHour = (hour: number) => {
    const period = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
    return `${displayHour}:00 ${period}`;
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Platform Timing Recommendations
          </h2>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
            AI-powered insights based on audience behavior and platform optimization
          </p>
        </div>
        <div className="flex space-x-3">
          <Select value={selectedTimezone} onValueChange={setSelectedTimezone}>
            <SelectTrigger className="w-40">
              <Globe className="w-4 h-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {timezoneOptions.map((tz) => (
                <SelectItem key={tz.value} value={tz.value}>
                  {tz.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={() => { loadPlatformRecommendations(); loadSchedulingRecommendations(); }} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="platforms">Platform Analysis</TabsTrigger>
          <TabsTrigger value="schedule">Optimal Schedule</TabsTrigger>
          <TabsTrigger value="insights">Audience Insights</TabsTrigger>
        </TabsList>

        {/* Platform Analysis Tab */}
        <TabsContent value="platforms" className="space-y-6">
          <div className="grid gap-6">
            {recommendations.map((platform) => (
              <Card key={platform.id} className="overflow-hidden">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        {platform.platformName}
                        <Badge className={getCompetitionColor(platform.competition.level)}>
                          {platform.competition.level} competition
                        </Badge>
                      </CardTitle>
                      <CardDescription>
                        Best times to post {contentType} content for maximum engagement
                      </CardDescription>
                    </div>
                    <div className="text-right">
                      <div className={`flex items-center gap-1 ${getConfidenceColor(platform.optimalTimes[0]?.confidence || 0)}`}>
                        {getConfidenceIcon(platform.optimalTimes[0]?.confidence || 0)}
                        <span className="text-sm font-medium">
                          {Math.round((platform.optimalTimes[0]?.confidence || 0) * 100)}% confidence
                        </span>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Optimal Times */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      Peak Hours ({platform.timezone})
                    </h4>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                      {platform.optimalTimes.map((timeSlot, index) => (
                        <div
                          key={index}
                          className="p-3 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg border border-blue-200 dark:border-blue-800"
                        >
                          <div className="text-lg font-bold text-gray-900 dark:text-white">
                            {formatHour(timeSlot.hour)}
                          </div>
                          <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">
                            {Math.round(timeSlot.engagement_score)}% engagement
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-500">
                            {Math.round(timeSlot.audience_active_percentage)}% active
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Best Days */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                      <Calendar className="w-4 h-4" />
                      Best Days
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {platform.bestDays.map((day, index) => (
                        <Badge key={index} variant="outline" className="px-3 py-1">
                          {day.day} (+{day.engagement_boost}%)
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* Recommendations */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                      <Target className="w-4 h-4" />
                      Strategy Recommendations
                    </h4>
                    <ul className="space-y-2">
                      {platform.recommendedStrategy.map((strategy, index) => (
                        <li key={index} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
                          <ArrowRight className="w-3 h-3 mt-0.5 flex-shrink-0" />
                          {strategy}
                        </li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Optimal Schedule Tab */}
        <TabsContent value="schedule" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Optimal Posting Schedule
              </CardTitle>
              <CardDescription>
                AI-selected time slots with highest predicted engagement
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {schedulingRecommendations.map((rec) => (
                  <div
                    key={rec.id}
                    className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer transition-colors"
                    onClick={() => onTimeSlotSelect?.(rec)}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                        <span className="font-medium text-gray-900 dark:text-white">
                          {formatDateTime(rec.window_start)} - {new Date(rec.window_end).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className={`flex items-center gap-1 ${getConfidenceColor(rec.confidence)}`}>
                          {getConfidenceIcon(rec.confidence)}
                          <span className="text-sm font-medium">
                            {Math.round(rec.score * 100)}% score
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2 mb-2">
                      {rec.platforms.map((platform) => (
                        <Badge key={platform} variant="secondary" className="text-xs">
                          {platformNames[platform] || platform}
                        </Badge>
                      ))}
                      {rec.content_types.map((type) => (
                        <Badge key={type} variant="outline" className="text-xs">
                          {type}
                        </Badge>
                      ))}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      <strong>Why this time:</strong> {rec.reasons.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Timing Chart */}
          <TimingChart
            platformData={recommendations}
            selectedTimezone={selectedTimezone}
            onTimeSlotSelect={onTimeSlotSelect}
          />
        </TabsContent>

        {/* Audience Insights Tab */}
        <TabsContent value="insights" className="space-y-6">
          <div className="grid gap-6">
            {recommendations.map((platform) => (
              <Card key={`insights-${platform.id}`}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="w-5 h-5" />
                    {platform.platformName} Audience Insights
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                        Peak Activity Hours
                      </h4>
                      <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                        {platform.audienceInsights.peak_hours.map(formatHour).join(', ')}
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        Highest audience activity periods
                      </p>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                        Active Demographics
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {platform.audienceInsights.active_demographics.map((demo, index) => (
                          <Badge key={index} variant="secondary">
                            {demo}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                  
                  <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                      <span className="text-sm font-medium text-blue-800 dark:text-blue-200">
                        Weekend vs Weekday Performance
                      </span>
                    </div>
                    <p className="text-sm text-blue-700 dark:text-blue-300">
                      {platform.audienceInsights.weekend_vs_weekday > 0 ? '+' : ''}
                      {platform.audienceInsights.weekend_vs_weekday}% higher engagement on weekends
                    </p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}