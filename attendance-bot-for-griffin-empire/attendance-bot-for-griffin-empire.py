# ----- ----- ----- -----
# attendance-bot-for-griffin-empire.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/17
# Update Date: 2025/04/17
# Version: v1.0
# ----- ----- ----- -----

import csv
import requests
from datetime import datetime, timedelta, timezone
import json
import os
import hashlib
import time
import pickle

# 🔴 Constants
GUILD_TAGS = ["GE"]
GUILD_NAMES = ["Griffin Empire"]
ATTENDANCE_INTERVALS = [7, 14, 28]
MIN_GP = 50
USE_CACHE = True
CACHE_EXPIRY_HOURS = 8
MAX_CSV_VERSIONS = 3
CSV_FILENAME_PREFIX = "attendance_data_"
CSV_EXTENSION = ".csv"
KEY_PLAYER = "Player"
KEY_7D = "7DaysAttendance"
KEY_14D = "14DaysAttendance"
KEY_28D = "28DaysAttendance"
CSV_HEADERS = [KEY_PLAYER, KEY_7D, KEY_14D, KEY_28D]

attendance_data = {interval: {} for interval in ATTENDANCE_INTERVALS}

# Generate a random cache filename using SHA256 hash of timestamp
def generate_cache_filename():
    timestamp = str(time.time()).encode("utf-8")
    return hashlib.sha256(timestamp).hexdigest()[:16] + ".cache"

# Save data to a uniquely named binary cache file
def save_to_cache(data):
    filename = generate_cache_filename()
    with open(filename, "wb") as f:
        pickle.dump({
            "timestamp": datetime.now(timezone.utc),
            "fetched_data": data
        }, f)
    print(f"Data cached as \"{filename}\".")

# Load latest valid cache from existing .cache files
def load_from_cache():
    cache_files = [f for f in os.listdir() if f.endswith(".cache")]
    latest_valid_cache = None
    latest_time = None

    for fname in cache_files:
        try:
            if os.path.getsize(fname) == 0:
                print(f"Skipping empty cache file \"{fname}\".")
                os.remove(fname)
                continue
            with open(fname, "rb") as f:
                cache_payload = pickle.load(f)
                cache_time = cache_payload["timestamp"]

                if not isinstance(cache_time, datetime):
                    raise ValueError("Invalid timestamp format")
                if datetime.now(timezone.utc) - cache_time >= timedelta(hours=CACHE_EXPIRY_HOURS):
                    print(f"Deleting expired cache file \"{fname}\".")
                    os.remove(fname)
                    continue
                if latest_time is None or cache_time > latest_time:
                    latest_time = cache_time
                    latest_valid_cache = cache_payload
        except Exception as e:
            print(f"Failed to read cache file \"{fname}\": {str(e)}")
            os.remove(fname)

    if latest_valid_cache:
        print("Loaded from valid cache.")
        return latest_valid_cache["fetched_data"]
    return None

# Step 0: Try loading cache
if USE_CACHE:
    cached = load_from_cache()
    if cached:
        attendance_data = {int(k): v for k, v in cached.items()}
    else:
        fetch_new = True
else:
    fetch_new = True

# Step 1: Fetch data if not loaded from cache
if not USE_CACHE or "fetch_new" in locals():
    for interval in ATTENDANCE_INTERVALS:
        for guild in GUILD_NAMES:
            print(f"Fetching data for guild \"{guild}\" at {interval} days...")
            url = f"https://api-east.albionbattles.com/player?guildSearch={guild}&interval={interval}&minGP={MIN_GP}"
            try:
                response = requests.get(url)
                if response.status_code != 200:
                    print(f"Error fetching data: HTTP {response.status_code}.")
                    continue
                data = response.json()
                if not isinstance(data, list):
                    print(f"Invalid response format at {interval} days.")
                    continue
                for player in data:
                    if "name" in player and isinstance(player.get("battleNumber"), int):
                        player_name = player["name"]
                        battle_number = player["battleNumber"]
                        attendance_data[interval][player_name] = attendance_data[interval].get(player_name, 0) + battle_number
                print(f"Fetched data for \"{guild}\" at {interval} days.")
            except Exception as e:
                print(f"Error fetching data for \"{guild}\" at {interval} days: {str(e)}.")
    save_to_cache(attendance_data)

# Step 2: Prepare data for output
all_players = set()
for interval in ATTENDANCE_INTERVALS:
    all_players.update(attendance_data[interval].keys())

results = []
for player_name in sorted(all_players):
    result_row = {
        KEY_PLAYER: player_name,
        KEY_7D: attendance_data[7].get(player_name, 0),
        KEY_14D: attendance_data[14].get(player_name, 0),
        KEY_28D: attendance_data[28].get(player_name, 0),
    }
    results.append(result_row)

# Step 3: Write results to timestamped CSV and manage version retention
def write_csv_with_timestamp_and_limit_versions(data_rows):
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{CSV_FILENAME_PREFIX}{timestamp_str}{CSV_EXTENSION}"

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(data_rows)
    print(f"Attendance data has been written to \"{filename}\".")

    # Clean up old CSV files
    csv_files = sorted(
        [f for f in os.listdir() if f.startswith(CSV_FILENAME_PREFIX) and f.endswith(CSV_EXTENSION)],
        key=lambda x: os.path.getmtime(x),
        reverse=True
    )
    for old_file in csv_files[MAX_CSV_VERSIONS:]:
        os.remove(old_file)
        print(f"Deleted old CSV file: {old_file}")

write_csv_with_timestamp_and_limit_versions(results)