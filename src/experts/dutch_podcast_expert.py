# dutch_podcast_expert.py
# ================================================
# Dutch Podcast Expert - Real-time Interactive Podcast Conversations
# Two Dutch hosts discussing topics with real-time user interaction
# ================================================

import os
import json
import httpx
import asyncio
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import threading
import queue
from src.utils.prompt_manager import get_prompt, get_prompt_config

# === CONFIG ===
DEFAULT_MODEL = "google/gemma-2-9b-it"
FALLBACK_MODEL = "deepseek-ai/DeepSeek-R1"
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
HF_TOKEN = os.getenv("HF_TOKEN", "")

# === Dutch Podcast Hosts ===
DUTCH_HOSTS = {
    "host1": {
        "name": "Emma",
        "personality": "Enthousiaste Nederlandse presentatrice, stelt goede vragen, nieuwsgierig naar details",
        "voice": "nl-NL-ColetteNeural",  # Female Dutch voice
        "style": "vriendelijk, toegankelijk, goed luisterend"
    },
    "host2": {
        "name": "Daan",
        "personality": "Ervaren Nederlandse journalist, analytisch, brengt verschillende perspectieven naar voren",
        # Male Dutch voice - should sound distinctly different
        "voice": "nl-NL-MaartenNeural",
        "style": "doordachte vragen, bouwt voort op gesprek, professioneel maar toegankelijk"
    }
}


class DutchPodcastConversation:
    """
    Manages real-time Dutch podcast conversation with two hosts
    """

    def __init__(self):
        self.conversation_history = []
        self.current_topic = ""
        self.is_active = False
        self.hosts = DUTCH_HOSTS
        self.current_speaker = "host1"  # Start with Emma

    async def start_podcast(self, initial_topic: str) -> Dict:
        """
        Start the podcast conversation with initial topic

        Args:
            initial_topic: User's topic or question to discuss

        Returns:
            Initial podcast response
        """
        self.current_topic = initial_topic
        self.is_active = True
        self.conversation_history = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": f"Onderwerp om te bespreken: {initial_topic}"}
        ]

        # Generate opening from Emma
        return await self._generate_host_response("host1", True)

    async def continue_conversation(self, user_input: Optional[str] = None) -> Dict:
        """
        Continue the podcast conversation, optionally with user interruption

        Args:
            user_input: User's question or comment (None for natural flow)

        Returns:
            Next host response
        """
        if not self.is_active:
            return {"error": "Podcast is not active"}

        # Handle user interruption
        if user_input:
            self.conversation_history.append({
                "role": "user",
                "content": f"Luisteraar onderbreekt: {user_input}"
            })

        # Switch to next host
        previous_speaker = self.current_speaker
        self.current_speaker = "host2" if self.current_speaker == "host1" else "host1"

        print(
            f"🎙️ Podcast: Switching from {previous_speaker} ({self.hosts[previous_speaker]['name']}) to {self.current_speaker} ({self.hosts[self.current_speaker]['name']})")

        return await self._generate_host_response(self.current_speaker, False)

    def stop_podcast(self) -> Dict:
        """Stop the podcast conversation"""
        self.is_active = False
        return {
            "type": "podcast_end",
            "message": "Bedankt voor het luisteren naar onze Nederlandse podcast! Tot de volgende keer!",
            "speaker": "both",
            "audio_needed": True
        }

    def _get_system_prompt(self) -> str:
        """Get system prompt for Dutch podcast hosts"""
        return get_prompt('dutch_podcast_expert', 'system_prompt')

    async def _generate_host_response(self, host_key: str, is_opening: bool) -> Dict:
        """Generate response from specific host"""
        host = self.hosts[host_key]

        # Create specific prompt for this host using prompt manager
        host_instructions_key = f"{host['name'].lower()}_instructions"
        host_instruction = get_prompt(
            'dutch_podcast_expert', host_instructions_key)

        if not host_instruction:
            # Fallback if prompt not found
            host_instruction = f"Je bent {host['name']} in deze Nederlandse podcast. Geef een korte, inhoudelijke reactie."

        messages = self.conversation_history + [
            {"role": "system", "content": host_instruction}
        ]

        try:
            # Try with primary model first
            response_text = await self._call_api(messages, DEFAULT_MODEL)
            if not response_text:
                response_text = await self._call_api(messages, FALLBACK_MODEL)

            if not response_text:
                # Use fallback responses from prompt manager
                fallback_data = get_prompt_config(
                    'dutch_podcast_expert', 'fallback_responses')
                if fallback_data and isinstance(fallback_data, list):
                    response_text = random.choice(fallback_data)
                else:
                    # Ultimate fallback
                    response_text = "Dat is een interessant punt! Wat denken onze luisteraars hiervan?"

            # Add to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": f"{host['name']}: {response_text}"
            })

            # Keep history manageable
            if len(self.conversation_history) > 20:
                # Keep system prompt + last 15 messages
                self.conversation_history = [
                    self.conversation_history[0]] + self.conversation_history[-15:]

            response_data = {
                "type": "podcast_message",
                "speaker": host['name'],
                "speaker_key": host_key,
                "message": response_text,
                "voice": host['voice'],
                "audio_needed": True,
                "timestamp": datetime.now().isoformat()
            }

            print(
                f"🎭 Generated response: {host['name']} ({host_key}) with voice {host['voice']}: {response_text[:50]}...")

            return response_data

        except Exception as e:
            print(f"❌ Error generating podcast response: {e}")
            return {
                "type": "podcast_error",
                "message": "Sorry, er ging iets mis. Probeer het opnieuw.",
                "speaker": host['name'],
                "speaker_key": host_key
            }

    async def _call_api(self, messages: List[Dict], model: str) -> Optional[str]:
        """Call HuggingFace API"""
        if not HF_TOKEN:
            return None

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 100,  # Shorter responses for faster flow
            "temperature": 0.7,  # Slightly less creative for more reliable responses
            "top_p": 0.85
        }

        headers = {"Authorization": f"Bearer {HF_TOKEN}"}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(HF_API_URL, json=payload, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    print(
                        f"❌ API Error {response.status_code}: {response.text}")
                    return None

        except Exception as e:
            print(f"❌ API Call Error: {e}")
            return None


# Global conversation manager
podcast_conversation = DutchPodcastConversation()


async def generate_podcast_response(message: str, conversation_history: List[Dict]) -> Dict:
    """
    Main function for generating podcast responses

    Args:
        message: User's message/topic
        conversation_history: Previous conversation context

    Returns:
        Podcast response dict
    """
    global podcast_conversation

    # Handle special commands
    if message.lower().strip() in ["stop", "stop podcast", "einde", "stoppen"]:
        return podcast_conversation.stop_podcast()

    # Check if this is starting a new podcast
    if not podcast_conversation.is_active:
        return await podcast_conversation.start_podcast(message)
    else:
        # Continue existing conversation with user input
        return await podcast_conversation.continue_conversation(message)


async def get_continuous_podcast_response() -> Optional[Dict]:
    """
    Get next natural conversation turn without user input
    Used for continuous podcast flow
    """
    global podcast_conversation

    if podcast_conversation.is_active:
        return await podcast_conversation.continue_conversation()
    return None


# === Utility Functions ===

def reset_podcast():
    """Reset podcast conversation state"""
    global podcast_conversation
    podcast_conversation = DutchPodcastConversation()


def get_podcast_status() -> Dict:
    """Get current podcast status"""
    global podcast_conversation
    return {
        "is_active": podcast_conversation.is_active,
        "current_topic": podcast_conversation.current_topic,
        "current_speaker": podcast_conversation.current_speaker,
        "message_count": len(podcast_conversation.conversation_history)
    }


# === Testing Function ===
async def test_podcast():
    """Test the podcast functionality"""
    print("🎙️ Testing Dutch Podcast Expert...")

    # Start podcast
    response = await generate_podcast_response("Kunstmatige intelligentie in het dagelijks leven", [])
    print(f"\n{response['speaker']}: {response['message']}")

    # Continue conversation
    for i in range(3):
        await asyncio.sleep(1)  # Simulate natural timing
        response = await get_continuous_podcast_response()
        if response:
            print(f"\n{response['speaker']}: {response['message']}")

    # User interruption
    response = await generate_podcast_response("Wat betekent dit voor privacy?", [])
    print(f"\n{response['speaker']}: {response['message']}")

    # Final turn
    response = await get_continuous_podcast_response()
    if response:
        print(f"\n{response['speaker']}: {response['message']}")

    # Stop podcast
    response = await generate_podcast_response("stop", [])
    print(f"\n{response.get('message', 'Podcast gestopt')}")


if __name__ == "__main__":
    if not HF_TOKEN:
        print("❌ HF_TOKEN environment variable required")
        exit(1)

    asyncio.run(test_podcast())
