import { useState, useRef } from 'react'
import PropTypes from 'prop-types'

function MessageInput({ onSendMessage, disabled = false, placeholder = 'Type a message...' }) {
  const [message, setMessage] = useState('')
  const [messageType, setMessageType] = useState('text')
  const textareaRef = useRef(null)
  const fileInputRef = useRef(null)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (message.trim() && !disabled) {
      onSendMessage(message, messageType)
      setMessage('')
      setMessageType('text')
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
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

  const getTypeIcon = (type) => {
    switch (type) {
      case 'code':
        return '💻'
      case 'file':
        return '📎'
      default:
        return '💬'
    }
  }

  return (
    <form onSubmit={handleSubmit} className="p-4">
      <div className="flex items-end space-x-3">
        {/* Message Type Selector */}
        <div className="flex flex-col space-y-1">
          <select
            value={messageType}
            onChange={(e) => setMessageType(e.target.value)}
            className="bg-gray-800 border border-gray-600 rounded px-2 py-1 text-xs text-cyber-text font-mono focus:outline-none focus:border-neon-green"
            disabled={disabled}
          >
            <option value="text">💬 Text</option>
            <option value="code">💻 Code</option>
          </select>
        </div>

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

        {/* Action Buttons */}
        <div className="flex space-x-2">
          {/* File Upload Button */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            className="p-2 bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-lg text-cyber-muted hover:text-cyber-text transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Upload file"
          >
            📎
          </button>

          {/* Send Button */}
          <button
            type="submit"
            disabled={disabled || !message.trim()}
            className="px-4 py-2 bg-neon-green/20 hover:bg-neon-green/30 border border-neon-green text-neon-green rounded-lg font-mono text-sm transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {disabled ? (
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 border-2 border-neon-green border-t-transparent rounded-full animate-spin"></div>
                <span>Sending...</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <span>{getTypeIcon(messageType)}</span>
                <span>Send</span>
              </div>
            )}
          </button>
        </div>
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileUpload}
        className="hidden"
        accept="*/*"
      />

      {/* Help Text */}
      <div className="mt-2 text-xs text-cyber-muted font-mono">
        Press Enter to send, Shift+Enter for new line
      </div>
    </form>
  )
}

MessageInput.propTypes = {
  onSendMessage: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
  placeholder: PropTypes.string
}

export default MessageInput