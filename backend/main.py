import os
import io
import shutil
import asyncio
import logging
import time
import json
import uuid
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

from openai import OpenAI
from utils.utils_async import process_uploaded_documents, process_webpage_background, process_image_background, process_query_background
from utils.db_async import init_db, fetch_task_result
from youtube_service import get_youtube_transcript, batch_youtube_transcripts, BatchRequest

# Handle multiple tasks statuses
TASK_STATUS = {}  # Ex: {task_id: "processing" | "done" | "failed"}
TASK_LOCK = Lock()

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

# === OpenAI Key Check ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable must be set.")
    raise RuntimeError("OPENAI_API_KEY environment variable must be set.")

# === FastAPI Initialization with Lifespan ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized.")
    
    logger.info("Initializing LightRAG...")
    rag = LightRAG(
        working_dir=RAG_DIR,
        embedding_func=openai_embed,
        llm_model_func=gpt_4o_mini_complete,
    )
    await rag.initialize_storages()
    await initialize_pipeline_status()
    app.state.rag = rag
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    app.state.openai_client = openai_client
    logger.info("OpenAI client initialized.")
    yield
    await rag.finalize_storages()

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
    
    def fire_and_forget(saved_paths, rag, callback_url):
        try:
            asyncio.run(process_uploaded_documents(saved_paths, rag, callback_url))
            with TASK_LOCK:
                TASK_STATUS[task_id] = "done"
        except Exception as e:
            with TASK_LOCK:
                TASK_STATUS[task_id] = "failed"
            logger.error(f"[{task_id}] Background task failed: {e}")
    
    background_tasks.add_task(fire_and_forget, saved_paths, rag, callback_url)

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
    
    def fire_and_forget(url, rag, callback_url):
        try:
            asyncio.run(process_webpage_background(url, rag, callback_url))
            with TASK_LOCK:
                TASK_STATUS[task_id] = "done"
        except Exception as e:
            with TASK_LOCK:
                TASK_STATUS[task_id] = "failed"
            logger.error(f"[{task_id}] Background task failed: {e}")
    
    background_tasks.add_task(fire_and_forget, url, rag, callback_url)
    
    return {"status": "processing", "url": url, "task_id": task_id}

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
    start_total = time.perf_counter()
    try:
        # Log start of query
        t0 = time.perf_counter()
        param = QueryParam(mode=mode)
        result = await asyncio.to_thread(rag.query, query, param=param)
        t1 = time.perf_counter()
        logger.info(f"[query] LightRAG.query execution: {t1 - t0:.2f}s")

        total = time.perf_counter() - start_total
        logger.info(f"[query] Total endpoint time: {total:.2f}s")

        return {"result": result}
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/query-async", tags=["Queries"])
async def query_rag_async(
    background_tasks: BackgroundTasks,
    query: str = Query(...),
    mode: Optional[str] = Query("hybrid"),
    callback_url: Optional[str] = Form(None),
    rag: LightRAG = Depends(get_rag),
):
    task_id = str(uuid.uuid4())

    with TASK_LOCK:
        TASK_STATUS[task_id] = "processing"

    def fire_and_forget():
        try:
            asyncio.run(process_query_background(query, mode, rag, task_id, callback_url))
            with TASK_LOCK:
                TASK_STATUS[task_id] = "done"
        except Exception as e:
            with TASK_LOCK:
                TASK_STATUS[task_id] = "failed"
            logger.error(f"[{task_id}] Background query failed: {e}")

    background_tasks.add_task(fire_and_forget)

    return {"status": "processing", "task_id": task_id, "query": query}

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
    
    def fire_and_forget(file_path, prompt, image_filename, openai_client, rag, callback_url):
        try:
            asyncio.run(process_image_background(file_path, prompt, image_filename, openai_client, rag, callback_url))
            with TASK_LOCK:
                TASK_STATUS[task_id] = "done"
        except Exception as e:
            with TASK_LOCK:
                TASK_STATUS[task_id] = "failed"
            logger.error(f"[{task_id}] Background task failed: {e}")

    background_tasks.add_task(fire_and_forget, file_path, prompt, image.filename, openai_client, rag, callback_url)

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