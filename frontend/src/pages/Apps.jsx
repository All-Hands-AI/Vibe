import { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getUserUUID } from '../utils/uuid'
import ConfirmationModal from '../components/ConfirmationModal'
import { 
  getStatusIcon, 
  getStatusText, 
  getStatusColor, 
  getBranchName, 
  getBranchStatus, 
  getDeployStatus 
} from '../utils/statusUtils'

function Apps() {
  const navigate = useNavigate()
  const [apps, setApps] = useState([])
  const [loading, setLoading] = useState(true)
  const [appsWithDetails, setAppsWithDetails] = useState([])
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

  // Create slug for real-time display (allows trailing hyphens)
  const createSlugForDisplay = (name) => {
    console.log('🔧 createSlugForDisplay input:', JSON.stringify(name))
    
    const step1 = name.toLowerCase()
    console.log('🔧 Step 1 (toLowerCase):', JSON.stringify(step1))
    
    const step2 = step1.replace(/[^a-zA-Z0-9\s-]/g, '')
    console.log('🔧 Step 2 (remove invalid chars):', JSON.stringify(step2))
    
    const step3 = step2.replace(/\s+/g, '-')
    console.log('🔧 Step 3 (spaces to hyphens):', JSON.stringify(step3))
    
    const step4 = step3.replace(/-+/g, '-')
    console.log('🔧 Step 4 (collapse multiple hyphens):', JSON.stringify(step4))
    
    const step5 = step4.replace(/^-/g, '') // Only remove leading hyphens, keep trailing
    console.log('🔧 Step 5 (remove leading hyphens only):', JSON.stringify(step5))
    
    console.log('🔧 createSlugForDisplay final result:', JSON.stringify(step5))
    return step5
  }

  // Create final slug for submission (removes trailing hyphens)
  const createFinalSlug = (name) => {
    console.log('🔧 createFinalSlug input:', JSON.stringify(name))
    
    const result = name
      .toLowerCase()
      .replace(/[^a-zA-Z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '') // Remove both leading and trailing hyphens
    
    console.log('🔧 createFinalSlug result:', JSON.stringify(result))
    return result
  }



  // Fetch apps from backend
  const fetchApps = useCallback(async () => {
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
      
      const appsList = data.apps || []
      setApps(appsList)
      console.log('✅ Apps loaded successfully')
      
      // Fetch detailed data for each app
      if (appsList.length > 0) {
        await fetchAppsDetails(appsList)
      }
    } catch (err) {
      console.error('❌ Error fetching apps:', err)
      console.error('❌ Error stack:', err.stack)
      setError('Failed to load apps. Please try again.')
    } finally {
      setLoading(false)
      console.log('🔄 Fetch apps completed')
    }
  }, [])

  // Fetch detailed app data for each app
  const fetchAppsDetails = async (appsList) => {
    console.log('🔄 Fetching detailed data for', appsList.length, 'apps...')
    try {
      const uuid = getUserUUID()
      const headers = {
        'X-User-UUID': uuid
      }

      // Fetch details for all apps in parallel
      const detailPromises = appsList.map(async (app) => {
        try {
          console.log('📡 Fetching details for app:', app.slug)
          const response = await fetch(`/api/apps/${app.slug}`, { headers })
          
          if (!response || !response.ok) {
            console.warn('⚠️ Failed to fetch details for app:', app.slug)
            return app // Return original app data if details fetch fails
          }
          
          const detailedApp = await response.json()
          console.log('✅ Loaded details for app:', app.slug)
          return detailedApp
        } catch (err) {
          console.warn('⚠️ Error fetching details for app:', app.slug, err)
          return app // Return original app data if details fetch fails
        }
      })

      const appsWithDetailedData = await Promise.all(detailPromises)
      setAppsWithDetails(appsWithDetailedData)
      console.log('✅ All app details loaded successfully')
    } catch (err) {
      console.error('❌ Error fetching app details:', err)
      // If details fetching fails, use original apps data
      setAppsWithDetails(appsList)
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

    const slug = createFinalSlug(newAppName.trim())
    console.log('📝 App details:', { name: slug, slug })
    
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
        slug: slug
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
      setSuccess(`App "${slug}" created successfully!`)
      setNewAppName('')
      
      // Refresh apps list
      console.log('🔄 Refreshing apps list...')
      await fetchApps()
      
      // Redirect to the new app's page
      console.log('🔄 Redirecting to new app:', data.app.slug)
      navigate(`/apps/${data.app.slug}`)
      
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
    
    console.log('🗑️ Delete button clicked for app:', app.slug)
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

    console.log('🗑️ Confirming deletion of app:', app.slug)
    
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
      let successMessage = `App "${app.slug}" deleted successfully!`
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
  }, [fetchApps])

  // Clear error when user starts typing
  useEffect(() => {
    if (error && newAppName) {
      setError('')
    }
  }, [newAppName, error])

  return (
    <div className="min-h-screen bg-black text-cyber-text">
      <div className="max-w-6xl mx-auto px-6 py-8">
        <header className="text-left mb-8">
          <h1 className="text-4xl font-bold text-cyber-text mb-2 font-mono">🤙 OpenHands Vibe</h1>
        </header>

        {/* Create New App Form */}
        <section className="mb-8">
          <h2 className="text-2xl font-bold text-cyber-text mb-4 font-mono">Create New App</h2>
          <div className="hacker-card max-w-2xl">
            <form onSubmit={handleCreateApp} className="space-y-4">
              <div>
                <label htmlFor="appName" className="block text-sm font-medium text-cyber-text mb-2 font-mono">
                  <span className="text-cyber-muted">{'>'}</span> App Name:
                </label>
                <input
                  type="text"
                  id="appName"
                  value={newAppName}
                  onChange={(e) => {
                    const inputValue = e.target.value
                    console.log('📝 App name input onChange - raw input:', JSON.stringify(inputValue))
                    const slug = createSlugForDisplay(inputValue)
                    console.log('📝 App name input onChange - setting state to:', JSON.stringify(slug))
                    setNewAppName(slug)
                  }}
                  placeholder="Enter app name"
                  disabled={creating}
                  className={`w-full px-4 py-3 bg-black text-cyber-text font-mono border-2 transition-colors duration-200 focus:outline-none focus:border-neon-green ${
                    error ? 'border-red-500' : 'border-cyber-border'
                  }`}
                />
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
          <h2 className="text-2xl font-bold text-cyber-text mb-4 font-mono">Your Apps</h2>
          
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {(appsWithDetails.length > 0 ? appsWithDetails : apps).map((app) => (
                <Link 
                  key={app.slug} 
                  to={`/apps/${app.slug}`}
                  className="hacker-card transition-all duration-300 hover:transform hover:-translate-y-1 block cursor-pointer"
                >
                  <div className="p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <h3 className="text-xl font-semibold text-cyber-text mb-1 font-mono">{app.slug}</h3>
                      </div>
                      <button 
                        className="text-red-400 hover:text-red-300 text-lg p-2 hover:bg-red-900/20 rounded transition-colors duration-200 z-10 relative"
                        onClick={(e) => handleDeleteClick(app, e)}
                        title={`Delete app "${app.slug}"`}
                        aria-label={`Delete app "${app.slug}"`}
                      >
                        🗑️
                      </button>
                    </div>
                    
                    {/* Status Information */}
                    <div className="space-y-2">
                      {app.github_status || app.deployment_status || app.pr_status ? (
                        // Show actual status when detailed data is available
                        <>
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
                        </>
                      ) : (
                        // Show loading state when detailed data is not yet available
                        <div className="flex items-center gap-2 text-cyber-muted font-mono text-xs">
                          <div className="w-3 h-3 border border-cyber-muted border-t-transparent rounded-full animate-spin"></div>
                          <span>Loading status...</span>
                        </div>
                      )}
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
              Are you sure you want to delete the app <strong>&ldquo;{deleteModal.app.slug}&rdquo;</strong>?
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