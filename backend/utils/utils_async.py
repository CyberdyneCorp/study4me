import time
import asyncio
import os
import base64
from typing import Optional
from openai import OpenAI
from openai import AuthenticationError, RateLimitError, APIError
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

        except AuthenticationError as e:
            error_msg = f"OpenAI authentication failed: {str(e)}"
            logger.error(f"[{filename}] {error_msg}")
            logger.error("Please check your OPENAI_API_KEY environment variable.")
            if callback_url:
                await notify_callback(callback_url, {
                    "filename": filename,
                    "status": "error",
                    "error": error_msg,
                    "error_type": "authentication"
                })
        except RateLimitError as e:
            error_msg = f"OpenAI rate limit exceeded: {str(e)}"
            logger.warning(f"[{filename}] {error_msg}")
            if callback_url:
                await notify_callback(callback_url, {
                    "filename": filename,
                    "status": "error",
                    "error": error_msg,
                    "error_type": "rate_limit"
                })
        except APIError as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(f"[{filename}] {error_msg}")
            if callback_url:
                await notify_callback(callback_url, {
                    "filename": filename,
                    "status": "error",
                    "error": error_msg,
                    "error_type": "api_error"
                })
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[{filename}] Unexpected error: {error_msg}")
            if callback_url:
                await notify_callback(callback_url, {
                    "filename": filename,
                    "status": "error",
                    "error": error_msg,
                    "error_type": "unexpected"
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

    except AuthenticationError as e:
        error_msg = f"OpenAI authentication failed: {str(e)}"
        logger.error(f"[{filename}] {error_msg}")
        logger.error("Please check your OPENAI_API_KEY environment variable.")
        if callback_url:
            await notify_callback(callback_url, {
                "filename": filename,
                "status": "error",
                "error": error_msg,
                "error_type": "authentication"
            })
    except RateLimitError as e:
        error_msg = f"OpenAI rate limit exceeded: {str(e)}"
        logger.warning(f"[{filename}] {error_msg}")
        if callback_url:
            await notify_callback(callback_url, {
                "filename": filename,
                "status": "error",
                "error": error_msg,
                "error_type": "rate_limit"
            })
    except APIError as e:
        error_msg = f"OpenAI API error: {str(e)}"
        logger.error(f"[{filename}] {error_msg}")
        if callback_url:
            await notify_callback(callback_url, {
                "filename": filename,
                "status": "error",
                "error": error_msg,
                "error_type": "api_error"
            })
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[{filename}] Unexpected error: {error_msg}")
        if callback_url:
            await notify_callback(callback_url, {
                "filename": filename,
                "status": "error",
                "error": error_msg,
                "error_type": "unexpected"
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

    except AuthenticationError as e:
        error_msg = f"OpenAI authentication failed: {str(e)}"
        logger.error(f"[webpage] {error_msg}")
        logger.error("Please check your OPENAI_API_KEY environment variable.")
        if callback_url:
            await notify_callback(callback_url, {
                "url": url,
                "status": "error",
                "error": error_msg,
                "error_type": "authentication"
            })
    except RateLimitError as e:
        error_msg = f"OpenAI rate limit exceeded: {str(e)}"
        logger.warning(f"[webpage] {error_msg}")
        if callback_url:
            await notify_callback(callback_url, {
                "url": url,
                "status": "error",
                "error": error_msg,
                "error_type": "rate_limit"
            })
    except APIError as e:
        error_msg = f"OpenAI API error: {str(e)}"
        logger.error(f"[webpage] {error_msg}")
        if callback_url:
            await notify_callback(callback_url, {
                "url": url,
                "status": "error",
                "error": error_msg,
                "error_type": "api_error"
            })
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[webpage] Unexpected error processing {url}: {error_msg}")
        if callback_url:
            await notify_callback(callback_url, {
                "url": url,
                "status": "error",
                "error": error_msg,
                "error_type": "unexpected"
            })
            
async def process_query_background(
    query: str,
    mode: str,
    rag: LightRAG,
    task_id: str,
    callback_url: Optional[str] = None,
):
    short_id = task_id[:8]
    logger.info(f"🧠 [bg-{short_id}] Starting background query processing")
    logger.info(f"📊 [bg-{short_id}] Query stats: {len(query)} chars, mode='{mode}'")
    
    start_total = time.perf_counter()

    try:
        # Phase 1: LightRAG Query Processing
        logger.info(f"⚙️ [bg-{short_id}] Phase 1: Initializing LightRAG query...")
        t0 = time.perf_counter()
        
        param = QueryParam(mode=mode)
        logger.info(f"🔍 [bg-{short_id}] Executing RAG query with mode '{mode}'...")
        
        result = await asyncio.to_thread(rag.query, query, param=param)
        
        t1 = time.perf_counter()
        rag_time = t1 - t0
        logger.info(f"✅ [bg-{short_id}] LightRAG query completed: {rag_time:.2f}s")

        # Phase 2: Result Processing
        logger.info(f"📝 [bg-{short_id}] Phase 2: Processing results...")
        t2 = time.perf_counter()
        
        total = time.perf_counter() - start_total
        result_length = len(str(result)) if result else 0
        result_json = json.dumps(result)
        
        # Save result in database
        await save_task_result(task_id, "done", result_json, total)
        t3 = time.perf_counter()
        db_time = t3 - t2
        
        logger.info(f"💾 [bg-{short_id}] Result saved to database: {db_time:.3f}s")

        # Phase 3: Callback Notification
        if callback_url:
            logger.info(f"📞 [bg-{short_id}] Phase 3: Sending callback notification...")
            t4 = time.perf_counter()
            
            await notify_callback(callback_url, {
                "task_id": task_id,
                "status": "done",
                "response": result,
                "processing_time_seconds": round(total, 2)
            })
            
            t5 = time.perf_counter()
            callback_time = t5 - t4
            logger.info(f"📡 [bg-{short_id}] Callback sent: {callback_time:.3f}s")
        else:
            logger.info(f"🔕 [bg-{short_id}] No callback URL provided")

        # Final summary
        logger.info(f"🎉 [bg-{short_id}] Background query completed successfully:")
        logger.info(f"   ⏱️  Total time: {total:.2f}s")
        logger.info(f"   🧠 LightRAG time: {rag_time:.2f}s ({(rag_time/total)*100:.1f}%)")
        logger.info(f"   💾 Database time: {db_time:.3f}s ({(db_time/total)*100:.1f}%)")
        if callback_url:
            logger.info(f"   📡 Callback time: {callback_time:.3f}s ({(callback_time/total)*100:.1f}%)")
        logger.info(f"   📊 Result length: {result_length} chars")
        logger.info(f"   🔧 Mode: {mode}")

        return result

    except AuthenticationError as e:
        total_time = time.perf_counter() - start_total
        error_msg = f"OpenAI authentication failed: {str(e)}"
        logger.error(f"❌ [bg-{short_id}] {error_msg} (after {total_time:.2f}s)")
        logger.error(f"🔑 [bg-{short_id}] Please check your OPENAI_API_KEY environment variable.")
        await save_task_result(task_id, "failed", error_msg, total_time)
        if callback_url:
            await notify_callback(callback_url, {
                "task_id": task_id,
                "status": "failed",
                "error": error_msg,
                "error_type": "authentication",
                "processing_time_seconds": round(total_time, 2)
            })
        raise
    except RateLimitError as e:
        total_time = time.perf_counter() - start_total
        error_msg = f"OpenAI rate limit exceeded: {str(e)}"
        logger.warning(f"⚠️ [bg-{short_id}] {error_msg} (after {total_time:.2f}s)")
        logger.warning(f"💰 [bg-{short_id}] Consider upgrading your OpenAI plan or try again later.")
        await save_task_result(task_id, "failed", error_msg, total_time)
        if callback_url:
            await notify_callback(callback_url, {
                "task_id": task_id,
                "status": "failed",
                "error": error_msg,
                "error_type": "rate_limit",
                "processing_time_seconds": round(total_time, 2)
            })
        raise
    except APIError as e:
        total_time = time.perf_counter() - start_total
        error_msg = f"OpenAI API error: {str(e)}"
        logger.error(f"🔴 [bg-{short_id}] {error_msg} (after {total_time:.2f}s)")
        logger.error(f"🌐 [bg-{short_id}] This may be a temporary OpenAI service issue.")
        await save_task_result(task_id, "failed", error_msg, total_time)
        if callback_url:
            await notify_callback(callback_url, {
                "task_id": task_id,
                "status": "failed",
                "error": error_msg,
                "error_type": "api_error",
                "processing_time_seconds": round(total_time, 2)
            })
        raise
    except Exception as e:
        total_time = time.perf_counter() - start_total
        error_msg = str(e)
        logger.error(f"💥 [bg-{short_id}] Unexpected error: {error_msg} (after {total_time:.2f}s)")
        logger.error(f"🔍 [bg-{short_id}] Error type: {type(e).__name__}")
        logger.error(f"📊 [bg-{short_id}] Query length: {len(query)} chars, mode: {mode}")
        await save_task_result(task_id, "failed", error_msg, total_time)
        if callback_url:
            await notify_callback(callback_url, {
                "task_id": task_id,
                "status": "failed",
                "error": error_msg,
                "error_type": "unexpected",
                "processing_time_seconds": round(total_time, 2)
            })
        raise