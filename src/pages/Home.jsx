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
    <div className="min-h-[calc(100vh-200px)] relative">
      <section className="bg-gradient-to-br from-black via-terminal-darkgray to-terminal-gray py-16 px-8 text-center relative z-10">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-6xl font-bold text-neon-green mb-4 font-mono neon-glow-strong glitch-text" data-text="Welcome to OpenVibe">
            <span className="text-neon-cyan">{'>'}</span> Welcome to OpenVibe <span className="animate-terminal-blink">_</span>
          </h1>
          <p className="text-xl text-neon-green/80 mb-8 max-w-2xl mx-auto font-mono">
            🔥 Your Cyberpunk React App is Running with Python Backend! 🐍
          </p>
          
          <div className="terminal-window mb-8 max-w-lg mx-auto">
            <div className="terminal-header">
              💻 BACKEND CONNECTION TEST
            </div>
            <div className="terminal-content">
              {loading ? (
                <p className="text-neon-green font-mono">
                  <span className="animate-pulse">{'>'}</span> Connecting to backend...
                  <span className="animate-terminal-blink">_</span>
                </p>
              ) : (
                <div className="space-y-4 text-left">
                  <div className="bg-terminal-gray/50 rounded p-3 text-neon-green text-sm font-mono border border-neon-green/30">
                    <span className="text-neon-cyan">$</span> <strong className="text-neon-green">Hello API:</strong> {backendMessage}
                  </div>
                  <div className="bg-terminal-gray/50 rounded p-3 text-neon-green text-sm font-mono border border-neon-green/30">
                    <span className="text-neon-cyan">$</span> <strong className="text-neon-green">Health Check:</strong> {healthStatus}
                  </div>
                </div>
              )}
              <button 
                className="btn-hacker mt-4 text-sm disabled:opacity-60 disabled:cursor-not-allowed" 
                onClick={testBackendConnection}
                disabled={testLoading}
              >
                {testLoading ? '🔄 Testing...' : '🧪 Test Backend Again'}
              </button>
            </div>
          </div>
          
          <div className="flex gap-4 justify-center flex-wrap">
            <button className="btn-hacker-primary text-base">
              🚀 Get Started
            </button>
            <button className="btn-hacker text-base">
              📖 Learn More
            </button>
          </div>
        </div>
      </section>
      
      <section className="py-16 px-8 bg-black relative z-10">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-center text-4xl font-bold text-neon-green mb-12 font-mono neon-glow">
            <span className="text-neon-cyan">{'<'}</span> Features <span className="text-neon-cyan">{'/>'}</span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="hacker-card text-center group">
              <h3 className="text-2xl font-semibold text-neon-green mb-4 font-mono neon-glow group-hover:animate-pulse-neon">
                🐍 Full-Stack
              </h3>
              <p className="text-neon-green/80 leading-relaxed font-mono">
                React frontend with Python Flask backend - complete cyberpunk solution
              </p>
            </div>
            <div className="hacker-card text-center group">
              <h3 className="text-2xl font-semibold text-neon-green mb-4 font-mono neon-glow group-hover:animate-pulse-neon">
                ⚡ Lightning Fast
              </h3>
              <p className="text-neon-green/80 leading-relaxed font-mono">
                Built with Vite for matrix-speed development and builds
              </p>
            </div>
            <div className="hacker-card text-center group">
              <h3 className="text-2xl font-semibold text-neon-green mb-4 font-mono neon-glow group-hover:animate-pulse-neon">
                🔧 Cutting Edge
              </h3>
              <p className="text-neon-green/80 leading-relaxed font-mono">
                Latest React features with hooks, context, and futuristic JavaScript
              </p>
            </div>
            <div className="hacker-card text-center group">
              <h3 className="text-2xl font-semibold text-neon-green mb-4 font-mono neon-glow group-hover:animate-pulse-neon">
                🚀 Deploy Ready
              </h3>
              <p className="text-neon-green/80 leading-relaxed font-mono">
                Dockerized container with nginx proxy - ready for cyber deployment
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default Home