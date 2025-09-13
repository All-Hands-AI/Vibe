import { describe, it, expect, beforeEach, vi } from 'vitest'
import { generateUUID, getUserUUID, clearUserUUID } from './uuid'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
}
global.localStorage = localStorageMock

describe('UUID utilities', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks()
    localStorageMock.getItem.mockClear()
    localStorageMock.setItem.mockClear()
    localStorageMock.removeItem.mockClear()
  })

  describe('generateUUID', () => {
    it('generates a valid UUID v4', () => {
      const uuid = generateUUID()
      
      // Check UUID format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
      expect(uuid).toMatch(uuidRegex)
      expect(uuid).toHaveLength(36)
    })

    it('generates unique UUIDs', () => {
      const uuid1 = generateUUID()
      const uuid2 = generateUUID()
      
      expect(uuid1).not.toBe(uuid2)
    })
  })

  describe('getUserUUID', () => {
    it('generates new UUID when none exists in localStorage', () => {
      localStorageMock.getItem.mockReturnValue(null)
      
      const uuid = getUserUUID()
      
      expect(localStorageMock.getItem).toHaveBeenCalledWith('user_uuid') // legacy cleanup check
      expect(localStorageMock.getItem).toHaveBeenCalledWith('openvibe_user_uuid')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('openvibe_user_uuid', uuid)
      expect(uuid).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i)
    })

    it('returns existing UUID from localStorage', () => {
      const existingUUID = 'existing-uuid-12345'
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'user_uuid') return null // no legacy key
        if (key === 'openvibe_user_uuid') return existingUUID
        return null
      })
      
      const uuid = getUserUUID()
      
      expect(localStorageMock.getItem).toHaveBeenCalledWith('user_uuid') // legacy cleanup check
      expect(localStorageMock.getItem).toHaveBeenCalledWith('openvibe_user_uuid')
      expect(localStorageMock.setItem).not.toHaveBeenCalled()
      expect(uuid).toBe(existingUUID)
    })

    it('generates new UUID when localStorage returns empty string', () => {
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'user_uuid') return null // no legacy key
        if (key === 'openvibe_user_uuid') return ''
        return null
      })
      
      const uuid = getUserUUID()
      
      expect(localStorageMock.getItem).toHaveBeenCalledWith('user_uuid') // legacy cleanup check
      expect(localStorageMock.getItem).toHaveBeenCalledWith('openvibe_user_uuid')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('openvibe_user_uuid', uuid)
      expect(uuid).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i)
    })

    it('cleans up legacy user_uuid when present', () => {
      const legacyUUID = 'legacy-uuid-12345'
      const currentUUID = 'current-uuid-67890'
      
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'user_uuid') return legacyUUID // legacy key exists
        if (key === 'openvibe_user_uuid') return currentUUID
        return null
      })
      
      const uuid = getUserUUID()
      
      expect(localStorageMock.getItem).toHaveBeenCalledWith('user_uuid') // legacy cleanup check
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('user_uuid') // legacy cleanup
      expect(localStorageMock.getItem).toHaveBeenCalledWith('openvibe_user_uuid')
      expect(uuid).toBe(currentUUID)
    })
  })

  describe('clearUserUUID', () => {
    it('removes UUID from localStorage (including legacy entries)', () => {
      clearUserUUID()
      
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('openvibe_user_uuid')
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('user_uuid')
    })
  })

  describe('integration tests', () => {
    it('maintains UUID persistence across multiple calls', () => {
      // First call - no UUID exists
      localStorageMock.getItem.mockReturnValue(null)
      const uuid1 = getUserUUID()
      
      // Second call - UUID exists (mock both legacy check and main check)
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'user_uuid') return null // no legacy key
        if (key === 'openvibe_user_uuid') return uuid1
        return null
      })
      const uuid2 = getUserUUID()
      
      expect(uuid1).toBe(uuid2)
      expect(localStorageMock.setItem).toHaveBeenCalledTimes(1)
    })

    it('generates new UUID after clearing', () => {
      // Set up existing UUID
      const existingUUID = 'existing-uuid-12345'
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === 'user_uuid') return null // no legacy key
        if (key === 'openvibe_user_uuid') return existingUUID
        return null
      })
      const uuid1 = getUserUUID()
      
      // Clear UUID
      clearUserUUID()
      
      // Get new UUID
      localStorageMock.getItem.mockReturnValue(null)
      const uuid2 = getUserUUID()
      
      expect(uuid1).toBe(existingUUID)
      expect(uuid2).not.toBe(existingUUID)
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('openvibe_user_uuid')
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('user_uuid')
    })
  })
})