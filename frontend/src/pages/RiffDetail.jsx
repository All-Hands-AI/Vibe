import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'

function RiffDetail() {
  const { slug: appSlug, riffSlug } = useParams()
  const [app, setApp] = useState(null)
  const [riff, setRiff] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Fetch app and riff details
  const fetchData = useCallback(async () => {
    console.log('🔄 Fetching riff details:', { appSlug, riffSlug })
    try {
      setLoading(true)
      
      // First, get the app to find its ID
      const appResponse = await fetch(`/api/apps/${appSlug}`)
      console.log('📡 App response status:', appResponse?.status)
      
      if (!appResponse || !appResponse.ok) {
        const errorText = await appResponse?.text() || 'Unknown error'
        console.error('❌ Fetch app failed:', errorText)
        throw new Error(`Failed to fetch app: ${appResponse?.status} ${errorText}`)
      }
      
      const appData = await appResponse.json()
      console.log('📊 Received app data:', appData)
      setApp(appData)
      
      // Now get the riffs for this app
      const riffsResponse = await fetch(`/api/apps/${appData.slug}/riffs`)
      console.log('📡 Riffs response status:', riffsResponse?.status)
      
      if (!riffsResponse || !riffsResponse.ok) {
        const errorText = await riffsResponse?.text() || 'Unknown error'
        console.error('❌ Fetch riffs failed:', errorText)
        throw new Error(`Failed to fetch riffs: ${riffsResponse?.status} ${errorText}`)
      }
      
      const riffsData = await riffsResponse.json()
      console.log('📊 Received riffs data:', riffsData)
      
      // Find the specific riff by slug
      const foundRiff = riffsData.riffs.find(
        c => c.slug === riffSlug
      )
      
      if (!foundRiff) {
        console.error('❌ Riff not found:', riffSlug)
        throw new Error('Riff not found')
      }
      
      setRiff(foundRiff)
      console.log('✅ Data loaded successfully')
    } catch (err) {
      console.error('❌ Error fetching data:', err)
      setError(err.message || 'Failed to load riff. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [appSlug, riffSlug])

  // Load data on component mount
  useEffect(() => {
    fetchData()
  }, [fetchData])

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-cyber-text">
        <div className="flex flex-col items-center justify-center py-16">
          <div className="w-10 h-10 border-4 border-gray-600 border-t-cyber-muted rounded-full animate-spin mb-4"></div>
          <p className="text-cyber-muted">Loading riff...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black text-cyber-text">
        <div className="max-w-4xl mx-auto px-8 py-16">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-red-400 mb-4">Error</h2>
            <p className="text-cyber-muted mb-8">{error}</p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link to="/" className="inline-flex items-center text-cyber-muted hover:text-neon-green font-medium transition-colors duration-200">
                ← Back to Apps
              </Link>
              {app && (
                <Link to={`/apps/${app.slug}`} className="inline-flex items-center text-cyber-muted hover:text-neon-green font-medium transition-colors duration-200">
                  ← Back to {app.name}
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!app || !riff) {
    return (
      <div className="min-h-screen bg-black text-cyber-text">
        <div className="max-w-4xl mx-auto px-8 py-16">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-red-400 mb-4">Not Found</h2>
            <p className="text-cyber-muted mb-8">The riff could not be found.</p>
            <Link to="/" className="inline-flex items-center text-cyber-muted hover:text-neon-green font-medium transition-colors duration-200">
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
          <div className="flex items-center space-x-2 text-sm">
            <Link to="/" className="text-cyber-muted hover:text-neon-green transition-colors duration-200">
              ← Apps
            </Link>
            <span className="text-gray-500">/</span>
            <Link to={`/apps/${app.slug}`} className="text-cyber-muted hover:text-neon-green transition-colors duration-200">
              {app.name}
            </Link>
            <span className="text-gray-500">/</span>
            <span className="text-cyber-muted">{riff.name}</span>
          </div>
        </nav>

        {/* Riff Header */}
        <header className="mb-12">
          <div className="mb-6">
            <h1 className="text-4xl font-bold text-cyber-text mb-2">{riff.name}</h1>
            <span className="text-cyber-muted font-mono text-lg">{riff.slug}</span>
          </div>
          
          <div className="flex flex-wrap items-center gap-6 text-cyber-muted">
            <p>Created: {new Date(riff.created_at).toLocaleDateString()}</p>
            {riff.last_message_at && (
              <p>Last activity: {new Date(riff.last_message_at).toLocaleDateString()}</p>
            )}
            <p>Messages: {riff.message_count || 0}</p>
          </div>
        </header>

        {/* Riff Content */}
        <section className="mb-12">
          <div className="hacker-card rounded-lg border border-gray-700 p-12 text-center">
            <div className="text-6xl mb-6">💬</div>
            <h3 className="text-2xl font-bold text-cyber-muted mb-4">Riff Interface</h3>
            <p className="text-cyber-muted mb-6">This is where the riff interface would be implemented.</p>
            <div className="text-left max-w-md mx-auto">
              <p className="text-cyber-muted mb-4 font-semibold">Features to add:</p>
              <ul className="space-y-2 text-cyber-muted">
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-cyber-muted rounded-full mr-3"></span>
                  Message history display
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-cyber-muted rounded-full mr-3"></span>
                  Message input and sending
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-cyber-muted rounded-full mr-3"></span>
                  Real-time updates
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-cyber-muted rounded-full mr-3"></span>
                  File attachments
                </li>
                <li className="flex items-center">
                  <span className="w-2 h-2 bg-cyber-muted rounded-full mr-3"></span>
                  Message search and filtering
                </li>
              </ul>
            </div>
          </div>
        </section>

        {/* Riff Actions */}
        <section>
          <h2 className="text-2xl font-bold text-cyber-muted mb-6">Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="hacker-card p-6 rounded-lg border border-gray-700">
              <h4 className="text-lg font-semibold text-cyber-text mb-2">Export Riff</h4>
              <p className="text-cyber-muted mb-4">Download this riff as a file</p>
              <button className="w-full px-4 py-2 bg-gray-600 text-cyber-muted rounded-md cursor-not-allowed" disabled>
                Export (Coming Soon)
              </button>
            </div>
            
            <div className="hacker-card p-6 rounded-lg border border-gray-700">
              <h4 className="text-lg font-semibold text-cyber-text mb-2">Share Riff</h4>
              <p className="text-cyber-muted mb-4">Generate a shareable link</p>
              <button className="w-full px-4 py-2 bg-gray-600 text-cyber-muted rounded-md cursor-not-allowed" disabled>
                Share (Coming Soon)
              </button>
            </div>
            
            <div className="hacker-card p-6 rounded-lg border border-gray-700">
              <h4 className="text-lg font-semibold text-cyber-text mb-2">Archive Riff</h4>
              <p className="text-cyber-muted mb-4">Move to archived riffs</p>
              <button className="w-full px-4 py-2 bg-red-600/20 text-red-400 border border-red-500 rounded-md cursor-not-allowed" disabled>
                Archive (Coming Soon)
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

export default RiffDetail