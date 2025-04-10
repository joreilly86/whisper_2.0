import time
import json
import logging
from typing import Tuple, Dict, List, Any, Optional, Literal

import openai
import anthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

class SummarizationService:
    """Service for summarizing transcripts into meeting notes"""
    
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.anthropic_api_key = settings.ANTHROPIC_API_KEY
        self.default_model_provider = settings.DEFAULT_SUMMARY_MODEL
        self.openai_model = settings.OPENAI_MODEL
        self.anthropic_model = settings.ANTHROPIC_MODEL
        self.max_tokens = settings.SUMMARY_MAX_TOKENS
        
        # Initialize clients if keys are available
        self.openai_client = None
        self.anthropic_client = None
        
        if self.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        else:
            logger.warning("No OpenAI API key provided")
            
        if self.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        else:
            logger.warning("No Anthropic API key provided")
            
        # Validate configuration
        if not self.openai_client and not self.anthropic_client:
            logger.error("No API keys provided for either OpenAI or Anthropic - summarization will not work")
        elif self.default_model_provider == "openai" and not self.openai_client:
            logger.warning("Default provider is OpenAI but no API key provided - will try Anthropic if available")
        elif self.default_model_provider == "anthropic" and not self.anthropic_client:
            logger.warning("Default provider is Anthropic but no API key provided - will try OpenAI if available")
    
    def summarize(self, transcript_text: str, model_provider: Optional[str] = None) -> Tuple[str, Dict[str, Any], float]:
        """
        Summarize a transcript into meeting notes
        
        Args:
            transcript_text: The transcript text to summarize
            model_provider: Override the default model provider (openai or anthropic)
            
        Returns:
            - summary_text: plain text summary (markdown format)
            - summary_data: structured summary data
            - processing_time: how long the summarization took
        """
        logger.info("Generating meeting notes...")
        
        # Determine which provider to use
        provider = model_provider or self.default_model_provider
        
        # Fallback if the requested provider is not available
        if provider == "openai" and not self.openai_client:
            if self.anthropic_client:
                logger.warning("Falling back to Anthropic as OpenAI client is not available")
                provider = "anthropic"
            else:
                raise ValueError("OpenAI API key not provided and no fallback available")
        elif provider == "anthropic" and not self.anthropic_client:
            if self.openai_client:
                logger.warning("Falling back to OpenAI as Anthropic client is not available")
                provider = "openai"
            else:
                raise ValueError("Anthropic API key not provided and no fallback available")
        
        # Call the appropriate provider's summarization method
        if provider == "openai":
            return self._summarize_with_openai(transcript_text)
        else:
            return self._summarize_with_anthropic(transcript_text)
    
    def _summarize_with_openai(self, transcript_text: str) -> Tuple[str, Dict[str, Any], float]:
        """Use OpenAI to generate meeting notes"""
        if not self.openai_client:
            raise ValueError("OpenAI API key not provided")
        
        start_time = time.time()
        
        try:
            # Prepare system message
            system_message = """
            You are an expert meeting assistant. Your task is to analyze a meeting transcript and create comprehensive meeting notes.
            Organize the notes into the following sections:
            1. Summary: A concise overview of the meeting (2-3 paragraphs)
            2. Key Points: The main discussion points or topics covered
            3. Action Items: Tasks that were assigned or need to be completed
            4. Decisions: Any conclusions or decisions that were made
            
            Keep your notes clear, concise, and professional. Format in a way that's easy to read and action-oriented.
            Return your response as a JSON object with these fields: summary, key_points (array), action_items (array), and decisions (array).
            """
            
            # Make the API call
            completion = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": transcript_text}
                ],
                max_tokens=self.max_tokens,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Extract the response
            response_content = completion.choices[0].message.content
            
            # Parse the JSON response
            summary_data = json.loads(response_content)
            
            # Format the summary text
            summary_text = self._format_summary_text(summary_data)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Meeting notes generated with OpenAI ({self.openai_model}) in {processing_time:.2f} seconds")
            
            return summary_text, summary_data, processing_time
            
        except Exception as e:
            logger.error(f"Error during OpenAI summarization: {e}")
            raise
    
    def _summarize_with_anthropic(self, transcript_text: str) -> Tuple[str, Dict[str, Any], float]:
        """Use Anthropic Claude to generate meeting notes"""
        if not self.anthropic_client:
            raise ValueError("Anthropic API key not provided")
        
        start_time = time.time()
        
        try:
            # Prepare system message (Claude uses a single prompt with system instructions)
            prompt = f"""
            You are an expert meeting assistant. Your task is to analyze a meeting transcript and create comprehensive meeting notes.
            Organize the notes into the following sections:
            1. Summary: A concise overview of the meeting (2-3 paragraphs)
            2. Key Points: The main discussion points or topics covered
            3. Action Items: Tasks that were assigned or need to be completed
            4. Decisions: Any conclusions or decisions that were made
            
            Keep your notes clear, concise, and professional. Format in a way that's easy to read and action-oriented.
            Return your response as a JSON object with these fields: summary, key_points (array), action_items (array), and decisions (array).
            
            Here is the transcript to summarize:
            
            {transcript_text}
            """
            
            # Make the API call
            completion = self.anthropic_client.messages.create(
                model=self.anthropic_model,
                max_tokens=self.max_tokens,
                temperature=0.3,
                system="Analyze the meeting transcript and create well-structured meeting notes in JSON format.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract the response
            response_content = completion.content[0].text
            
            # Check if the response is already valid JSON
            try:
                summary_data = json.loads(response_content)
            except json.JSONDecodeError:
                # If not valid JSON, try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r"```(?:json)?(.*?)```", response_content, re.DOTALL)
                if json_match:
                    try:
                        summary_data = json.loads(json_match.group(1).strip())
                    except:
                        raise ValueError("Could not parse JSON from Claude response")
                else:
                    raise ValueError("Claude response does not contain valid JSON")
            
            # Format the summary text
            summary_text = self._format_summary_text(summary_data)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Meeting notes generated with Anthropic ({self.anthropic_model}) in {processing_time:.2f} seconds")
            
            return summary_text, summary_data, processing_time
            
        except Exception as e:
            logger.error(f"Error during Anthropic summarization: {e}")
            raise
    
    def _format_summary_text(self, summary_data: Dict[str, Any]) -> str:
        """Format the summary data into markdown text"""
        # Create plain text summary in markdown format
        summary_text = f"# Meeting Summary\n\n{summary_data['summary']}\n\n"
        
        summary_text += "## Key Points\n\n"
        for point in summary_data['key_points']:
            summary_text += f"- {point}\n"
            
        summary_text += "\n## Action Items\n\n"
        for item in summary_data['action_items']:
            summary_text += f"- {item}\n"
            
        summary_text += "\n## Decisions\n\n"
        for decision in summary_data['decisions']:
            summary_text += f"- {decision}\n"
        
        return summary_text

# Create a singleton instance
summarization_service = SummarizationService()
