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
        agent_finished: false,
        agent_paused: false,
        agent_waiting_for_confirmation: false,
        thread_alive: false,
        running: false
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
  
  if (status.status === 'error') {
    return 'Error'
  }
  
  if (status.status === 'not_found') {
    return 'Not Found'
  }
  
  if (status.status === 'not_initialized') {
    return 'Not Initialized'
  }
  
  if (status.agent_finished) {
    return 'Finished'
  }
  
  if (status.agent_paused) {
    return 'Paused'
  }
  
  if (status.agent_waiting_for_confirmation) {
    return 'Waiting for Confirmation'
  }
  
  if (status.running) {
    return 'Ready'
  }
  
  // Agent is idle - check if it has any activity
  if (status.has_recent_activity === false || status.event_count <= 1) {
    return 'Idle (No Messages)'
  }
  
  return 'Idle'
}

/**
 * Get status color class for UI styling
 * @param {Object} status - Agent status object
 * @returns {string} CSS color class
 */
export function getStatusColor(status) {
  if (!status) return 'text-gray-400'
  
  if (status.status === 'error') {
    return 'text-red-400'
  }
  
  if (status.status === 'not_found' || status.status === 'not_initialized') {
    return 'text-gray-400'
  }
  
  if (status.agent_finished) {
    return 'text-green-400'
  }
  
  if (status.agent_paused) {
    return 'text-yellow-400'
  }
  
  if (status.agent_waiting_for_confirmation) {
    return 'text-blue-400'
  }
  
  if (status.running) {
    return 'text-neon-green'
  }
  
  return 'text-gray-400'
}