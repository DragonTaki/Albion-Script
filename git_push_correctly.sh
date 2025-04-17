#!/bin/bash

# Exit immediately on error
set -e

# Check if we're in the project root
if [ ! -d "attendance-bot-for-griffin-empire" ]; then
  echo "❌ Error: Please run this script from the project root (Albion-Script)"
  exit 1
fi

# Remove mistakenly initialized Git repo in subfolder
if [ -d "attendance-bot-for-griffin-empire/.git" ]; then
  echo "🧹 Removing incorrect Git config from attendance-bot-for-griffin-empire..."
  rm -rf attendance-bot-for-griffin-empire/.git
fi

# Initialize Git if not already initialized
if [ ! -d ".git" ]; then
  echo "🔧 Initializing Git repository..."
  git init
  git remote add origin https://github.com/DragonTaki/Albion-Script.git
else
  echo "✅ Git already initialized. Skipping init."
fi

# Stage all files and commit
echo "📦 Staging all files and committing..."
git add .
git commit -m "✅ First valid commit from correct project root"

# Force push to remote 'main' branch
echo "🚀 Pushing to GitHub (force push)..."
git push --force origin main

echo "✅ Done! Your code is now correctly uploaded to GitHub."