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
      
      expect(localStorageMock.getItem).toHaveBeenCalledWith('openvibe_user_uuid')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('openvibe_user_uuid', uuid)
      expect(uuid).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i)
    })

    it('returns existing UUID from localStorage', () => {
      const existingUUID = 'existing-uuid-12345'
      localStorageMock.getItem.mockReturnValue(existingUUID)
      
      const uuid = getUserUUID()
      
      expect(localStorageMock.getItem).toHaveBeenCalledWith('openvibe_user_uuid')
      expect(localStorageMock.setItem).not.toHaveBeenCalled()
      expect(uuid).toBe(existingUUID)
    })

    it('generates new UUID when localStorage returns empty string', () => {
      localStorageMock.getItem.mockReturnValue('')
      
      const uuid = getUserUUID()
      
      expect(localStorageMock.getItem).toHaveBeenCalledWith('openvibe_user_uuid')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('openvibe_user_uuid', uuid)
      expect(uuid).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i)
    })
  })

  describe('clearUserUUID', () => {
    it('removes UUID from localStorage', () => {
      clearUserUUID()
      
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('openvibe_user_uuid')
    })
  })

  describe('integration tests', () => {
    it('maintains UUID persistence across multiple calls', () => {
      // First call - no UUID exists
      localStorageMock.getItem.mockReturnValueOnce(null)
      const uuid1 = getUserUUID()
      
      // Second call - UUID exists
      localStorageMock.getItem.mockReturnValueOnce(uuid1)
      const uuid2 = getUserUUID()
      
      expect(uuid1).toBe(uuid2)
      expect(localStorageMock.setItem).toHaveBeenCalledTimes(1)
    })

    it('generates new UUID after clearing', () => {
      // Set up existing UUID
      const existingUUID = 'existing-uuid-12345'
      localStorageMock.getItem.mockReturnValueOnce(existingUUID)
      const uuid1 = getUserUUID()
      
      // Clear UUID
      clearUserUUID()
      
      // Get new UUID
      localStorageMock.getItem.mockReturnValueOnce(null)
      const uuid2 = getUserUUID()
      
      expect(uuid1).toBe(existingUUID)
      expect(uuid2).not.toBe(existingUUID)
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('openvibe_user_uuid')
    })
  })
})