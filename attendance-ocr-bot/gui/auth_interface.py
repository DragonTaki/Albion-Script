# ----- ----- ----- -----
# auth_interface.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/27
# Update Date: 2025/04/27
# Version: v1.0
# ----- ----- ----- -----

import tkinter as tk
from tkinter import messagebox


def show_auth_file_warning() -> None:
    """
    Show a popup window warning the user to fill in 'auth.json' file correctly.
    """
    root = tk.Tk()
    root.withdraw()
    messagebox.showwarning(
        title="Authentication Setup Required",
        message=(
            "⚠️ Authentication file 'auth.json' is missing or invalid.\n\n"
            "A template has been created. Please open 'auth.json', "
            "fill in your username, key, and token, then restart the application."
        )
    )
    root.destroy()


def show_auth_failed_warning() -> None:
    """
    Show a popup window indicating that authentication failed.
    """
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        title="Authentication Failed",
        message=(
            "❌ Authentication failed.\n\n"
            "Please check your username, key, and token in 'auth.json'."
        )
    )
    root.destroy()
