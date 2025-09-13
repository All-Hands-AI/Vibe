import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import App from './App'

// Mock fetch globally
global.fetch = vi.fn()

describe('App', () => {
  beforeEach(() => {
    fetch.mockClear()
  })

  it('shows loading state initially', () => {
    // Mock fetch to never resolve to test loading state
    fetch.mockImplementation(() => new Promise(() => {}))
    
    render(<App />)
    
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('shows setup window when API keys are not configured', async () => {
    // Mock API response indicating no keys are configured
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ anthropic: false, github: false, fly: false })
    })
    
    render(<App />)
    
    await waitFor(() => {
      expect(screen.getByText('🚀 Welcome to OpenVibe!')).toBeInTheDocument()
      expect(screen.getByText('Please configure your API keys to get started. All keys are required.')).toBeInTheDocument()
    })
  })

  it('shows main app when all API keys are configured', async () => {
    // Mock API response indicating all keys are configured
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ anthropic: true, github: true, fly: true })
    })
    
    render(<App />)
    
    await waitFor(() => {
      // Should show main app content instead of setup window
      expect(screen.queryByText('🚀 Welcome to OpenVibe!')).not.toBeInTheDocument()
      expect(screen.getByRole('link', { name: 'OpenVibe' })).toBeInTheDocument()
    })
  })

  it('shows setup window when API check fails', async () => {
    // Mock API failure (backend not available)
    fetch.mockRejectedValueOnce(new Error('Network error'))
    
    render(<App />)
    
    await waitFor(() => {
      expect(screen.getByText('🚀 Welcome to OpenVibe!')).toBeInTheDocument()
    })
  })
})