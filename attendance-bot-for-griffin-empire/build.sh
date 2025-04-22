# ----- ----- ----- -----
# build.sh
# For Albion Online "Griffin Empire" Guilds only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/22
# Update Date: 2025/04/22
# Version: v1.0
# ----- ----- ----- -----

#!/bin/bash
set -e # Exit on error

# ----- Config -----
ENTRY_POINT="run.py"
DIST_DIR="dist"
CONFIG_FILE="botcore/config.py"
RESOURCE_FOLDER="data"
OUTPUT_NAME="Albion_Attendance_Bot_made_by_DragonTaki"
ICON_FILE="icon.ico"

CONFIG_MODULE=$(echo "$CONFIG_FILE" | sed 's/\//./g' | sed 's/\.py$//')

# ----- Check icon file -----
ICON_OPTION=""
if [[ -f "$ICON_FILE" ]]; then
  ICON_OPTION="--icon=$ICON_FILE"
  echo "🧿 Icon file found: $ICON_FILE"
else
  echo "⚠️ Icon file not found: $ICON_FILE — skipping icon"
fi

# ----- Get trial days -----
TRIAL_DATE=$(python -c "
import importlib
mod = importlib.import_module('${CONFIG_MODULE}')
print(mod.TRIAL_DATE if hasattr(mod, 'TRIAL_DATE') else '')" 2>/dev/null)

# ----- Validate TRIAL_DATE is an integer -----
if ! [[ "$TRIAL_DATE" =~ ^[0-9]+$ ]]; then
  echo "❌ ERROR: Invalid TRIAL_DATE in $CONFIG_FILE. Expected integer, got: '$TRIAL_DATE'"
  exit 1
fi

# ----- Calculate expire date -----
EXPIRE_DATE=$(date -d "+$TRIAL_DATE days" +"%Y-%m-%d")
echo "🔧 Setting trial expire date: $EXPIRE_DATE"

# ----- Write EXPIRE_DATE back to config.py -----  
echo "Writing EXPIRE_DATE to $CONFIG_FILE"
sed -i "s/^EXPIRE_DATE = .*/EXPIRE_DATE = \"$EXPIRE_DATE\"/" "$CONFIG_FILE"

# ----- Determine data separator (for Windows/macOS) -----
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
  SEP=";"
else
  SEP=":"
fi

# ----- Run PyInstaller -----
echo "🚀 Packaging with PyInstaller..."
pyinstaller --noconfirm --onefile --windowed \
  --name "$OUTPUT_NAME" \
  --add-data "$RESOURCE_FOLDER$SEP$RESOURCE_FOLDER" \
  $ICON_OPTION \
  "$ENTRY_POINT"

# ----- Restore EXPIRE_DATE to original value -----
echo "🔄 Restoring original EXPIRE_DATE to $CONFIG_FILE"
sed -i "s/^EXPIRE_DATE = .*/EXPIRE_DATE = \"YYYY-MM-DD\"/" "$CONFIG_FILE"

# ----- Optional cleanup (keep for now) -----
echo "🧹 Cleaning up build files..."
rm -rf build __pycache__ "$ENTRY_POINT".spec

# ----- Done -----
echo "✅ Build complete. Output file:"
ls -lh "$DIST_DIR/$OUTPUT_NAME" 2>/dev/null || ls -lh "$DIST_DIR"