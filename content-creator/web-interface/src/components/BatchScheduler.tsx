import { useState } from 'react';
import { 
  X, 
  Calendar, 
  Clock, 
  Settings, 
  Palette, 
  CheckCircle, 
  AlertCircle, 
  Upload,
  CalendarDays,
  Zap,
  Target,
  Filter,
  RefreshCw,
  FileSpreadsheet
} from 'lucide-react';
import apiClient from '../lib/api';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

interface BatchSchedulerProps {
  isOpen: boolean;
  onClose: () => void;
  onJobScheduled: (job: any) => void;
}

interface SheetConnection {
  sheet_id: string;
  range: string;
  tenant_id: string;
  status: string;
  last_validated_at: string;
  sample?: {
    row_count: number;
    columns: string[];
  };
}

interface SchedulingRule {
  id: string;
  name: string;
  type: 'time_based' | 'content_based' | 'priority_based';
  enabled: boolean;
  settings: {
    time_window?: string;
    days_of_week?: number[];
    max_concurrent?: number;
    min_interval_ms?: number;
    content_tags?: string[];
    priority_threshold?: 'low' | 'normal' | 'high';
  };
}

export default function BatchScheduler({ isOpen, onClose, onJobScheduled }: BatchSchedulerProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [sheetConnection, setSheetConnection] = useState<SheetConnection | null>(null);
  const [connectLoading, setConnectLoading] = useState(false);
  const [optimizationLoading, setOptimizationLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    // Job Details
    title: '',
    priority: 'normal' as 'low' | 'normal' | 'high',
    processing_deadline_ms: 7200000, // 2 hours default
    callback_url: '',
    
    // Sheet Connection
    sheet_id: '',
    range: 'A1:Z1000',
    
    // Output Configuration
    format: 'mp4' as 'mp4' | 'mov' | 'webm',
    video_codec: 'h264' as 'h264' | 'h265' | 'vp9',
    audio_codec: 'aac' as 'aac' | 'opus',
    resolution: '1080p' as '720p' | '1080p' | '4k',
    output_bucket: '',
    
    // Template
    template_id: '',
    overrides: {
      style: 'modern',
      voice: 'female',
    },

    // Scheduling Configuration
    scheduling_mode: 'smart' as 'smart' | 'time_based' | 'content_based' | 'manual',
    start_immediately: false,
    schedule_start_time: '',
    schedule_end_time: '',
    optimization_level: 'balanced' as 'speed' | 'balanced' | 'quality',
    max_concurrent_jobs: 3,
    priority_queue: false,
    
    // Advanced Scheduling
    scheduling_rules: [] as SchedulingRule[],
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [schedulingTips, setSchedulingTips] = useState<string[]>([]);

  if (!isOpen) return null;

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleNestedInputChange = (parent: string, field: string, value: any) => {
    setFormData(prev => {
      const parentData = prev[parent as keyof typeof prev] as Record<string, any>;
      return {
        ...prev,
        [parent]: {
          ...parentData,
          [field]: value,
        },
      };
    });
  };

  const handleSchedulingRuleChange = (ruleId: string, field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      scheduling_rules: prev.scheduling_rules.map(rule => 
        rule.id === ruleId 
          ? { ...rule, [field]: value }
          : rule
      )
    }));
  };

  const validateStep = (step: number): boolean => {
    const newErrors: Record<string, string> = {};

    switch (step) {
      case 1:
        if (!formData.sheet_id.trim()) {
          newErrors.sheet_id = 'Sheet ID is required';
        }
        if (!formData.range.trim()) {
          newErrors.range = 'Range is required';
        }
        break;
      
      case 2:
        if (!formData.output_bucket.trim()) {
          newErrors.output_bucket = 'Output bucket is required';
        }
        if (!formData.template_id.trim()) {
          newErrors.template_id = 'Template ID is required';
        }
        break;
      
      case 3:
        if (!formData.title.trim()) {
          newErrors.title = 'Title is required';
        }
        if (formData.callback_url && !isValidUrl(formData.callback_url)) {
          newErrors.callback_url = 'Please enter a valid URL';
        }
        break;
      
      case 4:
        if (!formData.start_immediately && !formData.schedule_start_time) {
          newErrors.schedule_start_time = 'Schedule start time is required when not starting immediately';
        }
        if (formData.schedule_start_time && formData.schedule_end_time && 
            new Date(formData.schedule_start_time) >= new Date(formData.schedule_end_time)) {
          newErrors.schedule_end_time = 'End time must be after start time';
        }
        if (formData.max_concurrent_jobs < 1 || formData.max_concurrent_jobs > 10) {
          newErrors.max_concurrent_jobs = 'Concurrent jobs must be between 1 and 10';
        }
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const isValidUrl = (url: string): boolean => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      if (currentStep === 4) {
        generateSchedulingTips();
      }
      setCurrentStep(prev => Math.min(prev + 1, 5));
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const generateSchedulingTips = async () => {
    setOptimizationLoading(true);
    try {
      // Generate scheduling optimization tips based on form data
      const tips = [];
      
      if (formData.scheduling_mode === 'smart') {
        tips.push('🚀 Smart scheduling will automatically optimize processing times based on system load');
        tips.push('⚡ Batch processing will be distributed across available resources');
        tips.push('📊 Content will be prioritized based on engagement metrics');
      }
      
      if (formData.optimization_level === 'speed') {
        tips.push('⚡ Speed optimization will use maximum parallel processing');
        tips.push('🎯 Lower quality settings will be used for faster generation');
      } else if (formData.optimization_level === 'quality') {
        tips.push('🎨 Quality optimization will use maximum quality settings');
        tips.push('⏳ Processing may take longer but results will be higher quality');
      }
      
      if (formData.max_concurrent_jobs > 5) {
        tips.push('⚠️ High concurrent job count may impact system performance');
      }
      
      if (formData.priority_queue) {
        tips.push('⭐ Priority queue enabled - jobs will be processed before others');
      }
      
      tips.push('📅 Scheduling will automatically handle rate limits and resource constraints');
      
      setSchedulingTips(tips);
    } catch (error) {
      console.error('Failed to generate scheduling tips:', error);
    } finally {
      setOptimizationLoading(false);
    }
  };

  const handleConnectSheet = async () => {
    if (!validateStep(1)) return;
    
    setConnectLoading(true);
    try {
      const response = await apiClient.connectSheet({
        sheet_id: formData.sheet_id,
        range: formData.range,
        share_permissions: 'read',
      });
      
      setSheetConnection(response.data);
      setCurrentStep(2);
    } catch (error) {
      console.error('Failed to connect sheet:', error);
      setErrors({ sheet_connection: 'Failed to connect to sheet. Please check the sheet ID and permissions.' });
    } finally {
      setConnectLoading(false);
    }
  };

  const handleScheduleJob = async () => {
    if (!validateStep(4)) return;
    
    setLoading(true);
    try {
      const jobData = {
        title: formData.title,
        priority: formData.priority,
        processing_deadline_ms: formData.processing_deadline_ms,
        callback_url: formData.callback_url || undefined,
        input_source: {
          type: 'sheet' as const,
          sheet_id: formData.sheet_id,
          range: formData.range,
        },
        output: {
          format: formData.format,
          video_codec: formData.video_codec,
          audio_codec: formData.audio_codec,
          resolution: formData.resolution,
          output_bucket: formData.output_bucket,
        },
        template: {
          template_id: formData.template_id,
          overrides: formData.overrides,
        },
        scheduling: {
          mode: formData.scheduling_mode,
          start_immediately: formData.start_immediately,
          schedule_start_time: formData.start_immediately ? null : formData.schedule_start_time,
          schedule_end_time: formData.schedule_end_time || null,
          optimization_level: formData.optimization_level,
          max_concurrent_jobs: formData.max_concurrent_jobs,
          priority_queue: formData.priority_queue,
          scheduling_rules: formData.scheduling_rules.filter(rule => rule.enabled),
        },
      };

      const response = await apiClient.createBulkJob(jobData);
      onJobScheduled(response.data);
      onClose();
      
      // Reset form
      resetForm();
    } catch (error) {
      console.error('Failed to schedule job:', error);
      setErrors({ creation: 'Failed to schedule job. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setCurrentStep(1);
    setFormData({
      title: '',
      priority: 'normal',
      processing_deadline_ms: 7200000,
      callback_url: '',
      sheet_id: '',
      range: 'A1:Z1000',
      format: 'mp4',
      video_codec: 'h264',
      audio_codec: 'aac',
      resolution: '1080p',
      output_bucket: '',
      template_id: '',
      overrides: { style: 'modern', voice: 'female' },
      scheduling_mode: 'smart',
      start_immediately: false,
      schedule_start_time: '',
      schedule_end_time: '',
      optimization_level: 'balanced',
      max_concurrent_jobs: 3,
      priority_queue: false,
      scheduling_rules: [],
    });
    setSheetConnection(null);
    setErrors({});
    setSchedulingTips([]);
  };

  const steps = [
    { number: 1, title: 'Connect Sheet', icon: FileSpreadsheet },
    { number: 2, title: 'Output Config', icon: Settings },
    { number: 3, title: 'Job Details', icon: Palette },
    { number: 4, title: 'Scheduling', icon: CalendarDays },
    { number: 5, title: 'Review', icon: CheckCircle },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-900 rounded-xl max-w-5xl w-full mx-4 max-h-[95vh] overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-800">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Schedule Batch Jobs
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Smart scheduling for bulk content generation
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Steps Indicator */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.number} className="flex items-center">
                <div
                  className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors ${
                    currentStep >= step.number
                      ? 'bg-blue-600 border-blue-600 text-white'
                      : 'border-gray-300 text-gray-500'
                  }`}
                >
                  <step.icon className="w-5 h-5" />
                </div>
                <span
                  className={`ml-2 text-sm font-medium ${
                    currentStep >= step.number
                      ? 'text-blue-600 dark:text-blue-400'
                      : 'text-gray-500'
                  }`}
                >
                  {step.title}
                </span>
                {index < steps.length - 1 && (
                  <div
                    className={`w-16 h-0.5 mx-4 ${
                      currentStep > step.number
                        ? 'bg-blue-600'
                        : 'bg-gray-300'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[70vh] overflow-y-auto">
          {/* Step 1: Connect Sheet */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Connect Google Sheet
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Connect a Google Sheet that contains your content data. The sheet should have columns for video scripts, assets, and metadata.
                </p>
              </div>

              <div className="grid grid-cols-1 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Sheet ID *
                  </label>
                  <input
                    type="text"
                    value={formData.sheet_id}
                    onChange={(e) => handleInputChange('sheet_id', e.target.value)}
                    placeholder="1A2B3C4D5E6F7G8H9I0J..."
                    className={`w-full px-4 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      errors.sheet_id ? 'border-red-500' : 'border-gray-300 dark:border-gray-700'
                    }`}
                  />
                  {errors.sheet_id && (
                    <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                      <AlertCircle className="w-4 h-4" />
                      {errors.sheet_id}
                    </p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Data Range *
                  </label>
                  <input
                    type="text"
                    value={formData.range}
                    onChange={(e) => handleInputChange('range', e.target.value)}
                    placeholder="A1:Z1000"
                    className={`w-full px-4 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      errors.range ? 'border-red-500' : 'border-gray-300 dark:border-gray-700'
                    }`}
                  />
                  {errors.range && (
                    <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                      <AlertCircle className="w-4 h-4" />
                      {errors.range}
                    </p>
                  )}
                  <p className="mt-1 text-sm text-gray-500">
                    Example: A1:Z1000 (first 1000 rows, columns A through Z)
                  </p>
                </div>
              </div>

              {errors.sheet_connection && (
                <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <p className="text-red-800 dark:text-red-400 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5" />
                    {errors.sheet_connection}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Output Configuration */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Output Configuration
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Configure the output format and storage settings for your generated videos.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Video Format
                  </label>
                  <select
                    value={formData.format}
                    onChange={(e) => handleInputChange('format', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="mp4">MP4</option>
                    <option value="mov">MOV</option>
                    <option value="webm">WebM</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Video Codec
                  </label>
                  <select
                    value={formData.video_codec}
                    onChange={(e) => handleInputChange('video_codec', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="h264">H.264</option>
                    <option value="h265">H.265</option>
                    <option value="vp9">VP9</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Audio Codec
                  </label>
                  <select
                    value={formData.audio_codec}
                    onChange={(e) => handleInputChange('audio_codec', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="aac">AAC</option>
                    <option value="opus">Opus</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Resolution
                  </label>
                  <select
                    value={formData.resolution}
                    onChange={(e) => handleInputChange('resolution', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="720p">720p (HD)</option>
                    <option value="1080p">1080p (Full HD)</option>
                    <option value="4k">4K (Ultra HD)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Output Bucket *
                </label>
                <input
                  type="text"
                  value={formData.output_bucket}
                  onChange={(e) => handleInputChange('output_bucket', e.target.value)}
                  placeholder="my-videos-bucket"
                  className={`w-full px-4 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.output_bucket ? 'border-red-500' : 'border-gray-300 dark:border-gray-700'
                  }`}
                />
                {errors.output_bucket && (
                  <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    {errors.output_bucket}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Template ID *
                </label>
                <input
                  type="text"
                  value={formData.template_id}
                  onChange={(e) => handleInputChange('template_id', e.target.value)}
                  placeholder="tpl_abc123"
                  className={`w-full px-4 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.template_id ? 'border-red-500' : 'border-gray-300 dark:border-gray-700'
                  }`}
                />
                {errors.template_id && (
                  <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    {errors.template_id}
                  </p>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Style
                  </label>
                  <select
                    value={formData.overrides.style}
                    onChange={(e) => handleNestedInputChange('overrides', 'style', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="modern">Modern</option>
                    <option value="classic">Classic</option>
                    <option value="minimal">Minimal</option>
                    <option value="corporate">Corporate</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Voice
                  </label>
                  <select
                    value={formData.overrides.voice}
                    onChange={(e) => handleNestedInputChange('overrides', 'voice', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="female">Female</option>
                    <option value="male">Male</option>
                    <option value="neutral">Neutral</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Job Details */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Job Details
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Configure the job settings and processing options.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Job Title *
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  placeholder="Campaign Spring Launch"
                  className={`w-full px-4 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.title ? 'border-red-500' : 'border-gray-300 dark:border-gray-700'
                  }`}
                />
                {errors.title && (
                  <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    {errors.title}
                  </p>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Priority
                  </label>
                  <select
                    value={formData.priority}
                    onChange={(e) => handleInputChange('priority', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="low">Low</option>
                    <option value="normal">Normal</option>
                    <option value="high">High</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Processing Deadline (minutes)
                  </label>
                  <input
                    type="number"
                    value={Math.floor(formData.processing_deadline_ms / 60000)}
                    onChange={(e) => handleInputChange('processing_deadline_ms', parseInt(e.target.value) * 60000)}
                    min="1"
                    max="1440"
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Callback URL (optional)
                </label>
                <input
                  type="url"
                  value={formData.callback_url}
                  onChange={(e) => handleInputChange('callback_url', e.target.value)}
                  placeholder="https://client.example.com/webhooks/job"
                  className={`w-full px-4 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.callback_url ? 'border-red-500' : 'border-gray-300 dark:border-gray-700'
                  }`}
                />
                {errors.callback_url && (
                  <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    {errors.callback_url}
                  </p>
                )}
                <p className="mt-1 text-sm text-gray-500">
                  URL to receive job status updates via webhook
                </p>
              </div>
            </div>
          )}

          {/* Step 4: Scheduling Configuration */}
          {currentStep === 4 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Smart Scheduling Configuration
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Configure intelligent scheduling and optimization settings for your batch jobs.
                </p>
              </div>

              <Tabs value={formData.scheduling_mode} onValueChange={(value) => handleInputChange('scheduling_mode', value)} className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="smart" className="flex items-center gap-2">
                    <Zap className="w-4 h-4" />
                    Smart
                  </TabsTrigger>
                  <TabsTrigger value="time_based" className="flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    Time-based
                  </TabsTrigger>
                  <TabsTrigger value="content_based" className="flex items-center gap-2">
                    <Filter className="w-4 h-4" />
                    Content-based
                  </TabsTrigger>
                  <TabsTrigger value="manual" className="flex items-center gap-2">
                    <Settings className="w-4 h-4" />
                    Manual
                  </TabsTrigger>
                </TabsList>

                <div className="mt-6">
                  <TabsContent value="smart" className="space-y-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Target className="w-5 h-5 text-blue-600" />
                          AI-Powered Smart Scheduling
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-gray-600 dark:text-gray-400 mb-4">
                          Automatically optimizes scheduling based on system load, content complexity, and resource availability.
                        </p>
                        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                          <h4 className="font-medium text-blue-900 dark:text-blue-300 mb-2">Smart Features:</h4>
                          <ul className="text-sm text-blue-800 dark:text-blue-400 space-y-1">
                            <li>• Dynamic load balancing across available resources</li>
                            <li>• Content complexity analysis for optimal processing order</li>
                            <li>• Automatic retry logic for failed items</li>
                            <li>• Real-time performance monitoring and adjustment</li>
                          </ul>
                        </div>
                      </CardContent>
                    </Card>
                  </TabsContent>

                  <TabsContent value="time_based" className="space-y-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Calendar className="w-5 h-5 text-green-600" />
                          Time-Based Scheduling
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="flex items-center gap-2">
                              <input
                                type="radio"
                                name="timing"
                                checked={formData.start_immediately}
                                onChange={() => handleInputChange('start_immediately', true)}
                                className="text-blue-600"
                              />
                              <span className="text-sm font-medium">Start Immediately</span>
                            </label>
                          </div>
                          <div>
                            <label className="flex items-center gap-2">
                              <input
                                type="radio"
                                name="timing"
                                checked={!formData.start_immediately}
                                onChange={() => handleInputChange('start_immediately', false)}
                                className="text-blue-600"
                              />
                              <span className="text-sm font-medium">Schedule for Later</span>
                            </label>
                          </div>
                        </div>

                        {!formData.start_immediately && (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Start Time
                              </label>
                              <input
                                type="datetime-local"
                                value={formData.schedule_start_time}
                                onChange={(e) => handleInputChange('schedule_start_time', e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              />
                              {errors.schedule_start_time && (
                                <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                                  <AlertCircle className="w-4 h-4" />
                                  {errors.schedule_start_time}
                                </p>
                              )}
                            </div>
                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                End Time (optional)
                              </label>
                              <input
                                type="datetime-local"
                                value={formData.schedule_end_time}
                                onChange={(e) => handleInputChange('schedule_end_time', e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              />
                              {errors.schedule_end_time && (
                                <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                                  <AlertCircle className="w-4 h-4" />
                                  {errors.schedule_end_time}
                                </p>
                              )}
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </TabsContent>

                  <TabsContent value="content_based" className="space-y-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Filter className="w-5 h-5 text-purple-600" />
                          Content-Based Scheduling
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <p className="text-gray-600 dark:text-gray-400">
                          Schedule jobs based on content tags, complexity, and metadata.
                        </p>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Priority Threshold
                          </label>
                          <select
                            value={formData.priority_queue ? 'high' : 'normal'}
                            onChange={(e) => handleInputChange('priority_queue', e.target.value === 'high')}
                            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          >
                            <option value="low">Process Low Priority Content First</option>
                            <option value="normal">Process Normal Priority Content</option>
                            <option value="high">Process High Priority Content First</option>
                          </select>
                        </div>
                      </CardContent>
                    </Card>
                  </TabsContent>

                  <TabsContent value="manual" className="space-y-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Settings className="w-5 h-5 text-orange-600" />
                          Manual Scheduling
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                              Max Concurrent Jobs
                            </label>
                            <input
                              type="number"
                              value={formData.max_concurrent_jobs}
                              onChange={(e) => handleInputChange('max_concurrent_jobs', parseInt(e.target.value))}
                              min="1"
                              max="10"
                              className={`w-full px-4 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                                errors.max_concurrent_jobs ? 'border-red-500' : 'border-gray-300 dark:border-gray-700'
                              }`}
                            />
                            {errors.max_concurrent_jobs && (
                              <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                                <AlertCircle className="w-4 h-4" />
                                {errors.max_concurrent_jobs}
                              </p>
                            )}
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                              Optimization Level
                            </label>
                            <select
                              value={formData.optimization_level}
                              onChange={(e) => handleInputChange('optimization_level', e.target.value)}
                              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            >
                              <option value="speed">Speed Optimization</option>
                              <option value="balanced">Balanced (Recommended)</option>
                              <option value="quality">Quality Optimization</option>
                            </select>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </TabsContent>
                </div>
              </Tabs>
            </div>
          )}

          {/* Step 5: Review & Schedule */}
          {currentStep === 5 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Review & Schedule
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Review your batch scheduling configuration before creating it.
                </p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Configuration Summary */}
                <Card>
                  <CardHeader>
                    <CardTitle>Configuration Summary</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">Sheet Source</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        ID: {formData.sheet_id}<br />
                        Range: {formData.range}
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">Output Format</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {formData.format.toUpperCase()} • {formData.resolution} • {formData.video_codec}
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">Template</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {formData.template_id} • {formData.overrides.style} • {formData.overrides.voice}
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">Settings</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Priority: {formData.priority}<br />
                        Deadline: {Math.floor(formData.processing_deadline_ms / 60000)} minutes
                      </p>
                    </div>
                  </CardContent>
                </Card>

                {/* Scheduling Summary */}
                <Card>
                  <CardHeader>
                    <CardTitle>Scheduling Summary</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">Scheduling Mode</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                        {formData.scheduling_mode.replace('_', '-')}
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">Timing</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {formData.start_immediately ? 'Start Immediately' : `Start: ${formData.schedule_start_time}`}
                        {formData.schedule_end_time && ` • End: ${formData.schedule_end_time}`}
                      </p>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">Optimization</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {formData.optimization_level} • Max {formData.max_concurrent_jobs} concurrent jobs
                        {formData.priority_queue && ' • Priority queue enabled'}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Scheduling Tips */}
              {optimizationLoading ? (
                <Card>
                  <CardContent className="flex items-center justify-center py-8">
                    <div className="flex items-center gap-2">
                      <RefreshCw className="w-5 h-5 animate-spin text-blue-600" />
                      <span className="text-gray-600 dark:text-gray-400">Generating optimization tips...</span>
                    </div>
                  </CardContent>
                </Card>
              ) : schedulingTips.length > 0 ? (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="w-5 h-5 text-green-600" />
                      Optimization Tips
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {schedulingTips.map((tip, index) => (
                        <p key={index} className="text-sm text-gray-600 dark:text-gray-400">
                          {tip}
                        </p>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ) : null}

              {errors.creation && (
                <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <p className="text-red-800 dark:text-red-400 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5" />
                    {errors.creation}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center p-6 border-t border-gray-200 dark:border-gray-800">
          <div>
            {currentStep > 1 && (
              <button
                onClick={handlePrevious}
                className="px-6 py-2 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                Previous
              </button>
            )}
          </div>

          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              Cancel
            </button>

            {currentStep < 5 ? (
              <button
                onClick={currentStep === 1 ? handleConnectSheet : handleNext}
                disabled={connectLoading || optimizationLoading}
                className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50"
              >
                {(connectLoading || optimizationLoading) ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    {currentStep === 1 ? 'Connecting...' : 'Loading...'}
                  </div>
                ) : (
                  'Next'
                )}
              </button>
            ) : (
              <button
                onClick={handleScheduleJob}
                disabled={loading}
                className="px-6 py-2 bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-lg hover:from-green-700 hover:to-blue-700 transition-all disabled:opacity-50"
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Scheduling...
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <CalendarDays className="w-4 h-4" />
                    Schedule Job
                  </div>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
