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

from dotenv import load_dotenv

import networkx as nx
import matplotlib.pyplot as plt
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Body, Request, Depends, BackgroundTasks, Form
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
from lightrag.kg.shared_storage import initialize_pipeline_status

from openai import OpenAI, AuthenticationError, RateLimitError, APIError
from utils.utils_async import process_uploaded_documents, process_webpage_background, process_image_background, process_query_background, process_youtube_background
from utils.db_async import init_db, fetch_task_result
from youtube_service import get_youtube_transcript, batch_youtube_transcripts, BatchRequest

# Handle multiple tasks statuses
TASK_STATUS = {}  # Ex: {task_id: "processing" | "done" | "failed"}
TASK_LOCK = Lock()

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

# === Routes ===

@app.get("/", tags=["Debug"])
def root():
    """Basic health check route."""
    return {"message": "Study4Me FastAPI + Docling + LightRAG is running."}

@app.get("/readyz", tags=["Debug"])
def readiness():
    """Kubernetes readiness probe endpoint."""
    return {"status": "ready", "message": "Service is ready to accept requests"}

@app.post("/documents/upload", tags=["Knowledge Upload"])
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    callback_url: Optional[str] = Form(None),
    rag: LightRAG = Depends(get_rag),
):
    saved_paths = []
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in {".pdf", ".docx", ".xls", ".xlsx"}:
            raise HTTPException(status_code=400, detail=f"File type {ext} not supported.")
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        saved_paths.append((file.filename, file_path))

    # Run in background
    task_id = str(uuid.uuid4())
    with TASK_LOCK:
        TASK_STATUS[task_id] = "processing"
    
    async def process_with_tracking():
        try:
            await process_uploaded_documents(saved_paths, rag, callback_url)
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

    return {"status": "processing", "files": [name for name, _ in saved_paths], "task_id": task_id}

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
    callback_url: Optional[str] = Body(None, embed=True),
    rag: LightRAG = Depends(get_rag),
):
    # Run in background
    task_id = str(uuid.uuid4())
    with TASK_LOCK:
        TASK_STATUS[task_id] = "processing"
    
    async def process_with_tracking():
        try:
            await process_webpage_background(url, rag, callback_url)
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
    
    return {"status": "processing", "url": url, "task_id": task_id}

@app.post("/youtube/process", tags=["Knowledge Upload"])
async def process_youtube_video(
    background_tasks: BackgroundTasks,
    url: str = Body(..., embed=True),
    callback_url: Optional[str] = Body(None, embed=True),
    rag: LightRAG = Depends(get_rag),
):
    """Process YouTube video transcript and add to LightRAG knowledge base"""
    task_id = str(uuid.uuid4())
    
    # Log YouTube processing initiation
    logger.info(f"📺 [youtube-{task_id[:8]}] Initiating YouTube video processing")
    logger.info(f"🔗 [youtube-{task_id[:8]}] URL: {url}")
    logger.info(f"📞 [youtube-{task_id[:8]}] Callback URL: {'Yes' if callback_url else 'No'}")
    
    with TASK_LOCK:
        TASK_STATUS[task_id] = "processing"

    async def process_with_tracking():
        try:
            logger.info(f"⚙️ [youtube-{task_id[:8]}] Starting background processing...")
            start_bg = time.perf_counter()
            
            await process_youtube_background(url, rag, task_id, callback_url)
            
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
    mode: Optional[str] = Query("hybrid"),
    rag: LightRAG = Depends(get_rag)
):
    """Query the LightRAG system using different RAG modes."""
    query_id = str(uuid.uuid4())[:8]  # Short ID for tracking
    start_total = time.perf_counter()
    
    # Log query start with details
    logger.info(f"🔍 [query-{query_id}] Starting synchronous query")
    logger.info(f"📝 [query-{query_id}] Mode: {mode} | Query length: {len(query)} chars")
    logger.debug(f"📄 [query-{query_id}] Query content: {query[:200]}{'...' if len(query) > 200 else ''}")
    
    try:
        # Log LightRAG processing start
        t0 = time.perf_counter()
        logger.info(f"⚙️ [query-{query_id}] Starting LightRAG processing...")
        
        param = QueryParam(mode=mode)
        result = await asyncio.to_thread(rag.query, query, param=param)
        
        t1 = time.perf_counter()
        rag_time = t1 - t0
        logger.info(f"✅ [query-{query_id}] LightRAG processing completed: {rag_time:.2f}s")

        # Calculate total time and log results
        total = time.perf_counter() - start_total
        result_length = len(str(result)) if result else 0
        
        logger.info(f"🎉 [query-{query_id}] Query completed successfully:")
        logger.info(f"   ⏱️  Total time: {total:.2f}s")
        logger.info(f"   🧠 LightRAG time: {rag_time:.2f}s ({(rag_time/total)*100:.1f}%)")
        logger.info(f"   📊 Response length: {result_length} chars")
        logger.info(f"   🔧 Mode used: {mode}")

        return {"result": result}
        
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
    mode: Optional[str] = Query("hybrid"),
    callback_url: Optional[str] = Form(None),
    rag: LightRAG = Depends(get_rag),
):
    task_id = str(uuid.uuid4())
    
    # Log async query initiation
    logger.info(f"🚀 [async-{task_id[:8]}] Initiating async query")
    logger.info(f"📝 [async-{task_id[:8]}] Mode: {mode} | Query length: {len(query)} chars")
    logger.info(f"🔗 [async-{task_id[:8]}] Callback URL: {'Yes' if callback_url else 'No'}")
    logger.debug(f"📄 [async-{task_id[:8]}] Query content: {query[:200]}{'...' if len(query) > 200 else ''}")

    with TASK_LOCK:
        TASK_STATUS[task_id] = "processing"

    async def process_with_tracking():
        try:
            logger.info(f"⚙️ [async-{task_id[:8]}] Starting background processing...")
            start_bg = time.perf_counter()
            
            await process_query_background(query, mode, rag, task_id, callback_url)
            
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
    prompt: Optional[str] = Body("Describe this image and extract key information", embed=True),
    callback_url: Optional[str] = Form(None),
    openai_client: OpenAI = Depends(get_openai_client),
    rag: LightRAG = Depends(get_rag)
):
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
            await process_image_background(file_path, prompt, image.filename, openai_client, rag, callback_url)
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

    return {"status": "processing", "filename": image.filename, "task_id": task_id}
    
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