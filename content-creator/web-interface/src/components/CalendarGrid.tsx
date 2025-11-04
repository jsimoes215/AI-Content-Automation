import React, { useState, useMemo } from 'react';
import { ChevronLeft, ChevronRight, Plus, Filter, Grid3X3, List } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import CalendarEvent from './CalendarEvent';
import { cn } from '@/lib/utils';

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

interface CalendarGridProps {
  events: CalendarEvent[];
  currentDate: Date;
  onDateChange: (date: Date) => void;
  onEventClick?: (event: CalendarEvent) => void;
  onEventEdit?: (event: CalendarEvent) => void;
  onCreateEvent?: (date: Date) => void;
  onRefresh?: () => void;
  view?: 'month' | 'week' | 'day';
  onViewChange?: (view: 'month' | 'week' | 'day') => void;
  loading?: boolean;
  platforms?: string[];
  selectedPlatforms?: string[];
  onPlatformFilterChange?: (platforms: string[]) => void;
}

export default function CalendarGrid({
  events,
  currentDate,
  onDateChange,
  onEventClick,
  onEventEdit,
  onCreateEvent,
  onRefresh,
  view = 'month',
  onViewChange,
  loading = false,
  platforms = [],
  selectedPlatforms = [],
  onPlatformFilterChange
}: CalendarGridProps) {
  const [showFilters, setShowFilters] = useState(false);

  // Generate calendar days
  const calendarDays = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    const firstDayOfMonth = new Date(year, month, 1);
    const lastDayOfMonth = new Date(year, month + 1, 0);
    const firstDayOfWeek = firstDayOfMonth.getDay();
    const daysInMonth = lastDayOfMonth.getDate();
    
    const days = [];
    
    // Add days from previous month to fill the first week
    for (let i = firstDayOfWeek - 1; i >= 0; i--) {
      const day = new Date(year, month, -i);
      days.push({ date: day, isCurrentMonth: false });
    }
    
    // Add days of current month
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      days.push({ date, isCurrentMonth: true });
    }
    
    // Add days from next month to complete the grid (6 rows × 7 days = 42 cells)
    const remainingCells = 42 - days.length;
    for (let day = 1; day <= remainingCells; day++) {
      const date = new Date(year, month + 1, day);
      days.push({ date, isCurrentMonth: false });
    }
    
    return days;
  }, [currentDate]);

  // Get events for a specific date
  const getEventsForDate = (date: Date) => {
    const dateStr = date.toISOString().split('T')[0];
    return events.filter(event => {
      const eventDate = new Date(event.scheduled_time).toISOString().split('T')[0];
      return eventDate === dateStr;
    }).sort((a, b) => 
      new Date(a.scheduled_time).getTime() - new Date(b.scheduled_time).getTime()
    );
  };

  // Get today's events
  const getTodayEvents = () => {
    const today = new Date().toISOString().split('T')[0];
    return events.filter(event => 
      event.scheduled_time.startsWith(today)
    );
  };

  // Navigation functions
  const goToPreviousPeriod = () => {
    const newDate = new Date(currentDate);
    switch (view) {
      case 'month':
        newDate.setMonth(newDate.getMonth() - 1);
        break;
      case 'week':
        newDate.setDate(newDate.getDate() - 7);
        break;
      case 'day':
        newDate.setDate(newDate.getDate() - 1);
        break;
    }
    onDateChange(newDate);
  };

  const goToNextPeriod = () => {
    const newDate = new Date(currentDate);
    switch (view) {
      case 'month':
        newDate.setMonth(newDate.getMonth() + 1);
        break;
      case 'week':
        newDate.setDate(newDate.getDate() + 7);
        break;
      case 'day':
        newDate.setDate(newDate.getDate() + 1);
        break;
    }
    onDateChange(newDate);
  };

  const goToToday = () => {
    onDateChange(new Date());
  };

  // Filter events by selected platforms
  const filteredEvents = selectedPlatforms.length > 0 
    ? events.filter(event => selectedPlatforms.includes(event.platform))
    : events;

  // Get platform statistics
  const platformStats = platforms.reduce((acc, platform) => {
    const count = filteredEvents.filter(event => event.platform === platform).length;
    acc[platform] = count;
    return acc;
  }, {} as Record<string, number>);

  const todayEvents = getTodayEvents();

  if (loading) {
    return (
      <Card className="h-[600px]">
        <CardContent className="flex items-center justify-center h-full">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Calendar Header */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <CardTitle className="text-2xl">
                {currentDate.toLocaleDateString('en-US', { 
                  month: 'long', 
                  year: 'numeric' 
                })}
              </CardTitle>
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm" onClick={goToPreviousPeriod}>
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <Button variant="outline" size="sm" onClick={goToToday}>
                  Today
                </Button>
                <Button variant="outline" size="sm" onClick={goToNextPeriod}>
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {/* View Toggle */}
              <div className="flex items-center space-x-1">
                <Button
                  variant={view === 'month' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => onViewChange?.('month')}
                >
                  Month
                </Button>
                <Button
                  variant={view === 'week' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => onViewChange?.('week')}
                >
                  Week
                </Button>
                <Button
                  variant={view === 'day' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => onViewChange?.('day')}
                >
                  Day
                </Button>
              </div>

              <Button variant="outline" size="sm" onClick={() => setShowFilters(!showFilters)}>
                <Filter className="w-4 h-4 mr-2" />
                Filter
              </Button>

              <Button variant="outline" size="sm" onClick={onRefresh}>
                <Grid3X3 className="w-4 h-4 mr-2" />
                Refresh
              </Button>

              <Button onClick={() => onCreateEvent?.(new Date())}>
                <Plus className="w-4 h-4 mr-2" />
                New Event
              </Button>
            </div>
          </div>

          {/* Today's Summary */}
          {todayEvents.length > 0 && (
            <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <h3 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
                Today's Schedule ({todayEvents.length} events)
              </h3>
              <div className="flex flex-wrap gap-2">
                {todayEvents.slice(0, 3).map(event => (
                  <Badge key={event.id} variant="outline" className="text-xs">
                    {event.platform} - {new Date(event.scheduled_time).toLocaleTimeString('en-US', {
                      hour: '2-digit',
                      minute: '2-digit',
                      hour12: false
                    })}
                  </Badge>
                ))}
                {todayEvents.length > 3 && (
                  <Badge variant="outline" className="text-xs">
                    +{todayEvents.length - 3} more
                  </Badge>
                )}
              </div>
            </div>
          )}

          {/* Filters */}
          {showFilters && platforms.length > 0 && (
            <div className="mt-4 p-4 border rounded-lg">
              <h4 className="font-medium mb-3">Filter by Platform</h4>
              <div className="flex flex-wrap gap-2">
                {platforms.map(platform => (
                  <Button
                    key={platform}
                    variant={selectedPlatforms.includes(platform) ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => {
                      const newSelection = selectedPlatforms.includes(platform)
                        ? selectedPlatforms.filter(p => p !== platform)
                        : [...selectedPlatforms, platform];
                      onPlatformFilterChange?.(newSelection);
                    }}
                    className="capitalize"
                  >
                    {platform} ({platformStats[platform] || 0})
                  </Button>
                ))}
              </div>
            </div>
          )}
        </CardHeader>
      </Card>

      {/* Calendar Grid */}
      <Card>
        <CardContent className="p-0">
          {/* Week headers */}
          <div className="grid grid-cols-7 border-b">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div key={day} className="p-4 text-center font-medium text-gray-500 dark:text-gray-400 border-r last:border-r-0">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar days */}
          <div className="grid grid-cols-7">
            {calendarDays.map(({ date, isCurrentMonth }, index) => {
              const dayEvents = getEventsForDate(date);
              const isToday = date.toDateString() === new Date().toDateString();
              
              return (
                <div
                  key={index}
                  className={cn(
                    "min-h-[120px] border-r border-b last:border-r-0 p-2 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors",
                    !isCurrentMonth && "bg-gray-50 dark:bg-gray-900/50 text-gray-400",
                    isToday && "bg-blue-50 dark:bg-blue-900/20"
                  )}
                  onClick={() => onCreateEvent?.(date)}
                >
                  <div className={cn(
                    "text-sm font-medium mb-2",
                    isToday && "text-blue-600 dark:text-blue-400",
                    !isCurrentMonth && "text-gray-400"
                  )}>
                    {date.getDate()}
                  </div>
                  
                  <div className="space-y-1">
                    {dayEvents.slice(0, 3).map(event => (
                      <div
                        key={event.id}
                        onClick={(e) => {
                          e.stopPropagation();
                          onEventClick?.(event);
                        }}
                        className={cn(
                          "text-xs p-1 rounded truncate cursor-pointer hover:opacity-80 transition-opacity",
                          event.state === 'published' && "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
                          event.state === 'scheduled' && "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
                          event.state === 'pending' && "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300",
                          event.state === 'failed' && "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300"
                        )}
                      >
                        {new Date(event.scheduled_time).toLocaleTimeString('en-US', {
                          hour: '2-digit',
                          minute: '2-digit',
                          hour12: false
                        })} {event.platform}
                      </div>
                    ))}
                    {dayEvents.length > 3 && (
                      <div className="text-xs text-gray-500 dark:text-gray-400 p-1">
                        +{dayEvents.length - 3} more
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Today's Events Detail */}
      {todayEvents.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Today's Events
              <Badge variant="outline">{todayEvents.length} events</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {todayEvents.map(event => (
              <CalendarEvent
                key={event.id}
                event={event}
                onEventClick={onEventClick}
                onEventEdit={onEventEdit}
              />
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}