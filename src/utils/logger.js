/**
 * Enhanced logging utilities for debugging in production
 */

// Log levels
const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3
}

// Current log level (can be controlled via environment)
const CURRENT_LOG_LEVEL = LOG_LEVELS.DEBUG

/**
 * Enhanced console logger with timestamps and context
 */
class Logger {
  constructor(context = 'App') {
    this.context = context
  }

  _log(level, message, ...args) {
    if (LOG_LEVELS[level] < CURRENT_LOG_LEVEL) return

    const timestamp = new Date().toISOString()
    const prefix = `[${timestamp}] [${this.context}] [${level}]`
    
    switch (level) {
      case 'DEBUG':
        console.debug(prefix, message, ...args)
        break
      case 'INFO':
        console.info(prefix, message, ...args)
        break
      case 'WARN':
        console.warn(prefix, message, ...args)
        break
      case 'ERROR':
        console.error(prefix, message, ...args)
        break
    }
  }

  debug(message, ...args) {
    this._log('DEBUG', message, ...args)
  }

  info(message, ...args) {
    this._log('INFO', message, ...args)
  }

  warn(message, ...args) {
    this._log('WARN', message, ...args)
  }

  error(message, ...args) {
    this._log('ERROR', message, ...args)
  }

  // Log system information
  logSystemInfo() {
    this.info('🚀 OpenVibe Frontend Starting...')
    this.info('='.repeat(50))
    
    // Browser information
    this.info('🌐 Browser Information:')
    this.info(`  - User Agent: ${navigator.userAgent}`)
    this.info(`  - Platform: ${navigator.platform}`)
    this.info(`  - Language: ${navigator.language}`)
    this.info(`  - Online: ${navigator.onLine}`)
    this.info(`  - Cookies Enabled: ${navigator.cookieEnabled}`)
    
    // Window information
    this.info('🖥️ Window Information:')
    this.info(`  - Inner Width: ${window.innerWidth}`)
    this.info(`  - Inner Height: ${window.innerHeight}`)
    this.info(`  - Screen Width: ${window.screen.width}`)
    this.info(`  - Screen Height: ${window.screen.height}`)
    this.info(`  - Location: ${window.location.href}`)
    this.info(`  - Protocol: ${window.location.protocol}`)
    this.info(`  - Host: ${window.location.host}`)
    
    // Storage information
    this.info('💾 Storage Information:')
    this.info(`  - localStorage available: ${typeof localStorage !== 'undefined'}`)
    this.info(`  - sessionStorage available: ${typeof sessionStorage !== 'undefined'}`)
    
    if (typeof localStorage !== 'undefined') {
      try {
        const testKey = '__storage_test__'
        localStorage.setItem(testKey, 'test')
        localStorage.removeItem(testKey)
        this.info('  - localStorage working: true')
      } catch (e) {
        this.warn('  - localStorage working: false', e.message)
      }
    }
    
    // Environment information
    this.info('🌍 Environment Information:')
    this.info(`  - NODE_ENV: ${process.env.NODE_ENV || 'unknown'}`)
    this.info(`  - Development Mode: ${import.meta.env?.DEV || false}`)
    
    // Network information
    if ('connection' in navigator) {
      const connection = navigator.connection
      this.info('📡 Network Information:')
      this.info(`  - Effective Type: ${connection.effectiveType}`)
      this.info(`  - Downlink: ${connection.downlink}`)
      this.info(`  - RTT: ${connection.rtt}`)
    }
    
    this.info('='.repeat(50))
  }

  // Log API request/response
  logApiCall(method, url, requestData, response, error) {
    if (error) {
      this.error(`❌ API ${method} ${url} failed:`, error)
    } else {
      this.info(`📡 API ${method} ${url}:`, {
        request: requestData,
        response: response,
        status: response?.status
      })
    }
  }

  // Log component lifecycle
  logComponentLifecycle(componentName, event, data) {
    this.debug(`🔄 ${componentName} ${event}:`, data)
  }
}

// Create default logger instance
export const logger = new Logger('OpenVibe')

// Create logger for specific contexts
export const createLogger = (context) => new Logger(context)

// Export for global use
window.OpenVibeLogger = logger