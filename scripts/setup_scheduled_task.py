#!/usr/bin/env python3
"""
Voice Notes Scheduler - Configure Windows Task Scheduler for automated processing.
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv


def load_schedule_config():
    """Load schedule configuration from .env file."""
    load_dotenv()

    config = {
        "profile": os.getenv("SCHEDULE_PROFILE", "normal_frequency"),
        "interval": int(os.getenv("SCHEDULE_INTERVAL", "15")),
        "start_time": os.getenv("SCHEDULE_START_TIME", "08:00"),
        "end_time": os.getenv("SCHEDULE_END_TIME", "17:00"),
        "days": os.getenv("SCHEDULE_DAYS", "MON,TUE,WED,THU,FRI").split(","),
    }

    return config


def calculate_duration(start_time, end_time):
    """Calculate duration between start and end times."""
    start = datetime.strptime(start_time, "%H:%M")
    end = datetime.strptime(end_time, "%H:%M")

    if end < start:  # Next day
        end += timedelta(days=1)

    duration = end - start
    hours = int(duration.total_seconds() // 3600)
    minutes = int((duration.total_seconds() % 3600) // 60)

    return f"PT{hours}H{minutes}M"


def setup_scheduled_task():
    """Set up or update the Windows scheduled task."""
    config = load_schedule_config()

    print(f"🔧 Setting up scheduled task with profile: {config['profile']}")
    print(
        f"📅 Schedule: Every {config['interval']} minutes from {config['start_time']} to {config['end_time']}"
    )
    print(f"📆 Days: {', '.join(config['days'])}")

    if config["interval"] == 0:
        print("⚠️  Manual mode selected - removing scheduled task")
        try:
            subprocess.run(
                ["schtasks", "/delete", "/tn", "ProcessVoiceNotes", "/f"],
                check=False,
                capture_output=True,
            )
            print("✅ Scheduled task removed")
        except Exception as e:
            print(f"ℹ️  No existing task to remove: {e}")
        return

    # Get script path - use VBS for hidden execution
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(script_dir, "process_voice_notes_hidden.vbs")

    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return

    try:
        # Remove existing task if it exists
        subprocess.run(
            ["schtasks", "/delete", "/tn", "ProcessVoiceNotes", "/f"],
            check=False,
            capture_output=True,
        )

        # Convert days to Windows format (MON,TUE,WED,THU,FRI)
        days_str = ",".join(config["days"])

        # Create new task using direct schtasks command
        cmd = [
            "schtasks",
            "/create",
            "/tn",
            "ProcessVoiceNotes",
            "/tr",
            script_path,
            "/sc",
            "weekly",
            "/d",
            days_str,
            "/st",
            config["start_time"],
            "/ri",
            str(config["interval"]),
            "/du",
            calculate_duration(config["start_time"], config["end_time"]),
            "/f",  # Force create (overwrite if exists)
        ]

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        print("✅ Scheduled task created successfully!")
        print("🔍 You can view it in Task Scheduler under 'ProcessVoiceNotes'")
        print(f"📋 Task details:")
        print(f"   - Runs: {days_str}")
        print(f"   - Start: {config['start_time']}")
        print(f"   - Repeat: Every {config['interval']} minutes")
        print(
            f"   - Duration: {calculate_duration(config['start_time'], config['end_time'])}"
        )

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create scheduled task: {e}")
        print(f"Command: {' '.join(cmd) if 'cmd' in locals() else 'N/A'}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        print("\n💡 Manual alternative:")
        print("1. Open Task Scheduler (taskschd.msc)")
        print("2. Create Basic Task")
        print(f"3. Set to run: {script_path}")
        print(f"4. Schedule: Weekly on {days_str} at {config['start_time']}")
        print(
            f"5. Repeat every {config['interval']} minutes for {calculate_duration(config['start_time'], config['end_time'])}"
        )
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def main():
    """Main function."""
    print("🗓️  Voice Notes Scheduler Setup")
    print("=" * 40)

    setup_scheduled_task()

    print("\n💡 To change your schedule:")
    print("1. Edit your .env file")
    print("2. Comment/uncomment the desired profile")
    print("3. Run this script again: uv run scripts/setup_scheduled_task.py")


if __name__ == "__main__":
    main()