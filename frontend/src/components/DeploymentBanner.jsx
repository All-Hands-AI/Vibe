import PropTypes from 'prop-types'

function DeploymentBanner({ deployStatus, prStatus }) {
  // Only show banner when deployment is in "running" status
  if (deployStatus !== 'running') {
    return null
  }

  // Find the GitHub Actions URL from PR status checks
  const getGitHubActionUrl = () => {
    if (!prStatus?.checks) {
      return null
    }

    // Look for deployment-related checks first
    const deployCheck = prStatus.checks.find(check => 
      check.name && check.name.toLowerCase().includes('deploy')
    )
    
    if (deployCheck?.details_url) {
      return deployCheck.details_url
    }

    // If no deploy check found, look for any check with a details_url
    const anyCheck = prStatus.checks.find(check => check.details_url)
    return anyCheck?.details_url || null
  }

  const actionUrl = getGitHubActionUrl()

  return (
    <div className="bg-yellow-900 bg-opacity-30 border border-yellow-400 rounded-lg p-3 mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-yellow-400 font-mono text-sm">
            Hold tight, a new version is rolling out
          </span>
        </div>
        {actionUrl && (
          <a
            href={actionUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-yellow-400 hover:text-yellow-300 transition-colors duration-200 font-mono text-sm underline"
          >
            View Progress →
          </a>
        )}
      </div>
    </div>
  )
}

DeploymentBanner.propTypes = {
  deployStatus: PropTypes.string,
  prStatus: PropTypes.shape({
    checks: PropTypes.arrayOf(PropTypes.shape({
      name: PropTypes.string,
      status: PropTypes.string,
      conclusion: PropTypes.string,
      details_url: PropTypes.string
    }))
  })
}

export default DeploymentBanner