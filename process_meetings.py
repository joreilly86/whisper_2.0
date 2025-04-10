import logging
import sys
import time
import os
import json
import math
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# Ensure app modules can be imported
sys.path.append(str(Path(__file__).resolve().parent))

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("MeetingProcessor")

# --- Constants ---
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
# Target a slightly smaller chunk to be safe
TARGET_CHUNK_SIZE_MB = 20
TARGET_CHUNK_SIZE_BYTES = TARGET_CHUNK_SIZE_MB * 1024 * 1024

from app.core.config import settings
from app.services.file_watcher import FileWatcherService
from app.services.summarization import summarization_service
from app.services.transcription import transcription_service


def split_audio_file(file_path, max_chunk_size=TARGET_CHUNK_SIZE_BYTES):
    """
    Split a large audio file into smaller chunks using direct byte-based chunking.
    Returns a list of temporary files that caller should delete when done.
    """
    file_size = os.path.getsize(file_path)
    if file_size <= max_chunk_size:
        # No need to split
        return [file_path], False
    
    # Create a temporary directory for chunks
    temp_dir = tempfile.mkdtemp(prefix="audio_chunks_")
    logger.info(f"Created temporary directory for chunks: {temp_dir}")
    
    # For MP3 files, need to be careful about splitting
    # Since we're using OpenAI's API, it can handle some corruption
    # But we should try to be somewhat intelligent about the split
    
    # Estimate the number of chunks needed
    num_chunks = math.ceil(file_size / max_chunk_size)
    bytes_per_chunk = math.ceil(file_size / num_chunks)
    # Ensure bytes_per_chunk is below our target
    if bytes_per_chunk > max_chunk_size:
        num_chunks += 1
        bytes_per_chunk = math.ceil(file_size / num_chunks)
    
    logger.info(f"Splitting {file_path.name} ({file_size / (1024*1024):.2f} MB) into {num_chunks} chunks")
    
    # Read the source file and create chunks
    chunk_files = []
    with open(file_path, 'rb') as src_file:
        for i in range(num_chunks):
            # Calculate this chunk's size
            current_chunk_size = min(bytes_per_chunk, file_size - (i * bytes_per_chunk))
            if current_chunk_size <= 0:
                break
                
            # Create chunk file path
            chunk_path = os.path.join(temp_dir, f"chunk_{i+1}{file_path.suffix}")
            chunk_files.append(chunk_path)
            
            # Read and write the chunk
            chunk_data = src_file.read(current_chunk_size)
            with open(chunk_path, 'wb') as chunk_file:
                chunk_file.write(chunk_data)
                
            logger.info(f"Created chunk {i+1}/{num_chunks}: {os.path.basename(chunk_path)} ({len(chunk_data) / (1024*1024):.2f} MB)")
    
    return chunk_files, True


def cleanup_chunks(chunk_files, created_temp_dir):
    """Clean up temporary chunk files"""
    if created_temp_dir and chunk_files:
        # Get the directory from the first chunk
        temp_dir = os.path.dirname(chunk_files[0])
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary directory {temp_dir}: {e}")


# --- Processing Logic ---
def process_new_file(file_path: Path):
    """Callback function to process a newly detected audio file."""
    logger.info(f"Detected new file: {file_path.name}. Starting processing...")
    transcript_text = None
    full_transcript_text = ""
    total_transcription_time = 0
    chunk_confidences = []  # Store confidence if needed later, currently default 1.0 from API
    chunks_created = False
    chunk_files = []

    try:
        file_size = os.path.getsize(file_path)
        logger.info(f"File size: {file_size / (1024 * 1024):.2f} MB")

        # Split file if needed
        try:
            chunk_files, chunks_created = split_audio_file(file_path)
            
            # Process each chunk
            chunk_texts = []
            for i, chunk_file in enumerate(chunk_files):
                logger.info(f"Processing chunk {i+1}/{len(chunk_files)}: {os.path.basename(chunk_file)}")
                
                # Convert string path to Path object before passing to transcription service
                chunk_path = Path(chunk_file)
                chunk_transcript, _, chunk_time, chunk_conf = transcription_service.transcribe(chunk_path)
                chunk_texts.append(chunk_transcript)
                total_transcription_time += chunk_time
                chunk_confidences.append(chunk_conf)
                
                logger.info(f"Chunk {i+1} transcribed in {chunk_time:.2f}s")
                
            # Combine all chunk transcripts
            full_transcript_text = "\n\n".join(chunk_texts)
            logger.info(f"Finished processing all chunks. Total transcription time: {total_transcription_time:.2f}s")
            
        except Exception as split_err:
            logger.error(f"Error during file splitting/processing: {split_err}", exc_info=True)
            return  # Stop processing this file if splitting fails
        finally:
            # Clean up temporary files if we created them
            if chunks_created:
                cleanup_chunks(chunk_files, chunks_created)

        # Use the combined transcript text
        transcript_text = full_transcript_text
        
        # Calculate average confidence if needed (currently default 1.0 from API)
        avg_confidence = sum(chunk_confidences) / len(chunk_confidences) if chunk_confidences else 1.0

        # Save the final combined transcription text file with date stamp
        today_date = datetime.now().strftime("%Y_%m_%d")
        original_stem = file_path.stem
        transcript_filename = f"{today_date} - {original_stem}.txt"
        transcript_txt_path = settings.TRANSCRIPT_FOLDER / transcript_filename

        with open(transcript_txt_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)
        logger.info(f"Transcription text saved to: {transcript_txt_path}")

    except Exception as e:
        logger.error(f"Error during transcription for {file_path.name}: {e}", exc_info=True)
        return  # Stop processing this file if transcription fails

    try:
        # 2. Summarization (only if transcription succeeded)
        if transcript_text:
            logger.info(f"Starting summarization for {file_path.name}...")
            # Add specific instructions for engineering meetings
            prompt_context = (
                "You are a senior engineering analyst summarizing technical and project coordination meetings. "
                "Structure the summary as formal meeting minutes with these sections:\n"
                "- Meeting Title (if discernible)\n"
                "- Date & Time (if mentioned)\n"
                "- Attendees and Roles (especially noting KP vs other parties)\n"
                "- Purpose of Meeting\n"
                "- Discussion Summary (use subheadings for multiple topics)\n"
                "- Decisions Made\n"
                "- Action Items (with assignees and deadlines)\n"
                "- Next Steps / Follow-Up\n\n"
                "Use correct engineering terminology. Focus on technical details, design constraints, "
                "and coordination needs. Remove conversational filler. Distinguish between decisions "
                "and open items. Format for clarity using bullet points where appropriate."
            )
            # Removed context=prompt_context as the service doesn't accept it
            summary_text, summary_data, summ_time = summarization_service.summarize(
                transcript_text
            )
            logger.info(f"Summarization complete for {file_path.name}. Time: {summ_time:.2f}s")

            # Save summary text file with date stamp
            today_date = datetime.now().strftime("%Y_%m_%d")
            original_stem = file_path.stem
            summary_filename = f"{today_date} - {original_stem}_summary.txt"
            summary_txt_path = settings.SUMMARY_FOLDER / summary_filename

            with open(summary_txt_path, "w", encoding="utf-8") as f:
                f.write(summary_text)
            logger.info(f"Summary text saved to: {summary_txt_path}")

    except Exception as e:
        logger.error(f"Error during summarization for {file_path.name}: {e}", exc_info=True)

    finally:
        logger.info(f"Finished processing attempt for: {file_path.name}")


# --- Main Execution ---
if __name__ == "__main__":
    logger.info("Starting Streamlined Meeting Processor...")
    logger.info(f"Watching directory: {settings.UPLOAD_FOLDER}")

    # Ensure target directories exist
    settings.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    settings.TRANSCRIPT_FOLDER.mkdir(parents=True, exist_ok=True)
    settings.SUMMARY_FOLDER.mkdir(parents=True, exist_ok=True)
    logger.info("Upload, transcript, and summary directories checked/created.")

    # Check for API keys needed for summarization
    api_key_ok = False
    if settings.DEFAULT_SUMMARY_MODEL == "openai":
        if settings.OPENAI_API_KEY:
            logger.info("OpenAI API key found. Using OpenAI for summarization.")
            api_key_ok = True
        else:
            logger.warning(
                "DEFAULT_SUMMARY_MODEL is 'openai' but OPENAI_API_KEY is missing in '.env'. Summarization will fail."
            )
    elif settings.DEFAULT_SUMMARY_MODEL == "anthropic":
        if settings.ANTHROPIC_API_KEY:
            logger.info("Anthropic API key found. Using Anthropic for summarization.")
            api_key_ok = True
        else:
            logger.warning(
                "DEFAULT_SUMMARY_MODEL is 'anthropic' but ANTHROPIC_API_KEY is missing in '.env'. Summarization will fail."
            )
    else:
        logger.error(
            f"Invalid DEFAULT_SUMMARY_MODEL configured: {settings.DEFAULT_SUMMARY_MODEL}"
        )

    # Initialize and start the file watcher
    # Note: Using the FileWatcherService from app.services which uses watchdog
    watcher_service = FileWatcherService(process_callback=process_new_file)
    watcher_service.start()

    logger.info("File watcher started. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping file watcher...")
        watcher_service.stop()
        logger.info("File watcher stopped.")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred in the main loop: {e}", exc_info=True
        )
        watcher_service.stop()

    logger.info("Streamlined Meeting Processor finished.")
