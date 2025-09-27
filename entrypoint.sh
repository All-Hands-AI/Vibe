#!/bin/bash

# Generate .htpasswd file from environment variables
if [ -n "$BASIC_AUTH_PASSWORD" ]; then
    echo "Generating .htpasswd file with username: ${BASIC_AUTH_USERNAME:-openhands}"
    htpasswd -cb /etc/nginx/.htpasswd "${BASIC_AUTH_USERNAME:-openhands}" "$BASIC_AUTH_PASSWORD"
else
    echo "ERROR: BASIC_AUTH_PASSWORD environment variable is not set"
    exit 1
fi

# Start supervisor to manage both nginx and python backend
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf