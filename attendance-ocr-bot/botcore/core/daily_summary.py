# ----- ----- ----- -----
# daily_summary.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/23
# Update Date: 2025/04/26
# Version: v2.0
# ----- ----- ----- -----

import json
import os
from datetime import datetime, timedelta
from types import SimpleNamespace
from collections import Counter

from botcore.config.constant import CacheType, EXTENSIONS, DATETIME_FORMATS, INTERVALS, DAYS_LOOKBACK, TEXTFILE_ENCODING
from botcore.config.settings_manager import get_settings
settings = get_settings()
from botcore.logging.app_logger import LogLevel, log
from .process_textfile import parse_txt_file
from .process_screenshot import parse_screenshot_file, get_valid_player_list, create_word_list_file
from botcore.utils.file_utils import ensure_folder_exists, get_file_checksum, get_path, get_relative_path_to_target, is_valid_folder_name, list_dirs_sorted_by_date


# ----- Constants ----- #
FILENAME_TEMPLATE = "{prefix}{name}{ext}"

DAILY_SUMMARY = SimpleNamespace(
    TEXTFILE=SimpleNamespace(
        META=FILENAME_TEMPLATE.format(prefix="text_", name="meta", ext=".meta"),
        SUMMARY=FILENAME_TEMPLATE.format(prefix="text_", name="summary", ext=".json"),
        cache_type=CacheType.TEXTFILE
    ),
    SCREENSHOT=SimpleNamespace(
        META=FILENAME_TEMPLATE.format(prefix="screenshot_", name="meta", ext=".meta"),
        SUMMARY=FILENAME_TEMPLATE.format(prefix="screenshot_", name="summary", ext=".json"),
        cache_type=CacheType.SCREENSHOT
    )
)


# ----- Helper Functions ----- #
def _get_summary_file_paths(folder_input: str, summary_type: SimpleNamespace) -> tuple[str, str]:
    """
    Return summary and meta file paths for a given folder.

    Args:
        folder_input (str): Either folder name (YYYY-MM-DD) or full path.
        summary_type (SimpleNamespace): TEXTFILE or SCREENSHOT summary config.

    Returns:
        tuple[str, str]: (summary_path, meta_path)
    """
    if os.path.isabs(folder_input):  # already a full path
        folder_path = folder_input
    else:  # convert folder name to full path
        ensure_folder_exists(settings.folder_paths.attendance)
        folder_path = get_path(settings.folder_paths.attendance, folder_input)

    # Build the summary and meta file paths
    summary_path = get_path(folder_path, summary_type.SUMMARY)
    meta_path = get_path(folder_path, summary_type.META)
    return summary_path, meta_path


def _check_summary_valid(summary_type: SimpleNamespace, folder_path: str) -> bool:
    """
    Verify if summary and meta files exist and match the checksum of the source files.
    
    Args:
        summary_type (SimpleNamespace): Defines if the summary is of text or screenshot type.
        folder_path (str): The folder path containing the summary files.
    
    Returns:
        bool: Returns True if the summary is valid and up-to-date, False otherwise.
    """
    # Get the paths for the summary and meta files
    summary_path, meta_path = _get_summary_file_paths(folder_path, summary_type)

    # If either summary or meta file does not exist, the summary is invalid
    if not os.path.exists(summary_path) or not os.path.exists(meta_path):
        return False

    try:
        with open(meta_path, "r", encoding=TEXTFILE_ENCODING) as f:
            recorded_meta = json.load(f)

        # Verify that the file checksums match for each file in the metadata
        for filename, old_checksum in recorded_meta.items():
            filepath = os.path.join(folder_path, filename)
            if not os.path.exists(filepath) or get_file_checksum(filepath) != old_checksum:
                return False
        return True
    except Exception as e:
        log(f"Failed to verify summary integrity at \"{folder_path}\": {e}.", LogLevel.ERROR)
        return False


def _get_summary_type_name(summary_type: SimpleNamespace) -> str:
    """
    Returns a human-readable name for the summary type.
    
    Args:
        summary_type (SimpleNamespace): The type of summary (TEXTFILE or SCREENSHOT).
    
    Returns:
        str: The name of the summary type.
    """
    if summary_type not in (DAILY_SUMMARY.TEXTFILE, DAILY_SUMMARY.SCREENSHOT):
        raise ValueError(f"Unsupported summary type: {summary_type}")
    
    if summary_type == DAILY_SUMMARY.TEXTFILE:
        return "TEXTFILE"
    elif summary_type == DAILY_SUMMARY.SCREENSHOT:
        return "SCREENSHOT"
    return "UNKNOWN"


# ----- Main Functions ----- #
def load_daily_summary(summary_type: SimpleNamespace, folder_name: str) -> tuple[list[dict] | None, dict | None]:
    """
    Load saved daily summary and meta from disk.

    Args:
        summary_type (SimpleNamespace): Type of summary to load.
        folder_name (str): Folder name containing the summary.

    Returns:
        tuple: (attendance list, meta dict), or (None, None) if loading fails.
    """
    summary_path, meta_path = _get_summary_file_paths(folder_name, summary_type)

    if not os.path.exists(summary_path) or not os.path.exists(meta_path):
        return None, None

    try:
        with open(summary_path, "r", encoding=TEXTFILE_ENCODING) as f:
            summary = json.load(f)
        with open(meta_path, "r", encoding=TEXTFILE_ENCODING) as f:
            meta = json.load(f)
        return summary, meta
    except Exception as e:
        log(f"Failed to load \"{_get_summary_type_name(summary_type)}\" cache from \"{folder_name}\": {e}.", LogLevel.ERROR)
        return None, None
    

def save_daily_summary(summary_type: SimpleNamespace, folder_name: str, attendance_list: list[dict], meta: dict) -> list[dict]:
    """
    Save daily attendance summary and metadata into JSON files.
    
    Args:
        summary_type (SimpleNamespace): Defines if the summary is of text or screenshot type.
        folder_name (str): The folder name (in YYYY-MM-DD format) where the data will be saved.
        attendance_list (list[dict]): The list of player attendance records.
        meta (dict): Metadata for the summary, typically containing file names and checksums.
    
    Returns:
        list[dict]: Returns the attendance list as a confirmation.
    """
    # Get the paths for summary and metadata files
    summary_path, meta_path = _get_summary_file_paths(folder_name, summary_type)

    try:
        # Ensure the directory exists and save the attendance data
        ensure_folder_exists(os.path.dirname(summary_path))

        # Save the summary data as a JSON file
        with open(summary_path, "w", encoding=TEXTFILE_ENCODING) as f:
            json.dump(attendance_list, f, indent=2, ensure_ascii=False)
        
        # Save the metadata as a JSON file
        with open(meta_path, "w", encoding=TEXTFILE_ENCODING) as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        
        log(f"Saved summary and meta to \"{folder_name}\".")
    except Exception as e:
        # Log any errors during the save process
        log(f"Failed to save summary/meta in \"{folder_name}\": {e}.", LogLevel.ERROR)

    return attendance_list


def collect_all_daily_attendance(summary_type: SimpleNamespace) -> dict[str, list[dict]]:
    """
    Automatically collect all daily attendance data.

    - For each folder in the attendance directory:
        - Verify if summary is present and valid.
        - If not, parse raw data and save new summary.
    - Screenshot mode requires player name list and word list file.

    Args:
        summary_type (SimpleNamespace): Type of summary (either textfile or screenshot).

    Returns:
        dict[str, list[dict]]: A dictionary where each key is the folder name and the corresponding value is the attendance summary list.
    """
    result_by_day = {}  # Result dictionary to store attendance data for each day
    player_list = []  # List of valid player names
    wordlist_path = None  # Path to the wordlist file for screenshots

    # Prepare for screenshot mode
    if summary_type == DAILY_SUMMARY.SCREENSHOT:
        player_list = get_valid_player_list()  # Fetch valid player list
        wordlist_path = create_word_list_file(player_list)  # Generate wordlist file for OCR matching
    # Validate that summary type is supported
    elif summary_type not in vars(DAILY_SUMMARY).values():
        raise ValueError(f"Unsupported summary type: {summary_type}")

    # Iterate over all folders in the attendance directory
    ensure_folder_exists(settings.folder_paths.attendance)
    for folder_name in os.listdir(settings.folder_paths.attendance):
        folder_path = os.path.join(settings.folder_paths.attendance, folder_name)

        # Skip if the folder is invalid or does not contain the correct name format
        if not os.path.isdir(folder_path) or not is_valid_folder_name(folder_name):
            continue

        # Determine if the summary needs to be re-parsed or is outdated
        needs_reparse = settings.force_regenerate_daily_summary or not _check_summary_valid(summary_type, folder_path)

        if needs_reparse:
            log(f"Summary not found or outdated in \"{folder_name}\". Rebuilding...", LogLevel.DEBUG)

            # Handle textfile summary type
            if summary_type == DAILY_SUMMARY.TEXTFILE:
                txt_files = [f for f in os.listdir(folder_path) if f.endswith(EXTENSIONS.text)]
                if not txt_files:
                    log(f"No .txt file found in \"{folder_name}\".", LogLevel.WARN)
                    continue

                txt_path = os.path.join(folder_path, txt_files[0])
                extra_player_list = parse_txt_file(txt_path)  # Parse player data from .txt file

                if not extra_player_list:
                    log(f"No valid player entries in \"{txt_files[0]}\".", LogLevel.WARN)
                    continue

                # Aggregate player attendance data
                summary_data = [
                    {"name": name, "attendance": count}
                    for name, count in Counter(extra_player_list).items()
                ]
                meta = {txt_files[0]: get_file_checksum(txt_path)}  # Store metadata (checksum of the .txt file)

            # Handle screenshot summary type
            elif summary_type == DAILY_SUMMARY.SCREENSHOT:
                summary_data, meta = parse_screenshot_file(folder_name, player_list, wordlist_path)
                if not summary_data:
                    log(f"No valid screenshot data found in \"{folder_name}\".", LogLevel.WARN)
                    continue

            else:
                log(f"Unknown summary type for \"{folder_name}\".", LogLevel.ERROR)
                continue

            # Save the newly parsed summary and metadata
            save_daily_summary(summary_type, folder_name, summary_data, meta)
            result_by_day[folder_name] = summary_data  # Add the parsed data to the result dictionary

        else:
            # If the summary is valid, load it from the disk
            summary, _ = load_daily_summary(summary_type, folder_name)
            if summary:
                result_by_day[folder_name] = summary

    return result_by_day


def calculate_interval_summary(summary_type: SimpleNamespace, result_by_day: dict[str, list[dict]]) -> dict[int, dict[str, int]]:
    """
    Aggregate attendance into 7/14/28-day intervals.

    This function processes the daily attendance data and aggregates it by intervals (7, 14, and 28 days).
    For each player, the attendance count over the specified intervals is calculated.

    Args:
        summary_type (SimpleNamespace): Summary type (unused but retained for future use).
        result_by_day (dict): Daily attendance mapping from folder to summary list.

    Returns:
        dict[int, dict[str, int]]: Mapping from interval (7, 14, 28) to player attendance counts.
    """
    today = datetime.today()  # Get today's date
    summary_by_interval = {i: {} for i in INTERVALS}  # Initialize result dictionary for each interval

    # Iterate over the past DAYS_LOOKBACK days to aggregate attendance data
    for i in range(DAYS_LOOKBACK):
        date = today - timedelta(days=i)  # Calculate the date for this iteration
        folder_name = date.strftime(DATETIME_FORMATS.folder)  # Format the date as folder name

        # Get the attendance summary for the current day
        summary = result_by_day.get(folder_name)
        if not summary:
            continue  # Skip if no summary found for the day

        # Process each entry (player) in the summary
        for entry in summary:
            name = entry["name"]  # Player name
            count = entry["attendance"]  # Player attendance count
            delta_days = (today - date).days  # Calculate the number of days between today and the summary date

            # Aggregate attendance counts by interval (7, 14, 28 days)
            for interval in INTERVALS:
                if delta_days < interval:
                    summary_by_interval[interval].setdefault(name, 0)
                    summary_by_interval[interval][name] += count

    return summary_by_interval


def cleanup_old_daily_summary_files(keep_count: int) -> int:
    """
    Delete old summary/meta files, retaining only the most recent `keep_count` per day.

    This function iterates through all folders in the attendance directory, sorts summary files by their modification time,
    and deletes all but the most recent `keep_count` files.

    Args:
        keep_count (int): Number of recent files to keep per day.

    Returns:
        int: Total number of files deleted.
    """
    deleted_count = 0  # Counter for deleted files
    ensure_folder_exists(settings.folder_paths.attendance)
    attendance_folders = list_dirs_sorted_by_date(settings.folder_paths.attendance)  # Get all attendance folder names sorted by date

    # Iterate over each attendance folder
    for folder_name in attendance_folders:
        folder_path = os.path.join(settings.folder_paths.attendance, folder_name)
        summary_files = [
            f for f in os.listdir(folder_path)
            if f.endswith(DAILY_SUMMARY.TEXTFILE.SUMMARY) or f.endswith(DAILY_SUMMARY.TEXTFILE.META) or
               f.endswith(DAILY_SUMMARY.SCREENSHOT.SUMMARY) or f.endswith(DAILY_SUMMARY.SCREENSHOT.META)
        ]

        # Sort files by their modification time, keeping the latest `keep_count`
        full_paths = [
            (os.path.join(folder_path, f), os.path.getmtime(os.path.join(folder_path, f)))
            for f in summary_files
        ]
        full_paths.sort(key=lambda x: x[1], reverse=True)

        # Delete files exceeding the `keep_count`
        for file_path, _ in full_paths[keep_count:]:
            try:
                os.remove(file_path)
                log(f"Removed old daily summary: \"{get_relative_path_to_target(file_path)}\".", LogLevel.WARN)
                deleted_count += 1
            except Exception as e:
                log(f"Failed to delete file \"{file_path}\": {e}.", LogLevel.ERROR)

    return deleted_count

def clear_all_daily_summary_files() -> int:
    """
    Delete all summary and meta files in attendance folders.

    This function deletes every summary and meta file in the attendance folders.

    Returns:
        int: Total number of files deleted.
    """
    return cleanup_old_daily_summary_files(keep_count=0)  # Deletes all files by setting `keep_count` to 0
