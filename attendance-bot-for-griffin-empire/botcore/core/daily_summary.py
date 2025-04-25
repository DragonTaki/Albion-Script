# ----- ----- ----- -----
# daily_summary.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/23
# Update Date: 2025/04/25
# Version: v1.1
# ----- ----- ----- -----

import json
import os
from datetime import datetime, timedelta
from types import SimpleNamespace
from collections import Counter

from botcore.config.constant import CONSTANTS, INTERVALS, DAYS_LOOKBACK, TEXTFILE_ENCODING
from botcore.config.settings import EXTRA_ATTENDANCE_FOLDER, IF_FORCE_NEW_DAILY_SUMMARY
EXTENSIONS = CONSTANTS.EXTENSIONS
DATETIME_FORMATS = CONSTANTS.DATETIME_FORMATS
from .logger import LogLevel, log
from .process_textfile import parse_txt_file
from .process_screenshot import parse_screenshot_file, get_valid_player_list, create_word_list_file
from .utils import ensure_folder_exists, get_file_checksum, get_relative_path_to_target, is_valid_folder_name

# Constants for Daily Summary
FILENAME_TEMPLATE = "{prefix}{name}{ext}"

DAILY_SUMMARY = SimpleNamespace(
    TEXTFILE = SimpleNamespace(
        META    = FILENAME_TEMPLATE.format(prefix="text_", name="meta",    ext=".meta"),
        SUMMARY = FILENAME_TEMPLATE.format(prefix="text_", name="summary", ext=".json"),
    ),
    SCREENSHOT = SimpleNamespace(
        META    = FILENAME_TEMPLATE.format(prefix="screenshot_", name="meta",    ext=".meta"),
        SUMMARY = FILENAME_TEMPLATE.format(prefix="screenshot_", name="summary", ext=".json"),
    )
)

def save_daily_summary(summary_type: SimpleNamespace, folder_name: str, attendance_list: list[dict], meta: dict) -> list[dict]:
    """
    Save formatted daily attendance and meta data into correct summary files.
    :param summary_type: DAILY_SUMMARY.TEXTFILE or DAILY_SUMMARY.SCREENSHOT
    :param folder_name: Name of the folder in format "%d-%m-%Y"
    :param attendance_list: List of dicts in format [{"name": "Player1", "attendance": 1}, ...]
    :param meta: Metadata (e.g., checksums or OCR source)
    """
    folder_path = os.path.join(EXTRA_ATTENDANCE_FOLDER, folder_name)
    summary_path = os.path.join(folder_path, summary_type.SUMMARY)
    meta_path = os.path.join(folder_path, summary_type.META)

    try:
        ensure_folder_exists(folder_path)

        with open(summary_path, "w", encoding=TEXTFILE_ENCODING) as f:
            json.dump(attendance_list, f, indent=2, ensure_ascii=False)
        with open(meta_path, "w", encoding=TEXTFILE_ENCODING) as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        log(f"Saved summary and meta to \"{folder_name}\".")
    except Exception as e:
        log(f"Failed to save summary/meta in \"{folder_name}\": {e}.", level="error")

    return attendance_list

def collect_all_daily_attendance(summary_type: SimpleNamespace):
    result_by_day = {}
    if summary_type == DAILY_SUMMARY.SCREENSHOT:
        player_list = get_valid_player_list()
        WORDLIST_TEMP_FILE = create_word_list_file(player_list)
    elif summary_type not in vars(DAILY_SUMMARY).values():
        raise ValueError(f"Unsupported summary type: \"{summary_type}\"")

    for folder_name in os.listdir(EXTRA_ATTENDANCE_FOLDER):
        folder_path = os.path.join(EXTRA_ATTENDANCE_FOLDER, folder_name)
        if not os.path.isdir(folder_path):
            continue
        try:
            datetime.strptime(folder_name, DATETIME_FORMATS.folder)
        except ValueError:
            continue

        if IF_FORCE_NEW_DAILY_SUMMARY or not check_daily_summary(summary_type, folder_path):
            log(f"Summary not found in \"{folder_name}\", attempting parse...", LogLevel.DEBUG)

            if summary_type == DAILY_SUMMARY.TEXTFILE:
                txt_files = [f for f in os.listdir(folder_path) if f.endswith(EXTENSIONS.text)]
                if not txt_files:
                    log(f"No .txt file found in \"{folder_name}\".", LogLevel.WARN)
                    continue

                txt_path = os.path.join(folder_path, txt_files[0])
                log(f"Found txt file: {txt_files[0]}", LogLevel.DEBUG)

                extra_player_list = parse_txt_file(txt_path)
                if not extra_player_list:
                    log(f"No online players found in \"{txt_files[0]}\".", LogLevel.WARN)
                    continue

                summary_data = [
                    {"name": name, "attendance": count}
                    for name, count in Counter(extra_player_list).items()
                ]
                meta = {txt_files[0]: get_file_checksum(txt_path)}

            elif summary_type == DAILY_SUMMARY.SCREENSHOT:
                summary_data, meta = parse_screenshot_file(folder_name, player_list, WORDLIST_TEMP_FILE)
                if not summary_data:
                    log(f"No valid screenshot data found in \"{folder_name}\".", LogLevel.WARN)
                    continue

            else:
                log(f"Unknown summary type for \"{folder_name}\".", LogLevel.ERROR)
                continue

            log(f"Saving summary for \"{folder_name}\" with {len(summary_data)} players...", LogLevel.DEBUG)
            save_daily_summary(summary_type, folder_name, summary_data, meta)
            result_by_day[folder_name] = summary_data
            continue

        log(f"Summary already exists for \"{folder_name}\". Loading instead.", LogLevel.DEBUG)
        summary, _ = load_daily_summary(summary_type, folder_name)
        if summary:
            result_by_day[folder_name] = summary

    return result_by_day

# Check if summary + meta exist and match
def check_daily_summary(summary_type: SimpleNamespace, folder_path: str):
    summary_path = os.path.join(folder_path, summary_type.SUMMARY)
    meta_path = os.path.join(folder_path, summary_type.META)

    if not os.path.exists(summary_path) or not os.path.exists(meta_path):
        return False

    try:
        with open(meta_path, "r", encoding=TEXTFILE_ENCODING) as f:
            recorded_meta = json.load(f)

        for filename, old_checksum in recorded_meta.items():
            filepath = os.path.join(folder_path, filename)
            if not os.path.exists(filepath):
                return False
            if get_file_checksum(filepath) != old_checksum:
                return False
        return True
    except Exception as e:
        log(f"Failed to verify summary integrity at \"{folder_path}\": {e}.", LogLevel.ERROR)
        return False

def load_daily_summary(summary_type: SimpleNamespace, folder_name: str) -> tuple[list[dict] | None, dict | None]:
    """
    Load summary and metadata for a specific day and type (TEXTFILE or SCREENSHOT).
    """
    folder_path = os.path.join(EXTRA_ATTENDANCE_FOLDER, folder_name)
    summary_path = os.path.join(folder_path, summary_type.SUMMARY)
    meta_path = os.path.join(folder_path, summary_type.META)

    if not os.path.exists(summary_path) or not os.path.exists(meta_path):
        return None, None

    try:
        with open(summary_path, "r", encoding=TEXTFILE_ENCODING) as f:
            summary = json.load(f)
        with open(meta_path, "r", encoding=TEXTFILE_ENCODING) as f:
            meta = json.load(f)
        return summary, meta
    except Exception as e:
        log(f"Failed to load \"{summary_type}\" cache from \"{folder_path}\": {e}.", level="error")
        return None, None

def calculate_interval_summary(summary_type: SimpleNamespace, result_by_day: dict) -> dict[int, dict[str, int]]:
    """
    Calculate interval attendance summary for the given summary type (TEXTFILE or SCREENSHOT).
    :param summary_type: DAILY_SUMMARY.TEXTFILE or DAILY_SUMMARY.SCREENSHOT
    :return: Dictionary mapping interval days to player attendance counts
    """
    today = datetime.today()
    summary_by_interval = {i: {} for i in INTERVALS}

    for i in range(DAYS_LOOKBACK):
        date = today - timedelta(days=i)
        folder_name = date.strftime(DATETIME_FORMATS.folder)

        summary, _ = load_daily_summary(summary_type, folder_name)
        if summary is None:
            continue

        for entry in summary:
            name = entry["name"]
            count = entry["attendance"]
            delta_days = (today - date).days

            for interval in INTERVALS:
                if delta_days < interval:
                    summary_by_interval[interval].setdefault(name, 0)
                    summary_by_interval[interval][name] += count

    return summary_by_interval

# Delete old daily summary files, keeping only the latest `keep_count`
def cleanup_old_daily_summary_files(keep_count):
    # Get all folders under EXTRA_ATTENDANCE_FOLDER that match the required format
    attendance_folders = [
        folder for folder in os.listdir(EXTRA_ATTENDANCE_FOLDER)
        if os.path.isdir(os.path.join(EXTRA_ATTENDANCE_FOLDER, folder)) and is_valid_folder_name(folder)
    ]
    
    deleted_count = 0
    for folder in attendance_folders:
        folder_path = os.path.join(EXTRA_ATTENDANCE_FOLDER, folder)
        
        # Get all .json and .meta files in the current folder
        all_files = [
            f for f in os.listdir(folder_path)
            if f.endswith(DAILY_SUMMARY.TEXTFILE.SUMMARY) or f.endswith(DAILY_SUMMARY.TEXTFILE.META) or 
               f.endswith(DAILY_SUMMARY.SCREENSHOT.SUMMARY) or f.endswith(DAILY_SUMMARY.SCREENSHOT.META)
        ]
        
        # Get the full paths of the files and their modification times
        full_paths = [
            (os.path.join(folder_path, f), os.path.getmtime(os.path.join(folder_path, f)))
            for f in all_files
        ]
        
        # Sort files by modification time (newest first)
        full_paths.sort(key=lambda x: x[1], reverse=True)
        
        # Files to delete (everything after the most recent `keep_count` files)
        files_to_delete = full_paths[keep_count:]
        
        # Delete the files
        for file_path, _ in files_to_delete:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    relative_path = get_relative_path_to_target(file_path)
                    log(f"Removed old daily summary: \"{relative_path}\".", LogLevel.WARN)
                    deleted_count += 1
                except Exception as e:
                    log(f"Failed to delete file \"{file_path}\": {e}.", LogLevel.ERROR)
            else:
                log(f"File does not exist: \"{file_path}\".", LogLevel.ERROR)

    return deleted_count

# Clear all daily summary files (keep_count=0 will remove everything)
def clear_all_daily_summary_files():
    return cleanup_old_daily_summary_files(keep_count=0)
