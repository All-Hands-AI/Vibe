function Footer() {
  return (
    <footer className="bg-black border-t-2 border-cyber-border mt-auto pt-8 pb-4 relative z-10">
      <div className="max-w-6xl mx-auto px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div>
            <h3 className="text-cyber-text text-2xl mb-4 font-mono">
              <span className="text-cyber-muted">{'<'}</span>
              OpenVibe
              <span className="text-cyber-muted">{'/>'}</span>
            </h3>
            <p className="text-cyber-muted leading-relaxed font-mono">
              🚀 Building cyberpunk experiences with React
            </p>
          </div>
          <div>
            <h4 className="text-cyber-text text-lg mb-4 font-mono">
              📡 Quick Links
            </h4>
            <ul className="list-none p-0 m-0 font-mono">
              <li className="mb-2">
                <a href="/" className="text-cyber-muted no-underline transition-all duration-300 hover:text-neon-green">
                  {'>'} Apps
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="text-cyber-text text-lg mb-4 font-mono">
              🔗 Connect
            </h4>
            <ul className="list-none p-0 m-0 font-mono">
              <li className="mb-2">
                <a 
                  href="https://github.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-cyber-muted no-underline transition-all duration-300 hover:text-neon-green"
                >
                  {'>'} 🐙 GitHub
                </a>
              </li>
              <li className="mb-2">
                <a 
                  href="https://twitter.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-cyber-muted no-underline transition-all duration-300 hover:text-neon-green"
                >
                  {'>'} 🐦 Twitter
                </a>
              </li>
              <li className="mb-2">
                <a 
                  href="https://linkedin.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-cyber-muted no-underline transition-all duration-300 hover:text-neon-green"
                >
                  {'>'} 💼 LinkedIn
                </a>
              </li>
            </ul>
          </div>
        </div>
        <div className="border-t-2 border-cyber-border pt-4 text-center">
          <p className="text-cyber-muted m-0 text-sm font-mono">
            <span className="text-cyber-text">©</span> 2025 OpenVibe. 
            <span className="text-cyber-muted"> All rights reserved.</span>
          </p>
          <p className="text-cyber-muted text-xs mt-2 font-mono">
            🔐 Powered by cyberpunk energy ⚡
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Footer