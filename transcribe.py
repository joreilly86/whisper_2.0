#!/usr/bin/env python3

import os
import sys
import time
import math
import shutil
import argparse
from dotenv import load_dotenv
import google.generativeai as genai
from pydub import AudioSegment
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Constants
MAX_CHUNK_SIZE_BYTES = 24.5 * 1024 * 1024  # 24.5 MB to be safe under OpenAI's 25MB limit
TARGET_BITRATE_KBPS = "192k" # Target bitrate for MP3 chunk export and size estimation
UPLOADS_DIR = "uploads"
TRANSCRIPTIONS_DIR = "transcriptions"
RAW_TRANSCRIPTIONS_DIR = os.path.join(TRANSCRIPTIONS_DIR, "raw")
TEMP_CHUNK_SUBDIR = "temp_audio_chunks" # Relative to project root
POST_PROCESSING_PROMPT_FILE = "post_processing_prompt.txt"

import google.generativeai as genai

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not openai_api_key:
    print("Error: OPENAI_API_KEY not found in .env file or environment variables.")
    sys.exit(1)

client = OpenAI(api_key=openai_api_key)

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

def estimate_segment_duration_ms(audio_duration_ms, audio_channels, target_bitrate_kbps_str, max_size_bytes):
    try:
        target_bitrate_kbps = int(target_bitrate_kbps_str.replace('k', ''))
    except ValueError:
        print(f"Error: Invalid target bitrate format: {target_bitrate_kbps_str}. Expected format like '192k'.")
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

def post_process_transcript(raw_transcript, prompt_text):
    if gemini_api_key:
        print("Post-processing transcript with Gemini 1.5 Pro...")
        try:
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            response = model.generate_content(prompt_text + "\n\n" + raw_transcript)
            return response.text.strip()
        except Exception as e:
            print(f"Error during post-processing with Gemini: {e}")
            return f"[Post-processing failed. Raw transcript below]\n\n{raw_transcript}"
    else:
        print("Post-processing transcript with GPT-4...")
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": prompt_text
                    },
                    {
                        "role": "user",
                        "content": raw_transcript
                    }
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error during post-processing with GPT-4: {e}")
            return f"[Post-processing failed. Raw transcript below]\n\n{raw_transcript}"

def process_audio_file(input_file_path):
    base_name, input_ext_with_dot = os.path.splitext(os.path.basename(input_file_path))
    output_filename = base_name + ".txt"
    output_file_path = os.path.join(TRANSCRIPTIONS_DIR, output_filename)
    raw_output_file_path = os.path.join(RAW_TRANSCRIPTIONS_DIR, output_filename)

    if os.path.exists(output_file_path):
        print(f"Skipping already transcribed file: {input_file_path}")
        return

    print(f"Processing new audio file: {input_file_path}")

    # Manage temporary chunk directory
    if os.path.exists(TEMP_CHUNK_SUBDIR):
        shutil.rmtree(TEMP_CHUNK_SUBDIR)
    os.makedirs(TEMP_CHUNK_SUBDIR, exist_ok=True)

    transcribed_texts = []
    chunk_files = []

    try:
        audio = AudioSegment.from_file(input_file_path, format=input_ext_with_dot[1:])
        audio_duration_ms = len(audio)
        segment_duration_ms = estimate_segment_duration_ms(audio_duration_ms, audio.channels, TARGET_BITRATE_KBPS, MAX_CHUNK_SIZE_BYTES)

        if not segment_duration_ms or segment_duration_ms <= 0:
            print("Error: Could not estimate segment duration.")
            return

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
            return

        print(f"Starting transcription for {len(chunk_files)} chunks...")
        for i, chunk_file_path in enumerate(chunk_files):
            print(f"Transcribing slice {i+1}/{len(chunk_files)}...")
            with open(chunk_file_path, "rb") as audio_file_handle:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file_handle
                )
            transcribed_texts.append(transcript.text.strip())
        
        full_transcript = "\n\n".join(transcribed_texts)

        # Save the raw transcript as a backup
        with open(raw_output_file_path, "w", encoding="utf-8") as f:
            f.write(full_transcript)
        print(f"Raw transcript saved to {raw_output_file_path}")

        # Post-processing step
        if os.path.exists(POST_PROCESSING_PROMPT_FILE):
            with open(POST_PROCESSING_PROMPT_FILE, "r", encoding="utf-8") as f:
                prompt_text = f.read()
            final_transcript = post_process_transcript(full_transcript, prompt_text)
        else:
            print("Warning: Post-processing prompt file not found. Skipping this step.")
            final_transcript = full_transcript

        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(final_transcript)
        
        print(f"Post-processed transcript successfully written to {output_file_path}")

    except Exception as e:
        print(f"An unexpected error occurred during processing: {e}")
    finally:
        if os.path.exists(TEMP_CHUNK_SUBDIR):
            shutil.rmtree(TEMP_CHUNK_SUBDIR)

class AudioFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith((".m4a", ".mp3")):
            time.sleep(1)  # Wait a bit for the file to be fully written
            process_audio_file(event.src_path)

import argparse

def main():
    parser = argparse.ArgumentParser(description="Transcribe audio files from a watched directory.")
    parser.add_argument(
        "--watch-dir",
        type=str,
        default=UPLOADS_DIR,
        help=f"The directory to watch for new audio files. Defaults to '{UPLOADS_DIR}'.",
    )
    args = parser.parse_args()

    watch_directory = args.watch_dir

    if not os.path.isdir(watch_directory):
        print(f"Error: The specified watch directory does not exist or is not a directory: {watch_directory}")
        sys.exit(1)

    os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)
    os.makedirs(RAW_TRANSCRIPTIONS_DIR, exist_ok=True)

    print(f"Watching for new audio files in: {watch_directory}")
    event_handler = AudioFileHandler()
    observer = Observer()
    observer.schedule(event_handler, watch_directory, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
    main()
