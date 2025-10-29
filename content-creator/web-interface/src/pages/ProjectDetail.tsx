import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Play,
  Clock,
  CheckCircle,
  AlertCircle,
  FileText,
  Download,
} from 'lucide-react';
import apiClient from '../lib/api';

interface Job {
  id: string;
  job_type: string;
  status: string;
  progress: number;
  current_step: number;
  total_steps: number;
  error_message: string | null;
  created_at: string;
}

interface Project {
  id: string;
  original_idea: string;
  target_audience: string | null;
  tone: string | null;
  status: string;
  created_at: string;
  jobs: Job[];
  analytics: {
    total_views: number;
    total_likes: number;
    total_comments: number;
    avg_engagement: number;
  };
}

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (id) {
      loadProject();

      // Connect to WebSocket for real-time updates
      apiClient.connectWebSocket((data) => {
        if (data.type === 'job_progress' || data.type === 'job_completed') {
          loadProject();
        }
      });

      return () => {
        apiClient.disconnectWebSocket();
      };
    }
  }, [id]);

  const loadProject = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getProject(id!);
      setProject(response.data);
    } catch (error) {
      console.error('Failed to load project:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateScript = async () => {
    if (!project) return;

    try {
      setGenerating(true);
      await apiClient.generateScript({
        project_id: project.id,
        target_duration: 300,
        scene_count: 5,
      });
      // Job will be updated via WebSocket
    } catch (error) {
      console.error('Failed to generate script:', error);
      alert('Failed to generate script');
    } finally {
      setGenerating(false);
    }
  };

  const getJobStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />;
      case 'processing':
        return <Clock className="w-5 h-5 text-blue-600 dark:text-blue-400 animate-pulse" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getJobTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      script_generation: 'Script Generation',
      video_generation: 'Video Generation',
      audio_generation: 'Audio Generation',
      platform_adaptation: 'Platform Adaptation',
    };
    return labels[type] || type;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600 dark:text-gray-400">Project not found</p>
        <button
          onClick={() => navigate('/projects')}
          className="mt-4 text-blue-600 dark:text-blue-400 hover:underline"
        >
          Back to Projects
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <button
        onClick={() => navigate('/projects')}
        className="flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
      >
        <ArrowLeft className="w-5 h-5 mr-2" />
        Back to Projects
      </button>

      <div className="bg-white dark:bg-gray-900 rounded-xl p-8 shadow-sm border border-gray-200 dark:border-gray-800">
        <div className="flex justify-between items-start mb-6">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              {project.original_idea}
            </h1>
            <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
              {project.target_audience && (
                <span>Audience: {project.target_audience}</span>
              )}
              {project.tone && <span>Tone: {project.tone}</span>}
              <span>Created {new Date(project.created_at).toLocaleDateString()}</span>
            </div>
          </div>
          <span
            className={`px-4 py-2 rounded-full text-sm font-medium ${
              project.status === 'completed'
                ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                : project.status === 'processing'
                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
                : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
            }`}
          >
            {project.status}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p className="text-sm text-blue-800 dark:text-blue-400 font-medium">Total Views</p>
            <p className="text-2xl font-bold text-blue-900 dark:text-blue-300 mt-1">
              {project.analytics.total_views || 0}
            </p>
          </div>
          <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <p className="text-sm text-green-800 dark:text-green-400 font-medium">Total Likes</p>
            <p className="text-2xl font-bold text-green-900 dark:text-green-300 mt-1">
              {project.analytics.total_likes || 0}
            </p>
          </div>
          <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
            <p className="text-sm text-purple-800 dark:text-purple-400 font-medium">
              Total Comments
            </p>
            <p className="text-2xl font-bold text-purple-900 dark:text-purple-300 mt-1">
              {project.analytics.total_comments || 0}
            </p>
          </div>
          <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
            <p className="text-sm text-orange-800 dark:text-orange-400 font-medium">
              Avg Engagement
            </p>
            <p className="text-2xl font-bold text-orange-900 dark:text-orange-300 mt-1">
              {project.analytics.avg_engagement
                ? (project.analytics.avg_engagement * 100).toFixed(1) + '%'
                : '0%'}
            </p>
          </div>
        </div>

        <div className="mt-8">
          <button
            onClick={handleGenerateScript}
            disabled={generating || project.status === 'processing'}
            className="flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play className="w-5 h-5 mr-2" />
            {generating ? 'Starting...' : 'Generate Script'}
          </button>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-900 rounded-xl p-8 shadow-sm border border-gray-200 dark:border-gray-800">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
          Generation Jobs
        </h2>

        {project.jobs && project.jobs.length > 0 ? (
          <div className="space-y-4">
            {project.jobs.map((job) => (
              <div
                key={job.id}
                className="p-4 border border-gray-200 dark:border-gray-800 rounded-lg"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    {getJobStatusIcon(job.status)}
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {getJobTypeLabel(job.job_type)}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Created {new Date(job.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {job.progress}%
                  </span>
                </div>

                {job.status === 'processing' && (
                  <div className="mt-3">
                    <div className="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${job.progress}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                      Step {job.current_step} of {job.total_steps}
                    </p>
                  </div>
                )}

                {job.status === 'failed' && job.error_message && (
                  <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                    <p className="text-sm text-red-800 dark:text-red-400">
                      {job.error_message}
                    </p>
                  </div>
                )}

                {job.status === 'completed' && (
                  <div className="mt-3 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-green-600 dark:text-green-400" />
                    <span className="text-sm text-green-800 dark:text-green-400">
                      Completed successfully
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-600 dark:text-gray-400">No generation jobs yet</p>
            <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
              Click "Generate Script" to start processing
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// Add these imports at the top
import { Download, Eye, FileText, Music, Video } from 'lucide-react';
