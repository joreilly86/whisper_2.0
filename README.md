# Meeting Notes Generator (Folder Watcher Version)

A simple, local tool to automatically transcribe meeting recordings and generate well-organized meeting notes using Whisper and modern LLMs by monitoring a folder.

## Features

-   **Folder Monitoring**: Automatically processes audio files dropped into a designated `raw_audio` folder.
-   **Automatic Transcription**: Uses OpenAI's Whisper model locally.
-   **AI-Generated Meeting Notes**: Creates summaries with key points, action items, and decisions.
-   **Multiple AI Providers**: Supports OpenAI (GPT models) and Anthropic (Claude models) for summarization.
-   **Organized Output**: Saves transcripts and summaries to separate folders (`transcriptions`, `summaries`).
-   **Processed File Handling**: Moves original audio files to a `completed` folder after processing.

## Requirements

-   Python 3.9+
-   **FFmpeg**: Must be installed and accessible system-wide or placed in the project's `bin` directory as configured.
-   **API Keys** (stored in `.env` file):
    -   OpenAI API Key (for Whisper transcription and optional GPT summarization)
    -   Anthropic API Key (optional, for Claude summarization)

## Quick Start

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/meeting-notes-generator.git
    cd meeting-notes-generator
    ```

2.  **Set up Virtual Environment & Install Dependencies**:
    ```bash
    # Create venv (replace 'python' with 'python3' if needed)
    python -m venv .venv
    # Activate (adjust for your shell)
    # Windows CMD: .venv\Scripts\activate.bat
    # Windows PowerShell: .venv\Scripts\Activate.ps1
    # Linux/macOS: source .venv/bin/activate
    source .venv/bin/activate

    # Install dependencies using uv
    uv pip install -r requirements.txt # Or use uv sync if pyproject.toml is primary
    # If you don't have uv: pip install -r requirements.txt
    ```
    *(Note: If `requirements.txt` is outdated, generate it from `pyproject.toml` if needed or install directly from `pyproject.toml` using `uv pip install .`)*

3.  **Configure Environment Variables**:
    -   Create or edit the `.env` file in the project root.
    -   Add your API keys:
        ```dotenv
        OPENAI_API_KEY="your-openai-api-key-here"
        ANTHROPIC_API_KEY="your-anthropic-api-key-here"
        ```
    -   Choose your default AI provider for summarization:
        ```dotenv
        DEFAULT_SUMMARY_MODEL="openai"  # or "anthropic"
        ```
    -   Configure AI models and Whisper model size if desired (see Customization section).

4.  **Place FFmpeg**:
    -   Ensure `ffmpeg.exe` and `ffprobe.exe` are accessible. Either:
        -   Install FFmpeg system-wide and add it to your PATH.
        -   OR Download FFmpeg and place the `ffmpeg.exe` and `ffprobe.exe` files inside a `bin/ffmpeg-master-latest-win64-gpl/bin` subdirectory within the project root (as configured in the script).

5.  **Run the Folder Watcher**:
    ```bash
    python folder_watcher.py
    ```
    The script will start monitoring the `raw_audio` folder.

## How It Works

1.  Run `python folder_watcher.py`.
2.  Drop an audio file (MP3, WAV, M4A, FLAC) into the `raw_audio` folder located in the project directory.
3.  The watcher detects the new file and starts processing:
    -   **Transcription**: Converts audio to text using Whisper. Saves `.txt` and `.json` files to the `transcriptions` folder.
    -   **Summarization**: Generates meeting notes using the configured AI provider (OpenAI or Anthropic). Saves `.txt` and `.json` files to the `summaries` folder.
4.  Once both steps are complete (or if transcription fails), the original audio file is moved from `raw_audio` to the `completed` folder.

## Customization

### AI Models for Summarization

Configure your preferred models in the `.env` file:

-   **OpenAI**:
    -   `OPENAI_MODEL="gpt-4o"` (Default)
-   **Anthropic**:
    -   `ANTHROPIC_MODEL="claude-3-haiku"` (Default)
    -   Other options: `claude-3-sonnet`, `claude-3-opus`

Set `DEFAULT_SUMMARY_MODEL` in `.env` to `"openai"` or `"anthropic"`.

### Transcription Model

-   The application uses Whisper's `medium` model by default.
-   Configure in `.env` with `WHISPER_MODEL_SIZE`.
-   Options: `tiny`, `base`, `small`, `medium`, `large`. Larger models are more accurate but slower and require more resources (VRAM if using GPU).

## Troubleshooting

-   **FFmpeg Not Found**: Ensure FFmpeg is correctly installed and accessible (either in PATH or in the project's `bin` directory as configured). Check the paths set in `folder_watcher.py`.
-   **API Key Errors**: Verify your `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` in the `.env` file are correct and have the necessary permissions/credits.
-   **Processing Errors**: Check the console output where `folder_watcher.py` is running for detailed error messages and tracebacks.
-   **Permissions**: Ensure the script has read/write permissions for the `raw_audio`, `transcriptions`, `summaries`, and `completed` folders.
