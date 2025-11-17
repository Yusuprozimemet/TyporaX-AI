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
        self._recent_questions = []  # Track recent fallback questions
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
            # Try with primary model first with enhanced prompt
            enhanced_messages = self._enhance_conversation_context(
                messages, host)
            response_text = await self._call_api(enhanced_messages, DEFAULT_MODEL)

            if not response_text:
                # Second attempt: Retry with fallback model and different approach
                retry_messages = self._create_retry_prompt(messages, host)
                response_text = await self._call_api(retry_messages, FALLBACK_MODEL)

            if not response_text:
                # Third attempt: Try primary model again with simplified prompt
                simple_messages = self._create_simple_prompt(host)
                response_text = await self._call_api(simple_messages, DEFAULT_MODEL)

            if not response_text:
                # Fourth attempt: Try fallback model with simple prompt
                simple_messages = self._create_simple_prompt(host)
                response_text = await self._call_api(simple_messages, FALLBACK_MODEL)

            if not response_text:
                # Final attempt: Very direct approach
                direct_messages = self._create_direct_statement_prompt(host)
                response_text = await self._call_api(direct_messages, DEFAULT_MODEL)

            if not response_text:
                # Only now fall back to questions (should be very rare)
                response_text = self._generate_topic_question(host)
                print(
                    f"⚠️ Using fallback question for {host['name']}: {response_text[:50]}...")

            # Check for recent duplicate responses
            if self._is_recent_duplicate(response_text, host['name']):
                print(f"🔄 Detected duplicate response, generating alternative...")
                response_text = self._generate_alternative_response(
                    host, response_text)

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

    def _enhance_conversation_context(self, messages: List[Dict], host: Dict) -> List[Dict]:
        """Enhance messages with more specific context for better responses"""
        enhanced_messages = messages.copy()

        # Get last few messages for better context
        recent_context = ""
        if len(self.conversation_history) >= 2:
            last_messages = self.conversation_history[-2:]
            recent_context = f"\nRecente uitwisselingen: {[msg['content'] for msg in last_messages]}"

        # Add specific context about current conversation state
        context_prompt = f"""
        Je bent {host['name']} in een Nederlandse podcast over: {self.current_topic}
        
        KRITISCHE INSTRUCTIES:
        - Geef NIEUWE, SPECIFIEKE informatie over dit onderwerp
        - Gebruik concrete Nederlandse voorbeelden of actuele feiten
        - ABSOLUUT GEEN generieke uitspraken zoals 'interessant punt' of 'goed punt'
        - Maximaal 2-3 inhoudelijke zinnen
        - Bouw voort op het gesprek met VERSE, relevante inhoud
        - GEEN vragen stellen aan luisteraars (die komen later)
        
        Gesprek status: {len(self.conversation_history)} berichten uitgewisseld{recent_context}
        
        FOCUS: Deel specifieke informatie, voorbeelden of inzichten over {self.current_topic}
        """

        enhanced_messages.append({"role": "system", "content": context_prompt})
        return enhanced_messages

    def _create_retry_prompt(self, messages: List[Dict], host: Dict) -> List[Dict]:
        """Create alternative prompt approach for retry"""
        retry_messages = [
            {"role": "system", "content": f"""
            Je bent {host['name']}, Nederlandse podcast host.
            Onderwerp: {self.current_topic}
            
            Geef een korte, inhoudelijke reactie (2-3 zinnen) met:
            - Specifieke informatie of voorbeelden
            - GEEN clichés of algemene opmerkingen
            - Nieuw perspektief op het onderwerp
            """}
        ]

        # Add last few messages for context
        if len(self.conversation_history) > 0:
            retry_messages.extend(self.conversation_history[-3:])

        return retry_messages

    def _create_simple_prompt(self, host: Dict) -> List[Dict]:
        """Create simple but specific prompt as final attempt"""
        return [
            {"role": "system", "content": f"""
            Je bent {host['name']} in een Nederlandse podcast.
            Geef één specifiek feit of voorbeeld over: {self.current_topic}
            Maximaal 2 zinnen. GEEN algemene opmerkingen.
            """},
            {"role": "user", "content": f"Vertel iets specifieks over {self.current_topic}"}
        ]

    def _create_direct_statement_prompt(self, host: Dict) -> List[Dict]:
        """Create very direct prompt for making a statement"""
        host_style = "persoonlijk verhaal" if host['name'] == 'Emma' else "feit met cijfer"
        return [
            {"role": "system", "content": f"""
            Je bent {host['name']}. Maak ÉÉN directe uitspraak over {self.current_topic}.
            Gebruik {host_style}. Maximaal 2 zinnen. GEEN vragen.
            Begin meteen met je punt.
            """},
            {"role": "user", "content": "Maak een korte, directe opmerking."}
        ]

    def _generate_topic_question(self, host: Dict) -> str:
        """Generate a varied, context-aware question as last resort"""
        topic = self.current_topic.lower()
        conversation_length = len(self.conversation_history)

        # Track recently used questions to avoid repetition
        if not hasattr(self, '_recent_questions'):
            self._recent_questions = []

        # Topic-specific questions for Emma (enthusiastic, personal)
        if host['name'] == 'Emma':
            if 'ai' in topic or 'kunstmatige intelligentie' in topic:
                questions = [
                    "Ik ben zo benieuwd - gebruiken jullie zelf al AI-tools in jullie werk of studie?",
                    "Mijn neef werkt bij een tech-bedrijf en vertelde laatst over AI in Nederland. Hebben jullie daar ervaring mee?",
                    "Wat vinden jullie het spannendste aan AI-ontwikkelingen? Ik kan er uren over praten!",
                    "Hoe denken jullie dat AI ons dagelijks leven gaat veranderen de komende jaren?"
                ]
            elif 'leren' in topic or 'onderwijs' in topic or 'taal' in topic:
                questions = [
                    "Wat is jullie geheime truc voor het leren van nieuwe vaardigheden? Ik leer zelf het beste door te doen!",
                    "Hebben jullie weleens geprobeerd om met AI te leren? Ik ben zo nieuwsgierig naar jullie ervaringen!",
                    "Mijn vriendin gebruikt zo'n slimme leer-app en ze is er helemaal weg van. Kennen jullie dat ook?",
                    "Wat motiveeert jullie het meest om nieuwe dingen te blijven leren?"
                ]
            else:
                questions = [
                    f"Wat is jullie eerste indruk van {self.current_topic}? Ik ben echt nieuwsgierig!",
                    f"Hebben jullie al ervaring met {self.current_topic}? Vertel eens jullie verhaal!",
                    f"Wat zou {self.current_topic} kunnen betekenen voor onze toekomst, denken jullie?"
                ]

        # Topic-specific questions for Daan (analytical, factual)
        else:  # Daan
            if 'ai' in topic or 'kunstmatige intelligentie' in topic:
                questions = [
                    "Interessant om te zien dat Nederland op Europees niveau voorloopt in AI-adoptie. Hoe ervaren jullie dat?",
                    "Volgens recent onderzoek groeit de AI-markt in Nederland met 15% per jaar. Wat zijn jullie gedachten hierover?",
                    "De Nederlandse overheid investeert flink in AI-ethiek en regelgeving. Hoe belangrijk vinden jullie dat?",
                    "Welke sectoren in Nederland profiteren volgens jullie het meest van AI-technologie?"
                ]
            elif 'leren' in topic or 'onderwijs' in topic or 'taal' in topic:
                questions = [
                    "Nederlandse universiteiten doen baanbrekend onderzoek naar digitaal leren. Wat vinden jullie daarvan?",
                    "Uit cijfers blijkt dat interactief leren 40% effectiever is. Herkennen jullie dat?",
                    "Het Nederlandse onderwijssysteem omarmt steeds meer technologie. Hoe kijken jullie daartegen aan?",
                    "Welke leertrends zien jullie opkomen in Nederland de laatste tijd?"
                ]
            else:
                questions = [
                    f"Welke Nederlandse ontwikkelingen rond {self.current_topic} vallen jullie op?",
                    f"Hoe positioneert Nederland zich internationaal op het gebied van {self.current_topic}?",
                    f"Wat zijn volgens jullie de belangrijkste trends rond {self.current_topic}?"
                ]

        # Filter out recently used questions
        available_questions = [
            q for q in questions if q not in self._recent_questions]
        if not available_questions:
            # If all questions were used recently, reset and use all
            self._recent_questions = []
            available_questions = questions

        # Select a question and add to recent list
        import random
        selected_question = random.choice(available_questions)
        self._recent_questions.append(selected_question)

        # Keep only last 3 questions to prevent long-term repetition
        if len(self._recent_questions) > 3:
            self._recent_questions = self._recent_questions[-3:]

        return selected_question

    def _is_recent_duplicate(self, response_text: str, speaker_name: str) -> bool:
        """Check if response is too similar to recent messages from same speaker"""
        # Check last 4 messages for duplicates from same speaker
        recent_messages = self.conversation_history[-4:] if len(
            self.conversation_history) >= 4 else self.conversation_history

        for msg in recent_messages:
            if f"{speaker_name}:" in msg.get('content', ''):
                # Extract just the response part
                prev_response = msg['content'].split(':', 1)[1].strip(
                ) if ':' in msg['content'] else msg['content']

                # Simple similarity check
                if len(response_text) > 20 and len(prev_response) > 20:
                    # Check for exact matches or very similar starts
                    if response_text == prev_response or response_text[:30] == prev_response[:30]:
                        return True

        return False

    def _generate_alternative_response(self, host: Dict, original_response: str) -> str:
        """Generate an alternative when duplicate is detected"""
        alternatives = {
            'Emma': [
                f"Oh wacht, ik wilde nog iets anders zeggen over {self.current_topic}...",
                f"Eigenlijk, wat ik net bedoelde over {self.current_topic} is...",
                f"Laat me dat anders zeggen - {self.current_topic} is volgens mij..."
            ],
            'Daan': [
                f"Om het anders te formuleren: {self.current_topic} toont interessante ontwikkelingen.",
                f"Vanuit een ander perspectief bekeken, {self.current_topic} heeft verschillende aspecten.",
                f"Als we het breder bekijken, {self.current_topic} raakt aan meerdere thema's."
            ]
        }

        return alternatives.get(host['name'], alternatives['Emma'])[0]

    async def _call_api(self, messages: List[Dict], model: str) -> Optional[str]:
        """Call HuggingFace API"""
        if not HF_TOKEN:
            return None

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 120,  # Allow slightly longer responses for better content
            "temperature": 0.8,  # More creative for dynamic responses
            "top_p": 0.9
        }

        headers = {"Authorization": f"Bearer {HF_TOKEN}"}

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
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
