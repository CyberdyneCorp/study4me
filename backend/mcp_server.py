#!/usr/bin/env python3
"""
Study4Me MCP Server using FastMCP v2

This MCP server provides functions to interact with the Study4Me backend:
- get_content_from_study: Get all content for a specific study topic
- query_study: Query a study topic using LightRAG or ChatGPT
- list_all_studies: List all study topics with summaries
"""

import os
import asyncio
import json
import argparse
import sys
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP
from dotenv import load_dotenv

# Import from the existing backend modules
from utils.db_async import get_study_topic, list_study_topics, list_content_items_by_topic, get_content_item
from utils.utils_async import count_tokens, query_with_context
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
from openai import OpenAI

# Load environment variables
load_dotenv("config.env")
load_dotenv()  # Also load from .env if it exists

# Initialize MCP server
mcp = FastMCP("Study4Me Knowledge Server")

# Configuration
RAG_DIR = os.getenv("RAG_DIR", "./rag_storage")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Global variables for RAG instances (cached)
_topic_rag_cache = {}
_openai_client = None

def get_openai_client():
    """Get or create OpenAI client"""
    global _openai_client
    if _openai_client is None:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client

async def get_topic_rag(study_topic_id: str) -> Optional[LightRAG]:
    """
    Get or create a LightRAG instance for a specific study topic.
    Only creates instances for topics with knowledge graph enabled.
    """
    if not study_topic_id:
        return None
    
    # Check if we already have a cached instance
    if study_topic_id in _topic_rag_cache:
        return _topic_rag_cache[study_topic_id]
    
    # Check if topic exists and has knowledge graph enabled
    topic = await get_study_topic(study_topic_id)
    if not topic:
        print(f"Study topic not found: {study_topic_id}")
        return None
    
    if not topic.get('use_knowledge_graph', True):
        print(f"Study topic '{topic['name']}' has knowledge graph disabled, skipping LightRAG creation")
        return None
    
    # Create topic-specific directory
    topic_rag_dir = os.path.join(RAG_DIR, f"topic_{study_topic_id}")
    os.makedirs(topic_rag_dir, exist_ok=True)
    
    print(f"Creating LightRAG instance for topic: {topic['name']} ({study_topic_id})")
    
    try:
        topic_rag = LightRAG(
            working_dir=topic_rag_dir,
            embedding_func=openai_embed,
            llm_model_func=gpt_4o_mini_complete,
        )
        await topic_rag.initialize_storages()
        
        # Cache the instance
        _topic_rag_cache[study_topic_id] = topic_rag
        
        print(f"LightRAG instance created successfully for topic: {topic['name']}")
        return topic_rag
        
    except Exception as e:
        print(f"Failed to create LightRAG for topic {study_topic_id}: {str(e)}")
        return None

@mcp.tool
async def get_content_from_study(study_topic_id: str) -> Dict[str, Any]:
    """
    Get all content for a specific study topic.
    
    Args:
        study_topic_id: The UUID of the study topic
        
    Returns:
        Dictionary containing topic information and all content items
    """
    try:
        # Check if topic exists
        topic = await get_study_topic(study_topic_id)
        if not topic:
            return {
                "error": f"Study topic with ID '{study_topic_id}' not found",
                "success": False
            }
        
        # Get all content items for this topic
        content_items_summary = await list_content_items_by_topic(study_topic_id)
        
        # Get full content for each item and calculate token counts
        detailed_content_items = []
        total_token_count = 0
        total_content_length = 0
        
        for item in content_items_summary:
            # Get the full content item with content field
            full_item = await get_content_item(item['content_id'])
            if full_item:
                content_text = full_item.get('content', '')
                item_token_count = count_tokens(content_text) if content_text else 0
                
                detailed_content_items.append({
                    "content_id": full_item['content_id'],
                    "content_type": full_item['content_type'],
                    "title": full_item['title'],
                    "content": content_text,
                    "source_url": full_item.get('source_url'),
                    "file_path": full_item.get('file_path'),
                    "metadata": full_item.get('metadata'),
                    "created_at": full_item['created_at'],
                    "content_length": len(content_text),
                    "number_tokens": item_token_count
                })
                
                total_token_count += item_token_count
                total_content_length += len(content_text)
        
        return {
            "success": True,
            "topic_id": topic_id,
            "topic_name": topic['name'],
            "topic_description": topic.get('description', ''),
            "use_knowledge_graph": topic.get('use_knowledge_graph', True),
            "content_items_count": len(detailed_content_items),
            "total_content_length": total_content_length,
            "total_tokens": total_token_count,
            "content_items": detailed_content_items
        }
        
    except Exception as e:
        return {
            "error": f"Failed to get content for study topic: {str(e)}",
            "success": False
        }

@mcp.tool
async def query_study(study_topic_id: str, query: str, mode: str = "hybrid") -> Dict[str, Any]:
    """
    Query a specific study topic using LightRAG or ChatGPT with context.
    
    Args:
        study_topic_id: The UUID of the study topic to query
        query: The question to ask
        mode: RAG mode for LightRAG queries (hybrid, naive, local, global, etc.)
        
    Returns:
        Dictionary containing the query result and metadata
    """
    try:
        # Check if topic exists
        topic = await get_study_topic(study_topic_id)
        if not topic:
            return {
                "error": f"Study topic with ID '{study_topic_id}' not found",
                "success": False
            }
        
        # Branch based on knowledge graph setting
        if topic.get('use_knowledge_graph', True):
            # Use LightRAG for knowledge graph enabled topics
            print(f"Using LightRAG for topic: {topic['name']}")
            rag = await get_topic_rag(study_topic_id)
            if not rag:
                return {
                    "error": f"Failed to initialize LightRAG for topic '{topic['name']}'",
                    "success": False
                }
            
            param = QueryParam(mode=mode)
            result = await asyncio.to_thread(rag.query, query, param=param)
            processing_method = "LightRAG"
            
        else:
            # Use ChatGPT with context for non-knowledge graph topics
            print(f"Using ChatGPT with context for topic: {topic['name']}")
            
            # Get all content for the topic
            content_items = await list_content_items_by_topic(study_topic_id)
            
            # Combine all content
            combined_content = ""
            for item in content_items:
                full_item = await get_content_item(item['content_id'])
                if full_item and full_item.get('content'):
                    combined_content += f"\n\n--- {full_item['title']} ---\n{full_item['content']}"
            
            if not combined_content.strip():
                return {
                    "error": f"No content available for topic '{topic['name']}'. Please upload content first.",
                    "success": False
                }
            
            # Query using ChatGPT with context
            openai_client = get_openai_client()
            result = await query_with_context(query, combined_content, topic['name'], openai_client)
            processing_method = "ChatGPT+Context"

        return {
            "success": True,
            "result": result,
            "processing_method": processing_method,
            "study_topic_id": study_topic_id,
            "study_topic_name": topic['name'],
            "use_knowledge_graph": topic.get('use_knowledge_graph', True),
            "mode_used": mode if topic.get('use_knowledge_graph', True) else "context",
            "query": query
        }
        
    except Exception as e:
        return {
            "error": f"Failed to query study topic: {str(e)}",
            "success": False
        }

@mcp.tool
async def list_all_studies(include_content_count: bool = True, include_summary: bool = True) -> Dict[str, Any]:
    """
    List all study topics with their metadata and optionally content counts and summaries.
    
    Args:
        include_content_count: Whether to include content item counts for each topic
        include_summary: Whether to include cached summaries for each topic
        
    Returns:
        Dictionary containing all study topics with metadata
    """
    try:
        # Get all study topics
        topics = await list_study_topics(limit=1000, offset=0)  # Get all topics
        
        enriched_topics = []
        
        for topic in topics:
            enriched_topic = {
                "topic_id": topic['topic_id'],
                "name": topic['name'],
                "description": topic.get('description', ''),
                "use_knowledge_graph": topic.get('use_knowledge_graph', True),
                "created_at": topic['created_at'],
                "updated_at": topic['updated_at']
            }
            
            # Add summary if requested and available
            if include_summary and topic.get('summary'):
                enriched_topic['summary'] = topic['summary']
                enriched_topic['summary_generated_at'] = topic.get('summary_generated_at')
            
            # Add content count if requested
            if include_content_count:
                try:
                    content_items = await list_content_items_by_topic(topic['topic_id'])
                    enriched_topic['content_items_count'] = len(content_items)
                    
                    # Calculate total content length and tokens
                    total_content_length = 0
                    total_tokens = 0
                    
                    for item in content_items:
                        full_item = await get_content_item(item['content_id'])
                        if full_item and full_item.get('content'):
                            content_text = full_item['content']
                            total_content_length += len(content_text)
                            total_tokens += count_tokens(content_text)
                    
                    enriched_topic['total_content_length'] = total_content_length
                    enriched_topic['total_tokens'] = total_tokens
                    
                except Exception as e:
                    enriched_topic['content_items_count'] = 0
                    enriched_topic['content_count_error'] = str(e)
            
            enriched_topics.append(enriched_topic)
        
        return {
            "success": True,
            "total_studies": len(enriched_topics),
            "studies": enriched_topics,
            "metadata": {
                "include_content_count": include_content_count,
                "include_summary": include_summary
            }
        }
        
    except Exception as e:
        return {
            "error": f"Failed to list study topics: {str(e)}",
            "success": False
        }

def main():
    """Main function with argument parsing for transport selection"""
    parser = argparse.ArgumentParser(description="Study4Me MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport type: stdio for Claude Desktop, http for debugging (default: stdio)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port for HTTP transport (default: 8001)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for HTTP transport (default: 127.0.0.1)"
    )
    
    args = parser.parse_args()
    
    print("🚀 Starting Study4Me MCP Server...")
    print("📚 Available tools:")
    print("   - get_content_from_study: Get all content for a specific study topic")
    print("   - query_study: Query a study topic using LightRAG or ChatGPT")
    print("   - list_all_studies: List all study topics with summaries")
    print()
    
    if args.transport == "http":
        print(f"🌐 HTTP Transport Mode")
        print(f"   Server URL: http://{args.host}:{args.port}/mcp/")
        print(f"   Use this URL in your MCP client configuration")
        print()
        mcp.run(transport="http", port=args.port, host=args.host)
    else:
        print(f"📡 STDIO Transport Mode")
        print(f"   Ready for Claude Desktop connection")
        print()
        mcp.run()

if __name__ == "__main__":
    main()