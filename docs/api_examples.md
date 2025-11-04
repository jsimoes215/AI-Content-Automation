# Bulk Operations API Examples

## Table of Contents

1. [Quick Start Guide](#quick-start-guide)
2. [Basic Job Creation](#basic-job-creation)
3. [Progress Monitoring](#progress-monitoring)
4. [Google Sheets Integration](#google-sheets-integration)
5. [Error Handling Patterns](#error-handling-patterns)
6. [WebSocket Real-time Updates](#websocket-real-time-updates)
7. [Advanced Workflows](#advanced-workflows)
8. [SDK Examples](#sdk-examples)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Quick Start Guide

### Authentication Setup

```javascript
// Environment variables
const API_KEY = process.env.CONTENTCREATOR_API_KEY;
const BASE_URL = 'https://api.contentcreator.com/api/v1';
const TENANT_ID = 'your-tenant-id';

// HTTP client setup
const client = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  },
  timeout: 30000
});
```

```python
import os
import requests

# Configuration
API_KEY = os.environ['CONTENTCREATOR_API_KEY']
BASE_URL = 'https://api.contentcreator.com/api/v1'
HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

# HTTP client setup
client = requests.Session()
client.headers.update(HEADERS)
client.timeout = 30
```

## Basic Job Creation

### Create Your First Job

#### JavaScript/TypeScript

```javascript
import axios from 'axios';

class BulkOperationsClient {
  constructor(apiKey, baseUrl) {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.client = axios.create({
      baseURL: baseUrl,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });
  }

  async createJob(jobConfig) {
    try {
      const response = await this.client.post('/bulk-jobs', jobConfig, {
        headers: {
          'Idempotency-Key': this.generateIdempotencyKey()
        }
      });
      
      return {
        success: true,
        job: response.data,
        jobId: response.data.id
      };
    } catch (error) {
      return {
        success: false,
        error: this.handleError(error)
      };
    }
  }

  generateIdempotencyKey() {
    return `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  handleError(error) {
    if (error.response) {
      return {
        status: error.response.status,
        code: error.response.data.error_code,
        message: error.response.data.error_message,
        details: error.response.data.detail
      };
    }
    return {
      status: 0,
      code: 'network_error',
      message: error.message
    };
  }
}

// Example usage
async function main() {
  const client = new BulkOperationsClient('your-api-key', BASE_URL);
  
  const jobConfig = {
    title: 'My First Video Campaign',
    priority: 'normal',
    processing_deadline_ms: 3600000, // 1 hour
    input_source: {
      type: 'sheet',
      sheet_id: '1A2B3C4D5E6F7G8H9I0J',
      range: 'A1:Z10' // Small batch for testing
    },
    output: {
      format: 'mp4',
      video_codec: 'h264',
      audio_codec: 'aac',
      resolution: '1080p',
      output_bucket: 'my-campaign-videos'
    },
    template: {
      template_id: 'tpl_promotional',
      overrides: {
        style: 'modern',
        voice: 'professional_female',
        background_music: 'upbeat_corporate'
      }
    }
  };

  const result = await client.createJob(jobConfig);
  
  if (result.success) {
    console.log(`Job created successfully: ${result.jobId}`);
    console.log(`Initial state: ${result.job.state}`);
    console.log(`Items to process: ${result.job.items_total}`);
  } else {
    console.error('Job creation failed:', result.error);
  }
}

main().catch(console.error);
```

#### Python

```python
import requests
import json
import uuid
from datetime import datetime, timedelta

class BulkOperationsClient:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def create_job(self, job_config):
        try:
            idempotency_key = self._generate_idempotency_key()
            response = self.session.post(
                f'{self.base_url}/bulk-jobs',
                json=job_config,
                headers={'Idempotency-Key': idempotency_key}
            )
            response.raise_for_status()
            
            return {
                'success': True,
                'job': response.json(),
                'job_id': response.json()['id']
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': self._handle_error(e)
            }
    
    def _generate_idempotency_key(self):
        return f"job_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
    
    def _handle_error(self, error):
        if hasattr(error, 'response') and error.response is not None:
            return {
                'status': error.response.status_code,
                'code': error.response.json().get('error_code'),
                'message': error.response.json().get('error_message'),
                'details': error.response.json().get('detail')
            }
        return {
            'status': 0,
            'code': 'network_error',
            'message': str(error)
        }

# Example usage
def main():
    client = BulkOperationsClient('your-api-key', BASE_URL)
    
    job_config = {
        'title': 'My First Video Campaign',
        'priority': 'normal',
        'processing_deadline_ms': 3600000,  # 1 hour
        'input_source': {
            'type': 'sheet',
            'sheet_id': '1A2B3C4D5E6F7G8H9I0J',
            'range': 'A1:Z10'  # Small batch for testing
        },
        'output': {
            'format': 'mp4',
            'video_codec': 'h264',
            'audio_codec': 'aac',
            'resolution': '1080p',
            'output_bucket': 'my-campaign-videos'
        },
        'template': {
            'template_id': 'tpl_promotional',
            'overrides': {
                'style': 'modern',
                'voice': 'professional_female',
                'background_music': 'upbeat_corporate'
            }
        }
    }

    result = client.create_job(job_config)
    
    if result['success']:
        print(f"Job created successfully: {result['job_id']}")
        print(f"Initial state: {result['job']['state']}")
        print(f"Items to process: {result['job']['items_total']}")
    else:
        print('Job creation failed:', result['error'])

if __name__ == '__main__':
    main()
```

### Batch Job with Multiple Templates

```javascript
async function createBatchJob() {
  // Create multiple jobs with different templates
  const templates = [
    { id: 'tpl_promotional', overrides: { style: 'modern', voice: 'female' } },
    { id: 'tpl_tutorial', overrides: { style: 'educational', voice: 'male' } },
    { id: 'tpl_testimonial', overrides: { style: 'casual', voice: 'natural' } }
  ];

  const jobs = [];
  for (const template of templates) {
    const jobConfig = {
      title: `${template.id} Campaign`,
      priority: 'normal',
      input_source: {
        type: 'sheet',
        sheet_id: '1A2B3C4D5E6F7G8H9I0J',
        range: 'A1:Z50'
      },
      output: {
        format: 'mp4',
        video_codec: 'h264',
        audio_codec: 'aac',
        resolution: '1080p',
        output_bucket: 'batch-campaign-videos'
      },
      template: {
        template_id: template.id,
        overrides: template.overrides
      }
    };

    const result = await client.createJob(jobConfig);
    if (result.success) {
      jobs.push(result.job);
      console.log(`Created job: ${result.jobId} for template: ${template.id}`);
    } else {
      console.error(`Failed to create job for template ${template.id}:`, result.error);
    }
  }

  return jobs;
}
```

## Progress Monitoring

### Polling-Based Monitoring

```javascript
class JobMonitor {
  constructor(client) {
    this.client = client;
    this.pollInterval = 5000; // 5 seconds
    this.maxPollTime = 3600000; // 1 hour
  }

  async monitorJob(jobId, onProgress) {
    const startTime = Date.now();
    const timeout = startTime + this.maxPollTime;

    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          // Get job status
          const response = await this.client.client.get(`/bulk-jobs/${jobId}`);
          const job = response.data;

          // Call progress callback
          if (onProgress) {
            onProgress(job);
          }

          // Check if job is terminal
          if (['completed', 'failed', 'canceled'].includes(job.state)) {
            resolve(job);
            return;
          }

          // Check timeout
          if (Date.now() > timeout) {
            reject(new Error('Job monitoring timeout'));
            return;
          }

          // Continue polling
          setTimeout(poll, this.pollInterval);
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  }

  async monitorJobWithRetries(jobId, onProgress, maxRetries = 5) {
    let attempt = 0;
    while (attempt < maxRetries) {
      try {
        return await this.monitorJob(jobId, onProgress);
      } catch (error) {
        attempt++;
        if (attempt >= maxRetries) {
          throw error;
        }
        console.warn(`Polling attempt ${attempt} failed, retrying...`);
        await this.sleep(1000 * attempt); // Exponential backoff
      }
    }
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Usage example
const monitor = new JobMonitor(client);

const result = await monitor.monitorJob('job_01HABCDEF0123456789', (job) => {
  console.log(`Progress: ${job.percent_complete.toFixed(1)}%`);
  console.log(`Completed: ${job.items_completed}/${job.items_total}`);
  console.log(`Failed: ${job.items_failed}`);
  console.log(`ETA: ${Math.round(job.eta_ms / 60000)} minutes`);
});

console.log(`Job completed with state: ${result.state}`);
```

### Python Progress Monitor

```python
import time
from datetime import datetime, timedelta

class JobMonitor:
    def __init__(self, client):
        self.client = client
        self.poll_interval = 5  # seconds
        self.max_poll_time = 3600  # 1 hour
    
    def monitor_job(self, job_id, on_progress=None):
        start_time = time.time()
        timeout = start_time + self.max_poll_time
        
        while time.time() < timeout:
            try:
                response = self.client.session.get(f'{self.client.base_url}/bulk-jobs/{job_id}')
                response.raise_for_status()
                job = response.json()
                
                if on_progress:
                    on_progress(job)
                
                if job['state'] in ['completed', 'failed', 'canceled']:
                    return job
                
                time.sleep(self.poll_interval)
            except requests.exceptions.RequestException as e:
                print(f"Polling error: {e}")
                time.sleep(self.poll_interval)
        
        raise TimeoutError("Job monitoring timeout")

# Usage example
def progress_callback(job):
    percent = job['percent_complete']
    completed = job['items_completed']
    total = job['items_total']
    failed = job['items_failed']
    eta_minutes = round(job['eta_ms'] / 60000) if job['eta_ms'] else 'N/A'
    
    print(f"Progress: {percent:.1f}% | "
          f"Completed: {completed}/{total} | "
          f"Failed: {failed} | "
          f"ETA: {eta_minutes} minutes")

monitor = JobMonitor(client)
result = monitor.monitor_job('job_01HABCDEF0123456789', progress_callback)
print(f"Job completed with state: {result['state']}")
```

## Google Sheets Integration

### Sheet Connection and Validation

```javascript
class SheetManager {
  constructor(client) {
    this.client = client;
  }

  async connectSheet(sheetId, range) {
    try {
      const response = await this.client.client.post('/sheets/connect', {
        sheet_id: sheetId,
        range: range,
        share_permissions: 'read'
      });

      return {
        success: true,
        connection: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: this.client.handleError(error)
      };
    }
  }

  validateSheetData(connection) {
    const { sample } = connection;
    
    // Validate required columns
    const requiredColumns = ['A', 'B', 'C']; // title, script, image
    const missingColumns = requiredColumns.filter(col => !sample.columns.includes(col));
    
    if (missingColumns.length > 0) {
      return {
        valid: false,
        errors: [`Missing required columns: ${missingColumns.join(', ')}`]
      };
    }

    // Validate data types
    const errors = [];
    for (let i = 0; i < sample.preview.length; i++) {
      const row = sample.preview[i];
      
      // Check if title is present
      if (!row[0] || row[0].trim() === '') {
        errors.push(`Row ${i + 1}: Title is required`);
      }
      
      // Check if script is present
      if (!row[1] || row[1].trim() === '') {
        errors.push(`Row ${i + 1}: Script is required`);
      }
      
      // Check if image URL is valid
      if (row[2] && !row[2].startsWith('http')) {
        errors.push(`Row ${i + 1}: Image URL must be valid HTTP(S) URL`);
      }
    }

    return {
      valid: errors.length === 0,
      errors: errors,
      warnings: this.generateWarnings(connection)
    };
  }

  generateWarnings(connection) {
    const warnings = [];
    
    // Warn about empty rows
    const emptyRows = connection.sample.preview.filter(row => 
      !row[0] || row[0].trim() === ''
    ).length;
    
    if (emptyRows > 0) {
      warnings.push(`${emptyRows} empty rows will be skipped`);
    }
    
    // Warn about large batch size
    if (connection.sample.row_count > 1000) {
      warnings.push('Large batch size may take extended processing time');
    }
    
    return warnings;
  }
}

// Complete integration example
async function setupCampaignFromSheet() {
  const sheetManager = new SheetManager(client);
  
  // Connect to sheet
  const sheetId = '1A2B3C4D5E6F7G8H9I0J';
  const range = 'A1:Z1000';
  
  console.log('Connecting to Google Sheet...');
  const connectionResult = await sheetManager.connectSheet(sheetId, range);
  
  if (!connectionResult.success) {
    throw new Error(`Failed to connect sheet: ${connectionResult.error.message}`);
  }
  
  const connection = connectionResult.connection;
  console.log('Sheet connected successfully');
  
  // Validate data
  const validation = sheetManager.validateSheetData(connection);
  console.log('Validation results:', validation);
  
  if (!validation.valid) {
    throw new Error(`Sheet validation failed: ${validation.errors.join(', ')}`);
  }
  
  if (validation.warnings.length > 0) {
    console.warn('Warnings:', validation.warnings);
  }
  
  // Create job using connected sheet
  const jobConfig = {
    title: 'Campaign from Google Sheet',
    priority: 'normal',
    processing_deadline_ms: 7200000,
    input_source: {
      type: 'sheet',
      sheet_id: connection.sheet_id,
      range: connection.range
    },
    output: {
      format: 'mp4',
      video_codec: 'h264',
      audio_codec: 'aac',
      resolution: '1080p',
      output_bucket: 'sheet-campaign-videos'
    },
    template: {
      template_id: 'tpl_standard',
      overrides: {
        style: 'modern',
        voice: 'professional',
        background_music: 'corporate_upbeat'
      }
    }
  };
  
  const jobResult = await client.createJob(jobConfig);
  if (jobResult.success) {
    console.log(`Job created: ${jobResult.jobId}`);
    return jobResult.job;
  } else {
    throw new Error(`Job creation failed: ${jobResult.error.message}`);
  }
}
```

### Python Sheet Management

```python
import re
import requests
from urllib.parse import urlparse

class SheetManager:
    def __init__(self, client):
        self.client = client
    
    def connect_sheet(self, sheet_id, range):
        try:
            response = self.client.session.post(
                f'{self.client.base_url}/sheets/connect',
                json={
                    'sheet_id': sheet_id,
                    'range': range,
                    'share_permissions': 'read'
                }
            )
            response.raise_for_status()
            
            return {
                'success': True,
                'connection': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': self.client._handle_error(e)
            }
    
    def validate_sheet_data(self, connection):
        sample = connection['sample']
        errors = []
        warnings = []
        
        # Check required columns
        required_columns = ['A', 'B', 'C']  # title, script, image
        missing_columns = [col for col in required_columns if col not in sample['columns']]
        
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # Validate data types
        for i, row in enumerate(sample['preview']):
            row_num = i + 1
            
            # Check title
            if not row[0] or not row[0].strip():
                errors.append(f"Row {row_num}: Title is required")
            
            # Check script
            if not row[1] or not row[1].strip():
                errors.append(f"Row {row_num}: Script is required")
            
            # Check image URL
            if row[2]:
                if not self._is_valid_url(row[2]):
                    errors.append(f"Row {row_num}: Image URL must be valid HTTP(S) URL")
        
        # Generate warnings
        empty_rows = sum(1 for row in sample['preview'] if not row[0] or not row[0].strip())
        if empty_rows > 0:
            warnings.append(f"{empty_rows} empty rows will be skipped")
        
        if sample['row_count'] > 1000:
            warnings.append("Large batch size may take extended processing time")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _is_valid_url(self, url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except:
            return False

# Usage example
def setup_campaign_from_sheet():
    sheet_manager = SheetManager(client)
    
    sheet_id = '1A2B3C4D5E6F7G8H9I0J'
    range = 'A1:Z1000'
    
    print('Connecting to Google Sheet...')
    connection_result = sheet_manager.connect_sheet(sheet_id, range)
    
    if not connection_result['success']:
        raise Exception(f"Failed to connect sheet: {connection_result['error']['message']}")
    
    connection = connection_result['connection']
    print('Sheet connected successfully')
    
    # Validate data
    validation = sheet_manager.validate_sheet_data(connection)
    print('Validation results:', validation)
    
    if not validation['valid']:
        raise Exception(f"Sheet validation failed: {', '.join(validation['errors'])}")
    
    if validation['warnings']:
        print('Warnings:', ', '.join(validation['warnings']))
    
    # Create job
    job_config = {
        'title': 'Campaign from Google Sheet',
        'priority': 'normal',
        'processing_deadline_ms': 7200000,
        'input_source': {
            'type': 'sheet',
            'sheet_id': connection['sheet_id'],
            'range': connection['range']
        },
        'output': {
            'format': 'mp4',
            'video_codec': 'h264',
            'audio_codec': 'aac',
            'resolution': '1080p',
            'output_bucket': 'sheet-campaign-videos'
        },
        'template': {
            'template_id': 'tpl_standard',
            'overrides': {
                'style': 'modern',
                'voice': 'professional',
                'background_music': 'corporate_upbeat'
            }
        }
    }
    
    job_result = client.create_job(job_config)
    if job_result['success']:
        print(f"Job created: {job_result['job_id']}")
        return job_result['job']
    else:
        raise Exception(f"Job creation failed: {job_result['error']['message']}")
```

## Error Handling Patterns

### Comprehensive Error Handler

```javascript
class RobustBulkOperationsClient extends BulkOperationsClient {
  async createJobWithRetry(jobConfig, maxRetries = 3) {
    let lastError;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const result = await this.createJob(jobConfig);
        
        if (result.success) {
          return result;
        }
        
        // Check if error is retryable
        const error = result.error;
        if (!this.isRetryableError(error)) {
          throw new Error(`Non-retryable error: ${error.message}`);
        }
        
        lastError = error;
        console.warn(`Job creation attempt ${attempt} failed, retrying...`, error);
        
        // Exponential backoff
        const delay = Math.min(1000 * Math.pow(2, attempt - 1), 30000);
        await this.sleep(delay);
        
      } catch (err) {
        lastError = err;
        if (attempt === maxRetries) {
          throw err;
        }
        
        const delay = Math.min(1000 * Math.pow(2, attempt - 1), 30000);
        await this.sleep(delay);
      }
    }
    
    throw new Error(`Failed after ${maxRetries} attempts: ${lastError.message}`);
  }

  isRetryableError(error) {
    const retryableCodes = [
      'rate_limited',
      'service_unavailable',
      'gateway_timeout',
      'network_error'
    ];
    
    const retryableStatuses = [429, 503, 504];
    
    return retryableCodes.includes(error.code) || 
           retryableStatuses.includes(error.status);
  }

  async monitorJobWithErrorHandling(jobId, onProgress) {
    const monitor = new JobMonitor(this);
    
    try {
      return await monitor.monitorJobWithRetries(jobId, onProgress);
    } catch (error) {
      // Log error with correlation ID
      console.error('Job monitoring failed:', {
        jobId: jobId,
        error: error.message,
        correlationId: error.headers?.['x-correlation-id']
      });
      
      // Attempt to get final job state
      try {
        const response = await this.client.get(`/bulk-jobs/${jobId}`);
        const job = response.data;
        console.log(`Final job state: ${job.state} (${job.percent_complete}% complete)`);
        return job;
      } catch (statusError) {
        throw new Error(`Unable to determine final job state: ${statusError.message}`);
      }
    }
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Usage with comprehensive error handling
async function robustJobExample() {
  const client = new RobustBulkOperationsClient('your-api-key', BASE_URL);
  
  const jobConfig = {
    title: 'Robust Job Example',
    // ... job configuration
  };
  
  try {
    // Create job with retry logic
    const jobResult = await client.createJobWithRetry(jobConfig);
    console.log(`Job created: ${jobResult.jobId}`);
    
    // Monitor with error handling
    const finalJob = await client.monitorJobWithErrorHandling(
      jobResult.jobId,
      (job) => console.log(`Progress: ${job.percent_complete}%`)
    );
    
    console.log(`Job completed: ${finalJob.state}`);
    
  } catch (error) {
    console.error('Job workflow failed:', error.message);
    
    // Implement fallback strategy
    await handleJobFailure(error);
  }
}
```

### Python Error Handling

```python
import time
import random
from requests.exceptions import RequestException, Timeout, ConnectionError

class RobustBulkOperationsClient(BulkOperationsClient):
    def create_job_with_retry(self, job_config, max_retries=3):
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                result = self.create_job(job_config)
                
                if result['success']:
                    return result
                
                error = result['error']
                if not self.is_retryable_error(error):
                    raise Exception(f"Non-retryable error: {error['message']}")
                
                last_error = error
                print(f"Job creation attempt {attempt} failed, retrying...", error)
                
                # Exponential backoff
                delay = min(1000 * (2 ** (attempt - 1)), 30000) / 1000
                time.sleep(delay)
                
            except (RequestException, Timeout, ConnectionError) as e:
                last_error = e
                if attempt == max_retries:
                    raise e
                
                delay = min(1000 * (2 ** (attempt - 1)), 30000) / 1000
                time.sleep(delay)
        
        raise Exception(f"Failed after {max_retries} attempts: {last_error}")
    
    def is_retryable_error(self, error):
        retryable_codes = ['rate_limited', 'service_unavailable', 'gateway_timeout', 'network_error']
        retryable_statuses = [429, 503, 504]
        
        return error.get('code') in retryable_codes or error.get('status') in retryable_statuses
    
    def monitor_job_with_error_handling(self, job_id, on_progress=None):
        monitor = JobMonitor(self)
        
        try:
            return monitor.monitor_job(job_id, on_progress)
        except (TimeoutError, Exception) as error:
            print(f"Job monitoring failed: {error}")
            
            # Try to get final state
            try:
                response = self.session.get(f'{self.base_url}/bulk-jobs/{job_id}')
                job = response.json()
                print(f"Final job state: {job['state']} ({job['percent_complete']}% complete)")
                return job
            except Exception as status_error:
                raise Exception(f"Unable to determine final job state: {status_error}")
```

## WebSocket Real-time Updates

### WebSocket Client Implementation

```javascript
import WebSocket from 'ws';

class WebSocketMonitor {
  constructor(jobId, apiKey, baseUrl) {
    this.jobId = jobId;
    this.apiKey = apiKey;
    this.baseUrl = baseUrl.replace('https://', 'wss://');
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
  }

  connect(onMessage, onError) {
    const wsUrl = `${this.baseUrl}/ws/bulk-jobs?job_id=${this.jobId}`;
    const headers = {
      'Authorization': `Bearer ${this.apiKey}`,
      'Sec-WebSocket-Protocol': `Bearer ${this.apiKey}`
    };

    this.ws = new WebSocket(wsUrl, { headers });

    this.ws.on('open', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    });

    this.ws.on('message', (data) => {
      try {
        const message = JSON.parse(data.toString());
        onMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    });

    this.ws.on('error', (error) => {
      console.error('WebSocket error:', error);
      if (onError) onError(error);
    });

    this.ws.on('close', () => {
      console.log('WebSocket disconnected');
      this.attemptReconnect(onMessage, onError);
    });
  }

  attemptReconnect(onMessage, onError) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
      
      setTimeout(() => {
        this.connect(onMessage, onError);
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Complete WebSocket monitoring example
async function monitorJobWithWebSocket(jobId) {
  const wsMonitor = new WebSocketMonitor(jobId, 'your-api-key', BASE_URL);
  
  const messageHandlers = {
    'job.state_changed': (data) => {
      console.log(`Job state changed: ${data.prior_state} → ${data.new_state}`);
      if (data.reason) {
        console.log(`Reason: ${data.reason}`);
      }
    },
    
    'job.progress': (data) => {
      console.log(`Progress: ${data.percent_complete.toFixed(1)}%`);
      console.log(`Items: ${data.items_completed}/${data.items_total} completed`);
      if (data.eta_ms) {
        console.log(`ETA: ${Math.round(data.eta_ms / 60000)} minutes`);
      }
      if (data.rate_limited) {
        console.log('⚠️  Rate limited - processing may be delayed');
      }
    },
    
    'video.completed': (data) => {
      console.log(`Video completed: ${data.id}`);
      console.log(`Artifacts: ${data.artifacts.length} file(s)`);
      
      // Download completed video
      data.artifacts.forEach(artifact => {
        if (artifact.type === 'video') {
          console.log(`Video URL: ${artifact.url}`);
          // Initiate download here
        }
      });
    },
    
    'video.failed': (data) => {
      console.error(`Video failed: ${data.id}`);
      data.errors.forEach(error => {
        console.error(`  ${error.error_code}: ${error.error_message}`);
      });
    },
    
    'job.completed': (data) => {
      console.log('🎉 Job completed successfully!');
      console.log(`Summary: ${data.summary.items_completed}/${data.summary.items_total} videos created`);
      
      if (data.artifacts) {
        data.artifacts.forEach(artifact => {
          console.log(`${artifact.type}: ${artifact.url}`);
        });
      }
    },
    
    'job.failed': (data) => {
      console.error('❌ Job failed');
      console.error(`Error: ${data.error_message}`);
    }
  };

  const onMessage = (message) => {
    const handler = messageHandlers[message.type];
    if (handler) {
      handler(message.data);
    } else {
      console.log('Unknown message type:', message.type);
    }
  };

  const onError = (error) => {
    console.error('WebSocket error:', error);
  };

  // Start monitoring
  wsMonitor.connect(onMessage, onError);

  // Return a promise that resolves when job completes
  return new Promise((resolve, reject) => {
    const checkCompletion = setInterval(() => {
      // You can also poll the job status here as backup
      // This ensures we don't miss completion events
    }, 30000);

    // Clean up after some time
    setTimeout(() => {
      clearInterval(checkCompletion);
      wsMonitor.disconnect();
    }, 3600000); // 1 hour timeout
  });
}

// Usage
async function main() {
  const jobId = 'job_01HABCDEF0123456789';
  
  try {
    await monitorJobWithWebSocket(jobId);
    console.log('Monitoring completed');
  } catch (error) {
    console.error('WebSocket monitoring failed:', error);
  }
}
```

### Python WebSocket Client

```python
import json
import time
import websocket
import threading

class WebSocketMonitor:
    def __init__(self, job_id, api_key, base_url):
        self.job_id = job_id
        self.api_key = api_key
        self.base_url = base_url.replace('https://', 'wss://')
        self.ws = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 1
    
    def connect(self, on_message, on_error=None):
        def on_open(ws):
            print('WebSocket connected')
            self.reconnect_attempts = 0
        
        def on_message_handler(ws, message):
            try:
                data = json.loads(message)
                on_message(data)
            except json.JSONDecodeError as e:
                print(f'Failed to parse WebSocket message: {e}')
        
        def on_error_handler(ws, error):
            print(f'WebSocket error: {error}')
            if on_error:
                on_error(error)
        
        def on_close(ws, close_status_code, close_msg):
            print('WebSocket disconnected')
            self.attempt_reconnect(on_message, on_error)
        
        ws_url = f"{self.base_url}/ws/bulk-jobs?job_id={self.job_id}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Sec-WebSocket-Protocol': f'Bearer {self.api_key}'
        }
        
        self.ws = websocket.WebSocketApp(
            ws_url,
            header=headers,
            on_open=on_open,
            on_message=on_message_handler,
            on_error=on_error_handler,
            on_close=on_close
        )
        
        self.ws.run_forever()
    
    def attempt_reconnect(self, on_message, on_error):
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            delay = self.reconnect_delay * (2 ** (self.reconnect_attempts - 1))
            print(f'Reconnecting in {delay}s (attempt {self.reconnect_attempts})')
            
            time.sleep(delay)
            self.connect(on_message, on_error)
        else:
            print('Max reconnection attempts reached')
    
    def disconnect(self):
        if self.ws:
            self.ws.close()

# Message handlers
def create_message_handlers():
    return {
        'job.state_changed': lambda data: print(f"Job state changed: {data['prior_state']} → {data['new_state']}"),
        'job.progress': lambda data: print(f"Progress: {data['percent_complete']:.1f}% | "
                                           f"Items: {data['items_completed']}/{data['items_total']}"),
        'video.completed': lambda data: print(f"Video completed: {data['id']}"),
        'job.completed': lambda data: print("🎉 Job completed successfully!"),
        'job.failed': lambda data: print("❌ Job failed")
    }

def monitor_job_websocket(job_id):
    ws_monitor = WebSocketMonitor(job_id, 'your-api-key', BASE_URL)
    message_handlers = create_message_handlers()
    
    def on_message(message):
        handler = message_handlers.get(message['type'])
        if handler:
            handler(message['data'])
        else:
            print(f'Unknown message type: {message["type"]}')
    
    # Run in separate thread
    ws_thread = threading.Thread(target=ws_monitor.connect, args=(on_message,))
    ws_thread.daemon = True
    ws_thread.start()
    
    return ws_monitor
```

## Advanced Workflows

### Multi-Stage Campaign Workflow

```javascript
class CampaignManager {
  constructor(client) {
    this.client = client;
    this.stages = [
      { name: 'concept', template: 'tpl_concept', range: 'A1:Z10' },
      { name: 'promotion', template: 'tpl_promotional', range: 'A1:Z25' },
      { name: 'testimonial', template: 'tpl_testimonial', range: 'A1:Z15' }
    ];
  }

  async createMultiStageCampaign(globalConfig) {
    const stages = {};
    
    for (const stage of this.stages) {
      console.log(`Creating ${stage.name} stage...`);
      
      const jobConfig = {
        title: `${globalConfig.campaignName} - ${stage.name} Stage`,
        priority: globalConfig.priority || 'normal',
        processing_deadline_ms: globalConfig.deadlineMs || 3600000,
        input_source: {
          type: 'sheet',
          sheet_id: globalConfig.sheetId,
          range: stage.range
        },
        output: {
          format: 'mp4',
          video_codec: 'h264',
          audio_codec: 'aac',
          resolution: '1080p',
          output_bucket: `${globalConfig.bucketPrefix}-${stage.name}`
        },
        template: {
          template_id: stage.template,
          overrides: {
            style: globalConfig.style || 'modern',
            voice: globalConfig.voice || 'professional',
            ...globalConfig.templateOverrides
          }
        }
      };

      const result = await this.client.createJob(jobConfig);
      if (result.success) {
        stages[stage.name] = result.job;
        console.log(`Created ${stage.name} job: ${result.jobId}`);
      } else {
        throw new Error(`Failed to create ${stage.name} job: ${result.error.message}`);
      }
    }

    return stages;
  }

  async monitorAllStages(stages, onProgress) {
    const stageMonitors = {};
    
    // Start monitoring all stages
    for (const [stageName, job] of Object.entries(stages)) {
      stageMonitors[stageName] = this.client.monitorJobWithErrorHandling(
        job.id,
        (jobData) => onProgress(stageName, jobData)
      );
    }

    // Wait for all stages to complete
    const results = {};
    for (const [stageName, monitor] of Object.entries(stageMonitors)) {
      try {
        results[stageName] = await monitor;
        console.log(`${stageName} stage completed: ${results[stageName].state}`);
      } catch (error) {
        console.error(`${stageName} stage failed:`, error.message);
        results[stageName] = { state: 'failed', error: error.message };
      }
    }

    return results;
  }
}

// Usage
async function runMultiStageCampaign() {
  const campaignManager = new CampaignManager(client);
  
  const globalConfig = {
    campaignName: 'Product Launch 2025',
    priority: 'high',
    deadlineMs: 7200000, // 2 hours
    sheetId: '1A2B3C4D5E6F7G8H9I0J',
    bucketPrefix: 'product-launch',
    style: 'premium',
    voice: 'energetic_female',
    templateOverrides: {
      background_music: 'launch_anthem',
      color_scheme: 'premium_gold'
    }
  };

  try {
    // Create all stage jobs
    const stages = await campaignManager.createMultiStageCampaign(globalConfig);
    console.log('All stage jobs created:', Object.keys(stages));

    // Monitor progress
    const onProgress = (stageName, job) => {
      console.log(`[${stageName}] ${job.percent_complete.toFixed(1)}% complete`);
    };

    const results = await campaignManager.monitorAllStages(stages, onProgress);
    
    // Generate campaign report
    const report = {
      campaignName: globalConfig.campaignName,
      stages: results,
      summary: {
        totalJobs: Object.keys(stages).length,
        completedJobs: Object.values(results).filter(r => r.state === 'completed').length,
        failedJobs: Object.values(results).filter(r => r.state === 'failed').length
      }
    };

    console.log('Campaign completed:', report.summary);
    return report;

  } catch (error) {
    console.error('Campaign failed:', error.message);
    throw error;
  }
}
```

### Bulk Operations with Conditional Logic

```javascript
class IntelligentBulkOperationsClient extends BulkOperationsClient {
  async createAdaptiveJob(baseConfig) {
    const sheetData = await this.getSheetData(baseConfig.sheetId, baseConfig.range);
    
    // Analyze content and adjust job configuration
    const adaptations = this.analyzeContent(sheetData);
    const adaptiveConfig = this.applyAdaptations(baseConfig, adaptations);
    
    return await this.createJob(adaptiveConfig);
  }

  analyzeContent(sheetData) {
    const adaptations = {
      highPriorityRows: [],
      templateOverrides: {},
      outputAdjustments: {}
    };

    for (let i = 0; i < sheetData.length; i++) {
      const row = sheetData[i];
      
      // Check for high-priority indicators
      if (row.includes('urgent') || row.includes('priority')) {
        adaptations.highPriorityRows.push(i);
      }
      
      // Analyze content type for template selection
      if (row.includes('tutorial') || row.includes('how-to')) {
        adaptations.templateOverrides[i] = { style: 'educational', voice: 'clear_male' };
      } else if (row.includes('testimonial') || row.includes('review')) {
        adaptations.templateOverrides[i] = { style: 'authentic', voice: 'natural' };
      }
    }

    return adaptations;
  }

  applyAdaptations(baseConfig, adaptations) {
    const config = { ...baseConfig };
    
    // Adjust processing deadline based on batch size
    if (config.input_source.range.includes('Z1000')) {
      config.processing_deadline_ms = 14400000; // 4 hours for large batches
    }
    
    // Add conditional template logic
    if (adaptations.highPriorityRows.length > 0) {
      config.priority = 'high';
      config.callback_url = `${config.callback_url}?priority_rows=${adaptations.highPriorityRows.length}`;
    }
    
    return config;
  }

  async getSheetData(sheetId, range) {
    // This would fetch actual sheet data
    // For now, return mock data
    return [
      ['Product Tutorial', 'Learn how to use our tool...', 'tutorial'],
      ['Customer Review', 'This product changed my life...', 'testimonial'],
      ['URGENT: Launch Video', 'Big announcement coming!', 'urgent']
    ];
  }
}

// Smart job creation with content analysis
async function createIntelligentCampaign() {
  const client = new IntelligentBulkOperationsClient('your-api-key', BASE_URL);
  
  const jobConfig = {
    title: 'Intelligent Campaign',
    priority: 'normal',
    processing_deadline_ms: 3600000,
    input_source: {
      type: 'sheet',
      sheet_id: '1A2B3C4D5E6F7G8H9I0J',
      range: 'A1:Z50'
    },
    output: {
      format: 'mp4',
      video_codec: 'h264',
      audio_codec: 'aac',
      resolution: '1080p',
      output_bucket: 'intelligent-campaign'
    },
    template: {
      template_id: 'tpl_adaptive',
      overrides: {
        style: 'modern',
        voice: 'professional'
      }
    },
    callback_url: 'https://client.example.com/webhooks/complete'
  };

  const result = await client.createAdaptiveJob(jobConfig);
  
  if (result.success) {
    console.log(`Created adaptive job: ${result.jobId}`);
    console.log(`Detected ${result.adaptations?.highPriorityRows?.length || 0} high-priority items`);
    return result.job;
  } else {
    throw new Error(`Job creation failed: ${result.error.message}`);
  }
}
```

## SDK Examples

### JavaScript SDK

```javascript
// content-creator-sdk.js
import axios from 'axios';
import WebSocket from 'ws';

export class ContentCreatorBulkSDK {
  constructor(config) {
    this.apiKey = config.apiKey;
    this.baseUrl = config.baseUrl || 'https://api.contentcreator.com/api/v1';
    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      }
    });
  }

  // Job management methods
  async createJob(config) {
    const response = await this.client.post('/bulk-jobs', config, {
      headers: { 'Idempotency-Key': this.generateIdempotencyKey() }
    });
    return response.data;
  }

  async getJob(jobId) {
    const response = await this.client.get(`/bulk-jobs/${jobId}`);
    return response.data;
  }

  async listJobs(filters = {}) {
    const response = await this.client.get('/bulk-jobs', { params: filters });
    return response.data;
  }

  async getJobVideos(jobId, filters = {}) {
    const response = await this.client.get(`/bulk-jobs/${jobId}/videos`, { 
      params: filters 
    });
    return response.data;
  }

  // Sheet management methods
  async connectSheet(sheetId, range) {
    const response = await this.client.post('/sheets/connect', {
      sheet_id: sheetId,
      range: range,
      share_permissions: 'read'
    });
    return response.data;
  }

  // WebSocket monitoring
  monitorJob(jobId, callbacks) {
    const wsUrl = this.baseUrl.replace('https://', 'wss://') + 
                  `/ws/bulk-jobs?job_id=${jobId}`;
    
    const ws = new WebSocket(wsUrl, {
      headers: { 'Authorization': `Bearer ${this.apiKey}` }
    });

    ws.on('open', () => callbacks.onConnect && callbacks.onConnect());
    ws.on('message', (data) => {
      const message = JSON.parse(data);
      const handler = callbacks[message.type];
      if (handler) handler(message.data);
    });
    ws.on('error', (error) => callbacks.onError && callbacks.onError(error));
    ws.on('close', () => callbacks.onClose && callbacks.onClose());

    return {
      disconnect: () => ws.close()
    };
  }

  // Utility methods
  generateIdempotencyKey() {
    return `sdk_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // High-level workflow methods
  async createAndMonitorJob(jobConfig, progressCallback) {
    const job = await this.createJob(jobConfig);
    
    // Start monitoring
    const monitor = this.monitorJob(job.id, {
      'job.progress': (data) => {
        progressCallback && progressCallback(data);
      },
      'job.completed': (data) => {
        console.log('Job completed:', data.summary);
      },
      'job.failed': (data) => {
        console.error('Job failed:', data.error_message);
      }
    });

    return { job, monitor };
  }
}

// Usage examples
import { ContentCreatorBulkSDK } from './content-creator-sdk.js';

// Example 1: Simple job creation
const sdk = new ContentCreatorBulkSDK({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.contentcreator.com/api/v1'
});

// Example 2: Job with real-time monitoring
async function exampleWithMonitoring() {
  const jobConfig = {
    title: 'SDK Example Job',
    input_source: {
      type: 'sheet',
      sheet_id: '1A2B3C4D5E6F7G8H9I0J',
      range: 'A1:Z10'
    },
    output: {
      format: 'mp4',
      video_codec: 'h264',
      audio_codec: 'aac',
      resolution: '1080p',
      output_bucket: 'sdk-examples'
    },
    template: {
      template_id: 'tpl_example',
      overrides: { style: 'modern' }
    }
  };

  const { job, monitor } = await sdk.createAndMonitorJob(
    jobConfig,
    (progress) => console.log(`Progress: ${progress.percent_complete}%`)
  );

  console.log(`Monitoring job: ${job.id}`);
}

// Example 3: Sheet connection and validation
async function exampleWithSheet() {
  const sheet = await sdk.connectSheet(
    '1A2B3C4D5E6F7G8H9I0J',
    'A1:Z100'
  );

  console.log('Sheet connected:', sheet.status);
  
  const jobConfig = {
    title: 'Sheet-based Job',
    input_source: {
      type: 'sheet',
      sheet_id: sheet.sheet_id,
      range: sheet.range
    },
    // ... other config
  };

  const job = await sdk.createJob(jobConfig);
  console.log(`Job created: ${job.id}`);
}
```

### Python SDK

```python
# content_creator_sdk.py
import requests
import websocket
import json
import threading
import time

class ContentCreatorBulkSDK:
    def __init__(self, api_key, base_url='https://api.contentcreator.com/api/v1'):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def create_job(self, config):
        response = self.session.post(
            f'{self.base_url}/bulk-jobs',
            json=config,
            headers={'Idempotency-Key': self.generate_idempotency_key()}
        )
        response.raise_for_status()
        return response.json()
    
    def get_job(self, job_id):
        response = self.session.get(f'{self.base_url}/bulk-jobs/{job_id}')
        response.raise_for_status()
        return response.json()
    
    def list_jobs(self, filters=None):
        response = self.session.get(f'{self.base_url}/bulk-jobs', params=filters or {})
        response.raise_for_status()
        return response.json()
    
    def get_job_videos(self, job_id, filters=None):
        response = self.session.get(
            f'{self.base_url}/bulk-jobs/{job_id}/videos',
            params=filters or {}
        )
        response.raise_for_status()
        return response.json()
    
    def connect_sheet(self, sheet_id, range):
        response = self.session.post(
            f'{self.base_url}/sheets/connect',
            json={
                'sheet_id': sheet_id,
                'range': range,
                'share_permissions': 'read'
            }
        )
        response.raise_for_status()
        return response.json()
    
    def monitor_job(self, job_id, callbacks):
        ws_url = self.base_url.replace('https://', 'wss://') + f'/ws/bulk-jobs?job_id={job_id}'
        
        def on_open(ws):
            callbacks.get('on_connect', lambda: None)()
        
        def on_message(ws, message):
            data = json.loads(message)
            handler = callbacks.get(data['type'])
            if handler:
                handler(data['data'])
        
        def on_error(ws, error):
            callbacks.get('on_error', lambda e: None)(error)
        
        def on_close(ws, close_status_code, close_msg):
            callbacks.get('on_close', lambda: None)()
        
        ws = websocket.WebSocketApp(
            ws_url,
            header={'Authorization': f'Bearer {self.api_key}'},
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # Run in separate thread
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        return {
            'disconnect': ws.close,
            'thread': ws_thread
        }
    
    def create_and_monitor_job(self, job_config, progress_callback=None):
        job = self.create_job(job_config)
        
        callbacks = {
            'job.progress': lambda data: progress_callback and progress_callback(data),
            'job.completed': lambda data: print('Job completed:', data.get('summary')),
            'job.failed': lambda data: print('Job failed:', data.get('error_message'))
        }
        
        monitor = self.monitor_job(job['id'], callbacks)
        return {'job': job, 'monitor': monitor}
    
    def generate_idempotency_key(self):
        import time
        import random
        return f"sdk_{int(time.time())}_{random.randint(100000, 999999)}"

# Usage examples
def example_simple_job():
    sdk = ContentCreatorBulkSDK('your-api-key')
    
    job_config = {
        'title': 'Python SDK Example',
        'input_source': {
            'type': 'sheet',
            'sheet_id': '1A2B3C4D5E6F7G8H9I0J',
            'range': 'A1:Z10'
        },
        'output': {
            'format': 'mp4',
            'video_codec': 'h264',
            'audio_codec': 'aac',
            'resolution': '1080p',
            'output_bucket': 'python-sdk-examples'
        },
        'template': {
            'template_id': 'tpl_example',
            'overrides': {'style': 'modern'}
        }
    }
    
    job = sdk.create_job(job_config)
    print(f"Job created: {job['id']}")
    return job

def example_with_monitoring():
    sdk = ContentCreatorBulkSDK('your-api-key')
    
    def progress_callback(progress):
        print(f"Progress: {progress['percent_complete']:.1f}%")
    
    job_config = {
        'title': 'Monitored Job',
        # ... config
    }
    
    result = sdk.create_and_monitor_job(job_config, progress_callback)
    print(f"Monitoring job: {result['job']['id']}")
    return result
```

## Best Practices

### Job Creation Best Practices

```javascript
class BestPracticesClient {
  constructor(apiKey, baseUrl) {
    this.client = new BulkOperationsClient(apiKey, baseUrl);
    this.rateLimiter = new RateLimiter(10, 60000); // 10 requests per minute
  }

  async createJobOptimized(config) {
    // 1. Always use idempotency
    const idempotencyKey = this.generateIdempotencyKey();
    
    // 2. Validate configuration before submission
    const validation = this.validateJobConfig(config);
    if (!validation.valid) {
      throw new Error(`Invalid config: ${validation.errors.join(', ')}`);
    }
    
    // 3. Apply rate limiting
    await this.rateLimiter.acquire();
    
    try {
      // 4. Use appropriate timeout and retry logic
      const result = await this.createJobWithRetry(config, idempotencyKey);
      
      // 5. Log successful creation
      console.log(`Job created successfully: ${result.jobId}`, {
        jobId: result.jobId,
        itemsTotal: result.job.items_total,
        templateId: config.template.template_id
      });
      
      return result;
    } catch (error) {
      // 6. Log failures with context
      console.error('Job creation failed:', {
        error: error.message,
        config: {
          templateId: config.template?.template_id,
          items: config.input_source?.range,
          bucket: config.output?.output_bucket
        }
      });
      throw error;
    }
  }

  validateJobConfig(config) {
    const errors = [];
    
    // Required fields
    if (!config.input_source?.sheet_id) {
      errors.push('sheet_id is required');
    }
    
    if (!config.template?.template_id) {
      errors.push('template_id is required');
    }
    
    if (!config.output?.output_bucket) {
      errors.push('output_bucket is required');
    }
    
    // Validation rules
    if (config.input_source?.range) {
      const rangeMatch = config.input_source.range.match(/A1:Z(\d+)/);
      if (rangeMatch) {
        const rowCount = parseInt(rangeMatch[1]);
        if (rowCount > 10000) {
          errors.push('Maximum 10,000 rows allowed');
        }
        if (rowCount > 1000) {
          console.warn(`Large batch (${rowCount} rows) may take extended time`);
        }
      }
    }
    
    return {
      valid: errors.length === 0,
      errors: errors
    };
  }

  async createJobWithRetry(config, idempotencyKey) {
    let lastError;
    
    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        const result = await this.client.client.post('/bulk-jobs', config, {
          headers: { 'Idempotency-Key': idempotencyKey }
        });
        
        return {
          success: true,
          job: result.data,
          jobId: result.data.id
        };
      } catch (error) {
        lastError = error;
        
        if (attempt === 3 || !this.isRetryableError(error)) {
          break;
        }
        
        const delay = Math.min(1000 * Math.pow(2, attempt - 1), 5000);
        await this.sleep(delay);
      }
    }
    
    return {
      success: false,
      error: this.client.handleError(lastError)
    };
  }

  isRetryableError(error) {
    if (error.response) {
      const status = error.response.status;
      return [429, 500, 502, 503, 504].includes(status);
    }
    return false;
  }

  generateIdempotencyKey() {
    return `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Rate limiter implementation
class RateLimiter {
  constructor(maxRequests, timeWindow) {
    this.maxRequests = maxRequests;
    this.timeWindow = timeWindow;
    this.requests = [];
  }

  async acquire() {
    const now = Date.now();
    
    // Remove old requests outside the time window
    this.requests = this.requests.filter(timestamp => now - timestamp < this.timeWindow);
    
    if (this.requests.length >= this.maxRequests) {
      const oldestRequest = Math.min(...this.requests);
      const waitTime = this.timeWindow - (now - oldestRequest);
      
      if (waitTime > 0) {
        console.log(`Rate limit reached, waiting ${waitTime}ms`);
        await this.sleep(waitTime);
        return this.acquire(); // Recursive call after waiting
      }
    }
    
    this.requests.push(now);
  }
}
```

### Progress Monitoring Best Practices

```javascript
class OptimizedJobMonitor {
  constructor(client) {
    this.client = client;
    this.watchers = new Map();
  }

  async monitorJobOptimized(jobId, options = {}) {
    const {
      onProgress = () => {},
      onStateChange = () => {},
      onVideoComplete = () => {},
      onError = () => {},
      pollInterval = 5000,
      maxRetries = 5,
      enableWebSocket = true
    } = options;

    let lastProgress = 0;
    let retryCount = 0;
    let lastState = null;

    // 1. Use WebSocket for real-time updates if enabled
    let wsMonitor = null;
    if (enableWebSocket) {
      wsMonitor = this.client.monitorJob(jobId, {
        'job.progress': (data) => {
          if (data.percent_complete > lastProgress) {
            lastProgress = data.percent_complete;
            onProgress(data);
          }
        },
        'job.state_changed': (data) => {
          if (data.new_state !== lastState) {
            lastState = data.new_state;
            onStateChange(data);
          }
        },
        'video.completed': onVideoComplete,
        'job.failed': onError,
        'job.completed': (data) => {
          onStateChange({ new_state: 'completed', data });
        }
      });
    }

    // 2. Polling fallback with smart interval adjustment
    const pollJob = async () => {
      try {
        const job = await this.client.getJob(jobId);
        
        // 3. Smart polling - reduce frequency when progress is slow
        let currentPollInterval = pollInterval;
        if (job.percent_complete - lastProgress < 1) {
          // Progress is slow, poll less frequently
          currentPollInterval = Math.min(pollInterval * 2, 30000);
        }
        
        // 4. Check for terminal state
        if (['completed', 'failed', 'canceled'].includes(job.state)) {
          if (wsMonitor) wsMonitor.disconnect();
          return job;
        }
        
        // 5. Continue polling
        setTimeout(pollJob, currentPollInterval);
        retryCount = 0; // Reset retry count on success
        
      } catch (error) {
        retryCount++;
        
        if (retryCount >= maxRetries) {
          if (wsMonitor) wsMonitor.disconnect();
          onError(error);
          throw new Error(`Monitoring failed after ${maxRetries} retries`);
        }
        
        // 6. Exponential backoff for polling errors
        const backoffDelay = Math.min(1000 * Math.pow(2, retryCount - 1), 30000);
        setTimeout(pollJob, backoffDelay);
      }
    };

    // Start polling (WebSocket + polling provides redundancy)
    pollJob();

    return {
      disconnect: () => {
        if (wsMonitor) wsMonitor.disconnect();
      }
    };
  }

  // Batch monitoring for multiple jobs
  async monitorMultipleJobs(jobIds, onProgress) {
    const monitors = new Map();
    
    // Create monitors for all jobs
    for (const jobId of jobIds) {
      const monitor = await this.monitorJobOptimized(jobId, {
        onProgress: (data) => onProgress(jobId, data),
        enableWebSocket: false // Disable WebSocket for batch monitoring to avoid connection limits
      });
      monitors.set(jobId, monitor);
    }
    
    return {
      disconnectAll: () => {
        for (const monitor of monitors.values()) {
          monitor.disconnect();
        }
      }
    };
  }
}

// Usage with best practices
async function monitorWithBestPractices() {
  const client = new BulkOperationsClient('your-api-key', BASE_URL);
  const monitor = new OptimizedJobMonitor(client);

  const jobId = 'job_01HABCDEF0123456789';

  const monitorSession = await monitor.monitorJobOptimized(jobId, {
    onProgress: (data) => {
      // 7. Efficient progress updates
      if (data.percent_complete % 10 === 0) {
        console.log(`Milestone: ${data.percent_complete}% complete`);
      }
      
      // 8. Monitor rate limiting
      if (data.rate_limited) {
        console.log('⚠️  Rate limited - consider reducing batch size');
      }
      
      // 9. ETA warnings
      if (data.eta_ms && data.eta_ms > 3600000) {
        console.warn(`Long processing time: ${Math.round(data.eta_ms / 3600000)} hours remaining`);
      }
    },
    
    onStateChange: (data) => {
      console.log(`State change: ${data.prior_state} → ${data.new_state}`);
      
      if (data.new_state === 'paused') {
        console.log('Job paused - may need manual intervention');
      }
    },
    
    onVideoComplete: (data) => {
      // 10. Process completed videos efficiently
      if (data.artifacts) {
        const videoArtifacts = data.artifacts.filter(a => a.type === 'video');
        videoArtifacts.forEach(artifact => {
          console.log(`Video ready: ${artifact.url}`);
          // Initiate download or further processing here
        });
      }
    },
    
    onError: (error) => {
      console.error('Job monitoring error:', error);
    }
  });

  return monitorSession;
}
```

## Troubleshooting

### Common Issues and Solutions

```javascript
class TroubleshootingGuide {
  
  static diagnoseJobCreationError(error) {
    const diagnosis = {
      error: error,
      commonCauses: [],
      solutions: [],
      escalation: false
    };

    switch (error.code) {
      case 'validation_error':
        diagnosis.commonCauses.push(
          'Invalid Google Sheets ID format',
          'Sheet range syntax error (use A1:Z100 format)',
          'Template ID not found',
          'Missing required configuration fields'
        );
        diagnosis.solutions.push(
          'Verify Google Sheets ID is correct (44-character string)',
          'Check range format: start_cell:end_cell (e.g., A1:Z100)',
          'Confirm template ID exists in your account',
          'Review job configuration against API specification'
        );
        break;

      case 'forbidden':
        diagnosis.commonCauses.push(
          'Insufficient API permissions',
          'Service account lacks sheet access',
          'Tenant ID mismatch'
        );
        diagnosis.solutions.push(
          'Check API key has required scopes (jobs:write, sheets:connect)',
          'Verify service account has read access to Google Sheet',
          'Ensure API key belongs to correct tenant'
        );
        break;

      case 'rate_limited':
        diagnosis.commonCauses.push(
          'Exceeding per-tenant request limits',
          'Too many concurrent job creation requests',
          'Burst capacity exceeded'
        );
        diagnosis.solutions.push(
          'Implement exponential backoff retry logic',
          'Reduce request frequency (max 10 RPS)',
          'Use idempotency keys to avoid duplicate requests',
          'Consider upgrading rate limit tier'
        );
        break;

      case 'idempotency_conflict':
        diagnosis.commonCauses.push(
          'Duplicate idempotency key for different requests',
          'Key reuse across different tenants',
          'Key过期 (expired after 24 hours)'
        );
        diagnosis.solutions.push(
          'Use unique idempotency keys per request',
          'Generate keys with timestamp and randomness',
          'Ensure keys are tenant-specific',
          'Refresh keys if older than 24 hours'
        );
        break;
    }

    // Determine if escalation is needed
    diagnosis.escalation = [
      'internal_error',
      'service_unavailable',
      'gateway_timeout'
    ].includes(error.code);

    return diagnosis;
  }

  static async troubleshootJobStuck(jobId, client) {
    console.log(`Troubleshooting stuck job: ${jobId}`);
    
    try {
      // 1. Get current job state
      const job = await client.getJob(jobId);
      console.log(`Current state: ${job.state}`);
      console.log(`Progress: ${job.percent_complete}%`);
      console.log(`Last updated: ${job.updated_at}`);
      
      // 2. Check for common issues
      const ageMinutes = (Date.now() - new Date(job.updated_at).getTime()) / 60000;
      
      if (ageMinutes > 60 && job.state === 'pending') {
        console.warn('Job stuck in pending state for over 1 hour');
        return {
          issue: 'Stuck in pending state',
          recommendation: 'Contact support - possible queue issue',
          action: 'escalate'
        };
      }
      
      if (job.rate_limited) {
        console.warn('Job is rate limited');
        return {
          issue: 'Rate limited',
          recommendation: 'Wait for rate limit reset or reduce batch size',
          action: 'wait'
        };
      }
      
      if (ageMinutes > 120 && job.state === 'running' && job.percent_complete === 0) {
        console.warn('Job not processing after 2 hours');
        return {
          issue: 'No processing progress',
          recommendation: 'Cancel and recreate with smaller batch',
          action: 'recreate'
        };
      }
      
      // 3. Get video details for more insight
      const videos = await client.getJobVideos(jobId, { 
        state: 'failed', 
        page_size: 10 
      });
      
      if (videos.data.length > 0) {
        console.log(`${videos.data.length} failed videos found`);
        const errorTypes = videos.data.flatMap(v => v.errors.map(e => e.error_code));
        const commonError = this.findMostCommonError(errorTypes);
        
        return {
          issue: `Common video errors: ${commonError.code}`,
          details: commonError.details,
          recommendation: this.getRecommendationForError(commonError.code),
          action: 'fix_and_retry'
        };
      }
      
      return {
        issue: 'No obvious issues detected',
        recommendation: 'Monitor for a bit longer',
        action: 'continue'
      };
      
    } catch (error) {
      console.error('Troubleshooting failed:', error);
      return {
        issue: 'Unable to diagnose',
        error: error.message,
        action: 'escalate'
      };
    }
  }

  static findMostCommonError(errorCodes) {
    const counts = {};
    errorCodes.forEach(code => counts[code] = (counts[code] || 0) + 1);
    
    const mostCommon = Object.entries(counts)
      .sort(([,a], [,b]) => b - a)[0];
    
    return {
      code: mostCommon[0],
      count: mostCommon[1],
      details: this.getErrorDetails(mostCommon[0])
    };
  }

  static getErrorDetails(errorCode) {
    const errorDetails = {
      'asset_download_failed': 'Cannot download required assets (images, videos)',
      'template_render_error': 'Template rendering failed - check template configuration',
      'audio_generation_failed': 'Text-to-speech generation failed',
      'video_encoding_error': 'Video encoding failed - may be format compatibility issue',
      'storage_upload_failed': 'Failed to upload to storage bucket',
      'quota_exceeded': 'Storage or processing quota exceeded'
    };
    
    return errorDetails[errorCode] || 'Unknown error type';
  }

  static getRecommendationForError(errorCode) {
    const recommendations = {
      'asset_download_failed': 'Check asset URLs are accessible and valid',
      'template_render_error': 'Verify template exists and has required parameters',
      'audio_generation_failed': 'Check text content for special characters',
      'video_encoding_error': 'Try different output format or resolution',
      'storage_upload_failed': 'Verify storage bucket permissions and space',
      'quota_exceeded': 'Clear old files or upgrade quota'
    };
    
    return recommendations[errorCode] || 'Review error logs for specific details';
  }
}

// Usage example
async function handleJobIssues() {
  const client = new BulkOperationsClient('your-api-key', BASE_URL);
  const jobId = 'job_01HABCDEF0123456789';
  
  try {
    const job = await client.getJob(jobId);
    
    if (['failed', 'canceled'].includes(job.state)) {
      const diagnosis = TroubleshootingGuide.diagnoseJobCreationError(job.last_error);
      console.log('Job issue diagnosis:', diagnosis);
      
      if (diagnosis.escalation) {
        console.log('This issue requires support escalation');
        // Send to support team
      }
    }
    
    // Check for stuck job
    const troubleshooting = await TroubleshootingGuide.troubleshootJobStuck(jobId, client);
    console.log('Troubleshooting result:', troubleshooting);
    
    switch (troubleshooting.action) {
      case 'escalate':
        // Send to support with correlation ID
        break;
      case 'recreate':
        // Cancel and recreate with smaller batch
        break;
      case 'fix_and_retry':
        // Fix identified issues and retry
        break;
    }
    
  } catch (error) {
    console.error('Error handling failed:', error);
  }
}
```

### Python Troubleshooting

```python
import time
from collections import Counter
from datetime import datetime, timedelta

class TroubleshootingGuide:
    @staticmethod
    def diagnose_job_creation_error(error):
        diagnosis = {
            'error': error,
            'common_causes': [],
            'solutions': [],
            'escalation': False
        }
        
        error_code = error.get('code', '')
        
        if error_code == 'validation_error':
            diagnosis['common_causes'].extend([
                'Invalid Google Sheets ID format',
                'Sheet range syntax error (use A1:Z100 format)',
                'Template ID not found',
                'Missing required configuration fields'
            ])
            diagnosis['solutions'].extend([
                'Verify Google Sheets ID is correct (44-character string)',
                'Check range format: start_cell:end_cell (e.g., A1:Z100)',
                'Confirm template ID exists in your account',
                'Review job configuration against API specification'
            ])
        
        elif error_code == 'forbidden':
            diagnosis['common_causes'].extend([
                'Insufficient API permissions',
                'Service account lacks sheet access',
                'Tenant ID mismatch'
            ])
            diagnosis['solutions'].extend([
                'Check API key has required scopes (jobs:write, sheets:connect)',
                'Verify service account has read access to Google Sheet',
                'Ensure API key belongs to correct tenant'
            ])
        
        elif error_code == 'rate_limited':
            diagnosis['common_causes'].extend([
                'Exceeding per-tenant request limits',
                'Too many concurrent job creation requests',
                'Burst capacity exceeded'
            ])
            diagnosis['solutions'].extend([
                'Implement exponential backoff retry logic',
                'Reduce request frequency (max 10 RPS)',
                'Use idempotency keys to avoid duplicate requests',
                'Consider upgrading rate limit tier'
            ])
        
        # Determine escalation
        diagnosis['escalation'] = error_code in ['internal_error', 'service_unavailable', 'gateway_timeout']
        
        return diagnosis
    
    @staticmethod
    def troubleshoot_job_stuck(job_id, client):
        print(f'Troubleshooting stuck job: {job_id}')
        
        try:
            job = client.get_job(job_id)
            print(f'Current state: {job["state"]}')
            print(f'Progress: {job["percent_complete"]}%')
            print(f'Last updated: {job["updated_at"]}')
            
            # Check job age
            updated_time = datetime.fromisoformat(job['updated_at'].replace('Z', '+00:00'))
            age_minutes = (datetime.now(timezone.utc) - updated_time).total_seconds() / 60
            
            if age_minutes > 60 and job['state'] == 'pending':
                print('Job stuck in pending state for over 1 hour')
                return {
                    'issue': 'Stuck in pending state',
                    'recommendation': 'Contact support - possible queue issue',
                    'action': 'escalate'
                }
            
            if job.get('rate_limited', False):
                print('Job is rate limited')
                return {
                    'issue': 'Rate limited',
                    'recommendation': 'Wait for rate limit reset or reduce batch size',
                    'action': 'wait'
                }
            
            # Get video details
            videos = client.get_job_videos(job_id, {
                'state': 'failed',
                'page_size': 10
            })
            
            if videos['data']:
                print(f'{len(videos["data"])} failed videos found')
                error_codes = [error['error_code'] 
                              for video in videos['data'] 
                              for error in video.get('errors', [])]
                most_common = Counter(error_codes).most_common(1)[0]
                
                return {
                    'issue': f'Common video errors: {most_common[0]}',
                    'count': most_common[1],
                    'recommendation': TroubleshootingGuide.get_recommendation_for_error(most_common[0]),
                    'action': 'fix_and_retry'
                }
            
            return {
                'issue': 'No obvious issues detected',
                'recommendation': 'Monitor for a bit longer',
                'action': 'continue'
            }
            
        except Exception as e:
            print(f'Troubleshooting failed: {e}')
            return {
                'issue': 'Unable to diagnose',
                'error': str(e),
                'action': 'escalate'
            }
    
    @staticmethod
    def get_recommendation_for_error(error_code):
        recommendations = {
            'asset_download_failed': 'Check asset URLs are accessible and valid',
            'template_render_error': 'Verify template exists and has required parameters',
            'audio_generation_failed': 'Check text content for special characters',
            'video_encoding_error': 'Try different output format or resolution',
            'storage_upload_failed': 'Verify storage bucket permissions and space',
            'quota_exceeded': 'Clear old files or upgrade quota'
        }
        return recommendations.get(error_code, 'Review error logs for specific details')
```

This comprehensive guide provides practical examples, real-world scenarios, and detailed code samples for working with the Bulk Operations API. The examples cover everything from basic job creation to advanced error handling and troubleshooting patterns, making it easier for developers to integrate and use the API effectively.
