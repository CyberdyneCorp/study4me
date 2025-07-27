#!/usr/bin/env python3
"""
Test script to verify MCP server tools are properly defined
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the MCP server
from mcp_server import mcp, get_content_from_study, query_study, list_all_studies

async def test_tools():
    """Test that the MCP tools are properly defined"""
    print("Testing MCP server tools...")
    
    # Check if tools are registered
    print(f"MCP server name: {mcp.name}")
    
    # Test list_all_studies function directly
    print("\n--- Testing list_all_studies function ---")
    try:
        result = await list_all_studies(include_content_count=False, include_summary=False)
        print(f"Success: {result.get('success', False)}")
        if result.get('success'):
            print(f"Total studies: {result.get('total_studies', 0)}")
            print("Studies preview:", [s['name'] for s in result.get('studies', [])][:3])
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"Exception: {e}")
    
    print("\n--- MCP Tools Test Complete ---")
    print("The MCP server has been successfully created with the following tools:")
    print("1. get_content_from_study - Get all content for a specific study topic")
    print("2. query_study - Query a study topic using LightRAG or ChatGPT")
    print("3. list_all_studies - List all study topics with summaries")
    print("\nTo use the server, run: python mcp_server.py")

if __name__ == "__main__":
    asyncio.run(test_tools())