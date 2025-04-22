# ----- ----- ----- -----
# fetch_web_attendance.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/18
# Version: v1.0
# ----- ----- ----- -----

import requests

from .config import CacheType, GUILD_INFO_LIST, INTERVALS
from .cache import save_to_cache
from .logger import log

# API constants
MIN_GP = 50
API_BASE_URL = "https://api-east.albionbattles.com/player"
API_ENDPOINT_TEMPLATE = f"{API_BASE_URL}?guildSearch={{guild_name}}&interval={{interval}}&minGP={MIN_GP}"
HEADERS = {"Accept": "application/json, text/plain, */*"}

def fetch_web_attendance(if_save_to_cache=True):
    fetched_data = {interval: {} for interval in INTERVALS}
    for interval in INTERVALS:
        for guild in GUILD_INFO_LIST:
            guild_name = guild.get("name")
            url = API_ENDPOINT_TEMPLATE.format(guild_name=guild_name, interval=interval)
            try:
                response = requests.get(url, headers=HEADERS)
                if response.status_code != 200:
                    log(f"Failed to fetch data for {guild_name} at {interval}d. HTTP {response.status_code}.", "w")
                    continue
                data = response.json()
                if isinstance(data, list):
                    for player in data:
                        if "name" in player and isinstance(player.get("battleNumber"), int):
                            name = player["name"]
                            num = player["battleNumber"]
                            fetched_data[interval][name] = fetched_data[interval].get(name, 0) + num
            except Exception as e:
                log(f"Exception occurred while fetching data: {e}.", "e")
                continue

    # Save to cache
    if if_save_to_cache:
        if fetched_data:
            cache_data = {
                "type": CacheType.ATTENDANCE.value,
                "json_data": fetched_data
            }
            save_to_cache(cache_data)
            log(f"Attendance saved to cache.")

    return fetched_data
