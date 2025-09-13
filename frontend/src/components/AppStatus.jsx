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
        return 'text-green-400'
      case 'failure':
      case 'error':
        return 'text-red-400'
      case 'pending':
      case 'running':
        return 'text-yellow-400'
      default:
        return 'text-cyber-muted'
    }
  }

  const getDraftStatusColor = (isDraft) => {
    return isDraft ? 'text-gray-400' : 'text-green-400'
  }

  const getMergeableStatusColor = (mergeable) => {
    if (mergeable === null) return 'text-yellow-400'
    return mergeable ? 'text-green-400' : 'text-red-400'
  }

  const getDraftStatusIcon = (isDraft) => {
    return isDraft ? '📝' : '🟢'
  }

  const getMergeableStatusIcon = (mergeable) => {
    if (mergeable === null) return '🔄'
    return mergeable ? '✅' : '⚠️'
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

  const getBranchUrl = () => {
    const branch = getBranchName()
    const githubUrl = app?.github_url
    if (!githubUrl) return null
    
    // If it's main branch, link to repo homepage
    if (branch === 'main') {
      return githubUrl
    }
    
    // Otherwise, link to the specific branch
    return `${githubUrl}/tree/${branch}`
  }

  return (
    <div className="hacker-card">
      <div className="space-y-4">
        {/* Branch Information */}
        <div className="flex items-center gap-3">
          <span className="text-cyber-muted font-mono text-sm min-w-[100px]">Branch:</span>
          {getBranchUrl() ? (
            <a
              href={getBranchUrl()}
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyber-text hover:text-blue-400 font-mono text-sm transition-colors duration-200"
            >
              🌿 {getBranchName()}
            </a>
          ) : (
            <span className="text-cyber-text font-mono text-sm">
              🌿 {getBranchName()}
            </span>
          )}
        </div>

        {/* PR Information (if exists) */}
        {prData && (
          <div className="flex items-center gap-3">
            <span className="text-cyber-muted font-mono text-sm min-w-[100px]">PR:</span>
            <a
              href={prData.html_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyber-text hover:text-blue-400 font-mono text-sm transition-colors duration-200"
            >
              🔗 #{prData.number} - {prData.title}
            </a>
          </div>
        )}

        {/* No PR message (only for non-main branches) */}
        {shouldShowNoPRMessage() && (
          <div className="flex items-center gap-3">
            <span className="text-cyber-muted font-mono text-sm min-w-[100px]">PR:</span>
            <span className="text-cyber-muted font-mono text-sm">
              ❌ No active pull request found
            </span>
          </div>
        )}

        {/* Last Commit (if available) */}
        {getLastCommit() && (
          <div className="flex items-center gap-3">
            <span className="text-cyber-muted font-mono text-sm min-w-[100px]">Last commit:</span>
            <span className="text-cyber-text font-mono text-sm">
              📝 {getLastCommit().substring(0, 7)}
            </span>
          </div>
        )}

        {/* CI Status */}
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <span className="text-cyber-muted font-mono text-sm min-w-[100px]">CI Status:</span>
            <span className={`font-mono text-sm ${getStatusColor(getBranchStatus())}`}>
              {getStatusIcon(getBranchStatus())} {getStatusText(getBranchStatus())}
            </span>
          </div>

          {/* Individual Check Commits (from PR) */}
          {prData?.checks && prData.checks.length > 0 && (
            <div className="ml-[115px] space-y-1">
              {prData.checks.map((check, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`text-sm ${getStatusColor(check.status)}`}>
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



        {/* PR-specific status (only if PR exists) */}
        {prData && (
          <>
            {/* Draft/Open Status */}
            <div className="flex items-center gap-3">
              <span className="text-cyber-muted font-mono text-sm min-w-[100px]">Status:</span>
              <span className={`font-mono text-sm ${getDraftStatusColor(prData.draft)}`}>
                {getDraftStatusIcon(prData.draft)} {prData.draft ? 'Draft' : 'Open'}
              </span>
            </div>

            {/* Mergeable Status */}
            <div className="flex items-center gap-3">
              <span className="text-cyber-muted font-mono text-sm min-w-[100px]">Mergeable:</span>
              <span className={`font-mono text-sm ${getMergeableStatusColor(prData.mergeable)}`}>
                {getMergeableStatusIcon(prData.mergeable)} {getMergeableText(prData.mergeable)}
              </span>
            </div>

            {/* Files Changed */}
            {prData.changed_files && (
              <div className="flex items-center gap-3">
                <span className="text-cyber-muted font-mono text-sm min-w-[100px]">Files Changed:</span>
                <a
                  href={`${prData.html_url}/files`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 font-mono text-sm transition-colors duration-200"
                >
                  📁 {prData.changed_files} files
                </a>
              </div>
            )}
          </>
        )}

        {/* Deploy CI Status */}
        <div className="flex items-center gap-3">
          <span className="text-cyber-muted font-mono text-sm min-w-[100px]">Deploy:</span>
          <span className={`font-mono text-sm ${getStatusColor(deploymentData?.deploy_status || 'pending')}`}>
            {getStatusIcon(deploymentData?.deploy_status || 'pending')} {getStatusText(deploymentData?.deploy_status || 'pending')}
          </span>
        </div>

        {/* Fly.io App Link */}
        <div className="flex items-center gap-3">
          <span className="text-cyber-muted font-mono text-sm min-w-[100px]">App:</span>
          <a
            href={getFlyAppUrl()}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300 font-mono text-sm transition-colors duration-200"
          >
            🚀 {getFlyAppUrl()}
          </a>
        </div>


      </div>
    </div>
  )
}

AppStatus.propTypes = {
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
  })
}

export default AppStatus