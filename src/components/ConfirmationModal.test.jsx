import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ConfirmationModal from './ConfirmationModal'

describe('ConfirmationModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onConfirm: vi.fn(),
    title: 'Test Modal',
    message: 'Are you sure you want to proceed?'
  }

  it('renders modal when isOpen is true', () => {
    render(<ConfirmationModal {...defaultProps} />)
    
    expect(screen.getByText('Test Modal')).toBeInTheDocument()
    expect(screen.getByText('Are you sure you want to proceed?')).toBeInTheDocument()
    expect(screen.getByText('Delete')).toBeInTheDocument()
    expect(screen.getByText('Cancel')).toBeInTheDocument()
  })

  it('does not render modal when isOpen is false', () => {
    render(<ConfirmationModal {...defaultProps} isOpen={false} />)
    
    expect(screen.queryByText('Test Modal')).not.toBeInTheDocument()
  })

  it('calls onClose when cancel button is clicked', () => {
    const onClose = vi.fn()
    render(<ConfirmationModal {...defaultProps} onClose={onClose} />)
    
    fireEvent.click(screen.getByText('Cancel'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('calls onConfirm when confirm button is clicked', () => {
    const onConfirm = vi.fn()
    render(<ConfirmationModal {...defaultProps} onConfirm={onConfirm} />)
    
    fireEvent.click(screen.getByText('Delete'))
    expect(onConfirm).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when close button (×) is clicked', () => {
    const onClose = vi.fn()
    render(<ConfirmationModal {...defaultProps} onClose={onClose} />)
    
    fireEvent.click(screen.getByLabelText('Close modal'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('shows loading state when isLoading is true', () => {
    render(<ConfirmationModal {...defaultProps} isLoading={true} />)
    
    expect(screen.getByText('Deleting...')).toBeInTheDocument()
    expect(screen.getByText('Deleting...')).toBeDisabled()
    expect(screen.getByText('Cancel')).toBeDisabled()
  })

  it('uses custom button text when provided', () => {
    render(
      <ConfirmationModal 
        {...defaultProps} 
        confirmText="Remove" 
        cancelText="Keep" 
      />
    )
    
    expect(screen.getByText('Remove')).toBeInTheDocument()
    expect(screen.getByText('Keep')).toBeInTheDocument()
  })

  it('applies destructive styling by default', () => {
    render(<ConfirmationModal {...defaultProps} />)
    
    const confirmButton = screen.getByText('Delete')
    expect(confirmButton).toHaveClass('modal-button-destructive')
  })

  it('applies primary styling when isDestructive is false', () => {
    render(<ConfirmationModal {...defaultProps} isDestructive={false} />)
    
    const confirmButton = screen.getByText('Delete')
    expect(confirmButton).toHaveClass('modal-button-primary')
  })
})