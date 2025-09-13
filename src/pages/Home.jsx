import { useState, useEffect } from 'react'
import { Card, Button, LoadingSpinner } from '../components/ui'
import Layout from '../components/Layout'

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
    <Layout>
      {/* Hero Section */}
      <div className="text-center mb-16">
        <div className="bg-gradient-to-br from-background-secondary to-background-tertiary rounded-2xl p-12 mb-8">
          <h1 className="text-5xl font-bold text-primary-300 mb-4">Welcome to OpenVibe</h1>
          <p className="text-xl text-text-secondary mb-8 max-w-2xl mx-auto">
            Your React App is Running with Python Backend!
          </p>
          
          {/* Backend Status Card */}
          <Card variant="primary" className="p-6 mb-8 max-w-lg mx-auto">
            <h3 className="text-lg font-semibold text-primary-300 mb-4">🔗 Backend Connection Test</h3>
            {loading ? (
              <LoadingSpinner text="Connecting to backend..." />
            ) : (
              <div className="space-y-3">
                <div className="bg-background-primary/50 rounded-lg p-3">
                  <span className="text-primary-300 font-medium">Hello API:</span>
                  <span className="text-text-secondary ml-2">{backendMessage}</span>
                </div>
                <div className="bg-background-primary/50 rounded-lg p-3">
                  <span className="text-primary-300 font-medium">Health Check:</span>
                  <span className="text-text-secondary ml-2">{healthStatus}</span>
                </div>
              </div>
            )}
            <Button 
              variant="success"
              onClick={testBackendConnection}
              disabled={testLoading}
              loading={testLoading}
              className="mt-4"
            >
              🧪 Test Backend Again
            </Button>
          </Card>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg">Get Started</Button>
            <Button variant="secondary" size="lg">Learn More</Button>
          </div>
        </div>
      </div>
      
      {/* Features Section */}
      <div>
        <h2 className="text-3xl font-bold text-primary-300 text-center mb-12">Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card hover className="p-6 text-center">
            <h3 className="text-xl font-semibold text-primary-300 mb-3">🐍 Full-Stack</h3>
            <p className="text-text-secondary">React frontend with Python Flask backend - complete full-stack solution</p>
          </Card>
          <Card hover className="p-6 text-center">
            <h3 className="text-xl font-semibold text-primary-300 mb-3">⚡ Fast</h3>
            <p className="text-text-secondary">Built with Vite for lightning-fast development and builds</p>
          </Card>
          <Card hover className="p-6 text-center">
            <h3 className="text-xl font-semibold text-primary-300 mb-3">🔧 Modern</h3>
            <p className="text-text-secondary">Latest React features with hooks, context, and modern JavaScript</p>
          </Card>
          <Card hover className="p-6 text-center">
            <h3 className="text-xl font-semibold text-primary-300 mb-3">🚀 Deploy Ready</h3>
            <p className="text-text-secondary">Single Docker container with nginx proxy - ready for Fly.io deployment</p>
          </Card>
        </div>
      </div>
    </Layout>
  )
}

export default Home