import React from 'react';
import { Calendar as CalendarIcon, Clock, Youtube, Instagram, Twitter, CheckCircle, AlertCircle, Play } from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
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

interface CalendarEventProps {
  event: CalendarEvent;
  onEventClick?: (event: CalendarEvent) => void;
  onEventEdit?: (event: CalendarEvent) => void;
  className?: string;
}

export default function CalendarEvent({ event, onEventClick, onEventEdit, className }: CalendarEventProps) {
  const getPlatformIcon = (platform: string) => {
    switch (platform.toLowerCase()) {
      case 'youtube':
        return <Youtube className="w-4 h-4" />;
      case 'instagram':
        return <Instagram className="w-4 h-4" />;
      case 'twitter':
      case 'x':
        return <Twitter className="w-4 h-4" />;
      default:
        return <CalendarIcon className="w-4 h-4" />;
    }
  };

  const getPlatformColor = (platform: string) => {
    switch (platform.toLowerCase()) {
      case 'youtube':
        return 'text-red-600 bg-red-50 border-red-200 dark:text-red-400 dark:bg-red-900/20 dark:border-red-800';
      case 'instagram':
        return 'text-pink-600 bg-pink-50 border-pink-200 dark:text-pink-400 dark:bg-pink-900/20 dark:border-pink-800';
      case 'twitter':
      case 'x':
        return 'text-blue-600 bg-blue-50 border-blue-200 dark:text-blue-400 dark:bg-blue-900/20 dark:border-blue-800';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200 dark:text-gray-400 dark:bg-gray-900/20 dark:border-gray-800';
    }
  };

  const getStateColor = (state: string) => {
    switch (state) {
      case 'published':
        return 'text-green-600 bg-green-50 border-green-200 dark:text-green-400 dark:bg-green-900/20 dark:border-green-800';
      case 'scheduled':
        return 'text-blue-600 bg-blue-50 border-blue-200 dark:text-blue-400 dark:bg-blue-900/20 dark:border-blue-800';
      case 'pending':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200 dark:text-yellow-400 dark:bg-yellow-900/20 dark:border-yellow-800';
      case 'failed':
        return 'text-red-600 bg-red-50 border-red-200 dark:text-red-400 dark:bg-red-900/20 dark:border-red-800';
      case 'skipped':
        return 'text-gray-600 bg-gray-50 border-gray-200 dark:text-gray-400 dark:bg-gray-900/20 dark:border-gray-800';
      case 'canceled':
        return 'text-red-600 bg-red-50 border-red-200 dark:text-red-400 dark:bg-red-900/20 dark:border-red-800';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200 dark:text-gray-400 dark:bg-gray-900/20 dark:border-gray-800';
    }
  };

  const getStateIcon = (state: string) => {
    switch (state) {
      case 'published':
        return <CheckCircle className="w-3 h-3" />;
      case 'failed':
        return <AlertCircle className="w-3 h-3" />;
      case 'scheduled':
      case 'pending':
        return <Clock className="w-3 h-3" />;
      default:
        return <Play className="w-3 h-3" />;
    }
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };

  return (
    <Card 
      className={cn(
        "cursor-pointer hover:shadow-md transition-all duration-200 border-l-4",
        getPlatformColor(event.platform),
        className
      )}
      onClick={() => onEventClick?.(event)}
    >
      <CardContent className="p-3">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center space-x-2">
            {getPlatformIcon(event.platform)}
            <span className="font-medium text-sm capitalize">
              {event.platform}
            </span>
          </div>
          <Badge 
            variant="outline" 
            className={cn(
              "flex items-center space-x-1 text-xs",
              getStateColor(event.state)
            )}
          >
            {getStateIcon(event.state)}
            <span className="capitalize">{event.state}</span>
          </Badge>
        </div>

        <div className="space-y-1">
          <div className="flex items-center text-xs text-gray-600 dark:text-gray-400">
            <Clock className="w-3 h-3 mr-1" />
            <span>{formatTime(event.scheduled_time)}</span>
          </div>

          {event.metadata?.content_type && (
            <div className="text-xs text-gray-500 dark:text-gray-400 capitalize">
              {event.metadata.content_type.replace('_', ' ')}
            </div>
          )}

          {event.title && (
            <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
              {event.title}
            </div>
          )}

          {event.errors && event.errors.length > 0 && (
            <div className="text-xs text-red-600 dark:text-red-400 mt-1">
              {event.errors.length} error{event.errors.length > 1 ? 's' : ''}
            </div>
          )}
        </div>

        {event.published_time && (
          <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
            <div className="text-xs text-green-600 dark:text-green-400">
              Published: {formatDateTime(event.published_time)}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}