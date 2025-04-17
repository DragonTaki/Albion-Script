#!/bin/bash

# -------- CONFIG --------
COMMIT_MSG="Update project files"
APPEND_GITIGNORE=true   # 🔴 Set to false if you don't want to touch .gitignore
# ------------------------

if $APPEND_GITIGNORE; then
    echo "📄 Ensuring .gitignore includes necessary patterns..."
    cat <<EOF >> .gitignore

# Auto-appended patterns
__pycache__/
*.py[cod]
*.pyo
*.cache
attendance_data_*.csv
*.png
*.jpg
*.jpeg
*.bmp
*.log
.vscode/
.DS_Store
Thumbs.db
EOF
    # Remove duplicate lines
    sort -u .gitignore -o .gitignore
fi

echo "📂 Staging all changes..."
git add .

echo "📝 Committing with message: \"$COMMIT_MSG\""
git commit -m "$COMMIT_MSG"

echo "🚀 Pushing to current remote and branch..."
git push

echo "✅ Done!"
