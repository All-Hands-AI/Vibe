#!/bin/bash

# Startup script that configures services based on environment variables
# Handles both production and development modes

set -e

SUPERVISOR_CONF="/etc/supervisor/conf.d/supervisord.conf"

echo "Starting OpenVibe services..."
echo "PULL_FROM_BRANCH: ${PULL_FROM_BRANCH:-not set}"

# Create the supervisor configuration based on environment
cat > "$SUPERVISOR_CONF" << 'EOF'
[supervisord]
nodaemon=true
user=root
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid

EOF

# Check if we're in development mode (PULL_FROM_BRANCH is set)
if [ -n "$PULL_FROM_BRANCH" ]; then
    echo "Configuring for DEVELOPMENT mode with hot-reload"
    
    # Install Node.js in the final stage for development
    if ! command -v node &> /dev/null; then
        echo "Installing Node.js for development mode..."
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        apt-get update -qq && apt-get install -y nodejs
    fi
    
    # Ensure npm dependencies are installed
    cd /app
    if [ ! -d "node_modules" ]; then
        echo "Installing npm dependencies..."
        npm install
    fi
    
    # Create development supervisor configuration
    cat >> "$SUPERVISOR_CONF" << 'EOF'
[program:git-watcher]
command=/usr/local/bin/git-watcher.sh
autostart=true
autorestart=true
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
environment=PULL_FROM_BRANCH="%(ENV_PULL_FROM_BRANCH)s"

[program:service-restarter]
command=/usr/local/bin/service-restarter.sh
autostart=true
autorestart=true
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0

[program:vite-dev]
command=npm run dev
directory=/app
autostart=true
autorestart=true
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
environment=HOST="0.0.0.0",PORT="3000"

[program:flask-dev]
command=python3 -m flask run --host=0.0.0.0 --port=8000 --debug
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
environment=FLASK_APP="app.py",FLASK_ENV="development",FLASK_DEBUG="1"

EOF

    # Create restart trigger file
    touch /tmp/restart-services
    
else
    echo "Configuring for PRODUCTION mode"
    
    # Create production supervisor configuration
    cat >> "$SUPERVISOR_CONF" << 'EOF'
[program:nginx]
command=nginx -g "daemon off;"
autostart=true
autorestart=true
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0

[program:backend]
command=python3 -m gunicorn --bind 0.0.0.0:8000 --workers 2 app:app
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
environment=PORT=8000

EOF
fi

echo "Supervisor configuration created:"
cat "$SUPERVISOR_CONF"

# Start supervisor
exec /usr/bin/supervisord -c "$SUPERVISOR_CONF"