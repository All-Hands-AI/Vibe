import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import AppDetail from './AppDetail'

// Mock the uuid utility
vi.mock('../utils/uuid', () => ({
  getUserUUID: () => 'test-uuid-12345'
}))

// Mock useParams to return a test slug
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useParams: () => ({ slug: 'test-app' })
  }
})

const renderAppDetail = () => {
  return render(
    <BrowserRouter>
      <AppDetail />
    </BrowserRouter>
  )
}

describe('AppDetail', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    vi.clearAllMocks()
    
    // Mock fetch globally
    global.fetch = vi.fn()
  })

  it('displays "Running" status when CI/CD is pending', async () => {
    // Mock app API response with pending CI/CD status
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        app: {
          id: 1,
          name: 'Test App',
          slug: 'test-app',
          github_url: 'https://github.com/user/test-app',
          created_at: '2025-01-01T00:00:00.000Z',
          github_status: {
            tests_passing: null, // null indicates pending/running
            last_commit: 'abc1234567890',
            status: 'pending',
            total_count: 1
          },
          fly_status: {
            deployed: true,
            app_url: 'https://test-app.fly.dev',
            status: 'running'
          }
        }
      })
    })

    // Mock riffs API response
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        riffs: []
      })
    })

    renderAppDetail()

    // Wait for the app to load
    await waitFor(() => {
      expect(screen.getByText('Test App')).toBeInTheDocument()
    })

    // Check that CI/CD status shows "Running"
    expect(screen.getByText('🔄 Running')).toBeInTheDocument()
    expect(screen.queryByText('❌ Failing')).not.toBeInTheDocument()
    expect(screen.queryByText('✅ Passing')).not.toBeInTheDocument()
  })

  it('displays "Passing" status when CI/CD is successful', async () => {
    // Mock app API response with successful CI/CD status
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        app: {
          id: 1,
          name: 'Test App',
          slug: 'test-app',
          github_url: 'https://github.com/user/test-app',
          created_at: '2025-01-01T00:00:00.000Z',
          github_status: {
            tests_passing: true, // true indicates success
            last_commit: 'abc1234567890',
            status: 'success',
            total_count: 1
          },
          fly_status: {
            deployed: true,
            app_url: 'https://test-app.fly.dev',
            status: 'running'
          }
        }
      })
    })

    // Mock riffs API response
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        riffs: []
      })
    })

    renderAppDetail()

    // Wait for the app to load
    await waitFor(() => {
      expect(screen.getByText('Test App')).toBeInTheDocument()
    })

    // Check that CI/CD status shows "Passing"
    expect(screen.getByText('✅ Passing')).toBeInTheDocument()
    expect(screen.queryByText('❌ Failing')).not.toBeInTheDocument()
    expect(screen.queryByText('🔄 Running')).not.toBeInTheDocument()
  })

  it('displays "Failing" status when CI/CD has failed', async () => {
    // Mock app API response with failed CI/CD status
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        app: {
          id: 1,
          name: 'Test App',
          slug: 'test-app',
          github_url: 'https://github.com/user/test-app',
          created_at: '2025-01-01T00:00:00.000Z',
          github_status: {
            tests_passing: false, // false indicates failure
            last_commit: 'abc1234567890',
            status: 'failure',
            total_count: 1
          },
          fly_status: {
            deployed: true,
            app_url: 'https://test-app.fly.dev',
            status: 'running'
          }
        }
      })
    })

    // Mock riffs API response
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        riffs: []
      })
    })

    renderAppDetail()

    // Wait for the app to load
    await waitFor(() => {
      expect(screen.getByText('Test App')).toBeInTheDocument()
    })

    // Check that CI/CD status shows "Failing"
    expect(screen.getByText('❌ Failing')).toBeInTheDocument()
    expect(screen.queryByText('✅ Passing')).not.toBeInTheDocument()
    expect(screen.queryByText('🔄 Running')).not.toBeInTheDocument()
  })

  it('displays "Checking..." status when github_status is null', async () => {
    // Mock app API response with no github_status
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        app: {
          id: 1,
          name: 'Test App',
          slug: 'test-app',
          github_url: 'https://github.com/user/test-app',
          created_at: '2025-01-01T00:00:00.000Z',
          github_status: null, // null indicates checking
          fly_status: {
            deployed: true,
            app_url: 'https://test-app.fly.dev',
            status: 'running'
          }
        }
      })
    })

    // Mock riffs API response
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        riffs: []
      })
    })

    renderAppDetail()

    // Wait for the app to load
    await waitFor(() => {
      expect(screen.getByText('Test App')).toBeInTheDocument()
    })

    // Check that CI/CD status shows "Checking..."
    expect(screen.getByText('🔄 Checking...')).toBeInTheDocument()
    expect(screen.queryByText('❌ Failing')).not.toBeInTheDocument()
    expect(screen.queryByText('✅ Passing')).not.toBeInTheDocument()
    expect(screen.queryByText('🔄 Running')).not.toBeInTheDocument()
  })
})