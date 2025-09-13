# 📊 Logging Guide for OpenVibe on Fly.io

## Overview

The OpenVibe backend now includes comprehensive logging to help debug API key validation issues and monitor application behavior. This guide shows you how to view and analyze these logs on Fly.io.

## 🔍 Viewing Logs on Fly.io

### 1. Real-time Log Streaming

To view live logs as they happen:

```bash
fly logs
```

This will show logs from all instances of your app in real-time.

### 2. View Recent Logs

To see the last 100 log entries:

```bash
fly logs --lines 100
```

### 3. Filter Logs by Time

View logs from the last hour:
```bash
fly logs --since 1h
```

View logs from the last 30 minutes:
```bash
fly logs --since 30m
```

View logs from a specific time:
```bash
fly logs --since "2025-09-13T10:00:00Z"
```

### 4. Filter by Log Level

View only error logs:
```bash
fly logs | grep ERROR
```

View only warning and error logs:
```bash
fly logs | grep -E "(WARNING|ERROR)"
```

### 5. Follow Logs for Debugging

To continuously monitor logs while testing:
```bash
fly logs -f
```

Then in another terminal, test your API key validation to see real-time feedback.

## 📋 Log Format and Emojis

Our logs use emojis to make them easy to scan:

- 🚀 **Startup events** - Server starting, initialization
- 📍 **Endpoint access** - Route access logs
- 🔑 **API key operations** - Setting/checking keys
- 🔍 **Validation process** - API key validation steps
- 📡 **External API calls** - Responses from Anthropic, GitHub, Fly.io
- ✅ **Success events** - Successful validations
- ❌ **Error events** - Validation failures, errors
- ⚠️ **Warning events** - Non-critical issues
- 💥 **Exception events** - Caught exceptions
- 📊 **Status reports** - Summary information

## 🐛 Debugging API Key Issues

### Step 1: Start Log Monitoring

```bash
fly logs -f | grep -E "(🪰|Fly|fly)"
```

This filters for Fly.io-related logs only.

### Step 2: Test Your API Key

Use the setup window or make a direct API call:

```bash
curl -X POST https://your-app.fly.dev/integrations/fly \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your-fly-token-here"}'
```

### Step 3: Analyze the Logs

Look for these log patterns:

**Successful Validation:**
```
🪰 Validating Fly.io API key (length: 64)
🔍 Token prefix check - has valid prefix: true
✅ Found valid prefix: fo1_...
🔑 Using FlyV1 authentication format
🔍 Making test request to Fly.io API...
📡 Fly.io API response: 200
✅ Fly.io token validated successfully
```

**Failed Validation:**
```
🪰 Validating Fly.io API key (length: 32)
🔍 Token prefix check - has valid prefix: true
✅ Found valid prefix: fo1_...
🔑 Using FlyV1 authentication format
🔍 Making test request to Fly.io API...
📡 Fly.io API response: 401
❌ Fly.io authentication failed (401)
```

**Format Issues:**
```
🪰 Validating Fly.io API key (length: 8)
❌ Fly.io token too short or empty
```

## 🔧 Advanced Logging Commands

### View Logs from Specific Instance

If you have multiple instances:
```bash
fly logs --instance <instance-id>
```

### Export Logs to File

```bash
fly logs --since 1h > debug-logs.txt
```

### Search for Specific Patterns

```bash
# Find all API key validation attempts
fly logs | grep "Validating.*API key"

# Find all failed validations
fly logs | grep "❌.*validation failed"

# Find all successful validations
fly logs | grep "✅.*validated successfully"
```

## 📈 Log Analysis Tips

### 1. Check Token Format

Look for logs like:
```
🔍 Token prefix check - has valid prefix: false
❌ No valid prefix and token too short for personal token
```

This indicates your token doesn't match expected Fly.io formats.

### 2. Check Authentication Method

Look for:
```
🔑 Using FlyV1 authentication format
```
or
```
🔑 Using Bearer authentication format
```

Org tokens (fo1_*) should use FlyV1, personal tokens should use Bearer.

### 3. Check API Response

Look for the HTTP status code:
```
📡 Fly.io API response: 404
```

- **200**: Success
- **401**: Authentication failed (bad token)
- **403**: Authenticated but no permission (token might be valid but limited)
- **404**: Endpoint not found (might still be valid token)

## 🚨 Common Issues and Solutions

### Issue: "404 page not found"

**Log Pattern:**
```
📡 Fly.io API response: 404
⚠️ Fly.io API returned 404, accepting as valid due to format check
```

**Solution:** This is actually OK! The token format is valid, and 404 might just mean you don't have apps or the endpoint has limited access.

### Issue: "401 Unauthorized"

**Log Pattern:**
```
📡 Fly.io API response: 401
❌ Fly.io authentication failed (401)
```

**Solution:** Your token is invalid or expired. Generate a new one:
```bash
fly tokens create org --name "openvibe-setup"
```

### Issue: "Token too short"

**Log Pattern:**
```
❌ Fly.io token too short or empty
```

**Solution:** Make sure you copied the complete token. Fly.io org tokens are typically 60+ characters.

## 📱 Mobile/Remote Monitoring

You can also view logs from the Fly.io dashboard:

1. Go to https://fly.io/dashboard
2. Select your app
3. Click on "Monitoring" tab
4. View logs in the web interface

## 🔄 Log Rotation and Retention

Fly.io automatically manages log rotation. Logs are typically retained for:
- **Real-time logs**: Last 24 hours
- **Historical logs**: Up to 7 days (varies by plan)

For longer retention, consider setting up log forwarding to external services like:
- Papertrail
- Loggly
- Datadog
- CloudWatch

## 🎯 Quick Debug Checklist

When debugging API key issues:

1. ✅ **Start log monitoring**: `fly logs -f`
2. ✅ **Test the key**: Use setup window or curl
3. ✅ **Check token length**: Should be 60+ chars for org tokens
4. ✅ **Verify prefix**: Should start with `fo1_` for org tokens
5. ✅ **Check auth method**: Should use `FlyV1` for org tokens
6. ✅ **Analyze API response**: 200/403/404 are acceptable, 401 means invalid
7. ✅ **Generate new token if needed**: `fly tokens create org`

## 📞 Getting Help

If you're still having issues:

1. **Capture logs**: `fly logs --since 1h > issue-logs.txt`
2. **Include token prefix**: Share first 4 characters (e.g., "fo1_")
3. **Include error patterns**: Copy relevant log lines
4. **Check Fly.io status**: https://status.fly.io/

---

**Happy debugging! 🐛✨**