# ----- ----- ----- -----
# logger.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/23
# Version: v1.2
# ----- ----- ----- -----

from datetime import datetime
import json

from .config import LogLevel, DEBUG_MODE, TIMESTAMP_FORMAT

external_logger = None  # GUI logger callback

# Default color mapping
LEVEL_COLOR_MAP = {
    "info": "white",
    "warn": "yellow",
    "error": "red"
}

def set_external_logger(callback_fn):
    global external_logger
    external_logger = callback_fn

# Main function to log messages
def log(message, level=LogLevel.INFO):
    if level == LogLevel.DEBUG and not DEBUG_MODE:
        return

    level_str = level.label
    level_color = level.color or "white"

    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
    full_text = f"{timestamp} [{level_str}] {message}"
    print(full_text)  # Console

    if external_logger:
        log_json = json.dumps({
            "text": full_text,
            "color": level_color,
            "tag": f"tag_{level_str}"
        })
        external_logger(log_json)

def log_welcome_message():
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
    author = "Author: DragonTaki"
    rainbow_line = []
    for i, char in enumerate(welcome):
        rainbow_line.append({
            "text": char,
            "color": pastel_rainbow_colors[i % len(pastel_rainbow_colors)],
            "bold": True,
            "tag": f"rainbow_{i}"
        })

    if external_logger:
        external_logger(json.dumps(rainbow_line))
        # Add the author info with special style
        external_logger(json.dumps([{
            "text": "\n" + author + "\n",
            "color": "cyan",
            "italic": True,
            "tag": "author_tag"
        }]))
