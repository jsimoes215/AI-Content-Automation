import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar as CalendarIcon, Plus, Settings, Download, Upload, RefreshCw } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import CalendarGrid from '../components/CalendarGrid';
import apiClient from '../lib/api';

interface CalendarEvent {
  id: string;
  content_id: string;
  platform: string;
  state: 'pending' | 'scheduled' | 'published' | 'failed' | 'skipped' | 'canceled';
  scheduled_time: string;
  title?: string;
  metadata?: {
    campaign_id?: string;
    format?: string;
    content_type?: string;
  };
  published_time?: string;
  errors?: string[];
  created_at: string;
  updated_at: string;
}

interface Schedule {
  id: string;
  title: string;
  state: string;
  timezone: string;
  items_total: number;
  items_completed: number;
  items_pending: number;
  items_failed: number;
  created_at: string;
  updated_at: string;
}

interface Platform {
  id: string;
  name: string;
  supports: string[];
}

export default function ContentCalendar() {
  const navigate = useNavigate();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<'month' | 'week' | 'day'>('month');
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    loadCalendarData();
  }, [currentDate, view, selectedPlatforms]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadPlatforms(),
        loadSchedules(),
      ]);
    } catch (error) {
      console.error('Failed to load initial data:', error);
      setError('Failed to load calendar data');
    } finally {
      setLoading(false);
    }
  };

  const loadCalendarData = async () => {
    try {
      setRefreshing(true);
      
      // Calculate date range based on current view
      const startDate = new Date(currentDate);
      const endDate = new Date(currentDate);
      
      switch (view) {
        case 'month':
          startDate.setDate(1);
          startDate.setDate(startDate.getDate() - startDate.getDay());
          endDate.setMonth(endDate.getMonth() + 1, 0);
          endDate.setDate(endDate.getDate() + (6 - endDate.getDay()));
          break;
        case 'week':
          startDate.setDate(startDate.getDate() - startDate.getDay());
          endDate.setDate(endDate.getDate() + (6 - endDate.getDay()));
          break;
        case 'day':
          // Just load events for the current day
          break;
      }

      // Load events from all schedules in the date range
      const allEvents: CalendarEvent[] = [];
      
      for (const schedule of schedules) {
        try {
          const scheduleData = await apiClient.getSchedule(schedule.id, {
            expand: ['items'],
            page_size: 1000,
            sort: 'created_at',
            order: 'asc'
          });

          if (scheduleData.data?.items) {
            const scheduleEvents = scheduleData.data.items
              .filter((item: any) => {
                const itemDate = new Date(item.scheduled_time);
                return itemDate >= startDate && itemDate <= endDate;
              })
              .map((item: any) => ({
                ...item,
                title: scheduleData.data?.title || 'Scheduled Content',
                schedule_id: schedule.id
              }));
            
            allEvents.push(...scheduleEvents);
          }
        } catch (error) {
          console.warn(`Failed to load events for schedule ${schedule.id}:`, error);
        }
      }

      setEvents(allEvents);
    } catch (error) {
      console.error('Failed to load calendar data:', error);
      setError('Failed to load calendar events');
    } finally {
      setRefreshing(false);
    }
  };

  const loadPlatforms = async () => {
    try {
      const response = await apiClient.getSupportedPlatforms();
      if (response.data) {
        setPlatforms(response.data);
        // Auto-select all platforms initially
        setSelectedPlatforms(response.data.map((p: Platform) => p.id));
      }
    } catch (error) {
      console.error('Failed to load platforms:', error);
      // Use default platforms if API fails
      setPlatforms([
        { id: 'youtube', name: 'YouTube', supports: ['long_form', 'shorts'] },
        { id: 'instagram', name: 'Instagram', supports: ['posts', 'stories'] },
        { id: 'twitter', name: 'Twitter', supports: ['tweets'] },
        { id: 'tiktok', name: 'TikTok', supports: ['videos'] }
      ]);
      setSelectedPlatforms(['youtube', 'instagram', 'twitter', 'tiktok']);
    }
  };

  const loadSchedules = async () => {
    try {
      // For now, we'll get a few recent schedules
      // In a real implementation, you'd have a proper list endpoint
      const mockSchedules: Schedule[] = [
        {
          id: 'sched_1',
          title: 'Weekly Content Mix',
          state: 'running',
          timezone: 'UTC',
          items_total: 15,
          items_completed: 8,
          items_pending: 5,
          items_failed: 2,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: 'sched_2',
          title: 'Product Launch Campaign',
          state: 'completed',
          timezone: 'UTC',
          items_total: 8,
          items_completed: 8,
          items_pending: 0,
          items_failed: 0,
          created_at: new Date(Date.now() - 86400000).toISOString(),
          updated_at: new Date(Date.now() - 86400000).toISOString()
        }
      ];
      
      setSchedules(mockSchedules);
    } catch (error) {
      console.error('Failed to load schedules:', error);
    }
  };

  const handleEventClick = (event: CalendarEvent) => {
    // Navigate to event details or open modal
    console.log('Event clicked:', event);
    // You could open a modal here or navigate to a detail page
  };

  const handleEventEdit = (event: CalendarEvent) => {
    console.log('Event edit requested:', event);
    // Implement edit functionality
  };

  const handleCreateEvent = (date: Date) => {
    console.log('Create event requested for:', date);
    // Open create event modal or navigate to create page
    navigate('/bulk-jobs', { 
      state: { 
        prefillDate: date.toISOString(),
        selectedPlatforms 
      } 
    });
  };

  const handleRefresh = () => {
    loadCalendarData();
  };

  const getStatusStats = () => {
    const stats = events.reduce((acc, event) => {
      acc[event.state] = (acc[event.state] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      total: events.length,
      published: stats.published || 0,
      scheduled: stats.scheduled || 0,
      pending: stats.pending || 0,
      failed: stats.failed || 0
    };
  };

  const stats = getStatusStats();

  // Connect to WebSocket for real-time updates
  useEffect(() => {
    const handleWebSocketMessage = (data: any) => {
      switch (data.type) {
        case 'schedule.state_changed':
        case 'schedule.progress':
        case 'item.published':
        case 'optimization.completed':
          // Refresh calendar data when updates come in
          loadCalendarData();
          break;
      }
    };

    // Connect to scheduling WebSocket
    apiClient.connectSchedulingWebSocket(undefined, handleWebSocketMessage);

    return () => {
      apiClient.disconnectWebSocket();
    };
  }, [schedules]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center">
            <CalendarIcon className="w-8 h-8 mr-3" />
            Content Calendar
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Manage and schedule content across all platforms
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            onClick={() => navigate('/bulk-jobs')}
            className="flex items-center"
          >
            <Upload className="w-4 h-4 mr-2" />
            Import Content
          </Button>
          
          <Button
            variant="outline"
            onClick={() => console.log('Export calendar')}
            className="flex items-center"
          >
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          
          <Button
            variant="outline"
            onClick={() => console.log('Settings')}
            className="flex items-center"
          >
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Events</p>
                <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">{stats.total}</p>
              </div>
              <div className="p-3 rounded-lg bg-blue-100 dark:bg-blue-900/30">
                <CalendarIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Published</p>
                <p className="mt-2 text-3xl font-bold text-green-600 dark:text-green-400">{stats.published}</p>
              </div>
              <div className="p-3 rounded-lg bg-green-100 dark:bg-green-900/30">
                <div className="w-6 h-6 bg-green-600 dark:bg-green-400 rounded"></div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Scheduled</p>
                <p className="mt-2 text-3xl font-bold text-blue-600 dark:text-blue-400">{stats.scheduled}</p>
              </div>
              <div className="p-3 rounded-lg bg-blue-100 dark:bg-blue-900/30">
                <div className="w-6 h-6 bg-blue-600 dark:bg-blue-400 rounded"></div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Failed</p>
                <p className="mt-2 text-3xl font-bold text-red-600 dark:text-red-400">{stats.failed}</p>
              </div>
              <div className="p-3 rounded-lg bg-red-100 dark:bg-red-900/30">
                <div className="w-6 h-6 bg-red-600 dark:bg-red-400 rounded"></div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Platform Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Platform Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {platforms.map(platform => {
              const platformEvents = events.filter(event => event.platform === platform.id);
              const publishedCount = platformEvents.filter(e => e.state === 'published').length;
              
              return (
                <div key={platform.id} className="text-center p-4 border rounded-lg">
                  <div className="font-medium capitalize mb-2">{platform.name}</div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                    {platformEvents.length}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {publishedCount} published
                  </div>
                  <Badge variant="outline" className="mt-2 text-xs">
                    {platform.supports.join(', ')}
                  </Badge>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Calendar Grid */}
      <CalendarGrid
        events={events}
        currentDate={currentDate}
        onDateChange={setCurrentDate}
        onEventClick={handleEventClick}
        onEventEdit={handleEventEdit}
        onCreateEvent={handleCreateEvent}
        onRefresh={handleRefresh}
        view={view}
        onViewChange={setView}
        loading={loading}
        platforms={platforms.map(p => p.id)}
        selectedPlatforms={selectedPlatforms}
        onPlatformFilterChange={setSelectedPlatforms}
      />

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50 dark:bg-red-900/20 dark:border-red-800">
          <CardContent className="p-4">
            <div className="flex items-center">
              <div className="text-red-600 dark:text-red-400">{error}</div>
              <Button
                variant="outline"
                size="sm"
                className="ml-auto"
                onClick={() => setError(null)}
              >
                Dismiss
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}