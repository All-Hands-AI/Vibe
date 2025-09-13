# OpenVibe Backend Logging Standards

This document outlines the centralized logging approach used in the OpenVibe backend.

## Overview

OpenVibe uses a simplified, centralized logging format that provides clean, readable logs while maintaining consistency across all modules.

## Logging Format

The backend uses a simplified format configured in `app.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname).1s %(message)s",
    stream=sys.stdout,
)
```

This format shows:
- **First letter of log level**: `D` (Debug), `I` (Info), `W` (Warning), `E` (Error)
- **Message**: The actual log message

Example output:
```
I 🚀 OpenVibe Backend System Information
I 📡 GET /api/apps/test-app/riffs/test-riff/ready (user: 12345678)
E ❌ Failed to create LLM for riff: Invalid API key
```

## Usage Guidelines

### 1. Getting a Logger

Always use the centralized logging utility:

```python
from utils.logging import get_logger

logger = get_logger(__name__)
```

**Don't use:**
```python
import logging
logger = logging.getLogger(__name__)  # Old pattern
```

### 2. API Request/Response Logging

Use the standardized API logging functions:

```python
from utils.logging import log_api_request, log_api_response

# Log incoming request
log_api_request(logger, "GET", "/api/apps/test/riffs", user_uuid)

# Log response
log_api_response(logger, "GET", "/api/apps/test/riffs", 200, user_uuid)
```

### 3. System Information Logging

Use the centralized system info function:

```python
from utils.logging import log_system_info

log_system_info(logger)
```

### 4. Standard Log Messages

Follow these emoji conventions for consistency:

- **🚀** - System startup/initialization
- **📡** - API requests
- **✅** - Success operations
- **❌** - Errors/failures
- **⚠️** - Warnings
- **🔍** - Debug/investigation
- **🔄** - Processing/operations
- **📊** - Statistics/data
- **🗑️** - Cleanup/deletion
- **🤖** - AI/LLM operations
- **📁** - File system operations
- **🌍** - Environment information
- **🐍** - Python/system information

## Architecture

### Centralized Configuration

- **Primary config**: `app.py` - Sets up the basic logging configuration
- **Utility module**: `utils/logging.py` - Provides helper functions and consistent patterns
- **Module loggers**: Each module uses `get_logger(__name__)` to inherit the central config

### Benefits

1. **Consistency**: All modules use the same format automatically
2. **Maintainability**: Changes to logging format only need to be made in one place
3. **Readability**: Simplified format gives more space to actual messages
4. **Standardization**: Common patterns for API logging and system info

### File Structure

```
backend/
├── app.py                 # Main logging configuration
├── utils/
│   └── logging.py        # Centralized logging utilities
├── routes/
│   ├── riffs.py          # Uses centralized logging
│   ├── apps.py           # Uses centralized logging
│   └── ...
└── storage/
    └── ...               # All modules use centralized logging
```

## Migration Guide

To update existing modules to use centralized logging:

1. **Replace import:**
   ```python
   # Old
   import logging
   logger = logging.getLogger(__name__)
   
   # New
   from utils.logging import get_logger
   logger = get_logger(__name__)
   ```

2. **Use standardized API logging:**
   ```python
   # Old
   logger.info(f"GET /api/endpoint - Processing request")
   
   # New
   from utils.logging import log_api_request
   log_api_request(logger, "GET", "/api/endpoint", user_uuid)
   ```

3. **Follow emoji conventions:**
   ```python
   # Good
   logger.info("✅ Operation completed successfully")
   logger.error("❌ Failed to process request")
   
   # Avoid
   logger.info("Operation completed successfully")
   logger.error("Failed to process request")
   ```

## Testing

The logging utilities can be tested independently:

```python
from utils.logging import get_logger, log_api_request

logger = get_logger('test')
logger.info("✅ Test message")
log_api_request(logger, "GET", "/test", "user123")
```

## Best Practices

1. **Use appropriate log levels**: Debug for development, Info for normal operations, Warning for issues, Error for failures
2. **Include context**: User IDs, operation details, relevant data
3. **Be consistent**: Use the same patterns across similar operations
4. **Keep messages concise**: The simplified format gives more space, but don't waste it
5. **Use emojis**: They make logs more readable and easier to scan
6. **Include timing for long operations**: Help with performance debugging

## Examples

### Good Logging Examples

```python
# API operations
log_api_request(logger, "POST", "/api/apps/test/riffs", user_uuid)
logger.info(f"🤖 Creating LLM for riff: {riff_name}")
logger.info(f"✅ Riff created successfully: {riff_name}")
log_api_response(logger, "POST", "/api/apps/test/riffs", 201, user_uuid)

# Error handling
logger.error(f"❌ Failed to create LLM: {error_message}")
logger.warning(f"⚠️ No Anthropic token found for user {user_uuid[:8]}")

# Debug information
logger.debug(f"🔍 Checking AgentLoop for key: {key}")
logger.debug(f"📊 Current stats: {stats}")
```

### Avoid These Patterns

```python
# Don't use old logging import
import logging
logger = logging.getLogger(__name__)

# Don't create custom formatters
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(message)s')

# Don't use inconsistent message formats
logger.info("Request received")  # Missing emoji and context
logger.error("Error occurred")   # Too vague
```