# ----- ----- ----- -----
# fetch_guild_members.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/05/01
# Version: v1.3
# ----- ----- ----- -----

from botcore.config.constant import CacheType
from botcore.config.static_settings import GUILD_INFO_LIST
from botcore.logging.app_logger import LogLevel, log
from .cache import save_to_cache_if_needed
from botcore.utils.network_utils import safe_web_fetch


# ----- Constants ----- #
API_BASE_URL = "https://gameinfo-sgp.albiononline.com/api/gameinfo"
API_ENDPOINT_TEMPLATE = f"{API_BASE_URL}/guilds/{{guild_id}}/members"
HEADERS = {"Accept": "application/json, text/plain, */*"}


# ----- Main Function ----- #
def fetch_guild_members(if_save_to_cache: bool = True) -> dict[str, str]:
    """
    Fetch member lists from the API for all configured guilds.

    Args:
        if_save_to_cache (bool): Whether to store the fetched member map in cache.

    Returns:
        dict[str, str]: A mapping from player names to their respective guild names.
    """
    result_map = {}

    for guild in GUILD_INFO_LIST:
        guild_name = guild.get("name")
        guild_id = guild.get("id")
        url = API_ENDPOINT_TEMPLATE.format(guild_id=guild_id)

        log(f"Fetching members for guild: {guild_name}...")

        data = safe_web_fetch(url, headers=HEADERS, context=f"{guild_name} members")
        if not data:
            log(f"No data returned from API for {guild_name}.", LogLevel.ERROR)
            continue

        for player in data:
            name = player.get("Name")
            if name:
                result_map[name] = guild_name

        log(f"Successfully fetched {len(data)} members from {guild_name}.")

    save_to_cache_if_needed(CacheType.MEMBERLIST, result_map, if_save_to_cache, "Member list")
    return result_map
