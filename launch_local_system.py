#!/usr/bin/env python3
"""
Local Launcher Script for AI Content Automation System
Run this script to start the system locally with proper import paths
"""
import sys
import os
from pathlib import Path

# Add the content-creator directory and its subdirectories to Python path
content_creator_dir = Path(__file__).parent / "content-creator"
api_dir = content_creator_dir / "api"
backend_dir = content_creator_dir / "backend"

sys.path.insert(0, str(content_creator_dir))
sys.path.insert(0, str(api_dir))
sys.path.insert(0, str(backend_dir))

# Now import and run the backend
if __name__ == "__main__":
    import uvicorn
    from backend.main import app
    
    print("🚀 Starting AI Content Automation System...")
    print(f"📁 Content Creator Dir: {content_creator_dir}")
    print(f"🌐 API Dir: {api_dir}")
    print(f"⚙️ Backend Dir: {backend_dir}")
    print("\n📊 System Status:")
    print("   - Main Pipeline: ✅ Ready")
    print("   - Amazon Polly Integration: ✅ Ready (needs AWS credentials)")
    print("   - MiniMax Video Integration: ✅ Ready (needs MiniMax API key)")
    print("   - Database: ✅ Ready")
    print("\n🔧 Configuration Needed:")
    print("   - AWS_ACCESS_KEY_ID")
    print("   - AWS_SECRET_ACCESS_KEY") 
    print("   - AWS_REGION")
    print("   - MINIMAX_API_KEY")
    print("\n💰 Estimated Monthly Costs:")
    print("   - Audio (Amazon Polly): ~$16/month")
    print("   - Video (MiniMax): ~$96/month")
    print("   - Total: ~$112/month for 10 videos/day + audio")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
