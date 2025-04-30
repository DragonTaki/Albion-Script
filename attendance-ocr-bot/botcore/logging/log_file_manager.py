# ----- ----- ----- -----
# log_file_manager.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/23
# Update Date: 2025/04/26
# Version: v1.4
# ----- ----- ----- -----

import os
import platform
import msvcrt
from datetime import datetime

from botcore.config.constant import EXTENSIONS, DATETIME_FORMATS, TEXTFILE_ENCODING
from botcore.config.settings_manager import settings
from .app_logger import LogLevel, log
from botcore.core.utils import ensure_folder_exists

# Ensure log folder exists
ensure_folder_exists(settings.folder_paths.log)

# Log prefixes for different types of logs
LOG_PREFIXES = {
    "runtime": "runtime_log_",
    "user_saved": "user_saved_log_"
}


def get_log_file_path(log_type: str) -> str:
    """
    Generate the file path for the log based on the log type.

    Args:
        log_type (str): The type of log ("runtime" or "user_saved").

    Returns:
        str: The full path to the log file.

    Raises:
        ValueError: If an unsupported log type is provided.
    """
    if log_type not in LOG_PREFIXES:
        raise ValueError(f"Unsupported log type: {log_type}")

    timestamp = datetime.now().strftime(DATETIME_FORMATS.log)
    filename = f"{LOG_PREFIXES[log_type]}{timestamp}{EXTENSIONS.log}"
    return os.path.join(settings.folder_paths.log, filename)


# Persistent log paths
RUNTIME_LOG_PATH = get_log_file_path("runtime")  # One persistent runtime log file

# Runtime log file handle (shared during runtime)
try:
    _log_file = open(RUNTIME_LOG_PATH, "a", encoding=TEXTFILE_ENCODING)
except Exception as e:
    print(f"[Logger] Failed to initialize runtime log: {e}")
    _log_file = None


def initialize_runtime_log() -> None:
    """
    Initializes the runtime log by logging the start of the logger.
    This should be called once when the module is imported.
    """
    append_runtime_log("Logger started at " + datetime.now().strftime(DATETIME_FORMATS.general))
    append_runtime_log("----- ----- ----- -----")


def shutdown_runtime_log() -> None:
    """
    Shuts down the runtime logger, closing the log file.
    Unlocks the file on Windows if necessary.
    """
    append_runtime_log("Logger shutting down.")
    if platform.system() == "Windows":
        unlock_log_file_windows()
    if _log_file:
        try:
            _log_file.close()
        except Exception as e:
            print(f"[Logger] Failed to close log file: {e}")


def log_ini(message: str) -> None:
    """
    Logs initial messages both to the console and to the persistent log file.

    Args:
        message (str): The message to log at initialization.
    """
    timestamp = datetime.now().strftime(DATETIME_FORMATS.general)
    full_text = f"{timestamp} [{LogLevel.INIT.label}] {message}"
    print(full_text)
    append_runtime_log(full_text)


def append_runtime_log(message: str) -> None:
    """
    Appends a message to the runtime log file.

    Args:
        message (str): The message to be appended to the log.
    """
    try:
        with open(RUNTIME_LOG_PATH, "a", encoding=TEXTFILE_ENCODING) as log_file:
            log_file.write(message.strip() + "\n")
    except Exception as e:
        print(f"[Logger] Failed to write log: {e}")


def save_log(log_lines: list[str]) -> str:
    """
    Saves a list of selected log lines into a new user-saved log file.

    Args:
        log_lines (list[str]): List of log lines to save.

    Returns:
        str: The file path of the saved log, or empty string if failed.
    """
    try:
        save_path = get_log_file_path("user_saved")
        with open(save_path, "w", encoding=TEXTFILE_ENCODING) as f:
            f.writelines(line + "\n" for line in log_lines)
        return save_path
    except Exception as e:
        log(f"Failed to save log: {e}", LogLevel.ERROR)
        return ""


def save_all_logs(full_log_text: str) -> str:
    """
    Saves all logs from the provided text into a user-saved log file.

    Args:
        full_log_text (str): The full log text to save.

    Returns:
        str: The file path of the saved log, or empty string if failed.
    """
    lines = full_log_text.splitlines()
    return save_log(lines)


def clear_log(tk_logger) -> None:
    """
    Clears the log display in the UI (Tkinter widget).

    Args:
        tk_logger: The Tkinter Text widget to clear.
    """
    try:
        tk_logger.config(state="normal")
        tk_logger.delete("1.0", "end")
        tk_logger.config(state="disabled")
        log("Log cleared.", LogLevel.INFO)
    except Exception as e:
        log(f"Failed to clear log: {e}", LogLevel.WARN)


def lock_log_file_windows() -> None:
    """
    Locks the runtime log file on Windows to prevent concurrent access.
    This function ensures that no other process can write to the log file while it is in use.
    """
    try:
        with open(RUNTIME_LOG_PATH, "a", encoding=TEXTFILE_ENCODING) as log_file:
            msvcrt.locking(log_file.fileno(), msvcrt.LK_NBLCK, 1)  # lock first byte
    except OSError:
        log("Failed to lock runtime log file.", LogLevel.WARN)


def unlock_log_file_windows() -> None:
    """
    Unlocks the runtime log file on Windows to allow other processes to access it.
    """
    try:
        with open(RUNTIME_LOG_PATH, "a", encoding=TEXTFILE_ENCODING) as log_file:
            msvcrt.locking(log_file.fileno(), msvcrt.LK_UNLCK, 1)
    except Exception:
        pass


# Initialize the runtime log at the start
initialize_runtime_log()
