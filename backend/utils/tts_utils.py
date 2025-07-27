"""
Text-to-Speech utilities for Study4Me backend

This module contains utilities for text-to-speech generation using ElevenLabs API.
Provides functions for voice listing, audio generation, and TTS management.

Functions included:
- ElevenLabs API client management
- Voice listing and management
- Text-to-speech audio generation
- Audio file handling and storage
"""

import os
import io
import logging
import requests
import uuid
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException

# Set up logging
logger = logging.getLogger(__name__)

# ElevenLabs API configuration
ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"
ELEVENLABS_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

class ElevenLabsError(Exception):
    """Custom exception for ElevenLabs API errors"""
    pass

def get_elevenlabs_headers(api_key: str) -> Dict[str, str]:
    """
    Get headers for ElevenLabs API requests with API key
    """
    headers = ELEVENLABS_HEADERS.copy()
    headers["xi-api-key"] = api_key
    return headers

async def list_voices(api_key: str) -> List[Dict[str, Any]]:
    """
    List all available voices from ElevenLabs API
    
    Args:
        api_key: ElevenLabs API key
        
    Returns:
        List of voice objects with metadata
        
    Raises:
        ElevenLabsError: If API request fails
    """
    if not api_key:
        raise ElevenLabsError("ElevenLabs API key is required")
    
    try:
        logger.info("🎙️ Fetching voices from ElevenLabs API...")
        
        response = requests.get(
            "https://api.elevenlabs.io/v2/voices",
            headers=get_elevenlabs_headers(api_key),
            timeout=10
        )
        
        if response.status_code == 401:
            logger.error("❌ ElevenLabs API authentication failed")
            raise ElevenLabsError("Invalid ElevenLabs API key")
        elif response.status_code == 429:
            logger.error("❌ ElevenLabs API rate limit exceeded")
            raise ElevenLabsError("Rate limit exceeded. Please try again later.")
        elif response.status_code != 200:
            logger.error(f"❌ ElevenLabs API error: {response.status_code}")
            raise ElevenLabsError(f"API request failed with status {response.status_code}")
        
        data = response.json()
        voices = data.get("voices", [])
        
        logger.info(f"✅ Retrieved {len(voices)} voices from ElevenLabs")
        
        # Format voice data for our API
        formatted_voices = []
        for voice in voices:
            formatted_voice = {
                "voice_id": voice.get("voice_id"),
                "name": voice.get("name"),
                "category": voice.get("category", "Unknown"),
                "description": voice.get("description"),
                "preview_url": voice.get("preview_url"),
                "settings": voice.get("settings"),
                "labels": voice.get("labels", {}),
                "available_for_tiers": voice.get("available_for_tiers", []),
                "high_quality_base_model_ids": voice.get("high_quality_base_model_ids", [])
            }
            formatted_voices.append(formatted_voice)
        
        return formatted_voices
        
    except requests.exceptions.Timeout:
        logger.error("❌ ElevenLabs API request timed out")
        raise ElevenLabsError("Request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        logger.error("❌ Failed to connect to ElevenLabs API")
        raise ElevenLabsError("Failed to connect to ElevenLabs API")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ ElevenLabs API request failed: {str(e)}")
        raise ElevenLabsError(f"API request failed: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error listing voices: {str(e)}")
        raise ElevenLabsError(f"Unexpected error: {str(e)}")

async def text_to_speech(
    text: str,
    voice_id: str,
    api_key: str,
    model_id: str = "eleven_multilingual_v2",
    voice_settings: Optional[Dict[str, float]] = None,
    output_format: str = "mp3_44100_128",
    language_code: Optional[str] = None,
    enable_logging: bool = True
) -> Tuple[bytes, str]:
    """
    Convert text to speech using ElevenLabs API
    
    Args:
        text: Text content to convert to speech
        voice_id: ElevenLabs voice ID to use
        api_key: ElevenLabs API key
        model_id: Model to use for TTS (default: eleven_multilingual_v2)
        output_format: Audio output format (default: mp3_44100_128)
        language_code: Optional language code to enforce
        enable_logging: Whether to enable request logging (default: True)
        voice_settings: Voice settings (stability, similarity_boost, etc.)
        
    Returns:
        Tuple of (audio_bytes, filename)
        
    Raises:
        ElevenLabsError: If TTS generation fails
    """
    if not api_key:
        raise ElevenLabsError("ElevenLabs API key is required")
    
    if not text or not text.strip():
        raise ElevenLabsError("Text content is required")
    
    if not voice_id:
        raise ElevenLabsError("Voice ID is required")
    
    # Default voice settings
    default_settings = {
        "stability": 0.5,
        "similarity_boost": 0.5,
        "style": 0.0,
        "use_speaker_boost": True
    }
    
    if voice_settings:
        default_settings.update(voice_settings)
    
    try:
        logger.info(f"🎙️ Generating TTS audio for {len(text)} characters...")
        logger.info(f"   Voice ID: {voice_id}")
        logger.info(f"   Model: {model_id}")
        logger.info(f"   Output format: {output_format}")
        logger.info(f"   Language: {language_code or 'auto-detect'}")
        logger.info(f"   Logging enabled: {enable_logging}")
        logger.info(f"   Settings: {default_settings}")
        
        # Prepare request payload
        payload = {
            "text": text.strip(),
            "model_id": model_id,
            "voice_settings": default_settings,
            "output_format": output_format
        }
        
        # Add optional parameters
        if language_code:
            payload["language_code"] = language_code
            
        # Add query parameters
        query_params = {}
        if not enable_logging:
            query_params["enable_logging"] = "false"
            
        url = f"{ELEVENLABS_API_BASE}/text-to-speech/{voice_id}"
        if query_params:
            from urllib.parse import urlencode
            url += "?" + urlencode(query_params)
        
        # Make TTS API request
        response = requests.post(
            url,
            json=payload,
            headers=get_elevenlabs_headers(api_key),
            timeout=60  # Longer timeout for TTS generation
        )
        
        if response.status_code == 401:
            logger.error("❌ ElevenLabs API authentication failed")
            raise ElevenLabsError("Invalid ElevenLabs API key")
        elif response.status_code == 400:
            logger.error("❌ ElevenLabs API bad request")
            error_detail = response.json().get("detail", {})
            if isinstance(error_detail, dict):
                message = error_detail.get("message", "Bad request")
            else:
                message = str(error_detail)
            raise ElevenLabsError(f"Bad request: {message}")
        elif response.status_code == 422:
            logger.error("❌ ElevenLabs API validation error")
            raise ElevenLabsError("Invalid voice ID or parameters")
        elif response.status_code == 429:
            logger.error("❌ ElevenLabs API rate limit exceeded")
            raise ElevenLabsError("Rate limit exceeded. Please try again later.")
        elif response.status_code != 200:
            logger.error(f"❌ ElevenLabs API error: {response.status_code}")
            try:
                error_data = response.json()
                error_message = error_data.get("detail", {}).get("message", f"API error {response.status_code}")
            except:
                error_message = f"API error {response.status_code}"
            raise ElevenLabsError(error_message)
        
        # Check if response is audio
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("audio/"):
            logger.error(f"❌ Unexpected content type: {content_type}")
            raise ElevenLabsError("Invalid response format from TTS API")
        
        audio_data = response.content
        
        if not audio_data:
            logger.error("❌ Empty audio response from ElevenLabs")
            raise ElevenLabsError("Empty audio response")
        
        # Generate filename
        audio_id = str(uuid.uuid4())[:8]
        filename = f"tts_audio_{audio_id}.mp3"
        
        logger.info(f"✅ TTS audio generated successfully:")
        logger.info(f"   Audio size: {len(audio_data)} bytes")
        logger.info(f"   Filename: {filename}")
        logger.info(f"   Content type: {content_type}")
        
        return audio_data, filename
        
    except requests.exceptions.Timeout:
        logger.error("❌ ElevenLabs TTS request timed out")
        raise ElevenLabsError("TTS generation timed out. Try with shorter text.")
    except requests.exceptions.ConnectionError:
        logger.error("❌ Failed to connect to ElevenLabs API")
        raise ElevenLabsError("Failed to connect to ElevenLabs API")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ ElevenLabs TTS request failed: {str(e)}")
        raise ElevenLabsError(f"TTS request failed: {str(e)}")
    except ElevenLabsError:
        raise  # Re-raise our custom errors
    except Exception as e:
        logger.error(f"❌ Unexpected error in TTS generation: {str(e)}")
        raise ElevenLabsError(f"Unexpected error: {str(e)}")

def validate_voice_settings(settings: Dict[str, Any]) -> Dict[str, float]:
    """
    Validate and sanitize voice settings
    
    Args:
        settings: Raw voice settings dictionary
        
    Returns:
        Validated settings dictionary
        
    Raises:
        ValueError: If settings are invalid
    """
    validated = {}
    
    # Stability: 0.0 to 1.0
    if "stability" in settings:
        stability = float(settings["stability"])
        if not 0.0 <= stability <= 1.0:
            raise ValueError("Stability must be between 0.0 and 1.0")
        validated["stability"] = stability
    
    # Similarity boost: 0.0 to 1.0
    if "similarity_boost" in settings:
        similarity_boost = float(settings["similarity_boost"])
        if not 0.0 <= similarity_boost <= 1.0:
            raise ValueError("Similarity boost must be between 0.0 and 1.0")
        validated["similarity_boost"] = similarity_boost
    
    # Style: 0.0 to 1.0
    if "style" in settings:
        style = float(settings["style"])
        if not 0.0 <= style <= 1.0:
            raise ValueError("Style must be between 0.0 and 1.0")
        validated["style"] = style
    
    # Use speaker boost: boolean
    if "use_speaker_boost" in settings:
        validated["use_speaker_boost"] = bool(settings["use_speaker_boost"])
    
    return validated

def get_recommended_voice_settings(voice_type: str = "default") -> Dict[str, float]:
    """
    Get recommended voice settings for different use cases
    
    Args:
        voice_type: Type of voice usage (default, lecture, conversation, etc.)
        
    Returns:
        Recommended settings dictionary
    """
    settings = {
        "default": {
            "stability": 0.5,
            "similarity_boost": 0.5,
            "style": 0.0,
            "use_speaker_boost": True
        },
        "lecture": {
            "stability": 0.7,  # More stable for educational content
            "similarity_boost": 0.6,
            "style": 0.2,  # Slightly more expressive
            "use_speaker_boost": True
        },
        "conversation": {
            "stability": 0.4,  # More dynamic
            "similarity_boost": 0.7,
            "style": 0.3,  # More expressive
            "use_speaker_boost": True
        },
        "audiobook": {
            "stability": 0.8,  # Very stable for long content
            "similarity_boost": 0.5,
            "style": 0.1,  # Minimal style variation
            "use_speaker_boost": True
        }
    }
    
    return settings.get(voice_type, settings["default"])