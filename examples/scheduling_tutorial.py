#!/usr/bin/env python3
"""
AI Content Automation System - Scheduling Tutorial
==================================================

This tutorial demonstrates how to integrate with the AI Content Automation System's
scheduling API for backend applications. You'll learn how to:

1. Set up authentication and client initialization
2. Get optimal posting time recommendations
3. Create and manage content schedules
4. Monitor schedule progress and status
5. Handle errors and implement best practices

Prerequisites:
- Python 3.8+
- aiohttp for async HTTP requests
- pandas for data manipulation (optional)
- Access to the AI Content Automation API

Setup:
pip install aiohttp pandas asyncio
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass
from pathlib import Path
import aiohttp
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# TUTORIAL 1: Basic Setup and Authentication
# =============================================================================

class SchedulingTutorial:
    """Main tutorial class demonstrating scheduling API integration"""
    
    def __init__(self, api_base_url: str, api_key: str):
        """
        Initialize the scheduling client
        
        Args:
            api_base_url: Base URL of the scheduling API
            api_key: API authentication key
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        print(f"✅ Initialized scheduling client for {api_base_url}")
    
    async def test_connection(self) -> bool:
        """
        Test the API connection and authentication
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/health",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ API connection successful: {data.get('status', 'healthy')}")
                        return True
                    else:
                        print(f"❌ API connection failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

# =============================================================================
# TUTORIAL 2: Getting Recommendations
# =============================================================================

@dataclass
class Recommendation:
    """Data class for posting time recommendations"""
    platform: str
    recommended_time: str
    confidence_score: float
    reason: str
    audience_activity: str = ""
    estimated_engagement: float = 0.0

class RecommendationClient:
    """Client for getting optimal posting time recommendations"""
    
    def __init__(self, base_client: SchedulingTutorial):
        self.client = base_client
    
    async def get_platform_recommendations(
        self, 
        platforms: List[str], 
        target_count: int = 10,
        timezone_name: str = "America/New_York"
    ) -> List[Recommendation]:
        """
        Get optimal posting time recommendations for specified platforms
        
        Args:
            platforms: List of platforms (youtube, tiktok, instagram, linkedin, twitter)
            target_count: Number of recommendations to generate
            timezone_name: Target timezone for recommendations
            
        Returns:
            List of Recommendation objects
        """
        try:
            params = {
                "platforms": ",".join(platforms),
                "target_count": target_count,
                "timezone": timezone_name
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.client.api_base_url}/api/v1/scheduling/recommendations",
                    headers=self.client.headers,
                    params=params
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        recommendations = []
                        
                        for rec_data in data.get("data", []):
                            recommendation = Recommendation(
                                platform=rec_data.get("platform", ""),
                                recommended_time=rec_data.get("recommended_time", ""),
                                confidence_score=rec_data.get("confidence_score", 0.0),
                                reason=rec_data.get("reason", ""),
                                audience_activity=rec_data.get("audience_activity", ""),
                                estimated_engagement=rec_data.get("estimated_engagement", 0.0)
                            )
                            recommendations.append(recommendation)
                        
                        print(f"✅ Got {len(recommendations)} recommendations")
                        return recommendations
                    
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to get recommendations: {response.status} - {error_text}")
        
        except Exception as e:
            print(f"❌ Error getting recommendations: {e}")
            return []
    
    def print_recommendations(self, recommendations: List[Recommendation]):
        """Pretty print recommendations for analysis"""
        if not recommendations:
            print("No recommendations available")
            return
        
        print("\n" + "="*80)
        print("📊 OPTIMAL POSTING TIMES RECOMMENDATIONS")
        print("="*80)
        
        # Group by platform
        by_platform = {}
        for rec in recommendations:
            if rec.platform not in by_platform:
                by_platform[rec.platform] = []
            by_platform[rec.platform].append(rec)
        
        for platform, platform_recs in by_platform.items():
            print(f"\n🎯 {platform.upper()}")
            print("-" * 40)
            
            for i, rec in enumerate(platform_recs, 1):
                confidence_pct = rec.confidence_score * 100
                engagement_pct = rec.estimated_engagement * 100
                
                # Format datetime for better readability
                dt = datetime.fromisoformat(rec.recommended_time.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%a, %b %d %Y at %I:%M %p")
                
                print(f"  {i}. {formatted_time}")
                print(f"     Confidence: {confidence_pct:.1f}% | Est. Engagement: {engagement_pct:.1f}%")
                print(f"     Activity: {rec.audience_activity} | Reason: {rec.reason}")
                print()

# =============================================================================
# TUTORIAL 3: Creating Schedules
# =============================================================================

@dataclass
class ScheduleItem:
    """Individual scheduled content item"""
    content_id: str
    platform: str
    scheduled_time: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ContentSchedule:
    """Complete content schedule"""
    title: str
    timezone: str
    items: List[ScheduleItem]
    description: Optional[str] = None

class ScheduleManagementClient:
    """Client for creating and managing content schedules"""
    
    def __init__(self, base_client: SchedulingTutorial):
        self.client = base_client
    
    async def create_schedule(self, schedule: ContentSchedule) -> Optional[str]:
        """
        Create a new content schedule
        
        Args:
            schedule: ContentSchedule object with schedule details
            
        Returns:
            str: Schedule ID if successful, None otherwise
        """
        try:
            # Convert to API format
            schedule_data = {
                "title": schedule.title,
                "timezone": schedule.timezone,
                "description": schedule.description or ""
            }
            
            # Convert schedule items to API format
            items = []
            for item in schedule.items:
                item_data = {
                    "content_id": item.content_id,
                    "platform": item.platform,
                    "scheduled_time": item.scheduled_time,
                    "metadata": item.metadata or {}
                }
                items.append(item_data)
            
            schedule_data["items"] = items
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.client.api_base_url}/api/v1/scheduling/calendar",
                    headers=self.client.headers,
                    json=schedule_data
                ) as response:
                    
                    if response.status == 201:
                        result = await response.json()
                        schedule_id = result["data"]["id"]
                        print(f"✅ Schedule created successfully: {schedule_id}")
                        print(f"   Title: {schedule.title}")
                        print(f"   Items: {len(schedule.items)} content pieces")
                        return schedule_id
                    
                    else:
                        error_text = await response.text()
                        print(f"❌ Failed to create schedule: {response.status}")
                        print(f"   Error: {error_text}")
                        return None
        
        except Exception as e:
            print(f"❌ Error creating schedule: {e}")
            return None
    
    async def get_schedule_status(self, schedule_id: str) -> Optional[Dict]:
        """
        Get the status and details of a schedule
        
        Args:
            schedule_id: ID of the schedule to check
            
        Returns:
            Dict: Schedule details or None if not found
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.client.api_base_url}/api/v1/scheduling/calendar/{schedule_id}",
                    headers=self.client.headers
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        schedule_data = result["data"]
                        
                        # Extract key information
                        status = schedule_data.get("status", "unknown")
                        item_count = len(schedule_data.get("items", []))
                        created_at = schedule_data.get("created_at", "")
                        title = schedule_data.get("title", "Untitled")
                        
                        print(f"📋 Schedule Status: {title}")
                        print(f"   ID: {schedule_id}")
                        print(f"   Status: {status}")
                        print(f"   Items: {item_count}")
                        print(f"   Created: {created_at}")
                        
                        return schedule_data
                    
                    else:
                        print(f"❌ Schedule not found: {schedule_id}")
                        return None
        
        except Exception as e:
            print(f"❌ Error getting schedule status: {e}")
            return None
    
    async def list_schedules(
        self, 
        status: Optional[str] = None,
        limit: int = 50,
        platform: Optional[str] = None
    ) -> List[Dict]:
        """
        List schedules with optional filtering
        
        Args:
            status: Filter by status (pending, running, completed, failed)
            limit: Maximum number of schedules to return
            platform: Filter by platform
            
        Returns:
            List of schedule dictionaries
        """
        try:
            params = {}
            if status:
                params["status"] = status
            if limit:
                params["limit"] = limit
            if platform:
                params["platform"] = platform
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.client.api_base_url}/api/v1/scheduling/calendar",
                    headers=self.client.headers,
                    params=params
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        schedules = result.get("data", [])
                        
                        print(f"📋 Found {len(schedules)} schedules")
                        for schedule in schedules[:5]:  # Show first 5
                            print(f"   • {schedule.get('title', 'Untitled')} - {schedule.get('status', 'unknown')}")
                        
                        return schedules
                    
                    else:
                        print(f"❌ Failed to list schedules: {response.status}")
                        return []
        
        except Exception as e:
            print(f"❌ Error listing schedules: {e}")
            return []
    
    async def optimize_schedule(self, schedule_id: str) -> bool:
        """
        Optimize an existing schedule for better engagement
        
        Args:
            schedule_id: ID of schedule to optimize
            
        Returns:
            bool: True if optimization successful
        """
        try:
            optimization_data = {
                "schedule_id": schedule_id,
                "optimization_type": "engagement_maximization",
                "constraints": {
                    "keep_existing_platforms": True,
                    "respect_timezone": True,
                    "max_adjustment_hours": 2
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.client.api_base_url}/api/v1/scheduling/optimize",
                    headers=self.client.headers,
                    json=optimization_data
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Schedule optimized successfully")
                        print(f"   Original items: {result['data'].get('original_count', 0)}")
                        print(f"   Optimized items: {result['data'].get('optimized_count', 0)}")
                        print(f"   Expected improvement: {result['data'].get('expected_improvement', 'N/A')}")
                        return True
                    
                    else:
                        error_text = await response.text()
                        print(f"❌ Optimization failed: {response.status}")
                        print(f"   Error: {error_text}")
                        return False
        
        except Exception as e:
            print(f"❌ Error optimizing schedule: {e}")
            return False

# =============================================================================
# TUTORIAL 4: Real-time Progress Monitoring
# =============================================================================

class ProgressMonitor:
    """Real-time progress monitoring for schedule execution"""
    
    def __init__(self, base_client: SchedulingTutorial):
        self.client = base_client
        self.active_monitors = {}
    
    async def monitor_schedule_progress(
        self, 
        schedule_id: str, 
        callback: Optional[callable] = None,
        check_interval: int = 5
    ) -> Dict:
        """
        Monitor schedule progress in real-time
        
        Args:
            schedule_id: Schedule to monitor
            callback: Optional callback function for progress updates
            check_interval: Seconds between status checks
            
        Returns:
            Dict: Final status and metrics
        """
        print(f"🔍 Monitoring schedule progress: {schedule_id}")
        print(f"   Check interval: {check_interval} seconds")
        
        start_time = datetime.now()
        progress_history = []
        
        while True:
            try:
                # Get current status
                schedule_data = await self.client._get_schedule_details(schedule_id)
                
                if not schedule_data:
                    print(f"❌ Schedule not found: {schedule_id}")
                    break
                
                # Extract progress information
                status = schedule_data.get("status", "unknown")
                items = schedule_data.get("items", [])
                
                # Calculate progress metrics
                total_items = len(items)
                completed_items = sum(1 for item in items if item.get("status") == "published")
                failed_items = sum(1 for item in items if item.get("status") == "failed")
                pending_items = sum(1 for item in items if item.get("status") == "pending")
                
                progress_pct = (completed_items / total_items * 100) if total_items > 0 else 0
                
                # Record progress
                progress_snapshot = {
                    "timestamp": datetime.now().isoformat(),
                    "status": status,
                    "completed_items": completed_items,
                    "failed_items": failed_items,
                    "pending_items": pending_items,
                    "total_items": total_items,
                    "progress_percentage": progress_pct
                }
                progress_history.append(progress_snapshot)
                
                # Display progress
                elapsed_time = datetime.now() - start_time
                print(f"\r⏱️  Progress: {progress_pct:.1f}% | "
                      f"Completed: {completed_items}/{total_items} | "
                      f"Elapsed: {str(elapsed_time).split('.')[0]}", end="", flush=True)
                
                # Call optional callback
                if callback:
                    callback(progress_snapshot)
                
                # Check if schedule is complete
                if status in ["completed", "failed", "canceled"]:
                    print(f"\n✅ Monitoring complete. Final status: {status}")
                    break
                
                # Wait before next check
                await asyncio.sleep(check_interval)
            
            except Exception as e:
                print(f"\n❌ Error monitoring schedule: {e}")
                break
        
        # Return final summary
        final_snapshot = progress_history[-1] if progress_history else {}
        final_snapshot["total_monitoring_time"] = str(datetime.now() - start_time).split('.')[0]
        final_snapshot["progress_history"] = progress_history
        
        return final_snapshot
    
    async def batch_monitor_schedules(self, schedule_ids: List[str]) -> Dict[str, Dict]:
        """
        Monitor multiple schedules concurrently
        
        Args:
            schedule_ids: List of schedule IDs to monitor
            
        Returns:
            Dict: Final status for each schedule
        """
        print(f"🔍 Monitoring {len(schedule_ids)} schedules concurrently")
        
        # Create monitoring tasks
        monitor_tasks = []
        for schedule_id in schedule_ids:
            task = asyncio.create_task(
                self.monitor_schedule_progress(schedule_id, check_interval=10)
            )
            monitor_tasks.append((schedule_id, task))
        
        # Wait for all to complete
        results = {}
        for schedule_id, task in monitor_tasks:
            try:
                result = await task
                results[schedule_id] = result
                print(f"✅ {schedule_id}: {result.get('status', 'unknown')}")
            except Exception as e:
                results[schedule_id] = {"error": str(e)}
                print(f"❌ {schedule_id}: Error - {e}")
        
        return results

# =============================================================================
# TUTORIAL 5: Working with Google Sheets Data
# =============================================================================

class SheetsIntegrationClient:
    """Client for integrating with Google Sheets data"""
    
    def __init__(self, base_client: SchedulingTutorial):
        self.client = base_client
    
    def import_sheets_data(self, file_path: str) -> pd.DataFrame:
        """
        Import content data from CSV file (simulating Google Sheets export)
        
        Args:
            file_path: Path to CSV file containing content data
            
        Returns:
            pd.DataFrame: Imported data
        """
        try:
            df = pd.read_csv(file_path)
            print(f"✅ Imported {len(df)} rows from {file_path}")
            print(f"   Columns: {', '.join(df.columns.tolist())}")
            
            # Display first few rows
            print("\n📊 First 3 rows:")
            print(df.head(3).to_string(index=False))
            
            return df
        
        except Exception as e:
            print(f"❌ Error importing sheets data: {e}")
            return pd.DataFrame()
    
    async def create_schedule_from_sheets(
        self, 
        df: pd.DataFrame,
        schedule_title: str,
        timezone: str = "America/New_York"
    ) -> List[str]:
        """
        Create schedules from imported sheets data
        
        Args:
            df: DataFrame containing content data
            schedule_title: Title for the schedule
            timezone: Target timezone
            
        Returns:
            List[str]: Created schedule IDs
        """
        print(f"📝 Creating schedules from {len(df)} rows of data")
        
        created_schedules = []
        
        # Group data by platform for efficient processing
        platforms = df['platform'].unique() if 'platform' in df.columns else []
        
        for platform in platforms:
            platform_data = df[df['platform'] == platform]
            print(f"\n🎯 Processing {len(platform_data)} items for {platform}")
            
            # Create schedule items for this platform
            schedule_items = []
            for idx, row in platform_data.iterrows():
                # Parse scheduled time (handle various formats)
                scheduled_time = self._parse_datetime(row.get('scheduled_time', ''))
                
                if scheduled_time:
                    item = ScheduleItem(
                        content_id=f"sheets_{idx}_{platform}",
                        platform=platform,
                        scheduled_time=scheduled_time,
                        metadata={
                            "title": row.get('title', ''),
                            "content": row.get('content', ''),
                            "target_audience": row.get('target_audience', ''),
                            "tone": row.get('tone', 'professional'),
                            "source": "google_sheets"
                        }
                    )
                    schedule_items.append(item)
            
            # Create schedule for this platform
            if schedule_items:
                schedule = ContentSchedule(
                    title=f"{schedule_title} - {platform.title()}",
                    timezone=timezone,
                    items=schedule_items,
                    description=f"Auto-generated from Google Sheets data"
                )
                
                # Add to batch processing
                schedule_id = await self._create_schedule_batch(schedule)
                if schedule_id:
                    created_schedules.append(schedule_id)
        
        return created_schedules
    
    def _parse_datetime(self, time_str: str) -> Optional[str]:
        """Parse datetime string from various formats"""
        if not time_str:
            return None
        
        # Common formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%m/%d/%Y %H:%M",
            "%m/%d/%Y %H:%M %p",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(time_str.strip(), fmt)
                return dt.isoformat() + "Z"
            except ValueError:
                continue
        
        # If no format matches, try pandas parser
        try:
            dt = pd.to_datetime(time_str)
            return dt.isoformat() + "Z"
        except:
            return None
    
    async def _create_schedule_batch(self, schedule: ContentSchedule) -> Optional[str]:
        """Create a schedule (internal method)"""
        try:
            # This would use the actual API call
            # For tutorial purposes, simulating with a placeholder
            schedule_id = f"sched_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"   ✅ Created schedule: {schedule_id} with {len(schedule.items)} items")
            return schedule_id
        
        except Exception as e:
            print(f"   ❌ Failed to create schedule: {e}")
            return None
    
    async def export_schedule_to_sheets(self, schedule_ids: List[str], output_file: str):
        """
        Export schedule results back to CSV file
        
        Args:
            schedule_ids: Schedule IDs to export
            output_file: Output CSV file path
        """
        print(f"📤 Exporting {len(schedule_ids)} schedules to {output_file}")
        
        export_data = []
        
        for schedule_id in schedule_ids:
            # Get schedule details
            schedule_data = await self.client._get_schedule_details(schedule_id)
            
            if schedule_data:
                for item in schedule_data.get('items', []):
                    export_row = {
                        'schedule_id': schedule_id,
                        'schedule_title': schedule_data.get('title', ''),
                        'content_id': item.get('content_id', ''),
                        'platform': item.get('platform', ''),
                        'scheduled_time': item.get('scheduled_time', ''),
                        'status': item.get('status', ''),
                        'metadata_title': item.get('metadata', {}).get('title', ''),
                        'created_at': schedule_data.get('created_at', ''),
                        'exported_at': datetime.now().isoformat()
                    }
                    export_data.append(export_row)
        
        if export_data:
            # Save to CSV
            df_export = pd.DataFrame(export_data)
            df_export.to_csv(output_file, index=False)
            print(f"✅ Exported {len(export_data)} records to {output_file}")
            
            # Display summary
            print(f"📊 Export summary:")
            print(f"   Total records: {len(export_data)}")
            print(f"   Platforms: {', '.join(df_export['platform'].unique())}")
            print(f"   Status breakdown: {dict(df_export['status'].value_counts())}")
        else:
            print("❌ No data to export")

# =============================================================================
# TUTORIAL 6: Best Practices and Error Handling
# =============================================================================

class RobustSchedulingClient:
    """Advanced client with comprehensive error handling and best practices"""
    
    def __init__(self, api_base_url: str, api_key: str, max_retries: int = 3):
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.max_retries = max_retries
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.rate_limit_remaining = float('inf')
        self.rate_limit_reset = 0
    
    async def create_schedule_with_retry(
        self, 
        schedule: ContentSchedule,
        retry_delay: float = 1.0
    ) -> Optional[str]:
        """
        Create schedule with retry logic and rate limiting
        
        Args:
            schedule: Schedule to create
            retry_delay: Initial delay between retries (exponential backoff)
            
        Returns:
            str: Schedule ID if successful
        """
        
        for attempt in range(self.max_retries + 1):
            try:
                # Check rate limits
                if self.rate_limit_remaining <= 0:
                    wait_time = max(0, self.rate_limit_reset - time.time())
                    if wait_time > 0:
                        print(f"⏳ Rate limited. Waiting {wait_time:.1f} seconds...")
                        await asyncio.sleep(wait_time)
                
                # Convert schedule to API format
                schedule_data = {
                    "title": schedule.title,
                    "timezone": schedule.timezone,
                    "description": schedule.description or ""
                }
                
                items = []
                for item in schedule.items:
                    items.append({
                        "content_id": item.content_id,
                        "platform": item.platform,
                        "scheduled_time": item.scheduled_time,
                        "metadata": item.metadata or {}
                    })
                
                schedule_data["items"] = items
                
                # Make API request with timeout
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as session:
                    async with session.post(
                        f"{self.api_base_url}/api/v1/scheduling/calendar",
                        headers=self.headers,
                        json=schedule_data
                    ) as response:
                        
                        # Update rate limit info
                        if 'X-RateLimit-Remaining' in response.headers:
                            self.rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
                        if 'X-RateLimit-Reset' in response.headers:
                            self.rate_limit_reset = int(response.headers['X-RateLimit-Reset'])
                        
                        if response.status == 429:  # Rate limited
                            retry_after = int(response.headers.get('Retry-After', 60))
                            print(f"⏳ Rate limited. Retrying after {retry_after} seconds...")
                            await asyncio.sleep(retry_after)
                            continue
                        
                        if response.status >= 400:
                            error_text = await response.text()
                            raise Exception(f"API Error {response.status}: {error_text}")
                        
                        if response.status == 201:
                            result = await response.json()
                            schedule_id = result["data"]["id"]
                            print(f"✅ Schedule created successfully: {schedule_id}")
                            return schedule_id
                        
                        # Unexpected status code
                        error_text = await response.text()
                        raise Exception(f"Unexpected status {response.status}: {error_text}")
            
            except asyncio.TimeoutError:
                print(f"⏰ Request timeout on attempt {attempt + 1}")
            
            except aiohttp.ClientError as e:
                print(f"🌐 Network error on attempt {attempt + 1}: {e}")
            
            except Exception as e:
                print(f"❌ Error on attempt {attempt + 1}: {e}")
            
            # If not the last attempt, wait before retry
            if attempt < self.max_retries:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                print(f"🔄 Retrying in {wait_time:.1f} seconds...")
                await asyncio.sleep(wait_time)
        
        print(f"❌ Failed to create schedule after {self.max_retries + 1} attempts")
        return None
    
    async def batch_create_schedules(
        self, 
        schedules: List[ContentSchedule],
        batch_size: int = 5
    ) -> List[str]:
        """
        Create multiple schedules in batches to avoid overwhelming the API
        
        Args:
            schedules: List of schedules to create
            batch_size: Number of schedules to process concurrently per batch
            
        Returns:
            List[str]: Created schedule IDs
        """
        print(f"📦 Creating {len(schedules)} schedules in batches of {batch_size}")
        
        created_ids = []
        
        # Process in batches
        for i in range(0, len(schedules), batch_size):
            batch = schedules[i:i + batch_size]
            print(f"🔄 Processing batch {i//batch_size + 1}/{(len(schedules) + batch_size - 1)//batch_size}")
            
            # Create tasks for concurrent processing
            tasks = []
            for schedule in batch:
                task = asyncio.create_task(
                    self.create_schedule_with_retry(schedule)
                )
                tasks.append(task)
            
            # Execute batch with concurrency control
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    print(f"❌ Batch item failed: {result}")
                elif result:
                    created_ids.append(result)
            
            # Add delay between batches to respect rate limits
            if i + batch_size < len(schedules):
                print(f"⏳ Waiting 2 seconds before next batch...")
                await asyncio.sleep(2)
        
        print(f"✅ Successfully created {len(created_ids)}/{len(schedules)} schedules")
        return created_ids
    
    async def health_check(self) -> Dict:
        """
        Perform comprehensive health check
        
        Returns:
            Dict: Health check results
        """
        health_info = {
            "timestamp": datetime.now().isoformat(),
            "api_base_url": self.api_base_url,
            "tests": {}
        }
        
        try:
            # Test basic connectivity
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    health_info["tests"]["connectivity"] = {
                        "status": "pass" if response.status == 200 else "fail",
                        "response_code": response.status
                    }
        except Exception as e:
            health_info["tests"]["connectivity"] = {
                "status": "fail",
                "error": str(e)
            }
        
        try:
            # Test authentication
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/api/v1/scheduling/platforms",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    health_info["tests"]["authentication"] = {
                        "status": "pass" if response.status == 200 else "fail",
                        "response_code": response.status
                    }
        except Exception as e:
            health_info["tests"]["authentication"] = {
                "status": "fail",
                "error": str(e)
            }
        
        return health_info

# =============================================================================
# TUTORIAL 7: Complete Example Workflows
# =============================================================================

class TutorialWorkflows:
    """Complete example workflows demonstrating real-world usage"""
    
    def __init__(self, api_base_url: str, api_key: str):
        self.base_client = SchedulingTutorial(api_base_url, api_key)
        self.recommendation_client = RecommendationClient(self.base_client)
        self.schedule_client = ScheduleManagementClient(self.base_client)
        self.progress_monitor = ProgressMonitor(self.base_client)
        self.sheets_client = SheetsIntegrationClient(self.base_client)
        self.robust_client = RobustSchedulingClient(api_base_url, api_key)
    
    async def workflow_1_basic_schedule_creation(self):
        """
        Workflow 1: Basic schedule creation from recommendations
        """
        print("\n" + "="*80)
        print("🚀 WORKFLOW 1: Basic Schedule Creation")
        print("="*80)
        
        # Step 1: Test connection
        if not await self.base_client.test_connection():
            return False
        
        # Step 2: Get recommendations
        print("\n📊 Step 2: Getting posting time recommendations...")
        recommendations = await self.recommendation_client.get_platform_recommendations(
            platforms=["youtube", "linkedin", "twitter"],
            target_count=6
        )
        
        if not recommendations:
            print("❌ No recommendations available")
            return False
        
        # Step 3: Create schedule items from recommendations
        print("\n📅 Step 3: Creating schedule from recommendations...")
        schedule_items = []
        
        for rec in recommendations[:3]:  # Use first 3 recommendations
            item = ScheduleItem(
                content_id=f"tutorial_content_{rec.platform}",
                platform=rec.platform,
                scheduled_time=rec.recommended_time,
                metadata={
                    "tutorial_workflow": "workflow_1",
                    "confidence_score": rec.confidence_score,
                    "generated_from": "recommendations"
                }
            )
            schedule_items.append(item)
        
        # Step 4: Create the schedule
        schedule = ContentSchedule(
            title="Tutorial Schedule - Basic Creation",
            timezone="America/New_York",
            items=schedule_items,
            description="Created via tutorial workflow 1"
        )
        
        schedule_id = await self.schedule_client.create_schedule(schedule)
        
        if schedule_id:
            print(f"\n🎉 Schedule created successfully!")
            print(f"   Schedule ID: {schedule_id}")
            
            # Step 5: Monitor progress
            print("\n🔍 Step 5: Monitoring progress...")
            final_status = await self.progress_monitor.monitor_schedule_progress(
                schedule_id, 
                check_interval=3
            )
            
            print(f"\n📈 Final Status: {final_status.get('status', 'unknown')}")
            return True
        
        return False
    
    async def workflow_2_sheets_integration(self, csv_file: str):
        """
        Workflow 2: Import content from Google Sheets (CSV) and create schedules
        """
        print("\n" + "="*80)
        print("📊 WORKFLOW 2: Google Sheets Integration")
        print("="*80)
        
        # Step 1: Import data
        print(f"\n📥 Step 1: Importing data from {csv_file}...")
        df = self.sheets_client.import_sheets_data(csv_file)
        
        if df.empty:
            print("❌ No data imported")
            return False
        
        # Step 2: Validate required columns
        required_columns = ['title', 'content', 'platform', 'scheduled_time']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"❌ Missing required columns: {', '.join(missing_columns)}")
            return False
        
        # Step 3: Create schedules from data
        print("\n📅 Step 3: Creating schedules from sheets data...")
        schedule_ids = await self.sheets_client.create_schedule_from_sheets(
            df, 
            "Tutorial Sheets Integration",
            "America/New_York"
        )
        
        if not schedule_ids:
            print("❌ No schedules created")
            return False
        
        # Step 4: Monitor all schedules
        print("\n🔍 Step 4: Monitoring all schedules...")
        monitoring_results = await self.progress_monitor.batch_monitor_schedules(schedule_ids)
        
        # Step 5: Export results
        print("\n📤 Step 5: Exporting results...")
        output_file = f"tutorial_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        await self.sheets_client.export_schedule_to_sheets(schedule_ids, output_file)
        
        print(f"\n🎉 Sheets workflow completed!")
        print(f"   Created schedules: {len(schedule_ids)}")
        print(f"   Export file: {output_file}")
        
        return True
    
    async def workflow_3_robust_batch_processing(self):
        """
        Workflow 3: Robust batch processing with error handling
        """
        print("\n" + "="*80)
        print("🛡️  WORKFLOW 3: Robust Batch Processing")
        print("="*80)
        
        # Step 1: Health check
        print("\n🏥 Step 1: Performing health check...")
        health_result = await self.robust_client.health_check()
        
        print(f"📋 Health Check Results:")
        for test_name, result in health_result["tests"].items():
            status_icon = "✅" if result["status"] == "pass" else "❌"
            print(f"   {status_icon} {test_name}: {result['status']}")
        
        # Step 2: Create test schedules with potential issues
        print("\n📝 Step 2: Creating test schedules...")
        
        # Create schedules with various scenarios
        test_schedules = []
        
        # Valid schedule
        test_schedules.append(ContentSchedule(
            title="Valid Schedule Test",
            timezone="America/New_York",
            items=[
                ScheduleItem(
                    content_id="valid_content_1",
                    platform="youtube",
                    scheduled_time=(datetime.now() + timedelta(days=1)).isoformat() + "Z",
                    metadata={"test_type": "valid"}
                )
            ]
        ))
        
        # Schedule with multiple platforms
        test_schedules.append(ContentSchedule(
            title="Multi-Platform Test",
            timezone="America/New_York",
            items=[
                ScheduleItem(
                    content_id="multi_platform_1",
                    platform="linkedin",
                    scheduled_time=(datetime.now() + timedelta(days=2)).isoformat() + "Z",
                    metadata={"test_type": "multi_platform"}
                ),
                ScheduleItem(
                    content_id="multi_platform_2", 
                    platform="twitter",
                    scheduled_time=(datetime.now() + timedelta(days=2, hours=1)).isoformat() + "Z",
                    metadata={"test_type": "multi_platform"}
                )
            ]
        ))
        
        # Step 3: Batch create with retry logic
        print("\n📦 Step 3: Batch creating with retry logic...")
        created_ids = await self.robust_client.batch_create_schedules(
            test_schedules, 
            batch_size=2
        )
        
        print(f"\n✅ Successfully created {len(created_ids)} schedules")
        print(f"   Schedule IDs: {created_ids}")
        
        # Step 4: Final verification
        print("\n🔍 Step 4: Verifying created schedules...")
        for schedule_id in created_ids:
            status = await self.schedule_client.get_schedule_status(schedule_id)
            if status:
                print(f"   ✅ {schedule_id}: {status.get('status', 'unknown')}")
            else:
                print(f"   ❌ {schedule_id}: Not found")
        
        print("\n🎉 Robust workflow completed!")
        return len(created_ids) > 0

# =============================================================================
# MAIN TUTORIAL EXECUTION
# =============================================================================

async def run_complete_tutorial():
    """
    Run the complete tutorial with all workflows
    """
    print("="*80)
    print("🎓 AI CONTENT AUTOMATION SYSTEM - SCHEDULING TUTORIAL")
    print("="*80)
    print("\nThis tutorial will guide you through integrating with the")
    print("AI Content Automation System's scheduling API.")
    
    # Configuration
    API_BASE_URL = "http://localhost:8000"  # Change to your API URL
    API_KEY = "your-api-key-here"  # Change to your API key
    
    # Create workflows instance
    workflows = TutorialWorkflows(API_BASE_URL, API_KEY)
    
    try:
        # Run workflow 1: Basic schedule creation
        print("\n" + "🎯" * 40)
        success1 = await workflows.workflow_1_basic_schedule_creation()
        
        if success1:
            print("\n✅ Workflow 1 completed successfully!")
        else:
            print("\n❌ Workflow 1 failed")
        
        # Pause between workflows
        await asyncio.sleep(2)
        
        # Run workflow 3: Robust batch processing
        print("\n" + "🛡️" * 40)
        success3 = await workflows.workflow_3_robust_batch_processing()
        
        if success3:
            print("\n✅ Workflow 3 completed successfully!")
        else:
            print("\n❌ Workflow 3 failed")
        
        # Optional: Run workflow 2 if CSV file exists
        csv_file = "sample_content_data.csv"
        if Path(csv_file).exists():
            print("\n" + "📊" * 40)
            success2 = await workflows.workflow_2_sheets_integration(csv_file)
            
            if success2:
                print("\n✅ Workflow 2 completed successfully!")
            else:
                print("\n❌ Workflow 2 failed")
        else:
            print(f"\n📝 Skipping Workflow 2 - CSV file not found: {csv_file}")
        
        print("\n" + "="*80)
        print("🎊 TUTORIAL COMPLETED!")
        print("="*80)
        print("\n✅ Next steps:")
        print("1. Customize the tutorial for your specific use case")
        print("2. Implement error handling for your production environment")
        print("3. Set up monitoring and logging for your schedules")
        print("4. Integrate with your existing content creation pipeline")
        print("\n📚 For more examples, see:")
        print("   • examples/react_scheduling_example.tsx")
        print("   • examples/google_sheets_scheduling.py")
        print("   • docs/integration_examples.md")
        
    except Exception as e:
        print(f"\n❌ Tutorial failed with error: {e}")
        import traceback
        traceback.print_exc()

# =============================================================================
# HELPER FUNCTIONS FOR TUTORIAL
# =============================================================================

def create_sample_csv_data():
    """Create sample CSV data for testing the sheets workflow"""
    import csv
    
    sample_data = [
        ["title", "content", "platform", "scheduled_time", "target_audience", "tone"],
        ["AI Tutorial Part 1", "Introduction to AI concepts", "youtube", 
         "2025-11-10 15:00:00", "beginners", "educational"],
        ["Quick AI Tips", "5 AI tools to know", "linkedin", 
         "2025-11-11 09:00:00", "professionals", "concise"],
        ["AI News Update", "Latest AI developments", "twitter", 
         "2025-11-11 12:00:00", "tech enthusiasts", "informative"],
        ["AI Demo Video", "See AI in action", "youtube", 
         "2025-11-12 14:00:00", "visual learners", "demonstrative"],
        ["AI Career Advice", "Getting started in AI", "linkedin", 
         "2025-11-13 10:00:00", "career changers", "encouraging"]
    ]
    
    with open("sample_content_data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(sample_data)
    
    print("✅ Created sample CSV file: sample_content_data.csv")

# =============================================================================
# USAGE EXAMPLES
# =============================================================================

async def example_basic_usage():
    """Example: Basic usage of the scheduling API"""
    print("\n📝 Example 1: Basic Usage")
    
    # Initialize client
    client = SchedulingTutorial("http://localhost:8000", "your-api-key")
    
    # Test connection
    connected = await client.test_connection()
    if not connected:
        return
    
    # Get recommendations
    rec_client = RecommendationClient(client)
    recommendations = await rec_client.get_platform_recommendations(
        platforms=["youtube", "linkedin"],
        target_count=5
    )
    
    # Display recommendations
    rec_client.print_recommendations(recommendations)

async def example_creating_schedule():
    """Example: Creating a simple schedule"""
    print("\n📝 Example 2: Creating a Schedule")
    
    client = SchedulingTutorial("http://localhost:8000", "your-api-key")
    schedule_client = ScheduleManagementClient(client)
    
    # Create schedule items
    items = [
        ScheduleItem(
            content_id="video_001",
            platform="youtube",
            scheduled_time=(datetime.now() + timedelta(days=1)).isoformat() + "Z",
            metadata={"title": "My Tutorial Video", "description": "Learn AI basics"}
        ),
        ScheduleItem(
            content_id="post_001",
            platform="linkedin", 
            scheduled_time=(datetime.now() + timedelta(days=1, hours=2)).isoformat() + "Z",
            metadata={"title": "AI Career Tips", "type": "article"}
        )
    ]
    
    # Create schedule
    schedule = ContentSchedule(
        title="My Content Series",
        timezone="America/New_York",
        items=items,
        description="Weekly content series about AI"
    )
    
    schedule_id = await schedule_client.create_schedule(schedule)
    
    if schedule_id:
        # Monitor progress
        monitor = ProgressMonitor(client)
        result = await monitor.monitor_schedule_progress(schedule_id, check_interval=5)
        print(f"Final result: {result}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--sample-data":
            create_sample_csv_data()
        elif sys.argv[1] == "--basic-example":
            asyncio.run(example_basic_usage())
        elif sys.argv[1] == "--schedule-example":
            asyncio.run(example_creating_schedule())
        elif sys.argv[1] == "--full-tutorial":
            asyncio.run(run_complete_tutorial())
        else:
            print("Usage:")
            print("  python scheduling_tutorial.py --sample-data    # Create sample CSV")
            print("  python scheduling_tutorial.py --basic-example  # Run basic example")
            print("  python scheduling_tutorial.py --schedule-example # Run schedule example")
            print("  python scheduling_tutorial.py --full-tutorial  # Run complete tutorial")
    else:
        print("AI Content Automation System - Scheduling Tutorial")
        print("\nTo get started, run:")
        print("  python scheduling_tutorial.py --full-tutorial")
        print("\nOr create sample data:")
        print("  python scheduling_tutorial.py --sample-data")
