"""
Functions for interacting with Notion.
"""

import os
from datetime import datetime
from . import api_clients
from . import config


def save_backup_markdown(title, content, original_filename):
    """Save a local markdown backup of the transcription."""
    try:
        # Create backup folder if it doesn't exist
        os.makedirs(config.BACKUP_FOLDER, exist_ok=True)

        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(
            c for c in title if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        backup_filename = f"{timestamp}_{safe_title}.md"
        backup_path = os.path.join(config.BACKUP_FOLDER, backup_filename)

        # Create markdown content
        markdown_content = f"# {title}\n\n"
        markdown_content += f"**Original File:** {original_filename}\n"
        markdown_content += (
            f"**Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )
        markdown_content += "---\n\n"
        markdown_content += content

        # Save to file
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"[BACKUP] Backup saved: {backup_filename}")
        return backup_path
    except Exception as e:
        print(f"Warning: Failed to save backup: {e}")
        return None


def add_to_notion(title, content):
    """Add summarized content to Notion database."""
    if not title or not title.strip():
        print("Error: Title cannot be empty")
        return None

    if not content or not content.strip():
        print("Error: Content cannot be empty")
        return None

    if not config.NOTION_DATABASE_ID:
        print("Error: NOTION_DATABASE_ID not configured")
        return None

    print(f"Adding '{title}' to Notion...")
    try:
        meeting_date = datetime.now().strftime("%Y-%m-%d")

        # Split content into chunks to respect Notion's limit and to render markdown
        content_chunks = []
        for block in content.split("\n\n"):
            if not block.strip():
                continue

            # Notion API has a 2000 character limit per block
            for i in range(0, len(block), config.NOTION_MAX_CHUNK_SIZE):
                chunk = block[i : i + config.NOTION_MAX_CHUNK_SIZE]
                content_chunks.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": chunk}}]
                        },
                    }
                )

        response = api_clients.notion.pages.create(
            parent={"database_id": config.NOTION_DATABASE_ID},
            properties={
                "Title": {"title": [{"text": {"content": title}}]},
                "Meeting Date": {"date": {"start": meeting_date}},
            },
            children=content_chunks,
        )
        print("Successfully added to Notion.")
        return response
    except Exception as e:
        print(f"Error adding to Notion: {e}")
        return None
