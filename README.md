# Voice Note Transcription & Notion Integration

A command-line tool for transcribing voice notes and saving structured meeting minutes to Notion.

This tool is discussed as part of the [**Flocode Newsletter**](https://flocode.substack.com/), which is for professional engineers using Python and AI tools to support their work. Although this tool is domain agnostic!

## Features

- **🎤 High-Quality Transcription**: Utilizes Groq (whisper-large-v3-turbo) and OpenAI Whisper for accurate speech-to-text conversion.
- **🤖 AI-Powered Summarization**: Leverages Google Gemini (with an OpenAI fallback) to generate structured and insightful meeting minutes.
- **📝 Notion Integration**: Automatically creates new entries in your Notion database with a title, date, and the full transcription.
- **🔔 Real-Time Notifications**: Get desktop notifications on the status of your transcriptions.
- **💾 Local Backups**: Keeps a local markdown backup of every transcription for your records.
- **🔒 Secure Configuration**: All API keys and sensitive information are managed securely through environment variables.

## Getting Started

### Prerequisites

- **Python 3.12+**
- **`uv`**: A fast Python package installer. If you don't have it, run: `pip install uv`
- **FFmpeg**: A required tool for audio processing.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/whisper_2.0.git
    cd whisper_2.0
    ```

2.  **Install dependencies:**
    ```bash
    uv sync
    ```

3.  **Install FFmpeg:**
    - **Windows (with Chocolatey):**
      ```powershell
      choco install ffmpeg
      ```
    - **macOS (with Homebrew):**
      ```bash
      brew install ffmpeg
      ```
    - **Linux (with apt):**
      ```bash
      sudo apt update && sudo apt install ffmpeg
      ```

### Configuration

1.  **Create a `.env` file:**
    ```bash
    cp .env.example .env
    ```

2.  **Add your API keys to the `.env` file:**
    - `OPENAI_API_KEY`: Your OpenAI API key.
    - `GROQ_API_KEY`: Your Groq API key (for faster transcriptions).
    - `GEMINI_API_KEY`: Your Google Gemini API key (for better summarization).
    - `NOTION_API_KEY`: Your Notion integration secret.
    - `NOTION_DATABASE_ID`: The ID of your Notion database.
    - `COMPANY_NAME` (optional): Your company's name for personalizing meeting minutes (e.g. 'Flocode').
    - `COMPANY_SHORTHAND` (optional): A shorthand for your company (e.g. 'FC').

### Test Your Setup

Run the test suite to ensure everything is configured correctly:
```bash
uv run python tests/test_voice_system.py
```

## Usage

### Interactive Mode

The easiest way to use the tool is in interactive mode:
```bash
uv run python scripts/process_voice_notes.py --interactive
```
This will give you a list of commands to add, process, and manage your transcription queue.

### Command-Line

You can also process files directly from the command line:
```bash
uv run python scripts/process_voice_notes.py /path/to/your/audio.mp3
```

## My Preferred Workflow

For a seamless experience, you can use the included `quick_process.bat` script. This is my preferred method for quick, on-the-fly transcriptions.

1.  **Create a shortcut** to `quick_process.bat` on your desktop.
2.  **Drag and drop** an audio file directly onto the shortcut.
3.  The script will immediately start processing the file, providing you with notifications along the way.

This workflow is especially powerful when combined with a tool like [**VoiceMeeter Banana**](https://vb-audio.com/Voicemeeter/banana.htm), which can be configured to record all desktop audio and microphone input into a single audio file.

> **📢 Disclaimer:** Please be aware of and comply with all local laws and regulations regarding obtaining consent before recording conversations.

## How It Works

1.  **Queue Management**: Files and URLs are added to a persistent queue.
2.  **Audio Processing**: Audio files are chunked into smaller segments for efficient processing.
3.  **Transcription**: The audio is transcribed using either Groq or OpenAI's Whisper model.
4.  **Summarization**: The transcript is summarized by Gemini or GPT-4 into structured meeting minutes.
5.  **Storage**: The final output is saved as a local markdown file and as a new page in your Notion database.

## Contributing

Contributions are welcome! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for details.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
