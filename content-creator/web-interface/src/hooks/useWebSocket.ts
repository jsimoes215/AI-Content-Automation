import { useState, useEffect, useRef, useCallback } from 'react';

export interface WebSocketMessage {
  type: string;
  ts: string;
  correlation_id: string;
  data: any;
}

export interface JobProgress {
  percent_complete: number;
  items_total: number;
  items_completed: number;
  items_failed: number;
  items_skipped: number;
  items_canceled: number;
  items_pending: number;
  time_to_start_ms: number | null;
  time_processing_ms: number;
  average_duration_ms_per_item: number | null;
  eta_ms: number | null;
  rate_limited: boolean;
}

export interface VideoProgress {
  id: string;
  job_id: string;
  state: string;
  percent_complete: number;
  row_index: number;
  title: string;
  created_at: string;
  updated_at: string;
  artifacts?: Array<{
    type: string;
    content_type: string;
    size: number;
    url: string;
  }>;
  errors?: Array<{
    error_code: string;
    error_message: string;
    error_class: string;
    occurred_at: string;
  }>;
}

export interface JobState {
  prior_state: string;
  new_state: string;
  reason: string;
}

export interface ConnectionState {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  lastMessage: WebSocketMessage | null;
  connectionId: string | null;
}

interface UseWebSocketOptions {
  jobId?: string;
  token?: string;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onProgress?: (progress: JobProgress) => void;
  onStateChange?: (state: JobState) => void;
  onVideoUpdate?: (video: VideoProgress) => void;
  onVideoCompleted?: (video: VideoProgress) => void;
  onVideoFailed?: (video: VideoProgress) => void;
  onJobCompleted?: (data: any) => void;
  onJobFailed?: (data: any) => void;
  onJobCanceled?: (data: any) => void;
}

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8765';

export function useWebSocket(options: UseWebSocketOptions) {
  const {
    jobId,
    token,
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onProgress,
    onStateChange,
    onVideoUpdate,
    onVideoCompleted,
    onVideoFailed,
    onJobCompleted,
    onJobFailed,
    onJobCanceled,
  } = options;

  const [connectionState, setConnectionState] = useState<ConnectionState>({
    connected: false,
    connecting: false,
    error: null,
    lastMessage: null,
    connectionId: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const messageHistoryRef = useRef<WebSocketMessage[]>([]);
  const connectionIdRef = useRef<string>(generateConnectionId());

  const generateConnectionId = () => {
    return `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

  const processMessage = useCallback((message: WebSocketMessage) => {
    // Store message history
    messageHistoryRef.current.push(message);
    if (messageHistoryRef.current.length > 100) {
      messageHistoryRef.current.shift();
    }

    setConnectionState(prev => ({ ...prev, lastMessage: message }));

    // Process different event types
    switch (message.type) {
      case 'job.progress':
        if (onProgress && message.data) {
          onProgress(message.data as JobProgress);
        }
        break;
      case 'job.state_changed':
        if (onStateChange && message.data) {
          onStateChange(message.data as JobState);
        }
        break;
      case 'video.created':
        if (onVideoUpdate && message.data) {
          onVideoUpdate(message.data as VideoProgress);
        }
        break;
      case 'video.updated':
        if (onVideoUpdate && message.data) {
          onVideoUpdate(message.data as VideoProgress);
        }
        break;
      case 'video.completed':
        if (onVideoCompleted && message.data) {
          onVideoCompleted(message.data as VideoProgress);
        }
        break;
      case 'video.failed':
        if (onVideoFailed && message.data) {
          onVideoFailed(message.data as VideoProgress);
        }
        break;
      case 'job.completed':
        if (onJobCompleted && message.data) {
          onJobCompleted(message.data);
        }
        break;
      case 'job.failed':
        if (onJobFailed && message.data) {
          onJobFailed(message.data);
        }
        break;
      case 'job.canceled':
        if (onJobCanceled && message.data) {
          onJobCanceled(message.data);
        }
        break;
      case 'pong':
        // Handle ping/pong for connection health
        break;
      default:
        console.debug('Unhandled WebSocket message type:', message.type, message.data);
    }
  }, [
    onProgress,
    onStateChange,
    onVideoUpdate,
    onVideoCompleted,
    onVideoFailed,
    onJobCompleted,
    onJobFailed,
    onJobCanceled,
  ]);

  const connect = useCallback(() => {
    if (!jobId || !token) {
      setConnectionState(prev => ({
        ...prev,
        error: 'Job ID and token are required for WebSocket connection',
      }));
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    setConnectionState(prev => ({
      ...prev,
      connecting: true,
      error: null,
    }));

    try {
      // Build WebSocket URL with query parameters
      const wsUrl = new URL(WS_BASE_URL);
      wsUrl.searchParams.set('job_id', jobId);
      wsUrl.searchParams.set('token', token);
      wsUrl.searchParams.set('connection_id', connectionIdRef.current);

      const ws = new WebSocket(wsUrl.toString());
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected for job:', jobId);
        setConnectionState(prev => ({
          ...prev,
          connected: true,
          connecting: false,
          error: null,
          connectionId: connectionIdRef.current,
        }));
        reconnectAttemptsRef.current = 0;

        // Send initial ping
        ws.send(JSON.stringify({ type: 'ping', ts: new Date().toISOString() }));
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          processMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
          setConnectionState(prev => ({
            ...prev,
            error: 'Invalid message format received',
          }));
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionState(prev => ({
          ...prev,
          connecting: false,
          error: 'WebSocket connection error',
        }));
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setConnectionState(prev => ({
          ...prev,
          connected: false,
          connecting: false,
        }));

        // Auto-reconnect if enabled and not a manual close
        if (autoReconnect && event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(`Attempting to reconnect... (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setConnectionState(prev => ({
            ...prev,
            error: 'Maximum reconnection attempts reached',
          }));
        }
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionState(prev => ({
        ...prev,
        connecting: false,
        error: 'Failed to establish WebSocket connection',
      }));
    }
  }, [
    jobId,
    token,
    autoReconnect,
    reconnectInterval,
    maxReconnectAttempts,
    processMessage,
  ]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }
    
    setConnectionState(prev => ({
      ...prev,
      connected: false,
      connecting: false,
    }));
    
    reconnectAttemptsRef.current = 0;
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(message));
        return true;
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
        return false;
      }
    } else {
      console.warn('WebSocket is not connected');
      return false;
    }
  }, []);

  const ping = useCallback(() => {
    return sendMessage({ type: 'ping', ts: new Date().toISOString() });
  }, [sendMessage]);

  const getMessageHistory = useCallback(() => {
    return messageHistoryRef.current.slice();
  }, []);

  const clearMessageHistory = useCallback(() => {
    messageHistoryRef.current = [];
  }, []);

  // Auto-connect when jobId and token are available
  useEffect(() => {
    if (jobId && token) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [jobId, token, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // Connection health check
  useEffect(() => {
    if (connectionState.connected) {
      const pingInterval = setInterval(() => {
        ping();
      }, 30000); // Ping every 30 seconds

      return () => clearInterval(pingInterval);
    }
  }, [connectionState.connected, ping]);

  return {
    // Connection state
    connected: connectionState.connected,
    connecting: connectionState.connecting,
    error: connectionState.error,
    lastMessage: connectionState.lastMessage,
    connectionId: connectionState.connectionId,
    
    // Actions
    connect,
    disconnect,
    sendMessage,
    ping,
    
    // Message history
    getMessageHistory,
    clearMessageHistory,
    
    // Utility
    getConnectionHealth: () => ({
      connected: connectionState.connected,
      lastMessageTime: connectionState.lastMessage?.ts,
      reconnectAttempts: reconnectAttemptsRef.current,
      messageCount: messageHistoryRef.current.length,
    }),
  };
}

export default useWebSocket;