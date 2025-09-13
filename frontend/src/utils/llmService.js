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
 * @returns {Promise<{success: boolean, error?: string}>} - Result with success status and optional error message
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
      let errorMessage = `Reset failed with status ${response.status}`
      try {
        const errorData = await response.json()
        if (errorData.error) {
          errorMessage = errorData.error
        }
      } catch {
        // If we can't parse JSON, use the status text
        errorMessage = `Reset failed: ${response.status} ${response.statusText}`
      }
      console.error('❌ Failed to reset LLM:', errorMessage)
      return { success: false, error: errorMessage }
    }

    const data = await response.json()
    console.log('✅ LLM reset successfully:', data.message)
    
    // Verify that the LLM is actually ready after reset
    console.log('🔍 Verifying LLM readiness after reset...')
    const isReady = await checkLLMReady(appSlug, riffSlug)
    
    if (!isReady) {
      console.error('❌ LLM reset succeeded but LLM is still not ready')
      return { 
        success: false, 
        error: 'Reset completed but LLM is still not ready. Please try again or check your API keys.' 
      }
    }
    
    console.log('✅ LLM reset and verification successful')
    return { success: true }
  } catch (error) {
    console.error('❌ Error resetting LLM:', error)
    return { success: false, error: `Network error: ${error.message}` }
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
  let consecutiveErrors = 0
  const maxConsecutiveErrors = 3

  const poll = async () => {
    if (!isPolling) return

    try {
      const isReady = await checkLLMReady(appSlug, riffSlug)
      consecutiveErrors = 0 // Reset error count on success
      
      // Only call callback if readiness state changed
      if (isReady !== lastReadyState) {
        lastReadyState = isReady
        onReadyChange(isReady)
      }
    } catch (error) {
      consecutiveErrors++
      console.error(`❌ Polling error (${consecutiveErrors}/${maxConsecutiveErrors}):`, error)
      
      // If we have too many consecutive errors, assume LLM is not ready
      if (consecutiveErrors >= maxConsecutiveErrors && lastReadyState !== false) {
        lastReadyState = false
        onReadyChange(false)
      }
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