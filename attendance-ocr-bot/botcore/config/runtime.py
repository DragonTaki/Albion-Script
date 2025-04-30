# ----- ----- ----- -----
# runtime.py
# For Albion Online "Griffin Empire" Guild only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/25
# Update Date: 2025/04/25
# Version: v1.0
# ----- ----- ----- -----

import os
import sys

# Detect if running in a PyInstaller environment
IS_PACKAGED = hasattr(sys, "_MEIPASS")

# PyInstaller _MEIPASS temp directory (used for resource access)
MEIPASS_PATH = getattr(sys, "_MEIPASS", None)

# Executable base path: .exe directory (packed) or project root directory (IDE run)
EXE_BASE_PATH = os.path.dirname(sys.executable) if IS_PACKAGED else os.path.abspath(".")
