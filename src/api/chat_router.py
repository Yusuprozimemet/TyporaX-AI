"""
Chat API router for expert conversations
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import json
import httpx
import logging
from datetime import datetime

from src.experts.healthcare_expert import generate_patient_response as healthcare_response
from src.experts.it_backend_interviewer import generate_interviewer_response as interview_response
from src.experts.dutch_podcast_expert import generate_podcast_response, get_continuous_podcast_response
from src.utils.prompt_manager import get_prompt
from src.utils.utils import get_logger

router = APIRouter()
logger = get_logger("chat_router")

# Configuration
DEFAULT_MODEL = "google/gemma-2-9b-it"
FALLBACK_MODEL = "deepseek-ai/DeepSeek-R1"
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
HF_TOKEN = os.getenv("HF_TOKEN")


class ChatMessage(BaseModel):
    message: str
    expert: str = "healthcare"
    user_id: str = "anonymous"


class ChatHistory(BaseModel):
    role: str
    content: str


def detect_message_language(message: str) -> str:
    """Simple language detection"""
    dutch_words = ["het", "de", "een", "van", "is", "ik", "ben", "heb", "dit",
                   "dat", "met", "voor", "op", "aan", "door", "als", "maar", "niet", "en", "of"]
    english_words = ["the", "and", "but", "with", "have", "this", "that",
                     "from", "they", "know", "want", "been", "good", "much", "some"]

    words = message.lower().split()
    dutch_count = sum(1 for word in words if word in dutch_words)
    english_count = sum(1 for word in words if word in english_words)

    if dutch_count > english_count:
        return "dutch"
    elif english_count > dutch_count:
        return "english"
    else:
        return "mixed"


def clean_response_text(text: str) -> str:
    """Clean response text for audio generation"""
    import re

    # Remove markdown formatting
    text = re.sub(r'\*\*(.+?)\*\*', r'\\1', text)  # Bold
    text = re.sub(r'\*(.+?)\*', r'\\1', text)      # Italic
    text = re.sub(r'`(.+?)`', r'\\1', text)        # Code
    text = re.sub(r'#{1,6}\s*(.+)', r'\\1', text)  # Headers

    # Remove special characters but keep Dutch characters
    text = re.sub(
        r'[^\w\s\.,!?;:()\-\'\"àáâãäåèéêëìíîïòóôõöùúûüýÿñçÀÁÂÃÄÅÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜÝŸÑÇ]', '', text)

    # Clean up multiple spaces and newlines
    text = re.sub(r'\n+', '. ', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


async def generate_language_coach_response(message: str, conversation_history: List[Dict]) -> str:
    """Fallback language coach for general Dutch learning"""
    system_prompt = get_prompt('app', 'language_coach')

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history[-10:])  # Last 10 messages
    messages.append({"role": "user", "content": message})

    # Try models with fallback
    models_to_try = [DEFAULT_MODEL, FALLBACK_MODEL]

    for model in models_to_try:
        try:
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": 800,
                "temperature": 0.7
            }

            headers = {"Authorization": f"Bearer {HF_TOKEN}"}

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(HF_API_URL, json=payload, headers=headers)
                response.raise_for_status()

                result = response.json()
                return result["choices"][0]["message"]["content"]

        except Exception as e:
            logger.warning(f"Language coach with {model} failed: {e}")
            if model == models_to_try[-1]:  # Last model failed
                raise


def generate_fallback_response(expert: str, message: str) -> str:
    """Generate fallback response when AI is unavailable"""
    fallbacks = {
        "healthcare": "Bedankt voor je vraag over gezondheid. Ik help je graag verder met je Nederlands in medische situaties. Kun je me meer vertellen over je situatie?",
        "interview": "Dank je voor je interesse in IT-sollicitatiegesprekken. Ik help je graag met je technische Nederlands. Welk aspect van solliciteren wil je oefenen?",
        "language": "Welkom bij onze Nederlandse taalles! Ik help je graag je Nederlands te verbeteren. Wat wil je vandaag leren?"
    }
    return fallbacks.get(expert, fallbacks["language"])


def log_chat_interaction(user_id: str, expert: str, user_message: str, assistant_response: str):
    """Log chat interaction for analytics"""
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "expert": expert,
            "user_message": user_message,
            "assistant_response": assistant_response,
            "detected_language": detect_message_language(user_message)
        }

        user_dir = f"data/users/{user_id}"
        os.makedirs(user_dir, exist_ok=True)

        logs_file = f"{user_dir}/logs.txt"
        with open(logs_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    except Exception as e:
        logger.error(f"Failed to log interaction: {e}")


@router.post("/chat")
async def chat_endpoint(chat_data: ChatMessage):
    """Main chat endpoint for expert conversations"""
    try:
        message = chat_data.message.strip()
        expert = chat_data.expert
        user_id = chat_data.user_id

        if not message:
            raise HTTPException(
                status_code=400, detail="Message cannot be empty")

        logger.info(
            f"Chat request - User: {user_id}, Expert: {expert}, Message: {message[:50]}...")

        # Detect language for better processing
        detected_language = detect_message_language(message)

        # Get expert prompts from configuration
        system_prompt = get_prompt('app', f'expert_prompts.{expert}') or get_prompt(
            'app', 'expert_prompts.healthcare')

        # Use HuggingFace API for response generation
        if not HF_TOKEN:
            logger.warning("No HF_TOKEN found - using fallback response")
            fallback_response = generate_fallback_response(expert, message)
            return JSONResponse({"response": fallback_response})

        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
        }

        # Handle podcast expert specially
        if expert == "podcast":
            # Generate podcast response
            podcast_response = await generate_podcast_response(message, [])

            # Log the conversation
            log_chat_interaction(user_id, expert, message,
                                 podcast_response.get("message", ""))

            return JSONResponse({
                "response": podcast_response.get("message", ""),
                "speaker": podcast_response.get("speaker", "Host"),
                "speaker_key": podcast_response.get("speaker_key", "host1"),
                "voice": podcast_response.get("voice", "nl-NL-ColetteNeural"),
                "type": podcast_response.get("type", "podcast_message"),
                "audio_needed": podcast_response.get("audio_needed", True)
            })

        # Use chat completions format
        payload = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            "max_tokens": 150,
            "temperature": 0.7,
            "stream": False
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(HF_API_URL, headers=headers, json=payload, timeout=30.0)

            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    assistant_response = result["choices"][0]["message"]["content"].strip(
                    )

                    # Clean the response for better audio generation
                    cleaned_response = clean_response_text(assistant_response)

                    # Log the conversation
                    log_chat_interaction(
                        user_id, expert, message, assistant_response)

                    return JSONResponse({"response": cleaned_response})
                else:
                    # Fallback response
                    fallback_response = generate_fallback_response(
                        expert, message)
                    log_chat_interaction(
                        user_id, expert, message, fallback_response)
                    return JSONResponse({"response": fallback_response})
            else:
                # API error - use fallback
                logger.warning(
                    f"HuggingFace API error: {response.status_code}")
                fallback_response = generate_fallback_response(expert, message)
                log_chat_interaction(
                    user_id, expert, message, fallback_response)
                return JSONResponse({"response": fallback_response})

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        fallback_response = generate_fallback_response(
            chat_data.expert, chat_data.message)
        return JSONResponse({"response": fallback_response})


@router.post("/podcast/continue")
async def continue_podcast_endpoint():
    """Get next natural podcast response without user input"""
    try:
        podcast_response = await get_continuous_podcast_response()

        if not podcast_response:
            return JSONResponse({
                "response": "Podcast is niet actief",
                "type": "podcast_inactive"
            })

        return JSONResponse({
            "response": podcast_response.get("message", ""),
            "speaker": podcast_response.get("speaker", "Host"),
            "speaker_key": podcast_response.get("speaker_key", "host1"),
            "voice": podcast_response.get("voice", "nl-NL-ColetteNeural"),
            "type": podcast_response.get("type", "podcast_message"),
            "audio_needed": podcast_response.get("audio_needed", True)
        })

    except Exception as e:
        logger.error(f"Continue podcast error: {e}")
        return JSONResponse({
            "response": "Er ging iets mis met de podcast",
            "type": "podcast_error"
        })


@router.post("/generate_speech")
async def generate_speech_endpoint(request: dict):
    """Generate speech from text using edge-tts"""
    try:
        text = request.get("text", "")
        language = request.get("language", "dutch")
        voice = request.get("voice", None)  # Optional specific voice

        logger.info(
            f"🎙️ Speech request - Text: '{text[:50]}...', Language: {language}, Voice: {voice}")

        if not text:
            raise HTTPException(status_code=400, detail="Text is required")

        # Import audio utility
        from src.utils.audio import AudioEngine

        # Generate speech
        audio_engine = AudioEngine()
        if voice:
            logger.info(f"🔊 Using specific voice: {voice}")
            # Use specific voice if provided
            audio_bytes = await audio_engine.generate_speech_bytes_with_voice(text, voice)
        else:
            logger.info(f"🔊 Using default voice for language: {language}")
            # Use default voice for language
            audio_bytes = await audio_engine.generate_speech_bytes(text, language)

        if audio_bytes:
            response_obj = {
                "success": True,
                "audio_data": audio_bytes.hex() if isinstance(audio_bytes, bytes) else str(audio_bytes),
                "format": "mp3"
            }
            logger.info(f"Speech response: {str(response_obj)[:120]}")
            return JSONResponse(response_obj)
        else:
            raise HTTPException(
                status_code=500, detail="Speech generation failed")

    except Exception as e:
        logger.error(f"Speech generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
