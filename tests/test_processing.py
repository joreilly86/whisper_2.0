import os
import unittest
import subprocess
from unittest.mock import patch, MagicMock
from src.whisper_2_0 import audio_processing, transcription, summarization, config, notion_integration

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

    def test_api_key_configuration(self):
        """Test that required API keys are configured."""
        # Check that at least one transcription API key is set
        transcription_keys_configured = (
            bool(os.environ.get('GROQ_API_KEY')) or 
            bool(os.environ.get('OPENAI_API_KEY'))
        )
        self.assertTrue(transcription_keys_configured, 
                       "At least one transcription API key (GROQ_API_KEY or OPENAI_API_KEY) must be configured")
        
        # Check that at least one summarization API key is set
        summarization_keys_configured = (
            bool(os.environ.get('GEMINI_API_KEY')) or 
            bool(os.environ.get('OPENAI_API_KEY'))
        )
        self.assertTrue(summarization_keys_configured,
                       "At least one summarization API key (GEMINI_API_KEY or OPENAI_API_KEY) must be configured")
        
        # Check Notion configuration
        notion_configured = (
            bool(os.environ.get('NOTION_API_KEY')) and 
            bool(os.environ.get('NOTION_DATABASE_ID'))
        )
        self.assertTrue(notion_configured,
                       "Both NOTION_API_KEY and NOTION_DATABASE_ID must be configured")

    def test_batch_file_exists_and_executable(self):
        """Test that the quick_process.bat file exists and is properly configured."""
        bat_file_path = 'quick_process.bat'
        self.assertTrue(os.path.exists(bat_file_path), 
                       "quick_process.bat file must exist in the project root")
        
        # Test that the batch file contains proper error handling
        with open(bat_file_path, 'r', encoding='utf-8') as f:
            bat_content = f.read()
        
        # Check for error handling keywords
        self.assertIn('errorlevel', bat_content, 
                     "Batch file should include error level checking")
        self.assertIn('error_exit', bat_content, 
                     "Batch file should include error exit handling")
        self.assertIn('pause', bat_content, 
                     "Batch file should pause on errors so user can see messages")

    def test_notion_markdown_parsing(self):
        """Test that markdown content is properly parsed for Notion blocks."""
        # Test various markdown elements
        test_content = """# Main Heading

This is a **bold** paragraph with *italic* text.

## Subheading

- Bullet point 1
- Bullet point 2
- Bullet point 3

1. Numbered item 1
2. Numbered item 2

> This is a quote

```
This is a code block
```

Regular paragraph text."""

        blocks = notion_integration.parse_markdown_to_notion_blocks(test_content)
        
        # Should have multiple blocks
        self.assertGreater(len(blocks), 1, "Should parse multiple blocks from markdown")
        
        # Check for heading blocks
        heading_blocks = [b for b in blocks if b['type'] in ['heading_1', 'heading_2', 'heading_3']]
        self.assertGreater(len(heading_blocks), 0, "Should parse heading blocks")
        
        # Check for list blocks
        list_blocks = [b for b in blocks if b['type'] in ['bulleted_list_item', 'numbered_list_item']]
        self.assertGreater(len(list_blocks), 0, "Should parse list blocks")
        
        # Check for paragraph blocks
        paragraph_blocks = [b for b in blocks if b['type'] == 'paragraph']
        self.assertGreater(len(paragraph_blocks), 0, "Should parse paragraph blocks")

    def test_rich_text_formatting(self):
        """Test that rich text formatting works correctly."""
        # Test bold text
        bold_result = notion_integration.parse_rich_text("This is **bold** text")
        bold_found = any(item.get('annotations', {}).get('bold') for item in bold_result)
        self.assertTrue(bold_found, "Should parse bold formatting")
        
        # Test italic text
        italic_result = notion_integration.parse_rich_text("This is *italic* text")
        italic_found = any(item.get('annotations', {}).get('italic') for item in italic_result)
        self.assertTrue(italic_found, "Should parse italic formatting")

    def test_environment_file_exists(self):
        """Test that .env file exists or warn user."""
        env_file_exists = os.path.exists('.env')
        if not env_file_exists:
            print("\nWARNING: .env file not found. Please ensure API keys are configured.")
            print("Run: cp .env.example .env and add your API keys")

if __name__ == '__main__':
    unittest.main()
