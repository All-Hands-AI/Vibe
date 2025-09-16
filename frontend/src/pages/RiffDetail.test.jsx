import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import RiffDetail from './RiffDetail'

// Mock the context
vi.mock('../context/SetupContext', () => ({
  useSetup: () => ({
    userUUID: 'test-user-uuid'
  })
}))

// Mock the child components
vi.mock('../components/ChatWindow', () => ({
  default: ({ app, riff, userUuid }) => (
    <div 
      data-testid="chat-window"
      className="flex flex-col h-full bg-black border border-gray-700 rounded-lg"
    >
      <div className="flex-1 min-h-0 overflow-hidden">
        <div 
          data-testid="message-list-mock"
          className="h-full overflow-y-auto p-4 space-y-4"
        >
          <div>Chat for {app.slug}/{riff.slug} (User: {userUuid})</div>
          {/* Simulate many messages */}
          {Array.from({ length: 50 }, (_, i) => (
            <div key={i} data-testid={`mock-message-${i}`}>
              Mock message {i + 1}
            </div>
          ))}
        </div>
      </div>
      <div className="flex-shrink-0">
        <div data-testid="status-bar-mock">Status Bar</div>
      </div>
      <div className="flex-shrink-0">
        <div data-testid="input-mock">Message Input</div>
      </div>
    </div>
  )
}))

vi.mock('../components/LLMErrorModal', () => ({
  default: () => null
}))

vi.mock('../components/FirstRiffModal', () => ({
  default: () => null
}))

vi.mock('../components/CIStatus', () => ({
  default: () => <div data-testid="ci-status">CI Status</div>
}))

// Mock utility functions
vi.mock('../utils/uuid', () => ({
  getUserUUID: () => 'test-user-uuid'
}))

vi.mock('../utils/llmService', () => ({
  startLLMPolling: vi.fn(() => vi.fn()),
  checkLLMReady: vi.fn(() => Promise.resolve(true))
}))

vi.mock('../utils/useDocumentTitle', () => ({
  useDocumentTitle: vi.fn(),
  formatPageTitle: vi.fn((type, appName, riffName) => `${type} - ${appName} - ${riffName}`)
}))

// Mock fetch globally
global.fetch = vi.fn()

const mockApp = {
  slug: 'test-app',
  name: 'Test App'
}

const mockRiff = {
  slug: 'test-riff',
  name: 'Test Riff'
}

describe('RiffDetail Height Constraints Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock successful API responses
    fetch.mockImplementation((url) => {
      if (url.includes('/api/apps/test-app/riffs')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ riffs: [mockRiff] })
        })
      }
      if (url.includes('/api/apps/test-app')) {
        return Promise.resolve({
          ok: true,
          json: async () => mockApp
        })
      }
      if (url.includes('/pr-status')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ pr_status: null })
        })
      }
      if (url.includes('/deployment')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ status: 'success' })
        })
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({})
      })
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should maintain viewport height constraints for chat window', async () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/apps/test-app/riffs/test-riff']}>
        <Routes>
          <Route path="/apps/:appSlug/riffs/:riffSlug" element={
            <div style={{ height: '100vh' }}>
              <RiffDetail />
            </div>
          } />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('chat-window')).toBeInTheDocument()
    })

    // Check that the main container has proper height constraint
    const mainContainer = container.querySelector('.h-\\[calc\\(100vh-200px\\)\\]')
    expect(mainContainer).toBeInTheDocument()
    expect(mainContainer).toHaveClass('flex', 'flex-col', 'lg:flex-row')

    // Check that the chat container has proper flex structure
    const chatContainer = screen.getByTestId('chat-window')
    expect(chatContainer).toHaveClass('flex', 'flex-col', 'h-full')

    // Check that the left sidebar has proper flex structure
    const leftSidebar = chatContainer.closest('.flex.flex-col')
    expect(leftSidebar).toBeInTheDocument()

    // Check that the chat window wrapper has flex-1 and min-h-0
    const chatWrapper = chatContainer.closest('.flex-1.min-h-0')
    expect(chatWrapper).toBeInTheDocument()
  })

  it('should maintain height constraints with many messages in chat', async () => {
    render(
      <MemoryRouter initialEntries={['/apps/test-app/riffs/test-riff']}>
        <Routes>
          <Route path="/apps/:appSlug/riffs/:riffSlug" element={
            <div style={{ height: '800px' }} data-testid="viewport">
              <RiffDetail />
            </div>
          } />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('chat-window')).toBeInTheDocument()
    })

    // Should render many mock messages
    const mockMessages = screen.getAllByTestId(/^mock-message-\d+$/)
    expect(mockMessages).toHaveLength(50)

    // Message list should be scrollable
    const messageList = screen.getByTestId('message-list-mock')
    expect(messageList).toHaveClass('h-full', 'overflow-y-auto')

    // Chat window should maintain its structure
    const chatWindow = screen.getByTestId('chat-window')
    expect(chatWindow).toHaveClass('flex', 'flex-col', 'h-full')

    // Status bar and input should be flex-shrink-0
    const statusBar = screen.getByTestId('status-bar-mock')
    const messageInput = screen.getByTestId('input-mock')
    
    expect(statusBar.parentElement).toHaveClass('flex-shrink-0')
    expect(messageInput.parentElement).toHaveClass('flex-shrink-0')
  })

  it('should handle responsive layout while maintaining height constraints', async () => {
    // Test large screen layout
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1200,
    })

    const { container } = render(
      <MemoryRouter initialEntries={['/apps/test-app/riffs/test-riff']}>
        <Routes>
          <Route path="/apps/:appSlug/riffs/:riffSlug" element={
            <div style={{ height: '100vh' }}>
              <RiffDetail />
            </div>
          } />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('chat-window')).toBeInTheDocument()
    })

    // Should have row layout on large screens
    const mainContainer = container.querySelector('.h-\\[calc\\(100vh-200px\\)\\]')
    expect(mainContainer).toHaveClass('lg:flex-row')

    // Height constraint should still apply
    expect(mainContainer).toHaveClass('h-[calc(100vh-200px)]')

    // Chat should still maintain proper structure
    const chatWindow = screen.getByTestId('chat-window')
    expect(chatWindow).toHaveClass('h-full')
  })

  it('should maintain height constraints during loading state', () => {
    // Mock loading state
    fetch.mockImplementation(() => new Promise(() => {})) // Never resolves

    render(
      <MemoryRouter initialEntries={['/apps/test-app/riffs/test-riff']}>
        <Routes>
          <Route path="/apps/:appSlug/riffs/:riffSlug" element={
            <div style={{ height: '100vh' }}>
              <RiffDetail />
            </div>
          } />
        </Routes>
      </MemoryRouter>
    )

    // Should show loading state
    expect(screen.getByText('Loading riff...')).toBeInTheDocument()

    // Loading container should have proper height
    const loadingContainer = screen.getByText('Loading riff...').closest('.min-h-screen')
    expect(loadingContainer).toBeInTheDocument()
  })

  it('should maintain height constraints with error state', async () => {
    fetch.mockRejectedValue(new Error('Network error'))

    render(
      <MemoryRouter initialEntries={['/apps/test-app/riffs/test-riff']}>
        <Routes>
          <Route path="/apps/:appSlug/riffs/:riffSlug" element={
            <div style={{ height: '100vh' }}>
              <RiffDetail />
            </div>
          } />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Error')).toBeInTheDocument()
    })

    // Error container should have proper height
    const errorContainer = screen.getByText('Error').closest('.min-h-screen')
    expect(errorContainer).toBeInTheDocument()
  })

  it('should maintain height constraints with iframe and chat side by side', async () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/apps/test-app/riffs/test-riff']}>
        <Routes>
          <Route path="/apps/:appSlug/riffs/:riffSlug" element={
            <div style={{ height: '100vh' }}>
              <RiffDetail />
            </div>
          } />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('chat-window')).toBeInTheDocument()
    })

    // Should have flexbox layout
    const mainContainer = container.querySelector('.h-\\[calc\\(100vh-200px\\)\\]')
    expect(mainContainer).toBeInTheDocument()
    expect(mainContainer).toHaveClass('flex', 'flex-col', 'lg:flex-row')

    // Both columns should have proper flex structure
    const columns = container.querySelectorAll('.flex-1')
    expect(columns.length).toBeGreaterThanOrEqual(1)

    // Chat column should have proper structure
    const chatWindow = screen.getByTestId('chat-window')
    const chatColumn = chatWindow.closest('.flex-1')
    expect(chatColumn).toBeInTheDocument()

    // Container should constrain height
    expect(mainContainer).toHaveClass('h-[calc(100vh-200px)]')
  })

  it('should handle dynamic content changes while maintaining height constraints', async () => {
    let deploymentStatus = { status: 'pending' }
    
    fetch.mockImplementation((url) => {
      if (url.includes('/api/apps/test-app/riffs')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ riffs: [mockRiff] })
        })
      }
      if (url.includes('/api/apps/test-app')) {
        return Promise.resolve({
          ok: true,
          json: async () => mockApp
        })
      }
      if (url.includes('/pr-status')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ pr_status: null })
        })
      }
      if (url.includes('/deployment')) {
        return Promise.resolve({
          ok: true,
          json: async () => deploymentStatus
        })
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({})
      })
    })

    const { container } = render(
      <MemoryRouter initialEntries={['/apps/test-app/riffs/test-riff']}>
        <Routes>
          <Route path="/apps/:appSlug/riffs/:riffSlug" element={
            <div style={{ height: '100vh' }}>
              <RiffDetail />
            </div>
          } />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByTestId('chat-window')).toBeInTheDocument()
    })

    // Should maintain height constraints regardless of deployment status
    const mainContainer = container.querySelector('.h-\\[calc\\(100vh-200px\\)\\]')
    expect(mainContainer).toHaveClass('h-[calc(100vh-200px)]')

    const chatWindow = screen.getByTestId('chat-window')
    expect(chatWindow).toHaveClass('h-full')
  })
})