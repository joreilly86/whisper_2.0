"""
Functions for interacting with Notion.
"""

import os
import re
from datetime import datetime

from . import api_clients, config


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


def parse_markdown_to_notion_blocks(content):
    """Parse markdown content and convert to Notion blocks."""
    blocks = []
    lines = content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Headings
        if line.startswith("#"):
            heading_level = min(
                len(line) - len(line.lstrip("#")), 3
            )  # Notion supports h1, h2, h3
            heading_text = line.lstrip("#").strip()

            if heading_level == 1:
                block_type = "heading_1"
            elif heading_level == 2:
                block_type = "heading_2"
            else:
                block_type = "heading_3"

            blocks.append(
                {
                    "object": "block",
                    "type": block_type,
                    block_type: {
                        "rich_text": [
                            {"type": "text", "text": {"content": heading_text}}
                        ]
                    },
                }
            )

        # Bullet points
        elif line.startswith(("- ", "* ", "+ ")):
            # Collect all consecutive bullet points
            bullet_items = []
            while i < len(lines) and lines[i].strip().startswith(("- ", "* ", "+ ")):
                bullet_text = lines[i].strip()[2:].strip()  # Remove bullet marker
                bullet_items.append(bullet_text)
                i += 1
            i -= 1  # Back up one since we'll increment at the end of the loop

            # Create bulleted list items
            for item in bullet_items:
                blocks.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {"rich_text": parse_rich_text(item)},
                    }
                )

        # Numbered lists
        elif re.match(r"^\d+\.", line):
            # Collect all consecutive numbered items
            numbered_items = []
            while i < len(lines) and re.match(r"^\d+\.", lines[i].strip()):
                numbered_text = re.sub(r"^\d+\.\s*", "", lines[i].strip())
                numbered_items.append(numbered_text)
                i += 1
            i -= 1  # Back up one since we'll increment at the end of the loop

            # Create numbered list items
            for item in numbered_items:
                blocks.append(
                    {
                        "object": "block",
                        "type": "numbered_list_item",
                        "numbered_list_item": {"rich_text": parse_rich_text(item)},
                    }
                )

        # Code blocks
        elif line.startswith("```"):
            code_content = []
            i += 1  # Skip the opening ```
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_content.append(lines[i])
                i += 1

            blocks.append(
                {
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "\n".join(code_content)},
                            }
                        ],
                        "language": "plain text",
                    },
                }
            )

        # Block quotes
        elif line.startswith(">"):
            quote_content = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_text = lines[i].strip()[1:].strip()  # Remove > marker
                if quote_text:  # Only add non-empty lines
                    quote_content.append(quote_text)
                i += 1
            i -= 1  # Back up one since we'll increment at the end of the loop

            if quote_content:
                blocks.append(
                    {
                        "object": "block",
                        "type": "quote",
                        "quote": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": " ".join(quote_content)},
                                }
                            ]
                        },
                    }
                )

        # Regular paragraph
        else:
            # Collect multi-line paragraphs
            paragraph_lines = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not is_special_line(lines[i]):
                paragraph_lines.append(lines[i].strip())
                i += 1
            i -= 1  # Back up one since we'll increment at the end of the loop

            paragraph_text = " ".join(paragraph_lines)

            # Split long paragraphs to respect Notion's limit
            if len(paragraph_text) > config.NOTION_MAX_CHUNK_SIZE:
                chunks = [
                    paragraph_text[j : j + config.NOTION_MAX_CHUNK_SIZE]
                    for j in range(0, len(paragraph_text), config.NOTION_MAX_CHUNK_SIZE)
                ]
                for chunk in chunks:
                    blocks.append(
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {"rich_text": parse_rich_text(chunk)},
                        }
                    )
            else:
                blocks.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {"rich_text": parse_rich_text(paragraph_text)},
                    }
                )

        i += 1

    return blocks


def is_special_line(line):
    """Check if a line is a special markdown element."""
    stripped = line.strip()
    return (
        stripped.startswith("#")
        or stripped.startswith(("- ", "* ", "+ "))
        or re.match(r"^\d+\.", stripped)
        or stripped.startswith("```")
        or stripped.startswith(">")
    )


def parse_rich_text(text):
    """Parse text with basic markdown formatting for Notion rich text."""
    if not text:
        return [{"type": "text", "text": {"content": ""}}]

    # Simple implementation - can be enhanced for more complex formatting
    rich_text = []

    # Handle bold text (**text** or __text__)
    parts = re.split(r"(\*\*.*?\*\*|__.*?__)", text)

    for part in parts:
        if not part:
            continue

        if part.startswith("**") and part.endswith("**"):
            # Bold text
            bold_text = part[2:-2]
            rich_text.append(
                {
                    "type": "text",
                    "text": {"content": bold_text},
                    "annotations": {"bold": True},
                }
            )
        elif part.startswith("__") and part.endswith("__"):
            # Bold text
            bold_text = part[2:-2]
            rich_text.append(
                {
                    "type": "text",
                    "text": {"content": bold_text},
                    "annotations": {"bold": True},
                }
            )
        else:
            # Handle italic text (*text* or _text_) within remaining text
            italic_parts = re.split(r"(\*.*?\*|_.*?_)", part)
            for italic_part in italic_parts:
                if not italic_part:
                    continue
                if (
                    italic_part.startswith("*")
                    and italic_part.endswith("*")
                    and not italic_part.startswith("**")
                ):
                    # Italic text
                    italic_text = italic_part[1:-1]
                    rich_text.append(
                        {
                            "type": "text",
                            "text": {"content": italic_text},
                            "annotations": {"italic": True},
                        }
                    )
                elif (
                    italic_part.startswith("_")
                    and italic_part.endswith("_")
                    and not italic_part.startswith("__")
                ):
                    # Italic text
                    italic_text = italic_part[1:-1]
                    rich_text.append(
                        {
                            "type": "text",
                            "text": {"content": italic_text},
                            "annotations": {"italic": True},
                        }
                    )
                else:
                    # Regular text
                    if italic_part:
                        rich_text.append(
                            {"type": "text", "text": {"content": italic_part}}
                        )

    # If no rich text was created, return plain text
    if not rich_text:
        rich_text = [{"type": "text", "text": {"content": text}}]

    return rich_text


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

        # Parse content and create proper Notion blocks with markdown support
        content_chunks = parse_markdown_to_notion_blocks(content)

        response = api_clients.notion.pages.create(
            parent={"database_id": config.NOTION_DATABASE_ID},
            properties={
                "Title": {"title": [{"text": {"content": title}}]},
                "Date": {"date": {"start": meeting_date}},
            },
            children=content_chunks,
        )
        print("Successfully added to Notion.")
        return response
    except Exception as e:
        print(f"Error adding to Notion: {e}")
        return None
