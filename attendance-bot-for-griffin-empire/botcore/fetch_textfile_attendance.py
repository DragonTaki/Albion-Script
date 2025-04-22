# ----- ----- ----- -----
# fetch_textfile_attendance.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/22
# Update Date: 2025/04/22
# Version: v1.0
# ----- ----- ----- -----

import os
import hashlib
import json
from datetime import datetime, timedelta

from .config import CacheType, INTERVALS, DAYS_LOOKBACK, EXTRA_ATTENDANCE_FOLDER, EXTRA_ATTENDANCE_FOLDER_FORMAT, TEXT_EXTENSIONS
from .cache import save_to_cache
from .logger import log
from .utils import get_path

# Constants
DAILY_SUMMARY_FILENAME = "summary.json"
DAILY_META_FILENAME = "meta.json"
REQUIRED_COLUMNS = ["Character Name", "Last Seen", "Roles"]

# Constant for standardized cache wrapper for interval-based summary
TEXTFILE_CACHE_OBJECT = {
    "type": CacheType.TEXTFILE.value,
    "json_data": None  # Will be filled dynamically
}


# Helper: calculate checksum of a file
def get_file_checksum(filepath):
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


# Helper: parse a valid attendance .txt file
def parse_txt_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines or lines[0].replace('"', "").split("\t") != REQUIRED_COLUMNS:
            log(f"Invalid format in file: {filepath}", "w")
            return []
        entries = []
        for line in lines[1:]:
            parts = line.replace('"', "").split("\t")
            if len(parts) >= 2 and parts[1].strip() == "Online":
                entries.append(parts[0].strip())
        log(f"Read attendance from file: {filepath}", "i")
        return entries
    except Exception as e:
        log(f"Failed to parse {filepath}: {e}", "e")
        return []


# Helper: check if daily folder has valid cached summary and meta
def load_cached_summary(folder_path):
    summary_path = get_path(folder_path, DAILY_SUMMARY_FILENAME)
    meta_path = get_path(folder_path, DAILY_META_FILENAME)
    if not os.path.exists(summary_path) or not os.path.exists(meta_path):
        return None, None
    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        return summary, meta
    except Exception as e:
        log(f"Failed to load cache from {folder_path}: {e}", "e")
        return None, None


# Core: process one day's attendance folder
def process_day_folder(folder_path):
    txt_files = [
        f for f in os.listdir(folder_path)
        if f.lower().endswith(TEXT_EXTENSIONS)
    ]
    if not txt_files:
        return None

    current_meta = {}
    all_online_players = set()

    for filename in txt_files:
        full_path = get_path(folder_path, filename)
        players = parse_txt_file(full_path)
        if players:
            all_online_players.update(players)
            current_meta[filename] = get_file_checksum(full_path)

    formatted = [{"name": name, "attendance": 1} for name in sorted(all_online_players)]

    summary_path = get_path(folder_path, DAILY_SUMMARY_FILENAME)
    meta_path = get_path(folder_path, DAILY_META_FILENAME)

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(formatted, f, indent=2, ensure_ascii=False)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(current_meta, f, indent=2, ensure_ascii=False)

    return formatted


# Top-Level: collect all available daily summaries
def collect_all_daily_attendance():
    result_by_day = {}
    today = datetime.today()
    for i in range(DAYS_LOOKBACK):
        date = today - timedelta(days=i)
        folder_name = date.strftime(EXTRA_ATTENDANCE_FOLDER_FORMAT)
        folder_path = get_path(EXTRA_ATTENDANCE_FOLDER, folder_name)
        if not os.path.isdir(folder_path):
            continue

        summary, meta = load_cached_summary(folder_path)

        current_files = [
            f for f in os.listdir(folder_path)
            if f.lower().endswith(TEXT_EXTENSIONS)
        ]
        current_meta = {
            f: get_file_checksum(get_path(folder_path, f))
            for f in current_files
        }

        if summary is None or meta is None or meta != current_meta:
            summary = process_day_folder(folder_path)
            if not summary:
                continue

        for entry in summary:
            name = entry["name"]
            result_by_day.setdefault(folder_name, {}).setdefault(name, 0)
            result_by_day[folder_name][name] += entry["attendance"]

    return result_by_day


# Core: calculate interval summaries from daily attendance
def calculate_interval_summary(result_by_day):
    today = datetime.today()
    summary_by_interval = {i: {} for i in INTERVALS}

    for folder_name, attendance in result_by_day.items():
        try:
            date = datetime.strptime(folder_name, EXTRA_ATTENDANCE_FOLDER_FORMAT)
        except ValueError:
            continue

        delta_days = (today - date).days
        for interval in INTERVALS:
            if delta_days < interval:
                for name, count in attendance.items():
                    summary_by_interval[interval].setdefault(name, 0)
                    summary_by_interval[interval][name] += count

    return summary_by_interval

# Helper: build cache-ready structure from interval summary
def build_textfile_cache(interval_summary):
    return {
        **TEXTFILE_CACHE_OBJECT,
        "json_data": interval_summary
    }

# Main function: call externally
def fetch_textfile_attendance(if_save_to_cache=True):
    result_by_day = collect_all_daily_attendance()
    summary_by_interval = calculate_interval_summary(result_by_day)

    if if_save_to_cache:
        if summary_by_interval:
            cache_data = build_textfile_cache(summary_by_interval)
            save_to_cache(cache_data)
            log(f"Extra attendance processed and saved. {len(result_by_day)} days processed.")
        else:
            log("No valid extra attendance data found. Nothing saved.", "e")

    return summary_by_interval
