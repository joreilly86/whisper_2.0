"""
Functions for processing audio files.
"""

import os
import math
import shutil
from pydub import AudioSegment
from . import config

AudioSegment.converter = "ffmpeg"
AudioSegment.ffmpeg = "ffmpeg"
AudioSegment.ffprobe = "ffprobe"


def estimate_segment_duration_ms(
    audio_duration_ms, audio_channels, target_bitrate_kbps_str, max_size_bytes
):
    """Estimate optimal segment duration for audio chunking."""
    if not target_bitrate_kbps_str or not audio_duration_ms or not max_size_bytes:
        return None

    try:
        target_bitrate_kbps = int(target_bitrate_kbps_str.replace("k", ""))
        if target_bitrate_kbps <= 0:
            print(
                f"Error: Target bitrate must be positive. Got: {target_bitrate_kbps_str}"
            )
            return None
    except ValueError:
        print(f"Error: Invalid target bitrate format: {target_bitrate_kbps_str}")
        return None

    bytes_per_second_at_target_bitrate = (target_bitrate_kbps * 1000) / 8
    max_duration_seconds_for_chunk = max_size_bytes / bytes_per_second_at_target_bitrate
    estimated_chunk_duration_ms = math.floor(max_duration_seconds_for_chunk * 1000)

    return min(estimated_chunk_duration_ms, audio_duration_ms)


def create_audio_chunks(file_path):
    """Create audio chunks for transcription. Returns list of chunk file paths."""
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return []

    # Clean up any existing temp chunks
    os.makedirs(config.TEMP_CHUNK_SUBDIR, exist_ok=True)
    if os.path.exists(config.TEMP_CHUNK_SUBDIR):
        shutil.rmtree(config.TEMP_CHUNK_SUBDIR)
    os.makedirs(config.TEMP_CHUNK_SUBDIR, exist_ok=True)

    try:
        # Load audio file
        base_name, ext = os.path.splitext(os.path.basename(file_path))
        audio = AudioSegment.from_file(file_path, format=ext[1:])
        audio_duration_ms = len(audio)

        # Estimate chunk duration
        segment_duration_ms = estimate_segment_duration_ms(
            audio_duration_ms,
            audio.channels,
            config.TARGET_BITRATE_KBPS,
            config.MAX_CHUNK_SIZE_BYTES,
        )

        if not segment_duration_ms or segment_duration_ms <= 0:
            print("Error: Could not estimate segment duration.")
            return []

        # Split audio into chunks
        num_chunks = math.ceil(audio_duration_ms / segment_duration_ms)
        print(f"Splitting into {num_chunks} chunks...")

        chunk_files = []
        for i in range(num_chunks):
            start_ms = i * segment_duration_ms
            end_ms = min((i + 1) * segment_duration_ms, audio_duration_ms)
            if start_ms >= end_ms:
                continue

            chunk = audio[start_ms:end_ms]
            chunk_file_path = os.path.join(
                config.TEMP_CHUNK_SUBDIR, f"chunk_{i:03d}.mp3"
            )
            chunk.export(
                chunk_file_path, format="mp3", bitrate=config.TARGET_BITRATE_KBPS
            )
            chunk_files.append(chunk_file_path)

        return chunk_files

    except FileNotFoundError as e:
        if "ffmpeg" in str(e).lower() or "ffprobe" in str(e).lower():
            print("[ERROR] FFmpeg not found! Please install FFmpeg:")
            print("  1. Open PowerShell as Administrator")
            print("  2. Run: choco install ffmpeg")
            print("  3. Restart your terminal")
            print("  4. Test with: ffmpeg -version")
        else:
            print(f"Error: File not found - {e}")
        return []
    except Exception as e:
        print(f"Error creating audio chunks: {e}")
        return []
