/**
 * Agent service utilities for interacting with agent status and control endpoints
 */

import { getUserUUID } from './uuid'

/**
 * Get the current status of an agent
 * @param {string} appSlug - The app slug
 * @param {string} riffSlug - The riff slug
 * @returns {Promise<Object>} Agent status object
 */
export async function getAgentStatus(appSlug, riffSlug) {
  try {
    const uuid = getUserUUID()
    const response = await fetch(`/api/apps/${appSlug}/riffs/${riffSlug}/status`, {
      method: 'GET',
      headers: {
        'X-User-UUID': uuid,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.error || `HTTP ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('❌ Failed to get agent status:', error)
    throw error
  }
}

/**
 * Play/resume an agent
 * @param {string} appSlug - The app slug
 * @param {string} riffSlug - The riff slug
 * @returns {Promise<Object>} Response object
 */
export async function playAgent(appSlug, riffSlug) {
  try {
    const uuid = getUserUUID()
    const response = await fetch(`/api/apps/${appSlug}/riffs/${riffSlug}/play`, {
      method: 'POST',
      headers: {
        'X-User-UUID': uuid,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.error || `HTTP ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('❌ Failed to play agent:', error)
    throw error
  }
}

/**
 * Pause an agent
 * @param {string} appSlug - The app slug
 * @param {string} riffSlug - The riff slug
 * @returns {Promise<Object>} Response object
 */
export async function pauseAgent(appSlug, riffSlug) {
  try {
    const uuid = getUserUUID()
    const response = await fetch(`/api/apps/${appSlug}/riffs/${riffSlug}/pause`, {
      method: 'POST',
      headers: {
        'X-User-UUID': uuid,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.error || `HTTP ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('❌ Failed to pause agent:', error)
    throw error
  }
}

/**
 * Reset an agent
 * @param {string} appSlug - The app slug
 * @param {string} riffSlug - The riff slug
 * @returns {Promise<Object>} Response object
 */
export async function resetAgent(appSlug, riffSlug) {
  try {
    const uuid = getUserUUID()
    const response = await fetch(`/api/apps/${appSlug}/riffs/${riffSlug}/reset`, {
      method: 'POST',
      headers: {
        'X-User-UUID': uuid,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.error || `HTTP ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('❌ Failed to reset agent:', error)
    throw error
  }
}

/**
 * Start polling for agent status updates
 * @param {string} appSlug - The app slug
 * @param {string} riffSlug - The riff slug
 * @param {Function} callback - Callback function to handle status updates
 * @param {number} interval - Polling interval in milliseconds (default: 5000)
 * @returns {Function} Stop polling function
 */
export function startAgentStatusPolling(appSlug, riffSlug, callback, interval = 5000) {
  let isPolling = true
  let timeoutId = null

  const poll = async () => {
    if (!isPolling) return

    try {
      const status = await getAgentStatus(appSlug, riffSlug)
      callback(status)
    } catch (error) {
      console.error('❌ Agent status polling error:', error)
      // Call callback with error status
      callback({
        status: 'error',
        error: error.message,
        is_running: false,
        has_active_task: false,
        event_count: 0,
        // Keep agent_status for backward compatibility
        agent_status: 'error'
      })
    }

    if (isPolling) {
      timeoutId = setTimeout(poll, interval)
    }
  }

  // Start polling immediately
  poll()

  // Return stop function
  return () => {
    isPolling = false
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutId = null
    }
  }
}

/**
 * Get a human-readable status description
 * @param {Object} status - Agent status object
 * @returns {string} Human-readable status
 */
export function getStatusDescription(status) {
  if (!status) return 'Unknown'
  
  // Handle special backend status values
  if (status.status === 'not_found') {
    return 'Not Found'
  }
  
  if (status.status === 'not_initialized') {
    return 'Not Initialized'
  }
  
  // Primary status field is now the SDK status (transparent passthrough)
  switch (status.status) {
    case 'idle':
      // Check if it has any activity
      if (status.event_count <= 1) {
        return 'Idle (No Messages)'
      }
      return 'Idle'
    case 'running':
      return 'Running'
    case 'paused':
      return 'Paused'
    case 'waiting_for_confirmation':
      return 'Waiting for Confirmation'
    case 'finished':
      return 'Finished'
    case 'error':
      return 'Error'
    case 'stuck':
      return 'Stuck'
    default:
      // Fallback for any unknown status
      return status.status || 'Unknown'
  }
}

/**
 * Get status color class for UI styling
 * @param {Object} status - Agent status object
 * @returns {string} CSS color class
 */
export function getStatusColor(status) {
  if (!status) return 'text-gray-400'
  
  // Handle special backend status values
  if (status.status === 'not_found' || status.status === 'not_initialized') {
    return 'text-gray-400'
  }
  
  // Primary status field is now the SDK status (transparent passthrough)
  switch (status.status) {
    case 'idle':
      return 'text-gray-400'
    case 'running':
      return 'text-neon-green'
    case 'paused':
      return 'text-yellow-400'
    case 'waiting_for_confirmation':
      return 'text-blue-400'
    case 'finished':
      return 'text-green-400'
    case 'error':
      return 'text-red-400'
    case 'stuck':
      return 'text-orange-400'
    default:
      return 'text-gray-400'
  }
}

/**
 * Check if agent can be played/resumed
 * @param {Object} status - Agent status object
 * @returns {boolean} Whether agent can be played
 */
export function canPlayAgent(status) {
  if (!status) return false
  
  // Primary status field is now the SDK status (transparent passthrough)
  return status.status === 'paused' || 
         (status.status === 'idle' && status.event_count <= 1)
}

/**
 * Check if agent can be paused
 * @param {Object} status - Agent status object
 * @returns {boolean} Whether agent can be paused
 */
export function canPauseAgent(status) {
  if (!status) return false
  
  // Primary status field is now the SDK status (transparent passthrough)
  return status.status === 'running' || 
         status.status === 'waiting_for_confirmation'
}

/**
 * Check if agent is currently running
 * @param {Object} status - Agent status object
 * @returns {boolean} Whether agent is running
 */
export function isAgentRunning(status) {
  if (!status) return false
  
  // Primary status field is now the SDK status (transparent passthrough)
  return status.status === 'running' || 
         status.status === 'waiting_for_confirmation'
}

/**
 * Check if agent is finished
 * @param {Object} status - Agent status object
 * @returns {boolean} Whether agent is finished
 */
export function isAgentFinished(status) {
  if (!status) return false
  
  // Primary status field is now the SDK status (transparent passthrough)
  return status.status === 'finished'
}

/**
 * Check if agent is paused
 * @param {Object} status - Agent status object
 * @returns {boolean} Whether agent is paused
 */
export function isAgentPaused(status) {
  if (!status) return false
  
  // Primary status field is now the SDK status (transparent passthrough)
  return status.status === 'paused'
}