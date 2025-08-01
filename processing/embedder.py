#!/usr/bin/env python3
"""
Text Embedder Module
- Chunks text using LangChain's RecursiveCharacterTextSplitter
- Creates embeddings using Gemini API (gemini-embedding-001)
- Handles rate limiting and retries
"""

import os
import logging
import time
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class TextEmbedder:
    """Text chunking and embedding using Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "models/embedding-001"):
        """Initialize with Gemini API."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY in .env file")
        
        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        
        # Text splitter configuration (optimized for speed)
        self.chunk_size = 800  # Smaller chunks for faster processing
        self.chunk_overlap = 150  # Reduced overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Rate limiting
        self.max_retries = 3
        self.retry_delay = 1.0
        
        logger.info(f"✅ TextEmbedder initialized with {model_name}")
    
    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """Split text into semantic chunks."""
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            # Create chunk objects with metadata
            chunk_objects = []
            for i, chunk_text in enumerate(chunks):
                if len(chunk_text.strip()) > 50:  # Only include substantial chunks
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
            
            logger.info(f"✅ Created {len(chunk_objects)} chunks from {len(text)} chars")
            return chunk_objects
        
        except Exception as e:
            logger.error(f"❌ Chunking failed: {e}")
            raise
    
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding for text using Gemini API with retries."""
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
    
    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create embeddings for all chunks with rate limiting."""
        embedded_chunks = []
        
        for i, chunk in enumerate(chunks):
            try:
                logger.info(f"🧠 Embedding chunk {i + 1}/{len(chunks)}")
                
                # Create embedding
                embedding = self.create_embedding(chunk["text"])
                
                # Add embedding to chunk
                embedded_chunk = chunk.copy()
                embedded_chunk["embedding"] = embedding
                embedded_chunk["embedding_model"] = self.model_name
                embedded_chunk["embedding_dimensions"] = len(embedding)
                
                embedded_chunks.append(embedded_chunk)
                
                # Rate limiting - reduced delay for faster processing
                if i < len(chunks) - 1:
                    time.sleep(0.2)  # Reduced from 0.5 to 0.2 seconds
            
            except Exception as e:
                logger.error(f"❌ Failed to embed chunk {i}: {e}")
                # Continue with other chunks
                continue
        
        logger.info(f"✅ Successfully embedded {len(embedded_chunks)}/{len(chunks)} chunks")
        return embedded_chunks
    
    def chunk_and_embed(self, text: str) -> List[Dict[str, Any]]:
        """Complete pipeline: chunk text and create embeddings."""
        try:
            # Step 1: Chunk text
            chunks = self.chunk_text(text)
            if not chunks:
                raise ValueError("No valid chunks created from text")
            
            # Step 2: Create embeddings
            embedded_chunks = self.embed_chunks(chunks)
            if not embedded_chunks:
                raise ValueError("No embeddings created")
            
            logger.info(f"🎯 Complete: {len(embedded_chunks)} chunks with embeddings")
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
            "retry_delay": self.retry_delay
        }