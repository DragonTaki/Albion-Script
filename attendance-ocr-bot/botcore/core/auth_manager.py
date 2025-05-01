# ----- ----- ----- -----
# auth_manager.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/27
# Update Date: 2025/04/27
# Version: v1.0
# ----- ----- ----- -----

import base64
import json
import hashlib
import os
from typing import Any, Dict, Literal, Optional

from botcore.config.constant import TEXTFILE_ENCODING
from botcore.config.settings_manager import get_settings
settings = get_settings()
from botcore.utils.network_utils import safe_web_fetch

# Constants
AUTH_FILENAME = "auth.json"

class AuthConfig:
    USERNAME_FIELD = "username"  # Username
    KEY_FIELD = "key"            # Password
    TOKEN_FIELD = "token"        # Token for Github auth
    REQUIRED_FIELDS = {USERNAME_FIELD, KEY_FIELD, TOKEN_FIELD}


# ----- Helper Functions ----- #
def _generate_auth_template(file_path: str = AUTH_FILENAME) -> None:
    """
    Generate a template auth.json file if missing or invalid.

    Args:
        file_path (str): Path where the auth.json file should be created.

    Returns:
        None
    """
    template = {
        AuthConfig.USERNAME_FIELD: "Your_Username_Here",
        AuthConfig.KEY_FIELD: "Your_Key_Here",
        AuthConfig.TOKEN_FIELD: "Your_Token_Here"
    }
    try:
        with open(file_path, "w") as file:
            json.dump(template, file, indent=4)
        print(f"Template '{file_path}' created. Please update it with your actual credentials.")
    except Exception as e:
        print(f"Error creating template auth file: {e}")


def _get_hash(key: str, username: str) -> str:
    """
    Generate a SHA-256 hash using the user's key and username as salt.

    Args:
        key (str): The user's key input.
        username (str): The user's username used as salt.

    Returns:
        str: A hexadecimal string representing the hashed key.
    """
    salt = username.encode()
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        key.encode(),
        salt,
        100000  # Iteration count
    )
    return hashed.hex()


def _load_auth_data(file_path: str = AUTH_FILENAME) -> Optional[Dict[str, str]]:
    """
    Load local authentication data, including username, key, and GitHub token.

    Args:
        file_path (str): Path to the auth.json file.

    Returns:
        Optional[Dict[str, str]]: Dictionary containing 'username', 'key', and 'token' if successful, None otherwise.
    """
    if not os.path.exists(file_path):
        print(f"Warning: '{file_path}' not found. Creating template...")
        _generate_auth_template(file_path)
        return None

    try:
        with open(file_path, "r") as file:
            auth_data = json.load(file)

        if not all(field in auth_data for field in AuthConfig.REQUIRED_FIELDS):
            missing_fields = [field for field in AuthConfig.REQUIRED_FIELDS if field not in auth_data]
            print(f"Error: Missing required fields: {', '.join(missing_fields)} in '{file_path}'.")
            return None

        return auth_data

    except (json.JSONDecodeError, Exception) as e:
        print(f"Warning: Invalid auth file '{file_path}': {e}. Recreating template...")
        _generate_auth_template(file_path)
        return None
    except Exception as e:
        print(f"Error reading auth file: {e}")
        return None


def _get_keys_from_github(token: str) -> Optional[Dict[str, Any]]:
    """
    Fetch encrypted API keys from the GitHub repository.

    Args:
        token (str): GitHub personal access token for authentication.

    Returns:
        Optional[Dict[str, Any]]: The parsed JSON data containing users and their hashed keys, or None on failure.
    """
    REPO_OWNER = "DragonTaki"
    REPO_NAME = "taki-key-repo"
    FILE_PATH = "albion-attendance-bot/api_keys.json"

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    HEADERS = {"Authorization": f"token {token}"}

    response_json = safe_web_fetch(url, headers=HEADERS, context="GitHub API keys", use_logger=False)
    if not response_json:
        return None

    try:
        file_content = response_json.get("content")
        if not file_content:
            print("Error: No content found in GitHub response.")
            return None

        decoded_content = base64.b64decode(file_content).decode(TEXTFILE_ENCODING)
        api_keys = json.loads(decoded_content)
        return api_keys

    except Exception as e:
        print(f"Error decoding GitHub file content: {e}")
        return None


def _validate_user(username: str, key: str, api_keys: Dict[str, Any]) -> bool:
    """
    Validate a user's key against the stored API keys.

    Args:
        username (str): The username of the user.
        key (str): The plain key provided by the user.
        api_keys (Dict[str, Any]): The dictionary containing stored usernames and their hashed keys.

    Returns:
        bool: True if the user is authorized, False otherwise.
    """
    if not api_keys:
        print("Error: API keys data is empty or invalid.")
        return False

    hashed_key = _get_hash(key, username)

    for user in api_keys.get("users", []):
        if user.get(AuthConfig.USERNAME_FIELD) == username:
            stored_key = user.get(AuthConfig.KEY_FIELD)
            if stored_key and stored_key == hashed_key:
                return True
            else:
                return False

    return False


# ----- Main Function ----- #
def auth_manager() -> Literal["success", "fail", "undefined"]:
    """
    Main entry point for authenticating a user.

    Returns:
        Literal["success", "fail", "undefined"]: 
        - "success" if the user is authorized,
        - "fail" if authentication failed,
        - "undefined" if auth.json is missing or invalid.
    """
    auth_data = _load_auth_data()
    if not auth_data:
        return "undefined"

    username = auth_data[AuthConfig.USERNAME_FIELD]
    key = auth_data[AuthConfig.KEY_FIELD]
    token = auth_data[AuthConfig.TOKEN_FIELD]

    api_keys = _get_keys_from_github(token)
    if not api_keys:
        return "undefined"

    if _validate_user(username, key, api_keys):
        print(f"✅ User '{username}' is authorized.")
        settings.current_user = username
        return "success"
    else:
        print(f"❌ User '{username}' is not authorized.")
        return "fail"


# ----- Entrypoint ----- #
if __name__ == "__main__":
    result = auth_manager()
    print(f"Authentication result: {result}")
