import { useState, useEffect, useCallback, useRef } from 'react'
import { getUserUUID } from '../utils/uuid'

/**
 * Custom hook for managing conversation messages and API interactions
 */
export function useConversation(projectId, conversationId) {
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
    if (!projectId || !conversationId) return

    try {
      console.log('🔄 Loading conversation:', { projectId, conversationId })
      
      const data = await apiCall(`/projects/${projectId}/conversations/${conversationId}`)
      console.log('📊 Conversation data:', data)
      
      setConversation(data)
      
      // Extract messages from conversation data
      if (data.messages && Array.isArray(data.messages)) {
        setMessages(data.messages)
        console.log('💬 Loaded messages:', data.messages.length)
      }
      
      setError('')
    } catch (err) {
      console.error('❌ Error loading conversation:', err)
      setError(err.message || 'Failed to load conversation')
    }
  }, [projectId, conversationId, apiCall])

  // Load conversation events
  const loadEvents = useCallback(async () => {
    if (!projectId || !conversationId) return

    try {
      console.log('🔄 Loading events for conversation:', conversationId)
      
      const data = await apiCall(`/projects/${projectId}/conversations/${conversationId}/events`)
      console.log('📊 Events data:', data)
      
      setEvents(data.events || [])
      
      // Check if we have new events (for polling)
      const newEventCount = data.events?.length || 0
      if (newEventCount > lastEventCountRef.current) {
        console.log('🆕 New events detected:', newEventCount - lastEventCountRef.current)
        lastEventCountRef.current = newEventCount
        
        // Reload conversation to get updated messages
        await loadConversation()
      }
      
    } catch (err) {
      console.error('❌ Error loading events:', err)
      // Don't set error state for events loading failure
      // as it's not critical for the main functionality
    }
  }, [projectId, conversationId, apiCall, loadConversation])

  // Send a message
  const sendMessage = useCallback(async (messageContent) => {
    if (!projectId || !conversationId || !messageContent.trim()) {
      throw new Error('Invalid message or conversation parameters')
    }

    setSending(true)
    
    try {
      console.log('📤 Sending message:', messageContent)
      
      const data = await apiCall(`/projects/${projectId}/conversations/${conversationId}/messages`, {
        method: 'POST',
        body: JSON.stringify({
          message: messageContent.trim()
        })
      })
      
      console.log('✅ Message sent successfully:', data)
      
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
      console.error('❌ Error sending message:', err)
      throw err
    } finally {
      setSending(false)
    }
  }, [projectId, conversationId, apiCall, loadConversation, loadEvents])

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
      if (!projectId || !conversationId) return

      setLoading(true)
      setError('')
      
      try {
        await loadConversation()
        await loadEvents()
      } catch (err) {
        console.error('❌ Error loading initial data:', err)
        setError(err.message || 'Failed to load conversation data')
      } finally {
        setLoading(false)
      }
    }

    loadInitialData()
  }, [projectId, conversationId, loadConversation, loadEvents])

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