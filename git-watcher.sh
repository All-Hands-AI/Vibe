#!/bin/bash

# Simplified git watcher script with better error handling
# This script runs when PULL_FROM_BRANCH environment variable is set

BRANCH="${PULL_FROM_BRANCH}"
POLL_INTERVAL="${GIT_POLL_INTERVAL:-60}"  # Default to 60 seconds (less frequent)

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] GIT-WATCHER: $1"
}

if [ -z "$BRANCH" ]; then
    log "PULL_FROM_BRANCH not set, git watcher disabled"
    exit 0
fi

log "🔄 Git watcher starting for branch: $BRANCH"
log "📅 Poll interval: ${POLL_INTERVAL} seconds"

# Function to pull latest changes
pull_changes() {
    log "🔍 Checking for updates on branch $BRANCH"
    
    # Fetch latest changes (with timeout and error handling)
    timeout 30 git fetch origin "$BRANCH" 2>/dev/null || {
        log "⚠️  Failed to fetch from origin/$BRANCH (network issue?)"
        return 1
    }
    
    # Check if there are new commits
    LOCAL=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    REMOTE=$(git rev-parse "origin/$BRANCH" 2>/dev/null || echo "unknown")
    
    if [ "$LOCAL" != "$REMOTE" ] && [ "$REMOTE" != "unknown" ]; then
        log "🆕 New changes detected, pulling..."
        
        # Stash any local changes
        git stash push -m "Auto-stash before pull $(date)" 2>/dev/null || true
        
        # Pull the latest changes
        if git pull origin "$BRANCH" 2>/dev/null; then
            log "✅ Successfully pulled latest changes"
            
            # Trigger service restart
            touch /tmp/restart-services
            log "🔄 Triggered service restart"
            return 0
        else
            log "❌ Failed to pull changes"
            return 1
        fi
    else
        log "📝 No new changes"
        return 1
    fi
}

# Initial setup
cd /app || {
    log "❌ Failed to change to /app directory"
    exit 1
}

# Set up git config
git config --global --add safe.directory /app 2>/dev/null || true
git config user.name "${GIT_USER_NAME:-openvibe-watcher}" 2>/dev/null || true
git config user.email "${GIT_USER_EMAIL:-watcher@openvibe.local}" 2>/dev/null || true

# Ensure we're on the correct branch (with error handling)
if ! git checkout "$BRANCH" 2>/dev/null; then
    log "⚠️  Failed to checkout branch $BRANCH, trying to create it"
    if ! git checkout -b "$BRANCH" "origin/$BRANCH" 2>/dev/null; then
        log "❌ Failed to create/checkout branch $BRANCH, continuing anyway"
    fi
fi

log "✅ Git watcher initialized on branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"

# Main polling loop with error recovery
while true; do
    # Try to pull changes, but don't exit on failure
    pull_changes 2>/dev/null || true
    
    # Sleep with interruption handling
    sleep "$POLL_INTERVAL" || {
        log "🛑 Git watcher interrupted, exiting"
        exit 0
    }
done