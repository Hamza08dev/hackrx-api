#!/usr/bin/env python3
"""
Text Embedder Module
- Chunks text using LangChain's RecursiveCharacterTextSplitter
- Creates embeddings using Gemini API (gemini-embedding-001)
- Handles rate limiting and retries
- OPTIMIZED for speed with larger chunks and batch processing
"""

import os
import logging
import time
import asyncio
import concurrent.futures
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class TextEmbedder:
    """Text chunking and embedding using Gemini API - OPTIMIZED for speed."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "models/embedding-001", config: Optional[Dict[str, Any]] = None):
        """Initialize with Gemini API."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY in .env file")
        
        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        
        # Load configuration
        if config is None:
            try:
                from config import Config
                config = Config.get_embedding_config()
            except ImportError:
                # Fallback to default values
                config = {
                    "chunk_size": 1500,
                    "chunk_overlap": 100,
                    "min_chunk_size": 100,
                    "batch_size": 5,
                    "max_workers": 3,
                    "max_retries": 2,
                    "retry_delay": 0.5,
                    "batch_delay": 0.1
                }
        
        # OPTIMIZED Text splitter configuration for speed
        self.chunk_size = config.get("chunk_size", 1500)
        self.chunk_overlap = config.get("chunk_overlap", 100)
        self.min_chunk_size = config.get("min_chunk_size", 100)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # OPTIMIZED Rate limiting and batch processing
        self.max_retries = config.get("max_retries", 2)
        self.retry_delay = config.get("retry_delay", 0.5)
        self.batch_size = config.get("batch_size", 5)
        self.batch_delay = config.get("batch_delay", 0.1)
        self.max_workers = config.get("max_workers", 3)
        
        logger.info(f"✅ TextEmbedder initialized with {model_name} (OPTIMIZED)")
    
    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """Split text into semantic chunks - OPTIMIZED."""
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            # Create chunk objects with metadata - FILTER for substantial chunks
            chunk_objects = []
            for i, chunk_text in enumerate(chunks):
                # Use configurable minimum chunk size for better quality
                if len(chunk_text.strip()) > self.min_chunk_size:
                    chunk_objects.append({
                        "id": f"chunk_{i}",
                        "text": chunk_text.strip(),
                        "index": i,
                        "length": len(chunk_text),
                        "metadata": {
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "chunk_size": self.chunk_size,
                            "overlap": self.chunk_overlap
                        }
                    })
            
            logger.info(f"✅ Created {len(chunk_objects)} chunks from {len(text)} chars (OPTIMIZED)")
            return chunk_objects
        
        except Exception as e:
            logger.error(f"❌ Chunking failed: {e}")
            raise
    
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding for text using Gemini API with retries - OPTIMIZED."""
        for attempt in range(self.max_retries):
            try:
                # Call Gemini embedding API
                result = genai.embed_content(
                    model=self.model_name,
                    content=text,
                    task_type="retrieval_document"
                )
                
                embedding = result['embedding']
                logger.debug(f"✅ Created embedding: {len(embedding)} dimensions")
                return embedding
            
            except Exception as e:
                logger.warning(f"⚠️ Embedding attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"🔄 Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"❌ All embedding attempts failed for text: {text[:100]}...")
                    raise
    
    def embed_chunks_batch(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create embeddings for chunks in batches - OPTIMIZED for speed."""
        embedded_chunks = []
        
        # Process chunks in batches
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            batch_start = i + 1
            batch_end = min(i + self.batch_size, len(chunks))
            
            logger.info(f"🧠 Processing batch {batch_start}-{batch_end}/{len(chunks)}")
            
            # Process batch with ThreadPoolExecutor for parallel API calls
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit embedding tasks
                future_to_chunk = {
                    executor.submit(self.create_embedding, chunk["text"]): chunk 
                    for chunk in batch
                }
                
                # Collect results
                for future in concurrent.futures.as_completed(future_to_chunk):
                    chunk = future_to_chunk[future]
                    try:
                        embedding = future.result()
                        
                        # Add embedding to chunk
                        embedded_chunk = chunk.copy()
                        embedded_chunk["embedding"] = embedding
                        embedded_chunk["embedding_model"] = self.model_name
                        embedded_chunk["embedding_dimensions"] = len(embedding)
                        
                        embedded_chunks.append(embedded_chunk)
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to embed chunk {chunk['index']}: {e}")
                        # Continue with other chunks
                        continue
            
            # Reduced delay between batches
            if i + self.batch_size < len(chunks):
                time.sleep(self.batch_delay)
        
        logger.info(f"✅ Successfully embedded {len(embedded_chunks)}/{len(chunks)} chunks (BATCHED)")
        return embedded_chunks
    
    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Legacy method - now uses optimized batch processing."""
        return self.embed_chunks_batch(chunks)
    
    def chunk_and_embed(self, text: str) -> List[Dict[str, Any]]:
        """Complete pipeline: chunk text and create embeddings - OPTIMIZED."""
        try:
            # Step 1: Chunk text (optimized)
            chunks = self.chunk_text(text)
            if not chunks:
                raise ValueError("No valid chunks created from text")
            
            # Step 2: Create embeddings (batch processing)
            embedded_chunks = self.embed_chunks_batch(chunks)
            if not embedded_chunks:
                raise ValueError("No embeddings created")
            
            logger.info(f"🎯 Complete: {len(embedded_chunks)} chunks with embeddings (OPTIMIZED)")
            return embedded_chunks
        
        except Exception as e:
            logger.error(f"❌ Chunk and embed pipeline failed: {e}")
            raise
    
    def create_query_embedding(self, query: str) -> List[float]:
        """Create embedding for search query."""
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=query,
                task_type="retrieval_query"
            )
            
            embedding = result['embedding']
            logger.debug(f"✅ Query embedding: {len(embedding)} dimensions")
            return embedding
        
        except Exception as e:
            logger.error(f"❌ Query embedding failed: {e}")
            raise
    
    def get_embedding_info(self) -> Dict[str, Any]:
        """Get information about the embedding model."""
        return {
            "model": self.model_name,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "batch_size": self.batch_size,
            "batch_delay": self.batch_delay,
            "optimized": True
        }