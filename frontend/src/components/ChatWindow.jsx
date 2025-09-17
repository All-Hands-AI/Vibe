import { useState, useEffect, useRef, useCallback } from 'react'
import PropTypes from 'prop-types'
import MessageList from './MessageList'
import MessageInput from './MessageInput'
import AgentStatusBar from './AgentStatusBar'

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
    console.log('📜 scrollToBottom called')
    console.log('📜 messagesEndRef.current:', messagesEndRef.current)
    console.log('📜 scrollContainerRef.current:', scrollContainerRef.current)
    
    if (messagesEndRef.current) {
      console.log('📜 Attempting to scroll to bottom using scrollIntoView')
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
      
      // Also try direct scroll as backup
      if (scrollContainerRef.current) {
        console.log('📜 Also trying direct scroll as backup')
        setTimeout(() => {
          if (scrollContainerRef.current) {
            scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight
          }
        }, 100)
      }
    } else {
      console.log('❌ messagesEndRef.current is null, cannot scroll')
    }
  }

  // Check if user is scrolled to bottom (or close to it)
  const isScrolledToBottom = () => {
    if (!scrollContainerRef.current) {
      console.log('🔍 isScrolledToBottom: No scroll container ref, defaulting to true')
      return true // Default to true if no container
    }
    
    const container = scrollContainerRef.current
    const threshold = 50 // Allow 50px tolerance
    const scrollTop = container.scrollTop
    const clientHeight = container.clientHeight
    const scrollHeight = container.scrollHeight
    const isAtBottom = scrollTop + clientHeight >= scrollHeight - threshold
    
    console.log('🔍 Scroll position check:', {
      scrollTop,
      clientHeight,
      scrollHeight,
      threshold,
      calculation: `${scrollTop} + ${clientHeight} >= ${scrollHeight} - ${threshold}`,
      result: `${scrollTop + clientHeight} >= ${scrollHeight - threshold}`,
      isAtBottom
    })
    
    return isAtBottom
  }

  // Handle scroll events (simplified - no longer tracking user scroll)
  const handleScroll = () => {
    // Scroll handler for MessageList component
  }

  // Fetch messages from API
  const fetchMessages = useCallback(async () => {
    console.log('🔄 fetchMessages called')
    console.log('🔄 Current loading state:', loading)
    console.log('🔄 Current messages count:', messages.length)
    
    // Check if user was at bottom before fetching
    const wasAtBottom = isScrolledToBottom()
    console.log('🔄 User was at bottom before fetch:', wasAtBottom)
    
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
      
      console.log('🔄 Fetched messages count:', newMessageCount)
      console.log('🔄 Previous messages count:', messages.length)
      
      // Check if messages actually changed
      const messagesChanged = JSON.stringify(newMessages) !== JSON.stringify(messages)
      console.log('🔄 Messages changed:', messagesChanged)
      
      // Only update messages if there's actually a change
      if (messagesChanged) {
        console.log('🔄 Updating messages state')
        setMessages(newMessages)
        setPreviousMessageCount(newMessageCount)
      }
      
      // Scroll to bottom if:
      // 1. Initial load (loading is true), OR
      // 2. User was at bottom and messages changed
      const shouldScroll = loading || (wasAtBottom && messagesChanged)
      console.log('🔄 Should scroll decision:', {
        loading,
        wasAtBottom,
        messagesChanged,
        shouldScroll
      })
      
      if (shouldScroll) {
        console.log('🔄 Scheduling scroll to bottom with requestAnimationFrame')
        // Use requestAnimationFrame to ensure DOM is updated
        requestAnimationFrame(() => {
          scrollToBottom()
        })
      } else {
        console.log('🔄 Not scrolling - conditions not met')
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
      console.log('💬 Message sent, fetching updated messages')
      await fetchMessages()
      
      // Always scroll to bottom after sending a message
      // (user just sent it, they should see it)
      console.log('💬 Scheduling scroll after sending message')
      requestAnimationFrame(() => {
        scrollToBottom()
      })
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
    <div className="h-full max-h-full flex flex-col bg-black border-t border-b border-gray-700 overflow-hidden">
      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-900/20 border-b border-red-500/30 flex-shrink-0">
          <p className="text-red-400 text-sm font-mono">⚠️ {error}</p>
        </div>
      )}

      {/* Messages Area - This should be the scrollable part */}
      <div className="flex-1 min-h-0">
        <MessageList 
          messages={messages} 
          userUuid={userUuid}
          scrollContainerRef={scrollContainerRef}
          onScroll={handleScroll}
          messagesEndRef={messagesEndRef}
        />
      </div>

      {/* Agent Status Bar */}
      <div className="flex-shrink-0">
        <AgentStatusBar 
          appSlug={app.slug}
          riffSlug={riff.slug}
        />
      </div>

      {/* Message Input */}
      <div className="border-t border-gray-700 flex-shrink-0">
        <MessageInput 
          onSendMessage={sendMessage}
          disabled={sending}
          placeholder="What's next?"
        />
      </div>
    </div>
  )
}

ChatWindow.propTypes = {
  app: PropTypes.shape({
    slug: PropTypes.string.isRequired
  }).isRequired,
  riff: PropTypes.shape({
    slug: PropTypes.string.isRequired
  }).isRequired,
  userUuid: PropTypes.string.isRequired
}

export default ChatWindow