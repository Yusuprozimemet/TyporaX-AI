#!/usr/bin/env python3
"""
Test script for Dutch Podcast Expert functionality
"""

from src.experts.dutch_podcast_expert import test_podcast
import asyncio
import os
import sys

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


if __name__ == "__main__":
    print("🎙️ Testing Dutch Podcast Expert...")
    print("Make sure HF_TOKEN environment variable is set!")

    if not os.getenv("HF_TOKEN"):
        print("❌ Please set HF_TOKEN environment variable")
        print("Example: export HF_TOKEN='your_token_here'")
        sys.exit(1)

    asyncio.run(test_podcast())
