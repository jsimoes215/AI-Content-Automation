# Scheduling API Integration Guide

This comprehensive guide provides developers with detailed information on integrating the Scheduling Optimization API into various types of applications and systems. Whether you're building a web application, mobile app, or backend service, this guide covers architecture patterns, best practices, security considerations, and real-world implementation examples.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Integration Patterns](#integration-patterns)
- [Security Implementation](#security-implementation)
- [Error Handling Strategies](#error-handling-strategies)
- [Performance Optimization](#performance-optimization)
- [Web Application Integration](#web-application-integration)
- [Mobile App Integration](#mobile-app-integration)
- [Backend Service Integration](#backend-service-integration)
- [Third-Party Platform Integration](#third-party-platform-integration)
- [Real-Time Updates Implementation](#real-time-updates-implementation)
- [Monitoring and Observability](#monitoring-and-observability)
- [Testing Strategies](#testing-strategies)
- [Production Deployment](#production-deployment)
- [Common Use Cases](#common-use-cases)
- [Troubleshooting Guide](#troubleshooting-guide)

## Architecture Overview

### System Architecture

The Scheduling API is designed to integrate seamlessly into various application architectures:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Client    │    │   Mobile App     │    │  Desktop Client │
│  (React/Vue)    │    │ (React Native)   │    │   (Electron)    │
└─────────┬───────┘    └──────────┬───────┘    └─────────┬───────┘
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │   API Gateway/Layer   │
                    │  (Rate Limiting, Auth)│
                    └───────────┬───────────┘
                                │
                    ┌───────────┴───────────┐
                    │  Scheduling API       │
                    │  - Recommendations    │
                    │  - Schedule Management│
                    │  - Optimization       │
                    └───────────┬───────────┘
                                │
                    ┌───────────┴───────────┐
                    │  Data Layer           │
                    │  - PostgreSQL         │
                    │  - Redis Cache        │
                    │  - Queue System       │
                    └────────────────────────┘
```

### Core Components

1. **API Layer**: FastAPI-based RESTful API with WebSocket support
2. **Business Logic**: Scheduling optimization algorithms and recommendation engine
3. **Data Layer**: PostgreSQL for persistent storage, Redis for caching
4. **Message Queue**: Background processing for long-running operations
5. **Real-time Updates**: WebSocket connections for live status updates

## Integration Patterns

### 1. Direct API Integration

**Best for**: Simple applications with direct API access

```javascript
// Simple client integration
class ContentScheduler {
  constructor(apiKey, baseUrl = 'https://api.content-automation.com/api/v1') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
  }

  async createSchedule(scheduleData) {
    const response = await fetch(`${this.baseUrl}/scheduling/calendar`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        'Idempotency-Key': this.generateIdempotencyKey()
      },
      body: JSON.stringify(scheduleData)
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  }

  generateIdempotencyKey() {
    return 'key_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }
}
```

### 2. Proxy Pattern (Recommended)

**Best for**: Applications needing additional business logic or caching

```javascript
// Proxy with caching and validation
class SchedulingProxy {
  constructor(apiClient, cache, validator) {
    this.apiClient = apiClient;
    this.cache = cache;
    this.validator = validator;
  }

  async createSchedule(scheduleData) {
    // Validate input
    this.validator.validateSchedule(scheduleData);
    
    // Check cache for idempotency
    const idempotencyKey = this.generateIdempotencyKey(scheduleData);
    const cached = await this.cache.get(`schedule:${idempotencyKey}`);
    
    if (cached) {
      return cached;
    }

    // Create schedule via API
    const schedule = await this.apiClient.createSchedule(scheduleData, idempotencyKey);
    
    // Cache result
    await this.cache.set(`schedule:${idempotencyKey}`, schedule, 3600);
    
    return schedule;
  }
}
```

### 3. Message Queue Pattern

**Best for**: High-volume applications requiring async processing

```javascript
// Async processing with message queue
class AsyncSchedulingService {
  constructor(apiClient, messageQueue, webhookHandler) {
    this.apiClient = apiClient;
    this.messageQueue = messageQueue;
    this.webhookHandler = webhookHandler;
  }

  async submitSchedule(scheduleData) {
    // Validate and queue for processing
    const jobId = await this.messageQueue.enqueue('create-schedule', {
      scheduleData,
      timestamp: Date.now()
    });

    // Return immediate response with job ID
    return { jobId, status: 'queued' };

    // Processing happens asynchronously
    this.processScheduleJob(jobId);
  }

  async processScheduleJob(jobId) {
    try {
      const job = await this.messageQueue.getJob(jobId);
      const { scheduleData } = job.data;

      const schedule = await this.apiClient.createSchedule(scheduleData);
      
      // Update job status
      await this.messageQueue.updateJob(jobId, { status: 'completed', result: schedule });
      
      // Notify via webhook
      this.webhookHandler.notifyScheduleCreated(schedule);

    } catch (error) {
      await this.messageQueue.updateJob(jobId, { status: 'failed', error: error.message });
    }
  }
}
```

## Security Implementation

### Authentication Flow

#### JWT Token Management

```javascript
// JWT token management with refresh
class AuthManager {
  constructor(config) {
    this.config = config;
    this.token = null;
    this.refreshPromise = null;
  }

  async getToken() {
    if (!this.token || this.isTokenExpired()) {
      await this.refreshToken();
    }
    return this.token;
  }

  isTokenExpired() {
    if (!this.token || !this.token.expires_at) return true;
    return Date.now() >= this.token.expires_at;
  }

  async refreshToken() {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this.performTokenRefresh();
    const result = await this.refreshPromise;
    this.refreshPromise = null;
    return result;
  }

  async performTokenRefresh() {
    try {
      const response = await fetch(this.config.tokenUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grant_type: 'refresh_token',
          refresh_token: this.config.refreshToken
        })
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const tokenData = await response.json();
      this.token = {
        access_token: tokenData.access_token,
        expires_at: Date.now() + (tokenData.expires_in * 1000)
      };

      return this.token;
    } catch (error) {
      // Handle token refresh failure
      this.config.onTokenRefreshFailed?.(error);
      throw error;
    }
  }
}
```

#### API Key Security

```javascript
// Secure API key handling
class SecureAPIClient {
  constructor(apiKey, options = {}) {
    this.apiKey = this.maskApiKey(apiKey);
    this.secureStorage = options.secureStorage || this.getSecureStorage();
  }

  maskApiKey(apiKey) {
    if (apiKey.length <= 8) return '*'.repeat(apiKey.length);
    return apiKey.substring(0, 4) + '*'.repeat(apiKey.length - 8) + apiKey.substring(apiKey.length - 4);
  }

  async makeRequest(endpoint, options = {}) {
    const token = await this.secureStorage.getAccessToken();
    
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'User-Agent': `${options.appName}/${options.appVersion}`,
      ...options.headers
    };

    return fetch(endpoint, { ...options, headers });
  }

  // Implement secure storage based on platform
  getSecureStorage() {
    if (typeof window !== 'undefined') {
      // Web - use session storage
      return {
        async getAccessToken() {
          return sessionStorage.getItem('scheduling_api_token');
        }
      };
    } else if (typeof process !== 'undefined') {
      // Node.js - use environment variables
      return {
        async getAccessToken() {
          return process.env.SCHEDULING_API_TOKEN;
        }
      };
    }
    
    throw new Error('Unsupported environment');
  }
}
```

### Request Signing (Optional)

For enhanced security, implement request signing:

```javascript
import crypto from 'crypto';

class SignedAPIClient {
  constructor(apiKey, secretKey) {
    this.apiKey = apiKey;
    this.secretKey = secretKey;
  }

  createSignedRequest(url, method, body = null) {
    const timestamp = Date.now().toString();
    const bodyString = body ? JSON.stringify(body) : '';
    
    // Create signature
    const signature = this.createSignature(method, url, bodyString, timestamp);
    
    return {
      url,
      method,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'X-Signature': signature,
        'X-Timestamp': timestamp,
        'Content-Type': 'application/json'
      },
      body: bodyString
    };
  }

  createSignature(method, url, body, timestamp) {
    const stringToSign = `${method}\n${url}\n${body}\n${timestamp}`;
    return crypto
      .createHmac('sha256', this.secretKey)
      .update(stringToSign)
      .digest('hex');
  }
}
```

## Error Handling Strategies

### Comprehensive Error Handling

```javascript
// Centralized error handling
class APIErrorHandler {
  constructor(options = {}) {
    this.retryableCodes = options.retryableCodes || [408, 429, 500, 502, 503, 504];
    this.maxRetries = options.maxRetries || 3;
    this.backoffStrategy = options.backoffStrategy || this.exponentialBackoff;
  }

  async handleRequest(requestFn, context = {}) {
    let lastError;
    let attempt = 0;

    while (attempt <= this.maxRetries) {
      try {
        return await requestFn();
      } catch (error) {
        lastError = error;
        
        if (!this.shouldRetry(error, attempt)) {
          throw this.enhanceError(error, context);
        }

        const delay = this.backoffStrategy(attempt);
        await this.delay(delay);
        attempt++;
      }
    }

    throw this.enhanceError(lastError, context);
  }

  shouldRetry(error, attempt) {
    if (attempt >= this.maxRetries) return false;
    
    if (error.status === 401) {
      // Don't retry on auth errors
      return false;
    }

    return this.retryableCodes.includes(error.status);
  }

  exponentialBackoff(attempt) {
    return Math.min(1000 * Math.pow(2, attempt), 30000);
  }

  linearBackoff(attempt) {
    return Math.min(1000 * attempt, 30000);
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  enhanceError(error, context) {
    const enhanced = new Error(error.message);
    enhanced.originalError = error;
    enhanced.status = error.status;
    enhanced.context = context;
    enhanced.timestamp = new Date().toISOString();
    
    // Add context-specific information
    if (error.status === 429) {
      enhanced.retryAfter = error.headers?.get('Retry-After');
      enhanced.rateLimitInfo = this.parseRateLimitHeaders(error.headers);
    }
    
    return enhanced;
  }

  parseRateLimitHeaders(headers) {
    return {
      limit: headers.get('X-RateLimit-Limit'),
      remaining: headers.get('X-RateLimit-Remaining'),
      reset: headers.get('X-RateLimit-Reset')
    };
  }
}

// Usage
const errorHandler = new APIErrorHandler({
  maxRetries: 3,
  backoffStrategy: (attempt) => Math.min(1000 * Math.pow(1.5, attempt), 10000)
});

async function safeAPICall(apiCall, context) {
  return errorHandler.handleRequest(apiCall, context);
}
```

### Error Recovery Patterns

```javascript
// Circuit breaker pattern for error recovery
class CircuitBreaker {
  constructor(options = {}) {
    this.failureThreshold = options.failureThreshold || 5;
    this.recoveryTimeout = options.recoveryTimeout || 60000;
    this.monitor = options.monitor;
    
    this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
    this.failureCount = 0;
    this.nextAttempt = Date.now();
  }

  async execute(operation) {
    if (this.state === 'OPEN') {
      if (Date.now() < this.nextAttempt) {
        throw new Error('Circuit breaker is OPEN');
      }
      this.state = 'HALF_OPEN';
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  onSuccess() {
    this.failureCount = 0;
    this.state = 'CLOSED';
    this.monitor?.recordSuccess();
  }

  onFailure() {
    this.failureCount++;
    this.monitor?.recordFailure();
    
    if (this.failureCount >= this.failureThreshold) {
      this.state = 'OPEN';
      this.nextAttempt = Date.now() + this.recoveryTimeout;
    }
  }
}
```

## Performance Optimization

### Request Batching

```javascript
// Request batching for multiple operations
class BatchProcessor {
  constructor(options = {}) {
    this.batchSize = options.batchSize || 10;
    this.flushInterval = options.flushInterval || 1000;
    this.pendingRequests = [];
    this.flushTimer = null;
  }

  addRequest(request) {
    this.pendingRequests.push({
      ...request,
      id: this.generateRequestId(),
      timestamp: Date.now()
    });

    if (this.pendingRequests.length >= this.batchSize) {
      this.flush();
    } else if (!this.flushTimer) {
      this.flushTimer = setTimeout(() => this.flush(), this.flushInterval);
    }

    return new Promise((resolve, reject) => {
      const requestWithPromise = this.pendingRequests[this.pendingRequests.length - 1];
      requestWithPromise.resolve = resolve;
      requestWithPromise.reject = reject;
    });
  }

  async flush() {
    if (this.pendingRequests.length === 0) return;

    const batch = this.pendingRequests.splice(0);
    clearTimeout(this.flushTimer);
    this.flushTimer = null;

    try {
      // Group requests by endpoint
      const batches = this.groupByEndpoint(batch);
      
      // Execute batches in parallel
      const results = await Promise.allSettled(
        Object.values(batches).map(group => this.executeBatch(group))
      );

      // Resolve/reject individual promises
      results.forEach((result, index) => {
        const group = Object.values(batches)[index];
        group.forEach((request, reqIndex) => {
          if (result.status === 'fulfilled') {
            request.resolve(result.value[reqIndex]);
          } else {
            request.reject(result.reason);
          }
        });
      });
    } catch (error) {
      batch.forEach(request => request.reject(error));
    }
  }

  groupByEndpoint(requests) {
    return requests.reduce((groups, request) => {
      const endpoint = request.endpoint;
      if (!groups[endpoint]) {
        groups[endpoint] = [];
      }
      groups[endpoint].push(request);
      return groups;
    }, {});
  }

  async executeBatch(batch) {
    // Implement batch execution logic
    // This would depend on your specific API structure
    const endpoint = batch[0].endpoint;
    const requests = batch.map(r => r.request);
    
    return await apiClient.batchRequest(endpoint, requests);
  }

  generateRequestId() {
    return 'req_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  destroy() {
    clearTimeout(this.flushTimer);
    this.flush();
  }
}
```

### Caching Strategy

```javascript
// Multi-level caching implementation
class CachingScheduler {
  constructor(options = {}) {
    this.memoryCache = new Map(); // L1: Memory cache
    this.redisCache = options.redis; // L2: Redis cache
    this.apiClient = options.apiClient;
    
    // Cache TTL configuration
    this.ttl = {
      recommendations: 300, // 5 minutes
      schedules: 60, // 1 minute
      platforms: 3600 // 1 hour
    };
  }

  async getRecommendations(params) {
    const cacheKey = this.generateCacheKey('recommendations', params);
    
    // L1: Check memory cache
    let result = this.memoryCache.get(cacheKey);
    if (result) {
      return result;
    }

    // L2: Check Redis cache
    if (this.redisCache) {
      result = await this.redisCache.get(cacheKey);
      if (result) {
        this.memoryCache.set(cacheKey, result);
        return result;
      }
    }

    // Cache miss - fetch from API
    result = await this.apiClient.getRecommendations(params);
    
    // Populate caches
    this.memoryCache.set(cacheKey, result);
    if (this.redisCache) {
      await this.redisCache.setex(cacheKey, this.ttl.recommendations, JSON.stringify(result));
    }

    return result;
  }

  async invalidateSchedule(scheduleId) {
    // Invalidate all related cache entries
    const patterns = [
      `schedules:${scheduleId}*`,
      `recommendations:*`,
      `platforms:*`
    ];

    for (const pattern of patterns) {
      this.invalidatePattern(pattern);
    }
  }

  invalidatePattern(pattern) {
    // Remove from memory cache
    for (const key of this.memoryCache.keys()) {
      if (this.matchesPattern(key, pattern)) {
        this.memoryCache.delete(key);
      }
    }

    // Remove from Redis cache
    if (this.redisCache) {
      this.redisCache.keys(pattern).then(keys => {
        if (keys.length > 0) {
          this.redisCache.del(...keys);
        }
      });
    }
  }

  generateCacheKey(type, params) {
    const sorted = Object.keys(params).sort().reduce((result, key) => {
      result[key] = params[key];
      return result;
    }, {});
    return `${type}:${JSON.stringify(sorted)}`;
  }

  matchesPattern(key, pattern) {
    const regex = new RegExp(pattern.replace(/\*/g, '.*'));
    return regex.test(key);
  }
}
```

## Web Application Integration

### React Integration

```jsx
// React hooks for scheduling API
import { useState, useEffect, useCallback, useRef } from 'react';

export function useSchedulingAPI(apiClient) {
  const [recommendations, setRecommendations] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);

  const fetchRecommendations = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    
    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    abortControllerRef.current = new AbortController();
    
    try {
      const result = await apiClient.getRecommendations({
        ...params,
        signal: abortControllerRef.current.signal
      });
      setRecommendations(result.data);
      return result;
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err);
        throw err;
      }
    } finally {
      setLoading(false);
    }
  }, [apiClient]);

  const createSchedule = useCallback(async (scheduleData) => {
    setLoading(true);
    setError(null);
    
    try {
      const schedule = await apiClient.createSchedule(scheduleData);
      setSchedules(prev => [...prev, schedule]);
      return schedule;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiClient]);

  const optimizeSchedule = useCallback(async (scheduleId, optimizationData) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiClient.optimizeSchedule({
        scheduleId,
        ...optimizationData
      });
      
      // Update schedule if changes were applied
      if (optimizationData.apply) {
        setSchedules(prev => prev.map(schedule => 
          schedule.id === scheduleId 
            ? { ...schedule, ...result.schedule }
            : schedule
        ));
      }
      
      return result;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiClient]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    recommendations,
    schedules,
    loading,
    error,
    fetchRecommendations,
    createSchedule,
    optimizeSchedule
  };
}

// Usage component
function ScheduleCreator() {
  const { 
    recommendations, 
    loading, 
    error, 
    fetchRecommendations, 
    createSchedule 
  } = useSchedulingAPI(schedulingAPI);

  const [selectedPlatforms, setSelectedPlatforms] = useState(['youtube']);

  useEffect(() => {
    fetchRecommendations({
      platforms: selectedPlatforms,
      targetCount: 10,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
    });
  }, [selectedPlatforms, fetchRecommendations]);

  const handleCreateSchedule = async (recommendation) => {
    try {
      const schedule = await createSchedule({
        title: 'My Schedule',
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        items: [{
          contentId: 'content_123',
          platform: selectedPlatforms[0],
          scheduledTime: recommendation.window_start
        }]
      });
      
      console.log('Schedule created:', schedule);
    } catch (err) {
      console.error('Failed to create schedule:', err);
    }
  };

  return (
    <div>
      <h2>Create Schedule</h2>
      
      {error && <div className="error">{error.message}</div>}
      {loading && <div className="loading">Loading...</div>}
      
      <div className="platform-selector">
        {['youtube', 'tiktok', 'instagram'].map(platform => (
          <label key={platform}>
            <input
              type="checkbox"
              checked={selectedPlatforms.includes(platform)}
              onChange={(e) => {
                if (e.target.checked) {
                  setSelectedPlatforms(prev => [...prev, platform]);
                } else {
                  setSelectedPlatforms(prev => prev.filter(p => p !== platform));
                }
              }}
            />
            {platform}
          </label>
        ))}
      </div>

      <div className="recommendations">
        <h3>Recommended Times</h3>
        {recommendations.map(rec => (
          <div key={rec.id} className="recommendation">
            <div>Score: {rec.score.toFixed(2)}</div>
            <div>Time: {new Date(rec.window_start).toLocaleString()}</div>
            <div>Reasons: {rec.reasons.join(', ')}</div>
            <button onClick={() => handleCreateSchedule(rec)}>
              Schedule This Time
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Vue.js Integration

```vue
<template>
  <div class="schedule-creator">
    <h2>Create Schedule</h2>
    
    <div v-if="error" class="error">{{ error.message }}</div>
    <div v-if="loading" class="loading">Loading...</div>
    
    <div class="platform-selector">
      <label v-for="platform in availablePlatforms" :key="platform">
        <input
          type="checkbox"
          v-model="selectedPlatforms"
          :value="platform"
        />
        {{ platform }}
      </label>
    </div>

    <div class="recommendations" v-if="recommendations.length">
      <h3>Recommended Times</h3>
      <div
        v-for="rec in recommendations"
        :key="rec.id"
        class="recommendation"
      >
        <div>Score: {{ rec.score.toFixed(2) }}</div>
        <div>Time: {{ formatDate(rec.window_start) }}</div>
        <div>Reasons: {{ rec.reasons.join(', ') }}</div>
        <button @click="handleCreateSchedule(rec)">
          Schedule This Time
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted } from 'vue';

export default {
  setup() {
    const schedulingAPI = inject('schedulingAPI');
    
    const recommendations = ref([]);
    const selectedPlatforms = ref(['youtube']);
    const loading = ref(false);
    const error = ref(null);
    
    const availablePlatforms = ['youtube', 'tiktok', 'instagram', 'linkedin'];

    const fetchRecommendations = async () => {
      if (selectedPlatforms.value.length === 0) return;
      
      loading.value = true;
      error.value = null;
      
      try {
        const result = await schedulingAPI.value.getRecommendations({
          platforms: selectedPlatforms.value,
          targetCount: 10,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        });
        recommendations.value = result.data;
      } catch (err) {
        error.value = err;
      } finally {
        loading.value = false;
      }
    };

    const handleCreateSchedule = async (recommendation) => {
      try {
        const schedule = await schedulingAPI.value.createSchedule({
          title: 'My Schedule',
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          items: [{
            contentId: 'content_123',
            platform: selectedPlatforms.value[0],
            scheduledTime: recommendation.window_start
          }]
        });
        
        console.log('Schedule created:', schedule);
      } catch (err) {
        error.value = err;
      }
    };

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString();
    };

    watch(selectedPlatforms, fetchRecommendations);
    onMounted(fetchRecommendations);

    return {
      recommendations,
      selectedPlatforms,
      availablePlatforms,
      loading,
      error,
      fetchRecommendations,
      handleCreateSchedule,
      formatDate
    };
  }
};
</script>
```

## Mobile App Integration

### React Native Integration

```javascript
// React Native hooks for scheduling
import { useState, useEffect, useCallback } from 'react';
import { Alert } from 'react-native';
import { useNetInfo } from '@react-native-community/netinfo';

export function useSchedulingAPI(apiClient) {
  const [recommendations, setRecommendations] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const netInfo = useNetInfo();

  const fetchRecommendations = useCallback(async (params) => {
    if (!netInfo.isConnected) {
      Alert.alert('No Internet', 'Please check your internet connection');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await apiClient.getRecommendations(params);
      setRecommendations(result.data);
      return result;
    } catch (err) {
      setError(err);
      Alert.alert('Error', err.message);
    } finally {
      setLoading(false);
    }
  }, [apiClient, netInfo.isConnected]);

  const createSchedule = useCallback(async (scheduleData) => {
    if (!netInfo.isConnected) {
      Alert.alert('No Internet', 'Please check your internet connection');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const schedule = await apiClient.createSchedule(scheduleData);
      setSchedules(prev => [...prev, schedule]);
      Alert.alert('Success', 'Schedule created successfully');
      return schedule;
    } catch (err) {
      setError(err);
      Alert.alert('Error', err.message);
    } finally {
      setLoading(false);
    }
  }, [apiClient, netInfo.isConnected]);

  // Offline queue support
  const queueOfflineAction = useCallback((action, data) => {
    // Store in AsyncStorage for later processing
    AsyncStorage.getItem('offlineQueue')
      .then(queue => JSON.parse(queue || '[]'))
      .then(currentQueue => {
        const newQueue = [...currentQueue, { action, data, timestamp: Date.now() }];
        return AsyncStorage.setItem('offlineQueue', JSON.stringify(newQueue));
      });
  }, []);

  const processOfflineQueue = useCallback(async () => {
    if (!netInfo.isConnected) return;

    const queue = await AsyncStorage.getItem('offlineQueue');
    if (!queue) return;

    const offlineQueue = JSON.parse(queue);
    
    for (const item of offlineQueue) {
      try {
        switch (item.action) {
          case 'createSchedule':
            await createSchedule(item.data);
            break;
          // Add other offline actions
        }
      } catch (err) {
        console.error('Failed to process offline action:', err);
      }
    }

    // Clear queue after processing
    await AsyncStorage.removeItem('offlineQueue');
  }, [netInfo.isConnected, createSchedule]);

  useEffect(() => {
    if (netInfo.isConnected) {
      processOfflineQueue();
    }
  }, [netInfo.isConnected, processOfflineQueue]);

  return {
    recommendations,
    schedules,
    loading,
    error,
    fetchRecommendations,
    createSchedule,
    queueOfflineAction
  };
}

// Usage in React Native component
function ScheduleScreen() {
  const { 
    recommendations, 
    loading, 
    error, 
    fetchRecommendations, 
    createSchedule 
  } = useSchedulingAPI(schedulingAPI);

  const [selectedPlatforms, setSelectedPlatforms] = useState(['youtube']);

  useEffect(() => {
    fetchRecommendations({
      platforms: selectedPlatforms,
      targetCount: 5, // Smaller count for mobile
      timezone: Platform.OS === 'ios' 
        ? RNLocalize.getTimeZone()
        : NativeModules.SourceCode.scriptURL
    });
  }, [selectedPlatforms]);

  const handleCreateSchedule = async (recommendation) => {
    try {
      const schedule = await createSchedule({
        title: 'Mobile Schedule',
        timezone: getCurrentTimeZone(),
        items: [{
          contentId: 'content_123',
          platform: selectedPlatforms[0],
          scheduledTime: recommendation.window_start
        }]
      });
      
      // Navigate to schedule details
      navigation.navigate('ScheduleDetails', { scheduleId: schedule.id });
    } catch (err) {
      console.error('Failed to create schedule:', err);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Create Schedule</Text>
      
      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error.message}</Text>
        </View>
      )}
      
      <PlatformSelector
        platforms={['youtube', 'tiktok', 'instagram']}
        selected={selectedPlatforms}
        onSelectionChange={setSelectedPlatforms}
      />

      <RecommendationList
        recommendations={recommendations}
        loading={loading}
        onSchedulePress={handleCreateSchedule}
      />
    </ScrollView>
  );
}
```

### Flutter Integration

```dart
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

// Scheduling API client for Flutter
class SchedulingAPIClient {
  final String baseUrl;
  final String apiKey;
  
  SchedulingAPIClient({required this.baseUrl, required this.apiKey});

  Future<Map<String, dynamic>> getRecommendations(Map<String, dynamic> params) async {
    final uri = Uri.parse('$baseUrl/scheduling/recommendations')
        .replace(queryParameters: _buildQueryParams(params));
    
    final response = await http.get(
      uri,
      headers: {
        'Authorization': 'Bearer $apiKey',
        'Content-Type': 'application/json',
      },
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to get recommendations: ${response.statusCode}');
    }
  }

  Future<Map<String, dynamic>> createSchedule(Map<String, dynamic> scheduleData) async {
    final response = await http.post(
      Uri.parse('$baseUrl/scheduling/calendar'),
      headers: {
        'Authorization': 'Bearer $apiKey',
        'Content-Type': 'application/json',
        'Idempotency-Key': _generateIdempotencyKey(),
      },
      body: json.encode(scheduleData),
    );

    if (response.statusCode == 201) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to create schedule: ${response.statusCode}');
    }
  }

  Map<String, String> _buildQueryParams(Map<String, dynamic> params) {
    final queryParams = <String, String>{};
    
    params.forEach((key, value) {
      if (value is List) {
        value.forEach((item) => {
          queryParams.addAll({'${key}[]': item.toString()});
        });
      } else {
        queryParams[key] = value.toString();
      }
    });
    
    return queryParams;
  }

  String _generateIdempotencyKey() {
    return 'key_${DateTime.now().millisecondsSinceEpoch}_${DateTime.now().microsecond}';
  }
}

// Flutter widget
class ScheduleCreatorScreen extends StatefulWidget {
  @override
  _ScheduleCreatorScreenState createState() => _ScheduleCreatorScreenState();
}

class _ScheduleCreatorScreenState extends State<ScheduleCreatorScreen> {
  final apiClient = SchedulingAPIClient(
    baseUrl: 'https://api.content-automation.com/api/v1',
    apiKey: 'your-api-key',
  );

  List<Map<String, dynamic>> recommendations = [];
  bool isLoading = false;
  String? error;
  List<String> selectedPlatforms = ['youtube'];

  @override
  void initState() {
    super.initState();
    fetchRecommendations();
  }

  Future<void> fetchRecommendations() async {
    setState(() {
      isLoading = true;
      error = null;
    });

    try {
      final result = await apiClient.getRecommendations({
        'platforms': selectedPlatforms,
        'target_count': 5,
      });
      
      setState(() {
        recommendations = List<Map<String, dynamic>>.from(result['data']);
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        error = e.toString();
        isLoading = false;
      });
    }
  }

  Future<void> createSchedule(Map<String, dynamic> recommendation) async {
    try {
      final schedule = await apiClient.createSchedule({
        'title': 'Flutter Schedule',
        'timezone': 'America/New_York',
        'items': [
          {
            'content_id': 'content_123',
            'platform': selectedPlatforms.first,
            'scheduled_time': recommendation['window_start'],
          }
        ],
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Schedule created: ${schedule['id']}')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to create schedule: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Create Schedule')),
      body: Column(
        children: [
          // Platform selector
          PlatformSelector(
            selected: selectedPlatforms,
            onChanged: (platforms) {
              setState(() {
                selectedPlatforms = platforms;
              });
              fetchRecommendations();
            },
          ),

          // Error display
          if (error != null)
            Padding(
              padding: EdgeInsets.all(16),
              child: Text('Error: $error', style: TextStyle(color: Colors.red)),
            ),

          // Loading indicator
          if (isLoading)
            Padding(
              padding: EdgeInsets.all(16),
              child: CircularProgressIndicator(),
            ),

          // Recommendations list
          Expanded(
            child: ListView.builder(
              itemCount: recommendations.length,
              itemBuilder: (context, index) {
                final rec = recommendations[index];
                return RecommendationCard(
                  recommendation: rec,
                  onSchedule: () => createSchedule(rec),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class RecommendationCard extends StatelessWidget {
  final Map<String, dynamic> recommendation;
  final VoidCallback onSchedule;

  RecommendationCard({
    required this.recommendation,
    required this.onSchedule,
  });

  @override
  Widget build(BuildContext context) {
    final score = (recommendation['score'] as num).toDouble();
    final startTime = DateTime.parse(recommendation['window_start']);
    
    return Card(
      margin: EdgeInsets.all(8),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Score: ${(score * 100).toStringAsFixed(1)}%',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            Text('Time: ${startTime.toLocal()}'),
            Text('Reasons: ${(recommendation['reasons'] as List).join(', ')}'),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: onSchedule,
              child: Text('Schedule This Time'),
            ),
          ],
        ),
      ),
    );
  }
}
```

## Backend Service Integration

### Node.js Integration

```javascript
// Express.js middleware for scheduling API
const express = require('express');
const { SchedulingClient } = require('@content-automation/js-sdk');

const app = express();

// Initialize scheduling client
const schedulingClient = new SchedulingClient({
  apiKey: process.env.SCHEDULING_API_KEY,
  baseUrl: 'https://api.content-automation.com/api/v1',
  maxRetries: 3,
  retryDelay: 1000
});

// Middleware to add scheduling client to request
app.use((req, res, next) => {
  req.scheduling = schedulingClient;
  next();
});

// API endpoints
app.post('/api/schedules', async (req, res) => {
  try {
    const { title, items, timezone } = req.body;
    
    // Validate input
    if (!title || !items || !timezone) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    // Create schedule
    const schedule = await req.scheduling.createSchedule({
      title,
      timezone,
      items
    });

    res.status(201).json(schedule);
  } catch (error) {
    console.error('Schedule creation failed:', error);
    res.status(error.status || 500).json({
      error: error.message || 'Internal server error'
    });
  }
});

app.get('/api/schedules/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const schedule = await req.scheduling.getSchedule(id, {
      expand: ['items', 'metrics']
    });

    if (!schedule) {
      return res.status(404).json({ error: 'Schedule not found' });
    }

    res.json(schedule);
  } catch (error) {
    console.error('Failed to get schedule:', error);
    res.status(error.status || 500).json({
      error: error.message || 'Internal server error'
    });
  }
});

// Batch operations
app.post('/api/schedules/batch', async (req, res) => {
  const { operations } = req.body;
  
  if (!Array.isArray(operations)) {
    return res.status(400).json({ error: 'Operations must be an array' });
  }

  try {
    const results = await Promise.allSettled(
      operations.map(async (op) => {
        switch (op.type) {
          case 'create':
            return req.scheduling.createSchedule(op.data);
          case 'optimize':
            return req.scheduling.optimizeSchedule(op.data);
          default:
            throw new Error(`Unknown operation type: ${op.type}`);
        }
      })
    );

    const successful = [];
    const failed = [];

    results.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        successful.push({ index, result: result.value });
      } else {
        failed.push({ index, error: result.reason.message });
      }
    });

    res.json({ successful, failed });
  } catch (error) {
    console.error('Batch operations failed:', error);
    res.status(500).json({ error: 'Batch operations failed' });
  }
});

// Background job processing
const Bull = require('bull');
const scheduleQueue = new Bull('schedule processing', {
  redis: process.env.REDIS_URL
});

scheduleQueue.process(async (job) => {
  const { operation, data } = job.data;
  
  try {
    switch (operation) {
      case 'create_schedule':
        return await schedulingClient.createSchedule(data);
      case 'optimize_schedule':
        return await schedulingClient.optimizeSchedule(data);
      default:
        throw new Error(`Unknown operation: ${operation}`);
    }
  } catch (error) {
    throw new Error(`Job failed: ${error.message}`);
  }
});

// Enqueue background jobs
app.post('/api/schedules/:id/optimize', async (req, res) => {
  try {
    const { id } = req.params;
    const { targets, constraints } = req.body;

    await scheduleQueue.add('optimize_schedule', {
      operation: 'optimize_schedule',
      data: {
        scheduleId: id,
        targets,
        constraints,
        apply: true
      }
    });

    res.status(202).json({ status: 'queued' });
  } catch (error) {
    console.error('Failed to queue optimization:', error);
    res.status(500).json({ error: 'Failed to queue optimization' });
  }
});

app.listen(3000, () => {
  console.log('Scheduling API server running on port 3000');
});
```

### Python Integration (FastAPI)

```python
# FastAPI application with scheduling integration
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
import uuid
from datetime import datetime

from scheduling_client import SchedulingClient

app = FastAPI(title="Scheduling API Integration")

# Initialize scheduling client
scheduling_client = SchedulingClient({
    'base_url': 'https://api.content-automation.com/api/v1',
    'api_key': os.environ['SCHEDULING_API_KEY'],
    'max_retries': 3,
    'retry_delay': 1
})

# Pydantic models
class ScheduleItem(BaseModel):
    content_id: str
    platform: str
    scheduled_time: datetime
    metadata: Optional[Dict[str, Any]] = None
    callbacks: Optional[Dict[str, str]] = None

class CreateScheduleRequest(BaseModel):
    title: str
    timezone: str = "UTC"
    items: List[ScheduleItem]
    processing_deadline_ms: Optional[int] = 10800000

class OptimizationTarget(BaseModel):
    content_id: str
    platform: str
    current_scheduled_time: datetime

class OptimizationRequest(BaseModel):
    schedule_id: str
    targets: List[OptimizationTarget]
    apply: bool = False

# Dependency to get scheduling client
async def get_scheduling_client() -> SchedulingClient:
    return scheduling_client

# API endpoints
@app.post("/api/schedules", response_model=Dict[str, Any])
async def create_schedule(
    request: CreateScheduleRequest,
    scheduling_client: SchedulingClient = Depends(get_scheduling_client)
):
    """Create a new schedule"""
    try:
        # Validate input
        if not request.items:
            raise HTTPException(status_code=400, detail="At least one item is required")
        
        # Convert to API format
        schedule_data = {
            'title': request.title,
            'timezone': request.timezone,
            'items': [
                {
                    'content_id': item.content_id,
                    'platform': item.platform,
                    'scheduled_time': item.scheduled_time.isoformat(),
                    'metadata': item.metadata,
                    'callbacks': item.callbacks
                }
                for item in request.items
            ],
            'processing_deadline_ms': request.processing_deadline_ms
        }
        
        # Create schedule
        idempotency_key = str(uuid.uuid4())
        schedule = await scheduling_client.create_schedule(schedule_data, idempotency_key)
        
        return schedule
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/schedules/{schedule_id}", response_model=Dict[str, Any])
async def get_schedule(
    schedule_id: str,
    expand: Optional[List[str]] = None,
    scheduling_client: SchedulingClient = Depends(get_scheduling_client)
):
    """Get schedule details"""
    try:
        params = {}
        if expand:
            params['expand'] = expand
        
        schedule = await scheduling_client.get_schedule(schedule_id, params)
        return schedule
    except Exception as e:
        raise HTTPException(status_code=404, detail="Schedule not found")

@app.post("/api/schedules/{schedule_id}/optimize", response_model=Dict[str, Any])
async def optimize_schedule(
    schedule_id: str,
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    scheduling_client: SchedulingClient = Depends(get_scheduling_client)
):
    """Optimize schedule timing"""
    try:
        optimization_request = {
            'schedule_id': schedule_id,
            'targets': [
                {
                    'content_id': target.content_id,
                    'platform': target.platform,
                    'current_scheduled_time': target.current_scheduled_time.isoformat()
                }
                for target in request.targets
            ],
            'apply': request.apply
        }
        
        # Add background task for async processing
        background_tasks.add_task(
            run_optimization, 
            scheduling_client, 
            optimization_request
        )
        
        return {"status": "optimization_started", "schedule_id": schedule_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def run_optimization(client: SchedulingClient, request: Dict[str, Any]):
    """Background task to run optimization"""
    try:
        result = await client.optimize_schedule(request)
        # Notify webhook or update database
        print(f"Optimization completed: {result}")
    except Exception as e:
        print(f"Optimization failed: {e}")

# Batch operations
@app.post("/api/schedules/batch")
async def batch_operations(
    operations: List[Dict[str, Any]],
    scheduling_client: SchedulingClient = Depends(get_scheduling_client)
):
    """Execute batch operations"""
    results = []
    
    for i, operation in enumerate(operations):
        try:
            if operation['type'] == 'create_schedule':
                result = await scheduling_client.create_schedule(operation['data'])
                results.append({'index': i, 'status': 'success', 'result': result})
            elif operation['type'] == 'optimize_schedule':
                result = await scheduling_client.optimize_schedule(operation['data'])
                results.append({'index': i, 'status': 'success', 'result': result})
            else:
                results.append({
                    'index': i, 
                    'status': 'error', 
                    'error': f"Unknown operation: {operation['type']}"
                })
        except Exception as e:
            results.append({
                'index': i, 
                'status': 'error', 
                'error': str(e)
            })
    
    return {'results': results}

# WebSocket for real-time updates
@app.websocket("/ws/schedules/{schedule_id}")
async def schedule_websocket(websocket: WebSocket, schedule_id: str):
    await websocket.accept()
    
    try:
        # Connect to scheduling WebSocket
        connection_id = await scheduling_client.connect_to_websocket(
            schedule_id,
            on_message=lambda message: asyncio.create_task(
                websocket.send_json(message)
            )
        )
        
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
    except WebSocketDisconnect:
        scheduling_client.disconnect_from_websocket(connection_id)

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "scheduling_service": "available"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

This completes the comprehensive integration guide for the Scheduling API. The guide covers various integration patterns, security implementations, performance optimizations, and provides practical examples for different platforms and architectures.

Key highlights include:

- **Architecture patterns** for different complexity levels
- **Security implementations** with JWT, API keys, and request signing
- **Error handling strategies** with retry logic and circuit breakers
- **Performance optimizations** with caching, batching, and request optimization
- **Platform-specific integrations** for web, mobile, and backend applications
- **Real-time updates** implementation with WebSocket support
- **Production considerations** including monitoring and scaling

This guide provides developers with everything needed to successfully integrate the Scheduling Optimization API into their applications while following best practices for security, performance, and reliability.
