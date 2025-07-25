import time
import asyncio
import os
import base64
from typing import Optional
from openai import OpenAI
from lightrag import LightRAG, QueryParam
from docling.document_converter import DocumentConverter
from .utils_ws import notify_callback
import logging
from .db_async import save_task_result
import json

logger = logging.getLogger(__name__)

async def process_uploaded_documents(saved_paths, rag: LightRAG, callback_url: Optional[str]):
    converter = DocumentConverter()

    for filename, file_path in saved_paths:
        start_total = time.perf_counter()
        logger.info(f"[{filename}] Starting ingestion...")

        try:
            # --- Docling conversion ---
            t0 = time.perf_counter()
            conv = converter.convert(file_path)
            text = conv.document.export_to_markdown()
            t1 = time.perf_counter()
            logger.info(f"[{filename}] Docling conversion: {t1 - t0:.2f}s")

            # --- LightRAG insertion ---
            t0 = time.perf_counter()
            await asyncio.to_thread(rag.insert, text, file_paths=[file_path])
            t1 = time.perf_counter()
            logger.info(f"[{filename}] LightRAG.insert: {t1 - t0:.2f}s")

            total = time.perf_counter() - start_total
            logger.info(f"[{filename}] Total processing time: {total:.2f}s")

            if callback_url:
                await notify_callback(callback_url, {
                    "filename": filename,
                    "status": "success",
                    "processing_time_seconds": round(total, 2)
                })

        except Exception as e:
            logger.error(f"[{filename}] Error: {e}")
            if callback_url:
                await notify_callback(callback_url, {
                    "filename": filename,
                    "status": "error",
                    "error": str(e)
                })
                
async def process_image_background(
    file_path: str,
    prompt: str,
    filename: str,
    openai_client: OpenAI,
    rag: LightRAG,
    callback_url: Optional[str]
):
    start_total = time.perf_counter()
    logger.info(f"[{filename}] Starting image interpretation...")

    try:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in {".png", ".jpg", ".jpeg"}:
            raise ValueError("Unsupported image type")

        # Read image
        t0 = time.perf_counter()
        with open(file_path, "rb") as f:
            img_bytes = f.read()
        t1 = time.perf_counter()
        logger.info(f"[{filename}] read image: {t1 - t0:.2f}s")

        # Encode base64
        t0 = time.perf_counter()
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        t1 = time.perf_counter()
        logger.info(f"[{filename}] base64 encode: {t1 - t0:.2f}s")

        # OpenAI vision call
        t0 = time.perf_counter()
        resp = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/{ext[1:]};base64,{b64}"}}
            ]}],
            max_tokens=500
        )
        t1 = time.perf_counter()
        logger.info(f"[{filename}] OpenAI vision call: {t1 - t0:.2f}s")

        content = resp.choices[0].message.content

        # LightRAG insert
        t0 = time.perf_counter()
        await asyncio.to_thread(rag.insert, content, file_paths=[filename])
        t1 = time.perf_counter()
        logger.info(f"[{filename}] LightRAG.insert: {t1 - t0:.2f}s")

        # Final log
        total = time.perf_counter() - start_total
        logger.info(f"[{filename}] Total processing time: {total:.2f}s")

        # Callback
        if callback_url:
            await notify_callback(callback_url, {
                "filename": filename,
                "status": "success",
                "processing_time_seconds": round(total, 2),
                "response": content
            })

    except Exception as e:
        logger.error(f"[{filename}] Error: {e}")
        if callback_url:
            await notify_callback(callback_url, {
                "filename": filename,
                "status": "error",
                "error": str(e)
            })
            
async def process_webpage_background(
    url: str,
    rag: LightRAG,
    callback_url: Optional[str]
):
    start_total = time.perf_counter()
    logger.info(f"[webpage] Starting ingestion for: {url}")

    try:
        converter = DocumentConverter()

        # --- Docling conversion ---
        t0 = time.perf_counter()
        conv = converter.convert(url)
        text = conv.document.export_to_markdown()
        t1 = time.perf_counter()
        logger.info(f"[webpage] Docling conversion: {t1 - t0:.2f}s")

        # --- LightRAG insertion ---
        t0 = time.perf_counter()
        await asyncio.to_thread(rag.insert, text, file_paths=[url])
        t1 = time.perf_counter()
        logger.info(f"[webpage] LightRAG.insert: {t1 - t0:.2f}s")

        total = time.perf_counter() - start_total
        logger.info(f"[webpage] Total process time: {total:.2f}s")

        # --- Notify user ---
        if callback_url:
            await notify_callback(callback_url, {
                "url": url,
                "status": "success",
                "processing_time_seconds": round(total, 2)
            })

    except Exception as e:
        logger.error(f"[webpage] Error processing {url}: {e}")
        if callback_url:
            await notify_callback(callback_url, {
                "url": url,
                "status": "error",
                "error": str(e)
            })
            
async def process_query_background(
    query: str,
    mode: str,
    rag: LightRAG,
    task_id: str,
    callback_url: Optional[str] = None,
):
    logger.info(f"[{task_id}] Starting async query with mode='{mode}'")
    start_total = time.perf_counter()

    try:
        t0 = time.perf_counter()
        param = QueryParam(mode=mode)
        result = await asyncio.to_thread(rag.query, query, param=param)
        t1 = time.perf_counter()
        logger.info(f"[{task_id}] LightRAG.query executed in {t1 - t0:.2f}s")

        total = time.perf_counter() - start_total
        logger.info(f"[{task_id}] Total query processing time: {total:.2f}s")

        # Save result in memory
        await save_task_result(task_id, "done", json.dumps(result), total)

        if callback_url:
            await notify_callback(callback_url, {
                "task_id": task_id,
                "status": "done",
                "response": result,
                "processing_time_seconds": round(total, 2)
            })

        return result

    except Exception as e:
        logger.error(f"[{task_id}] Error during query: {e}")
        await save_task_result(task_id, "failed", str(e), 0)
        if callback_url:
            await notify_callback(callback_url, {
                "task_id": task_id,
                "status": "failed",
                "error": str(e)
            })
        raise