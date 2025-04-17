# ----- ----- ----- -----
# fetch_attendance.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/18
# Version: v1.0
# ----- ----- ----- -----

import requests
from .config import GUILD_NAME, INTERVALS, MIN_GP
from .cache import save_to_cache  # 🔴 Updated to use new structured cache system
from .logger import log

def fetch_attendance_data():
    fetched_data = {interval: {} for interval in INTERVALS}
    for interval in INTERVALS:
        for guild in GUILD_NAME:
            url = f"https://api-east.albionbattles.com/player?guildSearch={guild}&interval={interval}&minGP={MIN_GP}"
            try:
                response = requests.get(url)
                if response.status_code != 200:
                    log(f"Failed to fetch data for {guild} at {interval}d. HTTP {response.status_code}", "w")
                    continue
                data = response.json()
                if isinstance(data, list):
                    for player in data:
                        if "name" in player and isinstance(player.get("battleNumber"), int):
                            name = player["name"]
                            num = player["battleNumber"]
                            fetched_data[interval][name] = fetched_data[interval].get(name, 0) + num
            except Exception as e:
                log(f"Exception occurred while fetching data: {e}", "e")
                continue

    # 🔴 Wrap in dict with type before saving
    save_to_cache({
        "type": "attendance",  # 🔴 new required type field
        "json_data": fetched_data
    })
    return fetched_data
