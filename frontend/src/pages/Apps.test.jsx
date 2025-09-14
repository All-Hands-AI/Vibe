import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import Apps from './Apps'

// Mock fetch globally
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
  generateUUID: () => 'test-uuid-12345',
  getUserUUID: () => 'test-uuid-12345',
}))

// Helper function to render with router
const renderWithRouter = (component) => {
  return render(
    <MemoryRouter>
      {component}
    </MemoryRouter>
  )
}

describe('Apps', () => {
  beforeEach(() => {
    // Reset mocks before each test
    fetch.mockClear()
    localStorageMock.getItem.mockClear()
    localStorageMock.setItem.mockClear()
    localStorageMock.removeItem.mockClear()
    
    // Default localStorage behavior
    localStorageMock.getItem.mockReturnValue('test-uuid-12345')
  })

  it('renders apps page with header and form', async () => {
    // Mock successful apps fetch
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ apps: [], count: 0 })
    })

    renderWithRouter(<Apps />)
    
    // Check header content
    expect(screen.getByText('🤙 OpenHands Vibe')).toBeInTheDocument()
    
    // Check form elements
    expect(screen.getByText('Create New App')).toBeInTheDocument()
    expect(screen.getByLabelText('> App Name:')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Enter app name')).toBeInTheDocument()
    expect(screen.getByText('Create App')).toBeInTheDocument()
    
    // Wait for apps to load
    await waitFor(() => {
      expect(screen.getByText('Your Apps')).toBeInTheDocument()
    })
  })

  it('displays empty state when no apps exist', async () => {
    // Mock empty apps response
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ apps: [], count: 0 })
    })

    renderWithRouter(<Apps />)
    
    await waitFor(() => {
      expect(screen.getByText('No apps yet. Create your first app above!')).toBeInTheDocument()
    })
  })

  it('displays apps list when apps exist', async () => {
    // Mock apps response with data
    const mockApps = [
      {
        name: 'Test App',
        slug: 'test-app',
        github_url: 'https://github.com/user/test-app',
        created_at: '2025-01-01T00:00:00.000Z'
      },
      {
        name: 'Another App',
        slug: 'another-app',
        github_url: 'https://github.com/user/another-app',
        created_at: '2025-01-02T00:00:00.000Z'
      }
    ]

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ apps: mockApps, count: 2 })
    })

    renderWithRouter(<Apps />)
    
    await waitFor(() => {
      expect(screen.getByText('Test App')).toBeInTheDocument()
      expect(screen.getByText('Another App')).toBeInTheDocument()
    })
    
    // Check that cards are clickable (wrapped in links)
    const appLinks = screen.getAllByRole('link')
    const appCardLinks = appLinks.filter(link => 
      link.getAttribute('href')?.startsWith('/apps/')
    )
    expect(appCardLinks).toHaveLength(2)
    
    // Check that loading status is displayed (since detailed data isn't available in tests)
    expect(screen.getAllByText('Loading status...')).toHaveLength(2)
    
    // Verify that GitHub info and created date are NOT displayed
    expect(screen.queryByText('GitHub repository available')).not.toBeInTheDocument()
    expect(screen.queryByText(/Created:/)).not.toBeInTheDocument()
  })

  it('shows slug preview when typing app name', async () => {
    // Mock apps fetch
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ apps: [], count: 0 })
    })

    renderWithRouter(<Apps />)
    
    const nameInput = screen.getByLabelText('> App Name:')
    
    // Type in the input
    fireEvent.change(nameInput, { target: { value: 'My Awesome App!' } })
    
    // Check slug preview appears
    await waitFor(() => {
      expect(screen.getByText('Slug:')).toBeInTheDocument()
      expect(screen.getByText('my-awesome-app')).toBeInTheDocument()
    })
  })

  it('enables create button when app name is entered', async () => {
    // Mock apps fetch
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ apps: [], count: 0 })
    })

    renderWithRouter(<Apps />)
    
    const nameInput = screen.getByLabelText('> App Name:')
    const createButton = screen.getByText('Create App')
    
    // Initially disabled
    expect(createButton).toBeDisabled()
    
    // Type in the input
    fireEvent.change(nameInput, { target: { value: 'Test App' } })
    
    // Should be enabled now
    await waitFor(() => {
      expect(createButton).not.toBeDisabled()
    })
  })

  it('handles app creation successfully', async () => {
    // Mock apps fetch
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ apps: [], count: 0 })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message: 'App created successfully',
          app: {
            id: 1,
            name: 'Test App',
            slug: 'test-app',
            github_url: 'https://github.com/user/test-app',
            created_at: '2025-01-01T00:00:00.000Z'
          }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ apps: [], count: 0 })
      })

    renderWithRouter(<Apps />)
    
    const nameInput = screen.getByLabelText('> App Name:')
    const createButton = screen.getByText('Create App')
    
    // Fill form and submit
    fireEvent.change(nameInput, { target: { value: 'Test App' } })
    fireEvent.click(createButton)
    
    // Check success message appears
    await waitFor(() => {
      expect(screen.getByText('App "Test App" created successfully!')).toBeInTheDocument()
    })
    
    // Check that form was reset
    expect(nameInput.value).toBe('')
  })

  it('handles app creation error', async () => {
    // Mock apps fetch and failed creation
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ apps: [], count: 0 })
      })
      .mockResolvedValueOnce({
        ok: false,
        json: async () => ({ error: 'GitHub API key is required. Please set it up in integrations.' })
      })

    renderWithRouter(<Apps />)
    
    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Create New App')).toBeInTheDocument()
    })
    
    const nameInput = screen.getByLabelText('> App Name:')
    const createButton = screen.getByText('Create App')
    
    // Fill form and submit
    fireEvent.change(nameInput, { target: { value: 'Test App' } })
    fireEvent.click(createButton)
    
    // Check error message appears
    await waitFor(() => {
      expect(screen.getByText('GitHub API key is required. Please set it up in integrations.')).toBeInTheDocument()
    }, { timeout: 5000 })
  })

  it('handles fetch error gracefully', async () => {
    // Mock fetch failure
    fetch.mockRejectedValueOnce(new Error('Network error'))

    renderWithRouter(<Apps />)
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load apps. Please try again.')).toBeInTheDocument()
    })
  })

  it('clears error when user starts typing', async () => {
    // Mock apps fetch and failed creation
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ apps: [], count: 0 })
      })
      .mockResolvedValueOnce({
        ok: false,
        json: async () => ({ error: 'Some error occurred' })
      })

    renderWithRouter(<Apps />)
    
    const nameInput = screen.getByLabelText('> App Name:')
    const createButton = screen.getByText('Create App')
    
    // Fill form and submit to trigger error
    fireEvent.change(nameInput, { target: { value: 'Test App' } })
    fireEvent.click(createButton)
    
    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText('Some error occurred')).toBeInTheDocument()
    })
    
    // Clear input and type again
    fireEvent.change(nameInput, { target: { value: '' } })
    fireEvent.change(nameInput, { target: { value: 'New App' } })
    
    // Error should be cleared
    await waitFor(() => {
      expect(screen.queryByText('Some error occurred')).not.toBeInTheDocument()
    })
  })
})