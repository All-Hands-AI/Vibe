import { useState, useEffect, useCallback } from 'react'
import PropTypes from 'prop-types'
import { getUserUUID } from '../utils/uuid'

function RiffActionButtons({ appSlug, riffSlug }) {
  const [loadingStates, setLoadingStates] = useState({
    install: false,
    run: false,
    test: false,
    lint: false
  })
  
  const [actionStatus, setActionStatus] = useState({
    install: { status: 'none' },
    run: { status: 'none' },
    test: { status: 'none' },
    lint: { status: 'none' }
  })

  const executeAction = async (action) => {
    try {
      setLoadingStates(prev => ({ ...prev, [action]: true }))
      
      const uuid = getUserUUID()
      const headers = {
        'Content-Type': 'application/json',
        'X-User-UUID': uuid
      }

      const response = await fetch(`/api/apps/${appSlug}/riffs/${riffSlug}/actions/${action}`, {
        method: 'POST',
        headers
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to execute ${action}: ${response.status} ${errorText}`)
      }

      const result = await response.json()
      console.log(`✅ ${action} action executed:`, result)
      
      // Immediately fetch updated status
      fetchActionStatus()
      
    } catch (error) {
      console.error(`❌ Error executing ${action}:`, error)
      // You could add toast notifications here
    } finally {
      setLoadingStates(prev => ({ ...prev, [action]: false }))
    }
  }

  const fetchActionStatus = useCallback(async () => {
    try {
      const uuid = getUserUUID()
      const headers = {
        'Content-Type': 'application/json',
        'X-User-UUID': uuid
      }

      const response = await fetch(`/api/apps/${appSlug}/riffs/${riffSlug}/actions/status`, {
        method: 'GET',
        headers
      })

      if (response.ok) {
        const result = await response.json()
        if (result.success && result.actions) {
          setActionStatus(result.actions)
        }
      }
    } catch (error) {
      console.error('❌ Error fetching action status:', error)
    }
  }, [appSlug, riffSlug])

  // Fetch status on mount and periodically
  useEffect(() => {
    fetchActionStatus()
    const interval = setInterval(fetchActionStatus, 5000) // Poll every 5 seconds
    return () => clearInterval(interval)
  }, [fetchActionStatus])

  const actions = [
    { key: 'install', label: 'Install', icon: '📦', description: 'Install dependencies' },
    { key: 'run', label: 'Run', icon: '▶️', description: 'Run the application' },
    { key: 'test', label: 'Test', icon: '🧪', description: 'Run tests' },
    { key: 'lint', label: 'Lint', icon: '🔍', description: 'Run linting' }
  ]

  const getStatusIcon = (status) => {
    switch (status) {
      case 'sent': return '⏳'
      case 'executing': return '🔄'
      case 'completed': return '✅'
      case 'error': return '❌'
      default: return ''
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'sent': return 'text-yellow-400'
      case 'executing': return 'text-blue-400'
      case 'completed': return 'text-green-400'
      case 'error': return 'text-red-400'
      default: return 'text-gray-500'
    }
  }

  return (
    <div className="border-t border-gray-800 pt-4">
      <h3 className="text-sm font-medium text-cyber-muted mb-3">Quick Actions</h3>
      <div className="grid grid-cols-2 gap-2">
        {actions.map(({ key, label, icon, description }) => {
          const status = actionStatus[key]?.status || 'none'
          const isRunning = loadingStates[key]
          const statusIcon = getStatusIcon(status)
          const statusColor = getStatusColor(status)
          
          return (
            <div key={key} className="relative">
              <button
                onClick={() => executeAction(key)}
                disabled={isRunning}
                className={`
                  w-full flex items-center justify-center gap-2 px-3 py-2 rounded-md text-sm font-medium
                  transition-colors duration-200 border
                  ${isRunning
                    ? 'bg-gray-800 border-gray-700 text-gray-500 cursor-not-allowed'
                    : 'bg-gray-900 border-gray-700 text-cyber-text hover:bg-gray-800 hover:border-gray-600 hover:text-neon-green'
                  }
                `}
                title={`${description}${status !== 'none' ? ` - Status: ${status}` : ''}`}
              >
                {isRunning ? (
                  <>
                    <div className="w-4 h-4 border-2 border-gray-600 border-t-cyber-muted rounded-full animate-spin"></div>
                    <span>Running...</span>
                  </>
                ) : (
                  <>
                    <span>{icon}</span>
                    <span>{label}</span>
                  </>
                )}
              </button>
              {statusIcon && !isRunning && (
                <div className={`absolute -top-1 -right-1 text-xs ${statusColor}`}>
                  {statusIcon}
                </div>
              )}
            </div>
          )
        })}
      </div>
      
      {/* Status summary */}
      <div className="mt-3 text-xs text-gray-400">
        {Object.entries(actionStatus).some(([_, status]) => status.status !== 'none') && (
          <div className="space-y-1">
            {Object.entries(actionStatus)
              .filter(([_, status]) => status.status !== 'none')
              .map(([action, status]) => (
                <div key={action} className="flex justify-between items-center">
                  <span className="capitalize">{action}:</span>
                  <span className={`flex items-center gap-1 ${getStatusColor(status.status)}`}>
                    {getStatusIcon(status.status)}
                    <span>{status.status}</span>
                  </span>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  )
}

RiffActionButtons.propTypes = {
  appSlug: PropTypes.string.isRequired,
  riffSlug: PropTypes.string.isRequired
}

export default RiffActionButtons