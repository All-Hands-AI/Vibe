import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MessageList from './MessageList'

describe('MessageList', () => {
  it('renders loading state', () => {
    render(<MessageList loading={true} />)
    expect(screen.getByText('Loading messages...')).toBeInTheDocument()
  })

  it('renders error state', () => {
    render(<MessageList error="Failed to load messages" />)
    expect(screen.getByText('Failed to load messages')).toBeInTheDocument()
  })

  it('renders empty state', () => {
    render(<MessageList messages={[]} />)
    expect(screen.getByText('No messages yet')).toBeInTheDocument()
    expect(screen.getByText('Start the conversation by sending your first message below.')).toBeInTheDocument()
  })

  it('renders messages correctly', () => {
    const messages = [
      {
        role: 'user',
        content: 'Hello, agent!',
        timestamp: '2025-01-01T12:00:00Z'
      },
      {
        role: 'agent',
        content: 'Hello! How can I help you today?',
        timestamp: '2025-01-01T12:01:00Z'
      }
    ]

    render(<MessageList messages={messages} />)
    
    expect(screen.getByText('Hello, agent!')).toBeInTheDocument()
    expect(screen.getByText('Hello! How can I help you today?')).toBeInTheDocument()
    expect(screen.getByText('You')).toBeInTheDocument()
    expect(screen.getByText('Agent')).toBeInTheDocument()
  })

  it('handles array content correctly', () => {
    const messages = [
      {
        role: 'user',
        content: [
          { text: 'Here is some text' },
          { text: 'And some more text' }
        ],
        timestamp: '2025-01-01T12:00:00Z'
      }
    ]

    render(<MessageList messages={messages} />)
    
    expect(screen.getByText('Here is some text')).toBeInTheDocument()
    expect(screen.getByText('And some more text')).toBeInTheDocument()
  })
})