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

from botcore.config.constant import EXTENSIONS, DATETIME_FORMATS, INTERVALS, DAYS_LOOKBACK, TEXTFILE_ENCODING
from botcore.config.settings import FOLDER_PATHS, IF_FORCE_NEW_DAILY_SUMMARY
from .logger import LogLevel, log
from .process_textfile import parse_txt_file
from .process_screenshot import parse_screenshot_file, get_valid_player_list, create_word_list_file
from .utils import ensure_folder_exists, get_file_checksum, get_relative_path_to_target, is_valid_folder_name, list_dirs_sorted_by_date

# ----- Constants ----- #
FILENAME_TEMPLATE = "{prefix}{name}{ext}"

DAILY_SUMMARY = SimpleNamespace(
    TEXTFILE=SimpleNamespace(
        META=FILENAME_TEMPLATE.format(prefix="text_", name="meta", ext=".meta"),
        SUMMARY=FILENAME_TEMPLATE.format(prefix="text_", name="summary", ext=".json"),
    ),
    SCREENSHOT=SimpleNamespace(
        META=FILENAME_TEMPLATE.format(prefix="screenshot_", name="meta", ext=".meta"),
        SUMMARY=FILENAME_TEMPLATE.format(prefix="screenshot_", name="summary", ext=".json"),
    )
)

# ----- External: Save Daily Summary ----- #
def save_daily_summary(summary_type: SimpleNamespace, folder_name: str, attendance_list: list[dict], meta: dict) -> list[dict]:
    """
    Save daily attendance and meta into designated summary and meta file.
    """
    folder_path = os.path.join(FOLDER_PATHS.attendance, folder_name)
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
        log(f"Failed to save summary/meta in \"{folder_name}\": {e}.", LogLevel.ERROR)

    return attendance_list

# ----- Internal: Verify Summary Validity ----- #
def _check_summary_valid(summary_type: SimpleNamespace, folder_path: str) -> bool:
    summary_path = os.path.join(folder_path, summary_type.SUMMARY)
    meta_path = os.path.join(folder_path, summary_type.META)

    if not os.path.exists(summary_path) or not os.path.exists(meta_path):
        return False

    try:
        with open(meta_path, "r", encoding=TEXTFILE_ENCODING) as f:
            recorded_meta = json.load(f)

        for filename, old_checksum in recorded_meta.items():
            filepath = os.path.join(folder_path, filename)
            if not os.path.exists(filepath) or get_file_checksum(filepath) != old_checksum:
                return False
        return True
    except Exception as e:
        log(f"Failed to verify summary integrity at \"{folder_path}\": {e}.", LogLevel.ERROR)
        return False

# ----- External: Load Existing Summary ----- #
def load_daily_summary(summary_type: SimpleNamespace, folder_name: str) -> tuple[list[dict] | None, dict | None]:
    folder_path = os.path.join(FOLDER_PATHS.attendance, folder_name)
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
        log(f"Failed to load \"{summary_type}\" cache from \"{folder_path}\": {e}.", LogLevel.ERROR)
        return None, None

# ----- External: Collect All Daily Summary (Auto Parse) ----- #
def collect_all_daily_attendance(summary_type: SimpleNamespace) -> dict[str, list[dict]]:
    result_by_day = {}
    player_list = []
    wordlist_path = None

    if summary_type == DAILY_SUMMARY.SCREENSHOT:
        player_list = get_valid_player_list()
        wordlist_path = create_word_list_file(player_list)
    elif summary_type not in vars(DAILY_SUMMARY).values():
        raise ValueError(f"Unsupported summary type: {summary_type}")

    for folder_name in os.listdir(FOLDER_PATHS.attendance):
        folder_path = os.path.join(FOLDER_PATHS.attendance, folder_name)

        if not os.path.isdir(folder_path) or not is_valid_folder_name(folder_name):
            continue

        needs_reparse = IF_FORCE_NEW_DAILY_SUMMARY or not _check_summary_valid(summary_type, folder_path)

        if needs_reparse:
            log(f"Summary not found or outdated in \"{folder_name}\". Rebuilding...", LogLevel.DEBUG)

            if summary_type == DAILY_SUMMARY.TEXTFILE:
                txt_files = [f for f in os.listdir(folder_path) if f.endswith(EXTENSIONS.text)]
                if not txt_files:
                    log(f"No .txt file found in \"{folder_name}\".", LogLevel.WARN)
                    continue

                txt_path = os.path.join(folder_path, txt_files[0])
                extra_player_list = parse_txt_file(txt_path)

                if not extra_player_list:
                    log(f"No valid player entries in \"{txt_files[0]}\".", LogLevel.WARN)
                    continue

                summary_data = [
                    {"name": name, "attendance": count}
                    for name, count in Counter(extra_player_list).items()
                ]
                meta = {txt_files[0]: get_file_checksum(txt_path)}

            elif summary_type == DAILY_SUMMARY.SCREENSHOT:
                summary_data, meta = parse_screenshot_file(folder_name, player_list, wordlist_path)
                if not summary_data:
                    log(f"No valid screenshot data found in \"{folder_name}\".", LogLevel.WARN)
                    continue

            else:
                log(f"Unknown summary type for \"{folder_name}\".", LogLevel.ERROR)
                continue

            save_daily_summary(summary_type, folder_name, summary_data, meta)
            result_by_day[folder_name] = summary_data

        else:
            summary, _ = load_daily_summary(summary_type, folder_name)
            if summary:
                result_by_day[folder_name] = summary

    return result_by_day

# ----- External: Calculate Summary for Intervals ----- #
def calculate_interval_summary(summary_type: SimpleNamespace, result_by_day: dict[str, list[dict]]) -> dict[int, dict[str, int]]:
    today = datetime.today()
    summary_by_interval = {i: {} for i in INTERVALS}

    for i in range(DAYS_LOOKBACK):
        date = today - timedelta(days=i)
        folder_name = date.strftime(DATETIME_FORMATS.folder)

        summary = result_by_day.get(folder_name)
        if not summary:
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

# ----- External: Cleanup Old Summary Files ----- #
def cleanup_old_daily_summary_files(keep_count: int) -> int:
    deleted_count = 0
    attendance_folders = list_dirs_sorted_by_date(FOLDER_PATHS.attendance)

    for folder_name in attendance_folders:
        folder_path = os.path.join(FOLDER_PATHS.attendance, folder_name)
        summary_files = [
            f for f in os.listdir(folder_path)
            if f.endswith(DAILY_SUMMARY.TEXTFILE.SUMMARY) or f.endswith(DAILY_SUMMARY.TEXTFILE.META) or
               f.endswith(DAILY_SUMMARY.SCREENSHOT.SUMMARY) or f.endswith(DAILY_SUMMARY.SCREENSHOT.META)
        ]

        # Sort by modified time, keep latest `keep_count`
        full_paths = [
            (os.path.join(folder_path, f), os.path.getmtime(os.path.join(folder_path, f)))
            for f in summary_files
        ]
        full_paths.sort(key=lambda x: x[1], reverse=True)

        for file_path, _ in full_paths[keep_count:]:
            try:
                os.remove(file_path)
                log(f"Removed old daily summary: \"{get_relative_path_to_target(file_path)}\".", LogLevel.WARN)
                deleted_count += 1
            except Exception as e:
                log(f"Failed to delete file \"{file_path}\": {e}.", LogLevel.ERROR)

    return deleted_count

# ----- External: Clear All Summary Files ----- #
def clear_all_daily_summary_files() -> int:
    return cleanup_old_daily_summary_files(keep_count=0)
