import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import SetupWindow from './SetupWindow'

// Mock fetch
global.fetch = vi.fn()

describe('SetupWindow', () => {
  beforeEach(() => {
    fetch.mockClear()
  })

  test('renders setup window with all required fields', () => {
    const mockOnSetupComplete = vi.fn()
    
    render(<SetupWindow onSetupComplete={mockOnSetupComplete} />)
    
    expect(screen.getByText('🚀 Welcome to OpenVibe!')).toBeInTheDocument()
    expect(screen.getByLabelText(/Anthropic API Key/)).toBeInTheDocument()
    expect(screen.getByLabelText(/GitHub API Key/)).toBeInTheDocument()
    expect(screen.getByLabelText(/Fly.io API Key/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Validate All Keys/ })).toBeInTheDocument()
  })

  test('validates API key on input blur', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ valid: true, message: 'Valid API key' })
    })

    const mockOnSetupComplete = vi.fn()
    render(<SetupWindow onSetupComplete={mockOnSetupComplete} />)
    
    const anthropicInput = screen.getByLabelText(/Anthropic API Key/)
    
    fireEvent.change(anthropicInput, { target: { value: 'sk-ant-test-key' } })
    fireEvent.blur(anthropicInput)
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:3001/integrations/anthropic',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ apiKey: 'sk-ant-test-key' })
        })
      )
    })
  })

  test('shows validation status icons', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ valid: true })
    })

    const mockOnSetupComplete = vi.fn()
    render(<SetupWindow onSetupComplete={mockOnSetupComplete} />)
    
    const anthropicInput = screen.getByLabelText(/Anthropic API Key/)
    
    fireEvent.change(anthropicInput, { target: { value: 'sk-ant-test-key' } })
    fireEvent.blur(anthropicInput)
    
    await waitFor(() => {
      expect(screen.getByText('✅')).toBeInTheDocument()
    })
  })

  test('shows error message for invalid API key', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ valid: false, error: 'Invalid API key' })
    })

    const mockOnSetupComplete = vi.fn()
    render(<SetupWindow onSetupComplete={mockOnSetupComplete} />)
    
    const anthropicInput = screen.getByLabelText(/Anthropic API Key/)
    
    fireEvent.change(anthropicInput, { target: { value: 'invalid-key' } })
    fireEvent.blur(anthropicInput)
    
    await waitFor(() => {
      expect(screen.getByText('Invalid API key')).toBeInTheDocument()
      expect(screen.getByText('❌')).toBeInTheDocument()
    })
  })

  test('enables submit button when all keys are valid', async () => {
    // Mock successful validation for all services
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ valid: true })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ valid: true })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ valid: true })
      })

    const mockOnSetupComplete = vi.fn()
    render(<SetupWindow onSetupComplete={mockOnSetupComplete} />)
    
    const anthropicInput = screen.getByLabelText(/Anthropic API Key/)
    const githubInput = screen.getByLabelText(/GitHub API Key/)
    const flyInput = screen.getByLabelText(/Fly.io API Key/)
    
    fireEvent.change(anthropicInput, { target: { value: 'sk-ant-test' } })
    fireEvent.blur(anthropicInput)
    
    await waitFor(() => expect(screen.getByText('✅')).toBeInTheDocument())
    
    fireEvent.change(githubInput, { target: { value: 'ghp-test' } })
    fireEvent.blur(githubInput)
    
    await waitFor(() => expect(screen.getAllByText('✅')).toHaveLength(2))
    
    fireEvent.change(flyInput, { target: { value: 'fo1-test' } })
    fireEvent.blur(flyInput)
    
    await waitFor(() => {
      expect(screen.getAllByText('✅')).toHaveLength(3)
      expect(screen.getByRole('button', { name: /Complete Setup/ })).not.toBeDisabled()
    })
  })
})