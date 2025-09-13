#!/bin/bash

# Simplified startup script with extensive debugging
# Prioritizes getting basic services running first

set -e

echo "========================================="
echo "🚀 OpenVibe Container Starting"
echo "========================================="
echo "Timestamp: $(date)"
echo "PULL_FROM_BRANCH: ${PULL_FROM_BRANCH:-not set}"
echo "Working directory: $(pwd)"
echo "User: $(whoami)"
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
if [ -n "$PULL_FROM_BRANCH" ]; then
    log "🔧 DEVELOPMENT MODE ENABLED"
    log "Branch to watch: $PULL_FROM_BRANCH"
    
    # Install Node.js if not present
    if ! command -v node &> /dev/null; then
        log "📦 Installing Node.js for development mode..."
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash - || {
            log "❌ Failed to add Node.js repository"
            exit 1
        }
        apt-get update -qq && apt-get install -y nodejs || {
            log "❌ Failed to install Node.js"
            exit 1
        }
        log "✅ Node.js installed: $(node --version)"
    fi
    
    # Install npm dependencies
    cd /app
    if [ ! -d "node_modules" ]; then
        log "📦 Installing npm dependencies..."
        npm install || {
            log "❌ Failed to install npm dependencies"
            exit 1
        }
        log "✅ npm dependencies installed"
    fi
    
    # Start git watcher in background
    log "🔄 Starting git watcher..."
    /usr/local/bin/git-watcher.sh &
    GIT_WATCHER_PID=$!
    log "✅ Git watcher started (PID: $GIT_WATCHER_PID)"
    
    # Start service restarter in background
    log "🔄 Starting service restarter..."
    /usr/local/bin/service-restarter.sh &
    SERVICE_RESTARTER_PID=$!
    log "✅ Service restarter started (PID: $SERVICE_RESTARTER_PID)"
    
    # Start Flask backend in background
    log "🐍 Starting Flask backend..."
    cd /app/backend
    export FLASK_APP=app.py
    export FLASK_ENV=development
    export FLASK_DEBUG=1
    python3 -m flask run --host=0.0.0.0 --port=8000 --debug &
    FLASK_PID=$!
    log "✅ Flask backend started (PID: $FLASK_PID)"
    
    # Start Vite dev server in background
    log "⚡ Starting Vite dev server..."
    cd /app
    npm run dev &
    VITE_PID=$!
    log "✅ Vite dev server started (PID: $VITE_PID)"
    
    # Wait a bit for services to start
    sleep 5
    
    # Check services
    check_service "Vite" "3000" || log "⚠️  Vite dev server may still be starting"
    check_service "Flask" "8000" || log "⚠️  Flask backend may still be starting"
    
    log "🎉 Development mode services started!"
    log "📝 Access URLs:"
    log "   - React (Vite): http://localhost:3000"
    log "   - API (Flask): http://localhost:8000"
    
    # Keep the container running and monitor processes
    while true; do
        # Check if critical processes are still running
        if ! kill -0 $VITE_PID 2>/dev/null; then
            log "❌ Vite process died, restarting..."
            cd /app && npm run dev &
            VITE_PID=$!
        fi
        
        if ! kill -0 $FLASK_PID 2>/dev/null; then
            log "❌ Flask process died, restarting..."
            cd /app/backend && python3 -m flask run --host=0.0.0.0 --port=8000 --debug &
            FLASK_PID=$!
        fi
        
        sleep 30
    done
    
else
    log "🏭 PRODUCTION MODE"
    
    # Test nginx configuration
    log "🔍 Testing nginx configuration..."
    nginx -t || {
        log "❌ Nginx configuration test failed"
        log "📋 Nginx config:"
        cat /etc/nginx/sites-available/default
        exit 1
    }
    log "✅ Nginx configuration is valid"
    
    # Start nginx in background
    log "🌐 Starting nginx..."
    nginx -g "daemon off;" &
    NGINX_PID=$!
    log "✅ Nginx started (PID: $NGINX_PID)"
    
    # Start Python backend in background
    log "🐍 Starting Python backend..."
    cd /app/backend
    python3 -m gunicorn --bind 0.0.0.0:8000 --workers 2 app:app &
    GUNICORN_PID=$!
    log "✅ Gunicorn started (PID: $GUNICORN_PID)"
    
    # Wait a bit for services to start
    sleep 5
    
    # Check services
    check_service "Nginx" "80" || {
        log "❌ Nginx failed to start on port 80"
        log "📋 Nginx error log:"
        tail -20 /var/log/nginx/error.log 2>/dev/null || log "No nginx error log found"
        exit 1
    }
    
    check_service "Gunicorn" "8000" || {
        log "❌ Gunicorn failed to start on port 8000"
        exit 1
    }
    
    log "🎉 Production services started successfully!"
    log "📝 Access URL: http://localhost:80"
    
    # Keep the container running and monitor processes
    while true; do
        # Check if critical processes are still running
        if ! kill -0 $NGINX_PID 2>/dev/null; then
            log "❌ Nginx process died, restarting..."
            nginx -g "daemon off;" &
            NGINX_PID=$!
        fi
        
        if ! kill -0 $GUNICORN_PID 2>/dev/null; then
            log "❌ Gunicorn process died, restarting..."
            cd /app/backend && python3 -m gunicorn --bind 0.0.0.0:8000 --workers 2 app:app &
            GUNICORN_PID=$!
        fi
        
        sleep 30
    done
fi