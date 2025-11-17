#!/usr/bin/env python3

from src.utils.audio import generate_audio
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_audio_generation():
    """Test the fixed audio generation function"""

    # Test data
    user_id = "alex"
    sentences = ["Hallo, dit is een test.", "Nederlands is een mooie taal."]
    target_language = "dutch"

    print(f"Testing audio generation with:")
    print(f"User ID: {user_id}")
    print(f"Sentences: {sentences}")
    print(f"Target language: {target_language}")

    # Call generate_audio function
    try:
        audio_path = generate_audio(sentences, user_id, target_language)
        print(f"Generated audio path: {audio_path}")

        # Check if file exists
        if audio_path and os.path.exists(audio_path):
            print("✅ Audio file created successfully!")
            file_size = os.path.getsize(audio_path)
            print(f"File size: {file_size} bytes")
        else:
            print("❌ Audio file was not created")

    except Exception as e:
        print(f"❌ Error generating audio: {e}")


if __name__ == "__main__":
    test_audio_generation()
