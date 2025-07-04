#!/usr/bin/env python3

import os
import sys
import time
import math
import shutil
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from notion_client import Client
from pydub import AudioSegment
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from openai import OpenAI
from plyer import notification

# Load environment variables
load_dotenv()

# API Keys from environment
openai_api_key = os.getenv("OPENAI_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")
notion_api_key = os.getenv("NOTION_API_KEY")
notion_database_id = os.getenv("NOTION_DATABASE_ID")

# Configuration
FOLDER_TO_MONITOR = os.getenv("VOICE_NOTES_FOLDER", r'G:\My Drive\Voice Notes')
MAX_CHUNK_SIZE_BYTES = 24.5 * 1024 * 1024  # 24.5 MB
TARGET_BITRATE_KBPS = "192k"
TEMP_CHUNK_SUBDIR = "temp_voice_chunks"

# Validate required environment variables
if not openai_api_key:
    print("Error: OPENAI_API_KEY not found in .env file")
    sys.exit(1)

if not notion_api_key:
    print("Error: NOTION_API_KEY not found in .env file")
    sys.exit(1)

if not notion_database_id:
    print("Error: NOTION_DATABASE_ID not found in .env file")
    sys.exit(1)

# Initialize clients
client = OpenAI(api_key=openai_api_key)
notion = Client(auth=notion_api_key)

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

def show_notification(title, message, timeout=10):
    """Show Windows notification."""
    try:
        notification.notify(
            title=title,
            message=message,
            timeout=timeout,
            app_name="Voice Note Monitor",
            app_icon=None  # Uses default system icon
        )
    except Exception as e:
        print(f"Failed to show notification: {e}")

def show_success_notification(filename):
    """Show success notification for processed voice note."""
    show_notification(
        title="✅ Voice Note Processed",
        message=f"Successfully transcribed and added to Notion:\n{filename}",
        timeout=15
    )

def show_error_notification(filename, error_msg):
    """Show error notification for failed voice note processing."""
    show_notification(
        title="❌ Voice Note Processing Failed",
        message=f"Failed to process: {filename}\nError: {error_msg}",
        timeout=20
    )

def estimate_segment_duration_ms(audio_duration_ms, audio_channels, target_bitrate_kbps_str, max_size_bytes):
    """Estimate optimal segment duration for audio chunking."""
    try:
        target_bitrate_kbps = int(target_bitrate_kbps_str.replace('k', ''))
    except ValueError:
        print(f"Error: Invalid target bitrate format: {target_bitrate_kbps_str}")
        return None

    if target_bitrate_kbps <= 0:
        print(f"Error: Target bitrate must be positive. Got: {target_bitrate_kbps_str}")
        return None
        
    bytes_per_second_at_target_bitrate = (target_bitrate_kbps * 1000) / 8
    
    if bytes_per_second_at_target_bitrate <= 0:
        print(f"Error: Calculated bytes_per_second_at_target_bitrate is not positive.")
        return None

    max_duration_seconds_for_chunk = max_size_bytes / bytes_per_second_at_target_bitrate
    estimated_chunk_duration_ms = math.floor(max_duration_seconds_for_chunk * 1000)
    
    return min(estimated_chunk_duration_ms, audio_duration_ms)

def transcribe_audio_file(file_path):
    """Transcribe audio file using OpenAI Whisper with chunking if needed."""
    print(f"Transcribing audio file: {file_path}")
    
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
        print(f"Starting transcription for {len(chunk_files)} chunks...")
        for i, chunk_file_path in enumerate(chunk_files):
            print(f"Transcribing chunk {i+1}/{len(chunk_files)}...")
            with open(chunk_file_path, "rb") as audio_file_handle:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file_handle
                )
            transcribed_texts.append(transcript.text.strip())
        
        # Combine all transcripts
        full_transcript = "\n\n".join(transcribed_texts)
        return full_transcript
        
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None
    finally:
        # Clean up temp chunks
        if os.path.exists(TEMP_CHUNK_SUBDIR):
            shutil.rmtree(TEMP_CHUNK_SUBDIR)

def summarize_with_gemini(text):
    """Summarize text using Gemini API."""
    if not gemini_api_key:
        print("Warning: GEMINI_API_KEY not found, skipping Gemini summarization")
        return None
    
    print("Summarizing text with Gemini...")
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        prompt = (
            "Act as an expert meeting assistant. "
            "Create a structured summary of the following voice note transcript. "
            "Include a title, key discussion points, and any action items mentioned. "
            "Format the response in a clear, professional manner suitable for Notion.\n\n"
            f"TRANSCRIPT:\n{text}"
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error during Gemini summarization: {e}")
        return None

def summarize_with_openai(text):
    """Summarize text using OpenAI GPT-4 as fallback."""
    print("Summarizing text with OpenAI GPT-4...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Act as an expert meeting assistant. "
                        "Create a structured summary of voice note transcripts. "
                        "Include a title, key discussion points, and any action items mentioned. "
                        "Format the response in a clear, professional manner suitable for Notion."
                    )
                },
                {
                    "role": "user",
                    "content": f"Please summarize this voice note transcript:\n\n{text}"
                }
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error during OpenAI summarization: {e}")
        return None

def add_to_notion(title, content):
    """Add summarized content to Notion database."""
    print(f"Adding '{title}' to Notion...")
    try:
        meeting_date = datetime.now().strftime("%Y-%m-%d")
        
        response = notion.pages.create(
            parent={"database_id": notion_database_id},
            properties={
                # Title property
                "Title": {"title": [{"text": {"content": title}}]},
                
                # Meeting Date property
                "Meeting Date": {"date": {"start": meeting_date}},
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content}}]
                    }
                }
            ]
        )
        print("Successfully added to Notion.")
        return response
    except Exception as e:
        print(f"Error adding to Notion: {e}")
        return None

def process_new_audio(file_path):
    """Main workflow for processing new audio files."""
    print(f"Processing new voice note: {file_path}")
    
    try:
        # Step 1: Transcribe audio
        transcript = transcribe_audio_file(file_path)
        if not transcript:
            error_msg = "Failed to transcribe audio"
            print(error_msg)
            show_error_notification(os.path.basename(file_path), error_msg)
            return
        
        # Step 2: Summarize transcript
        summary = summarize_with_gemini(transcript)
        if not summary:
            print("Gemini summarization failed, trying OpenAI...")
            summary = summarize_with_openai(transcript)
        
        if not summary:
            print("Both summarization methods failed, using raw transcript...")
            summary = transcript
        
        # Step 3: Add to Notion
        meeting_title = os.path.splitext(os.path.basename(file_path))[0]
        result = add_to_notion(meeting_title, summary)
        
        if result:
            print(f"Successfully processed voice note: {meeting_title}")
            show_success_notification(meeting_title)
        else:
            error_msg = "Failed to add to Notion"
            print(f"Failed to add to Notion: {meeting_title}")
            show_error_notification(meeting_title, error_msg)
            
    except Exception as e:
        error_msg = str(e)
        print(f"Error processing voice note: {e}")
        show_error_notification(os.path.basename(file_path), error_msg)

class VoiceNoteHandler(FileSystemEventHandler):
    """Handler for new voice note files."""
    
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.mp3', '.wav', '.m4a', '.flac', '.ogg')):
            # Wait for file to be fully written
            time.sleep(3)
            process_new_audio(event.src_path)

def main():
    """Main monitoring loop."""
    if not os.path.exists(FOLDER_TO_MONITOR):
        print(f"Error: Monitor folder does not exist: {FOLDER_TO_MONITOR}")
        sys.exit(1)
    
    print(f"Starting voice note monitoring...")
    print(f"Monitoring folder: {FOLDER_TO_MONITOR}")
    print(f"Notion database: {notion_database_id}")
    
    event_handler = VoiceNoteHandler()
    observer = Observer()
    observer.schedule(event_handler, FOLDER_TO_MONITOR, recursive=False)
    
    observer.start()
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("Stopping voice note monitoring...")
        observer.stop()
    observer.join()
    print("Voice note monitoring stopped.")

if __name__ == "__main__":
    main()