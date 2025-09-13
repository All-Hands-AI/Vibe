#!/bin/bash

# Simplified service restarter script
# Monitors for restart triggers and handles dependency updates

RESTART_TRIGGER="/tmp/restart-services"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SERVICE-RESTARTER: $1"
}

log "🔄 Service restarter starting..."

# Function to restart development services
restart_services() {
    log "🔄 Restarting development services..."
    
    # Check if package.json changed and update dependencies
    if git diff --name-only HEAD~1 HEAD 2>/dev/null | grep -q "package.json\|package-lock.json"; then
        log "📦 Package files changed, updating npm dependencies..."
        cd /app && npm install 2>/dev/null || log "⚠️  Failed to update npm dependencies"
    fi
    
    # Check if Python dependencies changed
    if git diff --name-only HEAD~1 HEAD 2>/dev/null | grep -q "backend/pyproject.toml"; then
        log "🐍 Python dependencies changed, updating..."
        cd /app/backend && {
            uv pip compile pyproject.toml -o requirements.txt 2>/dev/null && \
            uv pip install --system -r requirements.txt 2>/dev/null && \
            rm requirements.txt
        } || log "⚠️  Failed to update Python dependencies"
        cd /app
    fi
    
    log "✅ Services restarted"
}

# Monitor for restart trigger with simple polling
while true; do
    if [ -f "$RESTART_TRIGGER" ]; then
        # Get the modification time to avoid duplicate restarts
        CURRENT_TIME=$(stat -c %Y "$RESTART_TRIGGER" 2>/dev/null || echo "0")
        LAST_TIME=$(cat /tmp/last-restart-time 2>/dev/null || echo "0")
        
        if [ "$CURRENT_TIME" != "$LAST_TIME" ]; then
            restart_services
            echo "$CURRENT_TIME" > /tmp/last-restart-time
        fi
    fi
    
    # Sleep with interruption handling
    sleep 10 || {
        log "🛑 Service restarter interrupted, exiting"
        exit 0
    }
done