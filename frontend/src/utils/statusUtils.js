/**
 * Shared utility functions for app status display
 * Used by both Apps page cards and AppStatus component
 */

export const getStatusIcon = (status) => {
  switch (status) {
    case 'success':
      return '✅'
    case 'failure':
    case 'error':
      return '❌'
    case 'pending':
    case 'running':
      return '🔄'
    case 'waiting':
      return '⏳'
    default:
      return '🔄'
  }
}

export const getStatusText = (status) => {
  switch (status) {
    case 'success':
      return 'Passing'
    case 'failure':
    case 'error':
      return 'Failing'
    case 'pending':
    case 'running':
      return 'Running'
    case 'waiting':
      return 'Waiting for status'
    default:
      return 'Checking...'
  }
}

export const getStatusColor = (status) => {
  switch (status) {
    case 'success':
      return 'text-green-400'
    case 'failure':
    case 'error':
      return 'text-red-400'
    case 'pending':
    case 'running':
      return 'text-yellow-400'
    case 'waiting':
      return 'text-blue-400'
    default:
      return 'text-cyber-muted'
  }
}

export const getBranchName = (app, riff) => {
  // If we have riff data, use the riff slug as the branch name
  if (riff?.slug) {
    return riff.slug
  }
  // Otherwise, fall back to app branch information
  return app?.branch || app?.github_status?.branch || 'main'
}

export const getBranchStatus = (app) => {
  // If we have PR data, use that for CI status
  if (app?.pr_status) {
    return app.pr_status.ci_status
  }
  // Otherwise, use github_status for branch-level CI
  if (app?.github_status?.tests_passing === true) return 'success'
  if (app?.github_status?.tests_passing === false) return 'failure'
  if (app?.github_status?.tests_passing === null) return 'pending'
  return 'pending'
}

export const getDeployStatus = (deploymentStatus) => {
  if (!deploymentStatus) return 'pending'
  
  // Map the new deployment status format to the old format for compatibility
  switch (deploymentStatus.status) {
    case 'success':
      return 'success'
    case 'error':
      return 'failure'
    case 'pending':
      return 'running'
    case 'waiting':
      return 'waiting'
    default:
      return 'pending'
  }
}