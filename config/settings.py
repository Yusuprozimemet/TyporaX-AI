"""
Application configuration
"""
import os
from typing import Optional


class Config:
    """Application configuration class"""

    # API Configuration
    DEFAULT_MODEL: str = "google/gemma-2-9b-it"
    FALLBACK_MODEL: str = "deepseek-ai/DeepSeek-R1"
    HF_API_URL: str = "https://router.huggingface.co/v1/chat/completions"
    HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN")

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
            print("Warning: HF_TOKEN not set - AI features will use fallbacks")
            return False
        return True


# Global configuration instance
config = Config()
