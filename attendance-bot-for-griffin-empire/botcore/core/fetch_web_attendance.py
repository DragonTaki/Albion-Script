# ----- ----- ----- -----
# fetch_web_attendance.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/25
# Version: v1.2
# ----- ----- ----- -----

import requests

from .config.constant import INTERVALS
from .config.settings import GUILD_INFO_LIST
from .cache import CacheType, save_to_cache_if_needed
from .logger import LogLevel, log

# Constants for Fetch API
API_BASE_URL = "https://api-east.albionbattles.com/player"
MIN_GP = 50
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
                    log(f"Failed to fetch data for {guild_name} at {interval}d. HTTP {response.status_code}.", LogLevel.ERROR)
                    continue
                data = response.json()
                if isinstance(data, list):
                    for player in data:
                        if "name" in player and isinstance(player.get("battleNumber"), int):
                            name = player["name"]
                            num = player["battleNumber"]
                            fetched_data[interval][name] = fetched_data[interval].get(name, 0) + num
            except Exception as e:
                log(f"Exception occurred while fetching data: {e}.", LogLevel.ERROR)
                continue

    # Save to cache
    save_to_cache_if_needed(CacheType.ATTENDANCE, fetched_data, if_save_to_cache, "Killboard attendance")

    return fetched_data
