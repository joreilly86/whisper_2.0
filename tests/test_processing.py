import os
import unittest
from unittest.mock import patch, MagicMock
from src.whisper_2_0 import audio_processing, transcription, summarization

class TestProcessing(unittest.TestCase):

    @patch('src.whisper_2_0.audio_processing.AudioSegment.from_file')
    def test_create_audio_chunks(self, mock_from_file):
        """Test the audio chunking functionality."""
        # Mock the AudioSegment object and its methods
        mock_audio = MagicMock()
        mock_audio.duration_seconds = 60
        mock_audio.channels = 1
        mock_audio.__len__.return_value = 60000  # 60 seconds in ms
        mock_from_file.return_value = mock_audio

        # Create a dummy file
        dummy_file = 'dummy.mp3'
        with open(dummy_file, 'w') as f:
            f.write('dummy content')

        # Run the function
        with patch('os.path.exists', return_value=True):
            chunks = audio_processing.create_audio_chunks(dummy_file)

        # Assert that the chunks were created
        self.assertGreater(len(chunks), 0)

        # Clean up the dummy file
        os.remove(dummy_file)

    @patch('src.whisper_2_0.transcription.audio_processing.create_audio_chunks')
    @patch('src.whisper_2_0.api_clients.groq_client')
    @patch('src.whisper_2_0.api_clients.client')
    def test_transcribe_audio_file(self, mock_openai_client, mock_groq_client, mock_create_chunks):
        """Test the transcription functionality."""
        # Mock the transcription clients
        mock_groq_client.audio.transcriptions.create.return_value.text = "Groq transcription"
        mock_openai_client.audio.transcriptions.create.return_value.text = "OpenAI transcription"
        mock_create_chunks.return_value = ['dummy_chunk.mp3']

        # Create a dummy file
        dummy_file = 'dummy.mp3'
        with open(dummy_file, 'w') as f:
            f.write('dummy content')

        # Test with Groq
        with patch('src.whisper_2_0.transcription.transcribe_chunks', return_value="Groq transcription"):
            result = transcription.transcribe_audio_file(dummy_file)
            self.assertEqual(result, "Groq transcription")

        # Test with OpenAI fallback
        with patch('src.whisper_2_0.transcription.transcribe_with_groq', return_value=None):
            with patch('src.whisper_2_0.transcription.transcribe_chunks', return_value="OpenAI transcription"):
                result = transcription.transcribe_audio_file(dummy_file)
                self.assertEqual(result, "OpenAI transcription")

        # Clean up the dummy file
        os.remove(dummy_file)

    @patch('src.whisper_2_0.api_clients.genai_client')
    @patch('src.whisper_2_0.api_clients.client')
    def test_summarization(self, mock_openai_client, mock_gemini_client):
        """Test the summarization functionality."""
        # Mock the summarization clients
        mock_gemini_client.GenerativeModel.return_value.generate_content.return_value.text = "Gemini summary"
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = "OpenAI summary"

        # Test with Gemini
        result = summarization.summarize_with_gemini("some text")
        self.assertEqual(result, "Gemini summary")

        # Test with OpenAI fallback
        with patch('src.whisper_2_0.summarization.summarize_with_gemini', return_value=None):
            result = summarization.summarize_with_openai("some text")
            self.assertEqual(result, "OpenAI summary")

if __name__ == '__main__':
    unittest.main()
