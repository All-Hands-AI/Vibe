import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import FirstRiffModal from './FirstRiffModal'

describe('FirstRiffModal', () => {
  it('renders modal when isOpen is true', () => {
    const mockOnClose = vi.fn()
    
    render(
      <FirstRiffModal 
        isOpen={true} 
        onClose={mockOnClose} 
        appName="test-app" 
      />
    )
    
    expect(screen.getByText('Welcome to Your First Riff!')).toBeInTheDocument()
    expect(screen.getByText('test-app')).toBeInTheDocument()
    expect(screen.getByText('🎯 What\'s happening now?')).toBeInTheDocument()
    expect(screen.getByText('⏱️ Timeline')).toBeInTheDocument()
    expect(screen.getByText('💬 What can you do?')).toBeInTheDocument()
    expect(screen.getByText('ℹ️ Pro Tip')).toBeInTheDocument()
  })

  it('does not render when isOpen is false', () => {
    const mockOnClose = vi.fn()
    
    render(
      <FirstRiffModal 
        isOpen={false} 
        onClose={mockOnClose} 
        appName="test-app" 
      />
    )
    
    expect(screen.queryByText('Welcome to Your First Riff!')).not.toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    const mockOnClose = vi.fn()
    
    render(
      <FirstRiffModal 
        isOpen={true} 
        onClose={mockOnClose} 
        appName="test-app" 
      />
    )
    
    const closeButton = screen.getByLabelText('Close modal')
    fireEvent.click(closeButton)
    
    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when "Got it!" button is clicked', () => {
    const mockOnClose = vi.fn()
    
    render(
      <FirstRiffModal 
        isOpen={true} 
        onClose={mockOnClose} 
        appName="test-app" 
      />
    )
    
    const gotItButton = screen.getByText('Got it! Let\'s go 🎉')
    fireEvent.click(gotItButton)
    
    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('displays the correct app name in the content', () => {
    const mockOnClose = vi.fn()
    
    render(
      <FirstRiffModal 
        isOpen={true} 
        onClose={mockOnClose} 
        appName="my-awesome-app" 
      />
    )
    
    expect(screen.getByText('my-awesome-app')).toBeInTheDocument()
  })

  it('contains timeline information', () => {
    const mockOnClose = vi.fn()
    
    render(
      <FirstRiffModal 
        isOpen={true} 
        onClose={mockOnClose} 
        appName="test-app" 
      />
    )
    
    expect(screen.getByText('Agent is working (~5 minutes)')).toBeInTheDocument()
    expect(screen.getByText('App deployment (~1-2 minutes)')).toBeInTheDocument()
    expect(screen.getByText('Your app will appear in the iframe')).toBeInTheDocument()
  })

  it('contains helpful information about what the user can do', () => {
    const mockOnClose = vi.fn()
    
    render(
      <FirstRiffModal 
        isOpen={true} 
        onClose={mockOnClose} 
        appName="test-app" 
      />
    )
    
    expect(screen.getByText(/You can chat with the AI agent in real-time/)).toBeInTheDocument()
    expect(screen.getByText(/Once the agent finishes and pushes its work/)).toBeInTheDocument()
  })
})