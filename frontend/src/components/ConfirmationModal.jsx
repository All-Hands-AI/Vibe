import { useEffect } from 'react'
import PropTypes from 'prop-types'

function ConfirmationModal({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title, 
  message, 
  confirmText = 'Delete', 
  cancelText = 'Cancel',
  isDestructive = true,
  isLoading = false 
}) {
  // Handle escape key press
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape' && isOpen && !isLoading) {
        onClose()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose, isLoading])

  // Handle backdrop click
  const handleBackdropClick = (event) => {
    if (event.target === event.currentTarget && !isLoading) {
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={handleBackdropClick}>
      <div className="terminal-window max-w-md w-full">
        <div className="terminal-header flex items-center justify-between">
          <h3 className="text-xl font-semibold font-mono">{title}</h3>
          {!isLoading && (
            <button 
              className="text-cyber-muted hover:text-cyber-text text-2xl leading-none transition-colors duration-200" 
              onClick={onClose}
              aria-label="Close modal"
            >
              ×
            </button>
          )}
        </div>
        
        <div className="terminal-content">
          <div className="text-cyber-text leading-relaxed font-mono">
            {message}
          </div>
        </div>
        
        <div className="flex gap-3 p-6 border-t border-cyber-border">
          <button 
            className="flex-1 btn-hacker disabled:opacity-50 disabled:cursor-not-allowed" 
            onClick={onClose}
            disabled={isLoading}
          >
            {cancelText}
          </button>
          <button 
            className={`flex-1 px-4 py-2 rounded-md font-medium font-mono transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed border-2 ${
              isDestructive 
                ? 'bg-red-600 text-white hover:bg-red-700 border-red-600' 
                : 'btn-hacker-primary'
            }`}
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? 'Deleting...' : confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}

ConfirmationModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onConfirm: PropTypes.func.isRequired,
  title: PropTypes.string.isRequired,
  message: PropTypes.oneOfType([PropTypes.string, PropTypes.node]).isRequired,
  confirmText: PropTypes.string,
  cancelText: PropTypes.string,
  isDestructive: PropTypes.bool,
  isLoading: PropTypes.bool
}

export default ConfirmationModal