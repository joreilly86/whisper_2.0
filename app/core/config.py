import os
from pathlib import Path
from typing import Optional, Literal

from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    # Application settings
    APP_NAME: str = os.getenv("APP_NAME", "Meeting Notes Generator")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_FOLDER: Path = BASE_DIR / os.getenv("UPLOAD_FOLDER", "data/uploads")
    TRANSCRIPT_FOLDER: Path = BASE_DIR / os.getenv("TRANSCRIPT_FOLDER", "data/transcripts")
    SUMMARY_FOLDER: Path = BASE_DIR / os.getenv("SUMMARY_FOLDER", "data/summaries")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./whisper.db")
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Processing settings
    TRANSCRIPTION_MODEL: str = os.getenv("TRANSCRIPTION_MODEL", "whisper")
    DEFAULT_SUMMARY_MODEL: Literal["openai", "anthropic"] = os.getenv("DEFAULT_SUMMARY_MODEL", "openai")
    
    # OpenAI settings
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # Anthropic settings
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku")
    
    # Model configurations
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "medium")
    SUMMARY_MAX_TOKENS: int = int(os.getenv("SUMMARY_MAX_TOKENS", "1000"))

# Create a singleton settings instance
settings = Settings()
