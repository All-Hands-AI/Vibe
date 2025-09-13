/**
 * UUID utility functions for user identification
 */

/**
 * Generate a UUID v4
 * @returns {string} UUID string
 */
export function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0
    const v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

/**
 * Get or create user UUID from localStorage
 * @returns {string} User UUID
 */
export function getUserUUID() {
  const STORAGE_KEY = 'openvibe_user_uuid'
  
  // Try to get existing UUID from localStorage
  let uuid = localStorage.getItem(STORAGE_KEY)
  
  // If no UUID exists, generate a new one
  if (!uuid) {
    uuid = generateUUID()
    localStorage.setItem(STORAGE_KEY, uuid)
    console.log('🆔 Generated new user UUID:', uuid)
  } else {
    console.log('🆔 Using existing user UUID:', uuid)
  }
  
  return uuid
}

/**
 * Clear user UUID (for testing/reset purposes)
 */
export function clearUserUUID() {
  const STORAGE_KEY = 'openvibe_user_uuid'
  localStorage.removeItem(STORAGE_KEY)
  console.log('🗑️ Cleared user UUID')
}