"""
Content Library Management - Handles scene storage, meta-tagging, and intelligent retrieval
"""

import json
import os
import pickle
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SceneMetadata:
    """Metadata for a scene in the content library"""
    id: str
    scene_id: str  # Reference to original scene
    title: str
    description: str
    duration: float
    content_type: str
    style: str
    mood: str
    quality_score: float
    usage_count: int
    performance_metrics: Dict[str, float]
    tags: Dict[str, List[str]]
    embedding_vector: Optional[List[float]]
    file_paths: Dict[str, str]  # video, audio, thumbnail paths
    created_at: str
    last_used: Optional[str]
    version: int
    library_category: str

@dataclass
class SearchQuery:
    """Search query for content library"""
    query_text: Optional[str]
    tags: List[str]
    duration_range: Tuple[float, float]
    content_types: List[str]
    quality_threshold: float
    platform: Optional[str]
    limit: int
    similarity_threshold: float

@dataclass
class SearchResult:
    """Search result from content library"""
    scene: SceneMetadata
    similarity_score: float
    match_reasons: List[str]

class ContentLibraryManager:
    """Main content library management system"""
    
    def __init__(self, library_dir: str):
        self.library_dir = Path(library_dir)
        self.scenes_dir = self.library_dir / "scenes"
        self.tags_dir = self.library_dir / "tags"
        self.embeddings_dir = self.library_dir / "embeddings"
        self.index_file = self.library_dir / "library_index.json"
        
        # Create directories
        self._ensure_directories()
        
        # Library statistics
        self.stats = {
            "total_scenes": 0,
            "total_tags": 0,
            "average_quality": 0.0,
            "most_used_scenes": [],
            "recently_added": [],
            "performance_leaders": []
        }
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        for directory in [self.library_dir, self.scenes_dir, self.tags_dir, self.embeddings_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def add_scene_to_library(self,
                                  scene_data: Dict[str, Any],
                                  tags: Dict[str, List[str]],
                                  file_paths: Dict[str, str],
                                  auto_tagging: bool = True,
                                  generate_embedding: bool = True) -> SceneMetadata:
        """
        Add a scene to the content library
        
        Args:
            scene_data: Scene information (id, title, description, etc.)
            tags: Meta-tags (specific and generic)
            file_paths: Paths to video, audio, thumbnail files
            auto_tagging: Whether to auto-generate additional tags
            generate_embedding: Whether to generate semantic embedding
            
        Returns:
            SceneMetadata object
        """
        
        logger.info(f"Adding scene to library: {scene_data.get('title', 'Untitled')}")
        
        # Generate or use existing scene ID
        scene_id = scene_data.get("id", str(uuid.uuid4()))
        
        # Auto-generate tags if enabled
        if auto_tagging:
            tags = await self._auto_generate_tags(scene_data, tags)
        
        # Generate semantic embedding if enabled
        embedding = None
        if generate_embedding:
            embedding = await self._generate_embedding(scene_data, tags)
        
        # Create metadata
        metadata = SceneMetadata(
            id=str(uuid.uuid4()),
            scene_id=scene_id,
            title=scene_data.get("title", "Untitled Scene"),
            description=scene_data.get("description", ""),
            duration=scene_data.get("duration", 30.0),
            content_type=scene_data.get("content_type", "explainer"),
            style=scene_data.get("style", "professional"),
            mood=scene_data.get("mood", "neutral"),
            quality_score=scene_data.get("quality_score", 7.0),
            usage_count=0,
            performance_metrics=scene_data.get("performance_metrics", {}),
            tags=tags,
            embedding_vector=embedding,
            file_paths=file_paths,
            created_at=datetime.now().isoformat(),
            last_used=None,
            version=1,
            library_category="experimental"
        )
        
        # Save scene data and metadata
        await self._save_scene_data(scene_id, scene_data)
        await self._save_metadata(metadata)
        await self._save_embedding(scene_id, embedding)
        await self._update_library_index()
        
        # Update statistics
        await self._update_statistics()
        
        logger.info(f"Scene added to library: {metadata.title}")
        return metadata
    
    async def _auto_generate_tags(self, 
                                 scene_data: Dict[str, Any], 
                                 initial_tags: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Auto-generate additional tags based on scene content"""
        
        enhanced_tags = initial_tags.copy()
        
        # Analyze text content for additional tags
        text_content = f"{scene_data.get('title', '')} {scene_data.get('description', '')}"
        
        # Technology tags
        tech_keywords = {
            "ai": ["artificial-intelligence", "machine-learning", "automation"],
            "software": ["apps", "tools", "platforms"],
            "productivity": ["workflow", "efficiency", "time-management"],
            "business": ["corporate", "strategy", "growth"],
            "education": ["learning", "tutorial", "guide"],
            "design": ["visual", "ui", "ux", "creative"],
            "marketing": ["branding", "advertising", "social-media"]
        }
        
        text_lower = text_content.lower()
        
        for keyword, related_tags in tech_keywords.items():
            if keyword in text_lower:
                for tag in related_tags:
                    if tag not in enhanced_tags.get("specific_tags", []):
                        enhanced_tags.setdefault("specific_tags", []).append(tag)
        
        # Mood and style detection
        mood_indicators = {
            "professional": ["corporate", "business", "formal"],
            "casual": ["friendly", "relaxed", "informal"],
            "energetic": ["dynamic", "exciting", "vibrant"],
            "calm": ["peaceful", "soothing", "gentle"],
            "technical": ["detailed", "complex", "advanced"]
        }
        
        for mood, indicators in mood_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                if mood not in enhanced_tags.get("mood_tags", []):
                    enhanced_tags.setdefault("mood_tags", []).append(mood)
        
        # Generic category tags
        if "tutorial" in text_lower or "how to" in text_lower:
            enhanced_tags.setdefault("generic_tags", []).append("education")
        if "review" in text_lower or "comparison" in text_lower:
            enhanced_tags.setdefault("generic_tags", []).append("analysis")
        if "demo" in text_lower or "show" in text_lower:
            enhanced_tags.setdefault("generic_tags", []).append("demonstration")
        
        return enhanced_tags
    
    async def _generate_embedding(self, 
                                 scene_data: Dict[str, Any], 
                                 tags: Dict[str, List[str]]) -> Optional[List[float]]:
        """Generate semantic embedding for scene content"""
        
        # Mock embedding generation - in production would use actual embedding model
        text_for_embedding = f"{scene_data.get('title', '')} {scene_data.get('description', '')}"
        
        # Combine all tags
        all_tags = []
        for tag_list in tags.values():
            all_tags.extend(tag_list)
        
        combined_text = f"{text_for_embedding} {' '.join(all_tags)}"
        
        # Simple mock embedding (1536 dimensions for OpenAI ada-002)
        import random
        random.seed(hash(combined_text) % 1000)  # Deterministic but pseudo-random
        
        embedding = [random.uniform(-1, 1) for _ in range(1536)]
        
        return embedding
    
    async def _save_scene_data(self, scene_id: str, scene_data: Dict[str, Any]):
        """Save raw scene data"""
        scene_file = self.scenes_dir / f"{scene_id}.json"
        with open(scene_file, "w") as f:
            json.dump(scene_data, f, indent=2)
    
    async def _save_metadata(self, metadata: SceneMetadata):
        """Save scene metadata"""
        metadata_file = self.scenes_dir / f"{metadata.scene_id}_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(asdict(metadata), f, indent=2)
    
    async def _save_embedding(self, scene_id: str, embedding: Optional[List[float]]):
        """Save embedding vector"""
        if embedding:
            embedding_file = self.embeddings_dir / f"{scene_id}.pkl"
            with open(embedding_file, "wb") as f:
                pickle.dump(embedding, f)
    
    async def _update_library_index(self):
        """Update the main library index"""
        
        # Scan all metadata files
        metadata_files = list(self.scenes_dir.glob("*_metadata.json"))
        
        index_data = {
            "last_updated": datetime.now().isoformat(),
            "total_scenes": len(metadata_files),
            "scenes": []
        }
        
        for metadata_file in metadata_files:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
                
                # Add to index (lightweight version)
                index_entry = {
                    "id": metadata["id"],
                    "scene_id": metadata["scene_id"],
                    "title": metadata["title"],
                    "tags": metadata["tags"],
                    "quality_score": metadata["quality_score"],
                    "usage_count": metadata["usage_count"],
                    "content_type": metadata["content_type"]
                }
                index_data["scenes"].append(index_entry)
        
        with open(self.index_file, "w") as f:
            json.dump(index_data, f, indent=2)
    
    async def search_scenes(self, 
                           query: SearchQuery) -> List[SearchResult]:
        """
        Search scenes in the content library
        
        Args:
            query: SearchQuery object with search criteria
            
        Returns:
            List of SearchResult objects ranked by relevance
        """
        
        logger.info(f"Searching scenes with query: {query}")
        
        # Load library index
        if not self.index_file.exists():
            logger.warning("Library index not found")
            return []
        
        with open(self.index_file, "r") as f:
            index_data = json.load(f)
        
        # Filter scenes based on criteria
        candidate_scenes = []
        
        for scene_entry in index_data["scenes"]:
            # Apply filters
            if not self._passes_filters(scene_entry, query):
                continue
            
            # Calculate relevance score
            similarity_score = await self._calculate_relevance(scene_entry, query)
            
            if similarity_score >= query.similarity_threshold:
                candidate_scenes.append((scene_entry, similarity_score))
        
        # Sort by relevance score
        candidate_scenes.sort(key=lambda x: x[1], reverse=True)
        
        # Load full metadata for top results
        results = []
        for scene_entry, similarity_score in candidate_scenes[:query.limit]:
            metadata = await self._load_metadata(scene_entry["scene_id"])
            if metadata:
                result = SearchResult(
                    scene=metadata,
                    similarity_score=similarity_score,
                    match_reasons=await self._get_match_reasons(scene_entry, query)
                )
                results.append(result)
        
        logger.info(f"Found {len(results)} matching scenes")
        return results
    
    def _passes_filters(self, scene_entry: Dict[str, Any], query: SearchQuery) -> bool:
        """Check if scene passes all filters"""
        
        # Quality filter
        if scene_entry["quality_score"] < query.quality_threshold:
            return False
        
        # Duration filter
        metadata_file = self.scenes_dir / f"{scene_entry['scene_id']}_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
                duration = metadata["duration"]
                if not (query.duration_range[0] <= duration <= query.duration_range[1]):
                    return False
        
        # Content type filter
        if query.content_types and scene_entry["content_type"] not in query.content_types:
            return False
        
        # Tag filter
        if query.tags:
            scene_tags = []
            for tag_list in scene_entry["tags"].values():
                scene_tags.extend(tag_list)
            
            if not any(tag in scene_tags for tag in query.tags):
                return False
        
        return True
    
    async def _calculate_relevance(self, 
                                  scene_entry: Dict[str, Any], 
                                  query: SearchQuery) -> float:
        """Calculate relevance score for a scene"""
        
        score = 0.0
        
        # Quality score contribution (30%)
        quality_score = scene_entry["quality_score"] / 10.0
        score += quality_score * 0.3
        
        # Usage count contribution (20%)
        usage_score = min(scene_entry["usage_count"] / 10.0, 1.0)
        score += usage_score * 0.2
        
        # Tag matching contribution (25%)
        if query.tags:
            scene_tags = []
            for tag_list in scene_entry["tags"].values():
                scene_tags.extend(tag_list)
            
            matching_tags = [tag for tag in query.tags if tag in scene_tags]
            tag_score = len(matching_tags) / len(query.tags) if query.tags else 0
            score += tag_score * 0.25
        
        # Content type match (10%)
        if query.content_types and scene_entry["content_type"] in query.content_types:
            score += 0.1
        
        # Text similarity (15%) - would use actual embedding similarity in production
        if query.query_text:
            text_similarity = await self._calculate_text_similarity(
                query.query_text, scene_entry
            )
            score += text_similarity * 0.15
        
        return min(score, 1.0)
    
    async def _calculate_text_similarity(self, 
                                        query_text: str, 
                                        scene_entry: Dict[str, Any]) -> float:
        """Calculate text similarity between query and scene"""
        
        # Simple word overlap similarity - would use embeddings in production
        query_words = set(query_text.lower().split())
        scene_words = set(scene_entry["title"].lower().split())
        
        if not query_words or not scene_words:
            return 0.0
        
        overlap = len(query_words.intersection(scene_words))
        union = len(query_words.union(scene_words))
        
        return overlap / union if union > 0 else 0.0
    
    async def _get_match_reasons(self, 
                                scene_entry: Dict[str, Any], 
                                query: SearchQuery) -> List[str]:
        """Get reasons why this scene matched the query"""
        
        reasons = []
        
        # Quality match
        if scene_entry["quality_score"] >= 8.0:
            reasons.append("High quality score")
        
        # Popularity match
        if scene_entry["usage_count"] >= 5:
            reasons.append("Frequently used")
        
        # Tag matches
        if query.tags:
            scene_tags = []
            for tag_list in scene_entry["tags"].values():
                scene_tags.extend(tag_list)
            
            matching_tags = [tag for tag in query.tags if tag in scene_tags]
            if matching_tags:
                reasons.append(f"Matches tags: {', '.join(matching_tags)}")
        
        # Content type match
        if query.content_types and scene_entry["content_type"] in query.content_types:
            reasons.append(f"Content type: {scene_entry['content_type']}")
        
        return reasons
    
    async def _load_metadata(self, scene_id: str) -> Optional[SceneMetadata]:
        """Load scene metadata"""
        
        metadata_file = self.scenes_dir / f"{scene_id}_metadata.json"
        if not metadata_file.exists():
            return None
        
        with open(metadata_file, "r") as f:
            data = json.load(f)
            return SceneMetadata(**data)
    
    async def update_scene_usage(self, scene_id: str, 
                                performance_data: Optional[Dict[str, float]] = None):
        """Update scene usage count and performance metrics"""
        
        metadata_file = self.scenes_dir / f"{scene_id}_metadata.json"
        if not metadata_file.exists():
            return
        
        with open(metadata_file, "r") as f:
            data = json.load(f)
        
        # Update usage count
        data["usage_count"] = data.get("usage_count", 0) + 1
        data["last_used"] = datetime.now().isoformat()
        
        # Update performance metrics
        if performance_data:
            data["performance_metrics"].update(performance_data)
            
            # Recalculate quality score based on performance
            data["quality_score"] = self._calculate_quality_from_performance(
                data["performance_metrics"]
            )
        
        # Save updated metadata
        with open(metadata_file, "w") as f:
            json.dump(data, f, indent=2)
        
        # Update index
        await self._update_library_index()
        
        logger.info(f"Updated usage for scene: {scene_id}")
    
    def _calculate_quality_from_performance(self, 
                                           metrics: Dict[str, float]) -> float:
        """Calculate quality score from performance metrics"""
        
        # Weighted performance metrics
        weights = {
            "engagement_rate": 0.3,
            "completion_rate": 0.25,
            "click_through_rate": 0.2,
            "sentiment_score": 0.15,
            "view_count": 0.1
        }
        
        # Normalize metrics and calculate weighted score
        normalized_scores = []
        
        for metric, weight in weights.items():
            if metric in metrics:
                value = metrics[metric]
                
                # Normalize based on metric type
                if metric == "engagement_rate":
                    normalized = min(value / 0.1, 1.0)  # 10% is excellent
                elif metric == "completion_rate":
                    normalized = min(value / 0.8, 1.0)  # 80% is excellent
                elif metric == "click_through_rate":
                    normalized = min(value / 0.05, 1.0)  # 5% is excellent
                elif metric == "sentiment_score":
                    normalized = (value + 1) / 2  # Convert -1,1 to 0,1
                elif metric == "view_count":
                    normalized = min(value / 10000, 1.0)  # 10k views is excellent
                else:
                    normalized = value
                
                normalized_scores.append(normalized * weight)
        
        # Calculate final quality score (0-10)
        quality_score = sum(normalized_scores) * 10
        return min(quality_score, 10.0)
    
    async def get_similar_scenes(self, 
                                scene_id: str, 
                                limit: int = 5,
                                similarity_threshold: float = 0.7) -> List[SearchResult]:
        """Find scenes similar to a given scene"""
        
        metadata = await self._load_metadata(scene_id)
        if not metadata:
            return []
        
        # Create search query based on scene characteristics
        query = SearchQuery(
            query_text=f"{metadata.title} {metadata.description}",
            tags=metadata.tags.get("specific_tags", []) + metadata.tags.get("generic_tags", []),
            duration_range=(metadata.duration * 0.7, metadata.duration * 1.3),
            content_types=[metadata.content_type],
            quality_threshold=6.0,
            platform=None,
            limit=limit * 2,  # Get more to filter out the original
            similarity_threshold=similarity_threshold
        )
        
        # Search for similar scenes
        results = await self.search_scenes(query)
        
        # Remove the original scene and return top results
        similar_scenes = [r for r in results if r.scene.scene_id != scene_id][:limit]
        
        return similar_scenes
    
    async def get_content_library_stats(self) -> Dict[str, Any]:
        """Get statistics about the content library"""
        
        if not self.index_file.exists():
            return self.stats
        
        with open(self.index_file, "r") as f:
            index_data = json.load(f)
        
        # Calculate updated statistics
        total_scenes = len(index_data["scenes"])
        
        # Average quality
        quality_scores = [s["quality_score"] for s in index_data["scenes"]]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Most used scenes
        most_used = sorted(index_data["scenes"], 
                          key=lambda x: x["usage_count"], reverse=True)[:5]
        
        # Recently added (last 7 days)
        cutoff_date = datetime.now() - timedelta(days=7)
        recently_added = []
        
        for scene in index_data["scenes"]:
            metadata_file = self.scenes_dir / f"{scene['scene_id']}_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                    created_at = datetime.fromisoformat(metadata["created_at"])
                    if created_at >= cutoff_date:
                        recently_added.append(scene)
        
        # Performance leaders (high quality + high usage)
        performance_scores = []
        for scene in index_data["scenes"]:
            performance = scene["quality_score"] * 0.6 + scene["usage_count"] * 0.4
            performance_scores.append((scene, performance))
        
        performance_leaders = sorted(performance_scores, 
                                   key=lambda x: x[1], reverse=True)[:5]
        
        self.stats = {
            "total_scenes": total_scenes,
            "total_tags": len(set(tag for scene in index_data["scenes"] 
                                for tags in scene["tags"].values() 
                                for tag in tags)),
            "average_quality": round(avg_quality, 2),
            "most_used_scenes": [{"id": s["scene_id"], "title": s["title"], "count": s["usage_count"]} 
                               for s in most_used],
            "recently_added": [{"id": s["scene_id"], "title": s["title"]} 
                              for s in recently_added[-5:]],
            "performance_leaders": [{"id": s["scene_id"], "title": s["title"], "score": round(perf, 2)} 
                                  for s, perf in performance_leaders]
        }
        
        return self.stats
    
    async def export_library(self, export_path: str, format: str = "json"):
        """Export content library to file"""
        
        if not self.index_file.exists():
            raise ValueError("Library index not found")
        
        with open(self.index_file, "r") as f:
            index_data = json.load(f)
        
        # Add full metadata for each scene
        export_data = {
            "export_info": {
                "exported_at": datetime.now().isoformat(),
                "total_scenes": len(index_data["scenes"]),
                "format": format
            },
            "scenes": []
        }
        
        for scene_entry in index_data["scenes"]:
            metadata = await self._load_metadata(scene_entry["scene_id"])
            if metadata:
                export_data["scenes"].append(asdict(metadata))
        
        # Save export file
        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Library exported to: {export_path}")

# Factory class for library management
class ContentLibraryFactory:
    """Factory for managing content library instances"""
    
    _libraries = {}
    
    @classmethod
    def get_library(cls, library_id: str = "default") -> ContentLibraryManager:
        """Get or create content library instance"""
        
        if library_id not in cls._libraries:
            library_dir = f"/workspace/content-creator/content-library/{library_id}"
            cls._libraries[library_id] = ContentLibraryManager(library_dir)
        
        return cls._libraries[library_id]

# Example usage
async def main():
    """Example usage of the content library system"""
    
    # Get library instance
    library = ContentLibraryFactory.get_library()
    
    # Sample scene data
    sample_scene = {
        "id": "scene_001",
        "title": "AI Productivity Tools Overview",
        "description": "Comprehensive guide to AI tools that can improve your daily productivity",
        "duration": 60.0,
        "content_type": "explainer",
        "style": "professional",
        "mood": "educational",
        "quality_score": 8.5
    }
    
    # Sample tags
    sample_tags = {
        "specific_tags": ["ai-tools", "productivity", "automation"],
        "generic_tags": ["technology", "business", "education"],
        "mood_tags": ["educational", "professional"],
        "style_tags": ["modern", "clean"]
    }
    
    # Sample file paths
    sample_files = {
        "video": "/workspace/content-creator/generated-content/videos/scene_001.mp4",
        "audio": "/workspace/content-creator/generated-content/audio/scene_001.mp3",
        "thumbnail": "/workspace/content-creator/generated-content/thumbnails/scene_001.jpg"
    }
    
    # Add scene to library
    metadata = await library.add_scene_to_library(
        scene_data=sample_scene,
        tags=sample_tags,
        file_paths=sample_files
    )
    
    print(f"Scene added to library: {metadata.title}")
    print(f"Tags: {metadata.tags}")
    
    # Search for scenes
    search_query = SearchQuery(
        query_text="productivity tools",
        tags=["productivity", "ai-tools"],
        duration_range=(30, 120),
        content_types=["explainer"],
        quality_threshold=7.0,
        platform=None,
        limit=10,
        similarity_threshold=0.5
    )
    
    results = await library.search_scenes(search_query)
    print(f"Found {len(results)} matching scenes")
    
    # Get library statistics
    stats = await library.get_content_library_stats()
    print(f"Library stats: {stats}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())