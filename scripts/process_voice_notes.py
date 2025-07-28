#!/usr/bin/env python3
"""
Voice Note Processor - Manual queue-based transcription and Notion integration.
"""
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from whisper_2_0.main import main

if __name__ == "__main__":
    main()
