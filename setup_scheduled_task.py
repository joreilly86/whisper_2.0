#!/usr/bin/env python3
"""
Automatically configure Windows Task Scheduler based on .env settings.
Run this script whenever you change your schedule profile.
"""

import os
import sys
import subprocess
from dotenv import load_dotenv
from datetime import datetime, timedelta

def load_schedule_config():
    """Load schedule configuration from .env file."""
    load_dotenv()
    
    config = {
        'profile': os.getenv('SCHEDULE_PROFILE', 'normal_frequency'),
        'interval': int(os.getenv('SCHEDULE_INTERVAL', '15')),
        'start_time': os.getenv('SCHEDULE_START_TIME', '08:00'),
        'end_time': os.getenv('SCHEDULE_END_TIME', '17:00'),
        'days': os.getenv('SCHEDULE_DAYS', 'MON,TUE,WED,THU,FRI').split(',')
    }
    
    return config

def calculate_duration(start_time, end_time):
    """Calculate duration between start and end times."""
    start = datetime.strptime(start_time, '%H:%M')
    end = datetime.strptime(end_time, '%H:%M')
    
    if end < start:  # Next day
        end += timedelta(days=1)
    
    duration = end - start
    hours = int(duration.total_seconds() // 3600)
    minutes = int((duration.total_seconds() % 3600) // 60)
    
    return f"PT{hours}H{minutes}M"

def create_task_xml(config, script_path):
    """Generate Windows Task Scheduler XML."""
    duration = calculate_duration(config['start_time'], config['end_time'])
    
    # Convert day names to numbers (Windows Task Scheduler format)
    day_map = {
        'MON': '2', 'TUE': '3', 'WED': '4', 'THU': '5', 'FRI': '6', 'SAT': '7', 'SUN': '1'
    }
    days_of_week = ','.join([day_map[day] for day in config['days']])
    
    xml_content = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>{datetime.now().isoformat()}</Date>
    <Author>Voice Note Monitor</Author>
    <Description>Process voice notes automatically - Profile: {config['profile']}</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <Repetition>
        <Interval>PT{config['interval']}M</Interval>
        <Duration>{duration}</Duration>
      </Repetition>
      <StartBoundary>{datetime.now().strftime('%Y-%m-%d')}T{config['start_time']}:00</StartBoundary>
      <ExecutionTimeLimit>PT10M</ExecutionTimeLimit>
      <Enabled>true</Enabled>
      <ScheduleByWeek>
        <DaysOfWeek>{days_of_week}</DaysOfWeek>
        <WeeksInterval>1</WeeksInterval>
      </ScheduleByWeek>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>true</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT10M</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>"{script_path}"</Command>
      <WorkingDirectory>{os.path.dirname(script_path)}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''
    
    return xml_content

def setup_scheduled_task():
    """Set up or update the Windows scheduled task."""
    config = load_schedule_config()
    
    print(f"🔧 Setting up scheduled task with profile: {config['profile']}")
    print(f"📅 Schedule: Every {config['interval']} minutes from {config['start_time']} to {config['end_time']}")
    print(f"📆 Days: {', '.join(config['days'])}")
    
    if config['interval'] == 0:
        print("⚠️  Manual mode selected - removing scheduled task")
        try:
            subprocess.run(['schtasks', '/delete', '/tn', 'ProcessVoiceNotes', '/f'], 
                         check=False, capture_output=True)
            print("✅ Scheduled task removed")
        except Exception as e:
            print(f"ℹ️  No existing task to remove: {e}")
        return
    
    # Get script path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, 'process_new_voice_notes.bat')
    
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return
    
    # Create XML file
    xml_content = create_task_xml(config, script_path)
    xml_file = os.path.join(script_dir, 'voice_notes_task.xml')
    
    with open(xml_file, 'w', encoding='utf-16') as f:
        f.write(xml_content)
    
    try:
        # Remove existing task if it exists
        subprocess.run(['schtasks', '/delete', '/tn', 'ProcessVoiceNotes', '/f'], 
                     check=False, capture_output=True)
        
        # Create new task
        result = subprocess.run([
            'schtasks', '/create', '/tn', 'ProcessVoiceNotes', 
            '/xml', xml_file
        ], check=True, capture_output=True, text=True)
        
        print("✅ Scheduled task created successfully!")
        print("🔍 You can view it in Task Scheduler under 'ProcessVoiceNotes'")
        
        # Clean up XML file
        os.remove(xml_file)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create scheduled task: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
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
    print("3. Run this script again: uv run setup_scheduled_task.py")

if __name__ == "__main__":
    main()