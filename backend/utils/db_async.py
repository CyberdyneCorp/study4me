import aiosqlite
import os

DB_PATH = os.getenv("DB_PATH", "rag_tasks.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS task_result (
            task_id TEXT PRIMARY KEY,
            status TEXT,
            result TEXT,
            processing_time REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
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