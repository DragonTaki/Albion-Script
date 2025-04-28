# ----- ----- ----- -----
# run.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/27
# Version: v1.2
# ----- ----- ----- -----

import atexit
import requests
import tkinter as tk
from datetime import datetime

from gui.auth_interface import show_auth_file_warning, show_auth_failed_warning
from gui.main_interface import AttendanceBotGUI
from gui.trial_notice_interface import show_trial_expired_warning, show_trial_notice
import botcore.config.settings
from botcore.config.static_settings import IF_TRIAL_VERSION, EXPIRE_DATE
from botcore.logging.log_file_manager import shutdown_runtime_log
from botcore.core.auth_manager import auth_manager

def _get_network_datetime() -> datetime | None:
    try:
        response = requests.get("https://www.google.com", timeout=5)
        date_str = response.headers["Date"]  # Format: 'Wed, 23 Apr 2025 07:12:17 GMT'
        return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S GMT")
    except Exception as e:
        print(f"[ERROR] Failed to get network time: {e}")
        return None

# Check expiration before running
def _is_expired() -> bool:
    if not IF_TRIAL_VERSION:
        return False
    try:
        if EXPIRE_DATE == "YYYY-MM-DD":  # Check for invalid default
            return True
        expire_date = datetime.strptime(EXPIRE_DATE, "%Y-%m-%d")
        now = _get_network_datetime()
        if not now:
            return True  # Fallback: block if can't verify time
        return now > expire_date
    except Exception:
        return True  # Fallback: block if invalid

def main() -> None:
    # Step 1. Run Authentication first
    auth_result = auth_manager()
    if auth_result == "undefined":
        show_auth_file_warning()
        return
    elif auth_result == "fail":
        show_auth_failed_warning()
        return

    # Step 2. Trial check
    if IF_TRIAL_VERSION:
        if _is_expired():
            print("❌ Trial expired. Please contact the developer.")
            show_trial_expired_warning()
            return
        else:
            show_trial_notice()

    # Step 3. Start GUI
    atexit.register(shutdown_runtime_log)

    root = tk.Tk()
    root.title("Attendance Bot for Griffin Empire - created by @DragonTaki")
    root.geometry("1280x720")
    app = AttendanceBotGUI(root)
    app.pack(fill="both", expand=True)
    root.mainloop()

if __name__ == "__main__":
    main()
