# Voice Note Transcription & Notion Integration

Manual queue-based pipeline for transcribing voice notes and saving structured meeting minutes to Notion with markdown backups.  

If you're here as a [Flocode](https://flocode.substack.com/) subscriber - welcome 👋

## 🚀 New User? Start Here!

**Never used this before? Follow these 4 steps:**
1. **Install dependencies**: `uv sync`
2. **Install FFmpeg**: Open PowerShell as Admin → `choco install ffmpeg`
3. **Get API keys**: OpenAI + Notion (required), Groq + Gemini (recommended)
4. **Test setup**: `uv run tests/test_voice_system.py`

**Then drag & drop your first voice note into `quick_process.bat`** ✨

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

### 2. Install FFmpeg (Required for Audio Processing)

**Windows - Easy Install (Recommended):**
1. **Open PowerShell as Administrator** (Right-click → "Run as administrator")
2. **Install Chocolatey** (if not installed):
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```
3. **Install FFmpeg**:
   ```powershell
   choco install ffmpeg
   ```
4. **Restart your terminal** and test: `ffmpeg -version`

**Alternative Methods:**
- **Scoop**: `scoop install ffmpeg`
- **Manual**: Download from https://ffmpeg.org/download.html, extract to `C:\ffmpeg`, add `C:\ffmpeg\bin` to PATH

### 3. Configure Environment

**Step 1: Copy the template**
```bash
# Copy the example file to create your .env
cp .env.example .env
```

**Step 2: Get your API keys**

🔑 **Required APIs** (you need at least these):
- **OpenAI**: Get API key from https://platform.openai.com/api-keys
- **Notion**: Create integration at https://www.notion.so/my-integrations

🚀 **Recommended APIs** (for best performance):
- **Groq**: Fast transcription - https://console.groq.com/keys
- **Gemini**: Best summarization - https://makersuite.google.com/app/apikey

📋 **Get Notion Database ID**:
1. Open your Notion database in web browser
2. Copy URL from address bar
3. Database ID is the 32-character string: `https://notion.so/workspace/Database-Name-1f39eccecd884ebab89eb1697c08ab10`
4. In this example: `1f39eccecd884ebab89eb1697c08ab10`

**Step 3: Update your `.env` file**
```env
# Required - Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-your_actual_openai_key_here

# Required - Create at https://www.notion.so/my-integrations  
NOTION_API_KEY=ntn_your_actual_notion_key_here
NOTION_DATABASE_ID=your_32_character_database_id_here

# Recommended - Get from https://console.groq.com/keys
GROQ_API_KEY=gsk_your_groq_key_here

# Recommended - Get from https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_key_here

# Your voice notes folder (use quotes for paths with spaces)
VOICE_NOTES_FOLDER="C:\Users\YourName\Documents\Voice Notes"

# Your organization info (personalizes meeting minutes)
COMPANY_NAME="Your Company Name"
COMPANY_SHORTHAND="YCN"
```

💡 **Tips:**
- Use quotes around paths with spaces
- Keep your `.env` file private - never commit it to git
- Share the database with your Notion integration for access

### 4. Test Your Setup

**Test API connections and configuration:**
```bash
# Test all APIs and create a test Notion entry
uv run tests/test_voice_system.py

# Test desktop notifications
uv run tests/test_notification.py
```

**Expected output for successful setup:**
```
🧪 Voice Note Monitoring System Test Suite
==================================================
🔍 Testing environment variables...
✅ All environment variables are set

🔍 Testing OpenAI connection...
✅ OpenAI connection successful

🔍 Testing Notion connection...
✅ Notion connection successful. Database: Your Database Name

🔍 Testing Gemini connection...
✅ Gemini connection successful

📊 Test Results: 6/6 tests passed
🎉 All tests passed! Your system is ready to use.
```

**If tests fail:**
- Check your `.env` file has the correct API keys
- Ensure Notion database is shared with your integration
- Verify your internet connection

## Usage

### 🚀 Quick Start Methods

#### Method 1: Drag & Drop (Easiest)
1. **Double-click** `quick_process.bat` 
2. **Drag and drop** your audio file into the terminal window
3. **Press Enter** - the file processes immediately with desktop notifications

💡 **Pro Tip**: Create a desktop shortcut to `quick_process.bat` for one-click access:
```
Right-click quick_process.bat → Send to → Desktop (create shortcut)
```

#### Method 2: File Browser Selection
1. **Double-click** `select_and_process.bat`
2. **Browse and select** your audio file from the dialog
3. **Automatic processing** starts immediately

#### Method 3: Interactive Mode (Advanced)
```bash
# Start interactive mode
uv run scripts/process_voice_notes.py --interactive

# Commands in interactive mode:
# add <file_or_url>  - Add file or URL to processing queue
# latest             - Process latest file from voice notes folder
# select             - Browse and select files to add to queue
# process            - Process next item in queue
# process_all        - Process all items in queue
# p                  - Quick process all queued items
# queue              - Show current queue
# clear              - Clear the queue
# quit               - Exit interactive mode
```

#### Method 4: Command Line
```bash
# Process single file or URL immediately
uv run scripts/process_voice_notes.py audio_file.mp3
uv run scripts/process_voice_notes.py https://example.com/audio.mp3

# Add multiple files to queue and process them
uv run scripts/process_voice_notes.py file1.mp3 file2.wav

# Process all items in queue
uv run scripts/process_voice_notes.py --process-queue
```

## Queue Management

The system uses a simple text-based queue (`processing_queue.txt`) that persists between sessions. You can:

1. **Add items**: Files or URLs are added to the queue
2. **Process items**: Items are processed one by one and removed from queue upon success
3. **View queue**: Check what's currently queued for processing
4. **Clear queue**: Remove all items from queue

## Output & Notifications

### 📁 File Output
Each processed file creates:
- **Markdown backup**: Saved in `transcription_backups/` with timestamp
- **Notion entry**: Added to your configured Notion database (if successful)
- **Processing log**: Tracks completed files to avoid reprocessing

### 🔔 Desktop Notifications
The system provides real-time feedback via Windows notifications:
- **✅ Success**: "Meeting Minutes successfully added to Notion" with filename
- **❌ Error**: Detailed error message if processing fails
- **📊 Batch Complete**: Summary when processing multiple files

No need to watch the terminal - you'll be notified when your transcription is ready!

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

### Common Issues

#### "FFmpeg not found" Error
```
[ERROR] FFmpeg not found! Please install FFmpeg
```
**Solution**: Install FFmpeg and add to PATH:
1. **Open PowerShell as Administrator** (Right-click → "Run as administrator")
2. **Install via Chocolatey**: `choco install ffmpeg`
3. **Restart your terminal** and test: `ffmpeg -version`

**Alternative**: Download from https://ffmpeg.org, extract, add `bin` folder to PATH

#### "Failed to transcribe audio"
- Check your API keys in `.env` file
- Ensure audio file exists and isn't corrupted
- Try smaller audio files first (< 10 minutes)

#### "Notion failed but backup saved"
- Check `NOTION_API_KEY` and `NOTION_DATABASE_ID` in `.env`
- Ensure Notion integration has access to the database
- Backup files are saved in `transcription_backups/` folder

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

- ⚠️ **Never commit your `.env` file** - it contains sensitive API keys
- 🔐 **Use environment variables for all secrets** - all sensitive data is properly configured via `.env`
- 🛡️ **Keep your `.env` file private** - add it to `.gitignore`
- 🔄 **Rotate API keys if exposed** - immediately regenerate any compromised keys
- 📝 **Company information is configurable** - no hardcoded company names in the codebase
- 🔒 **Safe for open source** - all sensitive data externalized to environment variables

## License

MIT

> 📢 Visit https://flocode.substack.com/ for more engineering tools.