import { useState, useEffect, useCallback } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { getUserUUID } from '../utils/uuid'
import AppStatus from '../components/AppStatus'
import ConfirmationModal from '../components/ConfirmationModal'

function AppDetail() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const [app, setApp] = useState(null)
  const [riffs, setRiffs] = useState([])
  const [loading, setLoading] = useState(true)
  const [riffsLoading, setRiffsLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newRiffName, setNewRiffName] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  
  // Delete modal state
  const [deleteModal, setDeleteModal] = useState({
    isOpen: false,
    riff: null,
    isDeleting: false
  })





  // Create slug from riff name
  const createSlug = (name) => {
    return name
      .toLowerCase()
      .replace(/[^a-zA-Z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '')
  }

  // Fetch app details
  const fetchApp = useCallback(async () => {
    console.log('🔄 Fetching app details for slug:', slug)
    try {
      setLoading(true)
      
      const uuid = getUserUUID()
      const headers = {
        'X-User-UUID': uuid
      }
      
      const response = await fetch(`/api/apps/${slug}`, { headers })
      console.log('📡 App response status:', response?.status)
      
      if (!response || !response.ok) {
        const errorText = await response?.text() || 'Unknown error'
        console.error('❌ Fetch app failed:', errorText)
        throw new Error(`Failed to fetch app: ${response?.status} ${errorText}`)
      }
      
      const data = await response.json()
      console.log('📊 Received app data:', data)
      
      setApp(data)
      console.log('✅ App loaded successfully')
    } catch (err) {
      console.error('❌ Error fetching app:', err)
      setError('Failed to load app. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [slug])

  // Fetch riffs for this app
  const fetchRiffs = useCallback(async () => {
    if (!app) return
    
    console.log('🔄 Fetching riffs for app:', app.slug)
    try {
      setRiffsLoading(true)
      
      const uuid = getUserUUID()
      const headers = {
        'X-User-UUID': uuid
      }
      
      const response = await fetch(`/api/apps/${app.slug}/riffs`, { headers })
      console.log('📡 Riffs response status:', response?.status)
      
      if (!response || !response.ok) {
        const errorText = await response?.text() || 'Unknown error'
        console.error('❌ Fetch riffs failed:', errorText)
        throw new Error(`Failed to fetch riffs: ${response?.status} ${errorText}`)
      }
      
      const data = await response.json()
      console.log('📊 Received riffs data:', data)
      
      setRiffs(data.riffs || [])
      console.log('✅ Riffs loaded successfully')
    } catch (err) {
      console.error('❌ Error fetching riffs:', err)
      // Don't set error for riffs, just log it
    } finally {
      setRiffsLoading(false)
    }
  }, [app])

  // Create new riff
  const handleCreateRiff = async (e) => {
    e.preventDefault()
    console.log('🆕 Creating new riff...')
    
    if (!newRiffName.trim()) {
      console.warn('❌ Riff name is empty')
      setError('Riff name is required')
      return
    }

    const riffSlug = newRiffName.trim()
    console.log('📝 Riff details:', { name: riffSlug, slug: riffSlug })
    
    if (!riffSlug) {
      console.warn('❌ Invalid riff slug generated')
      setError('Please enter a valid riff name')
      return
    }

    try {
      setCreating(true)
      setError('')
      setSuccess('')

      const uuid = getUserUUID()
      console.log('🆔 User UUID:', uuid)

      const requestData = {
        name: riffSlug,
        slug: riffSlug
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

      const response = await fetch(`/api/apps/${app.slug}/riffs`, requestOptions)
      
      console.log('📡 Create riff response status:', response?.status)

      const data = await response.json()
      console.log('📊 Create riff response data:', data)

      if (!response.ok) {
        console.error('❌ Create riff failed:', data)
        throw new Error(data.error || 'Failed to create riff')
      }

      console.log('✅ Riff created successfully:', data.riff)
      setSuccess(`Riff "${riffSlug}" created successfully!`)
      setNewRiffName('')
      
      // Refresh riffs list
      console.log('🔄 Refreshing riffs list...')
      await fetchRiffs()
      
      // Redirect to the new riff's page
      console.log('🔄 Redirecting to new riff:', data.riff.slug)
      navigate(`/apps/${app.slug}/riffs/${data.riff.slug}`)
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccess(''), 5000)
      
    } catch (err) {
      console.error('❌ Error creating riff:', err)
      setError(err.message || 'Failed to create riff. Please try again.')
    } finally {
      setCreating(false)
    }
  }

  // Handle delete riff button click
  const handleDeleteClick = (riff, event) => {
    event.preventDefault() // Prevent navigation to riff detail
    event.stopPropagation() // Stop event bubbling
    
    console.log('🗑️ Delete button clicked for riff:', riff.name)
    setDeleteModal({
      isOpen: true,
      riff: riff,
      isDeleting: false
    })
  }

  // Handle delete confirmation
  const handleDeleteConfirm = async () => {
    const riff = deleteModal.riff
    if (!riff) return

    console.log('🗑️ Confirming deletion of riff:', riff.name)
    
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

      const response = await fetch(`/api/apps/${app.slug}/riffs/${riff.slug}`, requestOptions)
      
      console.log('📡 Delete response status:', response?.status)
      console.log('📡 Delete response ok:', response?.ok)

      const data = await response.json()
      console.log('📊 Delete response data:', data)

      if (!response.ok) {
        console.error('❌ Delete riff failed:', data)
        throw new Error(data.error || 'Failed to delete riff')
      }

      console.log('✅ Riff deleted successfully:', data)
      
      // Show success message
      let successMessage = `Riff "${riff.name}" deleted successfully!`
      if (data.warnings && data.warnings.length > 0) {
        successMessage += ` (Note: ${data.warnings.join(', ')})`
      }
      setSuccess(successMessage)
      
      // Close modal
      setDeleteModal({
        isOpen: false,
        riff: null,
        isDeleting: false
      })
      
      // Refresh riffs list
      console.log('🔄 Refreshing riffs list...')
      await fetchRiffs()
      
      // Clear success message after 8 seconds (longer for delete confirmation)
      setTimeout(() => setSuccess(''), 8000)
      
    } catch (err) {
      console.error('❌ Error deleting riff:', err)
      console.error('❌ Error stack:', err.stack)
      setError(err.message || 'Failed to delete riff. Please try again.')
      
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
      riff: null,
      isDeleting: false
    })
  }

  // Load app on component mount
  useEffect(() => {
    fetchApp()
  }, [fetchApp])

  // Load riffs when app is loaded
  useEffect(() => {
    if (app) {
      fetchRiffs()
    }
  }, [app, fetchRiffs])

  // Clear error when user starts typing
  useEffect(() => {
    if (error && newRiffName) {
      setError('')
    }
  }, [newRiffName, error])

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-cyber-text">
        <div className="flex flex-col items-center justify-center py-16">
          <div className="w-10 h-10 border-4 border-cyber-border border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-cyber-muted font-mono">Loading app...</p>
        </div>
      </div>
    )
  }

  if (error && !app) {
    return (
      <div className="min-h-screen bg-black text-cyber-text">
        <div className="max-w-4xl mx-auto px-8 py-16">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-red-400 mb-4 font-mono">Error</h2>
            <p className="text-cyber-muted mb-8 font-mono">{error}</p>
            <Link to="/" className="inline-flex items-center text-cyber-muted hover:text-neon-green font-medium transition-colors duration-200 font-mono">
              ← Back to Apps
            </Link>
          </div>
        </div>
      </div>
    )
  }

  if (!app) {
    return (
      <div className="min-h-screen bg-black text-cyber-text">
        <div className="max-w-4xl mx-auto px-8 py-16">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-red-400 mb-4 font-mono">App Not Found</h2>
            <p className="text-cyber-muted mb-8 font-mono">The app &quot;{slug}&quot; could not be found.</p>
            <Link to="/" className="inline-flex items-center text-cyber-muted hover:text-neon-green font-medium transition-colors duration-200 font-mono">
              ← Back to Apps
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black text-cyber-text">
      <div className="max-w-6xl mx-auto px-6 py-6">
        {/* Navigation */}
        <nav className="mb-4">
          <div className="flex items-center space-x-2 text-sm">
            <Link to="/" className="text-cyber-muted hover:text-neon-green transition-colors duration-200">
              Apps
            </Link>
            <span className="text-gray-500">/</span>
            <span className="text-cyber-muted">{app.name}</span>
          </div>
        </nav>

        {/* App Header */}
        <header className="mb-4">
          <div className="flex flex-wrap items-baseline justify-between gap-4 mb-4">
            <div>
              <h1 className="text-3xl font-bold text-cyber-text mb-2 font-mono">{app.name}</h1>
            </div>
            <p className="text-cyber-muted font-mono text-sm">
              Created {new Date(app.created_at).toLocaleDateString()}
            </p>
          </div>
        </header>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* App Status */}
          <div className="lg:col-span-1">
            <AppStatus app={app} />
          </div>

          {/* Riffs Section */}
          <div className="lg:col-span-2">
            <section>
              {/* Create New Riff */}
              <div className="mb-12">
                <h3 className="text-xl font-semibold text-cyber-text mb-4">Create New Riff</h3>
                <div className="hacker-card p-6 rounded-lg border border-gray-700">
                  <form onSubmit={handleCreateRiff} className="space-y-6">
                    <div>
                      <input
                        type="text"
                        value={newRiffName}
                        onChange={(e) => {
                          const inputValue = e.target.value
                          const slug = createSlug(inputValue)
                          setNewRiffName(slug)
                        }}
                        placeholder="Enter riff name"
                        disabled={creating}
                        className={`w-full px-4 py-3 bg-gray-700 text-cyber-text rounded-md border transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-cyber-muted focus:border-transparent ${
                          error ? 'border-red-500' : 'border-gray-600'
                        }`}
                      />
                    </div>
                    
                    <button 
                      type="submit" 
                      disabled={creating || !newRiffName.trim()}
                      className="w-full px-6 py-3 bg-cyber-muted text-gray-900 rounded-md font-semibold hover:bg-neon-green disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 hover:transform hover:-translate-y-0.5"
                    >
                      {creating ? 'Creating...' : 'Create Riff'}
                    </button>
                  </form>

                  {error && (
                    <div className="mt-4 p-4 bg-red-900/20 border border-red-500 rounded-md text-red-400">
                      {error}
                    </div>
                  )}

                  {success && (
                    <div className="mt-4 p-4 bg-green-900/20 border border-green-500 rounded-md text-green-400">
                      {success}
                    </div>
                  )}
                </div>
              </div>

              {/* Riffs List */}
              <div>
                <h3 className="text-xl font-semibold text-cyber-text mb-4">All Riffs</h3>
                
                {riffsLoading ? (
                  <div className="flex flex-col items-center justify-center py-16">
                    <div className="w-10 h-10 border-4 border-gray-600 border-t-cyber-muted rounded-full animate-spin mb-4"></div>
                    <p className="text-cyber-muted">Loading riffs...</p>
                  </div>
                ) : riffs.length === 0 ? (
                  <div className="text-center py-16">
                    <p className="text-cyber-muted text-lg">No riffs yet. Create your first riff above!</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {riffs.map((riff) => (
                      <div 
                        key={riff.slug} 
                        className="hacker-card rounded-lg border border-gray-700 hover:border-cyber-muted transition-all duration-300 hover:transform hover:-translate-y-1 p-6 relative"
                      >
                        <Link 
                          to={`/apps/${app.slug}/riffs/${riff.slug}`}
                          className="block"
                        >
                          <div className="mb-4 pr-12">
                            <h4 className="text-xl font-semibold text-cyber-text mb-1">{riff.name}</h4>
                            <span className="text-sm text-cyber-muted font-mono">{riff.slug}</span>
                          </div>
                          
                          <div className="space-y-2">
                            <p className="text-sm text-cyber-muted">
                              Created: {new Date(riff.created_at).toLocaleDateString()}
                            </p>
                            {riff.last_message_at && (
                              <p className="text-sm text-cyber-muted">
                                Last activity: {new Date(riff.last_message_at).toLocaleDateString()}
                              </p>
                            )}
                          </div>
                        </Link>
                        
                        <button 
                          className="absolute top-4 right-4 text-red-400 hover:text-red-300 text-lg p-2 hover:bg-red-900/20 rounded transition-colors duration-200 z-10"
                          onClick={(e) => handleDeleteClick(riff, e)}
                          title={`Delete riff "${riff.name}"`}
                          aria-label={`Delete riff "${riff.name}"`}
                        >
                          🗑️
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={deleteModal.isOpen}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        title="Delete Riff"
        message={
          deleteModal.riff ? (
            <div>
              <p className="mb-4">
                Are you sure you want to delete the riff <strong>&quot;{deleteModal.riff.name}&quot;</strong>?
              </p>
              <p className="mb-4 text-cyber-muted">
                This will permanently delete:
              </p>
              <ul className="list-disc list-inside text-cyber-muted space-y-1 mb-4">
                <li>The Fly.io app: <code className="bg-cyber-accent px-1 rounded">{app?.slug}-{deleteModal.riff.slug}</code></li>
                <li>The GitHub branch: <code className="bg-cyber-accent px-1 rounded">{deleteModal.riff.slug}</code></li>
                <li>Any open pull request for this branch</li>
                <li>All riff data and chat history</li>
              </ul>
              <p className="text-red-400 font-semibold">
                This action cannot be undone.
              </p>
            </div>
          ) : null
        }
        confirmText="Delete Riff"
        cancelText="Cancel"
        isDestructive={true}
        isLoading={deleteModal.isDeleting}
      />
    </div>
  )
}

export default AppDetail