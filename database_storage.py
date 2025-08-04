#!/usr/bin/env python3
"""
Database Storage Solution
- Uses external database for persistent caching
- Works across server restarts
- Scalable for production use
"""

import os
import json
import hashlib
import time
import logging
from typing import Dict, Any, List, Optional
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseStorage:
    """Database-based document storage."""
    
    def __init__(self, db_path: str = "storage/documents.db"):
        """Initialize database storage."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"✅ Database Storage initialized: {db_path}")
    
    def _init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_hash TEXT UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    chunks TEXT NOT NULL,
                    entities TEXT NOT NULL,
                    metadata TEXT,
                    timestamp REAL NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    entity_count INTEGER NOT NULL
                )
            """)
            
            # Create embeddings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_hash TEXT UNIQUE NOT NULL,
                    embeddings TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)
            
            conn.commit()
    
    def get_document_hash(self, document_url: str) -> str:
        """Generate hash for document URL."""
        return hashlib.md5(document_url.encode()).hexdigest()
    
    def has_document(self, document_url: str) -> bool:
        """Check if document is cached."""
        doc_hash = self.get_document_hash(document_url)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents WHERE doc_hash = ?", (doc_hash,))
            return cursor.fetchone()[0] > 0
    
    def get_document(self, document_url: str) -> Optional[Dict[str, Any]]:
        """Get cached document data."""
        doc_hash = self.get_document_hash(document_url)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT url, chunks, entities, metadata, timestamp, chunk_count, entity_count 
                FROM documents 
                WHERE doc_hash = ? AND timestamp > ?
            """, (doc_hash, time.time() - 86400))  # 24 hours
            
            row = cursor.fetchone()
            
            if row:
                url, chunks_json, entities_json, metadata_json, timestamp, chunk_count, entity_count = row
                
                doc_data = {
                    'url': url,
                    'chunks': json.loads(chunks_json),
                    'entities': json.loads(entities_json),
                    'metadata': json.loads(metadata_json) if metadata_json else {},
                    'timestamp': timestamp,
                    'chunk_count': chunk_count,
                    'entity_count': entity_count
                }
                
                logger.info(f"✅ Retrieved from database: {doc_hash[:8]}...")
                return doc_data
            else:
                # Remove expired entry if exists
                cursor.execute("DELETE FROM documents WHERE doc_hash = ?", (doc_hash,))
                conn.commit()
        
        return None
    
    def store_document(self, document_url: str, chunks: List[Dict], 
                      entities: List[Dict], metadata: Dict[str, Any] = None):
        """Store document data in database."""
        doc_hash = self.get_document_hash(document_url)
        timestamp = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert or replace document
            cursor.execute("""
                INSERT OR REPLACE INTO documents 
                (doc_hash, url, chunks, entities, metadata, timestamp, chunk_count, entity_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_hash,
                document_url,
                json.dumps(chunks),
                json.dumps(entities),
                json.dumps(metadata or {}),
                timestamp,
                len(chunks),
                len(entities)
            ))
            
            conn.commit()
        
        logger.info(f"💾 Stored in database: {doc_hash[:8]}... ({len(chunks)} chunks)")
    
    def store_embeddings(self, document_url: str, embeddings: List[List[float]]):
        """Store document embeddings in database."""
        doc_hash = self.get_document_hash(document_url)
        timestamp = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO embeddings (doc_hash, embeddings, timestamp)
                VALUES (?, ?, ?)
            """, (doc_hash, json.dumps(embeddings), timestamp))
            
            conn.commit()
        
        logger.info(f"💾 Stored embeddings in database: {doc_hash[:8]}...")
    
    def get_embeddings(self, document_url: str) -> Optional[List[List[float]]]:
        """Get cached embeddings from database."""
        doc_hash = self.get_document_hash(document_url)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT embeddings FROM embeddings 
                WHERE doc_hash = ? AND timestamp > ?
            """, (doc_hash, time.time() - 86400))
            
            row = cursor.fetchone()
            
            if row:
                embeddings = json.loads(row[0])
                logger.info(f"✅ Retrieved embeddings from database: {doc_hash[:8]}...")
                return embeddings
            else:
                # Remove expired entry if exists
                cursor.execute("DELETE FROM embeddings WHERE doc_hash = ?", (doc_hash,))
                conn.commit()
        
        return None
    
    def remove_document(self, document_url: str):
        """Remove document from database."""
        doc_hash = self.get_document_hash(document_url)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE doc_hash = ?", (doc_hash,))
            cursor.execute("DELETE FROM embeddings WHERE doc_hash = ?", (doc_hash,))
            conn.commit()
        
        logger.info(f"🗑️ Removed from database: {doc_hash[:8]}...")
    
    def clear_all(self):
        """Clear all cached data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents")
            cursor.execute("DELETE FROM embeddings")
            conn.commit()
        
        logger.info("🗑️ Cleared all database data")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Document stats
            cursor.execute("SELECT COUNT(*) FROM documents")
            doc_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM embeddings")
            emb_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM documents")
            time_range = cursor.fetchone()
            
            return {
                'documents_cached': doc_count,
                'embeddings_cached': emb_count,
                'database_path': str(self.db_path),
                'oldest_cache': time_range[0] if time_range[0] else None,
                'newest_cache': time_range[1] if time_range[1] else None
            } 