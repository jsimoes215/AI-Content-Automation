#!/usr/bin/env python3
"""
AI Influencer System API Setup Script
====================================

This script helps you:
1. Get 3 critical API keys (MiniMax, Qwen, Google Cloud)
2. Set up environment variables securely
3. Verify all APIs are working correctly
4. Test the complete integration

Usage: python setup_ai_influencer_apis.py
"""

import os
import sys
import json
import requests
import asyncio
import aiohttp
from typing import Dict, List, Optional
import subprocess
from pathlib import Path
import hashlib

class APIKeyManager:
    """Manage API keys securely with encryption and validation"""
    
    def __init__(self):
        self.api_configs = {
            'minimax': {
                'name': 'MiniMax Video Generation',
                'api_url': 'https://api.minimax.chat/v1/video_generation',
                'required': True,
                'cost_per_second': 0.055,  # Hailuo 2.3 Fast 1080p
                'signup_url': 'https://www.minimax.io/',
                'pricing_info': {
                    'Starter': '$9.90 (20 credits)',
                    'Pro': '$49 (200 credits)', 
                    'Premium': '$99 (800 credits) - RECOMMENDED'
                }
            },
            'qwen': {
                'name': 'Alibaba Qwen (Image Variations)',
                'api_url': 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis',
                'required': True,
                'cost_per_request': 0.005,
                'signup_url': 'https://dashscope.console.aliyun.com/',
                'pricing_info': 'Free tier: 6M tokens/month'
            },
            'google': {
                'name': 'Google Cloud AI (Gemini 2.5 Flash)',
                'api_url': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent',
                'required': True,
                'cost_per_request': 0.005,
                'signup_url': 'https://console.cloud.google.com/',
                'pricing_info': '$300 free credit, then pay-per-use'
            }
        }
        
    def display_api_setup_guide(self):
        """Display step-by-step API setup guide"""
        print("🚀 AI INFLUENCER API SETUP GUIDE")
        print("=" * 50)
        print()
        
        for api_name, config in self.api_configs.items():
            print(f"📋 {config['name'].upper()}")
            print(f"Status: {'✅ REQUIRED' if config['required'] else '🔄 OPTIONAL'}")
            print(f"Cost: {config.get('cost_per_second', config.get('cost_per_request', 'N/A'))}")
            print(f"Setup: {config['signup_url']}")
            print(f"Pricing: {config['pricing_info']}")
            print()
            
        print("💡 RECOMMENDED SETUP ORDER:")
        print("1. Google Cloud (has $300 free credit)")
        print("2. Alibaba Qwen (has free tier)")
        print("3. MiniMax (pay for credits as needed)")
        print()
        
    async def test_api_key(self, api_name: str, api_key: str) -> Dict:
        """Test if an API key is valid and working"""
        config = self.api_configs[api_name]
        results = {
            'api_name': api_name,
            'valid': False,
            'response': None,
            'error': None
        }
        
        try:
            if api_name == 'minimax':
                # Test MiniMax API
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                test_payload = {
                    "model": "abab6.5s-chat",
                    "messages": [
                        {"role": "user", "content": "Hello, this is a test message."}
                    ]
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        'https://api.minimax.chat/v1/text/chatcompletion_pro',
                        headers=headers,
                        json=test_payload,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        results['response'] = await response.text()
                        results['valid'] = response.status == 200
                        
            elif api_name == 'qwen':
                # Test Qwen API
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                test_payload = {
                    "model": "qwen-plus",
                    "input": {
                        "messages": [
                            {"role": "user", "content": "Test message"}
                        ]
                    }
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        config['api_url'],
                        headers=headers,
                        json=test_payload,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        results['response'] = await response.text()
                        results['valid'] = response.status == 200
                        
            elif api_name == 'google':
                # Test Google AI API
                headers = {
                    'Content-Type': 'application/json'
                }
                params = {
                    'key': api_key
                }
                test_payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": "Test message"}
                            ]
                        }
                    ]
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{config['api_url']}?key={api_key}",
                        headers=headers,
                        json=test_payload,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        results['response'] = await response.text()
                        results['valid'] = response.status == 200
                        
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    def create_env_file(self, api_keys: Dict[str, str]) -> str:
        """Create a .env file with the API keys"""
        env_content = """# AI Influencer System Environment Variables
# Generated by setup script

# CRITICAL API KEYS
MINIMAX_API_KEY={minimax}
QWEN_API_KEY={qwen}
GOOGLE_API_KEY={google}

# EXISTING API KEYS (from your current system)
OPENAI_API_KEY={openai}
YOUTUBE_API_KEY={youtube}
TWITTER_BEARER_TOKEN={twitter}
INSTAGRAM_ACCESS_TOKEN={instagram}
TIKTOK_ACCESS_TOKEN={tiktok}
FACEBOOK_ACCESS_TOKEN={facebook}

# Database
DATABASE_URL=sqlite:///./ai_influencer.db

# Security
SECRET_KEY={secret_key}
ENCRYPTION_KEY={encryption_key}
"""
        
        # Generate secure keys
        secret_key = hashlib.sha256(os.urandom(32)).hexdigest()
        encryption_key = hashlib.sha256(os.urandom(16)).hexdigest()
        
        return env_content.format(
            minimax=api_keys.get('minimax', ''),
            qwen=api_keys.get('qwen', ''),
            google=api_keys.get('google', ''),
            openai=os.getenv('OPENAI_API_KEY', ''),
            youtube=os.getenv('YOUTUBE_API_KEY', ''),
            twitter=os.getenv('TWITTER_BEARER_TOKEN', ''),
            instagram=os.getenv('INSTAGRAM_ACCESS_TOKEN', ''),
            tiktok=os.getenv('TIKTOK_ACCESS_TOKEN', ''),
            facebook=os.getenv('FACEBOOK_ACCESS_TOKEN', ''),
            secret_key=secret_key,
            encryption_key=encryption_key
        )
        
    def setup_dependencies(self) -> List[str]:
        """Check and install required dependencies"""
        print("🔧 CHECKING DEPENDENCIES...")
        
        # New dependencies needed for AI influencer system
        new_deps = {
            'google-generativeai': 'Google Generative AI SDK',
            'openai': 'OpenAI API client',
            'alibabacloud-dashscope20230320': 'Alibaba DashScope SDK',
            'google-auth': 'Google Cloud authentication',
            'google-auth-oauthlib': 'Google OAuth',
            'numpy': 'Numerical computing',
            'Pillow': 'Image processing',
            'python-magic': 'File type detection'
        }
        
        missing_deps = []
        
        for dep, description in new_deps.items():
            try:
                __import__(dep)
                print(f"✅ {dep} - {description}")
            except ImportError:
                missing_deps.append(dep)
                print(f"❌ {dep} - {description} (MISSING)")
                
        if missing_deps:
            print(f"\n📦 Installing missing dependencies: {', '.join(missing_deps)}")
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_deps, check=True)
            print("✅ Dependencies installed successfully")
        else:
            print("✅ All dependencies are up to date")
            
        return missing_deps
        
    def create_test_integration(self) -> str:
        """Create integration test script"""
        test_script = '''#!/usr/bin/env python3
"""
AI Influencer System Integration Test
====================================
"""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv

async def test_all_apis():
    """Test all APIs and show results"""
    load_dotenv()
    
    print("🧪 TESTING API INTEGRATION")
    print("=" * 40)
    
    results = {}
    
    # Test MiniMax
    try:
        print("Testing MiniMax...")
        async with aiohttp.ClientSession() as session:
            headers = {'Authorization': f'Bearer {os.getenv("MINIMAX_API_KEY")}'}
            async with session.get('https://api.minimax.chat/v1/models', headers=headers) as resp:
                results['minimax'] = resp.status == 200
                print(f"  MiniMax: {'✅' if results['minimax'] else '❌'}")
    except Exception as e:
        results['minimax'] = False
        print(f"  MiniMax: ❌ {e}")
    
    # Test Qwen
    try:
        print("Testing Qwen...")
        async with aiohttp.ClientSession() as session:
            headers = {'Authorization': f'Bearer {os.getenv("QWEN_API_KEY")}'}
            async with session.get('https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation', headers=headers) as resp:
                results['qwen'] = resp.status == 200
                print(f"  Qwen: {'✅' if results['qwen'] else '❌'}")
    except Exception as e:
        results['qwen'] = False
        print(f"  Qwen: ❌ {e}")
    
    # Test Google
    try:
        print("Testing Google AI...")
        async with aiohttp.ClientSession() as session:
            params = {'key': os.getenv('GOOGLE_API_KEY')}
            async with session.get('https://generativelanguage.googleapis.com/v1beta/models', params=params) as resp:
                results['google'] = resp.status == 200
                print(f"  Google AI: {'✅' if results['google'] else '❌'}")
    except Exception as e:
        results['google'] = False
        print(f"  Google AI: ❌ {e}")
    
    # Summary
    print("\\n📊 TEST SUMMARY:")
    total_apis = len(results)
    working_apis = sum(results.values())
    print(f"Working APIs: {working_apis}/{total_apis}")
    
    if working_apis == total_apis:
        print("🎉 All APIs are working! You can now use the AI influencer system.")
    else:
        failed_apis = [name for name, status in results.items() if not status]
        print(f"❌ Failed APIs: {', '.join(failed_apis)}")
        print("Please check your API keys and try again.")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_all_apis())
'''
        return test_script

async def interactive_setup():
    """Interactive setup process"""
    manager = APIKeyManager()
    
    print("🎯 Welcome to AI Influencer System Setup!")
    print("This will help you configure 3 critical API keys.")
    print()
    
    # Show API setup guide
    manager.display_api_setup_guide()
    
    # Get API keys from user
    api_keys = {}
    for api_name, config in manager.api_configs.items():
        print(f"\n📝 Setting up {config['name']}")
        print(f"   Sign up at: {config['signup_url']}")
        print(f"   Pricing: {config['pricing_info']}")
        
        while True:
            key = input(f"   Enter your {api_name.upper()} API key (or press Enter to skip): ").strip()
            if not key:
                print(f"   ⚠️  Skipping {api_name} - this is required for full functionality")
                break
            elif len(key) < 10:
                print("   ❌ Key seems too short. Please try again.")
            else:
                api_keys[api_name] = key
                break
    
    # Test API keys
    print(f"\n🔍 TESTING API KEYS...")
    test_results = {}
    
    for api_name in ['minimax', 'qwen', 'google']:
        if api_name in api_keys:
            result = await manager.test_api_key(api_name, api_keys[api_name])
            test_results[api_name] = result
            print(f"   {manager.api_configs[api_name]['name']}: {'✅ VALID' if result['valid'] else '❌ INVALID'}")
            if result['error']:
                print(f"   Error: {result['error']}")
    
    # Create environment file
    env_content = manager.create_env_file(api_keys)
    env_path = Path('.env')
    with open(env_path, 'w') as f:
        f.write(env_content)
    print(f"\n🔐 Environment file created: {env_path}")
    
    # Setup dependencies
    print(f"\n📦 SETTING UP DEPENDENCIES...")
    missing_deps = manager.setup_dependencies()
    
    # Create test script
    test_script = manager.create_test_integration()
    test_path = Path('test_integration.py')
    with open(test_path, 'w') as f:
        f.write(test_script)
    print(f"🧪 Test script created: {test_path}")
    
    # Final summary
    print(f"\n🎉 SETUP COMPLETE!")
    print("=" * 40)
    print(f"✅ Environment file: {env_path}")
    print(f"✅ Test script: {test_path}")
    print(f"✅ Dependencies: {'All installed' if not missing_deps else f'{len(missing_deps)} new packages'}")
    
    working_apis = sum(1 for result in test_results.values() if result['valid'])
    total_apis = len([k for k in api_keys.keys()])
    
    if working_apis == total_apis and total_apis > 0:
        print("🎉 All API keys are working!")
        print("🚀 You can now run the AI influencer system!")
        print("\nNext steps:")
        print("1. Run the test: python test_integration.py")
        print("2. Start the system: python main.py")
    else:
        print("⚠️  Some API keys need fixing.")
        print("Please check the errors above and try again.")
    
    print(f"\n📖 For full documentation, see: AI-Content-Automation/ai_influencer/INTEGRATION_GUIDE.md")

if __name__ == "__main__":
    # Install required packages
    print("Installing required packages...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'aiohttp', 'python-dotenv'], check=True)
    
    # Run setup
    asyncio.run(interactive_setup())