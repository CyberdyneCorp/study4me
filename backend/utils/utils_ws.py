import httpx
import logging

logger = logging.getLogger(__name__)

async def notify_callback(callback_url: str, payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(callback_url, json=payload)
        logger.info(f"Callback sent to {callback_url}")
    except Exception as e:
        logger.warning(f"Failed to call callback URL {callback_url}: {e}")