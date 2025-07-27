"""
Synchronous endpoint utilities for Study4Me backend

This module contains business logic for synchronous API endpoints that were 
extracted from main.py to improve code organization and maintainability.

Functions included:
- Study topic content summarization
- Study topic mindmap generation
- Other complex synchronous endpoint logic
"""

import os
import time
import uuid
import asyncio
import logging
from typing import Optional, Dict, Any
from openai import OpenAI
from fastapi import HTTPException

# Import database and utility functions
from .utils_async import count_tokens
from .db_async import (
    get_study_topic, 
    list_content_items_by_topic, 
    get_content_item,
    save_study_topic_summary,
    save_study_topic_mindmap,
    save_study_topic_lecture
)

# Set up logging
logger = logging.getLogger(__name__)


def handle_openai_error(e: Exception) -> HTTPException:
    """Convert OpenAI errors to appropriate HTTP exceptions"""
    from openai import AuthenticationError, RateLimitError, APIError
    
    if isinstance(e, AuthenticationError):
        logger.error(f"OpenAI authentication error: {str(e)}")
        return HTTPException(
            status_code=401, 
            detail={
                "error": "OpenAI authentication failed",
                "message": "Invalid or missing API key. Please check your OPENAI_API_KEY environment variable.",
                "type": "authentication_error"
            }
        )
    elif isinstance(e, RateLimitError):
        logger.warning(f"OpenAI rate limit error: {str(e)}")
        return HTTPException(
            status_code=429,
            detail={
                "error": "OpenAI rate limit exceeded",
                "message": "Please try again later or upgrade your OpenAI plan.",
                "type": "rate_limit_error"
            }
        )
    elif isinstance(e, APIError):
        logger.error(f"OpenAI API error: {str(e)}")
        return HTTPException(
            status_code=502,
            detail={
                "error": "OpenAI API error",
                "message": f"OpenAI service error: {str(e)}",
                "type": "api_error"
            }
        )
    else:
        logger.error(f"Unexpected error: {str(e)}")
        return HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": str(e),
                "type": "unexpected_error"
            }
        )


async def summarize_study_topic_content_logic(
    topic_id: str,
    openai_client: OpenAI
) -> Dict[str, Any]:
    """
    Generate a comprehensive summary of all content for a specific study topic using OpenAI with SQLite caching
    
    Args:
        topic_id: UUID of the study topic
        openai_client: OpenAI client instance
        
    Returns:
        Dict containing summary data and metadata
        
    Raises:
        HTTPException: For various error conditions (topic not found, no content, API errors)
    """
    summary_id = str(uuid.uuid4())[:8]  # Short ID for tracking
    start_total = time.perf_counter()
    
    # Log summary request start
    logger.info(f"📝 [summary-{summary_id}] Starting content summarization for topic: {topic_id[:8]}")
    
    try:
        # Check if topic exists
        topic = await get_study_topic(topic_id)
        if not topic:
            logger.warning(f"❌ [summary-{summary_id}] Study topic not found: {topic_id}")
            raise HTTPException(status_code=404, detail=f"Study topic with ID '{topic_id}' not found")
        
        logger.info(f"✅ [summary-{summary_id}] Study topic validated: '{topic['name']}'")
        
        # Check if we have a cached summary
        if topic.get('summary') and topic.get('summary_generated_at'):
            logger.info(f"💾 [summary-{summary_id}] Found cached summary from {topic['summary_generated_at']}")
            
            # Return cached summary with timing info
            total_time = time.perf_counter() - start_total
            summary_length = len(topic['summary']) if topic['summary'] else 0
            
            logger.info(f"🎉 [summary-{summary_id}] Cached summary returned successfully:")
            logger.info(f"   ⏱️  Total time: {total_time:.2f}s (cached)")
            logger.info(f"   📝 Summary length: {summary_length} chars")
            
            return {
                "topic_id": topic_id,
                "topic_name": topic['name'],
                "topic_description": topic.get('description', ''),
                "summary": topic['summary'],
                "content_items_processed": "cached",
                "total_content_length": "cached",
                "total_content_tokens": "cached",
                "summary_length": summary_length,
                "processing_time_seconds": 0.0,  # No processing time for cached result
                "total_time_seconds": round(total_time, 2),
                "generated_at": topic['summary_generated_at'],
                "cached": True
            }
        
        logger.info(f"🔄 [summary-{summary_id}] No cached summary found, generating new one...")
        
        # Get all content items for this topic
        content_items_summary = await list_content_items_by_topic(topic_id)
        
        if not content_items_summary:
            logger.warning(f"❌ [summary-{summary_id}] No content found for topic: {topic['name']}")
            raise HTTPException(
                status_code=404, 
                detail=f"No content available for topic '{topic['name']}'. Please upload content first."
            )
        
        logger.info(f"📄 [summary-{summary_id}] Found {len(content_items_summary)} content items")
        
        # Collect all content with metadata
        content_sections = []
        total_chars = 0
        
        for item in content_items_summary:
            # Get the full content item with content field
            full_item = await get_content_item(item['content_id'])
            if full_item and full_item.get('content'):
                content_text = full_item['content']
                content_length = len(content_text)
                total_chars += content_length
                
                # Create a structured section for the AI
                section = f"""
--- {full_item['title']} ---
Content Type: {full_item['content_type']}
{f"Source: {full_item.get('source_url', 'N/A')}" if full_item.get('source_url') else f"File: {full_item.get('file_path', 'N/A').split('/')[-1] if full_item.get('file_path') else 'N/A'}"}
{content_text}
"""
                content_sections.append(section)
        
        if not content_sections:
            logger.warning(f"❌ [summary-{summary_id}] No valid content found for summarization")
            raise HTTPException(
                status_code=404,
                detail=f"No valid content available for summarization in topic '{topic['name']}'"
            )
        
        # Combine all content
        combined_content = "\n".join(content_sections)
        total_tokens = count_tokens(combined_content)
        
        logger.info(f"📊 [summary-{summary_id}] Content prepared: {total_chars} chars, {total_tokens} tokens")
        
        # Check if content is too large (leaving room for response and prompt)
        MAX_CONTEXT_TOKENS = 120000  # Conservative limit for GPT-4o-mini
        if total_tokens > MAX_CONTEXT_TOKENS:
            # Truncate content proportionally
            truncate_ratio = MAX_CONTEXT_TOKENS / total_tokens
            logger.warning(f"⚠️ [summary-{summary_id}] Content too large ({total_tokens} tokens), truncating to {truncate_ratio:.2%}")
            
            truncated_sections = []
            for section in content_sections:
                section_tokens = count_tokens(section)
                if section_tokens > 500:  # Only truncate larger sections
                    target_length = int(len(section) * truncate_ratio)
                    truncated_section = section[:target_length] + "\n[... content truncated ...]"
                    truncated_sections.append(truncated_section)
                else:
                    truncated_sections.append(section)
            
            combined_content = "\n".join(truncated_sections)
            total_tokens = count_tokens(combined_content)
            logger.info(f"📊 [summary-{summary_id}] Content after truncation: {len(combined_content)} chars, {total_tokens} tokens")
        
        # Create comprehensive summarization prompt
        summary_prompt = f"""You are an expert academic content summarizer. Please create a comprehensive summary of the following study materials for the topic "{topic['name']}".
INSTRUCTIONS:
1. Provide a structured, well-organized summary that captures the key concepts, themes, and important details
2. Organize the summary with clear headings and subheadings
3. Include the main arguments, findings, and conclusions from the materials
4. Highlight any important relationships, patterns, or connections between different sources
5. Make the summary suitable for study and review purposes
6. Use bullet points, numbered lists, and formatting to enhance readability
7. If there are conflicting viewpoints in the sources, note them clearly
8. Aim for a thorough but concise summary (approximately 1000-2000 words depending on content volume)
STUDY TOPIC: {topic['name']}
{f"TOPIC DESCRIPTION: {topic.get('description', 'No description provided')}" if topic.get('description') else ""}
MATERIALS TO SUMMARIZE:
{combined_content}
Please provide your comprehensive summary below:"""
        
        # Call OpenAI API for summarization
        t0 = time.perf_counter()
        logger.info(f"⚙️ [summary-{summary_id}] Starting OpenAI summarization...")
        
        try:
            response = await asyncio.to_thread(
                openai_client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert academic content summarizer who creates comprehensive, well-structured summaries for study purposes."
                    },
                    {
                        "role": "user", 
                        "content": summary_prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent summaries
                max_tokens=4000   # Allow for comprehensive summaries
            )
            
            summary_text = response.choices[0].message.content
            
        except Exception as openai_error:
            logger.error(f"❌ [summary-{summary_id}] OpenAI API error: {str(openai_error)}")
            raise handle_openai_error(openai_error)
        
        t1 = time.perf_counter()
        processing_time = t1 - t0
        total_time = time.perf_counter() - start_total
        
        # Save summary to database for caching
        try:
            await save_study_topic_summary(topic_id, summary_text)
            logger.info(f"💾 [summary-{summary_id}] Summary saved to database for caching")
        except Exception as save_error:
            logger.warning(f"⚠️ [summary-{summary_id}] Failed to save summary to cache: {str(save_error)}")
            # Continue anyway - the summary was generated successfully
        
        # Log successful completion
        summary_length = len(summary_text) if summary_text else 0
        logger.info(f"🎉 [summary-{summary_id}] Summarization completed successfully:")
        logger.info(f"   ⏱️  Total time: {total_time:.2f}s")
        logger.info(f"   ⚡ OpenAI processing time: {processing_time:.2f}s ({(processing_time/total_time)*100:.1f}%)")
        logger.info(f"   📄 Content items processed: {len(content_items_summary)}")
        logger.info(f"   📊 Input: {total_chars} chars, {total_tokens} tokens")
        logger.info(f"   📝 Summary length: {summary_length} chars")
        
        return {
            "topic_id": topic_id,
            "topic_name": topic['name'],
            "topic_description": topic.get('description', ''),
            "summary": summary_text,
            "content_items_processed": len(content_items_summary),
            "total_content_length": total_chars,
            "total_content_tokens": total_tokens,
            "summary_length": summary_length,
            "processing_time_seconds": round(processing_time, 2),
            "total_time_seconds": round(total_time, 2),
            "generated_at": time.time(),
            "cached": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        total_time = time.perf_counter() - start_total
        error_msg = str(e)
        logger.error(f"❌ [summary-{summary_id}] Unexpected error: {error_msg} (after {total_time:.2f}s)")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {error_msg}")


async def generate_study_topic_mindmap_logic(
    topic_id: str,
    openai_client: OpenAI
) -> Dict[str, Any]:
    """
    Generate a Mermaid mindmap code for all content in a specific study topic using OpenAI with SQLite caching
    
    Args:
        topic_id: UUID of the study topic
        openai_client: OpenAI client instance
        
    Returns:
        Dict containing mindmap data and metadata
        
    Raises:
        HTTPException: For various error conditions (topic not found, no content, API errors)
    """
    from openai import AuthenticationError, RateLimitError, APIError
    import re
    
    mindmap_id = str(uuid.uuid4())[:8]  # Short ID for tracking
    start_total = time.perf_counter()
    
    # Log mindmap request start
    logger.info(f"🧠 [mindmap-{mindmap_id}] Starting mindmap generation for topic: {topic_id[:8]}")
    
    try:
        # Check if topic exists
        topic = await get_study_topic(topic_id)
        if not topic:
            logger.warning(f"❌ [mindmap-{mindmap_id}] Study topic not found: {topic_id}")
            raise HTTPException(status_code=404, detail=f"Study topic with ID '{topic_id}' not found")
        
        logger.info(f"✅ [mindmap-{mindmap_id}] Study topic validated: '{topic['name']}'")
        
        # Check if we have a cached mindmap
        if topic.get('mindmap') and topic.get('mindmap_generated_at'):
            logger.info(f"💾 [mindmap-{mindmap_id}] Found cached mindmap from {topic['mindmap_generated_at']}")
            
            # Return cached mindmap with timing info
            total_time = time.perf_counter() - start_total
            mindmap_length = len(topic['mindmap']) if topic['mindmap'] else 0
            
            logger.info(f"🎉 [mindmap-{mindmap_id}] Cached mindmap returned successfully:")
            logger.info(f"   ⏱️  Total time: {total_time:.2f}s (cached)")
            logger.info(f"   🧠 Mindmap length: {mindmap_length} chars")
            
            return {
                "topic_id": topic_id,
                "topic_name": topic['name'],
                "topic_description": topic.get('description', ''),
                "mindmap": topic['mindmap'],
                "content_items_processed": "cached",
                "total_content_length": "cached",
                "total_content_tokens": "cached",
                "mindmap_length": mindmap_length,
                "processing_time_seconds": 0.0,  # No processing time for cached result
                "total_time_seconds": round(total_time, 2),
                "generated_at": topic['mindmap_generated_at'],
                "cached": True
            }
        
        logger.info(f"🔄 [mindmap-{mindmap_id}] No cached mindmap found, generating new one...")
        
        # Get all content items for this topic
        content_items_summary = await list_content_items_by_topic(topic_id)
        
        if not content_items_summary:
            logger.warning(f"❌ [mindmap-{mindmap_id}] No content found for topic: {topic['name']}")
            raise HTTPException(
                status_code=404, 
                detail=f"No content available for topic '{topic['name']}'. Please upload content first."
            )
        
        logger.info(f"📄 [mindmap-{mindmap_id}] Found {len(content_items_summary)} content items")
        
        # Collect all content with metadata
        content_sections = []
        total_chars = 0
        
        for item in content_items_summary:
            # Get the full content item with content field
            full_item = await get_content_item(item['content_id'])
            if full_item and full_item.get('content'):
                content_text = full_item['content']
                content_length = len(content_text)
                total_chars += content_length
                
                # Create a structured section for the AI
                section = f"""
--- {full_item['title']} ---
Content Type: {full_item['content_type']}
{f"Source: {full_item.get('source_url', 'N/A')}" if full_item.get('source_url') else f"File: {full_item.get('file_path', 'N/A').split('/')[-1] if full_item.get('file_path') else 'N/A'}"}
{content_text}
"""
                content_sections.append(section)
        
        if not content_sections:
            logger.warning(f"❌ [mindmap-{mindmap_id}] No valid content found for mindmap generation")
            raise HTTPException(
                status_code=404,
                detail=f"No valid content available for mindmap generation in topic '{topic['name']}'"
            )
        
        # Combine all content
        combined_content = "\n".join(content_sections)
        total_tokens = count_tokens(combined_content)
        
        logger.info(f"📊 [mindmap-{mindmap_id}] Content prepared: {total_chars} chars, {total_tokens} tokens")
        
        # Check if content is too large (leaving room for response and prompt)
        MAX_CONTEXT_TOKENS = 100000  # Conservative limit for GPT-4o-mini with mindmap generation
        if total_tokens > MAX_CONTEXT_TOKENS:
            # Truncate content proportionally
            truncate_ratio = MAX_CONTEXT_TOKENS / total_tokens
            logger.warning(f"⚠️ [mindmap-{mindmap_id}] Content too large ({total_tokens} tokens), truncating to {truncate_ratio:.2%}")
            
            truncated_sections = []
            for section in content_sections:
                section_tokens = count_tokens(section)
                if section_tokens > 500:  # Only truncate larger sections
                    target_length = int(len(section) * truncate_ratio)
                    truncated_section = section[:target_length] + "\n[... content truncated ...]"
                    truncated_sections.append(truncated_section)
                else:
                    truncated_sections.append(section)
            
            combined_content = "\n".join(truncated_sections)
            total_tokens = count_tokens(combined_content)
            logger.info(f"📊 [mindmap-{mindmap_id}] Content after truncation: {len(combined_content)} chars, {total_tokens} tokens")
        
        # Create comprehensive mindmap generation prompt
        mindmap_prompt = f"""You are an expert knowledge visualization specialist. Generate a comprehensive Mermaid mindmap source code for the study materials about "{topic['name']}".
CRITICAL FORMATTING REQUIREMENTS:
1. Start with "mindmap" on the first line
2. ALL text labels MUST use double quotes (") - never single quotes or no quotes
3. Use proper 2-space indentation for each level
4. Return ONLY pure Mermaid mindmap source code - NO markdown blocks, NO explanations, NO additional text
MERMAID MINDMAP SYNTAX RULES:
- Root node: root("Topic Name")
- Child nodes: Branch("Label Text")  
- Use proper indentation (2 spaces per level)
- ALL labels must be wrapped in double quotes
- Use parentheses () for rounded rectangles (most common)
- Use square brackets [] for rectangles when needed
- Use curly braces {{}} for circles when appropriate
CONTENT ORGANIZATION:
1. Create a hierarchical structure with main concepts as primary branches
2. Include subtopics, key theories, processes, and relationships
3. Add important facts, figures, dates, and details as leaf nodes
4. Group related concepts logically
5. Keep node labels concise but descriptive (max 60 characters)
6. Ensure comprehensive coverage without clutter
EXAMPLE FORMAT:
mindmap
  root("Study Topic")
    branch1("Main Concept 1")
      detail1("Key Point A")
      detail2("Key Point B")
    branch2("Main Concept 2")
      subbranch1("Subtopic 1")
        leaf1("Detail 1")
        leaf2("Detail 2")
STUDY TOPIC: {topic['name']}
{f"TOPIC DESCRIPTION: {topic.get('description', 'No description provided')}" if topic.get('description') else ""}
MATERIALS TO ANALYZE:
{combined_content}
Generate the Mermaid mindmap source code:"""
        
        # Call OpenAI API for mindmap generation
        t0 = time.perf_counter()
        logger.info(f"⚙️ [mindmap-{mindmap_id}] Starting OpenAI mindmap generation...")
        
        try:
            response = await asyncio.to_thread(
                openai_client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Mermaid mindmap generator. You MUST follow these rules strictly:\n1. Return ONLY pure Mermaid mindmap source code\n2. Start with 'mindmap' on first line\n3. ALL text labels MUST use double quotes (\")\n4. Use 2-space indentation\n5. NO markdown code blocks, NO explanations, NO additional text\n6. Generate valid Mermaid syntax only"
                    },
                    {
                        "role": "user", 
                        "content": mindmap_prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent mindmaps
                max_tokens=3000   # Allow for comprehensive mindmaps
            )
            
            mindmap_code = response.choices[0].message.content.strip()
            
            # Clean up the response to ensure proper Mermaid format
            logger.info(f"🔧 [mindmap-{mindmap_id}] Cleaning and validating generated mindmap...")
            
            # Remove markdown code blocks if present
            if '```mermaid' in mindmap_code:
                logger.warning(f"⚠️ [mindmap-{mindmap_id}] Found markdown wrapper, extracting code")
                start = mindmap_code.find('```mermaid') + 10
                end = mindmap_code.find('```', start)
                if end != -1:
                    mindmap_code = mindmap_code[start:end].strip()
            elif '```' in mindmap_code:
                logger.warning(f"⚠️ [mindmap-{mindmap_id}] Found generic code block, extracting code")
                start = mindmap_code.find('```') + 3
                end = mindmap_code.find('```', start)
                if end != -1:
                    mindmap_code = mindmap_code[start:end].strip()
            
            # Ensure it starts with 'mindmap'
            if not mindmap_code.startswith('mindmap'):
                logger.warning(f"⚠️ [mindmap-{mindmap_id}] Content doesn't start with 'mindmap', fixing")
                mindmap_code = f"mindmap\n  root(\"{topic['name']}\")\n" + mindmap_code
            
            # Fix quote consistency - convert single quotes to double quotes for labels
            # Pattern to match node labels with single quotes
            single_quote_pattern = r"(\w+)\('([^']+)'\)"
            mindmap_code = re.sub(single_quote_pattern, r'\1("\2")', mindmap_code)
            
            # Pattern to match labels without quotes at all (more complex)
            no_quote_pattern = r"(\w+)\(([^\"'][^)]*[^\"'])\)"
            def add_quotes(match):
                node_id = match.group(1)
                label = match.group(2).strip()
                # Don't add quotes if it already has them or if it's empty
                if label.startswith('"') and label.endswith('"'):
                    return match.group(0)
                return f'{node_id}("{label}")'
            
            mindmap_code = re.sub(no_quote_pattern, add_quotes, mindmap_code)
            
            # Validate final structure
            lines = mindmap_code.split('\n')
            if not lines[0].strip() == 'mindmap':
                logger.warning(f"⚠️ [mindmap-{mindmap_id}] First line is not 'mindmap': {lines[0][:50]}")
            
            # Check for proper quote usage in a sample of lines
            quote_issues = []
            for i, line in enumerate(lines[:10]):  # Check first 10 lines
                if '(' in line and ')' in line and '"' not in line and "'" not in line:
                    quote_issues.append(i)
            
            if quote_issues:
                logger.warning(f"⚠️ [mindmap-{mindmap_id}] Potential quote issues in lines: {quote_issues}")
            
            logger.info(f"✅ [mindmap-{mindmap_id}] Mindmap validation completed")
            
        except Exception as openai_error:
            logger.error(f"❌ [mindmap-{mindmap_id}] OpenAI API error: {str(openai_error)}")
            raise handle_openai_error(openai_error)
        
        t1 = time.perf_counter()
        processing_time = t1 - t0
        total_time = time.perf_counter() - start_total
        
        # Save mindmap to database for caching
        try:
            await save_study_topic_mindmap(topic_id, mindmap_code)
            logger.info(f"💾 [mindmap-{mindmap_id}] Mindmap saved to database for caching")
        except Exception as save_error:
            logger.warning(f"⚠️ [mindmap-{mindmap_id}] Failed to save mindmap to cache: {str(save_error)}")
            # Continue anyway - the mindmap was generated successfully
        
        # Log successful completion
        mindmap_length = len(mindmap_code) if mindmap_code else 0
        logger.info(f"🎉 [mindmap-{mindmap_id}] Mindmap generation completed successfully:")
        logger.info(f"   ⏱️  Total time: {total_time:.2f}s")
        logger.info(f"   ⚡ OpenAI processing time: {processing_time:.2f}s ({(processing_time/total_time)*100:.1f}%)")
        logger.info(f"   📄 Content items processed: {len(content_items_summary)}")
        logger.info(f"   📊 Input: {total_chars} chars, {total_tokens} tokens")
        logger.info(f"   🧠 Mindmap length: {mindmap_length} chars")
        
        return {
            "topic_id": topic_id,
            "topic_name": topic['name'],
            "topic_description": topic.get('description', ''),
            "mindmap": mindmap_code,
            "content_items_processed": len(content_items_summary),
            "total_content_length": total_chars,
            "total_content_tokens": total_tokens,
            "mindmap_length": mindmap_length,
            "processing_time_seconds": round(processing_time, 2),
            "total_time_seconds": round(total_time, 2),
            "generated_at": time.time(),
            "cached": False
        }
        
    except (AuthenticationError, RateLimitError, APIError) as e:
        logger.error(f"❌ [mindmap-{mindmap_id}] OpenAI API error after {time.perf_counter() - start_total:.2f}s")
        raise handle_openai_error(e)
    except HTTPException:
        raise
    except Exception as e:
        total_time = time.perf_counter() - start_total
        logger.error(f"💥 [mindmap-{mindmap_id}] Mindmap generation failed after {total_time:.2f}s: {str(e)}")
        logger.error(f"🔍 [mindmap-{mindmap_id}] Error details: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate mindmap for topic '{topic.get('name', topic_id)}': {str(e)}"
        )


async def generate_study_topic_lecture_logic(
    topic_id: str,
    openai_client: OpenAI,
    language: str = "english",
    focus_topic: str = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive lecture about all content in a specific study topic using OpenAI with SQLite caching
    
    Args:
        topic_id: UUID of the study topic
        openai_client: OpenAI client instance
        language: Output language (english, portuguese, spanish, etc.)
        focus_topic: Optional specific topic to focus on within the content
        
    Returns:
        Dict containing lecture data and metadata
        
    Raises:
        HTTPException: For various error conditions (topic not found, no content, API errors)
    """
    from openai import AuthenticationError, RateLimitError, APIError
    
    lecture_id = str(uuid.uuid4())[:8]  # Short ID for tracking
    start_total = time.perf_counter()
    
    # Create cache key for this specific lecture configuration
    customization = focus_topic if focus_topic else "general"
    
    # Log lecture request start
    logger.info(f"🎓 [lecture-{lecture_id}] Starting lecture generation for topic: {topic_id[:8]}")
    logger.info(f"🌐 [lecture-{lecture_id}] Language: {language}, Focus: {customization}")
    
    try:
        # Check if topic exists
        topic = await get_study_topic(topic_id)
        if not topic:
            logger.warning(f"❌ [lecture-{lecture_id}] Study topic not found: {topic_id}")
            raise HTTPException(status_code=404, detail=f"Study topic with ID '{topic_id}' not found")
        
        logger.info(f"✅ [lecture-{lecture_id}] Study topic validated: '{topic['name']}'")
        
        # Check if we have a cached lecture with matching language and customization
        if (topic.get('lecture') and topic.get('lecture_generated_at') and 
            topic.get('lecture_language') == language and 
            topic.get('lecture_customization') == customization):
            logger.info(f"💾 [lecture-{lecture_id}] Found cached lecture from {topic['lecture_generated_at']}")
            
            # Return cached lecture with timing info
            total_time = time.perf_counter() - start_total
            lecture_length = len(topic['lecture']) if topic['lecture'] else 0
            lecture_speech_length = len(topic.get('lecture_speech', '')) if topic.get('lecture_speech') else 0
            
            logger.info(f"🎉 [lecture-{lecture_id}] Cached lecture returned successfully:")
            logger.info(f"   ⏱️  Total time: {total_time:.2f}s (cached)")
            logger.info(f"   🎓 Lecture length: {lecture_length} chars")
            logger.info(f"   🎙️ Speech version length: {lecture_speech_length} chars")
            
            return {
                "topic_id": topic_id,
                "topic_name": topic['name'],
                "topic_description": topic.get('description', ''),
                "lecture": topic['lecture'],
                "lecture_speech": topic.get('lecture_speech', ''),
                "language": topic['lecture_language'],
                "focus_topic": topic.get('lecture_customization'),
                "content_items_processed": "cached",
                "total_content_length": "cached",
                "total_content_tokens": "cached",
                "lecture_length": lecture_length,
                "lecture_speech_length": lecture_speech_length,
                "processing_time_seconds": 0.0,  # No processing time for cached result
                "total_time_seconds": round(total_time, 2),
                "generated_at": topic['lecture_generated_at'],
                "cached": True
            }
        
        logger.info(f"🔄 [lecture-{lecture_id}] No cached lecture found or parameters changed, generating new one...")
        
        # Get all content items for this topic
        content_items_summary = await list_content_items_by_topic(topic_id)
        
        if not content_items_summary:
            logger.warning(f"❌ [lecture-{lecture_id}] No content found for topic: {topic['name']}")
            raise HTTPException(
                status_code=404, 
                detail=f"No content available for topic '{topic['name']}'. Please upload content first."
            )
        
        logger.info(f"📄 [lecture-{lecture_id}] Found {len(content_items_summary)} content items")
        
        # Collect all content with metadata
        content_sections = []
        total_chars = 0
        
        for item in content_items_summary:
            # Get the full content item with content field
            full_item = await get_content_item(item['content_id'])
            if full_item and full_item.get('content'):
                content_text = full_item['content']
                content_length = len(content_text)
                total_chars += content_length
                
                # Create a structured section for the AI
                section = f"""
--- {full_item['title']} ---
Content Type: {full_item['content_type']}
{f"Source: {full_item.get('source_url', 'N/A')}" if full_item.get('source_url') else f"File: {full_item.get('file_path', 'N/A').split('/')[-1] if full_item.get('file_path') else 'N/A'}"}
{content_text}
"""
                content_sections.append(section)
        
        if not content_sections:
            logger.warning(f"❌ [lecture-{lecture_id}] No valid content found for lecture generation")
            raise HTTPException(
                status_code=404,
                detail=f"No valid content available for lecture generation in topic '{topic['name']}'"
            )
        
        # Combine all content
        combined_content = "\n".join(content_sections)
        total_tokens = count_tokens(combined_content)
        
        logger.info(f"📊 [lecture-{lecture_id}] Content prepared: {total_chars} chars, {total_tokens} tokens")
        
        # Check if content is too large (leaving room for response and prompt)
        MAX_CONTEXT_TOKENS = 100000  # Conservative limit for GPT-4o-mini with lecture generation
        if total_tokens > MAX_CONTEXT_TOKENS:
            # Truncate content proportionally
            truncate_ratio = MAX_CONTEXT_TOKENS / total_tokens
            logger.warning(f"⚠️ [lecture-{lecture_id}] Content too large ({total_tokens} tokens), truncating to {truncate_ratio:.2%}")
            
            truncated_sections = []
            for section in content_sections:
                section_tokens = count_tokens(section)
                if section_tokens > 500:  # Only truncate larger sections
                    target_length = int(len(section) * truncate_ratio)
                    truncated_section = section[:target_length] + "\n[... content truncated ...]"
                    truncated_sections.append(truncated_section)
                else:
                    truncated_sections.append(section)
            
            combined_content = "\n".join(truncated_sections)
            total_tokens = count_tokens(combined_content)
            logger.info(f"📊 [lecture-{lecture_id}] Content after truncation: {len(combined_content)} chars, {total_tokens} tokens")
        
        # Create language-specific instruction
        language_instructions = {
            "english": "Write the lecture in English with clear, academic language suitable for university-level students.",
            "portuguese": "Escreva a palestra em português brasileiro com linguagem clara e acadêmica adequada para estudantes universitários.",
            "spanish": "Escriba la conferencia en español con lenguaje claro y académico adecuado para estudiantes universitarios.",
            "french": "Rédigez la conférence en français avec un langage clair et académique adapté aux étudiants universitaires.",
            "german": "Schreiben Sie die Vorlesung auf Deutsch mit klarer, akademischer Sprache, die für Universitätsstudenten geeignet ist.",
            "italian": "Scrivi la conferenza in italiano con linguaggio chiaro e accademico adatto agli studenti universitari."
        }
        
        language_instruction = language_instructions.get(language.lower(), 
            f"Write the lecture in {language} with clear, academic language suitable for university-level students.")
        
        # Create focus instruction if specified
        focus_instruction = ""
        if focus_topic:
            focus_instruction = f"\nSPECIAL FOCUS: Pay particular attention to '{focus_topic}' and provide deeper analysis and explanation of this specific aspect within the broader context of the materials."
        
        # Create comprehensive lecture generation prompt
        lecture_prompt = f"""You are an expert university professor preparing a comprehensive lecture based on the provided study materials about "{topic['name']}".

LECTURE REQUIREMENTS:
1. Create a well-structured, engaging lecture that would be suitable for a 45-60 minute university class
2. Include an introduction that outlines what will be covered
3. Organize content with clear sections and smooth transitions between topics
4. Provide detailed explanations of key concepts, theories, and processes
5. Include relevant examples, case studies, or applications where appropriate
6. Add engaging elements like rhetorical questions, thought-provoking statements, or real-world connections
7. Include a conclusion that summarizes key takeaways and their significance
8. Use appropriate academic tone while remaining engaging and accessible
9. {language_instruction}{focus_instruction}

STRUCTURE GUIDELINES:
- Introduction (5-10% of content)
- Main body with 3-5 major sections (80-85% of content)
- Conclusion with key takeaways (5-10% of content)
- Use clear headings and subheadings
- Include speaker notes in [brackets] where helpful for pacing or emphasis

STUDY TOPIC: {topic['name']}
{f"TOPIC DESCRIPTION: {topic.get('description', 'No description provided')}" if topic.get('description') else ""}

MATERIALS TO BASE THE LECTURE ON:
{combined_content}

Generate a comprehensive university-level lecture:"""

        # Create speech-optimized lecture generation prompt
        speech_prompt = f"""You are an expert university professor preparing a lecture script specifically optimized for text-to-speech audio generation based on the provided study materials about "{topic['name']}".

SPEECH-OPTIMIZED LECTURE REQUIREMENTS:
1. Create content that flows naturally when spoken aloud by AI text-to-speech
2. Use short, clear sentences that are easy to pronounce and understand
3. Include natural speech patterns with appropriate pauses (indicated by periods and commas)
4. Avoid complex formatting, special characters, or visual elements
5. Use conversational academic tone suitable for audio consumption
6. Include verbal transitions and connectors between sections
7. Replace any visual references with audio-friendly descriptions
8. Add natural speech cues like "Let's begin", "Moving on to", "In conclusion"
9. {language_instruction}{focus_instruction}

SPEECH FORMATTING GUIDELINES:
- No headings or markdown formatting - use verbal section introductions instead
- Replace bullet points with "First," "Second," "Additionally," etc.
- Use full sentences rather than fragments
- Include natural pauses with punctuation
- Spell out numbers and abbreviations where appropriate for clarity
- Use "pause" or "brief pause" where longer silence is needed for emphasis

STUDY TOPIC: {topic['name']}
{f"TOPIC DESCRIPTION: {topic.get('description', 'No description provided')}" if topic.get('description') else ""}

MATERIALS TO BASE THE LECTURE ON:
{combined_content}

Generate a speech-optimized lecture script for text-to-speech conversion:"""
        
        # Call OpenAI API for both lecture versions
        t0 = time.perf_counter()
        logger.info(f"⚙️ [lecture-{lecture_id}] Starting OpenAI lecture generation (both versions)...")
        
        try:
            # Generate formatted lecture version
            logger.info(f"📝 [lecture-{lecture_id}] Generating formatted lecture...")
            response = await asyncio.to_thread(
                openai_client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert university professor who creates engaging, comprehensive lectures. You must write in {language} and create content suitable for a 45-60 minute university lecture with clear structure, engaging delivery, and academic rigor."
                    },
                    {
                        "role": "user", 
                        "content": lecture_prompt
                    }
                ],
                temperature=0.4,  # Slightly higher temperature for more engaging content
                max_tokens=4000   # Allow for comprehensive lectures
            )
            
            lecture_text = response.choices[0].message.content
            
            # Generate speech-optimized lecture version
            logger.info(f"🎙️ [lecture-{lecture_id}] Generating speech-optimized lecture...")
            speech_response = await asyncio.to_thread(
                openai_client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert university professor who creates lecture scripts optimized for text-to-speech audio generation. You must write in {language} and create content that flows naturally when spoken by AI text-to-speech systems like ElevenLabs."
                    },
                    {
                        "role": "user", 
                        "content": speech_prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent speech patterns
                max_tokens=4000   # Allow for comprehensive speech scripts
            )
            
            lecture_speech_text = speech_response.choices[0].message.content
            
        except Exception as openai_error:
            logger.error(f"❌ [lecture-{lecture_id}] OpenAI API error: {str(openai_error)}")
            raise handle_openai_error(openai_error)
        
        t1 = time.perf_counter()
        processing_time = t1 - t0
        total_time = time.perf_counter() - start_total
        
        # Save both lecture versions to database for caching
        try:
            await save_study_topic_lecture(topic_id, lecture_text, lecture_speech_text, language, customization)
            logger.info(f"💾 [lecture-{lecture_id}] Both lecture versions saved to database for caching")
        except Exception as save_error:
            logger.warning(f"⚠️ [lecture-{lecture_id}] Failed to save lectures to cache: {str(save_error)}")
            # Continue anyway - the lectures were generated successfully
        
        # Log successful completion
        lecture_length = len(lecture_text) if lecture_text else 0
        lecture_speech_length = len(lecture_speech_text) if lecture_speech_text else 0
        logger.info(f"🎉 [lecture-{lecture_id}] Lecture generation completed successfully:")
        logger.info(f"   ⏱️  Total time: {total_time:.2f}s")
        logger.info(f"   ⚡ OpenAI processing time: {processing_time:.2f}s ({(processing_time/total_time)*100:.1f}%)")
        logger.info(f"   📄 Content items processed: {len(content_items_summary)}")
        logger.info(f"   📊 Input: {total_chars} chars, {total_tokens} tokens")
        logger.info(f"   🎓 Lecture length: {lecture_length} chars")
        logger.info(f"   🎙️ Speech version length: {lecture_speech_length} chars")
        logger.info(f"   🌐 Language: {language}")
        logger.info(f"   🎯 Focus: {customization}")
        
        return {
            "topic_id": topic_id,
            "topic_name": topic['name'],
            "topic_description": topic.get('description', ''),
            "lecture": lecture_text,
            "lecture_speech": lecture_speech_text,
            "language": language,
            "focus_topic": focus_topic,
            "content_items_processed": len(content_items_summary),
            "total_content_length": total_chars,
            "total_content_tokens": total_tokens,
            "lecture_length": lecture_length,
            "lecture_speech_length": lecture_speech_length,
            "processing_time_seconds": round(processing_time, 2),
            "total_time_seconds": round(total_time, 2),
            "generated_at": time.time(),
            "cached": False
        }
        
    except (AuthenticationError, RateLimitError, APIError) as e:
        logger.error(f"❌ [lecture-{lecture_id}] OpenAI API error after {time.perf_counter() - start_total:.2f}s")
        raise handle_openai_error(e)
    except HTTPException:
        raise
    except Exception as e:
        total_time = time.perf_counter() - start_total
        logger.error(f"💥 [lecture-{lecture_id}] Lecture generation failed after {total_time:.2f}s: {str(e)}")
        logger.error(f"🔍 [lecture-{lecture_id}] Error details: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate lecture for topic '{topic.get('name', topic_id)}': {str(e)}"
        )