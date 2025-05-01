# ----- ----- ----- -----
# fetch_killboard_attendance.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/05/01
# Version: v1.3
# ----- ----- ----- -----

import requests

from botcore.config.constant import CacheType, INTERVALS
from botcore.config.static_settings import GUILD_INFO_LIST
from botcore.logging.app_logger import LogLevel, log
from .cache import save_to_cache_if_needed
from botcore.utils.network_utils import safe_web_fetch


# ----- Constants ----- #
API_BASE_URL = "https://api-east.albionbattles.com/player"
MIN_GP = 50
API_ENDPOINT_TEMPLATE = f"{API_BASE_URL}?guildSearch={{guild_name}}&interval={{interval}}&minGP={MIN_GP}"
HEADERS = {"Accept": "application/json, text/plain, */*"}


# ----- Main Function ----- #
def fetch_killboard_attendance(if_save_to_cache: bool = True) -> dict:
    """
    Fetch attendance data from killboard API for all configured guilds over defined intervals.

    Args:
        if_save_to_cache (bool): Whether to store the fetched data in cache.

    Returns:
        dict: Nested dictionary where keys are interval days, and values are maps of player names to kill counts.
    """
    fetched_data = {interval: {} for interval in INTERVALS}
    for interval in INTERVALS:
        for guild in GUILD_INFO_LIST:
            guild_name = guild.get("name")
            url = API_ENDPOINT_TEMPLATE.format(guild_name=guild_name, interval=interval)

            data = safe_web_fetch(url, headers=HEADERS, context=f"{guild_name} at {interval}d")
            if isinstance(data, list):
                for player in data:
                    if "name" in player and isinstance(player.get("battleNumber"), int):
                        name = player["name"]
                        num = player["battleNumber"]
                        fetched_data[interval][name] = fetched_data[interval].get(name, 0) + num

    save_to_cache_if_needed(CacheType.KILLBOARD, fetched_data, if_save_to_cache, "Killboard attendance")
    return fetched_data
