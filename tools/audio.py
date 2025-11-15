# tools/audio.py
import edge_tts
import asyncio
import os


async def _tts(text, output_path, voice="ja-JP-NanamiNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def generate_audio(sentences, user_id):
    text = " ".join(sentences)
    path = f"data/users/{user_id}/lesson_audio.mp3"
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_tts(text, path))
        loop.close()
    except Exception as e:
        print(f"TTS failed: {e}")
        return None
    return path
