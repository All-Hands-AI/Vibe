#!/bin/bash

# Service restarter script that monitors for restart triggers
# and restarts development servers when code changes are detected

set -e

RESTART_TRIGGER="/tmp/restart-services"

echo "Service restarter starting..."

# Function to restart development services
restart_services() {
    echo "$(date): Restarting development services..."
    
    # Install/update npm dependencies if package.json changed
    if git diff --name-only HEAD~1 HEAD | grep -q "package.json\|package-lock.json"; then
        echo "$(date): Package files changed, updating dependencies..."
        npm install
    fi
    
    # Install/update Python dependencies if pyproject.toml changed
    if git diff --name-only HEAD~1 HEAD | grep -q "backend/pyproject.toml"; then
        echo "$(date): Python dependencies changed, updating..."
        cd backend && uv pip compile pyproject.toml -o requirements.txt && uv pip install --system -r requirements.txt && rm requirements.txt
        cd ..
    fi
    
    # Restart supervisor services
    supervisorctl restart all || true
    
    echo "$(date): Services restarted"
}

# Monitor for restart trigger
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
    
    sleep 5
done