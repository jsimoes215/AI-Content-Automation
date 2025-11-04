"""
Configuration settings for Platform Timing Service

This module handles configuration management for the platform timing service,
including database connections, API settings, and environment variables.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    supabase_url: str
    supabase_key: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30


@dataclass
class APIConfig:
    """API configuration settings"""
    base_url: str
    api_key: str
    timeout: int = 30
    max_retries: int = 3
    rate_limit_per_minute: int = 100


@dataclass
class ServiceConfig:
    """Main service configuration"""
    database: DatabaseConfig
    api: APIConfig
    logging_level: str = "INFO"
    timezone_default: str = "UTC"
    cache_ttl: int = 3600  # 1 hour
    enable_monitoring: bool = True


def load_config_from_env() -> ServiceConfig:
    """
    Load configuration from environment variables
    
    Returns:
        ServiceConfig: Configuration object
    """
    # Database configuration
    database_config = DatabaseConfig(
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_key=os.getenv("SUPABASE_KEY", ""),
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
        pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30"))
    )
    
    # API configuration
    api_config = APIConfig(
        base_url=os.getenv("API_BASE_URL", "http://localhost:8000"),
        api_key=os.getenv("API_KEY", ""),
        timeout=int(os.getenv("API_TIMEOUT", "30")),
        max_retries=int(os.getenv("API_MAX_RETRIES", "3")),
        rate_limit_per_minute=int(os.getenv("API_RATE_LIMIT", "100"))
    )
    
    # Main service configuration
    service_config = ServiceConfig(
        database=database_config,
        api=api_config,
        logging_level=os.getenv("LOGGING_LEVEL", "INFO"),
        timezone_default=os.getenv("TIMEZONE_DEFAULT", "UTC"),
        cache_ttl=int(os.getenv("CACHE_TTL", "3600")),
        enable_monitoring=os.getenv("ENABLE_MONITORING", "true").lower() == "true"
    )
    
    return service_config


def validate_config(config: ServiceConfig) -> bool:
    """
    Validate configuration settings
    
    Args:
        config: Service configuration to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Check required database settings
    if not config.database.supabase_url:
        raise ValueError("SUPABASE_URL environment variable is required")
    
    if not config.database.supabase_key:
        raise ValueError("SUPABASE_KEY environment variable is required")
    
    # Check required API settings
    if not config.api.api_key:
        raise ValueError("API_KEY environment variable is required")
    
    return True


# Default configuration for development
DEFAULT_CONFIG = ServiceConfig(
    database=DatabaseConfig(
        supabase_url="",
        supabase_key=""
    ),
    api=APIConfig(
        base_url="http://localhost:8000",
        api_key=""
    ),
    logging_level="INFO",
    timezone_default="UTC",
    cache_ttl=3600,
    enable_monitoring=True
)