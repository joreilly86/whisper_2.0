"""
Initializes and configures API clients for the Voice Note Processor.
"""

import sys
import google.generativeai as genai
from openai import OpenAI
from notion_client import Client
import groq
from . import config


def get_openai_client():
    """Initializes and returns the OpenAI client."""
    if not config.OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in .env file")
        sys.exit(1)
    return OpenAI(api_key=config.OPENAI_API_KEY)


def get_notion_client():
    """Initializes and returns the Notion client."""
    if not config.NOTION_API_KEY:
        print("Error: NOTION_API_KEY not found in .env file")
        sys.exit(1)
    if not config.NOTION_DATABASE_ID:
        print("Error: NOTION_DATABASE_ID not found in .env file")
        sys.exit(1)
    return Client(auth=config.NOTION_API_KEY)


def get_gemini_client():
    """Initializes and returns the Gemini client."""
    if config.GEMINI_API_KEY:
        genai.configure(api_key=config.GEMINI_API_KEY)
        return genai
    return None


def get_groq_client():
    """Initializes and returns the Groq client."""
    if config.GROQ_API_KEY:
        return groq.Groq(api_key=config.GROQ_API_KEY)
    return None


# Initialize clients
client = get_openai_client()
notion = get_notion_client()
genai_client = get_gemini_client()
groq_client = get_groq_client()
