#!/usr/bin/env python3
"""
JSON Storage Module
- Fast document storage and retrieval
- Persistent caching of processed documents
- Reduces processing time significantly
"""

import os
import json
import hashlib
import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class JSONStorage:
    """Fast JSON-based document storage."""
    
    def __init__(self, storage_dir: str = "storage"):
        """Initialize JSON storage."""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.documents_file = self.storage_dir / "documents.json"
        self.embeddings_file = self.storage_dir / "embeddings.json"
        
        # Load existing data
        self.documents = self._load_json(self.documents_file, {})
        self.embeddings = self._load_json(self.embeddings_file, {})
        
        logger.info(f"✅ JSON Storage initialized: {len(self.documents)} documents cached")
    
    def _load_json(self, file_path: Path, default: Any) -> Any:
        """Load JSON file safely."""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ Failed to load {file_path}: {e}")
        return default
    
    def _save_json(self, file_path: Path, data: Any):
        """Save JSON file safely."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Failed to save {file_path}: {e}")
    
    def get_document_hash(self, document_url: str) -> str:
        """Generate hash for document URL."""
        return hashlib.md5(document_url.encode()).hexdigest()
    
    def has_document(self, document_url: str) -> bool:
        """Check if document is cached."""
        doc_hash = self.get_document_hash(document_url)
        return doc_hash in self.documents
    
    def get_document(self, document_url: str) -> Optional[Dict[str, Any]]:
        """Get cached document data."""
        doc_hash = self.get_document_hash(document_url)
        
        if doc_hash in self.documents:
            doc_data = self.documents[doc_hash]
            
            # Check if cache is not too old (24 hours)
            if time.time() - doc_data.get('timestamp', 0) < 86400:
                logger.info(f"✅ Retrieved cached document: {doc_hash[:8]}...")
                return doc_data
            else:
                logger.info(f"🗑️ Removing expired cache: {doc_hash[:8]}...")
                self.remove_document(document_url)
        
        return None
    
    def store_document(self, document_url: str, chunks: List[Dict], 
                      entities: List[Dict], metadata: Dict[str, Any] = None):
        """Store document data in JSON."""
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
        
        self.documents[doc_hash] = doc_data
        self._save_json(self.documents_file, self.documents)
        
        logger.info(f"💾 Stored document in JSON: {doc_hash[:8]}... ({len(chunks)} chunks)")
    
    def store_embeddings(self, document_url: str, embeddings: List[List[float]]):
        """Store document embeddings separately."""
        doc_hash = self.get_document_hash(document_url)
        
        self.embeddings[doc_hash] = {
            'embeddings': embeddings,
            'timestamp': time.time()
        }
        self._save_json(self.embeddings_file, self.embeddings)
        
        logger.info(f"💾 Stored embeddings: {doc_hash[:8]}... ({len(embeddings)} vectors)")
    
    def get_embeddings(self, document_url: str) -> Optional[List[List[float]]]:
        """Get cached embeddings."""
        doc_hash = self.get_document_hash(document_url)
        
        if doc_hash in self.embeddings:
            emb_data = self.embeddings[doc_hash]
            
            # Check if cache is not too old (24 hours)
            if time.time() - emb_data.get('timestamp', 0) < 86400:
                logger.info(f"✅ Retrieved cached embeddings: {doc_hash[:8]}...")
                return emb_data['embeddings']
            else:
                logger.info(f"🗑️ Removing expired embeddings: {doc_hash[:8]}...")
                self.remove_embeddings(document_url)
        
        return None
    
    def remove_document(self, document_url: str):
        """Remove document from cache."""
        doc_hash = self.get_document_hash(document_url)
        
        if doc_hash in self.documents:
            del self.documents[doc_hash]
            self._save_json(self.documents_file, self.documents)
            logger.info(f"🗑️ Removed document: {doc_hash[:8]}...")
    
    def remove_embeddings(self, document_url: str):
        """Remove embeddings from cache."""
        doc_hash = self.get_document_hash(document_url)
        
        if doc_hash in self.embeddings:
            del self.embeddings[doc_hash]
            self._save_json(self.embeddings_file, self.embeddings)
            logger.info(f"🗑️ Removed embeddings: {doc_hash[:8]}...")
    
    def clear_all(self):
        """Clear all cached data."""
        self.documents.clear()
        self.embeddings.clear()
        self._save_json(self.documents_file, self.documents)
        self._save_json(self.embeddings_file, self.embeddings)
        logger.info("🗑️ Cleared all cached data")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            'documents_cached': len(self.documents),
            'embeddings_cached': len(self.embeddings),
            'storage_size_mb': self._get_storage_size(),
            'oldest_cache': self._get_oldest_timestamp(),
            'newest_cache': self._get_newest_timestamp()
        }
    
    def _get_storage_size(self) -> float:
        """Calculate storage size in MB."""
        total_size = 0
        for file_path in [self.documents_file, self.embeddings_file]:
            if file_path.exists():
                total_size += file_path.stat().st_size
        return total_size / 1024 / 1024
    
    def _get_oldest_timestamp(self) -> Optional[float]:
        """Get oldest cache timestamp."""
        timestamps = []
        for data in self.documents.values():
            timestamps.append(data.get('timestamp', 0))
        return min(timestamps) if timestamps else None
    
    def _get_newest_timestamp(self) -> Optional[float]:
        """Get newest cache timestamp."""
        timestamps = []
        for data in self.documents.values():
            timestamps.append(data.get('timestamp', 0))
        return max(timestamps) if timestamps else None 