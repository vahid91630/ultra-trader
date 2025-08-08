"""
GPT Response Caching Layer
Provides MongoDB-backed caching with in-memory fallback for OpenAI responses.
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import lru_cache

try:
    from pymongo import MongoClient
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    MongoClient = None

logger = logging.getLogger(__name__)


class GPTCache:
    """Cache for GPT responses with MongoDB and in-memory fallback."""
    
    def __init__(self):
        """Initialize cache with MongoDB connection if available."""
        self.mongo_client = None
        self.mongo_db = None
        self.cache_collection = None
        self.use_mongo = False
        
        # In-memory cache as fallback
        self._memory_cache = {}
        self._cache_timestamps = {}
        self._max_memory_cache = 100  # Maximum items in memory cache
        
        # Try to connect to MongoDB
        mongodb_uri = os.getenv("MONGODB_URI")
        if PYMONGO_AVAILABLE and mongodb_uri:
            try:
                self.mongo_client = MongoClient(mongodb_uri)
                # Extract database name from URI
                db_name = mongodb_uri.split("/")[-1].split("?")[0]
                if not db_name or db_name == mongodb_uri:
                    db_name = "ultra_trader"  # Default database name
                
                self.mongo_db = self.mongo_client[db_name]
                self.cache_collection = self.mongo_db["gpt_cache"]
                
                # Test connection
                self.mongo_client.admin.command('ping')
                self.use_mongo = True
                logger.info("GPT cache initialized with MongoDB backend")
                
                # Create TTL index for automatic cleanup (30 days)
                try:
                    self.cache_collection.create_index(
                        "timestamp", 
                        expireAfterSeconds=30*24*60*60  # 30 days
                    )
                except Exception as e:
                    logger.warning(f"Could not create TTL index: {e}")
                    
            except Exception as e:
                logger.warning(f"Failed to connect to MongoDB for caching: {e}")
                self.use_mongo = False
        else:
            logger.info("MongoDB not available, using in-memory cache only")
    
    def _generate_cache_key(self, prompt: str, template: str = "", params: Dict = None) -> str:
        """Generate a cache key from prompt, template, and parameters."""
        if params is None:
            params = {}
        
        # Create a consistent string representation
        cache_input = {
            "prompt": prompt.strip(),
            "template": template.strip(),
            "params": params
        }
        
        # Generate MD5 hash as cache key
        cache_str = json.dumps(cache_input, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def get(self, prompt: str, template: str = "", params: Dict = None) -> Optional[str]:
        """
        Retrieve cached response.
        
        Args:
            prompt: The original prompt
            template: Template used (if any)
            params: Additional parameters used
            
        Returns:
            Cached response if found, None otherwise
        """
        cache_key = self._generate_cache_key(prompt, template, params)
        
        # Try MongoDB first
        if self.use_mongo:
            try:
                result = self.cache_collection.find_one({"_id": cache_key})
                if result:
                    # Check if not expired (additional check beyond TTL)
                    created = result.get("timestamp", datetime.utcnow())
                    if isinstance(created, str):
                        created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    
                    # Consider cache valid for 24 hours
                    if datetime.utcnow() - created < timedelta(hours=24):
                        logger.debug(f"Cache hit (MongoDB): {cache_key[:8]}...")
                        return result.get("response")
                    else:
                        # Remove expired entry
                        self.cache_collection.delete_one({"_id": cache_key})
            except Exception as e:
                logger.warning(f"MongoDB cache read error: {e}")
        
        # Fallback to memory cache
        if cache_key in self._memory_cache:
            # Check timestamp
            timestamp = self._cache_timestamps.get(cache_key, datetime.utcnow())
            if datetime.utcnow() - timestamp < timedelta(hours=1):  # Shorter TTL for memory
                logger.debug(f"Cache hit (memory): {cache_key[:8]}...")
                return self._memory_cache[cache_key]
            else:
                # Remove expired entry
                del self._memory_cache[cache_key]
                del self._cache_timestamps[cache_key]
        
        logger.debug(f"Cache miss: {cache_key[:8]}...")
        return None
    
    def set(self, prompt: str, response: str, template: str = "", params: Dict = None) -> None:
        """
        Store response in cache.
        
        Args:
            prompt: The original prompt
            response: The GPT response to cache
            template: Template used (if any)
            params: Additional parameters used
        """
        if not response or len(response.strip()) == 0:
            return  # Don't cache empty responses
        
        cache_key = self._generate_cache_key(prompt, template, params)
        timestamp = datetime.utcnow()
        
        # Store in MongoDB if available
        if self.use_mongo:
            try:
                doc = {
                    "_id": cache_key,
                    "prompt": prompt[:500],  # Store truncated prompt for debugging
                    "response": response,
                    "template": template,
                    "params": params or {},
                    "timestamp": timestamp
                }
                self.cache_collection.replace_one(
                    {"_id": cache_key}, 
                    doc, 
                    upsert=True
                )
                logger.debug(f"Cached to MongoDB: {cache_key[:8]}...")
            except Exception as e:
                logger.warning(f"MongoDB cache write error: {e}")
        
        # Always store in memory cache as backup
        self._cleanup_memory_cache()
        self._memory_cache[cache_key] = response
        self._cache_timestamps[cache_key] = timestamp
        logger.debug(f"Cached to memory: {cache_key[:8]}...")
    
    def _cleanup_memory_cache(self) -> None:
        """Clean up memory cache when it gets too large."""
        if len(self._memory_cache) >= self._max_memory_cache:
            # Remove oldest entries
            sorted_items = sorted(
                self._cache_timestamps.items(), 
                key=lambda x: x[1]
            )
            
            # Remove oldest 20% of entries
            remove_count = len(sorted_items) // 5
            for cache_key, _ in sorted_items[:remove_count]:
                if cache_key in self._memory_cache:
                    del self._memory_cache[cache_key]
                if cache_key in self._cache_timestamps:
                    del self._cache_timestamps[cache_key]
    
    def clear(self) -> None:
        """Clear all cached entries."""
        # Clear MongoDB cache
        if self.use_mongo:
            try:
                self.cache_collection.delete_many({})
                logger.info("Cleared MongoDB cache")
            except Exception as e:
                logger.warning(f"Error clearing MongoDB cache: {e}")
        
        # Clear memory cache
        self._memory_cache.clear()
        self._cache_timestamps.clear()
        logger.info("Cleared memory cache")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "use_mongo": self.use_mongo,
            "memory_cache_size": len(self._memory_cache),
            "max_memory_cache": self._max_memory_cache
        }
        
        if self.use_mongo:
            try:
                mongo_count = self.cache_collection.count_documents({})
                stats["mongo_cache_size"] = mongo_count
            except Exception as e:
                stats["mongo_cache_size"] = f"Error: {e}"
        
        return stats


# Global cache instance
gpt_cache = GPTCache()


def get_gpt_cache() -> GPTCache:
    """Get the global GPT cache instance."""
    return gpt_cache