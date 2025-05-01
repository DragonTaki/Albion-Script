# ----- ----- ----- -----
# app_logger.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/05/01
# Version: v1.4
# ----- ----- ----- -----

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable

from botcore.config.constant import DATETIME_FORMATS
from botcore.config.settings_manager import get_settings
settings = get_settings()

# Logger default color if not specified
DEFAULT_LOG_COLOR = "white"

# External GUI logger callback
external_logger: Callable[[str], None] | None = None


# ----- Log Level Enum ----- #
class LogLevel(Enum):
    """
    Enum for different log levels, each associated with a label and color.
    """
    INIT  = ("init",  None)      # No color for init
    DEBUG = ("debug", "gray")
    INFO  = ("info",  "white")
    WARN  = ("warn",  "yellow")
    ERROR = ("error", "red")

    def __init__(self, label: str, color: str | None):
        """
        Initialize a LogLevel instance with a label and color.

        Args:
            label (str): The label for the log level (e.g., 'info', 'error').
            color (str | None): The associated color for the log level (e.g., 'white', 'red').
        """
        self._label = label
        self._color = color

    @property
    def label(self) -> str:
        """
        Return the uppercase label of the log level (e.g., INFO, ERROR).

        Returns:
            str: The log level label in uppercase.
        """
        return self._label.upper()

    @property
    def color(self) -> str | None:
        """
        Return the associated display color for the log level.

        Returns:
            str | None: The color for display, or None if no color is set.
        """
        return self._color


# ----- Dataclass for a Log Record ----- #
@dataclass
class LogRecord:
    """
    A log record representing a single log entry with message, level, and timestamp.
    """
    message: str
    level: LogLevel
    timestamp: str = field(default_factory=lambda: datetime.now().strftime(DATETIME_FORMATS.general))

    def to_text(self) -> str:
        """
        Convert the log record to a plain text format.

        Returns:
            str: A formatted string representation of the log record.
        """
        return f"{self.timestamp} [{self.level.label}] {self.message}"

    def to_json(self) -> str:
        """
        Convert the log record to a JSON format for GUI display.

        Returns:
            str: A JSON string representing the log record.
        """
        return json.dumps({
            "text" : self.to_text(),
            "color": self.level.color or DEFAULT_LOG_COLOR,
            "tag"  : f"tag_{self.level.label}"
        })


# ----- Main Functions ----- #
def set_external_logger(callback_fn: Callable[[str], None]) -> None:
    """
    Assign a callback function for logging to an external GUI.

    Args:
        callback_fn (Callable[[str], None]): A function that accepts a string (log message in JSON format) to display in the GUI.
    """
    global external_logger
    external_logger = callback_fn


def log(message: str, level: LogLevel = LogLevel.INFO) -> None:
    """
    Log a message to the console and optionally to an external GUI if the callback is set.

    Args:
        message (str): The message to log.
        level (LogLevel): The severity level of the log (default is INFO).
    """
    if level == LogLevel.DEBUG and not settings.enable_debug_mode:
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
    """
    Send a rainbow-colored welcome message to the external GUI.

    This includes a welcome message and the author's name.
    """
    if not external_logger:
        return

    pastel_rainbow_colors = [
        "#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9",
        "#BAE1FF", "#D5BAFF", "#FFBAED"
    ]
    print(f"[DEBUG] current_user in log_welcome_message: {settings.current_user}")
    greeting = f"Hello, {settings.current_user}!" if settings.current_user else "Hello!"
    welcome = "Welcome to use Griffin Empire Attendance Bot!"
    author  = "Author: DragonTaki"

    rainbow_line = [{
        "text": char,
        "color": pastel_rainbow_colors[i % len(pastel_rainbow_colors)],
        "bold": True,
        "tag": f"rainbow_{i}"
    } for i, char in enumerate(welcome)]

    try:
        external_logger(json.dumps([{
            "text": greeting + "\n",
            "color": "lightgreen",
            "bold": True,
            "tag": "greeting_tag"
        }]))
        external_logger(json.dumps(rainbow_line))
        external_logger(json.dumps([{
            "text": "\n" + author + "\n",
            "color": "cyan",
            "italic": True,
            "tag": "author_tag"
        }]))
    except Exception as e:
        print(f"[WELCOME ERROR] Failed to send welcome message: {e}")
