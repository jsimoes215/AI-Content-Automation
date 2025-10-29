import requests
import time

print("Quick API Test")
print("=" * 60)

# Create project
r = requests.post("http://localhost:8000/api/projects", json={
    "original_idea": "AI Content Test - 2025",
    "target_audience": "Developers",
    "tone": "professional"
})
print(f"Create project: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    project_id = data['data']['id']
    print(f"Project ID: {project_id}")
    
    # Generate script  
    r2 = requests.post("http://localhost:8000/api/scripts/generate", json={
        "project_id": project_id,
        "target_duration": 30,
        "scene_count": 3
    })
    print(f"Generate script: {r2.status_code}")
    if r2.status_code == 200:
        data2 = r2.json()
        job_id = data2['data']['job_id']
        script_id = data2['data'].get('script_id')
        print(f"Job ID: {job_id}")
        print(f"Script ID: {script_id}")
        
        # Monitor for 30 seconds
        for i in range(10):
            time.sleep(3)
            r3 = requests.get(f"http://localhost:8000/api/jobs/{job_id}")
            if r3.status_code == 200:
                job = r3.json()['data']
                print(f"[{i*3}s] Status:{job['status']} Progress:{job.get('progress',0)}% Stage:{job.get('current_stage', 'N/A')}")
                if job['status'] in ['completed', 'failed', 'error']:
                    print(f"\nFinal: {job['status']}")
                    if job.get('result'):
                        print(f"Result: {job['result']}")
                    break
    else:
        print(f"Error: {r2.text}")
else:
    print(f"Error: {r.text}")

print("\nDone!")
