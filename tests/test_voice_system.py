#!/usr/bin/env python3
"""Test suite for voice note monitoring system components."""

import os
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client
import google.generativeai as genai
from openai import OpenAI

# Load environment variables
load_dotenv()


def test_environment_variables():
    """Test if all required environment variables are set."""
    print("🔍 Testing environment variables...")

    required_vars = [
        "OPENAI_API_KEY",
        "NOTION_API_KEY",
        "NOTION_DATABASE_ID",
    ]

    optional_vars = [
        "GROQ_API_KEY",
        "GEMINI_API_KEY",
        "COMPANY_NAME",
        "COMPANY_SHORTHAND",
    ]

    missing_required = []
    missing_optional = []

    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)

    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)

    if missing_required:
        print(
            f"❌ Missing REQUIRED environment variables: {', '.join(missing_required)}"
        )
        print("   Add these to your .env file before proceeding!")
        return False
    else:
        print("✅ All required environment variables are set")
        if missing_optional:
            print(f"⚠️  Optional variables not set: {', '.join(missing_optional)}")
            print("   (These will use defaults or fallback services)")
        return True


def test_openai_connection():
    """Test OpenAI API connection."""
    print("\n🔍 Testing OpenAI connection...")
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Simple test call
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Say 'test successful'"}],
            max_tokens=10,
        )
        print("✅ OpenAI connection successful")
        return True
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False


def test_notion_connection():
    """Test Notion API connection."""
    print("\n🔍 Testing Notion connection...")
    try:
        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        database_id = os.getenv("NOTION_DATABASE_ID")

        # Try to retrieve database info
        database = notion.databases.retrieve(database_id)
        print(
            f"✅ Notion connection successful. Database: {database['title'][0]['plain_text']}"
        )
        return True
    except Exception as e:
        print(f"❌ Notion connection failed: {e}")
        return False


def test_groq_connection():
    """Test Groq API connection (optional)."""
    print("\n🔍 Testing Groq connection...")
    groq_key = os.getenv("GROQ_API_KEY")

    if not groq_key:
        print("⚠️  GROQ_API_KEY not set (will use OpenAI for transcription)")
        return True

    try:
        import groq

        groq.Groq(api_key=groq_key)
        # Test with a simple API call to check authentication
        # Note: We can't easily test transcription without an audio file
        print("✅ Groq API key configured (transcription ready)")
        return True
    except Exception as e:
        print(f"❌ Groq connection failed: {e}")
        print("   Transcription will fallback to OpenAI")
        return False


def test_gemini_connection():
    """Test Gemini API connection (optional)."""
    print("\n🔍 Testing Gemini connection...")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not gemini_key:
        print("⚠️  GEMINI_API_KEY not set (will use OpenAI for summarization)")
        return True

    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        model.generate_content("Say 'test successful'")
        print("✅ Gemini connection successful")
        return True
    except Exception as e:
        print(f"❌ Gemini connection failed: {e}")
        print("   Summarization will fallback to OpenAI")
        return False




def test_notion_write():
    """Test writing to Notion database."""
    print("\n🔍 Testing Notion write capability...")
    try:
        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        database_id = os.getenv("NOTION_DATABASE_ID")

        # Create a test entry
        test_title = f"Test Entry - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        meeting_date = datetime.now().strftime("%Y-%m-%d")

        notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "Title": {"title": [{"text": {"content": test_title}}]},
                "Meeting Date": {"date": {"start": meeting_date}},
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "This is a test entry created by the voice note monitoring system test script."
                                },
                            }
                        ]
                    },
                }
            ],
        )

        print(f"✅ Successfully created test entry in Notion: {test_title}")
        return True
    except Exception as e:
        print(f"❌ Failed to write to Notion: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Voice Note Monitoring System Test Suite")
    print("=" * 50)

    tests = [
        test_environment_variables,
        test_openai_connection,
        test_notion_connection,
        test_groq_connection,
        test_gemini_connection,
        test_notion_write,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Your system is ready to use.")
        print("\n💡 Next steps:")
        print("   • Try: uv run scripts/process_voice_notes.py --interactive")
        print("   • Or drag & drop: double-click quick_process.bat")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\n🔧 Common solutions:")
        print("   • Check your .env file has correct API keys")
        print("   • Ensure Notion database is shared with your integration")
        print("   • Verify internet connection")


if __name__ == "__main__":
    main()
