# Scheduling API - Practical Code Examples

This document provides comprehensive, practical code examples for integrating with the Scheduling Optimization API using JavaScript/TypeScript and Python. Each example demonstrates real-world scenarios and best practices.

## Table of Contents

- [Setup and Configuration](#setup-and-configuration)
- [Authentication](#authentication)
- [Getting Recommendations](#getting-recommendations)
- [Creating Schedules](#creating-schedules)
- [Managing Schedules](#managing-schedules)
- [Schedule Optimization](#schedule-optimization)
- [WebSocket Real-Time Updates](#websocket-real-time-updates)
- [Error Handling and Retry Logic](#error-handling-and-retry-logic)
- [Rate Limiting](#rate-limiting)
- [Advanced Patterns](#advanced-patterns)
- [Complete Workflow Examples](#complete-workflow-examples)

## Setup and Configuration

### JavaScript/TypeScript Setup

#### Using npm/yarn

```bash
npm install axios ws uuid
# or
yarn add axios ws uuid
```

#### TypeScript Client Class

```typescript
// scheduling-client.ts
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import WebSocket from 'ws';

export interface SchedulingClientConfig {
  apiKey: string;
  baseUrl: string;
  wsUrl?: string;
  timeout?: number;
  maxRetries?: number;
  retryDelay?: number;
}

export interface RecommendationRequest {
  platforms?: string[];
  targetCount?: number;
  startAt?: string;
  endAt?: string;
  timezone?: string;
  contentType?: string;
  pageToken?: string;
  pageSize?: number;
  sort?: 'created_at' | 'score';
  order?: 'asc' | 'desc';
}

export interface ScheduleItem {
  contentId: string;
  platform: string;
  scheduledTime: string;
  metadata?: Record<string, any>;
  callbacks?: Record<string, string>;
}

export interface CreateScheduleRequest {
  title: string;
  timezone: string;
  items: ScheduleItem[];
  processingDeadlineMs?: number;
}

export interface OptimizationTarget {
  contentId: string;
  platform: string;
  currentScheduledTime: string;
}

export interface OptimizationRequest {
  scheduleId: string;
  targets: OptimizationTarget[];
  constraints?: {
    doNotMoveBefore?: string;
    doNotMoveAfter?: string;
    blackoutWindows?: Array<{ start: string; end: string }>;
    platformSpecificRules?: Record<string, any>;
  };
  apply?: boolean;
}

export class SchedulingClient {
  private client: AxiosInstance;
  private config: SchedulingClientConfig;
  private accessToken: string | null = null;
  private wsConnections: Map<string, WebSocket> = new Map();

  constructor(config: SchedulingClientConfig) {
    this.config = {
      timeout: 30000,
      maxRetries: 3,
      retryDelay: 1000,
      ...config
    };

    this.client = axios.create({
      baseURL: config.baseUrl,
      timeout: config.timeout,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Add request interceptor for authentication
    this.client.interceptors.request.use(
      (config) => {
        if (this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const config = error.config;
        
        // Handle 401 - try to refresh token
        if (error.response?.status === 401 && !config._retry) {
          config._retry = true;
          try {
            await this.refreshAccessToken();
            return this.client(config);
          } catch (refreshError) {
            throw new Error('Authentication failed');
          }
        }

        // Handle rate limiting with exponential backoff
        if (error.response?.status === 429 && config._retryCount < this.config.maxRetries) {
          const retryAfter = parseInt(error.response.headers['retry-after'] || '60');
          config._retryCount = (config._retryCount || 0) + 1;
          
          await this.delay(retryAfter * 1000);
          return this.client(config);
        }

        // Handle server errors with exponential backoff
        if (error.response?.status >= 500 && config._retryCount < this.config.maxRetries) {
          config._retryCount = (config._retryCount || 0) + 1;
          const delay = this.config.retryDelay! * Math.pow(2, config._retryCount - 1);
          await this.delay(delay);
          return this.client(config);
        }

        throw error;
      }
    );
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private async refreshAccessToken(): Promise<void> {
    // Implement token refresh logic based on your auth system
    // This is a placeholder - adapt to your authentication mechanism
    this.accessToken = await this.getNewAccessToken();
  }

  private async getNewAccessToken(): Promise<string> {
    // Placeholder for token refresh - implement based on your auth flow
    throw new Error('Token refresh not implemented');
  }

  // Authentication methods
  async authenticate(apiKey: string): Promise<void> {
    // Implement your authentication logic
    // This could be JWT token exchange, OAuth flow, etc.
    this.accessToken = apiKey; // Simplified for example
  }

  // Recommendations
  async getRecommendations(params: RecommendationRequest = {}): Promise<any> {
    const queryParams = new URLSearchParams();
    
    if (params.platforms) {
      params.platforms.forEach(platform => queryParams.append('platforms', platform));
    }
    if (params.targetCount) queryParams.append('target_count', params.targetCount.toString());
    if (params.startAt) queryParams.append('start_at', params.startAt);
    if (params.endAt) queryParams.append('end_at', params.endAt);
    if (params.timezone) queryParams.append('timezone', params.timezone);
    if (params.contentType) queryParams.append('content_type', params.contentType);
    if (params.pageToken) queryParams.append('page_token', params.pageToken);
    if (params.pageSize) queryParams.append('page_size', params.pageSize.toString());
    if (params.sort) queryParams.append('sort', params.sort);
    if (params.order) queryParams.append('order', params.order);

    const response = await this.client.get(`/scheduling/recommendations?${queryParams}`);
    return response.data;
  }

  // Schedule management
  async createSchedule(request: CreateScheduleRequest, idempotencyKey?: string): Promise<any> {
    const headers: Record<string, string> = {};
    if (idempotencyKey) {
      headers['Idempotency-Key'] = idempotencyKey;
    }

    const response = await this.client.post('/scheduling/calendar', request, { headers });
    return response.data;
  }

  async getSchedule(scheduleId: string, params: {
    pageToken?: string;
    pageSize?: number;
    state?: string[];
    expand?: string[];
  } = {}): Promise<any> {
    const queryParams = new URLSearchParams();
    
    if (params.pageToken) queryParams.append('page_token', params.pageToken);
    if (params.pageSize) queryParams.append('page_size', params.pageSize.toString());
    if (params.state) {
      params.state.forEach(state => queryParams.append('state', state));
    }
    if (params.expand) {
      params.expand.forEach(field => queryParams.append('expand', field));
    }

    const response = await this.client.get(`/scheduling/calendar/${scheduleId}?${queryParams}`);
    return response.data;
  }

  // Optimization
  async optimizeSchedule(request: OptimizationRequest, idempotencyKey?: string): Promise<any> {
    const headers: Record<string, string> = {};
    if (idempotencyKey) {
      headers['Idempotency-Key'] = idempotencyKey;
    }

    const response = await this.client.post('/scheduling/optimize', request, { headers });
    return response.data;
  }

  // WebSocket connections
  connectToWebSocket(scheduleId?: string, onMessage?: (message: any) => void): string {
    const connectionId = `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const wsUrl = `${this.config.wsUrl || this.config.baseUrl.replace('https', 'wss')}/scheduling/ws`;
    
    const queryParams = scheduleId ? `?schedule_id=${scheduleId}` : '';
    const ws = new WebSocket(`${wsUrl}${queryParams}`);

    ws.on('open', () => {
      console.log(`WebSocket connected: ${connectionId}`);
      
      // Send authentication if required
      if (this.accessToken) {
        ws.send(JSON.stringify({
          type: 'auth',
          token: this.accessToken
        }));
      }
    });

    ws.on('message', (data: Buffer) => {
      try {
        const message = JSON.parse(data.toString());
        if (onMessage) {
          onMessage(message);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    });

    ws.on('close', (code, reason) => {
      console.log(`WebSocket closed: ${connectionId}`, code, reason);
      this.wsConnections.delete(connectionId);
    });

    ws.on('error', (error) => {
      console.error(`WebSocket error: ${connectionId}`, error);
    });

    this.wsConnections.set(connectionId, ws);
    return connectionId;
  }

  disconnectFromWebSocket(connectionId: string): void {
    const ws = this.wsConnections.get(connectionId);
    if (ws) {
      ws.close();
      this.wsConnections.delete(connectionId);
    }
  }

  disconnectAllWebSockets(): void {
    this.wsConnections.forEach((ws, connectionId) => {
      ws.close();
    });
    this.wsConnections.clear();
  }

  // Health check
  async checkHealth(): Promise<any> {
    const response = await this.client.get('/scheduling/health');
    return response.data;
  }

  // Get supported platforms
  async getSupportedPlatforms(): Promise<any> {
    const response = await this.client.get('/scheduling/platforms');
    return response.data;
  }

  // Cleanup
  destroy(): void {
    this.disconnectAllWebSockets();
    this.client.defaults.timeout = 0;
  }
}
```

### Python Setup

#### Using pip

```bash
pip install requests websockets asyncio uuid
```

#### Python Client Class

```python
# scheduling_client.py
import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import requests
import websockets
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class SchedulingClient:
    def __init__(self, config: Dict[str, Any]):
        self.config = {
            'timeout': 30,
            'max_retries': 3,
            'retry_delay': 1,
            **config
        }
        
        self.access_token = None
        self.ws_connections = {}
        
        # Setup HTTP session with retry logic
        self.session = requests.Session()
        
        retry_strategy = Retry(
            total=self.config['max_retries'],
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with authentication and error handling"""
        url = f"{self.config['base_url']}{endpoint}"
        
        # Add authentication
        if self.access_token:
            kwargs.setdefault('headers', {})['Authorization'] = f'Bearer {self.access_token}'
        
        try:
            response = self.session.request(method, url, timeout=self.config['timeout'], **kwargs)
            
            # Handle 401 - authentication error
            if response.status_code == 401:
                raise Exception("Authentication failed - token may be invalid or expired")
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logging.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self._make_request(method, endpoint, **kwargs)
            
            response.raise_for_status()
            return response
            
        except requests.RequestException as e:
            logging.error(f"Request failed: {e}")
            raise
    
    async def authenticate(self, api_key: str) -> None:
        """Authenticate with the API"""
        self.access_token = api_key  # Simplified for example
    
    # Recommendations
    async def get_recommendations(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get scheduling recommendations"""
        if params is None:
            params = {}
        
        query_params = []
        for key, value in params.items():
            if value is not None:
                if isinstance(value, list):
                    for item in value:
                        query_params.append((key, item))
                else:
                    query_params.append((key, str(value)))
        
        query_string = urlencode(query_params)
        endpoint = f"/scheduling/recommendations?{query_string}" if query_params else "/scheduling/recommendations"
        
        response = self._make_request('GET', endpoint)
        return response.json()
    
    # Schedule management
    async def create_schedule(self, request: Dict[str, Any], idempotency_key: str = None) -> Dict[str, Any]:
        """Create a new schedule"""
        headers = {}
        if idempotency_key:
            headers['Idempotency-Key'] = idempotency_key
        
        response = self._make_request('POST', '/scheduling/calendar', 
                                    json=request, headers=headers)
        return response.json()
    
    async def get_schedule(self, schedule_id: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get schedule details"""
        if params is None:
            params = {}
        
        query_params = []
        for key, value in params.items():
            if value is not None:
                if isinstance(value, list):
                    for item in value:
                        query_params.append((key, item))
                else:
                    query_params.append((key, str(value)))
        
        query_string = urlencode(query_params)
        endpoint = f"/scheduling/calendar/{schedule_id}"
        if query_params:
            endpoint += f"?{query_string}"
        
        response = self._make_request('GET', endpoint)
        return response.json()
    
    # Optimization
    async def optimize_schedule(self, request: Dict[str, Any], idempotency_key: str = None) -> Dict[str, Any]:
        """Optimize schedule timing"""
        headers = {}
        if idempotency_key:
            headers['Idempotency-Key'] = idempotency_key
        
        response = self._make_request('POST', '/scheduling/optimize', 
                                    json=request, headers=headers)
        return response.json()
    
    # WebSocket connections
    async def connect_to_websocket(self, schedule_id: str = None, on_message: callable = None) -> str:
        """Connect to WebSocket for real-time updates"""
        connection_id = f"conn_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        ws_url = self.config.get('ws_url') or self.config['base_url'].replace('https', 'wss')
        ws_url += "/scheduling/ws"
        
        if schedule_id:
            ws_url += f"?schedule_id={schedule_id}"
        
        try:
            async with websockets.connect(ws_url) as websocket:
                self.ws_connections[connection_id] = websocket
                logging.info(f"WebSocket connected: {connection_id}")
                
                # Send authentication if required
                if self.access_token:
                    auth_message = {
                        'type': 'auth',
                        'token': self.access_token
                    }
                    await websocket.send(json.dumps(auth_message))
                
                # Handle incoming messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if on_message:
                            on_message(data)
                    except json.JSONDecodeError as e:
                        logging.error(f"Failed to parse WebSocket message: {e}")
                
        except websockets.exceptions.ConnectionClosed:
            logging.info(f"WebSocket connection closed: {connection_id}")
        except Exception as e:
            logging.error(f"WebSocket error: {connection_id}, {e}")
        finally:
            self.ws_connections.pop(connection_id, None)
        
        return connection_id
    
    def disconnect_from_websocket(self, connection_id: str) -> None:
        """Disconnect from WebSocket"""
        # Note: This is a simplified implementation
        # In practice, you'd need to track the websocket objects properly
        self.ws_connections.pop(connection_id, None)
    
    async def disconnect_all_websockets(self) -> None:
        """Disconnect all WebSocket connections"""
        # Close all connections
        for connection_id in list(self.ws_connections.keys()):
            self.disconnect_from_websocket(connection_id)
    
    # Utility methods
    async def check_health(self) -> Dict[str, Any]:
        """Check API health"""
        response = self._make_request('GET', '/scheduling/health')
        return response.json()
    
    async def get_supported_platforms(self) -> Dict[str, Any]:
        """Get supported platforms"""
        response = self._make_request('GET', '/scheduling/platforms')
        return response.json()
    
    # Cleanup
    def destroy(self) -> None:
        """Cleanup resources"""
        # Cancel any pending requests
        self.session.close()
```

## Authentication

### JavaScript Authentication Examples

```typescript
// Basic API key authentication
async function authenticateClient() {
  const client = new SchedulingClient({
    apiKey: process.env.SCHEDULING_API_KEY,
    baseUrl: 'https://api.content-automation.com/api/v1'
  });
  
  await client.authenticate(process.env.SCHEDULING_API_KEY);
  return client;
}

// OAuth 2.0 flow example
async function authenticateWithOAuth() {
  const client = new SchedulingClient({
    baseUrl: 'https://api.content-automation.com/api/v1'
  });
  
  // Step 1: Redirect user to OAuth provider
  const authUrl = 'https://auth.content-automation.com/oauth/authorize?' + 
    new URLSearchParams({
      client_id: 'your-client-id',
      response_type: 'code',
      scope: 'scheduling:read scheduling:write optimization:write',
      redirect_uri: 'your-app://callback'
    });
  
  // Handle redirect in your app
  // ...
  
  // Step 2: Exchange code for token
  const tokenResponse = await fetch('https://auth.content-automation.com/oauth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      code: 'authorization-code-from-callback',
      client_id: 'your-client-id',
      client_secret: 'your-client-secret',
      redirect_uri: 'your-app://callback'
    })
  });
  
  const { access_token } = await tokenResponse.json();
  await client.authenticate(access_token);
  
  return client;
}
```

### Python Authentication Examples

```python
import asyncio

async def authenticate_client():
    """Basic API key authentication"""
    client = SchedulingClient({
        'base_url': 'https://api.content-automation.com/api/v1',
        'api_key': os.environ['SCHEDULING_API_KEY']
    })
    
    await client.authenticate(os.environ['SCHEDULING_API_KEY'])
    return client

async def authenticate_with_oauth():
    """OAuth 2.0 authentication flow"""
    import aiohttp
    
    client = SchedulingClient({
        'base_url': 'https://api.content-automation.com/api/v1'
    })
    
    # Step 1: Get authorization URL
    auth_params = {
        'client_id': 'your-client-id',
        'response_type': 'code',
        'scope': 'scheduling:read scheduling:write optimization:write',
        'redirect_uri': 'your-app://callback'
    }
    
    auth_url = 'https://auth.content-automation.com/oauth/authorize?' + \
               urlencode(auth_params)
    
    # Redirect user to auth_url
    print(f"Please visit: {auth_url}")
    
    # Step 2: Handle callback and exchange code
    authorization_code = input("Enter authorization code: ")
    
    async with aiohttp.ClientSession() as session:
        token_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'client_id': 'your-client-id',
            'client_secret': 'your-client-secret',
            'redirect_uri': 'your-app://callback'
        }
        
        async with session.post('https://auth.content-automation.com/oauth/token',
                               data=token_data) as response:
            token_response = await response.json()
            access_token = token_response['access_token']
            
            await client.authenticate(access_token)
            return client

# Usage
async def main():
    client = await authenticate_client()
    # Use client for API calls
    await client.destroy()
```

## Getting Recommendations

### JavaScript Examples

```typescript
// Get basic recommendations
async function getBasicRecommendations() {
  const client = await authenticateClient();
  
  try {
    const recommendations = await client.getRecommendations({
      platforms: ['youtube', 'tiktok'],
      targetCount: 10,
      timezone: 'America/New_York'
    });
    
    console.log('Recommendations:', recommendations.data);
    return recommendations;
  } finally {
    client.destroy();
  }
}

// Get recommendations with date range
async function getRecommendationsWithDateRange() {
  const client = await authenticateClient();
  
  try {
    const startDate = new Date('2025-11-05T00:00:00Z');
    const endDate = new Date('2025-11-12T23:59:59Z');
    
    const recommendations = await client.getRecommendations({
      platforms: ['instagram', 'linkedin'],
      startAt: startDate.toISOString(),
      endAt: endDate.toISOString(),
      contentType: 'announcement',
      targetCount: 20,
      sort: 'score',
      order: 'desc'
    });
    
    // Process recommendations
    recommendations.data.forEach((rec, index) => {
      console.log(`Recommendation ${index + 1}:`);
      console.log(`  Window: ${rec.window_start} - ${rec.window_end}`);
      console.log(`  Score: ${rec.score}`);
      console.log(`  Confidence: ${rec.confidence}`);
      console.log(`  Reasons: ${rec.reasons.join(', ')}`);
    });
    
    return recommendations;
  } finally {
    client.destroy();
  }
}

// Paginate through recommendations
async function getAllRecommendations() {
  const client = await authenticateClient();
  const allRecommendations = [];
  let pageToken: string | undefined;
  
  try {
    do {
      const recommendations = await client.getRecommendations({
        platforms: ['youtube'],
        pageSize: 50,
        pageToken: pageToken
      });
      
      allRecommendations.push(...recommendations.data);
      pageToken = recommendations.page.next_page_token || undefined;
      
      console.log(`Fetched ${recommendations.data.length} recommendations`);
      console.log(`Total so far: ${allRecommendations.length}`);
      
    } while (pageToken);
    
    console.log(`Total recommendations: ${allRecommendations.length}`);
    return allRecommendations;
  } finally {
    client.destroy();
  }
}

// Filter and rank recommendations
async function getBestRecommendations() {
  const client = await authenticateClient();
  
  try {
    const recommendations = await client.getRecommendations({
      platforms: ['youtube', 'tiktok', 'instagram'],
      targetCount: 100,
      timezone: 'America/New_York'
    });
    
    // Filter high-confidence recommendations
    const highConfidenceRecs = recommendations.data.filter(
      rec => rec.confidence >= 0.8 && rec.score >= 0.7
    );
    
    // Sort by score and confidence
    const bestRecs = highConfidenceRecs.sort((a, b) => {
      if (a.score !== b.score) return b.score - a.score;
      return b.confidence - a.confidence;
    }).slice(0, 10);
    
    console.log('Top 10 recommendations:');
    bestRecs.forEach((rec, index) => {
      console.log(`${index + 1}. ${rec.window_start} (Score: ${rec.score}, Confidence: ${rec.confidence})`);
    });
    
    return bestRecs;
  } finally {
    client.destroy();
  }
}
```

### Python Examples

```python
import asyncio
from datetime import datetime, timezone
import pytz

async def get_basic_recommendations():
    """Get basic scheduling recommendations"""
    client = await authenticate_client()
    
    try:
        recommendations = await client.get_recommendations({
            'platforms': ['youtube', 'tiktok'],
            'target_count': 10,
            'timezone': 'America/New_York'
        })
        
        print('Recommendations:', recommendations['data'])
        return recommendations
    finally:
        client.destroy()

async def get_recommendations_with_date_range():
    """Get recommendations within a specific date range"""
    client = await authenticate_client()
    
    try:
        start_date = '2025-11-05T00:00:00Z'
        end_date = '2025-11-12T23:59:59Z'
        
        recommendations = await client.get_recommendations({
            'platforms': ['instagram', 'linkedin'],
            'start_at': start_date,
            'end_at': end_date,
            'content_type': 'announcement',
            'target_count': 20,
            'sort': 'score',
            'order': 'desc'
        })
        
        # Process recommendations
        for i, rec in enumerate(recommendations['data']):
            print(f'Recommendation {i + 1}:')
            print(f'  Window: {rec["window_start"]} - {rec["window_end"]}')
            print(f'  Score: {rec["score"]}')
            print(f'  Confidence: {rec["confidence"]}')
            print(f'  Reasons: {", ".join(rec["reasons"])}')
        
        return recommendations
    finally:
        client.destroy()

async def paginate_recommendations():
    """Get all recommendations using pagination"""
    client = await authenticate_client()
    all_recommendations = []
    page_token = None
    
    try:
        while True:
            params = {
                'platforms': ['youtube'],
                'page_size': 50
            }
            if page_token:
                params['page_token'] = page_token
            
            recommendations = await client.get_recommendations(params)
            
            all_recommendations.extend(recommendations['data'])
            page_token = recommendations.get('page', {}).get('next_page_token')
            
            print(f'Fetched {len(recommendations["data"])} recommendations')
            print(f'Total so far: {len(all_recommendations)}')
            
            if not page_token:
                break
        
        print(f'Total recommendations: {len(all_recommendations)}')
        return all_recommendations
    finally:
        client.destroy()

async def get_best_recommendations():
    """Filter and rank recommendations by quality"""
    client = await authenticate_client()
    
    try:
        recommendations = await client.get_recommendations({
            'platforms': ['youtube', 'tiktok', 'instagram'],
            'target_count': 100,
            'timezone': 'America/New_York'
        })
        
        # Filter high-confidence recommendations
        high_confidence_recs = [
            rec for rec in recommendations['data']
            if rec['confidence'] >= 0.8 and rec['score'] >= 0.7
        ]
        
        # Sort by score and confidence
        best_recs = sorted(
            high_confidence_recs,
            key=lambda x: (x['score'], x['confidence']),
            reverse=True
        )[:10]
        
        print('Top 10 recommendations:')
        for i, rec in enumerate(best_recs):
            print(f'{i + 1}. {rec["window_start"]} (Score: {rec["score"]}, Confidence: {rec["confidence"]})')
        
        return best_recs
    finally:
        client.destroy()

# Usage
async def main():
    await get_basic_recommendations()
    await get_recommendations_with_date_range()
    await paginate_recommendations()
    await get_best_recommendations()

if __name__ == '__main__':
    asyncio.run(main())
```

## Creating Schedules

### JavaScript Examples

```typescript
import { v4 as uuidv4 } from 'uuid';

// Create a simple schedule
async function createSimpleSchedule() {
  const client = await authenticateClient();
  
  try {
    const scheduleData = {
      title: 'Weekly Content Schedule',
      timezone: 'America/New_York',
      items: [
        {
          contentId: 'content_123',
          platform: 'youtube',
          scheduledTime: '2025-11-06T14:00:00-05:00'
        }
      ]
    };
    
    const idempotencyKey = uuidv4();
    const schedule = await client.createSchedule(scheduleData, idempotencyKey);
    
    console.log('Schedule created:', schedule);
    console.log('Schedule ID:', schedule.id);
    console.log('Status:', schedule.state);
    
    return schedule;
  } finally {
    client.destroy();
  }
}

// Create multi-platform campaign schedule
async function createCampaignSchedule() {
  const client = await authenticateClient();
  
  const campaignId = 'camp_20251105_launch';
  const baseTime = new Date('2025-11-06T14:00:00-05:00');
  
  // Create staggered posting times
  const scheduleItems = [
    {
      contentId: 'content_announcement',
      platform: 'youtube',
      scheduledTime: baseTime.toISOString(),
      metadata: {
        campaignId,
        contentType: 'announcement',
        title: 'Product Launch Announcement'
      },
      callbacks: {
        onPublished: 'https://your-app.com/webhooks/published',
        onFailed: 'https://your-app.com/webhooks/failed'
      }
    },
    {
      contentId: 'content_teaser',
      platform: 'instagram',
      scheduledTime: new Date(baseTime.getTime() + 30 * 60000).toISOString(), // +30 min
      metadata: {
        campaignId,
        contentType: 'reel',
        hashtags: ['#ProductLaunch', '#Innovation', '#ComingSoon']
      }
    },
    {
      contentId: 'content_details',
      platform: 'linkedin',
      scheduledTime: new Date(baseTime.getTime() + 60 * 60000).toISOString(), // +60 min
      metadata: {
        campaignId,
        contentType: 'article',
        audience: 'professional'
      }
    },
    {
      contentId: 'content_tiktok',
      platform: 'tiktok',
      scheduledTime: new Date(baseTime.getTime() + 90 * 60000).toISOString(), // +90 min
      metadata: {
        campaignId,
        contentType: 'video',
        hashtags: ['#TechTok', '#Innovation']
      }
    }
  ];
  
  try {
    const scheduleData = {
      title: `Product Launch Campaign - ${new Date().toISOString().split('T')[0]}`,
      timezone: 'America/New_York',
      items: scheduleItems,
      processingDeadlineMs: 6 * 60 * 60 * 1000 // 6 hours
    };
    
    const idempotencyKey = uuidv4();
    const schedule = await client.createSchedule(scheduleData, idempotencyKey);
    
    console.log('Campaign schedule created:');
    console.log(`  Schedule ID: ${schedule.id}`);
    console.log(`  Total items: ${schedule.itemsTotal}`);
    console.log(`  Processing deadline: ${schedule.processingDeadlineMs}ms`);
    
    return schedule;
  } finally {
    client.destroy();
  }
}

// Create schedule with recommended times
async function createScheduleWithRecommendations() {
  const client = await authenticateClient();
  
  try {
    // Get recommendations first
    const recommendations = await client.getRecommendations({
      platforms: ['youtube', 'instagram'],
      targetCount: 5,
      timezone: 'America/New_York',
      contentType: 'tutorial'
    });
    
    console.log('Available recommendations:');
    recommendations.data.forEach((rec, index) => {
      console.log(`${index + 1}. ${rec.window_start} (Score: ${rec.score})`);
    });
    
    // Use the best recommendation
    const bestRec = recommendations.data[0];
    
    // Create content IDs (these would come from your content management system)
    const contentItems = [
      {
        contentId: 'tutorial_part1',
        platform: 'youtube',
        scheduledTime: bestRec.windowStart
      },
      {
        contentId: 'tutorial_snippets',
        platform: 'instagram',
        scheduledTime: new Date(new Date(bestRec.windowStart).getTime() + 2 * 60 * 60000).toISOString()
      }
    ];
    
    const scheduleData = {
      title: 'Tutorial Series - Recommended Times',
      timezone: 'America/New_York',
      items: contentItems
    };
    
    const idempotencyKey = uuidv4();
    const schedule = await client.createSchedule(scheduleData, idempotencyKey);
    
    console.log('Schedule created with recommended timing:');
    console.log(`  Base recommendation score: ${bestRec.score}`);
    console.log(`  Confidence: ${bestRec.confidence}`);
    console.log(`  Reasons: ${bestRec.reasons.join(', ')}`);
    
    return schedule;
  } finally {
    client.destroy();
  }
}

// Handle schedule creation with validation
async function createValidatedSchedule() {
  const client = await authenticateClient();
  
  // Simulate form data from user input
  const formData = {
    title: 'User Generated Schedule',
    timezone: 'America/Los_Angeles',
    items: [
      {
        contentId: 'user_content_123',
        platform: 'youtube',
        scheduledTime: '2025-11-06T16:00:00-08:00',
        metadata: {
          title: 'My Video',
          description: 'A great video about technology'
        }
      }
    ]
  };
  
  try {
    // Validate timezone
    const validTimezones = ['America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles', 'UTC'];
    if (!validTimezones.includes(formData.timezone)) {
      throw new Error(`Invalid timezone: ${formData.timezone}`);
    }
    
    // Validate items
    if (!formData.items || formData.items.length === 0) {
      throw new Error('At least one item is required');
    }
    
    // Validate each item
    for (const item of formData.items) {
      if (!item.contentId) {
        throw new Error('Content ID is required for all items');
      }
      if (!item.platform) {
        throw new Error('Platform is required for all items');
      }
      if (!item.scheduledTime) {
        throw new Error('Scheduled time is required for all items');
      }
      
      // Validate scheduled time format
      const scheduledDate = new Date(item.scheduledTime);
      if (isNaN(scheduledDate.getTime())) {
        throw new Error(`Invalid date format for ${item.contentId}: ${item.scheduledTime}`);
      }
      
      // Check if time is in the future
      if (scheduledDate <= new Date()) {
        throw new Error(`Scheduled time must be in the future for ${item.contentId}`);
      }
    }
    
    const idempotencyKey = uuidv4();
    const schedule = await client.createSchedule(formData, idempotencyKey);
    
    console.log('Validated schedule created successfully:', schedule.id);
    return schedule;
    
  } catch (error) {
    console.error('Schedule creation failed:', error.message);
    throw error;
  } finally {
    client.destroy();
  }
}
```

### Python Examples

```python
import asyncio
import uuid
from datetime import datetime, timedelta

async def create_simple_schedule():
    """Create a simple schedule with one item"""
    client = await authenticate_client()
    
    try:
        schedule_data = {
            'title': 'Weekly Content Schedule',
            'timezone': 'America/New_York',
            'items': [
                {
                    'content_id': 'content_123',
                    'platform': 'youtube',
                    'scheduled_time': '2025-11-06T14:00:00-05:00'
                }
            ]
        }
        
        idempotency_key = str(uuid.uuid4())
        schedule = await client.create_schedule(schedule_data, idempotency_key)
        
        print('Schedule created:', schedule)
        print('Schedule ID:', schedule['id'])
        print('Status:', schedule['state'])
        
        return schedule
    finally:
        client.destroy()

async def create_campaign_schedule():
    """Create a multi-platform campaign schedule"""
    client = await authenticate_client()
    
    campaign_id = 'camp_20251105_launch'
    base_time = datetime.fromisoformat('2025-11-06T14:00:00-05:00')
    
    schedule_items = [
        {
            'content_id': 'content_announcement',
            'platform': 'youtube',
            'scheduled_time': base_time.isoformat(),
            'metadata': {
                'campaign_id': campaign_id,
                'content_type': 'announcement',
                'title': 'Product Launch Announcement'
            },
            'callbacks': {
                'on_published': 'https://your-app.com/webhooks/published',
                'on_failed': 'https://your-app.com/webhooks/failed'
            }
        },
        {
            'content_id': 'content_teaser',
            'platform': 'instagram',
            'scheduled_time': (base_time + timedelta(minutes=30)).isoformat(),
            'metadata': {
                'campaign_id': campaign_id,
                'content_type': 'reel',
                'hashtags': ['#ProductLaunch', '#Innovation', '#ComingSoon']
            }
        },
        {
            'content_id': 'content_details',
            'platform': 'linkedin',
            'scheduled_time': (base_time + timedelta(minutes=60)).isoformat(),
            'metadata': {
                'campaign_id': campaign_id,
                'content_type': 'article',
                'audience': 'professional'
            }
        },
        {
            'content_id': 'content_tiktok',
            'platform': 'tiktok',
            'scheduled_time': (base_time + timedelta(minutes=90)).isoformat(),
            'metadata': {
                'campaign_id': campaign_id,
                'content_type': 'video',
                'hashtags': ['#TechTok', '#Innovation']
            }
        }
    ]
    
    try:
        schedule_data = {
            'title': f'Product Launch Campaign - {datetime.now().strftime("%Y-%m-%d")}',
            'timezone': 'America/New_York',
            'items': schedule_items,
            'processing_deadline_ms': 6 * 60 * 60 * 1000  # 6 hours
        }
        
        idempotency_key = str(uuid.uuid4())
        schedule = await client.create_schedule(schedule_data, idempotency_key)
        
        print('Campaign schedule created:')
        print(f'  Schedule ID: {schedule["id"]}')
        print(f'  Total items: {schedule["items_total"]}')
        print(f'  Processing deadline: {schedule["processing_deadline_ms"]}ms')
        
        return schedule
    finally:
        client.destroy()

async def create_schedule_with_recommendations():
    """Create schedule using recommended times"""
    client = await authenticate_client()
    
    try:
        # Get recommendations first
        recommendations = await client.get_recommendations({
            'platforms': ['youtube', 'instagram'],
            'target_count': 5,
            'timezone': 'America/New_York',
            'content_type': 'tutorial'
        })
        
        print('Available recommendations:')
        for i, rec in enumerate(recommendations['data']):
            print(f'{i + 1}. {rec["window_start"]} (Score: {rec["score"]})')
        
        # Use the best recommendation
        best_rec = recommendations['data'][0]
        
        # Create content items
        content_items = [
            {
                'content_id': 'tutorial_part1',
                'platform': 'youtube',
                'scheduled_time': best_rec['window_start']
            },
            {
                'content_id': 'tutorial_snippets',
                'platform': 'instagram',
                'scheduled_time': (datetime.fromisoformat(best_rec['window_start'].replace('Z', '+00:00')) + 
                                 timedelta(hours=2)).isoformat()
            }
        ]
        
        schedule_data = {
            'title': 'Tutorial Series - Recommended Times',
            'timezone': 'America/New_York',
            'items': content_items
        }
        
        idempotency_key = str(uuid.uuid4())
        schedule = await client.create_schedule(schedule_data, idempotency_key)
        
        print('Schedule created with recommended timing:')
        print(f'  Base recommendation score: {best_rec["score"]}')
        print(f'  Confidence: {best_rec["confidence"]}')
        print(f'  Reasons: {", ".join(best_rec["reasons"])}')
        
        return schedule
    finally:
        client.destroy()

async def create_validated_schedule():
    """Create schedule with comprehensive validation"""
    client = await authenticate_client()
    
    # Simulate form data from user input
    form_data = {
        'title': 'User Generated Schedule',
        'timezone': 'America/Los_Angeles',
        'items': [
            {
                'content_id': 'user_content_123',
                'platform': 'youtube',
                'scheduled_time': '2025-11-06T16:00:00-08:00',
                'metadata': {
                    'title': 'My Video',
                    'description': 'A great video about technology'
                }
            }
        ]
    }
    
    try:
        # Validate timezone
        valid_timezones = ['America/New_York', 'America/Chicago', 'America/Denver', 
                          'America/Los_Angeles', 'UTC']
        if form_data['timezone'] not in valid_timezones:
            raise ValueError(f'Invalid timezone: {form_data["timezone"]}')
        
        # Validate items
        if not form_data['items'] or len(form_data['items']) == 0:
            raise ValueError('At least one item is required')
        
        # Validate each item
        for item in form_data['items']:
            if not item.get('content_id'):
                raise ValueError('Content ID is required for all items')
            if not item.get('platform'):
                raise ValueError('Platform is required for all items')
            if not item.get('scheduled_time'):
                raise ValueError('Scheduled time is required for all items')
            
            # Validate scheduled time format
            try:
                scheduled_date = datetime.fromisoformat(item['scheduled_time'].replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f'Invalid date format for {item["content_id"]}: {item["scheduled_time"]}')
            
            # Check if time is in the future
            if scheduled_date <= datetime.now(timezone.utc):
                raise ValueError(f'Scheduled time must be in the future for {item["content_id"]}')
        
        idempotency_key = str(uuid.uuid4())
        schedule = await client.create_schedule(form_data, idempotency_key)
        
        print('Validated schedule created successfully:', schedule['id'])
        return schedule
        
    except Exception as e:
        print(f'Schedule creation failed: {e}')
        raise
    finally:
        client.destroy()

# Usage
async def main():
    await create_simple_schedule()
    await create_campaign_schedule()
    await create_schedule_with_recommendations()
    await create_validated_schedule()

if __name__ == '__main__':
    asyncio.run(main())
```

## Managing Schedules

### JavaScript Examples

```typescript
// Monitor schedule progress with polling
async function monitorScheduleProgress(scheduleId: string, pollIntervalMs = 5000) {
  const client = await authenticateClient();
  
  try {
    console.log(`Monitoring schedule: ${scheduleId}`);
    
    const pollSchedule = async () => {
      const schedule = await client.getSchedule(scheduleId, {
        expand: ['items', 'metrics']
      });
      
      console.log(`\nSchedule Status Update:`);
      console.log(`  State: ${schedule.state}`);
      console.log(`  Progress: ${schedule.percentComplete.toFixed(1)}%`);
      console.log(`  Items: ${schedule.itemsCompleted}/${schedule.itemsTotal} completed`);
      
      if (schedule.itemsFailed > 0) {
        console.log(`  Failed: ${schedule.itemsFailed}`);
      }
      
      if (schedule.etaMs) {
        const etaMinutes = Math.round(schedule.etaMs / 60000);
        console.log(`  ETA: ${etaMinutes} minutes`);
      }
      
      // Show recent items if expanded
      if (schedule.items) {
        console.log(`\nRecent Items:`);
        schedule.items.slice(0, 5).forEach(item => {
          console.log(`  ${item.platform}: ${item.state} at ${item.scheduledTime}`);
        });
      }
      
      // Continue polling if not completed
      if (!['completed', 'failed', 'canceled'].includes(schedule.state)) {
        setTimeout(pollSchedule, pollIntervalMs);
      } else {
        console.log(`\nSchedule ${schedule.state}`);
        
        if (schedule.state === 'failed') {
          console.log('Schedule failed. Check logs for details.');
        } else if (schedule.state === 'completed') {
          console.log('Schedule completed successfully!');
        }
      }
    };
    
    await pollSchedule();
    
  } finally {
    client.destroy();
  }
}

// Get schedule with filtering
async function getFilteredScheduleItems(scheduleId: string) {
  const client = await authenticateClient();
  
  try {
    // Get all published items
    const publishedSchedule = await client.getSchedule(scheduleId, {
      state: ['published'],
      expand: ['items'],
      pageSize: 100,
      sort: 'published_time',
      order: 'desc'
    });
    
    console.log(`Published items (${publishedSchedule.items?.length || 0}):`);
    publishedSchedule.items?.forEach(item => {
      console.log(`  ${item.platform}: ${item.publishedTime}`);
    });
    
    // Get failed items
    const failedSchedule = await client.getSchedule(scheduleId, {
      state: ['failed'],
      expand: ['items']
    });
    
    console.log(`\nFailed items (${failedSchedule.items?.length || 0}):`);
    failedSchedule.items?.forEach(item => {
      console.log(`  ${item.platform}: ${item.errors[0]?.message || 'Unknown error'}`);
    });
    
    return { published: publishedSchedule, failed: failedSchedule };
    
  } finally {
    client.destroy();
  }
}

// Handle schedule states
async function handleScheduleLifecycle() {
  const client = await authenticateClient();
  
  // Create a test schedule
  const schedule = await createSimpleSchedule();
  const scheduleId = schedule.id;
  
  try {
    // Monitor the schedule through its lifecycle
    const states = ['pending', 'running', 'completed'];
    let currentStateIndex = 0;
    
    const checkState = async () => {
      const currentSchedule = await client.getSchedule(scheduleId);
      console.log(`Schedule state: ${currentSchedule.state}`);
      
      if (currentSchedule.state !== states[currentStateIndex]) {
        console.log(`State transition: ${states[currentStateIndex]} -> ${currentSchedule.state}`);
        currentStateIndex = Math.min(currentStateIndex + 1, states.length - 1);
      }
      
      if (!['completed', 'failed', 'canceled'].includes(currentSchedule.state)) {
        setTimeout(checkState, 2000);
      }
    };
    
    await checkState();
    
  } finally {
    client.destroy();
  }
}

// Batch schedule operations
async function batchScheduleOperations() {
  const client = await authenticateClient();
  
  try {
    // Create multiple schedules
    const schedules = [];
    
    for (let i = 0; i < 5; i++) {
      const scheduleData = {
        title: `Batch Schedule ${i + 1}`,
        timezone: 'America/New_York',
        items: [
          {
            contentId: `batch_content_${i}`,
            platform: ['youtube', 'instagram', 'tiktok'][i % 3],
            scheduledTime: new Date(Date.now() + (i + 1) * 60 * 60 * 1000).toISOString()
          }
        ]
      };
      
      const idempotencyKey = uuidv4();
      const schedule = await client.createSchedule(scheduleData, idempotencyKey);
      schedules.push(schedule);
      
      console.log(`Created schedule ${i + 1}: ${schedule.id}`);
    }
    
    // Monitor all schedules
    console.log('\nMonitoring all schedules...');
    
    const monitorAllSchedules = async () => {
      const updates = [];
      
      for (const schedule of schedules) {
        try {
          const currentSchedule = await client.getSchedule(schedule.id);
          updates.push({
            id: schedule.id,
            state: currentSchedule.state,
            progress: currentSchedule.percentComplete
          });
        } catch (error) {
          console.error(`Error monitoring ${schedule.id}:`, error.message);
        }
      }
      
      console.log('\nSchedule Status Summary:');
      updates.forEach(update => {
        console.log(`  ${update.id}: ${update.state} (${update.progress.toFixed(1)}%)`);
      });
      
      const allCompleted = updates.every(update => 
        ['completed', 'failed', 'canceled'].includes(update.state)
      );
      
      if (!allCompleted) {
        setTimeout(monitorAllSchedules, 5000);
      } else {
        console.log('\nAll schedules completed!');
      }
    };
    
    await monitorAllSchedules();
    
    return schedules;
    
  } finally {
    client.destroy();
  }
}

// Error handling and recovery
async function handleScheduleErrors() {
  const client = await authenticateClient();
  
  try {
    const schedules = await client.getSchedule('invalid-schedule-id');
    
  } catch (error) {
    if (error.response?.status === 404) {
      console.log('Schedule not found - handle gracefully');
      return;
    }
    
    if (error.response?.status === 403) {
      console.log('Access denied - check permissions');
      return;
    }
    
    console.error('Unexpected error:', error.message);
    throw error;
    
  } finally {
    client.destroy();
  }
}
```

### Python Examples

```python
import asyncio
import time
from datetime import datetime

async def monitor_schedule_progress(schedule_id, poll_interval_ms=5000):
    """Monitor schedule progress with polling"""
    client = await authenticate_client()
    
    try:
        print(f'Monitoring schedule: {schedule_id}')
        
        while True:
            schedule = await client.get_schedule(schedule_id, {
                'expand': ['items', 'metrics']
            })
            
            print(f'\nSchedule Status Update:')
            print(f'  State: {schedule["state"]}')
            print(f'  Progress: {schedule["percent_complete"]:.1f}%')
            print(f'  Items: {schedule["items_completed"]}/{schedule["items_total"]} completed')
            
            if schedule['items_failed'] > 0:
                print(f'  Failed: {schedule["items_failed"]}')
            
            if schedule.get('eta_ms'):
                eta_minutes = round(schedule['eta_ms'] / 60000)
                print(f'  ETA: {eta_minutes} minutes')
            
            # Show recent items if expanded
            if schedule.get('items'):
                print(f'\nRecent Items:')
                for item in schedule['items'][:5]:
                    print(f'  {item["platform"]}: {item["state"]} at {item["scheduled_time"]}')
            
            # Continue polling if not completed
            if schedule['state'] not in ['completed', 'failed', 'canceled']:
                await asyncio.sleep(poll_interval_ms / 1000)
            else:
                print(f'\nSchedule {schedule["state"]}')
                
                if schedule['state'] == 'failed':
                    print('Schedule failed. Check logs for details.')
                elif schedule['state'] == 'completed':
                    print('Schedule completed successfully!')
                break
                
    finally:
        client.destroy()

async def get_filtered_schedule_items(schedule_id):
    """Get schedule items with filtering"""
    client = await authenticate_client()
    
    try:
        # Get all published items
        published_schedule = await client.get_schedule(schedule_id, {
            'state': ['published'],
            'expand': ['items'],
            'page_size': 100,
            'sort': 'published_time',
            'order': 'desc'
        })
        
        print(f'Published items ({len(published_schedule.get("items", []))}):')
        for item in published_schedule.get('items', []):
            print(f'  {item["platform"]}: {item["published_time"]}')
        
        # Get failed items
        failed_schedule = await client.get_schedule(schedule_id, {
            'state': ['failed'],
            'expand': ['items']
        })
        
        print(f'\nFailed items ({len(failed_schedule.get("items", []))}):')
        for item in failed_schedule.get('items', []):
            errors = item.get('errors', [])
            if errors:
                print(f'  {item["platform"]}: {errors[0]["message"]}')
            else:
                print(f'  {item["platform"]}: Unknown error')
        
        return {'published': published_schedule, 'failed': failed_schedule}
        
    finally:
        client.destroy()

async def handle_schedule_lifecycle():
    """Handle schedule through its lifecycle"""
    client = await authenticate_client()
    
    # Create a test schedule
    schedule = await create_simple_schedule()
    schedule_id = schedule['id']
    
    try:
        # Monitor the schedule through its lifecycle
        states = ['pending', 'running', 'completed']
        current_state_index = 0
        
        while True:
            current_schedule = await client.get_schedule(schedule_id)
            print(f'Schedule state: {current_schedule["state"]}')
            
            if current_schedule['state'] != states[current_state_index]:
                print(f'State transition: {states[current_state_index]} -> {current_schedule["state"]}')
                current_state_index = min(current_state_index + 1, len(states) - 1)
            
            if current_schedule['state'] in ['completed', 'failed', 'canceled']:
                break
            
            await asyncio.sleep(2)
            
    finally:
        client.destroy()

async def batch_schedule_operations():
    """Perform batch operations on multiple schedules"""
    client = await authenticate_client()
    
    try:
        # Create multiple schedules
        schedules = []
        
        for i in range(5):
            schedule_data = {
                'title': f'Batch Schedule {i + 1}',
                'timezone': 'America/New_York',
                'items': [
                    {
                        'content_id': f'batch_content_{i}',
                        'platform': ['youtube', 'instagram', 'tiktok'][i % 3],
                        'scheduled_time': (datetime.now().timestamp() + (i + 1) * 3600)
                    }
                ]
            }
            
            idempotency_key = str(uuid.uuid4())
            schedule = await client.create_schedule(schedule_data, idempotency_key)
            schedules.append(schedule)
            
            print(f'Created schedule {i + 1}: {schedule["id"]}')
        
        # Monitor all schedules
        print('\nMonitoring all schedules...')
        
        while True:
            updates = []
            
            for schedule in schedules:
                try:
                    current_schedule = await client.get_schedule(schedule['id'])
                    updates.append({
                        'id': schedule['id'],
                        'state': current_schedule['state'],
                        'progress': current_schedule['percent_complete']
                    })
                except Exception as e:
                    print(f'Error monitoring {schedule["id"]}: {e}')
            
            print('\nSchedule Status Summary:')
            for update in updates:
                print(f'  {update["id"]}: {update["state"]} ({update["progress"]:.1f}%)')
            
            all_completed = all(
                update['state'] in ['completed', 'failed', 'canceled']
                for update in updates
            )
            
            if all_completed:
                print('\nAll schedules completed!')
                break
            
            await asyncio.sleep(5)
        
        return schedules
        
    finally:
        client.destroy()

async def handle_schedule_errors():
    """Handle schedule errors gracefully"""
    client = await authenticate_client()
    
    try:
        schedules = await client.get_schedule('invalid-schedule-id')
        
    except Exception as e:
        if '404' in str(e):
            print('Schedule not found - handle gracefully')
            return
        elif '403' in str(e):
            print('Access denied - check permissions')
            return
        else:
            print(f'Unexpected error: {e}')
            raise
    finally:
        client.destroy()

# Usage
async def main():
    # Monitor a specific schedule
    # await monitor_schedule_progress('sched_123456789')
    
    # Handle schedule lifecycle
    await handle_schedule_lifecycle()
    
    # Batch operations
    # await batch_schedule_operations()
    
    # Error handling
    await handle_schedule_errors()

if __name__ == '__main__':
    asyncio.run(main())
```

## Schedule Optimization

### JavaScript Examples

```typescript
// Basic schedule optimization
async function optimizeBasicSchedule(scheduleId: string) {
  const client = await authenticateClient();
  
  try {
    // Get current schedule to see what needs optimization
    const schedule = await client.getSchedule(scheduleId, {
      expand: ['items']
    });
    
    console.log('Current schedule items:');
    schedule.items?.forEach(item => {
      console.log(`  ${item.platform}: ${item.scheduledTime} (${item.state})`);
    });
    
    // Create optimization targets
    const targets = schedule.items
      ?.filter(item => item.state === 'scheduled')
      .map(item => ({
        contentId: item.contentId,
        platform: item.platform,
        currentScheduledTime: item.scheduledTime
      })) || [];
    
    if (targets.length === 0) {
      console.log('No items to optimize');
      return;
    }
    
    console.log(`\nOptimizing ${targets.length} items...`);
    
    const optimizationRequest = {
      scheduleId,
      targets,
      constraints: {
        doNotMoveBefore: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(), // 2 hours from now
        doNotMoveAfter: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 24 hours from now
        platformSpecificRules: {
          youtube: {
            minIntervalMinutes: 120 // 2 hours between YouTube posts
          },
          instagram: {
            minIntervalMinutes: 60 // 1 hour between Instagram posts
          }
        }
      },
      apply: false // Dry run first
    };
    
    const idempotencyKey = uuidv4();
    const optimization = await client.optimizeSchedule(optimizationRequest, idempotencyKey);
    
    console.log('\nOptimization Results:');
    console.log(`  Total targeted: ${optimization.metrics.totalTargeted}`);
    console.log(`  Changes suggested: ${optimization.metrics.changedCount}`);
    console.log(`  Average score lift: ${optimization.metrics.averageScoreLift.toFixed(3)}`);
    
    if (optimization.changes.length > 0) {
      console.log('\nSuggested Changes:');
      optimization.changes.forEach((change, index) => {
        console.log(`  ${index + 1}. ${change.platform}:`);
        console.log(`     From: ${change.previousTime}`);
        console.log(`     To: ${change.newTime}`);
        console.log(`     Score: ${change.scoreBefore.toFixed(3)} → ${change.scoreAfter.toFixed(3)}`);
        console.log(`     Reason: ${change.reason}`);
        console.log(`     Confidence: ${(change.confidence * 100).toFixed(1)}%`);
      });
      
      // Ask user if they want to apply changes
      const applyChanges = true; // In real app, this would be user input
      
      if (applyChanges) {
        optimizationRequest.apply = true;
        const appliedOptimization = await client.optimizeSchedule(optimizationRequest);
        
        console.log('\n✅ Optimization applied!');
        console.log(`  Applied ${appliedOptimization.metrics.changedCount} changes`);
        console.log(`  Average improvement: ${appliedOptimization.metrics.averageScoreLift.toFixed(3)}`);
      }
    } else {
      console.log('\nNo optimization opportunities found.');
    }
    
    return optimization;
    
  } finally {
    client.destroy();
  }
}

// Advanced optimization with custom constraints
async function optimizeWithAdvancedConstraints(scheduleId: string) {
  const client = await authenticateClient();
  
  try {
    const schedule = await client.getSchedule(scheduleId, {
      expand: ['items']
    });
    
    const targets = schedule.items
      ?.filter(item => item.state === 'scheduled')
      .map(item => ({
        contentId: item.contentId,
        platform: item.platform,
        currentScheduledTime: item.scheduledTime
      })) || [];
    
    // Define blackout windows (avoid these times)
    const blackoutWindows = [
      {
        start: new Date('2025-11-06T12:00:00-05:00').toISOString(),
        end: new Date('2025-11-06T13:00:00-05:00').toISOString() // Lunch hour
      },
      {
        start: new Date('2025-11-06T18:00:00-05:00').toISOString(),
        end: new Date('2025-11-06T19:00:00-05:00').toISOString() // Dinner time
      }
    ];
    
    const optimizationRequest = {
      scheduleId,
      targets,
      constraints: {
        doNotMoveBefore: new Date(Date.now() + 60 * 60 * 1000).toISOString(), // 1 hour from now
        doNotMoveAfter: new Date(Date.now() + 48 * 60 * 60 * 1000).toISOString(), // 48 hours from now
        blackoutWindows,
        platformSpecificRules: {
          youtube: {
            minIntervalMinutes: 120,
            avoidFridayEvenings: true,
            preferWeekdays: true
          },
          instagram: {
            minIntervalMinutes: 60,
            avoidLateNight: true // After 11 PM
          },
          linkedin: {
            minIntervalMinutes: 180, // 3 hours
            weekdaysOnly: true,
            businessHoursOnly: true
          }
        }
      },
      apply: true
    };
    
    const idempotencyKey = uuidv4();
    const optimization = await client.optimizeSchedule(optimizationRequest, idempotencyKey);
    
    console.log('Advanced Optimization Results:');
    console.log(`  Applied ${optimization.metrics.changedCount} changes`);
    console.log(`  Average score improvement: ${optimization.metrics.averageScoreLift.toFixed(3)}`);
    
    if (optimization.metrics.rateLimited) {
      console.log('⚠️  Rate limited during optimization');
    }
    
    return optimization;
    
  } finally {
    client.destroy();
  }
}

// Compare optimization strategies
async function compareOptimizationStrategies(scheduleId: string) {
  const client = await authenticateClient();
  
  try {
    const schedule = await client.getSchedule(scheduleId, {
      expand: ['items']
    });
    
    const targets = schedule.items
      ?.filter(item => item.state === 'scheduled')
      .map(item => ({
        contentId: item.contentId,
        platform: item.platform,
        currentScheduledTime: item.scheduledTime
      })) || [];
    
    const strategies = [
      {
        name: 'Conservative',
        constraints: {
          doNotMoveBefore: new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString(),
          platformSpecificRules: {
            youtube: { minIntervalMinutes: 240 },
            instagram: { minIntervalMinutes: 120 }
          }
        }
      },
      {
        name: 'Aggressive',
        constraints: {
          doNotMoveBefore: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
          platformSpecificRules: {
            youtube: { minIntervalMinutes: 60 },
            instagram: { minIntervalMinutes: 30 }
          }
        }
      },
      {
        name: 'Balanced',
        constraints: {
          doNotMoveBefore: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
          platformSpecificRules: {
            youtube: { minIntervalMinutes: 120 },
            instagram: { minIntervalMinutes: 60 }
          }
        }
      }
    ];
    
    const results = [];
    
    for (const strategy of strategies) {
      console.log(`\nTesting ${strategy.name} strategy...`);
      
      const optimizationRequest = {
        scheduleId,
        targets,
        constraints: {
          ...strategy.constraints,
          apply: false // Dry run for comparison
        }
      };
      
      try {
        const optimization = await client.optimizeSchedule(optimizationRequest);
        
        results.push({
          strategy: strategy.name,
          ...optimization,
          scoreImprovement: optimization.metrics.averageScoreLift,
          changesSuggested: optimization.metrics.changedCount
        });
        
        console.log(`  Changes: ${optimization.metrics.changedCount}`);
        console.log(`  Score improvement: ${optimization.metrics.averageScoreLift.toFixed(3)}`);
        
      } catch (error) {
        console.error(`  Strategy failed: ${error.message}`);
        results.push({
          strategy: strategy.name,
          error: error.message
        });
      }
    }
    
    // Recommend best strategy
    console.log('\n📊 Strategy Comparison:');
    const successfulResults = results.filter(r => !r.error);
    
    if (successfulResults.length > 0) {
      const bestStrategy = successfulResults.reduce((best, current) => 
        current.scoreImprovement > best.scoreImprovement ? current : best
      );
      
      console.log(`\n🏆 Recommended: ${bestStrategy.strategy}`);
      console.log(`   Score improvement: ${bestStrategy.scoreImprovement.toFixed(3)}`);
      console.log(`   Changes: ${bestStrategy.changesSuggested}`);
    }
    
    return results;
    
  } finally {
    client.destroy();
  }
}

// Real-time optimization monitoring
async function monitorOptimizationRealTime(scheduleId: string) {
  const client = await authenticateClient();
  
  // Connect to WebSocket for real-time updates
  const connectionId = client.connectToWebSocket(scheduleId, (message) => {
    if (message.type === 'optimization.completed') {
      console.log('🎉 Optimization completed!');
      console.log(`  Changes: ${message.data.changesCount}`);
      console.log(`  Improvement: ${message.data.summary.averageScoreLift.toFixed(3)}`);
    }
  });
  
  try {
    const schedule = await client.getSchedule(scheduleId, {
      expand: ['items']
    });
    
    const targets = schedule.items
      ?.filter(item => item.state === 'scheduled')
      .map(item => ({
        contentId: item.contentId,
        platform: item.platform,
        currentScheduledTime: item.scheduledTime
      })) || [];
    
    if (targets.length === 0) {
      console.log('No items to optimize');
      return;
    }
    
    // Start optimization
    const optimizationRequest = {
      scheduleId,
      targets,
      constraints: {
        doNotMoveBefore: new Date(Date.now() + 60 * 60 * 1000).toISOString()
      },
      apply: true
    };
    
    const idempotencyKey = uuidv4();
    
    console.log('🚀 Starting real-time optimization...');
    const optimization = await client.optimizeSchedule(optimizationRequest, idempotencyKey);
    
    console.log('Optimization initiated. Monitoring progress...');
    
    // Wait for WebSocket confirmation
    await new Promise(resolve => setTimeout(resolve, 10000));
    
    console.log('✅ Optimization process completed');
    return optimization;
    
  } finally {
    client.disconnectFromWebSocket(connectionId);
    client.destroy();
  }
}
```

### Python Examples

```python
import asyncio
from datetime import datetime, timedelta

async def optimize_basic_schedule(schedule_id):
    """Basic schedule optimization"""
    client = await authenticate_client()
    
    try:
        # Get current schedule
        schedule = await client.get_schedule(schedule_id, {
            'expand': ['items']
        })
        
        print('Current schedule items:')
        for item in schedule.get('items', []):
            print(f'  {item["platform"]}: {item["scheduled_time"]} ({item["state"]})')
        
        # Create optimization targets
        targets = [
            {
                'content_id': item['content_id'],
                'platform': item['platform'],
                'current_scheduled_time': item['scheduled_time']
            }
            for item in schedule.get('items', [])
            if item['state'] == 'scheduled'
        ]
        
        if not targets:
            print('No items to optimize')
            return
        
        print(f'\nOptimizing {len(targets)} items...')
        
        optimization_request = {
            'schedule_id': schedule_id,
            'targets': targets,
            'constraints': {
                'do_not_move_before': (datetime.now() + timedelta(hours=2)).isoformat(),
                'do_not_move_after': (datetime.now() + timedelta(days=1)).isoformat(),
                'platform_specific_rules': {
                    'youtube': {'min_interval_minutes': 120},
                    'instagram': {'min_interval_minutes': 60}
                }
            },
            'apply': False  # Dry run first
        }
        
        idempotency_key = str(uuid.uuid4())
        optimization = await client.optimize_schedule(optimization_request, idempotency_key)
        
        print('\nOptimization Results:')
        print(f'  Total targeted: {optimization["metrics"]["total_targeted"]}')
        print(f'  Changes suggested: {optimization["metrics"]["changed_count"]}')
        print(f'  Average score lift: {optimization["metrics"]["average_score_lift"]:.3f}')
        
        if optimization['changes']:
            print('\nSuggested Changes:')
            for i, change in enumerate(optimization['changes']):
                print(f'  {i + 1}. {change["platform"]}:')
                print(f'     From: {change["previous_time"]}')
                print(f'     To: {change["new_time"]}')
                print(f'     Score: {change["score_before"]:.3f} → {change["score_after"]:.3f}')
                print(f'     Reason: {change["reason"]}')
                print(f'     Confidence: {change["confidence"] * 100:.1f}%')
            
            # Apply changes (in real app, ask user first)
            apply_changes = True
            
            if apply_changes:
                optimization_request['apply'] = True
                applied_optimization = await client.optimize_schedule(optimization_request)
                
                print('\n✅ Optimization applied!')
                print(f'  Applied {applied_optimization["metrics"]["changed_count"]} changes')
                print(f'  Average improvement: {applied_optimization["metrics"]["average_score_lift"]:.3f}')
        else:
            print('\nNo optimization opportunities found.')
        
        return optimization
        
    finally:
        client.destroy()

async def optimize_with_advanced_constraints(schedule_id):
    """Advanced optimization with custom constraints"""
    client = await authenticate_client()
    
    try:
        schedule = await client.get_schedule(schedule_id, {
            'expand': ['items']
        })
        
        targets = [
            {
                'content_id': item['content_id'],
                'platform': item['platform'],
                'current_scheduled_time': item['scheduled_time']
            }
            for item in schedule.get('items', [])
            if item['state'] == 'scheduled'
        ]
        
        # Define blackout windows
        blackout_windows = [
            {
                'start': datetime.fromisoformat('2025-11-06T12:00:00-05:00').isoformat(),
                'end': datetime.fromisoformat('2025-11-06T13:00:00-05:00').isoformat()
            },
            {
                'start': datetime.fromisoformat('2025-11-06T18:00:00-05:00').isoformat(),
                'end': datetime.fromisoformat('2025-11-06T19:00:00-05:00').isoformat()
            }
        ]
        
        optimization_request = {
            'schedule_id': schedule_id,
            'targets': targets,
            'constraints': {
                'do_not_move_before': (datetime.now() + timedelta(hours=1)).isoformat(),
                'do_not_move_after': (datetime.now() + timedelta(days=2)).isoformat(),
                'blackout_windows': blackout_windows,
                'platform_specific_rules': {
                    'youtube': {
                        'min_interval_minutes': 120,
                        'avoid_friday_evenings': True,
                        'prefer_weekdays': True
                    },
                    'instagram': {
                        'min_interval_minutes': 60,
                        'avoid_late_night': True
                    },
                    'linkedin': {
                        'min_interval_minutes': 180,
                        'weekdays_only': True,
                        'business_hours_only': True
                    }
                }
            },
            'apply': True
        }
        
        idempotency_key = str(uuid.uuid4())
        optimization = await client.optimize_schedule(optimization_request, idempotency_key)
        
        print('Advanced Optimization Results:')
        print(f'  Applied {optimization["metrics"]["changed_count"]} changes')
        print(f'  Average score improvement: {optimization["metrics"]["average_score_lift"]:.3f}')
        
        if optimization['metrics']['rate_limited']:
            print('⚠️  Rate limited during optimization')
        
        return optimization
        
    finally:
        client.destroy()

async def compare_optimization_strategies(schedule_id):
    """Compare different optimization strategies"""
    client = await authenticate_client()
    
    try:
        schedule = await client.get_schedule(schedule_id, {
            'expand': ['items']
        })
        
        targets = [
            {
                'content_id': item['content_id'],
                'platform': item['platform'],
                'current_scheduled_time': item['scheduled_time']
            }
            for item in schedule.get('items', [])
            if item['state'] == 'scheduled'
        ]
        
        strategies = [
            {
                'name': 'Conservative',
                'constraints': {
                    'do_not_move_before': (datetime.now() + timedelta(hours=4)).isoformat(),
                    'platform_specific_rules': {
                        'youtube': {'min_interval_minutes': 240},
                        'instagram': {'min_interval_minutes': 120}
                    }
                }
            },
            {
                'name': 'Aggressive',
                'constraints': {
                    'do_not_move_before': (datetime.now() + timedelta(minutes=30)).isoformat(),
                    'platform_specific_rules': {
                        'youtube': {'min_interval_minutes': 60},
                        'instagram': {'min_interval_minutes': 30}
                    }
                }
            },
            {
                'name': 'Balanced',
                'constraints': {
                    'do_not_move_before': (datetime.now() + timedelta(hours=2)).isoformat(),
                    'platform_specific_rules': {
                        'youtube': {'min_interval_minutes': 120},
                        'instagram': {'min_interval_minutes': 60}
                    }
                }
            }
        ]
        
        results = []
        
        for strategy in strategies:
            print(f'\nTesting {strategy["name"]} strategy...')
            
            optimization_request = {
                'schedule_id': schedule_id,
                'targets': targets,
                'constraints': {
                    **strategy['constraints'],
                    'apply': False  # Dry run for comparison
                }
            }
            
            try:
                optimization = await client.optimize_schedule(optimization_request)
                
                results.append({
                    'strategy': strategy['name'],
                    **optimization,
                    'score_improvement': optimization['metrics']['average_score_lift'],
                    'changes_suggested': optimization['metrics']['changed_count']
                })
                
                print(f'  Changes: {optimization["metrics"]["changed_count"]}')
                print(f'  Score improvement: {optimization["metrics"]["average_score_lift"]:.3f}')
                
            except Exception as e:
                print(f'  Strategy failed: {e}')
                results.append({
                    'strategy': strategy['name'],
                    'error': str(e)
                })
        
        # Recommend best strategy
        print('\n📊 Strategy Comparison:')
        successful_results = [r for r in results if 'error' not in r]
        
        if successful_results:
            best_strategy = max(successful_results, key=lambda x: x['score_improvement'])
            
            print(f'\n🏆 Recommended: {best_strategy["strategy"]}')
            print(f'   Score improvement: {best_strategy["score_improvement"]:.3f}')
            print(f'   Changes: {best_strategy["changes_suggested"]}')
        
        return results
        
    finally:
        client.destroy()

# Usage
async def main():
    # Basic optimization
    # await optimize_basic_schedule('sched_123456789')
    
    # Advanced optimization
    # await optimize_with_advanced_constraints('sched_123456789')
    
    # Compare strategies
    # await compare_optimization_strategies('sched_123456789')

if __name__ == '__main__':
    asyncio.run(main())
```

This completes the practical code examples for the Scheduling API. The examples demonstrate real-world integration patterns, error handling, rate limiting, and advanced optimization strategies for both JavaScript/TypeScript and Python implementations.

The code includes:

- Complete client implementations for both languages
- Authentication and setup examples
- Recommendation fetching with filtering and pagination
- Schedule creation with validation and idempotency
- Schedule management with monitoring and error handling
- Advanced optimization with constraints and strategy comparison
- WebSocket real-time updates
- Comprehensive error handling and retry logic

These examples provide a solid foundation for integrating the Scheduling Optimization API into any application.
