# Docker Debugging Guide

This guide helps troubleshoot the enhanced Docker setup for OpenVibe.

## 🔍 Quick Debugging Commands

### Check Container Logs
```bash
# View startup logs
docker logs <container-name>

# Follow logs in real-time
docker logs -f <container-name>

# View last 50 lines
docker logs --tail 50 <container-name>
```

### Check Running Services
```bash
# Check what's listening on ports
docker exec <container-name> netstat -tuln

# Check running processes
docker exec <container-name> ps aux

# Check specific processes
docker exec <container-name> ps aux | grep -E "(nginx|python|node)"
```

### Interactive Debugging
```bash
# Get a shell inside the container
docker exec -it <container-name> /bin/bash

# Check service status manually
docker exec <container-name> curl -s http://localhost:80
docker exec <container-name> curl -s http://localhost:8000
```

## 🚨 Common Issues and Solutions

### Issue: "instance refused connection" on port 80

**Symptoms:**
- Fly.io shows connection refused errors
- Port 80 not accessible

**Debug Steps:**
1. Check if nginx is running:
   ```bash
   docker exec <container> ps aux | grep nginx
   ```

2. Check if nginx is listening on port 80:
   ```bash
   docker exec <container> netstat -tuln | grep :80
   ```

3. Test nginx configuration:
   ```bash
   docker exec <container> nginx -t
   ```

4. Check nginx error logs:
   ```bash
   docker exec <container> cat /var/log/nginx/error.log
   ```

**Common Solutions:**
- Ensure nginx config is valid
- Check if another process is using port 80
- Verify nginx is binding to 0.0.0.0:80, not 127.0.0.1:80

### Issue: Services not starting in development mode

**Symptoms:**
- Development servers not accessible
- Git watcher not working

**Debug Steps:**
1. Check if Node.js was installed:
   ```bash
   docker exec <container> node --version
   ```

2. Check if npm dependencies are installed:
   ```bash
   docker exec <container> ls -la /app/node_modules
   ```

3. Check development server processes:
   ```bash
   docker exec <container> ps aux | grep -E "(vite|flask)"
   ```

**Common Solutions:**
- Ensure PULL_FROM_BRANCH environment variable is set
- Check if Node.js installation completed successfully
- Verify npm dependencies were installed

### Issue: Git watcher not pulling changes

**Symptoms:**
- Code changes not reflected in container
- No git activity in logs

**Debug Steps:**
1. Check git watcher process:
   ```bash
   docker exec <container> ps aux | grep git-watcher
   ```

2. Check git configuration:
   ```bash
   docker exec <container> git config --list
   ```

3. Test git connectivity:
   ```bash
   docker exec <container> git fetch origin
   ```

**Common Solutions:**
- Verify git credentials are configured
- Check network connectivity to git repository
- Ensure branch exists in remote repository

## 📊 Startup Sequence

### Production Mode (default)
1. Container starts with start-services.sh
2. Nginx configuration is tested
3. Nginx starts on port 80
4. Gunicorn starts on port 8000
5. Services are monitored and auto-restarted

### Development Mode (PULL_FROM_BRANCH set)
1. Container starts with start-services.sh
2. Node.js is installed (if not present)
3. npm dependencies are installed
4. Git watcher starts in background
5. Service restarter starts in background
6. Flask dev server starts on port 8000
7. Vite dev server starts on port 3000
8. All services are monitored and auto-restarted

## 🔧 Environment Variables for Debugging

```bash
# Enable development mode
PULL_FROM_BRANCH=main

# Adjust git polling (less frequent for debugging)
GIT_POLL_INTERVAL=300

# Set git credentials
GIT_USER_NAME=debug-user
GIT_USER_EMAIL=debug@example.com
```

## 📝 Log Patterns to Look For

### Successful Production Startup
```
🚀 OpenVibe Container Starting
🏭 PRODUCTION MODE
✅ Nginx configuration is valid
✅ Nginx started (PID: 123)
✅ Gunicorn started (PID: 456)
✅ Nginx is listening on port 80
✅ Gunicorn is listening on port 8000
🎉 Production services started successfully!
```

### Successful Development Startup
```
🚀 OpenVibe Container Starting
🔧 DEVELOPMENT MODE ENABLED
✅ Node.js installed: v20.x.x
✅ npm dependencies installed
✅ Git watcher started (PID: 123)
✅ Service restarter started (PID: 456)
✅ Flask backend started (PID: 789)
✅ Vite dev server started (PID: 101)
🎉 Development mode services started!
```

## 🆘 Emergency Debugging

If the container is completely unresponsive:

1. **Check container status:**
   ```bash
   docker ps -a
   ```

2. **Get container logs:**
   ```bash
   docker logs <container-name>
   ```

3. **Try to get a shell:**
   ```bash
   docker exec -it <container-name> /bin/bash
   ```

4. **If shell doesn't work, inspect the container:**
   ```bash
   docker inspect <container-name>
   ```

5. **Restart with debugging:**
   ```bash
   docker run -it --rm <image-name> /bin/bash
   ```

This will give you an interactive shell to debug the startup process manually.