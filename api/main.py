#!/usr/bin/env python3
"""
FastAPI REST API for Hybrid RAG System
- Document upload and processing endpoints
- Question answering endpoints
- System statistics and health checks
"""

import os
import sys
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our modular components
try:
    from processing.embedder import TextEmbedder
    from processing.entity_extractor import EntityExtractor
    from processing.vector_store import VectorStore
    from qa.llm_answer import LLMAnswerGenerator
    from qa.retriever import Retriever
    from ingestion.document_loader import extract_text_from_file, is_supported_file
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    sys.exit(1)

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Hybrid RAG System API",
    description="REST API for document processing and question answering using Gemini + OpenRouter",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class QuestionRequest(BaseModel):
    question: str
    style: Optional[str] = "concise"  # concise, detailed, bullet

class QuestionResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    stats: Dict[str, Any]
    processing_time: float

class DocumentResponse(BaseModel):
    document_id: str
    title: str
    status: str
    chunks: int
    entities: int
    relationships: int
    processing_time: float

class SystemStats(BaseModel):
    documents: int
    chunks: int
    entities: int
    relationships: int
    storage_type: str
    api_version: str
    timestamp: str

# Global system components
embedder = None
entity_extractor = None
vector_store = None
llm_generator = None
retriever = None
system_initialized = False

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG system on startup."""
    global embedder, entity_extractor, vector_store, llm_generator, retriever, system_initialized
    
    try:
        logger.info("🚀 Initializing Hybrid RAG System...")
        
        # Initialize components
        embedder = TextEmbedder()
        entity_extractor = EntityExtractor()
        vector_store = VectorStore()
        llm_generator = LLMAnswerGenerator()
        retriever = Retriever()
        
        system_initialized = True
        logger.info("✅ Hybrid RAG System initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize system: {e}")
        system_initialized = False

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy" if system_initialized else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "embedder": embedder is not None,
            "entity_extractor": entity_extractor is not None,
            "vector_store": vector_store is not None,
            "llm_generator": llm_generator is not None,
            "retriever": retriever is not None
        }
    }

@app.get("/stats", response_model=SystemStats)
async def get_system_stats():
    """Get system statistics."""
    if not system_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    stats = vector_store.get_stats()
    
    return SystemStats(
        documents=stats["documents"],
        chunks=stats["chunks"],
        entities=stats["entities"],
        relationships=stats["relationships"],
        storage_type=stats["storage_type"],
        api_version="1.0.0",
        timestamp=datetime.now().isoformat()
    )

@app.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document."""
    if not system_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    start_time = datetime.now()
    
    try:
        # Validate file type
        if not is_supported_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported: PDF, DOCX, TXT"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Extract text
            logger.info(f"📄 Processing uploaded file: {file.filename}")
            text = extract_text_from_file(temp_path)
            
            if len(text.strip()) < 50:
                raise HTTPException(
                    status_code=400,
                    detail="Document contains insufficient text content"
                )
            
            # Generate document ID
            doc_id = f"doc_{uuid.uuid4().hex[:8]}"
            
            # Process with embedder
            logger.info(f"🧠 Creating embeddings...")
            chunks = embedder.chunk_and_embed(text)
            
            # Extract entities
            logger.info(f"🏷️ Extracting entities...")
            entities_data = entity_extractor.extract_entities_batch(chunks)
            
            # Store in vector store
            logger.info(f"💾 Storing data...")
            success = vector_store.add_document(doc_id, file.filename, chunks, entities_data)
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to store document")
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Count results
            entity_count = sum(len(v) for v in entities_data.get("entities", {}).values())
            relationship_count = len(entities_data.get("relationships", []))
            
            logger.info(f"✅ Document processed: {len(chunks)} chunks, {entity_count} entities")
            
            return DocumentResponse(
                document_id=doc_id,
                title=file.filename,
                status="processed",
                chunks=len(chunks),
                entities=entity_count,
                relationships=relationship_count,
                processing_time=processing_time
            )
        
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Document processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Answer a question using the RAG system."""
    if not system_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    start_time = datetime.now()
    
    try:
        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Check if we have documents
        stats = vector_store.get_stats()
        if stats["documents"] == 0:
            raise HTTPException(status_code=400, detail="No documents uploaded yet")
        
        logger.info(f"❓ Processing question: {question}")
        
        # Create query embedding
        query_embedding = embedder.create_query_embedding(question)
        
        # Perform hybrid search
        search_results = retriever.search(question, vector_store, query_embedding)
        
        if not search_results:
            raise HTTPException(status_code=404, detail="No relevant information found")
        
        # Generate answer
        answer = llm_generator.generate_answer_with_style(
            question, search_results, request.style
        )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Question answered in {processing_time:.2f}s")
        
        return QuestionResponse(
            answer=answer,
            sources=search_results,
            stats=stats,
            processing_time=processing_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Question answering failed: {e}")
        raise HTTPException(status_code=500, detail=f"Question processing failed: {str(e)}")

@app.get("/documents")
async def list_documents():
    """List all uploaded documents."""
    if not system_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        documents = []
        for doc_id, doc_info in vector_store.documents.items():
            documents.append({
                "document_id": doc_id,
                "title": doc_info["title"],
                "chunk_count": doc_info["chunk_count"],
                "timestamp": doc_info["timestamp"],
                "metadata": doc_info.get("metadata", {})
            })
        
        return {
            "documents": documents,
            "total": len(documents)
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")

@app.get("/entities")
async def list_entities(entity_type: Optional[str] = Query(None, description="Filter by entity type")):
    """List entities, optionally filtered by type."""
    if not system_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        all_entities = vector_store.get_all_entities_by_type()
        
        if entity_type:
            if entity_type in all_entities:
                return {
                    "entities": {entity_type: all_entities[entity_type]},
                    "total": len(all_entities[entity_type])
                }
            else:
                return {"entities": {}, "total": 0}
        else:
            total = sum(len(entities) for entities in all_entities.values())
            return {
                "entities": all_entities,
                "total": total
            }
    
    except Exception as e:
        logger.error(f"❌ Failed to list entities: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve entities")

@app.get("/relationships")
async def list_relationships():
    """List all relationships."""
    if not system_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        relationships = vector_store.get_all_relationships()
        
        return {
            "relationships": relationships,
            "total": len(relationships)
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to list relationships: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve relationships")

@app.delete("/clear")
async def clear_storage():
    """Clear all stored data."""
    if not system_initialized:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        vector_store.clear_storage()
        logger.info("🗑️ Storage cleared via API")
        
        return {"message": "Storage cleared successfully"}
    
    except Exception as e:
        logger.error(f"❌ Failed to clear storage: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear storage")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Hybrid RAG System API",
        "version": "1.0.0",
        "description": "REST API for document processing and question answering",
        "architecture": "Gemini (processing) + OpenRouter (answers)",
        "endpoints": {
            "health": "/health",
            "stats": "/stats",
            "upload": "/upload",
            "ask": "/ask",
            "documents": "/documents",
            "entities": "/entities",
            "relationships": "/relationships",
            "clear": "/clear"
        },
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)