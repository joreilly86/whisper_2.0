import os
import time
import json
from pathlib import Path
from typing import Tuple
import time
import logging
from openai import OpenAI # Import OpenAI library

from app.core.config import settings

logger = logging.getLogger(__name__)

class TranscriptionService:
    """Service for transcribing audio files using OpenAI Whisper API"""

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set in the environment or .env file to use the OpenAI Transcription API.")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        # Using the standard 'whisper-1' model via API
        self.model_name = "whisper-1"
        logger.info(f"TranscriptionService initialized to use OpenAI API with model: {self.model_name}")

    # Removed _load_model as it's not needed for API usage

    def transcribe(self, file_path: Path) -> Tuple[str, str, float, float]:
        """
        Transcribe an audio file using the OpenAI Whisper API.

        Returns:
            - transcript_text: plain text transcript
            - transcript_json: Empty JSON string (API doesn't provide detailed segments)
            - processing_time: how long the API call took
            - confidence: Default confidence score (1.0, as API doesn't provide this)
        """
        logger.info(f"Transcribing file via OpenAI API: {file_path}")

        start_time = time.time()

        try:
            # Ensure file exists before opening
            if not file_path.is_file():
                 raise FileNotFoundError(f"Audio file not found: {file_path}")

            # Open the audio file in binary read mode
            with open(file_path, "rb") as audio_file:
                # Call the OpenAI API
                logger.info(f"Sending {file_path.name} to OpenAI Whisper API ({self.model_name})...")
                transcription = self.client.audio.transcriptions.create(
                    model=self.model_name,
                    file=audio_file,
                    response_format="text" # Request plain text response
                )
                logger.info("Received response from OpenAI API.")

            # The response is directly the transcript text when response_format="text"
            transcript_text = transcription if isinstance(transcription, str) else str(transcription)

            # API doesn't provide detailed segments or confidence like local model
            # Return empty JSON and default confidence
            transcript_json = json.dumps({"text": transcript_text, "segments": []}, ensure_ascii=False, indent=2)
            avg_confidence = 1.0 # Default confidence

            processing_time = time.time() - start_time
            logger.info(f"OpenAI API transcription completed in {processing_time:.2f} seconds")

            return transcript_text, transcript_json, processing_time, avg_confidence

        except Exception as e:
            logger.error(f"Error during OpenAI API transcription: {e}", exc_info=True)
            raise

# Create a singleton instance
transcription_service = TranscriptionService()
