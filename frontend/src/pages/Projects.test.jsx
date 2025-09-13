import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import Projects from './Projects'

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

describe('Projects', () => {
  beforeEach(() => {
    // Reset mocks before each test
    fetch.mockClear()
    localStorageMock.getItem.mockClear()
    localStorageMock.setItem.mockClear()
    localStorageMock.removeItem.mockClear()
    
    // Default localStorage behavior
    localStorageMock.getItem.mockReturnValue('test-uuid-12345')
  })

  it('renders projects page with header and form', async () => {
    // Mock successful projects fetch
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ projects: [], count: 0 })
    })

    renderWithRouter(<Projects />)
    
    // Check header content
    expect(screen.getByText('Projects')).toBeInTheDocument()
    expect(screen.getByText('Manage your OpenVibe projects')).toBeInTheDocument()
    
    // Check form elements
    expect(screen.getByText('Create New Project')).toBeInTheDocument()
    expect(screen.getByLabelText('> Project Name:')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Enter project name')).toBeInTheDocument()
    expect(screen.getByText('Create Project')).toBeInTheDocument()
    
    // Wait for projects to load
    await waitFor(() => {
      expect(screen.getByText('Your Projects')).toBeInTheDocument()
    })
  })

  it('displays empty state when no projects exist', async () => {
    // Mock empty projects response
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ projects: [], count: 0 })
    })

    renderWithRouter(<Projects />)
    
    await waitFor(() => {
      expect(screen.getByText('No projects yet. Create your first project above!')).toBeInTheDocument()
    })
  })

  it('displays projects list when projects exist', async () => {
    // Mock projects response with data
    const mockProjects = [
      {
        id: 1,
        name: 'Test Project',
        slug: 'test-project',
        github_url: 'https://github.com/user/test-project',
        created_at: '2025-01-01T00:00:00.000Z'
      },
      {
        id: 2,
        name: 'Another Project',
        slug: 'another-project',
        github_url: 'https://github.com/user/another-project',
        created_at: '2025-01-02T00:00:00.000Z'
      }
    ]

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ projects: mockProjects, count: 2 })
    })

    renderWithRouter(<Projects />)
    
    await waitFor(() => {
      expect(screen.getByText('Test Project')).toBeInTheDocument()
      expect(screen.getByText('Another Project')).toBeInTheDocument()
      expect(screen.getByText('test-project')).toBeInTheDocument()
      expect(screen.getByText('another-project')).toBeInTheDocument()
    })
    
    // Check GitHub info and project links
    expect(screen.getAllByText('GitHub repository available')).toHaveLength(2)
    expect(screen.getAllByText('View Project →')).toHaveLength(2)
  })

  it('shows slug preview when typing project name', async () => {
    // Mock projects fetch
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ projects: [], count: 0 })
    })

    renderWithRouter(<Projects />)
    
    const nameInput = screen.getByLabelText('> Project Name:')
    
    // Type in the input
    fireEvent.change(nameInput, { target: { value: 'My Awesome Project!' } })
    
    // Check slug preview appears
    await waitFor(() => {
      expect(screen.getByText('Slug:')).toBeInTheDocument()
      expect(screen.getByText('my-awesome-project')).toBeInTheDocument()
    })
  })

  it('enables create button when project name is entered', async () => {
    // Mock projects fetch
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ projects: [], count: 0 })
    })

    renderWithRouter(<Projects />)
    
    const nameInput = screen.getByLabelText('> Project Name:')
    const createButton = screen.getByText('Create Project')
    
    // Initially disabled
    expect(createButton).toBeDisabled()
    
    // Type in the input
    fireEvent.change(nameInput, { target: { value: 'Test Project' } })
    
    // Should be enabled now
    await waitFor(() => {
      expect(createButton).not.toBeDisabled()
    })
  })

  it('handles project creation successfully', async () => {
    // Mock projects fetch
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ projects: [], count: 0 })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message: 'Project created successfully',
          project: {
            id: 1,
            name: 'Test Project',
            slug: 'test-project',
            github_url: 'https://github.com/user/test-project',
            created_at: '2025-01-01T00:00:00.000Z'
          }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ projects: [], count: 0 })
      })

    renderWithRouter(<Projects />)
    
    const nameInput = screen.getByLabelText('> Project Name:')
    const createButton = screen.getByText('Create Project')
    
    // Fill form and submit
    fireEvent.change(nameInput, { target: { value: 'Test Project' } })
    fireEvent.click(createButton)
    
    // Check success message appears
    await waitFor(() => {
      expect(screen.getByText('Project "Test Project" created successfully!')).toBeInTheDocument()
    })
    
    // Check that form was reset
    expect(nameInput.value).toBe('')
  })

  it('handles project creation error', async () => {
    // Mock projects fetch and failed creation
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ projects: [], count: 0 })
      })
      .mockResolvedValueOnce({
        ok: false,
        json: async () => ({ error: 'GitHub API key is required. Please set it up in integrations.' })
      })

    renderWithRouter(<Projects />)
    
    const nameInput = screen.getByLabelText('> Project Name:')
    const createButton = screen.getByText('Create Project')
    
    // Fill form and submit
    fireEvent.change(nameInput, { target: { value: 'Test Project' } })
    fireEvent.click(createButton)
    
    // Check error message appears
    await waitFor(() => {
      expect(screen.getByText('GitHub API key is required. Please set it up in integrations.')).toBeInTheDocument()
    })
  })

  it('handles fetch error gracefully', async () => {
    // Mock fetch failure
    fetch.mockRejectedValueOnce(new Error('Network error'))

    renderWithRouter(<Projects />)
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load projects. Please try again.')).toBeInTheDocument()
    })
  })

  it('clears error when user starts typing', async () => {
    // Mock projects fetch and failed creation
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ projects: [], count: 0 })
      })
      .mockResolvedValueOnce({
        ok: false,
        json: async () => ({ error: 'Some error occurred' })
      })

    renderWithRouter(<Projects />)
    
    const nameInput = screen.getByLabelText('> Project Name:')
    const createButton = screen.getByText('Create Project')
    
    // Fill form and submit to trigger error
    fireEvent.change(nameInput, { target: { value: 'Test Project' } })
    fireEvent.click(createButton)
    
    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText('Some error occurred')).toBeInTheDocument()
    })
    
    // Clear input and type again
    fireEvent.change(nameInput, { target: { value: '' } })
    fireEvent.change(nameInput, { target: { value: 'New Project' } })
    
    // Error should be cleared
    await waitFor(() => {
      expect(screen.queryByText('Some error occurred')).not.toBeInTheDocument()
    })
  })
})