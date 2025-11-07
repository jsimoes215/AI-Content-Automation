"""
Phase 1 Main Integration Script
Demonstrates the complete AI influencer content generation and social media pipeline

Author: MiniMax Agent
Date: 2025-11-07
"""

import sys
import os
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sqlite3

# Add the phase1 directory to the Python path
sys.path.append('/workspace/ai_influencer_poc/phase1')

from content_generator import InfluencerContentGenerator, ContentRequest, GeneratedContent
from social_media_api import SocialMediaManager, MediaAsset, PostResult
from content_scheduler import ContentScheduler, ScheduledPost, ContentCampaign
from database_migration import create_phase1_tables, verify_phase1_setup

class Phase1Demo:
    """Main demonstration class for Phase 1 functionality"""
    
    def __init__(self):
        self.db_path = "/workspace/ai_influencer_poc/database/influencers.db"
        self.content_generator = InfluencerContentGenerator(self.db_path)
        self.social_manager = SocialMediaManager()
        self.scheduler = ContentScheduler(self.db_path)
        
        print("🤖 AI INFLUENCER MANAGEMENT - PHASE 1 DEMO")
        print("=" * 50)
    
    def setup_phase1(self) -> bool:
        """Setup Phase 1 database and verify everything is working"""
        print("\n📊 SETUP PHASE 1")
        print("-" * 30)
        
        try:
            # Run database migration
            create_phase1_tables(self.db_path)
            
            # Verify setup
            if verify_phase1_setup(self.db_path):
                print("✅ Phase 1 setup complete!")
                return True
            else:
                print("❌ Phase 1 setup failed!")
                return False
                
        except Exception as e:
            print(f"❌ Setup error: {e}")
            return False
    
    def demo_content_generation(self) -> List[GeneratedContent]:
        """Demonstrate content generation with different influencer personas"""
        print("\n🎨 CONTENT GENERATION DEMO")
        print("-" * 30)
        
        # Test different content requests
        test_requests = [
            ContentRequest(
                topic="Money Saving Tips", 
                niche="finance",
                influencer_id=1,  # Alex Finance Guru
                platform="youtube"
            ),
            ContentRequest(
                topic="Productivity Hacks",
                niche="tech", 
                influencer_id=2,  # Sarah Tech Vision
                platform="tiktok"
            ),
            ContentRequest(
                topic="Morning Workout Routine",
                niche="fitness",
                influencer_id=3,  # Mike Fit Coach
                platform="instagram"
            ),
            ContentRequest(
                topic="Professional Networking",
                niche="career",
                influencer_id=4,
                platform="linkedin"
            )
        ]
        
        generated_content = []
        
        for i, request in enumerate(test_requests, 1):
            print(f"\n📝 Generating content {i}/4: {request.topic}")
            
            try:
                content = self.content_generator.generate_content(request)
                generated_content.append(content)
                
                print(f"   ✅ Generated for: {content.influencer_name}")
                print(f"   💰 Cost: ${content.cost_estimate:.2f}")
                print(f"   🎯 Consistency Score: {content.persona_consistency_score:.2f}")
                print(f"   📱 Platform: {request.platform}")
                print(f"   📄 Title: {content.title[:60]}...")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n📊 Content Generation Summary:")
        print(f"   - Total generated: {len(generated_content)}")
        avg_cost = sum(c.cost_estimate for c in generated_content) / len(generated_content)
        avg_consistency = sum(c.persona_consistency_score for c in generated_content) / len(generated_content)
        print(f"   - Average cost: ${avg_cost:.2f}")
        print(f"   - Average consistency: {avg_consistency:.2f}")
        
        return generated_content
    
    def demo_social_media_posting(self, generated_content: List[GeneratedContent]):
        """Demonstrate posting to social media platforms"""
        print("\n📱 SOCIAL MEDIA POSTING DEMO")
        print("-" * 30)
        
        posting_results = {}
        
        for i, content in enumerate(generated_content, 1):
            # Map content to different platforms for demo
            platform = "youtube" if i % 5 == 1 else "tiktok" if i % 5 == 2 else "instagram" if i % 5 == 3 else "linkedin" if i % 5 == 4 else "twitter"
            
            print(f"\n📤 Posting {i}/4: {content.influencer_name} to {platform}")
            
            try:
                if platform == "youtube":
                    result = self.social_manager.post_to_platform(
                        platform,
                        content.title,
                        content.description
                    )
                else:
                    # Combine title and content for other platforms
                    full_content = f"{content.title}\n\n{content.content}"
                    result = self.social_manager.post_to_platform(
                        platform,
                        content.title,
                        full_content
                    )
                
                posting_results[platform] = result
                
                if result.success:
                    print(f"   ✅ Posted successfully!")
                    print(f"   🔗 URL: {result.url}")
                else:
                    print(f"   ❌ Failed: {result.error_message}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n📊 Posting Summary:")
        successful = sum(1 for r in posting_results.values() if r.success)
        print(f"   - Successful posts: {successful}/{len(posting_results)}")
        success_rate = (successful / len(posting_results)) * 100
        print(f"   - Success rate: {success_rate:.1f}%")
        
        return posting_results
    
    def demo_content_campaign(self) -> ContentCampaign:
        """Demonstrate creating and managing a content campaign"""
        print("\n📅 CONTENT CAMPAIGN DEMO")
        print("-" * 30)
        
        # Create a sample campaign
        campaign = self.scheduler.create_sample_campaign()
        
        print(f"📋 Campaign Created: {campaign.name}")
        print(f"   📝 Description: {campaign.description}")
        print(f"   🎯 Niche: {campaign.niche}")
        print(f"   📱 Platforms: {', '.join(campaign.target_platforms)}")
        print(f"   👥 Influencers: {len(campaign.influencers)}")
        print(f"   📅 Posts: {len(campaign.posts)}")
        
        # Schedule some posts for immediate execution
        print(f"\n⏰ Scheduling posts...")
        
        current_time = datetime.now()
        scheduled_posts = []
        
        for i, post in enumerate(campaign.posts):
            # Schedule posts 2 minutes apart starting now
            post.scheduled_time = current_time + timedelta(minutes=i*2)
            if self.scheduler.schedule_post(post):
                scheduled_posts.append(post)
                print(f"   ✅ Scheduled: {post.topic} -> {post.platform}")
            else:
                print(f"   ❌ Failed to schedule: {post.topic}")
        
        print(f"\n📊 Campaign Summary:")
        print(f"   - Total posts: {len(campaign.posts)}")
        print(f"   - Successfully scheduled: {len(scheduled_posts)}")
        print(f"   - Ready to execute: {len(scheduled_posts)}")
        
        return campaign
    
    def demo_scheduler_execution(self) -> Dict[str, int]:
        """Demonstrate the content scheduler in action"""
        print("\n⚙️  SCHEDULER EXECUTION DEMO")
        print("-" * 30)
        
        print("🔄 Running scheduler cycle...")
        
        try:
            # Run the scheduler
            results = self.scheduler.run_scheduler_cycle()
            
            print(f"\n📊 Scheduler Results:")
            for key, value in results.items():
                print(f"   - {key.replace('_', ' ').title()}: {value}")
            
            return results
            
        except Exception as e:
            print(f"❌ Scheduler error: {e}")
            return {"processed": 0, "successful": 0, "failed": 0, "errors": str(e)}
    
    def demo_analytics_dashboard(self, campaign: ContentCampaign = None):
        """Demonstrate analytics and performance tracking"""
        print("\n📈 ANALYTICS DASHBOARD DEMO")
        print("-" * 30)
        
        try:
            # Get database connection for analytics
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Overall system metrics
            metrics_queries = {
                "Total Influencers": "SELECT COUNT(*) as count FROM influencers WHERE is_active = 1",
                "Total Niches": "SELECT COUNT(*) as count FROM niches",
                "Scheduled Posts": "SELECT COUNT(*) as count FROM scheduled_posts WHERE status = 'scheduled'",
                "Generated Content": "SELECT COUNT(*) as count FROM generated_content",
                "Active Campaigns": "SELECT COUNT(*) as count FROM content_campaigns WHERE status = 'active'"
            }
            
            print("📊 System Overview:")
            for metric_name, query in metrics_queries.items():
                cursor.execute(query)
                count = cursor.fetchone()['count']
                print(f"   - {metric_name}: {count}")
            
            # Content performance breakdown by platform
            cursor.execute("""
                SELECT sp.platform, 
                       COUNT(*) as total_posts,
                       SUM(CASE WHEN sp.status = 'posted' THEN 1 ELSE 0 END) as successful_posts,
                       AVG(gc.cost_estimate) as avg_cost,
                       AVG(gc.persona_consistency_score) as avg_consistency
                FROM scheduled_posts sp
                LEFT JOIN generated_content gc ON sp.id = gc.post_id
                GROUP BY sp.platform
            """)
            
            print(f"\n📱 Platform Performance:")
            for row in cursor.fetchall():
                success_rate = (row['successful_posts'] / row['total_posts']) * 100 if row['total_posts'] > 0 else 0
                print(f"   - {row['platform']}: {success_rate:.1f}% success, ${row['avg_cost'] or 0:.2f} avg cost")
            
            # Recent posts performance
            cursor.execute("""
                SELECT sp.topic, sp.platform, sp.status, gc.cost_estimate, 
                       gc.persona_consistency_score, sp.created_at
                FROM scheduled_posts sp
                LEFT JOIN generated_content gc ON sp.id = gc.post_id
                ORDER BY sp.created_at DESC
                LIMIT 5
            """)
            
            print(f"\n🕐 Recent Posts:")
            for row in cursor.fetchall():
                status_emoji = "✅" if row['status'] == 'posted' else "⏳" if row['status'] == 'scheduled' else "❌"
                print(f"   {status_emoji} {row['topic']} ({row['platform']}) - {row['status']}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Analytics error: {e}")
    
    def run_complete_demo(self):
        """Run the complete Phase 1 demonstration"""
        print("🚀 PHASE 1 COMPLETE DEMONSTRATION")
        print("=" * 50)
        
        # Step 1: Setup
        if not self.setup_phase1():
            print("❌ Setup failed. Exiting demo.")
            return
        
        # Step 2: Content Generation Demo
        generated_content = self.demo_content_generation()
        
        if not generated_content:
            print("❌ No content generated. Exiting demo.")
            return
        
        # Step 3: Social Media Posting Demo
        self.demo_social_media_posting(generated_content)
        
        # Step 4: Content Campaign Demo
        campaign = self.demo_content_campaign()
        
        # Step 5: Scheduler Execution Demo
        self.demo_scheduler_execution()
        
        # Step 6: Analytics Dashboard Demo
        self.demo_analytics_dashboard(campaign)
        
        print("\n🎉 PHASE 1 DEMONSTRATION COMPLETE!")
        print("=" * 50)
        print("✅ Content generation with influencer personas")
        print("✅ Multi-platform social media integration")
        print("✅ Automated content scheduling and execution")
        print("✅ Performance tracking and analytics")
        print("✅ Integration with existing $2.40/content pipeline")
        
        print("\n💡 Next Steps:")
        print("1. Configure social media API credentials")
        print("2. Add media generation capabilities")
        print("3. Expand to more influencers and niches")
        print("4. Implement advanced analytics")
        print("5. Add content optimization based on performance")
    
    def interactive_demo(self):
        """Run an interactive demonstration"""
        print("\n🤝 INTERACTIVE PHASE 1 DEMO")
        print("=" * 40)
        
        print("Choose demo option:")
        print("1. Complete automated demo")
        print("2. Content generation only")
        print("3. Social media posting only")
        print("4. Content campaign only")
        print("5. Analytics dashboard only")
        
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == "1":
                self.run_complete_demo()
            elif choice == "2":
                self.demo_content_generation()
            elif choice == "3":
                content = self.demo_content_generation()
                if content:
                    self.demo_social_media_posting(content)
            elif choice == "4":
                self.demo_content_campaign()
            elif choice == "5":
                self.demo_analytics_dashboard()
            else:
                print("Invalid choice. Running complete demo.")
                self.run_complete_demo()
                
        except KeyboardInterrupt:
            print("\n👋 Demo interrupted by user.")
        except Exception as e:
            print(f"\n❌ Demo error: {e}")

def main():
    """Main function"""
    demo = Phase1Demo()
    
    # Check if running in interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        demo.interactive_demo()
    else:
        # Run complete automated demo
        demo.run_complete_demo()

if __name__ == "__main__":
    main()