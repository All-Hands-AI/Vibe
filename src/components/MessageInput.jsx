import React, { useState, useRef } from 'react'

function MessageInput({ onSendMessage, disabled, placeholder = "Type your message..." }) {
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)
  const textareaRef = useRef(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!message.trim() || sending || disabled) {
      return
    }

    const messageToSend = message.trim()
    setMessage('')
    setSending(true)

    try {
      await onSendMessage(messageToSend)
    } catch (error) {
      console.error('Failed to send message:', error)
      // Restore the message if sending failed
      setMessage(messageToSend)
    } finally {
      setSending(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleTextareaChange = (e) => {
    setMessage(e.target.value)
    
    // Auto-resize textarea
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
    }
  }

  const isDisabled = disabled || sending || !message.trim()

  return (
    <div className="bg-gray-850 border border-gray-700 rounded-lg p-4">
      <form onSubmit={handleSubmit} className="flex flex-col gap-2">
        <div className="flex items-end gap-3 bg-gray-800 border border-gray-600 rounded-lg p-3 focus-within:border-primary-500 transition-colors">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder={disabled ? "Conversation not available" : placeholder}
            disabled={disabled || sending}
            className="flex-1 bg-transparent text-white placeholder-gray-400 border-none outline-none resize-none min-h-[20px] max-h-[120px] text-sm leading-relaxed disabled:opacity-60 disabled:cursor-not-allowed"
            rows={1}
          />
          <button
            type="submit"
            disabled={isDisabled}
            className={`flex items-center justify-center w-10 h-10 rounded-lg transition-all duration-200 ${
              isDisabled
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed opacity-60'
                : 'bg-primary-600 text-white hover:bg-primary-700 hover:-translate-y-0.5 active:translate-y-0'
            }`}
            title={isDisabled ? 'Enter a message to send' : 'Send message (Enter)'}
          >
            {sending ? (
              <div className="w-4 h-4 border-2 border-gray-300 border-t-white rounded-full animate-spin"></div>
            ) : (
              <svg 
                width="16" 
                height="16" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2"
                className="transform rotate-45"
              >
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22,2 15,22 11,13 2,9"></polygon>
              </svg>
            )}
          </button>
        </div>
        {sending && (
          <div className="flex items-center gap-2 text-sm text-gray-400 px-1">
            <div className="w-3 h-3 border border-gray-400 border-t-primary-400 rounded-full animate-spin"></div>
            <span>Sending message...</span>
          </div>
        )}
      </form>
    </div>
  )
}

export default MessageInput