/**
 * AI Content Automation System - React Scheduling Examples
 * ========================================================
 * 
 * This file contains comprehensive React component examples for integrating
 * with the AI Content Automation System's scheduling functionality.
 * 
 * Components included:
 * 1. SchedulingDashboard - Main dashboard for managing schedules
 * 2. ScheduleCreator - Form for creating new schedules
 * 3. RecommendationViewer - Display optimal posting time recommendations
 * 4. ProgressMonitor - Real-time progress tracking
 * 5. ScheduleList - List and manage existing schedules
 * 6. PlatformSelector - Multi-platform selection component
 * 7. CalendarView - Calendar view of scheduled content
 * 8. AnalyticsView - Analytics and performance metrics
 * 
 * Prerequisites:
 * - React 18+
 * - TypeScript
 * - Tailwind CSS
 * - Lucide React icons
 * - date-fns for date formatting
 * - @tanstack/react-query for data fetching (optional)
 * - WebSocket client for real-time updates
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  Calendar, Clock, Play, Pause, CheckCircle, AlertCircle, 
  Plus, Settings, BarChart3, Filter, RefreshCw, 
  Target, Zap, Users, TrendingUp, ExternalLink,
  Edit, Trash2, Eye, Copy, Share, Download
} from 'lucide-react';

// =============================================================================
// TYPES AND INTERFACES
// =============================================================================

interface Platform {
  id: string;
  name: string;
  color: string;
  icon: string;
  maxDuration?: number;
  optimalTimes?: string[];
}

interface Recommendation {
  id: string;
  platform: string;
  recommendedTime: string;
  confidenceScore: number;
  reason: string;
  audienceActivity: 'high' | 'medium' | 'low';
  estimatedEngagement: number;
  timezone: string;
}

interface ScheduleItem {
  id: string;
  contentId: string;
  platform: string;
  scheduledTime: string;
  status: 'pending' | 'scheduled' | 'published' | 'failed' | 'canceled';
  metadata: {
    title?: string;
    description?: string;
    hashtags?: string[];
    targetAudience?: string;
    tone?: string;
    estimatedReach?: number;
    campaignId?: string;
  };
  progress?: number;
  errorMessage?: string;
  publishedAt?: string;
}

interface ContentSchedule {
  id: string;
  title: string;
  description: string;
  timezone: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'canceled';
  items: ScheduleItem[];
  createdAt: string;
  updatedAt: string;
  totalItems: number;
  completedItems: number;
  failedItems: number;
}

interface ScheduleFormData {
  title: string;
  description: string;
  timezone: string;
  items: {
    contentId: string;
    platform: string;
    scheduledTime: string;
    metadata: {
      title: string;
      description: string;
      targetAudience: string;
      tone: string;
      hashtags: string;
    };
  }[];
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short'
  });
};

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'scheduled': return 'bg-blue-100 text-blue-800 border-blue-200';
    case 'running': return 'bg-purple-100 text-purple-800 border-purple-200';
    case 'published': return 'bg-green-100 text-green-800 border-green-200';
    case 'failed': return 'bg-red-100 text-red-800 border-red-200';
    case 'canceled': return 'bg-gray-100 text-gray-800 border-gray-200';
    default: return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

const getPlatformColor = (platform: string): string => {
  const colors = {
    youtube: 'text-red-600 bg-red-50',
    tiktok: 'text-black bg-gray-50',
    instagram: 'text-pink-600 bg-pink-50',
    linkedin: 'text-blue-600 bg-blue-50',
    twitter: 'text-blue-400 bg-blue-50',
    facebook: 'text-blue-700 bg-blue-50'
  };
  return colors[platform] || 'text-gray-600 bg-gray-50';
};

const PLATFORMS: Platform[] = [
  { id: 'youtube', name: 'YouTube', color: '#FF0000', icon: 'youtube', optimalTimes: ['15:00', '16:00', '17:00'] },
  { id: 'tiktok', name: 'TikTok', color: '#000000', icon: 'tiktok', optimalTimes: ['15:00', '20:00', '21:00'] },
  { id: 'instagram', name: 'Instagram', color: '#E4405F', icon: 'instagram', optimalTimes: ['11:00', '14:00', '17:00'] },
  { id: 'linkedin', name: 'LinkedIn', color: '#0077B5', icon: 'linkedin', optimalTimes: ['09:00', '10:00', '14:00'] },
  { id: 'twitter', name: 'Twitter/X', color: '#1DA1F2', icon: 'twitter', optimalTimes: ['09:00', '12:00', '15:00'] },
  { id: 'facebook', name: 'Facebook', color: '#1877F2', icon: 'facebook', optimalTimes: ['13:00', '15:00', '19:00'] }
];

// =============================================================================
// API CLIENT HOOK
// =============================================================================

const useSchedulingAPI = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiCall = async <T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T | null> => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`/api/v1/scheduling${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
          ...options.headers
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}`);
      }

      const data = await response.json();
      return data.data || data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      console.error('API call failed:', errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const getRecommendations = useCallback(async (
    platforms: string[], 
    targetCount: number = 10
  ): Promise<Recommendation[]> => {
    const params = new URLSearchParams({
      platforms: platforms.join(','),
      targetCount: targetCount.toString()
    });

    const data = await apiCall<{ data: Recommendation[] }>(`/recommendations?${params}`);
    return data || [];
  }, []);

  const createSchedule = useCallback(async (scheduleData: ScheduleFormData): Promise<string | null> => {
    const data = await apiCall<{ data: { id: string } }>('/calendar', {
      method: 'POST',
      body: JSON.stringify(scheduleData)
    });
    return data?.id || null;
  }, []);

  const getSchedules = useCallback(async (): Promise<ContentSchedule[]> => {
    const data = await apiCall<{ data: ContentSchedule[] }>('/calendar');
    return data || [];
  }, []);

  const getScheduleStatus = useCallback(async (scheduleId: string): Promise<ContentSchedule | null> => {
    const data = await apiCall<{ data: ContentSchedule }>(`/calendar/${scheduleId}`);
    return data || null;
  }, []);

  return {
    loading,
    error,
    getRecommendations,
    createSchedule,
    getSchedules,
    getScheduleStatus
  };
};

// =============================================================================
// PLATFORM SELECTOR COMPONENT
// =============================================================================

interface PlatformSelectorProps {
  selectedPlatforms: string[];
  onChange: (platforms: string[]) => void;
  maxSelection?: number;
  showOptimalTimes?: boolean;
}

const PlatformSelector: React.FC<PlatformSelectorProps> = ({
  selectedPlatforms,
  onChange,
  maxSelection = 6,
  showOptimalTimes = false
}) => {
  const togglePlatform = (platformId: string) => {
    if (selectedPlatforms.includes(platformId)) {
      onChange(selectedPlatforms.filter(id => id !== platformId));
    } else if (selectedPlatforms.length < maxSelection) {
      onChange([...selectedPlatforms, platformId]);
    }
  };

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-gray-700">
        Select Platforms ({selectedPlatforms.length}/{maxSelection})
      </label>
      
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {PLATFORMS.map(platform => {
          const isSelected = selectedPlatforms.includes(platform.id);
          
          return (
            <button
              key={platform.id}
              onClick={() => togglePlatform(platform.id)}
              disabled={!isSelected && selectedPlatforms.length >= maxSelection}
              className={`
                p-3 rounded-lg border-2 transition-all duration-200 text-left
                ${isSelected 
                  ? 'border-blue-500 bg-blue-50 shadow-md' 
                  : 'border-gray-200 bg-white hover:border-gray-300'
                }
                ${!isSelected && selectedPlatforms.length >= maxSelection 
                  ? 'opacity-50 cursor-not-allowed' 
                  : 'cursor-pointer'
                }
              `}
            >
              <div className="flex items-center gap-3">
                <div 
                  className="w-4 h-4 rounded-full" 
                  style={{ backgroundColor: platform.color }}
                />
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">
                    {platform.name}
                  </p>
                  {showOptimalTimes && platform.optimalTimes && (
                    <p className="text-xs text-gray-500 mt-1">
                      Best: {platform.optimalTimes.join(', ')}
                    </p>
                  )}
                </div>
                {isSelected && (
                  <CheckCircle className="w-5 h-5 text-blue-500" />
                )}
              </div>
            </button>
          );
        })}
      </div>
      
      {selectedPlatforms.length > 0 && (
        <div className="pt-2 border-t border-gray-200">
          <p className="text-sm text-gray-600 mb-2">Selected platforms:</p>
          <div className="flex flex-wrap gap-2">
            {selectedPlatforms.map(platformId => {
              const platform = PLATFORMS.find(p => p.id === platformId);
              return platform ? (
                <span
                  key={platformId}
                  className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm ${getPlatformColor(platformId)}`}
                >
                  {platform.name}
                  <button
                    onClick={() => togglePlatform(platformId)}
                    className="hover:bg-black hover:bg-opacity-10 rounded-full p-0.5"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </span>
              ) : null;
            })}
          </div>
        </div>
      )}
    </div>
  );
};

// =============================================================================
// RECOMMENDATION VIEWER COMPONENT
// =============================================================================

interface RecommendationViewerProps {
  platforms: string[];
  onScheduleClick: (recommendation: Recommendation) => void;
  loading?: boolean;
}

const RecommendationViewer: React.FC<RecommendationViewerProps> = ({
  platforms,
  onScheduleClick,
  loading = false
}) => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const { getRecommendations } = useSchedulingAPI();

  const fetchRecommendations = useCallback(async () => {
    if (platforms.length === 0) return;
    
    setRefreshing(true);
    const data = await getRecommendations(platforms, 12);
    setRecommendations(data);
    setRefreshing(false);
  }, [platforms, getRecommendations]);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  const groupedRecommendations = useMemo(() => {
    const grouped = recommendations.reduce((acc, rec) => {
      if (!acc[rec.platform]) {
        acc[rec.platform] = [];
      }
      acc[rec.platform].push(rec);
      return acc;
    }, {} as Record<string, Recommendation[]>);

    // Sort by confidence score within each platform
    Object.keys(grouped).forEach(platform => {
      grouped[platform].sort((a, b) => b.confidenceScore - a.confidenceScore);
    });

    return grouped;
  }, [recommendations]);

  if (loading || refreshing) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Loading recommendations...</span>
      </div>
    );
  }

  if (platforms.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <Target className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p>Select platforms to see optimal posting times</p>
      </div>
    );
  }

  if (recommendations.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <AlertCircle className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p>No recommendations available for selected platforms</p>
        <button 
          onClick={fetchRecommendations}
          className="mt-4 text-blue-600 hover:text-blue-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          AI Recommendations ({recommendations.length})
        </h3>
        <button
          onClick={fetchRecommendations}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Object.entries(groupedRecommendations).map(([platform, platformRecs]) => (
          <div key={platform} className="space-y-3">
            <h4 className="font-medium text-gray-900 flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${getPlatformColor(platform).replace('text-', 'bg-').split(' ')[0]}`} />
              {platform.charAt(0).toUpperCase() + platform.slice(1)} ({platformRecs.length})
            </h4>
            
            <div className="space-y-2">
              {platformRecs.map((rec) => (
                <div
                  key={rec.id}
                  className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">
                        {formatDateTime(rec.recommendedTime)}
                      </p>
                      <div className="flex items-center gap-4 mt-1">
                        <span className="text-sm text-gray-500">
                          {Math.round(rec.confidenceScore * 100)}% confidence
                        </span>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          rec.audienceActivity === 'high' 
                            ? 'bg-green-100 text-green-700'
                            : rec.audienceActivity === 'medium'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-gray-100 text-gray-700'
                        }`}>
                          {rec.audienceActivity} activity
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => onScheduleClick(rec)}
                      className="px-3 py-1 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                    >
                      Schedule
                    </button>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-2">
                    {rec.reason}
                  </p>
                  
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>Est. engagement: {Math.round(rec.estimatedEngagement * 100)}%</span>
                    <span>{rec.timezone}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// =============================================================================
// SCHEDULE CREATOR COMPONENT
// =============================================================================

interface ScheduleCreatorProps {
  onScheduleCreated: (scheduleId: string) => void;
  onCancel: () => void;
  initialData?: Partial<ScheduleFormData>;
}

const ScheduleCreator: React.FC<ScheduleCreatorProps> = ({
  onScheduleCreated,
  onCancel,
  initialData
}) => {
  const [formData, setFormData] = useState<ScheduleFormData>({
    title: '',
    description: '',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    items: []
  });
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const { createSchedule } = useSchedulingAPI();

  const addScheduleItem = () => {
    const newItem = {
      contentId: `content_${Date.now()}`,
      platform: selectedPlatforms[0] || '',
      scheduledTime: '',
      metadata: {
        title: '',
        description: '',
        targetAudience: '',
        tone: 'professional',
        hashtags: ''
      }
    };

    setFormData(prev => ({
      ...prev,
      items: [...prev.items, newItem]
    }));
  };

  const updateScheduleItem = (index: number, field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      items: prev.items.map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    }));
  };

  const removeScheduleItem = (index: number) => {
    setFormData(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index)
    }));
  };

  const updateMetadata = (index: number, field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      items: prev.items.map((item, i) => 
        i === index ? {
          ...item,
          metadata: { ...item.metadata, [field]: value }
        } : item
      )
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (formData.items.length === 0) {
      alert('Please add at least one schedule item');
      return;
    }

    setLoading(true);
    
    try {
      const scheduleId = await createSchedule(formData);
      if (scheduleId) {
        onScheduleCreated(scheduleId);
      }
    } catch (error) {
      console.error('Failed to create schedule:', error);
      alert('Failed to create schedule. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const canProceedToStep2 = selectedPlatforms.length > 0;
  const canSubmit = formData.title && formData.items.length > 0;

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Create Content Schedule</h2>
        <p className="text-gray-600">Set up your content posting schedule across multiple platforms</p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center mb-8">
        <div className="flex items-center">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
            currentStep >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
          }`}>
            1
          </div>
          <span className={`ml-2 text-sm ${currentStep >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
            Platforms
          </span>
        </div>
        
        <div className="flex-1 h-px bg-gray-200 mx-4" />
        
        <div className="flex items-center">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
            currentStep >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
          }`}>
            2
          </div>
          <span className={`ml-2 text-sm ${currentStep >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
            Content Details
          </span>
        </div>
        
        <div className="flex-1 h-px bg-gray-200 mx-4" />
        
        <div className="flex items-center">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
            currentStep >= 3 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
          }`}>
            3
          </div>
          <span className={`ml-2 text-sm ${currentStep >= 3 ? 'text-blue-600' : 'text-gray-400'}`}>
            Schedule
          </span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Step 1: Platform Selection */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-4">
                Basic Information
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Schedule Title</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="My Content Series"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Timezone</label>
                  <select
                    value={formData.timezone}
                    onChange={(e) => setFormData(prev => ({ ...prev, timezone: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="America/New_York">Eastern Time</option>
                    <option value="America/Chicago">Central Time</option>
                    <option value="America/Denver">Mountain Time</option>
                    <option value="America/Los_Angeles">Pacific Time</option>
                    <option value="Europe/London">London</option>
                    <option value="Europe/Paris">Paris</option>
                    <option value="Asia/Tokyo">Tokyo</option>
                  </select>
                </div>
              </div>
              <div className="mt-4">
                <label className="block text-sm text-gray-600 mb-1">Description (Optional)</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
                  placeholder="Describe your content series..."
                />
              </div>
            </div>

            <PlatformSelector
              selectedPlatforms={selectedPlatforms}
              onChange={setSelectedPlatforms}
              maxSelection={6}
            />

            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => setCurrentStep(2)}
                disabled={!canProceedToStep2}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                Next: Add Content
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Content Details */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Content Items</h3>
              <button
                type="button"
                onClick={addScheduleItem}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-4 h-4" />
                Add Item
              </button>
            </div>

            {formData.items.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Plus className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>No content items yet. Add your first item to get started.</p>
              </div>
            ) : (
              <div className="space-y-6">
                {formData.items.map((item, index) => (
                  <div key={index} className="p-6 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="font-medium text-gray-900">Content Item {index + 1}</h4>
                      <button
                        type="button"
                        onClick={() => removeScheduleItem(index)}
                        className="text-red-600 hover:text-red-700 p-1"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Platform</label>
                        <select
                          value={item.platform}
                          onChange={(e) => updateScheduleItem(index, 'platform', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        >
                          {selectedPlatforms.map(platform => (
                            <option key={platform} value={platform}>
                              {platform.charAt(0).toUpperCase() + platform.slice(1)}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Scheduled Time</label>
                        <input
                          type="datetime-local"
                          value={item.scheduledTime}
                          onChange={(e) => updateScheduleItem(index, 'scheduledTime', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Content Title</label>
                        <input
                          type="text"
                          value={item.metadata.title}
                          onChange={(e) => updateMetadata(index, 'title', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                          placeholder="Enter content title"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Description</label>
                        <textarea
                          value={item.metadata.description}
                          onChange={(e) => updateMetadata(index, 'description', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                          rows={3}
                          placeholder="Describe your content..."
                        />
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm text-gray-600 mb-1">Target Audience</label>
                          <input
                            type="text"
                            value={item.metadata.targetAudience}
                            onChange={(e) => updateMetadata(index, 'targetAudience', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                            placeholder="e.g., tech professionals"
                          />
                        </div>
                        <div>
                          <label className="block text-sm text-gray-600 mb-1">Tone</label>
                          <select
                            value={item.metadata.tone}
                            onChange={(e) => updateMetadata(index, 'tone', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="professional">Professional</option>
                            <option value="casual">Casual</option>
                            <option value="educational">Educational</option>
                            <option value="entertaining">Entertaining</option>
                            <option value="inspirational">Inspirational</option>
                          </select>
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Hashtags</label>
                        <input
                          type="text"
                          value={item.metadata.hashtags}
                          onChange={(e) => updateMetadata(index, 'hashtags', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                          placeholder="#AI #Technology #Tutorial"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="flex justify-between">
              <button
                type="button"
                onClick={() => setCurrentStep(1)}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Back
              </button>
              <button
                type="button"
                onClick={() => setCurrentStep(3)}
                disabled={formData.items.length === 0}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
              >
                Review & Schedule
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Review and Submit */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900">Review Your Schedule</h3>
            
            <div className="bg-gray-50 p-6 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">{formData.title}</h4>
              {formData.description && (
                <p className="text-gray-600 mb-4">{formData.description}</p>
              )}
              <p className="text-sm text-gray-500">Timezone: {formData.timezone}</p>
            </div>

            <div className="space-y-4">
              <h5 className="font-medium text-gray-900">Content Items ({formData.items.length})</h5>
              {formData.items.map((item, index) => (
                <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <span className={`px-2 py-1 text-xs rounded-full ${getPlatformColor(item.platform)}`}>
                        {item.platform}
                      </span>
                      <span className="text-sm font-medium">{item.metadata.title || 'Untitled'}</span>
                    </div>
                    <p className="text-sm text-gray-500">
                      {formatDateTime(item.scheduledTime)}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setCurrentStep(2)}
                    className="text-blue-600 hover:text-blue-700 text-sm"
                  >
                    Edit
                  </button>
                </div>
              ))}
            </div>

            <div className="flex justify-between">
              <button
                type="button"
                onClick={() => setCurrentStep(2)}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={loading || !canSubmit}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Creating Schedule...
                  </>
                ) : (
                  <>
                    <Calendar className="w-4 h-4" />
                    Create Schedule
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  );
};

// =============================================================================
// PROGRESS MONITOR COMPONENT
// =============================================================================

interface ProgressMonitorProps {
  scheduleId: string;
  onComplete?: (result: any) => void;
  checkInterval?: number;
}

const ProgressMonitor: React.FC<ProgressMonitorProps> = ({
  scheduleId,
  onComplete,
  checkInterval = 5
}) => {
  const [schedule, setSchedule] = useState<ContentSchedule | null>(null);
  const [progress, setProgress] = useState(0);
  const [isMonitoring, setIsMonitoring] = useState(true);
  const { getScheduleStatus } = useSchedulingAPI();

  const fetchScheduleStatus = useCallback(async () => {
    const data = await getScheduleStatus(scheduleId);
    if (data) {
      setSchedule(data);
      
      const completed = data.completedItems;
      const total = data.totalItems;
      const progressPct = total > 0 ? (completed / total) * 100 : 0;
      setProgress(progressPct);
      
      if (data.status === 'completed' || data.status === 'failed' || data.status === 'canceled') {
        setIsMonitoring(false);
        onComplete?.(data);
      }
    }
  }, [scheduleId, getScheduleStatus, onComplete]);

  useEffect(() => {
    if (!isMonitoring) return;

    fetchScheduleStatus();
    
    const interval = setInterval(fetchScheduleStatus, checkInterval * 1000);
    return () => clearInterval(interval);
  }, [fetchScheduleStatus, checkInterval, isMonitoring]);

  if (!schedule) {
    return (
      <div className="flex items-center justify-center py-8">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Loading schedule...</span>
      </div>
    );
  }

  const completedItems = schedule.items.filter(item => item.status === 'published');
  const failedItems = schedule.items.filter(item => item.status === 'failed');
  const pendingItems = schedule.items.filter(item => item.status === 'pending' || item.status === 'scheduled');

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">{schedule.title}</h3>
        <div className="flex items-center gap-2">
          {isMonitoring && (
            <div className="flex items-center gap-2 text-sm text-green-600">
              <div className="w-2 h-2 bg-green-600 rounded-full animate-pulse" />
              Monitoring
            </div>
          )}
          <span className={`px-3 py-1 rounded-full text-sm border ${getStatusColor(schedule.status)}`}>
            {schedule.status}
          </span>
        </div>
      </div>

      {/* Overall Progress */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Overall Progress</span>
          <span className="text-sm text-gray-600">{Math.round(progress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div 
            className="bg-blue-600 h-3 rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex items-center justify-between mt-2 text-sm text-gray-600">
          <span>{completedItems.length} completed</span>
          <span>{failedItems.length} failed</span>
          <span>{pendingItems.length} pending</span>
        </div>
      </div>

      {/* Item Details */}
      <div className="space-y-3">
        <h4 className="font-medium text-gray-900">Content Items</h4>
        {schedule.items.map((item) => (
          <div key={item.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
            <div className="flex items-center gap-3">
              <span className={`px-2 py-1 text-xs rounded-full ${getPlatformColor(item.platform)}`}>
                {item.platform}
              </span>
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {item.metadata.title || `Content ${item.contentId}`}
                </p>
                <p className="text-xs text-gray-500">
                  {formatDateTime(item.scheduledTime)}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {item.status === 'running' && (
                <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
              )}
              {item.status === 'published' && (
                <CheckCircle className="w-4 h-4 text-green-500" />
              )}
              {item.status === 'failed' && (
                <AlertCircle className="w-4 h-4 text-red-500" />
              )}
              <span className={`px-2 py-1 text-xs rounded-full border ${getStatusColor(item.status)}`}>
                {item.status}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
        <div className="text-sm text-gray-500">
          Created: {formatDateTime(schedule.createdAt)}
        </div>
        <div className="flex items-center gap-2">
          {isMonitoring ? (
            <button
              onClick={() => setIsMonitoring(false)}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Stop Monitoring
            </button>
          ) : (
            <button
              onClick={() => setIsMonitoring(true)}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Resume Monitoring
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// =============================================================================
// SCHEDULE LIST COMPONENT
// =============================================================================

interface ScheduleListProps {
  onScheduleSelect: (scheduleId: string) => void;
  onCreateNew: () => void;
  refreshTrigger?: number;
}

const ScheduleList: React.FC<ScheduleListProps> = ({
  onScheduleSelect,
  onCreateNew,
  refreshTrigger = 0
}) => {
  const [schedules, setSchedules] = useState<ContentSchedule[]>([]);
  const [filteredSchedules, setFilteredSchedules] = useState<ContentSchedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterPlatform, setFilterPlatform] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'created' | 'updated' | 'title'>('created');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const { getSchedules } = useSchedulingAPI();

  const fetchSchedules = useCallback(async () => {
    setLoading(true);
    const data = await getSchedules();
    setSchedules(data);
    setLoading(false);
  }, [getSchedules]);

  useEffect(() => {
    fetchSchedules();
  }, [fetchSchedules, refreshTrigger]);

  useEffect(() => {
    let filtered = [...schedules];

    // Apply status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter(schedule => schedule.status === filterStatus);
    }

    // Apply platform filter
    if (filterPlatform !== 'all') {
      filtered = filtered.filter(schedule => 
        schedule.items.some(item => item.platform === filterPlatform)
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sortBy) {
        case 'title':
          aValue = a.title.toLowerCase();
          bValue = b.title.toLowerCase();
          break;
        case 'updated':
          aValue = new Date(a.updatedAt);
          bValue = new Date(b.updatedAt);
          break;
        default:
          aValue = new Date(a.createdAt);
          bValue = new Date(b.createdAt);
      }

      if (sortOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });

    setFilteredSchedules(filtered);
  }, [schedules, filterStatus, filterPlatform, sortBy, sortOrder]);

  const uniquePlatforms = Array.from(new Set(
    schedules.flatMap(schedule => 
      schedule.items.map(item => item.platform)
    )
  ));

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Loading schedules...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header and Actions */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Content Schedules</h2>
        <button
          onClick={onCreateNew}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          New Schedule
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">Filters:</span>
        </div>
        
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-3 py-1 border border-gray-300 rounded-md text-sm"
        >
          <option value="all">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="canceled">Canceled</option>
        </select>

        <select
          value={filterPlatform}
          onChange={(e) => setFilterPlatform(e.target.value)}
          className="px-3 py-1 border border-gray-300 rounded-md text-sm"
        >
          <option value="all">All Platforms</option>
          {uniquePlatforms.map(platform => (
            <option key={platform} value={platform}>
              {platform.charAt(0).toUpperCase() + platform.slice(1)}
            </option>
          ))}
        </select>

        <div className="flex items-center gap-2 ml-auto">
          <span className="text-sm text-gray-600">Sort by:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-2 py-1 border border-gray-300 rounded-md text-sm"
          >
            <option value="created">Created Date</option>
            <option value="updated">Updated Date</option>
            <option value="title">Title</option>
          </select>
          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="px-2 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
          >
            {sortOrder === 'asc' ? '↑' : '↓'}
          </button>
        </div>
      </div>

      {/* Schedule List */}
      {filteredSchedules.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Calendar className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p className="mb-4">
            {schedules.length === 0 ? 'No schedules created yet' : 'No schedules match your filters'}
          </p>
          {schedules.length === 0 && (
            <button
              onClick={onCreateNew}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Create Your First Schedule
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredSchedules.map((schedule) => {
            const completionRate = schedule.totalItems > 0 
              ? (schedule.completedItems / schedule.totalItems) * 100 
              : 0;

            return (
              <div
                key={schedule.id}
                className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => onScheduleSelect(schedule.id)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-1">{schedule.title}</h3>
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {schedule.description || 'No description'}
                    </p>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full border ${getStatusColor(schedule.status)}`}>
                    {schedule.status}
                  </span>
                </div>

                {/* Platform Pills */}
                <div className="flex flex-wrap gap-2 mb-4">
                  {Array.from(new Set(schedule.items.map(item => item.platform))).map(platform => (
                    <span
                      key={platform}
                      className={`px-2 py-1 text-xs rounded-full ${getPlatformColor(platform)}`}
                    >
                      {platform}
                    </span>
                  ))}
                </div>

                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-600">Progress</span>
                    <span className="text-xs text-gray-600">
                      {schedule.completedItems}/{schedule.totalItems}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${completionRate}%` }}
                    />
                  </div>
                </div>

                {/* Stats */}
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>Created {new Date(schedule.createdAt).toLocaleDateString()}</span>
                  <div className="flex items-center gap-2">
                    {schedule.failedItems > 0 && (
                      <span className="text-red-600">{schedule.failedItems} failed</span>
                    )}
                    <button 
                      className="text-blue-600 hover:text-blue-700"
                      onClick={(e) => {
                        e.stopPropagation();
                        onScheduleSelect(schedule.id);
                      }}
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

// =============================================================================
// MAIN SCHEDULING DASHBOARD COMPONENT
// =============================================================================

const SchedulingDashboard: React.FC = () => {
  const [currentView, setCurrentView] = useState<'list' | 'create' | 'detail' | 'recommendations'>('list');
  const [selectedScheduleId, setSelectedScheduleId] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const { error } = useSchedulingAPI();

  const handleScheduleCreated = (scheduleId: string) => {
    setSelectedScheduleId(scheduleId);
    setCurrentView('detail');
    setRefreshTrigger(prev => prev + 1);
  };

  const handleScheduleSelect = (scheduleId: string) => {
    setSelectedScheduleId(scheduleId);
    setCurrentView('detail');
  };

  const handleBackToList = () => {
    setCurrentView('list');
    setSelectedScheduleId(null);
    setRefreshTrigger(prev => prev + 1);
  };

  const handleRecommendationSchedule = (recommendation: Recommendation) => {
    // Pre-fill the schedule creator with recommendation data
    setCurrentView('create');
  };

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Connection Error</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Calendar className="w-8 h-8 text-blue-600" />
              <h1 className="text-xl font-semibold text-gray-900">
                AI Content Scheduling
              </h1>
            </div>
            
            <nav className="flex items-center gap-4">
              <button
                onClick={() => setCurrentView('list')}
                className={`px-3 py-2 rounded-lg text-sm font-medium ${
                  currentView === 'list'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <BarChart3 className="w-4 h-4 mr-2 inline" />
                Dashboard
              </button>
              <button
                onClick={() => setCurrentView('recommendations')}
                className={`px-3 py-2 rounded-lg text-sm font-medium ${
                  currentView === 'recommendations'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <Target className="w-4 h-4 mr-2 inline" />
                Recommendations
              </button>
              <button
                onClick={() => setCurrentView('create')}
                className={`px-3 py-2 rounded-lg text-sm font-medium ${
                  currentView === 'create'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <Plus className="w-4 h-4 mr-2 inline" />
                Create
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentView === 'list' && (
          <ScheduleList
            onScheduleSelect={handleScheduleSelect}
            onCreateNew={() => setCurrentView('create')}
            refreshTrigger={refreshTrigger}
          />
        )}

        {currentView === 'create' && (
          <div className="mb-6">
            <button
              onClick={handleBackToList}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
            >
              ← Back to Dashboard
            </button>
            <ScheduleCreator
              onScheduleCreated={handleScheduleCreated}
              onCancel={handleBackToList}
            />
          </div>
        )}

        {currentView === 'detail' && selectedScheduleId && (
          <div className="mb-6">
            <button
              onClick={handleBackToList}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
            >
              ← Back to Dashboard
            </button>
            <ProgressMonitor
              scheduleId={selectedScheduleId}
              onComplete={() => setRefreshTrigger(prev => prev + 1)}
            />
          </div>
        )}

        {currentView === 'recommendations' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">Optimal Posting Times</h2>
              <button
                onClick={handleBackToList}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
              >
                <Calendar className="w-4 h-4" />
                Back to Dashboard
              </button>
            </div>
            
            <RecommendationViewer
              platforms={PLATFORMS.map(p => p.id)}
              onScheduleClick={handleRecommendationSchedule}
            />
          </div>
        )}
      </main>
    </div>
  );
};

// =============================================================================
// EXPORTS
// =============================================================================

export default SchedulingDashboard;
export {
  SchedulingDashboard,
  ScheduleCreator,
  RecommendationViewer,
  ProgressMonitor,
  ScheduleList,
  PlatformSelector,
  useSchedulingAPI
};

// =============================================================================
// USAGE EXAMPLES
// =============================================================================

/**
 * Basic usage example:
 * 
 * import SchedulingDashboard from './react_scheduling_example';
 * 
 * function App() {
 *   return (
 *     <div className="App">
 *       <SchedulingDashboard />
 *     </div>
 *   );
 * }
 * 
 * Advanced usage with custom API endpoints:
 * 
 * import { useSchedulingAPI } from './react_scheduling_example';
 * 
 * function CustomComponent() {
 *   const api = useSchedulingAPI();
 *   
 *   const handleGetRecommendations = async () => {
 *     const recommendations = await api.getRecommendations(['youtube', 'linkedin'], 10);
 *     console.log(recommendations);
 *   };
 *   
 *   const handleCreateSchedule = async () => {
 *     const scheduleId = await api.createSchedule({
 *       title: 'My Schedule',
 *       timezone: 'America/New_York',
 *       items: [...]
 *     });
 *     console.log('Created:', scheduleId);
 *   };
 * 
 *   return (
 *     <div>
 *       <button onClick={handleGetRecommendations}>Get Recommendations</button>
 *       <button onClick={handleCreateSchedule}>Create Schedule</button>
 *     </div>
 *   );
 * }
 */
