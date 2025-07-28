"""
Utility functions for the Voice Note Processor.
"""

import os
import glob
import time
import urllib.request
from datetime import datetime
from plyer import notification
from . import config


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
        timeout=config.NOTIFICATION_TIMEOUT_SUCCESS,
    )


def show_error_notification(filename, error_msg):
    """Show error notification for failed voice note processing."""
    show_notification(
        title="[ERROR] Voice Note Processing Failed",
        message=f"Failed to process: {filename}\nError: {error_msg}",
        timeout=config.NOTIFICATION_TIMEOUT_ERROR,
    )


def is_temp_file(file_path):
    """Check if a file is likely a temporary recording in progress."""
    filename = os.path.basename(file_path).lower()

    # Check if filename contains temp patterns
    for pattern in config.TEMP_FILE_PATTERNS:
        if pattern in filename:
            return True

    # Check if file was modified very recently (might still be actively recording)
    try:
        file_mtime = os.path.getmtime(file_path)
        current_time = datetime.now().timestamp()
        if current_time - file_mtime < config.TEMP_FILE_AGE_THRESHOLD:
            return True
    except OSError:
        pass

    return False


def download_audio_file(url, temp_dir):
    """Download audio file from URL to temp directory."""
    if not url or not url.strip():
        print("Error: URL cannot be empty")
        return None

    if not url.startswith(("http://", "https://")):
        print(f"Error: Invalid URL format: {url}")
        return None

    if not temp_dir:
        print("Error: Temp directory not specified")
        return None

    try:
        # Create temp directory if it doesn't exist
        os.makedirs(temp_dir, exist_ok=True)

        # Extract filename from URL or create one
        filename = url.split("/")[-1]
        if "." not in filename:
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
    if os.path.exists(config.QUEUE_FILE):
        with open(config.QUEUE_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    queue_items.append(line)
    return queue_items


def save_queue(queue_items):
    """Save processing queue to file."""
    with open(config.QUEUE_FILE, "w") as f:
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
    return item.startswith(("http://", "https://"))




def resolve_file_path(item):
    """Resolve file path from queue item (URL or local path)."""
    if is_url(item):
        # Download the file
        downloaded_file = download_audio_file(item, config.TEMP_DOWNLOAD_DIR)
        return downloaded_file
    else:
        # Local file path
        if os.path.exists(item):
            return item
        else:
            print(f"[ERROR] File not found: {item}")
            return None


def mark_as_processed(file_path):
    """Mark a file as processed."""
    with open(config.PROCESSED_FILES_LOG, "a") as f:
        f.write(f"{file_path}\n")
