# ----- ----- ----- -----
# logger.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/18
# Version: v1.1
# ----- ----- ----- -----

from datetime import datetime
import json

external_logger = None  # GUI logger callback

# 🔴 Default color mapping
LEVEL_COLOR_MAP = {
    "info": "white",
    "warn": "yellow",
    "error": "red"
}

def set_external_logger(callback_fn):
    global external_logger
    external_logger = callback_fn

def log(message, level=""):
    level_str = "info"
    if level == "w":
        level_str = "warn"
    elif level == "e":
        level_str = "error"

    timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    prefix = level_str.capitalize()
    full_text = f"{timestamp} [{prefix}] {message}"
    print(full_text)  # Console

    if external_logger:
        log_json = json.dumps({
            "text": full_text,
            "color": LEVEL_COLOR_MAP.get(level_str, "white"),
            "tag": f"tag_{level_str}"
        })
        external_logger(log_json)

def log_welcome_message():
    # 🔴 Define pastel rainbow colors
    pastel_rainbow_colors = [
        "#FFB3BA",  # soft red
        "#FFDFBA",  # soft orange
        "#FFFFBA",  # soft yellow
        "#BAFFC9",  # soft green
        "#BAE1FF",  # soft blue
        "#D5BAFF",  # soft indigo
        "#FFBAED",  # soft violet
    ]

    welcome = "Welcome to use Griffin Empire Attendance Bot!"
    author = "Author: DragonTaki - github.com/DragonTaki"

    # 🔴 Combine all characters into one list with different styles
    rainbow_line = []
    for i, char in enumerate(welcome):
        rainbow_line.append({
            "text": char,
            "color": pastel_rainbow_colors[i % len(pastel_rainbow_colors)],
            "bold": True,
            "tag": f"rainbow_{i}"
        })

    # 🔴 Send the entire rainbow message and the author info in one call
    if external_logger:
        external_logger(json.dumps(rainbow_line))  # Send as a list of styled chars
        # Add the author info with special style
        external_logger(json.dumps([{
            "text": "\n" + author + "\n",
            "color": "cyan",
            "italic": True,
            "tag": "author_tag"
        }]))
