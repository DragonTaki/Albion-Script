# ----- ----- ----- -----
# run.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/22
# Version: v1.1
# ----- ----- ----- -----

import requests
from datetime import datetime

from gui.interface import AttendanceBotGUI
from gui.trial_interface import show_trial_expired_warning, show_trial_notice
from botcore.config import TRIAL_VERSION, EXPIRE_DATE

def get_network_datetime() -> datetime | None:
    try:
        response = requests.get("https://www.google.com", timeout=5)
        date_str = response.headers["Date"]  # Format: 'Wed, 23 Apr 2025 07:12:17 GMT'
        return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S GMT")
    except Exception as e:
        print(f"[ERROR] Failed to get network time: {e}")
        return None
    
# Check expiration before running
def is_expired():
    if not TRIAL_VERSION:
        return False
    try:
        if EXPIRE_DATE == "YYYY-MM-DD":  # Check for invalid default
            return True
        expire_date = datetime.strptime(EXPIRE_DATE, "%Y-%m-%d")
        now = get_network_datetime()
        if not now:
            return True  # Fallback: block if can't verify time
        return now > expire_date
    except Exception:
        return True  # Fallback: block if invalid

def main():
    if TRIAL_VERSION:
        if is_expired():
            print("❌ Trial expired. Please contact the developer.")
            show_trial_expired_warning()
            return
        else:
            show_trial_notice()
    app = AttendanceBotGUI()
    app.mainloop()

if __name__ == "__main__":
    main()