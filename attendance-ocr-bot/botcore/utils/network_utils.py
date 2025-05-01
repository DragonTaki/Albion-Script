# ----- ----- ----- -----
# network_utils.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/05/01
# Update Date: 2025/05/01
# Version: v1.0
# ----- ----- ----- -----

import requests
import time
from typing import Optional, Union

from botcore.logging.app_logger import log, LogLevel

# ----- Network Related Functions ----- #
def safe_web_fetch(
    url: str,
    headers: Optional[dict] = None,
    context: str = "",
    use_logger: bool = True,
    retries: int = 3,
    delay_sec: float = 1.0
) -> Union[dict, list, None]:
    """
    Send a GET request with retry mechanism and optional logging.

    Args:
        url (str): The API endpoint to request.
        headers (dict, optional): Headers to include in the request.
        context (str): Human-readable context for log messages.
        use_logger (bool): If False, fallback to print instead of GUI logger (for pre-login).
        retries (int): Number of times to retry on failure.
        delay_sec (float): Delay (in seconds) between retries.

    Returns:
        dict | list | None: The parsed JSON data or None on failure.
    """
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=headers or {})
            if response.status_code == 200:
                return response.json()
            else:
                msg = f"HTTP {response.status_code} error while fetching {context or url} (Attempt {attempt}/{retries})."
                if use_logger:
                    log(msg, LogLevel.ERROR)
                else:
                    print(msg)
        except Exception as e:
            msg = f"Exception during request to {context or url}: {e} (Attempt {attempt}/{retries})."
            if use_logger:
                log(msg, LogLevel.ERROR)
            else:
                print(msg)

        if attempt < retries:
            time.sleep(delay_sec)

    return None
