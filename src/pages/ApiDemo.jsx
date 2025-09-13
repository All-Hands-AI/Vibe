import { useState } from 'react'
import './ApiDemo.css'

function ApiDemo() {
  const [apiResponse, setApiResponse] = useState(null)
  const [vibes, setVibes] = useState([])
  const [loading, setLoading] = useState(false)

  const callHelloApi = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/hello')
      const data = await response.json()
      setApiResponse(data)
      setVibes([]) // Clear vibes when showing hello response
    } catch (error) {
      setApiResponse({ error: error.message })
    } finally {
      setLoading(false)
    }
  }

  const callVibesApi = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/vibes')
      const data = await response.json()
      setVibes(data.vibes || [])
      setApiResponse(data)
    } catch (error) {
      setApiResponse({ error: error.message })
      setVibes([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="api-demo">
      <div className="container">
        <h1>API Demo</h1>
        <p>Test the Python serverless functions deployed on Vercel</p>
        
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