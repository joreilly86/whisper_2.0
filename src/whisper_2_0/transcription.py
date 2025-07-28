"""
Functions for transcribing audio files.
"""

import os
import shutil
from . import audio_processing
from . import api_clients
from . import config


def transcribe_chunks(chunk_files, service="groq"):
    """Transcribe audio chunks using specified service."""
    if not chunk_files:
        return None

    transcribed_texts = []

    try:
        for i, chunk_file_path in enumerate(chunk_files):
            print(
                f"Transcribing chunk {i + 1}/{len(chunk_files)} with {service.title()}..."
            )

            with open(chunk_file_path, "rb") as audio_file_handle:
                if service == "groq" and api_clients.groq_client:
                    transcript = api_clients.groq_client.audio.transcriptions.create(
                        model="whisper-large-v3-turbo",
                        file=audio_file_handle,
                        response_format="text",
                    )
                    transcribed_texts.append(transcript.strip())
                elif service == "openai":
                    transcript = api_clients.client.audio.transcriptions.create(
                        model="whisper-1", file=audio_file_handle
                    )
                    transcribed_texts.append(transcript.text.strip())
                else:
                    print(f"Error: Unsupported transcription service: {service}")
                    return None

        return "\n\n".join(transcribed_texts)

    except Exception as e:
        print(f"Error during {service} transcription: {e}")
        return None


def transcribe_with_groq(file_path):
    """Transcribe audio file using Groq Whisper with chunking if needed."""
    if not api_clients.groq_client:
        print("Warning: GROQ_API_KEY not found, falling back to OpenAI")
        return None

    print(f"Transcribing audio file with Groq: {file_path}")

    try:
        chunk_files = audio_processing.create_audio_chunks(file_path)
        if not chunk_files:
            return None

        result = transcribe_chunks(chunk_files, service="groq")
        return result
    finally:
        # Clean up temp chunks
        if os.path.exists(config.TEMP_CHUNK_SUBDIR):
            shutil.rmtree(config.TEMP_CHUNK_SUBDIR)


def transcribe_audio_file(file_path):
    """Transcribe audio file using Groq Whisper first, then OpenAI as fallback."""
    if not file_path or not os.path.exists(file_path):
        print(f"Error: Invalid file path: {file_path}")
        return None

    print(f"Transcribing audio file: {file_path}")

    # Try Groq first
    transcript = transcribe_with_groq(file_path)
    if transcript:
        return transcript

    print("Groq failed, trying OpenAI...")

    try:
        chunk_files = audio_processing.create_audio_chunks(file_path)
        if not chunk_files:
            return None

        result = transcribe_chunks(chunk_files, service="openai")
        return result
    finally:
        # Clean up temp chunks
        if os.path.exists(config.TEMP_CHUNK_SUBDIR):
            shutil.rmtree(config.TEMP_CHUNK_SUBDIR)
