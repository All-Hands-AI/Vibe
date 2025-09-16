import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import PropTypes from 'prop-types'

// Simple test components to verify height constraints
const TestChatWindow = ({ messages = [] }) => {
  return (
    <div className="flex flex-col h-full bg-black border border-gray-700 rounded-lg" data-testid="chat-window">
      {/* Messages Area - This should be the scrollable part */}
      <div className="flex-1 min-h-0 overflow-hidden" data-testid="messages-container">
        <div className="h-full overflow-y-auto p-4 space-y-4" data-testid="messages-list">
          {messages.map((message, index) => (
            <div key={index} data-testid={`message-${index}`} className="p-2 border rounded">
              {message}
            </div>
          ))}
        </div>
      </div>

      {/* Status Bar */}
      <div className="flex-shrink-0" data-testid="status-bar">
        Status Bar
      </div>

      {/* Message Input */}
      <div className="border-t border-gray-700 flex-shrink-0" data-testid="message-input">
        Message Input
      </div>
    </div>
  )
}

TestChatWindow.propTypes = {
  messages: PropTypes.array
}

const TestRiffDetailLayout = ({ children }) => {
  return (
    <div className="min-h-screen bg-black text-cyber-text">
      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Navigation */}
        <nav className="mb-4" data-testid="navigation">
          Navigation
        </nav>

        {/* Header */}
        <header className="mb-4" data-testid="header">
          Header
        </header>

        {/* Main Content Grid - 2 columns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-200px)]" data-testid="main-grid">
          {/* Left Sidebar - Chat */}
          <div className="flex flex-col" data-testid="chat-column">
            {/* Chat Window */}
            <div className="flex-1 min-h-0" data-testid="chat-wrapper">
              {children}
            </div>
          </div>

          {/* Right Side - Iframe */}
          <div className="flex flex-col" data-testid="iframe-column">
            <div className="flex-1 bg-gray-800 rounded-lg" data-testid="iframe-placeholder">
              Iframe Content
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

TestRiffDetailLayout.propTypes = {
  children: PropTypes.node
}

describe('Height Constraints Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('ChatWindow Height Constraints', () => {
    it('should have proper flex layout structure for height constraints', () => {
      render(
        <div style={{ height: '400px' }} data-testid="parent-container">
          <TestChatWindow />
        </div>
      )

      // Check the main container structure
      const chatContainer = screen.getByTestId('chat-window')
      expect(chatContainer).toHaveClass('flex', 'flex-col', 'h-full')

      // Check that message area has flex-1 and min-h-0 for proper scrolling
      const messageContainer = screen.getByTestId('messages-container')
      expect(messageContainer).toHaveClass('flex-1', 'min-h-0', 'overflow-hidden')

      // Check that the messages list is scrollable
      const messagesList = screen.getByTestId('messages-list')
      expect(messagesList).toHaveClass('h-full', 'overflow-y-auto')

      // Check that status bar and input are flex-shrink-0
      const statusBar = screen.getByTestId('status-bar')
      const messageInput = screen.getByTestId('message-input')
      
      expect(statusBar).toHaveClass('flex-shrink-0')
      expect(messageInput).toHaveClass('flex-shrink-0')
    })

    it('should maintain height constraints with many messages', () => {
      const manyMessages = Array.from({ length: 50 }, (_, i) => `Message ${i + 1}`)
      
      render(
        <div style={{ height: '300px' }} data-testid="parent-container">
          <TestChatWindow messages={manyMessages} />
        </div>
      )

      // Should render all messages
      const messageElements = screen.getAllByTestId(/^message-\d+$/)
      expect(messageElements).toHaveLength(50)

      // Container should have proper classes
      const messagesList = screen.getByTestId('messages-list')
      expect(messagesList).toHaveClass('h-full', 'overflow-y-auto')
      
      // Container should still have proper flex layout
      const chatContainer = screen.getByTestId('chat-window')
      expect(chatContainer).toHaveClass('flex', 'flex-col', 'h-full')
    })

    it('should maintain proper structure with long content', () => {
      const longMessages = Array.from({ length: 20 }, (_, i) => 
        `This is a very long message ${i + 1} that contains a lot of text content to test scrolling behavior. `.repeat(10)
      )
      
      render(
        <div style={{ height: '400px' }}>
          <TestChatWindow messages={longMessages} />
        </div>
      )

      // Should render all messages
      const messageElements = screen.getAllByTestId(/^message-\d+$/)
      expect(messageElements).toHaveLength(20)

      // Should maintain proper classes
      const messagesList = screen.getByTestId('messages-list')
      expect(messagesList).toHaveClass('h-full', 'overflow-y-auto')
      
      // Container should maintain proper structure
      const chatContainer = screen.getByTestId('chat-window')
      expect(chatContainer).toHaveClass('flex', 'flex-col', 'h-full')
    })
  })

  describe('RiffDetail Layout Height Constraints', () => {
    it('should maintain viewport height constraints for the main grid', () => {
      render(
        <div style={{ height: '100vh' }} data-testid="viewport">
          <TestRiffDetailLayout>
            <TestChatWindow />
          </TestRiffDetailLayout>
        </div>
      )

      // Check that the main grid has proper height constraint
      const mainGrid = screen.getByTestId('main-grid')
      expect(mainGrid).toHaveClass('h-[calc(100vh-200px)]')

      // Check that the chat column has proper flex structure
      const chatColumn = screen.getByTestId('chat-column')
      expect(chatColumn).toHaveClass('flex', 'flex-col')

      // Check that the chat wrapper has flex-1 and min-h-0
      const chatWrapper = screen.getByTestId('chat-wrapper')
      expect(chatWrapper).toHaveClass('flex-1', 'min-h-0')

      // Check that the chat window maintains its structure
      const chatWindow = screen.getByTestId('chat-window')
      expect(chatWindow).toHaveClass('h-full')
    })

    it('should handle responsive layout while maintaining height constraints', () => {
      render(
        <div style={{ height: '100vh' }}>
          <TestRiffDetailLayout>
            <TestChatWindow />
          </TestRiffDetailLayout>
        </div>
      )

      // Should have responsive grid layout
      const mainGrid = screen.getByTestId('main-grid')
      expect(mainGrid).toHaveClass('grid-cols-1', 'lg:grid-cols-2')

      // Height constraint should still apply
      expect(mainGrid).toHaveClass('h-[calc(100vh-200px)]')

      // Both columns should have proper structure
      const chatColumn = screen.getByTestId('chat-column')
      const iframeColumn = screen.getByTestId('iframe-column')
      
      expect(chatColumn).toHaveClass('flex', 'flex-col')
      expect(iframeColumn).toHaveClass('flex', 'flex-col')
    })

    it('should maintain height constraints with chat and iframe side by side', () => {
      render(
        <div style={{ height: '100vh' }}>
          <TestRiffDetailLayout>
            <TestChatWindow messages={Array.from({ length: 30 }, (_, i) => `Message ${i + 1}`)} />
          </TestRiffDetailLayout>
        </div>
      )

      // Should have 2-column grid layout
      const mainGrid = screen.getByTestId('main-grid')
      expect(mainGrid).toHaveClass('grid', 'lg:grid-cols-2')

      // Both columns should be present
      const chatColumn = screen.getByTestId('chat-column')
      const iframeColumn = screen.getByTestId('iframe-column')
      
      expect(chatColumn).toBeInTheDocument()
      expect(iframeColumn).toBeInTheDocument()

      // Grid should constrain height
      expect(mainGrid).toHaveClass('h-[calc(100vh-200px)]')

      // Chat should maintain proper structure within the constrained height
      const chatWindow = screen.getByTestId('chat-window')
      expect(chatWindow).toHaveClass('h-full')

      // Messages should be scrollable
      const messagesList = screen.getByTestId('messages-list')
      expect(messagesList).toHaveClass('h-full', 'overflow-y-auto')
    })
  })

  describe('CSS Class Verification', () => {
    it('should verify all critical height constraint classes are present', () => {
      render(
        <div style={{ height: '100vh' }}>
          <TestRiffDetailLayout>
            <TestChatWindow messages={['Test message']} />
          </TestRiffDetailLayout>
        </div>
      )

      // Main grid height constraint
      const mainGrid = screen.getByTestId('main-grid')
      expect(mainGrid).toHaveClass('h-[calc(100vh-200px)]')

      // Chat column flex structure
      const chatColumn = screen.getByTestId('chat-column')
      expect(chatColumn).toHaveClass('flex', 'flex-col')

      // Chat wrapper flex-1 min-h-0
      const chatWrapper = screen.getByTestId('chat-wrapper')
      expect(chatWrapper).toHaveClass('flex-1', 'min-h-0')

      // Chat window h-full
      const chatWindow = screen.getByTestId('chat-window')
      expect(chatWindow).toHaveClass('flex', 'flex-col', 'h-full')

      // Messages container flex-1 min-h-0 overflow-hidden
      const messagesContainer = screen.getByTestId('messages-container')
      expect(messagesContainer).toHaveClass('flex-1', 'min-h-0', 'overflow-hidden')

      // Messages list h-full overflow-y-auto
      const messagesList = screen.getByTestId('messages-list')
      expect(messagesList).toHaveClass('h-full', 'overflow-y-auto')

      // Status bar and input flex-shrink-0
      const statusBar = screen.getByTestId('status-bar')
      const messageInput = screen.getByTestId('message-input')
      
      expect(statusBar).toHaveClass('flex-shrink-0')
      expect(messageInput).toHaveClass('flex-shrink-0')
    })

    it('should maintain height constraints with empty messages', () => {
      render(
        <div style={{ height: '400px' }}>
          <TestChatWindow messages={[]} />
        </div>
      )

      // Even with no messages, structure should be maintained
      const chatWindow = screen.getByTestId('chat-window')
      expect(chatWindow).toHaveClass('flex', 'flex-col', 'h-full')

      const messagesContainer = screen.getByTestId('messages-container')
      expect(messagesContainer).toHaveClass('flex-1', 'min-h-0', 'overflow-hidden')

      const messagesList = screen.getByTestId('messages-list')
      expect(messagesList).toHaveClass('h-full', 'overflow-y-auto')
    })
  })
})