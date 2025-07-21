#!/usr/bin/env python3
"""
Voice Note Processor - Manual queue-based transcription and Notion integration.
Usage: python process_voice_notes.py [audio_file_or_url] [additional_files...]
"""

import argparse
import glob
import math
import os
import shutil
import sys
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from queue import Queue

import google.generativeai as genai
from dotenv import load_dotenv
from notion_client import Client
from openai import OpenAI
from plyer import notification
from pydub import AudioSegment
from pydub.utils import which
import groq

# Load environment variables
load_dotenv()

# Configure ffmpeg path for pydub - Windows paths
AudioSegment.converter = "ffmpeg"
AudioSegment.ffmpeg = "ffmpeg"
AudioSegment.ffprobe = "ffprobe"

# Configuration
MAX_CHUNK_SIZE_BYTES = 24.5 * 1024 * 1024  # 24.5 MB
TARGET_BITRATE_KBPS = "192k"
TEMP_CHUNK_SUBDIR = "temp_voice_chunks"
POST_PROCESSING_PROMPT_FILE = "post_processing_prompt.txt"
BACKUP_FOLDER = "transcription_backups"
QUEUE_FILE = "processing_queue.txt"
TEMP_DOWNLOAD_DIR = "temp_downloads"
DEFAULT_VOICE_FOLDER = r"G:\My Drive\Voice Notes"

# Initialize API clients
openai_api_key = os.getenv("OPENAI_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")
notion_api_key = os.getenv("NOTION_API_KEY")
notion_database_id = os.getenv("NOTION_DATABASE_ID")

if not openai_api_key:
    print("Error: OPENAI_API_KEY not found in .env file")
    sys.exit(1)

if not notion_api_key:
    print("Error: NOTION_API_KEY not found in .env file")
    sys.exit(1)

if not notion_database_id:
    print("Error: NOTION_DATABASE_ID not found in .env file")
    sys.exit(1)

client = OpenAI(api_key=openai_api_key)
notion = Client(auth=notion_api_key)

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

if groq_api_key:
    groq_client = groq.Groq(api_key=groq_api_key)

# Clean up temp download directory on startup
if os.path.exists(TEMP_DOWNLOAD_DIR):
    shutil.rmtree(TEMP_DOWNLOAD_DIR)


def show_notification(title, message, timeout=10):
    """Show Windows notification."""
    try:
        notification.notify(
            title=title,
            message=message,
            timeout=timeout,
            app_name="Voice Note Monitor",
            app_icon=None,
        )
    except Exception as e:
        print(f"Failed to show notification: {e}")


def show_success_notification(filename):
    """Show success notification for processed voice note."""
    show_notification(
        title="[SUCCESS] Voice Note Processed",
        message=f"Successfully transcribed and added to Notion:\n{filename}",
        timeout=15,
    )


def show_error_notification(filename, error_msg):
    """Show error notification for failed voice note processing."""
    show_notification(
        title="[ERROR] Voice Note Processing Failed",
        message=f"Failed to process: {filename}\nError: {error_msg}",
        timeout=20,
    )


def estimate_segment_duration_ms(
    audio_duration_ms, audio_channels, target_bitrate_kbps_str, max_size_bytes
):
    """Estimate optimal segment duration for audio chunking."""
    try:
        target_bitrate_kbps = int(target_bitrate_kbps_str.replace("k", ""))
    except ValueError:
        print(f"Error: Invalid target bitrate format: {target_bitrate_kbps_str}")
        return None

    if target_bitrate_kbps <= 0:
        print(f"Error: Target bitrate must be positive. Got: {target_bitrate_kbps_str}")
        return None

    bytes_per_second_at_target_bitrate = (target_bitrate_kbps * 1000) / 8

    if bytes_per_second_at_target_bitrate <= 0:
        print("Error: Calculated bytes_per_second_at_target_bitrate is not positive.")
        return None

    max_duration_seconds_for_chunk = max_size_bytes / bytes_per_second_at_target_bitrate
    estimated_chunk_duration_ms = math.floor(max_duration_seconds_for_chunk * 1000)

    return min(estimated_chunk_duration_ms, audio_duration_ms)


def transcribe_with_groq(file_path):
    """Transcribe audio file using Groq Whisper with chunking if needed."""
    if not groq_api_key:
        print("Warning: GROQ_API_KEY not found, falling back to OpenAI")
        return None

    print(f"Transcribing audio file with Groq: {file_path}")

    # Clean up any existing temp chunks
    if os.path.exists(TEMP_CHUNK_SUBDIR):
        shutil.rmtree(TEMP_CHUNK_SUBDIR)
    os.makedirs(TEMP_CHUNK_SUBDIR, exist_ok=True)

    transcribed_texts = []
    chunk_files = []

    try:
        # Load audio file
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        audio = AudioSegment.from_file(file_path, format=ext[1:])
        audio_duration_ms = len(audio)

        # Estimate chunk duration
        segment_duration_ms = estimate_segment_duration_ms(
            audio_duration_ms, audio.channels, TARGET_BITRATE_KBPS, MAX_CHUNK_SIZE_BYTES
        )

        if not segment_duration_ms or segment_duration_ms <= 0:
            print("Error: Could not estimate segment duration.")
            return None

        # Split audio into chunks
        num_chunks = math.ceil(audio_duration_ms / segment_duration_ms)
        print(f"Splitting into {num_chunks} chunks...")

        for i in range(num_chunks):
            start_ms = i * segment_duration_ms
            end_ms = min((i + 1) * segment_duration_ms, audio_duration_ms)
            if start_ms >= end_ms:
                continue

            chunk = audio[start_ms:end_ms]
            chunk_file_path = os.path.join(TEMP_CHUNK_SUBDIR, f"chunk_{i:03d}.mp3")
            chunk.export(chunk_file_path, format="mp3", bitrate=TARGET_BITRATE_KBPS)
            chunk_files.append(chunk_file_path)

        if not chunk_files:
            print("No audio chunks were generated.")
            return None

        # Transcribe each chunk
        print(f"Starting Groq transcription for {len(chunk_files)} chunks...")
        for i, chunk_file_path in enumerate(chunk_files):
            print(f"Transcribing chunk {i + 1}/{len(chunk_files)}...")
            with open(chunk_file_path, "rb") as audio_file_handle:
                transcript = groq_client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo",
                    file=audio_file_handle,
                    response_format="text"
                )
            transcribed_texts.append(transcript.strip())

        # Combine all transcripts
        full_transcript = "\n\n".join(transcribed_texts)
        return full_transcript

    except Exception as e:
        print(f"Error during Groq transcription: {e}")
        return None
    finally:
        # Clean up temp chunks
        if os.path.exists(TEMP_CHUNK_SUBDIR):
            shutil.rmtree(TEMP_CHUNK_SUBDIR)


def transcribe_audio_file(file_path):
    """Transcribe audio file using Groq Whisper first, then OpenAI as fallback."""
    print(f"Transcribing audio file: {file_path}")

    # Try Groq first
    transcript = transcribe_with_groq(file_path)
    if transcript:
        return transcript

    print("Groq failed, trying OpenAI...")
    
    # Clean up any existing temp chunks
    if os.path.exists(TEMP_CHUNK_SUBDIR):
        shutil.rmtree(TEMP_CHUNK_SUBDIR)
    os.makedirs(TEMP_CHUNK_SUBDIR, exist_ok=True)

    transcribed_texts = []
    chunk_files = []

    try:
        # Load audio file
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        audio = AudioSegment.from_file(file_path, format=ext[1:])
        audio_duration_ms = len(audio)

        # Estimate chunk duration
        segment_duration_ms = estimate_segment_duration_ms(
            audio_duration_ms, audio.channels, TARGET_BITRATE_KBPS, MAX_CHUNK_SIZE_BYTES
        )

        if not segment_duration_ms or segment_duration_ms <= 0:
            print("Error: Could not estimate segment duration.")
            return None

        # Split audio into chunks
        num_chunks = math.ceil(audio_duration_ms / segment_duration_ms)
        print(f"Splitting into {num_chunks} chunks...")

        for i in range(num_chunks):
            start_ms = i * segment_duration_ms
            end_ms = min((i + 1) * segment_duration_ms, audio_duration_ms)
            if start_ms >= end_ms:
                continue

            chunk = audio[start_ms:end_ms]
            chunk_file_path = os.path.join(TEMP_CHUNK_SUBDIR, f"chunk_{i:03d}.mp3")
            chunk.export(chunk_file_path, format="mp3", bitrate=TARGET_BITRATE_KBPS)
            chunk_files.append(chunk_file_path)

        if not chunk_files:
            print("No audio chunks were generated.")
            return None

        # Transcribe each chunk
        print(f"Starting OpenAI transcription for {len(chunk_files)} chunks...")
        for i, chunk_file_path in enumerate(chunk_files):
            print(f"Transcribing chunk {i + 1}/{len(chunk_files)}...")
            with open(chunk_file_path, "rb") as audio_file_handle:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file_handle
                )
            transcribed_texts.append(transcript.text.strip())

        # Combine all transcripts
        full_transcript = "\n\n".join(transcribed_texts)
        return full_transcript

    except Exception as e:
        print(f"Error during OpenAI transcription: {e}")
        return None
    finally:
        # Clean up temp chunks
        if os.path.exists(TEMP_CHUNK_SUBDIR):
            shutil.rmtree(TEMP_CHUNK_SUBDIR)


def summarize_with_gemini(text):
    """Summarize text using Gemini API with post-processing prompt."""
    if not gemini_api_key:
        print("Warning: GEMINI_API_KEY not found, skipping Gemini summarization")
        return None

    print("Summarizing text with Gemini...")
    try:
        model = genai.GenerativeModel("gemini-2.5-pro")

        # Load the post-processing prompt
        if os.path.exists("scripts/processing_prompt.md"):
            with open("scripts/processing_prompt.md", "r", encoding="utf-8") as f:
                prompt_text = f.read()
        elif os.path.exists(POST_PROCESSING_PROMPT_FILE):
            with open(POST_PROCESSING_PROMPT_FILE, "r", encoding="utf-8") as f:
                prompt_text = f.read()
        else:
            prompt_text = (
                "Act as an expert meeting assistant. "
                "Create a structured summary of the following voice note transcript. "
                "Include a title, key discussion points, and any action items mentioned. "
                "Format the response in a clear, professional manner suitable for Notion."
            )

        response = model.generate_content(prompt_text + "\n\n" + text)
        return response.text
    except Exception as e:
        print(f"Error during Gemini summarization: {e}")
        return None


def summarize_with_openai(text):
    """Summarize text using OpenAI GPT-4 as fallback with post-processing prompt."""
    print("Summarizing text with OpenAI GPT-4...")
    try:
        # Load the post-processing prompt
        if os.path.exists("scripts/processing_prompt.md"):
            with open("scripts/processing_prompt.md", "r", encoding="utf-8") as f:
                prompt_text = f.read()
        elif os.path.exists(POST_PROCESSING_PROMPT_FILE):
            with open(POST_PROCESSING_PROMPT_FILE, "r", encoding="utf-8") as f:
                prompt_text = f.read()
        else:
            prompt_text = (
                "Act as an expert meeting assistant. "
                "Create a structured summary of voice note transcripts. "
                "Include a title, key discussion points, and any action items mentioned. "
                "Format the response in a clear, professional manner suitable for Notion."
            )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt_text},
                {"role": "user", "content": text},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error during OpenAI summarization: {e}")
        return None


def save_backup_markdown(title, content, original_filename):
    """Save a local markdown backup of the transcription."""
    try:
        # Create backup folder if it doesn't exist
        os.makedirs(BACKUP_FOLDER, exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        backup_filename = f"{timestamp}_{safe_title}.md"
        backup_path = os.path.join(BACKUP_FOLDER, backup_filename)
        
        # Create markdown content
        markdown_content = f"# {title}\n\n"
        markdown_content += f"**Original File:** {original_filename}\n"
        markdown_content += f"**Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        markdown_content += "---\n\n"
        markdown_content += content
        
        # Save to file
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        print(f"[BACKUP] Backup saved: {backup_filename}")
        return backup_path
    except Exception as e:
        print(f"Warning: Failed to save backup: {e}")
        return None


def add_to_notion(title, content):
    """Add summarized content to Notion database."""
    print(f"Adding '{title}' to Notion...")
    try:
        meeting_date = datetime.now().strftime("%Y-%m-%d")

        # Split content into chunks of 2000 characters to respect Notion's limit
        max_chunk_size = 2000
        content_chunks = []
        
        for i in range(0, len(content), max_chunk_size):
            chunk = content[i:i + max_chunk_size]
            content_chunks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                },
            })

        response = notion.pages.create(
            parent={"database_id": notion_database_id},
            properties={
                "Title": {"title": [{"text": {"content": title}}]},
                "Meeting Date": {"date": {"start": meeting_date}},
            },
            children=content_chunks,
        )
        print("Successfully added to Notion.")
        return response
    except Exception as e:
        print(f"Error adding to Notion: {e}")
        return None


def is_temp_file(file_path):
    """Check if a file is likely a temporary recording in progress."""
    filename = os.path.basename(file_path).lower()
    
    # Common temp file patterns
    temp_patterns = [
        'temp',
        'tmp',
        'recording',
        'rec_',
        '.part',
        '.tmp',
        '~',
        'untitled',
        'new recording',
        'voice memo'
    ]
    
    # Check if filename contains temp patterns
    for pattern in temp_patterns:
        if pattern in filename:
            return True
    
    # Check if file was modified very recently (within last 30 seconds)
    # This catches files that might still be actively recording
    try:
        file_mtime = os.path.getmtime(file_path)
        current_time = datetime.now().timestamp()
        if current_time - file_mtime < 30:  # 30 seconds
            return True
    except OSError:
        pass
    
    return False


def download_audio_file(url, temp_dir):
    """Download audio file from URL to temp directory."""
    try:
        # Create temp directory if it doesn't exist
        os.makedirs(temp_dir, exist_ok=True)
        
        # Extract filename from URL or create one
        filename = url.split('/')[-1]
        if '.' not in filename:
            filename = f"downloaded_audio_{int(time.time())}.mp3"
        
        filepath = os.path.join(temp_dir, filename)
        
        print(f"[DOWNLOAD] Downloading: {url}")
        urllib.request.urlretrieve(url, filepath)
        print(f"[SUCCESS] Downloaded to: {filepath}")
        
        return filepath
    except Exception as e:
        print(f"[ERROR] Failed to download {url}: {e}")
        return None


def load_queue():
    """Load processing queue from file."""
    queue_items = []
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    queue_items.append(line)
    return queue_items


def save_queue(queue_items):
    """Save processing queue to file."""
    with open(QUEUE_FILE, "w") as f:
        f.write("# Voice Note Processing Queue\n")
        f.write("# Format: file_path_or_url\n")
        f.write("# Lines starting with # are comments\n\n")
        for item in queue_items:
            f.write(f"{item}\n")


def add_to_queue(items):
    """Add items to processing queue."""
    current_queue = load_queue()
    
    for item in items:
        if item not in current_queue:
            current_queue.append(item)
            print(f"[QUEUE] Added to queue: {item}")
        else:
            print(f"[WARNING] Already in queue: {item}")
    
    save_queue(current_queue)
    return current_queue


def remove_from_queue(item):
    """Remove item from processing queue."""
    current_queue = load_queue()
    if item in current_queue:
        current_queue.remove(item)
        save_queue(current_queue)
        print(f"[SUCCESS] Removed from queue: {item}")
    return current_queue


def is_url(item):
    """Check if item is a URL."""
    return item.startswith(('http://', 'https://'))


def get_available_files(folder_path=DEFAULT_VOICE_FOLDER):
    """Get all available audio files in the folder, excluding processed ones."""
    if not os.path.exists(folder_path):
        return []
    
    audio_extensions = (".mp3", ".wav", ".m4a", ".flac", ".ogg")
    
    # Load processed files
    processed_files = set()
    if os.path.exists("processed_files.txt"):
        with open("processed_files.txt", "r", encoding="utf-8") as f:
            processed_files = {line.strip() for line in f}
    
    # Find all audio files
    all_files = []
    for ext in audio_extensions:
        pattern = os.path.join(folder_path, f"*{ext}")
        all_files.extend(glob.glob(pattern, recursive=False))
    
    # Filter out processed files and temp files
    available_files = []
    for file_path in all_files:
        if file_path not in processed_files and not is_temp_file(file_path):
            available_files.append(file_path)
    
    # Sort by modification time (newest first)
    available_files.sort(key=os.path.getmtime, reverse=True)
    return available_files


def get_latest_file(folder_path=DEFAULT_VOICE_FOLDER):
    """Get the latest unprocessed file in the folder."""
    available_files = get_available_files(folder_path)
    return available_files[0] if available_files else None


def resolve_file_path(item):
    """Resolve file path from queue item (URL or local path)."""
    if is_url(item):
        # Download the file
        downloaded_file = download_audio_file(item, TEMP_DOWNLOAD_DIR)
        return downloaded_file
    else:
        # Local file path
        if os.path.exists(item):
            return item
        else:
            print(f"[ERROR] File not found: {item}")
            return None


def mark_as_processed(file_path, processed_log):
    """Mark a file as processed."""
    with open(processed_log, "a") as f:
        f.write(f"{file_path}\n")


def process_file(file_path, processed_log):
    """Process a single audio file."""
    print(f"Processing: {os.path.basename(file_path)}")

    try:
        # Step 1: Transcribe
        transcript = transcribe_audio_file(file_path)
        if not transcript:
            error_msg = "Failed to transcribe audio"
            print(f"[ERROR] {error_msg}")
            show_error_notification(os.path.basename(file_path), error_msg)
            return False

        # Step 2: Summarize
        summary = summarize_with_gemini(transcript)
        if not summary:
            print("Gemini failed, trying OpenAI...")
            summary = summarize_with_openai(transcript)

        if not summary:
            print("Both AI services failed, using raw transcript...")
            summary = transcript

        # Step 3: Save backup markdown
        title = os.path.splitext(os.path.basename(file_path))[0]
        original_filename = os.path.basename(file_path)
        backup_path = save_backup_markdown(title, summary, original_filename)
        
        # Step 4: Add to Notion
        result = add_to_notion(title, summary)

        # Mark as processed if we have a backup (transcription succeeded)
        if backup_path:
            mark_as_processed(file_path, processed_log)
            print(f"[SUCCESS] Successfully processed: {title}")
            
            if result:
                show_success_notification(title)
            else:
                print(f"[WARNING] Notion failed but backup saved at: {backup_path}")
                show_error_notification(title, "Notion failed but backup saved")
            return True
        else:
            error_msg = "Failed to transcribe and backup"
            print(f"[ERROR] {error_msg}")
            show_error_notification(title, error_msg)
            return False

    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Error processing {file_path}: {e}")
        show_error_notification(os.path.basename(file_path), error_msg)
        return False


def process_queue_item(item):
    """Process a single item from the queue."""
    print(f"\n[PROCESSING] Processing: {item}")
    
    # Resolve file path (download if URL)
    file_path = resolve_file_path(item)
    if not file_path:
        return False
    
    try:
        # Process the file
        success = process_file(file_path, "processed_files.txt")
        
        # Clean up downloaded file if it was a URL
        if is_url(item) and file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"[CLEAR] Cleaned up temporary file: {file_path}")
        
        return success
    except Exception as e:
        print(f"[ERROR] Error processing {item}: {e}")
        return False


def interactive_mode():
    """Interactive mode for adding files and processing queue."""
    print("\n[INTERACTIVE] Interactive Mode - Voice Note Processor")
    print("Commands:")
    print("  add <file_or_url> - Add file or URL to queue")
    print("  latest - Process the latest file from voice notes folder")
    print("  select - Select files from voice notes folder")
    print("  queue - Show current queue")
    print("  process - Process next item in queue")
    print("  process_all - Process all items in queue")
    print("  p - Process selected files")
    print("  clear - Clear the queue")
    print("  quit - Exit interactive mode")
    print("  OR: Paste file path directly to process immediately")
    print()
    
    while True:
        try:
            command = input(">> ").strip()
            
            if command.lower() in ['quit', 'exit', 'q']:
                print("[GOODBYE] Goodbye!")
                break
            
            elif command.lower() == 'queue':
                current_queue = load_queue()
                if current_queue:
                    print(f"\n[QUEUE] Current queue ({len(current_queue)} items):")
                    for i, item in enumerate(current_queue, 1):
                        print(f"  {i}. {item}")
                else:
                    print("[QUEUE] Queue is empty")
            
            elif command.lower() == 'clear':
                save_queue([])
                print("[CLEAR] Queue cleared")
            
            elif command.lower() == 'process':
                current_queue = load_queue()
                if current_queue:
                    item = current_queue[0]
                    if process_queue_item(item):
                        remove_from_queue(item)
                        print(f"[SUCCESS] Successfully processed and removed: {item}")
                    else:
                        print(f"[ERROR] Failed to process: {item}")
                        response = input("Remove from queue anyway? (y/n): ").strip().lower()
                        if response in ['y', 'yes']:
                            remove_from_queue(item)
                else:
                    print("[QUEUE] Queue is empty")
            
            elif command.lower() == 'process_all':
                current_queue = load_queue()
                if not current_queue:
                    print("[QUEUE] Queue is empty")
                    continue
                
                print(f"[RUNNING] Processing {len(current_queue)} items...")
                success_count = 0
                
                for item in current_queue.copy():  # Copy to avoid modification during iteration
                    if process_queue_item(item):
                        remove_from_queue(item)
                        success_count += 1
                    else:
                        print(f"[ERROR] Failed to process: {item}")
                        response = input("Remove from queue anyway? (y/n): ").strip().lower()
                        if response in ['y', 'yes']:
                            remove_from_queue(item)
                
                print(f"\n[RESULTS] Results: {success_count}/{len(current_queue)} items processed successfully")
                
                # Show summary notification
                if success_count > 0:
                    notification.notify(
                        title="[COMPLETE] Voice Note Processing Complete",
                        message=f"Successfully processed {success_count} items",
                        timeout=10,
                        app_name="Voice Note Processor",
                    )
            
            elif command.lower() == 'latest':
                latest_file = get_latest_file()
                if latest_file:
                    filename = os.path.basename(latest_file)
                    print(f"\n[FILE] Latest file: {filename}")
                    response = input("Process this file? (y/n): ").strip().lower()
                    if response in ['y', 'yes']:
                        if process_queue_item(latest_file):
                            print(f"[SUCCESS] Successfully processed: {filename}")
                        else:
                            print(f"[ERROR] Failed to process: {filename}")
                    else:
                        print("Skipped")
                else:
                    print("[ERROR] No unprocessed files found in voice notes folder")
            
            elif command.lower() == 'select':
                available_files = get_available_files()
                if not available_files:
                    print("[ERROR] No unprocessed files found in voice notes folder")
                    continue
                
                print(f"\n[FOLDER] Available files ({len(available_files)} total):")
                selected_files = []
                
                for i, file_path in enumerate(available_files, 1):
                    filename = os.path.basename(file_path)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M')
                    print(f"  {i}. {filename} ({file_time})")
                    
                    while True:
                        response = input(f"Select '{filename}'? (y/n): ").strip().lower()
                        if response in ['y', 'yes']:
                            selected_files.append(file_path)
                            print(f"[SUCCESS] Selected: {filename}")
                            break
                        elif response in ['n', 'no']:
                            print(f"[SKIP] Skipped: {filename}")
                            break
                        else:
                            print("Please enter 'y' or 'n'")
                
                if selected_files:
                    add_to_queue(selected_files)
                    print(f"\n[QUEUE] Added {len(selected_files)} files to queue")
                    print("Type 'p' to process selected files")
                else:
                    print("No files selected")
            
            elif command.lower() == 'p':
                current_queue = load_queue()
                if not current_queue:
                    print("[QUEUE] Queue is empty")
                    continue
                
                print(f"[RUNNING] Processing {len(current_queue)} items...")
                success_count = 0
                
                for item in current_queue.copy():
                    if process_queue_item(item):
                        remove_from_queue(item)
                        success_count += 1
                    else:
                        print(f"[ERROR] Failed to process: {item}")
                        response = input("Remove from queue anyway? (y/n): ").strip().lower()
                        if response in ['y', 'yes']:
                            remove_from_queue(item)
                
                print(f"\n[RESULTS] Results: {success_count}/{len(current_queue)} items processed successfully")
                
                if success_count > 0:
                    notification.notify(
                        title="[COMPLETE] Voice Note Processing Complete",
                        message=f"Successfully processed {success_count} items",
                        timeout=10,
                        app_name="Voice Note Processor",
                    )
            
            elif command.startswith('add '):
                item = command[4:].strip()
                # Remove quotes if present
                if item.startswith('"') and item.endswith('"'):
                    item = item[1:-1]
                elif item.startswith("'") and item.endswith("'"):
                    item = item[1:-1]
                if item:
                    add_to_queue([item])
                else:
                    print("[ERROR] Please provide a file path or URL")
            
            else:
                # Check if the command is a file path (starts with a drive letter or quote)
                stripped_command = command.strip()
                if stripped_command.startswith('"') and stripped_command.endswith('"'):
                    stripped_command = stripped_command[1:-1]
                elif stripped_command.startswith("'") and stripped_command.endswith("'"):
                    stripped_command = stripped_command[1:-1]
                
                # Check if it's a file path
                if (stripped_command and 
                    (os.path.exists(stripped_command) or 
                     stripped_command.startswith(('http://', 'https://')) or
                     (len(stripped_command) > 2 and stripped_command[1] == ':'))):  # Windows drive letter
                    
                    print(f"[PROCESSING] Processing file directly: {stripped_command}")
                    if process_queue_item(stripped_command):
                        print(f"[SUCCESS] Successfully processed: {os.path.basename(stripped_command)}")
                    else:
                        print(f"[ERROR] Failed to process: {os.path.basename(stripped_command)}")
                else:
                    print("[ERROR] Unknown command. Type 'quit' to exit.")
        
        except KeyboardInterrupt:
            print("\n[GOODBYE] Goodbye!")
            break
        except Exception as e:
            print(f"[ERROR] Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Manual queue-based voice note processor")
    parser.add_argument(
        "files",
        nargs="*",
        help="Audio files or URLs to add to queue and process"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--queue-only",
        action="store_true",
        help="Only add to queue, don't process"
    )
    parser.add_argument(
        "--process-queue",
        action="store_true",
        help="Process all items in the queue"
    )
    parser.add_argument(
        "--show-queue",
        action="store_true",
        help="Show current queue"
    )
    parser.add_argument(
        "--clear-queue",
        action="store_true",
        help="Clear the queue"
    )

    args = parser.parse_args()

    # Handle queue operations
    if args.clear_queue:
        save_queue([])
        print("[CLEAR] Queue cleared")
        return
    
    if args.show_queue:
        current_queue = load_queue()
        if current_queue:
            print(f"[QUEUE] Current queue ({len(current_queue)} items):")
            for i, item in enumerate(current_queue, 1):
                print(f"  {i}. {item}")
        else:
            print("[QUEUE] Queue is empty")
        return
    
    # Add files to queue
    if args.files:
        current_queue = add_to_queue(args.files)
        
        if args.queue_only:
            print(f"[QUEUE] Added {len(args.files)} items to queue")
            return
    
    # Process queue
    if args.process_queue:
        current_queue = load_queue()
        if not current_queue:
            print("[QUEUE] Queue is empty")
            return
        
        print(f"[RUNNING] Processing {len(current_queue)} items...")
        success_count = 0
        
        for item in current_queue.copy():
            if process_queue_item(item):
                remove_from_queue(item)
                success_count += 1
        
        print(f"\n[RESULTS] Results: {success_count}/{len(current_queue)} items processed successfully")
        
        # Show summary notification
        if success_count > 0:
            notification.notify(
                title="[COMPLETE] Voice Note Processing Complete",
                message=f"Successfully processed {success_count} items",
                timeout=10,
                app_name="Voice Note Processor",
            )
        return
    
    # Interactive mode
    if args.interactive or (not args.files and not args.process_queue):
        interactive_mode()
        return
    
    # Default: add files and process them
    if args.files:
        print(f"[RUNNING] Processing {len(args.files)} items...")
        success_count = 0
        
        for item in args.files:
            if process_queue_item(item):
                success_count += 1
        
        print(f"\n[RESULTS] Results: {success_count}/{len(args.files)} items processed successfully")
        
        # Show summary notification
        if success_count > 0:
            notification.notify(
                title="[COMPLETE] Voice Note Processing Complete",
                message=f"Successfully processed {success_count} items",
                timeout=10,
                app_name="Voice Note Processor",
            )


if __name__ == "__main__":
    main()