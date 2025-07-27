import aiosqlite
import os
import shutil
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "rag_tasks.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Task results table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS task_result (
            task_id TEXT PRIMARY KEY,
            status TEXT,
            result TEXT,
            processing_time REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Study topics table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS study_topics (
            topic_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            use_knowledge_graph BOOLEAN NOT NULL DEFAULT 1,
            summary TEXT,
            summary_generated_at TIMESTAMP,
            mindmap TEXT,
            mindmap_generated_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Content items table for storing text/transcript content
        await db.execute("""
        CREATE TABLE IF NOT EXISTS content_items (
            content_id TEXT PRIMARY KEY,
            study_topic_id TEXT NOT NULL,
            content_type TEXT NOT NULL CHECK (content_type IN ('document', 'webpage', 'youtube', 'image', 'text')),
            title TEXT,
            content TEXT NOT NULL,
            source_url TEXT,
            file_path TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (study_topic_id) REFERENCES study_topics (topic_id) ON DELETE CASCADE
        )
        """)
        
        # Create index on study_topic_id for faster queries
        await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_content_items_study_topic_id 
        ON content_items (study_topic_id)
        """)
        
        await db.commit()

async def save_task_result(task_id: str, status: str, result: str, processing_time: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT OR REPLACE INTO task_result (task_id, status, result, processing_time)
        VALUES (?, ?, ?, ?)
        """, (task_id, status, result, processing_time))
        await db.commit()

async def fetch_task_result(task_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT status, result, processing_time FROM task_result WHERE task_id = ?", (task_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {"status": row[0], "result": row[1], "processing_time": row[2]}
            return None

# === Study Topics Functions ===

async def create_study_topic(topic_id: str, name: str, description: str, use_knowledge_graph: bool):
    """Create a new study topic"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO study_topics (topic_id, name, description, use_knowledge_graph)
        VALUES (?, ?, ?, ?)
        """, (topic_id, name, description, use_knowledge_graph))
        await db.commit()

async def get_study_topic(topic_id: str):
    """Get a study topic by ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
        SELECT topic_id, name, description, use_knowledge_graph, summary, summary_generated_at, mindmap, mindmap_generated_at, created_at, updated_at 
        FROM study_topics WHERE topic_id = ?
        """, (topic_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "topic_id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "use_knowledge_graph": bool(row[3]),
                    "summary": row[4],
                    "summary_generated_at": row[5],
                    "mindmap": row[6],
                    "mindmap_generated_at": row[7],
                    "created_at": row[8],
                    "updated_at": row[9]
                }
            return None

async def list_study_topics(limit: int = 100, offset: int = 0):
    """List all study topics with pagination"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
        SELECT topic_id, name, description, use_knowledge_graph, summary, summary_generated_at, mindmap, mindmap_generated_at, created_at, updated_at 
        FROM study_topics 
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
        """, (limit, offset)) as cursor:
            rows = await cursor.fetchall()
            topics = []
            for row in rows:
                topics.append({
                    "topic_id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "use_knowledge_graph": bool(row[3]),
                    "summary": row[4],
                    "summary_generated_at": row[5],
                    "mindmap": row[6],
                    "mindmap_generated_at": row[7],
                    "created_at": row[8],
                    "updated_at": row[9]
                })
            return topics

async def update_study_topic(topic_id: str, name: str = None, description: str = None, use_knowledge_graph: bool = None):
    """Update an existing study topic"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Build dynamic update query
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if use_knowledge_graph is not None:
            updates.append("use_knowledge_graph = ?")
            params.append(use_knowledge_graph)
        
        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(topic_id)
            
            query = f"UPDATE study_topics SET {', '.join(updates)} WHERE topic_id = ?"
            await db.execute(query, params)
            await db.commit()
            return True
        return False

async def delete_study_topic(topic_id: str):
    """Delete a study topic and its associated content items"""
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Get all content items before deletion to clean up files
        async with db.execute("""
        SELECT file_path FROM content_items 
        WHERE study_topic_id = ? AND file_path IS NOT NULL
        """, (topic_id,)) as cursor:
            file_paths = await cursor.fetchall()
        
        # Delete from database (content items will cascade due to foreign key)
        cursor = await db.execute("DELETE FROM study_topics WHERE topic_id = ?", (topic_id,))
        await db.commit()
        
        if cursor.rowcount > 0:
            # Clean up files after successful database deletion
            upload_dir = os.getenv("UPLOAD_DIR", "./uploaded_docs")
            topic_upload_dir = os.path.join(upload_dir, topic_id)
            
            # Remove topic-specific upload directory
            if os.path.exists(topic_upload_dir):
                try:
                    shutil.rmtree(topic_upload_dir)
                    logger.info(f"🗑️ Deleted upload directory: {topic_upload_dir}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to delete upload directory {topic_upload_dir}: {e}")
            
            # Remove topic-specific RAG directory
            rag_dir = os.getenv("RAG_DIR", "./rag_storage")
            topic_rag_dir = os.path.join(rag_dir, f"topic_{topic_id}")
            if os.path.exists(topic_rag_dir):
                try:
                    shutil.rmtree(topic_rag_dir)
                    logger.info(f"🗑️ Deleted RAG directory: {topic_rag_dir}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to delete RAG directory {topic_rag_dir}: {e}")
            
            return True
        
        return False

async def save_study_topic_summary(topic_id: str, summary: str):
    """Save or update a study topic summary"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE study_topics 
        SET summary = ?, summary_generated_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE topic_id = ?
        """, (summary, topic_id))
        await db.commit()

async def save_study_topic_mindmap(topic_id: str, mindmap: str):
    """Save or update a study topic mindmap"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        UPDATE study_topics 
        SET mindmap = ?, mindmap_generated_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE topic_id = ?
        """, (mindmap, topic_id))
        await db.commit()

# === Content Items Functions ===

async def create_content_item(content_id: str, study_topic_id: str, content_type: str, 
                            title: str, content: str, source_url: str = None, 
                            file_path: str = None, metadata: str = None):
    """Create a new content item associated with a study topic"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO content_items (content_id, study_topic_id, content_type, title, content, source_url, file_path, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (content_id, study_topic_id, content_type, title, content, source_url, file_path, metadata))
        await db.commit()

async def get_content_item(content_id: str):
    """Get a content item by ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
        SELECT content_id, study_topic_id, content_type, title, content, source_url, file_path, metadata, created_at 
        FROM content_items WHERE content_id = ?
        """, (content_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "content_id": row[0],
                    "study_topic_id": row[1],
                    "content_type": row[2],
                    "title": row[3],
                    "content": row[4],
                    "source_url": row[5],
                    "file_path": row[6],
                    "metadata": row[7],
                    "created_at": row[8]
                }
            return None

async def list_content_items_by_topic(study_topic_id: str, limit: int = 100, offset: int = 0):
    """List all content items for a specific study topic"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
        SELECT content_id, study_topic_id, content_type, title, source_url, file_path, metadata, created_at 
        FROM content_items 
        WHERE study_topic_id = ?
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
        """, (study_topic_id, limit, offset)) as cursor:
            rows = await cursor.fetchall()
            content_items = []
            for row in rows:
                content_items.append({
                    "content_id": row[0],
                    "study_topic_id": row[1],
                    "content_type": row[2],
                    "title": row[3],
                    "source_url": row[4],
                    "file_path": row[5],
                    "metadata": row[6],
                    "created_at": row[7]
                })
            return content_items

async def get_content_items_count_by_topic(study_topic_id: str):
    """Get the count of content items for a specific study topic"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
        SELECT COUNT(*) FROM content_items WHERE study_topic_id = ?
        """, (study_topic_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def delete_content_item(content_id: str):
    """Delete a content item, associated file, and from LightRAG knowledge graph"""
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Get content item details before deletion
        async with db.execute("""
        SELECT file_path, study_topic_id, use_knowledge_graph FROM content_items 
        JOIN study_topics ON content_items.study_topic_id = study_topics.topic_id
        WHERE content_id = ?
        """, (content_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return False
            file_path, study_topic_id, use_knowledge_graph = row
        
        # Delete from LightRAG knowledge graph (only if study topic uses knowledge graph)
        if use_knowledge_graph:
            try:
                # Import here to avoid circular imports
                from main import get_topic_rag
                topic_rag = await get_topic_rag(study_topic_id)
                if topic_rag:
                    # Check if document exists before deletion
                    try:
                        doc_status = await topic_rag.aget_docs_by_ids([content_id])
                        if content_id in doc_status:
                            # Delete the document (adelete_by_doc_id is already async, don't wrap in to_thread)
                            await topic_rag.adelete_by_doc_id(content_id)
                            
                            # Clear cache to ensure consistency
                            await topic_rag.aclear_cache()
                            
                            # Verify deletion success
                            post_delete_status = await topic_rag.aget_docs_by_ids([content_id])
                            if content_id not in post_delete_status:
                                logger.info(f"🗑️ Successfully deleted from LightRAG: {content_id} (study topic has knowledge graph enabled)")
                            else:
                                logger.warning(f"⚠️ Document still exists in LightRAG after deletion: {content_id}")
                        else:
                            logger.info(f"📝 Document not found in LightRAG: {content_id}")
                    except AttributeError:
                        # Fallback if aget_docs_by_ids is not available
                        await topic_rag.adelete_by_doc_id(content_id)
                        await topic_rag.aclear_cache()
                        logger.info(f"🗑️ Deleted from LightRAG knowledge graph: {content_id} (study topic has knowledge graph enabled)")
                else:
                    logger.warning(f"⚠️ Could not get RAG instance for study topic: {study_topic_id}")
            except Exception as e:
                logger.error(f"⚠️ Failed to delete from LightRAG knowledge graph: {e}")
                # Continue with file/database deletion even if LightRAG deletion fails
        else:
            logger.info(f"📝 Skipping LightRAG deletion: study topic does not use knowledge graph")
        
        # Delete from database
        cursor = await db.execute("DELETE FROM content_items WHERE content_id = ?", (content_id,))
        await db.commit()
        
        if cursor.rowcount > 0:
            # Clean up file after successful database deletion
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"🗑️ Deleted file: {file_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to delete file {file_path}: {e}")
            
            return True
        
        return False