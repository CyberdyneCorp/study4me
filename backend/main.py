import os
import io
import shutil
import asyncio
import logging
import time
import json
import uuid
import signal
import sys
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
from threading import Lock

from pydantic import BaseModel, Field

from dotenv import load_dotenv

import networkx as nx
import matplotlib.pyplot as plt
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Body, Request, Depends, BackgroundTasks, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
from lightrag.kg.shared_storage import initialize_pipeline_status

from openai import OpenAI, AuthenticationError, RateLimitError, APIError
from utils.utils_async import process_uploaded_documents, process_webpage_background, process_image_background, process_query_background, process_youtube_background, count_tokens, query_with_context
from utils.db_async import (init_db, fetch_task_result, create_study_topic, get_study_topic, 
                           list_study_topics, update_study_topic, delete_study_topic, save_study_topic_summary,
                           save_study_topic_mindmap, create_content_item, get_content_item, list_content_items_by_topic, 
                           get_content_items_count_by_topic, delete_content_item)
from youtube_service import get_youtube_transcript, batch_youtube_transcripts, BatchRequest

# Handle multiple tasks statuses
TASK_STATUS = {}  # Ex: {task_id: "processing" | "done" | "failed"}
TASK_LOCK = Lock()

# WebSocket connection management
WEBSOCKET_CONNECTIONS = set()  # Active WebSocket connections
WEBSOCKET_LOCK = Lock()

# Global shutdown flag
SHUTDOWN_EVENT = asyncio.Event()
BACKGROUND_TASKS = set()  # Track running background tasks

# === Configs and Paths ===
# Load environment variables from config.env or .env
load_dotenv("config.env")
load_dotenv()  # Also load from .env if it exists

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploaded_docs")
RAG_DIR = os.getenv("RAG_DIR", "./rag_storage")
GRAPHML_FILENAME = os.getenv("GRAPHML_FILENAME", "graph_chunk_entity_relation.graphml")
GRAPHML_PATH = os.path.join(RAG_DIR, GRAPHML_FILENAME)

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RAG_DIR, exist_ok=True)

# === Logging ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger("ingest_kgraph")

# === Pydantic Models ===
class StudyTopicCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Name of the study topic")
    description: Optional[str] = Field(None, max_length=1000, description="Description of the study topic")
    use_knowledge_graph: bool = Field(True, description="Whether to use knowledge graph for this topic")

class StudyTopicResponse(BaseModel):
    topic_id: str
    name: str
    description: Optional[str]
    use_knowledge_graph: bool
    created_at: str
    updated_at: str

class StudyTopicUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Name of the study topic")
    description: Optional[str] = Field(None, max_length=1000, description="Description of the study topic")
    use_knowledge_graph: Optional[bool] = Field(None, description="Whether to use knowledge graph for this topic")

# === OpenAI Key Check (Moved to lifespan for graceful failure) ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def validate_openai_api_key(api_key: str) -> bool:
    """Validate OpenAI API key by making a test call"""
    try:
        test_client = OpenAI(api_key=api_key)
        # Make a simple API call to validate the key
        await asyncio.to_thread(
            test_client.models.list
        )
        return True
    except Exception as e:
        logger.error(f"❌ OpenAI API key validation failed: {str(e)}")
        if "401" in str(e) or "invalid_api_key" in str(e):
            logger.error("The provided API key is invalid or expired.")
            logger.error("Please check your API key at: https://platform.openai.com/account/api-keys")
        elif "429" in str(e):
            logger.warning("⚠️ Rate limit reached, but API key appears valid.")
            return True  # Key is valid, just rate limited
        else:
            logger.error("Network or other error during API key validation.")
        return False

def handle_openai_error(e: Exception) -> HTTPException:
    """Convert OpenAI errors to appropriate HTTP exceptions"""
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

# === Signal Handlers ===
def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
    SHUTDOWN_EVENT.set()

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Docker/Kubernetes shutdown

# === FastAPI Initialization with Lifespan ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Study4Me backend server...")
    
    logger.info("📊 Initializing database...")
    await init_db()
    logger.info("✅ Database initialized.")
    
    logger.info("🔑 Validating OpenAI API key...")
    
    # Check if API key is set
    if not OPENAI_API_KEY:
        logger.error("❌ OPENAI_API_KEY environment variable is not set!")
        logger.error("Please set your OpenAI API key:")
        logger.error("  1. Create a .env file in the backend directory")
        logger.error("  2. Add: OPENAI_API_KEY=your_actual_api_key_here")
        logger.error("  3. Get your API key from: https://platform.openai.com/account/api-keys")
        logger.error("🛑 Server startup aborted. Set your API key and restart.")
        raise RuntimeError("OPENAI_API_KEY environment variable must be set. Check logs for setup instructions.")
    
    # Check if API key is a placeholder
    if OPENAI_API_KEY in ["your_openai_api_key_here", "your_actual_api_key_here", "test-key-for-import-check"]:
        logger.error("❌ OPENAI_API_KEY is set to a placeholder value!")
        logger.error("Please set your actual OpenAI API key:")
        logger.error("  1. Get your API key from: https://platform.openai.com/account/api-keys")
        logger.error("  2. Update your .env file with: OPENAI_API_KEY=your_actual_api_key_here")
        logger.error("🛑 Server startup aborted. Set a real API key and restart.")
        raise RuntimeError("OPENAI_API_KEY must be set to your actual OpenAI API key, not a placeholder.")
    
    # Validate API key with OpenAI
    is_valid = await validate_openai_api_key(OPENAI_API_KEY)
    if not is_valid:
        logger.error("❌ Cannot start server with invalid OpenAI API key!")
        logger.error("Please check your API key and restart the server.")
        logger.error("🛑 Server startup aborted. Set a valid API key and restart.")
        raise RuntimeError("Invalid OpenAI API key. Server startup aborted.")
    logger.info("✅ OpenAI API key validated successfully.")
    
    logger.info("🧠 Initializing LightRAG...")
    rag = None
    try:
        rag = LightRAG(
            working_dir=RAG_DIR,
            embedding_func=openai_embed,
            llm_model_func=gpt_4o_mini_complete,
        )
        await rag.initialize_storages()
        await initialize_pipeline_status()
        app.state.rag = rag
        logger.info("✅ LightRAG initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize LightRAG: {str(e)}")
        raise RuntimeError(f"LightRAG initialization failed: {str(e)}")
    
    logger.info("🔧 Initializing OpenAI client...")
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    app.state.openai_client = openai_client
    logger.info("✅ OpenAI client initialized.")
    
    logger.info("🎉 Study4Me backend server startup complete!")
    
    try:
        yield
    finally:
        # Shutdown
        logger.info("🛑 Initiating graceful shutdown...")
        
        # Signal shutdown to background tasks
        SHUTDOWN_EVENT.set()
        
        # Wait for background tasks to complete (with timeout)
        if BACKGROUND_TASKS:
            logger.info(f"⏳ Waiting for {len(BACKGROUND_TASKS)} background tasks to complete...")
            try:
                await asyncio.wait_for(
                    asyncio.gather(*BACKGROUND_TASKS, return_exceptions=True),
                    timeout=5.0  # Reduced timeout
                )
                logger.info("✅ All background tasks completed.")
            except asyncio.TimeoutError:
                logger.warning("⚠️ Background tasks did not complete within 5 seconds, forcing shutdown.")
                # Cancel remaining tasks aggressively
                cancelled_tasks = []
                for task in BACKGROUND_TASKS.copy():  # Use copy to avoid modification during iteration
                    if not task.done():
                        task.cancel()
                        cancelled_tasks.append(task)
                
                # Wait a bit for cancellations to take effect
                if cancelled_tasks:
                    logger.info(f"🚫 Cancelled {len(cancelled_tasks)} background tasks")
                    try:
                        await asyncio.wait_for(
                            asyncio.gather(*cancelled_tasks, return_exceptions=True),
                            timeout=2.0
                        )
                    except asyncio.TimeoutError:
                        logger.warning("⚠️ Some tasks still didn't respond to cancellation")
                
                # Clear the set
                BACKGROUND_TASKS.clear()
        
        # Finalize LightRAG
        if rag:
            try:
                logger.info("🧠 Finalizing LightRAG...")
                await rag.finalize_storages()
                logger.info("✅ LightRAG finalized successfully.")
            except Exception as e:
                logger.warning(f"⚠️ Error finalizing LightRAG: {str(e)}")
        
        logger.info("✅ Graceful shutdown complete.")

app = FastAPI(title="Study4Me RAG Server", lifespan=lifespan)

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Dependency to access RAG instance ===
def get_rag(request: Request) -> LightRAG:
    return request.app.state.rag

def get_openai_client(request: Request) -> OpenAI:
    return request.app.state.openai_client

# Topic-specific LightRAG instances cache
_topic_rag_cache = {}

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
        logger.warning(f"❌ Study topic not found: {study_topic_id}")
        return None
    
    if not topic.get('use_knowledge_graph', True):
        logger.info(f"📚 Study topic '{topic['name']}' has knowledge graph disabled, skipping LightRAG creation")
        return None
    
    # Create topic-specific directory
    topic_rag_dir = os.path.join(RAG_DIR, f"topic_{study_topic_id}")
    os.makedirs(topic_rag_dir, exist_ok=True)
    
    logger.info(f"🧠 Creating LightRAG instance for topic: {topic['name']} ({study_topic_id})")
    
    try:
        topic_rag = LightRAG(
            working_dir=topic_rag_dir,
            embedding_func=openai_embed,
            llm_model_func=gpt_4o_mini_complete,
        )
        await topic_rag.initialize_storages()
        
        # Cache the instance
        _topic_rag_cache[study_topic_id] = topic_rag
        
        logger.info(f"✅ LightRAG instance created successfully for topic: {topic['name']}")
        return topic_rag
        
    except Exception as e:
        logger.error(f"❌ Failed to create LightRAG for topic {study_topic_id}: {str(e)}")
        return None

# === WebSocket Functions ===

async def broadcast_to_websockets(message: dict):
    """Broadcast a message to all connected WebSocket clients."""
    if not WEBSOCKET_CONNECTIONS:
        return
    
    # Create a list to track connections to remove
    disconnected = []
    
    for websocket in WEBSOCKET_CONNECTIONS.copy():
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Failed to send message to WebSocket: {e}")
            disconnected.append(websocket)
    
    # Remove disconnected WebSockets
    with WEBSOCKET_LOCK:
        for ws in disconnected:
            WEBSOCKET_CONNECTIONS.discard(ws)

async def send_task_update(task_id: str, status: str, message: str = None, progress: int = None, result: dict = None, error: str = None):
    """Send a task update to all connected WebSocket clients."""
    update = {
        "task_id": task_id,
        "status": status,
        "message": message,
        "progress": progress,
        "result": result,
        "error": error,
        "timestamp": time.time()
    }
    await broadcast_to_websockets(update)

def update_task_status(task_id: str, status: str, message: str = None, result: dict = None, error: str = None):
    """Update task status and send WebSocket notification."""
    with TASK_LOCK:
        TASK_STATUS[task_id] = status
    
    # Send WebSocket notification asynchronously
    asyncio.create_task(send_task_update(task_id, status, message, result=result, error=error))

# === Routes ===

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    
    with WEBSOCKET_LOCK:
        WEBSOCKET_CONNECTIONS.add(websocket)
    
    logger.info(f"✅ WebSocket client connected. Total connections: {len(WEBSOCKET_CONNECTIONS)}")
    
    try:
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "welcome",
            "message": "Connected to Study4Me WebSocket",
            "timestamp": time.time()
        }))
        
        # Keep the connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (optional)
                data = await websocket.receive_text()
                logger.info(f"Received WebSocket message: {data}")
                
                # Echo back for debugging
                await websocket.send_text(json.dumps({
                    "type": "echo",
                    "message": f"Received: {data}",
                    "timestamp": time.time()
                }))
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        # Remove from active connections
        with WEBSOCKET_LOCK:
            WEBSOCKET_CONNECTIONS.discard(websocket)
        logger.info(f"🔌 WebSocket client removed. Total connections: {len(WEBSOCKET_CONNECTIONS)}")

@app.get("/", tags=["Debug"])
def root():
    """Basic health check route."""
    return {"message": "Study4Me FastAPI + Docling + LightRAG is running."}

@app.get("/readyz", tags=["Debug"])
def readiness():
    """Kubernetes readiness probe endpoint."""
    return {"status": "ready", "message": "Service is ready to accept requests"}

@app.post("/debug/websocket-notification", tags=["Debug"])
async def send_debug_websocket_notification(
    request: dict = Body(...)
):
    """Debug endpoint to send WebSocket notifications to connected clients."""
    
    message = request.get("message", "Test notification")
    notification_type = request.get("notification_type", "debug")
    target_client = request.get("target_client", None)
    
    if not WEBSOCKET_CONNECTIONS:
        return {
            "status": "no_connections",
            "message": "No WebSocket clients connected",
            "total_connections": 0
        }
    
    notification = {
        "type": notification_type,
        "message": message,
        "target_client": target_client,
        "timestamp": time.time(),
        "from": "debug_endpoint"
    }
    
    try:
        await broadcast_to_websockets(notification)
        return {
            "status": "sent",
            "message": f"Notification sent to {len(WEBSOCKET_CONNECTIONS)} client(s)",
            "total_connections": len(WEBSOCKET_CONNECTIONS),
            "notification": notification
        }
    except Exception as e:
        logger.error(f"Failed to send debug notification: {e}")
        return {
            "status": "error",
            "message": f"Failed to send notification: {str(e)}",
            "total_connections": len(WEBSOCKET_CONNECTIONS)
        }

@app.get("/debug/websocket-status", tags=["Debug"])
def get_websocket_status():
    """Get current WebSocket connection status."""
    return {
        "total_connections": len(WEBSOCKET_CONNECTIONS),
        "connections_active": len(WEBSOCKET_CONNECTIONS) > 0,
        "timestamp": time.time()
    }

@app.post("/documents/upload", tags=["Knowledge Upload"])
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    study_topic_id: str = Form(..., description="UUID of the study topic this content belongs to"),
    callback_url: Optional[str] = Form(None),
):
    # Log upload initiation
    logger.info(f"📁 [upload] Starting document upload for study topic: {study_topic_id[:8]}")
    logger.info(f"📄 [upload] Number of files: {len(files)}")
    
    # Validate study topic exists
    study_topic = await get_study_topic(study_topic_id)
    if not study_topic:
        logger.warning(f"❌ [upload] Study topic not found: {study_topic_id}")
        raise HTTPException(status_code=404, detail=f"Study topic with ID '{study_topic_id}' not found")
    
    logger.info(f"✅ [upload] Study topic validated: '{study_topic['name']}'")
    
    saved_paths = []
    content_items = []
    
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in {".pdf", ".docx", ".xls", ".xlsx"}:
            raise HTTPException(status_code=400, detail=f"File type {ext} not supported.")
        
        # Save file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        saved_paths.append((file.filename, file_path))
        
        # Create content item record (content will be populated after processing)
        content_id = str(uuid.uuid4())
        content_items.append({
            "content_id": content_id,
            "filename": file.filename,
            "file_path": file_path
        })
        
        logger.info(f"📄 [upload] File saved: {file.filename} (ID: {content_id[:8]})")

    # Run in background
    task_id = str(uuid.uuid4())
    with TASK_LOCK:
        TASK_STATUS[task_id] = "processing"
    
    async def process_with_tracking():
        try:
            logger.info(f"⚙️ [upload-{task_id[:8]}] Starting document processing...")
            # Get topic-specific RAG instance
            topic_rag = await get_topic_rag(study_topic_id)
            await process_uploaded_documents(saved_paths, topic_rag, callback_url, study_topic_id, content_items)
            with TASK_LOCK:
                TASK_STATUS[task_id] = "done"
            logger.info(f"✅ [upload-{task_id[:8]}] Document processing completed successfully")
        except Exception as e:
            with TASK_LOCK:
                TASK_STATUS[task_id] = "failed"
            logger.error(f"💥 [upload-{task_id[:8]}] Background task failed: {e}")
    
    # Create and track the background task
    task = asyncio.create_task(process_with_tracking())
    BACKGROUND_TASKS.add(task)
    
    # Add cleanup when task completes
    def cleanup_task(finished_task):
        BACKGROUND_TASKS.discard(finished_task)
    
    task.add_done_callback(cleanup_task)

    logger.info(f"📤 [upload] Upload queued successfully - Task ID: {task_id}")
    return {
        "status": "processing", 
        "files": [name for name, _ in saved_paths], 
        "task_id": task_id,
        "study_topic_id": study_topic_id,
        "study_topic_name": study_topic['name']
    }

@app.get("/datasources", tags=["Datasource Management"])
async def list_datasources():
    """List all uploaded documents with metadata."""
    try:
        if not os.path.exists(UPLOAD_DIR):
            return {"datasources": []}
        
        datasources = []
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                stat_info = os.stat(file_path)
                file_info = {
                    "filename": filename,
                    "size_bytes": stat_info.st_size,
                    "size_mb": round(stat_info.st_size / (1024 * 1024), 2),
                    "upload_time": stat_info.st_mtime,
                    "file_extension": os.path.splitext(filename)[1].lower(),
                    "path": file_path
                }
                datasources.append(file_info)
        
        # Sort by upload time (newest first)
        datasources.sort(key=lambda x: x["upload_time"], reverse=True)
        
        return {
            "total_count": len(datasources),
            "datasources": datasources
        }
    except Exception as e:
        logger.error(f"Error listing datasources: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list datasources: {e}")

@app.get("/datasources/{filename}/info", tags=["Datasource Management"])
async def get_datasource_info(filename: str):
    """Get detailed metadata about a specific uploaded document."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Datasource '{filename}' not found.")
    
    try:
        stat_info = os.stat(file_path)
        file_info = {
            "filename": filename,
            "size_bytes": stat_info.st_size,
            "size_mb": round(stat_info.st_size / (1024 * 1024), 2),
            "upload_time": stat_info.st_mtime,
            "last_modified": stat_info.st_mtime,
            "file_extension": os.path.splitext(filename)[1].lower(),
            "absolute_path": os.path.abspath(file_path)
        }
        return file_info
    except Exception as e:
        logger.error(f"Error getting datasource info for {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get datasource info: {e}")

@app.get("/datasources/{filename}/download", tags=["Datasource Management"])
async def download_datasource(filename: str):
    """Download a specific uploaded document."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Datasource '{filename}' not found.")
    
    try:
        # Determine media type based on file extension
        ext = os.path.splitext(filename)[1].lower()
        media_type_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".txt": "text/plain",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg"
        }
        media_type = media_type_map.get(ext, "application/octet-stream")
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )
    except Exception as e:
        logger.error(f"Error downloading datasource {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download datasource: {e}")

@app.delete("/datasources/{filename}", tags=["Datasource Management"])
async def delete_datasource(filename: str):
    """Delete a specific uploaded document from storage."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Datasource '{filename}' not found.")
    
    try:
        os.remove(file_path)
        logger.info(f"Deleted datasource: {filename}")
        return {
            "message": f"Datasource '{filename}' has been successfully deleted.",
            "filename": filename,
            "status": "deleted"
        }
    except Exception as e:
        logger.error(f"Error deleting datasource {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete datasource: {e}")

@app.post("/webpage/process", tags=["Knowledge Upload"])
async def process_webpage(
    background_tasks: BackgroundTasks,
    url: str = Body(..., embed=True),
    study_topic_id: str = Body(..., description="UUID of the study topic this content belongs to", embed=True),
    callback_url: Optional[str] = Body(None, embed=True),
):
    # Log webpage processing initiation
    logger.info(f"🌐 [webpage] Starting webpage processing for study topic: {study_topic_id[:8]}")
    logger.info(f"🔗 [webpage] URL: {url}")
    
    # Validate study topic exists
    study_topic = await get_study_topic(study_topic_id)
    if not study_topic:
        logger.warning(f"❌ [webpage] Study topic not found: {study_topic_id}")
        raise HTTPException(status_code=404, detail=f"Study topic with ID '{study_topic_id}' not found")
    
    logger.info(f"✅ [webpage] Study topic validated: '{study_topic['name']}'")
    
    # Create content item record
    content_id = str(uuid.uuid4())
    logger.info(f"🌐 [webpage] Content item created (ID: {content_id[:8]})")
    
    # Run in background
    task_id = str(uuid.uuid4())
    with TASK_LOCK:
        TASK_STATUS[task_id] = "processing"
    
    async def process_with_tracking():
        try:
            logger.info(f"⚙️ [webpage-{task_id[:8]}] Starting background processing...")
            # Get topic-specific RAG instance
            topic_rag = await get_topic_rag(study_topic_id)
            await process_webpage_background(url, topic_rag, callback_url, study_topic_id, content_id)
            with TASK_LOCK:
                TASK_STATUS[task_id] = "done"
            logger.info(f"✅ [webpage-{task_id[:8]}] Background processing completed successfully")
        except Exception as e:
            with TASK_LOCK:
                TASK_STATUS[task_id] = "failed"
            logger.error(f"💥 [webpage-{task_id[:8]}] Background task failed: {e}")
    
    # Create and track the background task
    task = asyncio.create_task(process_with_tracking())
    BACKGROUND_TASKS.add(task)
    
    # Add cleanup when task completes
    def cleanup_task(finished_task):
        BACKGROUND_TASKS.discard(finished_task)
    
    task.add_done_callback(cleanup_task)
    
    logger.info(f"📤 [webpage] Webpage processing queued successfully - Task ID: {task_id}")
    return {
        "status": "processing", 
        "url": url, 
        "task_id": task_id,
        "study_topic_id": study_topic_id,
        "study_topic_name": study_topic['name'],
        "content_id": content_id
    }

@app.post("/youtube/process", tags=["Knowledge Upload"])
async def process_youtube_video(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    study_topic_id: str = Form(..., description="UUID of the study topic this content belongs to"),
    callback_url: Optional[str] = Form(None),
):
    """Process YouTube video transcript and add to LightRAG knowledge base"""
    # Log YouTube processing initiation
    logger.info(f"📺 [youtube] Starting YouTube processing for study topic: {study_topic_id[:8]}")
    logger.info(f"🔗 [youtube] URL: {url}")
    
    # Validate study topic exists
    study_topic = await get_study_topic(study_topic_id)
    if not study_topic:
        logger.warning(f"❌ [youtube] Study topic not found: {study_topic_id}")
        raise HTTPException(status_code=404, detail=f"Study topic with ID '{study_topic_id}' not found")
    
    logger.info(f"✅ [youtube] Study topic validated: '{study_topic['name']}'")
    
    # Create content item record
    content_id = str(uuid.uuid4())
    logger.info(f"📺 [youtube] Content item created (ID: {content_id[:8]})")
    
    task_id = str(uuid.uuid4())
    with TASK_LOCK:
        TASK_STATUS[task_id] = "processing"

    async def process_with_tracking():
        try:
            logger.info(f"⚙️ [youtube-{task_id[:8]}] Starting background processing...")
            start_bg = time.perf_counter()
            
            # Get topic-specific RAG instance
            topic_rag = await get_topic_rag(study_topic_id)
            await process_youtube_background(url, topic_rag, task_id, callback_url, study_topic_id, content_id)
            
            total_bg = time.perf_counter() - start_bg
            logger.info(f"✅ [youtube-{task_id[:8]}] Background processing completed in {total_bg:.2f}s")
            
            with TASK_LOCK:
                TASK_STATUS[task_id] = "done"
        except Exception as e:
            total_bg = time.perf_counter() - start_bg if 'start_bg' in locals() else 0
            logger.error(f"💥 [youtube-{task_id[:8]}] Background processing failed after {total_bg:.2f}s: {str(e)}")
            logger.error(f"🔍 [youtube-{task_id[:8]}] Error details: {type(e).__name__}: {str(e)}")
            
            with TASK_LOCK:
                TASK_STATUS[task_id] = "failed"
    
    # Create and track the background task
    task = asyncio.create_task(process_with_tracking())
    BACKGROUND_TASKS.add(task)
    
    # Add cleanup when task completes
    def cleanup_task(finished_task):
        BACKGROUND_TASKS.discard(finished_task)
    
    task.add_done_callback(cleanup_task)
    
    logger.info(f"📤 [youtube-{task_id[:8]}] YouTube processing queued successfully")
    return {
        "status": "processing", 
        "task_id": task_id, 
        "url": url,
        "study_topic_id": study_topic_id,
        "study_topic_name": study_topic['name'],
        "content_id": content_id,
        "message": "YouTube video processing started. Transcript will be extracted and added to knowledge base."
    }

@app.get("/youtube/transcript", tags=["YouTube"])
async def get_transcript(
    url: str = Query(..., description="YouTube video URL"),
    lang: Optional[str] = Query("en", description="Language code (e.g., 'en', 'es', 'pt')")
):
    """Get transcript for a single YouTube video"""
    return await get_youtube_transcript(url, lang)

@app.post("/youtube/batch", tags=["YouTube"])
async def batch_transcripts(request: BatchRequest):
    """Process multiple YouTube videos and return their transcripts"""
    return await batch_youtube_transcripts(request)

@app.get("/query", tags=["Queries"])
async def query_rag(
    query: str = Query(...),
    study_topic_id: str = Query(..., description="UUID of the study topic to query"),
    mode: Optional[str] = Query("hybrid"),
):
    """Query the LightRAG system using different RAG modes."""
    query_id = str(uuid.uuid4())[:8]  # Short ID for tracking
    start_total = time.perf_counter()
    
    # Log query start with details
    logger.info(f"🔍 [query-{query_id}] Starting synchronous query for topic: {study_topic_id[:8]}")
    logger.info(f"📝 [query-{query_id}] Mode: {mode} | Query length: {len(query)} chars")
    logger.debug(f"📄 [query-{query_id}] Query content: {query[:200]}{'...' if len(query) > 200 else ''}")
    
    try:
        # Check if topic exists first
        topic = await get_study_topic(study_topic_id)
        if not topic:
            raise HTTPException(
                status_code=404, 
                detail=f"Study topic with ID '{study_topic_id}' not found"
            )
        
        # Branch based on knowledge graph setting
        if topic.get('use_knowledge_graph', True):
            # Use LightRAG for knowledge graph enabled topics
            logger.info(f"🧠 [query-{query_id}] Using LightRAG (knowledge graph enabled)")
            rag = await get_topic_rag(study_topic_id)
            if not rag:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to initialize LightRAG for topic '{topic['name']}'"
                )
            
            t0 = time.perf_counter()
            logger.info(f"⚙️ [query-{query_id}] Starting LightRAG processing...")
            
            param = QueryParam(mode=mode)
            result = await asyncio.to_thread(rag.query, query, param=param)
            
            t1 = time.perf_counter()
            processing_time = t1 - t0
            logger.info(f"✅ [query-{query_id}] LightRAG processing completed: {processing_time:.2f}s")
            
        else:
            # Use ChatGPT with context for non-knowledge graph topics
            logger.info(f"💬 [query-{query_id}] Using ChatGPT with context (knowledge graph disabled)")
            
            t0 = time.perf_counter()
            logger.info(f"⚙️ [query-{query_id}] Loading topic content...")
            
            # Get all content for the topic
            content_items = await list_content_items_by_topic(study_topic_id)
            
            # Combine all content
            combined_content = ""
            for item in content_items:
                full_item = await get_content_item(item['content_id'])
                if full_item and full_item.get('content'):
                    combined_content += f"\n\n--- {full_item['title']} ---\n{full_item['content']}"
            
            if not combined_content.strip():
                raise HTTPException(
                    status_code=404,
                    detail=f"No content available for topic '{topic['name']}'. Please upload content first."
                )
            
            logger.info(f"📄 [query-{query_id}] Loaded {len(content_items)} content items ({len(combined_content)} chars)")
            
            # Query using ChatGPT with context
            openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            result = await query_with_context(query, combined_content, topic['name'], openai_client)
            
            t1 = time.perf_counter()
            processing_time = t1 - t0
            logger.info(f"✅ [query-{query_id}] ChatGPT processing completed: {processing_time:.2f}s")

        # Calculate total time and log results
        total = time.perf_counter() - start_total
        result_length = len(str(result)) if result else 0
        
        processing_method = "LightRAG" if topic.get('use_knowledge_graph', True) else "ChatGPT+Context"
        
        logger.info(f"🎉 [query-{query_id}] Query completed successfully:")
        logger.info(f"   ⏱️  Total time: {total:.2f}s")
        logger.info(f"   🤖 Processing method: {processing_method}")
        logger.info(f"   ⚡ Processing time: {processing_time:.2f}s ({(processing_time/total)*100:.1f}%)")
        logger.info(f"   📊 Response length: {result_length} chars")
        if topic.get('use_knowledge_graph', True):
            logger.info(f"   🔧 Mode used: {mode}")
        else:
            logger.info(f"   📄 Content items: {len(content_items)}")

        return {
            "result": result,
            "processing_method": processing_method,
            "processing_time_seconds": round(processing_time, 2),
            "total_time_seconds": round(total, 2),
            "study_topic_id": study_topic_id,
            "study_topic_name": topic['name'],
            "use_knowledge_graph": topic.get('use_knowledge_graph', True)
        }
        
    except (AuthenticationError, RateLimitError, APIError) as e:
        logger.error(f"❌ [query-{query_id}] OpenAI API error after {time.perf_counter() - start_total:.2f}s")
        raise handle_openai_error(e)
    except Exception as e:
        total_time = time.perf_counter() - start_total
        logger.error(f"💥 [query-{query_id}] Query failed after {total_time:.2f}s: {str(e)}")
        logger.error(f"🔍 [query-{query_id}] Error details: {type(e).__name__}: {str(e)}")
        return JSONResponse(status_code=500, content={
            "error": "Query processing failed",
            "message": str(e),
            "type": "processing_error",
            "query_id": query_id,
            "processing_time": round(total_time, 2)
        })

@app.post("/query-async", tags=["Queries"])
async def query_rag_async(
    background_tasks: BackgroundTasks,
    query: str = Query(...),
    study_topic_id: str = Query(..., description="UUID of the study topic to query"),
    mode: Optional[str] = Query("hybrid"),
    callback_url: Optional[str] = Form(None),
):
    task_id = str(uuid.uuid4())
    
    # Log async query initiation
    logger.info(f"🚀 [async-{task_id[:8]}] Initiating async query for topic: {study_topic_id[:8]}")
    logger.info(f"📝 [async-{task_id[:8]}] Mode: {mode} | Query length: {len(query)} chars")
    logger.info(f"🔗 [async-{task_id[:8]}] Callback URL: {'Yes' if callback_url else 'No'}")
    logger.debug(f"📄 [async-{task_id[:8]}] Query content: {query[:200]}{'...' if len(query) > 200 else ''}")

    with TASK_LOCK:
        TASK_STATUS[task_id] = "processing"

    async def process_with_tracking():
        try:
            logger.info(f"⚙️ [async-{task_id[:8]}] Starting background processing...")
            start_bg = time.perf_counter()
            
            # Get topic-specific RAG instance
            rag = await get_topic_rag(study_topic_id)
            await process_query_background(query, mode, rag, task_id, callback_url, study_topic_id)
            
            total_bg = time.perf_counter() - start_bg
            logger.info(f"✅ [async-{task_id[:8]}] Background processing completed in {total_bg:.2f}s")
            
            with TASK_LOCK:
                TASK_STATUS[task_id] = "done"
        except Exception as e:
            total_bg = time.perf_counter() - start_bg if 'start_bg' in locals() else 0
            logger.error(f"💥 [async-{task_id[:8]}] Background query failed after {total_bg:.2f}s: {str(e)}")
            logger.error(f"🔍 [async-{task_id[:8]}] Error details: {type(e).__name__}: {str(e)}")
            
            with TASK_LOCK:
                TASK_STATUS[task_id] = "failed"
    
    # Create and track the background task
    task = asyncio.create_task(process_with_tracking())
    BACKGROUND_TASKS.add(task)
    
    # Add cleanup when task completes
    def cleanup_task(finished_task):
        BACKGROUND_TASKS.discard(finished_task)
    
    task.add_done_callback(cleanup_task)
    
    logger.info(f"📤 [async-{task_id[:8]}] Async query queued successfully")
    return {
        "status": "processing", 
        "task_id": task_id, 
        "query_preview": query[:100] + "..." if len(query) > 100 else query,
        "mode": mode
    }

@app.get("/graph/json", tags=["Knowledge Graph"])
async def get_knowledge_graph_from_file():
    """Load the knowledge graph from GraphML and return it as JSON."""
    if not os.path.exists(GRAPHML_PATH):
        raise HTTPException(status_code=404, detail="GraphML file not found.")
    try:
        G = nx.read_graphml(GRAPHML_PATH)
        nodes = [{"id": str(n), **G.nodes[n]} for n in G.nodes]
        edges = [{"source": str(u), "target": str(v), **d} for u, v, d in G.edges(data=True)]
        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load graph: {e}")

@app.get("/graph/graphml", tags=["Knowledge Graph"])
async def download_graphml():
    """Download the knowledge graph file in GraphML format."""
    if not os.path.exists(GRAPHML_PATH):
        raise HTTPException(status_code=404, detail="GraphML file not found.")
    return FileResponse(
        path=GRAPHML_PATH,
        media_type="application/xml",
        filename=os.path.basename(GRAPHML_PATH)
    )

@app.get("/graph/png", tags=["Knowledge Graph"])
async def download_graph_png():
    """Render the knowledge graph as a PNG image and return it in-memory."""
    if not os.path.exists(GRAPHML_PATH):
        raise HTTPException(status_code=404, detail="GraphML file not found.")
    try:
        G = nx.read_graphml(GRAPHML_PATH)
        plt.figure(figsize=(20, 12))
        pos = nx.spring_layout(G, k=0.5)
        nx.draw(
            G, pos,
            with_labels=True,
            node_size=500,
            node_color="skyblue",
            font_size=8,
            edge_color="gray",
            arrows=True
        )
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format="png")
        plt.close()
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="image/png", headers={
            "Content-Disposition": "inline; filename=knowledge_graph.png"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render PNG: {e}")

@app.post("/image/interpret", tags=["Knowledge Upload"])
async def interpret_image(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    study_topic_id: str = Form(..., description="UUID of the study topic this content belongs to"),
    prompt: Optional[str] = Body("Describe this image and extract key information", embed=True),
    callback_url: Optional[str] = Form(None),
    openai_client: OpenAI = Depends(get_openai_client),
):
    # Log image processing initiation
    logger.info(f"🖼️ [image] Starting image processing for study topic: {study_topic_id[:8]}")
    logger.info(f"📄 [image] Filename: {image.filename}")
    
    # Validate study topic exists
    study_topic = await get_study_topic(study_topic_id)
    if not study_topic:
        logger.warning(f"❌ [image] Study topic not found: {study_topic_id}")
        raise HTTPException(status_code=404, detail=f"Study topic with ID '{study_topic_id}' not found")
    
    logger.info(f"✅ [image] Study topic validated: '{study_topic['name']}'")
    
    # Create content item record
    content_id = str(uuid.uuid4())
    logger.info(f"🖼️ [image] Content item created (ID: {content_id[:8]})")
    
    # Save file for later processing
    file_path = os.path.join(UPLOAD_DIR, image.filename)
    with open(file_path, "wb") as f:
        f.write(await image.read())

    # Run in background
    task_id = str(uuid.uuid4())
    with TASK_LOCK:
        TASK_STATUS[task_id] = "processing"
    
    async def process_with_tracking():
        try:
            # Get topic-specific RAG instance
            topic_rag = await get_topic_rag(study_topic_id)
            await process_image_background(file_path, prompt, image.filename, openai_client, topic_rag, callback_url, study_topic_id, content_id)
            with TASK_LOCK:
                TASK_STATUS[task_id] = "done"
        except Exception as e:
            with TASK_LOCK:
                TASK_STATUS[task_id] = "failed"
            logger.error(f"[{task_id}] Background task failed: {e}")
    
    # Create and track the background task
    task = asyncio.create_task(process_with_tracking())
    BACKGROUND_TASKS.add(task)
    
    # Add cleanup when task completes
    def cleanup_task(finished_task):
        BACKGROUND_TASKS.discard(finished_task)
    
    task.add_done_callback(cleanup_task)

    logger.info(f"📤 [image] Image processing queued successfully - Task ID: {task_id}")
    return {
        "status": "processing", 
        "filename": image.filename, 
        "task_id": task_id,
        "study_topic_id": study_topic_id,
        "study_topic_name": study_topic['name'],
        "content_id": content_id
    }
    
@app.get("/task-status/{task_id}", tags=["Tasks"])
async def get_task_status_combined(task_id: str):
    with TASK_LOCK:
        status = TASK_STATUS.get(task_id)

    if status is None:
        raise HTTPException(status_code=404, detail="Task ID not found")

    # Fetch result from database if available
    result = await fetch_task_result(task_id)

    return {
        "task_id": task_id,
        "status": status,
        "result": result["result"] if result and status == "done" else None,
        "processing_time_seconds": result["processing_time"] if result and status == "done" else None
    }

# === Study Topics Management ===

@app.post("/study-topics", tags=["Study Topics"], response_model=dict)
async def create_new_study_topic(topic: StudyTopicCreate):
    """Create a new study topic and return its UUID"""
    try:
        # Generate UUID for the topic
        topic_id = str(uuid.uuid4())
        
        # Log topic creation
        logger.info(f"📚 Creating new study topic: '{topic.name}' (ID: {topic_id[:8]})")
        logger.info(f"📝 Description: {topic.description[:100] + '...' if topic.description and len(topic.description) > 100 else topic.description or 'None'}")
        logger.info(f"🧠 Knowledge graph enabled: {topic.use_knowledge_graph}")
        
        # Save to database
        await create_study_topic(
            topic_id=topic_id,
            name=topic.name,
            description=topic.description,
            use_knowledge_graph=topic.use_knowledge_graph
        )
        
        logger.info(f"✅ Study topic created successfully: {topic_id}")
        
        return {
            "message": "Study topic created successfully",
            "topic_id": topic_id,
            "name": topic.name,
            "description": topic.description,
            "use_knowledge_graph": topic.use_knowledge_graph
        }
        
    except Exception as e:
        logger.error(f"❌ Error creating study topic: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create study topic: {str(e)}")

@app.get("/study-topics", tags=["Study Topics"], response_model=dict)
async def get_study_topics(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of topics to return"),
    offset: int = Query(0, ge=0, description="Number of topics to skip")
):
    """List all study topics with pagination"""
    try:
        logger.info(f"📚 Fetching study topics (limit: {limit}, offset: {offset})")
        
        topics = await list_study_topics(limit=limit, offset=offset)
        
        logger.info(f"✅ Retrieved {len(topics)} study topics")
        
        return {
            "total_retrieved": len(topics),
            "limit": limit,
            "offset": offset,
            "topics": topics
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching study topics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch study topics: {str(e)}")

@app.get("/study-topics/{topic_id}", tags=["Study Topics"], response_model=StudyTopicResponse)
async def get_study_topic_by_id(topic_id: str):
    """Get a specific study topic by its UUID"""
    try:
        logger.info(f"📚 Fetching study topic: {topic_id}")
        
        topic = await get_study_topic(topic_id)
        
        if not topic:
            logger.warning(f"❌ Study topic not found: {topic_id}")
            raise HTTPException(status_code=404, detail=f"Study topic with ID '{topic_id}' not found")
        
        logger.info(f"✅ Retrieved study topic: {topic['name']}")
        
        return topic
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching study topic {topic_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch study topic: {str(e)}")

@app.put("/study-topics/{topic_id}", tags=["Study Topics"], response_model=dict)
async def update_study_topic_by_id(topic_id: str, topic_update: StudyTopicUpdate):
    """Update an existing study topic"""
    try:
        logger.info(f"📚 Updating study topic: {topic_id}")
        
        # Check if topic exists
        existing_topic = await get_study_topic(topic_id)
        if not existing_topic:
            logger.warning(f"❌ Study topic not found for update: {topic_id}")
            raise HTTPException(status_code=404, detail=f"Study topic with ID '{topic_id}' not found")
        
        # Update the topic
        updated = await update_study_topic(
            topic_id=topic_id,
            name=topic_update.name,
            description=topic_update.description,
            use_knowledge_graph=topic_update.use_knowledge_graph
        )
        
        if not updated:
            logger.warning(f"⚠️ No changes made to study topic: {topic_id}")
            return {"message": "No changes made to study topic", "topic_id": topic_id}
        
        # Fetch updated topic
        updated_topic = await get_study_topic(topic_id)
        
        logger.info(f"✅ Study topic updated successfully: {topic_id}")
        
        return {
            "message": "Study topic updated successfully",
            "topic": updated_topic
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating study topic {topic_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update study topic: {str(e)}")

@app.delete("/study-topics/{topic_id}", tags=["Study Topics"], response_model=dict)
async def delete_study_topic_by_id(topic_id: str):
    """Delete a study topic"""
    try:
        logger.info(f"📚 Deleting study topic: {topic_id}")
        
        # Check if topic exists
        existing_topic = await get_study_topic(topic_id)
        if not existing_topic:
            logger.warning(f"❌ Study topic not found for deletion: {topic_id}")
            raise HTTPException(status_code=404, detail=f"Study topic with ID '{topic_id}' not found")
        
        # Delete the topic
        deleted = await delete_study_topic(topic_id)
        
        if not deleted:
            logger.error(f"❌ Failed to delete study topic: {topic_id}")
            raise HTTPException(status_code=500, detail="Failed to delete study topic")
        
        logger.info(f"✅ Study topic deleted successfully: {existing_topic['name']} ({topic_id})")
        
        return {
            "message": "Study topic deleted successfully",
            "topic_id": topic_id,
            "name": existing_topic["name"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting study topic {topic_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete study topic: {str(e)}")

@app.get("/study-topics/{topic_id}/content", tags=["Study Topics"], response_model=dict)
async def get_study_topic_content(topic_id: str):
    """Get all content items for a specific study topic with token count"""
    try:
        logger.info(f"📚 Fetching content for study topic: {topic_id}")
        
        # Check if topic exists
        topic = await get_study_topic(topic_id)
        if not topic:
            logger.warning(f"❌ Study topic not found: {topic_id}")
            raise HTTPException(status_code=404, detail=f"Study topic with ID '{topic_id}' not found")
        
        # Get all content items for this topic with full content
        content_items_summary = await list_content_items_by_topic(topic_id)
        logger.info(f"📄 Found {len(content_items_summary)} content items for topic: {topic['name']}")
        
        # Get full content for each item and calculate individual token counts
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
        
        logger.info(f"📊 Total content length: {total_content_length} chars, {total_token_count} tokens")
        
        return {
            "topic_id": topic_id,
            "topic_name": topic['name'],
            "topic_description": topic.get('description', ''),
            "use_knowledge_graph": topic.get('use_knowledge_graph', True),
            "content_items_count": len(detailed_content_items),
            "total_content_length": total_content_length,
            "number_tokens": total_token_count,
            "content_items": detailed_content_items
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching content for study topic {topic_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch study topic content: {str(e)}")

@app.get("/study-topics/{topic_id}/summarize", tags=["Study Topics"], response_model=dict)
async def summarize_study_topic_content(
    topic_id: str,
    openai_client: OpenAI = Depends(get_openai_client)
):
    """Generate a comprehensive summary of all content for a specific study topic using OpenAI with SQLite caching"""
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
        
    except (AuthenticationError, RateLimitError, APIError) as e:
        logger.error(f"❌ [summary-{summary_id}] OpenAI API error after {time.perf_counter() - start_total:.2f}s")
        raise handle_openai_error(e)
    except HTTPException:
        raise
    except Exception as e:
        total_time = time.perf_counter() - start_total
        logger.error(f"💥 [summary-{summary_id}] Summarization failed after {total_time:.2f}s: {str(e)}")
        logger.error(f"🔍 [summary-{summary_id}] Error details: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate summary for topic '{topic.get('name', topic_id)}': {str(e)}"
        )

@app.get("/study-topics/{topic_id}/mindmap", tags=["Study Topics"], response_model=dict)
async def generate_study_topic_mindmap(
    topic_id: str,
    openai_client: OpenAI = Depends(get_openai_client)
):
    """Generate a Mermaid mindmap code for all content in a specific study topic using OpenAI with SQLite caching"""
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
            import re
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