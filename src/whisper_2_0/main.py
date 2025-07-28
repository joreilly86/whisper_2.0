"""
Main entry point for the Voice Note Processor.
"""

import argparse
import os
import shutil
from datetime import datetime
from dotenv import load_dotenv

from . import (
    config,
    notion_integration,
    summarization,
    transcription,
    utils,
)

# Load environment variables from .env file
load_dotenv()


def process_file(file_path):
    """Process a single audio file."""
    if not file_path or not os.path.exists(file_path):
        error_msg = f"File not found: {file_path}"
        print(f"[ERROR] {error_msg}")
        return False

    print(f"Processing: {os.path.basename(file_path)}")

    try:
        # Step 1: Transcribe
        transcript = transcription.transcribe_audio_file(file_path)
        if not transcript:
            error_msg = "Failed to transcribe audio"
            print(f"[ERROR] {error_msg}")
            utils.show_error_notification(os.path.basename(file_path), error_msg)
            return False

        # Step 2: Summarize
        summary = summarization.summarize_with_gemini(transcript)
        if not summary:
            print("Gemini failed, trying OpenAI...")
            summary = summarization.summarize_with_openai(transcript)

        if not summary:
            print("Both AI services failed, using raw transcript...")
            summary = transcript

        # Step 3: Save backup markdown
        title = os.path.splitext(os.path.basename(file_path))[0]
        original_filename = os.path.basename(file_path)
        backup_path = notion_integration.save_backup_markdown(
            title, summary, original_filename
        )

        # Step 4: Add to Notion
        result = notion_integration.add_to_notion(title, summary)

        # Mark as processed if we have a backup (transcription succeeded)
        if backup_path:
            utils.mark_as_processed(file_path)
            print(f"[SUCCESS] Successfully processed: {title}")

            if result:
                utils.show_success_notification(title)
            else:
                print(f"[WARNING] Notion failed but backup saved at: {backup_path}")
                utils.show_error_notification(title, "Notion failed but backup saved")
            return True
        else:
            error_msg = "Failed to create backup"
            print(f"[ERROR] {error_msg}")
            utils.show_error_notification(title, error_msg)
            return False

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"[ERROR] Error processing {file_path}: {error_msg}")
        utils.show_error_notification(os.path.basename(file_path), error_msg)
        return False


def process_queue_item(item):
    """Process a single item from the queue."""
    print(f"\n[PROCESSING] Processing: {item}")

    # Resolve file path (download if URL)
    file_path = utils.resolve_file_path(item)
    if not file_path:
        return False

    try:
        # Process the file
        success = process_file(file_path)

        # Clean up downloaded file if it was a URL
        if utils.is_url(item) and file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"[CLEAR] Cleaned up temporary file: {file_path}")

        return success
    except Exception as e:
        print(f"[ERROR] Error processing {item}: {e}")
        return False


def handle_show_queue():
    """Show current queue contents."""
    current_queue = utils.load_queue()
    if current_queue:
        print(f"\n[QUEUE] Current queue ({len(current_queue)} items):")
        for i, item in enumerate(current_queue, 1):
            print(f"  {i}. {item}")
    else:
        print("[QUEUE] Queue is empty")


def handle_clear_queue():
    """Clear the processing queue."""
    utils.save_queue([])
    print("[CLEAR] Queue cleared")


def handle_process_next():
    """Process the next item in queue."""
    current_queue = utils.load_queue()
    if current_queue:
        item = current_queue[0]
        if process_queue_item(item):
            utils.remove_from_queue(item)
            print(f"[SUCCESS] Successfully processed and removed: {item}")
        else:
            print(f"[ERROR] Failed to process: {item}")
            response = input("Remove from queue anyway? (y/n): ").strip().lower()
            if response in ["y", "yes"]:
                utils.remove_from_queue(item)
    else:
        print("[QUEUE] Queue is empty")


def handle_process_all():
    """Process all items in queue."""
    current_queue = utils.load_queue()
    if not current_queue:
        print("[QUEUE] Queue is empty")
        return

    print(f"[RUNNING] Processing {len(current_queue)} items...")
    success_count = 0

    for item in current_queue.copy():  # Copy to avoid modification during iteration
        if process_queue_item(item):
            utils.remove_from_queue(item)
            success_count += 1
        else:
            print(f"[ERROR] Failed to process: {item}")
            response = input("Remove from queue anyway? (y/n): ").strip().lower()
            if response in ["y", "yes"]:
                utils.remove_from_queue(item)

    print(
        f"\n[RESULTS] Results: {success_count}/{len(current_queue)} items processed successfully"
    )

    # Show summary notification
    if success_count > 0:
        utils.show_notification(
            title="[COMPLETE] Voice Note Processing Complete",
            message=f"Successfully processed {success_count} items",
            timeout=config.NOTIFICATION_TIMEOUT_BATCH,
        )


def handle_latest_file():
    """Process the latest file from voice notes folder."""
    latest_file = utils.get_latest_file()
    if latest_file:
        filename = os.path.basename(latest_file)
        print(f"\n[FILE] Latest file: {filename}")
        response = input("Process this file? (y/n): ").strip().lower()
        if response in ["y", "yes"]:
            if process_queue_item(latest_file):
                print(f"[SUCCESS] Successfully processed: {filename}")
            else:
                print(f"[ERROR] Failed to process: {filename}")
        else:
            print("Skipped")
    else:
        print("[ERROR] No unprocessed files found in voice notes folder")


def handle_select_files():
    """Select multiple files from voice notes folder."""
    available_files = utils.get_available_files()
    if not available_files:
        print("[ERROR] No unprocessed files found in voice notes folder")
        return

    print(f"\n[FOLDER] Available files ({len(available_files)} total):")
    selected_files = []

    for i, file_path in enumerate(available_files, 1):
        filename = os.path.basename(file_path)
        file_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime(
            "%Y-%m-%d %H:%M"
        )
        print(f"  {i}. {filename} ({file_time})")

        while True:
            response = input(f"Select '{filename}'? (y/n): ").strip().lower()
            if response in ["y", "yes"]:
                selected_files.append(file_path)
                print(f"[SUCCESS] Selected: {filename}")
                break
            elif response in ["n", "no"]:
                print(f"[SKIP] Skipped: {filename}")
                break
            else:
                print("Please enter 'y' or 'n'")

    if selected_files:
        utils.add_to_queue(selected_files)
        print(f"\n[QUEUE] Added {len(selected_files)} files to queue")
        print("Type 'p' to process selected files")
    else:
        print("No files selected")


def handle_add_item(command):
    """Add item to queue."""
    item = command[4:].strip()
    # Remove quotes if present
    if item.startswith('"') and item.endswith('"'):
        item = item[1:-1]
    elif item.startswith("'") and item.endswith("'"):
        item = item[1:-1]
    if item:
        utils.add_to_queue([item])
    else:
        print("[ERROR] Please provide a file path or URL")


def handle_direct_path(command):
    """Handle direct file path processing."""
    stripped_command = command.strip()
    if stripped_command.startswith('"') and stripped_command.endswith('"'):
        stripped_command = stripped_command[1:-1]
    elif stripped_command.startswith("'") and stripped_command.endswith("'"):
        stripped_command = stripped_command[1:-1]

    # Check if it's a file path
    if stripped_command and (
        os.path.exists(stripped_command)
        or stripped_command.startswith(("http://", "https://"))
        or (len(stripped_command) > 2 and stripped_command[1] == ":")
    ):  # Windows drive letter

        print(f"[PROCESSING] Processing file directly: {stripped_command}")
        if process_queue_item(stripped_command):
            print(
                f"[SUCCESS] Successfully processed: {os.path.basename(stripped_command)}"
            )
        else:
            print(f"[ERROR] Failed to process: {os.path.basename(stripped_command)}")
        return True
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

            if command.lower() in ["quit", "exit", "q"]:
                print("[GOODBYE] Goodbye!")
                break
            elif command.lower() == "queue":
                handle_show_queue()
            elif command.lower() == "clear":
                handle_clear_queue()
            elif command.lower() == "process":
                handle_process_next()
            elif command.lower() in ["process_all", "p"]:
                handle_process_all()
            elif command.lower() == "latest":
                handle_latest_file()
            elif command.lower() == "select":
                handle_select_files()
            elif command.startswith("add "):
                handle_add_item(command)
            else:
                # Try to handle as direct file path
                if not handle_direct_path(command):
                    print("[ERROR] Unknown command. Type 'quit' to exit.")

        except KeyboardInterrupt:
            print("\n[GOODBYE] Goodbye!")
            break
        except Exception as e:
            print(f"[ERROR] Error: {e}")


def main():
    # Validate configuration before starting
    config_errors = config.validate_configuration()
    if config_errors:
        for error in config_errors:
            print(error)
        print("\nPlease fix the configuration issues above before running the application.")
        return 1
    
    # Clean up temp download directory on startup
    if os.path.exists(config.TEMP_DOWNLOAD_DIR):
        shutil.rmtree(config.TEMP_DOWNLOAD_DIR)

    parser = argparse.ArgumentParser(
        description="Manual queue-based voice note processor"
    )
    parser.add_argument(
        "files", nargs="*", help="Audio files or URLs to add to queue and process"
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Run in interactive mode"
    )
    parser.add_argument(
        "--queue-only", action="store_true", help="Only add to queue, don't process"
    )
    parser.add_argument(
        "--process-queue", action="store_true", help="Process all items in the queue"
    )
    parser.add_argument("--show-queue", action="store_true", help="Show current queue")
    parser.add_argument("--clear-queue", action="store_true", help="Clear the queue")

    args = parser.parse_args()

    # Handle queue operations
    if args.clear_queue:
        utils.save_queue([])
        print("[CLEAR] Queue cleared")
        return 0

    if args.show_queue:
        handle_show_queue()
        return 0

    # Add files to queue
    if args.files:
        utils.add_to_queue(args.files)

        if args.queue_only:
            print(f"[QUEUE] Added {len(args.files)} items to queue")
            return 0

    # Process queue
    if args.process_queue:
        handle_process_all()
        return 0

    # Interactive mode
    if args.interactive or (not args.files and not args.process_queue):
        interactive_mode()
        return 0

    # Default: add files and process them
    if args.files:
        print(f"[RUNNING] Processing {len(args.files)} items...")
        success_count = 0

        for item in args.files:
            if process_queue_item(item):
                success_count += 1

        print(
            f"\n[RESULTS] Results: {success_count}/{len(args.files)} items processed successfully"
        )

        # Show summary notification
        if success_count > 0:
            utils.show_notification(
                title="[COMPLETE] Voice Note Processing Complete",
                message=f"Successfully processed {success_count} items",
                timeout=config.NOTIFICATION_TIMEOUT_BATCH,
            )
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code:
        sys.exit(exit_code)
