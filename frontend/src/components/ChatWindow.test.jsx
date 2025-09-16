import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import ChatWindow from './ChatWindow'

// Mock the child components
vi.mock('./MessageList', () => ({
  default: ({ messages, scrollContainerRef, messagesEndRef }) => {
    // Mock scrollIntoView for the messagesEndRef
    const mockMessagesEndRef = {
      current: {
        scrollIntoView: vi.fn()
      }
    }
    
    // Set the ref if provided
    if (messagesEndRef) {
      messagesEndRef.current = mockMessagesEndRef.current
    }
    
    return (
      <div 
        data-testid="message-list"
        ref={scrollContainerRef}
        className="h-full overflow-y-auto p-4 space-y-4"
      >
        {messages.map((message, index) => (
          <div key={message.id || index} data-testid={`message-${index}`}>
            {message.content}
          </div>
        ))}
        <div ref={messagesEndRef} data-testid="messages-end" />
      </div>
    )
  }
}))

vi.mock('./MessageInput', () => ({
  default: ({ onSendMessage, disabled, placeholder }) => (
    <div data-testid="message-input">
      <input 
        data-testid="message-input-field"
        placeholder={placeholder}
        disabled={disabled}
        onChange={(e) => {
          if (e.target.value === 'send') {
            onSendMessage('Test message')
          }
        }}
      />
    </div>
  )
}))

vi.mock('./AgentStatusBar', () => ({
  default: ({ appSlug, riffSlug }) => (
    <div data-testid="agent-status-bar">
      Status for {appSlug}/{riffSlug}
    </div>
  )
}))

// Mock fetch globally
global.fetch = vi.fn()

const mockApp = {
  slug: 'test-app'
}

const mockRiff = {
  slug: 'test-riff'
}

const mockUserUuid = 'test-user-uuid'

// Helper function to create mock messages
const createMockMessages = (count) => {
  return Array.from({ length: count }, (_, index) => ({
    id: `message-${index}`,
    content: `Test message ${index + 1}`,
    created_at: new Date(Date.now() - (count - index) * 1000).toISOString(),
    created_by: index % 2 === 0 ? mockUserUuid : 'agent-uuid',
    type: 'text'
  }))
}

describe('ChatWindow Height Constraints', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock DOM methods that aren't available in jsdom
    Element.prototype.scrollIntoView = vi.fn()
    
    // Mock successful fetch responses
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ messages: [] })
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should maintain fixed height container structure', async () => {
    render(
      <div style={{ height: '500px' }}>
        <ChatWindow 
          app={mockApp} 
          riff={mockRiff} 
          userUuid={mockUserUuid} 
        />
      </div>
    )

    await waitFor(() => {
      expect(screen.getByTestId('message-list')).toBeInTheDocument()
    })

    const chatContainer = screen.getByTestId('message-list').closest('.flex.flex-col.h-full')
    expect(chatContainer).toBeInTheDocument()
    expect(chatContainer).toHaveClass('h-full')
  })

  it('should maintain height constraints when many messages are added', async () => {
    const manyMessages = createMockMessages(50)
    
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ messages: manyMessages })
    })

    const { container } = render(
      <div style={{ height: '500px' }} data-testid="parent-container">
        <ChatWindow 
          app={mockApp} 
          riff={mockRiff} 
          userUuid={mockUserUuid} 
        />
      </div>
    )

    await waitFor(() => {
      expect(screen.getByTestId('message-list')).toBeInTheDocument()
    })

    // Check that the chat window doesn't exceed its parent container
    const chatContainer = container.querySelector('.flex.flex-col.h-full')
    
    expect(chatContainer).toBeInTheDocument()
    
    // The chat container should have h-full class to fill its parent
    expect(chatContainer).toHaveClass('h-full')
    
    // The message list should be scrollable
    const messageList = screen.getByTestId('message-list')
    expect(messageList).toHaveClass('overflow-y-auto')
    expect(messageList).toHaveClass('h-full')
  })

  it('should have proper flex layout structure for height constraints', async () => {
    render(
      <div style={{ height: '400px' }}>
        <ChatWindow 
          app={mockApp} 
          riff={mockRiff} 
          userUuid={mockUserUuid} 
        />
      </div>
    )

    await waitFor(() => {
      expect(screen.getByTestId('message-list')).toBeInTheDocument()
    })

    // Check the main container structure
    const chatContainer = screen.getByTestId('message-list').closest('.flex.flex-col.h-full')
    expect(chatContainer).toHaveClass('flex', 'flex-col', 'h-full')

    // Check that message area has flex-1 and min-h-0 for proper scrolling
    const messageArea = screen.getByTestId('message-list').parentElement
    expect(messageArea).toHaveClass('flex-1', 'min-h-0')

    // Check that status bar and input are flex-shrink-0
    const statusBar = screen.getByTestId('agent-status-bar').parentElement
    const messageInput = screen.getByTestId('message-input').parentElement
    
    expect(statusBar).toHaveClass('flex-shrink-0')
    expect(messageInput).toHaveClass('flex-shrink-0')
  })

  it('should maintain scrollable message list with large content', async () => {
    const longMessages = createMockMessages(100).map((msg, index) => ({
      ...msg,
      content: `This is a very long message ${index + 1} that contains a lot of text content to test scrolling behavior. `.repeat(10)
    }))
    
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ messages: longMessages })
    })

    render(
      <div style={{ height: '300px' }}>
        <ChatWindow 
          app={mockApp} 
          riff={mockRiff} 
          userUuid={mockUserUuid} 
        />
      </div>
    )

    await waitFor(() => {
      expect(screen.getByTestId('message-list')).toBeInTheDocument()
    })

    const messageList = screen.getByTestId('message-list')
    
    // Should have overflow-y-auto for scrolling
    expect(messageList).toHaveClass('overflow-y-auto')
    
    // Should fill available height
    expect(messageList).toHaveClass('h-full')
    
    // Should have all messages rendered
    const messageElements = screen.getAllByTestId(/^message-\d+$/)
    expect(messageElements).toHaveLength(100)
  })

  it.skip('should handle dynamic message addition without breaking height constraints', async () => {
    let messageCount = 5
    
    fetch.mockImplementation(() => {
      const messages = createMockMessages(messageCount)
      return Promise.resolve({
        ok: true,
        json: async () => ({ messages })
      })
    })

    render(
      <div style={{ height: '400px' }}>
        <ChatWindow 
          app={mockApp} 
          riff={mockRiff} 
          userUuid={mockUserUuid} 
        />
      </div>
    )

    await waitFor(() => {
      expect(screen.getByTestId('message-list')).toBeInTheDocument()
    })

    // Simulate adding more messages
    act(() => {
      messageCount = 25
    })

    // Trigger a re-fetch (simulating polling)
    await act(async () => {
      // The component polls every 2 seconds, we can trigger it by waiting
      await new Promise(resolve => setTimeout(resolve, 100))
    })

    const messageList = screen.getByTestId('message-list')
    
    // Should still maintain proper classes
    expect(messageList).toHaveClass('h-full', 'overflow-y-auto')
    
    // Container should still have proper flex layout
    const chatContainer = messageList.closest('.flex.flex-col.h-full')
    expect(chatContainer).toHaveClass('flex', 'flex-col', 'h-full')
  })

  it('should maintain height constraints with error messages displayed', async () => {
    fetch.mockRejectedValue(new Error('Network error'))

    render(
      <div style={{ height: '400px' }}>
        <ChatWindow 
          app={mockApp} 
          riff={mockRiff} 
          userUuid={mockUserUuid} 
        />
      </div>
    )

    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument()
    })

    // Even with error, the container should maintain proper structure
    const chatContainer = document.querySelector('.flex.flex-col.h-full')
    expect(chatContainer).toBeInTheDocument()
    expect(chatContainer).toHaveClass('h-full')

    // Error message should have flex-shrink-0
    const errorContainer = screen.getByText(/Network error/).closest('.flex-shrink-0')
    expect(errorContainer).toBeInTheDocument()
  })

  it('should maintain proper height during loading state', () => {
    // Mock loading state by not resolving fetch immediately
    fetch.mockImplementation(() => new Promise(() => {})) // Never resolves

    render(
      <div style={{ height: '400px' }}>
        <ChatWindow 
          app={mockApp} 
          riff={mockRiff} 
          userUuid={mockUserUuid} 
        />
      </div>
    )

    // Should show loading spinner
    expect(screen.getByText('Loading messages...')).toBeInTheDocument()
    
    // Loading container should have proper height constraints
    const loadingContainer = screen.getByText('Loading messages...').closest('div')
    expect(loadingContainer).toHaveClass('h-64') // Fixed height for loading state
  })
})