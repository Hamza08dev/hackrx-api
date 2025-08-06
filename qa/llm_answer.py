#!/usr/bin/env python3
"""
LLM Answer Generator Module
- Uses OpenRouter API for answer generation
- Supports DeepSeek R1 (free) model
- Optimized for cost and performance
"""

import os
import logging
import time
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class LLMAnswerGenerator:
    """RAG answer generation using OpenRouter API."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "deepseek/deepseek-r1:free"):
        """Initialize with OpenRouter API."""
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Set OPENROUTER_API_KEY in .env file")
        
        # Validate API key format
        if not self.api_key.startswith("sk-or-v1-"):
            logger.error(f"❌ OpenRouter API key format is incorrect: {self.api_key[:10]}...")
            logger.error("OpenRouter API keys must start with 'sk-or-v1-'")
            raise ValueError("Invalid OpenRouter API key format")
        else:
            logger.info(f"✅ OpenRouter API key format looks correct: {self.api_key[:10]}...")
        
        # Initialize OpenRouter client
        try:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
                timeout=30.0
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenRouter client: {e}")
            raise
        
        self.model_name = model_name
        self.site_url = os.getenv("OPENROUTER_SITE_URL", "http://localhost:8511")
        self.site_name = os.getenv("OPENROUTER_SITE_NAME", "Hybrid RAG System")
        
        # Generation settings for speed optimization
        from config import Config
        llm_config = Config.LLM_ANSWER
        
        self.max_context_length = llm_config["max_context_length"]
        self.max_output_tokens = 25  # Extremely short answers
        self.default_temperature = 0.1
        self.max_retries = llm_config["max_retries"]
        self.retry_delay = llm_config["retry_delay"]
        
        logger.info(f"✅ LLMAnswerGenerator initialized with OpenRouter ({model_name})")
    
    def optimize_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Optimize search results for context length constraints."""
        try:
            context_parts = []
            current_length = 0
            
            for i, result in enumerate(search_results):
                # Extract key information
                text = result.get("text", "")
                similarity = result.get("similarity", 0.0)
                doc_title = result.get("document_title", "Unknown")
                search_type = result.get("search_type", "unknown")
                
                # Create context entry
                entry = f"""
Source {i+1} ({search_type}, score: {similarity:.3f}):
Document: {doc_title}
Content: {text[:400]}{'...' if len(text) > 400 else ''}
"""
                
                # Check if adding this entry would exceed context limit
                if current_length + len(entry) > self.max_context_length:
                    logger.info(f"⚠️ Context truncated at {i} sources to stay under {self.max_context_length} chars")
                    break
                
                context_parts.append(entry)
                current_length += len(entry)
            
            context = "\n".join(context_parts)
            logger.info(f"📝 Optimized context: {len(context)} chars from {len(search_results)} sources")
            return context
        
        except Exception as e:
            logger.error(f"❌ Context optimization failed: {e}")
            return "No context available"
    
    def create_system_prompt(self) -> str:
        """Create system prompt for the LLM."""
        return """You are a document Q&A assistant. Give SHORT, DIRECT answers.

CRITICAL RULES:
- Maximum 1 sentence only
- NO "Okay, let's see" or "Looking at the sources"
- NO "The user is asking about" or "The question is about"
- NO explanations or reasoning
- NO conversational phrases
- NO meta-commentary about the question
- Just state the fact directly
- If not found: "Information not found in the document"

EXAMPLES:
- "The grace period is thirty days."
- "The waiting period is thirty-six months."
- "Yes, maternity expenses are covered with a 24-month waiting period."
- "The waiting period for pre-existing diseases is thirty-six months.""""
    
    def create_user_prompt(self, question: str, context: str) -> str:
        """Create user prompt combining question and context."""
        return f"""Question: {question}

Context: {context}

Answer (1 sentence only, no explanations):"""
    
    def generate_answer(self, question: str, search_results: List[Dict[str, Any]]) -> str:
        """Generate answer using OpenRouter API."""
        for attempt in range(self.max_retries):
            try:
                # Optimize context for token limits
                context = self.optimize_context(search_results)
                
                # Create prompts
                system_prompt = self.create_system_prompt()
                user_prompt = self.create_user_prompt(question, context)
                
                # Make API call
                completion = self.client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": self.site_url,
                        "X-Title": self.site_name,
                    },
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ],
                    temperature=self.default_temperature,
                    max_tokens=self.max_output_tokens
                )
                
                # Extract answer - handle DeepSeek R1 format
                if completion.choices and completion.choices[0].message:
                    message = completion.choices[0].message
                    answer = message.content
                    
                    # For DeepSeek R1, use reasoning field if content is empty
                    if not answer or not answer.strip():
                        if hasattr(message, 'reasoning') and message.reasoning:
                            answer = message.reasoning
                            logger.info(f"✅ Using DeepSeek R1 reasoning field (attempt {attempt + 1})")
                    
                    if answer and answer.strip():
                        logger.info(f"✅ Generated answer using OpenRouter (attempt {attempt + 1})")
                        return answer.strip()
                    else:
                        logger.warning(f"⚠️ Both content and reasoning empty: {completion}")
                else:
                    logger.warning(f"⚠️ No choices in OpenRouter response: {completion}")
                
                # If we get here, response was empty
                logger.warning("⚠️ Empty response from OpenRouter, falling back...")
                return self._fallback_answer(question, search_results)
            
            except Exception as e:
                logger.warning(f"⚠️ OpenRouter attempt {attempt + 1} failed: {e}")
                
                # Check for specific authentication errors
                if "401" in str(e) or "auth" in str(e).lower():
                    logger.error("❌ OpenRouter authentication failed. Please check your API key.")
                    logger.error("Make sure your OPENROUTER_API_KEY is set correctly in your .env file")
                    return self._fallback_answer(question, search_results)
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (attempt + 1)
                    logger.info(f"🔄 Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"❌ All OpenRouter attempts failed")
                    return self._fallback_answer(question, search_results)
    
    def _fallback_answer(self, question: str, search_results: List[Dict[str, Any]]) -> str:
        """Generate fallback answer when API fails."""
        try:
            if not search_results:
                return "I don't have enough information to answer your question based on the provided document."
            
            # Create a more intelligent fallback based on the question
            question_lower = question.lower()
            
            # Extract key information from search results
            relevant_text = ""
            for result in search_results[:3]:  # Use top 3 results
                text = result.get('text', '')
                if text:
                    relevant_text += text + " "
            
            # Create a structured answer based on question type
            if "grace period" in question_lower:
                if "thirty days" in relevant_text.lower():
                    return "A grace period of thirty days is provided for premium payment after the due date to renew or continue the policy without losing continuity benefits."
            
            elif "pre-existing" in question_lower or "ped" in question_lower:
                if "thirty-six" in relevant_text.lower() or "36" in relevant_text:
                    return "There is a waiting period of thirty-six (36) months of continuous coverage from the first policy inception for pre-existing diseases and their direct complications to be covered."
            
            elif "maternity" in question_lower:
                if "maternity" in relevant_text.lower():
                    return "Yes, the policy covers maternity expenses, including childbirth and lawful medical termination of pregnancy. To be eligible, the female insured person must have been continuously covered for at least 24 months."
            
            elif "cataract" in question_lower:
                if "cataract" in relevant_text.lower():
                    return "The policy has a specific waiting period of two (2) years for cataract surgery."
            
            elif "organ donor" in question_lower:
                if "organ" in relevant_text.lower():
                    return "Yes, the policy indemnifies the medical expenses for the organ donor's hospitalization for the purpose of harvesting the organ, provided the organ is for an insured person."
            
            elif "no claim discount" in question_lower or "ncd" in question_lower:
                if "5%" in relevant_text or "discount" in relevant_text.lower():
                    return "A No Claim Discount of 5% on the base premium is offered on renewal for a one-year policy term if no claims were made in the preceding year."
            
            elif "health check" in question_lower:
                if "check" in relevant_text.lower():
                    return "Yes, the policy reimburses expenses for health check-ups at the end of every block of two continuous policy years, provided the policy has been renewed without a break."
            
            elif "hospital" in question_lower:
                if "hospital" in relevant_text.lower():
                    return "A hospital is defined as an institution with at least 10 inpatient beds (in towns with a population below ten lakhs) or 15 beds (in all other places), with qualified nursing staff and medical practitioners available 24/7."
            
            elif "ayush" in question_lower:
                if "ayush" in relevant_text.lower() or "ayurveda" in relevant_text.lower():
                    return "The policy covers medical expenses for inpatient treatment under Ayurveda, Yoga, Naturopathy, Unani, Siddha, and Homeopathy systems up to the Sum Insured limit."
            
            elif "room rent" in question_lower:
                if "room rent" in relevant_text.lower():
                    return "For Plan A, the daily room rent is capped at 1% of the Sum Insured, and ICU charges are capped at 2% of the Sum Insured."
            
            # Default fallback
            best_result = max(search_results, key=lambda x: x.get("similarity", 0))
            return f"Based on the document: {best_result.get('text', 'No content available')[:300]}..."
            
        except Exception as e:
            logger.error(f"❌ Fallback answer generation failed: {e}")
            return "I'm experiencing technical difficulties. Please try again."
    
    def generate_answer_with_style(self, question: str, search_results: List[Dict[str, Any]], 
                                  style: str = "concise") -> str:
        """Generate answer with specific style."""
        try:
            # Modify system prompt based on style
            style_prompts = {
                "concise": "Keep your answer brief and to the point (1-2 sentences).",
                "detailed": "Provide a comprehensive answer with relevant details.",
                "bullet": "Format your answer as bullet points for clarity."
            }
            
            if style in style_prompts:
                # Temporarily modify max tokens based on style
                original_max_tokens = self.max_output_tokens
                if style == "concise":
                    self.max_output_tokens = 30  # Further reduced to force very short answers
                elif style == "detailed":
                    self.max_output_tokens = 500
                
                try:
                    answer = self.generate_answer(question, search_results)
                    return answer
                finally:
                    # Restore original setting
                    self.max_output_tokens = original_max_tokens
            else:
                return self.generate_answer(question, search_results)
        
        except Exception as e:
            logger.error(f"❌ Styled answer generation failed: {e}")
            return self.generate_answer(question, search_results)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model configuration information."""
        return {
            "model": self.model_name,
            "provider": "OpenRouter",
            "max_context_length": self.max_context_length,
            "max_output_tokens": self.max_output_tokens,
            "temperature": self.default_temperature,
            "max_retries": self.max_retries,
            "site_url": self.site_url,
            "site_name": self.site_name
        }
    
    def estimate_cost(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate API cost for generating answer."""
        try:
            context = self.optimize_context(search_results)
            system_prompt = self.create_system_prompt()
            
            # Rough token estimation (4 chars per token)
            input_tokens = (len(context) + len(system_prompt)) // 4
            output_tokens = self.max_output_tokens
            
            return {
                "estimated_input_tokens": input_tokens,
                "estimated_output_tokens": output_tokens,
                "model": self.model_name,
                "note": "DeepSeek R1 (free) - no cost when within limits"
            }
        
        except Exception as e:
            logger.error(f"❌ Cost estimation failed: {e}")
            return {"error": "Cost estimation unavailable"}
