import { useState, useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  LineChart,
  Line,
  Area,
  AreaChart
} from 'recharts';
import {
  Clock,
  Calendar,
  TrendingUp,
  Zap,
  Eye,
  Users,
  Target,
  Filter,
  ChevronDown,
  Globe,
  Monitor
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

interface TimeSlot {
  hour: number;
  day: string;
  engagement_score: number;
  audience_active_percentage: number;
  confidence: number;
  platform: string;
  competition_level: number;
}

interface PlatformTimingData {
  platform: string;
  platformName: string;
  optimalTimes: {
    hour: number;
    confidence: number;
    engagement_score: number;
    audience_active_percentage: number;
  }[];
  timezone: string;
  bestDays: {
    day: string;
    score: number;
    engagement_boost: number;
  }[];
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

interface TimingChartProps {
  platformData: PlatformTimingData[];
  selectedTimezone?: string;
  onTimeSlotSelect?: (slot: SchedulingRecommendation) => void;
  height?: number;
}

export default function TimingChart({
  platformData,
  selectedTimezone = 'UTC',
  onTimeSlotSelect,
  height = 400
}: TimingChartProps) {
  const [selectedChart, setSelectedChart] = useState<'heatmap' | 'radar' | 'trends'>('heatmap');
  const [selectedDay, setSelectedDay] = useState('all');
  const [selectedPlatform, setSelectedPlatform] = useState('all');

  const platformNames: Record<string, string> = {
    youtube: 'YouTube',
    tiktok: 'TikTok',
    instagram: 'Instagram',
    linkedin: 'LinkedIn',
    twitter: 'Twitter/X',
    facebook: 'Facebook'
  };

  // Transform platform data into chart format
  const chartData = useMemo(() => {
    const data: TimeSlot[] = [];
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

    platformData.forEach((platform) => {
      platform.optimalTimes.forEach((timeSlot) => {
        days.forEach((day) => {
          const isBestDay = platform.bestDays.some(bestDay => bestDay.day === day);
          const dayMultiplier = isBestDay ? 1.15 : 0.85;
          
          data.push({
            hour: timeSlot.hour,
            day: day,
            engagement_score: Math.round(timeSlot.engagement_score * dayMultiplier),
            audience_active_percentage: Math.round(timeSlot.audience_active_percentage * dayMultiplier),
            confidence: timeSlot.confidence,
            platform: platform.platform,
            competition_level: Math.random() * 0.3 + 0.4 // Mock competition data
          });
        });
      });
    });

    // Filter based on selections
    return data.filter(item => {
      if (selectedDay !== 'all' && item.day !== selectedDay) return false;
      if (selectedPlatform !== 'all' && item.platform !== selectedPlatform) return false;
      return true;
    });
  }, [platformData, selectedDay, selectedPlatform]);

  // Aggregate data by hour for trend analysis
  const trendData = useMemo(() => {
    const hourlyData: Record<number, { engagement: number; audience: number; count: number }> = {};

    chartData.forEach(item => {
      if (!hourlyData[item.hour]) {
        hourlyData[item.hour] = { engagement: 0, audience: 0, count: 0 };
      }
      hourlyData[item.hour].engagement += item.engagement_score;
      hourlyData[item.hour].audience += item.audience_active_percentage;
      hourlyData[item.hour].count += 1;
    });

    return Object.entries(hourlyData).map(([hour, data]) => ({
      hour: parseInt(hour),
      engagement: Math.round(data.engagement / data.count),
      audience: Math.round(data.audience / data.count),
      time: formatHour(parseInt(hour))
    })).sort((a, b) => a.hour - b.hour);
  }, [chartData]);

  // Radar chart data for platform comparison
  const radarData = useMemo(() => {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    
    return days.map(day => {
      const dayData = chartData.filter(item => item.day === day);
      const avgEngagement = dayData.length > 0 
        ? dayData.reduce((sum, item) => sum + item.engagement_score, 0) / dayData.length 
        : 0;
      
      return {
        day: day.slice(0, 3), // Short form for radar chart
        engagement: Math.round(avgEngagement),
        fullName: day
      };
    });
  }, [chartData]);

  const dayOptions = [
    { value: 'all', label: 'All Days' },
    { value: 'Monday', label: 'Monday' },
    { value: 'Tuesday', label: 'Tuesday' },
    { value: 'Wednesday', label: 'Wednesday' },
    { value: 'Thursday', label: 'Thursday' },
    { value: 'Friday', label: 'Friday' },
    { value: 'Saturday', label: 'Saturday' },
    { value: 'Sunday', label: 'Sunday' }
  ];

  const platformOptions = [
    { value: 'all', label: 'All Platforms' },
    ...platformData.map(p => ({
      value: p.platform,
      label: p.platformName
    }))
  ];

  function formatHour(hour: number) {
    const period = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
    return `${displayHour}:00 ${period}`;
  }

  const getHeatmapColor = (engagement: number) => {
    const opacity = Math.min(engagement / 100, 1);
    return `rgba(59, 130, 246, ${opacity})`;
  };

  const getEngagementLevel = (score: number) => {
    if (score >= 90) return { label: 'Excellent', color: 'text-green-600 dark:text-green-400' };
    if (score >= 80) return { label: 'Good', color: 'text-blue-600 dark:text-blue-400' };
    if (score >= 70) return { label: 'Average', color: 'text-yellow-600 dark:text-yellow-400' };
    return { label: 'Low', color: 'text-red-600 dark:text-red-400' };
  };

  // Custom Tooltip for heatmap
  const HeatmapTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const engagement = getEngagementLevel(data.engagement_score);
      return (
        <div className="bg-white dark:bg-gray-900 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 dark:text-white">{data.day}</p>
          <p className="text-sm text-gray-600 dark:text-gray-400">{formatHour(data.hour)}</p>
          <div className="mt-2 space-y-1">
            <div className="flex justify-between gap-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">Engagement:</span>
              <span className={`text-sm font-medium ${engagement.color}`}>
                {data.engagement_score}%
              </span>
            </div>
            <div className="flex justify-between gap-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">Audience Active:</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {data.audience_active_percentage}%
              </span>
            </div>
            <div className="flex justify-between gap-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">Confidence:</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {Math.round(data.confidence * 100)}%
              </span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  // Transform data for heatmap visualization
  const heatmapData = useMemo(() => {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const hours = Array.from({ length: 24 }, (_, i) => i);
    
    return days.map(day => {
      const dayData = chartData.filter(item => item.day === day);
      return {
        day,
        ...hours.reduce((acc, hour) => {
          const hourData = dayData.find(item => item.hour === hour);
          acc[hour] = hourData ? hourData.engagement_score : 0;
          return acc;
        }, {} as Record<number, number>)
      };
    });
  }, [chartData]);

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Monitor className="w-5 h-5" />
              Visual Timing Analysis
            </CardTitle>
            <CardDescription>
              Interactive charts showing optimal posting times across platforms
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Select value={selectedDay} onValueChange={setSelectedDay}>
              <SelectTrigger className="w-32">
                <Calendar className="w-4 h-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {dayOptions.map((day) => (
                  <SelectItem key={day.value} value={day.value}>
                    {day.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={selectedPlatform} onValueChange={setSelectedPlatform}>
              <SelectTrigger className="w-36">
                <Filter className="w-4 h-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {platformOptions.map((platform) => (
                  <SelectItem key={platform.value} value={platform.value}>
                    {platform.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs value={selectedChart} onValueChange={setSelectedChart}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="heatmap">Heatmap</TabsTrigger>
            <TabsTrigger value="radar">Platform Comparison</TabsTrigger>
            <TabsTrigger value="trends">Hourly Trends</TabsTrigger>
          </TabsList>

          {/* Heatmap View */}
          <TabsContent value="heatmap" className="space-y-4">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Engagement score by day and hour - darker colors indicate higher engagement
            </div>
            <div className="overflow-x-auto">
              <div className="min-w-[800px]">
                {/* Hour headers */}
                <div className="flex mb-2">
                  <div className="w-20"></div>
                  {Array.from({ length: 24 }, (_, i) => (
                    <div key={i} className="flex-1 text-center text-xs text-gray-500 dark:text-gray-400 transform -rotate-45 origin-center">
                      {i % 2 === 0 ? formatHour(i) : ''}
                    </div>
                  ))}
                </div>
                
                {/* Day rows */}
                {heatmapData.map((day) => (
                  <div key={day.day} className="flex mb-1">
                    <div className="w-20 text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center">
                      {day.day.slice(0, 3)}
                    </div>
                    {Array.from({ length: 24 }, (_, hour) => (
                      <div
                        key={hour}
                        className="flex-1 h-8 m-0.5 rounded border border-gray-200 dark:border-gray-700 cursor-pointer hover:scale-105 transition-transform"
                        style={{
                          backgroundColor: getHeatmapColor(day[hour]),
                          minHeight: '32px'
                        }}
                        title={`${day.day} ${formatHour(hour)}: ${day[hour]}% engagement`}
                      />
                    ))}
                  </div>
                ))}
              </div>
            </div>
            
            {/* Legend */}
            <div className="flex items-center justify-center gap-4 mt-4">
              <span className="text-sm text-gray-600 dark:text-gray-400">Low Engagement</span>
              <div className="flex gap-1">
                {[0.2, 0.4, 0.6, 0.8, 1.0].map((opacity) => (
                  <div
                    key={opacity}
                    className="w-4 h-4 rounded border border-gray-200 dark:border-gray-700"
                    style={{ backgroundColor: `rgba(59, 130, 246, ${opacity})` }}
                  />
                ))}
              </div>
              <span className="text-sm text-gray-600 dark:text-gray-400">High Engagement</span>
            </div>
          </TabsContent>

          {/* Radar Chart View */}
          <TabsContent value="radar" className="space-y-4">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Platform engagement comparison across days of the week
            </div>
            <div style={{ height }}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="day" tick={{ fontSize: 12 }} />
                  <PolarRadiusAxis
                    angle={90}
                    domain={[0, 100]}
                    tick={{ fontSize: 10 }}
                    tickFormatter={(value) => `${value}%`}
                  />
                  <Radar
                    name="Engagement"
                    dataKey="engagement"
                    stroke="#3B82F6"
                    fill="#3B82F6"
                    fillOpacity={0.2}
                    strokeWidth={2}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            <div className="text-center text-sm text-gray-600 dark:text-gray-400">
              Average engagement scores by day of week
            </div>
          </TabsContent>

          {/* Trend Chart View */}
          <TabsContent value="trends" className="space-y-4">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Hourly engagement and audience activity trends
            </div>
            <div style={{ height }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
                  <XAxis 
                    dataKey="time" 
                    stroke="#9CA3AF"
                    fontSize={12}
                    interval={1}
                  />
                  <YAxis 
                    stroke="#9CA3AF"
                    fontSize={12}
                    tickFormatter={(value) => `${value}%`}
                  />
                  <Tooltip content={<HeatmapTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="engagement"
                    stackId="1"
                    stroke="#3B82F6"
                    fill="#3B82F6"
                    fillOpacity={0.3}
                    name="Engagement Score"
                  />
                  <Area
                    type="monotone"
                    dataKey="audience"
                    stackId="2"
                    stroke="#10B981"
                    fill="#10B981"
                    fillOpacity={0.3}
                    name="Audience Active %"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-blue-600 opacity-30"></div>
                <span className="text-gray-600 dark:text-gray-400">Engagement Score</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-green-600 opacity-30"></div>
                <span className="text-gray-600 dark:text-gray-400">Audience Active %</span>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* Key Insights */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <span className="text-sm font-medium text-blue-800 dark:text-blue-200">
                Peak Hours
              </span>
            </div>
            <p className="text-sm text-blue-700 dark:text-blue-300">
              {trendData.length > 0 && formatHour(trendData.reduce((max, current) => 
                current.engagement > max.engagement ? current : max
              ).hour)} shows highest engagement
            </p>
          </div>

          <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Users className="w-4 h-4 text-green-600 dark:text-green-400" />
              <span className="text-sm font-medium text-green-800 dark:text-green-200">
                Best Platform
              </span>
            </div>
            <p className="text-sm text-green-700 dark:text-green-300">
              {platformData.length > 0 && platformData[0].platformName} has highest overall engagement
            </p>
          </div>

          <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-4 h-4 text-purple-600 dark:text-purple-400" />
              <span className="text-sm font-medium text-purple-800 dark:text-purple-200">
                Recommendation
              </span>
            </div>
            <p className="text-sm text-purple-700 dark:text-purple-300">
              Post during evening hours (6-9 PM) for maximum reach
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}