#!/usr/bin/env python3
"""
Retriever Module
- Hybrid search combining vector similarity and graph traversal
- Intelligent query analysis and entity extraction
- Result ranking and deduplication
"""

import logging
import re
from typing import List, Dict, Any, Set
from processing.vector_store import VectorStore

logger = logging.getLogger(__name__)

class Retriever:
    """Hybrid retrieval system combining vector and graph search."""
    
    def __init__(self):
        """Initialize retriever."""
        self.semantic_weight = 0.7  # Weight for semantic search
        self.graph_weight = 0.3     # Weight for graph search
        self.max_semantic_results = 5
        self.max_graph_results = 3
        self.min_similarity_threshold = 0.1
        
        logger.info("✅ Retriever initialized (hybrid mode)")
    
    def extract_query_entities(self, query: str) -> List[str]:
        """Extract potential entity names from query using simple NLP."""
        try:
            # Remove common question words and prepositions
            stop_words = {
                'what', 'who', 'where', 'when', 'why', 'how', 'is', 'are', 'was', 'were',
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'from', 'about', 'into', 'through', 'during',
                'before', 'after', 'above', 'below', 'up', 'down', 'out', 'off',
                'over', 'under', 'again', 'further', 'then', 'once', 'can', 'could',
                'should', 'would', 'may', 'might', 'must', 'shall', 'will', 'do',
                'does', 'did', 'has', 'have', 'had', 'been', 'being', 'get', 'got'
            }
            
            # Split into words and clean
            words = re.findall(r'\b\w+\b', query.lower())
            
            # Filter out stop words and short words
            entities = []
            for word in words:
                if (len(word) > 2 and 
                    word not in stop_words and 
                    not word.isdigit()):
                    entities.append(word)
            
            # Also look for multi-word entities (capitalized words in original query)
            capitalized_words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
            entities.extend([word.lower() for word in capitalized_words])
            
            # Remove duplicates while preserving order
            unique_entities = []
            seen = set()
            for entity in entities:
                if entity not in seen:
                    seen.add(entity)
                    unique_entities.append(entity)
            
            logger.info(f"🔍 Extracted entities from query: {unique_entities}")
            return unique_entities
        
        except Exception as e:
            logger.error(f"❌ Query entity extraction failed: {e}")
            return []
    
    def semantic_search(self, query_embedding: List[float], vector_store: VectorStore) -> List[Dict[str, Any]]:
        """Perform semantic vector search."""
        try:
            results = vector_store.search_similar_chunks(
                query_embedding=query_embedding,
                top_k=self.max_semantic_results,
                min_similarity=self.min_similarity_threshold
            )
            
            # Add search type metadata
            for result in results:
                result["search_type"] = "semantic"
                result["search_score"] = result["similarity"]
            
            logger.info(f"🔍 Semantic search: {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"❌ Semantic search failed: {e}")
            return []
    
    def graph_search(self, query_entities: List[str], vector_store: VectorStore) -> List[Dict[str, Any]]:
        """Perform graph-based entity and relationship search."""
        try:
            graph_results = []
            seen_chunks = set()
            
            # Search for entities mentioned in query
            entity_results = vector_store.search_entities(query_entities)
            
            for entity in entity_results:
                # Get relationships for this entity
                relationships = vector_store.get_entity_relationships(entity["name"])
                
                # For each relationship, find related chunks
                for rel in relationships:
                    # Look for chunks containing the relationship entities
                    source = rel["source"]
                    target = rel["target"]
                    
                    # Search chunks for entities involved in relationships
                    for chunk in vector_store.chunks:
                        chunk_text_lower = chunk["text"].lower()
                        chunk_id = chunk["id"]
                        
                        # Skip if we've already included this chunk
                        if chunk_id in seen_chunks:
                            continue
                        
                        # Check if chunk contains relationship entities
                        contains_source = source.lower() in chunk_text_lower
                        contains_target = target.lower() in chunk_text_lower
                        
                        if contains_source or contains_target:
                            # Calculate graph relevance score
                            relevance_score = 0.0
                            if contains_source and contains_target:
                                relevance_score = 0.9  # Both entities
                            elif contains_source or contains_target:
                                relevance_score = 0.6  # One entity
                            
                            # Add relationship context bonus
                            relevance_score += rel.get("confidence", 0.0) * 0.1
                            
                            graph_result = {
                                "chunk_id": chunk["id"],
                                "text": chunk["text"],
                                "similarity": relevance_score,
                                "search_score": relevance_score,
                                "document_id": chunk.get("document_id"),
                                "document_title": chunk.get("document_title"),
                                "metadata": chunk.get("metadata", {}),
                                "search_type": "graph",
                                "related_entity": entity["name"],
                                "relationship": {
                                    "type": rel["type"],
                                    "source": rel["source"],
                                    "target": rel["target"]
                                }
                            }
                            
                            graph_results.append(graph_result)
                            seen_chunks.add(chunk_id)
            
            # Sort by relevance score and limit results
            graph_results.sort(key=lambda x: x["search_score"], reverse=True)
            graph_results = graph_results[:self.max_graph_results]
            
            logger.info(f"🔗 Graph search: {len(graph_results)} results")
            return graph_results
        
        except Exception as e:
            logger.error(f"❌ Graph search failed: {e}")
            return []
    
    def combine_and_rank_results(self, semantic_results: List[Dict[str, Any]], 
                                graph_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine and rank semantic and graph search results."""
        try:
            all_results = []
            seen_chunk_ids = set()
            
            # Add semantic results with weighting
            for result in semantic_results:
                result_copy = result.copy()
                result_copy["final_score"] = result["search_score"] * self.semantic_weight
                all_results.append(result_copy)
                seen_chunk_ids.add(result["chunk_id"])
            
            # Add graph results with weighting, avoiding duplicates
            for result in graph_results:
                if result["chunk_id"] not in seen_chunk_ids:
                    result_copy = result.copy()
                    result_copy["final_score"] = result["search_score"] * self.graph_weight
                    all_results.append(result_copy)
                else:
                    # If chunk already exists from semantic search, boost its score
                    for existing_result in all_results:
                        if existing_result["chunk_id"] == result["chunk_id"]:
                            existing_result["final_score"] += result["search_score"] * self.graph_weight
                            existing_result["search_type"] = "hybrid"  # Mark as hybrid
                            if "relationship" in result:
                                existing_result["relationship"] = result["relationship"]
                            break
            
            # Sort by final score
            all_results.sort(key=lambda x: x["final_score"], reverse=True)
            
            # Limit total results
            max_total_results = self.max_semantic_results + self.max_graph_results
            final_results = all_results[:max_total_results]
            
            logger.info(f"🎯 Combined results: {len(final_results)} total (hybrid ranking)")
            return final_results
        
        except Exception as e:
            logger.error(f"❌ Result combination failed: {e}")
            return semantic_results  # Fallback to semantic results
    
    def search(self, query: str, vector_store: VectorStore, 
              query_embedding: List[float] = None) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic and graph approaches.
        
        Args:
            query: The search query
            vector_store: VectorStore instance containing data
            query_embedding: Pre-computed query embedding (optional)
            
        Returns:
            List of ranked search results
        """
        try:
            # If no embedding provided, we need to create one
            # This would normally use the embedder, but for modularity,
            # we'll handle this in the calling code
            if query_embedding is None:
                logger.warning("⚠️ No query embedding provided for semantic search")
                semantic_results = []
            else:
                # Step 1: Semantic search
                semantic_results = self.semantic_search(query_embedding, vector_store)
            
            # Step 2: Extract entities from query
            query_entities = self.extract_query_entities(query)
            
            # Step 3: Graph search
            graph_results = self.graph_search(query_entities, vector_store)
            
            # Step 4: Combine and rank results
            final_results = self.combine_and_rank_results(semantic_results, graph_results)
            
            # Add query metadata
            for result in final_results:
                result["query"] = query
                result["query_entities"] = query_entities
            
            logger.info(f"🔍 Hybrid search complete: {len(final_results)} final results")
            return final_results
        
        except Exception as e:
            logger.error(f"❌ Hybrid search failed: {e}")
            return []
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get search configuration statistics."""
        return {
            "semantic_weight": self.semantic_weight,
            "graph_weight": self.graph_weight,
            "max_semantic_results": self.max_semantic_results,
            "max_graph_results": self.max_graph_results,
            "min_similarity_threshold": self.min_similarity_threshold,
            "search_type": "hybrid"
        }