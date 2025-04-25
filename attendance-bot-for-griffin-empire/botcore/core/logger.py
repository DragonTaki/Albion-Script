# ----- ----- ----- -----
# logger.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/25
# Version: v1.3
# ----- ----- ----- -----

import json
from datetime import datetime
from enum import Enum

from botcore.config.settings import IF_DEBUG_MODE

external_logger = None  # GUI logger callback

# Logger Time Formats
TIMESTAMP_FORMAT = "%d/%m/%Y %H:%M:%S"

# Logger Levels
class LogLevel(Enum):
    INIT  = ("init",  None)  # No color for init
    DEBUG = ("debug", "gray")
    INFO  = ("info",  "white")
    WARN  = ("warn",  "yellow")
    ERROR = ("error", "red")

    def __init__(self, label, color):
        self._label = label
        self._color = color

    @property
    def label(self) -> str:
        # Always return uppercase label like INIT, INFO, etc.
        return self._label.upper()

    @property
    def color(self) -> str | None:
        return self._color

# Default color mapping
LEVEL_COLOR_MAP = {
    "info" : "white",
    "warn" : "yellow",
    "error": "red"
}

def set_external_logger(callback_fn):
    global external_logger
    external_logger = callback_fn

# Main function to log messages
def log(message, level=LogLevel.INFO):
    if level == LogLevel.DEBUG and not IF_DEBUG_MODE:
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
