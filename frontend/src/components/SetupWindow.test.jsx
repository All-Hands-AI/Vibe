import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import SetupWindow from './SetupWindow'
import { SetupProvider } from '../context/SetupContext'

// Mock fetch
global.fetch = vi.fn()

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
}
global.localStorage = localStorageMock

// Mock UUID utility
vi.mock('../utils/uuid', () => ({
  getUserUUID: () => 'test-uuid-12345',
  generateUUID: () => 'test-uuid-12345',
  clearUserUUID: vi.fn(),
}))

// Helper function to render SetupWindow with providers
const renderSetupWindow = (props = {}) => {
  return render(
    <SetupProvider>
      <SetupWindow onSetupComplete={vi.fn()} {...props} />
    </SetupProvider>
  )
}

describe('SetupWindow', () => {
  const mockOnSetupComplete = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    fetch.mockClear()
    localStorageMock.getItem.mockClear()
    localStorageMock.setItem.mockClear()
    localStorageMock.removeItem.mockClear()
    
    // Mock initial setup check API calls (no keys found)
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ valid: false, message: 'Anthropic API key not set' })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ valid: false, message: 'GitHub API key not set' })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ valid: false, message: 'Fly API key not set' })
      })
  })

  test('renders setup window with all required fields', () => {
    renderSetupWindow({ onSetupComplete: mockOnSetupComplete })
    
    expect(screen.getByText('🚀 Welcome to OpenVibe')).toBeInTheDocument()
    expect(screen.getByText('Please configure your API keys to get started')).toBeInTheDocument()
    
    expect(screen.getByLabelText(/Anthropic API Key/)).toBeInTheDocument()
    expect(screen.getByLabelText(/GitHub API Key/)).toBeInTheDocument()
    expect(screen.getByLabelText(/Fly.io API Key/)).toBeInTheDocument()
    
    expect(screen.getByRole('button', { name: /Enter all API keys to continue/ })).toBeDisabled()
  })

  test('validates API key when input loses focus', async () => {
    // Add extra mock for the validation call
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ valid: true, message: 'Anthropic API key is valid' })
    })

    renderSetupWindow({ onSetupComplete: mockOnSetupComplete })
    
    const anthropicInput = screen.getByLabelText(/Anthropic API Key/)
    
    fireEvent.change(anthropicInput, { target: { value: 'sk-ant-test123' } })
    fireEvent.blur(anthropicInput)
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        '/api/integrations/anthropic',
        expect.objectContaining({
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'X-User-UUID': 'test-uuid-12345'
          },
          body: JSON.stringify({ 
            api_key: 'sk-ant-test123'
          })
        })
      )
    })
  })

  test('shows validation status icons', async () => {
    // Add extra mock for the validation call
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ valid: true, message: 'Anthropic API key is valid' })
    })

    renderSetupWindow({ onSetupComplete: mockOnSetupComplete })
    
    const anthropicInput = screen.getByLabelText(/Anthropic API Key/)
    
    fireEvent.change(anthropicInput, { target: { value: 'sk-ant-test123' } })
    fireEvent.blur(anthropicInput)
    
    await waitFor(() => {
      expect(screen.getByText('✅')).toBeInTheDocument()
      expect(screen.getByText('Anthropic API key is valid')).toBeInTheDocument()
    })
  })

  test('enables continue button when all keys are valid', async () => {
    // Mock successful validation for all three providers (in addition to initial setup checks)
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ valid: true, message: 'Anthropic API key is valid' })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ valid: true, message: 'GitHub API key is valid' })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ valid: true, message: 'Fly API key is valid' })
      })

    renderSetupWindow({ onSetupComplete: mockOnSetupComplete })
    
    const anthropicInput = screen.getByLabelText(/Anthropic API Key/)
    const githubInput = screen.getByLabelText(/GitHub API Key/)
    const flyInput = screen.getByLabelText(/Fly.io API Key/)
    
    // Fill and validate all inputs
    fireEvent.change(anthropicInput, { target: { value: 'sk-ant-test123' } })
    fireEvent.blur(anthropicInput)
    
    await waitFor(() => {
      expect(screen.getByText('Anthropic API key is valid')).toBeInTheDocument()
    })
    
    fireEvent.change(githubInput, { target: { value: 'ghp_test123' } })
    fireEvent.blur(githubInput)
    
    await waitFor(() => {
      expect(screen.getByText('GitHub API key is valid')).toBeInTheDocument()
    })
    
    fireEvent.change(flyInput, { target: { value: 'fo1_test123' } })
    fireEvent.blur(flyInput)
    
    await waitFor(() => {
      expect(screen.getByText('Fly API key is valid')).toBeInTheDocument()
    })
    
    // Button should now be enabled
    const continueButton = screen.getByRole('button', { name: /Continue to OpenVibe/ })
    expect(continueButton).toBeEnabled()
    
    // Clicking should call onSetupComplete
    fireEvent.click(continueButton)
    expect(mockOnSetupComplete).toHaveBeenCalled()
  })

  test('shows error message for invalid API key', async () => {
    // Add extra mock for the validation call
    fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ valid: false, message: 'Anthropic API key is invalid' })
    })

    renderSetupWindow({ onSetupComplete: mockOnSetupComplete })
    
    const anthropicInput = screen.getByLabelText(/Anthropic API Key/)
    
    fireEvent.change(anthropicInput, { target: { value: 'invalid-key' } })
    fireEvent.blur(anthropicInput)
    
    await waitFor(() => {
      expect(screen.getByText('❌')).toBeInTheDocument()
      expect(screen.getByText('Anthropic API key is invalid')).toBeInTheDocument()
    })
  })
})
