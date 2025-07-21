# Voice Note Transcription & Notion Integration

Manual queue-based pipeline for transcribing voice notes and saving structured meeting minutes to Notion with markdown backups.  

If you're here as a [Flocode](https://flocode.substack.com/) subscriber - welcome 👋

## Features

- **🎤 Manual Transcription**: Groq (whisper-large-v3-turbo) and/or OpenAI Whisper with intelligent audio chunking
- **🤖 AI Summarization**: Gemini (with OpenAI fallback) for structured meeting minutes
- **📝 Notion Integration**: Manual database entries with title and date
- **📋 Queue Management**: Add files or URLs to a processing queue
- **🔔 Desktop Notifications**: Real-time feedback on processing status
- **💾 Markdown Backups**: Local markdown files saved for all transcriptions
- **🔒 Secure**: Environment variable configuration for all API keys

## Quick Start

### 1. Install Dependencies
```bash
uv sync
```

### 2. Configure Environment
Copy `.env.example` to `.env` and add your API keys:
```env
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here
NOTION_API_KEY=your_notion_integration_secret
NOTION_DATABASE_ID=your_database_id
```

### 3. Test System
```bash
uv run tests/test_voice_system.py
uv run tests/test_notification.py
```

## Usage

### Interactive Mode (Recommended)
```bash
# Start interactive mode
uv run scripts/process_voice_notes.py --interactive

# Commands in interactive mode:
# add <file_or_url>  - Add file or URL to processing queue
# queue              - Show current queue
# process            - Process next item in queue
# process_all        - Process all items in queue
# clear              - Clear the queue
# quit               - Exit interactive mode
```

### Command Line Usage
```bash
# Process single file or URL immediately
uv run scripts/process_voice_notes.py audio_file.mp3
uv run scripts/process_voice_notes.py https://example.com/audio.mp3

# Add multiple files to queue and process them
uv run scripts/process_voice_notes.py file1.mp3 file2.wav https://example.com/audio.mp3

# Add to queue without processing
uv run scripts/process_voice_notes.py --queue-only file1.mp3 file2.wav

# Process all items in queue
uv run scripts/process_voice_notes.py --process-queue

# Show current queue
uv run scripts/process_voice_notes.py --show-queue

# Clear queue
uv run scripts/process_voice_notes.py --clear-queue
```

## Queue Management

The system uses a simple text-based queue (`processing_queue.txt`) that persists between sessions. You can:

1. **Add items**: Files or URLs are added to the queue
2. **Process items**: Items are processed one by one and removed from queue upon success
3. **View queue**: Check what's currently queued for processing
4. **Clear queue**: Remove all items from queue

## Output

Each processed file creates:
- **Markdown backup**: Saved in `transcription_backups/` with timestamp
- **Notion entry**: Added to your configured Notion database (if successful)
- **Processing log**: Tracks completed files to avoid reprocessing

## Project Structure

```
whisper_2.0/
├── README.md                           # This file
├── pyproject.toml                      # Project dependencies
├── .env.example                        # Environment configuration template
├── post_processing_prompt.txt          # AI summarization instructions
├── processing_queue.txt                # Queue file (auto-created)
├── processed_files.txt                 # Processed files log (auto-created)
├── scripts/
│   └── process_voice_notes.py          # Main processing script
├── tests/
│   ├── test_voice_system.py            # System component tests
│   └── test_notification.py            # Notification system test
├── transcription_backups/              # Markdown backups (auto-created)
└── temp_downloads/                     # Temporary downloads (auto-created)
```

## Supported Audio Formats

- MP3 (.mp3)
- M4A (.m4a) 
- WAV (.wav)
- FLAC (.flac)
- OGG (.ogg)

## How It Works

```
Voice Note/URL → Queue → Whisper Transcription → AI Summarization → Markdown + Notion
      ↓           ↓              ↓                      ↓              ↓
  Audio File   Queue File   Raw Transcript      Structured Summary   Local + Cloud
```

1. **Queue Management**: Files/URLs are added to a persistent queue
2. **Audio Processing**: Files are automatically chunked for optimal Whisper processing
3. **Transcription**: OpenAI Whisper converts speech to text with high accuracy
4. **Summarization**: Custom engineering-focused prompt creates structured meeting minutes
5. **Storage**: Results saved as markdown backup AND to Notion with proper formatting
6. **Tracking**: Processed files logged to prevent duplicate processing

## Customization

### AI Summarization
Edit `post_processing_prompt.txt` to customize the meeting minute format and focus areas.

## Troubleshooting

### Test Individual Components
```bash
uv run tests/test_voice_system.py
```

### Check Queue Status
```bash
# View current queue
uv run scripts/process_voice_notes.py --show-queue

# Clear stuck queue
uv run scripts/process_voice_notes.py --clear-queue
```

### Manual Cancellation
- **Ctrl+C**: Clean interrupt with proper cleanup
- **Close Terminal**: Force stop (files still cleaned up)
- **Downloaded files**: Automatically cleaned up after processing

## Security

- ⚠️ Never commit your `.env` file
- 🔐 Use environment variables for all secrets
- 🛡️ Keep repository private
- 🔄 Rotate API keys if exposed

## License

MIT

> 📢 Visit https://flocode.substack.com/ for more engineering tools.