/**
 * UUID utility functions for user identification
 */

// Storage key constant for user UUID
export const USER_UUID_STORAGE_KEY = 'openvibe_user_uuid'

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
  console.log('🆔 Getting user UUID...')
  console.log('🆔 STORAGE_KEY:', USER_UUID_STORAGE_KEY)
  console.log('🆔 localStorage available:', typeof localStorage !== 'undefined')
  
  // Try to get existing UUID from localStorage
  let uuid = localStorage.getItem(USER_UUID_STORAGE_KEY)
  console.log('🆔 Raw UUID from localStorage:', uuid)
  
  // If no UUID exists, generate a new one
  if (!uuid || uuid.trim() === '') {
    console.log('🆔 No valid UUID found, generating new one...')
    uuid = generateUUID()
    localStorage.setItem(USER_UUID_STORAGE_KEY, uuid)
    console.log('🆔 Generated new user UUID:', uuid)
    console.log('🆔 Saved to localStorage with key:', USER_UUID_STORAGE_KEY)
  } else {
    console.log('🆔 Using existing user UUID:', uuid)
  }
  
  // Verify it was saved correctly
  const verifyUuid = localStorage.getItem(USER_UUID_STORAGE_KEY)
  console.log('🆔 Verification - UUID in localStorage:', verifyUuid)
  
  return uuid
}

/**
 * Clear user UUID (for testing/reset purposes)
 */
export function clearUserUUID() {
  localStorage.removeItem(USER_UUID_STORAGE_KEY)
  console.log('🗑️ Cleared user UUID')
}