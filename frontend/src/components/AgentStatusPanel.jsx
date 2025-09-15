import { useState, useEffect, useCallback } from 'react'
import PropTypes from 'prop-types'
import { 
  getAgentStatus, 
  playAgent, 
  pauseAgent, 
  startAgentStatusPolling, 
  getStatusDescription, 
  getStatusColor,
  canPlayAgent,
  canPauseAgent,
  isAgentRunning,
  isAgentFinished,
  isAgentPaused
} from '../utils/agentService'

function AgentStatusPanel({ appSlug, riffSlug }) {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState('')

  // Fetch initial status and start polling
  useEffect(() => {
    if (!appSlug || !riffSlug) return

    console.log('🔄 Starting agent status polling for:', { appSlug, riffSlug })
    
    const stopPolling = startAgentStatusPolling(
      appSlug, 
      riffSlug, 
      (newStatus) => {
        console.log('📊 Agent status update:', newStatus)
        setStatus(newStatus)
        setLoading(false)
        setError('')
      },
      3000 // Poll every 3 seconds
    )

    return () => {
      console.log('🛑 Stopping agent status polling')
      stopPolling()
    }
  }, [appSlug, riffSlug])

  const handlePlay = useCallback(async () => {
    if (actionLoading) return
    
    setActionLoading(true)
    setError('')
    
    try {
      console.log('▶️ Playing agent for:', { appSlug, riffSlug })
      await playAgent(appSlug, riffSlug)
      
      // Refresh status immediately
      const newStatus = await getAgentStatus(appSlug, riffSlug)
      setStatus(newStatus)
    } catch (err) {
      console.error('❌ Failed to play agent:', err)
      setError(`Failed to play agent: ${err.message}`)
    } finally {
      setActionLoading(false)
    }
  }, [appSlug, riffSlug, actionLoading])

  const handlePause = useCallback(async () => {
    if (actionLoading) return
    
    setActionLoading(true)
    setError('')
    
    try {
      console.log('⏸️ Pausing agent for:', { appSlug, riffSlug })
      await pauseAgent(appSlug, riffSlug)
      
      // Refresh status immediately
      const newStatus = await getAgentStatus(appSlug, riffSlug)
      setStatus(newStatus)
    } catch (err) {
      console.error('❌ Failed to pause agent:', err)
      setError(`Failed to pause agent: ${err.message}`)
    } finally {
      setActionLoading(false)
    }
  }, [appSlug, riffSlug, actionLoading])

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-cyber-text mb-3 font-mono">Agent Status</h3>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 border-2 border-gray-600 border-t-cyber-muted rounded-full animate-spin"></div>
          <span className="text-cyber-muted">Loading status...</span>
        </div>
      </div>
    )
  }

  const statusDescription = getStatusDescription(status)
  const statusColor = getStatusColor(status)
  
  // Use helper functions for cleaner logic
  const canPlay = canPlayAgent(status)
  const canPause = canPauseAgent(status)
  const agentRunning = isAgentRunning(status)
  const agentFinished = isAgentFinished(status)
  const agentPaused = isAgentPaused(status)
  
  // Determine button text based on state
  const playButtonText = status && status.event_count <= 1 ? 'Activate' : 'Play'

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-4">
      <h3 className="text-lg font-semibold text-cyber-text mb-3 font-mono">Agent Status</h3>
      
      {/* Status Display */}
      <div className="mb-4">
        <div className="flex items-center space-x-2 mb-2">
          <div className={`w-3 h-3 rounded-full ${
            agentRunning && (status?.has_active_task || status?.thread_alive) ? 'bg-neon-green animate-pulse' : 
            agentPaused ? 'bg-yellow-400' :
            agentFinished ? 'bg-green-400' :
            status?.status === 'error' || status?.agent_status === 'error' ? 'bg-red-400' :
            'bg-gray-400'
          }`}></div>
          <span className={`font-mono text-sm font-medium ${statusColor}`}>
            {statusDescription}
          </span>
        </div>
        
        {/* Additional Status Info */}
        {status && status.status === 'initialized' && (
          <div className="text-xs text-cyber-muted space-y-1">
            {status.conversation_id && (
              <div>ID: {status.conversation_id.substring(0, 8)}...</div>
            )}
            {status.event_count !== undefined && (
              <div>Events: {status.event_count}</div>
            )}
            {status.agent_status && (
              <div>Agent Status: {status.agent_status}</div>
            )}
            <div className="flex space-x-4">
              <span>Active Task: {status.has_active_task ? '✅' : '❌'}</span>
              <span>Running: {(status.is_running || status.running) ? '✅' : '❌'}</span>
              {status.thread_alive !== undefined && (
                <span>Thread: {status.thread_alive ? '✅' : '❌'}</span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Control Buttons */}
      <div className="flex space-x-2">
        <button
          onClick={handlePlay}
          disabled={!canPlay || actionLoading}
          className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
            canPlay && !actionLoading
              ? 'bg-neon-green bg-opacity-20 text-neon-green border border-neon-green hover:bg-opacity-30'
              : 'bg-gray-700 text-gray-400 border border-gray-600 cursor-not-allowed'
          }`}
        >
          {actionLoading ? (
            <div className="w-4 h-4 border-2 border-gray-400 border-t-neon-green rounded-full animate-spin"></div>
          ) : (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
            </svg>
          )}
          <span>{playButtonText}</span>
        </button>

        <button
          onClick={handlePause}
          disabled={!canPause || actionLoading}
          className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
            canPause && !actionLoading
              ? 'bg-yellow-400 bg-opacity-20 text-yellow-400 border border-yellow-400 hover:bg-opacity-30'
              : 'bg-gray-700 text-gray-400 border border-gray-600 cursor-not-allowed'
          }`}
        >
          {actionLoading ? (
            <div className="w-4 h-4 border-2 border-gray-400 border-t-yellow-400 rounded-full animate-spin"></div>
          ) : (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          )}
          <span>Pause</span>
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mt-3 p-2 bg-red-900 bg-opacity-20 border border-red-400 rounded text-red-400 text-xs">
          {error}
        </div>
      )}

      {/* Status Error Display */}
      {status?.status === 'error' && status?.error && (
        <div className="mt-3 p-2 bg-red-900 bg-opacity-20 border border-red-400 rounded text-red-400 text-xs">
          {status.error}
        </div>
      )}
    </div>
  )
}

AgentStatusPanel.propTypes = {
  appSlug: PropTypes.string.isRequired,
  riffSlug: PropTypes.string.isRequired
}

export default AgentStatusPanel