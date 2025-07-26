#!/usr/bin/env python3
"""
Test script for the new mindmap endpoint
"""

import requests
import json
import time

def test_mindmap_endpoint():
    """Test the mindmap generation endpoint"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Mindmap Endpoint")
    print("=" * 50)
    
    try:
        # Check if server is running
        print("1. Checking server status...")
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   ✅ Server is running (status: {response.status_code})")
        
        # Get available study topics
        print("\n2. Fetching study topics...")
        topics_response = requests.get(f"{base_url}/study-topics", timeout=10)
        
        if topics_response.status_code != 200:
            print(f"   ❌ Failed to get topics: {topics_response.status_code}")
            return
            
        topics_data = topics_response.json()
        topics = topics_data.get('topics', [])
        
        if not topics:
            print("   ⚠️ No study topics found. Please create a topic with content first.")
            return
            
        # Find a topic with content
        topic_with_content = None
        for topic in topics:
            topic_id = topic['topic_id']
            print(f"   📚 Checking topic: {topic['name']}")
            
            # Check if topic has content
            content_response = requests.get(f"{base_url}/study-topics/{topic_id}/content", timeout=10)
            if content_response.status_code == 200:
                content_data = content_response.json()
                if content_data.get('content_items_count', 0) > 0:
                    topic_with_content = topic
                    print(f"   ✅ Found topic with {content_data['content_items_count']} content items")
                    break
                else:
                    print(f"   ⚠️ Topic has no content")
        
        if not topic_with_content:
            print("   ❌ No topics with content found. Please upload content to a topic first.")
            return
            
        # Test mindmap generation
        print(f"\n3. Testing mindmap generation for: {topic_with_content['name']}")
        topic_id = topic_with_content['topic_id']
        
        start_time = time.time()
        mindmap_response = requests.get(f"{base_url}/study-topics/{topic_id}/mindmap", timeout=120)
        end_time = time.time()
        
        print(f"   Request completed in {end_time - start_time:.2f}s")
        print(f"   Status code: {mindmap_response.status_code}")
        
        if mindmap_response.status_code == 200:
            mindmap_data = mindmap_response.json()
            
            print("\n4. 🎉 Mindmap Generation Results:")
            print(f"   📊 Topic: {mindmap_data.get('topic_name')}")
            print(f"   📄 Content items processed: {mindmap_data.get('content_items_processed')}")
            print(f"   📝 Total content length: {mindmap_data.get('total_content_length')} chars")
            print(f"   🧠 Mindmap length: {mindmap_data.get('mindmap_length')} chars")
            print(f"   ⏱️ Processing time: {mindmap_data.get('processing_time_seconds')}s")
            print(f"   💾 Cached: {mindmap_data.get('cached', False)}")
            
            mindmap_code = mindmap_data.get('mindmap', '')
            if mindmap_code:
                print(f"\n5. 🗺️ Generated Mindmap (first 300 chars):")
                print("   " + "─" * 50)
                print("   " + mindmap_code[:300].replace('\n', '\n   '))
                if len(mindmap_code) > 300:
                    print("   [... truncated ...]")
                print("   " + "─" * 50)
                
                # Validate it's proper Mermaid syntax
                validation_results = validate_mindmap_syntax(mindmap_code)
                for result in validation_results:
                    print(f"   {result}")
                    
            print("\n✅ Mindmap endpoint test completed successfully!")
            
        else:
            print(f"   ❌ Mindmap generation failed:")
            print(f"   Status: {mindmap_response.status_code}")
            print(f"   Error: {mindmap_response.text[:500]}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server. Make sure it's running on localhost:8000")
    except requests.exceptions.Timeout:
        print("❌ Request timed out. The server might be overloaded or not responding.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def validate_mindmap_syntax(mindmap_code):
    """Validate the generated mindmap follows proper Mermaid syntax"""
    results = []
    
    if not mindmap_code.strip():
        return ["❌ Empty mindmap code"]
    
    lines = mindmap_code.split('\n')
    
    # Check if starts with 'mindmap'
    if lines[0].strip() == 'mindmap':
        results.append("✅ Starts with 'mindmap'")
    else:
        results.append(f"❌ First line should be 'mindmap', got: '{lines[0][:30]}'")
    
    # Check for double quotes usage
    quote_issues = 0
    single_quote_usage = 0
    no_quote_usage = 0
    
    for i, line in enumerate(lines[1:], 1):  # Skip first 'mindmap' line
        if '(' in line and ')' in line:
            # Check for single quotes
            if "'" in line and '"' not in line:
                single_quote_usage += 1
            # Check for no quotes (basic pattern)
            elif '"' not in line and "'" not in line and '(' in line:
                # Simple check for unquoted labels
                import re
                if re.search(r'\([^")\']*\)', line):
                    no_quote_usage += 1
    
    if single_quote_usage == 0 and no_quote_usage == 0:
        results.append("✅ All labels use double quotes")
    else:
        if single_quote_usage > 0:
            results.append(f"⚠️ Found {single_quote_usage} lines with single quotes")
        if no_quote_usage > 0:
            results.append(f"⚠️ Found {no_quote_usage} lines with unquoted labels")
    
    # Check for proper indentation (basic check)
    indentation_ok = True
    for i, line in enumerate(lines[1:], 1):
        if line.strip() and not line.startswith('  '):
            indentation_ok = False
            break
    
    if indentation_ok:
        results.append("✅ Proper indentation detected")
    else:
        results.append("⚠️ Indentation issues detected")
    
    # Count total nodes
    node_count = sum(1 for line in lines if '(' in line and ')' in line)
    results.append(f"📊 Total nodes: {node_count}")
    
    return results

if __name__ == "__main__":
    test_mindmap_endpoint()