import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import App from './App'

// Mock fetch globally for App tests too
global.fetch = vi.fn()

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
}
global.localStorage = localStorageMock

// Mock UUID utility
vi.mock('./utils/uuid', () => ({
  getUserUUID: () => 'test-uuid-12345',
  generateUUID: () => 'test-uuid-12345',
  clearUserUUID: vi.fn(),
}))

describe('App', () => {
  beforeEach(() => {
    // Reset fetch mock before each test
    fetch.mockClear()
    localStorageMock.getItem.mockClear()
    localStorageMock.setItem.mockClear()
    localStorageMock.removeItem.mockClear()
  })

  it('shows loading screen initially', () => {
    // Mock API calls that will fail (no setup)
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

    render(<App />)
    
    // Should show loading screen initially
    expect(screen.getByText('Initializing OpenVibe...')).toBeInTheDocument()
  })

  it('shows setup window when API keys are not configured', async () => {
    // Mock API calls that will fail (no setup)
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

    render(<App />)
    
    // Wait for setup window to appear
    await waitFor(() => {
      expect(screen.getByText('🚀 Welcome to OpenVibe')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Please configure your API keys to get started')).toBeInTheDocument()
    expect(screen.getByLabelText(/Anthropic API Key/)).toBeInTheDocument()
    expect(screen.getByLabelText(/GitHub API Key/)).toBeInTheDocument()
    expect(screen.getByLabelText(/Fly.io API Key/)).toBeInTheDocument()
  })

  it('renders main app when all API keys are configured', async () => {
    // Mock successful API responses (all keys valid)
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
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ apps: [], count: 0 })
      })

    render(<App />)
    
    // Wait for main app to load by checking for the Apps page content
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'OpenHands Vibe 🤙' })).toBeInTheDocument()
    })
    
    // Wait for the apps to finish loading
    await waitFor(() => {
      expect(screen.getByText('No apps yet. Create your first app above!')).toBeInTheDocument()
    })
    
    // Check for apps page content (default route is now Apps)
    expect(screen.getByText('Create New App')).toBeInTheDocument()
    expect(screen.getByText('Your Apps')).toBeInTheDocument()
  })

  it('renders with theme provider', () => {
    // Mock API calls that will fail (no setup)
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

    const { container } = render(<App />)
    
    // Check that theme class is applied
    expect(container.querySelector('.app-theme-dark')).toBeInTheDocument()
  })
})