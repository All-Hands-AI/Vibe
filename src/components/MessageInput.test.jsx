import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import MessageInput from './MessageInput'

describe('MessageInput', () => {
  it('renders with default placeholder', () => {
    render(<MessageInput onSendMessage={() => {}} />)
    expect(screen.getByPlaceholderText('Type your message...')).toBeInTheDocument()
  })

  it('renders with custom placeholder', () => {
    render(<MessageInput onSendMessage={() => {}} placeholder="Custom placeholder" />)
    expect(screen.getByPlaceholderText('Custom placeholder')).toBeInTheDocument()
  })

  it('disables input when disabled prop is true', () => {
    render(<MessageInput onSendMessage={() => {}} disabled={true} />)
    const textarea = screen.getByRole('textbox')
    const button = screen.getByRole('button')
    
    expect(textarea).toBeDisabled()
    expect(button).toBeDisabled()
  })

  it('calls onSendMessage when form is submitted', async () => {
    const mockSendMessage = vi.fn()
    const user = userEvent.setup()
    
    render(<MessageInput onSendMessage={mockSendMessage} />)
    
    const textarea = screen.getByRole('textbox')
    const button = screen.getByRole('button')
    
    await user.type(textarea, 'Test message')
    await user.click(button)
    
    expect(mockSendMessage).toHaveBeenCalledWith('Test message')
  })

  it('calls onSendMessage when Enter is pressed', async () => {
    const mockSendMessage = vi.fn()
    const user = userEvent.setup()
    
    render(<MessageInput onSendMessage={mockSendMessage} />)
    
    const textarea = screen.getByRole('textbox')
    
    await user.type(textarea, 'Test message')
    await user.keyboard('{Enter}')
    
    expect(mockSendMessage).toHaveBeenCalledWith('Test message')
  })

  it('does not call onSendMessage when Shift+Enter is pressed', async () => {
    const mockSendMessage = vi.fn()
    const user = userEvent.setup()
    
    render(<MessageInput onSendMessage={mockSendMessage} />)
    
    const textarea = screen.getByRole('textbox')
    
    await user.type(textarea, 'Test message')
    await user.keyboard('{Shift>}{Enter}{/Shift}')
    
    expect(mockSendMessage).not.toHaveBeenCalled()
  })

  it('clears input after sending message', async () => {
    const mockSendMessage = vi.fn()
    const user = userEvent.setup()
    
    render(<MessageInput onSendMessage={mockSendMessage} />)
    
    const textarea = screen.getByRole('textbox')
    
    await user.type(textarea, 'Test message')
    await user.keyboard('{Enter}')
    
    expect(textarea.value).toBe('')
  })

  it('does not send empty messages', async () => {
    const mockSendMessage = vi.fn()
    const user = userEvent.setup()
    
    render(<MessageInput onSendMessage={mockSendMessage} />)
    
    const button = screen.getByRole('button')
    
    await user.click(button)
    
    expect(mockSendMessage).not.toHaveBeenCalled()
  })

  it('trims whitespace from messages', async () => {
    const mockSendMessage = vi.fn()
    const user = userEvent.setup()
    
    render(<MessageInput onSendMessage={mockSendMessage} />)
    
    const textarea = screen.getByRole('textbox')
    
    await user.type(textarea, '  Test message  ')
    await user.keyboard('{Enter}')
    
    expect(mockSendMessage).toHaveBeenCalledWith('Test message')
  })
})