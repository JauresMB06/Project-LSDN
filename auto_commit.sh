#!/bin/bash

# Auto commit script
# Add all changes
git add .

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "No changes to commit."
else
    # Commit with a timestamp message
    git commit -m "Auto commit: $(date)"
    # Push to origin master
    git push origin master
    echo "Changes committed and pushed."
fi
