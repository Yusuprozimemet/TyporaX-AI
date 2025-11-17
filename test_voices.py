#!/usr/bin/env python3
"""
Test script to verify that different Edge-TTS voices produce different audio
"""

import asyncio
import os
from src.utils.audio import AudioEngine


async def test_different_voices():
    """Test that Emma and Daan voices are actually different"""

    print("🎤 Testing Edge-TTS voices...")

    engine = AudioEngine()

    test_text = "Hallo, dit is een test van de Nederlandse stem."

    # Test Emma's voice (female)
    print("🎭 Testing Emma's voice (nl-NL-ColetteNeural)...")
    emma_bytes = await engine.generate_speech_bytes_with_voice(test_text, "nl-NL-ColetteNeural")
    print(f"Emma audio: {len(emma_bytes)} bytes")

    # Test Daan's voice (male)
    print("🎭 Testing Daan's voice (nl-NL-MaartenNeural)...")
    daan_bytes = await engine.generate_speech_bytes_with_voice(test_text, "nl-NL-MaartenNeural")
    print(f"Daan audio: {len(daan_bytes)} bytes")

    # Compare the audio
    if emma_bytes == daan_bytes:
        print("❌ ERROR: Both voices produced identical audio!")
        return False
    else:
        print("✅ SUCCESS: Voices produced different audio")

        # Save test files to verify manually
        os.makedirs("test_output", exist_ok=True)

        with open("test_output/emma_test.mp3", "wb") as f:
            f.write(emma_bytes)
        print("💾 Saved Emma test to: test_output/emma_test.mp3")

        with open("test_output/daan_test.mp3", "wb") as f:
            f.write(daan_bytes)
        print("💾 Saved Daan test to: test_output/daan_test.mp3")

        print("\n🎧 Play both files to verify they sound different!")
        return True

if __name__ == "__main__":
    asyncio.run(test_different_voices())
