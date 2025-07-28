"""
Configuration constants for the Voice Note Processor.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Audio Processing
MAX_CHUNK_SIZE_BYTES = 24.5 * 1024 * 1024  # 24.5 MB
TARGET_BITRATE_KBPS = "192k"
TEMP_CHUNK_SUBDIR = "temp_voice_chunks"
AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".flac", ".ogg")

# File Paths
POST_PROCESSING_PROMPT_FILE = "post_processing_prompt.txt"
BACKUP_FOLDER = "transcription_backups"
QUEUE_FILE = "processing_queue.txt"
PROCESSED_FILES_LOG = "processed_files.txt"
TEMP_DOWNLOAD_DIR = "temp_downloads"

# Notion Configuration
NOTION_MAX_CHUNK_SIZE = 2000  # Characters per block
NOTION_TIMEOUT = 10  # Seconds

# File Detection
TEMP_FILE_PATTERNS = [
    "temp",
    "tmp",
    "recording",
    "rec_",
    ".part",
    ".tmp",
    "~",
    "untitled",
    "new recording",
    "voice memo",
]
TEMP_FILE_AGE_THRESHOLD = 30  # Seconds

# Notification Settings
NOTIFICATION_TIMEOUT_SUCCESS = 15  # Seconds
NOTIFICATION_TIMEOUT_ERROR = 20  # Seconds
NOTIFICATION_TIMEOUT_BATCH = 10  # Seconds

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Company Information
COMPANY_NAME = os.getenv("COMPANY_NAME", "your company")
COMPANY_SHORTHAND = os.getenv("COMPANY_SHORTHAND", "your company")

# Configuration validation
def validate_configuration():
    """Validate that required configuration is present."""
    errors = []
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        errors.append("Error: .env file not found. Please copy .env.example to .env and configure your API keys.")
        return errors
    
    # Check transcription API keys
    if not OPENAI_API_KEY and not GROQ_API_KEY:
        errors.append("Error: No transcription API key found. Please set either OPENAI_API_KEY or GROQ_API_KEY in .env file")
    
    # Check summarization API keys  
    if not OPENAI_API_KEY and not GEMINI_API_KEY:
        errors.append("Error: No summarization API key found. Please set either OPENAI_API_KEY or GEMINI_API_KEY in .env file")
    
    # Check Notion configuration
    if not NOTION_API_KEY:
        errors.append("Error: NOTION_API_KEY not found in .env file")
    
    if not NOTION_DATABASE_ID:
        errors.append("Error: NOTION_DATABASE_ID not found in .env file")
    
    return errors
