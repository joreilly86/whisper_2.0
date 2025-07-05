# Voice Note Transcription & Notion Integration

Efficient, automated pipeline for transcribing voice notes and saving structured meeting minutes to Notion with configurable scheduling.

## Features

- **🎤 Automatic Transcription**: OpenAI Whisper with intelligent audio chunking
- **🤖 AI Summarization**: Gemini (with OpenAI fallback) for structured meeting minutes
- **📝 Notion Integration**: Automatic database entries with title and date
- **📅 Flexible Scheduling**: Configure processing frequency based on meeting load
- **🔔 Desktop Notifications**: Real-time feedback on processing status
- **⚡ Resource Efficient**: Only runs when needed, completely hidden background operation
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
VOICE_NOTES_FOLDER=your_voice_notes_folder_path_here
```

### 3. Test System
```bash
uv run tests/test_voice_system.py
uv run tests/test_notification.py
```

### 4. Set Up Automated Processing
```bash
uv run scripts/setup_scheduled_task.py
```

## Schedule Profiles

Configure different processing frequencies in your `.env` file:

### High Meeting Days (every 5 minutes)
```env
SCHEDULE_PROFILE=high_frequency
SCHEDULE_INTERVAL=5
```

### Normal Days (every 15 minutes) - Default
```env
SCHEDULE_PROFILE=normal_frequency
SCHEDULE_INTERVAL=15
```

### Light Meeting Days (every 30 minutes)
```env
SCHEDULE_PROFILE=low_frequency
SCHEDULE_INTERVAL=30
```

### Manual Processing Only
```env
SCHEDULE_PROFILE=manual_only
SCHEDULE_INTERVAL=0
```

### Extended Hours (7 AM - 7 PM)
```env
SCHEDULE_PROFILE=extended_hours
SCHEDULE_INTERVAL=10
SCHEDULE_START_TIME=07:00
SCHEDULE_END_TIME=19:00
```

## Usage

### Automatic Processing (Recommended)
1. Configure your schedule profile in `.env`
2. Run: `uv run scripts/setup_scheduled_task.py`
3. Drop voice notes into your configured folder
4. Get notifications when processing completes

### Manual Processing
```bash
# Process new files only
uv run scripts/process_voice_notes.py

# Process all files (including previously processed)
uv run scripts/process_voice_notes.py --all

# Process specific folder
uv run scripts/process_voice_notes.py --folder "C:\path\to\audio\files"
```

## Project Structure

```
whisper_2.0/
├── README.md                           # This file
├── pyproject.toml                      # Project dependencies
├── .env.example                        # Environment configuration template
├── post_processing_prompt.txt          # AI summarization instructions
├── process_voice_notes_hidden.vbs      # Hidden background scheduler
├── scripts/
│   ├── process_voice_notes.py          # Main processing script
│   └── setup_scheduled_task.py         # Windows Task Scheduler setup
└── tests/
    ├── test_voice_system.py            # System component tests
    └── test_notification.py            # Notification system test
```

## Supported Audio Formats

- MP3 (.mp3)
- M4A (.m4a) 
- WAV (.wav)
- FLAC (.flac)
- OGG (.ogg)

## How It Works

```
Voice Note → Whisper Transcription → AI Summarization → Notion Database
     ↓              ↓                      ↓               ↓
  Audio File    Raw Transcript      Structured Summary   Meeting Entry
```

1. **Audio Processing**: Files are automatically chunked for optimal Whisper processing
2. **Transcription**: OpenAI Whisper converts speech to text with high accuracy
3. **Summarization**: Custom engineering-focused prompt creates structured meeting minutes
4. **Storage**: Results saved to Notion with proper formatting and metadata
5. **Tracking**: Processed files logged to prevent duplicate processing

## Customization

### AI Summarization
Edit `post_processing_prompt.txt` to customize the meeting minute format and focus areas.

### Schedule Changes
1. Edit your `.env` file
2. Comment/uncomment desired profile
3. Run: `uv run scripts/setup_scheduled_task.py`

## Troubleshooting

### Test Individual Components
```bash
uv run tests/test_voice_system.py
```

### Check Scheduled Task
- Open Task Scheduler (`taskschd.msc`)
- Look for "ProcessVoiceNotes" task
- Check execution history

### Manual Cancellation
- **Ctrl+C**: Clean interrupt with proper cleanup
- **Close Terminal**: Force stop (files still cleaned up)

## Security

- ⚠️ Never commit your `.env` file
- 🔐 Use environment variables for all secrets
- 🛡️ Keep repository private
- 🔄 Rotate API keys if exposed

## License

Private repository for internal use.