# Voice Note Transcription & Notion Integration

An efficient, automated pipeline for transcribing voice notes and saving structured meeting minutes to Notion. Supports configurable scheduling for different meeting loads.

## ✨ Features

- **🎤 Automatic Transcription**: Uses OpenAI Whisper for high-quality audio transcription
- **🤖 AI Summarization**: Gemini (with OpenAI fallback) creates structured meeting minutes
- **📝 Notion Integration**: Automatically saves results to your Notion database
- **📅 Flexible Scheduling**: Configure processing frequency based on your meeting load
- **🔔 Desktop Notifications**: Get notified of successful processing or errors
- **⚡ Resource Efficient**: Only runs when needed, not continuously
- **🔒 Secure**: Uses environment variables for API keys

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Using UV (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and add your API keys:
```env
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here
NOTION_API_KEY=your_notion_integration_secret
NOTION_DATABASE_ID=your_database_id
VOICE_NOTES_FOLDER=G:\My Drive\Voice Notes
```

### 3. Test the System
```bash
uv run test_voice_system.py
```

### 4. Set Up Automated Processing
```bash
uv run setup_scheduled_task.py
```

## 📊 Schedule Profiles

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

## 🛠️ Usage

### Automatic Processing (Recommended)
1. Configure your schedule profile in `.env`
2. Run: `uv run setup_scheduled_task.py`
3. Drop voice notes into your configured folder
4. Get notifications when processing completes

### Manual Processing
```bash
# Process new files only
uv run process_voice_notes.py

# Process all files (including previously processed)
uv run process_voice_notes.py --all

# Process specific folder
uv run process_voice_notes.py --folder "C:\path\to\audio\files"
```

## 🔧 Scripts Overview

| Script | Purpose |
|--------|---------|
| `process_voice_notes.py` | Main processing script (on-demand) |
| `setup_scheduled_task.py` | Configure Windows Task Scheduler |
| `test_voice_system.py` | Test all system components |
| `test_notification.py` | Test notification system |
| `transcribe.py` | Legacy continuous monitoring (deprecated) |

## 📋 Supported Audio Formats

- MP3 (.mp3)
- M4A (.m4a) 
- WAV (.wav)
- FLAC (.flac)
- OGG (.ogg)

## 🔒 Security Notes

- ⚠️ **Never commit your `.env` file** - it contains sensitive API keys
- 🔐 Use environment variables for all secrets
- 🛡️ Keep your repository private if using real API keys
- 🔄 Rotate API keys if accidentally exposed

## 🏗️ Architecture

```
Voice Note → Whisper Transcription → AI Summarization → Notion Database
     ↓              ↓                      ↓               ↓
  Audio File    Raw Transcript      Structured Summary   Meeting Entry
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test your changes with `uv run test_voice_system.py`
4. Submit a pull request

## 📄 License

Private repository for Knight Piesold internal use.