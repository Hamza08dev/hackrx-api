#!/usr/bin/env python3
"""
Performance Test Script
- Measures chunking and embedding performance
- Compares optimized vs non-optimized settings
- Provides detailed timing breakdowns
"""

import time
import logging
from processing.embedder import TextEmbedder
from processing.entity_extractor import EntityExtractor
from ingestion.document_loader import extract_text_from_file
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_chunking_performance(text: str, embedder: TextEmbedder) -> dict:
    """Test chunking performance and return metrics."""
    logger.info("🧪 Testing chunking performance...")
    
    start_time = time.time()
    chunks = embedder.chunk_text(text)
    chunking_time = time.time() - start_time
    
    return {
        "chunking_time": chunking_time,
        "num_chunks": len(chunks),
        "avg_chunk_size": sum(len(chunk["text"]) for chunk in chunks) / len(chunks) if chunks else 0,
        "text_length": len(text)
    }

def test_embedding_performance(chunks: list, embedder: TextEmbedder) -> dict:
    """Test embedding performance and return metrics."""
    logger.info("🧪 Testing embedding performance...")
    
    start_time = time.time()
    embedded_chunks = embedder.embed_chunks_batch(chunks)
    embedding_time = time.time() - start_time
    
    return {
        "embedding_time": embedding_time,
        "num_embedded": len(embedded_chunks),
        "avg_time_per_chunk": embedding_time / len(chunks) if chunks else 0
    }

def test_full_pipeline_performance(text: str, embedder: TextEmbedder, entity_extractor: EntityExtractor) -> dict:
    """Test full pipeline performance."""
    logger.info("🧪 Testing full pipeline performance...")
    
    start_time = time.time()
    
    # Step 1: Chunk and embed
    chunks = embedder.chunk_and_embed(text)
    chunk_embed_time = time.time() - start_time
    
    # Step 2: Entity extraction
    entity_start = time.time()
    entities = entity_extractor.extract_entities_batch(chunks)
    entity_time = time.time() - entity_start
    
    total_time = time.time() - start_time
    
    return {
        "total_time": total_time,
        "chunk_embed_time": chunk_embed_time,
        "entity_time": entity_time,
        "num_chunks": len(chunks),
        "num_entities": sum(len(v) for v in entities.get("entities", {}).values())
    }

def compare_optimizations():
    """Compare performance with different configurations."""
    
    # Test with sample text (you can replace with actual document)
    sample_text = """
    This is a sample document for performance testing. It contains multiple paragraphs 
    to simulate real-world document processing scenarios. The text should be long enough 
    to create multiple chunks and test the embedding pipeline effectively.
    
    Performance optimization is crucial for real-time applications. We need to ensure 
    that document processing happens quickly while maintaining accuracy. The chunking 
    process should be efficient and the embedding calls should be optimized.
    
    Machine learning models require careful tuning of parameters. Chunk size, overlap, 
    and batch processing all affect performance. We need to find the right balance 
    between speed and quality.
    
    API rate limiting is another important consideration. We need to respect the 
    service provider's limits while maximizing throughput. Parallel processing and 
    intelligent batching can help achieve this.
    
    The entity extraction process should also be optimized. Reducing the number of 
    API calls while maintaining extraction quality is key. Single-pass processing 
    with comprehensive prompts can help achieve this goal.
    """ * 10  # Repeat to make it longer
    
    logger.info(f"📄 Test document length: {len(sample_text)} characters")
    
    # Test with optimized embedder
    embedder = TextEmbedder()
    entity_extractor = EntityExtractor()
    
    logger.info("🚀 Running performance tests...")
    
    # Test 1: Chunking performance
    chunk_metrics = test_chunking_performance(sample_text, embedder)
    
    # Test 2: Get chunks for embedding test
    chunks = embedder.chunk_text(sample_text)
    
    # Test 3: Embedding performance
    embed_metrics = test_embedding_performance(chunks, embedder)
    
    # Test 4: Full pipeline
    pipeline_metrics = test_full_pipeline_performance(sample_text, embedder, entity_extractor)
    
    # Print results
    print("\n" + "="*60)
    print("📊 PERFORMANCE TEST RESULTS")
    print("="*60)
    
    print(f"\n📝 CHUNKING METRICS:")
    print(f"   Time: {chunk_metrics['chunking_time']:.2f}s")
    print(f"   Chunks: {chunk_metrics['num_chunks']}")
    print(f"   Avg chunk size: {chunk_metrics['avg_chunk_size']:.0f} chars")
    print(f"   Speed: {chunk_metrics['text_length']/chunk_metrics['chunking_time']:.0f} chars/sec")
    
    print(f"\n🧠 EMBEDDING METRICS:")
    print(f"   Time: {embed_metrics['embedding_time']:.2f}s")
    print(f"   Embedded: {embed_metrics['num_embedded']}")
    print(f"   Avg time per chunk: {embed_metrics['avg_time_per_chunk']:.2f}s")
    print(f"   Speed: {embed_metrics['num_embedded']/embed_metrics['embedding_time']:.1f} chunks/sec")
    
    print(f"\n🎯 FULL PIPELINE METRICS:")
    print(f"   Total time: {pipeline_metrics['total_time']:.2f}s")
    print(f"   Chunk+Embed: {pipeline_metrics['chunk_embed_time']:.2f}s")
    print(f"   Entity extraction: {pipeline_metrics['entity_time']:.2f}s")
    print(f"   Entities found: {pipeline_metrics['num_entities']}")
    
    # Performance recommendations
    print(f"\n💡 PERFORMANCE INSIGHTS:")
    if chunk_metrics['chunking_time'] > 1.0:
        print("   ⚠️  Chunking is slow - consider larger chunk sizes")
    else:
        print("   ✅ Chunking performance is good")
    
    if embed_metrics['avg_time_per_chunk'] > 2.0:
        print("   ⚠️  Embedding is slow - check API rate limits")
    else:
        print("   ✅ Embedding performance is good")
    
    if pipeline_metrics['total_time'] > 30.0:
        print("   ⚠️  Total pipeline is slow - consider optimizations")
    else:
        print("   ✅ Pipeline performance is acceptable")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    compare_optimizations() 