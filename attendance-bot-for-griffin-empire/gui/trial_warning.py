# ----- ----- ----- -----
# trial_warning.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/22
# Update Date: 2025/04/22
# Version: v1.0
# ----- ----- ----- -----

import tkinter as tk
import sys
from tkinter import messagebox

# Show trial expired popup
def show_trial_expired_warning():
    """Show a blocking popup to inform the user the trial has expired"""
    root = tk.Tk()
    root.withdraw() # Hide main window

    messagebox.showerror(
        title="Trial Expired",
        message="❌ Trial expired. Please contact the developer."
    )

    root.destroy()
    sys.exit(1)