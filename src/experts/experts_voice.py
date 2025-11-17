# experts_voice.py
# ================================================
# Real-time Voice Interaction System for Language Learning Experts
# Supports Healthcare Expert, IT Backend Interviewer, and future experts
# ================================================

from it_backend_interviewer import run_backend_interview, INTERVIEW_SCENARIOS
from healthcare_expert import run_healthcare_conversation, HEALTHCARE_SCENARIOS
import os
import asyncio
import tempfile
import wave
import pyaudio
import edge_tts
import speech_recognition as sr
from typing import Optional, Dict, List, Callable
from datetime import datetime
import threading
import queue

# Import your experts
import sys
# Path append no longer needed with proper package structure


class VoiceInteractionEngine:
    """
    Handles real-time voice input/output for language learning experts
    """

    def __init__(self, target_language: str = "dutch"):
        """
        Initialize voice engine

        Args:
            target_language: "dutch", "japanese", "chinese", etc.
        """
        self.target_language = target_language
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Voice models for different languages
        self.voice_models = {
            "dutch": "nl-NL-ColetteNeural",  # Female Dutch voice
            "japanese": "ja-JP-NanamiNeural",
            "chinese": "zh-CN-XiaoxiaoNeural",
            "english": "en-US-JennyNeural"
        }

        # Speech recognition language codes
        self.stt_languages = {
            "dutch": "nl-NL",
            "japanese": "ja-JP",
            "chinese": "zh-CN",
            "english": "en-US"
        }

        # Audio playback setup
        self.audio_queue = queue.Queue()
        self.is_playing = False

        # Adjust for ambient noise once at startup
        print("🎤 Calibrating microphone for ambient noise (please wait 2 seconds)...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print("✓ Microphone ready!\n")

    async def text_to_speech(self, text: str, play_immediately: bool = True) -> Optional[str]:
        """
        Convert text to speech and optionally play it

        Args:
            text: Text to convert
            play_immediately: If True, play audio immediately

        Returns:
            Path to generated audio file
        """
        voice = self.voice_models.get(
            self.target_language, self.voice_models["dutch"])

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        output_path = temp_file.name
        temp_file.close()

        try:
            # Generate speech
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)

            if play_immediately:
                self._play_audio(output_path)

            return output_path
        except Exception as e:
            print(f"❌ TTS Error: {e}")
            return None

    def _play_audio(self, audio_path: str):
        """Play audio file using pyaudio"""
        try:
            # Convert MP3 to WAV using edge-tts's internal conversion
            # Or use pydub if available
            try:
                from pydub import AudioSegment
                from pydub.playback import play

                audio = AudioSegment.from_mp3(audio_path)
                play(audio)
            except ImportError:
                # Fallback: use system player
                if os.name == 'nt':  # Windows
                    os.system(f'start {audio_path}')
                elif os.name == 'posix':  # macOS/Linux
                    os.system(f'afplay {audio_path}' if sys.platform ==
                              'darwin' else f'mpg123 {audio_path}')
        except Exception as e:
            print(f"❌ Audio playback error: {e}")

    def listen(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
        """
        Listen for voice input and convert to text

        Args:
            timeout: Maximum seconds to wait for speech to start
            phrase_time_limit: Maximum seconds for a single phrase

        Returns:
            Recognized text or None
        """
        try:
            with self.microphone as source:
                print("🎤 Listening... (speak now)")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )

            print("🔄 Processing speech...")

            # Use language-specific recognition
            language_code = self.stt_languages.get(
                self.target_language, "nl-NL")
            text = self.recognizer.recognize_google(
                audio, language=language_code)

            print(f"✓ You said: {text}\n")
            return text

        except sr.WaitTimeoutError:
            print("⏱️ No speech detected (timeout)")
            return None
        except sr.UnknownValueError:
            print("❌ Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"❌ Speech recognition service error: {e}")
            return None

    def listen_continuous(self, callback: Callable[[str], None], stop_phrase: str = "stop sessie"):
        """
        Continuously listen for speech and call callback function

        Args:
            callback: Function to call with recognized text
            stop_phrase: Phrase to stop listening (in target language)
        """
        print(
            f"🎤 Continuous listening started. Say '{stop_phrase}' to stop.\n")

        while True:
            text = self.listen(timeout=10, phrase_time_limit=15)

            if text:
                if stop_phrase.lower() in text.lower():
                    print(f"🛑 Stop phrase detected: '{stop_phrase}'")
                    break

                callback(text)


class VoiceExpertSession:
    """
    Manages a voice conversation session with a language learning expert
    """

    def __init__(
        self,
        expert_type: str,
        scenario: str,
        target_language: str = "dutch"
    ):
        """
        Args:
            expert_type: "healthcare" or "it_backend"
            scenario: Scenario key from respective expert
            target_language: Target language for learning
        """
        self.expert_type = expert_type
        self.scenario = scenario
        self.target_language = target_language

        # Initialize voice engine
        self.voice_engine = VoiceInteractionEngine(target_language)

        # Conversation state
        self.conversation_history = []
        self.turn_count = 0
        self.feedback_history = []

        # Expert function mapping
        self.expert_functions = {
            "healthcare": run_healthcare_conversation,
            "it_backend": run_backend_interview
        }

        # Scenario info
        self.scenario_info = self._get_scenario_info()

    def _get_scenario_info(self) -> Dict:
        """Get scenario information"""
        if self.expert_type == "healthcare":
            return HEALTHCARE_SCENARIOS.get(self.scenario, {})
        elif self.expert_type == "it_backend":
            return INTERVIEW_SCENARIOS.get(self.scenario, {})
        return {}

    async def start_session(self):
        """Start interactive voice session"""
        print("\n" + "="*70)
        print(f"🎙️ VOICE SESSION STARTED".center(70))
        print("="*70)
        print(f"\n📋 Expert: {self.expert_type.upper()}")
        print(f"📋 Scenario: {self.scenario_info.get('title', self.scenario)}")
        print(f"🌍 Language: {self.target_language.upper()}")
        print(f"\n💡 Context: {self.scenario_info.get('context', 'N/A')}")
        print(f"🎭 AI Role: {self.scenario_info.get('ai_role', 'N/A')}")

        print("\n" + "-"*70)
        print("CONTROLS:")
        print("  • Speak naturally in Dutch when prompted")
        print("  • Say 'stop sessie' to end the conversation")
        print("  • Say 'herhaal' to repeat the last response")
        print("  • Say 'feedback' to get detailed feedback on your last response")
        print("-"*70 + "\n")

        # Generate and play opening question
        opening_question = self._get_opening_question()
        print(f"🤖 AI: {opening_question}\n")
        await self.voice_engine.text_to_speech(opening_question)

        # Start conversation loop
        await self._conversation_loop()

    def _get_opening_question(self) -> str:
        """Get opening question based on scenario"""
        if self.expert_type == "healthcare":
            openings = {
                "anamnese": "Goedemorgen, ik ben dokter. Wat kan ik vandaag voor u doen?",
                "symptom_assessment": "Goedemiddag, u heeft buikpijn zegt u. Kunt u vertellen waar precies?",
                "diagnosis_explanation": "Ik heb uw testresultaten. U heeft een verhoogde bloeddruk. Heeft u vragen?",
                "medication_instructions": "Ik schrijf u antibiotica voor. Luister goed naar de instructies.",
                "emergency_assessment": "Help! Ik kan moeilijk ademhalen!",
                "phone_pharmacy": "Goedemiddag, apotheek De Linde, waarmee kan ik u helpen?"
            }
        else:  # it_backend
            openings = {
                "system_design": "Hoe zou je een REST API ontwerpen die 10.000 verzoeken per seconde aankan?",
                "database_design": "Waarom heb je gekozen voor PostgreSQL in plaats van MongoDB?",
                "code_review": "Ik zie dat je async/await gebruikt. Kun je uitleggen waarom?",
                "debugging_scenario": "Er is een geheugenlek in productie. Wat is je aanpak?",
                "behavioral_conflict": "Vertel eens over een situatie waar je het oneens was met een teamlid.",
                "salary_negotiation": "We kunnen je 55.000 euro bruto per jaar aanbieden. Wat vind je daarvan?",
                "technical_screening": "Kun je in 30 seconden uitleggen wat RESTful betekent?",
                "architecture_discussion": "Wanneer zou je microservices verkiezen boven een monoliet?"
            }

        return openings.get(self.scenario, "Hallo, vertel eens over jezelf.")

    async def _conversation_loop(self):
        """Main conversation loop"""
        while True:
            # Listen for user input
            user_input = self.voice_engine.listen(
                timeout=15, phrase_time_limit=20)

            if not user_input:
                continue

            # Check for control commands
            if "stop sessie" in user_input.lower():
                await self._end_session()
                break

            if "herhaal" in user_input.lower():
                if self.conversation_history:
                    last_ai_response = self.conversation_history[-1].get(
                        "content", "")
                    print(f"🤖 AI (herhaling): {last_ai_response}\n")
                    await self.voice_engine.text_to_speech(last_ai_response)
                continue

            if "feedback" in user_input.lower():
                if self.feedback_history:
                    await self._speak_feedback(self.feedback_history[-1])
                continue

            # Process conversation turn
            await self._process_turn(user_input)
            self.turn_count += 1

    async def _process_turn(self, user_input: str):
        """Process a single conversation turn"""
        print(f"\n[Turn {self.turn_count + 1}]")
        print(f"👤 You: {user_input}")

        # Call appropriate expert function
        expert_func = self.expert_functions.get(self.expert_type)

        if not expert_func:
            print(f"❌ Unknown expert type: {self.expert_type}")
            return

        # Get AI response and feedback
        result = expert_func(
            self.scenario,
            user_input,
            self.conversation_history
        )

        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return

        # Extract response (different key names for different experts)
        ai_response = result.get("patient_response") or result.get(
            "interviewer_response", "")

        # Update history
        self.conversation_history = result.get(
            "history", self.conversation_history)
        self.feedback_history.append(result.get("feedback", {}))

        # Display and speak AI response
        print(f"🤖 AI: {ai_response}\n")
        await self.voice_engine.text_to_speech(ai_response)

        # Display text feedback (don't speak it automatically)
        self._display_feedback(result.get("feedback", {}))

        # For IT interviews, show score
        if "interview_score" in result:
            score = result["interview_score"]
            score_emoji = "🟢" if score >= 80 else "🟡" if score >= 65 else "🔴"
            print(f"\n{score_emoji} Interview Score: {score}/100\n")

    def _display_feedback(self, feedback: Dict):
        """Display text feedback"""
        print("─" * 50)
        print(f"📊 Your Level: {feedback.get('level', 'N/A')}")
        print(f"✏️  Grammar: {feedback.get('grammar', 'N/A')}")
        print(f"💡 Tip: {feedback.get('tip', 'N/A')}")
        print("─" * 50 + "\n")

    async def _speak_feedback(self, feedback: Dict):
        """Speak detailed feedback"""
        feedback_text = f"""
        Je niveau is {feedback.get('level', 'B1')}. 
        {feedback.get('grammar', '')}.
        Een betere versie zou zijn: {feedback.get('b2_improvement', '')}.
        Tip: {feedback.get('tip', '')}.
        """

        print(f"🔊 Speaking detailed feedback...\n")
        await self.voice_engine.text_to_speech(feedback_text.strip())

    async def _end_session(self):
        """End the session and provide summary"""
        print("\n" + "="*70)
        print("🛑 SESSION ENDED".center(70))
        print("="*70)

        if self.feedback_history:
            avg_level = self._calculate_average_level()
            print(f"\n📊 Session Summary:")
            print(f"   • Total turns: {self.turn_count}")
            print(f"   • Average level: {avg_level}")
            print(
                f"   • Scenario: {self.scenario_info.get('title', self.scenario)}")

        goodbye = "Bedankt voor het oefenen! Tot de volgende keer."
        print(f"\n🤖 AI: {goodbye}\n")
        await self.voice_engine.text_to_speech(goodbye)

    def _calculate_average_level(self) -> str:
        """Calculate average language level from feedback"""
        level_scores = {"B1": 1, "B2": 2, "C1": 3}
        scores = [level_scores.get(f.get("level", "B1"), 1)
                  for f in self.feedback_history]
        avg = sum(scores) / len(scores) if scores else 1

        if avg < 1.5:
            return "B1"
        elif avg < 2.5:
            return "B2"
        else:
            return "C1"


# ================================================
# MAIN INTERFACE
# ================================================

async def start_voice_session(expert_type: str, scenario: str, target_language: str = "dutch"):
    """
    Start a voice interaction session

    Args:
        expert_type: "healthcare" or "it_backend"
        scenario: Scenario key from respective expert
        target_language: "dutch", "japanese", "chinese", etc.
    """
    session = VoiceExpertSession(expert_type, scenario, target_language)
    await session.start_session()


# ================================================
# CLI INTERFACE
# ================================================

async def interactive_menu():
    """Interactive menu for selecting expert and scenario"""
    print("\n" + "="*70)
    print("🎙️ VOICE LANGUAGE LEARNING SYSTEM".center(70))
    print("="*70)

    print("\n1. Healthcare Expert (Doctor-Patient Roleplay)")
    print("2. IT Backend Interviewer (Technical Interview)")
    print("\nq. Quit")

    choice = input("\nSelect expert (1-2): ").strip()

    if choice == '1':
        expert_type = "healthcare"
        scenarios = HEALTHCARE_SCENARIOS
    elif choice == '2':
        expert_type = "it_backend"
        scenarios = INTERVIEW_SCENARIOS
    elif choice.lower() == 'q':
        return
    else:
        print("❌ Invalid choice")
        return

    # Show scenarios
    print(f"\n{'='*70}")
    print(f"{expert_type.upper()} SCENARIOS".center(70))
    print("="*70 + "\n")

    for idx, (key, info) in enumerate(scenarios.items(), 1):
        print(f"{idx}. {info['title']}")
        print(f"   {info['description']}\n")

    scenario_choice = input(f"Select scenario (1-{len(scenarios)}): ").strip()

    try:
        scenario_idx = int(scenario_choice) - 1
        scenario_key = list(scenarios.keys())[scenario_idx]
    except (ValueError, IndexError):
        print("❌ Invalid choice")
        return

    # Start session
    await start_voice_session(expert_type, scenario_key, "dutch")


if __name__ == "__main__":
    # Check dependencies
    try:
        import pyaudio
        import speech_recognition
        import edge_tts
    except ImportError as e:
        print(f"""
❌ Missing dependencies! Install with:

pip install pyaudio SpeechRecognition edge-tts pydub

Note: pyaudio may require additional system packages:
- macOS: brew install portaudio
- Linux: apt-get install portaudio19-dev python3-pyaudio
- Windows: Download from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
        """)
        exit(1)

    # Run interactive menu
    asyncio.run(interactive_menu())
