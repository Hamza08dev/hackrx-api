#!/usr/bin/env python3
"""
HackRx API - FastAPI Application
- Converts Streamlit app to API format
- Handles document processing and Q&A
- Meets hackathon requirements
"""

import os
import logging
import time
import uuid
import requests
import tempfile
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import hashlib
import json

# Load environment
load_dotenv()

# Import modular components
import sys
import os
# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processing.embedder import TextEmbedder
from processing.entity_extractor import EntityExtractor
from processing.vector_store import VectorStore
from qa.llm_answer import LLMAnswerGenerator
from qa.retriever import Retriever
from ingestion.document_loader import extract_text_from_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HackRx API",
    description="Document Processing and Q&A API for HackRx Hackathon",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
# Security
security = HTTPBearer()

# Pydantic models
class HackRxRequest(BaseModel):
    documents: str  # URL to document
    questions: List[str]

class HackRxResponse(BaseModel):
    answers: List[str]

# Global components (initialize once)
components = None

# Add caching
document_cache = {}

def get_document_hash(document_url: str) -> str:
    """Generate hash for document URL."""
    return hashlib.md5(document_url.encode()).hexdigest()

def get_cached_document(document_url: str) -> Dict[str, Any]:
    """Get cached document if available."""
    doc_hash = get_document_hash(document_url)
    if doc_hash in document_cache:
        cached_data = document_cache[doc_hash]
        # Check if cache is not too old (1 hour)
        if time.time() - cached_data.get('timestamp', 0) < 3600:
            logger.info(f"✅ Using cached document: {doc_hash[:8]}...")
            return cached_data.get('data', {})
    return None

def cache_document(document_url: str, data: Dict[str, Any]):
    """Cache document data."""
    doc_hash = get_document_hash(document_url)
    document_cache[doc_hash] = {
        'data': data,
        'timestamp': time.time()
    }
    logger.info(f"💾 Cached document: {doc_hash[:8]}...")
    
    # Keep cache size manageable (max 10 documents)
    if len(document_cache) > 10:
        oldest_key = min(document_cache.keys(), 
                        key=lambda k: document_cache[k]['timestamp'])
        del document_cache[oldest_key]
        logger.info(f"🗑️ Removed oldest cache entry: {oldest_key[:8]}...")

def get_components():
    """Get or initialize RAG components."""
    global components
    if components is None:
        try:
            components = {
                "embedder": TextEmbedder(),
                "entity_extractor": EntityExtractor(),
                "vector_store": VectorStore(),
                "llm_generator": LLMAnswerGenerator(),
                "retriever": Retriever(),
            }
            logger.info("✅ RAG components initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize components: {str(e)}"
            )
    return components

def download_document(url: str) -> str:
    """Download document from URL and return local file path."""
    try:
        logger.info(f"📥 Processing document from: {url}")
        
        # Handle file:// URLs
        if url.startswith('file://'):
            file_path = url.replace('file:///', '').replace('file://', '')
            # Convert forward slashes to backslashes on Windows
            file_path = file_path.replace('/', '\\')
            
            if not os.path.exists(file_path):
                raise ValueError(f"File not found: {file_path}")
            
            logger.info(f"✅ Using local file: {file_path}")
            return file_path
        
        # Handle HTTP URLs
        else:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_path = temp_file.name
            temp_file.close()
            
            # Download file
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✅ Document downloaded: {temp_path}")
            return temp_path
    
    except Exception as e:
        logger.error(f"❌ Document processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process document: {str(e)}"
        )

def process_document(components: Dict, document_url: str) -> str:
    """Process document and return document ID."""
    try:
        # Check cache first
        cached_data = get_cached_document(document_url)
        if cached_data:
            logger.info("✅ Using cached document data")
            return cached_data.get('document_id')
        
        # Download document with timeout
        logger.info("📥 Downloading document...")
        temp_path = download_document(document_url)
        
        # Extract text
        logger.info("📄 Extracting text...")
        text = extract_text_from_file(temp_path)
        
        if len(text.strip()) < 50:
            raise ValueError("Document text too short")
        
        # Generate document ID
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        
        # Process document with optimizations
        logger.info("📝 Processing document...")
        
        # Step 1: Chunk and embed (with smaller chunks for faster processing)
        logger.info("🧠 Creating embeddings...")
        chunks = components["embedder"].chunk_and_embed(text)
        
        # Step 2: Extract entities (optimized for speed)
        logger.info("🏷️ Extracting entities...")
        entities_data = components["entity_extractor"].extract_entities_batch(chunks)
        
        # Step 3: Store data
        logger.info("💾 Storing data...")
        success = components["vector_store"].add_document(doc_id, "Policy Document", chunks, entities_data)
        
        if not success:
            raise ValueError("Failed to store document")
        
        # Cache the result
        cache_document(document_url, {
            'document_id': doc_id,
            'text_length': len(text)
        })
        
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        logger.info(f"✅ Document processed: {doc_id}")
        return doc_id
    
    except Exception as e:
        logger.error(f"❌ Document processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )

def answer_questions(components: Dict, questions: List[str]) -> List[str]:
    """Answer multiple questions using the RAG system."""
    answers = []
    
    try:
        # Pre-compute query embeddings for all questions at once
        logger.info("🧠 Pre-computing query embeddings...")
        query_embeddings = []
        for question in questions:
            embedding = components["embedder"].create_query_embedding(question)
            query_embeddings.append(embedding)
        
        # Process questions with reduced delays
        for i, (question, query_embedding) in enumerate(zip(questions, query_embeddings)):
            logger.info(f"❓ Processing question {i+1}/{len(questions)}: {question[:50]}...")
            
            # Perform hybrid search
            search_results = components["retriever"].search(question, components["vector_store"], query_embedding)
            
            if not search_results:
                answer = "I don't have enough information to answer this question based on the provided document."
            else:
                # Generate answer with shorter timeout
                try:
                    answer = components["llm_generator"].generate_answer_with_style(
                        question, search_results, "concise"
                    )
                except Exception as e:
                    logger.warning(f"⚠️ LLM generation failed for question {i+1}: {e}")
                    answer = "Unable to generate answer due to processing timeout."
            
            answers.append(answer)
            
            # Reduced delay between questions
            if i < len(questions) - 1:
                time.sleep(0.5)  # Reduced from 1 second to 0.5 seconds
        
        logger.info(f"✅ Generated {len(answers)} answers")
        return answers
    
    except Exception as e:
        logger.error(f"❌ Question answering failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Question answering failed: {str(e)}"
        )

@app.post("/hackrx/run", response_model=HackRxResponse)
async def hackrx_run(
    request: HackRxRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Main endpoint for HackRx hackathon.
    
    Processes document and answers questions using RAG system.
    """
    try:
        start_time = time.time()
        
        # Validate API key (you can customize this)
        api_key = credentials.credentials
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required"
            )
        
        logger.info(f"🚀 Processing request: {len(request.questions)} questions")
        
        # Get components
        components = get_components()
        
        # Clear previous data
        components["vector_store"].clear_storage()
        
        # Process document
        doc_id = process_document(components, request.documents)
        
        # Answer questions
        answers = answer_questions(components, request.questions)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        logger.info(f"✅ Request completed in {processing_time:.2f}s")
        
        return HackRxResponse(answers=answers)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "HackRx API is running",
        "endpoints": {
            "main": "/hackrx/run",
            "health": "/health"
        }
    }

@app.options("/hackrx/run")
async def options_hackrx_run():
    """Handle OPTIONS requests for CORS preflight."""
    return {"message": "OK"}
if __name__ == "__main__":
    # Run with uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )