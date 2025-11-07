"""
Optimized Image Generation System - Base + Variations Strategy
Generate high-quality base images once, then create cost-effective variations

Author: MiniMax Agent
Date: 2025-11-07
"""

import json
import sqlite3
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib
import base64

@dataclass
class BaseImageRequest:
    """Request for high-quality base image generation"""
    influencer_id: int
    content_type: str  # portrait, lifestyle, professional
    style: str = "premium"  # premium, standard, budget
    high_res: bool = True
    multiple_angles: bool = False  # Generate 3-5 angles of same person

@dataclass
class VariationRequest:
    """Request for image variations based on base image"""
    base_image_id: str
    scenario: str  # "office setting", "casual outdoor", "workout gym", etc.
    pose: str = "neutral"  # standing, sitting, pointing, etc.
    background: str = "professional"  # office, home, outdoor, etc.
    lighting: str = "natural"  # natural, studio, dramatic, etc.
    clothing: str = "consistent"  # same outfit, casual variant, formal variant

@dataclass
class GeneratedImage:
    """Generated image with metadata"""
    id: str
    influencer_id: int
    base_image: bool
    base_image_id: Optional[str]
    image_url: str
    prompt_used: str
    style_consistency_score: float
    brand_alignment_score: float
    platform_optimized: Dict[str, any]
    created_at: datetime
    cost_estimate: float
    model_used: str

class OptimizedImageGenerator:
    """
    Cost-optimized image generation system
    Strategy: Generate 1 high-quality base image, then create inexpensive variations
    """
    
    def __init__(self, db_path: str = "/workspace/ai_influencer_poc/database/influencers.db"):
        self.db_path = db_path
        
        # Model cost structure (per image)
        self.model_costs = {
            "dall_e_3": {
                "base_image": 0.040,  # High quality base image
                "variation": 0.020,   # Variation using base
                "best_for": "base_images",
                "quality": "premium"
            },
            "gemini_2_5_flash": {
                "base_image": 0.010,  # Good base alternative
                "variation": 0.005,   # Very cheap variations
                "best_for": "variations",
                "quality": "good"
            },
            "qwen_vl": {
                "base_image": 0.015,  # Alternative base
                "variation": 0.008,   # Cheap variations
                "best_for": "variations", 
                "quality": "good"
            },
            "stable_diffusion": {
                "base_image": 0.020,  # Local/cheap base
                "variation": 0.005,   # Very cheap local
                "best_for": "bulk_variations",
                "quality": "standard"
            }
        }
        
        # Scenario templates for variations
        self.scenario_templates = {
            "finance": {
                "office": "professional office setting, desk, laptop, charts on screen, business attire",
                "home": "home office setup, laptop, financial documents, casual professional clothing",
                "outdoor": "coffee shop meeting, laptop, notebook, professional but approachable",
                "presentation": "conference room, presenting to audience, business presentation setup"
            },
            "tech": {
                "coding": "modern workspace, multiple monitors, coding setup, tech environment",
                "meeting": "tech office meeting room, brainstorming session, innovative atmosphere",
                "demo": "product demonstration setup, tech gadgets, futuristic environment",
                "remote": "home office tech setup, video call ready, modern tech aesthetics"
            },
            "fitness": {
                "gym": "modern gym environment, workout equipment, athletic wear, energetic",
                "outdoor": "outdoor fitness setting, park, workout gear, natural lighting",
                "home": "home workout space, minimal equipment, motivational atmosphere",
                "training": "personal training session, fitness instruction, supportive environment"
            },
            "career": {
                "interview": "professional interview setting, formal office, business attire",
                "networking": "networking event, professional gathering, business cards, handshakes",
                "office": "corporate office environment, desk, professional workspace",
                "consultation": "client meeting, consultation setting, professional advice"
            }
        }
        
        # Pose templates
        self.pose_templates = {
            "neutral": "standing or sitting naturally, confident posture, professional demeanor",
            "presenting": "facing forward, engaged expression, presenter stance",
            "pointing": "gesturing towards object or screen, instructional pose",
            "thinking": "thoughtful expression, hand on chin or considering pose",
            "explaining": "explaining concept, open hand gestures, teacher-like stance",
            "enthusiastic": "energetic pose, open body language, engaging expression"
        }

    def generate_base_image(self, request: BaseImageRequest) -> GeneratedImage:
        """Generate high-quality base image for influencer"""
        
        # Get influencer data
        influencer = self.get_influencer(request.influencer_id)
        if not influencer:
            raise ValueError(f"Influencer {request.influencer_id} not found")
        
        # Select best model for base image
        if request.style == "premium":
            model = "dall_e_3"  # Best quality
        else:
            model = "gemini_2_5_flash"  # Good quality, lower cost
        
        # Build base image prompt
        base_prompt = self._build_base_image_prompt(request, influencer)
        
        # Generate base image
        image_data, image_url = self._call_ai_service(base_prompt, model, "base_image")
        
        # Calculate costs and scores
        cost_estimate = self.model_costs[model]["base_image"]
        style_score = self._calculate_style_consistency(image_data, influencer)
        brand_score = self._calculate_brand_alignment(image_data, influencer, "base")
        
        # Create base image
        base_image_id = self._generate_image_id(request.influencer_id, "base")
        
        base_image = GeneratedImage(
            id=base_image_id,
            influencer_id=request.influencer_id,
            base_image=True,
            base_image_id=None,
            image_url=image_url,
            prompt_used=base_prompt,
            style_consistency_score=style_score,
            brand_alignment_score=brand_score,
            platform_optimized={},
            created_at=datetime.now(),
            cost_estimate=cost_estimate,
            model_used=model
        )
        
        # Store base image reference for future variations
        self._store_base_image_reference(base_image_id, request.influencer_id, image_url)
        
        return base_image
    
    def generate_variations(self, base_image_id: str, requests: List[VariationRequest]) -> List[GeneratedImage]:
        """Generate multiple variations based on base image"""
        
        # Get base image reference
        base_ref = self._get_base_image_reference(base_image_id)
        if not base_ref:
            raise ValueError(f"Base image {base_image_id} not found")
        
        variations = []
        for request in requests:
            variation = self._generate_single_variation(base_image_id, request, base_ref)
            variations.append(variation)
        
        return variations
    
    def _generate_single_variation(self, base_image_id: str, request: VariationRequest, base_ref: Dict) -> GeneratedImage:
        """Generate single variation based on base image"""
        
        # Use cheaper model for variations
        model = "gemini_2_5_flash"  # Fast and cheap for variations
        
        # Build variation prompt using base image + scenario
        variation_prompt = self._build_variation_prompt(base_ref, request)
        
        # Generate variation (would use image-to-image or reference-based generation)
        image_data, image_url = self._call_ai_service(variation_prompt, model, "variation", base_ref["image_url"])
        
        # Calculate costs and scores
        cost_estimate = self.model_costs[model]["variation"]
        style_score = self._calculate_style_consistency(image_data, base_ref["influencer"])
        brand_score = self._calculate_brand_alignment(image_data, base_ref["influencer"], "variation")
        
        # Create variation image
        variation_id = self._generate_image_id(base_ref["influencer_id"], "variation")
        
        variation = GeneratedImage(
            id=variation_id,
            influencer_id=base_ref["influencer_id"],
            base_image=False,
            base_image_id=base_image_id,
            image_url=image_url,
            prompt_used=variation_prompt,
            style_consistency_score=style_score,
            brand_alignment_score=brand_score,
            platform_optimized={},
            created_at=datetime.now(),
            cost_estimate=cost_estimate,
            model_used=model
        )
        
        return variation
    
    def _build_base_image_prompt(self, request: BaseImageRequest, influencer: Dict) -> str:
        """Build prompt for high-quality base image"""
        
        voice_type = influencer.get('voice_type', 'professional_male')
        personality_traits = influencer.get('personality_traits', [])
        niche = influencer.get('primary_niche', 'general')
        
        # Base appearance description
        appearance_desc = self._get_appearance_description(voice_type, personality_traits)
        
        # Professional photography style
        style_elements = {
            "premium": "professional headshot, studio lighting, high resolution, detailed, photorealistic",
            "standard": "good quality photo, natural lighting, clear, professional",
            "budget": "acceptable quality, decent lighting, clear enough for social media"
        }
        
        style = style_elements.get(request.style, style_elements["premium"])
        
        # Build comprehensive prompt
        prompt = f"Professional portrait of {appearance_desc}, {style}. "
        prompt += f"Confident, approachable, professional demeanor. "
        prompt += f"High quality, detailed facial features, professional appearance. "
        
        if request.multiple_angles:
            prompt += "Generate 3-5 different angles: front view, slight profile, three-quarter view."
        
        return prompt
    
    def _build_variation_prompt(self, base_ref: Dict, request: VariationRequest) -> str:
        """Build prompt for image variation based on base image"""
        
        influencer = base_ref["influencer"]
        voice_type = influencer.get('voice_type', 'professional_male')
        
        # Get scenario-specific elements
        niche = influencer.get('primary_niche', 'general')
        scenarios = self.scenario_templates.get(niche, {})
        scenario_desc = scenarios.get(request.scenario, f"{request.scenario} setting")
        
        # Get pose description
        pose_desc = self.pose_templates.get(request.pose, self.pose_templates["neutral"])
        
        # Build variation prompt
        prompt = f"Same person as reference image, {pose_desc}. "
        prompt += f"Setting: {scenario_desc}. "
        
        # Add lighting and clothing variations
        if request.lighting != "natural":
            prompt += f"Lighting: {request.lighting}. "
        
        if request.clothing != "consistent":
            prompt += f"Clothing: {request.clothing} variation. "
        
        prompt += "Maintain same person's facial features and identity. High quality, consistent with base image."
        
        return prompt
    
    def _get_appearance_description(self, voice_type: str, personality_traits: List[str]) -> str:
        """Get appearance description based on voice type and personality"""
        
        # Base appearance by voice type
        appearances = {
            "professional_male": "middle-aged professional man, business attire, clean-shaven or well-groomed, confident expression",
            "friendly_female": "young professional woman, business casual attire, warm smile, approachable demeanor", 
            "casual_young": "young adult, modern casual attire, energetic expression, contemporary style"
        }
        
        base_appearance = appearances.get(voice_type, appearances["professional_male"])
        
        # Adjust based on personality traits
        if "trustworthy" in personality_traits:
            base_appearance = base_appearance.replace("confident", "trustworthy and confident")
        if "energetic" in personality_traits:
            base_appearance = base_appearance.replace("professional", "energetic professional")
        if "creative" in personality_traits:
            base_appearance = base_appearance.replace("business", "creative business")
        
        return base_appearance
    
    def _call_ai_service(self, prompt: str, model: str, image_type: str, reference_url: str = None) -> Tuple[str, str]:
        """Call AI service to generate image (mock implementation)"""
        
        # In production, this would:
        # 1. For base images: Call DALL-E 3 or Gemini 2.5 Flash directly
        # 2. For variations: Use image-to-image generation with reference
        
        # Mock implementation
        model_config = self.model_costs[model]
        
        if image_type == "base_image":
            mock_image_data = f"base_{hashlib.md5(prompt.encode()).hexdigest()[:12]}"
            mock_url = f"https://images.example.com/base/{mock_image_data}.jpg"
        else:
            # Variation with reference
            ref_id = hashlib.md5(reference_url.encode()).hexdigest()[:8] if reference_url else "ref"
            mock_image_data = f"var_{ref_id}_{hashlib.md5(prompt.encode()).hexdigest()[:8]}"
            mock_url = f"https://images.example.com/variations/{mock_image_data}.jpg"
        
        # Simulate API processing time
        import time
        processing_time = 0.5 if image_type == "base_image" else 0.1
        time.sleep(processing_time)
        
        return mock_image_data, mock_url
    
    def calculate_cost_savings(self, num_base_images: int, num_variations_per_base: int) -> Dict:
        """Calculate cost savings of optimized approach"""
        
        # Traditional approach: All images with premium model
        traditional_cost = (num_base_images + (num_base_images * num_variations_per_base)) * 0.040
        
        # Optimized approach: Premium base + cheap variations
        optimized_cost = (num_base_images * 0.040) + (num_base_images * num_variations_per_base * 0.005)
        
        savings = traditional_cost - optimized_cost
        savings_percentage = (savings / traditional_cost) * 100
        
        return {
            "traditional_cost": traditional_cost,
            "optimized_cost": optimized_cost,
            "total_savings": savings,
            "savings_percentage": savings_percentage,
            "cost_per_image_traditional": traditional_cost / (num_base_images + (num_base_images * num_variations_per_base)),
            "cost_per_image_optimized": optimized_cost / (num_base_images + (num_base_images * num_variations_per_base))
        }
    
    def get_influencer(self, influencer_id: int) -> Optional[Dict]:
        """Get influencer data"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM influencers WHERE id = ? AND is_active = 1", (influencer_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            influencer = dict(row)
            influencer['personality_traits'] = json.loads(influencer['personality_traits'] or '[]')
            influencer['target_audience'] = json.loads(influencer['target_audience'] or '{}')
            influencer['branding_guidelines'] = json.loads(influencer['branding_guidelines'] or '{}')
            
            return influencer
            
        finally:
            conn.close()
    
    def _generate_image_id(self, influencer_id: int, image_type: str) -> str:
        """Generate unique image ID"""
        import time
        timestamp = int(time.time())
        return f"{image_type}_{influencer_id}_{timestamp}"
    
    def _store_base_image_reference(self, base_image_id: str, influencer_id: int, image_url: str):
        """Store base image reference for future variations"""
        # In production, this would store in database
        # For now, just return the reference data
        return {
            "base_image_id": base_image_id,
            "influencer_id": influencer_id,
            "image_url": image_url,
            "created_at": datetime.now()
        }
    
    def _get_base_image_reference(self, base_image_id: str) -> Optional[Dict]:
        """Get base image reference data"""
        # In production, this would query from database
        # Mock implementation
        return {
            "base_image_id": base_image_id,
            "influencer_id": 1,  # Mock data
            "image_url": f"https://images.example.com/base/{base_image_id}.jpg",
            "influencer": self.get_influencer(1)  # Mock influencer
        }
    
    def _calculate_style_consistency(self, image_data: str, influencer: Dict) -> float:
        """Calculate style consistency score"""
        # Mock implementation - would use computer vision in production
        import hashlib
        image_hash = hashlib.md5(image_data.encode()).hexdigest()
        hash_int = int(image_hash[:8], 16)
        return (hash_int % 100) / 100
    
    def _calculate_brand_alignment(self, image_data: str, influencer: Dict, image_type: str) -> float:
        """Calculate brand alignment score"""
        # Mock implementation
        import hashlib
        brand_hash = hashlib.md5(f"{influencer['name']}_{image_type}".encode()).hexdigest()
        hash_int = int(brand_hash[:8], 16)
        return (hash_int % 100) / 100