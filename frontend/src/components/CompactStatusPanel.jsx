import { useState, useEffect, useCallback } from 'react'
import PropTypes from 'prop-types'
import { 
  getStatusIcon, 
  getStatusText, 
  getStatusColor, 
  getBranchStatus, 
  getDeployStatus 
} from '../utils/statusUtils'
import { 
  getAgentStatus, 
  playAgent, 
  pauseAgent, 
  startAgentStatusPolling, 
  getStatusDescription, 
  getStatusColor as getAgentStatusColor 
} from '../utils/agentService'

function CompactStatusPanel({ app, prStatus = null, appSlug, riffSlug }) {
  const [prData, setPrData] = useState(null)
  const [agentStatus, setAgentStatus] = useState(null)
  const [agentLoading, setAgentLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  // Handle PR status
  useEffect(() => {
    if (prStatus) {
      setPrData(prStatus)
    } else if (app?.pr_status) {
      setPrData(app.pr_status)
    } else {
      setPrData(null)
    }
  }, [app, prStatus])

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
      const canPlay = agentStatus.agent_paused || 
        (!agentStatus.running && !agentStatus.agent_finished && agentStatus.event_count <= 1)
      
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

  const getLastCommit = () => {
    return app?.github_status?.last_commit
  }

  const getFlyAppUrl = () => {
    const project = app?.name || 'project'
    const conversation = app?.conversation_id || app?.slug || 'main'
    return `https://${project}-${conversation}.fly.dev`
  }

  // Determine agent button state
  const canPlay = agentStatus && (
    agentStatus.agent_paused || 
    (!agentStatus.running && !agentStatus.agent_finished && agentStatus.event_count <= 1)
  )
  const isRunning = agentStatus && agentStatus.running && !agentStatus.agent_paused && !agentStatus.agent_finished

  return (
    <div className="hacker-card space-y-2">
      {/* Agent Status Row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            agentStatus?.running && agentStatus?.thread_alive ? 'bg-neon-green animate-pulse' : 
            agentStatus?.agent_paused ? 'bg-yellow-400' :
            agentStatus?.agent_finished ? 'bg-green-400' :
            agentStatus?.status === 'error' ? 'bg-red-400' :
            'bg-gray-400'
          }`}></div>
          <span className={`font-mono text-xs ${getAgentStatusColor(agentStatus)}`}>
            {agentLoading ? 'Loading...' : getStatusDescription(agentStatus)}
          </span>
        </div>
        <button
          onClick={handleToggleAgent}
          disabled={actionLoading || agentLoading}
          className={`w-6 h-6 rounded-full flex items-center justify-center text-xs transition-colors duration-200 ${
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
            <div className="w-3 h-3 border border-gray-400 border-t-neon-green rounded-full animate-spin"></div>
          ) : canPlay ? (
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          )}
        </button>
      </div>

      {/* PR Info Row - All on one line */}
      {prData && (
        <div className="flex items-center gap-2 text-xs font-mono">
          <a
            href={prData.html_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300 transition-colors duration-200 truncate flex-1"
          >
            #{prData.number} {prData.title}
          </a>
          {getLastCommit() && (
            <span className="text-cyber-muted">
              {getLastCommit().substring(0, 7)}
            </span>
          )}
          <span className={`${prData.draft ? 'text-gray-400' : 'text-green-400'}`}>
            {prData.draft ? '📝' : '🟢'}
          </span>
          <span className={`${getStatusColor(getBranchStatus(app))}`}>
            {getStatusIcon(getBranchStatus(app))}
          </span>
        </div>
      )}

      {/* Deploy Status Row */}
      <div className="flex items-center justify-between text-xs font-mono">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 border border-cyber-muted border-t-transparent rounded-full animate-spin"></div>
          <span className="text-cyber-muted">Loading deploy status...</span>
        </div>
        <a
          href={getFlyAppUrl()}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-400 hover:text-blue-300 transition-colors duration-200"
        >
          🚀
        </a>
      </div>
    </div>
  )
}

CompactStatusPanel.propTypes = {
  app: PropTypes.shape({
    name: PropTypes.string,
    slug: PropTypes.string,
    conversation_id: PropTypes.string,
    branch: PropTypes.string,
    github_url: PropTypes.string,
    github_status: PropTypes.shape({
      branch: PropTypes.string,
      tests_passing: PropTypes.bool,
      last_commit: PropTypes.string
    }),
    pr_status: PropTypes.shape({
      number: PropTypes.number,
      title: PropTypes.string,
      html_url: PropTypes.string,
      draft: PropTypes.bool,
      mergeable: PropTypes.bool,
      changed_files: PropTypes.number,
      ci_status: PropTypes.string,
      checks: PropTypes.arrayOf(PropTypes.shape({
        name: PropTypes.string,
        status: PropTypes.string,
        details_url: PropTypes.string
      }))
    }),
    deployment_status: PropTypes.shape({
      deploy_status: PropTypes.string,
      deployed: PropTypes.bool,
      app_url: PropTypes.string
    })
  }),

  prStatus: PropTypes.shape({
    number: PropTypes.number,
    title: PropTypes.string,
    html_url: PropTypes.string,
    draft: PropTypes.bool,
    mergeable: PropTypes.bool,
    changed_files: PropTypes.number,
    ci_status: PropTypes.string,
    deploy_status: PropTypes.string,
    checks: PropTypes.arrayOf(PropTypes.shape({
      name: PropTypes.string,
      status: PropTypes.string,
      details_url: PropTypes.string
    }))
  }),
  appSlug: PropTypes.string.isRequired,
  riffSlug: PropTypes.string.isRequired
}

export default CompactStatusPanel