import { useState } from 'react'
import PropTypes from 'prop-types'

/**
 * Determine the overall CI status based on individual checks
 * @param {Array} checks - Array of check objects with status and conclusion
 * @param {string} ciStatus - Overall CI status from GitHub API
 * @returns {string} - 'success', 'failure', 'pending', or 'unknown'
 */
function getOverallCIStatus(checks, ciStatus) {
  if (!checks || checks.length === 0) {
    // Fall back to the overall CI status if no individual checks
    return ciStatus || 'unknown'
  }

  let hasFailure = false
  let hasPending = false
  let hasSuccess = false

  for (const check of checks) {
    if (check.status === 'completed') {
      if (check.conclusion === 'failure' || check.conclusion === 'cancelled' || check.conclusion === 'timed_out') {
        hasFailure = true
      } else if (check.conclusion === 'success') {
        hasSuccess = true
      }
    } else if (check.status === 'in_progress' || check.status === 'queued' || check.status === 'pending') {
      hasPending = true
    }
  }

  // Priority: failure > pending > success
  if (hasFailure) return 'failure'
  if (hasPending) return 'pending'
  if (hasSuccess) return 'success'
  
  return 'unknown'
}

/**
 * Get status icon and color based on CI status
 */
function getStatusDisplay(status) {
  switch (status) {
    case 'success':
      return { icon: '✅', color: 'text-green-400', bgColor: 'bg-green-900/20', label: 'All checks passed' }
    case 'failure':
      return { icon: '❌', color: 'text-red-400', bgColor: 'bg-red-900/20', label: 'Some checks failed' }
    case 'pending':
      return { icon: '🟡', color: 'text-yellow-400', bgColor: 'bg-yellow-900/20', label: 'Checks in progress' }
    default:
      return { icon: '❓', color: 'text-gray-400', bgColor: 'bg-gray-900/20', label: 'Status unknown' }
  }
}

/**
 * Format check status for display
 */
function formatCheckStatus(check) {
  if (check.status === 'completed') {
    switch (check.conclusion) {
      case 'success':
        return { icon: '✅', color: 'text-green-400', label: 'Passed' }
      case 'failure':
        return { icon: '❌', color: 'text-red-400', label: 'Failed' }
      case 'cancelled':
        return { icon: '🚫', color: 'text-gray-400', label: 'Cancelled' }
      case 'timed_out':
        return { icon: '⏰', color: 'text-orange-400', label: 'Timed out' }
      case 'neutral':
        return { icon: '⚪', color: 'text-gray-400', label: 'Neutral' }
      default:
        return { icon: '❓', color: 'text-gray-400', label: check.conclusion || 'Unknown' }
    }
  } else if (check.status === 'in_progress') {
    return { icon: '🔄', color: 'text-blue-400', label: 'In progress' }
  } else if (check.status === 'queued' || check.status === 'pending') {
    return { icon: '⏳', color: 'text-yellow-400', label: 'Queued' }
  } else {
    return { icon: '❓', color: 'text-gray-400', label: check.status || 'Unknown' }
  }
}

function CIStatus({ prStatus }) {
  const [showPopover, setShowPopover] = useState(false)

  if (!prStatus || (!prStatus.checks && !prStatus.ci_status)) {
    return null
  }

  const overallStatus = getOverallCIStatus(prStatus.checks, prStatus.ci_status)
  const statusDisplay = getStatusDisplay(overallStatus)

  return (
    <div className="relative inline-block">
      <div
        className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-mono cursor-pointer transition-all duration-200 ${statusDisplay.color} ${statusDisplay.bgColor} hover:bg-opacity-30`}
        onMouseEnter={() => setShowPopover(true)}
        onMouseLeave={() => setShowPopover(false)}
      >
        <span className="text-xs">{statusDisplay.icon}</span>
        <span>CI: {statusDisplay.label}</span>
      </div>

      {/* Popover */}
      {showPopover && (prStatus.checks && prStatus.checks.length > 0) && (
        <div className="absolute top-full left-0 mt-2 w-80 bg-gray-900 border border-gray-700 rounded-lg shadow-xl z-50 p-4">
          <div className="text-sm font-mono text-cyber-text mb-3">
            <div className="font-semibold text-neon-green mb-2">CI Checks</div>
            <div className="space-y-2">
              {prStatus.checks.map((check, index) => {
                const checkDisplay = formatCheckStatus(check)
                return (
                  <div key={index} className="flex items-center justify-between gap-3 p-2 bg-gray-800 rounded">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <span className="text-xs">{checkDisplay.icon}</span>
                      <span className="text-xs text-cyber-muted truncate">{check.name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs ${checkDisplay.color}`}>{checkDisplay.label}</span>
                      {check.details_url && (
                        <a
                          href={check.details_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:text-blue-300 text-xs"
                          onClick={(e) => e.stopPropagation()}
                        >
                          🔗
                        </a>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
          
          {/* Overall status summary */}
          <div className="border-t border-gray-700 pt-3 mt-3">
            <div className="flex items-center gap-2 text-xs font-mono">
              <span className="text-cyber-muted">Overall:</span>
              <span className={`${statusDisplay.color}`}>
                {statusDisplay.icon} {statusDisplay.label}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

CIStatus.propTypes = {
  prStatus: PropTypes.shape({
    ci_status: PropTypes.string,
    checks: PropTypes.arrayOf(
      PropTypes.shape({
        name: PropTypes.string.isRequired,
        status: PropTypes.string.isRequired,
        conclusion: PropTypes.string,
        details_url: PropTypes.string,
      })
    ),
  }),
}

export default CIStatus