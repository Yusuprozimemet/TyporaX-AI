# tools/audio.py
import edge_tts
import asyncio
import os


async def _tts(text, output_path, voice="ja-JP-NanamiNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def generate_audio(sentences, user_id, target_language="japanese"):
    """Generate audio for the given sentences in the specified language."""
    # Language-specific voice models
    voice_models = {
        "japanese": "ja-JP-NanamiNeural",
        "dutch": "nl-NL-ColetteNeural",
        "chinese": "zh-CN-XiaoxiaoNeural"
    }

    voice = voice_models.get(target_language, "ja-JP-NanamiNeural")
    text = " ".join(sentences)
    path = f"data/users/{user_id}/lesson_audio.mp3"

    try:
        # Check if event loop is already running (e.g., in FastAPI)
        try:
            loop = asyncio.get_running_loop()
            # If we get here, there's already a loop running
            # We need to run in a thread pool executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(_run_tts_sync, text, path, voice)
                future.result(timeout=30)
        except RuntimeError:
            # No event loop running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_tts(text, path, voice))
            loop.close()
    except Exception as e:
        print(f"TTS failed: {e}")
        return None
    return path


def _run_tts_sync(text, path, voice):
    """Synchronous wrapper to run TTS in a separate thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_tts(text, path, voice))
    finally:
        loop.close()
