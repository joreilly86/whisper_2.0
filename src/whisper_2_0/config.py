"""
Configuration constants for the Voice Note Processor.
"""

import os

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
DEFAULT_VOICE_FOLDER = os.getenv("VOICE_NOTES_FOLDER", r"G:\My Drive\Voice Notes")

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
