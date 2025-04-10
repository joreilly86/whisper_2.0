import os
import time
import threading
from pathlib import Path
from typing import Callable
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from app.core.config import settings
# Removed: from app.models.models import Recording, ProcessingStatus

class AudioFileHandler(FileSystemEventHandler):
    """Handler for audio file creation events"""
    
    def __init__(self, callback: Callable[[Path], None]):
        self.callback = callback
        self.processed_files = set()
    
    def on_created(self, event):
        if not event.is_directory:
            file_path = Path(event.src_path)
            
            # Check if it's an audio file and hasn't been processed
            if (file_path.suffix.lower() in ('.mp3', '.wav', '.m4a', '.flac') and 
                    str(file_path) not in self.processed_files):
                
                # Add to processed files set to avoid duplicate processing
                self.processed_files.add(str(file_path))
                
                # Wait a moment to ensure the file is completely written
                # This is important when files are being copied into the directory
                time.sleep(0.5)
                
                self.callback(file_path)
    
    def process_existing_files(self, directory: Path):
        """Process any existing files in the directory"""
        for file_path in directory.glob('*'):
            if (file_path.is_file() and 
                    file_path.suffix.lower() in ('.mp3', '.wav', '.m4a', '.flac') and
                    str(file_path) not in self.processed_files):
                
                # Simulate a file created event
                self.on_created(FileCreatedEvent(str(file_path)))

class FileWatcherService:
    """Service for watching a directory for new audio files"""
    
    def __init__(self, process_callback: Callable[[Path], None]):
        self.watch_dir = settings.UPLOAD_FOLDER
        self.process_callback = process_callback
        self.observer = None
        self.event_handler = None
        self.thread = None
        self.running = False
    
    def start(self):
        """Start watching the directory"""
        if self.running:
            return
        
        # Create event handler
        self.event_handler = AudioFileHandler(self.process_callback)
        
        # Create observer
        self.observer = Observer()
        self.observer.schedule(self.event_handler, str(self.watch_dir), recursive=False)
        
        # Start observer in a separate thread
        self.thread = threading.Thread(target=self._run_observer, daemon=True)
        self.running = True
        self.thread.start()
        
        # Process existing files
        self.event_handler.process_existing_files(self.watch_dir)
    
    def _run_observer(self):
        """Run the observer"""
        self.observer.start()
        try:
            while self.running:
                time.sleep(1)
        except Exception as e:
            print(f"Observer error: {e}")
        finally:
            self.observer.stop()
            self.observer.join()
    
    def stop(self):
        """Stop watching the directory"""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        if self.observer:
            self.observer.stop()
            self.observer.join()
