"""
API Key Management System for Comment Scraping.

This module handles secure storage, validation, and rotation of API keys
for all supported platforms in compliance with security best practices.
"""

import os
import json
import base64
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

from ..models.comment_models import Platform
from ..config.settings import settings

logger = logging.getLogger(__name__)


class APIKeyManager:
    """Manages API keys securely for all platforms."""
    
    def __init__(self, master_password: Optional[str] = None):
        """
        Initialize API key manager.
        
        Args:
            master_password: Master password for encryption (if None, uses environment)
        """
        self._platform_keys: Dict[Platform, str] = {}
        self._key_metadata: Dict[Platform, Dict] = {}
        self._encryption_key = self._derive_encryption_key(master_password)
        self._cipher_suite = Fernet(self._encryption_key)
        
        # Load keys from environment and validate
        self._load_keys_from_environment()
        
        logger.info("API Key Manager initialized")
    
    def _derive_encryption_key(self, master_password: Optional[str] = None) -> bytes:
        """Derive encryption key from master password."""
        if master_password is None:
            master_password = os.environ.get("COMMENT_SCRAPER_MASTER_KEY", "default_key_change_in_production")
        
        # Use PBKDF2 to derive key from password
        password = master_password.encode()
        salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def _load_keys_from_environment(self) -> None:
        """Load API keys from environment variables."""
        env_mappings = {
            Platform.YOUTUBE: "YOUTUBE_API_KEY",
            Platform.TWITTER: "TWITTER_BEARER_TOKEN", 
            Platform.INSTAGRAM: "INSTAGRAM_ACCESS_TOKEN",
            Platform.TIKTOK: "TIKTOK_CLIENT_KEY"
        }
        
        for platform, env_var in env_mappings.items():
            key = os.environ.get(env_var)
            if key:
                self._platform_keys[platform] = key
                self._key_metadata[platform] = {
                    "loaded_from": env_var,
                    "loaded_at": datetime.utcnow().isoformat(),
                    "last_validated": None,
                    "validation_status": "not_validated"
                }
                logger.info(f"Loaded API key for {platform} from environment")
            else:
                logger.warning(f"No API key found for {platform} in {env_var}")
    
    def get_api_key(self, platform: Platform) -> Optional[str]:
        """
        Get API key for a platform.
        
        Args:
            platform: Platform to get key for
            
        Returns:
            API key if available, None otherwise
        """
        return self._platform_keys.get(platform)
    
    def set_api_key(self, platform: Platform, key: str, validate: bool = True) -> bool:
        """
        Set API key for a platform.
        
        Args:
            platform: Platform to set key for
            key: API key value
            validate: Whether to validate the key
            
        Returns:
            True if key was set successfully
        """
        try:
            self._platform_keys[platform] = key
            self._key_metadata[platform] = {
                "loaded_from": "manual",
                "loaded_at": datetime.utcnow().isoformat(),
                "last_validated": None,
                "validation_status": "not_validated" if not validate else "validating"
            }
            
            if validate:
                # Validate the key asynchronously
                asyncio.create_task(self._validate_key_async(platform))
            
            logger.info(f"API key set for {platform}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set API key for {platform}: {e}")
            return False
    
    async def _validate_key_async(self, platform: Platform) -> bool:
        """Validate API key asynchronously."""
        try:
            key = self._platform_keys.get(platform)
            if not key:
                return False
            
            is_valid = await self._validate_key(platform, key)
            
            self._key_metadata[platform]["last_validated"] = datetime.utcnow().isoformat()
            self._key_metadata[platform]["validation_status"] = "valid" if is_valid else "invalid"
            
            if is_valid:
                logger.info(f"API key validated successfully for {platform}")
            else:
                logger.warning(f"API key validation failed for {platform}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating API key for {platform}: {e}")
            self._key_metadata[platform]["validation_status"] = "error"
            return False
    
    async def _validate_key(self, platform: Platform, key: str) -> bool:
        """Validate API key with platform-specific logic."""
        try:
            if platform == Platform.YOUTUBE:
                return await self._validate_youtube_key(key)
            elif platform == Platform.TWITTER:
                return await self._validate_twitter_key(key)
            elif platform == Platform.INSTAGRAM:
                return await self._validate_instagram_key(key)
            elif platform == Platform.TIKTOK:
                return await self._validate_tiktok_key(key)
            else:
                logger.error(f"No validation logic implemented for {platform}")
                return False
                
        except Exception as e:
            logger.error(f"Validation error for {platform}: {e}")
            return False
    
    async def _validate_youtube_key(self, key: str) -> bool:
        """Validate YouTube API key."""
        import aiohttp
        
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {"part": "snippet", "id": "dQw4w9WgXcQ", "key": key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def _validate_twitter_key(self, key: str) -> bool:
        """Validate Twitter Bearer Token."""
        import aiohttp
        
        url = "https://api.twitter.com/2/users/me"
        headers = {"Authorization": f"Bearer {key}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def _validate_instagram_key(self, key: str) -> bool:
        """Validate Instagram access token."""
        import aiohttp
        
        url = "https://graph.facebook.com/v18.0/me"
        params = {"access_token": key, "fields": "id,name"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def _validate_tiktok_key(self, key: str) -> bool:
        """Validate TikTok client key."""
        # TikTok validation would require additional setup
        # For now, just check if it's properly formatted
        return len(key) > 10 and key.isalnum()
    
    async def validate_all_keys(self) -> Dict[Platform, bool]:
        """Validate all loaded API keys."""
        validation_results = {}
        
        for platform in Platform:
            key = self._platform_keys.get(platform)
            if key:
                validation_results[platform] = await self._validate_key(platform, key)
            else:
                validation_results[platform] = False
        
        return validation_results
    
    def get_key_status(self, platform: Platform) -> Optional[Dict]:
        """Get status and metadata for a platform's API key."""
        return self._key_metadata.get(platform)
    
    def get_all_key_status(self) -> Dict[Platform, Dict]:
        """Get status for all platform API keys."""
        return dict(self._key_metadata)
    
    def has_valid_key(self, platform: Platform) -> bool:
        """Check if platform has a valid API key."""
        metadata = self._key_metadata.get(platform)
        if not metadata:
            return False
        
        status = metadata.get("validation_status", "not_validated")
        return status == "valid"
    
    def get_available_platforms(self) -> List[Platform]:
        """Get list of platforms with valid API keys."""
        return [platform for platform in Platform if self.has_valid_key(platform)]
    
    def rotate_key(self, platform: Platform, new_key: str) -> bool:
        """
        Rotate API key for a platform.
        
        Args:
            platform: Platform to rotate key for
            new_key: New API key
            
        Returns:
            True if rotation was successful
        """
        try:
            old_key = self._platform_keys.get(platform)
            
            # Set new key
            success = self.set_api_key(platform, new_key, validate=True)
            
            if success:
                # Log key rotation (without exposing the actual key)
                old_key_hash = hashlib.sha256(old_key.encode()).hexdigest()[:8] if old_key else "none"
                new_key_hash = hashlib.sha256(new_key.encode()).hexdigest()[:8]
                
                logger.info(
                    f"API key rotated for {platform}. "
                    f"Old key hash: {old_key_hash}, New key hash: {new_key_hash}"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Error rotating API key for {platform}: {e}")
            return False
    
    def get_health_report(self) -> Dict:
        """Get health report for all API keys."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "platforms": {},
            "summary": {
                "total_platforms": len(Platform),
                "configured": 0,
                "validated": 0,
                "errors": 0
            }
        }
        
        for platform in Platform:
            metadata = self._key_metadata.get(platform, {})
            
            status = metadata.get("validation_status", "not_configured")
            has_key = platform in self._platform_keys
            
            platform_info = {
                "configured": has_key,
                "status": status,
                "last_validated": metadata.get("last_validated"),
                "loaded_from": metadata.get("loaded_from")
            }
            
            report["platforms"][platform.value] = platform_info
            
            # Update summary
            if has_key:
                report["summary"]["configured"] += 1
            
            if status == "valid":
                report["summary"]["validated"] += 1
            elif status in ["invalid", "error"]:
                report["summary"]["errors"] += 1
        
        return report


# Global API key manager instance
api_key_manager = APIKeyManager()


async def require_api_key(platform: Platform) -> str:
    """
    Decorator-like function to require valid API key.
    
    Args:
        platform: Required platform
        
    Returns:
        API key for the platform
        
    Raises:
        ValueError: If no valid API key is available
    """
    key = api_key_manager.get_api_key(platform)
    if not key:
        raise ValueError(f"No API key configured for {platform}")
    
    if not api_key_manager.has_valid_key(platform):
        raise ValueError(f"Invalid API key for {platform}")
    
    return key