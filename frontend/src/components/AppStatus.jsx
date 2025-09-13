import { useState, useEffect } from 'react'
import PropTypes from 'prop-types'

function AppStatus({ app }) {
  const [prData, setPrData] = useState(null)
  const [deploymentData, setDeploymentData] = useState(null)

  useEffect(() => {
    // Extract PR data from app
    if (app?.pr_status) {
      setPrData(app.pr_status)
    }

    // Extract deployment data from app
    if (app?.deployment_status) {
      setDeploymentData(app.deployment_status)
    }
  }, [app])

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return '✅'
      case 'failure':
      case 'error':
        return '❌'
      case 'pending':
      case 'running':
        return '🔄'
      default:
        return '🔄'
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case 'success':
        return 'Passing'
      case 'failure':
      case 'error':
        return 'Failing'
      case 'pending':
      case 'running':
        return 'Running'
      default:
        return 'Checking...'
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'success':
        return 'bg-green-900/20 text-green-400 border-green-500'
      case 'failure':
      case 'error':
        return 'bg-red-900/20 text-red-400 border-red-500'
      case 'pending':
      case 'running':
        return 'bg-yellow-900/20 text-yellow-400 border-yellow-500'
      default:
        return 'bg-cyber-accent text-cyber-muted border-cyber-border'
    }
  }

  const getDraftStatusColor = (isDraft) => {
    return isDraft 
      ? 'bg-gray-900/20 text-gray-400 border-gray-500'
      : 'bg-green-900/20 text-green-400 border-green-500'
  }

  const getMergeableStatusColor = (mergeable) => {
    if (mergeable === null) return 'bg-yellow-900/20 text-yellow-400 border-yellow-500'
    return mergeable 
      ? 'bg-green-900/20 text-green-400 border-green-500'
      : 'bg-red-900/20 text-red-400 border-red-500'
  }

  const getMergeableText = (mergeable) => {
    if (mergeable === null) return 'Checking...'
    return mergeable ? 'Mergeable' : 'Conflicts'
  }

  const getProjectName = () => {
    return app?.name || 'project'
  }

  const getConversationId = () => {
    // Extract conversation ID from app data or generate from slug
    return app?.conversation_id || app?.slug || 'main'
  }

  const getFlyAppUrl = () => {
    const project = getProjectName()
    const conversation = getConversationId()
    return `https://${project}-${conversation}.fly.dev`
  }

  const getBranchName = () => {
    return app?.branch || app?.github_status?.branch || 'main'
  }

  const getBranchStatus = () => {
    // If we have PR data, use that for CI status
    if (prData) {
      return prData.ci_status
    }
    // Otherwise, use github_status for branch-level CI
    if (app?.github_status?.tests_passing === true) return 'success'
    if (app?.github_status?.tests_passing === false) return 'failure'
    if (app?.github_status?.tests_passing === null) return 'pending'
    return 'pending'
  }

  const getLastCommit = () => {
    return app?.github_status?.last_commit
  }

  const shouldShowNoPRMessage = () => {
    const branch = getBranchName()
    return !prData && branch !== 'main'
  }

  return (
    <div className="hacker-card">
      <div className="space-y-4">
        {/* Branch Information */}
        <div className="flex items-center gap-2">
          <span className="text-cyber-muted font-mono text-sm">Branch:</span>
          <code className="bg-cyber-accent px-2 py-1 rounded text-cyber-text font-mono text-sm border border-cyber-border">
            {getBranchName()}
          </code>
        </div>

        {/* PR Information (if exists) */}
        {prData && (
          <div className="flex items-center gap-3">
            <span className="text-cyber-muted font-mono text-sm">PR:</span>
            <a
              href={prData.html_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyber-text hover:text-blue-400 font-mono text-sm transition-colors duration-200"
            >
              #{prData.number} - {prData.title}
            </a>
          </div>
        )}

        {/* No PR message (only for non-main branches) */}
        {shouldShowNoPRMessage() && (
          <div className="text-cyber-muted font-mono text-sm">
            No active pull request found
          </div>
        )}

        {/* CI Status */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-cyber-muted font-mono text-sm">CI Status:</span>
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium font-mono border ${getStatusColor(getBranchStatus())}`}>
              {getStatusIcon(getBranchStatus())} {getStatusText(getBranchStatus())}
            </span>
          </div>

          {/* Individual Check Commits (from PR) */}
          {prData?.checks && prData.checks.length > 0 && (
            <div className="ml-4 space-y-1">
              {prData.checks.map((check, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`text-sm ${getStatusColor(check.status).split(' ')[1]}`}>
                      {getStatusIcon(check.status)}
                    </span>
                    <span className="text-cyber-text font-mono text-xs">{check.name}</span>
                  </div>
                  {check.details_url && (
                    <a
                      href={check.details_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyber-muted hover:text-blue-400 text-xs font-mono transition-colors duration-200"
                    >
                      View →
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Last Commit (if available) */}
        {getLastCommit() && (
          <div className="flex items-center gap-2">
            <span className="text-cyber-muted font-mono text-sm">Last commit:</span>
            <code className="bg-cyber-accent px-1 py-0.5 rounded text-xs text-cyber-text font-mono">
              {getLastCommit().substring(0, 7)}
            </code>
          </div>
        )}

        {/* PR-specific status (only if PR exists) */}
        {prData && (
          <>
            {/* Draft/Open Status */}
            <div className="flex items-center gap-2">
              <span className="text-cyber-muted font-mono text-sm">Status:</span>
              <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium font-mono border ${getDraftStatusColor(prData.draft)}`}>
                {prData.draft ? 'Draft' : 'Open'}
              </span>
            </div>

            {/* Mergeable Status */}
            <div className="flex items-center gap-2">
              <span className="text-cyber-muted font-mono text-sm">Mergeable:</span>
              <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium font-mono border ${getMergeableStatusColor(prData.mergeable)}`}>
                {getMergeableText(prData.mergeable)}
              </span>
            </div>

            {/* Files Changed */}
            {prData.changed_files && (
              <div className="flex items-center gap-2">
                <span className="text-cyber-muted font-mono text-sm">Files Changed:</span>
                <a
                  href={`${prData.html_url}/files`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 font-mono text-sm transition-colors duration-200"
                >
                  {prData.changed_files} files
                </a>
              </div>
            )}
          </>
        )}

        {/* Deploy CI Status */}
        <div className="flex items-center gap-2">
          <span className="text-cyber-muted font-mono text-sm">Deploy:</span>
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium font-mono border ${getStatusColor(deploymentData?.deploy_status || 'pending')}`}>
            {getStatusIcon(deploymentData?.deploy_status || 'pending')} {getStatusText(deploymentData?.deploy_status || 'pending')}
          </span>
        </div>

        {/* Fly.io App Link */}
        <div className="flex items-center gap-2">
          <span className="text-cyber-muted font-mono text-sm">App:</span>
          <a
            href={getFlyAppUrl()}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300 font-mono text-sm transition-colors duration-200"
          >
            {getFlyAppUrl()}
          </a>
        </div>

        {/* Deployment Status */}
        {deploymentData?.deployed !== undefined && (
          <div className="flex items-center gap-2">
            <span className="text-cyber-muted font-mono text-sm">Status:</span>
            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium font-mono border ${deploymentData.deployed ? 'bg-green-900/20 text-green-400 border-green-500' : 'bg-red-900/20 text-red-400 border-red-500'}`}>
              {deploymentData.deployed ? '🚀 Deployed' : '⏸️ Not Deployed'}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

AppStatus.propTypes = {
  app: PropTypes.shape({
    name: PropTypes.string,
    slug: PropTypes.string,
    conversation_id: PropTypes.string,
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
  })
}

export default AppStatus