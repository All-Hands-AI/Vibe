import { useState, useEffect, useRef, useCallback } from 'react'
import PropTypes from 'prop-types'
import MessageList from './MessageList'
import MessageInput from './MessageInput'

function ChatWindow({ app, riff, userUuid }) {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)
  const [previousMessageCount, setPreviousMessageCount] = useState(0)
  const pollingRef = useRef(null)
  const messagesEndRef = useRef(null)
  const scrollContainerRef = useRef(null)

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // Handle scroll events (simplified - no longer tracking user scroll)
  const handleScroll = () => {
    // Scroll handler for MessageList component
  }

  // Fetch messages from API
  const fetchMessages = useCallback(async () => {
    try {
      const response = await fetch(`/api/apps/${app.slug}/riffs/${riff.slug}/messages`, {
        headers: {
          'X-User-UUID': userUuid
        }
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch messages: ${response.status}`)
      }

      const data = await response.json()
      const newMessages = data.messages || []
      const newMessageCount = newMessages.length
      
      // Only update messages if there's actually a change
      if (JSON.stringify(newMessages) !== JSON.stringify(messages)) {
        setMessages(newMessages)
        
        // Only scroll to bottom on initial load
        if (loading) {
          // Use a small delay to ensure DOM is updated
          setTimeout(() => {
            scrollToBottom()
          }, 100)
        }
        
        setPreviousMessageCount(newMessageCount)
      }
      
      setError('')
    } catch (err) {
      console.error('Error fetching messages:', err)
      setError(err.message || 'Failed to load messages')
    } finally {
      setLoading(false)
    }
  }, [app.slug, riff.slug, userUuid, messages, loading])

  // Send a new message
  const sendMessage = async (content, type = 'text', metadata = {}) => {
    if (!content.trim()) return

    setSending(true)
    try {
      const response = await fetch(`/api/apps/${app.slug}/riffs/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-UUID': userUuid
        },
        body: JSON.stringify({
          riff_slug: riff.slug,
          content: content.trim(),
          type,
          metadata
        })
      })

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.status}`)
      }

      // Immediately fetch messages to update the UI
      // Don't reset user scroll state - let them stay where they are
      await fetchMessages()
    } catch (err) {
      console.error('Error sending message:', err)
      setError(err.message || 'Failed to send message')
    } finally {
      setSending(false)
    }
  }

  // Start polling for new messages
  const startPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
    }
    
    pollingRef.current = setInterval(() => {
      fetchMessages()
    }, 2000) // Poll every 2 seconds
  }, [fetchMessages])

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  // Initial load and setup polling
  useEffect(() => {
    fetchMessages()
    startPolling()

    return () => {
      stopPolling()
    }
  }, [fetchMessages, startPolling, stopPolling])

  // Initialize previous message count when messages first load
  useEffect(() => {
    if (messages.length > 0 && previousMessageCount === 0) {
      setPreviousMessageCount(messages.length)
    }
  }, [messages, previousMessageCount])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-gray-600 border-t-cyber-muted rounded-full animate-spin"></div>
        <span className="ml-3 text-cyber-muted">Loading messages...</span>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-black border border-gray-700 rounded-lg">
      {/* Chat Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div>
          <h3 className="text-lg font-semibold text-cyber-text font-mono">
            💬 {riff.name}
          </h3>
          <p className="text-sm text-cyber-muted">
            {messages.length} message{messages.length !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span className="text-xs text-cyber-muted font-mono">Live</span>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-900/20 border-b border-red-500/30">
          <p className="text-red-400 text-sm font-mono">⚠️ {error}</p>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-hidden">
        <MessageList 
          messages={messages} 
          userUuid={userUuid}
          scrollContainerRef={scrollContainerRef}
          onScroll={handleScroll}
        />
        <div ref={messagesEndRef} />
      </div>

      {/* Message Input */}
      <div className="border-t border-gray-700">
        <MessageInput 
          onSendMessage={sendMessage}
          disabled={sending}
          placeholder={`Message ${riff.name}...`}
        />
      </div>
    </div>
  )
}

ChatWindow.propTypes = {
  app: PropTypes.shape({
    slug: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired
  }).isRequired,
  riff: PropTypes.shape({
    slug: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired
  }).isRequired,
  userUuid: PropTypes.string.isRequired
}

export default ChatWindow