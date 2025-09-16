import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { createRef } from 'react'
import MessageList from './MessageList'

// Mock MarkdownRenderer
vi.mock('./MarkdownRenderer', () => ({
  default: ({ content }) => <div data-testid="markdown-content">{content}</div>
}))

const mockUserUuid = 'test-user-uuid'
const mockScrollContainerRef = createRef()
const mockMessagesEndRef = createRef()
const mockOnScroll = vi.fn()

// Helper function to create mock messages
const createMockMessages = (count, options = {}) => {
  const { longContent = false, mixedTypes = false } = options
  
  return Array.from({ length: count }, (_, index) => ({
    id: `message-${index}`,
    content: longContent 
      ? `This is a very long message ${index + 1} that contains a lot of text content to test scrolling behavior and height constraints. `.repeat(5)
      : `Test message ${index + 1}`,
    created_at: new Date(Date.now() - (count - index) * 60000).toISOString(), // 1 minute apart
    created_by: index % 2 === 0 ? mockUserUuid : 'agent-uuid',
    type: mixedTypes && index % 3 === 0 ? 'code' : 'text',
    metadata: mixedTypes && index % 4 === 0 ? { filename: `file${index}.txt` } : {}
  }))
}

describe('MessageList Height Constraints', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render with proper height classes for scrolling', () => {
    const messages = createMockMessages(10)
    
    render(
      <div style={{ height: '400px' }}>
        <MessageList
          messages={messages}
          userUuid={mockUserUuid}
          scrollContainerRef={mockScrollContainerRef}
          onScroll={mockOnScroll}
          messagesEndRef={mockMessagesEndRef}
        />
      </div>
    )

    const messageList = screen.getByTestId('message-0').closest('.h-full.overflow-y-auto')
    expect(messageList).toBeInTheDocument()
    expect(messageList).toHaveClass('h-full', 'overflow-y-auto')
  })

  it('should maintain height constraints with many messages', () => {
    const manyMessages = createMockMessages(100)
    
    const { container } = render(
      <div style={{ height: '300px' }} data-testid="parent-container">
        <MessageList
          messages={manyMessages}
          userUuid={mockUserUuid}
          scrollContainerRef={mockScrollContainerRef}
          onScroll={mockOnScroll}
          messagesEndRef={mockMessagesEndRef}
        />
      </div>
    )

    // Should render all messages
    const messageElements = screen.getAllByTestId(/^message-\d+$/)
    expect(messageElements).toHaveLength(100)

    // Container should have proper scrolling classes
    const scrollContainer = container.querySelector('.h-full.overflow-y-auto')
    expect(scrollContainer).toBeInTheDocument()
    expect(scrollContainer).toHaveClass('h-full', 'overflow-y-auto', 'p-4', 'space-y-4')
  })

  it('should handle long message content without breaking height constraints', () => {
    const longMessages = createMockMessages(20, { longContent: true })
    
    render(
      <div style={{ height: '400px' }}>
        <MessageList
          messages={longMessages}
          userUuid={mockUserUuid}
          scrollContainerRef={mockScrollContainerRef}
          onScroll={mockOnScroll}
          messagesEndRef={mockMessagesEndRef}
        />
      </div>
    )

    // Should render all messages
    const messageElements = screen.getAllByTestId(/^message-\d+$/)
    expect(messageElements).toHaveLength(20)

    // Container should maintain scrolling capability
    const scrollContainer = screen.getByTestId('message-0').closest('.h-full.overflow-y-auto')
    expect(scrollContainer).toHaveClass('h-full', 'overflow-y-auto')
  })

  it('should handle mixed message types while maintaining height constraints', () => {
    const mixedMessages = createMockMessages(30, { mixedTypes: true })
    
    render(
      <div style={{ height: '500px' }}>
        <MessageList
          messages={mixedMessages}
          userUuid={mockUserUuid}
          scrollContainerRef={mockScrollContainerRef}
          onScroll={mockOnScroll}
          messagesEndRef={mockMessagesEndRef}
        />
      </div>
    )

    // Should render all messages
    const messageElements = screen.getAllByTestId(/^message-\d+$/)
    expect(messageElements).toHaveLength(30)

    // Should have code blocks for some messages
    const codeElements = document.querySelectorAll('pre code')
    expect(codeElements.length).toBeGreaterThan(0)

    // Container should maintain proper structure
    const scrollContainer = screen.getByTestId('message-0').closest('.h-full.overflow-y-auto')
    expect(scrollContainer).toHaveClass('h-full', 'overflow-y-auto')
  })

  it('should render empty state with proper height', () => {
    render(
      <div style={{ height: '400px' }}>
        <MessageList
          messages={[]}
          userUuid={mockUserUuid}
          scrollContainerRef={mockScrollContainerRef}
          onScroll={mockOnScroll}
          messagesEndRef={mockMessagesEndRef}
        />
      </div>
    )

    // Should show empty state
    expect(screen.getByText('No messages yet')).toBeInTheDocument()
    expect(screen.getByText('Start the conversation by sending a message below.')).toBeInTheDocument()

    // Empty state should fill height
    const emptyContainer = screen.getByText('No messages yet').closest('.h-full')
    expect(emptyContainer).toBeInTheDocument()
    expect(emptyContainer).toHaveClass('h-full', 'flex', 'items-center', 'justify-center')
  })

  it('should properly attach scroll container ref', () => {
    const messages = createMockMessages(5)
    const testRef = createRef()
    
    render(
      <MessageList
        messages={messages}
        userUuid={mockUserUuid}
        scrollContainerRef={testRef}
        onScroll={mockOnScroll}
        messagesEndRef={mockMessagesEndRef}
      />
    )

    // Ref should be attached to the scrollable container
    expect(testRef.current).toBeTruthy()
    expect(testRef.current).toHaveClass('h-full', 'overflow-y-auto')
  })

  it('should properly attach messages end ref for scroll anchoring', () => {
    const messages = createMockMessages(10)
    const testMessagesEndRef = createRef()
    
    render(
      <MessageList
        messages={messages}
        userUuid={mockUserUuid}
        scrollContainerRef={mockScrollContainerRef}
        onScroll={mockOnScroll}
        messagesEndRef={testMessagesEndRef}
      />
    )

    // Messages end ref should be attached
    expect(testMessagesEndRef.current).toBeTruthy()
    
    // Should be at the end of the message list
    const messagesEndElement = screen.getByTestId('messages-end')
    expect(messagesEndElement).toBeInTheDocument()
    expect(testMessagesEndRef.current).toBe(messagesEndElement)
  })

  it('should group messages by date while maintaining height constraints', () => {
    // Create messages across different dates
    const messagesAcrossDates = [
      {
        id: 'msg-1',
        content: 'Message from today',
        created_at: new Date().toISOString(),
        created_by: mockUserUuid,
        type: 'text'
      },
      {
        id: 'msg-2',
        content: 'Message from yesterday',
        created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        created_by: 'agent-uuid',
        type: 'text'
      },
      {
        id: 'msg-3',
        content: 'Message from two days ago',
        created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        created_by: mockUserUuid,
        type: 'text'
      }
    ]
    
    render(
      <div style={{ height: '400px' }}>
        <MessageList
          messages={messagesAcrossDates}
          userUuid={mockUserUuid}
          scrollContainerRef={mockScrollContainerRef}
          onScroll={mockOnScroll}
          messagesEndRef={mockMessagesEndRef}
        />
      </div>
    )

    // Should show date separators
    expect(screen.getByText('Today')).toBeInTheDocument()
    expect(screen.getByText('Yesterday')).toBeInTheDocument()

    // Should render all messages
    expect(screen.getByText('Message from today')).toBeInTheDocument()
    expect(screen.getByText('Message from yesterday')).toBeInTheDocument()
    expect(screen.getByText('Message from two days ago')).toBeInTheDocument()

    // Container should maintain proper height
    const scrollContainer = screen.getByText('Message from today').closest('.h-full.overflow-y-auto')
    expect(scrollContainer).toHaveClass('h-full', 'overflow-y-auto')
  })

  it('should handle scroll events properly', () => {
    const messages = createMockMessages(20)
    
    render(
      <MessageList
        messages={messages}
        userUuid={mockUserUuid}
        scrollContainerRef={mockScrollContainerRef}
        onScroll={mockOnScroll}
        messagesEndRef={mockMessagesEndRef}
      />
    )

    const scrollContainer = screen.getByTestId('message-0').closest('.h-full.overflow-y-auto')
    
    // Simulate scroll event
    scrollContainer.dispatchEvent(new Event('scroll'))
    
    expect(mockOnScroll).toHaveBeenCalled()
  })

  it('should maintain proper message styling within height constraints', () => {
    const messages = [
      {
        id: 'user-msg',
        content: 'User message',
        created_at: new Date().toISOString(),
        created_by: mockUserUuid,
        type: 'text'
      },
      {
        id: 'agent-msg',
        content: 'Agent message',
        created_at: new Date().toISOString(),
        created_by: 'agent-uuid',
        type: 'text'
      },
      {
        id: 'code-msg',
        content: 'console.log("Hello World")',
        created_at: new Date().toISOString(),
        created_by: 'agent-uuid',
        type: 'code'
      }
    ]
    
    render(
      <div style={{ height: '400px' }}>
        <MessageList
          messages={messages}
          userUuid={mockUserUuid}
          scrollContainerRef={mockScrollContainerRef}
          onScroll={mockOnScroll}
          messagesEndRef={mockMessagesEndRef}
        />
      </div>
    )

    // User message should be right-aligned
    const userMessage = screen.getByText('User message').closest('.flex')
    expect(userMessage).toHaveClass('justify-end')

    // Agent message should be left-aligned
    const agentMessage = screen.getByText('Agent message').closest('.flex')
    expect(agentMessage).toHaveClass('justify-start')

    // Code message should have proper styling
    const codeMessage = screen.getByText('console.log("Hello World")').closest('pre')
    expect(codeMessage).toBeInTheDocument()
    expect(codeMessage).toHaveClass('bg-black/50', 'p-2', 'rounded', 'text-xs', 'font-mono', 'overflow-x-auto')

    // Container should maintain height constraints
    const scrollContainer = userMessage.closest('.h-full.overflow-y-auto')
    expect(scrollContainer).toHaveClass('h-full', 'overflow-y-auto')
  })
})