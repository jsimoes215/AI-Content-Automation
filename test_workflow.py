#!/usr/bin/env python3
"""Test the complete AI content generation workflow"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

print("=" * 80)
print("Testing AI Content Generation Workflow")
print("=" * 80)

# Test 1: Health check
print("\n1. Health Check...")
try:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.json()}")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: List projects
print("\n2. List Projects...")
try:
    r = requests.get(f"{BASE_URL}/api/projects", timeout=5)
    print(f"   Status: {r.status_code}")
    result = r.json()
    print(f"   Projects: {result.get('count', 0)}")
except Exception as e:
    print(f"   Error: {e}")

# Test 3: Create project
print("\n3. Create New Project...")
project_data = {
    "original_idea": "AI Agents Revolution 2025",
    "target_audience": "Tech enthusiasts",
    "tone": "professional"
}
try:
    r = requests.post(f"{BASE_URL}/api/projects", json=project_data, timeout=10)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        project_id = result['data']['id']
        print(f"   Project ID: {project_id}")
        
        # Test 4: Generate script
        print("\n4. Generate Script...")
        script_req = {
            "project_id": project_id,
            "target_duration": 60,
            "scene_count": 5
        }
        r2 = requests.post(f"{BASE_URL}/api/scripts/generate", json=script_req, timeout=30)
        print(f"   Status: {r2.status_code}")
        if r2.status_code == 200:
            result2 = r2.json()
            job_id = result2['data']['job_id']
            print(f"   Job ID: {job_id}")
            
            # Test 5: Monitor job
            print("\n5. Monitor Job Progress...")
            for i in range(10):
                time.sleep(3)
                r3 = requests.get(f"{BASE_URL}/api/jobs/{job_id}", timeout=5)
                if r3.status_code == 200:
                    job = r3.json()['data']
                    print(f"   [{i*3}s] {job['status']} - {job.get('progress', 0)}% - {job.get('current_stage', 'N/A')}")
                    if job['status'] in ['completed', 'failed', 'error']:
                        print(f"   Final status: {job['status']}")
                        if job.get('result'):
                            print(f"   Result keys: {list(job['result'].keys())}")
                        break
        else:
            print(f"   Error: {r2.text}")
    else:
        print(f"   Error: {r.text}")
except Exception as e:
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()

print("\nTest completed!")
