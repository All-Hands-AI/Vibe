import { useState, useRef } from 'react'
import PropTypes from 'prop-types'

function MessageInput({ onSendMessage, disabled = false, placeholder = 'Type a message...' }) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef(null)
  const fileInputRef = useRef(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (message.trim() && !disabled) {
      // Store reference before async operation
      const textareaElement = textareaRef.current
      
      try {
        await onSendMessage(message, 'text')
        setMessage('')
        
        // Reset textarea height and maintain focus
        if (textareaElement) {
          textareaElement.style.height = 'auto'
          // Use requestAnimationFrame to ensure DOM updates are complete
          requestAnimationFrame(() => {
            textareaElement.focus()
          })
        }
      } catch (error) {
        console.error('Error sending message:', error)
        // Still maintain focus even if there's an error
        if (textareaElement) {
          textareaElement.focus()
        }
      }
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleTextareaChange = (e) => {
    setMessage(e.target.value)
    
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }

  const handleFileUpload = (e) => {
    const file = e.target.files[0]
    if (file) {
      // For now, just send the filename as a message
      // In a real implementation, you'd upload the file first
      const fileMessage = `📎 ${file.name} (${(file.size / 1024).toFixed(1)} KB)`
      onSendMessage(fileMessage, 'file', {
        filename: file.name,
        size: `${(file.size / 1024).toFixed(1)} KB`,
        type: file.type
      })
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  return (
    <form onSubmit={handleSubmit} className="p-4">
      <div className="flex gap-3">
        {/* Message Input */}
        <div className="flex-1">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleTextareaChange}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            disabled={disabled}
            className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-cyber-text placeholder-cyber-muted resize-none focus:outline-none focus:border-neon-green transition-colors duration-200"
            style={{ minHeight: '40px', maxHeight: '120px' }}
            rows={1}
          />
        </div>

        {/* File Upload Button */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          className="h-10 w-10 flex-shrink-0 flex items-center justify-center bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-lg text-cyber-muted hover:text-cyber-text transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          title="Upload file"
        >
          📎
        </button>

        {/* Send Button */}
        <button
          type="submit"
          disabled={disabled || !message.trim()}
          className="h-10 px-4 flex-shrink-0 flex items-center justify-center bg-neon-green/20 hover:bg-neon-green/30 border border-neon-green text-neon-green rounded-lg font-mono text-sm transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {disabled ? (
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 border-2 border-neon-green border-t-transparent rounded-full animate-spin"></div>
              <span>Sending...</span>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <span>💬</span>
              <span>Send</span>
            </div>
          )}
        </button>
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileUpload}
        className="hidden"
        accept="*/*"
      />
    </form>
  )
}

MessageInput.propTypes = {
  onSendMessage: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
  placeholder: PropTypes.string
}

export default MessageInput