#!/bin/bash
# ----- ----- ----- -----
# git_push.sh
# For Albion Online "Malicious Crew", "Griffin Empire" Guilds only
# Do not distribute or modify
# Author: DragonTaki (https://github.com/DragonTaki)
# Create Date: 2025/04/18
# Update Date: 2025/04/20
# Version: v2.0
# ----- ----- ----- -----

# Constants
SUBMODULE_DIR="attendance-bot-for-griffin-empire"
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
  git remote add origin "$GIT_REMOTE_URL"
else
  echo "✅ Git already initialized. Skipping init."
fi

# Stage all files and commit
echo "📦 Staging all files and committing..."
git add .
git commit -m "Commit from Git Bash"

# Prompt before pushing
read -p "❓ Are you sure you want to push to '$MAIN_BRANCH'? (y/n): " confirm
if [[ "$confirm" =~ ^[Yy]$ ]]; then
    echo "🚀 Pushing to GitHub..."
    git push origin "$MAIN_BRANCH"
    echo "✅ Done! Your code is now correctly uploaded to GitHub."
else
    echo "❌ Push cancelled."
fi