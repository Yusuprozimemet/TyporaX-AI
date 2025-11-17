#!/usr/bin/env python3
"""
Test script for improved Dutch podcast expert
"""

from src.experts.dutch_podcast_expert import generate_podcast_response
import asyncio
import sys
import os
sys.path.append('.')


async def test_improved_podcast():
    """Test the improved podcast system with real input"""

    # Test input that was causing fallback responses
    test_input = "TyporaX-AI is an AI-powered Dutch language learning app that combines personalized expert coaching with real-time feedback. Users can practice Dutch conversation with healthcare, IT, and language specialist bots, receive instant grammar and vocabulary assessment, and get study methods tailored to their personality type (MBTI). The platform includes a markdown editor for writing practice, auto-generated Anki flashcards, realistic Dutch audio pronunciation, and progress tracking. Learners can export resources like PDF learning plans, flashcard decks, and audio files. The app is built using FastAPI, requires Python 3.13+, and is free for contributors aiming to add new experts or language features. It is designed for real-world language use and individual growth, leveraging AI for a truly adaptive learning journey."

    print("🎙️ Testing improved Dutch podcast expert...")
    print(f"Input: {test_input[:100]}...")
    print("=" * 60)

    try:
        # Start podcast conversation
        response = await generate_podcast_response(test_input, [])

        print(f"✅ Speaker: {response.get('speaker', 'Unknown')}")
        print(f"✅ Message: {response.get('message', 'No message')}")
        print(f"✅ Voice: {response.get('voice', 'No voice')}")
        print(f"✅ Type: {response.get('type', 'No type')}")

        # Check response quality
        message = response.get('message', '')
        if 'interessant punt' in message.lower() or 'wat denken onze luisteraars' in message.lower():
            print("❌ WARNING: Still using old fallback response!")
        elif '?' in message and len(message.split('?')) > 1:
            print("⚠️ NOTICE: Response contains question (might be fallback)")
        else:
            print("✅ SUCCESS: Generated dynamic statement response!")

        # Test continuous conversation to check for repetition
        print("\n" + "="*60)
        print("Testing continuous conversation for repetition...")

        from src.experts.dutch_podcast_expert import get_continuous_podcast_response

        for i in range(3):
            print(f"\n--- Turn {i+1} ---")
            next_response = await get_continuous_podcast_response()
            if next_response:
                print(f"Speaker: {next_response.get('speaker', 'Unknown')}")
                print(f"Message: {next_response.get('message', 'No message')}")

                msg = next_response.get('message', '')
                if '?' in msg and len(msg.split('?')) > 1:
                    print("⚠️ Question-based response (might be fallback)")
                else:
                    print("✅ Statement-based response")
            else:
                print("No response generated")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check for HF_TOKEN
    if not os.getenv("HF_TOKEN"):
        print("❌ HF_TOKEN environment variable required")
        sys.exit(1)

    asyncio.run(test_improved_podcast())
