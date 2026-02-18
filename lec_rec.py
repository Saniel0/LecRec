import subprocess
import time
import signal
import json
import os
import threading
from datetime import datetime

SCHEDULE_FILE   = "schedule.json"
UPDATE_INTERVAL = 30 # seconds

# track of active recordings
active_recordings = set()

def print_title():
    print("""
 /$$                           /$$$$$$$                     
| $$                          | $$__  $$                    
| $$        /$$$$$$   /$$$$$$$| $$  \ $$  /$$$$$$   /$$$$$$$
| $$       /$$__  $$ /$$_____/| $$$$$$$/ /$$__  $$ /$$_____/
| $$      | $$$$$$$$| $$      | $$__  $$| $$$$$$$$| $$      
| $$      | $$_____/| $$      | $$  \ $$| $$_____/| $$      
| $$$$$$$$|  $$$$$$$|  $$$$$$$| $$  | $$|  $$$$$$$|  $$$$$$$
|________/ \_______/ \_______/|__/  |__/ \_______/ \_______/
    """)

def get_seconds_until(time_str):
    now = datetime.now()
    target = datetime.strptime(time_str, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day
    )
    return (target - now).total_seconds()

def record_lecture(lecture_conf):
    name = lecture_conf['name']
    url = lecture_conf['url']
    folder = lecture_conf['folder']
    
    # Create folder if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Generate filename with timestamp: "Folder/Name_YYYY-MM-DD.mp4"
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{name.replace(' ', '_')}_{date_str}.mp4"
    output_path = os.path.join(folder, filename)

    # Calculate duration
    duration = get_seconds_until(lecture_conf['end_time'])
    
    if duration <= 0:
        print(f"[{name}] Error: End time is in the past. Skipping.")
        return

    print(f"[{name}] Lecture started. Started recording to: {output_path}")
    
    # yt-dlp recording command
    command = [
        "yt-dlp",
        url,
        "-o", output_path,
        "-f", "bestvideo+bestaudio/best",
        "--quiet",
        "--no-warnings"
    ]

    # Start the yt-dlp subprocess
    process = subprocess.Popen(command)

    try:
        # Wait until the lecture ends
        time.sleep(duration)
        
        print(f"[{name}] Lecture ended! Saving file...")
        process.send_signal(signal.SIGINT)
        
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutError:
            process.kill()

    except Exception as e:
        print(f"[{name}] Error: {e}")
        if process.poll() is None:
            process.kill()
    finally:
        # Remove from active list so it can be recorded next week
        active_recordings.discard(name)

def check_schedule():
    print_title()
    print("[SYSTEM] Starting...")
    print("[SYSTEM] Waiting for lectures...")
    
    while True:
        try:
            # Reload JSON every loop - lets user change the config without restart
            with open(SCHEDULE_FILE, 'r') as f:
                schedule = json.load(f)

            now = datetime.now()
            current_day = now.strftime("%A")
            
            # Check if it is time to record any lecture
            for lecture in schedule:
                name = lecture['name']
                
                # 1. Check Day
                if lecture['day'] != current_day:
                    continue

                # 2. Check Time
                start_seconds = get_seconds_until(lecture['start_time'])
                end_seconds = get_seconds_until(lecture['end_time'])
                is_lecture_time = start_seconds <= 0 and end_seconds > 0

                if is_lecture_time:
                    if name not in active_recordings:
                        # Add to active set
                        active_recordings.add(name)
                        
                        # Start recording in a separate thread
                        t = threading.Thread(target=record_lecture, args=(lecture,))
                        t.daemon = True # Thread dies if main program dies
                        t.start()
            
            # Check once every minute
            time.sleep(UPDATE_INTERVAL)

        except FileNotFoundError:
            print(f"Error: {SCHEDULE_FILE} not found!")
            time.sleep(UPDATE_INTERVAL)
        except json.JSONDecodeError:
            print(f"Error: {SCHEDULE_FILE} has invalid JSON syntax!")
            time.sleep(UPDATE_INTERVAL)
        except KeyboardInterrupt:
            print("\nStopping scheduler...")
            break

if __name__ == "__main__":
    check_schedule()
