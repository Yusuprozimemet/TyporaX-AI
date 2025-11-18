"""
Application configuration
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class"""

    # API Configuration - Groq (Fast, Free, Excellent)
    DEFAULT_MODEL: str = "llama-3.1-8b-instant"
    FALLBACK_MODEL: str = "mixtral-8x7b-instruct-v0.1"
    HF_API_URL: str = "https://api.groq.com/openai/v1/chat/completions"
    HF_TOKEN: Optional[str] = os.getenv("GROQ_API_KEY")

    # API Configuration - HuggingFace (Commented out for now)
    # DEFAULT_MODEL: str = "google/gemma-2-9b-it"
    # FALLBACK_MODEL: str = "deepseek-ai/DeepSeek-R1"
    # HF_API_URL: str = "https://router.huggingface.co/v1/chat/completions"
    # HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")

    # Application Settings
    APP_NAME: str = "TyporaX-AI"
    VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # File Paths
    DATA_DIR: str = "data"
    USERS_DIR: str = "data/users"
    STATIC_DIR: str = "static"
    TEMPLATES_DIR: str = "templates"
    PROMPTS_DIR: str = "prompts"

    # Audio Settings
    DEFAULT_VOICE_DUTCH: str = "nl-NL-ColetteNeural"
    DEFAULT_VOICE_ENGLISH: str = "en-US-JennyNeural"

    # Assessment Settings
    MAX_CONVERSATION_HISTORY: int = 10
    ASSESSMENT_TIMEOUT: float = 15.0

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        if not cls.HF_TOKEN:
            print("Warning: GROQ_API_KEY not set - AI features will use fallbacks")
            return False
        return True


# Global configuration instance
config = Config()
