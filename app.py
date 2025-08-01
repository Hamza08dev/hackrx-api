#!/usr/bin/env python3
"""
Hybrid RAG System - Streamlit UI
- Clean UI layer using modular components
- Document upload and processing interface
- Question answering with hybrid search
- Architecture: Gemini (processing) + OpenRouter (answers)
"""

import streamlit as st
import os
import time
import uuid
from typing import List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import modular components
@st.cache_resource
def load_rag_components():
    """Load and cache RAG system components."""
    try:
        from processing.embedder import TextEmbedder
        from processing.entity_extractor import EntityExtractor
        from processing.vector_store import VectorStore
        from qa.llm_answer import LLMAnswerGenerator
        from qa.retriever import Retriever
        from ingestion.document_loader import extract_text_from_file
        
        return {
            "embedder": TextEmbedder(),
            "entity_extractor": EntityExtractor(),
            "vector_store": VectorStore(),
            "llm_generator": LLMAnswerGenerator(),
            "retriever": Retriever(),
            "extract_text": extract_text_from_file
        }
    except Exception as e:
        st.error(f"❌ Failed to load components: {e}")
        st.stop()

def process_document(components: Dict, title: str, text: str) -> Dict[str, Any]:
    """Process document using modular components."""
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    
    try:
        with st.status("Processing document...", expanded=True) as status:
            # Step 1: Chunk and embed
            status.update(label="📝 Chunking and embedding with Gemini...")
            chunks = components["embedder"].chunk_and_embed(text)
            
            # Step 2: Extract entities
            status.update(label="🧠 Extracting entities with Gemini...")
            entities_data = components["entity_extractor"].extract_entities_batch(chunks)
            
            # Step 3: Store data
            status.update(label="💾 Storing data...")
            success = components["vector_store"].add_document(doc_id, title, chunks, entities_data)
            
            if success:
                status.update(label="✅ Processing complete!", state="complete")
                
                # Calculate stats
                entity_count = sum(len(v) for v in entities_data.get("entities", {}).values())
                relationship_count = len(entities_data.get("relationships", []))
                
                return {
                    "success": True,
                    "doc_id": doc_id,
                    "chunks": len(chunks),
                    "entities": entity_count,
                    "relationships": relationship_count
                }
            else:
                status.update(label="❌ Storage failed", state="error")
                return {"success": False, "error": "Failed to store document"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def answer_question(components: Dict, question: str) -> Dict[str, Any]:
    """Answer question using hybrid RAG system."""
    try:
        # Create query embedding
        query_embedding = components["embedder"].create_query_embedding(question)
        
        # Perform hybrid search
        search_results = components["retriever"].search(question, components["vector_store"], query_embedding)
        
        if not search_results:
            return {"success": False, "error": "No relevant information found"}
        
        # Generate answer (always concise for cost optimization)
        answer = components["llm_generator"].generate_answer_with_style(
            question, search_results, "concise"
        )
        
        return {
            "success": True,
            "answer": answer,
            "sources": search_results,
            "stats": components["vector_store"].get_stats()
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def display_entity_viewer(components: Dict):
    """Display entity and relationship viewer."""
    st.subheader("🏷️ Entity & Relationship Viewer")
    
    entities_by_type = components["vector_store"].get_all_entities_by_type()
    relationships = components["vector_store"].get_all_relationships()
    
    if not entities_by_type and not relationships:
        st.info("📝 Process documents first to see extracted entities and relationships")
        return
    
    # Entity viewer
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Entities by Type**")
        for entity_type, entities in entities_by_type.items():
            if entities:
                with st.expander(f"{entity_type} ({len(entities)})"):
                    for entity in entities[:10]:  # Limit display
                        st.write(f"• {entity['name']}")
                    if len(entities) > 10:
                        st.write(f"... and {len(entities) - 10} more")
    
    with col2:
        st.write("**Relationships**")
        if relationships:
            with st.expander(f"Relationships ({len(relationships)})"):
                for rel in relationships[:10]:  # Limit display
                    st.write(f"• {rel['source']} **{rel['type']}** {rel['target']}")
                if len(relationships) > 10:
                    st.write(f"... and {len(relationships) - 10} more")

def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="Hybrid RAG System",
        page_icon="🔀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Main header
    st.title("🔀 Hybrid RAG System")
    st.caption("**Clean Modular Architecture**: Gemini processing → OpenRouter answers")
    
    # Load components
    components = load_rag_components()
    
    # Get current stats
    stats = components["vector_store"].get_stats()
    
    # Sidebar with system info
    with st.sidebar:
        st.header("📊 System Status")
        st.metric("📚 Documents", stats.get("documents", 0))
        st.metric("📝 Chunks", stats.get("chunks", 0))
        st.metric("🏷️ Entities", stats.get("entities", 0))
        st.metric("🔗 Relations", stats.get("relationships", 0))
        
        st.divider()
        st.header("🔧 Architecture")
        st.success("🎯 **Processing**: Gemini API")
        st.info("🚀 **Answers**: OpenRouter API")
        st.caption("DeepSeek R1 (free tier)")
        
        if st.button("🗑️ Clear All Data", type="secondary"):
            components["vector_store"].clear_storage()
            st.rerun()
    
    # Main interface tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload Documents", "❓ Ask Questions", "🏷️ View Data"])
    
    # Tab 1: Document Upload
    with tab1:
        st.header("📤 Document Upload & Processing")
        
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            help="Supported formats: PDF, DOCX, TXT"
        )
        
        if uploaded_files:
            if st.button("🚀 Process All Documents", type="primary"):
                progress_bar = st.progress(0)
                success_count = 0
                
                for i, file in enumerate(uploaded_files):
                    st.write(f"**Processing**: {file.name}")
                    
                    try:
                        # Save temp file
                        temp_path = f"temp_{file.name}"
                        with open(temp_path, "wb") as f:
                            f.write(file.getbuffer())
                        
                        # Extract text
                        text = components["extract_text"](temp_path)
                        
                        if len(text.strip()) < 50:
                            st.error(f"❌ {file.name}: Text too short")
                            continue
                        
                        # Process document
                        result = process_document(components, file.name, text)
                        
                        if result["success"]:
                            st.success(f"✅ {file.name}: {result['chunks']} chunks, {result['entities']} entities")
                            success_count += 1
                        else:
                            st.error(f"❌ {file.name}: {result.get('error', 'Unknown error')}")
                        
                        # Cleanup
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                    
                    except Exception as e:
                        st.error(f"❌ {file.name}: {e}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                if success_count > 0:
                    st.balloons()
                    st.success(f"🎉 Successfully processed {success_count} documents!")
                    time.sleep(1)
                    st.rerun()
    
    # Tab 2: Question Answering
    with tab2:
        st.header("❓ Question & Answer")
        
        if stats.get("documents", 0) == 0:
            st.warning("⚠️ Please upload and process documents first!")
        else:
            st.success(f"📚 Ready! {stats.get('documents', 0)} documents loaded")
            
            # Question input
            col1, col2 = st.columns([4, 1])
            
            with col1:
                question = st.text_input(
                    "Ask your question:",
                    placeholder="What technologies are mentioned? Who are the key people? What projects are described?",
                    key="question_input"
                )
            
            with col2:
                st.metric("🔀 Mode", "Hybrid")
            
            if st.button("🔍 Ask Question", type="primary", disabled=not question):
                if question:
                    with st.spinner("🧠 Processing question..."):
                        result = answer_question(components, question)
                    
                    if result["success"]:
                        # Display answer
                        st.subheader("🎯 Answer")
                        st.write(result["answer"])
                        
                        # Display sources
                        st.subheader("📄 Sources")
                        sources = result["sources"]
                        
                        for i, source in enumerate(sources, 1):
                            similarity = source.get("similarity", 0)
                            search_type = source.get("search_type", "unknown")
                            title = source.get("document_title", "Unknown")
                            
                            # Color coding by search type
                            color = "🔍" if search_type == "semantic" else "🔗" if search_type == "graph" else "🔀"
                            
                            with st.expander(f"{color} Source {i} - {title} (score: {similarity:.3f}, {search_type})"):
                                st.write(source["text"][:500] + ("..." if len(source["text"]) > 500 else ""))
                                
                                # Show relationship info for graph results
                                if "relationship" in source:
                                    rel = source["relationship"]
                                    st.info(f"🔗 Relationship: {rel['source']} **{rel['type']}** {rel['target']}")
                    else:
                        st.error(f"❌ {result.get('error', 'Unknown error')}")
    
    # Tab 3: Data Viewer
    with tab3:
        if stats.get("documents", 0) == 0:
            st.info("📝 Upload documents first to see extracted data")
        else:
            display_entity_viewer(components)
    
    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("🔀 **Hybrid RAG System**")
    with col2:
        st.caption("🧠 **Modular Architecture**")
    with col3:
        st.caption("⚡ **Cost Optimized**")

if __name__ == "__main__":
    main()