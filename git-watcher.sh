#!/bin/bash

# Git watcher script for pulling latest changes from a specified branch
# This script runs when PULL_FROM_BRANCH environment variable is set

set -e

BRANCH="${PULL_FROM_BRANCH}"
POLL_INTERVAL="${GIT_POLL_INTERVAL:-30}"  # Default to 30 seconds

if [ -z "$BRANCH" ]; then
    echo "PULL_FROM_BRANCH not set, git watcher disabled"
    exit 0
fi

echo "Git watcher starting for branch: $BRANCH"
echo "Poll interval: ${POLL_INTERVAL} seconds"

# Function to pull latest changes
pull_changes() {
    echo "$(date): Checking for updates on branch $BRANCH"
    
    # Fetch latest changes
    git fetch origin "$BRANCH" 2>/dev/null || {
        echo "$(date): Failed to fetch from origin/$BRANCH"
        return 1
    }
    
    # Check if there are new commits
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse "origin/$BRANCH")
    
    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "$(date): New changes detected, pulling..."
        
        # Stash any local changes
        git stash push -m "Auto-stash before pull $(date)" 2>/dev/null || true
        
        # Pull the latest changes
        git pull origin "$BRANCH" || {
            echo "$(date): Failed to pull changes"
            return 1
        }
        
        echo "$(date): Successfully pulled latest changes"
        
        # Trigger rebuild/restart if needed
        if [ -f "/tmp/restart-services" ]; then
            echo "$(date): Triggering service restart"
            touch /tmp/restart-services
        fi
        
        return 0
    else
        echo "$(date): No new changes"
        return 1
    fi
}

# Initial setup
cd /app

# Ensure we're on the correct branch
git checkout "$BRANCH" 2>/dev/null || {
    echo "$(date): Failed to checkout branch $BRANCH, trying to create it"
    git checkout -b "$BRANCH" "origin/$BRANCH" || {
        echo "$(date): Failed to create/checkout branch $BRANCH"
        exit 1
    }
}

# Set up git config if not already set
git config --global --add safe.directory /app
git config user.name "${GIT_USER_NAME:-openvibe-watcher}" 2>/dev/null || true
git config user.email "${GIT_USER_EMAIL:-watcher@openvibe.local}" 2>/dev/null || true

echo "$(date): Git watcher initialized on branch $BRANCH"

# Main polling loop
while true; do
    pull_changes || true
    sleep "$POLL_INTERVAL"
done