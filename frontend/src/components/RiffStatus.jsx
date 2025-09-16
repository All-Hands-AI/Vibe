import { useState, useEffect } from 'react'
import PropTypes from 'prop-types'
import { getUserUUID } from '../utils/uuid'
import CIStatus from './CIStatus'

/**
 * Get agent status display information
 */
function getAgentStatusDisplay(agentStatus) {
  if (!agentStatus) {
    return { icon: '❓', color: 'text-gray-400', label: 'Unknown' }
  }

  switch (agentStatus.status) {
    case 'running':
    case 'waiting_for_user':
      return { icon: '🟢', color: 'text-green-400', label: 'Running' }
    case 'paused':
      return { icon: '⏸️', color: 'text-yellow-400', label: 'Paused' }
    case 'finished':
      return { icon: '✅', color: 'text-blue-400', label: 'Finished' }
    case 'not_initialized':
      return { icon: '⚪', color: 'text-gray-400', label: 'Not started' }
    case 'error':
      return { icon: '❌', color: 'text-red-400', label: 'Error' }
    default:
      return { icon: '❓', color: 'text-gray-400', label: agentStatus.status || 'Unknown' }
  }
}

/**
 * Get deployment status display information
 */
function getDeploymentStatusDisplay(deploymentStatus) {
  if (!deploymentStatus) {
    return { icon: '❓', color: 'text-gray-400', label: 'Unknown' }
  }

  switch (deploymentStatus.status) {
    case 'success':
      return { icon: '🚀', color: 'text-green-400', label: 'Deployed' }
    case 'failure':
      return { icon: '💥', color: 'text-red-400', label: 'Failed' }
    case 'pending':
      return { icon: '⏳', color: 'text-yellow-400', label: 'Deploying' }
    case 'error':
      return { icon: '❌', color: 'text-red-400', label: 'Error' }
    default:
      return { icon: '❓', color: 'text-gray-400', label: deploymentStatus.status || 'Unknown' }
  }
}

function RiffStatus({ appSlug, riffSlug, compact = false }) {
  const [status, setStatus] = useState({
    pr_status: null,
    agent_status: null,
    deployment_status: null,
    commit_info: null
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!appSlug || !riffSlug) return

    const fetchStatus = async () => {
      try {
        setLoading(true)
        setError('')

        const uuid = getUserUUID()
        const headers = {
          'X-User-UUID': uuid
        }

        // Fetch all status data in parallel using existing endpoints
        const [prResponse, agentResponse, deploymentResponse] = await Promise.allSettled([
          fetch(`/api/apps/${appSlug}/riffs/${riffSlug}/pr-status`, { headers }),
          fetch(`/api/apps/${appSlug}/riffs/${riffSlug}/status`, { headers }),
          fetch(`/api/apps/${appSlug}/riffs/${riffSlug}/deployment`, { headers })
        ])

        const newStatus = {
          pr_status: null,
          agent_status: null,
          deployment_status: null,
          commit_info: null
        }

        // Process PR status
        if (prResponse.status === 'fulfilled' && prResponse.value.ok) {
          const prData = await prResponse.value.json()
          newStatus.pr_status = prData
          if (prData) {
            newStatus.commit_info = {
              hash: prData.commit_hash,
              hash_short: prData.commit_hash_short,
              message: prData.commit_message
            }
          }
        }

        // Process agent status
        if (agentResponse.status === 'fulfilled' && agentResponse.value.ok) {
          const agentData = await agentResponse.value.json()
          newStatus.agent_status = {
            status: agentData.status,
            is_running: agentData.status === 'running' || agentData.status === 'waiting_for_user',
            is_paused: agentData.status === 'paused',
            is_finished: agentData.status === 'finished'
          }
        }

        // Process deployment status
        if (deploymentResponse.status === 'fulfilled' && deploymentResponse.value.ok) {
          const deploymentData = await deploymentResponse.value.json()
          newStatus.deployment_status = deploymentData
        }

        setStatus(newStatus)
      } catch (err) {
        console.error('❌ Error fetching riff status:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchStatus()
  }, [appSlug, riffSlug])

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-xs text-gray-400">
        <div className="w-3 h-3 border border-gray-600 border-t-gray-400 rounded-full animate-spin"></div>
        <span>Loading status...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 text-xs text-red-400">
        <span>❌</span>
        <span>Status unavailable</span>
      </div>
    )
  }

  if (!status) {
    return null
  }

  const agentDisplay = getAgentStatusDisplay(status.agent_status)
  const deploymentDisplay = getDeploymentStatusDisplay(status.deployment_status)

  if (compact) {
    return (
      <div className="flex flex-wrap items-center gap-2 text-xs">
        {/* PR Info */}
        {status.pr_status && (
          <div className="flex items-center gap-1 text-blue-400">
            <span>🔀</span>
            <span>#{status.pr_status.number}</span>
          </div>
        )}

        {/* CI Status */}
        {status.pr_status && (
          <CIStatus prStatus={status.pr_status} />
        )}

        {/* Agent Status */}
        <div className={`flex items-center gap-1 ${agentDisplay.color}`}>
          <span className="text-xs">{agentDisplay.icon}</span>
          <span>{agentDisplay.label}</span>
        </div>

        {/* Deployment Status */}
        {status.deployment_status && (
          <div className={`flex items-center gap-1 ${deploymentDisplay.color}`}>
            <span className="text-xs">{deploymentDisplay.icon}</span>
            <span>{deploymentDisplay.label}</span>
          </div>
        )}

        {/* Commit Hash */}
        {status.commit_info?.hash_short && (
          <div className="flex items-center gap-1 text-gray-400 font-mono">
            <span>📝</span>
            <span>{status.commit_info.hash_short}</span>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* PR Information */}
      {status.pr_status && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-blue-400">🔀</span>
            <a
              href={status.pr_status.html_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 text-sm font-medium"
            >
              PR #{status.pr_status.number}: {status.pr_status.title}
            </a>
            {status.pr_status.draft && (
              <span className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded">
                Draft
              </span>
            )}
          </div>
          
          {/* CI Status */}
          <div className="ml-6">
            <CIStatus prStatus={status.pr_status} />
          </div>
        </div>
      )}

      {/* Agent Status */}
      <div className="flex items-center gap-2">
        <span className={`${agentDisplay.color}`}>{agentDisplay.icon}</span>
        <span className={`text-sm ${agentDisplay.color}`}>
          Agent: {agentDisplay.label}
        </span>
      </div>

      {/* Deployment Status */}
      {status.deployment_status && (
        <div className="flex items-center gap-2">
          <span className={`${deploymentDisplay.color}`}>{deploymentDisplay.icon}</span>
          <span className={`text-sm ${deploymentDisplay.color}`}>
            Deploy: {deploymentDisplay.label}
          </span>
        </div>
      )}

      {/* Commit Information */}
      {status.commit_info && (
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span>📝</span>
            <span className="font-mono">{status.commit_info.hash_short}</span>
          </div>
          {status.commit_info.message && (
            <div className="ml-6 text-xs text-gray-500 truncate">
              {status.commit_info.message}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

RiffStatus.propTypes = {
  appSlug: PropTypes.string.isRequired,
  riffSlug: PropTypes.string.isRequired,
  compact: PropTypes.bool,
}

export default RiffStatus