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
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable

from botcore.config.constant import DATETIME_FORMATS
from botcore.config.settings import IF_DEBUG_MODE

# Logger default color if not specified
DEFAULT_LOG_COLOR = "white"

# External GUI logger callback
external_logger: Callable[[str], None] | None = None


# ----- Log Level Enum ----- #
class LogLevel(Enum):
    INIT  = ("init",  None)      # No color for init
    DEBUG = ("debug", "gray")
    INFO  = ("info",  "white")
    WARN  = ("warn",  "yellow")
    ERROR = ("error", "red")

    def __init__(self, label: str, color: str | None):
        self._label = label
        self._color = color

    @property
    def label(self) -> str:
        """Return uppercased label, e.g., INFO, ERROR"""
        return self._label.upper()

    @property
    def color(self) -> str | None:
        """Return associated display color"""
        return self._color


# ----- Dataclass for a Log Record ----- #
@dataclass
class LogRecord:
    message: str
    level: LogLevel
    timestamp: str = datetime.now().strftime(DATETIME_FORMATS.general)

    def to_text(self) -> str:
        """Format log record for console"""
        return f"{self.timestamp} [{self.level.label}] {self.message}"

    def to_json(self) -> str:
        """Format log record for GUI JSON logger"""
        return json.dumps({
            "text" : self.to_text(),
            "color": self.level.color or DEFAULT_LOG_COLOR,
            "tag"  : f"tag_{self.level.label}"
        })


# ----- Main logger API ----- #
def set_external_logger(callback_fn: Callable[[str], None]) -> None:
    """Assign GUI log callback for external logging"""
    global external_logger
    external_logger = callback_fn


def log(message: str, level: LogLevel = LogLevel.INFO) -> None:
    """Log to console and optionally to GUI if callback is set"""
    if level == LogLevel.DEBUG and not IF_DEBUG_MODE:
        return

    record = LogRecord(message=message, level=level)
    print(record.to_text())

    if external_logger:
        try:
            external_logger(record.to_json())
        except Exception as e:
            print(f"[LOGGER ERROR] Failed to send to external logger: {e}")


# ----- GUI Welcome Message ----- #
def log_welcome_message() -> None:
    """Send colored rainbow-style welcome message to GUI"""
    if not external_logger:
        return

    pastel_rainbow_colors = [
        "#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9",
        "#BAE1FF", "#D5BAFF", "#FFBAED"
    ]
    welcome = "Welcome to use Griffin Empire Attendance Bot!"
    author  = "Author: DragonTaki"

    rainbow_line = [{
        "text": char,
        "color": pastel_rainbow_colors[i % len(pastel_rainbow_colors)],
        "bold": True,
        "tag": f"rainbow_{i}"
    } for i, char in enumerate(welcome)]

    try:
        external_logger(json.dumps(rainbow_line))
        external_logger(json.dumps([{
            "text": "\n" + author + "\n",
            "color": "cyan",
            "italic": True,
            "tag": "author_tag"
        }]))
    except Exception as e:
        print(f"[WELCOME ERROR] Failed to send welcome message: {e}")
