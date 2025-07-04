# Local Transcription Service

This tool provides an automated pipeline for transcribing audio files. It watches a specified folder for new audio files (MP3 or M4A), transcribes them using OpenAI's Whisper API, and then post-processes the transcript into a structured format using a GPT-4 model.

## Features

*   **Automated Transcription:** Runs in the background and automatically processes new audio files.
*   **Custom Watch Folder:** Can be configured to watch any folder on your system.
*   **Post-processing:** Cleans up raw transcripts into a polished, professional format.
*   **Backup Raw Transcripts:** Saves a copy of the raw, unedited transcript for your records.

## Setup

1.  **Install FFmpeg:** This is required for audio processing. You can download it from [ffmpeg.org](https://ffmpeg.org/download.html) and add it to your system's PATH.
2.  **Set Up API Key:** Copy the `.env.example` file to a new file named `.env` and add your OpenAI API key.

## How to Use

### The Golden Rule: Start the Watcher First!

This tool works by watching a folder in real-time. For it to see and process a new file, the script must already be running.

### Daily Workflow

1.  **Start the Transcription Service:**
    *   Double-click the `transcribe.bat` file. A terminal window will open, indicating that the script is now watching the default `uploads` folder.
    *   **Keep this window open.** The service will stop if you close it.

2.  **Add Your Audio Files:**
    *   Save, copy, or drag your `.mp3` or `.m4a` files into the folder being watched.

3.  **Get Your Transcripts:**
    *   The script will automatically detect the new file and begin processing.
    *   A raw, unedited transcript will be saved in the `transcriptions/raw` folder.
    *   The final, post-processed meeting minutes will be saved in the main `transcriptions` folder.

### Watching a Specific Folder

If you want to watch a folder other than the default `uploads` directory (for example, your `Voice Notes` folder), you can create a shortcut to the `transcribe.bat` file. In the shortcut's properties, edit the "Target" field and add the full path to the folder you want to watch.

**Example Target:**

```
C:\Users\joreilly\dev\whisper_2.0\transcribe.bat "C:\Users\joreilly\OneDrive - Knight Piesold\Voice Notes"
```

## Customizing the Output

You can change the post-processing instructions by editing the `post_processing_prompt.txt` file. This allows you to tailor the final output to your specific needs.
