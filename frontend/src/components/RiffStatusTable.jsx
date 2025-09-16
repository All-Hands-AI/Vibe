import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getUserUUID } from '../utils/uuid'

const StatusBadge = ({ status, message, type = 'default' }) => {
  const getStatusColor = () => {
    switch (status) {
      case 'success':
        return 'bg-green-900/20 border-green-500 text-green-400'
      case 'pending':
      case 'running':
        return 'bg-yellow-900/20 border-yellow-500 text-yellow-400'
      case 'failure':
      case 'error':
        return 'bg-red-900/20 border-red-500 text-red-400'
      case 'idle':
        return 'bg-blue-900/20 border-blue-500 text-blue-400'
      default:
        return 'bg-gray-900/20 border-gray-500 text-gray-400'
    }
  }

  const getStatusIcon = () => {
    switch (status) {
      case 'success':
        return '✅'
      case 'pending':
        return '⏳'
      case 'running':
        return '🔄'
      case 'failure':
      case 'error':
        return '❌'
      case 'idle':
        return '💤'
      default:
        return '❓'
    }
  }

  return (
    <div className={`inline-flex items-center px-2 py-1 rounded-md border text-xs font-mono ${getStatusColor()}`}>
      <span className="mr-1">{getStatusIcon()}</span>
      <span>{message || status}</span>
    </div>
  )
}

const CommitInfo = ({ commit }) => {
  if (!commit || !commit.commit_sha) {
    return <span className="text-gray-500 text-xs">No commit</span>
  }

  const shortSha = commit.commit_sha.substring(0, 7)
  const shortMessage = commit.commit_message ? 
    (commit.commit_message.length > 50 ? 
      commit.commit_message.substring(0, 50) + '...' : 
      commit.commit_message) : 
    'No message'

  return (
    <div className="text-xs">
      {commit.commit_url ? (
        <a 
          href={commit.commit_url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-cyber-muted hover:text-neon-green font-mono"
        >
          {shortSha}
        </a>
      ) : (
        <span className="text-cyber-muted font-mono">{shortSha}</span>
      )}
      <div className="text-gray-500 mt-1" title={commit.commit_message}>
        {shortMessage}
      </div>
      {commit.commit_author && (
        <div className="text-gray-600 mt-1">
          by {commit.commit_author}
        </div>
      )}
    </div>
  )
}

const PRInfo = ({ pr }) => {
  if (!pr || !pr.has_pr) {
    return <span className="text-gray-500 text-xs">No PR</span>
  }

  const getStateColor = () => {
    switch (pr.pr_state) {
      case 'open':
        return 'text-green-400'
      case 'closed':
        return 'text-red-400'
      case 'merged':
        return 'text-purple-400'
      default:
        return 'text-gray-400'
    }
  }

  const getStateIcon = () => {
    switch (pr.pr_state) {
      case 'open':
        return '🔓'
      case 'closed':
        return '🔒'
      case 'merged':
        return '🔀'
      default:
        return '❓'
    }
  }

  return (
    <div className="text-xs">
      {pr.pr_url ? (
        <a 
          href={pr.pr_url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-cyber-muted hover:text-neon-green"
        >
          #{pr.pr_number}
        </a>
      ) : (
        <span className="text-cyber-muted">#{pr.pr_number}</span>
      )}
      <div className={`mt-1 ${getStateColor()}`}>
        <span className="mr-1">{getStateIcon()}</span>
        {pr.pr_state}
      </div>
      {pr.pr_title && (
        <div className="text-gray-500 mt-1" title={pr.pr_title}>
          {pr.pr_title.length > 30 ? pr.pr_title.substring(0, 30) + '...' : pr.pr_title}
        </div>
      )}
    </div>
  )
}

const RiffStatusTable = ({ appSlug }) => {
  const [statuses, setStatuses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [lastUpdated, setLastUpdated] = useState(null)

  const fetchStatuses = async () => {
    try {
      const uuid = getUserUUID()
      const headers = {
        'X-User-UUID': uuid
      }

      const response = await fetch(`/api/apps/${appSlug}/riffs/status`, { headers })
      
      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to fetch riff statuses: ${response.status} ${errorText}`)
      }

      const data = await response.json()
      setStatuses(data.statuses || [])
      setLastUpdated(new Date())
      setError('')
    } catch (err) {
      console.error('❌ Error fetching riff statuses:', err)
      setError(err.message || 'Failed to load riff statuses')
    } finally {
      setLoading(false)
    }
  }

  // Initial load
  useEffect(() => {
    fetchStatuses()
  }, [appSlug])

  // Auto-refresh every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchStatuses()
    }, 5000)

    return () => clearInterval(interval)
  }, [appSlug])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="w-10 h-10 border-4 border-gray-600 border-t-cyber-muted rounded-full animate-spin mb-4"></div>
        <p className="text-cyber-muted">Loading riff statuses...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-red-900/20 border border-red-500 rounded-md text-red-400">
        <p className="font-semibold">Error loading riff statuses</p>
        <p className="text-sm mt-1">{error}</p>
        <button 
          onClick={fetchStatuses}
          className="mt-2 px-3 py-1 bg-red-700 hover:bg-red-600 rounded text-sm transition-colors"
        >
          Retry
        </button>
      </div>
    )
  }

  if (statuses.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-cyber-muted text-lg">No riffs found. Create your first riff to see status information!</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-semibold text-cyber-text">Riff Status Dashboard</h3>
        <div className="text-xs text-gray-500">
          {lastUpdated && (
            <span>Last updated: {lastUpdated.toLocaleTimeString()}</span>
          )}
          <span className="ml-2">🔄 Auto-refresh: 5s</span>
        </div>
      </div>

      {/* Status Table */}
      <div className="hacker-card rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-800/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Riff
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Commit
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  PR
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  CI
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Deploy
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Agent
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {statuses.map((status, index) => (
                <tr 
                  key={status.riff.slug} 
                  className="hover:bg-gray-800/30 transition-colors"
                >
                  {/* Riff Name */}
                  <td className="px-4 py-4">
                    <div>
                      <Link 
                        to={`/apps/${appSlug}/riffs/${status.riff.slug}`}
                        className="text-cyber-text hover:text-neon-green font-semibold transition-colors"
                      >
                        {status.riff.slug}
                      </Link>
                      <div className="text-xs text-gray-500 mt-1">
                        {status.riff.message_count || 0} messages
                      </div>
                      {status.riff.last_message_at && (
                        <div className="text-xs text-gray-600 mt-1">
                          Last: {new Date(status.riff.last_message_at).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  </td>

                  {/* Commit Info */}
                  <td className="px-4 py-4">
                    <CommitInfo commit={status.commit} />
                  </td>

                  {/* PR Info */}
                  <td className="px-4 py-4">
                    <PRInfo pr={status.pr} />
                  </td>

                  {/* CI Status */}
                  <td className="px-4 py-4">
                    <StatusBadge 
                      status={status.ci.status} 
                      message={status.ci.message}
                      type="ci"
                    />
                    {status.ci.details && status.ci.details.latest_run_url && (
                      <div className="mt-1">
                        <a 
                          href={status.ci.details.latest_run_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-cyber-muted hover:text-neon-green"
                        >
                          View workflow →
                        </a>
                      </div>
                    )}
                  </td>

                  {/* Deploy Status */}
                  <td className="px-4 py-4">
                    <StatusBadge 
                      status={status.deploy.status} 
                      message={status.deploy.message}
                      type="deploy"
                    />
                    {status.deploy.details && status.deploy.details.workflow_url && (
                      <div className="mt-1">
                        <a 
                          href={status.deploy.details.workflow_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-cyber-muted hover:text-neon-green"
                        >
                          View deployment →
                        </a>
                      </div>
                    )}
                  </td>

                  {/* Agent Status */}
                  <td className="px-4 py-4">
                    <StatusBadge 
                      status={status.agent.status} 
                      message={status.agent.message}
                      type="agent"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer */}
      <div className="text-xs text-gray-500 text-center">
        Showing {statuses.length} riff{statuses.length !== 1 ? 's' : ''}
      </div>
    </div>
  )
}

export default RiffStatusTable