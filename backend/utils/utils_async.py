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
from .db_async import save_task_result, create_content_item
import json

logger = logging.getLogger(__name__)

# Import shutdown event from main module
def get_shutdown_event():
    """Get shutdown event from main module to avoid circular imports"""
    try:
        import sys
        if 'main' in sys.modules:
            return sys.modules['main'].SHUTDOWN_EVENT
    except (ImportError, AttributeError):
        pass
    return None

async def process_uploaded_documents(saved_paths, rag: LightRAG, callback_url: Optional[str], 
                                   study_topic_id: str = None, content_items: list = None):
    shutdown_event = get_shutdown_event()
    converter = DocumentConverter()

    # Create a mapping of file paths to content items if provided
    content_items_map = {}
    if content_items:
        for item in content_items:
            content_items_map[item['file_path']] = item

    for filename, file_path in saved_paths:
        # Check for shutdown signal or cancellation
        if shutdown_event and shutdown_event.is_set():
            logger.info(f"[{filename}] Shutdown signal received, stopping processing")
            return
        
        # Check for asyncio cancellation
        try:
            await asyncio.sleep(0)  # Yield control and check for cancellation
        except asyncio.CancelledError:
            logger.info(f"[{filename}] Task cancelled, stopping processing")
            raise
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

            # --- Save content item to database ---
            if study_topic_id and file_path in content_items_map:
                content_item = content_items_map[file_path]
                try:
                    await create_content_item(
                        content_id=content_item['content_id'],
                        study_topic_id=study_topic_id,
                        content_type='document',
                        title=filename,
                        content=text,
                        source_url=None,
                        file_path=file_path,
                        metadata=json.dumps({
                            "file_size": os.path.getsize(file_path),
                            "processing_time": round(t1 - t0, 2),
                            "docling_version": "latest"
                        })
                    )
                    logger.info(f"[{filename}] Content item saved to database (ID: {content_item['content_id'][:8]})")
                except Exception as db_error:
                    logger.error(f"[{filename}] Failed to save content item: {db_error}")

            total = time.perf_counter() - start_total
            logger.info(f"[{filename}] Total processing time: {total:.2f}s")

            if callback_url:
                await notify_callback(callback_url, {
                    "filename": filename,
                    "status": "success",
                    "processing_time_seconds": round(total, 2),
                    "study_topic_id": study_topic_id,
                    "content_id": content_items_map[file_path]['content_id'] if file_path in content_items_map else None
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
    shutdown_event = get_shutdown_event()
    if shutdown_event and shutdown_event.is_set():
        logger.info(f"[{filename}] Shutdown signal received, cancelling image processing")
        return
        
    # Check for asyncio cancellation
    try:
        await asyncio.sleep(0)  # Yield control and check for cancellation
    except asyncio.CancelledError:
        logger.info(f"[{filename}] Task cancelled, stopping image processing")
        raise
        
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
    callback_url: Optional[str],
    study_topic_id: str = None,
    content_id: str = None
):
    shutdown_event = get_shutdown_event()
    if shutdown_event and shutdown_event.is_set():
        logger.info(f"[webpage] Shutdown signal received, cancelling webpage processing")
        return
        
    # Check for asyncio cancellation
    try:
        await asyncio.sleep(0)  # Yield control and check for cancellation
    except asyncio.CancelledError:
        logger.info(f"[webpage] Task cancelled, stopping webpage processing")
        raise
        
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

        # --- Save content item to database ---
        if study_topic_id and content_id:
            try:
                await create_content_item(
                    content_id=content_id,
                    study_topic_id=study_topic_id,
                    content_type='webpage',
                    title=url,
                    content=text,
                    source_url=url,
                    file_path=None,
                    metadata=json.dumps({
                        "processing_time": round(t1 - t0, 2),
                        "docling_version": "latest",
                        "content_length": len(text)
                    })
                )
                logger.info(f"[webpage] Content item saved to database (ID: {content_id[:8]})")
            except Exception as db_error:
                logger.error(f"[webpage] Failed to save content item: {db_error}")

        total = time.perf_counter() - start_total
        logger.info(f"[webpage] Total process time: {total:.2f}s")

        # --- Notify user ---
        if callback_url:
            await notify_callback(callback_url, {
                "url": url,
                "status": "success",
                "processing_time_seconds": round(total, 2),
                "study_topic_id": study_topic_id,
                "content_id": content_id
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
    shutdown_event = get_shutdown_event()
    short_id = task_id[:8]
    
    if shutdown_event and shutdown_event.is_set():
        logger.info(f"🧠 [bg-{short_id}] Shutdown signal received, cancelling query processing")
        return
    
    # Check for asyncio cancellation
    try:
        await asyncio.sleep(0)  # Yield control and check for cancellation
    except asyncio.CancelledError:
        logger.info(f"🧠 [bg-{short_id}] Task cancelled, stopping query processing")
        raise
    
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

async def process_youtube_background(
    url: str,
    rag: LightRAG,
    task_id: str,
    callback_url: Optional[str] = None,
):
    """Process YouTube video transcript and add to LightRAG"""
    shutdown_event = get_shutdown_event()
    short_id = task_id[:8]
    
    if shutdown_event and shutdown_event.is_set():
        logger.info(f"📺 [yt-{short_id}] Shutdown signal received, cancelling YouTube processing")
        return
    
    # Check for asyncio cancellation
    try:
        await asyncio.sleep(0)  # Yield control and check for cancellation
    except asyncio.CancelledError:
        logger.info(f"📺 [yt-{short_id}] Task cancelled, stopping YouTube processing")
        raise
    
    logger.info(f"📺 [yt-{short_id}] Starting YouTube video processing")
    logger.info(f"🔗 [yt-{short_id}] URL: {url}")
    
    start_total = time.perf_counter()

    try:
        # Import here to avoid circular imports
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from youtube_service import get_youtube_transcript
        
        # Phase 1: Extract transcript from YouTube
        logger.info(f"⚙️ [yt-{short_id}] Phase 1: Extracting YouTube transcript...")
        t0 = time.perf_counter()
        
        try:
            transcript_response = await get_youtube_transcript(url, "en")
            transcript_text = transcript_response.transcript
            video_id = transcript_response.video_id
            language = transcript_response.language
            available_languages = transcript_response.available_languages
            
            t1 = time.perf_counter()
            extract_time = t1 - t0
            logger.info(f"✅ [yt-{short_id}] Transcript extracted: {extract_time:.2f}s")
            logger.info(f"📊 [yt-{short_id}] Video ID: {video_id} | Language: {language}")
            logger.info(f"📝 [yt-{short_id}] Transcript length: {len(transcript_text)} chars")
            logger.info(f"🌐 [yt-{short_id}] Available languages: {len(available_languages)}")
            
        except Exception as e:
            logger.error(f"❌ [yt-{short_id}] Failed to extract transcript: {str(e)}")
            raise Exception(f"YouTube transcript extraction failed: {str(e)}")

        # Phase 2: Process with LightRAG
        logger.info(f"🧠 [yt-{short_id}] Phase 2: Processing with LightRAG...")
        t2 = time.perf_counter()
        
        # Create formatted content for LightRAG
        formatted_content = f"""YouTube Video Transcript

Video ID: {video_id}
Language: {language}
URL: {url}
Available Languages: {', '.join(available_languages)}

Transcript:
{transcript_text}
"""
        
        # Insert into LightRAG
        await asyncio.to_thread(rag.insert, formatted_content, file_paths=[url])
        
        t3 = time.perf_counter()
        rag_time = t3 - t2
        logger.info(f"✅ [yt-{short_id}] LightRAG processing completed: {rag_time:.2f}s")

        # Phase 3: Save results and callback
        logger.info(f"📝 [yt-{short_id}] Phase 3: Finalizing results...")
        t4 = time.perf_counter()
        
        total = time.perf_counter() - start_total
        
        result_data = {
            "video_id": video_id,
            "url": url,
            "language": language,
            "available_languages": available_languages,
            "transcript_length": len(transcript_text),
            "processing_time_seconds": round(total, 2)
        }
        
        # Save result in database
        await save_task_result(task_id, "done", json.dumps(result_data), total)
        t5 = time.perf_counter()
        db_time = t5 - t4
        
        logger.info(f"💾 [yt-{short_id}] Result saved to database: {db_time:.3f}s")

        # Phase 4: Callback notification
        if callback_url:
            logger.info(f"📞 [yt-{short_id}] Phase 4: Sending callback notification...")
            t6 = time.perf_counter()
            
            await notify_callback(callback_url, {
                "task_id": task_id,
                "status": "success",
                "video_id": video_id,
                "url": url,
                "language": language,
                "transcript_length": len(transcript_text),
                "processing_time_seconds": round(total, 2)
            })
            
            t7 = time.perf_counter()
            callback_time = t7 - t6
            logger.info(f"📡 [yt-{short_id}] Callback sent: {callback_time:.3f}s")
        else:
            logger.info(f"🔕 [yt-{short_id}] No callback URL provided")
            callback_time = 0

        # Final summary
        logger.info(f"🎉 [yt-{short_id}] YouTube processing completed successfully:")
        logger.info(f"   ⏱️  Total time: {total:.2f}s")
        logger.info(f"   📺 Transcript extraction: {extract_time:.2f}s ({(extract_time/total)*100:.1f}%)")
        logger.info(f"   🧠 LightRAG processing: {rag_time:.2f}s ({(rag_time/total)*100:.1f}%)")
        logger.info(f"   💾 Database time: {db_time:.3f}s ({(db_time/total)*100:.1f}%)")
        if callback_url:
            logger.info(f"   📡 Callback time: {callback_time:.3f}s ({(callback_time/total)*100:.1f}%)")
        logger.info(f"   📊 Video ID: {video_id}")
        logger.info(f"   📝 Transcript: {len(transcript_text)} chars")
        logger.info(f"   🌐 Language: {language}")

        return result_data

    except AuthenticationError as e:
        total_time = time.perf_counter() - start_total
        error_msg = f"OpenAI authentication failed: {str(e)}"
        logger.error(f"❌ [yt-{short_id}] {error_msg} (after {total_time:.2f}s)")
        logger.error(f"🔑 [yt-{short_id}] Please check your OPENAI_API_KEY environment variable.")
        await save_task_result(task_id, "failed", error_msg, total_time)
        if callback_url:
            await notify_callback(callback_url, {
                "task_id": task_id,
                "status": "error",
                "error": error_msg,
                "error_type": "authentication",
                "processing_time_seconds": round(total_time, 2)
            })
        raise
    except RateLimitError as e:
        total_time = time.perf_counter() - start_total
        error_msg = f"OpenAI rate limit exceeded: {str(e)}"
        logger.warning(f"⚠️ [yt-{short_id}] {error_msg} (after {total_time:.2f}s)")
        logger.warning(f"💰 [yt-{short_id}] Consider upgrading your OpenAI plan or try again later.")
        await save_task_result(task_id, "failed", error_msg, total_time)
        if callback_url:
            await notify_callback(callback_url, {
                "task_id": task_id,
                "status": "error",
                "error": error_msg,
                "error_type": "rate_limit",
                "processing_time_seconds": round(total_time, 2)
            })
        raise
    except APIError as e:
        total_time = time.perf_counter() - start_total
        error_msg = f"OpenAI API error: {str(e)}"
        logger.error(f"🔴 [yt-{short_id}] {error_msg} (after {total_time:.2f}s)")
        logger.error(f"🌐 [yt-{short_id}] This may be a temporary OpenAI service issue.")
        await save_task_result(task_id, "failed", error_msg, total_time)
        if callback_url:
            await notify_callback(callback_url, {
                "task_id": task_id,
                "status": "error",
                "error": error_msg,
                "error_type": "api_error",
                "processing_time_seconds": round(total_time, 2)
            })
        raise
    except Exception as e:
        total_time = time.perf_counter() - start_total
        error_msg = str(e)
        logger.error(f"💥 [yt-{short_id}] Unexpected error: {error_msg} (after {total_time:.2f}s)")
        logger.error(f"🔍 [yt-{short_id}] Error type: {type(e).__name__}")
        logger.error(f"🔗 [yt-{short_id}] URL: {url}")
        await save_task_result(task_id, "failed", error_msg, total_time)
        if callback_url:
            await notify_callback(callback_url, {
                "task_id": task_id,
                "status": "error",
                "error": error_msg,
                "error_type": "unexpected",
                "processing_time_seconds": round(total_time, 2)
            })
        raise