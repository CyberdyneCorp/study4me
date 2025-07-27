#!/usr/bin/env python3

import asyncio
import os
import sys
from lightrag import LightRAG
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv("config.env")  # Also load config.env file

async def debug_lightrag_storage(topic_id):
    """Debug LightRAG storage for a specific topic"""
    rag_dir = os.getenv("RAG_DIR", "./rag_storage")
    topic_rag_dir = os.path.join(rag_dir, f"topic_{topic_id}")
    
    print(f"=== LightRAG Debug Report for Topic: {topic_id} ===")
    print(f"RAG Directory: {topic_rag_dir}")
    print(f"Directory exists: {os.path.exists(topic_rag_dir)}")
    print()
    
    if not os.path.exists(topic_rag_dir):
        print("❌ Topic RAG directory does not exist!")
        return
    
    # List all files in the RAG directory
    print("📁 Files in RAG directory:")
    for file in os.listdir(topic_rag_dir):
        file_path = os.path.join(topic_rag_dir, file)
        size = os.path.getsize(file_path)
        print(f"  - {file} ({size} bytes)")
    print()
    
    # Initialize LightRAG instance
    try:
        # Use OpenAI for LLM and embedding
        from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
        import openai
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("❌ OPENAI_API_KEY not found in environment variables")
            return None, None
            
        rag = LightRAG(
            working_dir=topic_rag_dir,
            embedding_func=openai_embed,
            llm_model_func=gpt_4o_mini_complete,
        )
        print("✅ LightRAG instance initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize LightRAG: {e}")
        return None, None
    
    # Check document status storage
    doc_status_file = os.path.join(topic_rag_dir, "kv_store_doc_status.json")
    if os.path.exists(doc_status_file):
        with open(doc_status_file, 'r') as f:
            doc_status = json.load(f)
        print(f"📄 Document Status Storage ({len(doc_status)} documents):")
        for doc_id, status in doc_status.items():
            print(f"  - {doc_id[:8]}... : {status.get('status', 'unknown')} ({status.get('chunks_count', 0)} chunks)")
            if 'file_path' in status:
                print(f"    File: {status['file_path']}")
        print()
        
        # Try to get docs by IDs
        try:
            doc_ids = list(doc_status.keys())
            docs_info = await rag.aget_docs_by_ids(doc_ids)
            print(f"🔍 Retrieved document info for {len(docs_info)} docs:")
            for doc_id, info in docs_info.items():
                print(f"  - {doc_id[:8]}... : {info}")
            print()
        except Exception as e:
            print(f"⚠️ Failed to get docs by IDs: {e}")
            print()
    
    # Check full docs storage
    full_docs_file = os.path.join(topic_rag_dir, "kv_store_full_docs.json")
    if os.path.exists(full_docs_file):
        with open(full_docs_file, 'r') as f:
            full_docs = json.load(f)
        print(f"📚 Full Documents Storage ({len(full_docs)} documents):")
        for doc_id, doc_data in full_docs.items():
            content_length = len(doc_data.get('content', '')) if isinstance(doc_data, dict) else len(str(doc_data))
            print(f"  - {doc_id[:8]}... : {content_length} chars")
        print()
    
    # Check chunks storage
    chunks_file = os.path.join(topic_rag_dir, "vdb_chunks.json")
    if os.path.exists(chunks_file):
        try:
            with open(chunks_file, 'r') as f:
                chunks_data = json.load(f)
            
            chunks = chunks_data.get('data', [])
            print(f"🧩 Vector Database Chunks ({len(chunks)} chunks):")
            doc_chunk_count = {}
            for chunk in chunks:
                doc_id = chunk.get('full_doc_id', 'unknown')
                doc_chunk_count[doc_id] = doc_chunk_count.get(doc_id, 0) + 1
            
            for doc_id, count in doc_chunk_count.items():
                print(f"  - {doc_id[:8]}... : {count} chunks")
            print()
        except Exception as e:
            print(f"⚠️ Failed to read chunks file: {e}")
            print()
    
    # Check entities storage
    entities_file = os.path.join(topic_rag_dir, "vdb_entities.json")
    if os.path.exists(entities_file):
        try:
            with open(entities_file, 'r') as f:
                entities_data = json.load(f)
            
            entities = entities_data.get('data', [])
            print(f"🏷️ Entities ({len(entities)} entities):")
            for entity in entities[:10]:  # Show first 10
                entity_name = entity.get('entity_name', 'unknown')
                description = entity.get('entity_description', '')[:50] + "..." if len(entity.get('entity_description', '')) > 50 else entity.get('entity_description', '')
                print(f"  - {entity_name}: {description}")
            if len(entities) > 10:
                print(f"  ... and {len(entities) - 10} more entities")
            print()
        except Exception as e:
            print(f"⚠️ Failed to read entities file: {e}")
            print()
    
    # Check relationships storage  
    relations_file = os.path.join(topic_rag_dir, "vdb_relationships.json")
    if os.path.exists(relations_file):
        try:
            with open(relations_file, 'r') as f:
                relations_data = json.load(f)
            
            relations = relations_data.get('data', [])
            print(f"🔗 Relationships ({len(relations)} relationships):")
            for rel in relations[:10]:  # Show first 10
                source = rel.get('src_id', 'unknown')
                target = rel.get('tgt_id', 'unknown')
                description = rel.get('description', '')[:50] + "..." if len(rel.get('description', '')) > 50 else rel.get('description', '')
                print(f"  - {source} → {target}: {description}")
            if len(relations) > 10:
                print(f"  ... and {len(relations) - 10} more relationships")
            print()
        except Exception as e:
            print(f"⚠️ Failed to read relationships file: {e}")
            print()

    return rag, doc_status if 'doc_status' in locals() else None

async def test_deletion(topic_id, doc_id_to_delete):
    """Test the deletion of a specific document"""
    rag_dir = os.getenv("RAG_DIR", "./rag_storage")
    topic_rag_dir = os.path.join(rag_dir, f"topic_{topic_id}")
    
    print(f"\n=== Testing Deletion of Document: {doc_id_to_delete} ===")
    
    try:
        from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
        rag = LightRAG(
            working_dir=topic_rag_dir,
            embedding_func=openai_embed,
            llm_model_func=gpt_4o_mini_complete,
        )
        
        # Check if document exists before deletion
        print("📋 Before deletion:")
        try:
            docs_before = await rag.aget_docs_by_ids(doc_id_to_delete)
            print(f"  Document found: {doc_id_to_delete in docs_before}")
            if doc_id_to_delete in docs_before:
                print(f"  Status: {docs_before[doc_id_to_delete]}")
        except Exception as e:
            print(f"  Error checking document: {e}")
        
        # Perform deletion
        print(f"\n🗑️ Deleting document: {doc_id_to_delete}")
        try:
            await rag.adelete_by_doc_id(doc_id_to_delete)
            print("  ✅ Deletion completed successfully")
        except Exception as e:
            print(f"  ❌ Deletion failed: {e}")
            return False
        
        # Check if document exists after deletion
        print("\n📋 After deletion:")
        try:
            docs_after = await rag.aget_docs_by_ids(doc_id_to_delete)
            print(f"  Document found: {doc_id_to_delete in docs_after}")
            if doc_id_to_delete in docs_after:
                print(f"  Status: {docs_after[doc_id_to_delete]}")
                print("  ⚠️ Warning: Document still exists after deletion!")
                return False
            else:
                print("  ✅ Document successfully removed")
                return True
        except Exception as e:
            print(f"  Error checking document after deletion: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test deletion: {e}")
        return False

async def export_data(topic_id):
    """Export LightRAG data for inspection"""
    rag_dir = os.getenv("RAG_DIR", "./rag_storage")
    topic_rag_dir = os.path.join(rag_dir, f"topic_{topic_id}")
    
    print(f"\n=== Exporting Data for Topic: {topic_id} ===")
    
    try:
        from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
        rag = LightRAG(
            working_dir=topic_rag_dir,
            embedding_func=openai_embed,
            llm_model_func=gpt_4o_mini_complete,
        )
        
        # Export to different formats
        export_path = f"/tmp/lightrag_export_{topic_id}"
        os.makedirs(export_path, exist_ok=True)
        
        for format_type in ['csv', 'txt', 'md']:
            try:
                export_file = os.path.join(export_path, f"export.{format_type}")
                await rag.aexport_data(export_file, file_format=format_type, include_vector_data=True)
                print(f"  ✅ Exported to {format_type}: {export_file}")
            except Exception as e:
                print(f"  ❌ Failed to export to {format_type}: {e}")
        
        print(f"\n📁 Export files saved in: {export_path}")
        
    except Exception as e:
        print(f"❌ Failed to export data: {e}")

async def main():
    # Topic ID from the storage we found
    topic_id = "ad7053f5-2bd1-4cc6-9f2a-b402d72b57b7"
    
    # First, debug the current state
    result = await debug_lightrag_storage(topic_id)
    
    if result is None:
        print("❌ Failed to initialize debugging. Exiting.")
        return
        
    rag, doc_status = result
    
    if doc_status:
        # Export data for inspection
        await export_data(topic_id)
        
        # Test deletion of one document
        doc_ids = list(doc_status.keys())
        if doc_ids:
            # Test deleting the first document
            first_doc_id = doc_ids[0]
            success = await test_deletion(topic_id, first_doc_id)
            
            if success:
                print(f"\n🔄 Re-checking storage after deletion...")
                await debug_lightrag_storage(topic_id)

if __name__ == "__main__":
    asyncio.run(main())