#!/usr/bin/env python3
"""
On-demand voice note processor - run when needed, not continuously.
Usage: python process_voice_notes.py [--folder path] [--all]
"""

import os
import sys
import argparse
import glob
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from notion_client import Client
from pydub import AudioSegment
from openai import OpenAI
import math
import shutil
from plyer import notification

# Load environment variables
load_dotenv()

# Import all the functions from the original monitor
# (We could refactor to a shared module, but keeping simple for now)
from voice_note_monitor import (
    transcribe_audio_file, 
    summarize_with_gemini, 
    summarize_with_openai,
    add_to_notion,
    show_success_notification,
    show_error_notification
)

def find_unprocessed_files(folder_path, processed_log="processed_files.txt"):
    """Find audio files that haven't been processed yet."""
    audio_extensions = ('.mp3', '.wav', '.m4a', '.flac', '.ogg')
    
    # Load list of already processed files
    processed_files = set()
    if os.path.exists(processed_log):
        with open(processed_log, 'r') as f:
            processed_files = {line.strip() for line in f}
    
    # Find all audio files
    all_files = []
    for ext in audio_extensions:
        pattern = os.path.join(folder_path, f"*{ext}")
        all_files.extend(glob.glob(pattern))
    
    # Filter out already processed files
    unprocessed = [f for f in all_files if f not in processed_files]
    
    return unprocessed, processed_log

def mark_as_processed(file_path, processed_log):
    """Mark a file as processed."""
    with open(processed_log, 'a') as f:
        f.write(f"{file_path}\n")

def process_file(file_path, processed_log):
    """Process a single audio file."""
    print(f"Processing: {os.path.basename(file_path)}")
    
    try:
        # Step 1: Transcribe
        transcript = transcribe_audio_file(file_path)
        if not transcript:
            error_msg = "Failed to transcribe audio"
            print(f"❌ {error_msg}")
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
        
        # Step 3: Add to Notion
        title = os.path.splitext(os.path.basename(file_path))[0]
        result = add_to_notion(title, summary)
        
        if result:
            print(f"✅ Successfully processed: {title}")
            show_success_notification(title)
            mark_as_processed(file_path, processed_log)
            return True
        else:
            error_msg = "Failed to add to Notion"
            print(f"❌ {error_msg}")
            show_error_notification(title, error_msg)
            return False
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error processing {file_path}: {e}")
        show_error_notification(os.path.basename(file_path), error_msg)
        return False

def main():
    parser = argparse.ArgumentParser(description="Process voice notes on-demand")
    parser.add_argument("--folder", default=os.getenv("VOICE_NOTES_FOLDER"), 
                       help="Folder to process")
    parser.add_argument("--all", action="store_true", 
                       help="Process all files, even previously processed ones")
    
    args = parser.parse_args()
    
    if not args.folder or not os.path.exists(args.folder):
        print(f"❌ Voice notes folder not found: {args.folder}")
        sys.exit(1)
    
    print(f"🔍 Scanning folder: {args.folder}")
    
    if args.all:
        # Process all audio files
        audio_extensions = ('.mp3', '.wav', '.m4a', '.flac', '.ogg')
        files_to_process = []
        for ext in audio_extensions:
            pattern = os.path.join(args.folder, f"*{ext}")
            files_to_process.extend(glob.glob(pattern))
        processed_log = "processed_files_all.txt"
    else:
        # Process only unprocessed files
        files_to_process, processed_log = find_unprocessed_files(args.folder)
    
    if not files_to_process:
        print("✅ No new files to process")
        return
    
    print(f"📁 Found {len(files_to_process)} files to process")
    
    success_count = 0
    for file_path in files_to_process:
        if process_file(file_path, processed_log):
            success_count += 1
    
    print(f"\n📊 Results: {success_count}/{len(files_to_process)} files processed successfully")
    
    # Show summary notification
    if success_count > 0:
        notification.notify(
            title="🎉 Voice Note Processing Complete",
            message=f"Successfully processed {success_count} files",
            timeout=10,
            app_name="Voice Note Processor"
        )

if __name__ == "__main__":
    main()