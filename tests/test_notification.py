#!/usr/bin/env python3
"""Simple test script to verify notification system works."""

from plyer import notification
import time


def test_notifications():
    """Test both success and error notifications."""
    print("Testing notification system...")

    # Test success notification
    print("Showing success notification...")
    notification.notify(
        title="✅ Voice Note Processed",
        message="Successfully transcribed and added to Notion:\ntest_recording.mp3",
        timeout=10,
        app_name="Voice Note Monitor",
    )

    time.sleep(3)

    # Test error notification
    print("Showing error notification...")
    notification.notify(
        title="❌ Voice Note Processing Failed",
        message="Failed to process: test_recording.mp3\nError: API key not found",
        timeout=10,
        app_name="Voice Note Monitor",
    )

    print("Notification test complete. Check your Windows notifications!")


if __name__ == "__main__":
    test_notifications()
