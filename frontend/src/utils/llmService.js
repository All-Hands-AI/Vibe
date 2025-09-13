/**
 * LLM Service for checking readiness and resetting LLM objects
 */

import { getUserUUID } from './uuid'

/**
 * Check if LLM is ready for a specific riff
 * @param {string} appSlug - The app slug
 * @param {string} riffSlug - The riff slug
 * @returns {Promise<boolean>} - True if LLM is ready, false otherwise
 */
export async function checkLLMReady(appSlug, riffSlug) {
  try {
    const uuid = getUserUUID()
    const headers = {
      'X-User-UUID': uuid
    }

    const response = await fetch(`/api/apps/${appSlug}/riffs/${riffSlug}/ready`, {
      method: 'GET',
      headers
    })

    if (!response.ok) {
      console.error('❌ Failed to check LLM readiness:', response.status)
      return false
    }

    const data = await response.json()
    return data.ready === true
  } catch (error) {
    console.error('❌ Error checking LLM readiness:', error)
    return false
  }
}

/**
 * Reset the LLM for a specific riff
 * @param {string} appSlug - The app slug
 * @param {string} riffSlug - The riff slug
 * @returns {Promise<boolean>} - True if reset was successful, false otherwise
 */
export async function resetLLM(appSlug, riffSlug) {
  try {
    const uuid = getUserUUID()
    const headers = {
      'X-User-UUID': uuid,
      'Content-Type': 'application/json'
    }

    const response = await fetch(`/api/apps/${appSlug}/riffs/${riffSlug}/reset`, {
      method: 'POST',
      headers
    })

    if (!response.ok) {
      console.error('❌ Failed to reset LLM:', response.status)
      return false
    }

    const data = await response.json()
    console.log('✅ LLM reset successfully:', data.message)
    return true
  } catch (error) {
    console.error('❌ Error resetting LLM:', error)
    return false
  }
}

/**
 * Start polling for LLM readiness
 * @param {string} appSlug - The app slug
 * @param {string} riffSlug - The riff slug
 * @param {function} onReadyChange - Callback function called when readiness changes
 * @param {number} intervalMs - Polling interval in milliseconds (default: 5000)
 * @returns {function} - Function to stop polling
 */
export function startLLMPolling(appSlug, riffSlug, onReadyChange, intervalMs = 5000) {
  let isPolling = true
  let lastReadyState = null

  const poll = async () => {
    if (!isPolling) return

    const isReady = await checkLLMReady(appSlug, riffSlug)
    
    // Only call callback if readiness state changed
    if (isReady !== lastReadyState) {
      lastReadyState = isReady
      onReadyChange(isReady)
    }

    if (isPolling) {
      setTimeout(poll, intervalMs)
    }
  }

  // Start polling immediately
  poll()

  // Return function to stop polling
  return () => {
    isPolling = false
  }
}