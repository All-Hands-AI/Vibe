import { useState, useEffect, useCallback } from 'react'
import PropTypes from 'prop-types'
import { 
  getAgentStatus, 
  playAgent, 
  pauseAgent, 
  resetAgent,
  startAgentStatusPolling, 
  getStatusColor as getAgentStatusColor,
  canPlayAgent,
  isAgentRunning,
  isAgentFinished,
  isAgentPaused
} from '../utils/agentService'

function AgentStatusBar({ appSlug, riffSlug }) {
  const [agentStatus, setAgentStatus] = useState(null)
  const [agentLoading, setAgentLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  // Handle agent status polling
  useEffect(() => {
    if (!appSlug || !riffSlug) return

    const stopPolling = startAgentStatusPolling(
      appSlug, 
      riffSlug, 
      (newStatus) => {
        setAgentStatus(newStatus)
        setAgentLoading(false)
      },
      3000
    )

    return () => stopPolling()
  }, [appSlug, riffSlug])

  const handleToggleAgent = useCallback(async () => {
    if (actionLoading || !agentStatus) return
    
    setActionLoading(true)
    
    try {
      const canPlay = canPlayAgent(agentStatus)
      
      if (canPlay) {
        await playAgent(appSlug, riffSlug)
      } else {
        await pauseAgent(appSlug, riffSlug)
      }
      
      const newStatus = await getAgentStatus(appSlug, riffSlug)
      setAgentStatus(newStatus)
    } catch (err) {
      console.error('❌ Failed to toggle agent:', err)
    } finally {
      setActionLoading(false)
    }
  }, [appSlug, riffSlug, agentStatus, actionLoading])

  const handleResetAgent = useCallback(async () => {
    if (actionLoading) return
    
    setActionLoading(true)
    
    try {
      await resetAgent(appSlug, riffSlug)
      const newStatus = await getAgentStatus(appSlug, riffSlug)
      setAgentStatus(newStatus)
    } catch (err) {
      console.error('❌ Failed to reset agent:', err)
    } finally {
      setActionLoading(false)
    }
  }, [appSlug, riffSlug, actionLoading])

  // Get user-friendly status text
  const getDisplayStatus = (status) => {
    if (!status) return 'Agent Ready'
    
    if (status.status === 'error') {
      return 'Agent Error'
    }
    
    if (status.status === 'stuck') {
      return 'Agent Stuck'
    }
    
    if (isAgentPaused(status)) {
      return 'Agent Paused'
    }
    
    if (isAgentRunning(status) && status.has_active_task) {
      return 'Agent Running'
    }
    
    return 'Agent Ready'
  }

  // Determine agent button state using helper functions
  const canPlay = canPlayAgent(agentStatus)
  const isRunning = isAgentRunning(agentStatus) && !isAgentFinished(agentStatus)

  return (
    <div className="flex items-center justify-between px-4 py-2 bg-gray-800">
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${
          isAgentRunning(agentStatus) && agentStatus?.has_active_task ? 'bg-neon-green animate-pulse' : 
          isAgentPaused(agentStatus) ? 'bg-yellow-400' :
          isAgentFinished(agentStatus) ? 'bg-green-400' :
          agentStatus?.status === 'error' ? 'bg-red-400' :
          agentStatus?.status === 'stuck' ? 'bg-orange-400 animate-pulse' :
          'bg-gray-400'
        }`}></div>
        <span className={`font-mono text-sm ${getAgentStatusColor(agentStatus)}`}>
          {agentLoading ? 'Loading...' : getDisplayStatus(agentStatus)}
        </span>
      </div>
      <div className="flex items-center gap-2">
        {/* Play/Pause Button */}
        <button
          onClick={handleToggleAgent}
          disabled={actionLoading || agentLoading}
          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm transition-colors duration-200 ${
            actionLoading || agentLoading
              ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
              : canPlay
              ? 'bg-neon-green bg-opacity-20 text-neon-green border border-neon-green hover:bg-opacity-30'
              : isRunning
              ? 'bg-yellow-400 bg-opacity-20 text-yellow-400 border border-yellow-400 hover:bg-opacity-30'
              : 'bg-gray-700 text-gray-400 cursor-not-allowed'
          }`}
        >
          {actionLoading ? (
            <div className="w-4 h-4 border border-gray-400 border-t-neon-green rounded-full animate-spin"></div>
          ) : canPlay ? (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          )}
        </button>
        
        {/* Reset Button */}
        <button
          onClick={handleResetAgent}
          disabled={actionLoading || agentLoading}
          title="Reset Agent"
          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm transition-colors duration-200 ${
            actionLoading || agentLoading
              ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
              : 'bg-red-400 bg-opacity-20 text-red-400 border border-red-400 hover:bg-opacity-30'
          }`}
        >
          {actionLoading ? (
            <div className="w-4 h-4 border border-gray-400 border-t-red-400 rounded-full animate-spin"></div>
          ) : (
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
            </svg>
          )}
        </button>
      </div>
    </div>
  )
}

AgentStatusBar.propTypes = {
  appSlug: PropTypes.string.isRequired,
  riffSlug: PropTypes.string.isRequired
}

export default AgentStatusBar