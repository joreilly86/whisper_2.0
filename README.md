# M4A Audio Transcriber

This tool splits large M4A audio files into smaller MP3 chunks, transcribes each chunk using OpenAI's Whisper API, and then combines the transcriptions into a single text file.

The project includes:
1.  `transcribe.py`: A script to manually transcribe a single audio file from the `uploads/` folder.
2.  `watcher.py`: A script that monitors the `uploads/` folder and automatically triggers `transcribe.py` for newly added M4A files.

Both scripts use an `uploads/` folder for input audio files and a `transcriptions/` folder for the output text files.

## Project Structure

```
.
├── .env             # (User-created with API key after setup)
├── .env.example     # (Template for .env)
├── .gitignore
├── .python-version
├── .venv/           # (Python virtual environment, created during setup at root)
├── pyproject.toml
├── README.md
├── requirements.txt # (Python dependencies)
├── transcribe.py    # (The manual transcription script)
├── watcher.py       # (The automatic folder watching script)
├── uploads/         # (Directory for input M4A audio files)
├── transcriptions/  # (Directory for output .txt transcript files)
└── uv.lock
```
The `uploads/` and `transcriptions/` directories will be created automatically by the scripts if they don't exist.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

1.  **Python**: Version 3.8 or higher is recommended.
2.  **`uv`**: This project uses `uv` for Python package and environment management. If you don't have it, please install it. (Follow instructions from [astral.sh/uv](https://astral.sh/uv)).
3.  **FFmpeg**: This is required by `pydub` (a dependency of this tool) to process audio files (M4A to MP3 conversion).
    *   Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html).
    *   Ensure the FFmpeg executable is in your system's PATH. The `transcribe.py` script will show an error if it cannot find FFmpeg.

## Setup

1.  **Clone the Repository (if applicable) or Ensure Files are Present:**
    Make sure you have all project files at the root directory.

2.  **Navigate to the Project Root Directory:**
    Open your terminal and ensure you are in the project's root directory (e.g., `c:/Users/joreilly/dev/whisper_2.0/`).

3.  **Create and Activate Virtual Environment:**
    Use `uv` to create a virtual environment in the project root:
    ```bash
    uv venv
    ```
    Activate the environment:
    ```bash
    # On Windows:
    .\.venv\Scripts\activate
    # On macOS/Linux:
    # source .venv/bin/activate
    ```
    `uv` might automatically use the `.venv` in the current directory for subsequent commands.

4.  **Install Dependencies:**
    Install the required Python packages (including `openai`, `pydub`, `python-dotenv`, and `watchdog`) using `uv`:
    ```bash
    uv pip install -r requirements.txt
    ```

5.  **Set Up OpenAI API Key:**
    *   Copy the example environment file:
        ```bash
        copy .env.example .env  # Windows
        # cp .env.example .env    # macOS/Linux
        ```
    *   Open the newly created `.env` file in a text editor.
    *   Replace `your_key_here` with your actual OpenAI API key:
        ```env
        OPENAI_API_KEY=sk-yourActualOpenAIKeyGoesHere
        ```
    *   Save the `.env` file.

## Usage

You have two ways to transcribe audio files:

### Option 1: Automatic Processing with Folder Watcher (Recommended for ease of use)

1.  **Start the Watcher:**
    Run the `watcher.py` script from the project root (ensure your virtual environment is active or use `uv run`):
    ```bash
    python watcher.py
    ```
    Or:
    ```bash
    uv run python watcher.py
    ```
    The watcher will log that it has started and is monitoring the `uploads/` directory. Keep this terminal window open.

2.  **Add Audio Files:**
    Simply drag and drop (or copy) your M4A audio files into the `uploads/` directory.
    The watcher will detect new M4A files and automatically trigger `transcribe.py` for each one.

3.  **Output:**
    *   Logs from both `watcher.py` and `transcribe.py` will appear in the terminal where `watcher.py` is running.
    *   Transcripts will be saved to the `transcriptions/` directory with matching filenames (e.g., `uploads/meeting.m4a` becomes `transcriptions/meeting.txt`).

4.  **Stop the Watcher:**
    Press `Ctrl+C` in the terminal where `watcher.py` is running.

### Option 2: Manual Transcription of a Single File

1.  **Place Audio File:**
    Ensure your M4A audio file (e.g., `my_meeting.m4a`) is in the `uploads/` directory.

2.  **Run the Transcription Script:**
    Execute `transcribe.py` from the project root, providing the **filename** of the audio file:
    ```bash
    python transcribe.py <audio_filename.m4a>
    ```
    **Example:**
    ```bash
    python transcribe.py my_meeting.m4a
    ```
    Or using `uv run`:
    ```bash
    uv run python transcribe.py my_meeting.m4a
    ```

3.  **Output:**
    *   Progress logs from `transcribe.py` will appear in the console.
    *   The transcript will be saved to the `transcriptions/` directory.

## Troubleshooting

*   **FFmpeg Not Found:** Ensure FFmpeg is installed and its `bin` directory is in your system's PATH.
*   **OpenAI API Key Not Found:** Check your `.env` file at the project root.
*   **File Not Found (for `transcribe.py` manual mode):** Ensure the audio file exists in `uploads/` and you're providing only the filename.
*   **Watcher Not Detecting Files:**
    *   Verify `watcher.py` is running and monitoring the correct `uploads/` directory.
    *   Ensure files are M4A (currently, only `.m4a` is processed by the watcher).
*   **Permission Errors:** Ensure write permissions for `uploads/`, `transcriptions/`, and `temp_audio_chunks/`.
