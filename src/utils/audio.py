# tools/audio.py
# ================================================
# Enhanced Audio System with Real-time TTS and STT
# ================================================

import edge_tts
import asyncio
import os
import tempfile
import speech_recognition as sr
from typing import Optional, List
import threading


class AudioEngine:
    """
    Unified audio engine for text-to-speech and speech-to-text
    """

    # Voice models for different languages
    VOICE_MODELS = {
        "japanese": "ja-JP-NanamiNeural",
        "dutch": "nl-NL-ColetteNeural",
        "chinese": "zh-CN-XiaoxiaoNeural",
        "english": "en-US-JennyNeural",
        "german": "de-DE-KatjaNeural",
        "french": "fr-FR-DeniseNeural",
        "spanish": "es-ES-ElviraNeural"
    }

    # Speech recognition language codes
    STT_LANGUAGES = {
        "japanese": "ja-JP",
        "dutch": "nl-NL",
        "chinese": "zh-CN",
        "english": "en-US",
        "german": "de-DE",
        "french": "fr-FR",
        "spanish": "es-ES"
    }

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self._calibrated = False

    def calibrate_microphone(self, duration: float = 2.0):
        """
        Calibrate microphone for ambient noise
        Call this once at startup for better recognition
        """
        if self._calibrated:
            return

        try:
            with sr.Microphone() as source:
                print(f"🎤 Calibrating microphone ({duration}s)...")
                self.recognizer.adjust_for_ambient_noise(
                    source, duration=duration)
                self._calibrated = True
                print("✓ Microphone calibrated")
        except Exception as e:
            print(f"⚠️  Microphone calibration failed: {e}")

    async def text_to_speech_async(
        self,
        text: str,
        output_path: Optional[str] = None,
        language: str = "dutch"
    ) -> str:
        """
        Convert text to speech (async version)

        Args:
            text: Text to convert
            output_path: Where to save audio (creates temp file if None)
            language: Target language

        Returns:
            Path to audio file
        """
        voice = self.VOICE_MODELS.get(language, self.VOICE_MODELS["dutch"])

        if output_path is None:
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".mp3")
            output_path = temp_file.name
            temp_file.close()

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

        return output_path

    def text_to_speech_sync(
        self,
        text: str,
        output_path: Optional[str] = None,
        language: str = "dutch"
    ) -> str:
        """
        Convert text to speech (synchronous version)
        Uses thread-safe event loop handling

        Args:
            text: Text to convert
            output_path: Where to save audio
            language: Target language

        Returns:
            Path to audio file
        """
        try:
            # Check if event loop is running
            try:
                loop = asyncio.get_running_loop()
                # If we're here, there's a running loop - use thread executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        self._run_async_in_thread,
                        text,
                        output_path,
                        language
                    )
                    return future.result(timeout=30)
            except RuntimeError:
                # No running loop - create new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        self.text_to_speech_async(text, output_path, language)
                    )
                finally:
                    loop.close()
        except Exception as e:
            print(f"❌ TTS failed: {e}")
            return None

    def _run_async_in_thread(self, text: str, output_path: Optional[str], language: str) -> str:
        """Helper to run async TTS in separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.text_to_speech_async(text, output_path, language)
            )
        finally:
            loop.close()

    async def generate_speech_bytes(self, text: str, language: str = "dutch") -> bytes:
        """
        Generate speech as bytes without saving to file

        Args:
            text: Text to convert to speech
            language: Target language

        Returns:
            Audio bytes
        """
        voice = self.VOICE_MODELS.get(language, self.VOICE_MODELS["dutch"])

        communicate = edge_tts.Communicate(text, voice)
        audio_bytes = b""

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]

        return audio_bytes

    async def generate_speech_bytes_with_voice(self, text: str, voice: str) -> bytes:
        """
        Generate speech as bytes with specific voice model

        Args:
            text: Text to convert to speech
            voice: Specific voice model (e.g., "nl-NL-MaartenNeural")

        Returns:
            Audio bytes
        """
        print(f"🎤 AudioEngine: Using voice {voice} for text: '{text[:50]}...'")
        communicate = edge_tts.Communicate(text, voice)
        audio_bytes = b""

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]

        print(
            f"✅ AudioEngine: Generated {len(audio_bytes)} bytes with voice {voice}")
        return audio_bytes

    def generate_speech_bytes_sync(self, text: str, language: str = "dutch") -> bytes:
        """
        Generate speech as bytes without saving to file (synchronous version)

        Args:
            text: Text to convert to speech
            language: Target language

        Returns:
            Audio bytes
        """
        try:
            # Check if event loop is running
            try:
                loop = asyncio.get_running_loop()
                # If we're here, there's a running loop - use thread executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        self._run_speech_bytes_in_thread,
                        text,
                        language
                    )
                    return future.result(timeout=30)
            except RuntimeError:
                # No running loop - create new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        self.generate_speech_bytes(text, language)
                    )
                finally:
                    loop.close()
        except Exception as e:
            print(f"❌ Speech bytes generation failed: {e}")
            return b""

    def _run_speech_bytes_in_thread(self, text: str, language: str) -> bytes:
        """Helper to run async speech bytes generation in separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.generate_speech_bytes(text, language)
            )
        finally:
            loop.close()

    def speech_to_text(
        self,
        audio_source: Optional[sr.AudioSource] = None,
        timeout: float = 5.0,
        phrase_time_limit: Optional[float] = None,
        language: str = "dutch"
    ) -> Optional[str]:
        """
        Convert speech to text

        Args:
            audio_source: Audio source (uses microphone if None)
            timeout: Max seconds to wait for speech
            phrase_time_limit: Max seconds for phrase
            language: Target language for recognition

        Returns:
            Recognized text or None
        """
        if not self._calibrated:
            self.calibrate_microphone()

        language_code = self.STT_LANGUAGES.get(language, "nl-NL")

        try:
            if audio_source is None:
                audio_source = sr.Microphone()

            with audio_source as source:
                print("🎤 Listening...")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )

            print("🔄 Processing...")
            text = self.recognizer.recognize_google(
                audio, language=language_code)
            print(f"✓ Recognized: {text}")
            return text

        except sr.WaitTimeoutError:
            print("⏱️  Timeout - no speech detected")
            return None
        except sr.UnknownValueError:
            print("❌ Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"❌ Recognition service error: {e}")
            return None


# ================================================
# LEGACY FUNCTIONS (for backward compatibility)
# ================================================

_engine = AudioEngine()


def generate_audio(
    sentences: List[str],
    user_id: str,
    target_language: str = "japanese"
) -> Optional[str]:
    """
    Legacy function for generating lesson audio

    Args:
        sentences: List of sentences to speak
        user_id: User identifier
        target_language: Target language

    Returns:
        Path to generated audio file
    """
    text = " ".join(sentences)
    path = f"data/users/{user_id}/lesson_audio.mp3"

    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)

    return _engine.text_to_speech_sync(text, path, target_language)


async def generate_audio_async(
    sentences: List[str],
    user_id: str,
    target_language: str = "japanese"
) -> Optional[str]:
    """
    Async version of generate_audio
    """
    text = " ".join(sentences)
    path = f"data/users/{user_id}/lesson_audio.mp3"

    os.makedirs(os.path.dirname(path), exist_ok=True)

    return await _engine.text_to_speech_async(text, path, target_language)


# ================================================
# REAL-TIME AUDIO STREAMING (Advanced)
# ================================================

class RealtimeAudioStreamer:
    """
    For real-time audio streaming with minimal latency
    Useful for conversational AI applications
    """

    def __init__(self, language: str = "dutch"):
        self.engine = AudioEngine()
        self.language = language
        self.audio_queue = []
        self._playing = False

    async def speak_immediately(self, text: str):
        """
        Generate and play audio with minimal delay
        """
        audio_path = await self.engine.text_to_speech_async(text, language=self.language)

        # Play audio (using system player for immediate playback)
        threading.Thread(target=self._play_audio, args=(
            audio_path,), daemon=True).start()

    def _play_audio(self, audio_path: str):
        """Play audio using system player"""
        try:
            import sys
            if sys.platform == 'darwin':  # macOS
                os.system(f'afplay {audio_path}')
            elif sys.platform == 'win32':  # Windows
                os.system(f'start {audio_path}')
            else:  # Linux
                os.system(f'mpg123 {audio_path}')
        except Exception as e:
            print(f"⚠️  Audio playback error: {e}")
        finally:
            # Clean up temp file
            try:
                os.remove(audio_path)
            except:
                pass


# ================================================
# TESTING
# ================================================

async def test_audio_system():
    """Test the audio system"""
    print("\n🧪 Testing Audio System\n")

    engine = AudioEngine()

    # Test TTS
    print("1. Testing Text-to-Speech (Dutch)...")
    audio_path = await engine.text_to_speech_async(
        "Hallo, dit is een test van het audio systeem.",
        language="dutch"
    )
    print(f"   ✓ Audio saved to: {audio_path}\n")

    # Test STT
    print("2. Testing Speech-to-Text (say something in Dutch)...")
    engine.calibrate_microphone()
    text = engine.speech_to_text(timeout=5, language="dutch")
    if text:
        print(f"   ✓ You said: {text}\n")

    # Test real-time streaming
    print("3. Testing Real-time Streaming...")
    streamer = RealtimeAudioStreamer(language="dutch")
    await streamer.speak_immediately("Dit is een real-time test.")
    print("   ✓ Streaming test complete\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run tests
        asyncio.run(test_audio_system())
    else:
        # Quick demo
        print("\n🎙️ Audio System Demo\n")
        print("Usage:")
        print("  python audio.py test    - Run full test suite")
        print("\nQuick test:")

        engine = AudioEngine()
        path = engine.text_to_speech_sync(
            "Welkom bij het Nederlandse leer systeem!",
            language="dutch"
        )
        print(f"\n✓ Audio generated: {path}")
