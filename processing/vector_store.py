#!/usr/bin/env python3
"""
Vector Store Module
- In-memory storage for documents, chunks, embeddings, entities, and relationships
- Efficient similarity search using cosine similarity
- Clean data management and retrieval
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorStore:
    """In-memory vector storage for hybrid RAG system."""
    
    def __init__(self):
        """Initialize empty storage."""
        # Document storage
        self.documents = {}  # doc_id -> {title, text, metadata, timestamp}
        
        # Chunk storage with embeddings
        self.chunks = []  # List of chunk objects with embeddings
        self.chunk_index = {}  # chunk_id -> chunk object
        
        # Entity storage
        self.entities = {}  # entity_name -> entity object
        self.entities_by_type = {}  # entity_type -> [entity_objects]
        
        # Relationship storage
        self.relationships = []  # List of relationship objects
        self.relationship_index = {}  # source -> [relationships]
        
        logger.info("✅ VectorStore initialized (in-memory)")
    
    def add_document(self, doc_id: str, title: str, chunks: List[Dict[str, Any]], 
                    entities_data: Dict[str, Any]) -> bool:
        """Add document with chunks, embeddings, and entities."""
        try:
            # Store document metadata
            self.documents[doc_id] = {
                "id": doc_id,
                "title": title,
                "chunk_count": len(chunks),
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "total_chunks": len(chunks),
                    "entity_count": sum(len(v) for v in entities_data.get("entities", {}).values()),
                    "relationship_count": len(entities_data.get("relationships", []))
                }
            }
            
            # Store chunks with document reference
            for chunk in chunks:
                chunk_with_doc = chunk.copy()
                chunk_with_doc["document_id"] = doc_id
                chunk_with_doc["document_title"] = title
                
                # Add to main chunks list
                self.chunks.append(chunk_with_doc)
                
                # Add to chunk index
                self.chunk_index[chunk["id"]] = chunk_with_doc
            
            # Store entities
            self._add_entities(entities_data.get("entities", {}), doc_id)
            
            # Store relationships
            self._add_relationships(entities_data.get("relationships", []), doc_id)
            
            logger.info(f"✅ Added document {doc_id}: {len(chunks)} chunks, "
                       f"{sum(len(v) for v in entities_data.get('entities', {}).values())} entities")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to add document {doc_id}: {e}")
            return False
    
    def _add_entities(self, entities_by_type: Dict[str, List[Dict]], doc_id: str):
        """Add entities to storage."""
        for entity_type, entity_list in entities_by_type.items():
            if entity_type not in self.entities_by_type:
                self.entities_by_type[entity_type] = []
            
            for entity in entity_list:
                entity_name = entity["name"].lower()
                
                # Add document reference
                entity_with_doc = entity.copy()
                entity_with_doc["document_id"] = doc_id
                entity_with_doc["entity_id"] = f"{entity_name}_{uuid.uuid4().hex[:8]}"
                
                # Store in main entities dict
                if entity_name not in self.entities:
                    self.entities[entity_name] = []
                self.entities[entity_name].append(entity_with_doc)
                
                # Store by type
                self.entities_by_type[entity_type].append(entity_with_doc)
    
    def _add_relationships(self, relationships: List[Dict], doc_id: str):
        """Add relationships to storage."""
        for rel in relationships:
            rel_with_doc = rel.copy()
            rel_with_doc["document_id"] = doc_id
            rel_with_doc["relationship_id"] = f"rel_{uuid.uuid4().hex[:8]}"
            
            # Add to main relationships list
            self.relationships.append(rel_with_doc)
            
            # Index by source for quick lookup
            source = rel["source"].lower()
            if source not in self.relationship_index:
                self.relationship_index[source] = []
            self.relationship_index[source].append(rel_with_doc)
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            # Convert to numpy arrays
            a = np.array(vec1, dtype=np.float32)
            b = np.array(vec2, dtype=np.float32)
            
            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            return float(dot_product / (norm_a * norm_b))
        
        except Exception as e:
            logger.error(f"❌ Cosine similarity calculation failed: {e}")
            return 0.0
    
    def search_similar_chunks(self, query_embedding: List[float], 
                             top_k: int = 5, min_similarity: float = 0.1) -> List[Dict[str, Any]]:
        """Search for similar chunks using cosine similarity."""
        try:
            if not self.chunks:
                logger.warning("⚠️ No chunks in storage")
                return []
            
            chunk_similarities = []
            
            for chunk in self.chunks:
                if "embedding" not in chunk:
                    continue
                
                similarity = self.cosine_similarity(query_embedding, chunk["embedding"])
                
                if similarity >= min_similarity:
                    chunk_result = {
                        "chunk_id": chunk["id"],
                        "text": chunk["text"],
                        "similarity": similarity,
                        "document_id": chunk.get("document_id"),
                        "document_title": chunk.get("document_title"),
                        "metadata": chunk.get("metadata", {})
                    }
                    chunk_similarities.append(chunk_result)
            
            # Sort by similarity (descending)
            chunk_similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Return top K results
            results = chunk_similarities[:top_k]
            logger.info(f"🔍 Vector search: {len(results)} chunks found (top-{top_k})")
            return results
        
        except Exception as e:
            logger.error(f"❌ Vector search failed: {e}")
            return []
    
    def search_entities(self, query_terms: List[str], entity_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search entities by name and type."""
        results = []
        query_terms_lower = [term.lower() for term in query_terms]
        
        try:
            # Search in specific entity types or all types
            search_types = entity_types if entity_types else self.entities_by_type.keys()
            
            for entity_type in search_types:
                if entity_type in self.entities_by_type:
                    for entity in self.entities_by_type[entity_type]:
                        entity_name_lower = entity["name"].lower()
                        
                        # Check if any query term matches entity name
                        for query_term in query_terms_lower:
                            if query_term in entity_name_lower or entity_name_lower in query_term:
                                results.append({
                                    "entity_id": entity["entity_id"],
                                    "name": entity["name"],
                                    "type": entity["type"],
                                    "confidence": entity.get("confidence", 0.0),
                                    "document_id": entity.get("document_id"),
                                    "match_type": "name_match"
                                })
                                break
            
            logger.info(f"🏷️ Entity search: {len(results)} entities found")
            return results
        
        except Exception as e:
            logger.error(f"❌ Entity search failed: {e}")
            return []
    
    def get_entity_relationships(self, entity_name: str) -> List[Dict[str, Any]]:
        """Get all relationships involving an entity."""
        entity_name_lower = entity_name.lower()
        results = []
        
        try:
            # Search relationships where entity is source or target
            for rel in self.relationships:
                if (entity_name_lower in rel["source"].lower() or 
                    entity_name_lower in rel["target"].lower()):
                    results.append(rel)
            
            logger.info(f"🔗 Found {len(results)} relationships for entity: {entity_name}")
            return results
        
        except Exception as e:
            logger.error(f"❌ Relationship search failed: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        entity_count = sum(len(entities) for entities in self.entities_by_type.values())
        
        return {
            "documents": len(self.documents),
            "chunks": len(self.chunks),
            "entities": entity_count,
            "relationships": len(self.relationships),
            "entity_types": len(self.entities_by_type),
            "storage_type": "in_memory"
        }
    
    def get_all_entities_by_type(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all entities organized by type."""
        return self.entities_by_type.copy()
    
    def get_all_relationships(self) -> List[Dict[str, Any]]:
        """Get all relationships."""
        return self.relationships.copy()
    
    def clear_storage(self):
        """Clear all stored data."""
        self.documents.clear()
        self.chunks.clear()
        self.chunk_index.clear()
        self.entities.clear()
        self.entities_by_type.clear()
        self.relationships.clear()
        self.relationship_index.clear()
        
        logger.info("🗑️ Storage cleared")
    
    def get_document_info(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document information by ID."""
        return self.documents.get(doc_id)