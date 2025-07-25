import aiosqlite
import os

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
        SELECT topic_id, name, description, use_knowledge_graph, created_at, updated_at 
        FROM study_topics WHERE topic_id = ?
        """, (topic_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "topic_id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "use_knowledge_graph": bool(row[3]),
                    "created_at": row[4],
                    "updated_at": row[5]
                }
            return None

async def list_study_topics(limit: int = 100, offset: int = 0):
    """List all study topics with pagination"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
        SELECT topic_id, name, description, use_knowledge_graph, created_at, updated_at 
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
                    "created_at": row[4],
                    "updated_at": row[5]
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
        # Delete associated content items first (will cascade automatically due to foreign key)
        cursor = await db.execute("DELETE FROM study_topics WHERE topic_id = ?", (topic_id,))
        await db.commit()
        return cursor.rowcount > 0

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
    """Delete a content item"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM content_items WHERE content_id = ?", (content_id,))
        await db.commit()
        return cursor.rowcount > 0