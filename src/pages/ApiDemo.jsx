import { useState, useEffect } from 'react'
import './ApiDemo.css'

function ApiDemo() {
  console.log('🎬 ApiDemo component rendering...')
  
  const [apiResponse, setApiResponse] = useState(null)
  const [vibes, setVibes] = useState([])
  const [loading, setLoading] = useState(false)
  const [backendStatus, setBackendStatus] = useState('checking')
  const [connectionLogs, setConnectionLogs] = useState([])

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString()
    console.log(`[API Demo ${type.toUpperCase()}] ${message}`)
    setConnectionLogs(prev => [...prev, { message, type, timestamp }])
  }

  const testBackendConnection = async () => {
    console.log('🚀 testBackendConnection function called')
    addLog('🔍 Testing backend connection...', 'info')
    
    try {
      console.log('📡 About to fetch /api/hello')
      const startTime = Date.now()
      const response = await fetch('/api/hello')
      const endTime = Date.now()
      const responseTime = endTime - startTime
      
      console.log('📨 Fetch response received:', response)
      console.log('📊 Response status:', response.status)
      console.log('⏱️ Response time:', responseTime + 'ms')
      
      if (response.ok) {
        console.log('✅ Response is OK, parsing JSON...')
        const data = await response.json()
        console.log('📄 Parsed JSON data:', data)
        
        setBackendStatus('connected')
        addLog(`✅ Backend connected successfully! (${responseTime}ms)`, 'success')
        addLog(`📡 Response: ${data.message}`, 'success')
        addLog(`🕐 Server timestamp: ${data.timestamp}`, 'info')
        return data
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
    } catch (error) {
      console.error('❌ Backend connection error:', error)
      setBackendStatus('error')
      addLog(`❌ Backend connection failed: ${error.message}`, 'error')
      return null
    }
  }

  useEffect(() => {
    console.log('🎯 useEffect triggered - API Demo page loaded')
    addLog('🚀 API Demo page loaded', 'info')
    console.log('🔄 About to call testBackendConnection')
    testBackendConnection()
  }, [])

  const callHelloApi = async () => {
    console.log('🔘 callHelloApi function called')
    setLoading(true)
    addLog('📞 Calling Hello API...', 'info')
    
    try {
      console.log('📡 Manual Hello API fetch starting...')
      const startTime = Date.now()
      const response = await fetch('/api/hello')
      const endTime = Date.now()
      const responseTime = endTime - startTime
      
      console.log('📨 Manual Hello API response:', response)
      const data = await response.json()
      console.log('📄 Manual Hello API data:', data)
      
      setApiResponse(data)
      setVibes([]) // Clear vibes when showing hello response
      addLog(`✅ Hello API responded in ${responseTime}ms`, 'success')
    } catch (error) {
      console.error('❌ Manual Hello API error:', error)
      setApiResponse({ error: error.message })
      addLog(`❌ Hello API failed: ${error.message}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  const callVibesApi = async () => {
    console.log('🎨 callVibesApi function called')
    setLoading(true)
    addLog('🎨 Calling Vibes API...', 'info')
    
    try {
      console.log('📡 Manual Vibes API fetch starting...')
      const startTime = Date.now()
      const response = await fetch('/api/vibes')
      const endTime = Date.now()
      const responseTime = endTime - startTime
      
      console.log('📨 Manual Vibes API response:', response)
      const data = await response.json()
      console.log('📄 Manual Vibes API data:', data)
      
      setVibes(data.vibes || [])
      setApiResponse(data)
      addLog(`✅ Vibes API responded with ${data.vibes?.length || 0} vibes in ${responseTime}ms`, 'success')
    } catch (error) {
      console.error('❌ Manual Vibes API error:', error)
      setApiResponse({ error: error.message })
      setVibes([])
      addLog(`❌ Vibes API failed: ${error.message}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="api-demo">
      <div className="container">
        <h1>API Demo</h1>
        <p>Test the Python serverless functions deployed on Vercel</p>
        
        <div className="backend-status">
          <h2>Backend Status</h2>
          <div className={`status-indicator ${backendStatus}`}>
            {backendStatus === 'checking' && '🔄 Checking connection...'}
            {backendStatus === 'connected' && '✅ Backend Connected'}
            {backendStatus === 'error' && '❌ Backend Disconnected'}
          </div>
        </div>

        <div className="connection-logs">
          <h3>Connection Logs</h3>
          <div className="logs-container">
            {connectionLogs.map((log, index) => (
              <div key={index} className={`log-entry ${log.type}`}>
                <span className="log-timestamp">[{log.timestamp}]</span>
                <span className="log-message">{log.message}</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="api-section">
          <h2>Available Endpoints</h2>
          <div className="button-group">
            <button onClick={callHelloApi} disabled={loading} className="api-button">
              {loading ? 'Loading...' : 'Test Hello API'}
            </button>
            <button onClick={callVibesApi} disabled={loading} className="api-button">
              {loading ? 'Loading...' : 'Get Random Vibes'}
            </button>
          </div>
          
          {apiResponse && (
            <div className="response-section">
              <h3>API Response:</h3>
              <pre className="response-json">{JSON.stringify(apiResponse, null, 2)}</pre>
            </div>
          )}
          
          {vibes.length > 0 && (
            <div className="vibes-section">
              <h3>Current Vibes ({vibes.length}):</h3>
              <div className="vibes-grid">
                {vibes.map(vibe => (
                  <div 
                    key={vibe.id} 
                    className="vibe-card"
                    style={{ borderColor: vibe.color }}
                  >
                    <div 
                      className="vibe-color"
                      style={{ backgroundColor: vibe.color }}
                    ></div>
                    <h4>{vibe.vibe}</h4>
                    <p className="vibe-description">{vibe.description}</p>
                    <div className="vibe-meta">
                      <span className="intensity">Intensity: {vibe.intensity}/10</span>
                      <span className="timestamp">
                        {new Date(vibe.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <div className="info-section">
          <h2>About This Demo</h2>
          <p>
            This page demonstrates the integration between the React frontend and Python 
            serverless functions running on Vercel. The API endpoints are automatically 
            deployed as serverless functions and can be called from the frontend.
          </p>
          <ul>
            <li><code>/api/hello</code> - Simple greeting endpoint with timestamp</li>
            <li><code>/api/vibes</code> - Returns randomly generated mood/vibe data</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default ApiDemo