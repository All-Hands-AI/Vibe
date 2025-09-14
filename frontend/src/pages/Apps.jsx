import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getUserUUID } from '../utils/uuid'
import ConfirmationModal from '../components/ConfirmationModal'

function Apps() {
  const [apps, setApps] = useState([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [newAppName, setNewAppName] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  
  // Delete modal state
  const [deleteModal, setDeleteModal] = useState({
    isOpen: false,
    app: null,
    isDeleting: false
  })

  // Create slug from app name for preview
  const createSlug = (name) => {
    return name
      .toLowerCase()
      .replace(/[^a-zA-Z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '')
  }

  // Status helper functions (extracted from AppStatus component)
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

  const getBranchName = (app) => {
    return app?.branch || app?.github_status?.branch || 'main'
  }

  const getBranchStatus = (app) => {
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

  const getDeployStatus = (app) => {
    return app?.deployment_status?.deploy_status || 'pending'
  }

  // Fetch apps from backend
  const fetchApps = async () => {
    console.log('🔄 Fetching apps from backend...')
    try {
      setLoading(true)
      
      const uuid = getUserUUID()
      console.log('🆔 User UUID:', uuid)
      
      const url = '/api/apps'
      console.log('📡 Making request to:', url)
      
      const requestOptions = {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-User-UUID': uuid
        }
      }
      
      console.log('📡 Request options:', requestOptions)
      
      const response = await fetch(url, requestOptions)
      console.log('📡 Response status:', response?.status)
      console.log('📡 Response ok:', response?.ok)
      console.log('📡 Response headers:', response?.headers ? Object.fromEntries(response.headers.entries()) : 'N/A')
      
      if (!response || !response.ok) {
        const errorText = await response?.text() || 'Unknown error'
        console.error('❌ Fetch failed:', errorText)
        throw new Error(`Failed to fetch apps: ${response?.status} ${errorText}`)
      }
      
      const data = await response.json()
      console.log('📊 Received data:', data)
      console.log('📊 Apps count:', data.apps?.length || 0)
      
      setApps(data.apps || [])
      console.log('✅ Apps loaded successfully')
    } catch (err) {
      console.error('❌ Error fetching apps:', err)
      console.error('❌ Error stack:', err.stack)
      setError('Failed to load apps. Please try again.')
    } finally {
      setLoading(false)
      console.log('🔄 Fetch apps completed')
    }
  }

  // Create new app
  const handleCreateApp = async (e) => {
    e.preventDefault()
    console.log('🆕 Creating new app...')
    
    if (!newAppName.trim()) {
      console.warn('❌ App name is empty')
      setError('App name is required')
      return
    }

    const slug = createSlug(newAppName.trim())
    console.log('📝 App details:', { name: newAppName.trim(), slug })
    
    if (!slug) {
      console.warn('❌ Invalid slug generated')
      setError('Please enter a valid app name')
      return
    }

    try {
      setCreating(true)
      setError('')
      setSuccess('')

      const uuid = getUserUUID()
      console.log('🆔 User UUID:', uuid)

      const requestData = {
        name: newAppName.trim()
      }
      
      const requestOptions = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-UUID': uuid
        },
        body: JSON.stringify(requestData),
      }
      
      console.log('📡 Request options:', requestOptions)
      console.log('📡 Request body:', requestData)

      const response = await fetch('/api/apps', requestOptions)
      
      console.log('📡 Create response status:', response?.status)
      console.log('📡 Create response ok:', response?.ok)
      console.log('📡 Create response headers:', response?.headers ? Object.fromEntries(response.headers.entries()) : 'N/A')

      const data = await response.json()
      console.log('📊 Create response data:', data)

      if (!response.ok) {
        console.error('❌ Create app failed:', data)
        throw new Error(data.error || 'Failed to create app')
      }

      console.log('✅ App created successfully:', data.app)
      setSuccess(`App "${newAppName}" created successfully!`)
      setNewAppName('')
      
      // Refresh apps list
      console.log('🔄 Refreshing apps list...')
      await fetchApps()
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccess(''), 5000)
      
    } catch (err) {
      console.error('❌ Error creating app:', err)
      console.error('❌ Error stack:', err.stack)
      setError(err.message || 'Failed to create app. Please try again.')
    } finally {
      setCreating(false)
      console.log('🆕 Create app completed')
    }
  }

  // Handle delete app button click
  const handleDeleteClick = (app, event) => {
    event.preventDefault() // Prevent navigation to app detail
    event.stopPropagation() // Stop event bubbling
    
    console.log('🗑️ Delete button clicked for app:', app.name)
    setDeleteModal({
      isOpen: true,
      app: app,
      isDeleting: false
    })
  }

  // Handle delete confirmation
  const handleDeleteConfirm = async () => {
    const app = deleteModal.app
    if (!app) return

    console.log('🗑️ Confirming deletion of app:', app.name)
    
    try {
      setDeleteModal(prev => ({ ...prev, isDeleting: true }))
      setError('')
      setSuccess('')

      const uuid = getUserUUID()
      console.log('🆔 User UUID:', uuid)

      const requestOptions = {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-User-UUID': uuid
        }
      }
      
      console.log('📡 Delete request options:', requestOptions)

      const response = await fetch(`/api/apps/${app.slug}`, requestOptions)
      
      console.log('📡 Delete response status:', response?.status)
      console.log('📡 Delete response ok:', response?.ok)

      const data = await response.json()
      console.log('📊 Delete response data:', data)

      if (!response.ok) {
        console.error('❌ Delete app failed:', data)
        throw new Error(data.error || 'Failed to delete app')
      }

      console.log('✅ App deleted successfully:', data)
      
      // Show success message
      let successMessage = `App "${app.name}" deleted successfully!`
      if (data.warnings && data.warnings.length > 0) {
        successMessage += ` (Note: ${data.warnings.join(', ')})`
      }
      setSuccess(successMessage)
      
      // Close modal
      setDeleteModal({
        isOpen: false,
        app: null,
        isDeleting: false
      })
      
      // Refresh apps list
      console.log('🔄 Refreshing apps list...')
      await fetchApps()
      
      // Clear success message after 8 seconds (longer for delete confirmation)
      setTimeout(() => setSuccess(''), 8000)
      
    } catch (err) {
      console.error('❌ Error deleting app:', err)
      console.error('❌ Error stack:', err.stack)
      setError(err.message || 'Failed to delete app. Please try again.')
      
      // Keep modal open but stop loading state
      setDeleteModal(prev => ({ ...prev, isDeleting: false }))
    }
  }

  // Handle delete modal close
  const handleDeleteCancel = () => {
    if (deleteModal.isDeleting) return // Prevent closing while deleting
    
    console.log('❌ Delete cancelled')
    setDeleteModal({
      isOpen: false,
      app: null,
      isDeleting: false
    })
  }

  // Load apps on component mount
  useEffect(() => {
    fetchApps()
  }, [])

  // Clear error when user starts typing
  useEffect(() => {
    if (error && newAppName) {
      setError('')
    }
  }, [newAppName, error])

  return (
    <div className="min-h-screen bg-black text-cyber-text">
      <div className="max-w-6xl mx-auto px-8 py-16">
        <header className="text-center mb-16">
          <h1 className="text-5xl font-bold text-cyber-text mb-4 font-mono">Apps</h1>
          <p className="text-xl text-cyber-muted font-mono">Manage your OpenVibe apps</p>
        </header>

        {/* Create New App Form */}
        <section className="mb-16">
          <h2 className="text-3xl font-bold text-cyber-text mb-8 font-mono">Create New App</h2>
          <div className="hacker-card max-w-2xl">
            <form onSubmit={handleCreateApp} className="space-y-6">
              <div>
                <label htmlFor="appName" className="block text-sm font-medium text-cyber-text mb-2 font-mono">
                  <span className="text-cyber-muted">{'>'}</span> App Name:
                </label>
                <input
                  type="text"
                  id="appName"
                  value={newAppName}
                  onChange={(e) => setNewAppName(e.target.value)}
                  placeholder="Enter app name"
                  disabled={creating}
                  className={`w-full px-4 py-3 bg-black text-cyber-text font-mono border-2 transition-colors duration-200 focus:outline-none focus:border-neon-green ${
                    error ? 'border-red-500' : 'border-cyber-border'
                  }`}
                />
                {newAppName && (
                  <div className="mt-2 text-sm text-cyber-muted font-mono">
                    Slug: <code className="bg-cyber-accent px-2 py-1 rounded text-cyber-text">{createSlug(newAppName)}</code>
                  </div>
                )}
              </div>
              
              <button 
                type="submit" 
                disabled={creating || !newAppName.trim()}
                className="btn-hacker-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creating ? 'Creating...' : 'Create App'}
              </button>
            </form>

            {error && (
              <div className="mt-4 p-4 bg-red-900/20 border border-red-500 rounded-md text-red-400 font-mono">
                {error}
              </div>
            )}

            {success && (
              <div className="mt-4 p-4 bg-green-900/20 border border-green-500 rounded-md text-green-400 font-mono">
                {success}
              </div>
            )}
          </div>
        </section>

        {/* Apps List */}
        <section>
          <h2 className="text-3xl font-bold text-cyber-text mb-8 font-mono">Your Apps</h2>
          
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16">
              <div className="w-10 h-10 border-4 border-cyber-border border-t-transparent rounded-full animate-spin mb-4"></div>
              <p className="text-cyber-muted font-mono">Loading apps...</p>
            </div>
          ) : apps.length === 0 ? (
            <div className="text-center py-16">
              <p className="text-cyber-muted text-lg font-mono">No apps yet. Create your first app above!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {apps.map((app) => (
                <Link 
                  key={app.slug} 
                  to={`/apps/${app.slug}`}
                  className="hacker-card transition-all duration-300 hover:transform hover:-translate-y-1 block cursor-pointer"
                >
                  <div className="p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <h3 className="text-xl font-semibold text-cyber-text mb-1 font-mono">{app.name}</h3>
                        <span className="text-sm text-cyber-muted font-mono">{app.slug}</span>
                      </div>
                      <button 
                        className="text-red-400 hover:text-red-300 text-lg p-2 hover:bg-red-900/20 rounded transition-colors duration-200 z-10 relative"
                        onClick={(e) => handleDeleteClick(app, e)}
                        title={`Delete app "${app.name}"`}
                        aria-label={`Delete app "${app.name}"`}
                      >
                        🗑️
                      </button>
                    </div>
                    
                    <div className="space-y-3">
                      <p className="text-sm text-cyber-muted font-mono">
                        Created: {new Date(app.created_at).toLocaleDateString()}
                      </p>
                      
                      {app.github_url && (
                        <div className="text-sm text-green-400 bg-green-900/20 px-3 py-1 rounded font-mono">
                          GitHub repository available
                        </div>
                      )}
                      
                      {/* Status Information */}
                      <div className="space-y-2 pt-2 border-t border-cyber-border">
                        {/* Branch */}
                        <div className="flex items-center gap-2">
                          <span className="text-cyber-muted font-mono text-xs">Branch:</span>
                          <span className="text-cyber-text font-mono text-xs">
                            🌿 {getBranchName(app)}
                          </span>
                        </div>
                        
                        {/* CI Status */}
                        <div className="flex items-center gap-2">
                          <span className="text-cyber-muted font-mono text-xs">CI:</span>
                          <span className={`font-mono text-xs ${getStatusColor(getBranchStatus(app))}`}>
                            {getStatusIcon(getBranchStatus(app))} {getStatusText(getBranchStatus(app))}
                          </span>
                        </div>
                        
                        {/* Deploy Status */}
                        <div className="flex items-center gap-2">
                          <span className="text-cyber-muted font-mono text-xs">Deploy:</span>
                          <span className={`font-mono text-xs ${getStatusColor(getDeployStatus(app))}`}>
                            {getStatusIcon(getDeployStatus(app))} {getStatusText(getDeployStatus(app))}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
      
      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={deleteModal.isOpen}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        title="Delete App"
        message={
          deleteModal.app ? (
            <>
              Are you sure you want to delete the app <strong>&ldquo;{deleteModal.app.name}&rdquo;</strong>?
              <br /><br />
              <strong>This action will permanently delete:</strong>
              <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
                <li>The app from OpenVibe</li>
                {deleteModal.app.github_url && <li>The associated GitHub repository</li>}
                <li>The associated Fly.io application</li>
                <li>All app riffs and data</li>
              </ul>
              <br />
              <strong>This action cannot be undone.</strong>
            </>
          ) : ''
        }
        confirmText="Delete App"
        cancelText="Cancel"
        isDestructive={true}
        isLoading={deleteModal.isDeleting}
      />
    </div>
  )
}

export default Apps