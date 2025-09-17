import PropTypes from 'prop-types'

function DeploymentStatus({ deploymentStatus, appSlug, riffSlug }) {
  return (
    <div>
      {deploymentStatus ? (
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            {deploymentStatus.status === 'pending' && (
              <>
                <div className="w-3 h-3 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin"></div>
                <h3 className="text-sm font-semibold text-yellow-400 font-mono">🚀 Deploying...</h3>
              </>
            )}
            {deploymentStatus.status === 'success' && (
              <>
                <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                <h3 className="text-sm font-semibold text-green-400 font-mono">🚀 Live App</h3>
              </>
            )}
            {deploymentStatus.status === 'error' && (
              <>
                <div className="w-3 h-3 bg-red-400 rounded-full"></div>
                <h3 className="text-sm font-semibold text-red-400 font-mono">🚀 Deployment Failed</h3>
              </>
            )}
            <div className="flex items-center gap-3 text-xs">
              {deploymentStatus.details?.workflow_url && (
                <a
                  href={deploymentStatus.details.workflow_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-cyber-muted hover:text-blue-400 font-mono transition-colors duration-200 underline"
                >
                  GitHub
                </a>
              )}
              <a
                href={`https://fly.io/apps/${appSlug}-${riffSlug}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-cyber-muted hover:text-blue-400 font-mono transition-colors duration-200 underline"
              >
                Fly.io
              </a>
            </div>
          </div>
          <a
            href={`https://${appSlug}-${riffSlug}.fly.dev`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-cyber-muted hover:text-blue-400 font-mono text-xs transition-colors duration-200 underline"
          >
            {appSlug}-{riffSlug}.fly.dev
          </a>
        </div>
      ) : (
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-cyber-text font-mono">🚀 Live App</h3>
            <div className="flex items-center gap-3 text-xs">
              <a
                href="https://github.com/rbren/OpenVibe/actions"
                target="_blank"
                rel="noopener noreferrer"
                className="text-cyber-muted hover:text-blue-400 font-mono transition-colors duration-200 underline"
              >
                GitHub
              </a>
              <a
                href={`https://fly.io/apps/${appSlug}-${riffSlug}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-cyber-muted hover:text-blue-400 font-mono transition-colors duration-200 underline"
              >
                Fly.io
              </a>
            </div>
          </div>
          <a
            href={`https://${appSlug}-${riffSlug}.fly.dev`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-cyber-muted hover:text-blue-400 font-mono text-xs transition-colors duration-200 underline"
          >
            {appSlug}-{riffSlug}.fly.dev
          </a>
        </div>
      )}
    </div>
  )
}

DeploymentStatus.propTypes = {
  deploymentStatus: PropTypes.shape({
    status: PropTypes.string,
    details: PropTypes.shape({
      workflow_url: PropTypes.string
    })
  }),
  appSlug: PropTypes.string.isRequired,
  riffSlug: PropTypes.string.isRequired
}

export default DeploymentStatus