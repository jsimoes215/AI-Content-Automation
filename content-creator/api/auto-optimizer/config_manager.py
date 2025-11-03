"""
Configuration Manager Module

Manages optimization settings, preferences, and system configuration.
"""

import json
import os
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class OptimizationConfig:
    """Configuration for optimization settings."""
    name: str
    description: str
    enabled: bool = True
    priority: int = 50  # 0-100, higher = more important
    parameters: Dict[str, Any] = None
    constraints: Dict[str, Any] = None
    success_threshold: float = 0.1  # Minimum improvement to be considered successful
    max_applications_per_day: int = 10
    auto_apply: bool = False
    last_updated: str = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.constraints is None:
            self.constraints = {}
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()


@dataclass
class PlatformConfig:
    """Platform-specific optimization configuration."""
    platform_name: str
    optimization_rules: Dict[str, Any]
    content_preferences: Dict[str, Any]
    performance_thresholds: Dict[str, float]
    success_metrics: List[str]
    enabled: bool = True
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()


class ConfigManager:
    """Manages configuration for the auto-optimizer system."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.optimization_configs: Dict[str, OptimizationConfig] = {}
        self.platform_configs: Dict[str, PlatformConfig] = {}
        self.global_settings = {}
        
        # Load existing configurations
        self._load_configurations()
        
        # Initialize default configurations if none exist
        if not self.optimization_configs:
            self._create_default_configs()
    
    def get_optimization_config(self, config_name: str) -> Optional[OptimizationConfig]:
        """Get optimization configuration by name."""
        return self.optimization_configs.get(config_name)
    
    def update_optimization_config(self, config: OptimizationConfig) -> bool:
        """Update an optimization configuration."""
        try:
            config.last_updated = datetime.now().isoformat()
            self.optimization_configs[config.name] = config
            self._save_optimization_config(config)
            return True
        except Exception as e:
            print(f"Error updating optimization config: {e}")
            return False
    
    def get_platform_config(self, platform_name: str) -> Optional[PlatformConfig]:
        """Get platform-specific configuration."""
        return self.platform_configs.get(platform_name.lower())
    
    def update_platform_config(self, config: PlatformConfig) -> bool:
        """Update platform-specific configuration."""
        try:
            config.platform_name = config.platform_name.lower()
            config.updated_at = datetime.now().isoformat()
            self.platform_configs[config.platform_name] = config
            self._save_platform_config(config)
            return True
        except Exception as e:
            print(f"Error updating platform config: {e}")
            return False
    
    def get_global_setting(self, key: str, default: Any = None) -> Any:
        """Get a global setting value."""
        return self.global_settings.get(key, default)
    
    def set_global_setting(self, key: str, value: Any) -> bool:
        """Set a global setting value."""
        try:
            self.global_settings[key] = value
            self._save_global_settings()
            return True
        except Exception as e:
            print(f"Error setting global setting: {e}")
            return False
    
    def get_active_optimizations(self, context: Dict[str, Any]) -> List[OptimizationConfig]:
        """Get list of active optimizations applicable to the context."""
        active_configs = []
        
        for config in self.optimization_configs.values():
            if not config.enabled:
                continue
            
            # Check if optimization applies to this context
            if self._is_applicable_to_context(config, context):
                active_configs.append(config)
        
        # Sort by priority
        active_configs.sort(key=lambda x: x.priority, reverse=True)
        return active_configs
    
    def check_optimization_limits(self, config_name: str, current_date: str = None) -> Dict[str, Any]:
        """Check if optimization is within daily limits."""
        if current_date is None:
            current_date = datetime.now().strftime('%Y-%m-%d')
        
        config = self.get_optimization_config(config_name)
        if not config:
            return {"error": "Configuration not found"}
        
        # Get usage statistics (simplified implementation)
        usage_file = self.config_dir / f"{config_name}_usage.json"
        usage_data = {}
        
        if usage_file.exists():
            try:
                with open(usage_file, 'r') as f:
                    usage_data = json.load(f)
            except Exception:
                usage_data = {}
        
        today_usage = usage_data.get(current_date, 0)
        limit = config.max_applications_per_day
        
        return {
            "config_name": config_name,
            "date": current_date,
            "current_usage": today_usage,
            "daily_limit": limit,
            "can_apply": today_usage < limit,
            "remaining_applications": max(0, limit - today_usage)
        }
    
    def increment_usage(self, config_name: str, current_date: str = None) -> bool:
        """Increment usage count for optimization."""
        if current_date is None:
            current_date = datetime.now().strftime('%Y-%m-%d')
        
        usage_file = self.config_dir / f"{config_name}_usage.json"
        usage_data = {}
        
        # Load existing usage data
        if usage_file.exists():
            try:
                with open(usage_file, 'r') as f:
                    usage_data = json.load(f)
            except Exception:
                usage_data = {}
        
        # Increment today's usage
        usage_data[current_date] = usage_data.get(current_date, 0) + 1
        
        try:
            with open(usage_file, 'w') as f:
                json.dump(usage_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error updating usage data: {e}")
            return False
    
    def reset_daily_usage(self, date: str = None) -> bool:
        """Reset daily usage statistics (typically called daily)."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Reset all optimization usage files
            for usage_file in self.config_dir.glob("*_usage.json"):
                try:
                    with open(usage_file, 'r') as f:
                        usage_data = json.load(f)
                    
                    # Keep only recent days (last 7 days)
                    cutoff_date = datetime.strptime(date, '%Y-%m-%d') - timedelta(days=7)
                    filtered_data = {
                        day: count for day, count in usage_data.items()
                        if datetime.strptime(day, '%Y-%m-%d') >= cutoff_date
                    }
                    
                    with open(usage_file, 'w') as f:
                        json.dump(filtered_data, f, indent=2)
                        
                except Exception as e:
                    print(f"Error processing usage file {usage_file}: {e}")
            
            return True
        except Exception as e:
            print(f"Error resetting daily usage: {e}")
            return False
    
    def export_configuration(self, filepath: str) -> bool:
        """Export all configurations to a file."""
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "optimization_configs": {
                    name: asdict(config) for name, config in self.optimization_configs.items()
                },
                "platform_configs": {
                    name: asdict(config) for name, config in self.platform_configs.items()
                },
                "global_settings": self.global_settings
            }
            
            # Determine file format
            if filepath.endswith('.yaml') or filepath.endswith('.yml'):
                with open(filepath, 'w') as f:
                    yaml.dump(export_data, f, indent=2, default=str)
            else:
                with open(filepath, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"Error exporting configuration: {e}")
            return False
    
    def import_configuration(self, filepath: str) -> bool:
        """Import configurations from a file."""
        try:
            # Determine file format
            if filepath.endswith('.yaml') or filepath.endswith('.yml'):
                with open(filepath, 'r') as f:
                    import_data = yaml.safe_load(f)
            else:
                with open(filepath, 'r') as f:
                    import_data = json.load(f)
            
            # Import optimization configs
            if "optimization_configs" in import_data:
                for name, config_data in import_data["optimization_configs"].items():
                    # Convert dict back to OptimizationConfig
                    config_data['last_updated'] = datetime.now().isoformat()
                    config = OptimizationConfig(**config_data)
                    self.optimization_configs[name] = config
            
            # Import platform configs
            if "platform_configs" in import_data:
                for name, config_data in import_data["platform_configs"].items():
                    config_data['updated_at'] = datetime.now().isoformat()
                    config = PlatformConfig(**config_data)
                    self.platform_configs[config.platform_name] = config
            
            # Import global settings
            if "global_settings" in import_data:
                self.global_settings.update(import_data["global_settings"])
            
            # Save all configurations
            self._save_all_configurations()
            return True
            
        except Exception as e:
            print(f"Error importing configuration: {e}")
            return False
    
    def _is_applicable_to_context(self, config: OptimizationConfig, context: Dict[str, Any]) -> bool:
        """Check if optimization configuration applies to the given context."""
        constraints = config.constraints
        
        if not constraints:
            return True
        
        # Check content type constraint
        if 'content_type' in constraints:
            if context.get('content_type') not in constraints['content_type']:
                return False
        
        # Check platform constraint
        if 'platform' in constraints:
            if context.get('platform') not in constraints['platform']:
                return False
        
        # Check minimum performance threshold
        if 'min_performance' in constraints:
            if context.get('performance_score', 0) < constraints['min_performance']:
                return False
        
        # Check time constraints (e.g., only apply during business hours)
        if 'business_hours_only' in constraints:
            if constraints['business_hours_only']:
                current_hour = datetime.now().hour
                if not (9 <= current_hour <= 17):  # 9 AM to 5 PM
                    return False
        
        return True
    
    def _load_configurations(self):
        """Load existing configurations from files."""
        # Load optimization configurations
        optimization_dir = self.config_dir / "optimizations"
        if optimization_dir.exists():
            for config_file in optimization_dir.glob("*.json"):
                try:
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                    
                    config = OptimizationConfig(**config_data)
                    self.optimization_configs[config.name] = config
                except Exception as e:
                    print(f"Error loading optimization config {config_file}: {e}")
        
        # Load platform configurations
        platform_dir = self.config_dir / "platforms"
        if platform_dir.exists():
            for config_file in platform_dir.glob("*.json"):
                try:
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                    
                    config = PlatformConfig(**config_data)
                    self.platform_configs[config.platform_name] = config
                except Exception as e:
                    print(f"Error loading platform config {config_file}: {e}")
        
        # Load global settings
        global_settings_file = self.config_dir / "global_settings.json"
        if global_settings_file.exists():
            try:
                with open(global_settings_file, 'r') as f:
                    self.global_settings = json.load(f)
            except Exception as e:
                print(f"Error loading global settings: {e}")
    
    def _save_optimization_config(self, config: OptimizationConfig):
        """Save optimization configuration to file."""
        optimization_dir = self.config_dir / "optimizations"
        optimization_dir.mkdir(exist_ok=True)
        
        config_file = optimization_dir / f"{config.name}.json"
        with open(config_file, 'w') as f:
            json.dump(asdict(config), f, indent=2)
    
    def _save_platform_config(self, config: PlatformConfig):
        """Save platform configuration to file."""
        platform_dir = self.config_dir / "platforms"
        platform_dir.mkdir(exist_ok=True)
        
        config_file = platform_dir / f"{config.platform_name}.json"
        with open(config_file, 'w') as f:
            json.dump(asdict(config), f, indent=2)
    
    def _save_global_settings(self):
        """Save global settings to file."""
        global_settings_file = self.config_dir / "global_settings.json"
        with open(global_settings_file, 'w') as f:
            json.dump(self.global_settings, f, indent=2)
    
    def _save_all_configurations(self):
        """Save all configurations to files."""
        # Save optimization configurations
        for config in self.optimization_configs.values():
            self._save_optimization_config(config)
        
        # Save platform configurations
        for config in self.platform_configs.values():
            self._save_platform_config(config)
        
        # Save global settings
        self._save_global_settings()
    
    def _create_default_configs(self):
        """Create default configurations."""
        # Default optimization configurations
        title_opt = OptimizationConfig(
            name="title_enhancement",
            description="Optimize titles for better engagement",
            priority=80,
            parameters={
                "min_length": 30,
                "max_length": 100,
                "power_words": ["amazing", "secret", "ultimate", "proven"],
                "engagement_triggers": ["?", "!", "..."]
            },
            constraints={
                "business_hours_only": False
            },
            max_applications_per_day=20,
            auto_apply=True
        )
        
        tag_opt = OptimizationConfig(
            name="tag_optimization",
            description="Optimize tags for better discoverability",
            priority=70,
            parameters={
                "min_tags": 5,
                "max_tags": 10,
                "trending_weight": 0.3,
                "performance_weight": 0.7
            },
            max_applications_per_day=15,
            auto_apply=True
        )
        
        timing_opt = OptimizationConfig(
            name="timing_optimization",
            description="Suggest optimal posting times",
            priority=60,
            parameters={
                "lookback_days": 30,
                "min_sample_size": 10,
                "confidence_threshold": 0.7
            },
            max_applications_per_day=10,
            auto_apply=False
        )
        
        # Default platform configurations
        youtube_config = PlatformConfig(
            platform_name="youtube",
            optimization_rules={
                "title_length_limit": 100,
                "description_length_limit": 5000,
                "tag_limit": 15,
                "thumbnail_required": True
            },
            content_preferences={
                "optimal_video_length": 300,  # seconds
                "engagement_hooks": [
                    "In this video",
                    "Today we're going to",
                    "Let me show you"
                ],
                "call_to_action": "Subscribe for more content"
            },
            performance_thresholds={
                "minimum_views": 100,
                "target_ctr": 0.05,
                "target_engagement_rate": 0.03
            },
            success_metrics=["views", "likes", "comments", "shares", "subscriber_growth"]
        )
        
        instagram_config = PlatformConfig(
            platform_name="instagram",
            optimization_rules={
                "caption_length_limit": 2200,
                "hashtag_limit": 30,
                "story_length_limit": 15,
                "reel_length_limit": 90
            },
            content_preferences={
                "visual_focus": True,
                "hashtag_style": "mix_popular_niche",
                "posting_frequency": "daily",
                "optimal_times": ["09:00", "12:00", "17:00", "19:00"]
            },
            performance_thresholds={
                "minimum_reach": 50,
                "target_engagement_rate": 0.04,
                "target_save_rate": 0.01
            },
            success_metrics=["reach", "engagement", "saves", "shares", "profile_visits"]
        )
        
        # Default global settings
        default_global_settings = {
            "optimization_enabled": True,
            "auto_learning_enabled": True,
            "min_improvement_threshold": 0.05,
            "max_concurrent_optimizations": 3,
            "learning_rate": 0.01,
            "performance_tracking_days": 30,
            "confidence_threshold": 0.7,
            "daily_optimization_limit": 50,
            "notification_enabled": True
        }
        
        # Add to configurations
        self.optimization_configs.update({
            "title_enhancement": title_opt,
            "tag_optimization": tag_opt,
            "timing_optimization": timing_opt
        })
        
        self.platform_configs.update({
            "youtube": youtube_config,
            "instagram": instagram_config
        })
        
        self.global_settings.update(default_global_settings)
        
        # Save all configurations
        self._save_all_configurations()
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of all configurations."""
        return {
            "optimization_configs": {
                name: {
                    "enabled": config.enabled,
                    "priority": config.priority,
                    "auto_apply": config.auto_apply,
                    "last_updated": config.last_updated
                }
                for name, config in self.optimization_configs.items()
            },
            "platform_configs": {
                name: {
                    "enabled": config.enabled,
                    "success_metrics": config.success_metrics,
                    "updated_at": config.updated_at
                }
                for name, config in self.platform_configs.items()
            },
            "global_settings": self.global_settings,
            "total_optimizations": len(self.optimization_configs),
            "total_platforms": len(self.platform_configs),
            "auto_apply_enabled": sum(1 for config in self.optimization_configs.values() if config.auto_apply)
        }