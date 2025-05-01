# ----- ----- ----- -----
# git_push.sh
# For Albion Online "Malicious Crew", "Griffin Empire" Guilds only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/22
# Version: v2.1
# ----- ----- ----- -----

#!/bin/bash

# ----- Config -----
SUBMODULE_DIR="attendance-ocr-bot"
GIT_REMOTE_NAME="origin"
GIT_REMOTE_URL="https://github.com/DragonTaki/Albion-Script.git"
MAIN_BRANCH="main"

# Exit immediately on error
set -e

# Check if we're in the project root
if [ ! -d "$SUBMODULE_DIR" ]; then
  echo "❌ Error: Please run this script from the project root (Albion-Script)"
  exit 1
fi

# Remove mistakenly initialized Git repo in subfolder
if [ -d "$SUBMODULE_DIR/.git" ]; then
  echo "🧹 Removing incorrect Git config from $SUBMODULE_DIR..."
  rm -rf "$SUBMODULE_DIR/.git"
fi

# Initialize Git if not already initialized
if [ ! -d ".git" ]; then
  echo "🔧 Initializing Git repository..."
  git init
  git remote add "$GIT_REMOTE_NAME" "$GIT_REMOTE_URL"
else
  echo "✅ Git already initialized. Skipping init."
fi

# Check remote version before pushing
echo "🔍 Checking remote version on GitHub..."
git fetch "$GIT_REMOTE_NAME" "$MAIN_BRANCH"

LOCAL_HASH=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse "$GIT_REMOTE_NAME/$MAIN_BRANCH")

if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
  echo "⚠️ Remote branch '$MAIN_BRANCH' has new commits."
  echo "🛑 Please pull the latest changes before pushing:"
  echo ""
  echo "   git pull --rebase $GIT_REMOTE_NAME $MAIN_BRANCH"
  echo ""
  echo "❌ Push aborted to prevent overwrite."
  exit 1
else
  echo "✅ Local branch is up to date with remote."
fi

# Stage all files and commit
echo "📦 Staging all files and committing..."
git add .
git status
git commit -m "Commit from Git Bash" || echo "ℹ️ No changes to commit."

# Prompt before pushing
read -p "❓ Are you sure you want to push to '$MAIN_BRANCH'? (y/n): " confirm
if [[ "$confirm" =~ ^[Yy]$ ]]; then
    echo "🚀 Pushing to GitHub..."
    git push "$GIT_REMOTE_NAME" "$MAIN_BRANCH"
    echo "✅ Done! Your code is now correctly uploaded to GitHub."
else
    echo "❌ Push cancelled."
fi
