import './Home.css'

function Home() {
  return (
    <div className="home">
      <section className="hero">
        <div className="hero-content">
          <h1>Welcome to OpenVibe</h1>
          <p>Your React App is Running!</p>
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
              <h3>⚡ Fast</h3>
              <p>Built with Vite for lightning-fast development and builds</p>
            </div>
            <div className="feature-card">
              <h3>🧪 Tested</h3>
              <p>Comprehensive testing setup with Vitest and React Testing Library</p>
            </div>
            <div className="feature-card">
              <h3>🔧 Modern</h3>
              <p>Latest React features with hooks, context, and modern JavaScript</p>
            </div>
            <div className="feature-card">
              <h3>🚀 CI/CD</h3>
              <p>GitHub Actions workflow for automated testing and deployment</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default Home