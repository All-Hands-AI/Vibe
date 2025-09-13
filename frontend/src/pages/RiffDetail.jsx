import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, Link, useLocation } from 'react-router-dom'
import { useSetup } from '../context/SetupContext'
import { getUserUUID } from '../utils/uuid'
import BranchStatus from '../components/BranchStatus'
import ChatWindow from '../components/ChatWindow'
import LLMErrorModal from '../components/LLMErrorModal'
import { startLLMPolling, checkLLMReady } from '../utils/llmService'

function RiffDetail() {
  const { slug: appSlug, riffSlug } = useParams()
  const { userUUID } = useSetup()
  const location = useLocation()
  const [app, setApp] = useState(null)
  const [riff, setRiff] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [, setLlmReady] = useState(true)
  const [showLLMError, setShowLLMError] = useState(false)
  const stopPollingRef = useRef(null)

  // Fetch app and riff details
  const fetchData = useCallback(async () => {
    console.log('🔄 Fetching riff details:', { appSlug, riffSlug })
    try {
      setLoading(true)
      
      const uuid = getUserUUID()
      const headers = {
        'X-User-UUID': uuid
      }
      
      // First, get the app to find its ID
      const appResponse = await fetch(`/api/apps/${appSlug}`, { headers })
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
      const riffsResponse = await fetch(`/api/apps/${appData.slug}/riffs`, { headers })
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

  // Check LLM readiness and handle polling
  const handleLLMReadyChange = useCallback((isReady) => {
    console.log('🔍 LLM readiness changed:', isReady)
    setLlmReady(isReady)
    setShowLLMError(!isReady)
  }, [])

  const startPolling = useCallback(() => {
    if (stopPollingRef.current) {
      stopPollingRef.current()
    }
    
    if (appSlug && riffSlug) {
      console.log('🔄 Starting LLM polling for:', { appSlug, riffSlug })
      stopPollingRef.current = startLLMPolling(appSlug, riffSlug, handleLLMReadyChange, 10000) // Poll every 10 seconds
    }
  }, [appSlug, riffSlug, handleLLMReadyChange])

  const checkInitialLLMReadiness = useCallback(async () => {
    if (appSlug && riffSlug) {
      console.log('🔍 Checking initial LLM readiness for:', { appSlug, riffSlug })
      const isReady = await checkLLMReady(appSlug, riffSlug)
      handleLLMReadyChange(isReady)
    }
  }, [appSlug, riffSlug, handleLLMReadyChange])

  // Load data on component mount
  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Check LLM readiness when riff data is loaded
  useEffect(() => {
    if (riff && app) {
      checkInitialLLMReadiness()
      startPolling()
    }
    
    // Cleanup polling on unmount
    return () => {
      if (stopPollingRef.current) {
        stopPollingRef.current()
      }
    }
  }, [riff, app, checkInitialLLMReadiness, startPolling])

  // Scroll to top when route changes
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [location.pathname])

  // Handle LLM reset
  const handleLLMReset = useCallback(() => {
    console.log('✅ LLM reset completed, restarting polling')
    setLlmReady(true)
    setShowLLMError(false)
    // Restart polling after reset
    startPolling()
  }, [startPolling])

  const handleCloseLLMError = useCallback(() => {
    setShowLLMError(false)
  }, [])

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

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Branch Status */}
          <div className="lg:col-span-1">
            <BranchStatus app={app} />
          </div>

          {/* Chat Window */}
          <div className="lg:col-span-2">
            <div className="h-[600px]">
              {userUUID ? (
                <ChatWindow 
                  app={app} 
                  riff={riff} 
                  userUuid={userUUID} 
                />
              ) : (
                <div className="flex items-center justify-center h-full border border-gray-700 rounded-lg">
                  <div className="text-center">
                    <div className="w-8 h-8 border-4 border-gray-600 border-t-cyber-muted rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-cyber-muted">Initializing chat...</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* LLM Error Modal */}
      <LLMErrorModal
        isOpen={showLLMError}
        onClose={handleCloseLLMError}
        appSlug={appSlug}
        riffSlug={riffSlug}
        onReset={handleLLMReset}
      />
    </div>
  )
}

export default RiffDetail