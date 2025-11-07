"""
Content Scheduler - Phase 1
Orchestrates content generation, influencer personas, and social media posting

Author: MiniMax Agent
Date: 2025-11-07
"""

import json
import sqlite3
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from content_generator import InfluencerContentGenerator, ContentRequest, GeneratedContent
from social_media_api import SocialMediaManager, MediaAsset, PostResult
import uuid
import logging

@dataclass
class ScheduledPost:
    """A scheduled post with full details"""
    id: str
    influencer_id: int
    topic: str
    niche: str
    content_type: str
    platform: str
    scheduled_time: datetime
    status: str  # scheduled, generating, ready, posted, failed
    generated_content: Optional[GeneratedContent] = None
    post_result: Optional[PostResult] = None
    created_at: datetime = None
    retry_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class ContentCampaign:
    """A campaign containing multiple scheduled posts"""
    id: str
    name: str
    description: str
    niche: str
    target_platforms: List[str]
    influencers: List[int]
    posts: List[ScheduledPost]
    start_date: datetime
    end_date: datetime
    total_budget: float
    status: str  # planning, active, completed, paused
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class ContentScheduler:
    """
    Main scheduler that coordinates:
    1. Content generation with influencer personas
    2. Social media posting across platforms
    3. Content scheduling and automation
    4. Performance tracking
    """
    
    def __init__(self, db_path: str = "/workspace/ai_influencer_poc/database/influencers.db"):
        self.db_path = db_path
        self.content_generator = InfluencerContentGenerator(db_path)
        self.social_manager = SocialMediaManager()
        self.logger = self._setup_logging()
        
        # Scheduling configuration
        self.max_retries = 3
        self.retry_delay_minutes = 15
        self.content_buffer_minutes = 10
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the scheduler"""
        logger = logging.getLogger('ContentScheduler')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_campaign(self, name: str, description: str, niche: str, 
                       target_platforms: List[str], influencers: List[int],
                       start_date: datetime, end_date: datetime, 
                       posts_schedule: List[Dict[str, Any]]) -> ContentCampaign:
        """Create a new content campaign"""
        
        campaign_id = str(uuid.uuid4())
        posts = []
        
        for post_config in posts_schedule:
            post_id = str(uuid.uuid4())
            scheduled_time = datetime.fromisoformat(post_config['scheduled_time'])
            
            post = ScheduledPost(
                id=post_id,
                influencer_id=post_config['influencer_id'],
                topic=post_config['topic'],
                niche=post_config['niche'],
                content_type=post_config['content_type'],
                platform=post_config['platform'],
                scheduled_time=scheduled_time,
                status="scheduled"
            )
            posts.append(post)
        
        campaign = ContentCampaign(
            id=campaign_id,
            name=name,
            description=description,
            niche=niche,
            target_platforms=target_platforms,
            influencers=influencers,
            posts=posts,
            start_date=start_date,
            end_date=end_date,
            total_budget=0.0,
            status="planning"
        )
        
        # Save to database
        self._save_campaign(campaign)
        
        return campaign
    
    def _save_campaign(self, campaign: ContentCampaign):
        """Save campaign to database"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Insert campaign
            cursor.execute("""
                INSERT INTO content_campaigns 
                (id, name, description, niche, target_platforms, influencers, 
                 start_date, end_date, total_budget, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                campaign.id, campaign.name, campaign.description, campaign.niche,
                json.dumps(campaign.target_platforms), json.dumps(campaign.influencers),
                campaign.start_date.isoformat(), campaign.end_date.isoformat(),
                campaign.total_budget, campaign.status, campaign.created_at.isoformat()
            ))
            
            # Insert scheduled posts
            for post in campaign.posts:
                cursor.execute("""
                    INSERT INTO scheduled_posts 
                    (id, campaign_id, influencer_id, topic, niche, content_type,
                     platform, scheduled_time, status, retry_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post.id, campaign.id, post.influencer_id, post.topic, post.niche,
                    post.content_type, post.platform, post.scheduled_time.isoformat(),
                    post.status, post.retry_count, post.created_at.isoformat()
                ))
            
            conn.commit()
    
    def schedule_post(self, post: ScheduledPost) -> bool:
        """Schedule a post for future execution"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO scheduled_posts 
                    (id, influencer_id, topic, niche, content_type, platform,
                     scheduled_time, status, retry_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post.id, post.influencer_id, post.topic, post.niche, post.content_type,
                    post.platform, post.scheduled_time.isoformat(), post.status,
                    post.retry_count, post.created_at.isoformat()
                ))
                conn.commit()
            
            self.logger.info(f"Scheduled post {post.id} for {post.scheduled_time}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to schedule post {post.id}: {e}")
            return False
    
    def get_pending_posts(self, current_time: datetime) -> List[ScheduledPost]:
        """Get all posts that are ready to be processed"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get posts that are scheduled and due for execution
            cursor.execute("""
                SELECT * FROM scheduled_posts 
                WHERE status = 'scheduled' 
                AND scheduled_time <= ? 
                AND scheduled_time >= ?  -- Only posts from the last week
                ORDER BY scheduled_time ASC
            """, (current_time.isoformat(), (current_time - timedelta(days=7)).isoformat()))
            
            posts = []
            for row in cursor.fetchall():
                post = ScheduledPost(
                    id=row['id'],
                    influencer_id=row['influencer_id'],
                    topic=row['topic'],
                    niche=row['niche'],
                    content_type=row['content_type'],
                    platform=row['platform'],
                    scheduled_time=datetime.fromisoformat(row['scheduled_time']),
                    status=row['status'],
                    retry_count=row['retry_count'],
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                posts.append(post)
            
            return posts
    
    def process_scheduled_post(self, post: ScheduledPost) -> bool:
        """Process a single scheduled post"""
        try:
            # Update status to generating
            self._update_post_status(post.id, "generating")
            
            # Generate content with influencer persona
            content_request = ContentRequest(
                topic=post.topic,
                niche=post.niche,
                influencer_id=post.influencer_id,
                content_type=post.content_type,
                platform=post.platform
            )
            
            generated_content = self.content_generator.generate_content(content_request)
            post.generated_content = generated_content
            
            # Update post with generated content
            self._save_generated_content(post, generated_content)
            
            # Post to social media
            post_result = self._post_to_social_media(generated_content, post)
            post.post_result = post_result
            
            if post_result.success:
                self._update_post_status(post.id, "posted")
                self.logger.info(f"Successfully posted {post.id} to {post.platform}")
                return True
            else:
                # Handle posting failure
                self._handle_posting_failure(post, post_result.error_message)
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing post {post.id}: {e}")
            self._update_post_status(post.id, "failed", error_message=str(e))
            return False
    
    def _save_generated_content(self, post: ScheduledPost, generated_content: GeneratedContent):
        """Save generated content to database"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Save generated content
            cursor.execute("""
                INSERT INTO generated_content 
                (id, post_id, influencer_id, content, hashtags, title, description,
                 platform_optimized, cost_estimate, persona_consistency_score, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                generated_content.id, post.id, generated_content.influencer_id,
                generated_content.content, json.dumps(generated_content.hashtags),
                generated_content.title, generated_content.description,
                json.dumps(generated_content.platform_optimized),
                generated_content.cost_estimate, generated_content.persona_consistency_score,
                generated_content.generated_at.isoformat()
            ))
            
            conn.commit()
    
    def _post_to_social_media(self, generated_content: GeneratedContent, post: ScheduledPost) -> PostResult:
        """Post content to social media platform"""
        try:
            media_asset = None  # TODO: Add media generation
            
            if post.platform == "youtube":
                return self.social_manager.post_to_platform(
                    post.platform, 
                    generated_content.title,
                    generated_content.description,
                    media_asset
                )
            else:
                # For other platforms, combine title and content
                full_content = f"{generated_content.title}\n\n{generated_content.content}"
                return self.social_manager.post_to_platform(
                    post.platform,
                    generated_content.title,
                    full_content,
                    media_asset
                )
                
        except Exception as e:
            return PostResult(
                platform=post.platform,
                post_id="",
                url=None,
                success=False,
                error_message=str(e)
            )
    
    def _handle_posting_failure(self, post: ScheduledPost, error_message: str):
        """Handle social media posting failure with retry logic"""
        post.retry_count += 1
        
        if post.retry_count < self.max_retries:
            # Schedule retry
            new_scheduled_time = datetime.now() + timedelta(minutes=self.retry_delay_minutes * post.retry_count)
            post.scheduled_time = new_scheduled_time
            post.status = "scheduled"
            
            self._update_post_status(post.id, "scheduled", retry_count=post.retry_count)
            self.logger.info(f"Scheduled retry {post.retry_count} for post {post.id} at {new_scheduled_time}")
        else:
            # Max retries reached
            self._update_post_status(post.id, "failed", error_message=error_message)
            self.logger.error(f"Max retries reached for post {post.id}: {error_message}")
    
    def _update_post_status(self, post_id: str, status: str, retry_count: int = 0, error_message: str = None):
        """Update post status in database"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            
            if error_message:
                cursor.execute("""
                    UPDATE scheduled_posts 
                    SET status = ?, retry_count = ?, error_message = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (status, retry_count, error_message, datetime.now().isoformat(), post_id))
            else:
                cursor.execute("""
                    UPDATE scheduled_posts 
                    SET status = ?, retry_count = ?, updated_at = ?
                    WHERE id = ?
                """, (status, retry_count, datetime.now().isoformat(), post_id))
            
            conn.commit()
    
    def run_scheduler_cycle(self) -> Dict[str, int]:
        """Run a single scheduler cycle"""
        current_time = datetime.now()
        results = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "retries_scheduled": 0
        }
        
        # Get pending posts
        pending_posts = self.get_pending_posts(current_time)
        
        for post in pending_posts:
            results["processed"] += 1
            
            if self.process_scheduled_post(post):
                results["successful"] += 1
            else:
                results["failed"] += 1
                if post.retry_count < self.max_retries:
                    results["retries_scheduled"] += 1
        
        if results["processed"] > 0:
            self.logger.info(f"Cycle completed: {results}")
        
        return results
    
    def get_campaign_performance(self, campaign_id: str) -> Dict[str, Any]:
        """Get performance metrics for a campaign"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get campaign posts and their performance
            cursor.execute("""
                SELECT sp.*, gc.content, gc.title, gc.cost_estimate, 
                       gc.persona_consistency_score
                FROM scheduled_posts sp
                LEFT JOIN generated_content gc ON sp.id = gc.post_id
                WHERE sp.campaign_id = ?
                ORDER BY sp.scheduled_time ASC
            """, (campaign_id,))
            
            posts_data = []
            total_cost = 0
            total_consistency_score = 0
            successful_posts = 0
            
            for row in cursor.fetchall():
                if row['cost_estimate']:
                    total_cost += row['cost_estimate']
                if row['persona_consistency_score']:
                    total_consistency_score += row['persona_consistency_score']
                
                if row['status'] == 'posted':
                    successful_posts += 1
                
                posts_data.append({
                    "id": row['id'],
                    "topic": row['topic'],
                    "niche": row['niche'],
                    "platform": row['platform'],
                    "status": row['status'],
                    "scheduled_time": row['scheduled_time'],
                    "cost_estimate": row['cost_estimate'],
                    "persona_consistency_score": row['persona_consistency_score']
                })
            
            total_posts = len(posts_data)
            avg_consistency_score = total_consistency_score / total_posts if total_posts > 0 else 0
            success_rate = (successful_posts / total_posts) * 100 if total_posts > 0 else 0
            
            return {
                "campaign_id": campaign_id,
                "total_posts": total_posts,
                "successful_posts": successful_posts,
                "success_rate": success_rate,
                "total_cost": total_cost,
                "average_cost_per_post": total_cost / total_posts if total_posts > 0 else 0,
                "average_persona_consistency": avg_consistency_score,
                "posts": posts_data
            }
    
    def create_sample_campaign(self) -> ContentCampaign:
        """Create a sample campaign for demonstration"""
        
        # Create sample scheduled posts
        posts_schedule = []
        base_time = datetime.now() + timedelta(minutes=5)  # Start 5 minutes from now
        
        # 6 posts across different influencers and platforms
        sample_posts = [
            {
                "topic": "Money Saving Tips",
                "niche": "finance",
                "influencer_id": 1,  # Alex Finance Guru
                "platform": "youtube"
            },
            {
                "topic": "Productivity Hacks", 
                "niche": "tech",
                "influencer_id": 2,  # Sarah Tech Vision
                "platform": "tiktok"
            },
            {
                "topic": "Morning Workout Routine",
                "niche": "fitness", 
                "influencer_id": 3,  # Mike Fit Coach
                "platform": "instagram"
            },
            {
                "topic": "Professional Networking",
                "niche": "career",
                "influencer_id": 4,
                "platform": "linkedin"
            },
            {
                "topic": "Budget Planning",
                "niche": "finance",
                "influencer_id": 1,  # Alex Finance Guru
                "platform": "twitter"
            },
            {
                "topic": "AI Tools Review",
                "niche": "tech",
                "influencer_id": 2,  # Sarah Tech Vision  
                "platform": "youtube"
            }
        ]
        
        for i, post_config in enumerate(sample_posts):
            scheduled_time = base_time + timedelta(minutes=i*3)  # 3 minutes apart
            posts_schedule.append({
                **post_config,
                "scheduled_time": scheduled_time.isoformat(),
                "content_type": "video" if post_config["platform"] in ["youtube"] else "post"
            })
        
        campaign = self.create_campaign(
            name="Phase 1 Demo Campaign",
            description="Demonstration of AI influencer content generation and social media posting",
            niche="multi",
            target_platforms=["youtube", "tiktok", "instagram", "linkedin", "twitter"],
            influencers=[1, 2, 3, 4],
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=1),
            posts_schedule=posts_schedule
        )
        
        return campaign