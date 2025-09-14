import PropTypes from 'prop-types'

function DeploymentBanner({ deploymentStatus }) {
  // Only show banner when deployment is in "pending" status (which maps to "running")
  if (!deploymentStatus || deploymentStatus.status !== 'pending') {
    return null
  }

  // Get the GitHub Actions URL from deployment status
  const actionUrl = deploymentStatus.details?.workflow_url

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
  deploymentStatus: PropTypes.shape({
    status: PropTypes.string,
    message: PropTypes.string,
    details: PropTypes.shape({
      workflow_url: PropTypes.string,
      commit_sha: PropTypes.string,
      workflow_name: PropTypes.string
    })
  })
}

export default DeploymentBanner