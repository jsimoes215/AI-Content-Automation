#!/usr/bin/env python3
"""
Test script for Scheduling Optimization API
Demonstrates the complete workflow: recommendations → create schedule → monitor → optimize
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
import aiohttp
import websockets
import uuid

class SchedulingAPITester:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.headers = {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json"
        }
    
    async def test_recommendations(self):
        """Test getting scheduling recommendations"""
        print("\n=== Testing GET /scheduling/recommendations ===")
        
        url = f"{self.base_url}/scheduling/recommendations"
        params = {
            "platforms": ["youtube", "tiktok"],
            "target_count": 5,
            "timezone": "America/New_York"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Successfully retrieved recommendations:")
                    for rec in data["data"]:
                        print(f"  - {rec['platforms'][0]}: {rec['window_start']} ({rec['score']:.2f})")
                    return data
                else:
                    print(f"❌ Failed with status {response.status}")
                    text = await response.text()
                    print(f"Error: {text}")
                    return None
    
    async def test_create_schedule(self, recommendations_data):
        """Test creating a schedule"""
        print("\n=== Testing POST /scheduling/calendar ===")
        
        url = f"{self.base_url}/scheduling/calendar"
        
        # Use recommendations to create schedule items
        schedule_items = []
        for i, rec in enumerate(recommendations_data["data"][:3]):  # Take first 3 recommendations
            schedule_items.append({
                "content_id": f"content_{uuid.uuid4().hex[:8]}",
                "platform": rec["platforms"][0],
                "scheduled_time": rec["window_start"],
                "metadata": {
                    "campaign_id": f"camp_{uuid.uuid4().hex[:8]}",
                    "format": "video",
                    "priority": "high" if i == 0 else "normal"
                },
                "callbacks": {
                    "on_published": "https://client.example.com/webhooks/published"
                } if i == 0 else None
            })
        
        request_data = {
            "title": f"Test Schedule {datetime.now().strftime('%Y%m%d_%H%M')}",
            "timezone": "America/New_York",
            "items": schedule_items,
            "processing_deadline_ms": 3600000  # 1 hour
        }
        
        idempotency_key = str(uuid.uuid4())
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, 
                headers=self.headers | {"Idempotency-Key": idempotency_key},
                json=request_data
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    print("✅ Successfully created schedule:")
                    print(f"  Schedule ID: {data['id']}")
                    print(f"  Title: {data['title']}")
                    print(f"  Items: {data['items_total']}")
                    print(f"  State: {data['state']}")
                    return data
                else:
                    print(f"❌ Failed with status {response.status}")
                    text = await response.text()
                    print(f"Error: {text}")
                    return None
    
    async def test_get_schedule(self, schedule_data):
        """Test getting schedule details"""
        print("\n=== Testing GET /scheduling/calendar/{id} ===")
        
        schedule_id = schedule_data["id"]
        url = f"{self.base_url}/scheduling/calendar/{schedule_id}"
        params = {"expand": "items", "page_size": 10}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Successfully retrieved schedule details:")
                    print(f"  State: {data['state']}")
                    print(f"  Progress: {data['percent_complete']:.1f}%")
                    print(f"  Items: {data['items_total']}")
                    if data.get('items'):
                        for item in data['items']:
                            print(f"    - {item['platform']}: {item['state']} at {item['scheduled_time']}")
                    return data
                else:
                    print(f"❌ Failed with status {response.status}")
                    text = await response.text()
                    print(f"Error: {text}")
                    return None
    
    async def test_optimize_schedule(self, schedule_data):
        """Test schedule optimization"""
        print("\n=== Testing POST /scheduling/optimize ===")
        
        url = f"{self.base_url}/scheduling/optimize"
        schedule_id = schedule_data["id"]
        
        # Get current schedule items to optimize
        items = schedule_data.get('items', [])
        if not items:
            # If no items in response, fetch them
            schedule_details = await self.test_get_schedule(schedule_data)
            items = schedule_details.get('items', [])
        
        if not items:
            print("⚠️ No items to optimize")
            return None
        
        targets = []
        for item in items[:2]:  # Optimize first 2 items
            targets.append({
                "content_id": item["content_id"],
                "platform": item["platform"],
                "current_scheduled_time": item["scheduled_time"]
            })
        
        request_data = {
            "schedule_id": schedule_id,
            "targets": targets,
            "constraints": {
                "do_not_move_before": (datetime.now() + timedelta(hours=1)).isoformat(),
                "do_not_move_after": (datetime.now() + timedelta(days=7)).isoformat()
            },
            "apply": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=request_data) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Successfully optimized schedule:")
                    print(f"  Optimization ID: {data['id']}")
                    print(f"  Changes: {data['metrics']['changed_count']}/{data['metrics']['total_targeted']}")
                    print(f"  Score lift: {data['metrics']['average_score_lift']:.2f}")
                    for change in data['changes']:
                        print(f"    - {change['platform']}: {change['previous_time']} → {change['new_time']}")
                    return data
                else:
                    print(f"❌ Failed with status {response.status}")
                    text = await response.text()
                    print(f"Error: {text}")
                    return None
    
    async def test_websocket(self, schedule_id):
        """Test WebSocket connection for real-time updates"""
        print(f"\n=== Testing WebSocket /scheduling/ws (Schedule: {schedule_id}) ===")
        
        ws_url = f"ws://localhost:8000/api/v1/scheduling/ws?schedule_id={schedule_id}"
        
        try:
            async with websockets.connect(ws_url) as websocket:
                print("✅ WebSocket connected")
                
                # Send ping
                await websocket.send(json.dumps({"type": "ping"}))
                response = await websocket.recv()
                print(f"  Received: {response}")
                
                # Subscribe to updates (if supported)
                await websocket.send(json.dumps({"type": "subscribe", "schedule_id": schedule_id}))
                
                # Listen for updates for 5 seconds
                print("  Listening for updates...")
                start_time = time.time()
                while time.time() - start_time < 5:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        print(f"  📡 Update: {data.get('type', 'unknown')}")
                    except asyncio.TimeoutError:
                        continue
                
                print("  WebSocket test completed")
                
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
    
    async def test_health_and_platforms(self):
        """Test utility endpoints"""
        print("\n=== Testing utility endpoints ===")
        
        # Test health endpoint
        health_url = f"{self.base_url}/scheduling/health"
        async with aiohttp.ClientSession() as session:
            async with session.get(health_url) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check: {data['status']}")
                else:
                    print("❌ Health check failed")
        
        # Test platforms endpoint
        platforms_url = f"{self.base_url}/scheduling/platforms"
        async with aiohttp.ClientSession() as session:
            async with session.get(platforms_url) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Supported platforms: {len(data['data'])}")
                    for platform in data['data']:
                        print(f"  - {platform['name']} ({platform['id']})")
                else:
                    print("❌ Platforms endpoint failed")
    
    async def run_complete_workflow(self):
        """Run the complete scheduling workflow"""
        print("🚀 Starting Scheduling API Test Workflow")
        print("=" * 50)
        
        try:
            # Test utility endpoints first
            await self.test_health_and_platforms()
            
            # Step 1: Get recommendations
            recommendations = await self.test_recommendations()
            if not recommendations:
                print("❌ Cannot proceed without recommendations")
                return
            
            # Step 2: Create schedule
            schedule = await self.test_create_schedule(recommendations)
            if not schedule:
                print("❌ Cannot proceed without schedule")
                return
            
            # Step 3: Get schedule details
            await asyncio.sleep(1)  # Small delay
            schedule_details = await self.test_get_schedule(schedule)
            
            # Step 4: Test WebSocket
            await self.test_websocket(schedule['id'])
            
            # Step 5: Optimize schedule
            await asyncio.sleep(1)  # Small delay
            optimization = await self.test_optimize_schedule(schedule)
            
            print("\n" + "=" * 50)
            print("🎉 Workflow completed successfully!")
            print(f"   Schedule ID: {schedule['id']}")
            if optimization:
                print(f"   Optimization ID: {optimization['id']}")
            
        except Exception as e:
            print(f"\n❌ Workflow failed with error: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Main test function"""
    print("Scheduling Optimization API Test Suite")
    print("=" * 40)
    
    # Check if server is running
    print("Checking if scheduling API server is running...")
    tester = SchedulingAPITester()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{tester.base_url}/scheduling/health") as response:
                if response.status == 200:
                    print("✅ Server is running")
                else:
                    print("❌ Server is not responding correctly")
                    return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please ensure the FastAPI server is running with:")
        print("  cd /workspace/content-creator/backend")
        print("  python main.py")
        return
    
    # Run the complete workflow
    await tester.run_complete_workflow()

if __name__ == "__main__":
    # Install required packages if not available
    try:
        import aiohttp
        import websockets
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.run(["pip", "install", "aiohttp", "websockets"])
        import aiohttp
        import websockets
    
    # Run the tests
    asyncio.run(main())