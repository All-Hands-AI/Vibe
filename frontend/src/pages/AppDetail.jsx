import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getUserUUID } from '../utils/uuid'
import AppStatus from '../components/AppStatus'

function AppDetail() {
  const { slug } = useParams()
  const [app, setApp] = useState(null)
  const [riffs, setRiffs] = useState([])
  const [loading, setLoading] = useState(true)
  const [riffsLoading, setRiffsLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newRiffName, setNewRiffName] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')



  // Helper function to extract repo name from GitHub URL
  const getRepoName = (githubUrl) => {
    if (!githubUrl) return null
    try {
      const urlObj = new URL(githubUrl)
      const pathParts = urlObj.pathname.split('/').filter(part => part)
      if (pathParts.length >= 2) {
        return `${pathParts[0]}/${pathParts[1]}`
      }
      return null
    } catch {
      return null
    }
  }

  // Helper function to get Fly.io dashboard URL
  const getFlyDashboardUrl = (appUrl) => {
    if (!appUrl) return null
    try {
      const urlObj = new URL(appUrl)
      const hostname = urlObj.hostname
      // Extract app name from hostname (e.g., "my-app.fly.dev" -> "my-app")
      const appName = hostname.replace('.fly.dev', '')
      return `https://fly.io/apps/${appName}`
    } catch {
      return null
    }
  }

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

    const riffSlug = createSlug(newRiffName.trim())
    console.log('📝 Riff details:', { name: newRiffName.trim(), slug: riffSlug })
    
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
        name: newRiffName.trim(),
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
      setSuccess(`Riff "${newRiffName}" created successfully!`)
      setNewRiffName('')
      
      // Refresh riffs list
      console.log('🔄 Refreshing riffs list...')
      await fetchRiffs()
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccess(''), 5000)
      
    } catch (err) {
      console.error('❌ Error creating riff:', err)
      setError(err.message || 'Failed to create riff. Please try again.')
    } finally {
      setCreating(false)
    }
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
      <div className="max-w-6xl mx-auto px-8 py-8">
        {/* Navigation */}
        <nav className="mb-8">
          <Link to="/" className="inline-flex items-center text-cyber-muted hover:text-neon-green font-medium transition-colors duration-200 font-mono">
            ← Back to Apps
          </Link>
        </nav>

        {/* App Header */}
        <header className="mb-12">
          <div className="flex flex-wrap items-baseline justify-between gap-4 mb-6">
            <div>
              <h1 className="text-4xl font-bold text-cyber-text mb-2 font-mono">{app.name}</h1>
              <span className="text-cyber-muted font-mono text-lg">{app.slug}</span>
            </div>
            <p className="text-cyber-muted font-mono text-sm">
              Created {new Date(app.created_at).toLocaleDateString()}
            </p>
          </div>
          
          <div className="flex flex-wrap items-center gap-6">
            {app.github_url && (
              <a 
                href={app.github_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-cyber-muted hover:text-neon-green font-medium transition-colors duration-200 font-mono"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                {getRepoName(app.github_url) || 'GitHub'}
              </a>
            )}
            {app.fly_status?.app_url && (
              <a 
                href={getFlyDashboardUrl(app.fly_status.app_url)} 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-cyber-muted hover:text-neon-green font-medium transition-colors duration-200 font-mono"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                </svg>
                Fly.io Dashboard
              </a>
            )}
          </div>
        </header>

        {/* App Status */}
        <section className="mb-12">
          <h2 className="text-3xl font-bold text-cyber-text mb-8 font-mono">App Status</h2>
          <AppStatus app={app} />
        </section>

        {/* Riffs Section */}
        <section>
          <h2 className="text-3xl font-bold text-cyber-muted mb-8">Riffs</h2>
          
          {/* Create New Riff */}
          <div className="mb-12">
            <h3 className="text-2xl font-semibold text-cyber-text mb-6">Create New Riff</h3>
            <div className="hacker-card p-6 rounded-lg border border-gray-700 max-w-2xl">
              <form onSubmit={handleCreateRiff} className="space-y-6">
                <div>
                  <input
                    type="text"
                    value={newRiffName}
                    onChange={(e) => setNewRiffName(e.target.value)}
                    placeholder="Enter riff name"
                    disabled={creating}
                    className={`w-full px-4 py-3 bg-gray-700 text-cyber-text rounded-md border transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-cyber-muted focus:border-transparent ${
                      error ? 'border-red-500' : 'border-gray-600'
                    }`}
                  />
                  {newRiffName && (
                    <div className="mt-2 text-sm text-cyber-muted">
                      Slug: <code className="bg-gray-700 px-2 py-1 rounded text-cyber-muted">{createSlug(newRiffName)}</code>
                    </div>
                  )}
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
            <h3 className="text-2xl font-semibold text-cyber-text mb-6">All Riffs</h3>
            
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
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {riffs.map((riff) => (
                  <Link 
                    key={riff.slug} 
                    to={`/apps/${app.slug}/riffs/${riff.slug}`}
                    className="block hacker-card rounded-lg border border-gray-700 hover:border-cyber-muted transition-all duration-300 hover:transform hover:-translate-y-1 p-6"
                  >
                    <div className="mb-4">
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
                ))}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}

export default AppDetail