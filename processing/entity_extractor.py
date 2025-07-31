#!/usr/bin/env python3
"""
Entity Extractor Module
- Extracts entities and relationships using Gemini API
- Supports various entity types: PERSON, ORGANIZATION, TECHNOLOGY, etc.
- Handles rate limiting and batch processing
"""

import os
import logging
import time
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class EntityExtractor:
    """Entity and relationship extraction using Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        """Initialize with Gemini API."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY in .env file")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        
        # REDUCED Entity types - only most important ones
        self.entity_types = [
            "PERSON", "ORGANIZATION", "TECHNOLOGY", "SKILL"
        ]
        
        # REDUCED Relationship types - only core ones
        self.relationship_types = [
            "WORKS_AT", "USES", "HAS_SKILL", "DEVELOPS"
        ]
        
        # INCREASED Rate limiting to save quota
        self.max_retries = 2  # Reduced retries
        self.retry_delay = 2.0  # Longer delays
        self.batch_delay = 3.0  # Much longer batch delays
        self.calls_per_document = 1  # LIMIT: Only 1 API call per document
        
        logger.info(f"✅ EntityExtractor initialized with {model_name}")
    
    def create_extraction_prompt(self, text: str) -> str:
        """Create focused prompt for CORE entity and relationship extraction."""
        prompt = f"""
Extract ONLY the most important entities and relationships from this text. Focus on quality over quantity.

Text: {text}

Extract ONLY these types:

ENTITIES (max 3-5 per type):
- PERSON: Key people mentioned (names only)
- ORGANIZATION: Main companies/institutions 
- TECHNOLOGY: Important technologies/tools/languages
- SKILL: Core professional skills

RELATIONSHIPS (max 5 total):
- [person] WORKS_AT [organization]
- [person] USES [technology]
- [person] HAS_SKILL [skill]
- [organization] DEVELOPS [technology]

Be selective - only include the MOST IMPORTANT entities and relationships.

Format response exactly as:
ENTITIES:
PERSON: name1, name2
ORGANIZATION: org1, org2
TECHNOLOGY: tech1, tech2
SKILL: skill1, skill2

RELATIONSHIPS:
source1 WORKS_AT target1
source2 USES target2
source3 HAS_SKILL target3
"""
        return prompt
    
    def parse_extraction_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini's response into structured entity and relationship data."""
        entities = {entity_type: [] for entity_type in self.entity_types}
        relationships = []
        
        if not response_text:
            return {"entities": entities, "relationships": relationships}
        
        lines = response_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if 'ENTITIES:' in line:
                current_section = 'entities'
                continue
            elif 'RELATIONSHIPS:' in line:
                current_section = 'relationships'
                continue
            
            if not line:
                continue
            
            if current_section == 'entities':
                # Parse entity lines: "TYPE: entity1, entity2, entity3"
                if ':' in line:
                    entity_type, entity_list = line.split(':', 1)
                    entity_type = entity_type.strip()
                    
                    if entity_type in self.entity_types:
                        names = [name.strip() for name in entity_list.split(',') if name.strip()]
                        for name in names:
                            if len(name) > 1:  # Filter out single characters
                                entities[entity_type].append({
                                    "name": name,
                                    "type": entity_type,
                                    "confidence": 0.8,
                                    "method": "gemini_api"
                                })
            
            elif current_section == 'relationships':
                # Parse relationship lines: "source RELATIONSHIP_TYPE target"
                for rel_type in self.relationship_types:
                    if rel_type in line:
                        parts = line.split(rel_type)
                        if len(parts) == 2:
                            source = parts[0].strip()
                            target = parts[1].strip()
                            if source and target:
                                relationships.append({
                                    "type": rel_type,
                                    "source": source,
                                    "target": target,
                                    "confidence": 0.7,
                                    "method": "gemini_api"
                                })
                        break
        
        return {"entities": entities, "relationships": relationships}
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities and relationships from text using Gemini API."""
        for attempt in range(self.max_retries):
            try:
                # Create extraction prompt
                prompt = self.create_extraction_prompt(text)
                
                # Call Gemini API
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=1500,
                        temperature=0.1
                    )
                )
                
                if not response.text:
                    logger.warning("⚠️ Empty response from Gemini")
                    return {"entities": {}, "relationships": []}
                
                # Parse response
                result = self.parse_extraction_response(response.text)
                
                # Log results
                entity_count = sum(len(v) for v in result["entities"].values())
                relationship_count = len(result["relationships"])
                logger.info(f"✅ Extracted {entity_count} entities and {relationship_count} relationships")
                
                return result
            
            except Exception as e:
                logger.warning(f"⚠️ Entity extraction attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"🔄 Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"❌ All entity extraction attempts failed")
                    return {"entities": {}, "relationships": []}
    
    def extract_entities_batch(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract entities from multiple text chunks with MINIMAL API calls."""
        all_entities = {entity_type: [] for entity_type in self.entity_types}
        all_relationships = []
        
        try:
            # OPTIMIZATION: Combine first few chunks into single text for 1 API call
            combined_text = ""
            max_chars = 3000  # Limit combined text to avoid token limits
            
            for chunk in chunks[:5]:  # Only use first 5 chunks max
                chunk_text = chunk["text"]
                if len(combined_text) + len(chunk_text) < max_chars:
                    combined_text += chunk_text + "\n\n"
                else:
                    break
            
            if combined_text.strip():
                logger.info(f"🧠 Processing document with SINGLE API call (quota optimization)")
                
                # Single API call for entire document
                result = self.extract_entities(combined_text)
                
                # Store results
                all_entities = result["entities"]
                all_relationships = result["relationships"]
                
                # Longer delay after single call
                logger.info(f"⏱️ Quota protection delay ({self.batch_delay}s)...")
                time.sleep(self.batch_delay)
            else:
                logger.warning("⚠️ No text to process for entity extraction")
        
        except Exception as e:
            logger.error(f"❌ Optimized entity extraction failed: {e}")
            # Fallback: return empty results to avoid further API calls
            return {"entities": all_entities, "relationships": all_relationships}
        
        # Deduplicate entities by name (case-insensitive)
        for entity_type in all_entities:
            seen_names = set()
            deduplicated = []
            for entity in all_entities[entity_type]:
                name_lower = entity["name"].lower()
                if name_lower not in seen_names:
                    seen_names.add(name_lower)
                    deduplicated.append(entity)
            all_entities[entity_type] = deduplicated
        
        # Deduplicate relationships
        seen_relationships = set()
        deduplicated_relationships = []
        for rel in all_relationships:
            rel_key = f"{rel['source'].lower()}|{rel['type']}|{rel['target'].lower()}"
            if rel_key not in seen_relationships:
                seen_relationships.add(rel_key)
                deduplicated_relationships.append(rel)
        
        total_entities = sum(len(v) for v in all_entities.values())
        logger.info(f"🎯 Final results: {total_entities} entities, {len(deduplicated_relationships)} relationships")
        
        return {
            "entities": all_entities,
            "relationships": deduplicated_relationships
        }
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get extraction configuration and stats."""
        return {
            "model": self.model_name,
            "entity_types": self.entity_types,
            "relationship_types": self.relationship_types,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "batch_delay": self.batch_delay
        }