"""
Functions for summarizing transcribed text.
"""

import os
from . import api_clients
from . import config


def load_processing_prompt():
    """Load and process the summarization prompt template."""
    # Load the post-processing prompt
    if os.path.exists("scripts/processing_prompt.md"):
        with open("scripts/processing_prompt.md", "r", encoding="utf-8") as f:
            prompt_text = f.read()
    elif os.path.exists(config.POST_PROCESSING_PROMPT_FILE):
        with open(config.POST_PROCESSING_PROMPT_FILE, "r", encoding="utf-8") as f:
            prompt_text = f.read()
    else:
        prompt_text = (
            "Act as an expert meeting assistant. "
            "Create a structured summary of voice note transcripts. "
            "Include a title, key discussion points, and any action items mentioned. "
            "Format the response in a clear, professional manner suitable for Notion."
        )

    # Replace company placeholders with environment variables
    prompt_text = prompt_text.replace("{COMPANY_NAME}", config.COMPANY_NAME)
    prompt_text = prompt_text.replace("{COMPANY_SHORTHAND}", config.COMPANY_SHORTHAND)

    return prompt_text


def clean_ai_response(response_text):
    """Clean AI response to remove conversational preamble."""
    if not response_text:
        return response_text
    
    # Common preamble patterns to remove
    preamble_patterns = [
        r"^(?:Of course[.,]?\s*)?Here (?:are|is) the meeting minutes?.*?(?:\n|$)",
        r"^Based on the (?:provided )?transcript.*?(?:\n|$)",
        r"^I'll (?:create|provide|generate).*?meeting minutes?.*?(?:\n|$)",
        r"^(?:Certainly[.,]?\s*)?(?:Here's|Here are).*?(?:summary|minutes?).*?(?:\n|$)",
        r"^(?:Sure[.,]?\s*)?(?:I'll|Let me).*?(?:summarize|create).*?(?:\n|$)",
        r"^(?:Absolutely[.,]?\s*)?(?:Here's|Here are) (?:a |the )?(?:clean |structured )?(?:meeting )?(?:summary|minutes?).*?(?:\n|$)",
    ]
    
    cleaned_text = response_text.strip()
    
    # Remove preamble patterns
    import re
    for pattern in preamble_patterns:
        cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
    
    # Remove any leading whitespace/newlines after cleaning
    cleaned_text = cleaned_text.strip()
    
    return cleaned_text


def summarize_with_gemini(text):
    """Summarize text using Gemini API with post-processing prompt."""
    if not api_clients.genai_client:
        print("Warning: GEMINI_API_KEY not found, skipping Gemini summarization")
        return None

    if not text or not text.strip():
        print("Error: No text provided for summarization")
        return None

    print("Summarizing text with Gemini...")
    try:
        model = api_clients.genai_client.GenerativeModel("gemini-2.5-pro")
        prompt_text = load_processing_prompt()
        response = model.generate_content(prompt_text + "\n\n" + text)
        return clean_ai_response(response.text)
    except Exception as e:
        print(f"Error during Gemini summarization: {e}")
        return None


def summarize_with_openai(text):
    """Summarize text using OpenAI GPT-4 as fallback with post-processing prompt."""
    if not text or not text.strip():
        print("Error: No text provided for summarization")
        return None

    print("Summarizing text with OpenAI GPT-4...")
    try:
        prompt_text = load_processing_prompt()
        response = api_clients.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt_text},
                {"role": "user", "content": text},
            ],
        )
        return clean_ai_response(response.choices[0].message.content.strip())
    except Exception as e:
        print(f"Error during OpenAI summarization: {e}")
        return None
