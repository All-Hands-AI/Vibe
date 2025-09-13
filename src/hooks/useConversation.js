import { useState, useEffect, useCallback, useRef } from 'react'
import { getUserUUID } from '../utils/uuid'

/**
 * Custom hook for managing conversation messages and API interactions
 * @param {string} projectSlug - Project slug (not numerical ID)
 * @param {string} conversationId - Conversation ID
 */
export function useConversation(projectSlug, conversationId) {
  const [messages, setMessages] = useState([])
  const [events, setEvents] = useState([])
  const [conversation, setConversation] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)
  const [pollingEnabled, setPollingEnabled] = useState(true)
  
  const pollingIntervalRef = useRef(null)
  const lastEventCountRef = useRef(0)

  // Get user UUID for API calls
  const userUUID = getUserUUID()

  // API call helper with proper headers
  const apiCall = useCallback(async (endpoint, options = {}) => {
    const headers = {
      'X-User-UUID': userUUID,
      'Content-Type': 'application/json',
      ...options.headers
    }

    const response = await fetch(endpoint, {
      ...options,
      headers
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`API call failed: ${response.status} ${errorText}`)
    }

    return response.json()
  }, [userUUID])

  // Load conversation details
  const loadConversation = useCallback(async () => {
    if (!projectSlug || !conversationId) {
      console.log('⚠️ useConversation: Missing required params:', { projectSlug, conversationId })
      return
    }

    try {
      const conversationUrl = `/api/projects/${projectSlug}/conversations/${conversationId}`
      console.log('🔄 useConversation: Loading conversation from URL:', conversationUrl)
      console.log('📋 useConversation: Params:', { projectSlug, conversationId })
      
      const data = await apiCall(conversationUrl)
      console.log('📊 useConversation: Received conversation data:', data)
      
      setConversation(data)
      
      // Extract messages from conversation data
      if (data.messages && Array.isArray(data.messages)) {
        setMessages(data.messages)
        console.log('💬 useConversation: Loaded messages:', data.messages.length)
      }
      
      setError('')
    } catch (err) {
      console.error('❌ useConversation: Error loading conversation:', err)
      setError(err.message || 'Failed to load conversation')
    }
  }, [projectSlug, conversationId, apiCall])

  // Load conversation events
  const loadEvents = useCallback(async () => {
    if (!projectSlug || !conversationId) {
      console.log('⚠️ useConversation: Missing required params for events:', { projectSlug, conversationId })
      return
    }

    try {
      const eventsUrl = `/api/projects/${projectSlug}/conversations/${conversationId}/events`
      console.log('🔄 useConversation: Loading events from URL:', eventsUrl)
      console.log('📋 useConversation: Events params:', { projectSlug, conversationId })
      
      const data = await apiCall(eventsUrl)
      console.log('📊 useConversation: Received events data:', data)
      
      setEvents(data.events || [])
      
      // Check if we have new events (for polling)
      const newEventCount = data.events?.length || 0
      if (newEventCount > lastEventCountRef.current) {
        console.log('🆕 useConversation: New events detected:', newEventCount - lastEventCountRef.current)
        lastEventCountRef.current = newEventCount
        
        // Reload conversation to get updated messages
        await loadConversation()
      }
      
    } catch (err) {
      console.error('❌ useConversation: Error loading events:', err)
      // Don't set error state for events loading failure
      // as it's not critical for the main functionality
    }
  }, [projectSlug, conversationId, apiCall, loadConversation])

  // Send a message
  const sendMessage = useCallback(async (messageContent) => {
    if (!projectSlug || !conversationId || !messageContent.trim()) {
      console.error('❌ useConversation: Invalid sendMessage params:', { projectSlug, conversationId, messageContent: messageContent?.length })
      throw new Error('Invalid message or conversation parameters')
    }

    setSending(true)
    
    try {
      const messageUrl = `/api/projects/${projectSlug}/conversations/${conversationId}/messages`
      console.log('📤 useConversation: Sending message to URL:', messageUrl)
      console.log('📋 useConversation: Message params:', { projectSlug, conversationId })
      console.log('💬 useConversation: Message content:', messageContent)
      
      const data = await apiCall(messageUrl, {
        method: 'POST',
        body: JSON.stringify({
          message: messageContent.trim()
        })
      })
      
      console.log('✅ useConversation: Message sent successfully:', data)
      
      // Add the message to local state immediately for better UX
      const newMessage = {
        role: 'user',
        content: messageContent.trim(),
        timestamp: new Date().toISOString()
      }
      
      setMessages(prev => [...prev, newMessage])
      
      // Reload conversation to get any immediate responses
      setTimeout(() => {
        loadConversation()
        loadEvents()
      }, 500)
      
    } catch (err) {
      console.error('❌ useConversation: Error sending message:', err)
      throw err
    } finally {
      setSending(false)
    }
  }, [projectSlug, conversationId, apiCall, loadConversation, loadEvents])

  // Start polling for updates
  const startPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
    }

    console.log('🔄 Starting polling for conversation updates')
    
    pollingIntervalRef.current = setInterval(() => {
      if (pollingEnabled) {
        loadEvents()
      }
    }, 5000) // Poll every 5 seconds
  }, [pollingEnabled, loadEvents])

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      console.log('⏹️ Stopping polling')
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
  }, [])

  // Initial load
  useEffect(() => {
    const loadInitialData = async () => {
      if (!projectSlug || !conversationId) {
        console.log('⚠️ useConversation: Skipping initial load - missing params:', { projectSlug, conversationId })
        return
      }

      console.log('🚀 useConversation: Starting initial data load:', { projectSlug, conversationId })
      setLoading(true)
      setError('')
      
      try {
        await loadConversation()
        await loadEvents()
        console.log('✅ useConversation: Initial data load completed')
      } catch (err) {
        console.error('❌ useConversation: Error loading initial data:', err)
        setError(err.message || 'Failed to load conversation data')
      } finally {
        setLoading(false)
      }
    }

    loadInitialData()
  }, [projectSlug, conversationId, loadConversation, loadEvents])

  // Start/stop polling based on component visibility and state
  useEffect(() => {
    if (!loading && !error && pollingEnabled) {
      startPolling()
    } else {
      stopPolling()
    }

    return () => stopPolling()
  }, [loading, error, pollingEnabled, startPolling, stopPolling])

  // Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        setPollingEnabled(false)
        stopPolling()
      } else {
        setPollingEnabled(true)
        // Immediately check for updates when page becomes visible
        if (!loading && !error) {
          loadEvents()
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      stopPolling()
    }
  }, [loading, error, loadEvents, stopPolling])

  // Refresh conversation data
  const refresh = useCallback(async () => {
    setLoading(true)
    setError('')
    
    try {
      await loadConversation()
      await loadEvents()
    } catch (err) {
      setError(err.message || 'Failed to refresh conversation')
    } finally {
      setLoading(false)
    }
  }, [loadConversation, loadEvents])

  return {
    // Data
    messages,
    events,
    conversation,
    
    // State
    loading,
    error,
    sending,
    pollingEnabled,
    
    // Actions
    sendMessage,
    refresh,
    setPollingEnabled,
    
    // Utilities
    isPolling: !!pollingIntervalRef.current
  }
}