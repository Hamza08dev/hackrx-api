#!/usr/bin/env python3
"""
Configuration Module
- Centralized settings for performance optimization
- Easy to adjust for different use cases
- Environment-specific configurations
"""

import os
from typing import Dict, Any

class Config:
    """Centralized configuration for the application."""
    
    # EMBEDDING OPTIMIZATION SETTINGS
    EMBEDDING = {
        # Chunking settings
        "chunk_size": int(os.getenv("CHUNK_SIZE", "1500")),  # Increased from 800
        "chunk_overlap": int(os.getenv("CHUNK_OVERLAP", "100")),  # Reduced from 150
        "min_chunk_size": int(os.getenv("MIN_CHUNK_SIZE", "100")),  # Increased from 50
        
        # Batch processing
        "batch_size": int(os.getenv("BATCH_SIZE", "5")),  # Process chunks in batches
        "max_workers": int(os.getenv("MAX_WORKERS", "3")),  # Parallel processing threads
        
        # Rate limiting
        "max_retries": int(os.getenv("MAX_RETRIES", "2")),  # Reduced from 3
        "retry_delay": float(os.getenv("RETRY_DELAY", "0.5")),  # Reduced from 1.0
        "batch_delay": float(os.getenv("BATCH_DELAY", "0.1")),  # Reduced delay between batches
        
        # Model settings
        "model_name": os.getenv("EMBEDDING_MODEL", "models/embedding-001"),
    }
    
    # ENTITY EXTRACTION OPTIMIZATION SETTINGS
    ENTITY_EXTRACTION = {
        # Rate limiting
        "max_retries": int(os.getenv("ENTITY_MAX_RETRIES", "1")),
        "retry_delay": float(os.getenv("ENTITY_RETRY_DELAY", "0.5")),
        "batch_delay": float(os.getenv("ENTITY_BATCH_DELAY", "0.5")),
        
        # Processing limits
        "max_chars_per_call": int(os.getenv("ENTITY_MAX_CHARS", "3000")),
        "max_chunks_per_call": int(os.getenv("ENTITY_MAX_CHUNKS", "5")),
        
        # Model settings
        "model_name": os.getenv("ENTITY_MODEL", "gemini-1.5-flash"),
    }
    
    # PERFORMANCE PROFILES
    PERFORMANCE_PROFILES = {
        "fast": {
            "chunk_size": 2000,
            "chunk_overlap": 50,
            "batch_size": 8,
            "max_workers": 5,
            "batch_delay": 0.05,
        },
        "balanced": {
            "chunk_size": 1500,
            "chunk_overlap": 100,
            "batch_size": 5,
            "max_workers": 3,
            "batch_delay": 0.1,
        },
        "quality": {
            "chunk_size": 1000,
            "chunk_overlap": 150,
            "batch_size": 3,
            "max_workers": 2,
            "batch_delay": 0.2,
        }
    }
    
    @classmethod
    def get_embedding_config(cls, profile: str = "balanced") -> Dict[str, Any]:
        """Get embedding configuration with optional performance profile."""
        config = cls.EMBEDDING.copy()
        
        if profile in cls.PERFORMANCE_PROFILES:
            profile_config = cls.PERFORMANCE_PROFILES[profile]
            config.update(profile_config)
        
        return config
    
    @classmethod
    def get_entity_config(cls) -> Dict[str, Any]:
        """Get entity extraction configuration."""
        return cls.ENTITY_EXTRACTION.copy()
    
    @classmethod
    def print_current_config(cls):
        """Print current configuration for debugging."""
        print("🔧 CURRENT CONFIGURATION")
        print("="*50)
        
        print("\n📝 EMBEDDING SETTINGS:")
        for key, value in cls.EMBEDDING.items():
            print(f"   {key}: {value}")
        
        print("\n🏷️ ENTITY EXTRACTION SETTINGS:")
        for key, value in cls.ENTITY_EXTRACTION.items():
            print(f"   {key}: {value}")
        
        print("\n⚡ PERFORMANCE PROFILES:")
        for profile, settings in cls.PERFORMANCE_PROFILES.items():
            print(f"   {profile}: {settings}")
        
        print("="*50)

# Environment-specific configurations
def get_config_for_environment(env: str = "production") -> Dict[str, Any]:
    """Get configuration optimized for specific environment."""
    
    if env == "development":
        return {
            "embedding": Config.get_embedding_config("quality"),
            "entity": Config.get_entity_config(),
            "debug": True,
            "timeout": 60
        }
    elif env == "testing":
        return {
            "embedding": Config.get_embedding_config("fast"),
            "entity": Config.get_entity_config(),
            "debug": True,
            "timeout": 30
        }
    else:  # production
        return {
            "embedding": Config.get_embedding_config("balanced"),
            "entity": Config.get_entity_config(),
            "debug": False,
            "timeout": 120
        }

if __name__ == "__main__":
    Config.print_current_config() 