import { useState, useEffect } from 'react'
import './Home.css'

function Home() {
  const [backendMessage, setBackendMessage] = useState('')
  const [healthStatus, setHealthStatus] = useState('')
  const [loading, setLoading] = useState(true)
  const [testLoading, setTestLoading] = useState(false)

  const testBackendConnection = async () => {
    setTestLoading(true)
    try {
      // Test the hello endpoint
      const helloResponse = await fetch('/api/hello')
      const helloData = await helloResponse.json()
      setBackendMessage(helloData.message)

      // Test the health endpoint
      const healthResponse = await fetch('/api/health')
      const healthData = await healthResponse.json()
      setHealthStatus(`${healthData.status} - ${healthData.service}`)
      
      setLoading(false)
    } catch (error) {
      console.error('Backend connection failed:', error)
      setBackendMessage('❌ Backend connection failed')
      setHealthStatus('❌ Health check failed')
      setLoading(false)
    }
    setTestLoading(false)
  }

  useEffect(() => {
    // Test the backend API connection on component mount
    testBackendConnection()
  }, [])

  return (
    <div className="home">
      <section className="hero">
        <div className="hero-content">
          <h1>Welcome to OpenVibe</h1>
          <p>Your React App is Running with Python Backend!</p>
          
          <div className="backend-status">
            <h3>🔗 Backend Connection Test</h3>
            {loading ? (
              <p>🔄 Connecting to backend...</p>
            ) : (
              <div className="api-results">
                <div className="api-result">
                  <strong>Hello API:</strong> {backendMessage}
                </div>
                <div className="api-result">
                  <strong>Health Check:</strong> {healthStatus}
                </div>
              </div>
            )}
            <button 
              className="btn btn-test" 
              onClick={testBackendConnection}
              disabled={testLoading}
            >
              {testLoading ? '🔄 Testing...' : '🧪 Test Backend Again'}
            </button>
          </div>
          
          <div className="hero-buttons">
            <button className="btn btn-primary">Get Started</button>
            <button className="btn btn-secondary">Learn More</button>
          </div>
        </div>
      </section>
      
      <section className="features">
        <div className="container">
          <h2>Features</h2>
          <div className="features-grid">
            <div className="feature-card">
              <h3>🐍 Full-Stack</h3>
              <p>React frontend with Python Flask backend - complete full-stack solution</p>
            </div>
            <div className="feature-card">
              <h3>⚡ Fast</h3>
              <p>Built with Vite for lightning-fast development and builds</p>
            </div>
            <div className="feature-card">
              <h3>🔧 Modern</h3>
              <p>Latest React features with hooks, context, and modern JavaScript</p>
            </div>
            <div className="feature-card">
              <h3>🚀 Deploy Ready</h3>
              <p>Single Docker container with nginx proxy - ready for Fly.io deployment</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default Home