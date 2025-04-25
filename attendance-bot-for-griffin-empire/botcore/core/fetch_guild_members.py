# ----- ----- ----- -----
# fetch_guild_members.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/25
# Version: v1.2
# ----- ----- ----- -----

import requests

from botcore.config.settings import GUILD_INFO_LIST
from .cache import CacheType, save_to_cache_if_needed
from .logger import LogLevel, log

# Constants for Fetch API
API_BASE_URL = "https://gameinfo-sgp.albiononline.com/api/gameinfo"
API_ENDPOINT_TEMPLATE = f"{API_BASE_URL}/guilds/{{guild_id}}/members"
HEADERS = {"Accept": "application/json, text/plain, */*"}

def fetch_guild_members(if_save_to_cache=True):
    result_map = {}

    for guild in GUILD_INFO_LIST:
        guild_name = guild.get("name")
        guild_id = guild.get("id")
        url = API_ENDPOINT_TEMPLATE.format(guild_id=guild_id)

        try:
            log(f"Fetching members for guild: {guild_name}...")

            response = requests.get(url, headers=HEADERS)
            if response.status_code != 200:
                log(f"HTTP {response.status_code} when fetching {guild_name} members.", LogLevel.ERROR)
                continue

            data = response.json()
            if not data:
                log(f"No data returned from API for {guild_name}.", LogLevel.ERROR)
                continue

            for player in data:
                name = player.get("Name")
                if name:
                    result_map[name] = guild_name

            log(f"Successfully fetched {len(data)} members from {guild_name}.")

        except Exception as e:
            log(f"Exception occurred while fetching {guild_name}: {str(e)}.", LogLevel.ERROR)
            continue

    # Save to cache
    save_to_cache_if_needed(CacheType.MEMBERLIST, result_map, if_save_to_cache, "Member list")

    return result_map
