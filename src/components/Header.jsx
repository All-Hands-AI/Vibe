import { Link, useLocation } from 'react-router-dom'

function Header() {
  const location = useLocation()
  
  const isActive = (path) => location.pathname === path

  return (
    <header className="bg-black border-b-2 border-neon-green sticky top-0 z-40 neon-border">
      <div className="max-w-6xl mx-auto flex justify-between items-center px-8 py-4">
        <Link to="/" className="text-neon-green no-underline group">
          <h1 className="text-3xl font-bold m-0 font-mono neon-glow group-hover:animate-pulse-neon">
            <span className="text-neon-cyan">{'<'}</span>
            OpenVibe
            <span className="text-neon-cyan">{'/>'}</span>
            <span className="animate-terminal-blink text-neon-green">_</span>
          </h1>
        </Link>
        <nav className="flex gap-6">
          <Link 
            to="/" 
            className={`no-underline font-mono font-semibold transition-all duration-300 px-4 py-2 border-2 ${
              isActive('/') 
                ? 'text-black bg-neon-green border-neon-green neon-glow' 
                : 'text-neon-green border-neon-green/30 hover:border-neon-green hover:bg-neon-green/10 hover:neon-glow'
            }`}
          >
            🗂️ Projects
          </Link>
          <Link 
            to="/home" 
            className={`no-underline font-mono font-semibold transition-all duration-300 px-4 py-2 border-2 ${
              isActive('/home') 
                ? 'text-black bg-neon-green border-neon-green neon-glow' 
                : 'text-neon-green border-neon-green/30 hover:border-neon-green hover:bg-neon-green/10 hover:neon-glow'
            }`}
          >
            🏠 Home
          </Link>
          <Link 
            to="/about" 
            className={`no-underline font-mono font-semibold transition-all duration-300 px-4 py-2 border-2 ${
              isActive('/about') 
                ? 'text-black bg-neon-green border-neon-green neon-glow' 
                : 'text-neon-green border-neon-green/30 hover:border-neon-green hover:bg-neon-green/10 hover:neon-glow'
            }`}
          >
            ℹ️ About
          </Link>
          <Link 
            to="/contact" 
            className={`no-underline font-mono font-semibold transition-all duration-300 px-4 py-2 border-2 ${
              isActive('/contact') 
                ? 'text-black bg-neon-green border-neon-green neon-glow' 
                : 'text-neon-green border-neon-green/30 hover:border-neon-green hover:bg-neon-green/10 hover:neon-glow'
            }`}
          >
            📞 Contact
          </Link>
        </nav>
      </div>
    </header>
  )
}

export default Header