import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, Link, useLocation } from 'react-router-dom'
import { useSetup } from '../context/SetupContext'
import { getUserUUID } from '../utils/uuid'
import ChatWindow from '../components/ChatWindow'
import LLMErrorModal from '../components/LLMErrorModal'
import CIStatus from '../components/CIStatus'
import { startLLMPolling, checkLLMReady } from '../utils/llmService'


function RiffDetail() {
  const { slug: appSlug, riffSlug } = useParams()
  const { userUUID } = useSetup()
  const location = useLocation()
  const [app, setApp] = useState(null)
  const [riff, setRiff] = useState(null)
  const [prStatus, setPrStatus] = useState(null)
  const [deploymentStatus, setDeploymentStatus] = useState(null)
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

  // Fetch PR status for the specific riff
  const fetchPrStatus = useCallback(async () => {
    console.log('🔄 [PR_STATUS_DEBUG] Starting fetchPrStatus for riff:', { appSlug, riffSlug })
    console.log('🔄 [PR_STATUS_DEBUG] Current app state:', app ? 'loaded' : 'not loaded')
    console.log('🔄 [PR_STATUS_DEBUG] Current riff state:', riff ? 'loaded' : 'not loaded')
    
    try {
      const uuid = getUserUUID()
      console.log('🔄 [PR_STATUS_DEBUG] User UUID:', uuid ? 'available' : 'missing')
      
      const headers = {
        'X-User-UUID': uuid
      }
      
      const apiUrl = `/api/apps/${appSlug}/riffs/${riffSlug}/pr-status`
      console.log('🔄 [PR_STATUS_DEBUG] Making API call to:', apiUrl)
      console.log('🔄 [PR_STATUS_DEBUG] Headers:', headers)
      
      const prResponse = await fetch(apiUrl, { headers })
      console.log('📡 [PR_STATUS_DEBUG] PR status response status:', prResponse?.status)
      console.log('📡 [PR_STATUS_DEBUG] PR status response ok:', prResponse?.ok)
      
      if (!prResponse || !prResponse.ok) {
        const errorText = await prResponse?.text() || 'Unknown error'
        console.error('❌ [PR_STATUS_DEBUG] Fetch PR status failed:', errorText)
        console.error('❌ [PR_STATUS_DEBUG] Response status:', prResponse?.status)
        // Don't throw error for PR status - it's optional
        setPrStatus(null)
        return
      }
      
      const prData = await prResponse.json()
      console.log('📊 [PR_STATUS_DEBUG] Received PR status data:', prData)
      console.log('📊 [PR_STATUS_DEBUG] PR status object:', prData.pr_status)
      
      if (prData.pr_status) {
        console.log('✅ [PR_STATUS_DEBUG] Setting PR status:', {
          number: prData.pr_status.number,
          title: prData.pr_status.title,
          ci_status: prData.pr_status.ci_status,
          checks: prData.pr_status.checks?.length || 0
        })
      } else {
        console.log('ℹ️ [PR_STATUS_DEBUG] No PR status in response')
      }
      
      setPrStatus(prData.pr_status)
      
    } catch (err) {
      console.error('❌ [PR_STATUS_DEBUG] Error fetching PR status:', err)
      console.error('❌ [PR_STATUS_DEBUG] Error stack:', err.stack)
      // Don't fail the whole page if PR status fails
      setPrStatus(null)
    }
  }, [appSlug, riffSlug, app, riff])

  // Fetch deployment status for the specific riff
  const fetchDeploymentStatus = useCallback(async () => {
    console.log('🚀 Fetching deployment status for riff:', { appSlug, riffSlug })
    try {
      const uuid = getUserUUID()
      const headers = {
        'X-User-UUID': uuid
      }
      
      const deployResponse = await fetch(`/api/apps/${appSlug}/riffs/${riffSlug}/deployment`, { headers })
      console.log('📡 Deployment status response status:', deployResponse?.status)
      
      if (!deployResponse || !deployResponse.ok) {
        const errorText = await deployResponse?.text() || 'Unknown error'
        console.error('❌ Fetch deployment status failed:', errorText)
        // Don't throw error for deployment status - it's optional
        setDeploymentStatus(null)
        return
      }
      
      const deployData = await deployResponse.json()
      console.log('📊 Received deployment status data:', deployData)
      setDeploymentStatus(deployData)
      
    } catch (err) {
      console.error('❌ Error fetching deployment status:', err)
      // Don't fail the whole page if deployment status fails
      setDeploymentStatus(null)
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
      stopPollingRef.current = startLLMPolling(appSlug, riffSlug, handleLLMReadyChange, 30000) // Poll every 30 seconds
    }
  }, [appSlug, riffSlug, handleLLMReadyChange])

  const checkInitialLLMReadiness = useCallback(async () => {
    if (appSlug && riffSlug) {
      console.log('🔍 Checking initial LLM readiness for:', { appSlug, riffSlug })
      // Wait a moment to allow LLM to be created if this is a new riff
      await new Promise(resolve => setTimeout(resolve, 1000))
      const isReady = await checkLLMReady(appSlug, riffSlug)
      handleLLMReadyChange(isReady)
    }
  }, [appSlug, riffSlug, handleLLMReadyChange])

  // Load data on component mount
  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Check LLM readiness and fetch PR status when riff data is loaded
  useEffect(() => {
    console.log('🔄 [PR_STATUS_DEBUG] useEffect triggered - checking conditions:', {
      riff: riff ? 'loaded' : 'not loaded',
      app: app ? 'loaded' : 'not loaded',
      appSlug,
      riffSlug
    })
    
    if (riff && app) {
      console.log('✅ [PR_STATUS_DEBUG] Both riff and app loaded, calling fetchPrStatus')
      checkInitialLLMReadiness()
      startPolling()
      fetchPrStatus() // Fetch PR status for this specific riff
      fetchDeploymentStatus() // Fetch deployment status for this specific riff
    } else {
      console.log('⏳ [PR_STATUS_DEBUG] Waiting for riff and app to load before fetching PR status')
    }
    
    // Cleanup polling on unmount
    return () => {
      if (stopPollingRef.current) {
        stopPollingRef.current()
      }
    }
  }, [riff, app, appSlug, riffSlug, checkInitialLLMReadiness, startPolling, fetchPrStatus, fetchDeploymentStatus])

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
      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Navigation */}
        <nav className="mb-4">
          <div className="flex items-center space-x-2 text-sm">
            <Link to="/" className="text-cyber-muted hover:text-neon-green transition-colors duration-200">
              Apps
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
        <header className="mb-4">
          <div className="flex flex-wrap items-baseline justify-between gap-4 mb-4">
            <div>
              <h1 className="text-3xl font-bold text-cyber-text font-mono mb-2">{riff.name}</h1>
              {/* PR Status Subheading */}
              {prStatus && (
                <div className="flex items-center gap-3 text-sm font-mono">
                  <a
                    href={prStatus.html_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 transition-colors duration-200"
                  >
                    #{prStatus.number} {prStatus.title}
                  </a>
                  <span className={`${prStatus.draft ? 'text-gray-400' : 'text-green-400'}`}>
                    {prStatus.draft ? '📝 Draft' : '🟢 Ready'}
                  </span>
                  {/* CI Status */}
                  <CIStatus prStatus={prStatus} />
                </div>
              )}
            </div>
            <p className="text-cyber-muted font-mono text-sm">
              Created {new Date(riff.created_at).toLocaleDateString()}
            </p>
          </div>
        </header>

        {/* Main Content Grid - 2 columns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-200px)]">
          {/* Left Sidebar - Chat */}
          <div className="flex flex-col">
            {/* Chat Window */}
            <div className="flex-1 min-h-0">
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

          {/* Right Side - Iframe */}
          <div className="flex flex-col">
            {/* Deployment Status Header */}
            <div className="mb-2">
              {deploymentStatus ? (
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    {deploymentStatus.status === 'pending' && (
                      <>
                        <div className="w-3 h-3 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin"></div>
                        <h3 className="text-sm font-semibold text-yellow-400 font-mono">🚀 Deploying...</h3>
                      </>
                    )}
                    {deploymentStatus.status === 'success' && (
                      <>
                        <div className="w-3 h-3 bg-green-400 rounded-full"></div>
                        <h3 className="text-sm font-semibold text-green-400 font-mono">🚀 Live App</h3>
                      </>
                    )}
                    {deploymentStatus.status === 'error' && (
                      <>
                        <div className="w-3 h-3 bg-red-400 rounded-full"></div>
                        <h3 className="text-sm font-semibold text-red-400 font-mono">🚀 Deployment Failed</h3>
                      </>
                    )}
                    <div className="flex items-center gap-3 text-xs">
                      {deploymentStatus.details?.workflow_url && (
                        <a
                          href={deploymentStatus.details.workflow_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-cyber-muted hover:text-blue-400 font-mono transition-colors duration-200 underline"
                        >
                          GitHub
                        </a>
                      )}
                      <a
                        href={`https://fly.io/apps/${app.name}-${riff.name}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-cyber-muted hover:text-blue-400 font-mono transition-colors duration-200 underline"
                      >
                        Fly.io
                      </a>
                    </div>
                  </div>
                  <a
                    href={`https://${app.name}-${riff.name}.fly.dev`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cyber-muted hover:text-blue-400 font-mono text-xs transition-colors duration-200 underline"
                  >
                    {app.name}-{riff.name}.fly.dev
                  </a>
                </div>
              ) : (
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-cyber-text font-mono">🚀 Live App</h3>
                    <div className="flex items-center gap-3 text-xs">
                      <a
                        href="https://github.com/rbren/OpenVibe/actions"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-cyber-muted hover:text-blue-400 font-mono transition-colors duration-200 underline"
                      >
                        GitHub
                      </a>
                      <a
                        href={`https://fly.io/apps/${app.name}-${riff.name}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-cyber-muted hover:text-blue-400 font-mono transition-colors duration-200 underline"
                      >
                        Fly.io
                      </a>
                    </div>
                  </div>
                  <a
                    href={`https://${app.name}-${riff.name}.fly.dev`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cyber-muted hover:text-blue-400 font-mono text-xs transition-colors duration-200 underline"
                  >
                    {app.name}-{riff.name}.fly.dev
                  </a>
                </div>
              )}
            </div>
            
            <div className="flex-1 border border-gray-700 rounded-lg overflow-hidden">
              <iframe
                src={`https://${app.name}-${riff.name}.fly.dev`}
                className="w-full h-full"
                title="Live App Preview"
                sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-popups-to-escape-sandbox"
              />
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