function Footer() {
  return (
    <footer className="bg-slate-900 border-t-2 border-slate-600 mt-auto pt-8 pb-4 relative z-10">
      <div className="max-w-6xl mx-auto px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div>
            <h3 className="text-slate-200 text-2xl mb-4 font-mono">
              <span className="text-slate-400">{'~'}</span>
              OpenVibe
              <span className="text-slate-400">{'~'}</span>
            </h3>
            <p className="text-slate-400 leading-relaxed font-mono">
              ✨ Creating vibecoding experiences with React
            </p>
          </div>
          <div>
            <h4 className="text-slate-200 text-lg mb-4 font-mono">
              🎨 Quick Links
            </h4>
            <ul className="list-none p-0 m-0 font-mono">
              <li className="mb-2">
                <a href="/" className="text-slate-400 no-underline transition-all duration-300 hover:text-violet-400">
                  {'~'} Vibes
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="text-slate-200 text-lg mb-4 font-mono">
              🌟 Connect
            </h4>
            <ul className="list-none p-0 m-0 font-mono">
              <li className="mb-2">
                <a 
                  href="https://github.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-slate-400 no-underline transition-all duration-300 hover:text-violet-400"
                >
                  {'~'} 🐙 GitHub
                </a>
              </li>
              <li className="mb-2">
                <a 
                  href="https://twitter.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-slate-400 no-underline transition-all duration-300 hover:text-violet-400"
                >
                  {'~'} 🐦 Twitter
                </a>
              </li>
              <li className="mb-2">
                <a 
                  href="https://linkedin.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-slate-400 no-underline transition-all duration-300 hover:text-violet-400"
                >
                  {'~'} 💼 LinkedIn
                </a>
              </li>
            </ul>
          </div>
        </div>
        <div className="border-t-2 border-slate-600 pt-4 text-center">
          <p className="text-slate-400 m-0 text-sm font-mono">
            <span className="text-slate-200">©</span> 2025 OpenVibe. 
            <span className="text-slate-400"> All rights reserved.</span>
          </p>
          <p className="text-slate-400 text-xs mt-2 font-mono">
            ✨ Powered by creative vibes 🎨
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Footer