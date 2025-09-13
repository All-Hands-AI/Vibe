function Footer() {
  return (
    <footer className="bg-black border-t-2 border-neon-green mt-auto pt-8 pb-4 neon-border relative z-10">
      <div className="max-w-6xl mx-auto px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div>
            <h3 className="text-neon-green text-2xl mb-4 font-mono neon-glow">
              <span className="text-neon-cyan">{'<'}</span>
              OpenVibe
              <span className="text-neon-cyan">{'/>'}</span>
            </h3>
            <p className="text-neon-green/80 leading-relaxed font-mono">
              🚀 Building cyberpunk experiences with React
            </p>
          </div>
          <div>
            <h4 className="text-neon-green text-lg mb-4 font-mono neon-glow">
              📡 Quick Links
            </h4>
            <ul className="list-none p-0 m-0 font-mono">
              <li className="mb-2">
                <a href="/" className="text-neon-green/70 no-underline transition-all duration-300 hover:text-neon-green hover:neon-glow">
                  {'>'} Home
                </a>
              </li>
              <li className="mb-2">
                <a href="/about" className="text-neon-green/70 no-underline transition-all duration-300 hover:text-neon-green hover:neon-glow">
                  {'>'} About
                </a>
              </li>
              <li className="mb-2">
                <a href="/contact" className="text-neon-green/70 no-underline transition-all duration-300 hover:text-neon-green hover:neon-glow">
                  {'>'} Contact
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="text-neon-green text-lg mb-4 font-mono neon-glow">
              🔗 Connect
            </h4>
            <ul className="list-none p-0 m-0 font-mono">
              <li className="mb-2">
                <a 
                  href="https://github.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-neon-green/70 no-underline transition-all duration-300 hover:text-neon-green hover:neon-glow"
                >
                  {'>'} 🐙 GitHub
                </a>
              </li>
              <li className="mb-2">
                <a 
                  href="https://twitter.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-neon-green/70 no-underline transition-all duration-300 hover:text-neon-green hover:neon-glow"
                >
                  {'>'} 🐦 Twitter
                </a>
              </li>
              <li className="mb-2">
                <a 
                  href="https://linkedin.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-neon-green/70 no-underline transition-all duration-300 hover:text-neon-green hover:neon-glow"
                >
                  {'>'} 💼 LinkedIn
                </a>
              </li>
            </ul>
          </div>
        </div>
        <div className="border-t-2 border-neon-green/30 pt-4 text-center">
          <p className="text-neon-green/60 m-0 text-sm font-mono">
            <span className="text-neon-cyan">©</span> 2025 OpenVibe. 
            <span className="text-neon-pink"> All rights reserved.</span>
            <span className="animate-terminal-blink text-neon-green"> _</span>
          </p>
          <p className="text-neon-green/40 text-xs mt-2 font-mono">
            🔐 Powered by cyberpunk energy ⚡
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Footer