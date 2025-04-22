# ----- ----- ----- -----
# run.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/22
# Version: v1.1
# ----- ----- ----- -----

from datetime import datetime
from gui.interface import AttendanceBotGUI
from gui.trial_warning import show_trial_expired_warning
from botcore.config import TRIAL_VERSION, EXPIRE_DATE

# Check expiration before running
def is_expired():
    if not TRIAL_VERSION:
        return False
    try:
        if EXPIRE_DATE == "YYYY-MM-DD":  # Check for invalid default
            return True
        expire_date = datetime.strptime(EXPIRE_DATE, "%Y-%m-%d")
        return datetime.today() > expire_date
    except Exception:
        return True  # Fallback: block if invalid

def main():
    if is_expired():
        print("❌ Trial expired. Please contact the developer.")
        show_trial_expired_warning()
        return
    app = AttendanceBotGUI()
    app.mainloop()

if __name__ == "__main__":
    main()