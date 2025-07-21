@echo off
echo.
echo Voice Note Processor - Quick Mode
echo =====================================
echo.
echo Instructions:
echo - Paste or type the full path to your voice note file
echo - Or drag and drop a file into this window
echo - Press Enter to process immediately
echo - Type 'quit' to exit
echo.

uv run scripts\process_voice_notes.py --interactive