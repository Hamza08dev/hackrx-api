#!/usr/bin/env python3
"""
Render Persistent Storage Solution
- Uses Render's persistent disk for caching
- Survives server restarts
- Optimized for Render's environment
"""

import os
import json
import hashlib
import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class RenderPersistentStorage:
    """Persistent storage optimized for Render."""
    
    def __init__(self):
        """Initialize with Render's persistent disk."""
        # Use Render's persistent disk path
        self.storage_dir = Path("/opt/render/project/src/storage")
        
        # Fallback to local storage for development
        if not self.storage_dir.exists():
            self.storage_dir = Path("storage")
        
        self.storage_dir.mkdir(exist_ok=True)
        self.cache_file = self.storage_dir / "document_cache.json"
        
        # Load existing cache
        self.cache = self._load_cache()
        
        logger.info(f"✅ Render Persistent Storage: {len(self.cache)} documents cached")
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from persistent storage."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    
                # Clean expired entries
                current_time = time.time()
                expired_keys = []
                for key, data in cache.items():
                    if current_time - data.get('timestamp', 0) > 86400:  # 24 hours
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del cache[key]
                
                if expired_keys:
                    self._save_cache(cache)
                    logger.info(f"🗑️ Cleaned {len(expired_keys)} expired cache entries")
                
                return cache
        except Exception as e:
            logger.warning(f"⚠️ Failed to load cache: {e}")
        
        return {}
    
    def _save_cache(self, cache: Dict[str, Any]):
        """Save cache to persistent storage."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Failed to save cache: {e}")
    
    def get_document_hash(self, document_url: str) -> str:
        """Generate hash for document URL."""
        return hashlib.md5(document_url.encode()).hexdigest()
    
    def has_document(self, document_url: str) -> bool:
        """Check if document is cached."""
        doc_hash = self.get_document_hash(document_url)
        return doc_hash in self.cache
    
    def get_document(self, document_url: str) -> Optional[Dict[str, Any]]:
        """Get cached document data."""
        doc_hash = self.get_document_hash(document_url)
        
        if doc_hash in self.cache:
            doc_data = self.cache[doc_hash]
            
            # Check if cache is not too old (24 hours)
            if time.time() - doc_data.get('timestamp', 0) < 86400:
                logger.info(f"✅ Retrieved from persistent cache: {doc_hash[:8]}...")
                return doc_data
            else:
                logger.info(f"🗑️ Removing expired cache: {doc_hash[:8]}...")
                self.remove_document(document_url)
        
        return None
    
    def store_document(self, document_url: str, chunks: List[Dict], 
                      entities: List[Dict], metadata: Dict[str, Any] = None):
        """Store document data in persistent cache."""
        doc_hash = self.get_document_hash(document_url)
        
        doc_data = {
            'url': document_url,
            'chunks': chunks,
            'entities': entities,
            'metadata': metadata or {},
            'timestamp': time.time(),
            'chunk_count': len(chunks),
            'entity_count': len(entities)
        }
        
        self.cache[doc_hash] = doc_data
        self._save_cache(self.cache)
        
        logger.info(f"💾 Stored in persistent cache: {doc_hash[:8]}... ({len(chunks)} chunks)")
    
    def remove_document(self, document_url: str):
        """Remove document from cache."""
        doc_hash = self.get_document_hash(document_url)
        
        if doc_hash in self.cache:
            del self.cache[doc_hash]
            self._save_cache(self.cache)
            logger.info(f"🗑️ Removed from cache: {doc_hash[:8]}...")
    
    def clear_all(self):
        """Clear all cached data."""
        self.cache.clear()
        self._save_cache(self.cache)
        logger.info("🗑️ Cleared all cached data")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            'documents_cached': len(self.cache),
            'storage_path': str(self.storage_dir),
            'cache_file_size_mb': self.cache_file.stat().st_size / 1024 / 1024 if self.cache_file.exists() else 0,
            'oldest_cache': min([data.get('timestamp', 0) for data in self.cache.values()]) if self.cache else None,
            'newest_cache': max([data.get('timestamp', 0) for data in self.cache.values()]) if self.cache else None
        } 