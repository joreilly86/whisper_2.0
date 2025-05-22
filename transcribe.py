#!/usr/bin/env python3

import os
import sys
import math
import shutil
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment
# from pydub.utils import mediainfo # mediainfo not directly used in this version

# Constants
MAX_CHUNK_SIZE_BYTES = 24.5 * 1024 * 1024  # 24.5 MB to be safe under OpenAI's 25MB limit
TARGET_BITRATE_KBPS = "192k" # Target bitrate for MP3 chunk export and size estimation
UPLOADS_DIR = "uploads"
TRANSCRIPTIONS_DIR = "transcriptions"
TEMP_CHUNK_SUBDIR = "temp_audio_chunks" # Relative to project root

def estimate_segment_duration_ms(audio_duration_ms, audio_channels, target_bitrate_kbps_str, max_size_bytes):
    """
    Estimates the duration (in ms) for audio segments to keep them under max_size_bytes
    when exported as MP3 at target_bitrate_kbps.
    """
    try:
        target_bitrate_kbps = int(target_bitrate_kbps_str.replace('k', ''))
    except ValueError:
        print(f"Error: Invalid target bitrate format: {target_bitrate_kbps_str}. Expected format like '192k'.")
        sys.exit(1)

    if target_bitrate_kbps <= 0:
        print(f"Error: Target bitrate must be positive. Got: {target_bitrate_kbps_str}")
        sys.exit(1)
        
    bytes_per_second_at_target_bitrate = (target_bitrate_kbps * 1000) / 8
    
    if bytes_per_second_at_target_bitrate <= 0:
        print(f"Error: Calculated bytes_per_second_at_target_bitrate is not positive. Check target_bitrate_kbps.")
        sys.exit(1)

    max_duration_seconds_for_chunk = max_size_bytes / bytes_per_second_at_target_bitrate
    estimated_chunk_duration_ms = math.floor(max_duration_seconds_for_chunk * 1000)
    
    return min(estimated_chunk_duration_ms, audio_duration_ms)

def main():
    # Create necessary directories
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)
    
    # Load environment variables from .env file (expected at project root)
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env file or environment variables.")
        print("Please create a .env file at the project root with your API key (e.g., copy .env.example).")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # Read command-line arguments
    if len(sys.argv) != 2:
        print(f"Usage: python transcribe.py <audio_filename_in_{UPLOADS_DIR}>")
        print(f"Example: python transcribe.py my_meeting.m4a")
        sys.exit(1)

    audio_filename = sys.argv[1]
    
    input_file_path = os.path.join(UPLOADS_DIR, audio_filename)
    
    base_name, input_ext_with_dot = os.path.splitext(audio_filename)
    input_ext = input_ext_with_dot.lower()

    if input_ext not in [".m4a", ".mp3"]:
        print(f"Error: Unsupported input file type '{input_ext}'. This script currently supports '.m4a' and '.mp3' files.")
        print(f"Please provide a valid audio file in the '{UPLOADS_DIR}/' directory.")
        sys.exit(1)
    
    # Determine the format for pydub, removing the leading dot
    audio_format = input_ext[1:]

    output_filename = base_name + ".txt"
    output_file_path = os.path.join(TRANSCRIPTIONS_DIR, output_filename)

    # Validate input file
    if not os.path.exists(input_file_path):
        print(f"Error: Input file not found: {input_file_path}")
        print(f"Ensure '{audio_filename}' is placed in the '{UPLOADS_DIR}/' directory.")
        sys.exit(1)
    if os.path.getsize(input_file_path) == 0:
        print(f"Error: Input file is empty: {input_file_path}")
        sys.exit(1)

    # Manage temporary chunk directory (at project root)
    if os.path.exists(TEMP_CHUNK_SUBDIR):
        shutil.rmtree(TEMP_CHUNK_SUBDIR) 
    os.makedirs(TEMP_CHUNK_SUBDIR, exist_ok=True)

    transcribed_texts = []
    chunk_files = []

    try:
        print(f"Loading audio file: {input_file_path}...")
        audio = AudioSegment.from_file(input_file_path, format=audio_format)
        
        audio_duration_ms = len(audio)
        audio_channels = audio.channels
        
        segment_duration_ms = estimate_segment_duration_ms(
            audio_duration_ms, 
            audio_channels, 
            TARGET_BITRATE_KBPS, 
            MAX_CHUNK_SIZE_BYTES
        )

        if segment_duration_ms <= 0:
            print("Error: Calculated segment duration is zero or negative. This might be due to a very small or problematic audio file, or an issue with bitrate estimation.")
            sys.exit(1)

        num_chunks = math.ceil(audio_duration_ms / segment_duration_ms)
        print(f"Splitting into {num_chunks} chunks (estimated)...")

        for i in range(num_chunks):
            start_ms = i * segment_duration_ms
            end_ms = min((i + 1) * segment_duration_ms, audio_duration_ms)
            if start_ms >= end_ms: # Avoid creating empty chunks if calculation is off
                continue
            chunk = audio[start_ms:end_ms]
            
            chunk_file_path = os.path.join(TEMP_CHUNK_SUBDIR, f"chunk_{i:03d}.mp3")
            
            print(f"Exporting chunk {i+1}/{num_chunks} to {chunk_file_path}...")
            chunk.export(chunk_file_path, format="mp3", bitrate=TARGET_BITRATE_KBPS)
            
            actual_chunk_size = os.path.getsize(chunk_file_path)
            if actual_chunk_size > MAX_CHUNK_SIZE_BYTES * 1.1: 
                 print(f"Warning: Chunk {chunk_file_path} size ({actual_chunk_size / (1024*1024):.2f}MB) is larger than expected. Transcription might fail.")

            chunk_files.append(chunk_file_path)

        if not chunk_files:
            print("No audio chunks were generated. Check if the audio file is too short or empty.")
            sys.exit(1)

        print(f"\nStarting transcription for {len(chunk_files)} chunks...")
        for i, chunk_file_path in enumerate(chunk_files):
            print(f"Transcribing slice {i+1}/{len(chunk_files)} ({os.path.basename(chunk_file_path)})...")
            try:
                with open(chunk_file_path, "rb") as audio_file_handle:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file_handle
                    )
                transcribed_texts.append(transcript.text.strip())
            except Exception as e:
                print(f"Error transcribing chunk {chunk_file_path}: {e}")
                transcribed_texts.append(f"[Error transcribing {os.path.basename(chunk_file_path)}: {str(e)}]")


        print(f"\nWriting transcript to: {output_file_path}...")
        full_transcript = "\n\n".join(transcribed_texts)
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(full_transcript)
        
        print(f"Transcript successfully written to {output_file_path}")

    except FileNotFoundError as fnf_error:
        # This specific check is for FFmpeg not being found by pydub
        if 'ffmpeg' in str(fnf_error).lower() or 'avprobe' in str(fnf_error).lower() or 'avconv' in str(fnf_error).lower():
             print(f"Error: FFmpeg (or its components like avprobe/avconv) not found. pydub requires FFmpeg to be installed and in your system's PATH for M4A/MP3 processing.")
        else:
            print(f"A file-related error occurred: {fnf_error}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
    finally:
        if os.path.exists(TEMP_CHUNK_SUBDIR):
            print("Cleaning up temporary files...")
            shutil.rmtree(TEMP_CHUNK_SUBDIR)

if __name__ == "__main__":
    main()
