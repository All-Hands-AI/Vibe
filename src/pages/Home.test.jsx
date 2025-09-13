import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import Home from './Home'

// Mock fetch globally
global.fetch = vi.fn()

describe('Home', () => {
  beforeEach(() => {
    // Reset fetch mock before each test
    fetch.mockClear()
    
    // Mock successful API responses
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Hello from the API!', endpoint: '/api/hello' })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'healthy', service: 'OpenVibe Backend' })
      })
  })

  it('renders the hero section', async () => {
    render(<Home />)
    
    expect(screen.getByText('Welcome to OpenVibe')).toBeInTheDocument()
    expect(screen.getByText('Your React App is Running with Python Backend!')).toBeInTheDocument()
    
    // Wait for backend connection test to complete
    await waitFor(() => {
      expect(screen.getByText('🔗 Backend Connection Test')).toBeInTheDocument()
    })
  })

  it('renders hero buttons', () => {
    render(<Home />)
    
    expect(screen.getByRole('button', { name: 'Get Started' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Learn More' })).toBeInTheDocument()
  })

  it('renders features section', () => {
    render(<Home />)
    
    expect(screen.getByText('Features')).toBeInTheDocument()
    
    // Check for updated feature cards
    expect(screen.getByText('🐍 Full-Stack')).toBeInTheDocument()
    expect(screen.getByText('⚡ Fast')).toBeInTheDocument()
    expect(screen.getByText('🔧 Modern')).toBeInTheDocument()
    expect(screen.getByText('🚀 Deploy Ready')).toBeInTheDocument()
  })

  it('renders feature descriptions', () => {
    render(<Home />)
    
    expect(screen.getByText('React frontend with Python Flask backend - complete full-stack solution')).toBeInTheDocument()
    expect(screen.getByText('Built with Vite for lightning-fast development and builds')).toBeInTheDocument()
    expect(screen.getByText('Latest React features with hooks, context, and modern JavaScript')).toBeInTheDocument()
    expect(screen.getByText('Single Docker container with nginx proxy - ready for Fly.io deployment')).toBeInTheDocument()
  })

  it('displays backend connection test results', async () => {
    render(<Home />)
    
    // Initially shows connecting state
    expect(screen.getByText('🔄 Connecting to backend...')).toBeInTheDocument()
    
    // Wait for API calls to complete and results to display
    await waitFor(() => {
      expect(screen.getByText(/Hello API:/)).toBeInTheDocument()
      expect(screen.getByText(/Health Check:/)).toBeInTheDocument()
    })
    
    // Check that fetch was called with correct endpoints
    expect(fetch).toHaveBeenCalledWith('/api/hello')
    expect(fetch).toHaveBeenCalledWith('/api/health')
  })
})