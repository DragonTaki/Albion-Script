# ----- ----- ----- -----
# log.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/23
# Update Date: 2025/04/23
# Version: v1.0
# ----- ----- ----- -----

import os
from datetime import datetime

from .config import LogLevel, LOG_EXTENSION, LOG_FOLDER, LOG_TIMESTAMP_FORMAT, LOG_RUNTIME_PREFIX, LOG_USERSAVED_PREFIX, TIMESTAMP_FORMAT
from .logger import log
from .utils import ensure_folder_exists

# Ensure log folder exists
ensure_folder_exists(LOG_FOLDER)

# Persistent runtime logger file
RUNTIME_LOG_PATH = os.path.join(
    LOG_FOLDER,
    datetime.now().strftime(LOG_RUNTIME_PREFIX + LOG_TIMESTAMP_FORMAT + LOG_EXTENSION)
)

# Write to persistent log
def append_runtime_log(message: str):
    with open(RUNTIME_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(message.strip() + "\n")

# Run this once when module is imported
def initialize_runtime_log():
    log_ini(f"Logger started at {datetime.now()}")
    append_runtime_log("----- ----- ----- -----")

# Main function to log initial messages
def log_ini(message):
    """Log a message with [Init] tag to console only"""
    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
    full_text = f"{timestamp} [{LogLevel.INIT.label}] {message}"
    print(full_text)
    append_runtime_log(full_text)

# Append runtime log
def append_runtime_log(message: str):
    with open(RUNTIME_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(message.strip() + "\n")

# Save selected logs
def save_log(log_lines: list[str]):
    timestamp = datetime.now().strftime(LOG_TIMESTAMP_FORMAT)
    filename = f"{LOG_USERSAVED_PREFIX}{timestamp}{LOG_EXTENSION}"
    save_path = os.path.join(LOG_FOLDER, filename)
    
    # Open file and write logs
    with open(save_path, "w", encoding="utf-8") as f:
        f.writelines(line + "\n" for line in log_lines)
    
    return save_path

# Save all logs
def save_all_logs(full_log_text: str):
    lines = full_log_text.splitlines()
    return save_log(lines)

# Clear log content (UI should clear Tk.Text)
def clear_log(tk_logger):
    tk_logger.config(state="normal")
    tk_logger.delete("1.0", "end")
    tk_logger.config(state="disabled")
    log("Log cleared.", LogLevel.INFO)

initialize_runtime_log()