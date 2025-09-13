#!/bin/bash

# Simplified startup script with extensive debugging
# Prioritizes getting basic services running first

set -e

# Immediate startup indicator
echo "🚨 START-SERVICES.SH IS EXECUTING 🚨"
echo "Script path: $0"
echo "Arguments: $@"

# Check if supervisor is already running and stop it
if pgrep supervisord > /dev/null; then
    echo "⚠️  Found running supervisord, stopping it..."
    pkill supervisord || true
    sleep 2
fi

# Check for any existing services that might conflict
echo "📋 Checking for existing services..."
ps aux | grep -E "(nginx|gunicorn|vite|flask)" | grep -v grep || echo "No conflicting services found"

# Emergency fallback: if nothing is listening on port 80, start nginx immediately
if ! netstat -tuln 2>/dev/null | grep ":80 " > /dev/null; then
    echo "🚨 EMERGENCY: Nothing listening on port 80, starting nginx immediately..."
    nginx -g "daemon off;" &
    EMERGENCY_NGINX_PID=$!
    echo "🚨 Emergency nginx started (PID: $EMERGENCY_NGINX_PID)"
fi

echo "========================================="
echo "🚀 OpenVibe Container Starting"
echo "========================================="
echo "Timestamp: $(date)"
echo "PULL_FROM_BRANCH: ${PULL_FROM_BRANCH:-not set}"
echo "Working directory: $(pwd)"
echo "User: $(whoami)"
echo "Environment variables:"
env | grep -E "(PULL_FROM_BRANCH|FLASK|NODE|GIT)" | sort || echo "No relevant env vars found"
echo "========================================="

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if a service is running
check_service() {
    local service=$1
    local port=$2
    log "Checking if $service is listening on port $port..."
    if netstat -tuln | grep ":$port " > /dev/null 2>&1; then
        log "✅ $service is listening on port $port"
        return 0
    else
        log "❌ $service is NOT listening on port $port"
        return 1
    fi
}

# Check if we're in development mode
log "🔍 Checking mode: PULL_FROM_BRANCH='${PULL_FROM_BRANCH:-}'"
if [ -n "$PULL_FROM_BRANCH" ]; then
    log "🔧 DEVELOPMENT MODE ENABLED"
    log "Branch to watch: $PULL_FROM_BRANCH"
    
    # Install Node.js if not present
    NODE_AVAILABLE=false
    if ! command -v node &> /dev/null; then
        log "📦 Installing Node.js for development mode..."
        if curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get update -qq && apt-get install -y nodejs; then
            log "✅ Node.js installed: $(node --version)"
            log "✅ npm version: $(npm --version)"
            NODE_AVAILABLE=true
        else
            log "❌ Failed to install Node.js - will run in backend-only mode"
            NODE_AVAILABLE=false
        fi
    else
        log "✅ Node.js already available: $(node --version)"
        NODE_AVAILABLE=true
    fi
    
    # Install npm dependencies if Node.js is available
    VITE_AVAILABLE=false
    if [ "$NODE_AVAILABLE" = true ]; then
        cd /app
        if [ ! -d "node_modules" ] || [ ! -f "node_modules/.bin/vite" ]; then
            log "📦 Installing npm dependencies..."
            if npm install; then
                log "✅ npm dependencies installed"
                if [ -f "node_modules/.bin/vite" ]; then
                    log "✅ Vite binary: $(ls -la node_modules/.bin/vite)"
                    VITE_AVAILABLE=true
                else
                    log "❌ Vite binary not found after npm install"
                    VITE_AVAILABLE=false
                fi
            else
                log "❌ Failed to install npm dependencies - Vite will not be available"
                VITE_AVAILABLE=false
            fi
        else
            log "✅ npm dependencies already installed"
            if [ -f "node_modules/.bin/vite" ]; then
                log "✅ Vite binary confirmed: $(ls -la node_modules/.bin/vite)"
                VITE_AVAILABLE=true
            else
                log "❌ Vite binary missing despite node_modules existing"
                VITE_AVAILABLE=false
            fi
        fi
    else
        log "⚠️  Skipping npm dependencies - Node.js not available"
    fi
    
    # Start git watcher in background (optional)
    if [ "${DISABLE_GIT_WATCHER:-false}" != "true" ]; then
        log "🔄 Starting git watcher..."
        /usr/local/bin/git-watcher.sh &
        GIT_WATCHER_PID=$!
        log "✅ Git watcher started (PID: $GIT_WATCHER_PID)"
        
        # Start service restarter in background
        log "🔄 Starting service restarter..."
        /usr/local/bin/service-restarter.sh &
        SERVICE_RESTARTER_PID=$!
        log "✅ Service restarter started (PID: $SERVICE_RESTARTER_PID)"
    else
        log "⚠️  Git watcher disabled via DISABLE_GIT_WATCHER=true"
    fi
    
    # Start Flask backend in background
    log "🐍 Starting Flask backend..."
    cd /app/backend
    export FLASK_APP=app.py
    export FLASK_ENV=development
    export FLASK_DEBUG=1
    python3 -m flask run --host=0.0.0.0 --port=8000 --debug &
    FLASK_PID=$!
    log "✅ Flask backend started (PID: $FLASK_PID)"
    
    # Start Vite dev server in background (if available)
    VITE_PID=""
    NGINX_PID=""
    if [ "$VITE_AVAILABLE" = true ]; then
        log "⚡ Starting Vite dev server..."
        cd /app
        # Use npx to ensure we use the local vite binary
        npx vite --host 0.0.0.0 --port 3000 &
        VITE_PID=$!
        log "✅ Vite dev server started (PID: $VITE_PID)"
    else
        log "⚠️  Vite dev server not available - starting nginx for pre-built React app"
        nginx -g "daemon off;" &
        NGINX_PID=$!
        log "✅ Nginx started as fallback (PID: $NGINX_PID)"
    fi
    
    # Wait a bit for services to start
    sleep 5
    
    # Check services
    if [ "$VITE_AVAILABLE" = true ]; then
        check_service "Vite" "3000" || log "⚠️  Vite dev server may still be starting"
    else
        check_service "Nginx" "80" || log "⚠️  Nginx may still be starting"
    fi
    check_service "Flask" "8000" || log "⚠️  Flask backend may still be starting"
    
    log "🎉 Development mode services started!"
    log "📝 Access URLs:"
    if [ "$VITE_AVAILABLE" = true ]; then
        log "   - React (Vite): http://localhost:3000"
    else
        log "   - React (pre-built): http://localhost:80 (via nginx)"
    fi
    log "   - API (Flask): http://localhost:8000"
    
    # Keep the container running and monitor processes
    while true; do
        # Check if critical processes are still running
        if [ "$VITE_AVAILABLE" = true ] && [ -n "$VITE_PID" ]; then
            if ! kill -0 $VITE_PID 2>/dev/null; then
                log "❌ Vite process died, restarting..."
                cd /app && npx vite --host 0.0.0.0 --port 3000 &
                VITE_PID=$!
                log "✅ Vite restarted (PID: $VITE_PID)"
            fi
        elif [ -n "$NGINX_PID" ]; then
            if ! kill -0 $NGINX_PID 2>/dev/null; then
                log "❌ Nginx process died, restarting..."
                nginx -g "daemon off;" &
                NGINX_PID=$!
                log "✅ Nginx restarted (PID: $NGINX_PID)"
            fi
        fi
        
        if ! kill -0 $FLASK_PID 2>/dev/null; then
            log "❌ Flask process died, restarting..."
            cd /app/backend && python3 -m flask run --host=0.0.0.0 --port=8000 --debug &
            FLASK_PID=$!
            log "✅ Flask restarted (PID: $FLASK_PID)"
        fi
        
        sleep 30
    done
    
else
    log "🏭 PRODUCTION MODE"
    log "📋 Current processes before starting:"
    ps aux | head -10 || log "ps command failed"
    
    # Test nginx configuration
    log "🔍 Testing nginx configuration..."
    if nginx -t; then
        log "✅ Nginx configuration is valid"
    else
        log "❌ Nginx configuration test failed"
        log "📋 Nginx config:"
        cat /etc/nginx/sites-available/default 2>/dev/null || log "Could not read nginx config"
        log "📋 Nginx error log:"
        cat /var/log/nginx/error.log 2>/dev/null || log "No nginx error log found"
        # Don't exit, try to continue
    fi
    
    # Start nginx in background
    log "🌐 Starting nginx..."
    if nginx -g "daemon off;" & then
        NGINX_PID=$!
        log "✅ Nginx started (PID: $NGINX_PID)"
    else
        log "❌ Failed to start nginx"
        exit 1
    fi
    
    # Start Python backend in background
    log "🐍 Starting Python backend..."
    cd /app/backend
    if python3 -m gunicorn --bind 0.0.0.0:8000 --workers 2 app:app & then
        GUNICORN_PID=$!
        log "✅ Gunicorn started (PID: $GUNICORN_PID)"
    else
        log "❌ Failed to start gunicorn"
        exit 1
    fi
    
    # Wait a bit for services to start
    log "⏳ Waiting for services to initialize..."
    sleep 10
    
    # Check services
    log "🔍 Checking if services are listening on ports..."
    netstat -tuln | grep -E ":80|:8000" || log "No services found on expected ports"
    
    if check_service "Nginx" "80"; then
        log "✅ Nginx is listening on port 80"
    else
        log "❌ Nginx failed to start on port 80"
        log "📋 Nginx processes:"
        ps aux | grep nginx || log "No nginx processes found"
        log "📋 Nginx error log:"
        tail -20 /var/log/nginx/error.log 2>/dev/null || log "No nginx error log found"
        # Don't exit, continue to monitor
    fi
    
    if check_service "Gunicorn" "8000"; then
        log "✅ Gunicorn is listening on port 8000"
    else
        log "❌ Gunicorn failed to start on port 8000"
        log "📋 Gunicorn processes:"
        ps aux | grep gunicorn || log "No gunicorn processes found"
    fi
    
    log "🎉 Production mode startup completed!"
    log "📝 Access URL: http://localhost:80"
    
    # Keep the container running and monitor processes
    while true; do
        # Check if critical processes are still running
        if [ -n "$NGINX_PID" ] && ! kill -0 $NGINX_PID 2>/dev/null; then
            log "❌ Nginx process died, restarting..."
            nginx -g "daemon off;" &
            NGINX_PID=$!
            log "✅ Nginx restarted (PID: $NGINX_PID)"
        fi
        
        if [ -n "$GUNICORN_PID" ] && ! kill -0 $GUNICORN_PID 2>/dev/null; then
            log "❌ Gunicorn process died, restarting..."
            cd /app/backend && python3 -m gunicorn --bind 0.0.0.0:8000 --workers 2 app:app &
            GUNICORN_PID=$!
            log "✅ Gunicorn restarted (PID: $GUNICORN_PID)"
        fi
        
        sleep 30
    done
fi