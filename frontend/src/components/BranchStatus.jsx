import { useState, useEffect } from 'react'
import PropTypes from 'prop-types'

function BranchStatus({ app }) {
  const [branchName, setBranchName] = useState('main')
  const [failingChecks, setFailingChecks] = useState([])

  useEffect(() => {
    // Extract branch name from GitHub status or default to 'main'
    if (app?.github_status?.branch) {
      setBranchName(app.github_status.branch)
    }

    // Extract failing checks from GitHub status
    if (app?.github_status?.failing_checks) {
      setFailingChecks(app.github_status.failing_checks)
    } else if (app?.github_status?.tests_passing === false) {
      // If we don't have detailed failing checks but know tests are failing,
      // create a generic failing check entry
      setFailingChecks([
        {
          name: 'CI Tests',
          status: 'failure',
          conclusion: 'failure',
          details_url: app.github_url ? `${app.github_url}/actions` : null
        }
      ])
    } else {
      setFailingChecks([])
    }
  }, [app])

  const getStatusIcon = (status) => {
    switch (status) {
      case true:
        return '✅'
      case false:
        return '❌'
      case null:
        return '🔄'
      default:
        return '🔄'
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case true:
        return 'Passing'
      case false:
        return 'Failing'
      case null:
        return 'Running'
      default:
        return 'Checking...'
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case true:
        return 'bg-green-900/20 text-green-400 border-green-500'
      case false:
        return 'bg-red-900/20 text-red-400 border-red-500'
      case null:
        return 'bg-yellow-900/20 text-yellow-400 border-yellow-500'
      default:
        return 'bg-cyber-accent text-cyber-muted border-cyber-border'
    }
  }

  return (
    <div className="hacker-card">
      <div className="mb-4">
        <h3 className="text-xl font-semibold text-cyber-text mb-2 font-mono">Branch Status</h3>
        <div className="flex items-center gap-2 mb-3">
          <span className="text-cyber-muted font-mono text-sm">Branch:</span>
          <code className="bg-cyber-accent px-2 py-1 rounded text-cyber-text font-mono text-sm border border-cyber-border">
            {branchName}
          </code>
        </div>
      </div>

      <div className="mb-4">
        <h4 className="text-lg font-medium text-cyber-text mb-3 font-mono">CI/CD Status</h4>
        <div className="mb-3">
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium font-mono border ${getStatusColor(app?.github_status?.tests_passing)}`}>
            {getStatusIcon(app?.github_status?.tests_passing)} {getStatusText(app?.github_status?.tests_passing)}
          </span>
        </div>
        
        {app?.github_status?.last_commit && (
          <p className="text-cyber-muted text-sm font-mono mb-3">
            Last commit: <code className="bg-cyber-accent px-1 py-0.5 rounded text-xs">{app.github_status.last_commit.substring(0, 7)}</code>
          </p>
        )}
      </div>

      {failingChecks.length > 0 && (
        <div>
          <h4 className="text-lg font-medium text-red-400 mb-3 font-mono">Failing Checks</h4>
          <div className="space-y-2">
            {failingChecks.map((check, index) => (
              <div key={index} className="bg-red-900/10 border border-red-500/30 rounded-md p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-red-400">❌</span>
                    <span className="text-cyber-text font-mono text-sm font-medium">{check.name}</span>
                  </div>
                  {check.details_url && (
                    <a
                      href={check.details_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyber-muted hover:text-red-400 text-xs font-mono transition-colors duration-200"
                    >
                      View Details →
                    </a>
                  )}
                </div>
                {check.conclusion && check.conclusion !== 'failure' && (
                  <p className="text-cyber-muted text-xs font-mono mt-1">
                    Status: {check.conclusion}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

BranchStatus.propTypes = {
  app: PropTypes.shape({
    github_url: PropTypes.string,
    github_status: PropTypes.shape({
      branch: PropTypes.string,
      tests_passing: PropTypes.bool,
      last_commit: PropTypes.string,
      failing_checks: PropTypes.arrayOf(PropTypes.shape({
        name: PropTypes.string,
        status: PropTypes.string,
        conclusion: PropTypes.string,
        details_url: PropTypes.string
      }))
    })
  })
}

export default BranchStatus