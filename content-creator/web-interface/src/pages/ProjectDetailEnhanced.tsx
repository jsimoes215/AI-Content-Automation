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
  Eye,
  Video,
  Music,
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
  result_data: any;
}

interface Scene {
  id: string;
  scene_number: number;
  duration: number;
  voiceover_text: string;
  visual_description: string;
  scene_type: string;
  generated_content: Array<{
    id: string;
    content_type: string;
    file_path: string;
    platform: string;
    media_url?: string;
  }>;
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
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [scriptData, setScriptData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [previewContent, setPreviewContent] = useState<any>(null);
  const [showPreviewModal, setShowPreviewModal] = useState(false);

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

      // If project is completed, load scenes
      const completedJob = response.data.jobs.find(
        (j: Job) => j.status === 'completed' && j.result_data?.script_id
      );

      if (completedJob && completedJob.result_data?.script_id) {
        await loadScenes(completedJob.result_data.script_id);
        await loadScript(completedJob.result_data.script_id);
      }
    } catch (error) {
      console.error('Failed to load project:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadScenes = async (scriptId: string) => {
    try {
      const response = await apiClient.request(`/api/scripts/${scriptId}/scenes`);
      setScenes(response.data);
    } catch (error) {
      console.error('Failed to load scenes:', error);
    }
  };

  const loadScript = async (scriptId: string) => {
    try {
      const response = await apiClient.getScript(scriptId);
      setScriptData(response.data);
    } catch (error) {
      console.error('Failed to load script:', error);
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

  const handlePreviewContent = async (contentId: string) => {
    try {
      const response = await apiClient.request(`/api/preview/content/${contentId}`);
      setPreviewContent(response.data);
      setShowPreviewModal(true);
    } catch (error) {
      console.error('Failed to load content preview:', error);
      alert('Failed to load content preview');
    }
  };

  const handleDownloadContent = (contentId: string) => {
    const downloadUrl = `${apiClient.request.bind(apiClient, '')}/api/download/content/${contentId}`;
    window.open(downloadUrl, '_blank');
  };

  const handleExportProject = async () => {
    if (!project) return;

    try {
      const response = await apiClient.request('/api/export/project', {
        method: 'POST',
        body: JSON.stringify({
          project_id: project.id,
          content_types: ['video', 'audio', 'script'],
          format: 'zip',
        }),
      });

      // Trigger download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `project_${project.id}_export.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Failed to export project:', error);
      alert('Failed to export project');
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
      script_generation: 'Content Generation',
      video_generation: 'Video Generation',
      audio_generation: 'Audio Generation',
      platform_adaptation: 'Platform Adaptation',
    };
    return labels[type] || type;
  };

  const getContentTypeIcon = (type: string) => {
    switch (type) {
      case 'video':
        return <Video className="w-5 h-5" />;
      case 'audio':
        return <Music className="w-5 h-5" />;
      case 'script':
        return <FileText className="w-5 h-5" />;
      default:
        return <FileText className="w-5 h-5" />;
    }
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
          <div className="flex items-center gap-4">
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
            {project.status === 'completed' && (
              <button
                onClick={handleExportProject}
                className="flex items-center px-4 py-2 bg-gradient-to-r from-green-600 to-teal-600 text-white font-medium rounded-lg hover:from-green-700 hover:to-teal-700 transition-all"
              >
                <Download className="w-5 h-5 mr-2" />
                Export All
              </button>
            )}
          </div>
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
            {generating ? 'Starting...' : 'Generate Content'}
          </button>
        </div>
      </div>

      {/* Script Preview */}
      {scriptData && (
        <div className="bg-white dark:bg-gray-900 rounded-xl p-8 shadow-sm border border-gray-200 dark:border-gray-800">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            Generated Script
          </h2>
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {scriptData.content.title}
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mt-2">
                {scriptData.content.description}
              </p>
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
              <span>Duration: {scriptData.total_duration}s</span>
              <span>Words: {scriptData.word_count}</span>
              <span>Scenes: {scriptData.content.scenes?.length || 0}</span>
            </div>
          </div>
        </div>
      )}

      {/* Generated Scenes */}
      {scenes.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-xl p-8 shadow-sm border border-gray-200 dark:border-gray-800">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
            Generated Content
          </h2>
          <div className="space-y-6">
            {scenes.map((scene) => (
              <div
                key={scene.id}
                className="p-4 border border-gray-200 dark:border-gray-800 rounded-lg"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      Scene {scene.scene_number}: {scene.scene_type}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      Duration: {scene.duration}s
                    </p>
                  </div>
                </div>

                <p className="text-gray-700 dark:text-gray-300 mb-2 text-sm">
                  {scene.voiceover_text}
                </p>
                <p className="text-gray-600 dark:text-gray-400 mb-4 text-sm italic">
                  Visual: {scene.visual_description}
                </p>

                {scene.generated_content.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {scene.generated_content.map((content) => (
                      <div
                        key={content.id}
                        className="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-800 rounded-lg"
                      >
                        {getContentTypeIcon(content.content_type)}
                        <span className="text-sm text-gray-700 dark:text-gray-300">
                          {content.content_type} - {content.platform}
                        </span>
                        <button
                          onClick={() => handlePreviewContent(content.id)}
                          className="ml-2 p-1 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDownloadContent(content.id)}
                          className="p-1 text-green-600 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/30 rounded"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Generation Jobs */}
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
              Click "Generate Content" to start processing
            </p>
          </div>
        )}
      </div>

      {/* Preview Modal */}
      {showPreviewModal && previewContent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 rounded-xl p-8 max-w-4xl w-full mx-4 shadow-2xl">
            <div className="flex justify-between items-start mb-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Content Preview
              </h2>
              <button
                onClick={() => setShowPreviewModal(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                Close
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Type: {previewContent.content_type}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Platform: {previewContent.platform}</p>
                {previewContent.duration && (
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Duration: {previewContent.duration}s
                  </p>
                )}
              </div>

              {previewContent.media_url && previewContent.content_type === 'video' && (
                <video
                  controls
                  className="w-full max-h-96 bg-black rounded-lg"
                  src={previewContent.media_url}
                >
                  Your browser does not support video playback.
                </video>
              )}

              {previewContent.media_url && previewContent.content_type === 'audio' && (
                <audio controls className="w-full" src={previewContent.media_url}>
                  Your browser does not support audio playback.
                </audio>
              )}

              <div className="flex justify-end gap-4">
                <button
                  onClick={() => setShowPreviewModal(false)}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  Close
                </button>
                <button
                  onClick={() => handleDownloadContent(previewContent.id)}
                  className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700"
                >
                  <Download className="w-5 h-5 inline mr-2" />
                  Download
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
