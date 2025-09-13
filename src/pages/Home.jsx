import { useState, useEffect } from 'react'

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
    <div className="min-h-[calc(100vh-200px)]">
      <section className="bg-gradient-to-br from-gray-850 to-gray-700 py-16 px-8 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-5xl font-bold text-primary-300 mb-4">Welcome to OpenVibe</h1>
          <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">Your React App is Running with Python Backend!</p>
          
          <div className="bg-primary-300/10 border border-primary-300 rounded-lg p-6 mb-8 max-w-lg mx-auto">
            <h3 className="text-xl font-semibold text-primary-300 mb-4">🔗 Backend Connection Test</h3>
            {loading ? (
              <p className="text-primary-300">🔄 Connecting to backend...</p>
            ) : (
              <div className="space-y-4">
                <div className="bg-gray-850/50 rounded p-3 text-gray-300 text-sm">
                  <strong className="text-primary-300">Hello API:</strong> {backendMessage}
                </div>
                <div className="bg-gray-850/50 rounded p-3 text-gray-300 text-sm">
                  <strong className="text-primary-300">Health Check:</strong> {healthStatus}
                </div>
              </div>
            )}
            <button 
              className="bg-green-500 text-gray-900 mt-4 text-sm px-4 py-2 rounded font-medium hover:bg-green-400 disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 hover:transform hover:-translate-y-0.5" 
              onClick={testBackendConnection}
              disabled={testLoading}
            >
              {testLoading ? '🔄 Testing...' : '🧪 Test Backend Again'}
            </button>
          </div>
          
          <div className="flex gap-4 justify-center flex-wrap">
            <button className="px-8 py-3 bg-primary-300 text-gray-900 rounded-md text-base font-semibold hover:bg-primary-400 transition-all duration-300 hover:transform hover:-translate-y-0.5">
              Get Started
            </button>
            <button className="px-8 py-3 bg-transparent text-primary-300 border-2 border-primary-300 rounded-md text-base font-semibold hover:bg-primary-300 hover:text-gray-900 transition-all duration-300 hover:transform hover:-translate-y-0.5">
              Learn More
            </button>
          </div>
        </div>
      </section>
      
      <section className="py-16 px-8 bg-gray-900">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-center text-4xl font-bold text-primary-300 mb-12">Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="bg-gray-850 p-8 rounded-lg border border-gray-700 text-center transition-all duration-300 hover:transform hover:-translate-y-2 hover:border-primary-300">
              <h3 className="text-2xl font-semibold text-primary-300 mb-4">🐍 Full-Stack</h3>
              <p className="text-gray-300 leading-relaxed">React frontend with Python Flask backend - complete full-stack solution</p>
            </div>
            <div className="bg-gray-850 p-8 rounded-lg border border-gray-700 text-center transition-all duration-300 hover:transform hover:-translate-y-2 hover:border-primary-300">
              <h3 className="text-2xl font-semibold text-primary-300 mb-4">⚡ Fast</h3>
              <p className="text-gray-300 leading-relaxed">Built with Vite for lightning-fast development and builds</p>
            </div>
            <div className="bg-gray-850 p-8 rounded-lg border border-gray-700 text-center transition-all duration-300 hover:transform hover:-translate-y-2 hover:border-primary-300">
              <h3 className="text-2xl font-semibold text-primary-300 mb-4">🔧 Modern</h3>
              <p className="text-gray-300 leading-relaxed">Latest React features with hooks, context, and modern JavaScript</p>
            </div>
            <div className="bg-gray-850 p-8 rounded-lg border border-gray-700 text-center transition-all duration-300 hover:transform hover:-translate-y-2 hover:border-primary-300">
              <h3 className="text-2xl font-semibold text-primary-300 mb-4">🚀 Deploy Ready</h3>
              <p className="text-gray-300 leading-relaxed">Single Docker container with nginx proxy - ready for Fly.io deployment</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default Home